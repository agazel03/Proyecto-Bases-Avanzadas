# =====================================================================
# f2_abrir_preventa.py  —  F2: ABRIR UNA PREVENTA        (dueña: Paz)
# ---------------------------------------------------------------------
# El administrador escoge un evento del catálogo (MongoDB) e indica
# cuántas entradas habrá y cuántos minutos durará la preventa.
# La preventa se guarda en REDIS con un tiempo de vida (TTL): cuando
# el tiempo se acaba, Redis la borra sola y la preventa "vence".
#
# Aquí solo está la LÓGICA. La parte web está en app.py (/abrir-preventa).
#
# CÓMO QUEDA EN REDIS:
#   llave:  preventa:<id del evento>     ejemplo: preventa:E001
#   valor:  cantidad de entradas         ejemplo: "5"
#   TTL:    minutos x 60 segundos        ejemplo: 30 min -> 1800 s
#
# ENTRADAS:  id del evento, cantidad de entradas y duración en minutos.
# SALIDAS:   el evento al que se le abrió la preventa.
# RESTRICCIONES:
#   - El evento debe existir en el catálogo de MongoDB.
#   - Cantidad y minutos deben ser números enteros mayores que 0.
#   - No se puede abrir una preventa si el evento ya tiene una abierta.
#   - El vencimiento lo maneja Redis con TTL (lo exige el enunciado).
# =====================================================================

# Importamos la colección de eventos (Mongo), la conexión a Redis y el
# prefijo de las llaves de preventas, todo desde db.py.
from db import coleccion_eventos, cliente_redis, PREFIJO_PREVENTA


def obtener_catalogo():
    """
    QUÉ HACE:
        Trae todos los eventos del catálogo para mostrarlos en la lista
        donde el administrador escoge el evento.
    ENTRADAS:
        Ninguna.
    SALIDAS:
        Una lista de diccionarios con id, nombre, categoria y precio,
        ordenada por categoría y luego por nombre.
    RESTRICCIONES:
        - Si el catálogo está vacío (no se ha hecho la carga), devuelve [].
        - Mongo debe estar encendido.
    """
    # find({}, {...}) busca TODOS los eventos ({} = sin filtro) y solo trae
    # los campos marcados con 1. "_id": 0 quita el id interno de Mongo.
    cursor = coleccion_eventos.find(
        {},
        {"_id": 0, "id": 1, "nombre": 1, "categoria": 1, "precio": 1}
    )
    # sort() ordena: primero por categoría y después por nombre (1 = A→Z).
    cursor = cursor.sort([("categoria", 1), ("nombre", 1)])
    # list() convierte el resultado en una lista normal de Python.
    return list(cursor)


def convertir_entero_positivo(texto, nombre_campo):
    """
    QUÉ HACE:
        Convierte lo que escribió el usuario en un número entero mayor que 0.
    ENTRADAS:
        texto        -> lo que llegó del formulario (siempre llega como texto).
        nombre_campo -> el nombre del campo, para el mensaje de error.
    SALIDAS:
        El número entero.
    RESTRICCIONES:
        Lanza ValueError si el texto está vacío, no es un número entero
        o es menor o igual a 0.
    """
    try:
        # int() convierte el texto "5" en el número 5. Si es "abc" o "2.5", falla.
        numero = int(texto)
    except (TypeError, ValueError):
        raise ValueError(f"La {nombre_campo} debe ser un número entero.")

    # El número debe ser mayor que cero.
    if numero <= 0:
        raise ValueError(f"La {nombre_campo} debe ser mayor que 0.")

    # Si todo está bien, devolvemos el número.
    return numero


def abrir_preventa(id_evento, texto_cantidad, texto_minutos):
    """
    QUÉ HACE:
        Abre la preventa de un evento: la guarda en Redis con sus
        entradas disponibles y su tiempo de vida (TTL).
    ENTRADAS:
        id_evento      -> el id del evento escogido (ej. "E001").
        texto_cantidad -> la cantidad de entradas, como texto del formulario.
        texto_minutos  -> la duración en minutos, como texto del formulario.
    SALIDAS:
        Un diccionario con el evento (nombre y categoría), la cantidad y
        los minutos, para armar el mensaje de éxito.
    RESTRICCIONES:
        Lanza ValueError con un mensaje claro si:
          - no se escogió ningún evento o el evento no existe en Mongo,
          - la cantidad o los minutos no son enteros mayores que 0,
          - el evento ya tiene una preventa abierta en Redis.
    """
    # Paso 1: revisar que se haya escogido un evento.
    if not id_evento:
        raise ValueError("Debe seleccionar un evento.")

    # Paso 2: buscar el evento en el catálogo de MongoDB.
    # find_one() devuelve el primer evento con ese id, o None si no existe.
    evento = coleccion_eventos.find_one({"id": id_evento}, {"_id": 0})
    if evento is None:
        raise ValueError("El evento seleccionado no existe en el catálogo.")

    # Paso 3: convertir y validar la cantidad y los minutos.
    cantidad = convertir_entero_positivo(texto_cantidad, "cantidad de entradas")
    minutos = convertir_entero_positivo(texto_minutos, "duración en minutos")

    # Paso 4: armar la llave de Redis, por ejemplo "preventa:E001".
    llave = PREFIJO_PREVENTA + id_evento

    # Paso 5: guardar la preventa en Redis.
    #   set(llave, valor, ...) guarda el valor en esa llave.
    #   ex=minutos*60 -> TTL en SEGUNDOS: Redis la borrará sola al terminar el tiempo.
    #   nx=True       -> "solo si NO existe": si ya hay una preventa abierta
    #                    para ese evento, Redis NO la sobrescribe y devuelve None.
    guardado = cliente_redis.set(llave, cantidad, ex=minutos * 60, nx=True)

    # Si Redis devolvió None, es porque la llave ya existía: hay una preventa abierta.
    if not guardado:
        raise ValueError(f"El evento '{evento['nombre']}' ya tiene una preventa abierta.")

    # Paso 6: devolvemos los datos para el mensaje de éxito.
    return {
        "nombre": evento["nombre"],        # nombre del evento
        "categoria": evento["categoria"],  # categoría del evento
        "cantidad": cantidad,              # entradas disponibles
        "minutos": minutos,                # duración de la preventa
    }
