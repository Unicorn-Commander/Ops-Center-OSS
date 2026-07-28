-- ============================================================================
-- Unified LLM Management System - Database Migration V2 (FIXED)
-- Epic 3.2: Consolidation of 4 Fragmented LLM Pages into Single System
--
-- VERSION 2.0 CHANGES:
-- - Fixed to work with EXISTING production schema
-- - Uses information_schema checks before all operations
-- - Only creates NEW tables (not existing ones)
-- - Only adds NEW columns to existing tables
-- - Safe for production - no data loss
--
-- EXISTING PRODUCTION SCHEMA (DO NOT RECREATE):
-- - llm_providers (with columns: id, name, type, api_key_encrypted, enabled, priority, config, created_at, updated_at, health_status, last_health_check, encrypted_api_key, api_key_source, api_key_updated_at, api_key_last_tested, api_key_test_status)
-- - llm_models (exists but schema unknown)
-- - llm_usage_logs (exists but schema unknown)
-- - llm_routing_rules (exists)
-- - user_llm_settings (exists)
--
-- Author: Backend Database Specialist
-- Date: October 27, 2025
-- Version: 2.0.0 (PRODUCTION-SAFE)
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
-- STRATEGY: Only ADD new columns to existing table

DO $$
BEGIN
    -- Verify llm_providers exists (it DOES in production)
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'llm_providers') THEN
        RAISE EXCEPTION 'llm_providers table does not exist - unexpected!';
    END IF;

    -- Add base_url column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_providers' AND column_name = 'base_url'
    ) THEN
        ALTER TABLE llm_providers ADD COLUMN base_url VARCHAR(512);
        RAISE NOTICE 'Added base_url column to llm_providers';
    END IF;

    -- Add metadata column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_providers' AND column_name = 'metadata'
    ) THEN
        ALTER TABLE llm_providers ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
        RAISE NOTICE 'Added metadata column to llm_providers';
    END IF;

    -- Add created_by column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_providers' AND column_name = 'created_by'
    ) THEN
        ALTER TABLE llm_providers ADD COLUMN created_by VARCHAR(255);
        RAISE NOTICE 'Added created_by column to llm_providers';
    END IF;

    RAISE NOTICE 'Extended existing llm_providers table with new columns';
END;
$$;

-- Indexes for llm_providers (safe to add)
CREATE INDEX IF NOT EXISTS idx_llm_providers_enabled ON llm_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_llm_providers_type ON llm_providers(type);

-- ============================================================================
-- Table 2: Model Servers (Local Infrastructure)
-- ============================================================================
-- PURPOSE: Track local model servers (Ollama, vLLM, LMStudio)
-- STRATEGY: Create new table (does not exist in production)

CREATE TABLE IF NOT EXISTS model_servers (
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

-- Indexes for model_servers
CREATE INDEX IF NOT EXISTS idx_model_servers_health ON model_servers(health_status, enabled);
CREATE INDEX IF NOT EXISTS idx_model_servers_type ON model_servers(type);
CREATE INDEX IF NOT EXISTS idx_model_servers_location ON model_servers(location);

COMMENT ON TABLE model_servers IS 'Local LLM inference servers (Ollama, vLLM, etc.)';
COMMENT ON COLUMN model_servers.gpu_id IS 'GPU device ID (0, 1, etc.)';
COMMENT ON COLUMN model_servers.health_status IS 'Health status: healthy, degraded, unhealthy, unknown';

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
-- STRATEGY: Only ADD new columns to existing table

DO $$
BEGIN
    -- Verify llm_usage_logs exists (it DOES in production)
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables
                   WHERE table_name = 'llm_usage_logs') THEN
        RAISE EXCEPTION 'llm_usage_logs table does not exist - unexpected!';
    END IF;

    -- Add provider column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_usage_logs' AND column_name = 'provider'
    ) THEN
        ALTER TABLE llm_usage_logs ADD COLUMN provider VARCHAR(50);
        RAISE NOTICE 'Added provider column to llm_usage_logs';
    END IF;

    -- Add server_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_usage_logs' AND column_name = 'server_id'
    ) THEN
        ALTER TABLE llm_usage_logs ADD COLUMN server_id UUID;
        RAISE NOTICE 'Added server_id column to llm_usage_logs';
    END IF;

    -- Add deployment_id column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_usage_logs' AND column_name = 'deployment_id'
    ) THEN
        ALTER TABLE llm_usage_logs ADD COLUMN deployment_id UUID;
        RAISE NOTICE 'Added deployment_id column to llm_usage_logs';
    END IF;

    -- Add source column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_usage_logs' AND column_name = 'source'
    ) THEN
        ALTER TABLE llm_usage_logs ADD COLUMN source VARCHAR(50);
        RAISE NOTICE 'Added source column to llm_usage_logs';
    END IF;

    -- Add cost_usd column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_usage_logs' AND column_name = 'cost_usd'
    ) THEN
        ALTER TABLE llm_usage_logs ADD COLUMN cost_usd DECIMAL(10,6);
        RAISE NOTICE 'Added cost_usd column to llm_usage_logs';
    END IF;

    -- Add latency_ms column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'llm_usage_logs' AND column_name = 'latency_ms'
    ) THEN
        ALTER TABLE llm_usage_logs ADD COLUMN latency_ms INTEGER;
        RAISE NOTICE 'Added latency_ms column to llm_usage_logs';
    END IF;

    RAISE NOTICE 'Extended existing llm_usage_logs table with new columns';
