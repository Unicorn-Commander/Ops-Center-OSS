-- Migration: 004_notification_history
-- Description: Create notification_history table for email tracking
-- Created: 2025-10-17

-- Create notification_history table
CREATE TABLE IF NOT EXISTS notification_history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,  -- usage, hardware, billing, security
    email_subject VARCHAR(255),
    email_body TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- sent, failed, queued
    error_message TEXT,

    -- Indexes for common queries
    INDEX idx_user_id (user_id),
    INDEX idx_alert_type (alert_type),
    INDEX idx_sent_at (sent_at),
    INDEX idx_status (status),
    INDEX idx_user_alert_sent (user_id, alert_type, sent_at)
);

-- Add comment
COMMENT ON TABLE notification_history IS 'Tracks all sent notification emails';

-- Grant permissions
GRANT SELECT, INSERT ON notification_history TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE notification_history_id_seq TO unicorn;
