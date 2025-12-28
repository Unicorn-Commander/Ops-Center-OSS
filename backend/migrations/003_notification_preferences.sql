-- Migration: Create notification_preferences table
-- Date: 2025-10-17
-- Description: Store user notification preferences (Phase 2 - storage only, no email sending)

-- Create notification_preferences table
CREATE TABLE IF NOT EXISTS notification_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL,

    -- Alert types (boolean toggles)
    usage_alerts_enabled BOOLEAN DEFAULT true,
    hardware_alerts_enabled BOOLEAN DEFAULT true,
    billing_alerts_enabled BOOLEAN DEFAULT true,
    security_alerts_enabled BOOLEAN DEFAULT true,

    -- Thresholds
    usage_alert_threshold INT DEFAULT 80,  -- % of tier limit
    hardware_temp_threshold INT DEFAULT 80,  -- degrees Celsius

    -- Frequency
    alert_frequency VARCHAR(20) DEFAULT 'immediate',  -- immediate, daily, weekly

    -- Notification Channels
    email_enabled BOOLEAN DEFAULT true,
    slack_enabled BOOLEAN DEFAULT false,
    slack_webhook_url TEXT,
    sms_enabled BOOLEAN DEFAULT false,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    CONSTRAINT valid_alert_frequency CHECK (alert_frequency IN ('immediate', 'daily', 'weekly')),
    CONSTRAINT valid_usage_threshold CHECK (usage_alert_threshold >= 0 AND usage_alert_threshold <= 100),
    CONSTRAINT valid_temp_threshold CHECK (hardware_temp_threshold >= 0 AND hardware_temp_threshold <= 100)
);

-- Create index on user_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_notification_preferences_user_id ON notification_preferences(user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_notification_preferences_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_notification_preferences_updated_at
    BEFORE UPDATE ON notification_preferences
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_preferences_updated_at();

-- Insert default preferences for existing users (if any)
-- This will be handled by the API when users first access the settings page

COMMENT ON TABLE notification_preferences IS 'User notification preferences (Phase 2 - storage only, email sending in Phase 3)';
COMMENT ON COLUMN notification_preferences.alert_frequency IS 'How often to send alerts: immediate, daily, weekly';
COMMENT ON COLUMN notification_preferences.usage_alert_threshold IS 'Percentage of tier limit to trigger usage alert (0-100)';
COMMENT ON COLUMN notification_preferences.hardware_temp_threshold IS 'Temperature in Celsius to trigger hardware alert (0-100)';
