# Guía de despliegue local para el *Sistema de Telemetría GIS Simón Movilidad*

## Alcance de este documento

Esta guía permite desplegar el sistema completo en un entorno local (desarrollo), partiendo de un repositorio recién clonado y sin ningún servicio previamente configurado. En este sentido, se considera la base de datos, backend (API de ingesta), proceso de generación de datos de prueba, y tablero de visualización (BI). Asi, es importante mencionar que el proyecto **NO incluye los siguientes componentes**:

- No existe un frontend separado del tablero Streamlit descrito en el Paso 8.
- No existe un sistema de migraciones versionado (tipo Alembic/Flyway). La creación de esquema se resuelve mediante scripts SQL ejecutados automáticamente por Docker en el primer arranque (Paso 3.3), que cumplen la función de migración/seed inicial.
- No existe configuración de despliegue en producción, CI/CD, ni variables de entorno para ambientes distintos a local.

Esta guía es válida para Windows, Linux y macOS. Los comandos se presentan primero para PowerShell (Windows), con la variante en Bash (Linux/macOS) donde exista diferencia.

---

## Orden de ejecución (obligatorio)

Los pasos deben ejecutarse en este orden. Ningún paso posterior funciona si el anterior no se completó correctamente:

```
Paso 0  Verificar requisitos previos
Paso 1  Clonar el repositorio
Paso 2  Configurar variables de entorno
Paso 3  Desplegar base de datos (esquema completo se crea automáticamente)
Paso 4  Crear entorno virtual de Python
Paso 5  Instalar dependencias Python
Paso 6  Levantar API (Capa Bronce)         ← requiere Paso 3 y 5 completos
Paso 7  Generar datos de prueba            ← requiere Paso 6 en ejecución
Paso 8  Levantar tablero (Dashboard)       ← requiere Paso 3 completo (datos son opcionales para abrir, obligatorios para ver contenido)
Paso 9  Ejecutar pruebas unitarias         ← no depende de los anteriores
Paso 10 Verificación final de despliegue
Paso 11 Apagar el sistema / reiniciar desde cero
```

---

## Paso 0. Requisitos previos

| Herramienta | Versión usada en desarrollo | Verificación |
|---|---|---|
| Docker Desktop / Docker Engine | 28.3.3 | `docker --version` |
| Docker Compose (plugin v2) | v2.39.2 | `docker compose version` |
| Python | 3.13.7 (mínimo compatible: 3.12) | `python --version` (Windows) / `python3 --version` (Linux/macOS) |
| Git | Versión reciente, sin requisito específico | `git --version` |
| Puertos libres en el host | 5433, 8000, 8501 (ver Paso 3.1 y solución de problemas) | Ver Paso 0.2 |

**Nota sobre `python` vs `python3`:** en Windows, el comando `python` invoca Python 3 si está correctamente instalado. En Linux y macOS, `python` puede no existir o apuntar a Python 2; use `python3` y `pip3` en esos sistemas si `python`/`pip` fallan.

**Nota sobre `docker compose` vs `docker-compose`:** esta guía usa `docker compose` (sin guion, plugin v2, incluido en Docker Desktop y versiones recientes de Docker Engine). En sistemas con Docker más antiguo (Docker Engine anterior a 20.10 con plugin separado, o distribuciones que instalan solo la herramienta standalone), puede estar disponible únicamente como `docker-compose` (con guion, v1). Verificar con `docker compose version` primero; si falla, usar `docker-compose` en su lugar. No obstante, ambas sintaxis son funcionalmente equivalentes para los comandos de esta guía.

### Paso 0.1. Verificación de que Docker se encuentra en ejecución

```bash
docker ps
```

**Resultado esperado:**
```
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
```
(tabla vacía, sin filas, sin errores)

En Windows, si se presenta un error del tipo `error during connect: ... open //./pipe/dockerDesktopLinuxEngine`, Docker Desktop está instalado pero no iniciado. Debe abrirse desde el menú de inicio y esperar entre 30 y 60 segundos hasta que el ícono deje de estar animado, y repetir el comando.

