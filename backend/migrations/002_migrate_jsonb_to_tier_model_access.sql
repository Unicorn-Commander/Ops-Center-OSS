-- ============================================================================
-- Migration: Migrate JSONB data to tier_model_access table
-- Date: November 6, 2025
-- Purpose: Populate tier_model_access from existing tier_access JSONB column
-- ============================================================================

-- This script migrates data from:
--   model_access_control.tier_access (JSONB array)
--   model_access_control.tier_markup (JSONB object)
-- To:
--   tier_model_access table (normalized many-to-many)

DO $$
DECLARE
    model_record RECORD;
    tier_record RECORD;
    tier_code_value TEXT;
    markup_value NUMERIC;
    inserted_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Starting migration from JSONB to tier_model_access...';

    -- Loop through all models
    FOR model_record IN
        SELECT id, model_id, tier_access, tier_markup, enabled
        FROM model_access_control
        WHERE enabled = TRUE
    LOOP
        -- Loop through each tier in tier_access array
        FOR tier_code_value IN
            SELECT jsonb_array_elements_text(model_record.tier_access)
        LOOP
            -- Get tier ID from subscription_tiers
            SELECT id INTO tier_record
            FROM subscription_tiers
            WHERE tier_code = tier_code_value
            LIMIT 1;

            IF FOUND THEN
                -- Get markup multiplier for this tier (default to 1.0 if not found)
                BEGIN
                    markup_value := COALESCE(
                        (model_record.tier_markup->>tier_code_value)::NUMERIC,
                        1.0
                    );
                EXCEPTION WHEN OTHERS THEN
                    markup_value := 1.0;
                END;

                -- Insert into tier_model_access (skip if already exists)
                INSERT INTO tier_model_access (
                    tier_id,
                    model_id,
                    enabled,
                    markup_multiplier
                )
                VALUES (
                    tier_record.id,
                    model_record.id,
                    TRUE,
                    markup_value
                )
                ON CONFLICT (tier_id, model_id) DO NOTHING;

                inserted_count := inserted_count + 1;
            ELSE
                RAISE WARNING 'Tier not found: % for model %', tier_code_value, model_record.model_id;
            END IF;
        END LOOP;
    END LOOP;

    RAISE NOTICE 'Migration complete: % tier-model relationships created', inserted_count;

    -- Verification
    RAISE NOTICE 'Verification:';
    RAISE NOTICE '  - Models in model_access_control: %', (SELECT COUNT(*) FROM model_access_control WHERE enabled = TRUE);
    RAISE NOTICE '  - Tiers in subscription_tiers: %', (SELECT COUNT(*) FROM subscription_tiers WHERE is_active = TRUE);
    RAISE NOTICE '  - Relationships in tier_model_access: %', (SELECT COUNT(*) FROM tier_model_access WHERE enabled = TRUE);
END $$;

-- Create a verification view
CREATE OR REPLACE VIEW v_tier_model_summary AS
SELECT
    st.tier_code,
    st.tier_name,
    st.sort_order,
    COUNT(DISTINCT tma.model_id) as model_count,
    ARRAY_AGG(DISTINCT m.provider ORDER BY m.provider) as providers,
    MIN(tma.markup_multiplier) as min_markup,
    MAX(tma.markup_multiplier) as max_markup
FROM subscription_tiers st
LEFT JOIN tier_model_access tma ON st.id = tma.tier_id AND tma.enabled = TRUE
LEFT JOIN model_access_control m ON tma.model_id = m.id AND m.enabled = TRUE
WHERE st.is_active = TRUE
GROUP BY st.tier_code, st.tier_name, st.sort_order
ORDER BY st.sort_order;

COMMENT ON VIEW v_tier_model_summary IS 'Summary view of models available per tier';

-- Display migration results
SELECT * FROM v_tier_model_summary;
