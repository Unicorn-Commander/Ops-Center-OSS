-- Organization Billing System Database Migration
-- Version: 1.0.0
-- Created: 2025-11-12
-- Description: Create tables for organization-level billing, credit pools, and usage attribution
--
-- This extends the existing organization_tables.sql with billing-specific functionality

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== Organization Subscriptions Table ====================
-- Tracks organization-level subscription plans (Platform/BYOK/Hybrid)

CREATE TABLE IF NOT EXISTS organization_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Subscription details
    subscription_plan VARCHAR(50) NOT NULL CHECK (subscription_plan IN ('platform', 'byok', 'hybrid')),
    monthly_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    billing_cycle VARCHAR(20) DEFAULT 'monthly' CHECK (billing_cycle IN ('monthly', 'yearly', 'custom')),

    -- Billing provider integration
    lago_subscription_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'trialing', 'past_due', 'canceled', 'paused')),
    trial_ends_at TIMESTAMP WITH TIME ZONE,
    current_period_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    current_period_end TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create partial unique index for one active subscription per org
CREATE UNIQUE INDEX IF NOT EXISTS idx_org_subs_one_active
ON organization_subscriptions(org_id) WHERE status = 'active';

-- Create indexes for organization_subscriptions
CREATE INDEX IF NOT EXISTS idx_org_subs_org_id ON organization_subscriptions(org_id);
CREATE INDEX IF NOT EXISTS idx_org_subs_status ON organization_subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_org_subs_plan ON organization_subscriptions(subscription_plan);
CREATE INDEX IF NOT EXISTS idx_org_subs_lago ON organization_subscriptions(lago_subscription_id);
CREATE INDEX IF NOT EXISTS idx_org_subs_stripe ON organization_subscriptions(stripe_subscription_id);

-- Create trigger for updated_at
CREATE TRIGGER update_org_subs_updated_at BEFORE UPDATE ON organization_subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Organization Credit Pools Table ====================
-- Tracks shared credit pools for organizations

CREATE TABLE IF NOT EXISTS organization_credit_pools (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL UNIQUE REFERENCES organizations(id) ON DELETE CASCADE,

    -- Credit balances
    total_credits BIGINT NOT NULL DEFAULT 0,
    allocated_credits BIGINT NOT NULL DEFAULT 0,  -- Sum of all user allocations
    used_credits BIGINT NOT NULL DEFAULT 0,       -- Total used across all users
    available_credits BIGINT GENERATED ALWAYS AS (total_credits - allocated_credits) STORED,

    -- Quota management
    monthly_refresh_amount BIGINT DEFAULT 0,      -- Auto-refresh credits each month
    last_refresh_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_refresh_date TIMESTAMP WITH TIME ZONE,

    -- Overage handling
    allow_overage BOOLEAN DEFAULT false,
    overage_limit BIGINT DEFAULT 0,               -- Max overage allowed (0 = none)
    overage_rate DECIMAL(10, 6) DEFAULT 0.0,      -- Cost per overage credit

    -- Purchase tracking
    lifetime_purchased_credits BIGINT DEFAULT 0,
    lifetime_spent_amount DECIMAL(12, 2) DEFAULT 0.00,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for organization_credit_pools
CREATE INDEX IF NOT EXISTS idx_org_credit_pools_org_id ON organization_credit_pools(org_id);

-- Create trigger for updated_at
CREATE TRIGGER update_org_credit_pools_updated_at BEFORE UPDATE ON organization_credit_pools
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== User Credit Allocations Table ====================
-- Tracks per-user credit allocations within organizations

CREATE TABLE IF NOT EXISTS user_credit_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID

    -- Credit limits
    allocated_credits BIGINT NOT NULL DEFAULT 0,  -- How many credits this user can use
    used_credits BIGINT NOT NULL DEFAULT 0,       -- How many credits used this period
    remaining_credits BIGINT GENERATED ALWAYS AS (allocated_credits - used_credits) STORED,

    -- Quota management
    reset_period VARCHAR(20) DEFAULT 'monthly' CHECK (reset_period IN ('daily', 'weekly', 'monthly', 'never')),
    last_reset_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    next_reset_date TIMESTAMP WITH TIME ZONE,

    -- Allocation status
    is_active BOOLEAN DEFAULT true,
    allocated_by VARCHAR(255),  -- Admin who set allocation
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- One allocation per user per org
    UNIQUE(org_id, user_id)
);

