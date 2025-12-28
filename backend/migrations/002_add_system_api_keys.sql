-- ============================================================================
-- System API Key Storage Migration
-- Epic 3.1 Phase 2: Enable system provider key management
--
-- This migration adds columns to llm_providers table for storing
-- system-level API keys (admin-configured keys for shared use).
--
-- This complements the existing user_api_keys table (BYOK) by allowing
-- system administrators to configure provider keys that all users can use.
--
-- Author: Backend API Developer
-- Date: October 27, 2025
-- ============================================================================

-- ============================================================================
-- Add System API Key Columns to llm_providers
-- ============================================================================

-- Add encrypted_api_key column for Fernet-encrypted system API keys
ALTER TABLE llm_providers
ADD COLUMN IF NOT EXISTS encrypted_api_key TEXT NULL;

-- Add api_key_source column to track where the key comes from
-- Values: 'environment', 'database', 'hybrid'
-- - environment: Key loaded from environment variable only
-- - database: Key loaded from encrypted_api_key column
-- - hybrid: Prefers database, falls back to environment
ALTER TABLE llm_providers
ADD COLUMN IF NOT EXISTS api_key_source VARCHAR(50) DEFAULT 'environment';

-- Add timestamp for when API key was last updated
ALTER TABLE llm_providers
ADD COLUMN IF NOT EXISTS api_key_updated_at TIMESTAMP NULL;

-- Add timestamp for when API key was last successfully tested
ALTER TABLE llm_providers
ADD COLUMN IF NOT EXISTS api_key_last_tested TIMESTAMP NULL;

-- Add status of last API key test
-- Values: 'valid', 'invalid', 'untested', 'error'
ALTER TABLE llm_providers
ADD COLUMN IF NOT EXISTS api_key_test_status VARCHAR(20) NULL;

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Index for quick lookups by API key source
CREATE INDEX IF NOT EXISTS idx_llm_providers_api_key_source
ON llm_providers(api_key_source) WHERE enabled = TRUE;

-- Index for finding providers with database keys
CREATE INDEX IF NOT EXISTS idx_llm_providers_has_db_key
ON llm_providers(id) WHERE encrypted_api_key IS NOT NULL;

-- ============================================================================
-- Column Comments for Documentation
-- ============================================================================

COMMENT ON COLUMN llm_providers.encrypted_api_key IS
'Fernet-encrypted system API key for this provider. Uses BYOK_ENCRYPTION_KEY for encryption. NULL means no system key configured.';

COMMENT ON COLUMN llm_providers.api_key_source IS
'Source priority for API key: environment (env var only), database (encrypted_api_key only), hybrid (database preferred, env fallback)';

COMMENT ON COLUMN llm_providers.api_key_updated_at IS
'Timestamp when encrypted_api_key was last updated by an administrator';

COMMENT ON COLUMN llm_providers.api_key_last_tested IS
'Timestamp when the API key was last successfully validated against provider API';

COMMENT ON COLUMN llm_providers.api_key_test_status IS
'Result of last API key validation test: valid, invalid, untested, error';

-- ============================================================================
-- Update Existing Rows
-- ============================================================================

-- Set default api_key_source to 'environment' for all existing providers
-- This maintains backward compatibility (keys will continue to come from env vars)
UPDATE llm_providers
SET api_key_source = 'environment',
    api_key_test_status = 'untested'
WHERE api_key_source IS NULL;

-- ============================================================================
-- Verification Query
-- ============================================================================

-- Display migration summary
DO $$
DECLARE
    column_count INTEGER;
    row_count INTEGER;
BEGIN
    -- Check if all columns were added
    SELECT COUNT(*) INTO column_count
    FROM information_schema.columns
    WHERE table_name = 'llm_providers'
    AND column_name IN (
        'encrypted_api_key',
        'api_key_source',
        'api_key_updated_at',
        'api_key_last_tested',
        'api_key_test_status'
    );

    -- Get total provider count
    SELECT COUNT(*) INTO row_count FROM llm_providers;

    RAISE NOTICE 'Migration 002: Added % columns to llm_providers', column_count;
    RAISE NOTICE 'Updated % existing provider rows', row_count;
END;
$$;

-- Display column status
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'llm_providers'
AND column_name IN (
    'encrypted_api_key',
    'api_key_source',
    'api_key_updated_at',
    'api_key_last_tested',
    'api_key_test_status'
)
ORDER BY ordinal_position;

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Next steps:
-- 1. Update backend API to use new columns
-- 2. Create admin UI for managing system API keys
-- 3. Implement key rotation strategy
-- 4. Add health checks that test system keys
-- ============================================================================
