-- ============================================================================
-- Unified LLM Management System - Rollback Migration
-- Epic 3.2: Rollback Script for LLM Management Tables
--
-- This script safely rolls back the create_llm_management_tables.sql migration.
--
-- IMPORTANT SAFETY NOTES:
-- 1. Does NOT drop tables that existed before migration (llm_providers, model_servers, llm_usage_logs)
-- 2. Only removes NEW columns added to existing tables
-- 3. Drops NEW tables created by migration
-- 4. Preserves all user data in existing tables
-- 5. Use with caution in production
--
-- WHAT THIS SCRIPT DOES:
-- - Drops new tables: installed_models, model_deployments, model_permissions,
--   tier_model_rules, model_pricing, daily_cost_summary, audit_log
-- - Removes new columns from existing tables (llm_providers, model_servers, llm_usage_logs)
-- - Removes indexes created by migration
-- - Removes audit log protection rules
--
-- WHAT THIS SCRIPT DOES NOT DO:
-- - Does NOT drop llm_providers table (preserves existing provider data)
-- - Does NOT drop model_servers table (preserves existing server configs)
-- - Does NOT drop llm_usage_logs table (preserves usage history)
--
-- Author: Backend Database Specialist
-- Date: October 27, 2025
-- Version: 1.0.0
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Remove Audit Log Protection Rules
-- ============================================================================

DROP RULE IF EXISTS audit_log_no_update ON audit_log;
DROP RULE IF EXISTS audit_log_no_delete ON audit_log;


-- ============================================================================
-- Step 2: Drop New Tables (Reverse Dependency Order)
-- ============================================================================

-- Drop daily_cost_summary (no dependencies)
DROP TABLE IF EXISTS daily_cost_summary CASCADE;

-- Drop model_pricing (no dependencies)
DROP TABLE IF EXISTS model_pricing CASCADE;

-- Drop audit_log (no dependencies)
DROP TABLE IF EXISTS audit_log CASCADE;

-- Drop model_permissions (no dependencies)
DROP TABLE IF EXISTS model_permissions CASCADE;

-- Drop tier_model_rules (no dependencies)
DROP TABLE IF EXISTS tier_model_rules CASCADE;

-- Drop model_deployments (references installed_models)
DROP TABLE IF EXISTS model_deployments CASCADE;

-- Drop installed_models (references model_servers)
DROP TABLE IF EXISTS installed_models CASCADE;

-- ============================================================================
-- Step 3: Remove New Columns from Existing Tables
-- ============================================================================

-- Remove new columns from llm_usage_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_usage_logs') THEN
        ALTER TABLE llm_usage_logs
            DROP COLUMN IF EXISTS provider,
            DROP COLUMN IF EXISTS server_id,
            DROP COLUMN IF EXISTS deployment_id,
            DROP COLUMN IF EXISTS source,
            DROP COLUMN IF EXISTS cost_usd,
            DROP COLUMN IF EXISTS latency_ms;

        -- Drop foreign key constraints
        ALTER TABLE llm_usage_logs
            DROP CONSTRAINT IF EXISTS fk_usage_server,
            DROP CONSTRAINT IF EXISTS fk_usage_deployment;

        RAISE NOTICE 'Removed new columns from llm_usage_logs';
    END IF;
END;
$$;

-- Remove new columns from model_servers
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'model_servers') THEN
        ALTER TABLE model_servers
            DROP COLUMN IF EXISTS location,
            DROP COLUMN IF EXISTS host,
            DROP COLUMN IF EXISTS port,
            DROP COLUMN IF EXISTS gpu_id,
            DROP COLUMN IF EXISTS auto_start,
            DROP COLUMN IF EXISTS enabled;

        -- Rename type back to server_type if it was renamed
        DO $inner$
        BEGIN
            ALTER TABLE model_servers
                RENAME COLUMN type TO server_type;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- Column not renamed, skip
        END $inner$;

        RAISE NOTICE 'Removed new columns from model_servers';
    END IF;
END;
$$;

