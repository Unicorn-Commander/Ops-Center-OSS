-- ============================================================================
-- Unified LLM Management System - Database Migration
-- Epic 3.2: Consolidation of 4 Fragmented LLM Pages into Single System
--
-- This migration creates a comprehensive LLM management schema that unifies:
-- 1. Cloud Provider Management (OpenRouter, OpenAI, Anthropic, etc.)
-- 2. Local Model Server Infrastructure (Ollama, vLLM, LMStudio)
-- 3. Model Deployments & Runtime Management
-- 4. Access Control & Permission System
-- 5. Usage Tracking & Cost Analytics
-- 6. Audit Logging & Compliance
--
-- BACKWARD COMPATIBILITY:
-- - Preserves existing model_servers table (001_model_servers.sql)
-- - Preserves existing llm_providers table (create_llm_tables.sql)
-- - Preserves existing llm_usage_logs table (create_llm_tables.sql)
-- - Adds new columns via ALTER TABLE (safe for production)
--
-- Author: Backend Database Specialist
-- Date: October 27, 2025
-- Version: 1.0.0
-- ============================================================================

BEGIN;

-- ============================================================================
-- Enable Required Extensions
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- Table 1: Cloud Provider Management (llm_providers)
-- ============================================================================
-- STRATEGY: Extend existing table instead of creating new one

DO $$
BEGIN
    -- Check if llm_providers exists (from create_llm_tables.sql)
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'llm_providers') THEN

        -- Add new columns if they don't exist
        ALTER TABLE llm_providers
            ADD COLUMN IF NOT EXISTS api_key_encrypted TEXT,
            ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE,
            ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;

        -- Rename conflicting columns for consistency
        ALTER TABLE llm_providers
            RENAME COLUMN is_active TO enabled;

        RAISE NOTICE 'Extended existing llm_providers table';
    ELSE
        -- Create new table if it doesn't exist
        CREATE TABLE llm_providers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL, -- "openrouter", "openai", "anthropic", "custom"
            base_url VARCHAR(512),
            api_key_encrypted TEXT, -- AES-256 encrypted
            enabled BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by VARCHAR(255),
            metadata JSONB DEFAULT '{}'::jsonb,
            UNIQUE(name, type)
        );

        RAISE NOTICE 'Created new llm_providers table';
    END IF;
END;
$$;

-- Indexes for llm_providers
CREATE INDEX IF NOT EXISTS idx_llm_providers_enabled ON llm_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_llm_providers_type ON llm_providers(type);

-- ============================================================================
-- Table 2: Model Servers (Local Infrastructure)
-- ============================================================================
-- STRATEGY: Extend existing model_servers table (001_model_servers.sql)

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'model_servers') THEN

        -- Add missing columns for unified management
        ALTER TABLE model_servers
            ADD COLUMN IF NOT EXISTS location VARCHAR(20) DEFAULT 'local',
            ADD COLUMN IF NOT EXISTS host VARCHAR(255),
            ADD COLUMN IF NOT EXISTS port INTEGER,
            ADD COLUMN IF NOT EXISTS gpu_id INTEGER,
            ADD COLUMN IF NOT EXISTS auto_start BOOLEAN DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE;

        -- Ensure consistency with existing columns
        ALTER TABLE model_servers
            ALTER COLUMN server_type TYPE VARCHAR(50);

        -- Rename for clarity
        DO $inner$
        BEGIN
            ALTER TABLE model_servers
                RENAME COLUMN server_type TO type;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- Column already renamed
        END $inner$;

        RAISE NOTICE 'Extended existing model_servers table';
    ELSE
        -- Create new table if it doesn't exist
        CREATE TABLE model_servers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL UNIQUE,
            type VARCHAR(50) NOT NULL, -- "ollama", "vllm", "lmstudio", "llamacpp"
            location VARCHAR(20) DEFAULT 'local', -- "local", "remote"
            host VARCHAR(255) NOT NULL,
            port INTEGER NOT NULL,
            gpu_id INTEGER,
            auto_start BOOLEAN DEFAULT FALSE,
            enabled BOOLEAN DEFAULT TRUE,
            health_status VARCHAR(20) DEFAULT 'unknown',
            last_health_check TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'::jsonb,
            UNIQUE(host, port)
        );

        RAISE NOTICE 'Created new model_servers table';
    END IF;