En Linux, si el servicio no está activo:
```bash
sudo systemctl start docker
```

### Paso 0.2. Verificación de disponibilidad de puertos

El sistema requiere los puertos 5433 (base de datos), 8000 (API) y 8501 (dashboard) libres en el host.

```bash
# Windows (PowerShell)
Get-NetTCPConnection -LocalPort 5433,8000,8501 -ErrorAction SilentlyContinue

# Linux / macOS
lsof -i :5433 -i :8000 -i :8501
```

Si alguno de estos comandos devuelve un proceso activo en esos puertos, existe un conflicto que debe resolverse antes de continuar (ver tabla de solución de problemas al final de este documento).

---

## Paso 1. Clonación del repositorio

```bash
git clone https://github.com/ajulescobar/simon-movilidad-gis.git
cd simon-movilidad-gis
```

### Paso 1.1. Verificación de la estructura del proyecto

```bash
# Windows (PowerShell)
dir

# Linux / macOS
ls
```

Se debe observar, como mínimo: `bronze/`, `silver/`, `gold/`, `tests/`, `docs/`, `dashboard/`, `db/`, `docker-compose.yml`, `requirements.txt`, `.env.example`, `.gitignore`. Si falta alguno de estos elementos, la clonación fue incompleta o corresponde a una rama distinta de la esperada; debe verificarse antes de continuar.

---

## Paso 2. Configuración de variables de entorno

### Paso 2.1. Copia del archivo de ejemplo

```bash
# Windows (PowerShell)
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

### Paso 2.2. Verificación del contenido

```bash
# Windows (PowerShell)
Get-Content .env

# Linux / macOS
cat .env
```

**Resultado esperado:**
```
POSTGRES_USER=admin
POSTGRES_PASSWORD=admin123
POSTGRES_DB=simon_movilidad
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
```

No es necesario modificar estos valores para un entorno local. Si el puerto 5433 ya está ocupado en el host (ver Paso 0.2), debe ajustarse `POSTGRES_PORT` aquí y el mapeo de puertos correspondiente en `docker-compose.yml` (ver Paso 3.1).

**Nota:** este proyecto no utiliza variables de entorno adicionales a las anteriores. En particular, la integración con el servicio de rutas OSRM (usado por el simulador del Paso 7) se conecta a un endpoint público sin autenticación y sin variable de entorno propia; no debe buscarse una variable tipo `OSRM_URL` en `.env`, ya que no existe.

---

## Paso 3. Despliegue de la base de datos (PostgreSQL 16 + PostGIS 3.4)

```bash
docker compose up -d
```

En la primera ejecución se descarga la imagen `postgis/postgis:16-3.4` (aproximadamente 500 MB), lo que puede tardar entre 1 y 2 minutos según la conexión a internet.

**Resultado esperado (primera ejecución):**
```
[+] Running 3/3
 ✔ Network simon-movilidad-gis_default         Created
 ✔ Volume "simon-movilidad-gis_postgres_data"  Created
 ✔ Container simon_gis_db                      Started
```

### Paso 3.1. Justificación del puerto 5433

El contenedor mapea el puerto interno de PostgreSQL (5432) al puerto externo 5433 del host (`"5433:5432"` en `docker-compose.yml`). Esta decisión responde a que, durante el desarrollo original, una instalación nativa de PostgreSQL en el sistema operativo ocupaba el puerto 5432 estándar, provocando que los clientes de base de datos se conectaran de forma silenciosa al motor nativo en lugar del contenedor, sin ningún error visible en los registros de Docker.

Para verificar si existe un PostgreSQL nativo que pueda generar el mismo conflicto:

```bash
# Windows (PowerShell)
Get-Service -Name "*postgres*"

# Linux
sudo systemctl status postgresql

