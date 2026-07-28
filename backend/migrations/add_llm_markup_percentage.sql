-- ============================================================
-- ADD LLM MARKUP PERCENTAGE TO SUBSCRIPTION TIERS
-- ============================================================
-- Migration Date: 2025-11-17
-- Purpose: Add llm_markup_percentage column for database-driven pricing
-- Required by: litellm_credit_system.py (billing chain integration)
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: Add llm_markup_percentage column
-- ============================================================
ALTER TABLE subscription_tiers
ADD COLUMN IF NOT EXISTS llm_markup_percentage DECIMAL(5,2) DEFAULT 0.00;

COMMENT ON COLUMN subscription_tiers.llm_markup_percentage IS
'Markup percentage applied to LLM API costs. 0.00 = no markup (cost price), 10.00 = 10% markup, 25.00 = 25% markup';

-- ============================================================
-- STEP 2: Set default markup values for existing tiers
-- ============================================================

-- VIP Founder: 0% markup (cost price for admins/founders)
UPDATE subscription_tiers
SET llm_markup_percentage = 0.00
WHERE tier_code = 'vip_founder';

-- BYOK: 10% markup (minimal markup for bring-your-own-key users)
UPDATE subscription_tiers
SET llm_markup_percentage = 10.00
WHERE tier_code = 'byok';

-- Managed: 25% markup (standard markup for platform-managed keys)
UPDATE subscription_tiers
SET llm_markup_percentage = 25.00
WHERE tier_code = 'managed';

-- LoopNet tiers: 0% markup (business application tiers)
UPDATE subscription_tiers
SET llm_markup_percentage = 0.00
WHERE tier_code LIKE 'loopnet_%';

-- ============================================================
-- STEP 3: Verification
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE 'LLM Markup Percentage Migration Complete';
    RAISE NOTICE 'Updated tiers:';
END $$;

SELECT
    tier_code,
    tier_name,
    llm_markup_percentage,
    CASE
        WHEN llm_markup_percentage = 0.00 THEN 'Cost price (no markup)'
        ELSE llm_markup_percentage || '% markup'
    END as markup_description
FROM subscription_tiers
ORDER BY sort_order;

COMMIT;

-- ============================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================
-- To rollback this migration:
--
-- BEGIN;
-- ALTER TABLE subscription_tiers DROP COLUMN IF EXISTS llm_markup_percentage;
-- COMMIT;

-- ============================================================
-- DEPLOYMENT INSTRUCTIONS
-- ============================================================
--
-- 1. Apply this migration to the database:
--    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/add_llm_markup_percentage.sql
--
-- 2. Verify the column was added:
--    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d subscription_tiers"
--
-- 3. Verify markup values:
--    docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT tier_code, llm_markup_percentage FROM subscription_tiers;"
--
-- 4. Restart Ops-Center to load new pricing:
--    docker restart ops-center-direct
--
-- ============================================================
