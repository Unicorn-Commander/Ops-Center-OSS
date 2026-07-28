-- ============================================================================
-- Dynamic Tier-to-Model Mapping Migration
-- Converts hardcoded JSONB tier arrays to relational many-to-many model
--
-- Author: Database Migration Specialist
-- Date: November 6, 2025
-- Version: 1.0.0
--
-- Purpose: Replace tier_access JSONB column with tier_model_access junction table
-- for flexible many-to-many relationships between tiers and models
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create tier_model_access Junction Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS tier_model_access (
    id SERIAL PRIMARY KEY,
    tier_id INTEGER NOT NULL,
    model_id UUID NOT NULL,
    enabled BOOLEAN DEFAULT TRUE NOT NULL,
    markup_multiplier DECIMAL(4,2) DEFAULT 1.0 NOT NULL,
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW() NOT NULL,

    -- Foreign Keys
    CONSTRAINT fk_tier_model_tier
        FOREIGN KEY (tier_id)
        REFERENCES subscription_tiers(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_tier_model_model
        FOREIGN KEY (model_id)
        REFERENCES model_access_control(id)
        ON DELETE CASCADE,

    -- Unique Constraint
    CONSTRAINT unique_tier_model UNIQUE(tier_id, model_id)
);

COMMENT ON TABLE tier_model_access IS 'Many-to-many relationship between subscription tiers and LLM models';
COMMENT ON COLUMN tier_model_access.enabled IS 'Whether this model is enabled for this tier';
COMMENT ON COLUMN tier_model_access.markup_multiplier IS 'Pricing multiplier for this tier (1.0 = base price)';

-- ============================================================================
-- Step 2: Create Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_tier_model_tier_id
    ON tier_model_access(tier_id);

CREATE INDEX IF NOT EXISTS idx_tier_model_model_id
    ON tier_model_access(model_id);

CREATE INDEX IF NOT EXISTS idx_tier_model_enabled
    ON tier_model_access(enabled)
    WHERE enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_tier_model_lookup
    ON tier_model_access(tier_id, model_id, enabled);

-- ============================================================================
-- Step 3: Migrate Existing Data from JSONB to Relational Model
-- ============================================================================

-- This migration handles the conversion from tier_access JSONB array
-- Example tier_access: ["free", "starter", "professional"]
-- Example tier_markup: {"free": 1.0, "starter": 0.9, "professional": 0.8}

INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
SELECT
    st.id AS tier_id,
    m.id AS model_id,
    COALESCE(
        (m.tier_markup->>st.tier_code)::numeric,
        1.0
    ) AS markup_multiplier,
    TRUE AS enabled
FROM model_access_control m
CROSS JOIN subscription_tiers st
WHERE
    m.tier_access IS NOT NULL
    AND st.tier_code IS NOT NULL
    AND (
        -- Check if tier_code exists in tier_access JSONB array
        m.tier_access @> to_jsonb(st.tier_code::text)
        OR m.tier_access @> to_jsonb(ARRAY[st.tier_code])
    )
ON CONFLICT (tier_id, model_id) DO NOTHING;

-- ============================================================================
-- Step 4: Backup Old Columns Before Dropping
-- ============================================================================

-- Add backup columns to preserve original data
ALTER TABLE model_access_control
    ADD COLUMN IF NOT EXISTS tier_access_backup JSONB,
    ADD COLUMN IF NOT EXISTS tier_markup_backup JSONB;

-- Copy current data to backup columns
UPDATE model_access_control
SET
    tier_access_backup = tier_access,
    tier_markup_backup = tier_markup
WHERE tier_access IS NOT NULL OR tier_markup IS NOT NULL;

-- ============================================================================
-- Step 5: Create Compatibility View for Gradual Migration
-- ============================================================================

-- This view maintains backward compatibility with code expecting tier_access JSONB
CREATE OR REPLACE VIEW v_model_tier_access AS
SELECT
    m.id AS model_id,
    m.model_id AS model_identifier,
    m.provider,
    m.display_name,
    m.pricing AS base_pricing,
    st.id AS tier_id,
    st.tier_code,
    st.tier_name,
    tma.markup_multiplier,
    tma.enabled,
    -- Calculate effective pricing
    CASE
        WHEN m.pricing ? 'input_per_1k' THEN
            jsonb_build_object(
                'input_per_1k', (m.pricing->>'input_per_1k')::numeric * tma.markup_multiplier,
                'output_per_1k', (m.pricing->>'output_per_1k')::numeric * tma.markup_multiplier
            )
        ELSE m.pricing
    END AS effective_pricing,
    tma.created_at,
    tma.updated_at
FROM model_access_control m
INNER JOIN tier_model_access tma ON m.id = tma.model_id
INNER JOIN subscription_tiers st ON tma.tier_id = st.id
WHERE m.enabled = TRUE AND tma.enabled = TRUE;

COMMENT ON VIEW v_model_tier_access IS 'Compatibility view for tier-model relationships with effective pricing';

-- ============================================================================
-- Step 6: Create Helper Functions
-- ============================================================================

-- Function to get all models for a tier
CREATE OR REPLACE FUNCTION get_models_for_tier(p_tier_code VARCHAR)
RETURNS TABLE (
    model_id UUID,
    model_identifier VARCHAR,
    provider VARCHAR,
    display_name VARCHAR,
    markup_multiplier DECIMAL,
    effective_pricing JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        v.model_id,
        v.model_identifier,
        v.provider,
        v.display_name,
        v.markup_multiplier,
        v.effective_pricing
    FROM v_model_tier_access v
    WHERE v.tier_code = p_tier_code
    ORDER BY v.provider, v.display_name;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION get_models_for_tier IS 'Returns all models available for a specific tier with effective pricing';

-- Function to check if model is available for tier
CREATE OR REPLACE FUNCTION is_model_available_for_tier(
    p_model_id UUID,
    p_tier_code VARCHAR
) RETURNS BOOLEAN AS $$
DECLARE
    v_tier_id INTEGER;
BEGIN
    SELECT id INTO v_tier_id
    FROM subscription_tiers
    WHERE tier_code = p_tier_code;

    IF v_tier_id IS NULL THEN
        RETURN FALSE;
    END IF;

    RETURN EXISTS (
        SELECT 1
        FROM tier_model_access
        WHERE tier_id = v_tier_id
        AND model_id = p_model_id
        AND enabled = TRUE
    );
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION is_model_available_for_tier IS 'Check if a specific model is available for a tier';

-- ============================================================================
-- Step 7: Update Trigger for updated_at
-- ============================================================================

CREATE OR REPLACE FUNCTION update_tier_model_access_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tier_model_access_timestamp
    BEFORE UPDATE ON tier_model_access
    FOR EACH ROW
    EXECUTE FUNCTION update_tier_model_access_timestamp();

-- ============================================================================
-- Verification Queries
-- ============================================================================

DO $$
DECLARE
    v_total_models INTEGER;
    v_total_tiers INTEGER;
    v_total_associations INTEGER;
    v_migrated_models INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_total_models FROM model_access_control WHERE enabled = TRUE;
    SELECT COUNT(*) INTO v_total_tiers FROM subscription_tiers WHERE is_active = TRUE;
    SELECT COUNT(*) INTO v_total_associations FROM tier_model_access;
    SELECT COUNT(DISTINCT model_id) INTO v_migrated_models FROM tier_model_access;

    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Migration Verification Summary';
    RAISE NOTICE '=================================================';
    RAISE NOTICE 'Total active models: %', v_total_models;
    RAISE NOTICE 'Total active tiers: %', v_total_tiers;
    RAISE NOTICE 'Total tier-model associations: %', v_total_associations;
    RAISE NOTICE 'Models with tier associations: %', v_migrated_models;
    RAISE NOTICE '=================================================';

    IF v_total_associations = 0 THEN
        RAISE WARNING 'No tier-model associations created. Check if tier_access data exists.';
    END IF;
END;
$$;

-- Display tier breakdown
SELECT
    st.tier_code,
    st.tier_name,
    COUNT(tma.model_id) AS model_count,
    ROUND(AVG(tma.markup_multiplier)::numeric, 2) AS avg_markup
FROM subscription_tiers st
LEFT JOIN tier_model_access tma ON st.id = tma.tier_id AND tma.enabled = TRUE
WHERE st.is_active = TRUE
GROUP BY st.tier_code, st.tier_name
ORDER BY st.sort_order, st.tier_code;

-- ============================================================================
-- Optional: Drop Old Columns (Uncomment when ready)
-- ============================================================================

-- WARNING: Only uncomment these lines after verifying migration success
-- and updating all application code to use the new tier_model_access table

-- ALTER TABLE model_access_control DROP COLUMN IF EXISTS tier_access;
-- ALTER TABLE model_access_control DROP COLUMN IF EXISTS tier_markup;

COMMIT;

-- ============================================================================
-- Migration Complete
-- ============================================================================

SELECT
    'Migration completed successfully' AS status,
    NOW() AS completed_at,
    '1.0.0' AS version;
