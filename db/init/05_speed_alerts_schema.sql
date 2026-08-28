-- Capa Plata: Alertas de exceso de velocidad
-- Se genera un registro cada vez que un punto de telemetría excede
-- el límite de velocidad de la geocerca donde se encuentra.

CREATE TABLE speed_alerts (
    id BIGSERIAL PRIMARY KEY,
    telemetry_id BIGINT NOT NULL REFERENCES raw_telemetry(id),
    geofence_id BIGINT NOT NULL REFERENCES geofences(id),
    vehicle_id VARCHAR(20) NOT NULL,
    speed_recorded NUMERIC(5,2) NOT NULL,
    speed_limit NUMERIC(5,2) NOT NULL,
    excess_kmh NUMERIC(5,2) NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_actual_excess CHECK (excess_kmh > 0)
);

CREATE INDEX idx_speed_alerts_vehicle ON speed_alerts (vehicle_id, detected_at DESC);
CREATE INDEX idx_speed_alerts_telemetry ON speed_alerts (telemetry_id);

INSERT INTO speed_alerts (telemetry_id, geofence_id, vehicle_id, speed_recorded, speed_limit, excess_kmh)
SELECT 
    rt.id,
    g.id,
    rt.vehicle_id,
    rt.speed_kmh,
    g.max_speed_kmh,
    ROUND(rt.speed_kmh - g.max_speed_kmh, 2)
FROM raw_telemetry rt
JOIN geofences g ON ST_Within(rt.geom, g.geom)
WHERE rt.speed_kmh > g.max_speed_kmh;


SELECT vehicle_id, COUNT(*) AS total_alertas, ROUND(AVG(excess_kmh), 2) AS exceso_promedio
FROM speed_alerts
GROUP BY vehicle_id
ORDER BY total_alertas DESC;