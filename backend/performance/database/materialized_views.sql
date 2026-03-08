-- =============================================================================
-- AfCFTA Platform - Materialized Views for Complex Analytics
-- Pre-computed aggregations for sub-100ms regional analytics queries
-- =============================================================================

-- =============================================================================
-- Regional analytics materialized view
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_regional_analytics AS
SELECT
    r.regional_bloc,
    r.country_count,
    AVG(t.tariff_rate)              AS avg_tariff,
    COUNT(DISTINCT iz.zone_id)      AS investment_zones,
    SUM(td.trade_value_usd)         AS total_trade_value,
    AVG(iz.investment_score)        AS avg_investment_score,
    COUNT(DISTINCT c.iso_code)      AS active_countries
FROM regions r
LEFT JOIN countries c          ON r.regional_bloc = c.regional_bloc AND c.active = true
LEFT JOIN tariffs t             ON c.iso_code = t.country_code AND t.active = true
LEFT JOIN investment_zones iz   ON c.iso_code = iz.country_code AND iz.active = true
LEFT JOIN trade_data td         ON c.iso_code = td.origin_country
    AND td.trade_year = EXTRACT(YEAR FROM CURRENT_DATE) - 1
GROUP BY r.regional_bloc, r.country_count;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_regional_analytics_bloc
    ON mv_regional_analytics (regional_bloc);

-- =============================================================================
-- Country investment summary materialized view
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_country_investment_summary AS
SELECT
    c.iso_code,
    c.country_name_en,
    c.regional_bloc,
    COUNT(DISTINCT iz.zone_id)                          AS total_investment_zones,
    AVG(iz.investment_score)                            AS avg_investment_score,
    MAX(iz.investment_score)                            AS max_investment_score,
    SUM(CASE WHEN iz.zone_type = 'SEZ' THEN 1 ELSE 0 END)  AS sez_count,
    SUM(CASE WHEN iz.zone_type = 'FTZ' THEN 1 ELSE 0 END)  AS ftz_count,
    MIN(t.tariff_rate)                                  AS min_tariff_rate,
    AVG(t.tariff_rate)                                  AS avg_tariff_rate,
    COUNT(DISTINCT t.hs_code)                           AS tariff_lines_count,
    td_out.total_exports,
    td_in.total_imports
FROM countries c
LEFT JOIN investment_zones iz ON c.iso_code = iz.country_code AND iz.active = true
LEFT JOIN tariffs t           ON c.iso_code = t.country_code AND t.active = true
LEFT JOIN (
    SELECT origin_country, SUM(trade_value_usd) AS total_exports
    FROM trade_data
    WHERE trade_year = EXTRACT(YEAR FROM CURRENT_DATE) - 1
    GROUP BY origin_country
) td_out ON c.iso_code = td_out.origin_country
LEFT JOIN (
    SELECT destination_country, SUM(trade_value_usd) AS total_imports
    FROM trade_data
    WHERE trade_year = EXTRACT(YEAR FROM CURRENT_DATE) - 1
    GROUP BY destination_country
) td_in ON c.iso_code = td_in.destination_country
WHERE c.active = true
GROUP BY c.iso_code, c.country_name_en, c.regional_bloc,
         td_out.total_exports, td_in.total_imports;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_country_investment_iso
    ON mv_country_investment_summary (iso_code);

CREATE INDEX IF NOT EXISTS idx_mv_country_investment_score
    ON mv_country_investment_summary (avg_investment_score DESC);

-- =============================================================================
-- Trade corridor analytics materialized view
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_trade_corridors AS
SELECT
    td.origin_country,
    td.destination_country,
    co.country_name_en  AS origin_name,
    cd.country_name_en  AS destination_name,
    co.regional_bloc    AS origin_bloc,
    cd.regional_bloc    AS destination_bloc,
    SUM(td.trade_value_usd)     AS total_trade_value,
    AVG(td.trade_value_usd)     AS avg_annual_trade,
    COUNT(DISTINCT td.product_code) AS product_diversity,
    MAX(td.trade_year)          AS latest_year
FROM trade_data td
JOIN countries co ON td.origin_country = co.iso_code
JOIN countries cd ON td.destination_country = cd.iso_code
GROUP BY td.origin_country, td.destination_country,
         co.country_name_en, cd.country_name_en,
         co.regional_bloc, cd.regional_bloc;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_trade_corridors_pair
    ON mv_trade_corridors (origin_country, destination_country);

CREATE INDEX IF NOT EXISTS idx_mv_trade_corridors_value
    ON mv_trade_corridors (total_trade_value DESC);

-- =============================================================================
-- HS code popularity view (hot data candidate for L1 cache)
-- =============================================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hs_code_popularity AS
SELECT
    hs.hs_code,
    hs.description_en,
    hs.description_fr,
    hs.chapter,
    COUNT(DISTINCT t.country_code)  AS countries_with_tariff,
    AVG(t.tariff_rate)              AS avg_global_tariff,
    COUNT(DISTINCT td.origin_country) AS active_trading_countries
FROM hs_codes hs
LEFT JOIN tariffs t   ON hs.hs_code = t.hs_code AND t.active = true
LEFT JOIN trade_data td ON hs.hs_code = td.product_code
GROUP BY hs.hs_code, hs.description_en, hs.description_fr, hs.chapter
ORDER BY active_trading_countries DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_hs_popularity_code
    ON mv_hs_code_popularity (hs_code);

-- =============================================================================
-- Refresh function with dependency ordering
-- =============================================================================
CREATE OR REPLACE FUNCTION refresh_all_materialized_views()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_regional_analytics;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_country_investment_summary;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_trade_corridors;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_hs_code_popularity;
END;
$$ LANGUAGE plpgsql;

-- Schedule hourly refresh (requires pg_cron extension):
-- SELECT cron.schedule('refresh-mv', '0 * * * *', 'SELECT refresh_all_materialized_views()');
