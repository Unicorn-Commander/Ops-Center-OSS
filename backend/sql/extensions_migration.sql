-- Extensions Marketplace Migration Script
-- Alembic-style migration for production deployment
-- Database: PostgreSQL (unicorn_db)
-- Migration Version: 001_create_extensions_marketplace
-- Created: 2025-11-01

-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================

-- Create migrations tracking table if it doesn't exist
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Check if this migration has already been applied
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM alembic_version WHERE version_num = '001_extensions_marketplace') THEN
        RAISE EXCEPTION 'Migration 001_extensions_marketplace has already been applied';
    END IF;
END $$;

-- ============================================================================
-- PRE-MIGRATION CHECKS
-- ============================================================================

-- Verify database is unicorn_db
DO $$
BEGIN
    IF current_database() != 'unicorn_db' THEN
        RAISE EXCEPTION 'This migration must be run on unicorn_db database';
    END IF;
END $$;

-- Verify pgcrypto extension is available
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_available_extensions WHERE name = 'pgcrypto') THEN
        RAISE EXCEPTION 'pgcrypto extension is required but not available';
    END IF;
END $$;

-- ============================================================================
-- BEGIN MIGRATION
-- ============================================================================

BEGIN;

RAISE NOTICE 'Starting migration 001_extensions_marketplace...';

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- CREATE TABLES
-- ============================================================================

RAISE NOTICE 'Creating table: add_ons';
CREATE TABLE IF NOT EXISTS add_ons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL CHECK (category IN ('ai-services', 'infrastructure', 'analytics', 'development', 'productivity')),
    base_price DECIMAL(10,2) NOT NULL CHECK (base_price >= 0),
    billing_type VARCHAR(50) NOT NULL CHECK (billing_type IN ('one_time', 'monthly', 'annual', 'usage_based')),
    features JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

RAISE NOTICE 'Creating table: user_add_ons';
CREATE TABLE IF NOT EXISTS user_add_ons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'pending', 'suspended')),
    purchased_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    lago_subscription_id VARCHAR(255),
    auto_renew BOOLEAN DEFAULT TRUE,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_user_addon UNIQUE(user_id, add_on_id)
);

RAISE NOTICE 'Creating table: add_on_purchases';
CREATE TABLE IF NOT EXISTS add_on_purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE RESTRICT,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    stripe_payment_id VARCHAR(255),
    lago_invoice_id VARCHAR(255),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'disputed')),
    payment_method VARCHAR(50),
    refund_amount DECIMAL(10,2) DEFAULT 0,
    refunded_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    purchased_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

RAISE NOTICE 'Creating table: add_on_bundles';
CREATE TABLE IF NOT EXISTS add_on_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    add_on_ids UUID[] NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

RAISE NOTICE 'Creating table: pricing_rules';
CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    tier_code VARCHAR(50),
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    conditions JSONB DEFAULT '{}'::jsonb,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

RAISE NOTICE 'Creating table: cart_items';
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
    billing_type VARCHAR(50),
    added_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_cart_item UNIQUE(user_id, add_on_id)
);

RAISE NOTICE 'Creating table: add_on_features';
CREATE TABLE IF NOT EXISTS add_on_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_addon_feature UNIQUE(add_on_id, feature_key)
);

RAISE NOTICE 'Creating table: promotional_codes';
CREATE TABLE IF NOT EXISTS promotional_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount')),
    discount_value DECIMAL(10,2) NOT NULL CHECK (discount_value > 0),
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    applicable_to UUID[],
    min_purchase_amount DECIMAL(10,2) DEFAULT 0,
    user_restrictions JSONB DEFAULT '{}'::jsonb,
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- CREATE INDEXES
-- ============================================================================

RAISE NOTICE 'Creating indexes...';

-- add_ons indexes
CREATE INDEX idx_add_ons_category ON add_ons(category) WHERE is_active = TRUE;
CREATE INDEX idx_add_ons_active ON add_ons(is_active);
CREATE INDEX idx_add_ons_features ON add_ons USING GIN(features);
CREATE INDEX idx_add_ons_price ON add_ons(base_price) WHERE is_active = TRUE;

-- user_add_ons indexes (critical for performance)
CREATE INDEX idx_user_add_ons_user_id ON user_add_ons(user_id);
CREATE INDEX idx_user_add_ons_user_addon ON user_add_ons(user_id, add_on_id);
CREATE INDEX idx_user_add_ons_status ON user_add_ons(status) WHERE status = 'active';
CREATE INDEX idx_user_add_ons_expires ON user_add_ons(expires_at) WHERE expires_at IS NOT NULL AND status = 'active';
CREATE INDEX idx_user_add_ons_lago ON user_add_ons(lago_subscription_id) WHERE lago_subscription_id IS NOT NULL;

-- add_on_purchases indexes
CREATE INDEX idx_add_on_purchases_user_date ON add_on_purchases(user_id, purchased_at DESC);
CREATE INDEX idx_add_on_purchases_stripe ON add_on_purchases(stripe_payment_id) WHERE stripe_payment_id IS NOT NULL;
CREATE INDEX idx_add_on_purchases_lago ON add_on_purchases(lago_invoice_id) WHERE lago_invoice_id IS NOT NULL;
CREATE INDEX idx_add_on_purchases_status ON add_on_purchases(status, purchased_at DESC);
CREATE INDEX idx_add_on_purchases_addon ON add_on_purchases(add_on_id, purchased_at DESC);
CREATE INDEX idx_add_on_purchases_revenue ON add_on_purchases(purchased_at, amount) WHERE status = 'completed';

