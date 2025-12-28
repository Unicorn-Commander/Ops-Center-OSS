-- Extensions Marketplace Database Schema
-- Phase 1 MVP: Catalog, Cart, Purchase APIs
-- Created: 2025-11-01

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Add-Ons Catalog Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS add_ons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    long_description TEXT,
    category VARCHAR(100) NOT NULL, -- ai_tools, monitoring, storage, security, etc.

    -- Pricing
    base_price DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    billing_type VARCHAR(50) NOT NULL DEFAULT 'one_time', -- one_time, monthly, annually
    trial_days INTEGER DEFAULT 0,

    -- Features & Metadata
    features JSONB DEFAULT '[]'::jsonb, -- Array of feature descriptions
    metadata JSONB DEFAULT '{}'::jsonb, -- Additional metadata
    icon_url VARCHAR(512),
    banner_url VARCHAR(512),
    documentation_url VARCHAR(512),
    support_url VARCHAR(512),

    -- Display Flags
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT TRUE, -- If false, only visible to admins

    -- Metrics
    install_count INTEGER DEFAULT 0,
    rating_avg DECIMAL(3, 2) DEFAULT 0.00, -- 0.00 to 5.00
    rating_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL, -- Keycloak user ID

    -- Indexes
    CONSTRAINT add_ons_category_check CHECK (category IN ('ai_tools', 'monitoring', 'storage', 'security', 'networking', 'analytics', 'integrations', 'utilities', 'other'))
);

CREATE INDEX idx_add_ons_category ON add_ons(category);
CREATE INDEX idx_add_ons_is_active ON add_ons(is_active);
CREATE INDEX idx_add_ons_is_featured ON add_ons(is_featured);
CREATE INDEX idx_add_ons_created_at ON add_ons(created_at DESC);

-- ============================================================================
-- Shopping Cart Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS cart (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL, -- Keycloak user ID
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL DEFAULT 1,

    -- Pricing snapshot (in case add-on price changes)
    price_snapshot DECIMAL(10, 2) NOT NULL,
    billing_type_snapshot VARCHAR(50) NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT cart_quantity_positive CHECK (quantity > 0),
    CONSTRAINT cart_unique_user_addon UNIQUE (user_id, add_on_id)
);

CREATE INDEX idx_cart_user_id ON cart(user_id);
CREATE INDEX idx_cart_add_on_id ON cart(add_on_id);

-- ============================================================================
-- Purchases Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS addon_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL, -- Keycloak user ID
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE RESTRICT,

    -- Purchase Details
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    billing_type VARCHAR(50) NOT NULL, -- one_time, monthly, annually

    -- Subscription Management (for recurring billing)
    subscription_id VARCHAR(255), -- Stripe subscription ID
    subscription_status VARCHAR(50), -- active, canceled, past_due, etc.
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,

    -- Payment Processing
    stripe_customer_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),
    stripe_invoice_id VARCHAR(255),
    payment_method VARCHAR(50), -- card, bank_transfer, etc.

    -- Status
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- pending, active, canceled, expired, failed
    is_active BOOLEAN DEFAULT FALSE,

    -- Activation
    activated_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE, -- For time-limited add-ons

    -- Timestamps
    purchased_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT addon_purchases_status_check CHECK (status IN ('pending', 'active', 'canceled', 'expired', 'failed', 'refunded'))
);

CREATE INDEX idx_addon_purchases_user_id ON addon_purchases(user_id);
CREATE INDEX idx_addon_purchases_add_on_id ON addon_purchases(add_on_id);
CREATE INDEX idx_addon_purchases_status ON addon_purchases(status);
CREATE INDEX idx_addon_purchases_is_active ON addon_purchases(is_active);
CREATE INDEX idx_addon_purchases_subscription_id ON addon_purchases(subscription_id);

-- ============================================================================
-- Add-On Features Table (defines what features an add-on grants)
-- ============================================================================
CREATE TABLE IF NOT EXISTS addon_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    feature_key VARCHAR(255) NOT NULL, -- e.g., 'gpu_monitoring', 'advanced_analytics'
    feature_value JSONB DEFAULT '{}'::jsonb, -- Configuration/settings for the feature

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT addon_features_unique_addon_key UNIQUE (add_on_id, feature_key)
);

CREATE INDEX idx_addon_features_add_on_id ON addon_features(add_on_id);
CREATE INDEX idx_addon_features_feature_key ON addon_features(feature_key);

