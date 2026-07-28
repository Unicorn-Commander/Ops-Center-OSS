-- Alert Triggers Database Schema
-- Version: 1.0.0
-- Author: Backend Team Lead
-- Date: November 29, 2025
--
-- Purpose: Database tables for alert trigger system

-- Alert trigger history table
CREATE TABLE IF NOT EXISTS alert_trigger_history (
    id SERIAL PRIMARY KEY,
    trigger_id VARCHAR(100) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    context JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes separately
CREATE INDEX IF NOT EXISTS idx_trigger_history_trigger_id ON alert_trigger_history(trigger_id);
CREATE INDEX IF NOT EXISTS idx_trigger_history_created_at ON alert_trigger_history(created_at DESC);

-- Add comment
COMMENT ON TABLE alert_trigger_history IS 'Alert trigger execution history';

-- Alert trigger configuration table (optional, for persistence)
CREATE TABLE IF NOT EXISTS alert_trigger_config (
    trigger_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    condition_name VARCHAR(100) NOT NULL,
    recipients TEXT[] NOT NULL,
    cooldown_minutes INTEGER NOT NULL DEFAULT 60,
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    enabled BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Constraints
    CHECK (alert_type IN ('system_critical', 'billing', 'security', 'usage')),
    CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CHECK (cooldown_minutes >= 1 AND cooldown_minutes <= 1440),
    CHECK (array_length(recipients, 1) >= 1 AND array_length(recipients, 1) <= 10)
);

-- Add comment
COMMENT ON TABLE alert_trigger_config IS 'Alert trigger configuration (persisted)';

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_alert_trigger_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_alert_trigger_config_timestamp
    BEFORE UPDATE ON alert_trigger_config
    FOR EACH ROW
    EXECUTE FUNCTION update_alert_trigger_config_timestamp();

-- Add columns to existing tables for alert tracking

-- Add to billing_events (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'billing_events') THEN
        -- Add notified column
        ALTER TABLE billing_events ADD COLUMN IF NOT EXISTS notified BOOLEAN DEFAULT false;

        -- Add index
        CREATE INDEX IF NOT EXISTS idx_billing_events_notified
            ON billing_events(event_type, created_at)
            WHERE notified = false;
    END IF;
END $$;

-- Add to user_subscriptions (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_subscriptions') THEN
        -- Add notification tracking columns
        ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS renewal_notified BOOLEAN DEFAULT false;
        ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS quota_warning_sent BOOLEAN DEFAULT false;
        ALTER TABLE user_subscriptions ADD COLUMN IF NOT EXISTS quota_exceeded_sent BOOLEAN DEFAULT false;

        -- Add indexes
        CREATE INDEX IF NOT EXISTS idx_user_subscriptions_renewal
            ON user_subscriptions(end_date)
            WHERE renewal_notified = false;

        CREATE INDEX IF NOT EXISTS idx_user_subscriptions_quota
            ON user_subscriptions(api_calls_used, api_calls_limit)
            WHERE quota_warning_sent = false;
    END IF;
END $$;

-- Grant permissions
GRANT SELECT, INSERT, UPDATE ON alert_trigger_history TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE alert_trigger_history_id_seq TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON alert_trigger_config TO unicorn;
