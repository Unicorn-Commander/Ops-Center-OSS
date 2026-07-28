-- Email Logs Table Migration
-- Created: November 29, 2025
-- Purpose: Track all email alert sends for monitoring and debugging

-- Create email_logs table
CREATE TABLE IF NOT EXISTS email_logs (
    id SERIAL PRIMARY KEY,
    recipient VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    sent_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);
CREATE INDEX IF NOT EXISTS idx_email_logs_alert_type ON email_logs(alert_type);
CREATE INDEX IF NOT EXISTS idx_email_logs_sent_at ON email_logs(sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_logs_recipient ON email_logs(recipient);

-- Cleanup function to remove old logs (keep last 90 days)
CREATE OR REPLACE FUNCTION cleanup_old_email_logs()
RETURNS void AS $$
BEGIN
    DELETE FROM email_logs
    WHERE sent_at < NOW() - INTERVAL '90 days';
    RAISE NOTICE 'Deleted % old email log entries', FOUND;
END;
$$ LANGUAGE plpgsql;

-- Comment the table
COMMENT ON TABLE email_logs IS 'Email alert sending history and status tracking';
COMMENT ON COLUMN email_logs.alert_type IS 'Type: system_critical, billing, security, usage';
COMMENT ON COLUMN email_logs.status IS 'Status: pending, sent, failed';
COMMENT ON FUNCTION cleanup_old_email_logs IS 'Run daily to clean up logs older than 90 days';

-- Verification query
DO $$
BEGIN
    RAISE NOTICE 'Email logs table created successfully';
    RAISE NOTICE 'Total existing log entries: %', (SELECT COUNT(*) FROM email_logs);
END $$;
