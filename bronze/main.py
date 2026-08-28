import psycopg2
from fastapi import FastAPI, HTTPException
from schemas import TelemetryPacket
from database import get_connection, release_connection

app = FastAPI(title="Simón Movilidad - Capa Bronce (Ingesta GPS)")


@app.post("/telemetry", status_code=201)
def receive_telemetry(packet: TelemetryPacket):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # 1. Insertar el punto de telemetría
            cur.execute(
                """
                INSERT INTO raw_telemetry (vehicle_id, reported_at, speed_kmh, fuel_level, geom)
                VALUES (%s, NOW(), %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326))
                RETURNING id;
                """,
                (
                    packet.vehicle_id,
                    packet.speed_kmh,
                    packet.fuel_level,
                    packet.longitude,
                    packet.latitude,
                ),
            )
            new_id = cur.fetchone()[0]

            # 2. Verificar si el trigger generó una alerta de velocidad
            cur.execute(
                "SELECT geofence_id, excess_kmh FROM speed_alerts WHERE telemetry_id = %s;",
                (new_id,),
            )
            speed_alert = cur.fetchone()

            # 3. Verificar si el trigger generó una alerta de combustible
            cur.execute(
                "SELECT estimated_autonomy_km FROM fuel_alerts WHERE telemetry_id = %s;",
                (new_id,),
            )
            fuel_alert = cur.fetchone()

        conn.commit()

        # 4. Armar la respuesta incluyendo el estado de las alertas
        response = {
            "status": "ok",
            "id": new_id,
            "alerts": {
                "speed_alert": speed_alert is not None,
                "speed_excess_kmh": speed_alert[1] if speed_alert else None,
                "fuel_alert": fuel_alert is not None,
                "estimated_autonomy_km": fuel_alert[0] if fuel_alert else None,
            },
        }
        return response

    except psycopg2.Error as e:
        conn.rollback()
        raise HTTPException(status_code=503, detail=f"Error de base de datos: {str(e)}")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        release_connection(conn)


@app.get("/health")
def health_check():
    return {"status": "API funcionando correctamente"}