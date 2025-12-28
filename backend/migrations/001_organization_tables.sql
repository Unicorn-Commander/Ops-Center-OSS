-- Organization Management Database Migration
-- Version: 001
-- Created: 2025-10-15
-- Description: Create tables for enterprise organization management

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== Organizations Table ====================

CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) UNIQUE NOT NULL,
    display_name VARCHAR(255),
    logo_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    plan_tier VARCHAR(50) DEFAULT 'founders_friend',
    max_seats INTEGER DEFAULT 1,
    lago_customer_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted'))
);

-- Create indexes for organizations
CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name);
CREATE INDEX IF NOT EXISTS idx_organizations_status ON organizations(status);
CREATE INDEX IF NOT EXISTS idx_organizations_plan_tier ON organizations(plan_tier);
CREATE INDEX IF NOT EXISTS idx_organizations_lago_customer ON organizations(lago_customer_id);
CREATE INDEX IF NOT EXISTS idx_organizations_stripe_customer ON organizations(stripe_customer_id);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Organization Members Table ====================

CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('owner', 'admin', 'member', 'billing_admin')),
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, user_id)
);

-- Create indexes for organization_members
CREATE INDEX IF NOT EXISTS idx_org_members_org_id ON organization_members(org_id);
CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON organization_members(user_id);
CREATE INDEX IF NOT EXISTS idx_org_members_role ON organization_members(role);

-- ==================== Organization Quotas Table ====================

CREATE TABLE IF NOT EXISTS organization_quotas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    resource_type VARCHAR(100) NOT NULL CHECK (resource_type IN ('llm_calls', 'storage_gb', 'agents', 'seats')),
    limit_value BIGINT NOT NULL,
    used_value BIGINT DEFAULT 0,
    reset_period VARCHAR(50) DEFAULT 'monthly' CHECK (reset_period IN ('daily', 'monthly', 'never')),
    last_reset TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_id, resource_type)
);

-- Create indexes for organization_quotas
CREATE INDEX IF NOT EXISTS idx_org_quotas_org_id ON organization_quotas(org_id);
CREATE INDEX IF NOT EXISTS idx_org_quotas_resource_type ON organization_quotas(resource_type);

-- ==================== Organization Invitations Table ====================

CREATE TABLE IF NOT EXISTS organization_invitations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'billing_admin')),
    invited_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '7 days'),
    accepted BOOLEAN DEFAULT FALSE,
    accepted_at TIMESTAMP WITH TIME ZONE
);

-- Create indexes for organization_invitations
CREATE INDEX IF NOT EXISTS idx_org_invitations_org_id ON organization_invitations(org_id);
CREATE INDEX IF NOT EXISTS idx_org_invitations_email ON organization_invitations(email);
CREATE INDEX IF NOT EXISTS idx_org_invitations_accepted ON organization_invitations(accepted);
CREATE INDEX IF NOT EXISTS idx_org_invitations_expires_at ON organization_invitations(expires_at);

-- ==================== Organization Settings Table ====================

CREATE TABLE IF NOT EXISTS organization_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID UNIQUE NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    settings JSONB DEFAULT '{}',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for organization_settings
CREATE INDEX IF NOT EXISTS idx_org_settings_org_id ON organization_settings(org_id);
CREATE INDEX IF NOT EXISTS idx_org_settings_settings_gin ON organization_settings USING GIN (settings);

-- Create trigger for updated_at timestamp
CREATE TRIGGER update_org_settings_updated_at BEFORE UPDATE ON organization_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==================== Audit Log Table ====================

CREATE TABLE IF NOT EXISTS organization_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for audit log
CREATE INDEX IF NOT EXISTS idx_org_audit_org_id ON organization_audit_log(org_id);
CREATE INDEX IF NOT EXISTS idx_org_audit_user_id ON organization_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_org_audit_action ON organization_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_org_audit_created_at ON organization_audit_log(created_at);
CREATE INDEX IF NOT EXISTS idx_org_audit_details_gin ON organization_audit_log USING GIN (details);

-- ==================== Helper Functions ====================

-- Function to check if user is org admin
CREATE OR REPLACE FUNCTION is_org_admin(p_org_id UUID, p_user_id VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM organization_members
        WHERE org_id = p_org_id
          AND user_id = p_user_id
          AND role IN ('owner', 'admin')
    );
