-- Billing Events Schema
-- Cross-property billing events for unified metering and Lago integration
-- Created: 2026-04-09

CREATE TABLE IF NOT EXISTS billing_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,  -- compute_used, external_api_call, storage_billed, agent_invocation, app_subscription
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    origin_property TEXT NOT NULL,  -- which property initiated (magicunicorn.dev, centerdeep, gfl, commander)
    origin_user_id UUID,
    origin_org_id UUID,
    executed_on_property TEXT,  -- where the work ran (may differ from origin)
    executed_on_node_id TEXT,
    service_type TEXT,  -- llm_inference, image_gen, music_gen, embedding, agent_run, search, etc.
    model TEXT,
    provider TEXT,  -- openrouter, anthropic, local, etc.
    duration_ms INTEGER,
    tokens_in INTEGER,
    tokens_out INTEGER,
    gpu_seconds NUMERIC(12, 4),
    cost_internal_usd NUMERIC(12, 6),  -- what it actually cost us
    cost_provider_usd NUMERIC(12, 6),  -- what we paid a third party
    cost_billed_usd NUMERIC(12, 6),    -- what we charge the end user
    markup_percent NUMERIC(5, 2),
    payload JSONB DEFAULT '{}',
    lago_event_id TEXT,
    lago_status TEXT DEFAULT 'pending',  -- pending, sent, failed, skipped
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_billing_events_org ON billing_events(origin_org_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_billing_events_property ON billing_events(origin_property, timestamp);
CREATE INDEX IF NOT EXISTS idx_billing_events_type ON billing_events(event_type, timestamp);
CREATE INDEX IF NOT EXISTS idx_billing_events_lago ON billing_events(lago_status) WHERE lago_status != 'sent';
CREATE INDEX IF NOT EXISTS idx_billing_events_executed ON billing_events(executed_on_property, timestamp);
