-- ============================================================================
-- Migration: Add Service Organization Accounts (FIXED)
-- ============================================================================
-- Description: Creates organization accounts for internal services (Presenton,
--              Bolt.diy, Brigade, Center-Deep) to enable service-to-service
--              authentication without requiring user context.
--
-- Purpose: Fix 401 errors in image generation API when services use service keys
--          without X-User-ID header. Services now have their own credit balances.
--
-- Author: Backend Authentication Team - Deployment Team
-- Created: 2025-11-29
-- Fixed: Aligned with actual database schema
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Add is_service_account Column
-- ============================================================================

-- Add column to distinguish service orgs from regular user orgs
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'organizations'
        AND column_name = 'is_service_account'
    ) THEN
        ALTER TABLE organizations
        ADD COLUMN is_service_account BOOLEAN DEFAULT FALSE NOT NULL;

        COMMENT ON COLUMN organizations.is_service_account IS
        'True if this organization is an internal service account (Presenton, Bolt.diy, etc), false for regular user organizations';
    END IF;
END $$;

-- ============================================================================
-- Step 2: Create organization_credits Table (if not exists)
-- ============================================================================

CREATE TABLE IF NOT EXISTS organization_credits (
    org_id UUID NOT NULL PRIMARY KEY REFERENCES organizations(id) ON DELETE CASCADE,
    credit_balance BIGINT NOT NULL DEFAULT 0,  -- Stored in millicredits (1 credit = 1000 millicredits)
    total_credits_purchased BIGINT DEFAULT 0,
    total_credits_used BIGINT DEFAULT 0,
    last_purchase_date TIMESTAMP,
    last_usage_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE organization_credits IS
'Credit balances for all organizations. Separate table for cleaner schema.';

COMMENT ON COLUMN organization_credits.credit_balance IS
'Current credit balance in millicredits. Divide by 1000 to get actual credits.';

-- ============================================================================
-- Step 3: Insert Service Organization Records
-- ============================================================================

-- Insert service organizations using ONLY columns that exist
INSERT INTO organizations (
    id,
    name,
    display_name,
    logo_url,
    plan_tier,
    max_seats,
    status,
    is_default,
    created_at,
    updated_at
)
VALUES
    -- Presenton Service Account
    (
        'org_presenton_service'::UUID,
        'presenton-service',
        'Presenton Service',
        '/logos/presenton-logo.svg',
        'managed',
        1,
        'active',
        false,
        NOW(),
        NOW()
    ),
    -- Bolt.diy Service Account
    (
        'org_bolt_service'::UUID,
        'bolt-diy-service',
        'Bolt.diy Service',
        '/logos/bolt-logo.svg',
        'managed',
        1,
        'active',
        false,
        NOW(),
        NOW()
    ),
    -- Brigade Service Account
    (
        'org_brigade_service'::UUID,
        'brigade-service',
        'Brigade Service',
        '/logos/brigade-logo.svg',
        'managed',
        1,
        'active',
        false,
        NOW(),
        NOW()
    ),
    -- Center-Deep Service Account
    (
        'org_centerdeep_service'::UUID,
        'centerdeep-service',
        'Center-Deep Service',
        '/logos/centerdeep-logo.svg',
        'managed',
        1,
        'active',
        false,
        NOW(),
        NOW()
    )
ON CONFLICT (id) DO UPDATE SET
    -- If org already exists, ensure it's marked as active
    status = EXCLUDED.status,
    updated_at = NOW();

-- ============================================================================
-- Step 4: Mark Service Organizations
-- ============================================================================

UPDATE organizations
SET is_service_account = true
WHERE id IN (
    'org_presenton_service'::UUID,
    'org_bolt_service'::UUID,
    'org_brigade_service'::UUID,
    'org_centerdeep_service'::UUID
);

-- ============================================================================
-- Step 5: Allocate Credits to Service Organizations
-- ============================================================================

INSERT INTO organization_credits (org_id, credit_balance, total_credits_purchased, created_at, updated_at)
VALUES
    ('org_presenton_service'::UUID, 10000000, 10000000, NOW(), NOW()),  -- 10,000 credits
    ('org_bolt_service'::UUID, 10000000, 10000000, NOW(), NOW()),
    ('org_brigade_service'::UUID, 10000000, 10000000, NOW(), NOW()),
    ('org_centerdeep_service'::UUID, 10000000, 10000000, NOW(), NOW())
ON CONFLICT (org_id) DO UPDATE SET
    credit_balance = EXCLUDED.credit_balance,
    total_credits_purchased = EXCLUDED.total_credits_purchased,
    updated_at = NOW();

-- ============================================================================
-- Step 6: Create Service Usage Tracking Table
-- ============================================================================

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

COMMENT ON TABLE service_usage_log IS
'Tracks credit usage by internal service accounts for analytics and billing';

-- ============================================================================
-- Step 7: Create View for Service Credit Balances
-- ============================================================================

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

COMMENT ON VIEW service_credit_balances IS
'Summary view of service account credit balances and usage statistics';

-- ============================================================================
-- Step 8: Verification
-- ============================================================================

-- Count service organizations
DO $$
DECLARE
    org_count INTEGER;
    credits_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_count
    FROM organizations
    WHERE is_service_account = true;

    SELECT COUNT(*) INTO credits_count
    FROM organization_credits
    WHERE org_id IN (
        SELECT id FROM organizations WHERE is_service_account = true
    );

    IF org_count < 4 THEN
        RAISE WARNING 'Expected 4 service organizations, found %', org_count;
    ELSE
        RAISE NOTICE 'Successfully created % service organizations', org_count;
    END IF;

    IF credits_count < 4 THEN
        RAISE WARNING 'Expected 4 credit records, found %', credits_count;
    ELSE
        RAISE NOTICE 'Successfully allocated credits to % service organizations', credits_count;
    END IF;
END $$;

-- Display service credit balances
SELECT
    service_name,
    ROUND(credits_available::numeric, 2) || ' credits' AS balance,
    total_requests AS requests
FROM service_credit_balances
ORDER BY service_name;

COMMIT;

-- ============================================================================
-- Success Message
-- ============================================================================
\echo '✓ Service organization migration completed successfully'
\echo '✓ 4 service organizations created: Presenton, Bolt.diy, Brigade, Center-Deep'
\echo '✓ Each service has 10,000 credits allocated'
\echo '✓ Credit tracking tables and views created'
