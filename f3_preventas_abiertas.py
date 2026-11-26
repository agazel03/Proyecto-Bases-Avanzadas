# =====================================================================
# f3_preventas_abiertas.py  —  
# F3:  PREVENTAS ABIERTAS  (dueña: Rachel)
# ---------------------------------------------------------------------
# Arma la lista de preventas vigentes para la página principal ("/").
#
# De dónde sale cada dato (lo exige el enunciado):
#   - Entradas disponibles y tiempo restante -> REDIS
#       llave  preventa:<id del evento>   valor = entradas disponibles
#       TTL de la llave                   = segundos que le quedan
#   - Nombre y categoría del evento          -> MONGODB (colección "eventos")
#
# Aquí solo está la LÓGICA. La parte web está en app.py (ruta "/").
#
# ENTRADAS:  ninguna (lee directamente de Redis y Mongo).
# SALIDAS:   lista de preventas vigentes (ver obtener_preventas_abiertas).
# RESTRICCIONES:
#   - Una preventa es "vigente" si su llave existe en Redis (TTL > 0)
#     y todavía tiene al menos 1 entrada disponible.
#   - Redis y Mongo deben estar encendidos.
# =====================================================================

import math

# Conexiones y prefijo compartidos, definidos en db.py.
from db import coleccion_eventos, cliente_redis, PREFIJO_PREVENTA


def formato_tiempo(segundos):
    """
    QUÉ HACE:
        Convierte segundos en un texto fácil de leer.
    ENTRADAS:
        segundos -> entero (ej. 750).
    SALIDAS:
        Texto: 750 -> "12 min 30 s",  720 -> "12 minutos",  45 -> "45 segundos".
    RESTRICCIONES:
        Ninguna.
    """
    if segundos >= 60:
        # divmod devuelve (cociente, resto): minutos completos y segundos sobrantes.
        minutos, resto = divmod(segundos, 60)
        return f"{minutos} min {resto} s" if resto else f"{minutos} minutos"
    return f"{segundos} segundos"


def obtener_preventas_abiertas(redis_cli=cliente_redis, eventos=coleccion_eventos):
    """
    QUÉ HACE:
        Lee de Redis todas las preventas vigentes y les agrega el nombre y
        la categoría del evento desde MongoDB.
    ENTRADAS:
        redis_cli -> conexión a Redis (por defecto la de db.py).
        eventos   -> colección "eventos" de Mongo (por defecto la de db.py).
        (Los parámetros existen para poder probar con bases simuladas.)
    SALIDAS:
        Lista de diccionarios, ordenada de la que vence primero a la última:
          id, nombre, categoria, disponibles, segundos_restantes,
          minutos (segundos redondeados hacia arriba), tiempo_texto.
    RESTRICCIONES:
        - Se omiten las preventas vencidas, agotadas (0 entradas) o sin TTL.
        - Si el evento ya no existe en Mongo, se muestra con su id y
          categoría "Sin categoría" (no se rompe la página).
    """
    # Paso 1: buscar las llaves "preventa:*" con SCAN.
    # (KEYS bloquearía Redis si hubiera muchas llaves; SCAN las recorre por partes.)
    llaves = list(redis_cli.scan_iter(match=PREFIJO_PREVENTA + "*", count=100))
    if not llaves:
        return []

    # Paso 2: pedir el valor (entradas) y el TTL de TODAS las llaves en un solo
    # viaje a Redis (pipeline). Así valor y tiempo son del mismo instante.
    pipe = redis_cli.pipeline()
    for llave in llaves:
        pipe.get(llave)   # entradas disponibles
        pipe.ttl(llave)   # segundos restantes (-2 = ya no existe, -1 = sin TTL)
    respuestas = pipe.execute()

    # Paso 3: quedarnos solo con las preventas realmente vigentes.
    vigentes = []
    for i, llave in enumerate(llaves):
        valor, ttl = respuestas[2 * i], respuestas[2 * i + 1]
        if valor is None or ttl <= 0:     # venció justo ahora, o no tiene TTL
            continue
        disponibles = int(valor)
        if disponibles <= 0:              # agotada: ya no está disponible
            continue
        # Quitamos el prefijo para quedarnos con el id del evento ("E001").
        vigentes.append((llave[len(PREFIJO_PREVENTA):], disponibles, ttl))

    if not vigentes:
        return []

    # Paso 4: traer de Mongo nombre y categoría de todos esos eventos con UNA sola consulta.
    ids = [id_evento for id_evento, _, _ in vigentes]
    datos = {
        e["id"]: e
        for e in eventos.find({"id": {"$in": ids}}, {"_id": 0, "id": 1, "nombre": 1, "categoria": 1})
    }

    # Paso 5: armar la lista final.
    preventas = []
    for id_evento, disponibles, ttl in vigentes:
        evento = datos.get(id_evento, {})
        preventas.append({
            "id": id_evento,
            "nombre": evento.get("nombre", id_evento),
            "categoria": evento.get("categoria", "Sin categoría"),
            "disponibles": disponibles,
            "segundos_restantes": ttl,
            "minutos": math.ceil(ttl / 60),
            "tiempo_texto": formato_tiempo(ttl),
        })

    # Primero las que vencen antes.
    preventas.sort(key=lambda p: p["segundos_restantes"])
    return preventas
