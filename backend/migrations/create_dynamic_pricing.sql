-- ============================================================================
-- Dynamic Pricing System - Database Migration
--
-- This migration creates all tables required for the dynamic pricing system
-- Implements BYOK pricing, Platform pricing, promotional pricing, and audit trail
--
-- Author: System Architecture Designer
-- Date: January 12, 2025
-- ============================================================================

-- Enable UUID extension (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Table 1: pricing_rules
-- Purpose: Unified pricing rules for both BYOK and Platform keys
-- ============================================================================
CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Rule Type: 'byok' or 'platform'
    rule_type VARCHAR(20) NOT NULL CHECK (rule_type IN ('byok', 'platform')),

    -- Provider Configuration (for BYOK only)
    provider VARCHAR(50),  -- 'openrouter', 'openai', 'anthropic', '*' (global)

    -- Tier Configuration (for Platform only)
    tier_code VARCHAR(50),  -- 'trial', 'starter', 'professional', 'enterprise'

    -- Pricing Rules
    markup_type VARCHAR(20) NOT NULL DEFAULT 'percentage' CHECK (markup_type IN ('percentage', 'fixed', 'multiplier', 'none')),
    markup_value DECIMAL(10, 6) NOT NULL DEFAULT 0.10,
    min_charge DECIMAL(10, 6) DEFAULT 0.001,

    -- Base Cost Override (optional, for Platform rules)
    base_cost_override DECIMAL(10, 6),

    -- Per-Provider Overrides (JSON, for Platform rules)
    provider_overrides JSONB DEFAULT '{}'::jsonb,

    -- Free Credit Allocation (for BYOK only, monthly)
    free_credits_monthly DECIMAL(10, 2) DEFAULT 0.00,
    applies_to_tiers TEXT[] DEFAULT ARRAY['trial', 'starter', 'professional', 'enterprise'],

    -- Metadata
    rule_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,  -- Higher priority = applied first

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    updated_by VARCHAR(100),

    -- Constraints
    CONSTRAINT check_byok_has_provider CHECK (rule_type != 'byok' OR provider IS NOT NULL),
    CONSTRAINT check_platform_has_tier CHECK (rule_type != 'platform' OR tier_code IS NOT NULL)
);

-- Indexes for pricing_rules
CREATE INDEX IF NOT EXISTS idx_pricing_rules_type ON pricing_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_pricing_rules_provider ON pricing_rules(provider) WHERE is_active = TRUE AND rule_type = 'byok';
CREATE INDEX IF NOT EXISTS idx_pricing_rules_tier ON pricing_rules(tier_code) WHERE is_active = TRUE AND rule_type = 'platform';
CREATE INDEX IF NOT EXISTS idx_pricing_rules_active ON pricing_rules(is_active, priority);

-- Unique indexes (partial indexes for conditional uniqueness)
CREATE UNIQUE INDEX IF NOT EXISTS idx_pricing_rules_unique_byok ON pricing_rules(provider, priority) WHERE rule_type = 'byok';
CREATE UNIQUE INDEX IF NOT EXISTS idx_pricing_rules_unique_platform ON pricing_rules(tier_code) WHERE rule_type = 'platform';

-- ============================================================================
-- Table 2: tier_pricing_overrides
-- Purpose: Tier-specific pricing overrides (DEPRECATED - merged into pricing_rules)
-- Keeping for backward compatibility
-- ============================================================================
CREATE TABLE IF NOT EXISTS tier_pricing_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tier_code VARCHAR(50) NOT NULL UNIQUE,
    markup_percentage DECIMAL(10, 6) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tier_pricing_tier ON tier_pricing_overrides(tier_code) WHERE is_active = TRUE;

-- ============================================================================
-- Table 3: promotional_pricing (Enhanced credit_packages)
-- Purpose: Promotional pricing and time-limited offers
-- ============================================================================
-- Note: credit_packages table already exists, we'll add promotion fields
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS promo_price DECIMAL(10, 2);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS promo_code VARCHAR(50);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS promo_start_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS promo_end_date TIMESTAMP WITH TIME ZONE;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT FALSE;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS badge_text VARCHAR(50);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS available_to_tiers TEXT[] DEFAULT ARRAY['trial', 'starter', 'professional', 'enterprise'];
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS max_purchases_per_user INTEGER;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS max_purchases_per_month INTEGER;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT ARRAY[]::TEXT[];

-- Add index for promo codes
CREATE INDEX IF NOT EXISTS idx_credit_packages_promo ON credit_packages(promo_code) WHERE promo_code IS NOT NULL;

