-- ============================================================================
-- Rollback Migration 002: System API Key Storage
--
-- This script removes all columns added in migration 002 and reverts
-- llm_providers table to its original state.
--
-- WARNING: This will delete all stored system API keys!
-- Make sure to export encrypted_api_key values before rolling back.
--
-- Author: Backend API Developer
-- Date: October 27, 2025
-- ============================================================================

-- ============================================================================
-- Backup Reminder
-- ============================================================================

DO $$
BEGIN
    RAISE NOTICE '=======================================================';
    RAISE NOTICE 'WARNING: Rolling back migration 002';
    RAISE NOTICE 'This will delete all system API keys from llm_providers!';
    RAISE NOTICE '=======================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'If you need to preserve keys, run this query first:';
    RAISE NOTICE 'SELECT provider_slug, encrypted_api_key FROM llm_providers WHERE encrypted_api_key IS NOT NULL;';
    RAISE NOTICE '';
END;
$$;

-- ============================================================================
-- Create Backup Table (Optional Safety Net)
-- ============================================================================

-- Create temporary backup of encrypted keys
CREATE TEMP TABLE IF NOT EXISTS llm_providers_keys_backup AS
SELECT
    id,
    provider_slug,
    provider_name,
    encrypted_api_key,
    api_key_source,
    api_key_updated_at,
    api_key_last_tested,
    api_key_test_status,
    NOW() as backed_up_at
FROM llm_providers
WHERE encrypted_api_key IS NOT NULL;

-- Show what will be deleted
DO $$
DECLARE
    backup_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO backup_count FROM llm_providers_keys_backup;

    IF backup_count > 0 THEN
        RAISE NOTICE 'Backed up % provider keys to temp table: llm_providers_keys_backup', backup_count;
        RAISE NOTICE 'This backup will be lost when the session ends!';
    ELSE
        RAISE NOTICE 'No system API keys found to backup';
    END IF;
END;
$$;

-- ============================================================================
-- Drop Indexes
-- ============================================================================

-- Drop indexes created in migration 002
DROP INDEX IF EXISTS idx_llm_providers_api_key_source;
DROP INDEX IF EXISTS idx_llm_providers_has_db_key;

-- ============================================================================
-- Remove Columns
-- ============================================================================

-- Remove all columns added in migration 002
ALTER TABLE llm_providers
DROP COLUMN IF EXISTS encrypted_api_key,
DROP COLUMN IF EXISTS api_key_source,
DROP COLUMN IF EXISTS api_key_updated_at,
DROP COLUMN IF EXISTS api_key_last_tested,
DROP COLUMN IF EXISTS api_key_test_status;

-- ============================================================================
-- Verification
-- ============================================================================

-- Verify columns were removed
DO $$
DECLARE
    remaining_columns INTEGER;
BEGIN
    SELECT COUNT(*) INTO remaining_columns
    FROM information_schema.columns
    WHERE table_name = 'llm_providers'
    AND column_name IN (
        'encrypted_api_key',
        'api_key_source',
        'api_key_updated_at',
        'api_key_last_tested',
        'api_key_test_status'
    );

    IF remaining_columns = 0 THEN
        RAISE NOTICE 'Rollback successful: All migration 002 columns removed';
    ELSE
        RAISE WARNING 'Rollback incomplete: % columns still exist', remaining_columns;
    END IF;
END;
$$;

-- Display current schema
SELECT
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'llm_providers'
ORDER BY ordinal_position;

-- ============================================================================
-- Rollback Complete
-- ============================================================================
-- The llm_providers table is now in its original state (pre-migration 002)
-- All system API keys have been removed
-- Temporary backup (if any) is in: llm_providers_keys_backup
-- ============================================================================
