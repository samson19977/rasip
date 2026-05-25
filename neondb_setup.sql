-- ================================================================
-- RASIP — Rwanda Agricultural Spatial Intelligence Platform
-- NeonDB Setup SQL
-- Run this entire script in the NeonDB SQL Editor
-- ================================================================

-- ── 1. DROP old tables (clean start) ───────────────────────────
DROP TABLE IF EXISTS similarity_cache CASCADE;
DROP TABLE IF EXISTS climate_forecasts CASCADE;
DROP TABLE IF EXISTS climate_records CASCADE;
DROP TABLE IF EXISTS predictions CASCADE;
DROP TABLE IF EXISTS crop_trials CASCADE;
DROP TABLE IF EXISTS delivery_routes CASCADE;
DROP TABLE IF EXISTS districts CASCADE;

-- ── 2. CREATE TABLES ────────────────────────────────────────────

CREATE TABLE districts (
    id                    SERIAL PRIMARY KEY,
    name                  VARCHAR(100) UNIQUE NOT NULL,
    province              VARCHAR(50) NOT NULL,
    centroid_lat          FLOAT,
    centroid_lon          FLOAT,
    elevation_mean        FLOAT,
    elevation_min         FLOAT,
    elevation_max         FLOAT,
    slope_mean            FLOAT,
    area_km2              FLOAT,
    rainfall_annual_mm    FLOAT,
    rainfall_cv           FLOAT,
    temp_mean_c           FLOAT,
    temp_min_c            FLOAT,
    temp_max_c            FLOAT,
    humidity_pct          FLOAT,
    sunshine_hours_annual FLOAT,
    soil_type             VARCHAR(50),
    soil_ph               FLOAT,
    soil_organic_matter   FLOAT,
    soil_nitrogen         FLOAT,
    ndvi_mean             FLOAT,
    ndvi_trend            FLOAT,
    ndvi_std              FLOAT,
    flood_risk_score      FLOAT,
    drought_risk_score    FLOAT,
    soil_degradation_score FLOAT,
    avg_maize_yield       FLOAT,
    avg_potato_yield      FLOAT,
    avg_bean_yield        FLOAT,
    avg_coffee_yield      FLOAT,
    avg_tea_yield         FLOAT,
    coffee_suitable       BOOLEAN DEFAULT FALSE,
    tea_suitable          BOOLEAN DEFAULT FALSE,
    banana_suitable       BOOLEAN DEFAULT FALSE,
    created_at            TIMESTAMP DEFAULT NOW(),
    updated_at            TIMESTAMP DEFAULT NOW()
);