-- ============================================================================
-- Table 4: pricing_audit_log
-- Purpose: Audit trail for all pricing configuration changes
-- ============================================================================
CREATE TABLE IF NOT EXISTS pricing_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Change Details
    change_type VARCHAR(50) NOT NULL,  -- 'pricing_rule_create', 'pricing_rule_update', 'package_update', etc.
    entity_id UUID NOT NULL,           -- ID of the changed entity
    entity_type VARCHAR(50) NOT NULL,  -- 'pricing_rule', 'credit_package', 'tier_override'

    -- Change Data
    old_values JSONB,                  -- Previous values
    new_values JSONB,                  -- New values
    change_summary TEXT,               -- Human-readable summary

    -- User Details
    changed_by VARCHAR(100) NOT NULL,
    change_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for pricing_audit_log
CREATE INDEX IF NOT EXISTS idx_pricing_audit_type ON pricing_audit_log(change_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pricing_audit_entity ON pricing_audit_log(entity_id, entity_type);
CREATE INDEX IF NOT EXISTS idx_pricing_audit_user ON pricing_audit_log(changed_by, created_at DESC);

-- ============================================================================
-- Table 5: user_byok_credits
-- Purpose: Track free monthly BYOK credits per user
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_byok_credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User Details
    user_id VARCHAR(100) NOT NULL,
    tier_code VARCHAR(50) NOT NULL,

    -- Credits
    monthly_allowance DECIMAL(10, 2) NOT NULL DEFAULT 0.00,  -- Free credits per month
    credits_used DECIMAL(10, 2) DEFAULT 0.00,                 -- Credits used this period
    credits_remaining DECIMAL(10, 2) DEFAULT 0.00,            -- Remaining free credits

    -- Reset Tracking
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    next_reset TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '1 month'),

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT unique_user_tier UNIQUE (user_id, tier_code)
);

-- Indexes for user_byok_credits
CREATE INDEX IF NOT EXISTS idx_user_byok_credits_user ON user_byok_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_byok_credits_reset ON user_byok_credits(next_reset);

-- ============================================================================
-- Function: reset_monthly_byok_credits
-- Purpose: Reset BYOK credits for users whose reset date has passed
-- ============================================================================
CREATE OR REPLACE FUNCTION reset_monthly_byok_credits()
RETURNS INTEGER AS $$
DECLARE
    reset_count INTEGER := 0;
BEGIN
    -- Reset credits for users whose reset date has passed
    WITH reset_users AS (
        UPDATE user_byok_credits
        SET credits_used = 0.00,
            credits_remaining = monthly_allowance,
            last_reset = NOW(),
            next_reset = NOW() + INTERVAL '1 month',
            updated_at = NOW()
        WHERE next_reset <= NOW()
        RETURNING id
    )
    SELECT COUNT(*) INTO reset_count FROM reset_users;

    RETURN reset_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Function: log_pricing_change
-- Purpose: Automatically log pricing changes to audit table
-- ============================================================================
CREATE OR REPLACE FUNCTION log_pricing_change()
RETURNS TRIGGER AS $$
DECLARE
    changed_by_value VARCHAR(100);
