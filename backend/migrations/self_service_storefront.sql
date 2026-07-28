-- P-00107: storefront catalog and add-on entitlement persistence.
BEGIN;

ALTER TABLE add_on_purchases
    ADD COLUMN IF NOT EXISTS org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    ADD COLUMN IF NOT EXISTS stripe_session_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255),
    ADD COLUMN IF NOT EXISTS feature_key VARCHAR(255),
    ADD COLUMN IF NOT EXISTS activated_at TIMESTAMP WITH TIME ZONE,
    ADD COLUMN IF NOT EXISTS revoked_at TIMESTAMP WITH TIME ZONE;

CREATE UNIQUE INDEX IF NOT EXISTS uq_add_on_purchase_session_addon
    ON add_on_purchases(stripe_session_id, add_on_id)
    WHERE stripe_session_id IS NOT NULL;

INSERT INTO add_ons (
    name, slug, description, long_description, category, feature_key,
    launch_url, icon_url, base_price, billing_type, is_active, is_featured,
    is_public, access_type, min_org_role, sort_order, features
) VALUES (
    'Contact-Ops',
    'contact-ops',
    'Relationship and contact operations workspace',
    'Contact-Ops organizes contacts, relationship context, follow-ups, and communication workflows.',
    'productivity',
    'contact_ops_access',
    'https://contacts.magicunicorn.dev',
    '/logos/contact-ops.png',
    0.00,
    'monthly',
    TRUE,
    TRUE,
    TRUE,
    'tier_included',
    'member',
    21,
    '{"contacts": "Contact and relationship management", "follow_up": "Follow-up workflows", "sso": "Keycloak SSO"}'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    long_description = EXCLUDED.long_description,
    feature_key = EXCLUDED.feature_key,
    launch_url = EXCLUDED.launch_url,
    min_org_role = EXCLUDED.min_org_role,
    is_active = TRUE,
    is_public = TRUE;

INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT st.id, feature_key, 'true', TRUE
FROM subscription_tiers st
CROSS JOIN (VALUES ('meeting_ops_access'), ('contact_ops_access')) AS features(feature_key)
WHERE st.tier_code = 'app'
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

COMMIT;
