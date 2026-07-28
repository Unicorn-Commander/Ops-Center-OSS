-- ============================================================================
-- Tier Naming Standardization Migration
-- Purpose: Migrate from hybrid tier model to 4-tier consumer model
-- Author: Code Quality Analyzer
-- Date: November 6, 2025
-- Status: READY FOR REVIEW - DO NOT RUN WITHOUT APPROVAL
-- ============================================================================
--
-- WHAT THIS DOES:
-- 1. Backs up current user_credits table
-- 2. Migrates legacy tier codes to standard 4-tier model:
--    - free → trial
--    - vip_founder → enterprise
--    - byok → enterprise
--    - managed → professional
-- 3. Verifies all users have valid tier codes
-- 4. Provides rollback instructions
--
-- VALID TIERS AFTER MIGRATION:
--   - trial (was: free)
--   - starter (new tier, no existing users)
--   - professional (unchanged)
--   - enterprise (was: vip_founder, byok)
--
-- ESTIMATED TIME: 2 seconds (for 10 users)
-- RISK: Low (includes backup and rollback plan)
-- ============================================================================

\timing on
\set ON_ERROR_STOP on

-- Pre-flight checks
DO $$
DECLARE
    current_tiers TEXT[];
    tier_counts RECORD;
BEGIN
    RAISE NOTICE '=== PRE-MIGRATION STATUS ===';

    -- Show current tier distribution
    FOR tier_counts IN
        SELECT tier, COUNT(*) as count
        FROM user_credits
        GROUP BY tier
        ORDER BY tier
    LOOP
        RAISE NOTICE 'Tier: % - Users: %', tier_counts.tier, tier_counts.count;
    END LOOP;

    RAISE NOTICE '============================';
END $$;

-- ============================================================================
-- STEP 1: Create backup table
-- ============================================================================

DROP TABLE IF EXISTS user_credits_backup_20251106;

CREATE TABLE user_credits_backup_20251106 AS
SELECT * FROM user_credits;

-- Verify backup
DO $$
DECLARE
    backup_count INT;
    original_count INT;
BEGIN
    SELECT COUNT(*) INTO backup_count FROM user_credits_backup_20251106;
    SELECT COUNT(*) INTO original_count FROM user_credits;

    IF backup_count != original_count THEN
        RAISE EXCEPTION 'Backup verification failed: backup has % rows, original has % rows',
            backup_count, original_count;
    END IF;

    RAISE NOTICE 'Backup created: % users backed up', backup_count;
END $$;

-- ============================================================================
-- STEP 2: Migrate legacy tier codes
-- ============================================================================

BEGIN;

-- Migration: free → trial
UPDATE user_credits
SET tier = 'trial'
WHERE tier = 'free';

-- Migration: vip_founder → enterprise
UPDATE user_credits
SET tier = 'enterprise'
WHERE tier = 'vip_founder';

-- Migration: byok → enterprise
UPDATE user_credits
SET tier = 'enterprise'
WHERE tier = 'byok';

-- Migration: managed → professional
UPDATE user_credits
SET tier = 'professional'
WHERE tier = 'managed';

-- Update timestamps for migrated records
UPDATE user_credits
SET updated_at = CURRENT_TIMESTAMP
WHERE user_id IN (
    SELECT user_id FROM user_credits_backup_20251106
    WHERE tier IN ('free', 'vip_founder', 'byok', 'managed')
);

-- ============================================================================
-- STEP 3: Verify migration
-- ============================================================================

DO $$
DECLARE
    invalid_count INT;
    invalid_tiers TEXT;
    tier_counts RECORD;
BEGIN
    -- Check for invalid tier codes
    SELECT COUNT(*), STRING_AGG(DISTINCT tier, ', ')
    INTO invalid_count, invalid_tiers
    FROM user_credits
    WHERE tier NOT IN ('trial', 'starter', 'professional', 'enterprise');

    IF invalid_count > 0 THEN
        RAISE EXCEPTION 'Migration failed: Found % users with invalid tier codes: %',
            invalid_count, invalid_tiers;
    END IF;

    RAISE NOTICE '=== POST-MIGRATION STATUS ===';

    -- Show new tier distribution
    FOR tier_counts IN
        SELECT tier, COUNT(*) as count
        FROM user_credits
        GROUP BY tier
        ORDER BY
            CASE tier
                WHEN 'trial' THEN 1
                WHEN 'starter' THEN 2
                WHEN 'professional' THEN 3
                WHEN 'enterprise' THEN 4
            END
    LOOP
        RAISE NOTICE 'Tier: % - Users: %', tier_counts.tier, tier_counts.count;
    END LOOP;

    RAISE NOTICE '=============================';
    RAISE NOTICE 'Migration successful: All users have valid tier codes';
