-- Subscription Change History Schema
-- Tracks all subscription upgrades, downgrades, and cancellations
-- Created: 2025-11-12

-- Create subscription_changes table
CREATE TABLE IF NOT EXISTS subscription_changes (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    lago_subscription_id VARCHAR(255),
    change_type VARCHAR(20) NOT NULL CHECK (change_type IN ('upgrade', 'downgrade', 'cancel', 're activate')),
    from_plan VARCHAR(50),
    to_plan VARCHAR(50),
    effective_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason VARCHAR(100),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_subscription_changes_user_id ON subscription_changes(user_id);
CREATE INDEX IF NOT EXISTS idx_subscription_changes_change_type ON subscription_changes(change_type);
CREATE INDEX IF NOT EXISTS idx_subscription_changes_created_at ON subscription_changes(created_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_subscription_changes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS subscription_changes_updated_at_trigger ON subscription_changes;
CREATE TRIGGER subscription_changes_updated_at_trigger
    BEFORE UPDATE ON subscription_changes
    FOR EACH ROW
    EXECUTE FUNCTION update_subscription_changes_updated_at();

-- Comments for documentation
COMMENT ON TABLE subscription_changes IS 'Tracks all subscription plan changes (upgrades, downgrades, cancellations)';
COMMENT ON COLUMN subscription_changes.user_id IS 'Keycloak user ID (sub field)';
COMMENT ON COLUMN subscription_changes.lago_subscription_id IS 'Lago subscription ID if applicable';
COMMENT ON COLUMN subscription_changes.change_type IS 'Type of change: upgrade, downgrade, cancel, reactivate';
COMMENT ON COLUMN subscription_changes.from_plan IS 'Plan code before change';
COMMENT ON COLUMN subscription_changes.to_plan IS 'Plan code after change';
COMMENT ON COLUMN subscription_changes.effective_date IS 'When change becomes effective';
COMMENT ON COLUMN subscription_changes.reason IS 'Reason for change (especially for cancellations)';
COMMENT ON COLUMN subscription_changes.feedback IS 'User feedback about the change';
