# =====================================================================
# db.py
# ---------------------------------------------------------------------
# Este archivo tiene UNA sola responsabilidad: conectarse a las dos
# bases de datos del proyecto (MongoDB y Redis).
# Todos los demás archivos importan las conexiones desde aquí, así
# solo existe un lugar donde se configuran. Si algún día cambia el
# puerto o el nombre de la base de datos, se cambia solo aquí.
#
# ENTRADAS:  ninguna (las direcciones y puertos están escritos abajo).
# SALIDAS:   las variables que usan los demás archivos:
#              - coleccion_eventos   -> colección "eventos" en MongoDB
#              - coleccion_entradas  -> colección "entradas" en MongoDB
#              - cliente_redis       -> conexión a Redis
#              - PREFIJO_PREVENTA    -> "preventa:", inicio de las llaves en Redis
#            y la función probar_conexiones().
# RESTRICCIONES:
#   - MongoDB debe estar encendido en localhost, puerto 27017.
#   - Redis debe estar encendido en localhost, puerto 6379.
#   - (Con Docker: "docker compose up -d" enciende los dos.)
#   - Crear las conexiones NO falla aunque las bases estén apagadas;
#     el error aparece hasta que se intenta usarlas.
# =====================================================================

# Importamos MongoClient, que es el "cliente" (el conector) que nos
# permite hablar con MongoDB desde Python. Viene de la librería pymongo.
from pymongo import MongoClient

# Importamos la librería redis, que nos permite hablar con Redis desde Python.
import redis


# ---------------------------------------------------------------------
# CONFIGURACIÓN DE MONGODB  (base de datos principal)
# Aquí se guardan: el catálogo de eventos y las entradas obtenidas.
# ---------------------------------------------------------------------

# Dirección donde está corriendo MongoDB.
# "localhost" significa "en esta misma computadora" y 27017 es el
# puerto que MongoDB usa por defecto.
MONGO_URI = "mongodb://localhost:27017"

# Nombre de la base de datos dentro de MongoDB.
# Si no existe, MongoDB la crea solita la primera vez que guardemos algo.
MONGO_NOMBRE_BD = "productora_eventos"

# Creamos la conexión con MongoDB usando la dirección de arriba.
# serverSelectionTimeoutMS=3000 significa: "si en 3 segundos (3000
# milisegundos) no lográs conectarte, rendite y avisá con un error",
# para que la app no se quede pegada esperando.
cliente_mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)

# Seleccionamos (o creamos) nuestra base de datos dentro de MongoDB.
bd_mongo = cliente_mongo[MONGO_NOMBRE_BD]

# Colección "eventos": aquí va el catálogo que se carga desde eventos.json.
# (Una colección en MongoDB es como una "tabla" en SQL.)
coleccion_eventos = bd_mongo["eventos"]

# Colección "entradas": aquí se registra cada entrada que obtiene un cliente
# (código, nombre del cliente, evento, categoría y fecha/hora).
coleccion_entradas = bd_mongo["entradas"]


# ---------------------------------------------------------------------
# CONFIGURACIÓN DE REDIS  (preventas abiertas)
# Aquí se guardan las preventas abiertas, con sus entradas disponibles
# y su tiempo de vida (TTL). Cuando el TTL llega a cero, Redis borra
# la preventa automáticamente: así "vence".
# ---------------------------------------------------------------------

# Dirección donde corre Redis: en esta misma computadora.
REDIS_HOST = "localhost"

# Puerto que Redis usa por defecto.
REDIS_PUERTO = 6379

# Creamos la conexión con Redis.
# decode_responses=True hace que Redis nos devuelva texto normal
# ("5") en lugar de bytes (b"5"), que es más fácil de usar.
cliente_redis = redis.Redis(
    host=REDIS_HOST,          # dónde está Redis
    port=REDIS_PUERTO,        # en qué puerto escucha
    decode_responses=True,    # devolver texto en vez de bytes
    socket_connect_timeout=3  # si en 3 segundos no conecta, avisar con error
)

# Prefijo de las llaves de preventas en Redis.
# Cada preventa abierta se guarda como:   preventa:<id del evento>
# Ejemplo:  preventa:E001  ->  "5"   (5 entradas disponibles, con TTL)
# TODOS (F2, F3 y F4) deben usar este mismo prefijo para encontrar las preventas.
PREFIJO_PREVENTA = "preventa:"


# ---------------------------------------------------------------------
# FUNCIÓN DE PRUEBA DE CONEXIÓN
# Se ejecuta al arrancar la app (desde app.py) y muestra en la
# terminal si cada base de datos respondió. No es una funcionalidad
# de la aplicación: solo nos ayuda a nosotros a saber si Mongo y
# Redis están encendidos antes de empezar.
# ---------------------------------------------------------------------
def probar_conexiones():
    """
    QUÉ HACE:
        Revisa si MongoDB y Redis responden y lo muestra en la terminal.
    ENTRADAS:
        Ninguna.
    SALIDAS:
        No devuelve nada (None). Solo imprime en la terminal:
          "✔ ... conectado correctamente"  si la base respondió, o
          "✘ No se pudo conectar a ...: <error>"  si no respondió.
    RESTRICCIONES:
        - Espera como máximo 3 segundos por cada base de datos.
        - Si una base falla, NO detiene la app: solo avisa.
    """
    # --- Prueba de MongoDB ---
    try:
        # "ping" es un comando que le pregunta a MongoDB "¿estás vivo?".
        # Si responde, la conexión funciona.
        cliente_mongo.admin.command("ping")
        # Si llegamos a esta línea, Mongo respondió bien.
        print("✔ MongoDB conectado correctamente")
    except Exception as error:
        # Si Mongo no respondió, mostramos el problema en la terminal.
        print("✘ No se pudo conectar a MongoDB:", error)

    # --- Prueba de Redis ---
    try:
        # ping() le pregunta a Redis "¿estás vivo?". Devuelve True si responde.
        cliente_redis.ping()
        # Si llegamos aquí, Redis respondió bien.
        print("✔ Redis conectado correctamente")
    except Exception as error:
        # Si Redis no respondió, mostramos el problema en la terminal.
        print("✘ No se pudo conectar a Redis:", error)
