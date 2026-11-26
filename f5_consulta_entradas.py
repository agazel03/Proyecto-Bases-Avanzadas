# =====================================================================
# f5_consulta_entradas.py
# 5:  CONSULTA DE ENTRADAS  (dueña: Rachel)
# ---------------------------------------------------------------------
# Por cada categoría muestra cuántas entradas se obtuvieron en total y
# cuántos clientes DISTINTOS las obtuvieron.
#
# Aquí solo está la LÓGICA. La parte web está en app.py (ruta "/consulta").
#
# ENTRADAS:  ninguna (lee de MongoDB).
# SALIDAS:   lista de filas {categoria, total_entradas, clientes_distintos}.
# RESTRICCIONES:
#   - Un cliente con varias entradas de una misma categoría cuenta UNA sola
#     vez como cliente, pero todas sus entradas suman al total.
#   - Se listan también las categorías del catálogo que no tienen entradas (con 0).
#   - Usa los campos "categoria" y "cliente_clave" de cada documento de
#     "entradas" (los guarda f4_obtener_entrada.py).
# =====================================================================

from db import coleccion_eventos, coleccion_entradas


def consultar_por_categoria(entradas=coleccion_entradas, eventos=coleccion_eventos):
    """
    QUÉ HACE:
        Calcula, con una agregación de MongoDB, las entradas y los clientes
        distintos de cada categoría.
    ENTRADAS:
        entradas -> colección "entradas" (por defecto la de db.py).
        eventos  -> colección "eventos"  (por defecto la de db.py).
    SALIDAS:
        Lista ordenada por categoría, p. ej.
        [{"categoria": "Deportes", "total_entradas": 3, "clientes_distintos": 2}, ...]
    RESTRICCIONES:
        Ver el encabezado del archivo.
    """
    # Agregación en dos pasos (pipeline):
    pipeline = [
        # Paso 1: agrupar por (categoría, cliente) y contar cuántas entradas tiene
        # cada cliente en esa categoría. Se usa "cliente_clave" (el nombre en minúscula
        # que guarda F4), así "Ana" y "ana" cuentan como la misma persona.
        {"$group": {
            "_id": {"categoria": "$categoria", "cliente": "$cliente_clave"},
            "entradas": {"$sum": 1},
        }},
        # Paso 2: agrupar por categoría. Sumamos las entradas y, como cada grupo
        # del paso 1 es UN cliente, contar los grupos = clientes distintos.
        {"$group": {
            "_id": "$_id.categoria",
            "total_entradas": {"$sum": "$entradas"},
            "clientes_distintos": {"$sum": 1},
        }},
    ]
    resumen = {doc["_id"]: doc for doc in entradas.aggregate(pipeline)}

    # Categorías del catálogo (aunque no tengan entradas) + las que aparezcan en entradas.
    categorias = set(eventos.distinct("categoria")) | set(resumen)

    return [
        {
            "categoria": cat,
            "total_entradas": resumen.get(cat, {}).get("total_entradas", 0),
            "clientes_distintos": resumen.get(cat, {}).get("clientes_distintos", 0),
        }
        for cat in sorted(categorias)
    ]
