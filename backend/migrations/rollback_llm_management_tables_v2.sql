-- ============================================================================
-- Unified LLM Management System - Rollback Migration V2 (FIXED)
-- Epic 3.2: Rollback Script for LLM Management Tables V2
--
-- VERSION 2.0 CHANGES:
-- - Fixed to work with EXISTING production schema
-- - Only removes NEW columns added by V2 migration
-- - Only drops NEW tables created by V2 migration
-- - Safe for production - preserves all existing data
--
-- WHAT THIS SCRIPT DOES:
-- 1. Drops NEW tables: model_servers, installed_models, model_deployments,
--    model_permissions, tier_model_rules, model_pricing, daily_cost_summary, audit_log
-- 2. Removes NEW columns from existing tables (llm_providers, llm_usage_logs)
-- 3. Removes indexes created by V2 migration
-- 4. Removes audit log protection rules
--
-- WHAT THIS SCRIPT DOES NOT DO:
-- - Does NOT drop llm_providers table (preserves existing provider data)
-- - Does NOT drop llm_usage_logs table (preserves usage history)
-- - Does NOT drop llm_models table (preserves model data)
-- - Does NOT remove EXISTING columns
--
-- Author: Backend Database Specialist
-- Date: October 27, 2025
-- Version: 2.0.0 (PRODUCTION-SAFE)
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Remove Audit Log Protection Rules
-- ============================================================================

DROP RULE IF EXISTS audit_log_no_update ON audit_log;
DROP RULE IF EXISTS audit_log_no_delete ON audit_log;

RAISE NOTICE 'Removed audit log protection rules';

-- ============================================================================
-- Step 2: Drop New Tables (Reverse Dependency Order)
-- ============================================================================

-- Drop daily_cost_summary (no dependencies)
DROP TABLE IF EXISTS daily_cost_summary CASCADE;
RAISE NOTICE 'Dropped daily_cost_summary table';

-- Drop model_pricing (no dependencies)
DROP TABLE IF EXISTS model_pricing CASCADE;
RAISE NOTICE 'Dropped model_pricing table';

-- Drop audit_log (no dependencies)
DROP TABLE IF EXISTS audit_log CASCADE;
RAISE NOTICE 'Dropped audit_log table';

-- Drop model_permissions (no dependencies)
DROP TABLE IF EXISTS model_permissions CASCADE;
RAISE NOTICE 'Dropped model_permissions table';

-- Drop tier_model_rules (no dependencies)
DROP TABLE IF EXISTS tier_model_rules CASCADE;
RAISE NOTICE 'Dropped tier_model_rules table';

-- Drop model_deployments (references installed_models and model_servers)
DROP TABLE IF EXISTS model_deployments CASCADE;
RAISE NOTICE 'Dropped model_deployments table';

-- Drop installed_models (references model_servers)
DROP TABLE IF EXISTS installed_models CASCADE;
RAISE NOTICE 'Dropped installed_models table';

-- Drop model_servers (base table)
DROP TABLE IF EXISTS model_servers CASCADE;
RAISE NOTICE 'Dropped model_servers table';

-- ============================================================================
-- Step 3: Remove Foreign Key Constraints from llm_usage_logs
-- ============================================================================

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_usage_logs') THEN
        -- Drop foreign key constraints
        ALTER TABLE llm_usage_logs DROP CONSTRAINT IF EXISTS fk_usage_server;
        ALTER TABLE llm_usage_logs DROP CONSTRAINT IF EXISTS fk_usage_deployment;
        RAISE NOTICE 'Removed foreign key constraints from llm_usage_logs';
    END IF;
END;
$$;

-- ============================================================================
-- Step 4: Remove New Columns from Existing Tables
-- ============================================================================

-- Remove new columns from llm_usage_logs
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_usage_logs') THEN
        ALTER TABLE llm_usage_logs DROP COLUMN IF EXISTS provider;
        ALTER TABLE llm_usage_logs DROP COLUMN IF EXISTS server_id;
        ALTER TABLE llm_usage_logs DROP COLUMN IF EXISTS deployment_id;
        ALTER TABLE llm_usage_logs DROP COLUMN IF EXISTS source;
        ALTER TABLE llm_usage_logs DROP COLUMN IF EXISTS cost_usd;
        ALTER TABLE llm_usage_logs DROP COLUMN IF EXISTS latency_ms;
        RAISE NOTICE 'Removed new columns from llm_usage_logs';
    END IF;
END;
$$;

-- Remove new columns from llm_providers
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'llm_providers') THEN
        ALTER TABLE llm_providers DROP COLUMN IF EXISTS base_url;
        ALTER TABLE llm_providers DROP COLUMN IF EXISTS metadata;
        ALTER TABLE llm_providers DROP COLUMN IF EXISTS created_by;
        RAISE NOTICE 'Removed new columns from llm_providers';
    END IF;
END;
$$;

-- ============================================================================
-- Step 5: Drop Indexes Created by V2 Migration
-- ============================================================================

-- llm_providers indexes
DROP INDEX IF EXISTS idx_llm_providers_enabled;
DROP INDEX IF EXISTS idx_llm_providers_type;

-- model_servers indexes (table dropped, but be safe)
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

RAISE NOTICE 'Dropped all indexes created by V2 migration';

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    remaining_tables TEXT[];
    existing_tables TEXT[];
BEGIN
    -- Check which new tables still exist
    SELECT ARRAY_AGG(table_name)
    INTO remaining_tables
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

    IF remaining_tables IS NOT NULL THEN
        RAISE WARNING 'Some new tables still exist after rollback: %', remaining_tables;
    ELSE
        RAISE NOTICE '✅ All new tables successfully dropped';
    END IF;

    -- Verify existing tables still exist
    SELECT ARRAY_AGG(table_name)
    INTO existing_tables
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN (
        'llm_providers',
        'llm_usage_logs'
    );

    IF array_length(existing_tables, 1) >= 2 THEN
        RAISE NOTICE '✅ All existing tables preserved: %', existing_tables;
    ELSE
        RAISE WARNING '⚠️  Some existing tables missing: Expected 2+, found %', existing_tables;
    END IF;
END;
$$;

-- Display summary
SELECT
    'Rollback Summary' as status,
    'Unified LLM Management System V2' as system,
    '2.0.0 (PRODUCTION-SAFE)' as version,
    CURRENT_TIMESTAMP as rolled_back_at;

COMMIT;

-- ============================================================================
-- Rollback V2 Complete
-- ============================================================================

-- MANUAL VERIFICATION STEPS:
-- 1. Check that existing tables still have data:
--    SELECT COUNT(*) FROM llm_providers;
--    SELECT COUNT(*) FROM llm_usage_logs;
--
-- 2. Verify new tables are dropped:
--    \dt model_servers     (should not exist)
--    \dt installed_models  (should not exist)
--    \dt model_deployments (should not exist)
--
-- 3. Verify new columns are removed:
--    \d llm_providers   (should NOT have: base_url, metadata, created_by)
--    \d llm_usage_logs  (should NOT have: provider, server_id, deployment_id, source, cost_usd, latency_ms)
--
-- 4. If you need to restore from backup:
--    pg_restore -U unicorn -d unicorn_db backup.sql
