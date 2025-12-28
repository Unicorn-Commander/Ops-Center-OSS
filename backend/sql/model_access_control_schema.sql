-- ============================================================================
-- Model Access Control Schema for Epic 3.3
-- Purpose: Fine-grained model access control by subscription tier
-- Database: unicorn_db
-- Author: Database Architect
-- Created: November 6, 2025
-- ============================================================================

-- Drop existing table if exists (for clean setup)
DROP TABLE IF EXISTS model_access_control CASCADE;

-- Main access control table
CREATE TABLE model_access_control (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) NOT NULL UNIQUE,     -- "gpt-4o", "claude-3.5-sonnet"
    provider VARCHAR(50) NOT NULL,              -- "openrouter", "anthropic", "openai", etc.
    display_name VARCHAR(255) NOT NULL,         -- User-friendly name
    description TEXT,                           -- Model description
    enabled BOOLEAN DEFAULT true,               -- Global on/off switch

    -- Access Control
    tier_access JSONB DEFAULT '["trial","starter","professional","enterprise"]',

    -- Pricing (per 1K tokens)
    pricing JSONB,  -- {"input_per_1k": 0.01, "output_per_1k": 0.03}
    tier_markup JSONB DEFAULT '{"trial": 2.0, "starter": 1.5, "professional": 1.2, "enterprise": 1.0}',

    -- Capabilities
    context_length INTEGER,
    max_output_tokens INTEGER,
    supports_vision BOOLEAN DEFAULT false,
    supports_function_calling BOOLEAN DEFAULT false,
    supports_streaming BOOLEAN DEFAULT true,

    -- Metadata
    model_family VARCHAR(100),  -- "gpt-4", "claude-3", "llama-3"
    release_date DATE,
    deprecated BOOLEAN DEFAULT false,
    replacement_model VARCHAR(255),  -- If deprecated, suggest this instead
    metadata JSONB DEFAULT '{}',

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_model_access_enabled ON model_access_control(enabled);
CREATE INDEX IF NOT EXISTS idx_model_access_provider ON model_access_control(provider);
CREATE INDEX IF NOT EXISTS idx_model_access_tier ON model_access_control USING GIN(tier_access);
CREATE INDEX IF NOT EXISTS idx_model_access_family ON model_access_control(model_family);
CREATE INDEX IF NOT EXISTS idx_model_access_deprecated ON model_access_control(deprecated);

-- ============================================================================
-- Triggers for Automatic Timestamp Updates
-- ============================================================================

CREATE OR REPLACE FUNCTION update_model_access_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER model_access_updated_at
    BEFORE UPDATE ON model_access_control
    FOR EACH ROW
    EXECUTE FUNCTION update_model_access_updated_at();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE model_access_control IS 'Fine-grained model access control by subscription tier';
COMMENT ON COLUMN model_access_control.model_id IS 'Unique model identifier (e.g., gpt-4o, claude-3.5-sonnet)';
COMMENT ON COLUMN model_access_control.provider IS 'Model provider (openrouter, anthropic, openai, etc.)';
COMMENT ON COLUMN model_access_control.tier_access IS 'JSONB array of subscription tiers that can access this model';
COMMENT ON COLUMN model_access_control.pricing IS 'JSONB object with input_per_1k and output_per_1k token costs';
COMMENT ON COLUMN model_access_control.tier_markup IS 'JSONB object with markup multipliers per tier';
COMMENT ON COLUMN model_access_control.deprecated IS 'If true, model is no longer recommended for use';
COMMENT ON COLUMN model_access_control.replacement_model IS 'Model ID to suggest if this model is deprecated';

-- ============================================================================
-- Verification Query
-- ============================================================================

-- This query can be used to verify the schema was created successfully
DO $$
BEGIN
    RAISE NOTICE 'Model Access Control schema created successfully!';
    RAISE NOTICE 'Table: model_access_control';
    RAISE NOTICE 'Indexes: 5 created';
    RAISE NOTICE 'Triggers: 1 created (updated_at)';
END $$;
