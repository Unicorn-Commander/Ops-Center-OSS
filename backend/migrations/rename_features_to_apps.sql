-- ==================================================
-- Database Migration: Rename Features to Apps
-- ==================================================
-- Purpose: Rename all "feature" terminology to "app" terminology
-- Database: unicorn_db
-- Tables: feature_definitions → app_definitions
--         tier_features → tier_apps
-- Author: Database Migration Specialist
-- Date: 2025-11-09
-- ==================================================

BEGIN;

-- ==================================================
-- SAFETY CHECK: Prevent re-running migration
-- ==================================================
DO $$
BEGIN
    -- Check if migration already completed
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'app_definitions') THEN
        RAISE NOTICE 'Migration already completed - app_definitions table exists';
        RAISE NOTICE 'Skipping migration to prevent data loss';
        RAISE EXCEPTION 'Migration already applied' USING ERRCODE = 'unique_violation';
    END IF;
END $$;

-- ==================================================
-- STEP 1: Rename Tables
-- ==================================================

-- Rename feature_definitions to app_definitions
ALTER TABLE IF EXISTS feature_definitions
    RENAME TO app_definitions;

-- Rename tier_features to tier_apps
ALTER TABLE IF EXISTS tier_features
    RENAME TO tier_apps;

DO $$ BEGIN
    RAISE NOTICE 'Renamed tables: feature_definitions → app_definitions, tier_features → tier_apps';
END $$;

-- ==================================================
-- STEP 2: Rename Columns in app_definitions
-- ==================================================

-- Rename feature_key to app_key
ALTER TABLE app_definitions
    RENAME COLUMN feature_key TO app_key;

-- Rename feature_name to app_name
ALTER TABLE app_definitions
    RENAME COLUMN feature_name TO app_name;

DO $$ BEGIN
    RAISE NOTICE 'Renamed columns in app_definitions: feature_key → app_key, feature_name → app_name';
END $$;

-- ==================================================
-- STEP 3: Rename Columns in tier_apps
-- ==================================================

-- Rename feature_key to app_key
ALTER TABLE tier_apps
    RENAME COLUMN feature_key TO app_key;

-- Rename feature_value to app_value
ALTER TABLE tier_apps
    RENAME COLUMN feature_value TO app_value;

DO $$ BEGIN
    RAISE NOTICE 'Renamed columns in tier_apps: feature_key → app_key, feature_value → app_value';
END $$;

-- ==================================================
-- STEP 4: Rename Sequences
-- ==================================================

-- Rename sequences (if they exist)
DO $$
BEGIN
    -- tier_features_id_seq → tier_apps_id_seq
    IF EXISTS (SELECT 1 FROM pg_sequences WHERE schemaname = 'public' AND sequencename = 'tier_features_id_seq') THEN
        ALTER SEQUENCE tier_features_id_seq RENAME TO tier_apps_id_seq;
        RAISE NOTICE 'Renamed sequence: tier_features_id_seq → tier_apps_id_seq';
    END IF;

    -- Note: feature_definitions doesn't have an auto-increment sequence
END $$;

-- ==================================================
-- STEP 5: Rename Indexes
-- ==================================================

-- Rename tier_features indexes
ALTER INDEX IF EXISTS tier_features_pkey
    RENAME TO tier_apps_pkey;

ALTER INDEX IF EXISTS unique_tier_feature
    RENAME TO unique_tier_app;

ALTER INDEX IF EXISTS idx_tier_features_tier
    RENAME TO idx_tier_apps_tier;

ALTER INDEX IF EXISTS idx_tier_features_key
    RENAME TO idx_tier_apps_key;

DO $$ BEGIN
    RAISE NOTICE 'Renamed 4 indexes for tier_apps';
END $$;

-- Rename feature_definitions indexes (if they exist)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_feature_defs_category') THEN
        ALTER INDEX idx_feature_defs_category RENAME TO idx_app_defs_category;
        RAISE NOTICE 'Renamed index: idx_feature_defs_category → idx_app_defs_category';
    END IF;

    IF EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'idx_feature_defs_key') THEN
        ALTER INDEX idx_feature_defs_key RENAME TO idx_app_defs_key;
        RAISE NOTICE 'Renamed index: idx_feature_defs_key → idx_app_defs_key';
    END IF;
END $$;

