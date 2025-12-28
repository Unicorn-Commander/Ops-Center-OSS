-- ============================================================================
-- Epic 1.8: Credit & Usage Metering System - Database Schema
--
-- This migration creates all tables required for the credit system
--
-- Author: Testing & DevOps Team Lead
-- Date: October 23, 2025
-- ============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- user_credits table
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    credits_remaining DECIMAL(12, 6) DEFAULT 0.0 NOT NULL,
    credits_allocated DECIMAL(12, 6) DEFAULT 0.0 NOT NULL,
    tier VARCHAR(50) DEFAULT 'free' NOT NULL,
    monthly_cap DECIMAL(12, 6),
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT credits_remaining_positive CHECK (credits_remaining >= 0),
    CONSTRAINT valid_tier CHECK (tier IN ('free', 'trial', 'starter', 'professional', 'enterprise'))
);

CREATE INDEX IF NOT EXISTS idx_user_credits_user_id ON user_credits(user_id);
CREATE INDEX IF NOT EXISTS idx_user_credits_tier ON user_credits(tier);

-- credit_transactions table
CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    amount DECIMAL(12, 6) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    provider VARCHAR(100),
    model VARCHAR(200),
    tokens_used INTEGER,
    cost DECIMAL(12, 6),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_transaction_type CHECK (
        transaction_type IN ('usage', 'purchase', 'bonus', 'refund', 'adjustment')
    )
);

CREATE INDEX IF NOT EXISTS idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_created_at ON credit_transactions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_credit_transactions_type ON credit_transactions(transaction_type);

-- openrouter_accounts table
CREATE TABLE IF NOT EXISTS openrouter_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) UNIQUE NOT NULL,
    openrouter_api_key_encrypted TEXT NOT NULL,
    openrouter_account_id VARCHAR(255),
    free_credits DECIMAL(12, 6) DEFAULT 0.0,
    last_synced TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_openrouter_accounts_user_id ON openrouter_accounts(user_id);

-- coupon_codes table
CREATE TABLE IF NOT EXISTS coupon_codes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    discount_type VARCHAR(20) NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    max_uses INTEGER DEFAULT 1,
    times_used INTEGER DEFAULT 0,
    valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT valid_discount_type CHECK (discount_type IN ('percentage', 'fixed')),
    CONSTRAINT discount_value_positive CHECK (discount_value > 0)
);

CREATE INDEX IF NOT EXISTS idx_coupon_codes_code ON coupon_codes(code);

-- usage_events table
CREATE TABLE IF NOT EXISTS usage_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    service VARCHAR(50) NOT NULL,
    provider VARCHAR(100),
    model VARCHAR(200),
    tokens_used INTEGER,
    cost DECIMAL(12, 6),
    power_level VARCHAR(20),
    success BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_usage_events_user_id ON usage_events(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_events_created_at ON usage_events(created_at DESC);

-- Completion message
DO $$
BEGIN
    RAISE NOTICE 'Epic 1.8 migration complete!';
END $$;
