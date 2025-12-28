-- Migration: Create permission audit log table
-- Date: 2025-10-17
-- Description: Audit trail for all permission changes (assign, revoke, update)

-- Create permission audit log table
CREATE TABLE IF NOT EXISTS permission_audit_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Action performed
    action VARCHAR(20) NOT NULL CHECK (action IN ('assign', 'revoke', 'update')),

    -- Permission details
    level VARCHAR(20) NOT NULL CHECK (level IN ('system', 'platform', 'organization', 'application', 'user')),
    resource VARCHAR(50) NOT NULL,
    permission_action VARCHAR(20) NOT NULL,  -- The permission action (read, write, delete, admin, execute)

    -- Scope
    scope_id VARCHAR(255),  -- user_id, org_id, app_id, etc.
    granted BOOLEAN NOT NULL,

    -- Audit fields
    changed_by VARCHAR(255) NOT NULL,  -- User who made the change
    metadata JSONB DEFAULT '{}',  -- Additional context

    -- IP and user agent for security
    ip_address INET,
    user_agent TEXT
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON permission_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_scope ON permission_audit_log(scope_id) WHERE scope_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_audit_resource ON permission_audit_log(resource);
CREATE INDEX IF NOT EXISTS idx_audit_action ON permission_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_changed_by ON permission_audit_log(changed_by);

-- GIN index for metadata queries
CREATE INDEX IF NOT EXISTS idx_audit_metadata ON permission_audit_log USING GIN (metadata);

-- Comments
COMMENT ON TABLE permission_audit_log IS 'Audit trail for all permission changes';
COMMENT ON COLUMN permission_audit_log.action IS 'Type of change: assign, revoke, update';
COMMENT ON COLUMN permission_audit_log.permission_action IS 'The permission action being modified (read, write, delete, admin, execute)';
COMMENT ON COLUMN permission_audit_log.changed_by IS 'User ID who made the change';
COMMENT ON COLUMN permission_audit_log.metadata IS 'Additional context: reason for change, approval ticket, etc.';

COMMIT;
