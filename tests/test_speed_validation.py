def calculate_speed_excess(recorded_speed, geofence_limit):
    """
    Replica la lógica del trigger: determina si hay exceso de velocidad
    y por cuánto, según el límite específico de la geocerca.
    """
    if recorded_speed <= geofence_limit:
        return None
    return round(recorded_speed - geofence_limit, 2)


def test_speed_within_limit_no_excess():
    """Una velocidad igual o menor al límite no debe generar exceso."""
    assert calculate_speed_excess(recorded_speed=45, geofence_limit=60) is None


def test_speed_exactly_at_limit_no_excess():
    """Caso límite: velocidad exactamente igual al límite no cuenta como exceso."""
    assert calculate_speed_excess(recorded_speed=60, geofence_limit=60) is None


def test_speed_over_limit_calculates_correct_excess():
    """Una velocidad mayor al límite debe calcular el exceso correctamente."""
    assert calculate_speed_excess(recorded_speed=75, geofence_limit=60) == 15.0


def test_speed_limit_adapts_to_different_geofences():
    """
    El mismo valor de velocidad puede o no generar exceso dependiendo
    del límite de la geocerca — valida el comportamiento 'dinámico'
    que exige el enunciado.
    """
    speed = 45
    # En zona de alto riesgo (30 km/h), 45 km/h SÍ es exceso
    assert calculate_speed_excess(speed, geofence_limit=30) == 15.0
    # En zona de perímetro urbano (60 km/h), 45 km/h NO es exceso
    assert calculate_speed_excess(speed, geofence_limit=60) is None