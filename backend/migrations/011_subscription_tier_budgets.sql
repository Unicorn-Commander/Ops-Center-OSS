-- Billing-on-signup: per-plan monthly inference budget (USD) applied to the
-- org's LiteLLM gateway key (max_budget) when a plan activates or changes.
-- NULL = unlimited (e.g. vip_founder). Admin-editable via the tiers CRUD.
-- Idempotent: safe to re-run.

ALTER TABLE subscription_tiers
    ADD COLUMN IF NOT EXISTS max_monthly_llm_budget NUMERIC(10,2);

COMMENT ON COLUMN subscription_tiers.max_monthly_llm_budget IS
    'Monthly inference budget (USD) set as max_budget on the org gateway key at plan activation. NULL = unlimited.';
