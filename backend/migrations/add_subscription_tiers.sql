-- Subscription Tier Management Schema
-- Database: unicorn_db
-- Purpose: Store subscription tier definitions, features, and user migration history
-- Epic 4.4: Subscription Management GUI

-- ==================================================
-- TABLE: subscription_tiers
-- Purpose: Store subscription tier definitions
-- ==================================================
CREATE TABLE IF NOT EXISTS subscription_tiers (
    id SERIAL PRIMARY KEY,
    tier_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'vip_founder', 'byok', 'managed'
    tier_name VARCHAR(100) NOT NULL,        -- Display name
    description TEXT,
    price_monthly DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    price_yearly DECIMAL(10, 2) DEFAULT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_invite_only BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,  -- For display ordering

    -- Feature limits
    api_calls_limit INTEGER NOT NULL DEFAULT 0,  -- -1 for unlimited
    team_seats INTEGER NOT NULL DEFAULT 1,
    byok_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    priority_support BOOLEAN NOT NULL DEFAULT FALSE,

    -- Integration
    lago_plan_code VARCHAR(100),  -- Lago plan code for sync
    stripe_price_monthly VARCHAR(100),  -- Stripe price ID (monthly)
    stripe_price_yearly VARCHAR(100),   -- Stripe price ID (yearly)

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),  -- Admin who created this tier
    updated_by VARCHAR(255),  -- Admin who last updated

    -- Constraints
    CONSTRAINT tier_code_lowercase CHECK (tier_code = LOWER(tier_code)),
    CONSTRAINT valid_price CHECK (price_monthly >= 0),
    CONSTRAINT valid_api_limit CHECK (api_calls_limit >= -1)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_active ON subscription_tiers(is_active);
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_code ON subscription_tiers(tier_code);
CREATE INDEX IF NOT EXISTS idx_subscription_tiers_sort ON subscription_tiers(sort_order, is_active);

-- ==================================================
-- TABLE: tier_features
-- Purpose: Store feature flags per tier (key-value pairs)
-- ==================================================
CREATE TABLE IF NOT EXISTS tier_features (
    id SERIAL PRIMARY KEY,
    tier_id INTEGER NOT NULL REFERENCES subscription_tiers(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL,   -- e.g., 'chat_access', 'search_enabled', 'tts_enabled'
    feature_value TEXT,                   -- JSON value for complex features
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT unique_tier_feature UNIQUE(tier_id, feature_key)
);

-- Index for feature lookups
CREATE INDEX IF NOT EXISTS idx_tier_features_tier ON tier_features(tier_id, enabled);
CREATE INDEX IF NOT EXISTS idx_tier_features_key ON tier_features(feature_key);

-- ==================================================
-- TABLE: user_tier_history
-- Purpose: Audit log of user tier changes
-- ==================================================
CREATE TABLE IF NOT EXISTS user_tier_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    user_email VARCHAR(255),         -- For reference
    old_tier_code VARCHAR(50),       -- Previous tier
    new_tier_code VARCHAR(50),       -- New tier
    change_reason TEXT NOT NULL,     -- Admin must provide reason
    changed_by VARCHAR(255) NOT NULL, -- Admin who made the change
    change_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Impact tracking
    old_api_limit INTEGER,
    new_api_limit INTEGER,
    api_calls_used INTEGER DEFAULT 0,  -- Usage at time of change

    -- Metadata
    ip_address VARCHAR(50),
    user_agent TEXT,
    additional_notes TEXT
);

