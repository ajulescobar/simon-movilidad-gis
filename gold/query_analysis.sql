-- ============================================
-- Análisis de rendimiento: uso de índices espaciales GiST
-- ============================================

EXPLAIN ANALYZE
SELECT rt.id, rt.vehicle_id, g.name
FROM raw_telemetry rt
JOIN geofences g ON ST_Within(rt.geom, g.geom);

/*
QUERY PLAN                                                                                                                                      |
------------------------------------------------------------------------------------------------------------------------------------------------+
Nested Loop  (cost=0.14..2744.80 rows=162 width=239) (actual time=0.081..0.625 rows=775 loops=1)                                                |
  ->  Seq Scan on geofences g  (cost=0.00..12.10 rows=210 width=250) (actual time=0.009..0.011 rows=9 loops=1)                                  |
  ->  Index Scan using idx_raw_telemetry_geom on raw_telemetry rt  (cost=0.14..13.00 rows=1 width=53) (actual time=0.010..0.061 rows=86 loops=9)|
        Index Cond: (geom @ g.geom)                                                                                                             |
        Filter: st_within(geom, g.geom)                                                                                                         |
Planning Time: 0.229 ms                                                                                                                         |
Execution Time: 0.666 ms                                                                                                                        |
*/

-- ============================================
-- Comparación: rendimiento SIN índice GiST (forzado)
-- ============================================

SET enable_indexscan = off;
SET enable_bitmapscan = off;

EXPLAIN ANALYZE
SELECT rt.id, rt.vehicle_id, g.name
FROM raw_telemetry rt
JOIN geofences g ON ST_Within(rt.geom, g.geom);

SET enable_indexscan = on;
SET enable_bitmapscan = on;

/*
QUERY PLAN                                                                                                            |
----------------------------------------------------------------------------------------------------------------------+
Nested Loop  (cost=0.00..2031186.48 rows=162 width=239) (actual time=59.381..60.841 rows=775 loops=1)                 |
  Join Filter: st_within(rt.geom, g.geom)                                                                             |
  Rows Removed by Join Filter: 6200                                                                                   |
  ->  Seq Scan on raw_telemetry rt  (cost=0.00..19.73 rows=773 width=53) (actual time=0.014..0.067 rows=775 loops=1)  |
  ->  Materialize  (cost=0.00..13.15 rows=210 width=250) (actual time=0.077..0.077 rows=9 loops=775)                  |
        ->  Seq Scan on geofences g  (cost=0.00..12.10 rows=210 width=250) (actual time=59.336..59.341 rows=9 loops=1)|
Planning Time: 0.217 ms                                                                                               |
JIT:                                                                                                                  |
  Functions: 8                                                                                                        |
  Options: Inlining true, Optimization true, Expressions true, Deforming true                                         |
  Timing: Generation 1.423 ms, Inlining 2.163 ms, Optimization 34.276 ms, Emission 22.880 ms, Total 60.741 ms         |
Execution Time: 62.372 ms                                                                                             |
*/