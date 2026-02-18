-- Granite Extraction API Keys Schema
-- Manages API keys for the Granite extraction service
-- Created: 2026-02-06

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- API Keys table
CREATE TABLE IF NOT EXISTS granite_api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    api_key_hash TEXT NOT NULL,
    api_key_prefix VARCHAR(20) NOT NULL,  -- First 8 chars for display (e.g., "sk-gran-")
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_granite_api_keys_active ON granite_api_keys(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_granite_api_keys_prefix ON granite_api_keys(api_key_prefix);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_granite_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_granite_api_keys_updated_at ON granite_api_keys;
CREATE TRIGGER trigger_granite_api_keys_updated_at
    BEFORE UPDATE ON granite_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_granite_api_keys_updated_at();

-- View for active keys (for syncing to granite-proxy)
CREATE OR REPLACE VIEW granite_api_keys_active AS
SELECT
    id,
    name,
    api_key_prefix,
    created_at,
    last_used_at,
    expires_at,
    metadata
FROM granite_api_keys
WHERE is_active = true
  AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP);

-- Function to verify an API key (for potential direct DB validation)
CREATE OR REPLACE FUNCTION verify_granite_api_key(key_to_verify TEXT)
RETURNS TABLE(
    key_id UUID,
    key_name VARCHAR(255),
    is_valid BOOLEAN
) AS $$
DECLARE
    key_record RECORD;
BEGIN
    FOR key_record IN
        SELECT id, name, api_key_hash
        FROM granite_api_keys
        WHERE is_active = true
          AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
    LOOP
        IF key_record.api_key_hash = crypt(key_to_verify, key_record.api_key_hash) THEN
            -- Update last_used_at
            UPDATE granite_api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE id = key_record.id;
            RETURN QUERY SELECT key_record.id, key_record.name, true;
            RETURN;
        END IF;
    END LOOP;

    RETURN QUERY SELECT NULL::UUID, NULL::VARCHAR(255), false;
END;
$$ LANGUAGE plpgsql;

-- Comment on table
COMMENT ON TABLE granite_api_keys IS 'API keys for authenticating requests to the Granite Extraction service';