# macOS (instalación vía Homebrew)
brew services list | grep postgresql
```

Si no se encuentra ningún servicio nativo en ejecución, puede utilizarse el puerto estándar 5432 sin conflicto, ajustando `"5433:5432"` a `"5432:5432"` en `docker-compose.yml` y `POSTGRES_PORT=5432` en `.env`. De lo contrario, debe conservarse la configuración por defecto (5433).

### Paso 3.2. Verificación del estado del contenedor

```bash
docker ps
```

**Resultado esperado:**
```
CONTAINER ID   IMAGE                    COMMAND                  STATUS         PORTS                                         NAMES
xxxxxxxxxxxx   postgis/postgis:16-3.4   "docker-entrypoint.s…"   Up X seconds   0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp   simon_gis_db
```

Si el estado no es `Up`, o el contenedor no aparece, debe revisarse el registro completo con `docker logs simon_gis_db` para identificar el error de arranque.

### Paso 3.3. Verificación de la inicialización automática del esquema (equivalente a migración/seed inicial)

Este proyecto no usa una herramienta de migraciones dedicada. En su lugar, la carpeta `db/init/` contiene 9 scripts SQL numerados que PostgreSQL ejecuta automáticamente, en orden alfabético, la primera vez que el contenedor crea su volumen de datos. Esto reemplaza tanto la función de "migración" (creación de esquema) como de "seeder" (carga de las 9 geocercas iniciales).

```bash
docker logs simon_gis_db
```

Deben observarse, en orden, las siguientes líneas dentro de la salida:

```
running /docker-entrypoint-initdb.d/00_extensions.sql
CREATE EXTENSION

running /docker-entrypoint-initdb.d/01_schema_bronze.sql
CREATE TABLE
CREATE INDEX
CREATE INDEX

running /docker-entrypoint-initdb.d/02_masking_view.sql
CREATE VIEW
CREATE ROLE
GRANT
CREATE ROLE
GRANT

running /docker-entrypoint-initdb.d/03_schema_silver.sql
CREATE TABLE
CREATE INDEX

running /docker-entrypoint-initdb.d/04_seed_geofences.sql
INSERT 0 9

running /docker-entrypoint-initdb.d/05_speed_alerts_schema.sql
CREATE TABLE
CREATE INDEX
CREATE INDEX

running /docker-entrypoint-initdb.d/06_fuel_alerts_schema.sql
CREATE TABLE
CREATE INDEX
CREATE INDEX

running /docker-entrypoint-initdb.d/07_triggers.sql
CREATE FUNCTION
CREATE TRIGGER

running /docker-entrypoint-initdb.d/08_schema_gold.sql
CREATE VIEW
```

Y al final:
```
database system is ready to accept connections
```

Si se presenta el error `type "geometry" does not exist` en `01_schema_bronze.sql`, `00_extensions.sql` no se ejecutó o no existe en `db/init/`. Debe verificarse que dicho archivo, con el contenido `CREATE EXTENSION IF NOT EXISTS postgis;`, esté presente y ordenado antes de `01_schema_bronze.sql`, dado que el orden alfabético del nombre determina el orden de ejecución.

**Importante:** estos scripts solo se ejecutan la primera vez que se crea el volumen de datos. Si el contenedor ya existía previamente (por ejemplo, se corrió `docker compose up -d` antes sin `down -v`), los logs mostrarán `PostgreSQL Database directory appears to contain a database; Skipping initialization` y los scripts no se re-ejecutarán. Esto es esperado y no es un error; ver Paso 11 para forzar la re-inicialización.

### Paso 3.4. Verificación adicional mediante un cliente SQL

Conexión mediante DBeaver, pgAdmin, psql o cliente equivalente:

- **Host:** `localhost`
- **Port:** `5433`
- **Database:** `simon_movilidad`
- **Username:** `admin`
- **Password:** `admin123`

Verificación de tablas y vistas:

```sql
SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';
```

**Resultado esperado** (9 filas):
```
geography_columns
geometry_columns
spatial_ref_sys
vehicle_analytics_gold
raw_telemetry
telemetry_masked
geofences
speed_alerts
fuel_alerts
```

(Las primeras tres corresponden a tablas internas de la extensión PostGIS, no específicas de este proyecto.)

Verificación de roles:

```sql
SELECT rolname FROM pg_roles WHERE rolname IN ('gis_admin', 'gis_readonly');
```

**Resultado esperado:**
```
gis_admin
gis_readonly
```

Verificación de las 9 geocercas cargadas:

```sql
SELECT COUNT(*) FROM geofences;
```

**Resultado esperado:** `9`

---

## Paso 4. Entorno virtual de Python

### Paso 4.1. Creación

```bash
# Windows
python -m venv venv

