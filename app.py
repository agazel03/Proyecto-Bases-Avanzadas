# =====================================================================
# app.py
# ---------------------------------------------------------------------
# Este es el archivo PRINCIPAL. Es el que se ejecuta para encender la
# aplicación web. Su trabajo es:
#   1. Crear la aplicación Flask (el "servidor web").
#   2. Definir las "rutas": qué página se muestra en cada dirección
#      (por ejemplo, /carga muestra la pantalla de carga inicial).
#   3. Encender el servidor para poder abrir la app en el navegador.
#
# La página principal es la F3 (preventas abiertas). Las otras 4 por
# ahora muestran una página "pendiente". Cada dueño reemplaza su ruta:
#   F1 y F2 -> Paz   |   F4 -> Angel   |   F3 y F5 -> Rachel
#
# ENTRADAS:  las peticiones que hace el navegador (cuando alguien
#            entra a una dirección o envía un formulario).
# SALIDAS:   páginas HTML que se muestran en el navegador.
# RESTRICCIONES:
#   - Se ejecuta con:  python app.py
#   - La app queda en http://localhost:5000 (solo en esta compu).
#   - Mongo y Redis deben estar encendidos para que las funcionalidades
#     puedan leer o guardar datos.
#   - Solo se permiten las 5 funcionalidades del enunciado: no agregar
#     rutas ni pantallas extra.
# =====================================================================

# Importamos de Flask:
#   - Flask: la clase que crea la aplicación web.
#   - render_template: función que toma un archivo HTML de la carpeta
#     "templates", le rellena los datos y lo envía al navegador.
#   - request: trae lo que el usuario envió en un formulario (archivos, textos).
#   - redirect y url_for: mandan al navegador a otra página.
#   - flash: guarda un mensaje (de éxito o error) para mostrarlo en la página.
from flask import Flask, render_template, request, redirect, url_for, flash

# Importamos nuestra función de db.py que revisa si Mongo y Redis responden.
from db import probar_conexiones

# Importamos la lógica de cada funcionalidad (cada una vive en su propio archivo).
from f1_carga import cargar_eventos                            # F1 (Paz)
from f2_abrir_preventa import obtener_catalogo, abrir_preventa as abrir_preventa_redis  # F2 (Paz)
# Nota: a la función de F2 le ponemos otro nombre ("abrir_preventa_redis")
# para que no se confunda con la ruta abrir_preventa() de más abajo.


# Creamos la aplicación web. __name__ le dice a Flask dónde está este
# archivo, para que encuentre las carpetas "templates" y "static".
app = Flask(__name__)

# Clave secreta que Flask necesita para mostrar mensajes temporales
# (por ejemplo "Datos cargados correctamente" o un mensaje de error).
# Para un proyecto del curso basta con cualquier texto.
app.secret_key = "proyecto1-bd-avanzadas"


# ---------------------------------------------------------------------
# RUTAS DE LAS 5 FUNCIONALIDADES
# La PÁGINA PRINCIPAL ("/") es la F3: las preventas abiertas, que es
# lo primero que ve el cliente. Las de administración (F1, F2, F5) se
# abren desde el pie de página.
# Las que dicen "pendiente" las reemplaza su dueño con la lógica real.
# ---------------------------------------------------------------------

# F3 - Preventas abiertas = PÁGINA PRINCIPAL (dueña: Rachel)
@app.route("/")                      # "/" es la dirección principal: http://localhost:5000/
def preventas_abiertas():
    """
    QUÉ HACE (F3):
        Muestra la página principal con las preventas vigentes.
    ENTRADAS:
        Ninguna (el usuario solo entra a http://localhost:5000/).
    SALIDAS:
        La página preventas.html con una lista "preventas"; cada preventa
        trae: id, nombre, categoria, disponibles y minutos.
    RESTRICCIONES:
        - Las entradas disponibles y el tiempo restante DEBEN leerse de
          Redis (lo exige el enunciado).
        - El nombre y la categoría se leen de MongoDB.
        - PENDIENTE: por ahora devuelve una lista vacía.
    """
    # Por ahora enviamos una lista vacía; Rachel la llenará con los datos de Redis y Mongo.
    preventas = []
    # Mostramos preventas.html y le pasamos la lista de preventas.
    return render_template("preventas.html", preventas=preventas)


