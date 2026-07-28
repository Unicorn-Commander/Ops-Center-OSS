-- core parity 0005 — user_credits wallet column union (Phase B)
-- The new credit_system.py path writes lifetime_credits/monthly_usage/
-- monthly_reset_at/last_updated; the older litellm_credit_system.py +
-- email_notification_api paths write credits_allocated/last_reset/updated_at/
-- email_notifications_enabled. Carry the full union so every shipped writer works
-- on both nodes. 17 rows on commander, 1 on bigboy. Does NOT touch user_id type —
-- the uuid->varchar change is dangerous (core/pending_signoff/).
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS lifetime_credits NUMERIC DEFAULT 0.00;
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS monthly_usage NUMERIC DEFAULT 0.00;
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS monthly_reset_at TIMESTAMPTZ;
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS last_updated TIMESTAMPTZ DEFAULT now();
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS credits_allocated NUMERIC DEFAULT 0;
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS last_reset TIMESTAMPTZ DEFAULT now();
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE user_credits ADD COLUMN IF NOT EXISTS email_notifications_enabled BOOLEAN DEFAULT true;