-- cart_items indexes
CREATE INDEX idx_cart_items_user ON cart_items(user_id, added_at DESC);
CREATE INDEX idx_cart_items_user_addon ON cart_items(user_id, add_on_id);
CREATE INDEX idx_cart_items_added_at ON cart_items(added_at);

-- add_on_features indexes
CREATE INDEX idx_add_on_features_addon ON add_on_features(add_on_id) WHERE enabled = TRUE;
CREATE INDEX idx_add_on_features_key ON add_on_features(feature_key) WHERE enabled = TRUE;
CREATE INDEX idx_add_on_features_config ON add_on_features USING GIN(configuration);

-- promotional_codes indexes
CREATE UNIQUE INDEX idx_promotional_codes_code ON promotional_codes(code);
CREATE INDEX idx_promotional_codes_active ON promotional_codes(is_active) WHERE is_active = TRUE AND expires_at > NOW();
CREATE INDEX idx_promotional_codes_applicable ON promotional_codes USING GIN(applicable_to);
CREATE INDEX idx_promotional_codes_expires ON promotional_codes(expires_at) WHERE is_active = TRUE;

-- Other indexes
CREATE INDEX idx_add_on_bundles_active ON add_on_bundles(is_active);
CREATE INDEX idx_add_on_bundles_addon_ids ON add_on_bundles USING GIN(add_on_ids);
CREATE INDEX idx_pricing_rules_addon ON pricing_rules(add_on_id) WHERE is_active = TRUE;
CREATE INDEX idx_pricing_rules_tier ON pricing_rules(tier_code) WHERE is_active = TRUE;
CREATE INDEX idx_pricing_rules_priority ON pricing_rules(priority DESC, add_on_id) WHERE is_active = TRUE;

-- ============================================================================
-- CREATE TRIGGERS
-- ============================================================================

RAISE NOTICE 'Creating triggers...';

-- Trigger function for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers
CREATE TRIGGER update_add_ons_updated_at BEFORE UPDATE ON add_ons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_add_ons_updated_at BEFORE UPDATE ON user_add_ons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_add_on_bundles_updated_at BEFORE UPDATE ON add_on_bundles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pricing_rules_updated_at BEFORE UPDATE ON pricing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_add_on_features_updated_at BEFORE UPDATE ON add_on_features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promotional_codes_updated_at BEFORE UPDATE ON promotional_codes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ADD TABLE COMMENTS
-- ============================================================================

COMMENT ON TABLE add_ons IS 'Product catalog for all available extensions and add-ons';
COMMENT ON TABLE user_add_ons IS 'Tracks user purchases and subscription status for add-ons';
COMMENT ON TABLE add_on_purchases IS 'Complete transaction history for all add-on purchases';
COMMENT ON TABLE add_on_bundles IS 'Bundle definitions with multiple add-ons and discounts';
COMMENT ON TABLE pricing_rules IS 'Dynamic pricing rules based on tiers and conditions';
COMMENT ON TABLE cart_items IS 'Shopping cart for add-ons before checkout';
COMMENT ON TABLE add_on_features IS 'Maps add-ons to specific feature flags they enable';
COMMENT ON TABLE promotional_codes IS 'Promotional and discount codes for marketing campaigns';

-- ============================================================================
-- RECORD MIGRATION
-- ============================================================================

INSERT INTO alembic_version (version_num) VALUES ('001_extensions_marketplace');

RAISE NOTICE 'Migration 001_extensions_marketplace completed successfully';

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION
-- ============================================================================

-- Verify all tables were created
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'add_ons', 'user_add_ons', 'add_on_purchases', 'add_on_bundles',
        'pricing_rules', 'cart_items', 'add_on_features', 'promotional_codes'
    );

    IF table_count != 8 THEN
        RAISE EXCEPTION 'Expected 8 tables but found %', table_count;
    END IF;

    RAISE NOTICE 'Verification: All 8 tables created successfully';
END $$;

-- ============================================================================
-- ROLLBACK SCRIPT (for emergencies)
-- ============================================================================

-- To rollback this migration, run:
/*
BEGIN;

DROP TABLE IF EXISTS promotional_codes CASCADE;
DROP TABLE IF EXISTS add_on_features CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS pricing_rules CASCADE;
DROP TABLE IF EXISTS add_on_bundles CASCADE;
DROP TABLE IF EXISTS add_on_purchases CASCADE;
DROP TABLE IF EXISTS user_add_ons CASCADE;
DROP TABLE IF EXISTS add_ons CASCADE;

DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

DELETE FROM alembic_version WHERE version_num = '001_extensions_marketplace';

COMMIT;
*/

-- ============================================================================
-- NEXT STEPS
-- ============================================================================

-- After this migration:
-- 1. Run extensions_seed_data.sql to populate with initial data
-- 2. Verify indexes with: SELECT * FROM pg_indexes WHERE tablename LIKE 'add_%';
-- 3. Test queries with: \i backend/tests/test_extensions_schema.sql
-- 4. Update application ORM models to match schema
-- 5. Run integration tests

-- Migration complete!