# Linux / macOS
python3 -m venv venv
```

En distribuciones Debian/Ubuntu (incluyendo derivadas como OSGeoLive), el módulo `venv` puede no estar incluido por defecto junto con el intérprete de Python. Si aparece el error `The virtual environment was not created successfully because ensurepip is not available`, instalar el paquete correspondiente a la versión de Python en uso antes de reintentar (ajustar `3.12` a la versión real si difiere):

```bash
sudo apt update
sudo apt install python3.12-venv
```

Luego repetir `python3 -m venv venv`.

### Paso 4.2. Activación

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

**Resultado esperado:** el indicador `(venv)` aparece al inicio del prompt de la terminal.

En Windows, si se presenta el error `no se puede cargar el archivo ... porque la ejecución de scripts está deshabilitada`, debe ejecutarse una única vez (confirmando si se solicita):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Y repetir la activación.

**Regla importante:** el entorno virtual debe activarse en cada terminal nueva utilizada en los pasos 5 a 9. La activación es local a cada ventana de terminal y no persiste al abrir una nueva.

---

## Paso 5. Instalación de dependencias

Con el entorno virtual activado, desde la raíz del proyecto:

```bash
# Windows
pip install -r requirements.txt

# Linux / macOS
pip3 install -r requirements.txt
```

**Paquetes esperados:** `fastapi`, `uvicorn`, `psycopg2-binary`, `python-dotenv`, `faker`, `requests`, `numpy`, `pytest`, `shapely`, `streamlit`, `folium`, `streamlit-folium`, `pandas`, y sus dependencias transitivas. Debe verificarse que el proceso finalice sin líneas `ERROR:` en la salida. Un fallo común en Linux es la ausencia de herramientas de compilación para `psycopg2-binary`; si ocurre, instalar `python3-dev` y `libpq-dev` (Debian/Ubuntu) o el paquete equivalente de la distribución, y repetir la instalación.

---

## Paso 6. Despliegue de la API de ingesta (Capa Bronce)

Requiere que el Paso 3 (base de datos) y el Paso 5 (dependencias) estén completos.

En una terminal, con el entorno virtual activado:

```bash
cd bronze
uvicorn main:app --reload
```

**Resultado esperado:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Application startup complete.
```

Esta terminal debe permanecer abierta y en ejecución mientras se usen los pasos siguientes; cerrarla detiene la API.

### Paso 6.1. Verificación

Acceder en el navegador a: `http://127.0.0.1:8000/docs`

Debe cargar la documentación interactiva (Swagger UI) con los endpoints `POST /telemetry` y `GET /health` listados.

Alternativamente, desde otra terminal:
```bash
curl http://127.0.0.1:8000/health
```
**Resultado esperado:** `{"status":"API funcionando correctamente"}`

---

## Paso 7. Generación de datos de prueba (simulador de flota)

Requiere que el Paso 6 (API) esté en ejecución en otra terminal.

En una segunda terminal nueva, con el entorno virtual activado nuevamente:

```bash
# Windows (PowerShell), desde la raíz del proyecto
cd bronze
..\venv\Scripts\Activate.ps1
python simulate_devices.py

# Linux / macOS
cd bronze
source ../venv/bin/activate
python3 simulate_devices.py
```

El script simula 5 vehículos recorriendo rutas reales de Cali obtenidas mediante el servicio público OSRM (con mecanismo de respaldo por interpolación lineal si dicho servicio externo no responde). Por cada vehículo se muestra en consola cada punto insertado y, cuando corresponda, las alertas generadas en tiempo real por el trigger de la base de datos:

```
[45/207] OK - speed=45.2 fuel=25.3
[46/207] OK - speed=62.8 fuel=25.1 | ALERTA VELOCIDAD (+32.8 km/h)
[89/207] OK - speed=41.0 fuel=8.5 | ALERTA COMBUSTIBLE (autonomía: 34.0 km)
```