-- ============================================================================
-- Promotional Codes Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS promo_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,

    -- Discount Configuration
    discount_type VARCHAR(20) NOT NULL, -- percentage, fixed_amount
    discount_value DECIMAL(10, 2) NOT NULL, -- 10.00 for 10% or $10.00

    -- Restrictions
    min_purchase_amount DECIMAL(10, 2) DEFAULT 0.00,
    max_uses INTEGER, -- NULL for unlimited
    times_used INTEGER DEFAULT 0,

    -- Applicable Add-ons (NULL = all add-ons)
    applicable_addon_ids JSONB DEFAULT NULL, -- Array of add-on IDs

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP WITH TIME ZONE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,

    -- Constraints
    CONSTRAINT promo_codes_discount_type_check CHECK (discount_type IN ('percentage', 'fixed_amount')),
    CONSTRAINT promo_codes_discount_value_positive CHECK (discount_value > 0)
);

CREATE INDEX idx_promo_codes_code ON promo_codes(code);
CREATE INDEX idx_promo_codes_is_active ON promo_codes(is_active);
CREATE INDEX idx_promo_codes_expires_at ON promo_codes(expires_at);

-- ============================================================================
-- Add-On Reviews/Ratings Table (Future Phase 2)
-- ============================================================================
CREATE TABLE IF NOT EXISTS addon_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    add_on_id UUID NOT NULL REFERENCES add_ons(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL, -- Keycloak user ID

    -- Review Content
    rating INTEGER NOT NULL, -- 1 to 5 stars
    title VARCHAR(255),
    review_text TEXT,

    -- Status
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT TRUE, -- For moderation

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT addon_reviews_rating_check CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT addon_reviews_unique_user_addon UNIQUE (add_on_id, user_id)
);

CREATE INDEX idx_addon_reviews_add_on_id ON addon_reviews(add_on_id);
CREATE INDEX idx_addon_reviews_user_id ON addon_reviews(user_id);
CREATE INDEX idx_addon_reviews_rating ON addon_reviews(rating);

-- ============================================================================
-- Trigger: Update updated_at timestamp automatically
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_add_ons_updated_at BEFORE UPDATE ON add_ons
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_updated_at BEFORE UPDATE ON cart
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addon_purchases_updated_at BEFORE UPDATE ON addon_purchases
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addon_features_updated_at BEFORE UPDATE ON addon_features
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promo_codes_updated_at BEFORE UPDATE ON promo_codes
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addon_reviews_updated_at BEFORE UPDATE ON addon_reviews
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Seed Data: Sample Add-Ons for Testing
-- ============================================================================
INSERT INTO add_ons (name, slug, description, category, base_price, billing_type, features, is_featured, created_by)
VALUES
('Advanced GPU Monitoring', 'advanced-gpu-monitoring',
 'Real-time GPU metrics with historical data and alerting',
 'monitoring', 9.99, 'monthly',
 '["Real-time GPU utilization", "Memory tracking", "Temperature alerts", "Performance graphs"]'::jsonb,
 true, 'system'),

('LiteLLM Pro', 'litellm-pro',
 'Enhanced LLM routing with cost optimization and analytics',
 'ai_tools', 29.99, 'monthly',
 '["100+ LLM models", "Cost optimization", "Usage analytics", "Priority support"]'::jsonb,
 true, 'system'),

('S3-Compatible Storage', 's3-compatible-storage',
 'MinIO-based object storage for backups and file uploads',
 'storage', 19.99, 'monthly',
 '["100GB storage", "S3 API compatibility", "Encryption at rest", "CDN integration"]'::jsonb,
 false, 'system'),

('Advanced Firewall Rules', 'advanced-firewall-rules',
 'DDoS protection and geo-blocking with Cloudflare integration',
 'security', 14.99, 'monthly',
 '["DDoS protection", "Geo-blocking", "Rate limiting", "WAF rules"]'::jsonb,
 true, 'system'),

('Grafana Analytics Suite', 'grafana-analytics',
 'Pre-built Grafana dashboards for all UC-Cloud services',
 'analytics', 0.00, 'one_time',
 '["15+ dashboards", "Real-time metrics", "Custom alerts", "Export reports"]'::jsonb,
 false, 'system'),

('Center-Deep Premium', 'center-deep-premium',
 'Enhanced metasearch with unlimited queries and priority indexing',
 'integrations', 49.99, 'monthly',
 '["Unlimited searches", "Priority indexing", "Custom search engines", "API access"]'::jsonb,
 true, 'system')
ON CONFLICT (slug) DO NOTHING;

-- ============================================================================
-- End of Migration
-- ============================================================================
COMMENT ON TABLE add_ons IS 'Extensions marketplace catalog - available add-ons for purchase';
COMMENT ON TABLE cart IS 'User shopping carts for add-on purchases';
COMMENT ON TABLE addon_purchases IS 'Completed add-on purchases and subscriptions';
COMMENT ON TABLE addon_features IS 'Features granted by add-ons';
COMMENT ON TABLE promo_codes IS 'Promotional discount codes';
COMMENT ON TABLE addon_reviews IS 'User reviews and ratings for add-ons';
