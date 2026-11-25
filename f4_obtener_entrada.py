# LAS 3 VALIDACIONES (cada una con su mensaje de error claro):
#   1. La preventa ya venció            -> la llave ya no existe en Redis.
#   2. El cliente ya tiene entrada      -> ya hay una entrada suya de ese evento en Mongo.
#   3. No quedan entradas disponibles   -> el contador de Redis está en 0.
#
# ENTRADAS:  nombre del cliente e id del evento escogido.
# SALIDAS:   los datos de la entrada entregada (código, evento, etc.).
# RESTRICCIONES:
#   - Cada cliente solo puede tener UNA entrada por evento.
#   - El descuento en Redis es ATÓMICO (script Lua): si dos clientes piden
#     la última entrada al mismo tiempo, solo uno la recibe.
#   - Si algo falla al guardar en Mongo, la entrada se devuelve a Redis
#     para no perder entradas.
#   - Mongo y Redis deben estar encendidos.
# =====================================================================

# datetime nos da la fecha y hora actual para registrar cuándo se obtuvo la entrada.
from datetime import datetime

# DuplicateKeyError es el error de Mongo cuando se viola un índice único.
from pymongo.errors import DuplicateKeyError

# Colecciones de Mongo, conexión a Redis y prefijo de llaves, todo desde db.py.
from db import coleccion_eventos, coleccion_entradas, cliente_redis, PREFIJO_PREVENTA


# Largo máximo permitido para el nombre del cliente.
LARGO_MAXIMO_NOMBRE = 60

# Cuántas veces reintentamos guardar si dos entradas generan el mismo código a la vez.
INTENTOS_GUARDADO = 5


# ---------------------------------------------------------------------
# SCRIPTS LUA PARA REDIS
# Redis ejecuta un script Lua completo sin que nadie más se meta en medio
# (es atómico). Así evitamos que dos clientes se lleven la misma entrada.
# ---------------------------------------------------------------------

# DESCONTAR: resta 1 a las entradas disponibles.
#   Devuelve -1 si la llave no existe (preventa vencida),
#            -2 si ya no quedan entradas (valor en 0),
#            o las entradas que quedan después de descontar (0 o más).

LUA_DESCONTAR = """
local disponibles = redis.call('GET', KEYS[1])
if not disponibles then return -1 end
if tonumber(disponibles) <= 0 then return -2 end
return redis.call('DECR', KEYS[1])
"""

# DEVOLVER: suma 1 de vuelta (se usa si falló el guardado en Mongo).
#   Solo suma si la llave todavía existe, para no resucitar una preventa vencida.
LUA_DEVOLVER = """
if redis.call('EXISTS', KEYS[1]) == 1 then
    return redis.call('INCR', KEYS[1])
end
return -1
"""

# register_script() prepara cada script para llamarlo como una función normal.
descontar_entrada_redis = cliente_redis.register_script(LUA_DESCONTAR)
devolver_entrada_redis = cliente_redis.register_script(LUA_DEVOLVER)


def obtenerPreventasAbiertas():
    """
    QUÉ HACE:
        Trae las preventas abiertas para mostrarlas en la lista donde el
        cliente escoge el evento.
    ENTRADAS:
        Ninguna.
    SALIDAS:
        Una lista de diccionarios con id, nombre y categoria, ordenada por
        categoría y luego por nombre.
    RESTRICCIONES:
        - Una preventa está abierta si su llave existe en Redis (si venció,
          Redis ya la borró) y le quedan entradas (valor mayor que 0).
        - Si no hay preventas abiertas, devuelve [].
        - Redis y Mongo deben estar encendidos.
    """
    # Aquí guardamos los ids de los eventos que tienen preventa abierta.
    ids_abiertos = []

    # scan_iter recorre las llaves que empiezan con "preventa:" sin bloquear Redis.
    for llave in cliente_redis.scan_iter(match=PREFIJO_PREVENTA + "*"):
        # El valor es la cantidad de entradas disponibles (texto, o None si venció justo ahora).
        disponibles = cliente_redis.get(llave)
        # Solo cuentan las que existen y todavía tienen entradas.
        if disponibles is not None and int(disponibles) > 0:
            # Quitamos el prefijo para quedarnos con el id del evento (ej. "E001").
            ids_abiertos.append(llave[len(PREFIJO_PREVENTA):])

    # Si no hay ninguna, no hace falta consultar Mongo.
    if not ids_abiertos:
        return []

    # Buscamos en Mongo el nombre y la categoría de esos eventos.
    # {"$in": [...]} significa "cuyo id esté dentro de esta lista".
    cursor = coleccion_eventos.find(
        {"id": {"$in": ids_abiertos}},
        {"_id": 0, "id": 1, "nombre": 1, "categoria": 1}
    )
    # Ordenamos: primero por categoría y después por nombre.
    return sorted(cursor, key=lambda e: (e["categoria"], e["nombre"]))


