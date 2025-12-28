-- =====================================================
-- LiteLLM Credit System Database Schema
-- =====================================================
-- Version: 1.0.0
-- Date: 2025-10-20
-- Description: Complete database schema for LiteLLM credit system
--              supporting multi-provider LLM routing, BYOK, and
--              power level optimization
-- =====================================================

-- Drop existing tables if recreating (use with caution in production)
-- DROP TABLE IF EXISTS llm_usage_log CASCADE;
-- DROP TABLE IF EXISTS credit_transactions CASCADE;
-- DROP TABLE IF EXISTS user_provider_keys CASCADE;
-- DROP TABLE IF EXISTS user_credits CASCADE;
-- DROP TABLE IF EXISTS provider_health CASCADE;
-- DROP TABLE IF EXISTS credit_packages CASCADE;
-- DROP MATERIALIZED VIEW IF EXISTS llm_usage_summary CASCADE;

-- =====================================================
-- Table: user_credits
-- Description: Track user credit balances and subscription tiers
-- =====================================================
CREATE TABLE IF NOT EXISTS user_credits (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,  -- Keycloak user ID
    credits_remaining FLOAT NOT NULL DEFAULT 0.0,
    credits_lifetime FLOAT NOT NULL DEFAULT 0.0,  -- Total credits ever purchased
    monthly_cap FLOAT,  -- Optional spending limit (NULL = no limit)
    tier TEXT NOT NULL DEFAULT 'free',  -- free, starter, professional, enterprise
    power_level TEXT NOT NULL DEFAULT 'balanced',  -- eco, balanced, precision
    auto_recharge BOOLEAN DEFAULT FALSE,  -- Auto-purchase when below threshold
    recharge_threshold FLOAT DEFAULT 10.0,  -- Threshold for auto-recharge
    recharge_amount FLOAT DEFAULT 100.0,  -- Amount to auto-purchase
    stripe_customer_id TEXT,  -- Stripe customer ID for billing
    last_reset TIMESTAMP,  -- Last time monthly cap was reset
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_tier CHECK (tier IN ('free', 'starter', 'professional', 'enterprise')),
    CONSTRAINT valid_power_level CHECK (power_level IN ('eco', 'balanced', 'precision')),
    CONSTRAINT positive_credits CHECK (credits_remaining >= 0),
    CONSTRAINT positive_lifetime CHECK (credits_lifetime >= 0)
);

-- =====================================================
-- Table: credit_transactions
-- Description: Complete audit log of all credit movements
-- =====================================================
CREATE TABLE IF NOT EXISTS credit_transactions (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,  -- purchase, debit, refund, bonus, adjustment
    amount FLOAT NOT NULL,  -- Positive for credit, negative for debit
    balance_after FLOAT NOT NULL,

    -- LLM Usage Details (for debit transactions)
    provider TEXT,  -- openai, anthropic, openrouter, etc.
    model TEXT,  -- gpt-4, claude-3-opus, etc.
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    tokens_used INTEGER,  -- Total tokens (prompt + completion)
    cost_per_token FLOAT,  -- Cost calculation
    power_level TEXT,  -- eco, balanced, precision
    byok_used BOOLEAN DEFAULT FALSE,  -- True if user's API key was used

    -- Payment Details (for purchase transactions)
    payment_method TEXT,  -- stripe, paypal, manual, bonus
    stripe_transaction_id TEXT,  -- Stripe payment ID
    stripe_invoice_id TEXT,  -- Stripe invoice ID
    package_id INTEGER,  -- Reference to credit_packages

    -- Additional Context
    metadata JSONB,  -- Additional context (request_id, session_id, app_id, etc.)
    notes TEXT,  -- Human-readable notes for manual adjustments
    admin_user_id TEXT,  -- Admin who made manual adjustment

    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('purchase', 'debit', 'refund', 'bonus', 'adjustment')
    ),
    CONSTRAINT valid_payment_method CHECK (
        payment_method IS NULL OR
        payment_method IN ('stripe', 'paypal', 'manual', 'bonus', 'trial')
    )
);

