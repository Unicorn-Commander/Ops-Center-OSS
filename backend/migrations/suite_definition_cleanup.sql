-- Suite definition cleanup (2026-06-25). The Suite = the *-Ops apps only.
-- Both suite tiers have 0 subscribers, so this is non-disruptive. Reversible (enabled flags /
-- is_active). The Suite stays HIDDEN from the public picker until the suite launches; this just
-- gets its definition right.
--
--   * Drop Suite-BYOK ($49) for now — single Suite tier = Managed ($65).
--   * Suite (managed) keeps the 8 *-Ops apps + platform capabilities (LLM/STT/TTS/search/billing/
--     support/account). It drops the non-*-Ops product apps (OpenWebUI, Bolt, Presenton, Majik's
--     Studio, Lavora, Magic Outreach, Retirement Leads) and admin-only Brigade.
--   * Note: Listmonk/Postiz are standalone marketplace add-ons, never in the suite (no change here).

BEGIN;

-- Drop Suite-BYOK for now (0 active orgs; reversible).
UPDATE subscription_tiers
   SET is_active = FALSE, updated_by = 'system', updated_at = NOW()
 WHERE tier_code = 'byok';

-- Strip non-*-Ops apps from the Suite (managed). The *-Ops grants + platform features stay.
UPDATE tier_features
   SET enabled = FALSE
 WHERE tier_id = (SELECT id FROM subscription_tiers WHERE tier_code = 'managed')
   AND feature_key IN (
       'openwebui_access',
       'bolt_access',
       'presenton_access',
       'majiks_studio_access',
       'lavora_leads',
       'magic_outreach',
       'retirement_leads',
       'brigade_access'
   );

COMMIT;
