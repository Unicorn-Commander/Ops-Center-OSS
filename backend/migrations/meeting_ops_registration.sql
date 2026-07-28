-- Meeting-Ops - App Registration in Ops-Center
-- Date: 2026-05-27
-- Purpose: Register Meeting-Ops as an add-on in the dashboard app catalog
--          and grant access via tier_features. Additive only; idempotent.
-- App: AI meeting recording, transcription, diarization, and summaries (browser-first/private)
-- Live at: https://meetingops.magicunicorn.dev

BEGIN;

-- 1. Register Meeting-Ops in the add_ons catalog (the dashboard app-card source)
INSERT INTO add_ons (
    name, slug, description, long_description,
    category, feature_key, launch_url, icon_url,
    base_price, billing_type, is_active, is_featured, is_public,
    access_type, min_org_role, sort_order,
    features
) VALUES (
    'Meeting-Ops',
    'meeting-ops',
    'AI meeting recording, transcription, diarization, and summaries — browser-first/private.',
    'Browser-first meeting intelligence: live recording, automatic transcription, speaker diarization, and AI-generated summaries with action items. On-device processing keeps sensitive conversations private.',
    'ai-tools',
    'meeting_ops_access',
    'https://meetingops.magicunicorn.dev',
    '/logos/magic_unicorn_logo.png',
    0.00,
    'one_time',
    TRUE,
    FALSE,
    TRUE,
    'purchase',
    'member',
    26,
    '{"recording": "In-browser meeting recording", "transcription": "Automatic speech-to-text transcription", "diarization": "Speaker diarization (who said what)", "summaries": "AI-generated meeting summaries and action items", "privacy": "Browser-first, on-device processing for privacy"}'::jsonb
)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    long_description = EXCLUDED.long_description,
    category = EXCLUDED.category,
    feature_key = EXCLUDED.feature_key,
    launch_url = EXCLUDED.launch_url,
    icon_url = EXCLUDED.icon_url,
    features = EXCLUDED.features,
    is_active = TRUE;

-- 2. Grant meeting_ops_access to the standard tier set
--    (vip_founder, byok, managed, founder_friend, trial) so it has parity with
--    sibling ecosystem apps (Crisis Ops / Majik's Studio / Brigade).
--    Aaron (admin) sees it regardless of grants.
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT st.id, 'meeting_ops_access', 'true', TRUE
FROM subscription_tiers st
WHERE st.tier_code IN ('vip_founder', 'byok', 'managed', 'founder_friend', 'trial')
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

COMMIT;

-- Verification queries (run after migration)
-- SELECT * FROM add_ons WHERE slug = 'meeting-ops';
-- SELECT tf.*, st.tier_code FROM tier_features tf JOIN subscription_tiers st ON tf.tier_id = st.id WHERE tf.feature_key = 'meeting_ops_access';
-- curl -s https://magicunicorn.dev/api/v1/my-apps/authorized | python3 -c 'import sys,json; print([a["slug"] for a in json.load(sys.stdin)])'
