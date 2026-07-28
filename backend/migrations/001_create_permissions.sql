-- Migration: Create permissions table for 5-layer hierarchical permission system
-- Date: 2025-10-16
-- Description: Implements System → Platform → Organization → Application → User permission hierarchy

-- Drop existing table if exists (for clean migration)
DROP TABLE IF EXISTS permissions CASCADE;

-- Create permissions table
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,

    -- Permission hierarchy level
    level VARCHAR(20) NOT NULL CHECK (level IN ('system', 'platform', 'organization', 'application', 'user')),

    -- Resource being controlled
    resource VARCHAR(50) NOT NULL CHECK (resource IN (
        'services', 'hardware', 'models',
        'users', 'organizations', 'roles',
        'billing', 'subscriptions', 'usage_metrics', 'invoices',
        'llm_inference', 'agent_invocations', 'search_queries', 'tts_generation', 'stt_transcription',
        'api_keys', 'webhooks'
    )),

    -- Action being controlled
    action VARCHAR(20) NOT NULL CHECK (action IN ('read', 'write', 'delete', 'admin', 'execute')),

    -- Permission grant/deny
    granted BOOLEAN NOT NULL DEFAULT TRUE,

    -- Scope identifier (user_id, org_id, platform name, app_id, etc.)
    -- NULL for system-level permissions
    scope_id VARCHAR(255),

    -- Additional metadata (rate limits, constraints, etc.)
    metadata JSONB DEFAULT '{}',

    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    updated_by VARCHAR(255)
);

-- Indexes for fast permission lookups
CREATE INDEX idx_permissions_level ON permissions(level);
CREATE INDEX idx_permissions_resource_action ON permissions(resource, action);
CREATE INDEX idx_permissions_scope_id ON permissions(scope_id) WHERE scope_id IS NOT NULL;
CREATE INDEX idx_permissions_level_scope ON permissions(level, scope_id) WHERE scope_id IS NOT NULL;
CREATE INDEX idx_permissions_granted ON permissions(granted);

-- Index for fast user permission lookups
CREATE INDEX idx_permissions_user_lookup ON permissions(level, resource, action, scope_id)
    WHERE level = 'user' AND granted = TRUE;

-- GIN index for metadata JSONB queries
CREATE INDEX idx_permissions_metadata ON permissions USING GIN (metadata);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_permissions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_permissions_updated_at
    BEFORE UPDATE ON permissions
    FOR EACH ROW
    EXECUTE FUNCTION update_permissions_updated_at();

-- Insert default system-level permissions

-- Admin permissions (full access)
INSERT INTO permissions (level, resource, action, granted, metadata, created_by) VALUES
    ('system', 'users', 'admin', TRUE, '{"default": true, "description": "Admins can manage all users"}', 'migration'),
    ('system', 'organizations', 'admin', TRUE, '{"default": true, "description": "Admins can manage all organizations"}', 'migration'),
    ('system', 'billing', 'admin', TRUE, '{"default": true, "description": "Admins can manage billing"}', 'migration'),
    ('system', 'services', 'admin', TRUE, '{"default": true, "description": "Admins can manage services"}', 'migration'),
    ('system', 'hardware', 'admin', TRUE, '{"default": true, "description": "Admins can manage hardware"}', 'migration'),
    ('system', 'roles', 'admin', TRUE, '{"default": true, "description": "Admins can manage roles"}', 'migration'),
    ('system', 'api_keys', 'admin', TRUE, '{"default": true, "description": "Admins can manage all API keys"}', 'migration'),
    ('system', 'webhooks', 'admin', TRUE, '{"default": true, "description": "Admins can manage webhooks"}', 'migration');

-- Read permissions for authenticated users
INSERT INTO permissions (level, resource, action, granted, metadata, created_by) VALUES
    ('system', 'users', 'read', TRUE, '{"default": true, "description": "Users can read own profile", "scope": "self"}', 'migration'),
    ('system', 'usage_metrics', 'read', TRUE, '{"default": true, "description": "Users can read own usage"}', 'migration'),
    ('system', 'invoices', 'read', TRUE, '{"default": true, "description": "Users can read own invoices"}', 'migration'),
    ('system', 'subscriptions', 'read', TRUE, '{"default": true, "description": "Users can read own subscription"}', 'migration');

