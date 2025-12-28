-- ============================================================================
-- Migration: Add Service Organization Accounts (FINAL)
-- ============================================================================
-- Author: Backend Authentication Team - Deployment Team
-- Created: 2025-11-29
-- ============================================================================

BEGIN;

-- Step 1: Add is_service_account column
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS is_service_account BOOLEAN DEFAULT FALSE NOT NULL;

-- Step 2: Create organization_credits table
CREATE TABLE IF NOT EXISTS organization_credits (
    org_id UUID NOT NULL PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
    credit_balance BIGINT NOT NULL DEFAULT 0,
    total_credits_purchased BIGINT DEFAULT 0,
    total_credits_used BIGINT DEFAULT 0,
    last_purchase_date TIMESTAMP,
    last_usage_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Step 3: Insert service organizations with generated UUIDs
WITH service_orgs AS (
    SELECT
        gen_random_uuid() AS id,
        'presenton-service' AS name,
        'Presenton Service' AS display_name,
        '/logos/presenton-logo.svg' AS logo_url
    UNION ALL SELECT
        gen_random_uuid(),
        'bolt-diy-service',
        'Bolt.diy Service',
        '/logos/bolt-logo.svg'
    UNION ALL SELECT
        gen_random_uuid(),
        'brigade-service',
        'Brigade Service',
        '/logos/brigade-logo.svg'
    UNION ALL SELECT
        gen_random_uuid(),
        'centerdeep-service',
        'Center-Deep Service',
        '/logos/centerdeep-logo.svg'
)
INSERT INTO organizations (id, name, display_name, logo_url, plan_tier, max_seats, status, is_default, is_service_account, created_at, updated_at)
SELECT id, name, display_name, logo_url, 'managed', 1, 'active', false, true, NOW(), NOW()
FROM service_orgs
ON CONFLICT (name) DO UPDATE SET
    is_service_account = true,
    status = 'active',
    updated_at = NOW();

-- Step 4: Allocate credits (10,000 credits each)
INSERT INTO organization_credits (org_id, credit_balance, total_credits_purchased, created_at, updated_at)
SELECT id, 10000000, 10000000, NOW(), NOW()
FROM organizations
WHERE is_service_account = true
ON CONFLICT (org_id) DO UPDATE SET
    credit_balance = GREATEST(organization_credits.credit_balance, EXCLUDED.credit_balance),
    updated_at = NOW();

-- Step 5: Create service usage log table
CREATE TABLE IF NOT EXISTS service_usage_log (
    id SERIAL PRIMARY KEY,
    service_org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    credits_used BIGINT NOT NULL,
    model_used TEXT,
    user_id TEXT,
    request_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_service_usage_service ON service_usage_log(service_org_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service_usage_user ON service_usage_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_service_usage_endpoint ON service_usage_log(endpoint, created_at DESC);

-- Step 6: Create service credit balances view
CREATE OR REPLACE VIEW service_credit_balances AS
SELECT
    o.id AS service_org_id,
    o.display_name AS service_name,
    o.name AS service_slug,
    COALESCE(c.credit_balance / 1000.0, 0) AS credits_available,
    COALESCE(SUM(u.credits_used) / 1000.0, 0) AS total_credits_used,
    COUNT(u.id) AS total_requests,
    MAX(u.created_at) AS last_used_at
FROM organizations o
LEFT JOIN organization_credits c ON o.id = c.org_id
LEFT JOIN service_usage_log u ON o.id = u.service_org_id
WHERE o.is_service_account = true
GROUP BY o.id, o.display_name, o.name, c.credit_balance;

-- Step 7: Verification
DO $$
DECLARE
    org_count INTEGER;
    credits_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_count FROM organizations WHERE is_service_account = true;
    SELECT COUNT(*) INTO credits_count FROM organization_credits WHERE org_id IN (SELECT id FROM organizations WHERE is_service_account = true);

    RAISE NOTICE 'Service organizations created: %', org_count;
    RAISE NOTICE 'Credit records created: %', credits_count;

    IF org_count >= 4 AND credits_count >= 4 THEN
        RAISE NOTICE '✓ Migration successful';
    ELSE
        RAISE WARNING '⚠ Expected at least 4 service organizations and 4 credit records';
    END IF;
END $$;

COMMIT;