-- =====================================================
-- Table: user_provider_keys (BYOK - Bring Your Own Key)
-- Description: Store encrypted user API keys for providers
-- =====================================================
CREATE TABLE IF NOT EXISTS user_provider_keys (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,  -- openai, anthropic, openrouter, google, etc.
    encrypted_api_key TEXT NOT NULL,  -- Fernet encrypted
    key_name TEXT,  -- User-friendly name (e.g., "My OpenAI Key")
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,  -- Default key for this provider

    -- Usage Statistics
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    last_used TIMESTAMP,

    -- Key Management
    expires_at TIMESTAMP,  -- Optional expiration
    rotation_reminder TIMESTAMP,  -- When to remind user to rotate

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    UNIQUE(user_id, provider, key_name),
    CONSTRAINT valid_provider CHECK (
        provider IN ('openai', 'anthropic', 'openrouter', 'google', 'cohere',
                     'together', 'anyscale', 'deepinfra', 'custom')
    )
);

-- =====================================================
-- Table: llm_usage_log
-- Description: Detailed log of every LLM request for analytics
-- =====================================================
CREATE TABLE IF NOT EXISTS llm_usage_log (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,

    -- Provider & Model Info
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    power_level TEXT NOT NULL,

    -- Token Usage
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,

    -- Cost & Billing
    cost_credits FLOAT NOT NULL,
    cost_per_token FLOAT,
    byok_used BOOLEAN DEFAULT FALSE,  -- True if user's API key was used
    provider_key_id INTEGER,  -- Reference to user_provider_keys

    -- Request Details
    request_id TEXT UNIQUE,  -- Unique request identifier
    session_id TEXT,  -- User session
    app_id TEXT,  -- Which app made the request (Brigade, Open-WebUI, etc.)
    endpoint TEXT,  -- /v1/chat/completions, /v1/completions, etc.

    -- Performance Metrics
    latency_ms INTEGER,  -- Response time in milliseconds
    time_to_first_token_ms INTEGER,  -- Time until first token streamed
    tokens_per_second FLOAT,  -- Generation speed

    -- Status & Errors
    success BOOLEAN NOT NULL,
    status_code INTEGER,
    error_message TEXT,
    error_type TEXT,  -- rate_limit, insufficient_credits, timeout, etc.

    -- Additional Context
    metadata JSONB,  -- Full request/response metadata
    user_agent TEXT,  -- Client user agent
    ip_address INET,  -- Client IP address

    created_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT positive_tokens CHECK (
        prompt_tokens >= 0 AND
        completion_tokens >= 0 AND
        total_tokens >= 0
    ),
    CONSTRAINT valid_power_level_usage CHECK (
        power_level IN ('eco', 'balanced', 'precision')
    )
);

-- =====================================================
-- Table: provider_health
-- Description: Cached health status of LLM providers
-- =====================================================
CREATE TABLE IF NOT EXISTS provider_health (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,  -- healthy, degraded, down

    -- Performance Metrics
    avg_latency_ms INTEGER,
    p95_latency_ms INTEGER,  -- 95th percentile latency
    success_rate FLOAT,  -- Percentage of successful requests (0-100)

    -- Capacity Metrics
    requests_last_hour INTEGER DEFAULT 0,
    rate_limit_remaining INTEGER,  -- If provider exposes this

    -- Health Check Details
    last_check TIMESTAMP DEFAULT NOW(),
    last_success TIMESTAMP,
    last_failure TIMESTAMP,
    consecutive_failures INTEGER DEFAULT 0,

    -- Error Details
    last_error TEXT,
    error_count_24h INTEGER DEFAULT 0,

    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN ('healthy', 'degraded', 'down')),
    CONSTRAINT valid_success_rate CHECK (success_rate >= 0 AND success_rate <= 100)
);

-- =====================================================
-- Table: credit_packages
-- Description: Available credit packages for purchase
-- =====================================================
CREATE TABLE IF NOT EXISTS credit_packages (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    credits FLOAT NOT NULL,
    price_usd FLOAT NOT NULL,
    discount_percent FLOAT DEFAULT 0,

    -- Tier Restrictions
    min_tier TEXT,  -- Minimum tier required to purchase (NULL = any)

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_featured BOOLEAN DEFAULT FALSE,
    sort_order INTEGER DEFAULT 0,

    -- Display
    description TEXT,
    badge_text TEXT,  -- e.g., "BEST VALUE", "MOST POPULAR"

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Constraints
    CONSTRAINT positive_credits_pkg CHECK (credits > 0),
    CONSTRAINT positive_price CHECK (price_usd > 0),
    CONSTRAINT valid_discount CHECK (discount_percent >= 0 AND discount_percent <= 100)
);

