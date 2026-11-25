# =====================================================================
# app.py
# ---------------------------------------------------------------------
# Este es el archivo PRINCIPAL. Es el que se ejecuta para encender la
# aplicacion web. Su trabajo es:
#   1. Crear la aplicacion Flask (el "servidor web").
#   2. Definir las "rutas": que pagina se muestra en cada direccion
#      (por ejemplo, /carga muestra la pantalla de carga inicial).
#   3. Encender el servidor para poder abrir la app en el navegador.
#
# La pagina principal es la F3 (preventas abiertas). Las otras 4 por
# ahora muestran una pagina "pendiente". Cada dueno reemplaza su ruta:
#   F1 y F2 -> Paz   |   F4 -> Angel   |   F3 y F5 -> Rachel
#
# ENTRADAS:  las peticiones que hace el navegador (cuando alguien
#            entra a una direccion o envia un formulario).
# SALIDAS:   paginas HTML que se muestran en el navegador.
# RESTRICCIONES:
#   - Se ejecuta con:  python app.py
#   - La app queda en http://localhost:5000 (solo en esta compu).
#   - Mongo y Redis deben estar encendidos para que las funcionalidades
#     puedan leer o guardar datos.
#   - Solo se permiten las 5 funcionalidades del enunciado: no agregar
#     rutas ni pantallas extra.
# =====================================================================

# Importamos de Flask:
#   - Flask: la clase que crea la aplicacion web.
#   - render_template: funcion que toma un archivo HTML de la carpeta
#     "templates", le rellena los datos y lo envia al navegador.
#   - request: trae lo que el usuario envio en un formulario (archivos, textos).
#   - redirect y url_for: mandan al navegador a otra pagina.
#   - flash: guarda un mensaje (de exito o error) para mostrarlo en la pagina.
from flask import Flask, render_template, request, redirect, url_for, flash

# Importamos nuestra funcion de db.py que revisa si Mongo y Redis responden.
from db import probar_conexiones

# Importamos la logica de cada funcionalidad (cada una vive en su propio archivo).
from f1_carga import cargar_eventos                            # F1 (Paz)
from f2_abrir_preventa import obtener_catalogo, abrir_preventa as abrir_preventa_redis  # F2 (Paz)
from f4_obtener_entrada import obtener_entrada_bd, obtenerPreventasAbiertas  # F4 (Angel)
# Nota: a la funcion de F2 le ponemos otro nombre ("abrir_preventa_redis")
# para que no se confunda con la ruta abrir_preventa() de mas abajo.


# Creamos la aplicacion web. __name__ le dice a Flask donde esta este
# archivo, para que encuentre las carpetas "templates" y "static".
app = Flask(__name__)

# Clave secreta que Flask necesita para mostrar mensajes temporales
# (por ejemplo "Datos cargados correctamente" o un mensaje de error).
# Para un proyecto del curso basta con cualquier texto.
app.secret_key = "proyecto1-bd-avanzadas"


# ---------------------------------------------------------------------
# RUTAS DE LAS 5 FUNCIONALIDADES
# La PaGINA PRINCIPAL ("/") es la F3: las preventas abiertas, que es
# lo primero que ve el cliente. Las de administracion (F1, F2, F5) se
# abren desde el pie de pagina.
# Las que dicen "pendiente" las reemplaza su dueno con la logica real.
# ---------------------------------------------------------------------

# F3 - Preventas abiertas = PaGINA PRINCIPAL (duena: Rachel)
@app.route("/")                      # "/" es la direccion principal: http://localhost:5000/
def preventas_abiertas():
    """
    QUe HACE (F3):
        Muestra la pagina principal con las preventas vigentes.
    ENTRADAS:
        Ninguna (el usuario solo entra a http://localhost:5000/).
    SALIDAS:
        La pagina preventas.html con una lista "preventas"; cada preventa
        trae: id, nombre, categoria, disponibles y minutos.
    RESTRICCIONES:
        - Las entradas disponibles y el tiempo restante DEBEN leerse de
          Redis (lo exige el enunciado).
        - El nombre y la categoria se leen de MongoDB.
        - PENDIENTE: por ahora devuelve una lista vacia.
    """
    # Por ahora enviamos una lista vacia; Rachel la llenara con los datos de Redis y Mongo.
    preventas = []
    # Mostramos preventas.html y le pasamos la lista de preventas.
    return render_template("preventas.html", preventas=preventas)


# F1 - Carga inicial de datos (duena: Paz)
# methods=["GET", "POST"]:
#   GET  -> cuando la persona ENTRA a la pagina (se muestra el formulario).
#   POST -> cuando la persona ENViA el formulario (se procesa el archivo).
@app.route("/carga", methods=["GET", "POST"])
def carga_inicial():
    """
    QUE HACE (F1):
        Muestra el formulario para escoger el archivo JSON y, al enviarlo,
        carga los eventos en MongoDB.
    ENTRADAS:
        GET:  ninguna.
        POST: el archivo enviado en el campo "archivo" del formulario.
    SALIDAS:
        GET:  la pagina carga.html.
        POST: vuelve a /carga con un mensaje de exito o de error.
    RESTRICCIONES:
        - Solo se aceptan archivos con extension .json.
        - La validacion del contenido la hace f1_carga.py.
    """
    # Si la persona envio el formulario...
    if request.method == "POST":
        # request.files trae los archivos enviados; "archivo" es el nombre del campo en el HTML.
        archivo = request.files.get("archivo")

        # Si no escogio ningún archivo, avisamos.
        if archivo is None or archivo.filename == "":
            flash("Debe seleccionar un archivo JSON.", "error")
        # Si el nombre no termina en .json, avisamos.
        elif not archivo.filename.lower().endswith(".json"):
            flash("El archivo debe tener extension .json.", "error")
        else:
            try:
                # archivo.read() lee todo el contenido del archivo (en bytes)
                # y cargar_eventos() lo valida y lo guarda en MongoDB.
                cantidad = cargar_eventos(archivo.read())
                # Si todo salio bien, mensaje verde de exito.
                flash(f"Carga completada: se guardaron {cantidad} eventos en MongoDB.", "exito")
            except ValueError as error:
                # Si el archivo tenia un problema, mostramos el mensaje en rojo.
                flash(str(error), "error")

        # redirect: volvemos a cargar la pagina con GET. Asi, si la persona
        # refresca (F5), el archivo no se vuelve a enviar por accidente.
        return redirect(url_for("carga_inicial"))

    # Si solo entro a la pagina (GET), mostramos el formulario.
    return render_template("carga.html")


