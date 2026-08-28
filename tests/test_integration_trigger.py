import os
import psycopg2
import pytest
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def db_connection():
    """Conexion real a PostgreSQL usando las credenciales del .env."""
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    yield conn
    conn.close()


def test_trigger_generates_speed_alert_in_high_risk_zone(db_connection):
    cur = db_connection.cursor()

    # Punto dentro del rango de Norte-Este: lat 3.4467-3.52, lon -76.50 a -76.46
    test_lat = 3.47
    test_lon = -76.48
    test_vehicle_id = "VHC-TEST-INTEGRATION"
    test_speed = 50.0

    try:
        cur.execute(
            """
            INSERT INTO raw_telemetry (vehicle_id, reported_at, speed_kmh, fuel_level, geom)
            VALUES (%s, NOW(), %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            RETURNING id;
            """,
            (test_vehicle_id, test_speed, 80.0, test_lon, test_lat),
        )
        telemetry_id = cur.fetchone()[0]
        db_connection.commit()

        # Verifica que el trigger genero la alerta de velocidad
        cur.execute(
            "SELECT geofence_id, excess_kmh FROM speed_alerts WHERE telemetry_id = %s;",
            (telemetry_id,),
        )
        alert = cur.fetchone()

        assert alert is not None, (
            "El trigger no genero una alerta de velocidad para un punto "
            "en zona de alto riesgo con velocidad superior al limite."
        )
        assert alert[1] == pytest.approx(20.0, abs=0.01), (
            f"Exceso esperado de 20.0 km/h (50 - 30), se obtuvo {alert[1]}"
        )

    finally:
        # Limpieza: elimina el registro de prueba y su alerta asociada
        cur.execute(
            "DELETE FROM speed_alerts WHERE vehicle_id = %s;", (test_vehicle_id,)
        )
        cur.execute(
            "DELETE FROM raw_telemetry WHERE vehicle_id = %s;", (test_vehicle_id,)
        )
        db_connection.commit()
        cur.close()