-- Index for audit queries
CREATE INDEX IF NOT EXISTS idx_tier_history_user ON user_tier_history(user_id, change_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tier_history_admin ON user_tier_history(changed_by, change_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tier_history_timestamp ON user_tier_history(change_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tier_history_tier_codes ON user_tier_history(old_tier_code, new_tier_code);

-- ==================================================
-- TABLE: tier_feature_definitions
-- Purpose: Define available feature flags (metadata)
-- ==================================================
CREATE TABLE IF NOT EXISTS tier_feature_definitions (
    id SERIAL PRIMARY KEY,
    feature_key VARCHAR(100) UNIQUE NOT NULL,
    feature_name VARCHAR(200) NOT NULL,
    description TEXT,
    value_type VARCHAR(50) NOT NULL DEFAULT 'boolean',  -- 'boolean', 'integer', 'string', 'json'
    default_value TEXT,
    category VARCHAR(100),  -- e.g., 'services', 'limits', 'support'
    is_system BOOLEAN NOT NULL DEFAULT FALSE,  -- System features can't be deleted
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for feature definitions
CREATE INDEX IF NOT EXISTS idx_feature_defs_category ON tier_feature_definitions(category);
CREATE INDEX IF NOT EXISTS idx_feature_defs_key ON tier_feature_definitions(feature_key);

-- ==================================================
-- FUNCTION: Update timestamp on tier changes
-- ==================================================
CREATE OR REPLACE FUNCTION update_subscription_tier_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for subscription_tiers
DROP TRIGGER IF EXISTS trg_subscription_tiers_update ON subscription_tiers;
CREATE TRIGGER trg_subscription_tiers_update
    BEFORE UPDATE ON subscription_tiers
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_tier_timestamp();

-- Trigger for tier_features
DROP TRIGGER IF EXISTS trg_tier_features_update ON tier_features;
CREATE TRIGGER trg_tier_features_update
    BEFORE UPDATE ON tier_features
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_tier_timestamp();

-- ==================================================
-- SEED DATA: Default subscription tiers
-- Based on roadmap: VIP/Founder ($0), BYOK ($30), Managed ($50)
-- ==================================================

-- 1. VIP/Founder Tier (Invite-only, $0)
INSERT INTO subscription_tiers (tier_code, tier_name, description, price_monthly, price_yearly, is_active, is_invite_only, sort_order, api_calls_limit, team_seats, byok_enabled, priority_support, lago_plan_code, created_by)
VALUES (
    'vip_founder',
    'VIP / Founder',
    'Invite-only tier for founders'' friends, admins, staff, and partners. Must purchase credits separately.',
    0.00,
    0.00,
    TRUE,
    TRUE,
    1,
    10000,  -- 10k API calls/month
    1,
    TRUE,
    TRUE,
    'vip_founder',
    'system'
) ON CONFLICT (tier_code) DO NOTHING;

-- 2. BYOK Tier ($30/month)
INSERT INTO subscription_tiers (tier_code, tier_name, description, price_monthly, price_yearly, is_active, is_invite_only, sort_order, api_calls_limit, team_seats, byok_enabled, priority_support, lago_plan_code, created_by)
VALUES (
    'byok',
    'BYOK (Bring Your Own Key)',
    'Use your own API keys for OpenAI, Anthropic, Google, etc. No platform markup. Priority support included.',
    30.00,
    300.00,  -- ~$25/month annually
    TRUE,
    FALSE,
    2,
    -1,  -- Unlimited (user manages their own keys)
    1,
    TRUE,
    TRUE,
    'byok_monthly',
    'system'
) ON CONFLICT (tier_code) DO NOTHING;

-- 3. Managed Tier ($50/month - Recommended)
INSERT INTO subscription_tiers (tier_code, tier_name, description, price_monthly, price_yearly, is_active, is_invite_only, sort_order, api_calls_limit, team_seats, byok_enabled, priority_support, lago_plan_code, created_by)
VALUES (
    'managed',
    'Managed (Recommended)',
    'Platform manages all API keys and billing. Access to 100+ models via OpenRouter. Includes monthly credits. Priority support.',
    50.00,
    500.00,  -- ~$42/month annually
    TRUE,
    FALSE,
    3,
    50000,  -- 50k API calls/month
    5,  -- Team seats
    TRUE,  -- Can still use BYOK if desired
    TRUE,
    'managed_monthly',
    'system'
) ON CONFLICT (tier_code) DO NOTHING;

-- ==================================================
-- SEED DATA: Default feature definitions
-- ==================================================

INSERT INTO tier_feature_definitions (feature_key, feature_name, description, value_type, default_value, category, is_system)
VALUES
    ('chat_access', 'Open-WebUI Access', 'Access to Open-WebUI chat interface', 'boolean', 'true', 'services', TRUE),
    ('search_enabled', 'Center-Deep Search', 'Access to Center-Deep metasearch engine', 'boolean', 'false', 'services', TRUE),
    ('tts_enabled', 'Text-to-Speech', 'Access to Unicorn Orator (TTS) service', 'boolean', 'false', 'services', TRUE),
    ('stt_enabled', 'Speech-to-Text', 'Access to Unicorn Amanuensis (STT) service', 'boolean', 'false', 'services', TRUE),
    ('billing_dashboard', 'Billing Dashboard', 'Access to Lago billing dashboard', 'boolean', 'false', 'services', TRUE),
    ('litellm_access', 'LiteLLM Gateway', 'Access to LiteLLM AI model gateway', 'boolean', 'false', 'services', TRUE),
    ('brigade_access', 'Brigade Agents', 'Access to Unicorn Brigade agent platform', 'boolean', 'false', 'services', TRUE),
    ('bolt_access', 'Bolt.DIY', 'Access to Bolt.DIY development environment', 'boolean', 'false', 'services', TRUE),
    ('api_calls_limit', 'API Calls Limit', 'Maximum API calls per month', 'integer', '1000', 'limits', TRUE),
    ('team_seats', 'Team Seats', 'Number of team members allowed', 'integer', '1', 'limits', TRUE),
    ('storage_gb', 'Storage (GB)', 'Storage quota in gigabytes', 'integer', '10', 'limits', FALSE),
    ('priority_support', 'Priority Support', 'Access to priority customer support', 'boolean', 'false', 'support', TRUE),
    ('dedicated_support', 'Dedicated Support', '24/7 dedicated support channel', 'boolean', 'false', 'support', FALSE),
    ('sso_enabled', 'SSO Integration', 'Single Sign-On integration support', 'boolean', 'false', 'enterprise', FALSE),
    ('audit_logs', 'Audit Logs', 'Access to detailed audit logging', 'boolean', 'false', 'enterprise', FALSE),
    ('custom_integrations', 'Custom Integrations', 'Custom API integrations', 'boolean', 'false', 'enterprise', FALSE),
    ('white_label', 'White Label', 'White-label branding options', 'boolean', 'false', 'enterprise', FALSE)
ON CONFLICT (feature_key) DO NOTHING;

-- ==================================================
-- SEED DATA: Features per tier
-- ==================================================

-- VIP/Founder tier features
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT
    st.id,
    'chat_access',
    'true',
    TRUE
FROM subscription_tiers st WHERE st.tier_code = 'vip_founder'
ON CONFLICT (tier_id, feature_key) DO NOTHING;

INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT
    st.id,
    'search_enabled',
    'true',
    TRUE
FROM subscription_tiers st WHERE st.tier_code = 'vip_founder'
ON CONFLICT (tier_id, feature_key) DO NOTHING;

INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT
    st.id,
    'litellm_access',
    'true',
    TRUE
FROM subscription_tiers st WHERE st.tier_code = 'vip_founder'
ON CONFLICT (tier_id, feature_key) DO NOTHING;

INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT
    st.id,
    'priority_support',
    'true',
    TRUE
FROM subscription_tiers st WHERE st.tier_code = 'vip_founder'
ON CONFLICT (tier_id, feature_key) DO NOTHING;

-- BYOK tier features (all services except billing dashboard)
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT
    st.id,
    fd.feature_key,
    CASE fd.value_type
        WHEN 'boolean' THEN 'true'
        WHEN 'integer' THEN '-1'
        ELSE fd.default_value
    END,
    TRUE
FROM subscription_tiers st
CROSS JOIN tier_feature_definitions fd
WHERE st.tier_code = 'byok'
  AND fd.feature_key IN ('chat_access', 'search_enabled', 'tts_enabled', 'stt_enabled', 'litellm_access', 'brigade_access', 'priority_support')
ON CONFLICT (tier_id, feature_key) DO NOTHING;

-- Managed tier features (all services)
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT
    st.id,
    fd.feature_key,
    CASE fd.value_type
        WHEN 'boolean' THEN 'true'
        WHEN 'integer' THEN CASE
            WHEN fd.feature_key = 'api_calls_limit' THEN '50000'
            WHEN fd.feature_key = 'team_seats' THEN '5'
            WHEN fd.feature_key = 'storage_gb' THEN '100'
            ELSE fd.default_value
        END
        ELSE fd.default_value
    END,
    TRUE
FROM subscription_tiers st
CROSS JOIN tier_feature_definitions fd
WHERE st.tier_code = 'managed'
  AND fd.category IN ('services', 'support')
ON CONFLICT (tier_id, feature_key) DO NOTHING;

-- ==================================================
-- VIEWS: Convenient tier queries
-- ==================================================

-- View: Active tiers with feature counts
CREATE OR REPLACE VIEW v_active_tiers AS
SELECT
    st.id,
    st.tier_code,
    st.tier_name,
    st.description,
    st.price_monthly,
    st.price_yearly,
    st.is_invite_only,
    st.sort_order,
    st.api_calls_limit,
    st.team_seats,
    st.byok_enabled,
    st.priority_support,
    st.lago_plan_code,
    COUNT(tf.id) AS feature_count,
    st.created_at,
    st.updated_at
FROM subscription_tiers st
LEFT JOIN tier_features tf ON st.id = tf.tier_id AND tf.enabled = TRUE
WHERE st.is_active = TRUE
GROUP BY st.id
ORDER BY st.sort_order;

-- View: Tier migration summary
CREATE OR REPLACE VIEW v_tier_migrations_summary AS
SELECT
    new_tier_code,
    old_tier_code,
    COUNT(*) AS migration_count,
    AVG(new_api_limit - old_api_limit) AS avg_limit_change,
    MAX(change_timestamp) AS last_migration
FROM user_tier_history
GROUP BY new_tier_code, old_tier_code
ORDER BY migration_count DESC;

-- ==================================================
-- GRANTS: Ensure ops-center can access these tables
-- ==================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON subscription_tiers TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON tier_features TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON user_tier_history TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON tier_feature_definitions TO unicorn;

GRANT USAGE, SELECT ON SEQUENCE subscription_tiers_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE tier_features_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE user_tier_history_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE tier_feature_definitions_id_seq TO unicorn;

GRANT SELECT ON v_active_tiers TO unicorn;
GRANT SELECT ON v_tier_migrations_summary TO unicorn;

-- ==================================================
-- COMPLETION NOTES
-- ==================================================

-- Migration created: 2025-10-28
-- Tables: 4 (subscription_tiers, tier_features, user_tier_history, tier_feature_definitions)
-- Views: 2 (v_active_tiers, v_tier_migrations_summary)
-- Indexes: 12 for performance
-- Triggers: 2 for auto-timestamps
-- Seed data: 3 tiers, 17 feature definitions, ~25 tier-feature mappings

-- To apply: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/this/file.sql
-- To verify: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt subscription_*; \dt tier_*;"
