# =====================================================================
# limpiar_bd.py
# ---------------------------------------------------------------------
# HERRAMIENTA DE APOYO PARA PRUEBAS (NO es parte de la aplicación web).
#
# Deja MongoDB y Redis vacíos, para empezar las pruebas desde cero
# (por ejemplo, antes de sacar la captura de "colección vacía" que
# pide la documentación, o antes de la revisión con la profe).
#
# Se ejecuta desde la terminal con:   python limpiar_bd.py
#
# IMPORTANTE: no se agrega como botón en la app, porque el enunciado
# dice que NO se permiten funcionalidades diferentes a las solicitadas.
#
# ENTRADAS:  la respuesta que se escribe en la terminal ("s" o "n").
# SALIDAS:   mensajes en la terminal indicando qué se borró.
# RESTRICCIONES:
#   - Mongo y Redis deben estar encendidos.
#   - Solo borra si la respuesta es "s"; cualquier otra cosa cancela.
#   - Lo borrado NO se puede recuperar.
# =====================================================================

# Importamos las conexiones que ya están configuradas en db.py
from db import coleccion_eventos, coleccion_entradas, cliente_redis


# Pedimos confirmación para no borrar todo por accidente.
# input() muestra el texto en la terminal y espera que la persona escriba algo.
respuesta = input("¿Seguro que querés borrar TODOS los datos de Mongo y Redis? (s/n): ")

# .strip() quita espacios sobrantes y .lower() pasa a minúscula,
# así "S", " s " o "s" se toman igual.
if respuesta.strip().lower() == "s":

    # --- Limpiar MongoDB ---
    # delete_many({}) borra todos los documentos de la colección.
    # El {} vacío significa "sin filtro", o sea: todos.
    # .deleted_count nos dice cuántos documentos se borraron.
    borrados_eventos = coleccion_eventos.delete_many({}).deleted_count
    borrados_entradas = coleccion_entradas.delete_many({}).deleted_count

    # Mostramos cuántos documentos se borraron de cada colección.
    print(f"✔ Mongo: {borrados_eventos} eventos y {borrados_entradas} entradas borrados")

    # --- Limpiar Redis ---
    # flushdb() borra todas las llaves de la base de datos de Redis que
    # usa este proyecto (las preventas abiertas y cualquier contador).
    cliente_redis.flushdb()

    # Confirmamos en la terminal.
    print("✔ Redis: todas las preventas borradas")

else:
    # Si la persona no escribió "s", no se borra nada.
    print("Cancelado: no se borró nada.")