# F1 - Carga inicial de datos (dueña: Paz)
# methods=["GET", "POST"]:
#   GET  -> cuando la persona ENTRA a la página (se muestra el formulario).
#   POST -> cuando la persona ENVÍA el formulario (se procesa el archivo).
@app.route("/carga", methods=["GET", "POST"])
def carga_inicial():
    """
    QUÉ HACE (F1):
        Muestra el formulario para escoger el archivo JSON y, al enviarlo,
        carga los eventos en MongoDB.
    ENTRADAS:
        GET:  ninguna.
        POST: el archivo enviado en el campo "archivo" del formulario.
    SALIDAS:
        GET:  la página carga.html.
        POST: vuelve a /carga con un mensaje de éxito o de error.
    RESTRICCIONES:
        - Solo se aceptan archivos con extensión .json.
        - La validación del contenido la hace f1_carga.py.
    """
    # Si la persona envió el formulario...
    if request.method == "POST":
        # request.files trae los archivos enviados; "archivo" es el nombre del campo en el HTML.
        archivo = request.files.get("archivo")

        # Si no escogió ningún archivo, avisamos.
        if archivo is None or archivo.filename == "":
            flash("Debe seleccionar un archivo JSON.", "error")
        # Si el nombre no termina en .json, avisamos.
        elif not archivo.filename.lower().endswith(".json"):
            flash("El archivo debe tener extensión .json.", "error")
        else:
            try:
                # archivo.read() lee todo el contenido del archivo (en bytes)
                # y cargar_eventos() lo valida y lo guarda en MongoDB.
                cantidad = cargar_eventos(archivo.read())
                # Si todo salió bien, mensaje verde de éxito.
                flash(f"Carga completada: se guardaron {cantidad} eventos en MongoDB.", "exito")
            except ValueError as error:
                # Si el archivo tenía un problema, mostramos el mensaje en rojo.
                flash(str(error), "error")

        # redirect: volvemos a cargar la página con GET. Así, si la persona
        # refresca (F5), el archivo no se vuelve a enviar por accidente.
        return redirect(url_for("carga_inicial"))

    # Si solo entró a la página (GET), mostramos el formulario.
    return render_template("carga.html")


# F2 - Abrir una preventa (dueña: Paz)
@app.route("/abrir-preventa", methods=["GET", "POST"])
def abrir_preventa():
    """
    QUÉ HACE (F2):
        Muestra el catálogo para escoger un evento y el formulario de
        cantidad y duración; al enviarlo, abre la preventa en Redis.
    ENTRADAS:
        GET:  ninguna.
        POST: los campos del formulario "evento", "cantidad" y "minutos".
    SALIDAS:
        GET:  la página abrir_preventa.html con la lista "catalogo".
        POST: vuelve a /abrir-preventa con un mensaje de éxito o de error.
    RESTRICCIONES:
        - Las validaciones las hace f2_abrir_preventa.py.
        - Si el catálogo está vacío, la página pide hacer primero la carga (F1).
    """
    # Si la persona envió el formulario...
    if request.method == "POST":
        try:
            # request.form trae los textos del formulario, por el nombre de cada campo.
            datos = abrir_preventa_redis(
                request.form.get("evento"),     # id del evento escogido
                request.form.get("cantidad"),   # cantidad de entradas
                request.form.get("minutos"),    # duración en minutos
            )
            # Mensaje verde con el resumen de la preventa abierta.
            flash(
                f"Preventa abierta: {datos['nombre']} ({datos['categoria']}) con "
                f"{datos['cantidad']} entradas durante {datos['minutos']} minutos.",
                "exito",
            )
        except ValueError as error:
            # Si algo no cumple las reglas, mostramos el error en rojo.
            flash(str(error), "error")

        # Volvemos a la misma página con GET (igual que en F1).
        return redirect(url_for("abrir_preventa"))

    # Si solo entró a la página (GET), traemos el catálogo de Mongo y lo mostramos.
    catalogo = obtener_catalogo()
    return render_template("abrir_preventa.html", catalogo=catalogo)


# F4 - Obtener una entrada (dueño: Angel)
@app.route("/obtener-entrada")       # dirección: http://localhost:5000/obtener-entrada
def obtener_entrada():
    """
    QUÉ HACE (F4):
        Permitirá que un cliente obtenga una entrada de una preventa.
    ENTRADAS:
        (Pendiente) nombre del cliente y evento escogido.
    SALIDAS:
        Por ahora, la página "pendiente".
    RESTRICCIONES:
        - Descuenta una entrada en Redis y guarda la entrada en MongoDB
          (código, cliente, evento, categoría, fecha y hora).
        - Error claro si: la preventa venció, no quedan entradas o el
          cliente ya tiene entrada de ese evento.
    """
    return render_template("pendiente.html", titulo="Obtener una entrada")


# F5 - Consultar entradas por categoría (dueña: Rachel)
@app.route("/consulta")              # dirección: http://localhost:5000/consulta
def consultar_entradas():
    """
    QUÉ HACE (F5):
        Mostrará, por categoría, el total de entradas y de clientes distintos.
    ENTRADAS:
        Ninguna.
    SALIDAS:
        Por ahora, la página "pendiente".
    RESTRICCIONES:
        - Un cliente con varias entradas en la misma categoría cuenta una sola vez.
        - Los resultados se ven en la interfaz, nunca en JSON.
    """
    return render_template("pendiente.html", titulo="Consultar entradas")


# ---------------------------------------------------------------------
# ENCENDER LA APLICACIÓN
# Este bloque solo se ejecuta cuando corremos "python app.py".
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Antes de encender, revisamos en la terminal si Mongo y Redis responden.
    probar_conexiones()
    # Encendemos el servidor web.
    # debug=True hace dos cosas útiles mientras programamos:
    #   - Si cambiamos el código y guardamos, la app se reinicia sola.
    #   - Si hay un error, lo muestra con detalle en el navegador.
    app.run(debug=True)
