-- ============================================================
-- VIP FOUNDER TIER MIGRATION
-- ============================================================
-- Creates VIP/Founder subscription tier with $0 monthly fee
-- Associates 4 apps: Center Deep Pro, Open-WebUI, Bolt.diy, Presenton
-- Migration Date: 2025-11-12
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: Insert VIP Founder Tier
-- ============================================================
INSERT INTO subscription_tiers (
    tier_code,
    tier_name,
    description,
    price_monthly,
    price_yearly,
    is_active,
    is_invite_only,
    sort_order,
    api_calls_limit,
    team_seats,
    byok_enabled,
    priority_support,
    lago_plan_code,
    stripe_price_monthly,
    stripe_price_yearly,
    created_by
) VALUES (
    'vip_founder',                                -- tier_code
    'VIP Founder',                                -- tier_name
    'Lifetime access for founders, admins, staff, and partners. Includes 4 premium apps with BYOK or pay-per-use via platform credits. No monthly subscription fee.',  -- description
    0.00,                                         -- price_monthly (NO SUBSCRIPTION FEE)
    0.00,                                         -- price_yearly (NO SUBSCRIPTION FEE)
    TRUE,                                         -- is_active
    TRUE,                                         -- is_invite_only (VIP access only)
    0,                                            -- sort_order (top tier)
    -1,                                           -- api_calls_limit (-1 = unlimited, usage billed via credits)
    5,                                            -- team_seats
    TRUE,                                         -- byok_enabled (Bring Your Own Key supported)
    TRUE,                                         -- priority_support
    'vip_founder',                                -- lago_plan_code
    NULL,                                         -- stripe_price_monthly (not applicable)
    NULL,                                         -- stripe_price_yearly (not applicable)
    'system'                                      -- created_by
)
ON CONFLICT (tier_code) DO UPDATE SET
    tier_name = EXCLUDED.tier_name,
    description = EXCLUDED.description,
    price_monthly = EXCLUDED.price_monthly,
    price_yearly = EXCLUDED.price_yearly,
    is_active = EXCLUDED.is_active,
    is_invite_only = EXCLUDED.is_invite_only,
    sort_order = EXCLUDED.sort_order,
    api_calls_limit = EXCLUDED.api_calls_limit,
    team_seats = EXCLUDED.team_seats,
    byok_enabled = EXCLUDED.byok_enabled,
    priority_support = EXCLUDED.priority_support,
    updated_by = 'system',
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================
-- STEP 2: Associate Apps with VIP Founder Tier
-- ============================================================

-- Get the tier_id for VIP Founder
DO $$
DECLARE
    v_tier_id INTEGER;
BEGIN
    -- Get VIP Founder tier ID
    SELECT id INTO v_tier_id FROM subscription_tiers WHERE tier_code = 'vip_founder';

    IF v_tier_id IS NULL THEN
        RAISE EXCEPTION 'VIP Founder tier not found';
    END IF;

    -- App 1: Center Deep Pro
    INSERT INTO tier_apps (tier_id, app_key, app_value, enabled)
    VALUES (v_tier_id, 'center_deep_pro', 'https://centerdeep.online', TRUE)
    ON CONFLICT (tier_id, app_key) DO UPDATE SET
        app_value = EXCLUDED.app_value,
        enabled = EXCLUDED.enabled,
        updated_at = CURRENT_TIMESTAMP;

    -- App 2: Open-WebUI
    INSERT INTO tier_apps (tier_id, app_key, app_value, enabled)
    VALUES (v_tier_id, 'open_webui', 'http://localhost:8080', TRUE)
    ON CONFLICT (tier_id, app_key) DO UPDATE SET
        app_value = EXCLUDED.app_value,
        enabled = EXCLUDED.enabled,
        updated_at = CURRENT_TIMESTAMP;

    -- App 3: Bolt.diy (UC Fork)
    INSERT INTO tier_apps (tier_id, app_key, app_value, enabled)
    VALUES (v_tier_id, 'bolt_diy', 'https://bolt.unicorncommander.ai', TRUE)
    ON CONFLICT (tier_id, app_key) DO UPDATE SET
        app_value = EXCLUDED.app_value,
        enabled = EXCLUDED.enabled,
        updated_at = CURRENT_TIMESTAMP;

    -- App 4: Presenton (UC Fork)
    INSERT INTO tier_apps (tier_id, app_key, app_value, enabled)
    VALUES (v_tier_id, 'presenton', 'https://presentations.unicorncommander.ai', TRUE)
    ON CONFLICT (tier_id, app_key) DO UPDATE SET
        app_value = EXCLUDED.app_value,
        enabled = EXCLUDED.enabled,
        updated_at = CURRENT_TIMESTAMP;

    RAISE NOTICE 'Successfully associated 4 apps with VIP Founder tier (ID: %)', v_tier_id;
END $$;

-- ============================================================
-- STEP 3: Verification Queries
-- ============================================================

-- Verify tier was created
SELECT
    id,
    tier_code,
    tier_name,
    price_monthly,
    price_yearly,
    api_calls_limit,
    team_seats,
    byok_enabled,
    is_active,
    is_invite_only,
    sort_order
FROM subscription_tiers
WHERE tier_code = 'vip_founder';

-- Verify apps were associated
SELECT
    ta.id,
    st.tier_code,
    st.tier_name,
    ta.app_key,
    ta.app_value,
    ta.enabled
FROM tier_apps ta
JOIN subscription_tiers st ON ta.tier_id = st.id
WHERE st.tier_code = 'vip_founder'
ORDER BY ta.app_key;

-- Count total apps for VIP Founder
SELECT
    st.tier_name,
    COUNT(ta.id) as app_count
FROM subscription_tiers st
LEFT JOIN tier_apps ta ON st.id = ta.tier_id AND ta.enabled = TRUE
WHERE st.tier_code = 'vip_founder'
GROUP BY st.tier_name;

COMMIT;

-- ============================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================
-- To rollback this migration:
--
-- BEGIN;
-- DELETE FROM tier_apps WHERE tier_id = (SELECT id FROM subscription_tiers WHERE tier_code = 'vip_founder');
-- DELETE FROM subscription_tiers WHERE tier_code = 'vip_founder';
-- COMMIT;

-- ============================================================
-- DEPLOYMENT INSTRUCTIONS
-- ============================================================
--
-- 1. Apply this migration to the database:
--    docker exec uchub-postgres psql -U unicorn -d unicorn_db -f /path/to/add_vip_founder_tier.sql
--
-- 2. Verify the tier was created:
--    docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "SELECT * FROM subscription_tiers WHERE tier_code = 'vip_founder'"
--
-- 3. Verify apps were associated:
--    docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "SELECT ta.*, st.tier_name FROM tier_apps ta JOIN subscription_tiers st ON ta.tier_id = st.id WHERE st.tier_code = 'vip_founder'"
--
-- 4. Restart Ops-Center backend to load new tier:
--    docker restart ops-center-direct
--
-- ============================================================
