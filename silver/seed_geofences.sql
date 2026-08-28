-- Geocercas: cuadrícula 3x3 sobre el área metropolitana de Cali
-- Cada celda es un rectángulo definido por sus límites geográficos reales.
-- ST_MakeEnvelope(lon_min, lat_min, lon_max, lat_max, SRID) crea un
-- polígono rectangular directamente a partir de las coordenadas límite.

INSERT INTO geofences (name, zone_type, max_speed_kmh, geom) VALUES
('Norte-Oeste',   'urban_perimeter', 60, ST_MakeEnvelope(-76.58, 3.4467, -76.54, 3.52,   4326)),
('Norte-Centro',  'urban_perimeter', 60, ST_MakeEnvelope(-76.54, 3.4467, -76.50, 3.52,   4326)),
('Norte-Este',    'high_risk_zone',  30, ST_MakeEnvelope(-76.50, 3.4467, -76.46, 3.52,   4326)),
('Centro-Oeste',  'urban_perimeter', 60, ST_MakeEnvelope(-76.58, 3.3733, -76.54, 3.4467, 4326)),
('Centro-Centro', 'high_risk_zone',  30, ST_MakeEnvelope(-76.54, 3.3733, -76.50, 3.4467, 4326)),
('Centro-Este',   'urban_perimeter', 60, ST_MakeEnvelope(-76.50, 3.3733, -76.46, 3.4467, 4326)),
('Sur-Oeste',     'urban_perimeter', 60, ST_MakeEnvelope(-76.58, 3.30,   -76.54, 3.3733, 4326)),
('Sur-Centro',    'urban_perimeter', 60, ST_MakeEnvelope(-76.54, 3.30,   -76.50, 3.3733, 4326)),
('Sur-Este',      'restricted_area', 20, ST_MakeEnvelope(-76.50, 3.30,   -76.46, 3.3733, 4326));

SELECT id, name, zone_type, max_speed_kmh, ST_Area(geom) AS area_grados
FROM geofences
ORDER BY id;


SELECT 
    g.name AS geocerca,
    g.zone_type,
    g.max_speed_kmh,
    COUNT(rt.id) AS puntos_dentro
FROM geofences g
LEFT JOIN raw_telemetry rt ON ST_Within(rt.geom, g.geom)
GROUP BY g.id, g.name, g.zone_type, g.max_speed_kmh
ORDER BY puntos_dentro DESC;