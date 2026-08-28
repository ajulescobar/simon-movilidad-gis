-- Capa Plata: Geocercas (zonas geográficas para detección de infracciones)
-- Cada polígono representa una zona con su propio límite de velocidad permitido

CREATE TABLE geofences (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    zone_type VARCHAR(30) NOT NULL CHECK (zone_type IN ('urban_perimeter', 'high_risk_zone', 'restricted_area')),
    max_speed_kmh NUMERIC(5,2) NOT NULL CHECK (max_speed_kmh > 0),
    geom GEOMETRY(Polygon, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_valid_geofence_geom CHECK (ST_IsValid(geom))
);

CREATE INDEX idx_geofences_geom ON geofences USING GIST (geom);