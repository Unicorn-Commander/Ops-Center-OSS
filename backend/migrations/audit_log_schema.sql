-- ==============================================================================
-- Audit Log Schema Migration
-- System-wide audit logging for security, compliance, and debugging
--
-- Author: Ops-Center AI
-- Created: January 31, 2026
-- ==============================================================================

-- Drop existing table if exists (for clean migrations)
DROP TABLE IF EXISTS audit_log CASCADE;

-- ==============================================================================
-- Main Audit Log Table
-- ==============================================================================

CREATE TABLE IF NOT EXISTS audit_log (
    -- Primary identifier
    id SERIAL PRIMARY KEY,

    -- Event classification
    event_type VARCHAR(50) NOT NULL,           -- 'auth', 'billing', 'service', 'admin', 'api', 'user', 'system', 'security'
    severity VARCHAR(20) DEFAULT 'info',       -- 'info', 'warning', 'error', 'critical'

    -- User context (nullable for system events)
    user_id VARCHAR(255),                      -- Keycloak user ID (UUID)
    user_email VARCHAR(255),                   -- User email for quick reference

    -- Action details
    action VARCHAR(255) NOT NULL,              -- Brief action description (e.g., 'user.login', 'subscription.upgrade')
    description TEXT,                          -- Detailed description of what happened

    -- Resource context
    resource_type VARCHAR(100),                -- Type of resource affected (e.g., 'user', 'organization', 'subscription')
    resource_id VARCHAR(255),                  -- ID of the affected resource

    -- Request context
    ip_address VARCHAR(45),                    -- IPv4 or IPv6 address
    user_agent TEXT,                           -- Browser/client user agent string
    request_id VARCHAR(100),                   -- Unique request identifier for correlation
    session_id VARCHAR(255),                   -- Session ID if available

    -- Additional context (JSONB for flexibility)
    metadata JSONB DEFAULT '{}',               -- Additional context (old_value, new_value, error_details, etc.)

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT valid_event_type CHECK (event_type IN ('auth', 'billing', 'service', 'admin', 'api', 'user', 'system', 'security')),
    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'error', 'critical'))
);

-- ==============================================================================
-- Indexes for Performance
-- ==============================================================================

-- Primary lookup indexes
CREATE INDEX idx_audit_log_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_severity ON audit_log(severity);
CREATE INDEX idx_audit_log_resource_type ON audit_log(resource_type);
CREATE INDEX idx_audit_log_resource_id ON audit_log(resource_id);

-- Time-based queries (most common - DESC for recent first)
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at DESC);

-- Composite indexes for common query patterns
CREATE INDEX idx_audit_log_user_created ON audit_log(user_id, created_at DESC);
CREATE INDEX idx_audit_log_event_severity ON audit_log(event_type, severity);
CREATE INDEX idx_audit_log_event_created ON audit_log(event_type, created_at DESC);
CREATE INDEX idx_audit_log_resource ON audit_log(resource_type, resource_id);

-- Full-text search index for action and description
CREATE INDEX idx_audit_log_search ON audit_log
    USING gin(to_tsvector('english', action || ' ' || COALESCE(description, '')));

-- JSONB index for metadata queries
CREATE INDEX idx_audit_log_metadata ON audit_log USING gin(metadata);

-- ==============================================================================
-- Table Comments
-- ==============================================================================

COMMENT ON TABLE audit_log IS 'System-wide audit log for tracking all significant events';
COMMENT ON COLUMN audit_log.event_type IS 'Category: auth, billing, service, admin, api, user, system, security';
COMMENT ON COLUMN audit_log.severity IS 'Severity level: info, warning, error, critical';
COMMENT ON COLUMN audit_log.user_id IS 'Keycloak user UUID (null for system events)';
COMMENT ON COLUMN audit_log.action IS 'Brief action identifier (e.g., user.login, subscription.upgrade)';
COMMENT ON COLUMN audit_log.description IS 'Human-readable description of the event';
COMMENT ON COLUMN audit_log.resource_type IS 'Type of affected resource (user, organization, subscription, etc.)';
COMMENT ON COLUMN audit_log.resource_id IS 'Identifier of the affected resource';
COMMENT ON COLUMN audit_log.metadata IS 'Additional context as JSONB (old_value, new_value, error_details, etc.)';

-- ==============================================================================
-- Retention Policy (optional - use pg_cron or external scheduler)
-- ==============================================================================

-- Example: Delete audit logs older than 90 days
-- This should be run as a scheduled job, not automatically
-- DELETE FROM audit_log WHERE created_at < NOW() - INTERVAL '90 days';

-- ==============================================================================
-- Sample Data for Testing
-- ==============================================================================

-- Uncomment to insert sample data for testing

-- INSERT INTO audit_log (event_type, severity, user_id, user_email, action, description, resource_type, resource_id, ip_address, metadata)
-- VALUES
--     ('auth', 'info', 'user-123', 'admin@example.com', 'user.login', 'User logged in successfully', 'user', 'user-123', '192.168.1.1', '{"method": "password"}'),
--     ('billing', 'info', 'user-123', 'admin@example.com', 'subscription.upgrade', 'Upgraded from starter to professional tier', 'subscription', 'sub-456', '192.168.1.1', '{"old_tier": "starter", "new_tier": "professional"}'),
--     ('security', 'warning', 'user-789', 'user@example.com', 'auth.failed', 'Failed login attempt - invalid password', 'user', 'user-789', '10.0.0.5', '{"attempts": 3}'),
--     ('admin', 'info', 'admin-001', 'superadmin@example.com', 'user.role_change', 'Assigned admin role to user', 'user', 'user-123', '192.168.1.100', '{"role": "admin"}'),
--     ('api', 'error', 'user-456', 'developer@example.com', 'api.rate_limited', 'Rate limit exceeded for LLM endpoint', 'api_key', 'key-789', '172.16.0.50', '{"endpoint": "/api/v1/llm/chat/completions", "limit": 1000}'),
--     ('system', 'critical', NULL, NULL, 'database.connection_lost', 'Lost connection to primary database', 'database', 'postgres-primary', NULL, '{"error": "Connection refused", "retry_count": 5}');

-- ==============================================================================
-- Grant Permissions (adjust based on your database user)
-- ==============================================================================

-- Grant permissions to the ops-center database user
-- GRANT SELECT, INSERT ON audit_log TO ops_center_user;
-- GRANT USAGE, SELECT ON SEQUENCE audit_log_id_seq TO ops_center_user;

-- ==============================================================================
-- Migration Complete
-- ==============================================================================
