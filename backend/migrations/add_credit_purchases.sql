-- ============================================================================
-- Credit Purchase System - Database Migration
--
-- This migration creates tables for one-time credit purchases via Stripe
--
-- Author: Backend Team Lead
-- Date: November 12, 2025
-- ============================================================================

-- Enable UUID extension (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- credit_purchases table
-- Tracks all one-time credit purchases made via Stripe
CREATE TABLE IF NOT EXISTS credit_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,

    -- Purchase details
    package_name VARCHAR(100) NOT NULL,
    amount_credits DECIMAL(12, 6) NOT NULL,
    amount_paid DECIMAL(10, 2) NOT NULL,
    discount_applied DECIMAL(10, 2) DEFAULT 0.0,

    -- Stripe integration
    stripe_payment_id VARCHAR(255) UNIQUE,
    stripe_checkout_session_id VARCHAR(255),
    stripe_payment_intent_id VARCHAR(255),

    -- Status tracking
    status VARCHAR(50) DEFAULT 'pending' NOT NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Metadata
    metadata JSONB,

    -- Constraints
    CONSTRAINT valid_purchase_status CHECK (
        status IN ('pending', 'processing', 'completed', 'failed', 'refunded')
    ),
    CONSTRAINT amount_credits_positive CHECK (amount_credits > 0),
    CONSTRAINT amount_paid_positive CHECK (amount_paid > 0)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_credit_purchases_user_id ON credit_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_status ON credit_purchases(status);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_created_at ON credit_purchases(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_stripe_payment ON credit_purchases(stripe_payment_id);
CREATE INDEX IF NOT EXISTS idx_credit_purchases_stripe_session ON credit_purchases(stripe_checkout_session_id);

-- credit_packages table
-- Defines available credit packages for purchase
CREATE TABLE IF NOT EXISTS credit_packages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Package details
    package_code VARCHAR(50) UNIQUE NOT NULL,
    package_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Pricing
    credits INTEGER NOT NULL,
    price_usd DECIMAL(10, 2) NOT NULL,
    discount_percentage INTEGER DEFAULT 0,

    -- Stripe integration
    stripe_price_id VARCHAR(255),
    stripe_product_id VARCHAR(255),

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT credits_positive CHECK (credits > 0),
    CONSTRAINT price_positive CHECK (price_usd > 0),
    CONSTRAINT discount_valid CHECK (discount_percentage >= 0 AND discount_percentage <= 100)
);

CREATE INDEX IF NOT EXISTS idx_credit_packages_code ON credit_packages(package_code);
CREATE INDEX IF NOT EXISTS idx_credit_packages_active ON credit_packages(is_active);

-- Insert default credit packages
INSERT INTO credit_packages (package_code, package_name, description, credits, price_usd, discount_percentage, display_order)
VALUES
    ('starter', 'Starter Pack', '1,000 credits - Perfect for trying out the platform', 1000, 10.00, 0, 1),
    ('standard', 'Standard Pack', '5,000 credits - Best value with 10% discount', 5000, 45.00, 10, 2),
    ('pro', 'Pro Pack', '10,000 credits - Popular choice with 20% discount', 10000, 80.00, 20, 3),
    ('enterprise', 'Enterprise Pack', '50,000 credits - Maximum value with 30% discount', 50000, 350.00, 30, 4)
ON CONFLICT (package_code) DO NOTHING;

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_credit_purchases_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_credit_purchases_timestamp ON credit_purchases;
CREATE TRIGGER trigger_update_credit_purchases_timestamp
    BEFORE UPDATE ON credit_purchases
    FOR EACH ROW
    EXECUTE FUNCTION update_credit_purchases_timestamp();

DROP TRIGGER IF EXISTS trigger_update_credit_packages_timestamp ON credit_packages;
CREATE TRIGGER trigger_update_credit_packages_timestamp
    BEFORE UPDATE ON credit_packages
    FOR EACH ROW
    EXECUTE FUNCTION update_credit_purchases_timestamp();

-- Completion message
DO $$
BEGIN
    RAISE NOTICE 'Credit Purchase System migration complete!';
    RAISE NOTICE 'Tables created: credit_purchases, credit_packages';
    RAISE NOTICE 'Default packages: Starter ($10), Standard ($45), Pro ($80), Enterprise ($350)';
END $$;