-- ==================================================
-- STEP 6: Rename Constraints
-- ==================================================

-- Rename unique constraint on tier_apps (if it exists)
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'unique_tier_feature'
        AND conrelid = 'tier_apps'::regclass
    ) THEN
        ALTER TABLE tier_apps RENAME CONSTRAINT unique_tier_feature TO unique_tier_app;
        RAISE NOTICE 'Renamed constraint: unique_tier_feature → unique_tier_app';
    ELSE
        RAISE NOTICE 'Constraint unique_tier_feature not found on tier_apps, skipping rename';
    END IF;
END $$;

-- ==================================================
-- STEP 7: Update Trigger Names
-- ==================================================

-- Rename trigger on tier_apps
DROP TRIGGER IF EXISTS trg_tier_features_update ON tier_apps;

CREATE TRIGGER trg_tier_apps_update
    BEFORE UPDATE ON tier_apps
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_tier_timestamp();

DO $$ BEGIN
    RAISE NOTICE 'Renamed trigger: trg_tier_features_update → trg_tier_apps_update';
END $$;

-- ==================================================
-- STEP 8: Update Views (if they reference the tables)
-- ==================================================

-- Recreate v_active_tiers view with new table name
DROP VIEW IF EXISTS v_active_tiers CASCADE;

CREATE OR REPLACE VIEW v_active_tiers AS
SELECT
    st.id,
    st.tier_code,
    st.tier_name,
    st.description,
    st.price_monthly,
    st.price_yearly,
    st.is_invite_only,
    st.sort_order,
    st.api_calls_limit,
    st.team_seats,
    st.byok_enabled,
    st.priority_support,
    st.lago_plan_code,
    COUNT(ta.id) AS app_count,  -- Changed from feature_count
    st.created_at,
    st.updated_at
FROM subscription_tiers st
LEFT JOIN tier_apps ta ON st.id = ta.tier_id AND ta.enabled = TRUE
WHERE st.is_active = TRUE
GROUP BY st.id
ORDER BY st.sort_order;

DO $$ BEGIN
    RAISE NOTICE 'Recreated view: v_active_tiers (now uses tier_apps)';
END $$;

-- ==================================================
-- STEP 9: Create Backward-Compatible Views (Optional)
-- ==================================================

-- Create view for old table name (feature_definitions)
CREATE OR REPLACE VIEW feature_definitions AS
SELECT
    id,
    app_key AS feature_key,
    app_name AS feature_name,
    description,
    value_type,
    default_value,
    category,
    is_system,
    created_at,
    is_active,
    sort_order,
    updated_at
FROM app_definitions;

DO $$ BEGIN
    RAISE NOTICE 'Created backward-compatible view: feature_definitions';
END $$;

-- Create view for old table name (tier_features)
CREATE OR REPLACE VIEW tier_features AS
SELECT
    id,
    tier_id,
    app_key AS feature_key,
    app_value AS feature_value,
    enabled,
    created_at,
    updated_at
FROM tier_apps;

DO $$ BEGIN
    RAISE NOTICE 'Created backward-compatible view: tier_features';
END $$;

-- ==================================================
-- STEP 10: Grant Permissions
-- ==================================================

-- Grant permissions on new tables
GRANT SELECT, INSERT, UPDATE, DELETE ON app_definitions TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON tier_apps TO unicorn;

-- Grant permissions on sequence
GRANT USAGE, SELECT ON SEQUENCE tier_apps_id_seq TO unicorn;

-- Grant permissions on views
GRANT SELECT ON v_active_tiers TO unicorn;
GRANT SELECT ON feature_definitions TO unicorn;  -- Backward-compatible view
GRANT SELECT ON tier_features TO unicorn;        -- Backward-compatible view

DO $$ BEGIN
    RAISE NOTICE 'Granted permissions to unicorn user';
END $$;

-- ==================================================
-- STEP 11: Validate Data Integrity
-- ==================================================

DO $$
DECLARE
    app_def_count INTEGER;
    tier_app_count INTEGER;
