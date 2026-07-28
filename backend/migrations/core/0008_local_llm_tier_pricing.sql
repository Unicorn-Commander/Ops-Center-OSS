-- core parity 0008 — per-tier local-LLM pricing (3 modes) + per-org monthly token counter
-- Adds the columns that drive the local-pricing feature and the durable counter
-- of record for monthly per-org local token usage. ALL additive: new columns are
-- nullable/defaulted and the new table is CREATE IF NOT EXISTS, so existing rows
-- are untouched and every tier keeps today's behavior (free_unlimited, no quota,
-- $0 local) until an operator explicitly changes a tier's mode AND the runtime
-- flag LOCAL_PRICING_ENABLED is turned on. See backend/local_pricing.py.
--
-- local_pricing_mode:
--   'free_unlimited'      -> local is free, no cap (today's behavior; default)
--   'free_quota_overflow' -> local free up to local_monthly_token_quota tokens,
--                            then route to local_overflow_model (billed as cloud);
--                            if no overflow model is set it degrades to free (never denies)
--   'metered'             -> local priced at local_token_rate_per_1k (counts against wallet)
ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS local_pricing_mode VARCHAR(20) DEFAULT 'free_unlimited';
ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS local_monthly_token_quota BIGINT;          -- NULL = unlimited
ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS local_overflow_model VARCHAR(255);          -- paid model to swap to on overflow
ALTER TABLE subscription_tiers ADD COLUMN IF NOT EXISTS local_token_rate_per_1k DECIMAL(12,8) DEFAULT 0.0;  -- 'metered' mode rate

-- Per-org, per-month local token counter (durable system of record; Redis is a
-- cache in front of this). Org-scoped to match the credit wallet's org scope.
CREATE TABLE IF NOT EXISTS org_local_token_usage (
    org_id        VARCHAR(255) NOT NULL,
    billing_month CHAR(7)      NOT NULL,        -- 'YYYY-MM'
    tokens_used   BIGINT       NOT NULL DEFAULT 0,
    updated_at    TIMESTAMP    DEFAULT now(),
    PRIMARY KEY (org_id, billing_month)
);
