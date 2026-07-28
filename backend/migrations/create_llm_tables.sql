-- ============================================================================
-- LLM Infrastructure Database Migration
-- Epic 3.1: LiteLLM Multi-Provider Routing
--
-- This migration creates all tables needed for the LLM routing system:
-- 1. llm_providers - LLM provider definitions (OpenAI, Anthropic, etc.)
-- 2. llm_models - Individual models with pricing and capabilities
-- 3. user_api_keys - User BYOK (Bring Your Own Key) storage
-- 4. llm_routing_rules - Power level routing mappings
-- 5. llm_usage_logs - Usage tracking for billing integration
--
-- Author: Backend API Developer
-- Date: October 23, 2025
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================================
-- Table 1: LLM Providers
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_providers (
    id SERIAL PRIMARY KEY,

    -- Provider Identity
    provider_name VARCHAR(100) UNIQUE NOT NULL,
    provider_slug VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- API Configuration
    base_url VARCHAR(500),
    auth_type VARCHAR(50) DEFAULT 'api_key' NOT NULL,
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,

    -- Rate Limits
    rate_limit_rpm INTEGER,  -- Requests per minute
    rate_limit_tpm INTEGER,  -- Tokens per minute
    rate_limit_rpd INTEGER,  -- Requests per day

    -- Provider Status
    is_active BOOLEAN DEFAULT TRUE,
    is_byok_supported BOOLEAN DEFAULT TRUE,
    is_system_provider BOOLEAN DEFAULT FALSE,

    -- Metadata
    api_key_format VARCHAR(100),
    documentation_url VARCHAR(500),
    pricing_url VARCHAR(500),
    status_page_url VARCHAR(500),

    -- Health Monitoring
    health_status VARCHAR(50) DEFAULT 'unknown',
    health_last_checked TIMESTAMP,
    health_response_time_ms INTEGER,

    -- Access Control
    min_tier_required VARCHAR(50) DEFAULT 'free',

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for llm_providers
CREATE INDEX IF NOT EXISTS idx_llm_providers_active ON llm_providers(is_active);
CREATE INDEX IF NOT EXISTS idx_llm_providers_slug ON llm_providers(provider_slug);
CREATE INDEX IF NOT EXISTS idx_llm_providers_health ON llm_providers(health_status, is_active);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_llm_providers_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_llm_providers_updated_at
    BEFORE UPDATE ON llm_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_providers_updated_at();


-- ============================================================================
-- Table 2: LLM Models
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_models (
    id SERIAL PRIMARY KEY,

    -- Foreign Key
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE NOT NULL,

    -- Model Identity
    model_name VARCHAR(200) NOT NULL,
    model_id VARCHAR(200) NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Capabilities
    max_tokens INTEGER DEFAULT 4096 NOT NULL,
    context_window INTEGER DEFAULT 8192 NOT NULL,
    supports_streaming BOOLEAN DEFAULT TRUE,
    supports_function_calling BOOLEAN DEFAULT FALSE,
    supports_vision BOOLEAN DEFAULT FALSE,
    supports_json_mode BOOLEAN DEFAULT FALSE,

    -- Pricing (per 1M tokens in USD)
    cost_per_1m_input_tokens DECIMAL(10, 6),
    cost_per_1m_output_tokens DECIMAL(10, 6),
    cost_per_1m_tokens_cached DECIMAL(10, 6),

    -- Power Level Mapping
    power_level VARCHAR(50),
    power_level_priority INTEGER DEFAULT 999,

    -- Model Status
    is_active BOOLEAN DEFAULT TRUE,
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecation_date TIMESTAMP,
    replacement_model_id INTEGER REFERENCES llm_models(id),

    -- Access Control
    min_tier_required VARCHAR(50) DEFAULT 'free',

    -- Performance Metrics
    avg_latency_ms INTEGER,
    avg_tokens_per_second DECIMAL(10, 2),

    -- Metadata
    model_version VARCHAR(50),
    release_date TIMESTAMP,
    training_cutoff VARCHAR(100),

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    UNIQUE(provider_id, model_id)
);

-- Indexes for llm_models
CREATE INDEX IF NOT EXISTS idx_llm_models_provider ON llm_models(provider_id, is_active);
CREATE INDEX IF NOT EXISTS idx_llm_models_power_level ON llm_models(power_level, is_active);
CREATE INDEX IF NOT EXISTS idx_llm_models_model_name ON llm_models(model_name);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_llm_models_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_llm_models_updated_at
    BEFORE UPDATE ON llm_models
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_models_updated_at();


-- ============================================================================
-- Table 3: User API Keys (BYOK)
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_api_keys (
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE CASCADE NOT NULL,

    -- Key Details
    key_name VARCHAR(200),
    encrypted_api_key TEXT NOT NULL,
    key_prefix VARCHAR(20),
    key_suffix VARCHAR(20),

    -- Key Status
    is_active BOOLEAN DEFAULT TRUE,
    is_validated BOOLEAN DEFAULT FALSE,
    validation_error TEXT,
    last_validated_at TIMESTAMP,

    -- Usage Statistics
    total_requests INTEGER DEFAULT 0,
    total_tokens BIGINT DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    last_used_at TIMESTAMP,

    -- Security
    created_ip VARCHAR(100),
    last_rotated_at TIMESTAMP,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,

    -- Constraints
    UNIQUE(user_id, provider_id)
);

-- Indexes for user_api_keys
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user ON user_api_keys(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_provider ON user_api_keys(provider_id);
CREATE INDEX IF NOT EXISTS idx_user_api_keys_user_provider ON user_api_keys(user_id, provider_id, is_active);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_user_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_api_keys_updated_at
    BEFORE UPDATE ON user_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_user_api_keys_updated_at();


-- ============================================================================
-- Table 4: LLM Routing Rules
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id SERIAL PRIMARY KEY,

    -- Foreign Key
    model_id INTEGER REFERENCES llm_models(id) ON DELETE CASCADE NOT NULL,

    -- Routing Criteria
    power_level VARCHAR(50) NOT NULL,
    user_tier VARCHAR(50) NOT NULL,
    task_type VARCHAR(50),

    -- Routing Priority
    priority INTEGER DEFAULT 100,
    weight INTEGER DEFAULT 100,

    -- Routing Conditions
    min_tokens INTEGER,
    max_tokens INTEGER,
    requires_byok BOOLEAN DEFAULT FALSE,

    -- Fallback Configuration
    is_fallback BOOLEAN DEFAULT FALSE,
    fallback_order INTEGER DEFAULT 999,

    -- Rule Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for llm_routing_rules
CREATE INDEX IF NOT EXISTS idx_routing_rules_lookup ON llm_routing_rules(power_level, user_tier, task_type, is_active);
CREATE INDEX IF NOT EXISTS idx_routing_rules_priority ON llm_routing_rules(priority, is_active);
CREATE INDEX IF NOT EXISTS idx_routing_rules_model ON llm_routing_rules(model_id, is_active);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_llm_routing_rules_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_llm_routing_rules_updated_at
    BEFORE UPDATE ON llm_routing_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_routing_rules_updated_at();


-- ============================================================================
-- Table 5: LLM Usage Logs
-- ============================================================================

CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id SERIAL PRIMARY KEY,

    -- Foreign Keys
    user_id VARCHAR(255) NOT NULL,
    provider_id INTEGER REFERENCES llm_providers(id) ON DELETE SET NULL,
    model_id INTEGER REFERENCES llm_models(id) ON DELETE SET NULL,
    user_key_id INTEGER REFERENCES user_api_keys(id) ON DELETE SET NULL,

    -- Request Details
    request_id VARCHAR(100) UNIQUE,
    power_level VARCHAR(50),
    task_type VARCHAR(50),

    -- Usage Metrics
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cached_tokens INTEGER DEFAULT 0,

    -- Cost Calculation
    cost_input_usd DECIMAL(10, 6) DEFAULT 0.0,
    cost_output_usd DECIMAL(10, 6) DEFAULT 0.0,
    cost_total_usd DECIMAL(10, 6) DEFAULT 0.0,
    used_byok BOOLEAN DEFAULT FALSE,

    -- Performance Metrics
    latency_ms INTEGER,
    tokens_per_second DECIMAL(10, 2),

    -- Response Details
    status_code INTEGER,
    error_message TEXT,
    was_fallback BOOLEAN DEFAULT FALSE,
    fallback_reason VARCHAR(200),

    -- Billing Integration
    lago_event_id VARCHAR(100) UNIQUE,
    billed_at TIMESTAMP,

    -- Request Metadata
    request_ip VARCHAR(100),
    user_agent VARCHAR(500),
    session_id VARCHAR(100),

    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes for llm_usage_logs
CREATE INDEX IF NOT EXISTS idx_usage_logs_user_date ON llm_usage_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_provider_date ON llm_usage_logs(provider_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_cost ON llm_usage_logs(cost_total_usd, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_logs_request_id ON llm_usage_logs(request_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_lago_event ON llm_usage_logs(lago_event_id);

-- Partitioning hint: Consider partitioning by created_at for large-scale deployments
-- Example:
-- CREATE TABLE llm_usage_logs_2025_10 PARTITION OF llm_usage_logs
-- FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');


-- ============================================================================
-- Seed Data: Popular LLM Providers
-- ============================================================================

-- Insert popular providers (only if they don't exist)
INSERT INTO llm_providers (
    provider_name, provider_slug, display_name, description,
    base_url, auth_type, supports_streaming, supports_function_calling,
    is_active, is_byok_supported, is_system_provider,
    api_key_format, documentation_url, min_tier_required
) VALUES
-- OpenAI
('OpenAI', 'openai', 'OpenAI', 'Industry-leading models including GPT-4, GPT-3.5',
 'https://api.openai.com/v1', 'api_key', TRUE, TRUE,
 TRUE, TRUE, FALSE,
 'sk-*', 'https://platform.openai.com/docs', 'professional'),

-- Anthropic
('Anthropic', 'anthropic', 'Anthropic', 'Claude models for advanced reasoning and long context',
 'https://api.anthropic.com/v1', 'api_key', TRUE, TRUE,
 TRUE, TRUE, FALSE,
 'sk-ant-*', 'https://docs.anthropic.com', 'professional'),

-- Google
('Google', 'google', 'Google AI', 'Gemini models with multimodal capabilities',
 'https://generativelanguage.googleapis.com/v1', 'api_key', TRUE, FALSE,
 TRUE, TRUE, FALSE,
 NULL, 'https://ai.google.dev/docs', 'starter'),

-- OpenRouter (Aggregator)
('OpenRouter', 'openrouter', 'OpenRouter', 'Access to 100+ models through a single API',
 'https://openrouter.ai/api/v1', 'api_key', TRUE, TRUE,
 TRUE, TRUE, FALSE,
 'sk-or-*', 'https://openrouter.ai/docs', 'free'),

-- Together AI
('Together', 'together', 'Together AI', 'Fast inference for open-source models',
 'https://api.together.xyz/v1', 'api_key', TRUE, FALSE,
 TRUE, TRUE, FALSE,
 NULL, 'https://docs.together.ai', 'starter'),

-- Groq
('Groq', 'groq', 'Groq', 'Ultra-fast inference with LPU technology',
 'https://api.groq.com/openai/v1', 'api_key', TRUE, FALSE,
 TRUE, TRUE, FALSE,
 'gsk_*', 'https://console.groq.com/docs', 'free'),

-- Fireworks AI
('Fireworks', 'fireworks', 'Fireworks AI', 'High-performance model serving',
 'https://api.fireworks.ai/inference/v1', 'api_key', TRUE, TRUE,
 TRUE, TRUE, FALSE,
 NULL, 'https://docs.fireworks.ai', 'starter')

ON CONFLICT (provider_slug) DO NOTHING;


-- ============================================================================
-- Seed Data: Example Models
-- ============================================================================

-- OpenAI Models
WITH openai_provider AS (SELECT id FROM llm_providers WHERE provider_slug = 'openai')
INSERT INTO llm_models (
    provider_id, model_name, model_id, display_name, description,
    max_tokens, context_window, supports_streaming, supports_function_calling, supports_vision,
    cost_per_1m_input_tokens, cost_per_1m_output_tokens,
    power_level, power_level_priority, is_active, min_tier_required
) SELECT
    (SELECT id FROM openai_provider),
    'GPT-4o', 'gpt-4o', 'GPT-4o', 'Flagship multimodal model with vision',
    16384, 128000, TRUE, TRUE, TRUE,
    5.00, 15.00,
    'precision', 10, TRUE, 'professional'
WHERE EXISTS (SELECT 1 FROM openai_provider)
ON CONFLICT (provider_id, model_id) DO NOTHING;

WITH openai_provider AS (SELECT id FROM llm_providers WHERE provider_slug = 'openai')
INSERT INTO llm_models (
    provider_id, model_name, model_id, display_name, description,
    max_tokens, context_window, supports_streaming, supports_function_calling,
    cost_per_1m_input_tokens, cost_per_1m_output_tokens,
    power_level, power_level_priority, is_active, min_tier_required
) SELECT
    (SELECT id FROM openai_provider),
    'GPT-4 Turbo', 'gpt-4-turbo', 'GPT-4 Turbo', 'Fast and capable GPT-4',
    4096, 128000, TRUE, TRUE,
    10.00, 30.00,
    'balanced', 20, TRUE, 'professional'
WHERE EXISTS (SELECT 1 FROM openai_provider)
ON CONFLICT (provider_id, model_id) DO NOTHING;

-- Anthropic Models
WITH anthropic_provider AS (SELECT id FROM llm_providers WHERE provider_slug = 'anthropic')
INSERT INTO llm_models (
    provider_id, model_name, model_id, display_name, description,
    max_tokens, context_window, supports_streaming,
    cost_per_1m_input_tokens, cost_per_1m_output_tokens,
    power_level, power_level_priority, is_active, min_tier_required
) SELECT
    (SELECT id FROM anthropic_provider),
    'Claude 3.5 Sonnet', 'claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet', 'Most capable Claude model',
    8192, 200000, TRUE,
    3.00, 15.00,
    'precision', 5, TRUE, 'professional'
WHERE EXISTS (SELECT 1 FROM anthropic_provider)
ON CONFLICT (provider_id, model_id) DO NOTHING;

-- Groq Models (Free tier)
WITH groq_provider AS (SELECT id FROM llm_providers WHERE provider_slug = 'groq')
INSERT INTO llm_models (
    provider_id, model_name, model_id, display_name, description,
    max_tokens, context_window, supports_streaming,
    cost_per_1m_input_tokens, cost_per_1m_output_tokens,
    power_level, power_level_priority, is_active, min_tier_required
) SELECT
    (SELECT id FROM groq_provider),
    'Llama 3 70B', 'llama3-70b-8192', 'Meta Llama 3 70B', 'Fast open-source model',
    8192, 8192, TRUE,
    0.00, 0.00,  -- Free tier
    'eco', 50, TRUE, 'free'
WHERE EXISTS (SELECT 1 FROM groq_provider)
ON CONFLICT (provider_id, model_id) DO NOTHING;


-- ============================================================================
-- Seed Data: Example Routing Rules
-- ============================================================================

-- Precision level → Claude 3.5 Sonnet
WITH claude_model AS (SELECT id FROM llm_models WHERE model_id = 'claude-3-5-sonnet-20241022')
INSERT INTO llm_routing_rules (
    model_id, power_level, user_tier, task_type, priority, weight, is_active
) SELECT
    (SELECT id FROM claude_model),
    'precision', 'professional', NULL, 10, 100, TRUE
WHERE EXISTS (SELECT 1 FROM claude_model)
ON CONFLICT DO NOTHING;

-- Balanced level → GPT-4 Turbo
WITH gpt4_model AS (SELECT id FROM llm_models WHERE model_id = 'gpt-4-turbo')
INSERT INTO llm_routing_rules (
    model_id, power_level, user_tier, task_type, priority, weight, is_active
) SELECT
    (SELECT id FROM gpt4_model),
    'balanced', 'professional', NULL, 20, 100, TRUE
WHERE EXISTS (SELECT 1 FROM gpt4_model)
ON CONFLICT DO NOTHING;

-- Eco level → Llama 3 70B (free)
WITH llama_model AS (SELECT id FROM llm_models WHERE model_id = 'llama3-70b-8192')
INSERT INTO llm_routing_rules (
    model_id, power_level, user_tier, task_type, priority, weight, is_active
) SELECT
    (SELECT id FROM llama_model),
    'eco', 'free', NULL, 50, 100, TRUE
WHERE EXISTS (SELECT 1 FROM llama_model)
ON CONFLICT DO NOTHING;


-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify table creation
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('llm_providers', 'llm_models', 'user_api_keys', 'llm_routing_rules', 'llm_usage_logs');

    RAISE NOTICE 'Created % LLM infrastructure tables', table_count;
END;
$$;

-- Display summary
SELECT 'Providers' as entity, COUNT(*) as count FROM llm_providers
UNION ALL
SELECT 'Models' as entity, COUNT(*) as count FROM llm_models
UNION ALL
SELECT 'Routing Rules' as entity, COUNT(*) as count FROM llm_routing_rules
ORDER BY entity;

-- ============================================================================
-- Migration Complete
-- ============================================================================
