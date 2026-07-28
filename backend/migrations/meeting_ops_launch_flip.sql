-- Meeting-Ops standalone launch flip (2026-06-25).
-- Pairs with pricing_packages_api.py (public picker now shows ['free','app'] only).
-- Idempotent / reversible.
--
--   * $15 'app' tier  -> "Meeting-Ops" standalone (Contact-Ops dropped from the bundle).
--   * Free tier       -> granted meeting_ops_access for ON-DEVICE mode (live transcript +
--                        summary on the user's device). The end-of-meeting server pass is
--                        gated by Meeting-Ops on the active workspace's paid plan, so this
--                        grant does NOT hand Free users the paid server processing.
--   * Suite tiers ($49 byok / $65 managed) stay fully active for any existing subscribers;
--     they're simply not listed in the public picker until the suite launches.

BEGIN;

-- Rebrand the $15 entry to Meeting-Ops standalone.
UPDATE subscription_tiers
   SET tier_name   = 'Meeting-Ops',
       description = 'AI meeting intelligence — record, transcribe, summarize, and track action items. Live transcript + summary run on your device; server-side diarization + polished output included.',
       updated_by  = 'system',
       updated_at  = NOW()
 WHERE tier_code = 'app';

-- Drop Contact-Ops from the $15 tier (standalone Meeting-Ops only). Reversible (enabled flag).
UPDATE tier_features
   SET enabled = FALSE
 WHERE tier_id = (SELECT id FROM subscription_tiers WHERE tier_code = 'app')
   AND feature_key = 'contact_ops_access';

-- Free tier sees Meeting-Ops (on-device mode). Server pass remains gated on a paid plan.
INSERT INTO tier_features (tier_id, feature_key, feature_value, enabled)
SELECT id, 'meeting_ops_access', 'true', TRUE
FROM subscription_tiers
WHERE tier_code = 'free'
ON CONFLICT (tier_id, feature_key) DO UPDATE SET enabled = TRUE;

COMMIT;
