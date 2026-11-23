# Proyecto 1 – Bases de Datos Avanzadas (NoSQL)
**Equipo:** Paz Bloise · Angel Gazel · Rachel Rojas
**App web:** Python + Flask · **Bases de datos:** MongoDB + Redis

---

## 1. Qué hay en cada archivo

```
proyecto/
├── app.py               ← Archivo principal: enciende la app y define las páginas (rutas)
├── db.py                ← Conexiones a MongoDB y Redis (solo aquí se configuran)
├── f1_carga.py          ← Lógica F1: validar el JSON y guardarlo en Mongo (Paz)
├── f2_abrir_preventa.py ← Lógica F2: abrir la preventa en Redis con TTL (Paz)
├── requirements.txt     ← Lista de librerías de Python que hay que instalar
├── docker-compose.yml   ← Enciende Mongo y Redis con un solo comando (opcional)
├── datos/
│   └── eventos.json     ← Datos iniciales que dio la profe
├── templates/           ← Páginas HTML (lo que se ve)
│   ├── base.html        ← Molde común: encabezado (cliente), mensajes y pie de página (administración)
│   ├── preventas.html   ← Página principal = F3 Preventas abiertas
│   ├── carga.html       ← Pantalla F1
│   ├── abrir_preventa.html ← Pantalla F2
│   └── pendiente.html   ← Página temporal (se borra al terminar)
└── static/
    └── estilo.css       ← Colores, letras y espacios
```

**Dueños de cada funcionalidad:**
| Funcionalidad | Ruta | Dueño/a |
|---|---|---|
| F1 Carga inicial | `/carga` | Paz |
| F2 Abrir preventa | `/abrir-preventa` | Paz |
| F3 Preventas abiertas (página principal) | `/` | Rachel |
| F4 Obtener entrada | `/obtener-entrada` | Angel |
| F5 Consultar entradas | `/consulta` | Rachel |

---

## 2. Instalación (cada uno en su compu)

### a) Programas
1. **Python 3.12**: https://www.python.org/downloads/ → al instalar, **marcar "Add python.exe to PATH"**.
2. **Visual Studio Code**: https://code.visualstudio.com/ → instalar la extensión **"Python"** (de Microsoft).
   *(Si tenés Visual Studio "normal", el morado, también sirve, pero VS Code es más liviano y es el que vamos a usar todos.)*
3. **MongoDB Compass** (para ver los datos de Mongo y sacar capturas): https://www.mongodb.com/try/download/compass
4. **Redis Insight** (para ver Redis, las preventas y su TTL): https://redis.io/insight/

### b) MongoDB y Redis — elegir UNA opción
**Opción A (recomendada): Docker Desktop**
1. Instalar Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Abrir una terminal en la carpeta del proyecto y ejecutar:
   ```
   docker compose up -d
   ```
   Esto enciende Mongo y Redis. Para apagarlos: `docker compose down`.

**Opción B: instalar por separado**
- MongoDB Community Server: https://www.mongodb.com/try/download/community
- Redis en Windows no se instala directo: usar WSL (`wsl --install`, luego `sudo apt install redis-server` y `redis-server`).

### c) Librerías de Python
En la terminal de VS Code, dentro de la carpeta del proyecto:
```
pip install -r requirements.txt
```

---

## 3. Encender la app
```
python app.py
```
En la terminal debe salir:
```
✔ MongoDB conectado correctamente
✔ Redis conectado correctamente
```
Luego abrir en el navegador: **http://localhost:5000**

Si sale ✘ en alguna, es que Mongo o Redis no están encendidos (revisar Docker Desktop).

---

## 4. Dejar las bases de datos vacías (para pruebas)
Antes de probar la carga inicial o de ir a la revisión:
```
python limpiar_bd.py
```
Pide confirmación (s/n) y borra todo lo de Mongo y Redis.
**No es parte de la app** (no lleva botón), porque el enunciado no permite funcionalidades extra.
También se puede hacer a mano: en Compass → colección → *Drop collection*; en Redis Insight → *Flush DB*.

---

## 5. Recordatorios del enunciado
- Solo las 5 funcionalidades pedidas: **nada extra**.
- Todo se muestra en la interfaz, **nunca en formato JSON/CSV**.
- Cada funcionalidad: código comentado + pruebas + validaciones + screenshots (app + BD antes y después).
- PDF: `PazBloise-AngelGazel-RachelRojas.pdf` · Entrega: **lunes 30 nov, 11:00 p.m., TECDigital**.