def limpiarNombre(nombre):
    """
    QUÉ HACE:
        Valida el nombre del cliente y le quita los espacios sobrantes.
    ENTRADAS:
        nombre -> lo que escribió la persona (puede ser None si no llegó el campo).
    SALIDAS:
        El nombre limpio, por ejemplo "  Ana   Mora " -> "Ana Mora".
    RESTRICCIONES:
        Lanza ValueError si está vacío o pasa de LARGO_MAXIMO_NOMBRE letras.
    """
    # " ".join(texto.split()) quita espacios al inicio/final y deja un solo espacio entre palabras.
    limpio = " ".join((nombre or "").split())

    if not limpio:
        raise ValueError("Debe escribir el nombre del cliente.")
    if len(limpio) > LARGO_MAXIMO_NOMBRE:
        raise ValueError(f"El nombre no puede tener más de {LARGO_MAXIMO_NOMBRE} caracteres.")
    return limpio


def obtenerEntrada(nombre_cliente, id_evento):
    """
    QUÉ HACE:
        Entrega una entrada de la preventa de un evento: valida, descuenta
        1 en Redis y registra la entrada en MongoDB.
    ENTRADAS:
        nombre_cliente -> el nombre que escribió el cliente.
        id_evento      -> el id del evento escogido (ej. "E001").
    SALIDAS:
        Un diccionario con: codigo, cliente, nombre (del evento), categoria
        y disponibles (cuántas entradas le quedan a la preventa).
    RESTRICCIONES:
        Lanza ValueError con un mensaje claro si:
          - falta el nombre o no se escogió un evento,
          - el evento no existe en el catálogo,
          - la preventa ya venció,
          - el cliente ya tiene una entrada de ese evento,
          - ya no quedan entradas disponibles.
    """
    # Paso 1: revisar los datos que llegaron del formulario.
    cliente = limpiarNombre(nombre_cliente)
    if not id_evento:
        raise ValueError("Debe seleccionar un evento.")

    # "cliente_clave" es el nombre en minúscula: así "Ana" y "ana" son la misma persona.
    cliente_clave = cliente.casefold()

    # Paso 2: buscar el evento en el catálogo de Mongo (de ahí salen el nombre y la categoría).
    evento = coleccion_eventos.find_one({"id": id_evento}, {"_id": 0})
    if evento is None:
        raise ValueError("El evento seleccionado no existe en el catálogo.")

    # Paso 3: crear los ÍNDICES ÚNICOS (si ya existen, no hace nada).
    #   - (cliente_clave, evento_id): Mongo mismo impide dos entradas del mismo cliente al mismo evento.
    #   - codigo: Mongo mismo impide dos entradas con el mismo código.
    coleccion_entradas.create_index([("cliente_clave", 1), ("evento_id", 1)], unique=True)
    coleccion_entradas.create_index("codigo", unique=True)

    # La llave de Redis de esta preventa, por ejemplo "preventa:E001".
    llave = PREFIJO_PREVENTA + id_evento

    # VALIDACIÓN 1: ¿la preventa venció?
    # Cuando el TTL llega a cero Redis borra la llave, así que si no existe, ya venció.
    if not cliente_redis.exists(llave):
        raise ValueError(f"La preventa de '{evento['nombre']}' ya venció.")

    # VALIDACIÓN 2: ¿el cliente ya tiene una entrada de este evento?
    if clienteTieneEntrada(cliente_clave, id_evento):
        raise ValueError("Cliente ya tiene una entrada de este evento.")

    # VALIDACIÓN 3: ¿quedan entradas? Se descuenta en Redis de forma atómica.
    # El script devuelve -1 (venció justo ahora), -2 (agotadas) o lo que queda.
    disponibles = int(descontar_entrada_redis(keys=[llave]))
    if disponibles == -1:
        raise ValueError(f"La preventa de '{evento['nombre']}' ya venció.")
    if disponibles == -2:
        raise ValueError(f"Ya no hay entradas disponibles para '{evento['nombre']}'.")

    # Paso 4: guardar la entrada en Mongo.
    # Si algo sale mal aquí, devolvemos la entrada a Redis para no perderla.
    try:
        codigo = guardarEntrada(cliente, cliente_clave, evento)
    except Exception:
        devolver_entrada_redis(keys=[llave])
        raise

    # Paso 5: devolvemos los datos para el mensaje de éxito.
    return {
        "codigo": codigo,                    # código único de la entrada
        "cliente": cliente,                  # nombre del cliente
        "nombre": evento["nombre"],          # nombre del evento
        "categoria": evento["categoria"],    # categoría del evento
        "disponibles": disponibles,          # entradas que le quedan a la preventa
    }