CREATE TABLE crop_trials (
    id                  SERIAL PRIMARY KEY,
    district_id         INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    crop                VARCHAR(50) NOT NULL,
    variety             VARCHAR(100) NOT NULL,
    season              VARCHAR(20),
    year                INTEGER,
    soil_ph_trial       FLOAT,
    rainfall_season_mm  FLOAT,
    temp_mean_trial     FLOAT,
    humidity_trial      FLOAT,
    ndvi_at_planting    FLOAT,
    irrigation          VARCHAR(20) DEFAULT 'rainfed',
    fertilizer          VARCHAR(100),
    yield_t_ha          FLOAT,
    performance_score   FLOAT,
    disease_incidence   FLOAT,
    notes               TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE predictions (
    id                      SERIAL PRIMARY KEY,
    district_id             INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    crop                    VARCHAR(50),
    variety                 VARCHAR(100),
    suitability_score       FLOAT,
    yield_prediction_t_ha   FLOAT,
    risk_level              VARCHAR(20),
    confidence              FLOAT,
    shap_values_json        JSONB,
    recommendation          TEXT,
    model_version           VARCHAR(20) DEFAULT '2.0.0',
    created_at              TIMESTAMP DEFAULT NOW()
);

CREATE TABLE climate_records (
    id                  SERIAL PRIMARY KEY,
    district_id         INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    year                INTEGER NOT NULL,
    month               INTEGER NOT NULL,
    rainfall_mm         FLOAT,
    temp_mean_c         FLOAT,
    temp_max_c          FLOAT,
    temp_min_c          FLOAT,
    humidity_pct        FLOAT,
    ndvi                FLOAT,
    sunshine_hours      FLOAT,
    drought_score       FLOAT,
    heat_stress_score   FLOAT,
    flood_risk_score    FLOAT,
    created_at          TIMESTAMP DEFAULT NOW(),
    UNIQUE(district_id, year, month)
);

CREATE TABLE climate_forecasts (
    id                          SERIAL PRIMARY KEY,
    district_id                 INTEGER REFERENCES districts(id) ON DELETE CASCADE,
    forecast_for_year           INTEGER,
    forecast_for_month          INTEGER,
    predicted_rainfall_mm       FLOAT,
    predicted_temp_mean_c       FLOAT,
    drought_probability         FLOAT,
    flood_probability           FLOAT,
    crop_failure_probability    FLOAT,
    harvest_quality_score       FLOAT,
    model_used                  VARCHAR(50),
    confidence_interval_low     FLOAT,
    confidence_interval_high    FLOAT,
    created_at                  TIMESTAMP DEFAULT NOW(),
    UNIQUE(district_id, forecast_for_year, forecast_for_month)
);

CREATE TABLE similarity_cache (
    id              SERIAL PRIMARY KEY,
    district_a_id   INTEGER REFERENCES districts(id),
    district_b_id   INTEGER REFERENCES districts(id),
    similarity_score FLOAT,
    method          VARCHAR(30) DEFAULT 'cosine',
    feature_set     VARCHAR(50) DEFAULT 'full_v2',
    computed_at     TIMESTAMP DEFAULT NOW(),
    UNIQUE(district_a_id, district_b_id, method, feature_set)
);

-- ── 3. INDEXES ──────────────────────────────────────────────────
CREATE INDEX idx_districts_province    ON districts(province);
CREATE INDEX idx_crop_trials_district  ON crop_trials(district_id);
CREATE INDEX idx_predictions_district  ON predictions(district_id);
CREATE INDEX idx_climate_district_year ON climate_records(district_id, year);

-- ── 4. SEED ALL 30 RWANDA DISTRICTS ────────────────────────────

INSERT INTO districts (name,province,centroid_lat,centroid_lon,elevation_mean,elevation_min,elevation_max,slope_mean,area_km2,rainfall_annual_mm,rainfall_cv,temp_mean_c,temp_min_c,temp_max_c,humidity_pct,sunshine_hours_annual,soil_type,soil_ph,soil_organic_matter,soil_nitrogen,ndvi_mean,ndvi_trend,ndvi_std,flood_risk_score,drought_risk_score,soil_degradation_score,avg_maize_yield,avg_potato_yield,avg_bean_yield,avg_coffee_yield,avg_tea_yield,coffee_suitable,tea_suitable,banana_suitable) VALUES

-- NORTHERN PROVINCE
('Musanze','Northern',-1.4996,29.6340,1870,1600,4507,15.3,583,1340,0.22,15.5,10.0,23.0,78,1820,'Andosol',6.2,4.5,0.35,0.62,0.02,0.08,18,12,15,4.2,18.5,1.8,1.1,2.3,TRUE,TRUE,TRUE),
('Burera','Northern',-1.3697,29.8167,1650,1400,2400,12.0,632,960,0.35,17.8,12.0,25.0,65,1950,'Cambisol',5.5,3.2,0.25,0.44,-0.02,0.11,22,38,28,3.1,14.2,1.5,0.9,1.8,TRUE,FALSE,TRUE),
('Gakenke','Northern',-1.6895,29.7810,1750,1500,2500,18.2,735,1100,0.28,16.8,11.5,24.0,72,1870,'Andosol',5.9,3.8,0.30,0.54,0.01,0.09,30,20,35,3.8,16.0,1.6,1.0,2.1,TRUE,TRUE,TRUE),
('Gicumbi','Northern',-1.5746,30.0698,1800,1550,2600,14.5,853,1050,0.30,16.2,11.0,23.5,70,1900,'Cambisol',5.7,3.5,0.28,0.50,0.00,0.10,25,28,30,3.5,15.5,1.7,0.95,1.9,TRUE,TRUE,FALSE),
('Rulindo','Northern',-1.7339,29.9876,1700,1400,2300,16.0,568,1080,0.27,17.0,12.0,24.5,68,1920,'Ferralsol',5.8,3.0,0.24,0.48,-0.01,0.10,20,32,22,3.3,14.8,1.6,1.05,2.0,TRUE,TRUE,TRUE),

-- SOUTHERN PROVINCE
('Gisagara','Southern',-2.6167,29.8500,1450,1200,2100,10.5,748,1050,0.31,19.5,14.0,27.0,66,2050,'Ferralsol',5.6,2.5,0.20,0.41,-0.01,0.12,35,40,42,3.2,11.0,1.4,0.8,1.2,TRUE,FALSE,TRUE),
('Huye','Southern',-2.5922,29.7462,1580,1350,2200,9.8,583,1200,0.25,18.3,13.5,25.5,72,1980,'Cambisol',6.0,3.1,0.26,0.52,0.01,0.09,22,25,28,3.8,13.5,1.7,1.0,1.8,TRUE,TRUE,TRUE),
('Kamonyi','Southern',-2.0333,29.8667,1520,1300,1900,8.5,601,1150,0.26,19.0,14.5,26.0,68,2000,'Lixisol',6.1,2.8,0.23,0.47,0.00,0.11,38,30,32,3.6,12.8,1.6,0.75,0.5,FALSE,FALSE,TRUE),
('Muhanga','Southern',-2.1000,29.7500,1600,1400,2100,11.0,502,1180,0.24,18.0,13.0,25.0,71,1960,'Andosol',6.0,3.4,0.27,0.51,0.01,0.08,20,22,25,3.9,15.0,1.8,0.95,1.5,TRUE,TRUE,TRUE),
('Nyamagabe','Southern',-2.4167,29.4833,1900,1600,2800,19.0,1271,1400,0.20,14.5,9.0,22.0,80,1780,'Andosol',5.8,5.0,0.40,0.65,0.02,0.07,15,8,12,3.0,21.0,1.5,1.4,3.5,TRUE,TRUE,FALSE),
('Nyanza','Southern',-2.3500,29.7500,1480,1300,2000,9.2,726,1000,0.32,19.8,15.0,27.5,63,2100,'Lixisol',5.9,2.4,0.19,0.39,-0.02,0.13,42,45,48,3.0,10.5,1.3,0.7,0.4,FALSE,FALSE,TRUE),
('Nyaruguru','Southern',-2.7167,29.6333,1820,1500,2600,17.5,1551,1250,0.23,16.0,10.5,23.5,75,1830,'Andosol',5.7,4.2,0.33,0.59,0.01,0.08,18,15,20,3.4,18.0,1.7,1.2,2.8,TRUE,TRUE,TRUE),
('Ruhango','Southern',-2.2167,29.7833,1500,1300,1900,8.0,683,1100,0.28,19.2,14.5,26.5,67,2020,'Ferralsol',5.8,2.7,0.22,0.45,-0.01,0.11,32,35,38,3.3,12.0,1.5,0.8,0.8,FALSE,FALSE,TRUE),

-- EASTERN PROVINCE
('Bugesera','Eastern',-2.1989,30.1581,1370,1200,1600,5.0,1338,850,0.40,21.5,16.0,30.0,58,2200,'Lixisol',5.4,1.8,0.15,0.32,-0.03,0.15,55,62,58,2.8,8.0,1.2,0.5,0.0,FALSE,FALSE,TRUE),
('Gatsibo','Eastern',-1.5804,30.4678,1380,1200,1700,4.5,1541,920,0.38,21.0,16.0,29.5,60,2150,'Ferralsol',5.5,1.9,0.16,0.35,0.00,0.13,45,55,48,3.0,9.0,1.3,0.0,0.0,FALSE,FALSE,TRUE),
('Kayonza','Eastern',-1.8781,30.6447,1420,1250,1750,3.8,1754,900,0.42,21.8,16.5,30.5,56,2250,'Lixisol',5.3,1.6,0.14,0.30,-0.02,0.15,42,65,60,2.5,7.5,1.1,0.0,0.0,FALSE,FALSE,TRUE),
('Kirehe','Eastern',-2.2622,30.6761,1440,1300,1800,5.5,1551,980,0.35,20.5,15.5,29.0,61,2100,'Ferralsol',5.6,2.0,0.17,0.36,0.00,0.13,50,52,52,3.1,9.5,1.4,0.0,0.0,FALSE,FALSE,TRUE),
('Ngoma','Eastern',-2.1539,30.4556,1410,1250,1700,4.2,1275,930,0.37,21.2,16.0,29.5,59,2180,'Lixisol',5.5,1.8,0.15,0.33,-0.01,0.14,48,58,55,2.9,8.5,1.2,0.0,0.0,FALSE,FALSE,TRUE),
('Nyagatare','Eastern',-1.3000,30.3167,1500,1350,1900,3.5,3525,800,0.45,22.0,17.0,31.0,55,2300,'Cambisol',6.0,2.2,0.18,0.38,0.01,0.12,38,70,45,3.5,10.0,1.5,0.0,0.0,FALSE,FALSE,TRUE),
('Rwamagana','Eastern',-1.9500,30.4333,1460,1300,1800,4.8,716,1050,0.30,20.3,15.5,28.5,64,2050,'Ferralsol',5.7,2.3,0.19,0.42,0.00,0.12,40,42,40,3.2,11.5,1.4,0.6,0.0,FALSE,FALSE,TRUE),

-- WESTERN PROVINCE
('Karongi','Western',-2.0000,29.4167,1620,1400,2500,16.0,1338,1350,0.21,17.5,12.5,25.0,76,1820,'Andosol',6.1,4.0,0.32,0.60,0.02,0.08,20,12,18,3.7,16.5,1.7,1.2,2.5,TRUE,TRUE,TRUE),
('Ngororero','Western',-1.8818,29.5427,1730,1500,2600,17.2,883,1200,0.24,16.5,11.5,24.0,73,1860,'Andosol',5.9,3.8,0.30,0.55,0.01,0.09,28,18,30,3.6,15.8,1.7,1.0,2.0,TRUE,TRUE,TRUE),
('Nyabihu','Western',-1.5698,29.4832,1760,1500,3100,18.5,563,1280,0.24,16.3,11.0,24.0,75,1840,'Andosol',6.0,4.1,0.30,0.58,0.01,0.09,22,14,20,3.5,17.2,1.7,1.1,2.3,TRUE,TRUE,TRUE),
('Nyamasheke','Western',-2.3167,29.2333,1680,1400,2600,19.5,1529,1450,0.19,17.0,12.0,24.5,79,1790,'Andosol',5.8,4.8,0.38,0.66,0.03,0.07,16,8,14,3.3,19.0,1.6,1.5,3.8,TRUE,TRUE,TRUE),
('Rubavu','Western',-1.6832,29.3489,1540,1463,3000,10.1,440,1100,0.28,19.2,14.0,27.0,70,1930,'Ferralsol',5.8,2.8,0.22,0.48,-0.01,0.11,35,25,28,3.4,13.8,1.6,0.9,1.5,TRUE,TRUE,TRUE),
('Rutsiro','Western',-1.9000,29.4000,1580,1350,2400,13.5,1217,1220,0.26,18.2,13.0,26.0,73,1890,'Andosol',5.9,3.5,0.28,0.54,0.01,0.09,25,20,25,3.6,15.0,1.7,1.0,1.8,TRUE,TRUE,TRUE),

-- KIGALI CITY
('Gasabo','Kigali City',-1.9320,30.1353,1490,1350,1700,7.0,429,1050,0.30,19.5,14.5,27.0,65,2050,'Ferralsol',5.7,2.2,0.18,0.35,-0.02,0.14,52,35,55,2.8,10.0,1.3,0.0,0.0,FALSE,FALSE,TRUE),
('Kicukiro','Kigali City',-1.9833,30.1167,1460,1350,1650,6.5,168,1020,0.32,20.0,15.0,27.5,63,2080,'Ferralsol',5.6,2.0,0.16,0.30,-0.03,0.15,58,38,62,2.5,9.0,1.2,0.0,0.0,FALSE,FALSE,FALSE),
('Nyarugenge','Kigali City',-1.9536,30.0606,1480,1360,1680,8.2,173,1030,0.31,19.8,14.8,27.2,64,2060,'Ferralsol',5.7,2.1,0.17,0.28,-0.04,0.16,60,36,65,2.4,8.5,1.1,0.0,0.0,FALSE,FALSE,FALSE);

-- ── 5. SEED CROP TRIALS ─────────────────────────────────────────

INSERT INTO crop_trials (district_id, crop, variety, season, year, soil_ph_trial, rainfall_season_mm, temp_mean_trial, humidity_trial, ndvi_at_planting, yield_t_ha, performance_score)
SELECT
    d.id,
    t.crop,
    t.variety,
    t.season,
    t.year,
    d.soil_ph,
    d.rainfall_annual_mm / 2,
    d.temp_mean_c,
    d.humidity_pct,
    d.ndvi_mean,
    CASE t.crop
        WHEN 'potato' THEN ROUND((d.avg_potato_yield * (0.9 + random() * 0.2))::numeric, 1)
        WHEN 'maize'  THEN ROUND((d.avg_maize_yield  * (0.9 + random() * 0.2))::numeric, 1)
        WHEN 'bean'   THEN ROUND((d.avg_bean_yield   * (0.9 + random() * 0.2))::numeric, 1)
        WHEN 'coffee' THEN ROUND((d.avg_coffee_yield * (0.9 + random() * 0.2))::numeric, 1)
        ELSE 2.5
    END,
    CASE WHEN d.rainfall_annual_mm > 1100 THEN 80 ELSE 60 END
FROM districts d
CROSS JOIN (VALUES
    ('potato', 'Markies',      'Season A', 2023),
    ('potato', 'Shangi',       'Season B', 2023),
    ('maize',  'DK8031',       'Season A', 2023),
    ('maize',  'RWILI',        'Season B', 2022),
    ('bean',   'Lyamungu',     'Season B', 2022),
    ('bean',   'Urwintore',    'Season A', 2023),
    ('coffee', 'Red Bourbon',  'Annual',   2023)
) AS t(crop, variety, season, year)
WHERE NOT (t.crop = 'coffee' AND d.coffee_suitable = FALSE);

-- ── 6. SEED CLIMATE RECORDS (24 months) ─────────────────────────

INSERT INTO climate_records (district_id, year, month, rainfall_mm, temp_mean_c, temp_max_c, temp_min_c, humidity_pct, ndvi, drought_score, heat_stress_score, flood_risk_score)
SELECT
    d.id,
    yr,
    mo,
    ROUND((d.rainfall_annual_mm / 12 * season_factor * (0.7 + random() * 0.6))::numeric, 1),
    ROUND((d.temp_mean_c + (random() * 3 - 1.5))::numeric, 1),
    ROUND((d.temp_max_c  + (random() * 2 - 1.0))::numeric, 1),
    ROUND((d.temp_min_c  + (random() * 2 - 1.0))::numeric, 1),
    ROUND((d.humidity_pct + (random() * 10 - 5))::numeric, 1),
    ROUND((d.ndvi_mean + (random() * 0.1 - 0.05))::numeric, 3),
    GREATEST(0, LEAST(100, d.drought_risk_score + (random() * 30 - 15))),
    GREATEST(0, (d.temp_mean_c - 20) * 5),
    GREATEST(0, d.flood_risk_score * season_factor * (0.8 + random() * 0.4))
FROM districts d
CROSS JOIN generate_series(2022, 2023) AS yr
CROSS JOIN generate_series(1, 12) AS mo
CROSS JOIN LATERAL (
    SELECT CASE
        WHEN mo IN (3,4,5,9,10,11) THEN 1.3   -- rainy seasons
        ELSE 0.6                                -- dry seasons
    END AS season_factor
) sf
ON CONFLICT (district_id, year, month) DO NOTHING;

-- ── 7. VERIFY ───────────────────────────────────────────────────

SELECT 'districts' AS table_name,    COUNT(*) AS rows FROM districts
UNION ALL
SELECT 'crop_trials',                COUNT(*)         FROM crop_trials
UNION ALL
SELECT 'climate_records',            COUNT(*)         FROM climate_records
ORDER BY table_name;

-- Expected output:
-- climate_records  | 720   (30 districts × 24 months)
-- crop_trials      | ~165  (30 districts × up to 7 crops, minus non-suitable coffee)
-- districts        | 30