Al finalizar los 5 vehículos se muestra: `[OK] Simulación completa para toda la flota.`

Este proceso tarda aproximadamente entre 1 y 2 minutos, según la latencia de las consultas al servicio OSRM.

### Paso 7.1. Verificación

```sql
SELECT COUNT(*) FROM raw_telemetry;
```
Se espera un valor entre 500 y 900 registros (variable según la cantidad de puntos que devuelva OSRM en cada ejecución; no es un valor fijo).

```sql
SELECT COUNT(*) FROM speed_alerts;
SELECT COUNT(*) FROM fuel_alerts;
```
Ambos deben devolver un valor mayor a 0, confirmando que el trigger generó alertas automáticamente durante la inserción.

---

## Paso 8. Despliegue del tablero de visualización (Business Intelligence)

Requiere que el Paso 3 (base de datos) esté activo. Los datos del Paso 7 son necesarios para ver contenido en los mapas, pero el tablero puede abrirse sin ellos (mostrará una advertencia de ausencia de datos).

En una tercera terminal, desde la raíz del proyecto:

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1
streamlit run dashboard/app.py

# Linux / macOS
source venv/bin/activate
streamlit run dashboard/app.py
```

En la primera ejecución, Streamlit puede solicitar un correo electrónico opcional de registro; se omite presionando Enter sin ingresar información.

**Resultado esperado:**
```
You can now view your Streamlit app in your browser.

Local URL: http://localhost:8501
Network URL: http://192.168.x.x:8501
```

El navegador se abre automáticamente; si no ocurre, acceder manualmente a `http://localhost:8501`.

### Paso 8.1. Verificación

El tablero debe mostrar, sin errores en pantalla:
- Un selector para filtrar por uno o varios vehículos, o ver la flota completa.
- Un mapa con la ruta de los vehículos (marcadores de inicio "A" y fin "B") si se ejecutó el Paso 7.
- Capas activables/desactivables de mapa de calor de infracciones (velocidad y combustible) y de geocercas.
- Tarjetas de métricas: total de infracciones, velocidad promedio, nivel de combustible.
- Un botón de actualización manual de datos.

---

## Resumen de servicios y puertos

| Servicio | Comando | URL / Puerto | Terminal |
|---|---|---|---|
| PostgreSQL + PostGIS | `docker compose up -d` | `localhost:5433` | segundo plano (Docker) |
| API FastAPI | `uvicorn main:app --reload` (desde `bronze/`) | `http://127.0.0.1:8000` | Terminal 1 (permanece abierta) |
| Documentación API (Swagger) | — | `http://127.0.0.1:8000/docs` | navegador |
| Simulador de flota | `python simulate_devices.py` (desde `bronze/`) | — (cliente HTTP) | Terminal 2 (finaliza sola) |
| Tablero (Dashboard) | `streamlit run dashboard/app.py` (desde la raíz) | `http://localhost:8501` | Terminal 3 (permanece abierta) |

---

## Paso 9. Ejecución de pruebas unitarias

No depende de los pasos anteriores: las pruebas no requieren base de datos, API ni servicios activos.

Desde la raíz del proyecto, con el entorno virtual activado:

```bash
pytest -v
```

**Resultado esperado:** 15 pruebas exitosas (`15 passed`), correspondientes al cálculo de autonomía predictiva (`tests/test_fuel_prediction.py`), la detección de geocercas (`tests/test_geofences.py`) y la validación de exceso de velocidad (`tests/test_speed_validation.py`).

---

## Paso 10. Verificación final de despliegue exitoso

Antes de considerar el despliegue completo, confirmar todos los puntos siguientes:

