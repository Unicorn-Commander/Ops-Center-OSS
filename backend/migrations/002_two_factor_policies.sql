-- Migration: Two-Factor Authentication Policies
-- Date: 2025-10-28
-- Description: Creates tables for role-based 2FA policies and exemptions

-- ============================================================================
-- TABLE: two_factor_policies
-- Purpose: Store role-based 2FA requirements
-- ============================================================================

CREATE TABLE IF NOT EXISTS two_factor_policies (
    id SERIAL PRIMARY KEY,
    role VARCHAR(50) NOT NULL UNIQUE,
    require_2fa BOOLEAN NOT NULL DEFAULT false,
    grace_period_days INTEGER NOT NULL DEFAULT 7,
    enforcement_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),  -- Admin who created policy (Keycloak user ID)
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255)   -- Admin who last updated policy
);

-- Index for fast role lookups
CREATE INDEX IF NOT EXISTS idx_2fa_policies_role ON two_factor_policies(role);

-- Index for enforcement date queries
CREATE INDEX IF NOT EXISTS idx_2fa_policies_enforcement ON two_factor_policies(enforcement_date)
    WHERE enforcement_date IS NOT NULL;

COMMENT ON TABLE two_factor_policies IS 'Role-based 2FA enforcement policies';
COMMENT ON COLUMN two_factor_policies.role IS 'Keycloak role name (admin, moderator, developer, etc.)';
COMMENT ON COLUMN two_factor_policies.require_2fa IS 'Whether 2FA is required for this role';
COMMENT ON COLUMN two_factor_policies.grace_period_days IS 'Days before enforcement starts (0-90)';
COMMENT ON COLUMN two_factor_policies.enforcement_date IS 'Date when enforcement begins';

-- ============================================================================
-- TABLE: two_factor_policy_exemptions
-- Purpose: Store temporary exemptions from 2FA requirements
-- ============================================================================

CREATE TABLE IF NOT EXISTS two_factor_policy_exemptions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    role VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    exemption_start_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    exemption_end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255) NOT NULL,  -- Admin who granted exemption
    revoked_at TIMESTAMP WITH TIME ZONE,
    revoked_by VARCHAR(255),  -- Admin who revoked exemption
    revoked_reason TEXT
);

-- Index for fast user lookups
CREATE INDEX IF NOT EXISTS idx_2fa_exemptions_user ON two_factor_policy_exemptions(user_id);

-- Index for active exemptions
CREATE INDEX IF NOT EXISTS idx_2fa_exemptions_active ON two_factor_policy_exemptions(user_id, exemption_end_date)
    WHERE revoked_at IS NULL AND exemption_end_date > CURRENT_TIMESTAMP;

COMMENT ON TABLE two_factor_policy_exemptions IS 'Temporary exemptions from 2FA requirements';
COMMENT ON COLUMN two_factor_policy_exemptions.user_id IS 'Keycloak user ID';
COMMENT ON COLUMN two_factor_policy_exemptions.role IS 'Role for which exemption applies';
COMMENT ON COLUMN two_factor_policy_exemptions.reason IS 'Reason for exemption (required)';
COMMENT ON COLUMN two_factor_policy_exemptions.exemption_end_date IS 'When exemption expires';

-- ============================================================================
-- TABLE: two_factor_reset_log
-- Purpose: Track 2FA reset operations for rate limiting and audit
-- ============================================================================

CREATE TABLE IF NOT EXISTS two_factor_reset_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- User whose 2FA was reset
    admin_id VARCHAR(255) NOT NULL,  -- Admin who performed reset
    reason TEXT NOT NULL,
    credentials_removed INTEGER DEFAULT 0,  -- Number of credentials removed
    required_action_set BOOLEAN DEFAULT false,
    sessions_logged_out BOOLEAN DEFAULT false,
    client_ip VARCHAR(45),  -- IPv4 or IPv6
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for rate limiting queries
CREATE INDEX IF NOT EXISTS idx_2fa_reset_user_time ON two_factor_reset_log(user_id, created_at);

-- Index for admin activity audits
CREATE INDEX IF NOT EXISTS idx_2fa_reset_admin ON two_factor_reset_log(admin_id, created_at);

