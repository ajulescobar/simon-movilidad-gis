from shapely.geometry import Point, box


def make_geofence(lon_min, lat_min, lon_max, lat_max):
    """
    Crea un polígono rectangular, equivalente a ST_MakeEnvelope de PostGIS.
    """
    return box(lon_min, lat_min, lon_max, lat_max)


def is_point_within_geofence(lat, lon, geofence):
    """
    Verifica si un punto GPS (lat, lon) está dentro de una geocerca.
    Equivalente a ST_Within(punto, geocerca) en PostGIS.
    """
    point = Point(lon, lat)
    return point.within(geofence)


# Geocerca de prueba: replica la zona "Centro-Centro" real del proyecto
CENTRO_CENTRO = make_geofence(-76.54, 3.3733, -76.50, 3.4467)


def test_point_clearly_inside_geofence():
    """Un punto dentro de los límites debe detectarse correctamente."""
    assert is_point_within_geofence(lat=3.41, lon=-76.52, geofence=CENTRO_CENTRO) is True


def test_point_clearly_outside_geofence():
    """Un punto fuera de los límites no debe marcarse como dentro."""
    assert is_point_within_geofence(lat=3.50, lon=-76.60, geofence=CENTRO_CENTRO) is False


def test_point_on_the_edge_of_geofence():
    """
    Caso límite: un punto exactamente sobre el borde del polígono.
    Shapely considera 'within' como estrictamente interior (no incluye el borde),
    igual que el comportamiento de ST_Within en PostGIS.
    """
    edge_point = Point(-76.54, 3.41)  # exactamente sobre el límite oeste
    assert edge_point.within(CENTRO_CENTRO) is False


def test_point_far_away_different_hemisphere():
    """Un punto en coordenadas completamente distintas nunca debe coincidir."""
    assert is_point_within_geofence(lat=-33.45, lon=-70.65, geofence=CENTRO_CENTRO) is False  # Santiago de Chile


def test_geofence_covers_expected_area():
    """Verifica que el polígono generado tenga los límites esperados."""
    assert CENTRO_CENTRO.bounds == (-76.54, 3.3733, -76.50, 3.4467)