-- =====================================================
-- Table: power_level_configs
-- Description: Configuration for power level routing strategies
-- =====================================================
CREATE TABLE IF NOT EXISTS power_level_configs (
    id SERIAL PRIMARY KEY,
    power_level TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,

    -- Routing Strategy
    preferred_providers JSONB,  -- Array of providers in preference order
    fallback_strategy TEXT DEFAULT 'next_available',  -- next_available, cheapest, fastest

    -- Cost Multiplier
    cost_multiplier FLOAT DEFAULT 1.0,  -- Relative cost vs balanced

    -- Performance Targets
    max_latency_ms INTEGER,
    min_quality_score FLOAT,  -- 0-100 quality score

    is_active BOOLEAN DEFAULT TRUE,

    -- Constraints
    CONSTRAINT valid_power_level_config CHECK (
        power_level IN ('eco', 'balanced', 'precision')
    )
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- user_credits indexes
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_tier ON user_credits(tier);
CREATE INDEX IF NOT EXISTS idx_user_credits_updated_at ON user_credits(updated_at DESC);

-- credit_transactions indexes
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_date ON credit_transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_stripe ON credit_transactions(stripe_transaction_id) WHERE stripe_transaction_id IS NOT NULL;

-- user_provider_keys indexes
CREATE INDEX IF NOT EXISTS idx_user_provider_keys_user_id ON user_provider_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_provider_keys_provider ON user_provider_keys(provider);
CREATE INDEX IF NOT EXISTS idx_user_provider_keys_active ON user_provider_keys(user_id, is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_provider_keys_default ON user_provider_keys(user_id, provider, is_default) WHERE is_default = TRUE;

-- llm_usage_log indexes
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_user_id ON llm_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_created_at ON llm_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_provider ON llm_usage_log(provider);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_model ON llm_usage_log(model);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_success ON llm_usage_log(success);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_request_id ON llm_usage_log(request_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_session_id ON llm_usage_log(session_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_app_id ON llm_usage_log(app_id);
CREATE INDEX IF NOT EXISTS idx_llm_usage_log_user_date ON llm_usage_log(user_id, created_at DESC);

-- provider_health indexes
CREATE INDEX IF NOT EXISTS idx_provider_health_status ON provider_health(status);
CREATE INDEX IF NOT EXISTS idx_provider_health_updated_at ON provider_health(updated_at DESC);

-- credit_packages indexes
CREATE INDEX IF NOT EXISTS idx_credit_packages_active ON credit_packages(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_credit_packages_featured ON credit_packages(is_featured, sort_order) WHERE is_featured = TRUE;

-- =====================================================
-- Materialized View: llm_usage_summary
-- Description: Pre-aggregated usage statistics for fast analytics
-- =====================================================
CREATE MATERIALIZED VIEW IF NOT EXISTS llm_usage_summary AS
SELECT
    user_id,
    provider,
    model,
    power_level,
    DATE_TRUNC('day', created_at) as date,

    -- Request Counts
    COUNT(*) as request_count,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as error_count,

    -- Token Usage
    SUM(prompt_tokens) as total_prompt_tokens,
    SUM(completion_tokens) as total_completion_tokens,
    SUM(total_tokens) as total_tokens,
    AVG(total_tokens) as avg_tokens_per_request,

    -- Cost
    SUM(cost_credits) as total_cost,
    AVG(cost_credits) as avg_cost_per_request,

    -- Performance
    AVG(latency_ms) as avg_latency_ms,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY latency_ms) as p95_latency_ms,
    AVG(tokens_per_second) as avg_tokens_per_second,

    -- Success Rate
    (SUM(CASE WHEN success THEN 1 ELSE 0 END)::FLOAT / COUNT(*)) * 100 as success_rate,

    -- BYOK Usage
    SUM(CASE WHEN byok_used THEN 1 ELSE 0 END) as byok_requests

FROM llm_usage_log
GROUP BY user_id, provider, model, power_level, DATE_TRUNC('day', created_at);

-- Create unique index for efficient refresh
CREATE UNIQUE INDEX IF NOT EXISTS idx_llm_usage_summary_unique
    ON llm_usage_summary (user_id, provider, model, power_level, date);

-- Create additional indexes for common queries
CREATE INDEX IF NOT EXISTS idx_llm_usage_summary_user_date
    ON llm_usage_summary (user_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_llm_usage_summary_date
    ON llm_usage_summary (date DESC);

-- =====================================================
-- Functions & Stored Procedures
-- =====================================================

-- Function: debit_user_credits
-- Description: Atomically debit credits from user account
CREATE OR REPLACE FUNCTION debit_user_credits(
    p_user_id TEXT,
    p_amount FLOAT,
    p_provider TEXT,
    p_model TEXT,
    p_prompt_tokens INTEGER,
    p_completion_tokens INTEGER,
    p_power_level TEXT,
    p_metadata JSONB DEFAULT '{}'::JSONB
) RETURNS TABLE(
    new_balance FLOAT,
    transaction_id INTEGER,
    success BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    v_new_balance FLOAT;
    v_transaction_id INTEGER;
    v_current_balance FLOAT;
BEGIN
    -- Get current balance
    SELECT credits_remaining INTO v_current_balance
    FROM user_credits
    WHERE user_id = p_user_id
    FOR UPDATE;  -- Lock row for update

    -- Check if user exists
    IF v_current_balance IS NULL THEN
        RETURN QUERY SELECT 0.0::FLOAT, 0, FALSE, 'User not found';
        RETURN;
    END IF;

    -- Check if sufficient credits
    IF v_current_balance < p_amount THEN
        RETURN QUERY SELECT v_current_balance, 0, FALSE, 'Insufficient credits';
        RETURN;
    END IF;

    -- Atomic update
    UPDATE user_credits
    SET credits_remaining = credits_remaining - p_amount,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING credits_remaining INTO v_new_balance;

    -- Insert transaction record
    INSERT INTO credit_transactions (
        user_id, transaction_type, amount, balance_after,
        provider, model, prompt_tokens, completion_tokens,
        tokens_used, cost_per_token, power_level, metadata
    ) VALUES (
        p_user_id, 'debit', -p_amount, v_new_balance,
        p_provider, p_model, p_prompt_tokens, p_completion_tokens,
        p_prompt_tokens + p_completion_tokens,
        p_amount / NULLIF(p_prompt_tokens + p_completion_tokens, 0),
        p_power_level, p_metadata
    ) RETURNING id INTO v_transaction_id;

    RETURN QUERY SELECT v_new_balance, v_transaction_id, TRUE, NULL::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Function: add_user_credits
-- Description: Add credits to user account (purchase, bonus, refund)
CREATE OR REPLACE FUNCTION add_user_credits(
    p_user_id TEXT,
    p_amount FLOAT,
    p_transaction_type TEXT,
    p_payment_method TEXT DEFAULT NULL,
    p_stripe_transaction_id TEXT DEFAULT NULL,
    p_package_id INTEGER DEFAULT NULL,
    p_notes TEXT DEFAULT NULL
) RETURNS TABLE(
    new_balance FLOAT,
    transaction_id INTEGER,
    success BOOLEAN,
    error_message TEXT
) AS $$
DECLARE
    v_new_balance FLOAT;
    v_transaction_id INTEGER;
BEGIN
    -- Validate transaction type
    IF p_transaction_type NOT IN ('purchase', 'bonus', 'refund', 'adjustment') THEN
        RETURN QUERY SELECT 0.0::FLOAT, 0, FALSE, 'Invalid transaction type';
        RETURN;
    END IF;

    -- Atomic update
    UPDATE user_credits
    SET credits_remaining = credits_remaining + p_amount,
        credits_lifetime = credits_lifetime + CASE
            WHEN p_transaction_type = 'purchase' THEN p_amount
            ELSE 0
        END,
        updated_at = NOW()
    WHERE user_id = p_user_id
    RETURNING credits_remaining INTO v_new_balance;

    -- If user doesn't exist, create account
    IF v_new_balance IS NULL THEN
        INSERT INTO user_credits (user_id, credits_remaining, credits_lifetime)
        VALUES (p_user_id, p_amount, p_amount)
        RETURNING credits_remaining INTO v_new_balance;
    END IF;

    -- Insert transaction record
    INSERT INTO credit_transactions (
        user_id, transaction_type, amount, balance_after,
        payment_method, stripe_transaction_id, package_id, notes
    ) VALUES (
        p_user_id, p_transaction_type, p_amount, v_new_balance,
        p_payment_method, p_stripe_transaction_id, p_package_id, p_notes
    ) RETURNING id INTO v_transaction_id;

    RETURN QUERY SELECT v_new_balance, v_transaction_id, TRUE, NULL::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Function: get_user_balance
-- Description: Get current credit balance for user
CREATE OR REPLACE FUNCTION get_user_balance(p_user_id TEXT)
RETURNS TABLE(
    credits_remaining FLOAT,
    credits_lifetime FLOAT,
    tier TEXT,
    power_level TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        uc.credits_remaining,
        uc.credits_lifetime,
        uc.tier,
        uc.power_level
    FROM user_credits uc
    WHERE uc.user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function: refresh_usage_summary
-- Description: Refresh materialized view for latest analytics
CREATE OR REPLACE FUNCTION refresh_usage_summary()
RETURNS VOID AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY llm_usage_summary;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Triggers
-- =====================================================

-- Trigger: update_user_credits_timestamp
-- Description: Auto-update updated_at on user_credits changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_credits_updated_at
    BEFORE UPDATE ON user_credits
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_user_provider_keys_updated_at
    BEFORE UPDATE ON user_provider_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_credit_packages_updated_at
    BEFORE UPDATE ON credit_packages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Initial Data / Seed Data
-- =====================================================

-- Insert default credit packages
INSERT INTO credit_packages (name, credits, price_usd, discount_percent, description, badge_text, sort_order, is_featured)
VALUES
    ('Starter Pack', 100, 10.00, 0, 'Perfect for trying out the platform', NULL, 1, FALSE),
    ('Value Pack', 500, 45.00, 10, 'Best value for regular users', 'MOST POPULAR', 2, TRUE),
    ('Pro Pack', 1000, 80.00, 20, 'For power users and developers', 'BEST VALUE', 3, TRUE),
    ('Enterprise Pack', 5000, 350.00, 30, 'Maximum credits for teams', NULL, 4, FALSE)
ON CONFLICT DO NOTHING;

-- Insert power level configurations
INSERT INTO power_level_configs (power_level, name, description, preferred_providers, cost_multiplier, max_latency_ms, min_quality_score)
VALUES
    ('eco', 'Eco Mode', 'Cost-optimized routing using cheapest providers',
     '["openrouter", "together", "deepinfra"]'::JSONB, 0.7, 5000, 70),
    ('balanced', 'Balanced Mode', 'Balanced cost and performance',
     '["openai", "anthropic", "openrouter"]'::JSONB, 1.0, 3000, 85),
    ('precision', 'Precision Mode', 'Maximum quality, premium providers',
     '["anthropic", "openai"]'::JSONB, 1.5, 2000, 95)
ON CONFLICT (power_level) DO UPDATE
SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    preferred_providers = EXCLUDED.preferred_providers,
    cost_multiplier = EXCLUDED.cost_multiplier,
    max_latency_ms = EXCLUDED.max_latency_ms,
    min_quality_score = EXCLUDED.min_quality_score;

-- =====================================================
-- Grants (if using separate DB user)
-- =====================================================
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO litellm_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO litellm_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO litellm_user;

-- =====================================================
-- Comments (for documentation)
-- =====================================================
COMMENT ON TABLE user_credits IS 'Track user credit balances, tiers, and power levels';
COMMENT ON TABLE credit_transactions IS 'Complete audit log of all credit movements';
COMMENT ON TABLE user_provider_keys IS 'Encrypted user API keys for BYOK (Bring Your Own Key)';
COMMENT ON TABLE llm_usage_log IS 'Detailed log of every LLM request for analytics';
COMMENT ON TABLE provider_health IS 'Cached health status of LLM providers';
COMMENT ON TABLE credit_packages IS 'Available credit packages for purchase';
COMMENT ON TABLE power_level_configs IS 'Configuration for power level routing strategies';
COMMENT ON MATERIALIZED VIEW llm_usage_summary IS 'Pre-aggregated usage statistics for fast analytics';

COMMENT ON FUNCTION debit_user_credits IS 'Atomically debit credits from user account';
COMMENT ON FUNCTION add_user_credits IS 'Add credits to user account (purchase, bonus, refund)';
COMMENT ON FUNCTION get_user_balance IS 'Get current credit balance for user';
COMMENT ON FUNCTION refresh_usage_summary IS 'Refresh materialized view for latest analytics';

-- =====================================================
-- Schema Version Control
-- =====================================================
CREATE TABLE IF NOT EXISTS schema_version (
    id SERIAL PRIMARY KEY,
    version TEXT NOT NULL,
    description TEXT,
    applied_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO schema_version (version, description)
VALUES ('1.0.0', 'Initial LiteLLM credit system schema')
ON CONFLICT DO NOTHING;

-- =====================================================
-- End of Schema
-- =====================================================