-- Remove new columns from llm_providers
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_providers') THEN
        ALTER TABLE llm_providers
            DROP COLUMN IF EXISTS api_key_encrypted,
            DROP COLUMN IF EXISTS metadata;

        -- Rename enabled back to is_active if it was renamed
        DO $inner$
        BEGIN
            ALTER TABLE llm_providers
                RENAME COLUMN enabled TO is_active;
        EXCEPTION WHEN OTHERS THEN
            NULL; -- Column not renamed, skip
        END $inner$;

        RAISE NOTICE 'Removed new columns from llm_providers';
    END IF;
END;
$$;

-- ============================================================================
-- Step 4: Drop Indexes Created by Migration
-- ============================================================================

-- llm_providers indexes
DROP INDEX IF EXISTS idx_llm_providers_enabled;
DROP INDEX IF EXISTS idx_llm_providers_type;

-- model_servers indexes
DROP INDEX IF EXISTS idx_model_servers_health;
DROP INDEX IF EXISTS idx_model_servers_type;
DROP INDEX IF EXISTS idx_model_servers_location;

-- installed_models indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_installed_models_server;
DROP INDEX IF EXISTS idx_installed_models_name;
DROP INDEX IF EXISTS idx_installed_models_last_used;

-- model_deployments indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_deployments_server;
DROP INDEX IF EXISTS idx_deployments_model;
DROP INDEX IF EXISTS idx_deployments_alias;
DROP INDEX IF EXISTS idx_deployments_status;

-- model_permissions indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_permissions_model;
DROP INDEX IF EXISTS idx_permissions_access;
DROP INDEX IF EXISTS idx_permissions_lookup;

-- tier_model_rules indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_tier_rules_tier;
DROP INDEX IF EXISTS idx_tier_rules_pattern;

-- llm_usage_logs indexes
DROP INDEX IF EXISTS idx_usage_provider;
DROP INDEX IF EXISTS idx_usage_source;
DROP INDEX IF EXISTS idx_usage_timestamp_model;
DROP INDEX IF EXISTS idx_usage_server;
DROP INDEX IF EXISTS idx_usage_deployment;

-- model_pricing indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_pricing_provider;
DROP INDEX IF EXISTS idx_pricing_updated;

-- daily_cost_summary indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_daily_cost_user;
DROP INDEX IF EXISTS idx_daily_cost_provider;
DROP INDEX IF EXISTS idx_daily_cost_date;

-- audit_log indexes (table dropped, but be safe)
DROP INDEX IF EXISTS idx_audit_user;
DROP INDEX IF EXISTS idx_audit_resource;
DROP INDEX IF EXISTS idx_audit_timestamp;
DROP INDEX IF EXISTS idx_audit_action;


-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    remaining_tables TEXT[];
BEGIN
    -- Check which new tables still exist
    SELECT ARRAY_AGG(table_name)
    INTO remaining_tables
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'installed_models',
        'model_deployments',
        'model_permissions',
        'tier_model_rules',
        'model_pricing',
        'daily_cost_summary',
        'audit_log'
    );

    IF remaining_tables IS NOT NULL THEN
        RAISE WARNING 'Some tables still exist after rollback: %', remaining_tables;
    ELSE
        RAISE NOTICE 'All new tables successfully dropped';
    END IF;

    -- Verify existing tables still exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_providers') THEN
        RAISE WARNING 'llm_providers table missing - may need manual restoration';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'model_servers') THEN
        RAISE WARNING 'model_servers table missing - may need manual restoration';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_usage_logs') THEN
        RAISE WARNING 'llm_usage_logs table missing - may need manual restoration';
    END IF;
END;
$$;

-- Display summary
SELECT
    'Rollback Summary' as status,
    'Unified LLM Management System' as system,
    '1.0.0' as version,
    CURRENT_TIMESTAMP as rolled_back_at;

COMMIT;

-- ============================================================================
-- Rollback Complete
-- ============================================================================

-- MANUAL VERIFICATION STEPS:
-- 1. Check that existing tables still have data:
--    SELECT COUNT(*) FROM llm_providers;
--    SELECT COUNT(*) FROM model_servers;
--    SELECT COUNT(*) FROM llm_usage_logs;
--
-- 2. Verify new tables are dropped:
--    \dt installed_models  (should not exist)
--    \dt model_deployments (should not exist)
--
-- 3. If you need to restore from backup:
--    pg_restore -U unicorn -d unicorn_db backup.sql
