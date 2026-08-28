import requests
import numpy as np

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"


def generate_route_osrm(origin, destination, timeout=5):
    """
    Genera una ruta entre dos puntos usando OSRM.
    """
    lat1, lon1 = origin
    lat2, lon2 = destination

    url = f"{OSRM_BASE_URL}/{lon1},{lat1};{lon2},{lat2}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok":
            return None

        # GeoJSON viene como [lon, lat], lo invertimos a (lat, lon)
        coords = data["routes"][0]["geometry"]["coordinates"]
        route = [(lat, lon) for lon, lat in coords]
        return route

    except (requests.RequestException, KeyError, IndexError):
        return None


def generate_route_fallback(origin, destination, num_points=20):
    """
    Genera una ruta interpolando linealmente entre origen y destino.
    """
    lat1, lon1 = origin
    lat2, lon2 = destination

    lats = np.linspace(lat1, lat2, num_points)
    lons = np.linspace(lon1, lon2, num_points)

    return list(zip(lats, lons))


def generate_route(origin, destination, num_points=20):
    """
    Punto de entrada único: intenta OSRM primero, y si falla,
    recurre al fallback. Retorna la ruta junto con la fuente usada.
    """
    route = generate_route_osrm(origin, destination)
    if route is not None:
        return {"route": route, "route_source": "osrm"}

    route = generate_route_fallback(origin, destination, num_points)
    return {"route": route, "route_source": "interpolated_fallback"}