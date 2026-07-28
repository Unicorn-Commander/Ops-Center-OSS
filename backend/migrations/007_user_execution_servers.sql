-- Migration: Create user execution servers table
-- Description: Store user-configured execution environments for code execution
-- Date: 2025-10-20

CREATE TABLE IF NOT EXISTS user_execution_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    server_type VARCHAR(50) NOT NULL CHECK (server_type IN ('ssh', 'local', 'docker', 'kubernetes')),
    connection_config JSONB NOT NULL,
    workspace_path VARCHAR(500),
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMP,
    test_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Index for user lookups
CREATE INDEX IF NOT EXISTS idx_execution_servers_user_id ON user_execution_servers(user_id);
CREATE INDEX IF NOT EXISTS idx_execution_servers_default ON user_execution_servers(user_id, is_default) WHERE is_default = true;

-- Trigger to ensure only one default per user
CREATE OR REPLACE FUNCTION ensure_single_default_execution_server()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = true THEN
        UPDATE user_execution_servers
        SET is_default = false
        WHERE user_id = NEW.user_id AND id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_single_default_execution_server
    BEFORE INSERT OR UPDATE ON user_execution_servers
    FOR EACH ROW
    WHEN (NEW.is_default = true)
    EXECUTE FUNCTION ensure_single_default_execution_server();

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_execution_server_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_execution_server_timestamp
    BEFORE UPDATE ON user_execution_servers
    FOR EACH ROW
    EXECUTE FUNCTION update_execution_server_timestamp();

-- Comments
COMMENT ON TABLE user_execution_servers IS 'User-configured execution environments for code execution via Brigade';
COMMENT ON COLUMN user_execution_servers.connection_config IS 'JSONB config: {host, port, username, key_encrypted, etc.}';
COMMENT ON COLUMN user_execution_servers.server_type IS 'Execution environment: ssh, local, docker, kubernetes';
COMMENT ON COLUMN user_execution_servers.workspace_path IS 'Default working directory for code execution';
