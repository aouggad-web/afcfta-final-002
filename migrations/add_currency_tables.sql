-- Migration: Add currency and exchange rate tables
-- Supports the AfCFTA currency and exchange rate system

-- ---------------------------------------------------------------------------
-- Currencies table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS currencies (
    code            VARCHAR(3)   PRIMARY KEY,
    name_en         VARCHAR(100) NOT NULL,
    name_fr         VARCHAR(100) NOT NULL,
    symbol          VARCHAR(10)  NOT NULL,
    country_code    VARCHAR(2),
    subunit         VARCHAR(50),
    subunit_factor  INT          DEFAULT 100,
    central_bank    VARCHAR(200),
    convertible     BOOLEAN      DEFAULT FALSE,
    monetary_union  VARCHAR(20),
    forex_regulation VARCHAR(20) DEFAULT 'moderate',
    created_at      TIMESTAMP    DEFAULT NOW(),
    updated_at      TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE currencies IS 'ISO 4217 currency data for all 54 African Union member states';

-- ---------------------------------------------------------------------------
-- Exchange rates table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS exchange_rates (
    id              SERIAL       PRIMARY KEY,
    base_currency   VARCHAR(3)   NOT NULL,
    target_currency VARCHAR(3)   NOT NULL,
    rate            DECIMAL(18, 8) NOT NULL,
    timestamp       TIMESTAMP    NOT NULL,
    source          VARCHAR(50)  NOT NULL,
    created_at      TIMESTAMP    DEFAULT NOW(),
    UNIQUE (base_currency, target_currency, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair
    ON exchange_rates (base_currency, target_currency);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_timestamp
    ON exchange_rates (timestamp DESC);

COMMENT ON TABLE exchange_rates IS
    'Exchange rate snapshots fetched from multiple providers (CurrencyFreaks, Fixer, Frankfurter)';

-- ---------------------------------------------------------------------------
-- Rate alerts table
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS rate_alerts (
    id               SERIAL       PRIMARY KEY,
    currency_pair    VARCHAR(7)   NOT NULL,
    previous_rate    DECIMAL(18, 8) NOT NULL,
    current_rate     DECIMAL(18, 8) NOT NULL,
    change_percent   DECIMAL(8, 4) NOT NULL,
    direction        VARCHAR(4)   NOT NULL CHECK (direction IN ('up', 'down')),
    threshold_percent DECIMAL(5, 2) DEFAULT 5.00,
    alert_type       VARCHAR(20)  DEFAULT 'automatic',
    triggered_at     TIMESTAMP    NOT NULL,
    created_at       TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_rate_alerts_pair
    ON rate_alerts (currency_pair);

CREATE INDEX IF NOT EXISTS idx_rate_alerts_triggered_at
    ON rate_alerts (triggered_at DESC);

COMMENT ON TABLE rate_alerts IS
    'Rate change alerts triggered when a pair moves more than threshold_percent';

-- ---------------------------------------------------------------------------
-- View: latest rates per pair
-- ---------------------------------------------------------------------------
CREATE OR REPLACE VIEW latest_exchange_rates AS
SELECT DISTINCT ON (base_currency, target_currency)
    base_currency,
    target_currency,
    rate,
    timestamp,
    source
FROM exchange_rates
ORDER BY base_currency, target_currency, timestamp DESC;

COMMENT ON VIEW latest_exchange_rates IS
    'Convenience view returning the most recent rate for each currency pair';
