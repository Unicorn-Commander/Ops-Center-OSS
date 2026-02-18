-- ============================================================================
-- Webhooks Management Schema
--
-- Purpose: Store webhook configurations and track delivery history
-- Author: Ops-Center AI
-- Created: January 31, 2026
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- WEBHOOKS TABLE
-- Stores webhook configurations
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhooks (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    secret_key VARCHAR(255) NOT NULL,
    events TEXT[] NOT NULL, -- array of event types
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_triggered_at TIMESTAMP,

    -- Additional metadata
    description TEXT,
    headers JSONB DEFAULT '{}',  -- Custom headers to include
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,

    -- Constraints
    CONSTRAINT webhooks_name_not_empty CHECK (name <> ''),
    CONSTRAINT webhooks_url_not_empty CHECK (url <> ''),
    CONSTRAINT webhooks_events_not_empty CHECK (array_length(events, 1) > 0),
    CONSTRAINT webhooks_retry_count_valid CHECK (retry_count >= 0 AND retry_count <= 10),
    CONSTRAINT webhooks_timeout_valid CHECK (timeout_seconds > 0 AND timeout_seconds <= 120)
);

-- Add comment
COMMENT ON TABLE webhooks IS 'Webhook configurations for event notifications';
COMMENT ON COLUMN webhooks.events IS 'Array of event types: user.created, user.deleted, subscription.created, subscription.cancelled, payment.received, payment.failed, service.started, service.stopped';
COMMENT ON COLUMN webhooks.secret_key IS 'HMAC-SHA256 signing key for payload verification';
COMMENT ON COLUMN webhooks.headers IS 'Custom HTTP headers to include in webhook requests (JSON object)';

