-- ============================================================================
-- Rollback Dynamic Tier-to-Model Migration
-- Restores JSONB tier_access and tier_markup columns from backups
--
-- Author: Database Migration Specialist
-- Date: November 6, 2025
-- Version: 1.0.0
--
-- WARNING: This will delete the tier_model_access table and restore old schema
-- Only run this if migration failed or needs to be reverted
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Verify Backup Columns Exist
-- ============================================================================

DO $$
DECLARE
    v_has_backup BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'model_access_control'
        AND column_name = 'tier_access_backup'
    ) INTO v_has_backup;

    IF NOT v_has_backup THEN
        RAISE EXCEPTION 'Backup columns do not exist. Cannot safely rollback.';
    END IF;

    RAISE NOTICE 'Backup columns found. Proceeding with rollback...';
END;
$$;

-- ============================================================================
-- Step 2: Restore Old Columns from Backup
-- ============================================================================

-- Restore tier_access and tier_markup from backup columns
UPDATE model_access_control
SET
    tier_access = tier_access_backup,
    tier_markup = tier_markup_backup
WHERE tier_access_backup IS NOT NULL OR tier_markup_backup IS NOT NULL;

-- ============================================================================
-- Step 3: Drop New Objects Created by Migration
-- ============================================================================

-- Drop helper functions
DROP FUNCTION IF EXISTS get_models_for_tier(VARCHAR);
DROP FUNCTION IF EXISTS is_model_available_for_tier(UUID, VARCHAR);
DROP FUNCTION IF EXISTS update_tier_model_access_timestamp();

-- Drop compatibility view
DROP VIEW IF EXISTS v_model_tier_access;

-- Drop trigger
DROP TRIGGER IF EXISTS trigger_update_tier_model_access_timestamp ON tier_model_access;

-- Drop junction table (this will cascade delete all associations)
DROP TABLE IF EXISTS tier_model_access CASCADE;

-- ============================================================================
-- Step 4: Remove Backup Columns
-- ============================================================================

ALTER TABLE model_access_control
    DROP COLUMN IF EXISTS tier_access_backup,
    DROP COLUMN IF EXISTS tier_markup_backup;

-- ============================================================================
-- Verification
-- ============================================================================

DO $$
DECLARE
    v_models_with_tier_access INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_models_with_tier_access
    FROM model_access_control
    WHERE tier_access IS NOT NULL;

    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Rollback Verification';
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Models with tier_access restored: %', v_models_with_tier_access;
    RAISE NOTICE '=================================================';
END;
$$;

-- Display restored data sample
SELECT
    model_id,
    provider,
    display_name,
    tier_access,
    CASE
        WHEN tier_access IS NOT NULL THEN 'Restored'
        ELSE 'No data'
    END AS status
FROM model_access_control
WHERE enabled = TRUE
LIMIT 10;

COMMIT;

-- ============================================================================
-- Rollback Complete
-- ============================================================================

SELECT
    'Rollback completed successfully' AS status,
    NOW() AS completed_at,
    'Original schema restored' AS result;
