-- Locked self-service price sheet (decision 2026-06-24, project P-00107)
-- Free $0 / App (Meeting+Contact) $15 / Suite-BYOK $49 / Suite-Managed $65 + à-la-carte add-ons.
--
-- Idempotent: re-runnable. INSERTs use ON CONFLICT DO NOTHING; UPDATEs are keyed by tier_code.
-- NOTE: stripe_price_monthly / stripe_price_yearly are intentionally left NULL here — populate
--       them AFTER creating the Stripe products (setup_stripe_products.py) so display price and
--       the actual charged Stripe price stay in sync. Until then these tiers show the price but
--       checkout for them should remain disabled in the UI.

-- ── Free: the floor. On-device / bring-your-own AI + local storage, no platform LLM spend. ──
INSERT INTO subscription_tiers
  (tier_code, tier_name, description, price_monthly, price_yearly, is_active, is_invite_only,
   sort_order, api_calls_limit, team_seats, byok_enabled, priority_support, lago_plan_code, created_by)
VALUES
  ('free', 'Free',
   'On-device / bring-your-own AI, local storage, 1 seat. No platform LLM spend.',
   0.00, 0.00, TRUE, FALSE, 0, 0, 1, FALSE, FALSE, 'free', 'system')
ON CONFLICT (tier_code) DO NOTHING;

-- ── App: single-app entry — Meeting-Ops + Contact-Ops, MCP included, starter credits. ──
INSERT INTO subscription_tiers
  (tier_code, tier_name, description, price_monthly, price_yearly, is_active, is_invite_only,
   sort_order, api_calls_limit, team_seats, byok_enabled, priority_support, lago_plan_code, created_by)
VALUES
  ('app', 'App (Meeting + Contact)',
   'Meeting-Ops + Contact-Ops, MCP included, ~$4/mo platform credits, 1 seat.',
   15.00, 150.00, TRUE, FALSE, 2, -1, 1, FALSE, FALSE, 'app', 'system')
ON CONFLICT (tier_code) DO NOTHING;

-- ── Suite BYOK: all apps + MCP, bring your own model keys. Price 30 -> 49. ──
UPDATE subscription_tiers
   SET price_monthly = 49.00,
       price_yearly  = 490.00,
       tier_name     = 'Suite - BYOK',
       sort_order    = 3,
       byok_enabled  = TRUE,
       updated_by    = 'system',
       updated_at    = NOW()
 WHERE tier_code = 'byok';

-- ── Suite Managed: all apps + MCP + UC-hosted inference (~$10-12/mo credits). Price 50 -> 65, 3 seats. ──
UPDATE subscription_tiers
   SET price_monthly    = 65.00,
       price_yearly     = 650.00,
       tier_name        = 'Suite - Managed',
       team_seats       = 3,
       sort_order       = 4,
       priority_support = TRUE,
       updated_by       = 'system',
       updated_at       = NOW()
 WHERE tier_code = 'managed';

-- ── Stripe LIVE monthly price IDs (created 2026-06-24 on acct_1QwxFKDzk9HqAZnH). ──
-- Price IDs are not secret (used client-side in Stripe Checkout). Annual prices not yet
-- created → yearly checkout stays disabled in the UI. Free tier has no Stripe price.
UPDATE subscription_tiers SET stripe_price_monthly = 'price_1TllOZDzk9HqAZnHU5ijAlmP' WHERE tier_code = 'app';
UPDATE subscription_tiers SET stripe_price_monthly = 'price_1TllOaDzk9HqAZnHCkH7E20k' WHERE tier_code = 'byok';
UPDATE subscription_tiers SET stripe_price_monthly = 'price_1TllObDzk9HqAZnHw8mrzhou' WHERE tier_code = 'managed';