END;
$$;

-- Add foreign key constraints if they don't exist
DO $$
BEGIN
    -- Add FK to model_servers
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_usage_server'
    ) THEN
        ALTER TABLE llm_usage_logs
            ADD CONSTRAINT fk_usage_server
            FOREIGN KEY (server_id) REFERENCES model_servers(id) ON DELETE SET NULL;
        RAISE NOTICE 'Added foreign key fk_usage_server';
    END IF;

    -- Add FK to model_deployments
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_usage_deployment'
    ) THEN
        ALTER TABLE llm_usage_logs
            ADD CONSTRAINT fk_usage_deployment
            FOREIGN KEY (deployment_id) REFERENCES model_deployments(id) ON DELETE SET NULL;
        RAISE NOTICE 'Added foreign key fk_usage_deployment';
    END IF;
END;
$$;

-- Indexes for llm_usage_logs (safe to add)
CREATE INDEX IF NOT EXISTS idx_usage_provider ON llm_usage_logs(provider);
CREATE INDEX IF NOT EXISTS idx_usage_source ON llm_usage_logs(source);
CREATE INDEX IF NOT EXISTS idx_usage_timestamp_model ON llm_usage_logs(timestamp, model_id) WHERE timestamp IS NOT NULL AND model_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_server ON llm_usage_logs(server_id) WHERE server_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_usage_deployment ON llm_usage_logs(deployment_id) WHERE deployment_id IS NOT NULL;

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

-- Drop existing rules if they exist
DROP RULE IF EXISTS audit_log_no_update ON audit_log;
DROP RULE IF EXISTS audit_log_no_delete ON audit_log;

-- Create protection rules
CREATE RULE audit_log_no_update AS
    ON UPDATE TO audit_log
    DO INSTEAD NOTHING;

CREATE RULE audit_log_no_delete AS
    ON DELETE TO audit_log
    DO INSTEAD NOTHING;

COMMENT ON RULE audit_log_no_update ON audit_log IS 'Audit log is append-only - updates blocked';
COMMENT ON RULE audit_log_no_delete ON audit_log IS 'Audit log is append-only - deletes blocked';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    existing_count INTEGER;
    new_count INTEGER;
BEGIN
    -- Check existing tables
    SELECT COUNT(*) INTO existing_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'llm_providers',
        'llm_usage_logs'
    );

    -- Check new tables
    SELECT COUNT(*) INTO new_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'model_servers',
        'installed_models',
        'model_deployments',
        'model_permissions',
        'tier_model_rules',
        'model_pricing',
        'daily_cost_summary',
        'audit_log'
    );

    RAISE NOTICE 'Verified % existing tables', existing_count;
    RAISE NOTICE 'Verified % new tables created', new_count;

    IF existing_count < 2 THEN
        RAISE EXCEPTION 'Missing existing tables - only % of 2 found', existing_count;
    END IF;

    IF new_count < 8 THEN
        RAISE EXCEPTION 'Migration incomplete - only % of 8 new tables created', new_count;
    END IF;

    RAISE NOTICE '✅ Migration V2 completed successfully';
END;
$$;

-- Display summary
SELECT
    'Migration Summary' as status,
    'Unified LLM Management System V2' as system,
    '2.0.0 (PRODUCTION-SAFE)' as version,
    CURRENT_TIMESTAMP as completed_at;

COMMIT;

-- ============================================================================
-- Migration V2 Complete
-- ============================================================================
