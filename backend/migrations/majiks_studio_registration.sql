-- Majiks Music Studio - App Registration in Ops-Center
-- Date: 2026-02-16
-- Purpose: Register Majiks Studio as an add-on in the Apps Marketplace
--          and grant access to all active subscription tiers

BEGIN;

-- 1. Register Majiks Music Studio in the add_ons catalog
INSERT INTO add_ons (
    name, slug, description, long_description,
    category, feature_key, launch_url, icon_url,
    base_price, billing_type, is_active, is_featured, is_public,
    access_type, min_org_role, sort_order, features
) VALUES (
    'Majik''s Studio',
    'majiks-studio',
    'AI-powered music generation studio with ACE-Step',
    'Professional music production powered by AI. Generate full songs with customizable style, genre, tempo, key, and lyrics. Create multiple variants, preview with waveforms, rate and save to your library. GPU-accelerated with Tesla P40.',
    'ai-tools',
    'majiks_studio_access',
    'https://studio.magicunicorn.dev',
    '/logos/majiks-studio-logo.png',
    0.00, 'monthly', TRUE, TRUE, TRUE,
    'tier_included', 'member', 12,
    '{"music_generation": "AI-powered song creation", "lyrics_support": "Write or generate lyrics", "variant_generation": "Create multiple variations", "library_management": "Organize your music", "gpu_acceleration": "Tesla P40 accelerated", "ai_enhance": "AI-powered caption enhancement", "batch_operations": "Bulk library management", "chat_assistant": "AI music production assistant"}'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    long_description = EXCLUDED.long_description,
    launch_url = EXCLUDED.launch_url,
    features = EXCLUDED.features,
    is_active = TRUE;

-- 2. Grant access to ALL active tiers
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT st.id, 'majiks_studio_access', 'true', TRUE
FROM subscription_tiers st
WHERE st.is_active = TRUE
  AND st.tier_code IN ('vip_founder', 'founder_friend', 'byok', 'managed', 'trial', 'professional')
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

COMMIT;

-- Verification queries (run after migration)
-- SELECT * FROM add_ons WHERE slug = 'majiks-studio';
-- SELECT tf.*, st.tier_code FROM tier_features tf JOIN subscription_tiers st ON tf.tier_id = st.id WHERE tf.feature_key = 'majiks_studio_access';
