-- ============================================================================
-- Migration: Populate tier_model_access with all models for all tiers
-- Date: November 6, 2025
-- Purpose: Assign all active models to all active tiers with appropriate markup
-- ============================================================================

DO $$
DECLARE
    model_count INTEGER;
    relationship_count INTEGER := 0;
BEGIN
    RAISE NOTICE 'Populating tier_model_access with all models for all tiers...';

    -- Insert all models for vip_founder tier (0% markup - at cost)
    INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
    SELECT
        st.id AS tier_id,
        m.id AS model_id,
        0.0 AS markup_multiplier,  -- VIP Founder: no markup
        TRUE AS enabled
    FROM subscription_tiers st
    CROSS JOIN model_access_control m
    WHERE st.tier_code = 'vip_founder'
      AND m.enabled = TRUE
      AND m.deprecated = FALSE
    ON CONFLICT (tier_id, model_id) DO UPDATE SET
        enabled = TRUE,
        markup_multiplier = 0.0;

    GET DIAGNOSTICS relationship_count = ROW_COUNT;
    RAISE NOTICE '  - VIP Founder: % models assigned (0%% markup)', relationship_count;

    -- Insert all models for byok tier (0% markup - user brings own keys)
    INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
    SELECT
        st.id AS tier_id,
        m.id AS model_id,
        0.0 AS markup_multiplier,  -- BYOK: no markup (passthrough)
        TRUE AS enabled
    FROM subscription_tiers st
    CROSS JOIN model_access_control m
    WHERE st.tier_code = 'byok'
      AND m.enabled = TRUE
      AND m.deprecated = FALSE
    ON CONFLICT (tier_id, model_id) DO UPDATE SET
        enabled = TRUE,
        markup_multiplier = 0.0;

    GET DIAGNOSTICS relationship_count = ROW_COUNT;
    RAISE NOTICE '  - BYOK: % models assigned (0%% markup)', relationship_count;

    -- Insert all models for managed tier (20% markup)
    INSERT INTO tier_model_access (tier_id, model_id, markup_multiplier, enabled)
    SELECT
        st.id AS tier_id,
        m.id AS model_id,
        1.2 AS markup_multiplier,  -- Managed: 20% markup
        TRUE AS enabled
    FROM subscription_tiers st
    CROSS JOIN model_access_control m
    WHERE st.tier_code = 'managed'
      AND m.enabled = TRUE
      AND m.deprecated = FALSE
    ON CONFLICT (tier_id, model_id) DO UPDATE SET
        enabled = TRUE,
        markup_multiplier = 1.2;

    GET DIAGNOSTICS relationship_count = ROW_COUNT;
    RAISE NOTICE '  - Managed: % models assigned (20%% markup)', relationship_count;

    -- Get total counts
    SELECT COUNT(*) INTO model_count FROM model_access_control WHERE enabled = TRUE AND deprecated = FALSE;

    RAISE NOTICE 'Population complete!';
    RAISE NOTICE '  - Total models: %', model_count;
    RAISE NOTICE '  - Total tiers: 3';
    RAISE NOTICE '  - Total relationships: %', (SELECT COUNT(*) FROM tier_model_access WHERE enabled = TRUE);
END $$;

-- Verify results
SELECT * FROM v_tier_model_summary;
