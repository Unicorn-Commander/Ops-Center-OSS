-- Extensions Marketplace Schema for Ops-Center
-- Phase 1 MVP - 8 Core Tables
-- Database: PostgreSQL (unicorn_db)
-- Created: 2025-11-01

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- TABLE 1: add_ons (Product Catalog)
-- Stores all available extensions/add-ons in the marketplace
-- ============================================================================
CREATE TABLE IF NOT EXISTS add_ons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL CHECK (category IN ('ai-services', 'infrastructure', 'analytics', 'development', 'productivity')),
    base_price DECIMAL(10,2) NOT NULL CHECK (base_price >= 0),
    billing_type VARCHAR(50) NOT NULL CHECK (billing_type IN ('one_time', 'monthly', 'annual', 'usage_based')),
    features JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of feature_keys this add-on provides
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional flexible data
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 2: user_add_ons (User Purchases/Subscriptions)
-- Tracks which add-ons each user has purchased and their status
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_add_ons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Keycloak user ID
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'expired', 'pending', 'suspended')),
    purchased_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP, -- NULL for lifetime/one-time purchases
    lago_subscription_id VARCHAR(255), -- Lago integration
    auto_renew BOOLEAN DEFAULT TRUE,
    cancellation_reason TEXT,
    cancelled_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_user_addon UNIQUE(user_id, add_on_id)
);

-- ============================================================================
-- TABLE 3: add_on_purchases (Transaction History)
-- Records all payment transactions for add-on purchases
-- ============================================================================
CREATE TABLE IF NOT EXISTS add_on_purchases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Keycloak user ID
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE RESTRICT,
    amount DECIMAL(10,2) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(3) DEFAULT 'USD' NOT NULL,
    stripe_payment_id VARCHAR(255), -- Stripe payment intent ID
    lago_invoice_id VARCHAR(255), -- Lago invoice ID
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded', 'disputed')),
    payment_method VARCHAR(50), -- 'credit_card', 'paypal', 'crypto', etc.
    refund_amount DECIMAL(10,2) DEFAULT 0,
    refunded_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional transaction data
    purchased_at TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 4: add_on_bundles (Bundle Definitions)
-- Defines bundles/packages of multiple add-ons with discounts
-- ============================================================================
CREATE TABLE IF NOT EXISTS add_on_bundles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    add_on_ids UUID[] NOT NULL, -- Array of add_on IDs in bundle
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

-- ============================================================================
-- TABLE 5: pricing_rules (Dynamic Pricing)
-- Defines tier-based and conditional pricing rules
-- ============================================================================
CREATE TABLE IF NOT EXISTS pricing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    tier_code VARCHAR(50), -- 'vip_founder', 'byok', 'managed', etc. (references subscription_tiers)
    discount_percent DECIMAL(5,2) DEFAULT 0 CHECK (discount_percent >= 0 AND discount_percent <= 100),
    discount_amount DECIMAL(10,2) DEFAULT 0 CHECK (discount_amount >= 0),
    conditions JSONB DEFAULT '{}'::jsonb, -- e.g., {"min_quantity": 3, "requires_addon": ["uuid1", "uuid2"]}
    priority INTEGER DEFAULT 0, -- Higher priority rules apply first
    is_active BOOLEAN DEFAULT TRUE,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TABLE 6: cart_items (Shopping Cart)
-- Stores items users have added to cart but not yet purchased
-- ============================================================================
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL, -- Keycloak user ID
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1 CHECK (quantity > 0),
    billing_type VARCHAR(50), -- Override billing type if user selects different option
    added_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_cart_item UNIQUE(user_id, add_on_id)
);

-- ============================================================================
-- TABLE 7: add_on_features (Feature Mappings)
-- Maps add-ons to specific features they enable (references feature_definitions)
-- ============================================================================
CREATE TABLE IF NOT EXISTS add_on_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL, -- References feature_definitions table
    enabled BOOLEAN DEFAULT TRUE,
    configuration JSONB DEFAULT '{}'::jsonb, -- Feature-specific configuration
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_addon_feature UNIQUE(add_on_id, feature_key)
);

-- ============================================================================
-- TABLE 8: promotional_codes (Discount Codes)
-- Manages promotional/discount codes for marketing campaigns
-- ============================================================================
CREATE TABLE IF NOT EXISTS promotional_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) NOT NULL CHECK (discount_type IN ('percentage', 'fixed_amount')),
    discount_value DECIMAL(10,2) NOT NULL CHECK (discount_value > 0),
    max_uses INTEGER, -- NULL for unlimited
    current_uses INTEGER DEFAULT 0,
    applicable_to UUID[], -- Array of add_on_ids (NULL for all)
    min_purchase_amount DECIMAL(10,2) DEFAULT 0,
    user_restrictions JSONB DEFAULT '{}'::jsonb, -- e.g., {"tier": "vip_founder", "first_purchase_only": true}
    expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255), -- Admin user ID
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to all tables with updated_at
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
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE add_ons IS 'Product catalog for all available extensions and add-ons';
COMMENT ON TABLE user_add_ons IS 'Tracks user purchases and subscription status for add-ons';
COMMENT ON TABLE add_on_purchases IS 'Complete transaction history for all add-on purchases';
COMMENT ON TABLE add_on_bundles IS 'Bundle definitions with multiple add-ons and discounts';
COMMENT ON TABLE pricing_rules IS 'Dynamic pricing rules based on tiers and conditions';
COMMENT ON TABLE cart_items IS 'Shopping cart for add-ons before checkout';
COMMENT ON TABLE add_on_features IS 'Maps add-ons to specific feature flags they enable';
COMMENT ON TABLE promotional_codes IS 'Promotional and discount codes for marketing campaigns';

-- Schema creation complete
-- Run extensions_indexes.sql next for performance optimization
