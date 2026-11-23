# =====================================================================
# f1_carga.py  —  F1: CARGA INICIAL DE LOS DATOS        (dueña: Paz)
# ---------------------------------------------------------------------
# Lee el archivo JSON que el usuario selecciona en la página y guarda
# sus eventos en la colección "eventos" de MongoDB.
#
# Aquí solo está la LÓGICA (leer, validar y guardar). La parte web
# (el formulario y los mensajes) está en app.py, en la ruta /carga.
#
# ENTRADAS:  el contenido del archivo JSON (en bytes) que subió el usuario.
# SALIDAS:   la cantidad de eventos que se guardaron en MongoDB.
# RESTRICCIONES:
#   - El archivo debe ser un JSON válido con una LISTA de eventos.
#   - Cada evento debe tener como mínimo: id, nombre, categoria y precio.
#   - Los demás atributos (artista, estadio, etc.) son libres y se
#     guardan tal como vienen, porque cambian según la categoría.
#   - No se permiten dos eventos con el mismo "id" en MongoDB.
#   - Debe funcionar con cualquier archivo de esa misma estructura,
#     con más o menos eventos (así lo pide el enunciado).
# =====================================================================

# json es la librería de Python que convierte texto JSON en listas y
# diccionarios de Python (y al revés).
import json

# Importamos la colección "eventos" desde db.py (ahí está la conexión).
from db import coleccion_eventos

# BulkWriteError es el error que da MongoDB cuando, al guardar varios
# documentos de una vez, alguno falla (por ejemplo, un id repetido).
from pymongo.errors import BulkWriteError


# Campos que TODO evento debe traer. Si falta alguno, el archivo se rechaza.
CAMPOS_OBLIGATORIOS = ["id", "nombre", "categoria", "precio"]


def validar_eventos(contenido):
    """
    QUÉ HACE:
        Convierte el texto del archivo en una lista de eventos y revisa
        que tenga la estructura correcta.
    ENTRADAS:
        contenido -> el archivo leído, en bytes.
    SALIDAS:
        La lista de eventos (cada evento es un diccionario de Python).
    RESTRICCIONES:
        Lanza ValueError con un mensaje claro si:
          - el archivo no es un JSON válido,
          - el JSON no es una lista o está vacía,
          - algún evento no es un objeto o le falta un campo obligatorio,
          - el precio no es un número,
          - hay ids repetidos dentro del mismo archivo.
    """
    try:
        # .decode("utf-8") convierte los bytes en texto (respetando tildes y ñ).
        # json.loads() convierte ese texto JSON en datos de Python.
        eventos = json.loads(contenido.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        # Si el archivo no se puede leer como JSON, avisamos con un mensaje claro.
        raise ValueError("El archivo no es un JSON válido.")

    # isinstance(x, list) pregunta "¿x es una lista?". El archivo debe ser una lista [ ... ].
    if not isinstance(eventos, list) or len(eventos) == 0:
        raise ValueError("El archivo debe contener una lista con al menos un evento.")

    # Aquí iremos guardando los ids que ya vimos, para detectar repetidos.
    ids_vistos = set()   # un "set" es una colección sin elementos repetidos

    # enumerate() recorre la lista y además nos da el número de posición (empezando en 1).
    for posicion, evento in enumerate(eventos, start=1):

        # Cada evento debe ser un objeto { ... } (un diccionario en Python).
        if not isinstance(evento, dict):
            raise ValueError(f"El elemento #{posicion} no es un evento válido.")

        # Revisamos que el evento tenga cada uno de los campos obligatorios.
        for campo in CAMPOS_OBLIGATORIOS:
            if campo not in evento:
                raise ValueError(f"Al evento #{posicion} le falta el campo '{campo}'.")

        # El precio debe ser un número (int = entero, float = con decimales).
        # bool se excluye porque en Python True/False también cuentan como números.
        precio = evento["precio"]
        if isinstance(precio, bool) or not isinstance(precio, (int, float)):
            raise ValueError(f"El precio del evento '{evento['id']}' no es un número.")

        # Si el id ya apareció antes en este mismo archivo, es un error.
        if evento["id"] in ids_vistos:
            raise ValueError(f"El id '{evento['id']}' está repetido en el archivo.")
        # Si no estaba, lo agregamos a los ids vistos.
        ids_vistos.add(evento["id"])

    # Si pasó todas las revisiones, devolvemos la lista de eventos.
    return eventos


def cargar_eventos(contenido):
    """
    QUÉ HACE:
        Valida el archivo y guarda sus eventos en MongoDB.
    ENTRADAS:
        contenido -> el archivo leído, en bytes.
    SALIDAS:
        Un número entero: cuántos eventos se guardaron.
    RESTRICCIONES:
        - Lanza ValueError si el archivo no es válido (ver validar_eventos).
        - Lanza ValueError si algún id ya existe en MongoDB; en ese caso
          los eventos nuevos sí se guardan y los repetidos se omiten.
        - Mongo debe estar encendido.
    """
    # Paso 1: revisar el archivo (si algo está mal, aquí se detiene con ValueError).
    eventos = validar_eventos(contenido)

    # Paso 2: crear un ÍNDICE ÚNICO sobre el campo "id".
    # Así MongoDB mismo impide guardar dos eventos con el mismo id.
    # Si el índice ya existe, esta línea no hace nada.
    coleccion_eventos.create_index("id", unique=True)

    try:
        # Paso 3: guardar todos los eventos de una sola vez.
        # ordered=False: si uno falla (id repetido), igual intenta guardar los demás.
        resultado = coleccion_eventos.insert_many(eventos, ordered=False)
        # inserted_ids es la lista de documentos guardados; len() cuenta cuántos son.
        return len(resultado.inserted_ids)

    except BulkWriteError as error:
        # Si algunos ids ya existían en Mongo, llegamos aquí.
        # nInserted dice cuántos SÍ se guardaron.
        guardados = error.details["nInserted"]
        # writeErrors es la lista de los que fallaron.
        repetidos = len(error.details["writeErrors"])
        raise ValueError(
            f"Se guardaron {guardados} eventos. Se omitieron {repetidos} "
            f"porque su id ya existía en la base de datos."
        )
