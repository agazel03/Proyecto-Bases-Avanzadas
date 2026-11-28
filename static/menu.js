/* =====================================================================
   menu.js  —  COMPORTAMIENTO DEL MENÚ Y DE LA CUENTA REGRESIVA
   ---------------------------------------------------------------------
   Hace 4 cosas pequeñas (si este archivo no carga, la app funciona
   igual, solo se pierden estos detalles):
     1. Abre y cierra el menú en celulares (botón "hamburguesa").
     2. Cierra las listas desplegables al hacer clic afuera o con Escape,
        y deja solo una abierta a la vez.
     3. Hace bajar el tiempo restante de cada preventa segundo a segundo,
        sin recargar la página. El punto de partida viene de Redis
        (atributo data-segundos), así que el dato real sigue siendo el de Redis.
     4. Muestra el nombre del archivo escogido en la carga inicial.

   ENTRADAS:  atributos data-* que ponen los HTML (data-segundos, etc.).
   SALIDAS:   cambios visuales en la página.
   RESTRICCIONES:
     - La cuenta regresiva es solo visual: al recargar, el tiempo se
       vuelve a leer de Redis, que es la fuente real.
   ===================================================================== */

document.addEventListener("DOMContentLoaded", function () {

    /* ---------- 1. Menú de celular ---------- */
    var botonMenu = document.querySelector("[data-menu-toggle]");
    var menu = document.getElementById("menu-principal");
    if (botonMenu && menu) {
        botonMenu.addEventListener("click", function () {
            // classList.toggle agrega la clase "abierto" si no está, y la quita si ya está.
            var abierto = menu.classList.toggle("abierto");
            botonMenu.setAttribute("aria-expanded", abierto ? "true" : "false");
        });
    }

    /* ---------- 2. Listas desplegables ---------- */
    var listas = document.querySelectorAll("details.desplegable");

    listas.forEach(function (lista) {
        lista.addEventListener("toggle", function () {
            // Al abrir una lista, cerramos las demás.
            if (lista.open) {
                listas.forEach(function (otra) { if (otra !== lista) otra.open = false; });
            }
        });
    });

    // Clic fuera de las listas: se cierran todas.
    document.addEventListener("click", function (evento) {
        listas.forEach(function (lista) {
            if (!lista.contains(evento.target)) lista.open = false;
        });
    });

    // Tecla Escape: se cierran todas.
    document.addEventListener("keydown", function (evento) {
        if (evento.key === "Escape") listas.forEach(function (lista) { lista.open = false; });
    });

    /* ---------- 3. Cuenta regresiva ---------- */
    // Mismo formato que formato_tiempo() de f3_preventas_abiertas.py.
    function formatoTiempo(segundos) {
        if (segundos >= 60) {
            var minutos = Math.floor(segundos / 60);
            var resto = segundos % 60;
            return resto ? minutos + " min " + resto + " s" : minutos + " minutos";
        }
        return segundos + " segundos";
    }

    // Cada elemento con data-segundos tiene un texto .js-tiempo adentro.
    // Guardamos el MOMENTO en que vence (ahora + segundos) para no desfasarnos.
    var cuentas = [];
    document.querySelectorAll("[data-segundos]").forEach(function (el) {
        var segundos = parseInt(el.getAttribute("data-segundos"), 10);
        var texto = el.querySelector(".js-tiempo");
        if (!isNaN(segundos) && texto) {
            cuentas.push({ el: el, texto: texto, vence: Date.now() + segundos * 1000 });
        }
    });

    function actualizar() {
        cuentas.forEach(function (c) {
            var restan = Math.max(0, Math.round((c.vence - Date.now()) / 1000));
            if (restan === 0) {
                c.texto.textContent = "Venció";
                c.el.classList.add("vencida");     // la tarjeta se ve apagada y sin clic
            } else {
                c.texto.textContent = formatoTiempo(restan);
            }
        });
    }
    if (cuentas.length) setInterval(actualizar, 1000);

    /* ---------- 4. Nombre del archivo en la carga inicial ---------- */
    var inputArchivo = document.getElementById("archivo");
    var zona = document.querySelector(".zona-archivo");
    var nombreArchivo = document.querySelector("[data-nombre-archivo]");
    if (inputArchivo && zona && nombreArchivo) {
        inputArchivo.addEventListener("change", function () {
            var tiene = inputArchivo.files.length > 0;
            nombreArchivo.textContent = tiene ? inputArchivo.files[0].name : "Solo archivos .json";
            zona.classList.toggle("con-archivo", tiene);
        });
    }
});
