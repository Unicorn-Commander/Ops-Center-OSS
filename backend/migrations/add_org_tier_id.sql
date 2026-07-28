-- ============================================================================
-- Migration: Add tier_id to organizations (Org-Centric Multi-Tenancy)
-- Version: 002
-- Created: 2026-01-11
-- Description: Link organizations directly to subscription_tiers table
--              This enables org-centric access control instead of user-centric
-- ============================================================================

-- ==================== Step 1: Add tier_id column ====================
-- Add foreign key reference to subscription_tiers
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS tier_id INTEGER REFERENCES subscription_tiers(id);

-- Add slug column if it doesn't exist (for URL-friendly org identifiers)
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS slug VARCHAR(100);

-- ==================== Step 2: Create indexes ====================
CREATE INDEX IF NOT EXISTS idx_organizations_tier_id ON organizations(tier_id);
CREATE INDEX IF NOT EXISTS idx_organizations_slug ON organizations(slug);

-- ==================== Step 3: Backfill tier_id from plan_tier ====================
-- Map existing plan_tier strings to subscription_tiers.id

-- First, map exact matches
UPDATE organizations o
SET tier_id = st.id
FROM subscription_tiers st
WHERE o.tier_id IS NULL
  AND o.plan_tier = st.tier_code;

-- Map common variations
UPDATE organizations o
SET tier_id = st.id
FROM subscription_tiers st
WHERE o.tier_id IS NULL
  AND (
    -- founders_friend -> vip_founder
    (o.plan_tier = 'founders_friend' AND st.tier_code = 'vip_founder')
    OR (o.plan_tier = 'founder_friend' AND st.tier_code = 'vip_founder')
    -- professional/platform -> managed
    OR (o.plan_tier = 'professional' AND st.tier_code = 'managed')
    OR (o.plan_tier = 'platform' AND st.tier_code = 'managed')
    -- starter variations
    OR (o.plan_tier = 'starter' AND st.tier_code = 'managed')
    -- enterprise -> managed (for now)
    OR (o.plan_tier = 'enterprise' AND st.tier_code = 'managed')
  );

-- ==================== Step 4: Set default tier for remaining ====================
-- Any orgs still without tier_id get 'managed' tier
UPDATE organizations
SET tier_id = (SELECT id FROM subscription_tiers WHERE tier_code = 'managed' LIMIT 1)
WHERE tier_id IS NULL;

-- ==================== Step 5: Generate slugs ====================
-- Create URL-friendly slugs from org names
UPDATE organizations
SET slug = LOWER(REGEXP_REPLACE(REGEXP_REPLACE(name, '[^a-zA-Z0-9\s-]', '', 'g'), '\s+', '-', 'g'))
WHERE slug IS NULL OR slug = '';

-- Handle duplicate slugs by appending numbers
DO $$
DECLARE
    dup_slug VARCHAR;
    counter INT;
    org_rec RECORD;
BEGIN
    FOR dup_slug IN
        SELECT slug FROM organizations GROUP BY slug HAVING COUNT(*) > 1
    LOOP
        counter := 1;
        FOR org_rec IN
            SELECT id FROM organizations WHERE slug = dup_slug ORDER BY created_at OFFSET 1
        LOOP
            UPDATE organizations SET slug = dup_slug || '-' || counter WHERE id = org_rec.id;
            counter := counter + 1;
        END LOOP;
    END LOOP;
END $$;

-- ==================== Step 6: Create org_app_access view ====================
-- Convenient view for querying what apps an org can access
CREATE OR REPLACE VIEW org_app_access AS
SELECT
    o.id as org_id,
    o.name as org_name,
    o.slug as org_slug,
    st.id as tier_id,
    st.tier_code,
    st.tier_name,
    tf.feature_key,
    ao.id as app_id,
    ao.name as app_name,
    ao.slug as app_slug,
    ao.launch_url,
    ao.icon_url,
    ao.description
FROM organizations o
JOIN subscription_tiers st ON o.tier_id = st.id
JOIN tier_features tf ON st.id = tf.tier_id AND tf.enabled = TRUE
JOIN add_ons ao ON tf.feature_key = ao.feature_key AND ao.is_active = TRUE
WHERE o.status = 'active';

-- ==================== Step 7: Create user_org_access view ====================
-- View for querying all orgs a user can access with their apps
CREATE OR REPLACE VIEW user_org_access AS
SELECT
    om.user_id,
    om.role as member_role,
    o.id as org_id,
    o.name as org_name,
    o.slug as org_slug,
    st.tier_code,
    st.tier_name,
    COALESCE(
        json_agg(
            json_build_object(
                'slug', ao.slug,
                'name', ao.name,
                'url', ao.launch_url,
                'icon', ao.icon_url
            )
        ) FILTER (WHERE ao.slug IS NOT NULL),
        '[]'::json
    ) as apps
FROM organization_members om
JOIN organizations o ON om.org_id = o.id
JOIN subscription_tiers st ON o.tier_id = st.id
LEFT JOIN tier_features tf ON st.id = tf.tier_id AND tf.enabled = TRUE
LEFT JOIN add_ons ao ON tf.feature_key = ao.feature_key AND ao.is_active = TRUE
WHERE o.status = 'active'
GROUP BY om.user_id, om.role, o.id, o.name, o.slug, st.tier_code, st.tier_name;

-- ==================== Step 8: Add helper function ====================
-- Function to get org's tier code
CREATE OR REPLACE FUNCTION get_org_tier_code(p_org_id UUID)
RETURNS VARCHAR AS $$
DECLARE
    v_tier_code VARCHAR;
BEGIN
    SELECT st.tier_code INTO v_tier_code
    FROM organizations o
    JOIN subscription_tiers st ON o.tier_id = st.id
    WHERE o.id = p_org_id;

    RETURN COALESCE(v_tier_code, 'managed');
END;
$$ LANGUAGE plpgsql;

-- Function to check if user has access to app via org
CREATE OR REPLACE FUNCTION user_has_app_access(p_user_id VARCHAR, p_org_id UUID, p_feature_key VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM organization_members om
        JOIN organizations o ON om.org_id = o.id
        JOIN subscription_tiers st ON o.tier_id = st.id
        JOIN tier_features tf ON st.id = tf.tier_id
        WHERE om.user_id = p_user_id
          AND o.id = p_org_id
          AND tf.feature_key = p_feature_key
          AND tf.enabled = TRUE
    );
END;
$$ LANGUAGE plpgsql;

-- ==================== Migration Complete ====================
DO $$
DECLARE
    org_count INTEGER;
    linked_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_count FROM organizations;
    SELECT COUNT(*) INTO linked_count FROM organizations WHERE tier_id IS NOT NULL;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'Org-Centric Multi-Tenancy Migration Complete';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total organizations: %', org_count;
    RAISE NOTICE 'Organizations linked to tiers: %', linked_count;
    RAISE NOTICE 'Views created: org_app_access, user_org_access';
    RAISE NOTICE 'Functions created: get_org_tier_code, user_has_app_access';
    RAISE NOTICE '========================================';
END $$;