BEGIN
    -- Try to get updated_by from NEW, fallback to created_by, then 'system'
    BEGIN
        changed_by_value := COALESCE(
            (SELECT value FROM jsonb_each_text(to_jsonb(NEW)) WHERE key = 'updated_by'),
            (SELECT value FROM jsonb_each_text(to_jsonb(NEW)) WHERE key = 'created_by'),
            'system'
        );
    EXCEPTION WHEN OTHERS THEN
        changed_by_value := 'system';
    END;

    INSERT INTO pricing_audit_log (
        change_type, entity_id, entity_type, old_values, new_values, changed_by
    )
    VALUES (
        TG_TABLE_NAME || '_' || TG_OP,
        NEW.id,
        TG_TABLE_NAME,
        row_to_json(OLD),
        row_to_json(NEW),
        changed_by_value
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for pricing_rules
DROP TRIGGER IF EXISTS trigger_pricing_rules_audit ON pricing_rules;
CREATE TRIGGER trigger_pricing_rules_audit
AFTER INSERT OR UPDATE ON pricing_rules
FOR EACH ROW EXECUTE FUNCTION log_pricing_change();

-- Triggers for credit_packages
DROP TRIGGER IF EXISTS trigger_credit_packages_audit ON credit_packages;
CREATE TRIGGER trigger_credit_packages_audit
AFTER UPDATE ON credit_packages
FOR EACH ROW EXECUTE FUNCTION log_pricing_change();

-- ============================================================================
-- Default Pricing Rules
-- ============================================================================

-- BYOK Pricing Rules
INSERT INTO pricing_rules (rule_type, provider, markup_type, markup_value, free_credits_monthly, applies_to_tiers, rule_name, description, priority)
VALUES
-- Global default (10% markup)
('byok', '*', 'percentage', 0.10, 0.00, ARRAY['trial', 'starter', 'professional', 'enterprise'], 'Global BYOK Markup', 'Default 10% markup for all BYOK providers', 0),

-- OpenRouter (5% markup - preferred provider)
('byok', 'openrouter', 'percentage', 0.05, 100.00, ARRAY['professional', 'enterprise'], 'OpenRouter BYOK', 'Preferred provider - lower markup with 100 free monthly credits', 10),

-- OpenAI (15% markup - premium)
('byok', 'openai', 'percentage', 0.15, 0.00, ARRAY['professional', 'enterprise'], 'OpenAI BYOK', 'Premium provider - higher markup', 10),

-- Anthropic (15% markup - premium)
('byok', 'anthropic', 'percentage', 0.15, 0.00, ARRAY['professional', 'enterprise'], 'Anthropic BYOK', 'Premium provider - higher markup', 10),

-- HuggingFace (8% markup - community)
('byok', 'huggingface', 'percentage', 0.08, 50.00, ARRAY['starter', 'professional', 'enterprise'], 'HuggingFace BYOK', 'Community provider - mid-tier markup with 50 free monthly credits', 10)
ON CONFLICT DO NOTHING;

-- Platform Pricing Rules (matching current TIER_MARKUP)
INSERT INTO pricing_rules (rule_type, tier_code, markup_type, markup_value, rule_name, description)
VALUES
('platform', 'trial', 'percentage', 0.00, 'Trial Tier Markup', 'Free tier - platform absorbs costs'),
('platform', 'starter', 'percentage', 0.40, 'Starter Tier Markup', '40% markup for starter tier'),
('platform', 'professional', 'percentage', 0.60, 'Professional Tier Markup', '60% markup for professional tier'),
('platform', 'enterprise', 'percentage', 0.80, 'Enterprise Tier Markup', '80% markup for enterprise tier')
ON CONFLICT DO NOTHING;

-- ============================================================================
-- Enhanced Credit Packages (update existing records)
-- ============================================================================
UPDATE credit_packages
SET
    tags = ARRAY['starter'],
    available_to_tiers = ARRAY['trial', 'starter', 'professional', 'enterprise']
WHERE package_code = 'starter';

UPDATE credit_packages
SET
    tags = ARRAY['basic', 'value'],
    available_to_tiers = ARRAY['trial', 'starter', 'professional', 'enterprise'],
    is_featured = FALSE
WHERE package_code = 'standard';

UPDATE credit_packages
SET
    tags = ARRAY['professional', 'popular'],
    available_to_tiers = ARRAY['trial', 'starter', 'professional', 'enterprise'],
    is_featured = TRUE,
    badge_text = 'Most Popular'
WHERE package_code = 'pro';

UPDATE credit_packages
SET
    tags = ARRAY['enterprise', 'best-value'],
    available_to_tiers = ARRAY['professional', 'enterprise'],
    is_featured = FALSE,
    badge_text = 'Best Value'
WHERE package_code = 'enterprise';

-- ============================================================================
-- Completion Message
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '╔════════════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║ Dynamic Pricing System Migration Complete!                     ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║ Tables created/updated:                                        ║';
    RAISE NOTICE '║   ✓ pricing_rules (unified BYOK + Platform)                   ║';
    RAISE NOTICE '║   ✓ tier_pricing_overrides (backward compatibility)           ║';
    RAISE NOTICE '║   ✓ credit_packages (enhanced with promotions)                ║';
    RAISE NOTICE '║   ✓ pricing_audit_log (audit trail)                           ║';
    RAISE NOTICE '║   ✓ user_byok_credits (free monthly credits)                  ║';
    RAISE NOTICE '║                                                                ║';
    RAISE NOTICE '║ Functions created:                                             ║';
    RAISE NOTICE '║   ✓ reset_monthly_byok_credits()                              ║';
    RAISE NOTICE '║   ✓ log_pricing_change()                                      ║';
    RAISE NOTICE '║                                                                ║';
    RAISE NOTICE '║ Default rules:                                                 ║';
    RAISE NOTICE '║   ✓ 5 BYOK pricing rules (OpenRouter, OpenAI, Anthropic...)  ║';
    RAISE NOTICE '║   ✓ 4 Platform tier rules (0-80%% markup)                     ║';
    RAISE NOTICE '║   ✓ 4 Credit packages enhanced                                ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════════════╝';
END $$;
