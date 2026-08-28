-- Capa Plata: Alertas de consumo predictivo
-- Se genera una alerta cuando la autonomía restante estimada del vehículo
-- (calculada a partir del nivel de combustible actual) cae por debajo
-- de un umbral de seguridad mínimo.
--
-- Supuesto de diseño: se asume una autonomía total de 400 km con tanque
-- al 100%, un valor representativo para vehículos de flota de reparto/
-- carga liviana. En un sistema real, este valor vendría de la ficha
-- técnica de cada vehículo.

CREATE TABLE fuel_alerts (
    id BIGSERIAL PRIMARY KEY,
    telemetry_id BIGINT NOT NULL REFERENCES raw_telemetry(id),
    vehicle_id VARCHAR(20) NOT NULL,
    fuel_level NUMERIC(5,2) NOT NULL,
    estimated_autonomy_km NUMERIC(7,2) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_low_autonomy CHECK (estimated_autonomy_km >= 0)
);

CREATE INDEX idx_fuel_alerts_vehicle ON fuel_alerts (vehicle_id, detected_at DESC);
CREATE INDEX idx_fuel_alerts_telemetry ON fuel_alerts (telemetry_id);

-- Parámetros de negocio (documentados como constantes de configuración)
-- AUTONOMIA_TOTAL_KM = 400   -> km recorribles con tanque al 100%
-- UMBRAL_ALERTA_KM   = 100   -> por debajo de esto, se considera riesgo

INSERT INTO fuel_alerts (telemetry_id, vehicle_id, fuel_level, estimated_autonomy_km)
SELECT 
    rt.id,
    rt.vehicle_id,
    rt.fuel_level,
    ROUND((rt.fuel_level / 100.0) * 400, 2) AS estimated_autonomy_km
FROM raw_telemetry rt
WHERE (rt.fuel_level / 100.0) * 400 < 50;


SELECT vehicle_id, COUNT(*) AS total_alertas, 
       MIN(estimated_autonomy_km) AS autonomia_minima_detectada
FROM fuel_alerts
GROUP BY vehicle_id
ORDER BY total_alertas DESC;