BEGIN
    -- Count records in app_definitions
    SELECT COUNT(*) INTO app_def_count FROM app_definitions;
    RAISE NOTICE 'app_definitions contains % rows', app_def_count;

    -- Count records in tier_apps
    SELECT COUNT(*) INTO tier_app_count FROM tier_apps;
    RAISE NOTICE 'tier_apps contains % rows', tier_app_count;

    -- Verify foreign key relationships
    IF EXISTS (
        SELECT 1 FROM tier_apps ta
        LEFT JOIN subscription_tiers st ON ta.tier_id = st.id
        WHERE st.id IS NULL
    ) THEN
        RAISE WARNING 'Found orphaned records in tier_apps with invalid tier_id';
    ELSE
        RAISE NOTICE 'All tier_apps records have valid tier_id references';
    END IF;
END $$;

-- ==================================================
-- MIGRATION COMPLETE
-- ==================================================

COMMIT;

DO $$ BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tables renamed:';
    RAISE NOTICE '  - feature_definitions → app_definitions';
    RAISE NOTICE '  - tier_features → tier_apps';
    RAISE NOTICE 'Columns renamed:';
    RAISE NOTICE '  - feature_key → app_key';
    RAISE NOTICE '  - feature_name → app_name';
    RAISE NOTICE '  - feature_value → app_value';
    RAISE NOTICE 'Backward-compatible views created:';
    RAISE NOTICE '  - feature_definitions (view)';
    RAISE NOTICE '  - tier_features (view)';
    RAISE NOTICE '========================================';
END $$;

-- ==================================================
-- ROLLBACK SCRIPT (COMMENTED OUT - FOR EMERGENCIES)
-- ==================================================
-- To rollback this migration, run the following:
/*
BEGIN;

-- Drop backward-compatible views
DROP VIEW IF EXISTS feature_definitions CASCADE;
DROP VIEW IF EXISTS tier_features CASCADE;

-- Rename tables back
ALTER TABLE app_definitions RENAME TO feature_definitions;
ALTER TABLE tier_apps RENAME TO tier_features;

-- Rename columns back in feature_definitions
ALTER TABLE feature_definitions RENAME COLUMN app_key TO feature_key;
ALTER TABLE feature_definitions RENAME COLUMN app_name TO feature_name;

-- Rename columns back in tier_features
ALTER TABLE tier_features RENAME COLUMN app_key TO feature_key;
ALTER TABLE tier_features RENAME COLUMN app_value TO feature_value;

-- Rename sequence back
ALTER SEQUENCE tier_apps_id_seq RENAME TO tier_features_id_seq;

-- Rename indexes back
ALTER INDEX tier_apps_pkey RENAME TO tier_features_pkey;
ALTER INDEX unique_tier_app RENAME TO unique_tier_feature;
ALTER INDEX idx_tier_apps_tier RENAME TO idx_tier_features_tier;
ALTER INDEX idx_tier_apps_key RENAME TO idx_tier_features_key;
ALTER INDEX idx_app_defs_category RENAME TO idx_feature_defs_category;
ALTER INDEX idx_app_defs_key RENAME TO idx_feature_defs_key;

-- Rename constraint back
ALTER TABLE tier_features RENAME CONSTRAINT unique_tier_app TO unique_tier_feature;

-- Recreate trigger with old name
DROP TRIGGER IF EXISTS trg_tier_apps_update ON tier_features;
CREATE TRIGGER trg_tier_features_update
    BEFORE UPDATE ON tier_features
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_tier_timestamp();

-- Recreate v_active_tiers view with old naming
DROP VIEW IF EXISTS v_active_tiers CASCADE;
CREATE OR REPLACE VIEW v_active_tiers AS
SELECT
    st.id,
    st.tier_code,
    st.tier_name,
    st.description,
    st.price_monthly,
    st.price_yearly,
    st.is_invite_only,
    st.sort_order,
    st.api_calls_limit,
    st.team_seats,
    st.byok_enabled,
    st.priority_support,
    st.lago_plan_code,
    COUNT(tf.id) AS feature_count,
    st.created_at,
    st.updated_at
FROM subscription_tiers st
LEFT JOIN tier_features tf ON st.id = tf.tier_id AND tf.enabled = TRUE
WHERE st.is_active = TRUE
GROUP BY st.id
ORDER BY st.sort_order;

-- Regrant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON feature_definitions TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON tier_features TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE tier_features_id_seq TO unicorn;
GRANT SELECT ON v_active_tiers TO unicorn;

COMMIT;

RAISE NOTICE 'Rollback completed successfully';
*/