END;
$$;

-- Indexes for model_servers
CREATE INDEX IF NOT EXISTS idx_model_servers_health ON model_servers(health_status, enabled);
CREATE INDEX IF NOT EXISTS idx_model_servers_type ON model_servers(type);
CREATE INDEX IF NOT EXISTS idx_model_servers_location ON model_servers(location);

-- ============================================================================
-- Table 3: Installed Models
-- ============================================================================
-- PURPOSE: Track models installed on local servers

CREATE TABLE IF NOT EXISTS installed_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES model_servers(id) ON DELETE CASCADE,
    model_name VARCHAR(255) NOT NULL,
    file_path TEXT,
    size_bytes BIGINT,
    quantization VARCHAR(50),
    version VARCHAR(50),
    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(server_id, model_name, version)
);

-- Indexes for installed_models
CREATE INDEX IF NOT EXISTS idx_installed_models_server ON installed_models(server_id);
CREATE INDEX IF NOT EXISTS idx_installed_models_name ON installed_models(model_name);
CREATE INDEX IF NOT EXISTS idx_installed_models_last_used ON installed_models(last_used DESC NULLS LAST);

COMMENT ON TABLE installed_models IS 'Models installed on local infrastructure servers';
COMMENT ON COLUMN installed_models.file_path IS 'Local filesystem path to model files';
COMMENT ON COLUMN installed_models.quantization IS 'Quantization format (Q4_K_M, AWQ, GPTQ, etc.)';

-- ============================================================================
-- Table 4: Running Model Deployments
-- ============================================================================
-- PURPOSE: Track currently running model instances

CREATE TABLE IF NOT EXISTS model_deployments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID NOT NULL REFERENCES model_servers(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES installed_models(id) ON DELETE CASCADE,
    alias VARCHAR(255),
    status VARCHAR(20) DEFAULT 'loading', -- loading, running, stopped, error
    context_length INTEGER DEFAULT 2048,
    gpu_layers INTEGER,
    batch_size INTEGER,
    vram_usage_mb INTEGER,
    tokens_per_sec DECIMAL(10,2),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    stopped_at TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(server_id, alias)
);

-- Indexes for model_deployments
CREATE INDEX IF NOT EXISTS idx_deployments_server ON model_deployments(server_id, status);
CREATE INDEX IF NOT EXISTS idx_deployments_model ON model_deployments(model_id);
CREATE INDEX IF NOT EXISTS idx_deployments_alias ON model_deployments(alias);
CREATE INDEX IF NOT EXISTS idx_deployments_status ON model_deployments(status);

COMMENT ON TABLE model_deployments IS 'Currently running model instances on servers';
COMMENT ON COLUMN model_deployments.alias IS 'User-friendly name for the deployment (e.g., "production-chat")';
COMMENT ON COLUMN model_deployments.vram_usage_mb IS 'Current VRAM usage in megabytes';

-- ============================================================================
-- Table 5: Model Permissions (Access Control)
-- ============================================================================
-- PURPOSE: Control which users/roles/tiers can access which models

CREATE TABLE IF NOT EXISTS model_permissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) NOT NULL,
    access_type VARCHAR(50) NOT NULL, -- "user", "role", "tier", "agent"
    access_value VARCHAR(255) NOT NULL,
    allowed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    UNIQUE(model_id, access_type, access_value)
);

-- Indexes for model_permissions
CREATE INDEX IF NOT EXISTS idx_permissions_model ON model_permissions(model_id);
CREATE INDEX IF NOT EXISTS idx_permissions_access ON model_permissions(access_type, access_value);
CREATE INDEX IF NOT EXISTS idx_permissions_lookup ON model_permissions(model_id, access_type, access_value);

COMMENT ON TABLE model_permissions IS 'Fine-grained access control for models';
COMMENT ON COLUMN model_permissions.access_type IS 'Type of access control: user, role, tier, agent';
COMMENT ON COLUMN model_permissions.access_value IS 'Value for access type (user ID, role name, tier code)';

