-- Capa Bronce: Tabla de telemetría cruda (datos GPS sin procesar)
-- Cada fila representa un reporte puntual de un dispositivo IoT/AVL

CREATE TABLE raw_telemetry (
    id BIGSERIAL PRIMARY KEY,
    vehicle_id VARCHAR(20) NOT NULL,
    reported_at TIMESTAMPTZ NOT NULL,
    speed_kmh NUMERIC(5,2) NOT NULL CHECK (speed_kmh >= 0 AND speed_kmh <= 300),
    fuel_level NUMERIC(5,2) NOT NULL CHECK (fuel_level BETWEEN 0 AND 100),
    geom GEOMETRY(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_valid_geom CHECK (ST_IsValid(geom))
);

CREATE INDEX idx_raw_telemetry_geom ON raw_telemetry USING GIST (geom);
CREATE INDEX idx_raw_telemetry_vehicle_time ON raw_telemetry (vehicle_id, reported_at DESC);