# F2 - Abrir una preventa (duena: Paz)
@app.route("/abrir-preventa", methods=["GET", "POST"])
def abrir_preventa():
    """
    QUe HACE (F2):
        Muestra el catalogo para escoger un evento y el formulario de
        cantidad y duracion; al enviarlo, abre la preventa en Redis.
    ENTRADAS:
        GET:  ninguna.
        POST: los campos del formulario "evento", "cantidad" y "minutos".
    SALIDAS:
        GET:  la pagina abrir_preventa.html con la lista "catalogo".
        POST: vuelve a /abrir-preventa con un mensaje de exito o de error.
    RESTRICCIONES:
        - Las validaciones las hace f2_abrir_preventa.py.
        - Si el catalogo esta vacio, la pagina pide hacer primero la carga (F1).
    """
    # Si la persona envio el formulario...
    if request.method == "POST":
        try:
            # request.form trae los textos del formulario, por el nombre de cada campo.
            datos = abrir_preventa_redis(
                request.form.get("evento"),     # id del evento escogido
                request.form.get("cantidad"),   # cantidad de entradas
                request.form.get("minutos"),    # duracion en minutos
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

        # Volvemos a la misma pagina con GET (igual que en F1).
        return redirect(url_for("abrir_preventa"))

    # Si solo entro a la pagina (GET), traemos el catalogo de Mongo y lo mostramos.
    catalogo = obtener_catalogo()
    return render_template("abrir_preventa.html", catalogo=catalogo)


# F4 - Obtener una entrada (dueno: Angel)
@app.route("/obtenerEntrada")       # direccion: http://localhost:5000/obtener-entrada
def obtenerEntrada():
    """
    QUE HACE (F4):
        Muestra el formulario donde el cliente escribe su nombre y escoge
        una preventa abierta; al enviarlo, le entrega una entrada.
    ENTRADAS:
        GET:  opcionalmente "cliente" en la direccion (para dejar el nombre escrito).
        POST: los campos del formulario "cliente" y "evento".
    SALIDAS:
        GET:  la pagina obtener_entrada.html con la lista "preventas"
              (id, nombre y categoria) y el nombre del "cliente".
        POST: vuelve a /obtenerEntrada con un mensaje de exito (con el
              codigo de la entrada) o de error.
    RESTRICCIONES:
        - Las validaciones (preventa vencida, cliente que ya tiene entrada,
          sin entradas disponibles) las hace f4_obtener_entrada.py.
        - Descuenta una entrada en Redis y guarda la entrada en MongoDB.
    """
    # Si la persona envio el formulario...
    if request.method == "POST":
        cliente = request.form.get("cliente", "")
        try:
            # Intentamos entregar la entrada (descuenta en Redis y guarda en Mongo).
            datos = obtener_entrada_bd(cliente, request.form.get("evento"))
            # Mensaje verde con el codigo y las entradas que le quedan a la preventa.
            flash(
                f"Entrada obtenida: {datos['cliente']} recibio el codigo {datos['codigo']} "
                f"para {datos['nombre']} ({datos['categoria']}). "
                f"A la preventa le quedan {datos['disponibles']} entradas disponibles.",
                "exito",
            )
        except ValueError as error:
            # Preventa vencida, cliente repetido, sin entradas, etc.: mensaje en rojo.
            flash(str(error), "error")

        # Volvemos con GET (igual que en F1 y F2), dejando el nombre escrito.
        return redirect(url_for("obtenerEntrada", cliente=cliente.strip()))

    # Si solo entro a la pagina (GET), traemos las preventas abiertas y la mostramos.
    preventas = obtenerPreventasAbiertas()
    return render_template(
        "obtener_entrada.html",
        preventas=preventas,
        cliente=request.args.get("cliente", ""),
    )

# F5 - Consultar entradas por categoria (duena: Rachel)
@app.route("/consulta")              # direccion: http://localhost:5000/consulta
def consultar_entradas():
    """
    QUe HACE (F5):
        Mostrara, por categoria, el total de entradas y de clientes distintos.
    ENTRADAS:
        Ninguna.
    SALIDAS:
        Por ahora, la pagina "pendiente".
    RESTRICCIONES:
        - Un cliente con varias entradas en la misma categoria cuenta una sola vez.
        - Los resultados se ven en la interfaz, nunca en JSON.
    """
    return render_template("pendiente.html", titulo="Consultar entradas")


# ---------------------------------------------------------------------
# ENCENDER LA APLICACIoN
# Este bloque solo se ejecuta cuando corremos "python app.py".
# ---------------------------------------------------------------------
if __name__ == "__main__":
    # Antes de encender, revisamos en la terminal si Mongo y Redis responden.
    probar_conexiones()
    # Encendemos el servidor web.
    # debug=True hace dos cosas útiles mientras programamos:
    #   - Si cambiamos el codigo y guardamos, la app se reinicia sola.
    #   - Si hay un error, lo muestra con detalle en el navegador.
    app.run(debug=True)