-- Platform service access (by default, all users can use services within tier limits)
INSERT INTO permissions (level, resource, action, granted, metadata, created_by) VALUES
    ('system', 'llm_inference', 'execute', TRUE, '{"default": true, "description": "Users can use LLM inference", "tier_limited": true}', 'migration'),
    ('system', 'search_queries', 'execute', TRUE, '{"default": true, "description": "Users can use search", "tier_limited": true}', 'migration'),
    ('system', 'agent_invocations', 'execute', TRUE, '{"default": true, "description": "Users can invoke agents", "tier_limited": true}', 'migration'),
    ('system', 'tts_generation', 'execute', TRUE, '{"default": true, "description": "Users can use TTS", "tier_limited": true}', 'migration'),
    ('system', 'stt_transcription', 'execute', TRUE, '{"default": true, "description": "Users can use STT", "tier_limited": true}', 'migration');

-- API key management (users can create/manage own keys)
INSERT INTO permissions (level, resource, action, granted, metadata, created_by) VALUES
    ('system', 'api_keys', 'write', TRUE, '{"default": true, "description": "Users can create own API keys"}', 'migration'),
    ('system', 'api_keys', 'read', TRUE, '{"default": true, "description": "Users can list own API keys"}', 'migration'),
    ('system', 'api_keys', 'delete', TRUE, '{"default": true, "description": "Users can delete own API keys"}', 'migration');

-- Write permissions for subscription management
INSERT INTO permissions (level, resource, action, granted, metadata, created_by) VALUES
    ('system', 'subscriptions', 'write', TRUE, '{"default": true, "description": "Users can upgrade/downgrade subscription"}', 'migration');

-- Comments for documentation
COMMENT ON TABLE permissions IS 'Hierarchical permission system with 5 levels: system → platform → organization → application → user';
COMMENT ON COLUMN permissions.level IS 'Permission hierarchy level: system (platform-wide) → platform (service-level) → organization → application → user (individual override)';
COMMENT ON COLUMN permissions.resource IS 'Resource being controlled (e.g., users, billing, services)';
COMMENT ON COLUMN permissions.action IS 'Action being controlled (read, write, delete, admin, execute)';
COMMENT ON COLUMN permissions.granted IS 'TRUE = allow access, FALSE = deny access (explicit deny overrides)';
COMMENT ON COLUMN permissions.scope_id IS 'Scope identifier: user_id for user level, org_id for org level, NULL for system level';
COMMENT ON COLUMN permissions.metadata IS 'Additional constraints: rate limits, tier restrictions, feature flags, etc.';

-- Example permission checks:
-- 1. Check if user can execute LLM inference:
--    SELECT * FROM permissions
--    WHERE resource = 'llm_inference' AND action = 'execute'
--    AND (level = 'user' AND scope_id = :user_id) OR (level = 'system' AND scope_id IS NULL)
--    ORDER BY CASE level WHEN 'user' THEN 1 WHEN 'application' THEN 2 WHEN 'organization' THEN 3 WHEN 'platform' THEN 4 WHEN 'system' THEN 5 END
--    LIMIT 1;

-- 2. Get all permissions for a user:
--    SELECT * FROM permissions
--    WHERE (level = 'user' AND scope_id = :user_id)
--       OR (level = 'organization' AND scope_id = :org_id)
--       OR (level = 'system' AND scope_id IS NULL);

COMMIT;

-- Create unique index to prevent duplicate permissions (handles NULL scope_id)
CREATE UNIQUE INDEX unique_permission_with_scope 
    ON permissions(level, resource, action, scope_id) 
    WHERE scope_id IS NOT NULL;

CREATE UNIQUE INDEX unique_permission_without_scope 
    ON permissions(level, resource, action) 
    WHERE scope_id IS NULL;
