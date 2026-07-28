-- ============================================================================
-- Model Management System Migration
-- Database Architect Team Lead
-- Date: November 8, 2025
--
-- Purpose: Add model access control table for Bolt.DIY model translations
--
-- This migration creates a `models` table to manage LLM model access control,
-- including:
-- - Model ID translation (Bolt ID → LiteLLM ID)
-- - Tier-based access control
-- - Pricing information
-- - Provider routing
-- - Enabled/disabled state
--
-- Integration: This works alongside existing llm_models table but focuses on
-- access control and ID translation for frontend applications.
-- ============================================================================

-- Enable required extensions (idempotent)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Table: models (Model Access Control & Translation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS models (
    -- Primary Key
    id SERIAL PRIMARY KEY,

    -- Model Identifiers
    model_id VARCHAR(200) UNIQUE NOT NULL,  -- What Bolt sends: "kimi/kimi-dev-72b"
    litellm_model_id VARCHAR(300) NOT NULL,  -- What to send to LiteLLM: "openrouter/moonshot/kimi-v1-128k"
    display_name VARCHAR(300) NOT NULL,      -- Human-readable: "Kimi Dev 72B"

    -- Provider Information
    provider VARCHAR(100) NOT NULL,  -- openai, anthropic, openrouter, etc.
    description TEXT,                -- Optional detailed description

    -- Access Control (JSONB array for flexibility)
    tier_access JSONB NOT NULL DEFAULT '["trial", "starter", "professional", "enterprise"]'::jsonb,
    -- Example: '["professional", "enterprise"]' for premium-only models
    -- Example: '["trial", "starter", "professional", "enterprise"]' for all tiers

    -- Pricing (per 1K tokens, different from llm_models which uses per 1M)
    pricing_input DECIMAL(10, 6),    -- Cost per 1K input tokens in USD
    pricing_output DECIMAL(10, 6),   -- Cost per 1K output tokens in USD

    -- Model Capabilities
    context_length INTEGER DEFAULT 8192,  -- Maximum context window
    max_output_tokens INTEGER,            -- Maximum output tokens (if different from context)
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,

    -- Status
    enabled BOOLEAN DEFAULT TRUE,    -- Is this model currently available?

    -- Additional Metadata
    tags JSONB DEFAULT '[]'::jsonb,  -- For categorization: ["coding", "reasoning", "vision"]
    metadata JSONB DEFAULT '{}'::jsonb,  -- Flexible field for future expansion

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    CONSTRAINT valid_tier_access CHECK (
        jsonb_typeof(tier_access) = 'array'
    ),
    CONSTRAINT valid_tags CHECK (
        jsonb_typeof(tags) = 'array'
    ),
    CONSTRAINT valid_metadata CHECK (
        jsonb_typeof(metadata) = 'object'
    )
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Fast lookup by model_id (primary use case)
CREATE INDEX IF NOT EXISTS idx_models_model_id ON models(model_id) WHERE enabled = TRUE;

-- Filter by provider
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider) WHERE enabled = TRUE;

-- Filter by enabled status
CREATE INDEX IF NOT EXISTS idx_models_enabled ON models(enabled);

-- GIN index for JSONB tier_access queries
CREATE INDEX IF NOT EXISTS idx_models_tier_access ON models USING GIN (tier_access);

-- GIN index for tags (for future categorization)
CREATE INDEX IF NOT EXISTS idx_models_tags ON models USING GIN (tags);

-- Composite index for common query: enabled models by provider
CREATE INDEX IF NOT EXISTS idx_models_provider_enabled ON models(provider, enabled);

-- ============================================================================
-- Triggers
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_models_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_models_updated_at
    BEFORE UPDATE ON models
    FOR EACH ROW
    EXECUTE FUNCTION update_models_updated_at();

-- ============================================================================
-- Seed Data: Popular Models
-- ============================================================================

INSERT INTO models (
    model_id, litellm_model_id, display_name, provider, description,
    tier_access, pricing_input, pricing_output, context_length,
    supports_function_calling, supports_vision, enabled
) VALUES

-- OpenAI Models
('gpt-4o', 'openai/gpt-4o', 'GPT-4o', 'openai',
 'Flagship multimodal model with vision capabilities',
 '["professional", "enterprise"]'::jsonb, 5.00, 15.00, 128000, TRUE, TRUE, TRUE),

('gpt-4o-mini', 'openai/gpt-4o-mini', 'GPT-4o Mini', 'openai',
 'Efficient and affordable GPT-4 variant',
 '["trial", "starter", "professional", "enterprise"]'::jsonb, 0.15, 0.60, 128000, TRUE, FALSE, TRUE),

('gpt-4-turbo', 'openai/gpt-4-turbo', 'GPT-4 Turbo', 'openai',
 'Fast and capable GPT-4',
 '["professional", "enterprise"]'::jsonb, 10.00, 30.00, 128000, TRUE, FALSE, TRUE),

('gpt-3.5-turbo', 'openai/gpt-3.5-turbo', 'GPT-3.5 Turbo', 'openai',
 'Fast and affordable for most tasks',
 '["trial", "starter", "professional", "enterprise"]'::jsonb, 0.50, 1.50, 16385, TRUE, FALSE, TRUE),

-- Anthropic Models
('claude-3.5-sonnet', 'anthropic/claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 'anthropic',
 'Most capable Claude model for complex tasks',
 '["professional", "enterprise"]'::jsonb, 3.00, 15.00, 200000, TRUE, FALSE, TRUE),

('claude-3-opus', 'anthropic/claude-3-opus-20240229', 'Claude 3 Opus', 'anthropic',
 'Powerful model for high-stakes tasks',
 '["enterprise"]'::jsonb, 15.00, 75.00, 200000, TRUE, FALSE, TRUE),

('claude-3-haiku', 'anthropic/claude-3-haiku-20240307', 'Claude 3 Haiku', 'anthropic',
 'Fast and compact Claude model',
 '["starter", "professional", "enterprise"]'::jsonb, 0.25, 1.25, 200000, FALSE, FALSE, TRUE),

-- Google Models
('gemini-pro', 'google/gemini-pro', 'Gemini Pro', 'google',
 'Google flagship model with strong reasoning',
 '["starter", "professional", "enterprise"]'::jsonb, 0.50, 1.50, 32768, FALSE, FALSE, TRUE),

('gemini-pro-vision', 'google/gemini-pro-vision', 'Gemini Pro Vision', 'google',
 'Multimodal Gemini with vision capabilities',
 '["professional", "enterprise"]'::jsonb, 0.50, 1.50, 16384, FALSE, TRUE, TRUE),

-- OpenRouter Popular Models
('meta-llama-3.1-70b', 'openrouter/meta-llama/llama-3.1-70b-instruct', 'Llama 3.1 70B', 'openrouter',
 'Open source powerhouse for reasoning',
 '["trial", "starter", "professional", "enterprise"]'::jsonb, 0.35, 0.40, 131072, FALSE, FALSE, TRUE),

('mistral-large', 'openrouter/mistralai/mistral-large', 'Mistral Large', 'openrouter',
 'High-performance European model',
 '["professional", "enterprise"]'::jsonb, 2.00, 6.00, 32768, TRUE, FALSE, TRUE),

('kimi/kimi-dev-72b', 'openrouter/moonshot/kimi-v1-128k', 'Kimi Dev 72B', 'openrouter',
 'Long context Chinese-English bilingual model',
 '["professional", "enterprise"]'::jsonb, 0.12, 0.12, 128000, FALSE, FALSE, TRUE),

-- DeepSeek Models
('deepseek-chat', 'openrouter/deepseek/deepseek-chat', 'DeepSeek Chat', 'openrouter',
 'Affordable high-quality reasoning model',
 '["trial", "starter", "professional", "enterprise"]'::jsonb, 0.14, 0.28, 32768, FALSE, FALSE, TRUE),

('deepseek-coder', 'openrouter/deepseek/deepseek-coder', 'DeepSeek Coder', 'openrouter',
 'Specialized coding assistant',
 '["starter", "professional", "enterprise"]'::jsonb, 0.14, 0.28, 16384, FALSE, FALSE, TRUE),

-- Qwen Models
('qwen-2.5-72b', 'openrouter/qwen/qwen-2.5-72b-instruct', 'Qwen 2.5 72B', 'openrouter',
 'Powerful multilingual reasoning model',
 '["professional", "enterprise"]'::jsonb, 0.35, 0.40, 32768, FALSE, FALSE, TRUE)

ON CONFLICT (model_id) DO NOTHING;

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function to check if a model is accessible for a given tier
CREATE OR REPLACE FUNCTION is_model_accessible(
    p_model_id VARCHAR(200),
    p_user_tier VARCHAR(50)
)
RETURNS BOOLEAN AS $$
DECLARE
    v_tier_access JSONB;
BEGIN
    -- Get tier_access array for the model
    SELECT tier_access INTO v_tier_access
    FROM models
    WHERE model_id = p_model_id AND enabled = TRUE;

    -- Return FALSE if model not found or disabled
    IF v_tier_access IS NULL THEN
        RETURN FALSE;
    END IF;

    -- Check if user tier is in the tier_access array
    RETURN v_tier_access ? p_user_tier;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get all accessible models for a tier
CREATE OR REPLACE FUNCTION get_models_for_tier(p_user_tier VARCHAR(50))
RETURNS TABLE (
    model_id VARCHAR(200),
    litellm_model_id VARCHAR(300),
    display_name VARCHAR(300),
    provider VARCHAR(100),
    context_length INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        m.model_id,
        m.litellm_model_id,
        m.display_name,
        m.provider,
        m.context_length
    FROM models m
    WHERE m.enabled = TRUE
    AND m.tier_access ? p_user_tier
    ORDER BY m.provider, m.display_name;
END;
$$ LANGUAGE plpgsql STABLE;

-- ============================================================================
-- Verification & Summary
-- ============================================================================

-- Display migration summary
DO $$
DECLARE
    total_models INTEGER;
    openai_count INTEGER;
    anthropic_count INTEGER;
    openrouter_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_models FROM models WHERE enabled = TRUE;
    SELECT COUNT(*) INTO openai_count FROM models WHERE provider = 'openai' AND enabled = TRUE;
    SELECT COUNT(*) INTO anthropic_count FROM models WHERE provider = 'anthropic' AND enabled = TRUE;
    SELECT COUNT(*) INTO openrouter_count FROM models WHERE provider = 'openrouter' AND enabled = TRUE;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Model Management System Migration Complete';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total models seeded: %', total_models;
    RAISE NOTICE '  - OpenAI models: %', openai_count;
    RAISE NOTICE '  - Anthropic models: %', anthropic_count;
    RAISE NOTICE '  - OpenRouter models: %', openrouter_count;
    RAISE NOTICE '';
    RAISE NOTICE 'Indexes created: 7';
    RAISE NOTICE 'Helper functions created: 2';
    RAISE NOTICE '  - is_model_accessible(model_id, tier)';
    RAISE NOTICE '  - get_models_for_tier(tier)';
END;
$$;

-- Example usage queries
SELECT
    'Example: Get all Professional tier models' as description,
    COUNT(*) as model_count
FROM get_models_for_tier('professional');

SELECT
    'Example: Check if gpt-4o is accessible for trial users' as description,
    is_model_accessible('gpt-4o', 'trial') as is_accessible;

-- ============================================================================
-- Migration Complete
-- ============================================================================
