-- Capa Oro: Vista consolidada para consumo de Business Intelligence

CREATE VIEW vehicle_analytics_gold AS
SELECT
    rt.id AS telemetry_id,
    rt.vehicle_id,
    rt.reported_at,
    rt.speed_kmh,
    rt.fuel_level,
    ST_X(rt.geom) AS longitude,
    ST_Y(rt.geom) AS latitude,
    g.name AS geofence_name,
    g.zone_type,
    g.max_speed_kmh AS geofence_speed_limit,
    (sa.id IS NOT NULL) AS has_speed_alert,
    sa.excess_kmh AS speed_excess_kmh,
    (fa.id IS NOT NULL) AS has_fuel_alert,
    fa.estimated_autonomy_km
FROM raw_telemetry rt
LEFT JOIN geofences g ON ST_Within(rt.geom, g.geom)
LEFT JOIN speed_alerts sa ON sa.telemetry_id = rt.id
LEFT JOIN fuel_alerts fa ON fa.telemetry_id = rt.id;


SELECT vehicle_id, geofence_name, zone_type, speed_kmh, 
       has_speed_alert, has_fuel_alert
FROM vehicle_analytics_gold
WHERE has_speed_alert = true OR has_fuel_alert = true
LIMIT 10;