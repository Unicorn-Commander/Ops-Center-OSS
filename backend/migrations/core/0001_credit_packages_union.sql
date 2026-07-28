-- core parity 0001 — credit_packages additive column union (Phase B)
-- Converge the credit-packs catalog so the admin GUI + buyer endpoint find the
-- same columns on both nodes. commander shipped is_featured/badge_text/
-- available_to_tiers (dynamic_pricing_api writes them); bigboy lacked them.
-- name/price_cents are commander legacy duplicates (marked optional in the
-- contract) carried for completeness. This file does NOT touch the id PK type —
-- the uuid<->int change is dangerous and lives in core/pending_signoff/.
-- Idempotent: ADD COLUMN IF NOT EXISTS only; runs on both nodes.
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS is_featured BOOLEAN DEFAULT false;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS badge_text VARCHAR(64);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS available_to_tiers TEXT;
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE credit_packages ADD COLUMN IF NOT EXISTS price_cents INTEGER;
