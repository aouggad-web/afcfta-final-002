-- =============================================================================
-- AfCFTA Platform - Advanced Database Indexes for Performance Optimization
-- Supports 50+ country scale with sub-100ms query response times
-- =============================================================================

-- Composite index for frequent tariff lookups (country + HS code + effective date)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tariffs_performance
    ON tariffs (country_code, hs_code, effective_date DESC)
    WHERE active = true;

-- Full-text search index for investment zones
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_investment_zones_search
    ON investment_zones
    USING GIN (to_tsvector('english', zone_name || ' ' || description));

-- Trade routes optimization index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trade_routes_optimization
    ON trade_data (origin_country, destination_country, product_code, trade_year);

-- HS code description full-text search index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hs_codes_fulltext
    ON hs_codes
    USING GIN (to_tsvector('english', description_en || ' ' || COALESCE(description_fr, '')));

-- Country code index for fast lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countries_iso
    ON countries (iso_code)
    WHERE active = true;

-- Regional bloc index for regional analytics
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_countries_regional_bloc
    ON countries (regional_bloc, iso_code);

-- Investment zones by country for investment intelligence
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_investment_zones_country
    ON investment_zones (country_code, zone_type, investment_score DESC);

-- Tariff effective date range index for historical queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tariffs_date_range
    ON tariffs (effective_date DESC, expiry_date)
    WHERE active = true;

-- Trade value index for analytics aggregations
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trade_data_value
    ON trade_data (trade_year DESC, origin_country, trade_value_usd DESC);

-- Rules of origin compound index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_rules_of_origin_hs
    ON rules_of_origin (hs_chapter, hs_code, country_group);

-- Investment scoring composite index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_investment_scores_composite
    ON investment_scores (country_code, sector, score DESC, updated_at DESC);

-- User saved searches index
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_saved_searches_user
    ON saved_searches (user_id, created_at DESC)
    WHERE active = true;

-- Notifications index for real-time delivery
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_notifications_delivery
    ON notifications (user_id, delivered, created_at DESC)
    WHERE delivered = false;

-- =============================================================================
-- Partial indexes for common filter patterns
-- =============================================================================

-- Active tariff lines only (most queries filter on active=true)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tariffs_active_country_hs
    ON tariffs (country_code, hs_code)
    WHERE active = true;

-- High-value trade corridors
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_trade_corridors_high_value
    ON trade_data (origin_country, destination_country, trade_value_usd DESC)
    WHERE trade_value_usd > 1000000;

-- Verified investment zones only
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_investment_zones_verified
    ON investment_zones (country_code, zone_type)
    WHERE verified = true AND active = true;
