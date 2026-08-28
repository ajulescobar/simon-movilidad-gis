-- Vista con enmascaramiento del vehicle_id para usuarios no administradores
CREATE VIEW telemetry_masked AS
SELECT
    id,
    CASE 
        WHEN LENGTH(vehicle_id) >= 8 THEN 
            LEFT(vehicle_id, 4) || '****' || RIGHT(vehicle_id, 4)
        ELSE 
            vehicle_id
    END AS vehicle_id,
    reported_at,
    speed_kmh,
    fuel_level,
    geom,
    created_at
FROM raw_telemetry;

-- Rol administrador: acceso completo a datos crudos (sin enmascarar)
CREATE ROLE gis_admin WITH LOGIN PASSWORD 'admin_pass123';
GRANT SELECT, INSERT, UPDATE ON raw_telemetry TO gis_admin;

-- Rol de solo lectura: solo puede ver la vista enmascarada
CREATE ROLE gis_readonly WITH LOGIN PASSWORD 'readonly_pass123';
GRANT SELECT ON telemetry_masked TO gis_readonly;