-- Create indexes for user_credit_allocations
CREATE INDEX IF NOT EXISTS idx_user_credits_org_id ON user_credit_allocations(org_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credit_allocations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_active ON user_credit_allocations(is_active);

-- Create trigger for updated_at
CREATE TRIGGER update_user_credits_updated_at BEFORE UPDATE ON user_credit_allocations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Credit Usage Attribution Table ====================
-- Tracks which user used which credits (detailed audit trail)

CREATE TABLE IF NOT EXISTS credit_usage_attribution (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    allocation_id UUID REFERENCES user_credit_allocations(id) ON DELETE SET NULL,

    -- Usage details
    credits_used BIGINT NOT NULL,
    service_type VARCHAR(100) NOT NULL,  -- 'llm', 'image_generation', 'embeddings', etc.
    service_name VARCHAR(200),            -- Specific model/service used

    -- Cost tracking
    api_cost DECIMAL(12, 6) DEFAULT 0.0,  -- Actual API cost (if BYOK)
    markup_applied DECIMAL(12, 6) DEFAULT 0.0,  -- Markup charged
    total_cost DECIMAL(12, 6) GENERATED ALWAYS AS (api_cost + markup_applied) STORED,

    -- Request metadata
    request_id VARCHAR(255),
    request_metadata JSONB,  -- Store model, tokens, latency, etc.

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for credit_usage_attribution
CREATE INDEX IF NOT EXISTS idx_credit_usage_org_id ON credit_usage_attribution(org_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_user_id ON credit_usage_attribution(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_allocation_id ON credit_usage_attribution(allocation_id);
CREATE INDEX IF NOT EXISTS idx_credit_usage_service_type ON credit_usage_attribution(service_type);
CREATE INDEX IF NOT EXISTS idx_credit_usage_created_at ON credit_usage_attribution(created_at);
CREATE INDEX IF NOT EXISTS idx_credit_usage_metadata_gin ON credit_usage_attribution USING GIN (request_metadata);

-- ==================== Organization Billing History Table ====================
-- Tracks invoices, payments, and billing events

CREATE TABLE IF NOT EXISTS org_billing_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    subscription_id UUID REFERENCES organization_subscriptions(id) ON DELETE SET NULL,

    -- Billing event details
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'invoice_created', 'invoice_paid', 'invoice_failed',
        'subscription_created', 'subscription_upgraded', 'subscription_downgraded', 'subscription_canceled',
        'credit_purchase', 'credit_refund', 'overage_charged'
    )),

    -- Invoice details (if applicable)
    lago_invoice_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    amount DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',

    -- Payment details
    payment_status VARCHAR(50) CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded', 'canceled')),
    payment_method VARCHAR(100),  -- 'credit_card', 'bank_transfer', 'paypal', etc.
    paid_at TIMESTAMP WITH TIME ZONE,

    -- Period covered
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,

    -- Metadata
    event_metadata JSONB,  -- Store additional context
    notes TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for org_billing_history
CREATE INDEX IF NOT EXISTS idx_billing_history_org_id ON org_billing_history(org_id);
CREATE INDEX IF NOT EXISTS idx_billing_history_subscription_id ON org_billing_history(subscription_id);
CREATE INDEX IF NOT EXISTS idx_billing_history_event_type ON org_billing_history(event_type);
CREATE INDEX IF NOT EXISTS idx_billing_history_payment_status ON org_billing_history(payment_status);
CREATE INDEX IF NOT EXISTS idx_billing_history_created_at ON org_billing_history(created_at);
CREATE INDEX IF NOT EXISTS idx_billing_history_lago_invoice ON org_billing_history(lago_invoice_id);
CREATE INDEX IF NOT EXISTS idx_billing_history_stripe_invoice ON org_billing_history(stripe_invoice_id);

-- ==================== Helper Functions ====================

-- Function to check if user has sufficient credits
CREATE OR REPLACE FUNCTION has_sufficient_credits(
    p_org_id UUID,
    p_user_id VARCHAR,
    p_credits_needed BIGINT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_remaining BIGINT;
BEGIN
    SELECT remaining_credits INTO v_remaining
    FROM user_credit_allocations
    WHERE org_id = p_org_id
      AND user_id = p_user_id
      AND is_active = TRUE;

    IF v_remaining IS NULL THEN
        RETURN FALSE;  -- No allocation found
    END IF;

    RETURN v_remaining >= p_credits_needed;
END;
$$ LANGUAGE plpgsql;

-- Function to deduct credits from user allocation
CREATE OR REPLACE FUNCTION deduct_credits(
    p_org_id UUID,
    p_user_id VARCHAR,
    p_credits_used BIGINT,
    p_service_type VARCHAR,
    p_service_name VARCHAR DEFAULT NULL,
    p_request_id VARCHAR DEFAULT NULL,
    p_request_metadata JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_allocation_id UUID;
    v_remaining BIGINT;
BEGIN
    -- Get allocation ID and check remaining credits
    SELECT id, remaining_credits INTO v_allocation_id, v_remaining
    FROM user_credit_allocations
    WHERE org_id = p_org_id
      AND user_id = p_user_id
      AND is_active = TRUE
    FOR UPDATE;  -- Lock row for update

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No credit allocation found for user % in org %', p_user_id, p_org_id;
    END IF;

    IF v_remaining < p_credits_used THEN
        RAISE EXCEPTION 'Insufficient credits: % available, % needed', v_remaining, p_credits_used;
    END IF;

    -- Update user allocation
    UPDATE user_credit_allocations
    SET used_credits = used_credits + p_credits_used,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = v_allocation_id;

    -- Update org credit pool
    UPDATE organization_credit_pools
    SET used_credits = used_credits + p_credits_used,
        updated_at = CURRENT_TIMESTAMP
    WHERE org_id = p_org_id;

    -- Record usage attribution
    INSERT INTO credit_usage_attribution (
        org_id, user_id, allocation_id, credits_used,
        service_type, service_name, request_id, request_metadata
    ) VALUES (
        p_org_id, p_user_id, v_allocation_id, p_credits_used,
        p_service_type, p_service_name, p_request_id, p_request_metadata
    );

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to add credits to org pool
CREATE OR REPLACE FUNCTION add_credits_to_pool(
    p_org_id UUID,
    p_credits_amount BIGINT,
    p_purchase_amount DECIMAL DEFAULT 0.00
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE organization_credit_pools
    SET total_credits = total_credits + p_credits_amount,
        lifetime_purchased_credits = lifetime_purchased_credits + p_credits_amount,
        lifetime_spent_amount = lifetime_spent_amount + p_purchase_amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE org_id = p_org_id;

    IF NOT FOUND THEN
        -- Create pool if doesn't exist
        INSERT INTO organization_credit_pools (org_id, total_credits, lifetime_purchased_credits, lifetime_spent_amount)
        VALUES (p_org_id, p_credits_amount, p_credits_amount, p_purchase_amount);
    END IF;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to allocate credits to user
CREATE OR REPLACE FUNCTION allocate_credits_to_user(
    p_org_id UUID,
    p_user_id VARCHAR,
    p_credits_amount BIGINT,
    p_allocated_by VARCHAR DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_available BIGINT;
BEGIN
    -- Check if org has available credits
    SELECT available_credits INTO v_available
    FROM organization_credit_pools
    WHERE org_id = p_org_id
    FOR UPDATE;  -- Lock row

    IF NOT FOUND THEN
        RAISE EXCEPTION 'No credit pool found for org %', p_org_id;
    END IF;

    IF v_available < p_credits_amount THEN
        RAISE EXCEPTION 'Insufficient credits in pool: % available, % needed', v_available, p_credits_amount;
    END IF;

    -- Update or create user allocation
    INSERT INTO user_credit_allocations (org_id, user_id, allocated_credits, allocated_by)
    VALUES (p_org_id, p_user_id, p_credits_amount, p_allocated_by)
    ON CONFLICT (org_id, user_id) DO UPDATE
    SET allocated_credits = user_credit_allocations.allocated_credits + p_credits_amount,
        allocated_by = p_allocated_by,
        updated_at = CURRENT_TIMESTAMP;

    -- Update pool allocated amount
    UPDATE organization_credit_pools
    SET allocated_credits = allocated_credits + p_credits_amount,
        updated_at = CURRENT_TIMESTAMP
    WHERE org_id = p_org_id;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- ==================== Views for Convenience ====================

-- View: Organization billing summary
CREATE OR REPLACE VIEW org_billing_summary AS
SELECT
    o.id AS org_id,
    o.name AS org_name,
    os.subscription_plan,
    os.monthly_price,
    os.status AS subscription_status,
    ocp.total_credits,
    ocp.allocated_credits,
    ocp.used_credits,
    ocp.available_credits,
    ocp.lifetime_spent_amount,
    COUNT(DISTINCT om.user_id) AS member_count,
    COUNT(DISTINCT uca.id) AS allocated_users_count
FROM organizations o
LEFT JOIN organization_subscriptions os ON o.id = os.org_id AND os.status = 'active'
LEFT JOIN organization_credit_pools ocp ON o.id = ocp.org_id
LEFT JOIN organization_members om ON o.id = om.org_id
LEFT JOIN user_credit_allocations uca ON o.id = uca.org_id AND uca.is_active = TRUE
WHERE o.status = 'active'
GROUP BY o.id, o.name, os.subscription_plan, os.monthly_price, os.status,
         ocp.total_credits, ocp.allocated_credits, ocp.used_credits,
         ocp.available_credits, ocp.lifetime_spent_amount;

-- View: User credit allocations across all orgs
CREATE OR REPLACE VIEW user_multi_org_credits AS
SELECT
    uca.user_id,
    uca.org_id,
    o.name AS org_name,
    uca.allocated_credits,
    uca.used_credits,
    uca.remaining_credits,
    uca.reset_period,
    uca.next_reset_date,
    uca.is_active
FROM user_credit_allocations uca
JOIN organizations o ON uca.org_id = o.id
WHERE o.status = 'active'
ORDER BY uca.user_id, o.name;

-- View: Top credit users by organization
CREATE OR REPLACE VIEW top_credit_users_by_org AS
SELECT
    org_id,
    user_id,
    SUM(credits_used) AS total_credits_used,
    COUNT(*) AS request_count,
    ARRAY_AGG(DISTINCT service_type) AS services_used,
    MAX(created_at) AS last_usage
FROM credit_usage_attribution
WHERE created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
GROUP BY org_id, user_id
ORDER BY org_id, total_credits_used DESC;

-- View: Organization billing metrics (last 30 days)
CREATE OR REPLACE VIEW org_billing_metrics AS
SELECT
    o.id AS org_id,
    o.name AS org_name,
    COUNT(DISTINCT obh.id) FILTER (WHERE obh.event_type LIKE '%invoice%') AS invoice_count,
    SUM(obh.amount) FILTER (WHERE obh.payment_status = 'paid') AS total_revenue,
    SUM(obh.amount) FILTER (WHERE obh.payment_status = 'failed') AS failed_payments,
    SUM(cua.credits_used) AS total_credits_used,
    COUNT(DISTINCT cua.user_id) AS active_users
FROM organizations o
LEFT JOIN org_billing_history obh ON o.id = obh.org_id
    AND obh.created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
LEFT JOIN credit_usage_attribution cua ON o.id = cua.org_id
    AND cua.created_at >= CURRENT_TIMESTAMP - INTERVAL '30 days'
WHERE o.status = 'active'
GROUP BY o.id, o.name;

-- ==================== Sample Data (Optional - for testing) ====================

-- Uncomment to create sample organization with billing
/*
DO $$
DECLARE
    v_org_id UUID;
BEGIN
    -- Create test organization if doesn't exist
    INSERT INTO organizations (name, display_name, plan_tier, max_seats, status)
    VALUES ('test-org-billing', 'Test Organization (Billing)', 'professional', 10, 'active')
    ON CONFLICT (name) DO NOTHING
    RETURNING id INTO v_org_id;

    IF v_org_id IS NOT NULL THEN
        -- Create subscription
        INSERT INTO organization_subscriptions (org_id, subscription_plan, monthly_price, status)
        VALUES (v_org_id, 'platform', 50.00, 'active');

        -- Create credit pool with 100,000 credits
        INSERT INTO organization_credit_pools (org_id, total_credits, monthly_refresh_amount)
        VALUES (v_org_id, 100000, 100000);

        RAISE NOTICE 'Test organization created with billing setup';
    END IF;
END $$;
*/

-- ==================== Migration Complete ====================

DO $$
BEGIN
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Organization Billing System Migration Complete';
    RAISE NOTICE '=================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'Tables Created:';
    RAISE NOTICE '  - organization_subscriptions (org-level plans)';
    RAISE NOTICE '  - organization_credit_pools (shared credit pools)';
    RAISE NOTICE '  - user_credit_allocations (per-user limits)';
    RAISE NOTICE '  - credit_usage_attribution (detailed audit)';
    RAISE NOTICE '  - org_billing_history (invoices & payments)';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions Created:';
    RAISE NOTICE '  - has_sufficient_credits()';
    RAISE NOTICE '  - deduct_credits()';
    RAISE NOTICE '  - add_credits_to_pool()';
    RAISE NOTICE '  - allocate_credits_to_user()';
    RAISE NOTICE '';
    RAISE NOTICE 'Views Created:';
    RAISE NOTICE '  - org_billing_summary';
    RAISE NOTICE '  - user_multi_org_credits';
    RAISE NOTICE '  - top_credit_users_by_org';
    RAISE NOTICE '  - org_billing_metrics';
    RAISE NOTICE '';
    RAISE NOTICE 'Next Steps:';
    RAISE NOTICE '  1. Run migration: psql -U unicorn -d unicorn_db -f create_org_billing.sql';
    RAISE NOTICE '  2. Create org_billing_api.py backend';
    RAISE NOTICE '  3. Build frontend billing screens';
    RAISE NOTICE '=================================================';
END $$;
