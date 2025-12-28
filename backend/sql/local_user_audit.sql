-- Local User Audit Log Table
-- Tracks all local Linux user management operations

CREATE TABLE IF NOT EXISTS local_user_audit (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,  -- create_user, delete_user, set_password, add_ssh_key, remove_ssh_key, sudo_grant, sudo_revoke, list_users
    username TEXT NOT NULL,  -- Username operated on (or '*' for list operations)
    performed_by TEXT NOT NULL,  -- Email of Keycloak user who performed the action
    keycloak_user_id TEXT,  -- Keycloak user ID of performer
    success BOOLEAN NOT NULL,  -- True if operation succeeded
    error_message TEXT,  -- Error message if operation failed
    metadata JSONB,  -- Additional context (groups, shell, remove_home, key_fingerprint, etc.)
    client_ip TEXT,  -- IP address of client
    user_agent TEXT,  -- User agent string
    timestamp TIMESTAMP DEFAULT NOW(),  -- When the operation occurred

    -- Indexes for efficient querying
    CONSTRAINT valid_action CHECK (action IN (
        'create_user', 'delete_user', 'set_password',
        'add_ssh_key', 'remove_ssh_key',
        'sudo_grant', 'sudo_revoke', 'list_users'
    ))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_local_user_audit_username ON local_user_audit(username);
CREATE INDEX IF NOT EXISTS idx_local_user_audit_performed_by ON local_user_audit(performed_by);
CREATE INDEX IF NOT EXISTS idx_local_user_audit_timestamp ON local_user_audit(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_local_user_audit_action ON local_user_audit(action);
CREATE INDEX IF NOT EXISTS idx_local_user_audit_success ON local_user_audit(success);

-- Comment on table
COMMENT ON TABLE local_user_audit IS 'Audit log for all local Linux user management operations';

-- Comments on columns
COMMENT ON COLUMN local_user_audit.action IS 'Type of operation performed';
COMMENT ON COLUMN local_user_audit.username IS 'Username the operation was performed on (* for list operations)';
COMMENT ON COLUMN local_user_audit.performed_by IS 'Email of admin who performed the operation';
COMMENT ON COLUMN local_user_audit.success IS 'Whether the operation succeeded';
COMMENT ON COLUMN local_user_audit.error_message IS 'Error message if operation failed';
COMMENT ON COLUMN local_user_audit.metadata IS 'Additional operation details in JSON format';

-- Grant permissions (adjust role as needed)
-- GRANT SELECT, INSERT ON local_user_audit TO ops_center_backend;
-- GRANT USAGE, SELECT ON SEQUENCE local_user_audit_id_seq TO ops_center_backend;