END;
$$ LANGUAGE plpgsql;

-- Function to check seat availability
CREATE OR REPLACE FUNCTION has_available_seats(p_org_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
    v_max_seats INTEGER;
    v_used_seats INTEGER;
BEGIN
    SELECT max_seats INTO v_max_seats
    FROM organizations
    WHERE id = p_org_id;

    SELECT COUNT(*) INTO v_used_seats
    FROM organization_members
    WHERE org_id = p_org_id;

    RETURN v_used_seats < v_max_seats;
END;
$$ LANGUAGE plpgsql;

-- Function to get quota usage percentage
CREATE OR REPLACE FUNCTION get_quota_usage_percentage(p_org_id UUID, p_resource_type VARCHAR)
RETURNS DECIMAL AS $$
DECLARE
    v_quota RECORD;
BEGIN
    SELECT limit_value, used_value INTO v_quota
    FROM organization_quotas
    WHERE org_id = p_org_id
      AND resource_type = p_resource_type;

    IF v_quota.limit_value = 0 THEN
        RETURN 0;
    END IF;

    RETURN (v_quota.used_value::DECIMAL / v_quota.limit_value::DECIMAL) * 100;
END;
$$ LANGUAGE plpgsql;

-- ==================== Sample Data (Optional - for testing) ====================

-- Insert a default organization for testing
-- Uncomment the following lines if you want to create a test organization

/*
INSERT INTO organizations (name, display_name, plan_tier, max_seats, status)
VALUES
    ('default-org', 'Default Organization', 'founders_friend', 5, 'active')
ON CONFLICT (name) DO NOTHING;

-- Insert test quotas
INSERT INTO organization_quotas (org_id, resource_type, limit_value, used_value)
SELECT
    id,
    resource_type,
    limit_value,
    0
FROM organizations, (VALUES
    ('llm_calls', 10000),
    ('storage_gb', 100),
    ('agents', 50),
    ('seats', 5)
) AS quotas(resource_type, limit_value)
WHERE name = 'default-org'
ON CONFLICT (org_id, resource_type) DO NOTHING;
*/

-- ==================== Views for Convenience ====================

-- View for organization member count
CREATE OR REPLACE VIEW org_member_counts AS
SELECT
    o.id AS org_id,
    o.name AS org_name,
    COUNT(om.id) AS member_count,
    o.max_seats,
    o.max_seats - COUNT(om.id) AS available_seats
FROM organizations o
LEFT JOIN organization_members om ON o.id = om.org_id
GROUP BY o.id, o.name, o.max_seats;

-- View for quota usage summary
CREATE OR REPLACE VIEW org_quota_summary AS
SELECT
    o.id AS org_id,
    o.name AS org_name,
    oq.resource_type,
    oq.used_value,
    oq.limit_value,
    CASE
        WHEN oq.limit_value > 0 THEN
            ROUND((oq.used_value::DECIMAL / oq.limit_value::DECIMAL) * 100, 2)
        ELSE 0
    END AS usage_percentage,
    oq.reset_period,
    oq.last_reset
FROM organizations o
JOIN organization_quotas oq ON o.id = oq.org_id
WHERE o.status = 'active';

-- View for pending invitations
CREATE OR REPLACE VIEW org_pending_invitations AS
SELECT
    oi.*,
    o.name AS org_name
FROM organization_invitations oi
JOIN organizations o ON oi.org_id = o.id
WHERE oi.accepted = FALSE
  AND oi.expires_at > CURRENT_TIMESTAMP;

-- ==================== Permissions ====================

-- Grant permissions (adjust based on your roles)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ops_center_app;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ops_center_app;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ops_center_app;

-- ==================== Migration Complete ====================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Organization management tables created successfully';
    RAISE NOTICE 'Tables: organizations, organization_members, organization_quotas, organization_invitations, organization_settings, organization_audit_log';
    RAISE NOTICE 'Views: org_member_counts, org_quota_summary, org_pending_invitations';
    RAISE NOTICE 'Functions: is_org_admin, has_available_seats, get_quota_usage_percentage';
END $$;
