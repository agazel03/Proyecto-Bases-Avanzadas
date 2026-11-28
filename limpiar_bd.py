# =====================================================================
# limpiar_bd.py
# ---------------------------------------------------------------------
# Deja MongoDB y Redis vacíos, para que el proyecto empiece siempre
# desde cero.
#
# Se usa de DOS formas:
#   1. AUTOMÁTICA: app.py llama a limpiar_bases() al INICIAR el
#      proyecto ("python app.py") y al CERRARLO (Ctrl+C en la terminal).
#   2. MANUAL: desde la terminal con "python limpiar_bd.py" (pide
#      confirmación antes de borrar).
#
# IMPORTANTE: no tiene botón en la app, porque el enunciado dice que
# NO se permiten funcionalidades diferentes a las solicitadas.
#
# ENTRADAS:  ninguna (modo manual: la respuesta "s" o "n" en la terminal).
# SALIDAS:   mensajes en la terminal indicando qué se borró.
# RESTRICCIONES:
#   - Mongo y Redis deben estar encendidos.
#   - Lo borrado NO se puede recuperar.
# =====================================================================

# Importamos las conexiones que ya están configuradas en db.py
from db import coleccion_eventos, coleccion_entradas, cliente_redis


def limpiar_bases():
    """
    QUÉ HACE:
        Borra todos los eventos y entradas de MongoDB y todas las
        preventas de Redis.
    ENTRADAS:
        Ninguna.
    SALIDAS:
        No devuelve nada. Imprime en la terminal cuánto se borró.
    RESTRICCIONES:
        - No pide confirmación: quien la llama decide cuándo usarla.
        - Si Mongo o Redis están apagados, avisa en la terminal y NO
          detiene la app (así se ve el ✘ de probar_conexiones()).
    """
    try:
        # --- Limpiar MongoDB ---
        # delete_many({}) borra todos los documentos de la colección.
        # El {} vacío significa "sin filtro", o sea: todos.
        # .deleted_count nos dice cuántos documentos se borraron.
        borrados_eventos = coleccion_eventos.delete_many({}).deleted_count
        borrados_entradas = coleccion_entradas.delete_many({}).deleted_count
        # Mostramos cuántos documentos se borraron de cada colección.
        print(f"🧹 Mongo: {borrados_eventos} eventos y {borrados_entradas} entradas borrados")
    except Exception as error:
        # Si Mongo no responde, avisamos y seguimos.
        print("✘ No se pudo limpiar MongoDB:", error)

    try:
        # --- Limpiar Redis ---
        # flushdb() borra todas las llaves de Redis (las preventas abiertas).
        cliente_redis.flushdb()
        # Confirmamos en la terminal.
        print("🧹 Redis: todas las preventas borradas")
    except Exception as error:
        # Si Redis no responde, avisamos y seguimos.
        print("✘ No se pudo limpiar Redis:", error)


# ---------------------------------------------------------------------
# MODO MANUAL: este bloque solo se ejecuta con "python limpiar_bd.py".
# Cuando app.py importa este archivo, este bloque NO se ejecuta.
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Pedimos confirmación para no borrar todo por accidente.
    respuesta = input("¿Seguro que querés borrar TODOS los datos de Mongo y Redis? (s/n): ")
    # .strip() quita espacios sobrantes y .lower() pasa a minúscula.
    if respuesta.strip().lower() == "s":
        limpiar_bases()
    else:
        # Si la persona no escribió "s", no se borra nada.
        print("Cancelado: no se borró nada.")
