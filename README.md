# Simón Movilidad — Sistema de Telemetría GIS

Pipeline de datos geoespaciales para telemetría vehicular (GPS/IoT) en tiempo real, con arquitectura de tres capas (Bronce, Plata, Oro) sobre PostgreSQL + PostGIS. Detecta automáticamente infracciones de velocidad y alertas de combustible mediante triggers, y expone los resultados en un tablero interactivo de Business Intelligence.

## Características principales

- **Ingesta en tiempo real** vía API FastAPI con validación en dos capas (Pydantic + constraints SQL)
- **Enmascaramiento de privacidad** de identificadores de vehículo mediante roles y vistas a nivel de base de datos
- **Geocercas y alertas automáticas** (velocidad dinámica por zona, autonomía de combustible predictiva) mediante trigger de PostgreSQL
- **Optimización verificada**: índices espaciales GiST con evidencia real de rendimiento (~94-256x más rápido, ver `docs/DESIGN.md`)
- **Simulador de flota** con rutas reales sobre las vías de Cali (OSRM), con mecanismo de resiliencia ante fallos del servicio
- **Tablero interactivo** (Streamlit + Folium): rutas, mapas de calor de infracciones, geocercas, filtrado por vehículo
- **15 pruebas unitarias** cubriendo lógica de geocercas, alertas de velocidad y cálculo de autonomía

## Stack técnico

Python · FastAPI · PostgreSQL 16 + PostGIS 3.4 · Docker Compose · Streamlit · Folium · pytest

## Inicio rápido

```bash
git clone https://github.com/ajulescobar/simon-movilidad-gis.git
cd simon-movilidad-gis
cp .env.example .env
docker compose up -d
```

Guía completa de despliegue paso a paso, con verificaciones y solución de problemas: **[docs/SETUP.md](docs/SETUP.md)**

## Documentación

- **[docs/DESIGN.md](docs/DESIGN.md)** — Arquitectura, decisiones de diseño, trade-offs de rendimiento y evidencia de optimización
- **[docs/SETUP.md](docs/SETUP.md)** — Guía de despliegue local, paso a paso, con verificaciones

## Estructura del proyecto

```
bronze/     API de ingesta, esquema de datos crudos, simulador de flota
silver/     Geocercas, alertas de velocidad/combustible, triggers
gold/       Vista consolidada para BI, análisis de rendimiento
dashboard/  Tablero interactivo (Streamlit + Folium)
db/init/    Scripts de inicialización automática de la base de datos
tests/      Pruebas unitarias (pytest)
docs/       DESIGN.md y SETUP.md
```