COMMENT ON TABLE two_factor_reset_log IS 'Audit log of 2FA reset operations';
COMMENT ON COLUMN two_factor_reset_log.user_id IS 'User whose 2FA was reset';
COMMENT ON COLUMN two_factor_reset_log.admin_id IS 'Admin who performed the reset';
COMMENT ON COLUMN two_factor_reset_log.reason IS 'Reason provided for reset';

-- ============================================================================
-- FUNCTION: Update updated_at timestamp automatically
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to two_factor_policies
CREATE TRIGGER update_2fa_policies_updated_at
    BEFORE UPDATE ON two_factor_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- FUNCTION: Get active 2FA policy for user
-- ============================================================================

CREATE OR REPLACE FUNCTION get_user_2fa_policy(p_user_id VARCHAR, p_role VARCHAR)
RETURNS TABLE (
    require_2fa BOOLEAN,
    grace_period_days INTEGER,
    enforcement_date TIMESTAMP WITH TIME ZONE,
    has_exemption BOOLEAN,
    exemption_end_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.require_2fa,
        p.grace_period_days,
        p.enforcement_date,
        EXISTS (
            SELECT 1
            FROM two_factor_policy_exemptions e
            WHERE e.user_id = p_user_id
                AND e.role = p_role
                AND e.revoked_at IS NULL
                AND e.exemption_end_date > CURRENT_TIMESTAMP
        ) AS has_exemption,
        (
            SELECT MAX(e.exemption_end_date)
            FROM two_factor_policy_exemptions e
            WHERE e.user_id = p_user_id
                AND e.role = p_role
                AND e.revoked_at IS NULL
                AND e.exemption_end_date > CURRENT_TIMESTAMP
        ) AS exemption_end_date
    FROM two_factor_policies p
    WHERE p.role = p_role;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_user_2fa_policy IS 'Get effective 2FA policy for a user considering exemptions';

-- ============================================================================
-- FUNCTION: Check if user is within rate limit for 2FA resets
-- ============================================================================

CREATE OR REPLACE FUNCTION check_2fa_reset_rate_limit(p_user_id VARCHAR, p_limit INTEGER, p_window_hours INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    reset_count INTEGER;
BEGIN
    -- Count resets within window
    SELECT COUNT(*)
    INTO reset_count
    FROM two_factor_reset_log
    WHERE user_id = p_user_id
        AND created_at > (CURRENT_TIMESTAMP - (p_window_hours || ' hours')::INTERVAL);

    -- Return true if within limit
    RETURN reset_count < p_limit;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_2fa_reset_rate_limit IS 'Check if user has exceeded 2FA reset rate limit';

-- ============================================================================
-- SEED DATA: Default policies (optional)
-- ============================================================================

-- Default policy: Admins require 2FA with 7-day grace period
INSERT INTO two_factor_policies (role, require_2fa, grace_period_days, enforcement_date, created_by)
VALUES ('admin', true, 7, CURRENT_TIMESTAMP + INTERVAL '7 days', 'system')
ON CONFLICT (role) DO NOTHING;

-- Default policy: Moderators do not require 2FA (but recommended)
INSERT INTO two_factor_policies (role, require_2fa, grace_period_days, enforcement_date, created_by)
VALUES ('moderator', false, 0, NULL, 'system')
ON CONFLICT (role) DO NOTHING;

COMMENT ON TABLE two_factor_policies IS 'NOTE: Seeded with default policies for admin and moderator roles';

-- ============================================================================
-- PERMISSIONS (optional - adjust based on your setup)
-- ============================================================================

-- Grant read/write to ops-center backend user
-- GRANT SELECT, INSERT, UPDATE, DELETE ON two_factor_policies TO unicorn;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON two_factor_policy_exemptions TO unicorn;
-- GRANT SELECT, INSERT ON two_factor_reset_log TO unicorn;
-- GRANT USAGE, SELECT ON SEQUENCE two_factor_policies_id_seq TO unicorn;
-- GRANT USAGE, SELECT ON SEQUENCE two_factor_policy_exemptions_id_seq TO unicorn;
-- GRANT USAGE, SELECT ON SEQUENCE two_factor_reset_log_id_seq TO unicorn;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify tables created
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name LIKE 'two_factor%'
ORDER BY table_name;
