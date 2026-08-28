AUTONOMIA_TOTAL_KM = 400
UMBRAL_ALERTA_KM = 100


def calculate_autonomy(fuel_level_percent, autonomy_total_km=AUTONOMIA_TOTAL_KM):
    """
    Replica la lógica del trigger SQL en Python para poder testearla
    de forma aislada y rápida, sin necesitar conexión a la base de datos.
    """
    return round((fuel_level_percent / 100.0) * autonomy_total_km, 2)


def is_fuel_alert(fuel_level_percent, threshold_km=UMBRAL_ALERTA_KM):
    """Determina si el nivel de combustible actual dispara una alerta."""
    return calculate_autonomy(fuel_level_percent) < threshold_km


def test_full_tank_gives_full_autonomy():
    """Con 100% de combustible, la autonomía debe ser igual al total configurado."""
    assert calculate_autonomy(100) == 400.0


def test_empty_tank_gives_zero_autonomy():
    """Con 0% de combustible, la autonomía debe ser exactamente 0."""
    assert calculate_autonomy(0) == 0.0


def test_half_tank_gives_half_autonomy():
    """Con 50% de combustible, la autonomía debe ser la mitad del total."""
    assert calculate_autonomy(50) == 200.0


def test_low_fuel_triggers_alert():
    """Un nivel de combustible que resulte en menos de 100 km debe generar alerta."""
    assert is_fuel_alert(20) is True


def test_sufficient_fuel_does_not_trigger_alert():
    """Un nivel de combustible con suficiente autonomía no debe generar alerta."""
    assert is_fuel_alert(30) is False


def test_alert_boundary_exact_threshold():
    """
    Caso límite: exactamente en el umbral (100 km) NO debe generar alerta,
    porque la condición del trigger es '< 100', estrictamente menor.
    """
    # 25% de 400 km = exactamente 100 km
    assert is_fuel_alert(25) is False