-- ============================================================================
-- Table 6: Tier Model Rules (Subscription-Based Access)
-- ============================================================================
-- PURPOSE: Define which models are available to each subscription tier

CREATE TABLE IF NOT EXISTS tier_model_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tier_code VARCHAR(50) NOT NULL,
    model_pattern VARCHAR(255) NOT NULL,
    allowed BOOLEAN DEFAULT TRUE,
    max_requests_per_day INTEGER,
    max_context_length INTEGER,
    priority INTEGER DEFAULT 0,
    UNIQUE(tier_code, model_pattern)
);

-- Indexes for tier_model_rules
CREATE INDEX IF NOT EXISTS idx_tier_rules_tier ON tier_model_rules(tier_code);
CREATE INDEX IF NOT EXISTS idx_tier_rules_pattern ON tier_model_rules(model_pattern);

COMMENT ON TABLE tier_model_rules IS 'Tier-based access rules for subscription plans';
COMMENT ON COLUMN tier_model_rules.model_pattern IS 'Glob pattern (e.g., "ollama/*", "openai/gpt-4*")';
COMMENT ON COLUMN tier_model_rules.priority IS 'Higher priority rules override lower (0 = lowest)';

-- ============================================================================
-- Table 7: Usage Tracking (Extend Existing llm_usage_logs)
-- ============================================================================
-- STRATEGY: Add columns to existing table for unified tracking

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables
               WHERE table_name = 'llm_usage_logs') THEN

        -- Add new columns for unified tracking
        ALTER TABLE llm_usage_logs
            ADD COLUMN IF NOT EXISTS provider VARCHAR(50),
            ADD COLUMN IF NOT EXISTS server_id UUID,
            ADD COLUMN IF NOT EXISTS deployment_id UUID,
            ADD COLUMN IF NOT EXISTS source VARCHAR(50),
            ADD COLUMN IF NOT EXISTS cost_usd DECIMAL(10,6),
            ADD COLUMN IF NOT EXISTS latency_ms INTEGER;

        -- Add foreign keys if they don't exist
        DO $inner$
        BEGIN
            ALTER TABLE llm_usage_logs
                ADD CONSTRAINT fk_usage_server
                FOREIGN KEY (server_id) REFERENCES model_servers(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN
            NULL; -- Constraint already exists
        END $inner$;

        DO $inner$
        BEGIN
            ALTER TABLE llm_usage_logs
                ADD CONSTRAINT fk_usage_deployment
                FOREIGN KEY (deployment_id) REFERENCES model_deployments(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN
            NULL; -- Constraint already exists
        END $inner$;

        RAISE NOTICE 'Extended existing llm_usage_logs table';
    ELSE
        -- Create new table if it doesn't exist
        CREATE TABLE llm_usage_logs (
            id BIGSERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id VARCHAR(255) NOT NULL,
            model_id VARCHAR(255) NOT NULL,
            provider VARCHAR(50),
            server_id UUID REFERENCES model_servers(id) ON DELETE SET NULL,
            deployment_id UUID REFERENCES model_deployments(id) ON DELETE SET NULL,
            source VARCHAR(50), -- "openwebui", "brigade", "api"
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            cost_usd DECIMAL(10,6),
            latency_ms INTEGER,
            status_code INTEGER,
            error_message TEXT,
            metadata JSONB DEFAULT '{}'::jsonb
        );

        RAISE NOTICE 'Created new llm_usage_logs table';
    END IF;
END;
$$;

-- Indexes for llm_usage_logs (add to existing)
CREATE INDEX IF NOT EXISTS idx_usage_provider ON llm_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_usage_source ON llm_usage_logs(source);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp_model ON llm_usage_logs(timestamp, model_id);
CREATE INDEX IF NOT EXISTS idx_usage_server ON llm_usage_logs(server_id);
CREATE INDEX IF NOT EXISTS idx_usage_deployment ON llm_usage_logs(deployment_id);

COMMENT ON COLUMN llm_usage_logs.source IS 'Origin of request: openwebui, brigade, api';
COMMENT ON COLUMN llm_usage_logs.server_id IS 'Local server used (if local model)';
COMMENT ON COLUMN llm_usage_logs.deployment_id IS 'Specific deployment used (if local)';

-- ============================================================================
-- Table 8: Model Pricing (Cost Tracking)
-- ============================================================================
-- PURPOSE: Track per-model pricing for cost calculation

CREATE TABLE IF NOT EXISTS model_pricing (
    model_id VARCHAR(255) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    input_price_per_1k DECIMAL(10,6) NOT NULL,
    output_price_per_1k DECIMAL(10,6) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source VARCHAR(50) -- "manual", "provider_api", "openrouter"
);

-- Indexes for model_pricing
CREATE INDEX IF NOT EXISTS idx_pricing_provider ON model_pricing(provider);
CREATE INDEX IF NOT EXISTS idx_pricing_updated ON model_pricing(last_updated);

COMMENT ON TABLE model_pricing IS 'Per-model pricing for cost calculation';
COMMENT ON COLUMN model_pricing.source IS 'Where pricing data came from';

-- ============================================================================
-- Table 9: Daily Cost Summary (Analytics)
-- ============================================================================
-- PURPOSE: Pre-aggregated cost data for fast analytics queries

CREATE TABLE IF NOT EXISTS daily_cost_summary (
    date DATE NOT NULL,
    user_id VARCHAR(255),
    provider VARCHAR(50),
    model_id VARCHAR(255),
    total_cost_usd DECIMAL(10,2),
    total_requests INTEGER,
    total_tokens INTEGER,
    PRIMARY KEY (date, user_id, provider, model_id)
);

-- Indexes for daily_cost_summary
CREATE INDEX IF NOT EXISTS idx_daily_cost_user ON daily_cost_summary(user_id, date);
CREATE INDEX IF NOT EXISTS idx_daily_cost_provider ON daily_cost_summary(provider, date);
CREATE INDEX IF NOT EXISTS idx_daily_cost_date ON daily_cost_summary(date);

COMMENT ON TABLE daily_cost_summary IS 'Pre-aggregated daily cost data for analytics';

-- ============================================================================
-- Table 10: Audit Log (Append-Only)
-- ============================================================================
-- PURPOSE: Immutable audit trail for all LLM management operations

CREATE TABLE IF NOT EXISTS audit_log (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id VARCHAR(255),
    action_type VARCHAR(50), -- "model_deployed", "provider_added", "permission_changed"
    resource_type VARCHAR(50), -- "server", "model", "provider", "permission"
    resource_id VARCHAR(255),
    details JSONB DEFAULT '{}'::jsonb,
    ip_address INET,
    user_agent TEXT
);

-- Indexes for audit_log
CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_log(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action_type);

COMMENT ON TABLE audit_log IS 'Immutable audit trail for all LLM management operations';

-- ============================================================================
-- Audit Log Protection (Make Append-Only)
-- ============================================================================

-- Prevent updates
CREATE OR REPLACE RULE audit_log_no_update AS
    ON UPDATE TO audit_log
    DO INSTEAD NOTHING;

-- Prevent deletes
CREATE OR REPLACE RULE audit_log_no_delete AS
    ON DELETE TO audit_log
    DO INSTEAD NOTHING;

COMMENT ON RULE audit_log_no_update ON audit_log IS 'Audit log is append-only - updates blocked';
COMMENT ON RULE audit_log_no_delete ON audit_log IS 'Audit log is append-only - deletes blocked';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'llm_providers',
        'model_servers',
        'installed_models',
        'model_deployments',
        'model_permissions',
        'tier_model_rules',
        'llm_usage_logs',
        'model_pricing',
        'daily_cost_summary',
        'audit_log'
    );

    RAISE NOTICE 'Verified % LLM management tables exist', table_count;

    IF table_count < 10 THEN
        RAISE EXCEPTION 'Migration incomplete - only % of 10 tables created', table_count;
    END IF;
END;
$$;

-- Display summary
SELECT
    'Migration Summary' as status,
    'Unified LLM Management System' as system,
    '1.0.0' as version,
    CURRENT_TIMESTAMP as completed_at;

COMMIT;

-- ============================================================================
-- Migration Complete
-- ============================================================================