def clienteTieneEntrada(cliente_clave, id_evento):
    """
    QUÉ HACE:
        Revisa en Mongo si el cliente ya tiene una entrada de ese evento.
    ENTRADAS:
        cliente_clave -> nombre del cliente en minúscula.
        id_evento     -> id del evento.
    SALIDAS:
        True si ya tiene entrada, False si no.
    RESTRICCIONES:
        Ninguna.
    """
    # find_one devuelve el documento o None; "is not None" lo convierte en True/False.
    return coleccion_entradas.find_one(
        {"cliente_clave": cliente_clave, "evento_id": id_evento}, {"_id": 1}
    ) is not None


def guardarEntrada(cliente, cliente_clave, evento):
    """
    QUÉ HACE:
        Genera el código único y guarda la entrada en la colección "entradas".
    ENTRADAS:
        cliente: nombre del cliente (limpio).
        cliente_clave: nombre del cliente en minúscula.
        evento: el documento del evento (de Mongo).
    SALIDAS:
        El código generado, con la forma <id del evento>-<número de 4 cifras>,
        por ejemplo "E001-0001", "E001-0002", ...
    RESTRICCIONES:
        Lanza ValueError si el cliente ya tenía entrada (por si dos clics
        llegaron a la vez) o si no se logró generar un código único.
    """
    id_evento = evento["id"]
    # usa _ por ser el identificador de _id en Mongo, aunque no lo guardamos en la entrada.
    for _ in range(INTENTOS_GUARDADO):
        # El número de la entrada es: cuántas lleva ese evento + 1.
        numero = coleccion_entradas.count_documents({"evento_id": id_evento}) + 1
        codigo = f"{id_evento}-{numero:04d}"

        try:
            coleccion_entradas.insert_one({
                "codigo": codigo,
                "cliente": cliente,
                "cliente_clave": cliente_clave,
                "evento_id": id_evento,
                "evento": evento["nombre"],
                "categoria": evento["categoria"],
                "fecha": datetime.now(),     # fecha y hora en que se obtuvo
            })
            return codigo
        except DuplicateKeyError:
            # Pudo pasar por dos motivos: (a) el cliente ya tenía entrada (doble clic),
            # o (b) otra persona tomó ese mismo número de código justo antes.
            if clienteTieneEntrada(cliente_clave, id_evento):
                raise ValueError("Cliente ya tiene una entrada de este evento.")
            # Si fue (b), el for vuelve a calcular el número y reintenta.

    raise ValueError("No se pudo generar el código de la entrada. Intente de nuevo.")