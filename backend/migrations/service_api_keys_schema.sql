-- ============================================================================
-- Service API Keys Management Schema
-- ============================================================================
-- Author: Backend Authentication Team
-- Created: 2026-01-27
-- Description: Database-driven service API key management for internal services
--              (Brigade, Bolt.diy, Presenton, Center-Deep, PartnerPulse)
--
-- This replaces the hardcoded service keys in litellm_api.py with a proper
-- database-driven approach supporting:
-- - Secure key storage (bcrypt hashed + optionally Fernet encrypted)
-- - Permission scopes per service
-- - Usage tracking via last_used_at
-- - Key rotation support
-- - Audit trail via metadata
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create the service_api_keys table
-- ============================================================================

CREATE TABLE IF NOT EXISTS service_api_keys (
    -- Primary identifier
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Service identification
    service_name VARCHAR(100) NOT NULL UNIQUE,  -- e.g., "brigade", "bolt-diy"
    display_name VARCHAR(255) NOT NULL,          -- e.g., "Unicorn Brigade"

    -- Key storage (hashed for verification, optionally encrypted for admin viewing)
    api_key_hash TEXT NOT NULL,                  -- bcrypt hash for verification
    api_key_prefix VARCHAR(30) NOT NULL,         -- e.g., "sk-brigade-xxxx" for display
    encrypted_key TEXT,                          -- Fernet encrypted full key (optional, for admin viewing/rotation)

    -- Organization association (for billing and credit tracking)
    org_id UUID REFERENCES organizations(id) ON DELETE SET NULL,

    -- Permission scopes (JSONB array for flexibility)
    scopes JSONB NOT NULL DEFAULT '["llm:chat"]'::jsonb,

    -- Description and documentation
    description TEXT,

    -- Status and lifecycle
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,

    -- Audit fields
    created_by VARCHAR(255),                     -- Admin username who created the key

    -- Additional configuration (rate limits, custom settings, etc.)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add table comment
COMMENT ON TABLE service_api_keys IS
'Stores API keys for internal services (Brigade, Bolt.diy, Presenton, etc.) with secure hashing and organization association for billing';

-- ============================================================================
-- Step 2: Create indexes for performance
-- ============================================================================

-- Unique index on service_name (already implied by UNIQUE constraint, but explicit for clarity)
CREATE UNIQUE INDEX IF NOT EXISTS idx_service_api_keys_service_name
ON service_api_keys(service_name);

-- Index on api_key_prefix for fast lookups during authentication
CREATE INDEX IF NOT EXISTS idx_service_api_keys_prefix
ON service_api_keys(api_key_prefix);

-- Index on is_active for filtering active keys
CREATE INDEX IF NOT EXISTS idx_service_api_keys_active
ON service_api_keys(is_active) WHERE is_active = true;

-- Index on org_id for billing queries
CREATE INDEX IF NOT EXISTS idx_service_api_keys_org_id
ON service_api_keys(org_id) WHERE org_id IS NOT NULL;

-- Composite index for common query pattern (active + service lookup)
CREATE INDEX IF NOT EXISTS idx_service_api_keys_active_service
ON service_api_keys(service_name, is_active);

-- ============================================================================
-- Step 3: Add column comments for documentation
-- ============================================================================

COMMENT ON COLUMN service_api_keys.id IS
'Unique identifier for the service API key record';

COMMENT ON COLUMN service_api_keys.service_name IS
'Unique service identifier used in API calls (e.g., "brigade", "bolt-diy", "presenton")';

COMMENT ON COLUMN service_api_keys.display_name IS
'Human-readable service name for admin UI (e.g., "Unicorn Brigade")';

COMMENT ON COLUMN service_api_keys.api_key_hash IS
'bcrypt hash of the full API key for secure verification during authentication';

COMMENT ON COLUMN service_api_keys.api_key_prefix IS
'First 20 characters of the API key for display/identification (e.g., "sk-brigade-service-k...")';

COMMENT ON COLUMN service_api_keys.encrypted_key IS
'Fernet-encrypted full API key. Uses BYOK_ENCRYPTION_KEY. Optional - used for admin viewing and key rotation';

COMMENT ON COLUMN service_api_keys.org_id IS
'Associated organization UUID for billing and credit tracking. References organizations(id)';

COMMENT ON COLUMN service_api_keys.scopes IS
'JSONB array of permission scopes: ["llm:chat", "llm:image", "llm:embeddings", "llm:audio"]';

COMMENT ON COLUMN service_api_keys.description IS
'Description of the service and its purpose';

COMMENT ON COLUMN service_api_keys.is_active IS
'Whether the API key is currently active. Set to false to disable without deleting';

COMMENT ON COLUMN service_api_keys.created_at IS
'Timestamp when the key was created';

COMMENT ON COLUMN service_api_keys.updated_at IS
'Timestamp when the key was last updated';

COMMENT ON COLUMN service_api_keys.last_used_at IS
'Timestamp when the key was last used for an API call';

COMMENT ON COLUMN service_api_keys.created_by IS
'Username or ID of the admin who created this key';

COMMENT ON COLUMN service_api_keys.metadata IS
'Additional configuration as JSONB (rate_limit, custom_settings, etc.)';

-- ============================================================================
-- Step 4: Create trigger for updated_at
-- ============================================================================

-- Create or replace the trigger function
CREATE OR REPLACE FUNCTION update_service_api_keys_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS trigger_service_api_keys_updated_at ON service_api_keys;
CREATE TRIGGER trigger_service_api_keys_updated_at
    BEFORE UPDATE ON service_api_keys
    FOR EACH ROW
    EXECUTE FUNCTION update_service_api_keys_updated_at();

-- ============================================================================
-- Step 5: Insert default service keys
-- ============================================================================
-- NOTE: These use placeholder bcrypt hashes. The actual keys are:
-- - brigade: sk-brigade-service-key-2025
-- - bolt-diy: sk-bolt-diy-service-key-2025
-- - presenton: sk-presenton-service-key-2025
-- - centerdeep: sk-centerdeep-service-key-2025
-- - partnerpulse: sk-partnerpulse-service-key-2025
--
-- The bcrypt hashes below are generated for these exact keys.
-- In production, use: SELECT crypt('sk-brigade-service-key-2025', gen_salt('bf'));
--
-- IMPORTANT: org_id values must match the EXISTING organization UUIDs in the database.
-- These are the UUIDs from litellm_api.py service_org_ids mapping:
--   - brigade-service: e9b40f6b-b683-4bcf-b462-9fd526cfbb37
--   - bolt-diy-service: 3766e9ee-7cc1-472f-92ae-afec687f0d74
--   - presenton-service: 13587747-66e6-43df-b21d-4411c7373465
--   - centerdeep-service: 91d3b68e-e4c4-457e-80ce-de6997243c34
--   - partnerpulse-service: 8f5bf9a9-2e7c-4465-93d8-97f18bdac098
-- ============================================================================

-- Enable pgcrypto for bcrypt (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Insert service API keys
INSERT INTO service_api_keys (
    service_name,
    display_name,
    api_key_hash,
    api_key_prefix,
    encrypted_key,
    org_id,
    scopes,
    description,
    is_active,
    created_by,
    metadata
)
VALUES
    -- Brigade Service
    (
        'brigade',
        'Unicorn Brigade',
        crypt('sk-brigade-service-key-2025', gen_salt('bf', 12)),
        'sk-brigade-service-...',
        NULL,  -- Will be populated when key is rotated
        'e9b40f6b-b683-4bcf-b462-9fd526cfbb37'::uuid,
        '["llm:chat", "llm:embeddings"]'::jsonb,
        'Internal service account for Unicorn Brigade agent platform. Provides access to LLM chat and embeddings APIs for agent execution.',
        true,
        'system',
        '{"rate_limit": {"requests_per_minute": 1000, "tokens_per_minute": 500000}, "service_type": "agent_platform", "priority": "high"}'::jsonb
    ),

    -- Bolt.diy Service
    (
        'bolt-diy',
        'Bolt.diy',
        crypt('sk-bolt-diy-service-key-2025', gen_salt('bf', 12)),
        'sk-bolt-diy-service-...',
        NULL,
        '3766e9ee-7cc1-472f-92ae-afec687f0d74'::uuid,
        '["llm:chat", "llm:image"]'::jsonb,
        'Internal service account for Bolt.diy AI development environment. Provides access to LLM chat and image generation APIs.',
        true,
        'system',
        '{"rate_limit": {"requests_per_minute": 500, "tokens_per_minute": 250000}, "service_type": "development_environment", "priority": "high"}'::jsonb
    ),

    -- Presenton Service
    (
        'presenton',
        'Presenton',
        crypt('sk-presenton-service-key-2025', gen_salt('bf', 12)),
        'sk-presenton-service-...',
        NULL,
        '13587747-66e6-43df-b21d-4411c7373465'::uuid,
        '["llm:chat", "llm:image"]'::jsonb,
        'Internal service account for Presenton AI presentation generation platform. Provides access to LLM chat and image generation APIs for slide creation.',
        true,
        'system',
        '{"rate_limit": {"requests_per_minute": 300, "tokens_per_minute": 150000}, "service_type": "presentation_platform", "priority": "medium"}'::jsonb
    ),

    -- Center-Deep Service
    (
        'centerdeep',
        'Center-Deep Pro',
        crypt('sk-centerdeep-service-key-2025', gen_salt('bf', 12)),
        'sk-centerdeep-service-...',
        NULL,
        '91d3b68e-e4c4-457e-80ce-de6997243c34'::uuid,
        '["llm:chat", "llm:embeddings"]'::jsonb,
        'Internal service account for Center-Deep AI metasearch engine. Provides access to LLM chat and embeddings APIs for search enhancement.',
        true,
        'system',
        '{"rate_limit": {"requests_per_minute": 600, "tokens_per_minute": 300000}, "service_type": "metasearch_engine", "priority": "high"}'::jsonb
    ),

    -- PartnerPulse Service
    (
        'partnerpulse',
        'PartnerPulse',
        crypt('sk-partnerpulse-service-key-2025', gen_salt('bf', 12)),
        'sk-partnerpulse-service-...',
        NULL,
        '8f5bf9a9-2e7c-4465-93d8-97f18bdac098'::uuid,
        '["llm:chat"]'::jsonb,
        'Internal service account for PartnerPulse partner management platform. Provides access to LLM chat API for partner analytics and insights.',
        true,
        'system',
        '{"rate_limit": {"requests_per_minute": 200, "tokens_per_minute": 100000}, "service_type": "partner_management", "priority": "medium"}'::jsonb
    )
ON CONFLICT (service_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    api_key_hash = EXCLUDED.api_key_hash,
    api_key_prefix = EXCLUDED.api_key_prefix,
    org_id = EXCLUDED.org_id,
    scopes = EXCLUDED.scopes,
    description = EXCLUDED.description,
    metadata = EXCLUDED.metadata,
    updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- Step 6: Create view for service key status monitoring
-- ============================================================================

CREATE OR REPLACE VIEW service_api_keys_status AS
SELECT
    sak.id,
    sak.service_name,
    sak.display_name,
    sak.api_key_prefix,
    sak.is_active,
    sak.scopes,
    sak.last_used_at,
    sak.created_at,
    sak.updated_at,
    o.name AS org_name,
    o.display_name AS org_display_name,
    COALESCE(oc.credit_balance / 1000.0, 0) AS credits_available,
    CASE
        WHEN sak.last_used_at IS NULL THEN 'never_used'
        WHEN sak.last_used_at > NOW() - INTERVAL '1 hour' THEN 'active'
        WHEN sak.last_used_at > NOW() - INTERVAL '24 hours' THEN 'recent'
        WHEN sak.last_used_at > NOW() - INTERVAL '7 days' THEN 'stale'
        ELSE 'inactive'
    END AS usage_status,
    sak.metadata
FROM service_api_keys sak
LEFT JOIN organizations o ON sak.org_id = o.id
LEFT JOIN organization_credits oc ON o.id = oc.org_id;

COMMENT ON VIEW service_api_keys_status IS
'Provides service API key status with organization and credit information for admin dashboard';

-- ============================================================================
-- Step 7: Create helper function for key verification
-- ============================================================================

CREATE OR REPLACE FUNCTION verify_service_api_key(
    p_api_key TEXT,
    p_required_scope TEXT DEFAULT NULL
)
RETURNS TABLE (
    service_name VARCHAR(100),
    org_id UUID,
    scopes JSONB,
    is_valid BOOLEAN,
    has_scope BOOLEAN
) AS $$
DECLARE
    v_service_name VARCHAR(100);
    v_org_id UUID;
    v_scopes JSONB;
    v_stored_hash TEXT;
    v_is_active BOOLEAN;
BEGIN
    -- Look up the service key by checking the hash
    SELECT
        sak.service_name,
        sak.org_id,
        sak.scopes,
        sak.api_key_hash,
        sak.is_active
    INTO
        v_service_name,
        v_org_id,
        v_scopes,
        v_stored_hash,
        v_is_active
    FROM service_api_keys sak
    WHERE sak.api_key_hash = crypt(p_api_key, sak.api_key_hash)
      AND sak.is_active = true
    LIMIT 1;

    -- If found and active, update last_used_at and return
    IF v_service_name IS NOT NULL AND v_is_active THEN
        -- Update last_used_at (async in production, sync here for simplicity)
        UPDATE service_api_keys
        SET last_used_at = CURRENT_TIMESTAMP
        WHERE service_api_keys.service_name = v_service_name;

        RETURN QUERY SELECT
            v_service_name,
            v_org_id,
            v_scopes,
            true AS is_valid,
            CASE
                WHEN p_required_scope IS NULL THEN true
                WHEN v_scopes ? p_required_scope THEN true
                ELSE false
            END AS has_scope;
    ELSE
        -- Return not found
        RETURN QUERY SELECT
            NULL::VARCHAR(100) AS service_name,
            NULL::UUID AS org_id,
            NULL::JSONB AS scopes,
            false AS is_valid,
            false AS has_scope;
    END IF;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION verify_service_api_key IS
'Verifies a service API key and optionally checks for a required scope. Returns service info if valid.';

-- ============================================================================
-- Step 8: Verification
-- ============================================================================

DO $$
DECLARE
    key_count INTEGER;
    active_count INTEGER;
    org_linked INTEGER;
BEGIN
    SELECT COUNT(*) INTO key_count FROM service_api_keys;
    SELECT COUNT(*) INTO active_count FROM service_api_keys WHERE is_active = true;
    SELECT COUNT(*) INTO org_linked FROM service_api_keys WHERE org_id IS NOT NULL;

    RAISE NOTICE '============================================';
    RAISE NOTICE 'Service API Keys Migration Summary';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Total service keys created: %', key_count;
    RAISE NOTICE 'Active service keys: %', active_count;
    RAISE NOTICE 'Keys linked to organizations: %', org_linked;
    RAISE NOTICE '============================================';

    IF key_count >= 5 AND active_count >= 5 AND org_linked >= 5 THEN
        RAISE NOTICE '[ OK ] Migration completed successfully';
    ELSE
        RAISE WARNING '[ WARN ] Expected 5 service keys with org links';
    END IF;
END $$;

-- Display created keys
SELECT
    service_name,
    display_name,
    api_key_prefix,
    is_active,
    scopes,
    org_id,
    created_at
FROM service_api_keys
ORDER BY service_name;

COMMIT;

-- ============================================================================
-- Usage Examples
-- ============================================================================
--
-- 1. Verify a service API key:
--    SELECT * FROM verify_service_api_key('sk-brigade-service-key-2025', 'llm:chat');
--
-- 2. Check service key status:
--    SELECT * FROM service_api_keys_status;
--
-- 3. Rotate a service key (generate new hash):
--    UPDATE service_api_keys
--    SET api_key_hash = crypt('sk-brigade-new-key-2026', gen_salt('bf', 12)),
--        api_key_prefix = 'sk-brigade-new-key-...',
--        updated_at = NOW()
--    WHERE service_name = 'brigade';
--
-- 4. Disable a service temporarily:
--    UPDATE service_api_keys SET is_active = false WHERE service_name = 'partnerpulse';
--
-- 5. Add a new scope to a service:
--    UPDATE service_api_keys
--    SET scopes = scopes || '["llm:audio"]'::jsonb
--    WHERE service_name = 'brigade';
--
-- ============================================================================
