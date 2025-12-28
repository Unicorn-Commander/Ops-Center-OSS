-- Migration: Create BYOK keys table
-- Description: Table for storing encrypted user API keys (BYOK - Bring Your Own Key)
-- Date: 2025-10-17

CREATE TABLE IF NOT EXISTS byok_keys (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    key_name VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_tested_at TIMESTAMP,
    is_valid BOOLEAN,
    UNIQUE(user_id, key_name)
);

-- Create index for faster user lookups
CREATE INDEX IF NOT EXISTS idx_byok_keys_user_id ON byok_keys(user_id);
CREATE INDEX IF NOT EXISTS idx_byok_keys_provider ON byok_keys(provider);

-- Add comment for documentation
COMMENT ON TABLE byok_keys IS 'Encrypted API keys for BYOK (Bring Your Own Key) feature';
COMMENT ON COLUMN byok_keys.encrypted_key IS 'Fernet-encrypted API key';
COMMENT ON COLUMN byok_keys.provider IS 'API provider: openai, anthropic, huggingface, cohere, replicate, custom';
