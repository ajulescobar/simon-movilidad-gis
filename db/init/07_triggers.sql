-- Capa Plata: Automatización con triggers
-- Cada vez que se inserta un nuevo reporte de telemetría, se ejecuta
-- automáticamente la detección de geocerca, exceso de velocidad y
-- alerta de combustible — sin depender de un proceso batch externo.

CREATE OR REPLACE FUNCTION process_telemetry_alerts()
RETURNS TRIGGER AS $$
DECLARE
    matched_geofence RECORD;
    autonomy_km NUMERIC;
BEGIN
    -- 1. Buscar si el nuevo punto cae dentro de alguna geocerca
    SELECT id, name, max_speed_kmh
    INTO matched_geofence
    FROM geofences
    WHERE ST_Within(NEW.geom, geom)
    LIMIT 1;

    -- 2. Si está dentro de una geocerca y excede su límite, generar alerta de velocidad
    IF matched_geofence.id IS NOT NULL AND NEW.speed_kmh > matched_geofence.max_speed_kmh THEN
        INSERT INTO speed_alerts (telemetry_id, geofence_id, vehicle_id, speed_recorded, speed_limit, excess_kmh)
        VALUES (
            NEW.id,
            matched_geofence.id,
            NEW.vehicle_id,
            NEW.speed_kmh,
            matched_geofence.max_speed_kmh,
            ROUND(NEW.speed_kmh - matched_geofence.max_speed_kmh, 2)
        );
    END IF;

    -- 3. Calcular autonomía estimada y generar alerta de combustible si aplica
    autonomy_km := ROUND((NEW.fuel_level / 100.0) * 400, 2);

    IF autonomy_km < 100 THEN
        INSERT INTO fuel_alerts (telemetry_id, vehicle_id, fuel_level, estimated_autonomy_km)
        VALUES (NEW.id, NEW.vehicle_id, NEW.fuel_level, autonomy_km);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- El trigger que dispara la función después de cada inserción
CREATE TRIGGER trg_process_telemetry_alerts
AFTER INSERT ON raw_telemetry
FOR EACH ROW
EXECUTE FUNCTION process_telemetry_alerts();