-- Crisis Management Ops - App Registration in Ops-Center
-- Date: 2026-02-08
-- Purpose: Register Crisis Ops as an add-on, create Rocky's personal org,
--          grant access via tier_features and org_features

BEGIN;

-- 1. Register Crisis Management Ops in the add_ons catalog
INSERT INTO add_ons (
    name, slug, description, long_description,
    category, feature_key, launch_url, icon_url,
    base_price, is_active, is_featured, sort_order,
    features
) VALUES (
    'Crisis Management Ops',
    'crisis-ops',
    'Case management platform for investigations and crisis response',
    'Full-featured investigation management with knowledge graphs, timeline analysis, evidence management, strategy domains, and multi-role access control. Designed for investigators, clients, and legal teams.',
    'services',
    'crisis_ops_access',
    'https://crisis.your-domain.com',
    '/logos/crisis-ops-logo.svg',
    0.00,
    TRUE,
    FALSE,
    25,
    '{"case_management": "Full case lifecycle management", "knowledge_graph": "Interactive entity relationship visualization", "timeline": "Chronological event analysis", "evidence_browser": "286+ evidence file management", "strategy_domains": "Multi-domain strategy tracking", "documents": "Document management with markdown support", "rbac": "Role-based access control (admin, investigator, client, viewer)", "sso": "Keycloak SSO integration"}'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    launch_url = EXCLUDED.launch_url,
    features = EXCLUDED.features,
    is_active = TRUE;

-- 2. Grant crisis_ops_access to vip_founder tier (Aaron sees it automatically)
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT st.id, 'crisis_ops_access', 'true', TRUE
FROM subscription_tiers st
WHERE st.tier_code = 'vip_founder'
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

-- 3. Create Rocky Burke's personal organization
INSERT INTO organizations (
    id, name, display_name, plan_tier, max_seats, status
) VALUES (
    'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',
    'rocky-burke-personal',
    'Rocky Burke',
    'founder_friend',
    1,
    'active'
)
ON CONFLICT (name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    status = 'active';

-- 4. Link Rocky's org to the founder_friend tier (if tier exists)
-- If founder_friend tier doesn't exist, create it
INSERT INTO subscription_tiers (
    tier_code, tier_name, description,
    price_monthly, price_yearly, is_active, is_invite_only,
    sort_order, api_calls_limit, team_seats,
    byok_enabled, priority_support, created_by
) VALUES (
    'founder_friend',
    'Founder Friend',
    'Free tier for founding friends and early supporters',
    0.00, 0.00, TRUE, TRUE,
    2, 1000, 1,
    FALSE, FALSE, 'system'
)
ON CONFLICT (tier_code) DO NOTHING;

-- Update Rocky's org plan_tier to founder_friend
UPDATE organizations
SET plan_tier = 'founder_friend'
WHERE name = 'rocky-burke-personal';

-- 5. Grant crisis_ops_access to Rocky's org via org_features
INSERT INTO org_features (org_id, feature_key, enabled, granted_by, notes)
VALUES (
    'a1b2c3d4-e5f6-4a7b-8c9d-0e1f2a3b4c5d',
    'crisis_ops_access',
    TRUE,
    'admin@example.com',
    'Founding client - Rocky Burke investigation case (FRB911)'
)
ON CONFLICT (org_id, feature_key) DO UPDATE SET enabled = TRUE;

-- 6. Also grant crisis_ops_access to founder_friend tier itself
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT st.id, 'crisis_ops_access', 'true', TRUE
FROM subscription_tiers st
WHERE st.tier_code = 'founder_friend'
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

COMMIT;

-- Verification queries (run after migration)
-- SELECT * FROM add_ons WHERE slug = 'crisis-ops';
-- SELECT * FROM organizations WHERE name = 'rocky-burke-personal';
-- SELECT tf.*, st.tier_code FROM tier_features tf JOIN subscription_tiers st ON tf.tier_id = st.id WHERE tf.feature_key = 'crisis_ops_access';
-- SELECT * FROM org_features WHERE feature_key = 'crisis_ops_access';
