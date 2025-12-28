-- Usage Tracking System Schema
-- Database: unicorn_db
-- Purpose: Track API usage per user and enforce subscription limits
-- Epic: Usage Tracking & Metering
-- Date: November 12, 2025

-- ==================================================
-- TABLE: api_usage
-- Purpose: Store all API call events for billing and analytics
-- ==================================================
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    org_id VARCHAR(255),             -- Organization ID (nullable)
    endpoint VARCHAR(500) NOT NULL,  -- API endpoint called
    method VARCHAR(10) NOT NULL,     -- HTTP method (GET, POST, etc.)
    response_status INT,             -- HTTP response status code
    tokens_used INT DEFAULT 0,       -- Tokens consumed (for LLM calls)
    cost_credits DECIMAL(10, 4) DEFAULT 0,  -- Cost in credits
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,  -- When call was made
    billing_period VARCHAR(20) NOT NULL,  -- e.g., "2025-11" or "2025-11-12" for daily

    -- Performance metadata (optional, for future use)
    request_duration_ms INT,         -- How long the request took
    request_id VARCHAR(100),         -- Unique request identifier
    ip_address VARCHAR(50),          -- Client IP address
    user_agent TEXT                  -- Client user agent
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_api_usage_user_period ON api_usage(user_id, billing_period);
CREATE INDEX IF NOT EXISTS idx_api_usage_org_period ON api_usage(org_id, billing_period);
CREATE INDEX IF NOT EXISTS idx_api_usage_timestamp ON api_usage(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON api_usage(endpoint, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_usage_user_timestamp ON api_usage(user_id, timestamp DESC);

-- Partial index for recent data (last 90 days) - faster queries
CREATE INDEX IF NOT EXISTS idx_api_usage_recent ON api_usage(user_id, billing_period)
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '90 days';

-- ==================================================
-- TABLE: usage_quotas
-- Purpose: Store user subscription tier and usage quotas
-- ==================================================
CREATE TABLE IF NOT EXISTS usage_quotas (
    user_id VARCHAR(255) PRIMARY KEY,  -- Keycloak user ID
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'trial',  -- Tier code
    subscription_status VARCHAR(50) NOT NULL DEFAULT 'active',  -- active, cancelled, suspended
    api_calls_limit INT NOT NULL DEFAULT 100,  -- Monthly/period limit (-1 = unlimited)
    api_calls_used INT DEFAULT 0,              -- Current usage count (cached from api_usage)
    reset_date DATE NOT NULL,                  -- When quota resets
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Additional quotas (for future features)
    storage_limit_gb INT DEFAULT 5,
    team_seats_limit INT DEFAULT 1,
    priority_support BOOLEAN DEFAULT FALSE,
    byok_enabled BOOLEAN DEFAULT FALSE,

    -- Metadata
    last_api_call TIMESTAMP WITH TIME ZONE,  -- Last API call timestamp
    last_reset TIMESTAMP WITH TIME ZONE,     -- Last quota reset timestamp

    -- Constraints
    CONSTRAINT valid_tier CHECK (subscription_tier IN (
        'trial', 'free', 'starter', 'professional', 'enterprise',
        'vip_founder', 'byok', 'managed'
    )),
    CONSTRAINT valid_status CHECK (subscription_status IN (
        'active', 'cancelled', 'suspended', 'expired', 'pending'
    )),
    CONSTRAINT valid_api_limit CHECK (api_calls_limit >= -1)
);

-- Index for tier queries
CREATE INDEX IF NOT EXISTS idx_usage_quotas_tier ON usage_quotas(subscription_tier, subscription_status);
CREATE INDEX IF NOT EXISTS idx_usage_quotas_reset ON usage_quotas(reset_date);

-- ==================================================
-- TABLE: usage_alerts
-- Purpose: Track when users hit usage thresholds
-- ==================================================
CREATE TABLE IF NOT EXISTS usage_alerts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- '50_percent', '80_percent', '95_percent', 'limit_exceeded'
    threshold_percentage INT NOT NULL,  -- Percentage of quota used
    api_calls_used INT NOT NULL,
    api_calls_limit INT NOT NULL,
    alert_sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Ensure we only send one alert per threshold
    CONSTRAINT unique_user_alert UNIQUE(user_id, alert_type, created_at::DATE)
);

CREATE INDEX IF NOT EXISTS idx_usage_alerts_user ON usage_alerts(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_alerts_pending ON usage_alerts(alert_sent, created_at);

-- ==================================================
-- FUNCTION: Update usage quota cache
-- Purpose: Auto-update api_calls_used in usage_quotas table
-- ==================================================
CREATE OR REPLACE FUNCTION update_usage_quota_cache()
RETURNS TRIGGER AS $$
BEGIN
    -- Update usage_quotas.api_calls_used when new api_usage record is inserted
    UPDATE usage_quotas
    SET
        api_calls_used = api_calls_used + 1,
        last_api_call = NEW.timestamp,
        updated_at = CURRENT_TIMESTAMP
    WHERE user_id = NEW.user_id;

    -- If user doesn't have quota record, create one
    IF NOT FOUND THEN
        INSERT INTO usage_quotas (user_id, subscription_tier, api_calls_limit, api_calls_used, reset_date)
        VALUES (NEW.user_id, 'trial', 100, 1, CURRENT_DATE + INTERVAL '1 day')
        ON CONFLICT (user_id) DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update quota cache
DROP TRIGGER IF EXISTS trigger_update_usage_quota ON api_usage;
CREATE TRIGGER trigger_update_usage_quota
    AFTER INSERT ON api_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_usage_quota_cache();

-- ==================================================
-- FUNCTION: Check and send usage alerts
-- Purpose: Create alert records when users hit thresholds
-- ==================================================
CREATE OR REPLACE FUNCTION check_usage_alerts()
RETURNS TRIGGER AS $$
DECLARE
    quota_record RECORD;
    usage_percent INT;
BEGIN
    -- Get quota info
    SELECT * INTO quota_record
    FROM usage_quotas
    WHERE user_id = NEW.user_id;

    -- Skip if unlimited
    IF quota_record.api_calls_limit <= 0 THEN
        RETURN NEW;
    END IF;

    -- Calculate percentage
    usage_percent := (quota_record.api_calls_used * 100) / quota_record.api_calls_limit;

    -- Create alerts at thresholds
    IF usage_percent >= 95 AND NOT EXISTS (
        SELECT 1 FROM usage_alerts
        WHERE user_id = NEW.user_id
        AND alert_type = '95_percent'
        AND created_at::DATE = CURRENT_DATE
    ) THEN
        INSERT INTO usage_alerts (user_id, alert_type, threshold_percentage, api_calls_used, api_calls_limit)
        VALUES (NEW.user_id, '95_percent', 95, quota_record.api_calls_used, quota_record.api_calls_limit);
    ELSIF usage_percent >= 80 AND NOT EXISTS (
        SELECT 1 FROM usage_alerts
        WHERE user_id = NEW.user_id
        AND alert_type = '80_percent'
        AND created_at::DATE = CURRENT_DATE
    ) THEN
        INSERT INTO usage_alerts (user_id, alert_type, threshold_percentage, api_calls_used, api_calls_limit)
        VALUES (NEW.user_id, '80_percent', 80, quota_record.api_calls_used, quota_record.api_calls_limit);
    ELSIF usage_percent >= 50 AND NOT EXISTS (
        SELECT 1 FROM usage_alerts
        WHERE user_id = NEW.user_id
        AND alert_type = '50_percent'
        AND created_at::DATE = CURRENT_DATE
    ) THEN
        INSERT INTO usage_alerts (user_id, alert_type, threshold_percentage, api_calls_used, api_calls_limit)
        VALUES (NEW.user_id, '50_percent', 50, quota_record.api_calls_used, quota_record.api_calls_limit);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to check alerts after quota update
DROP TRIGGER IF EXISTS trigger_check_usage_alerts ON usage_quotas;
CREATE TRIGGER trigger_check_usage_alerts
    AFTER UPDATE OF api_calls_used ON usage_quotas
    FOR EACH ROW
    WHEN (NEW.api_calls_used > OLD.api_calls_used)
    EXECUTE FUNCTION check_usage_alerts();

-- ==================================================
-- MATERIALIZED VIEW: Daily usage summary (for dashboards)
-- Purpose: Pre-aggregate daily stats for fast dashboard queries
-- ==================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_usage_summary AS
SELECT
    user_id,
    DATE(timestamp) as usage_date,
    COUNT(*) as total_calls,
    SUM(tokens_used) as total_tokens,
    SUM(cost_credits) as total_cost,
    COUNT(DISTINCT endpoint) as unique_endpoints,
    MIN(timestamp) as first_call,
    MAX(timestamp) as last_call
FROM api_usage
WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '90 days'
GROUP BY user_id, DATE(timestamp);

-- Index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_daily_usage_user_date
ON mv_daily_usage_summary(user_id, usage_date DESC);

-- Refresh function (call this periodically via cron or background task)
CREATE OR REPLACE FUNCTION refresh_usage_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_usage_summary;
END;
$$ LANGUAGE plpgsql;

-- ==================================================
-- COMMENTS (documentation)
-- ==================================================
COMMENT ON TABLE api_usage IS 'Records every API call for usage tracking and billing';
COMMENT ON TABLE usage_quotas IS 'Stores user subscription tier and usage limits';
COMMENT ON TABLE usage_alerts IS 'Tracks usage threshold alerts for notifications';

COMMENT ON COLUMN api_usage.billing_period IS 'Format: YYYY-MM for monthly, YYYY-MM-DD for daily billing cycles';
COMMENT ON COLUMN usage_quotas.api_calls_limit IS '-1 means unlimited, positive integer is the monthly limit';
COMMENT ON COLUMN usage_quotas.reset_date IS 'Date when quota resets (start of next billing period)';

-- ==================================================
-- INITIAL DATA: Populate usage_quotas for existing users
-- ==================================================
-- This will be run by the migration script to ensure all Keycloak users have quota records

-- Example: Sync from Keycloak (run this after migration)
-- INSERT INTO usage_quotas (user_id, subscription_tier, api_calls_limit, reset_date)
-- SELECT
--     id as user_id,
--     COALESCE(attributes->>'subscription_tier', 'trial') as subscription_tier,
--     CASE COALESCE(attributes->>'subscription_tier', 'trial')
--         WHEN 'trial' THEN 700
--         WHEN 'starter' THEN 1000
--         WHEN 'professional' THEN 10000
--         ELSE -1
--     END as api_calls_limit,
--     CURRENT_DATE + INTERVAL '1 month' as reset_date
-- FROM keycloak_users
-- ON CONFLICT (user_id) DO NOTHING;

-- ==================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION (added 2025-11-12)
-- ==================================================
-- See performance_indexes.sql for additional composite indexes

-- Grant permissions (if using role-based access)
-- GRANT SELECT, INSERT ON api_usage TO api_backend;
-- GRANT SELECT, UPDATE ON usage_quotas TO api_backend;
-- GRANT SELECT, INSERT ON usage_alerts TO api_backend;