-- ============================================================================
-- WEBHOOK DELIVERIES TABLE
-- Tracks all webhook delivery attempts and their outcomes
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_deliveries (
    id SERIAL PRIMARY KEY,
    webhook_id INTEGER REFERENCES webhooks(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    payload JSONB,
    response_status INTEGER,
    response_body TEXT,
    response_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Request details for debugging
    request_headers JSONB,
    attempt_number INTEGER DEFAULT 1,

    -- Constraints
    CONSTRAINT webhook_deliveries_event_type_not_empty CHECK (event_type <> ''),
    CONSTRAINT webhook_deliveries_attempt_valid CHECK (attempt_number > 0)
);

-- Add comment
COMMENT ON TABLE webhook_deliveries IS 'Webhook delivery history and audit log';
COMMENT ON COLUMN webhook_deliveries.response_time_ms IS 'Time taken for the webhook request in milliseconds';
COMMENT ON COLUMN webhook_deliveries.attempt_number IS 'Which retry attempt this was (1 = first attempt)';

-- ============================================================================
-- INDEXES
-- ============================================================================

-- Webhook lookups
CREATE INDEX IF NOT EXISTS idx_webhooks_is_active ON webhooks(is_active);
CREATE INDEX IF NOT EXISTS idx_webhooks_created_by ON webhooks(created_by);
CREATE INDEX IF NOT EXISTS idx_webhooks_events ON webhooks USING GIN(events);

-- Delivery history lookups
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_id ON webhook_deliveries(webhook_id);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_created_at ON webhook_deliveries(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_event_type ON webhook_deliveries(event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_success ON webhook_deliveries(success);
CREATE INDEX IF NOT EXISTS idx_webhook_deliveries_webhook_created ON webhook_deliveries(webhook_id, created_at DESC);

-- ============================================================================
-- TRIGGER FOR updated_at
-- ============================================================================

-- Create or replace the trigger function
CREATE OR REPLACE FUNCTION update_webhooks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists and recreate
DROP TRIGGER IF EXISTS trigger_webhooks_updated_at ON webhooks;
CREATE TRIGGER trigger_webhooks_updated_at
    BEFORE UPDATE ON webhooks
    FOR EACH ROW
    EXECUTE FUNCTION update_webhooks_updated_at();

-- ============================================================================
-- SUPPORTED EVENTS REFERENCE TABLE (optional, for documentation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS webhook_event_types (
    event_type VARCHAR(100) PRIMARY KEY,
    description TEXT,
    payload_schema JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert supported event types
INSERT INTO webhook_event_types (event_type, description, payload_schema) VALUES
    ('user.created', 'Triggered when a new user is created', '{"user_id": "string", "email": "string", "username": "string", "created_at": "timestamp"}'),
    ('user.deleted', 'Triggered when a user is deleted', '{"user_id": "string", "email": "string", "deleted_at": "timestamp"}'),
    ('subscription.created', 'Triggered when a new subscription is created', '{"subscription_id": "string", "user_id": "string", "tier": "string", "created_at": "timestamp"}'),
    ('subscription.cancelled', 'Triggered when a subscription is cancelled', '{"subscription_id": "string", "user_id": "string", "tier": "string", "cancelled_at": "timestamp", "reason": "string"}'),
    ('payment.received', 'Triggered when a payment is received', '{"payment_id": "string", "user_id": "string", "amount": "number", "currency": "string", "received_at": "timestamp"}'),
    ('payment.failed', 'Triggered when a payment fails', '{"payment_id": "string", "user_id": "string", "amount": "number", "currency": "string", "error": "string", "failed_at": "timestamp"}'),
    ('service.started', 'Triggered when a service is started', '{"service_name": "string", "started_at": "timestamp", "started_by": "string"}'),
    ('service.stopped', 'Triggered when a service is stopped', '{"service_name": "string", "stopped_at": "timestamp", "stopped_by": "string", "reason": "string"}')
ON CONFLICT (event_type) DO UPDATE SET
    description = EXCLUDED.description,
    payload_schema = EXCLUDED.payload_schema;

COMMENT ON TABLE webhook_event_types IS 'Reference table documenting supported webhook event types and their payload schemas';

-- ============================================================================
-- VIEWS FOR ANALYTICS
-- ============================================================================

-- View for webhook delivery statistics
CREATE OR REPLACE VIEW webhook_delivery_stats AS
SELECT
    w.id AS webhook_id,
    w.name AS webhook_name,
    w.url AS webhook_url,
    w.is_active,
    COUNT(wd.id) AS total_deliveries,
    COUNT(CASE WHEN wd.success = true THEN 1 END) AS successful_deliveries,
    COUNT(CASE WHEN wd.success = false THEN 1 END) AS failed_deliveries,
    ROUND(
        (COUNT(CASE WHEN wd.success = true THEN 1 END)::DECIMAL / NULLIF(COUNT(wd.id), 0)) * 100,
        2
    ) AS success_rate,
    AVG(wd.response_time_ms) AS avg_response_time_ms,
    MAX(wd.created_at) AS last_delivery_at
FROM webhooks w
LEFT JOIN webhook_deliveries wd ON w.id = wd.webhook_id
GROUP BY w.id, w.name, w.url, w.is_active;

COMMENT ON VIEW webhook_delivery_stats IS 'Aggregated statistics for each webhook';

-- View for recent delivery failures (last 24 hours)
CREATE OR REPLACE VIEW recent_webhook_failures AS
SELECT
    wd.id AS delivery_id,
    w.name AS webhook_name,
    w.url AS webhook_url,
    wd.event_type,
    wd.response_status,
    wd.error_message,
    wd.response_time_ms,
    wd.created_at
FROM webhook_deliveries wd
JOIN webhooks w ON w.id = wd.webhook_id
WHERE wd.success = false
  AND wd.created_at > (CURRENT_TIMESTAMP - INTERVAL '24 hours')
ORDER BY wd.created_at DESC;

COMMENT ON VIEW recent_webhook_failures IS 'Failed webhook deliveries from the last 24 hours';

-- ============================================================================
-- SAMPLE DATA (optional, for testing)
-- ============================================================================

-- Uncomment to insert sample webhooks for testing
-- INSERT INTO webhooks (name, url, secret_key, events, created_by, description) VALUES
--     ('Slack Notifications', 'https://hooks.slack.com/services/xxx/yyy/zzz', 'test-secret-1', ARRAY['user.created', 'user.deleted'], 'admin', 'Posts user events to Slack'),
--     ('Billing Webhook', 'https://billing.example.com/webhooks', 'test-secret-2', ARRAY['payment.received', 'payment.failed', 'subscription.created', 'subscription.cancelled'], 'admin', 'Syncs billing events to external system'),
--     ('Service Monitor', 'https://monitor.example.com/events', 'test-secret-3', ARRAY['service.started', 'service.stopped'], 'admin', 'Monitors service lifecycle events');

-- ============================================================================
-- GRANTS (adjust as needed for your setup)
-- ============================================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON webhooks TO unicorn;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON webhook_deliveries TO unicorn;
-- GRANT SELECT ON webhook_event_types TO unicorn;
-- GRANT SELECT ON webhook_delivery_stats TO unicorn;
-- GRANT SELECT ON recent_webhook_failures TO unicorn;
-- GRANT USAGE, SELECT ON SEQUENCE webhooks_id_seq TO unicorn;
-- GRANT USAGE, SELECT ON SEQUENCE webhook_deliveries_id_seq TO unicorn;

-- ============================================================================
-- END OF MIGRATION
-- ============================================================================
