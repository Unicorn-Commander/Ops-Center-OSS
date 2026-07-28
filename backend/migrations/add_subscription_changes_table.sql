-- Migration: Add subscription_changes table
-- Date: 2025-10-24
-- Epic: 2.4 - Self-Service Upgrades
-- Purpose: Track subscription tier changes (upgrades and downgrades)

-- Create subscription_changes table
CREATE TABLE IF NOT EXISTS subscription_changes (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    old_tier VARCHAR(50),
    new_tier VARCHAR(50) NOT NULL,
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('upgrade', 'downgrade', 'cancel')),
    effective_date TIMESTAMP NOT NULL,
    proration_amount DECIMAL(10,2) DEFAULT 0.00,
    stripe_session_id VARCHAR(255),
    lago_subscription_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Create indexes for common queries
CREATE INDEX idx_subscription_changes_user ON subscription_changes(user_id);
CREATE INDEX idx_subscription_changes_effective_date ON subscription_changes(effective_date);
CREATE INDEX idx_subscription_changes_type ON subscription_changes(change_type);
CREATE INDEX idx_subscription_changes_created_at ON subscription_changes(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE subscription_changes IS 'Tracks all subscription tier changes including upgrades, downgrades, and cancellations';
COMMENT ON COLUMN subscription_changes.id IS 'Unique change ID (format: orgid_timestamp)';
COMMENT ON COLUMN subscription_changes.user_id IS 'Keycloak user ID who initiated the change';
COMMENT ON COLUMN subscription_changes.old_tier IS 'Previous subscription tier (null for first subscription)';
COMMENT ON COLUMN subscription_changes.new_tier IS 'New subscription tier';
COMMENT ON COLUMN subscription_changes.change_type IS 'Type of change: upgrade, downgrade, or cancel';
COMMENT ON COLUMN subscription_changes.effective_date IS 'When the change takes effect';
COMMENT ON COLUMN subscription_changes.proration_amount IS 'Proration amount charged (positive) or credited (negative)';
COMMENT ON COLUMN subscription_changes.stripe_session_id IS 'Stripe checkout session ID (for upgrades)';
COMMENT ON COLUMN subscription_changes.lago_subscription_id IS 'Lago subscription ID';
COMMENT ON COLUMN subscription_changes.created_at IS 'When the change was requested';
COMMENT ON COLUMN subscription_changes.notes IS 'Additional notes about the change';

-- Grant permissions (adjust as needed for your database user)
-- GRANT SELECT, INSERT, UPDATE ON subscription_changes TO ops_center_app;
