# Plan de pruebas manuales

Para que la revisión sea rápida, en las pruebas las preventas se abren con **3 minutos o menos** (el proyecto no impone ese límite).

Antes de empezar: Mongo y Redis encendidos, `python app.py` corriendo, (las bases se vacían solas cada vez que se enciende la app).
Para ver Redis: `redis-cli` (en WSL: `wsl -u root`). Para ver Mongo: MongoDB Compass, base `productora_eventos`.
Abrir **dos pestañas** del navegador en `http://localhost:5000` (pestaña A y pestaña B) para las pruebas 12 y 13.

| # | Func. | Qué hacer | Resultado esperado |
|---|---|---|---|
| 1 | F3 | Abrir `/` con todo vacío | "No hay preventas abiertas en este momento." |
| 2 | F5 | Abrir `/consulta` con todo vacío | Aviso para hacer primero la carga inicial |
| 3 | F2 | Abrir `/abrir-preventa` sin catálogo | Aviso "El catálogo está vacío" |
| 4 | F1 | `/carga`: elegir un `.txt` | El botón queda apagado y avisa que debe ser `.json` |
| 5 | F1 | Elegir un archivo con texto que no es JSON | Avisa "no es un JSON válido" y no deja enviar |
| 6 | F1 | Elegir `datos/eventos.json` y enviar | Mensaje verde "se guardaron 5 eventos". **Mongo:** `eventos` pasa de vacía a 5 documentos |
| 7 | F1 | Enviar el mismo archivo otra vez | Mensaje rojo "Se omitieron 5 porque su id ya existía"; Mongo sigue con 5 |
| 8 | F5 | `/consulta` con catálogo y sin entradas | 4 categorías (Conciertos, Deportes, Teatro, Conferencias) todas en 0 y 0 |
| 9 | F2 | Intentar abrir con cantidad 0 o sin evento | El botón no se activa; el resumen explica el error |
| 10 | F2 | Abrir E001 (Concierto) con **5 entradas, 3 min** | Mensaje verde. **Redis:** `GET preventa:E001` → `"5"` y `TTL preventa:E001` ≈ 180 |
| 11 | F2 | Abrir otra vez el mismo evento | Mensaje rojo "ya tiene una preventa abierta"; Redis no cambia |
| 12 | F2 | Abrir también: E002 con **2 entradas, 3 min**; E003 con **1 entrada, 3 min**; E005 con **3 entradas, 1 min** | Cuatro preventas abiertas |
| 13 | F3 | Ir a `/` | 4 tarjetas con entradas y tiempo; las cuentas bajan solas; la de E005 (1 min) se pone roja. Comparar con `GET` y `TTL` en Redis |
| 14 | F4 | Desde la tarjeta de E001, clic en "Obtener entrada" | `/obtener-entrada` con ese evento ya marcado |
| 15 | F4 | Escribir "Ana" y obtener la entrada de E001 | Verde con código `E001-0001` y "quedan 4". **Redis:** `GET preventa:E001` → `"4"`. **Mongo:** documento en `entradas` con código, cliente, evento, categoría y fecha |
| 16 | F4 | Pedir E001 otra vez como "Ana" (o " ana ") | Rojo: "Cliente ya tiene una entrada de este evento"; Redis sigue en 4 |
| 17 | F4 | Pedir E001 como "Luis" | Entrada `E001-0002`; Redis queda en `"3"` |
| 18 | F4 | **Agotada.** En pestaña A abrir `/obtener-entrada` (E003 aparece). En pestaña B, "Ana" toma E003. Volver a A y pedir E003 como "Luis" | Rojo: "Ya no hay entradas disponibles". En `/` la tarjeta de E003 ya no aparece |
| 19 | F4 | **Vencida.** Dejar abierta una pestaña en `/obtener-entrada` y esperar a que pase 1 min desde la prueba 12; pedir E005 | Rojo: "La preventa ... ya venció". **Redis:** `GET preventa:E005` → `nil` |
| 20 | F3 | Mirar `/` tras el minuto | La tarjeta de E005 desapareció sola, sin recargar la página |
| 21 | F4 | Enviar con el nombre vacío (si se salta el botón) o nombre de más de 60 letras | Mensaje de error claro |
| 22 | F5 | Deportes: "Ana" obtiene E002; "Juan" obtiene E002; "Ana" obtiene otra de Deportes | `/consulta`: Deportes con el total de entradas y **2 clientes distintos** (Ana cuenta una sola vez) |
| 23 | F5 | Revisar Conciertos y Teatro | Conciertos: 2 entradas, 2 clientes. Teatro: 1 entrada, 1 cliente |
| 24 | Revisión | Abrir una preventa con **1 minuto** y ver el vencimiento en vivo | La tarjeta pasa a rojo, llega a 0 y desaparece; en Redis la llave ya no existe |
| 25 | Revisión | Probar con otro `.json` (más o menos eventos, otra categoría) | Carga bien; la categoría nueva aparece en F5 |
| 26 | Reinicio | Apagar la app (`Ctrl + C`) y encenderla de nuevo (`python app.py`) | La terminal dice que se borraron eventos, entradas y preventas. `/` y `/consulta` quedan vacías; **Mongo:** `eventos` y `entradas` sin documentos; **Redis:** `KEYS preventa:*` vacío. Hay que repetir la carga inicial |
| 27 | General | `python -m pytest tests` | 19 pruebas aprobadas |