END $$;

-- ============================================================================
-- STEP 4: Update schema documentation
-- ============================================================================

COMMENT ON COLUMN user_credits.tier IS
'Valid subscription tiers: trial, starter, professional, enterprise.
Legacy tiers (free, vip_founder, byok, managed) have been migrated.
See /docs/TIER_NAMING_STANDARD.md for details.
Migration date: 2025-11-06';

-- ============================================================================
-- STEP 5: Create audit log entry
-- ============================================================================

DO $$
DECLARE
    migration_summary TEXT;
    migrated_count INT;
BEGIN
    SELECT COUNT(*) INTO migrated_count
    FROM user_credits_backup_20251106
    WHERE tier IN ('free', 'vip_founder', 'byok', 'managed');

    migration_summary := FORMAT(
        'Tier naming standardization migration completed. %s users migrated to new tier codes. ' ||
        'Backup table: user_credits_backup_20251106. ' ||
        'See /docs/TIER_NAMING_STANDARD.md for details.',
        migrated_count
    );

    -- Log to audit table if it exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        INSERT INTO audit_logs (
            action, status, user_id, resource_type, resource_id, metadata, created_at
        )
        VALUES (
            'tier_migration',
            'success',
            'system',
            'user_credits',
            'all',
            jsonb_build_object(
                'migrated_users', migrated_count,
                'migration_date', CURRENT_TIMESTAMP,
                'backup_table', 'user_credits_backup_20251106'
            ),
            CURRENT_TIMESTAMP
        );
    END IF;

    RAISE NOTICE '%', migration_summary;
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION VERIFICATION QUERIES
-- ============================================================================

-- Show tier distribution comparison
SELECT
    'Before' as status,
    tier,
    COUNT(*) as count
FROM user_credits_backup_20251106
GROUP BY tier

UNION ALL

SELECT
    'After' as status,
    tier,
    COUNT(*) as count
FROM user_credits
GROUP BY tier
ORDER BY status, tier;

-- Show migrated users
SELECT
    b.user_id,
    b.tier as old_tier,
    u.tier as new_tier,
    u.credits_remaining,
    u.updated_at
FROM user_credits_backup_20251106 b
JOIN user_credits u ON b.user_id = u.user_id
WHERE b.tier != u.tier
ORDER BY b.tier, u.tier;

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (in case of emergency)
-- ============================================================================
/*
-- EMERGENCY ROLLBACK (only if migration fails)

BEGIN;

-- Restore from backup
TRUNCATE user_credits;

INSERT INTO user_credits
SELECT * FROM user_credits_backup_20251106;

-- Verify restoration
SELECT tier, COUNT(*)
FROM user_credits
GROUP BY tier;

COMMIT;

-- If rollback successful, you can drop the backup:
-- DROP TABLE user_credits_backup_20251106;

*/

-- ============================================================================
-- CLEANUP (run after 90 days if migration is stable)
-- ============================================================================
/*
-- After verifying migration is stable for 90 days:

BEGIN;

-- Drop backup table
DROP TABLE IF EXISTS user_credits_backup_20251106;

-- Remove backup reference from schema comment
COMMENT ON COLUMN user_credits.tier IS
'Valid subscription tiers: trial, starter, professional, enterprise.';

COMMIT;

*/

\timing off

-- Final success message
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '╔════════════════════════════════════════════════════════╗';
    RAISE NOTICE '║  TIER NAMING MIGRATION COMPLETED SUCCESSFULLY          ║';
    RAISE NOTICE '╠════════════════════════════════════════════════════════╣';
    RAISE NOTICE '║  Backup table: user_credits_backup_20251106            ║';
    RAISE NOTICE '║  Valid tiers: trial, starter, professional, enterprise ║';
    RAISE NOTICE '║  Rollback: See ROLLBACK INSTRUCTIONS in this file     ║';
    RAISE NOTICE '╚════════════════════════════════════════════════════════╝';
    RAISE NOTICE '';
END $$;