- [ ] `docker ps` muestra el contenedor `simon_gis_db` con estado `Up`.
- [ ] La consulta `SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';` devuelve las 9 tablas/vistas esperadas (Paso 3.4).
- [ ] Los roles `gis_admin` y `gis_readonly` existen (Paso 3.4).
- [ ] `http://127.0.0.1:8000/docs` carga la documentación de la API sin errores.
- [ ] El simulador (`simulate_devices.py`) finalizó con el mensaje `[OK] Simulación completa para toda la flota.`, sin líneas `ERROR` ni `Fallo de conexión`.
- [ ] `SELECT COUNT(*) FROM raw_telemetry;` devuelve un valor mayor a 0.
- [ ] `SELECT COUNT(*) FROM speed_alerts;` y `SELECT COUNT(*) FROM fuel_alerts;` devuelven valores mayores a 0.
- [ ] `http://localhost:8501` muestra el tablero con el mapa poblado y las métricas calculadas.
- [ ] `pytest -v` reporta `15 passed`.

Si todos los puntos se cumplen, el despliegue local es funcional de punta a punta.

---

## Paso 11. Apagado del sistema y reinicio desde cero

### Paso 11.1. Detener los servicios sin perder datos

En las Terminales 1 y 3 (API y dashboard), presionar `Ctrl+C` para detener cada proceso.

Para detener el contenedor de base de datos sin eliminar los datos:
```bash
docker compose stop
```

Para reanudar posteriormente sin perder lo ya cargado:
```bash
docker compose start
```

### Paso 11.2. Reinicio completo desde cero (elimina todos los datos)

```bash
docker compose down -v
docker compose up -d
```

El indicador `-v` elimina el volumen de datos, forzando la re-ejecución de los scripts de `db/init/` en el siguiente arranque (Paso 3.3), recreando extensión, tablas, vistas, roles, geocercas y trigger. Después de esto, debe repetirse el Paso 7 para volver a generar datos de telemetría.

---

## Solución de problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| `docker ps` retorna error de conexión | Docker Desktop no está en ejecución | Abrir Docker Desktop y esperar su inicio completo (Paso 0.1) |
| Error de autenticación al conectar con DBeaver/pgAdmin usando el puerto correcto | Otro PostgreSQL (nativo) está usando el mismo puerto | Confirmar el uso del puerto 5433, no 5432 (Paso 3.1) |
| `uvicorn: command not found` / `'uvicorn' no se reconoce` | El entorno virtual no está activado en la terminal actual | Activar el entorno virtual en esa terminal (Paso 4.2) |
| `type "geometry" does not exist` en los registros de Docker | Ausencia o mal ordenamiento de `db/init/00_extensions.sql` | Verificar la existencia del archivo con `CREATE EXTENSION IF NOT EXISTS postgis;`, con nombre alfabéticamente anterior a `01_schema_bronze.sql` |
| Los scripts de `db/init/` no se ejecutan tras modificarlos | El volumen de datos ya existía de una ejecución previa | Ejecutar `docker compose down -v` y luego `docker compose up -d` (Paso 11.2) |
| `psycopg2.pool.PoolError: connection pool exhausted` | Se agotaron las 10 conexiones del pool sin liberación adecuada | Verificar que la API ejecute la versión del código que libera conexiones con `release_connection()`, no `conn.close()` |
| El simulador reporta `route_source: interpolated_fallback` en lugar de `osrm` | El servicio público de OSRM no respondió (límite de tasa o caída temporal) | Comportamiento esperado, no es un error; el sistema continúa operando con rutas interpoladas |
| `Address already in use` al iniciar `uvicorn` o `streamlit` | El puerto 8000 u 8501 ya está ocupado por otro proceso | Verificar con el comando del Paso 0.2 y cerrar el proceso, o iniciar el servicio en un puerto distinto (`uvicorn main:app --port 8001`, `streamlit run dashboard/app.py --server.port 8502`) |
| Error de compilación al instalar `psycopg2-binary` en Linux | Faltan cabeceras de desarrollo de PostgreSQL | Instalar `python3-dev` y `libpq-dev` (Debian/Ubuntu) o equivalente, y repetir el Paso 5 |
| El dashboard muestra "No hay datos de telemetría" | El Paso 7 no se ejecutó, o se ejecutó contra una base de datos distinta | Verificar `.env` en ambas terminales (API y dashboard) y repetir el Paso 7 |