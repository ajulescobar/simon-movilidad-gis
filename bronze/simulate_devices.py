import time
import random
import requests
from route_generator import generate_route
from datetime import datetime, timedelta, timezone

API_URL = "http://127.0.0.1:8000/telemetry"

FLEET = [
    {
        "vehicle_id": "VHC-1001-CAL",
        "origin": (3.4516, -76.5320),
        "destination": (3.4700, -76.5100),
        "fuel_start": 85.0,
    },
    {
        "vehicle_id": "VHC-1002-CAL",
        "origin": (3.4200, -76.5450),
        "destination": (3.4450, -76.5200),
        "fuel_start": 60.0,
    },
    {
        "vehicle_id": "VHC-1003-CAL",
        "origin": (3.3900, -76.5300),
        "destination": (3.4100, -76.5000),
        "fuel_start": 95.0,
    },
    {
        "vehicle_id": "VHC-1004-CAL",
        "origin": (3.4600, -76.5000),
        "destination": (3.4800, -76.4800),
        "fuel_start": 30.0,
    },
    {
        "vehicle_id": "VHC-1005-CAL",
        "origin": (3.4000, -76.5500),
        "destination": (3.3800, -76.5250),
        "fuel_start": 100.0,
    },
]


def generate_realistic_speed(is_first_point):
    """
    Simula velocidades para tráfico urbano
    """
    if is_first_point:
        return 0.0
    if random.random() < 0.1:  # 10% de probabilidad: semáforo, tráfico lento
        return round(random.uniform(0, 15), 2)
    return round(random.uniform(20, 65), 2)


def simulate_vehicle(vehicle, report_interval_seconds=2):
    """
    Recorre la ruta de un vehículo y envía cada punto como un reporte
    de telemetría a la API.
    """
    vehicle_id = vehicle["vehicle_id"]
    print(f"\n[INFO] Iniciando simulación para {vehicle_id}...")

    route_result = generate_route(vehicle["origin"], vehicle["destination"])
    route = route_result["route"]
    print(f"   Ruta obtenida vía: {route_result['route_source']} ({len(route)} puntos)")

    start_time = datetime.now(timezone.utc) - timedelta(seconds=report_interval_seconds * len(route))

    fuel = vehicle["fuel_start"]
    fuel_decrement = (fuel / len(route)) * 0.3

    for i in range(len(route)):
        curr_point = route[i]

        speed = generate_realistic_speed(is_first_point=(i == 0))
        fuel = max(fuel - fuel_decrement, 0)

        point_timestamp = start_time + timedelta(seconds=report_interval_seconds * i)
        payload = {
            "vehicle_id": vehicle_id,
            "latitude": curr_point[0],
            "longitude": curr_point[1],
            "speed_kmh": round(speed, 2),
            "fuel_level": round(fuel, 2),
            "reported_at": point_timestamp.isoformat(),
        }

        try:
            response = requests.post(API_URL, json=payload, timeout=5)
            if response.status_code == 201:
                data = response.json()
                alerts = data.get("alerts", {})

                status_line = f"   [{i+1}/{len(route)}] OK - speed={payload['speed_kmh']} fuel={payload['fuel_level']}"

                if alerts.get("speed_alert"):
                    status_line += f" | ALERTA VELOCIDAD (+{alerts['speed_excess_kmh']} km/h)"

                if alerts.get("fuel_alert"):
                    status_line += f" | ALERTA COMBUSTIBLE (autonomía: {alerts['estimated_autonomy_km']} km)"

                print(status_line)
            else:
                print(f"   [{i+1}/{len(route)}] ERROR {response.status_code}: {response.text}")
        except requests.RequestException as e:
            print(f"   [{i+1}/{len(route)}] Fallo de conexión: {e}")

        time.sleep(0.1)  # Pausa para no saturar la API


def main():
    print("=" * 60)
    print("SIMULADOR DE FLOTA - Simón Movilidad (Capa Bronce)")
    print("=" * 60)

    for vehicle in FLEET:
        simulate_vehicle(vehicle)

    print("\n[OK] Simulación completa para toda la flota.")


if __name__ == "__main__":
    main()