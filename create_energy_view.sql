-- Energy Records View for Dashboard Compatibility
-- Creates a view to bridge IoT energy_records table to dashboard metrics API

USE test_tanaka;

-- Create monthly energy view
CREATE OR REPLACE VIEW energy_monthly_view AS
SELECT 
    DATE_FORMAT(`timestamp`,'%Y-%m') AS ym,
    YEAR(`timestamp`) AS year,
    MONTH(`timestamp`) AS month,
    user_id,
    SUM(energy_consumed) AS electricity_kwh,
    SUM(energy_produced) AS electricity_produced_kwh,
    -- Convert to CO2 using standard factors
    SUM(energy_consumed) * 0.000518 AS co2_reduction_kg,
    COUNT(*) AS record_count
FROM energy_records
WHERE `timestamp` IS NOT NULL
GROUP BY ym, user_id;

-- Create daily energy view for more granular analysis
CREATE OR REPLACE VIEW energy_daily_view AS  
SELECT
    DATE(`timestamp`) AS date,
    user_id,
    SUM(energy_consumed) AS electricity_kwh,
    SUM(energy_produced) AS electricity_produced_kwh,
    SUM(energy_consumed) * 0.000518 AS co2_reduction_kg
FROM energy_records
WHERE `timestamp` IS NOT NULL  
GROUP BY DATE(`timestamp`), user_id;