-- ============================================================================
-- Migration: Add Service Organization Accounts
-- ============================================================================
-- Description: Creates organization accounts for internal services (Presenton,
--              Bolt.diy, Brigade, Center-Deep) to enable service-to-service
--              authentication without requiring user context.
--
-- Purpose: Fix 401 errors in image generation API when services use service keys
--          without X-User-ID header. Services now have their own credit balances.
--
-- Author: Backend Authentication Team
-- Created: 2025-11-29
-- Related: IMAGE_GENERATION_AUTH_ROOT_CAUSE_ANALYSIS.md
-- ============================================================================

BEGIN;

-- ============================================================================
-- Step 1: Create Service Organization Records
-- ============================================================================

-- Check if organizations table exists (it should from previous migrations)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organizations') THEN
        RAISE EXCEPTION 'Table organizations does not exist. Run previous migrations first.';
    END IF;
END $$;

-- Insert service organization accounts
-- Each service gets its own org for credit billing and usage tracking
INSERT INTO organizations (
    id,
    name,
    slug,
    description,
    billing_type,
    subscription_tier,
    credit_balance,
    created_at,
    updated_at,
    is_active,
    is_service_account
)
VALUES
    -- Presenton Service Account
    (
        'org_presenton_service',
        'Presenton Service',
        'presenton-service',
        'Internal service account for Presenton AI presentation generation platform',
        'prepaid',
        'managed',
        10000000,  -- 10,000 credits (stored as millicredits)
        NOW(),
        NOW(),
        true,
        true
    ),
    -- Bolt.diy Service Account
    (
        'org_bolt_service',
        'Bolt.diy Service',
        'bolt-diy-service',
        'Internal service account for Bolt.diy AI development environment',
        'prepaid',
        'managed',
        10000000,  -- 10,000 credits (stored as millicredits)
        NOW(),
        NOW(),
        true,
        true
    ),
    -- Brigade Service Account
    (
        'org_brigade_service',
        'Brigade Service',
        'brigade-service',
        'Internal service account for Unicorn Brigade agent platform',
        'prepaid',
        'managed',
        10000000,  -- 10,000 credits (stored as millicredits)
        NOW(),
        NOW(),
        true,
        true
    ),
    -- Center-Deep Service Account
    (
        'org_centerdeep_service',
        'Center-Deep Service',
        'centerdeep-service',
        'Internal service account for Center-Deep AI metasearch engine',
        'prepaid',
        'managed',
        10000000,  -- 10,000 credits (stored as millicredits)
        NOW(),
        NOW(),
        true,
        true
    )
ON CONFLICT (id) DO UPDATE SET
    -- If org already exists, ensure fields are correct
    name = EXCLUDED.name,
    slug = EXCLUDED.slug,
    description = EXCLUDED.description,
    billing_type = EXCLUDED.billing_type,
    subscription_tier = EXCLUDED.subscription_tier,
    is_service_account = EXCLUDED.is_service_account,
    updated_at = NOW();

-- ============================================================================
-- Step 2: Add is_service_account Column (if it doesn't exist)
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
-- Step 3: Create Service Usage Tracking Table
-- ============================================================================

-- Create table to track service credit usage for analytics
CREATE TABLE IF NOT EXISTS service_usage_log (
    id SERIAL PRIMARY KEY,
    service_org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    service_name TEXT NOT NULL,  -- 'presenton-service', 'bolt-diy-service', etc.
    endpoint TEXT NOT NULL,  -- '/api/v1/llm/image/generations', etc.
    credits_used DECIMAL(15,3) NOT NULL,
    model_used TEXT,  -- 'dall-e-3', 'gpt-4', etc.
    user_id TEXT,  -- If X-User-ID header was provided (proxying for user)
    request_metadata JSONB,  -- Additional request details
    created_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_service_usage_service (service_org_id, created_at DESC),
    INDEX idx_service_usage_user (user_id, created_at DESC),
    INDEX idx_service_usage_endpoint (endpoint, created_at DESC)
);

COMMENT ON TABLE service_usage_log IS
'Tracks credit usage by internal service accounts for analytics and billing';

COMMENT ON COLUMN service_usage_log.service_org_id IS
'Organization ID of the service (org_presenton_service, etc)';

COMMENT ON COLUMN service_usage_log.user_id IS
'User ID if service was proxying for a user (from X-User-ID header), NULL for service-initiated requests';

COMMENT ON COLUMN service_usage_log.request_metadata IS
'JSON object with request details: {prompt, size, quality, n, etc}';

-- ============================================================================
-- Step 4: Create View for Service Credit Balances
-- ============================================================================

CREATE OR REPLACE VIEW service_credit_balances AS
SELECT
    o.id AS service_org_id,
    o.name AS service_name,
    o.slug,
    o.credit_balance / 1000.0 AS credits_available,  -- Convert millicredits to credits
    COALESCE(SUM(u.credits_used), 0) AS total_credits_used,
    COUNT(u.id) AS total_requests,
    MAX(u.created_at) AS last_used_at
FROM organizations o
LEFT JOIN service_usage_log u ON o.id = u.service_org_id
WHERE o.is_service_account = true
GROUP BY o.id, o.name, o.slug, o.credit_balance;

COMMENT ON VIEW service_credit_balances IS
'Summary view of service account credit balances and usage statistics';

-- ============================================================================
-- Step 5: Create Function to Log Service Usage
-- ============================================================================

CREATE OR REPLACE FUNCTION log_service_usage(
    p_service_org_id TEXT,
    p_service_name TEXT,
    p_endpoint TEXT,
    p_credits_used DECIMAL,
    p_model_used TEXT DEFAULT NULL,
    p_user_id TEXT DEFAULT NULL,
    p_request_metadata JSONB DEFAULT '{}'::jsonb
) RETURNS VOID AS $$
BEGIN
    INSERT INTO service_usage_log (
        service_org_id,
        service_name,
        endpoint,
        credits_used,
        model_used,
        user_id,
        request_metadata
    ) VALUES (
        p_service_org_id,
        p_service_name,
        p_endpoint,
        p_credits_used,
        p_model_used,
        p_user_id,
        p_request_metadata
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION log_service_usage IS
'Utility function to log service credit usage for analytics';

-- ============================================================================
-- Step 6: Create Admin Alerts for Low Service Credit Balances
-- ============================================================================

CREATE TABLE IF NOT EXISTS service_credit_alerts (
    id SERIAL PRIMARY KEY,
    service_org_id TEXT NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL CHECK (alert_type IN ('low_balance', 'exhausted', 'high_usage')),
    threshold_value DECIMAL(15,3),  -- Credits threshold that triggered alert
    current_value DECIMAL(15,3),  -- Actual current value
    alert_message TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    resolved_at TIMESTAMP,
    INDEX idx_service_alerts_unresolved (service_org_id, is_resolved, created_at DESC)
);

COMMENT ON TABLE service_credit_alerts IS
'Stores alerts for service credit issues (low balance, exhaustion, unusual usage)';

-- Create function to check and create alerts
CREATE OR REPLACE FUNCTION check_service_credit_alerts() RETURNS VOID AS $$
DECLARE
    service_record RECORD;
    current_balance DECIMAL;
BEGIN
    -- Check each service organization
    FOR service_record IN
        SELECT id, name, credit_balance / 1000.0 AS credits
        FROM organizations
        WHERE is_service_account = true AND is_active = true
    LOOP
        current_balance := service_record.credits;

        -- Alert if balance < 1,000 credits
        IF current_balance < 1000 THEN
            -- Check if alert already exists and is unresolved
            IF NOT EXISTS (
                SELECT 1 FROM service_credit_alerts
                WHERE service_org_id = service_record.id
                AND alert_type = 'low_balance'
                AND is_resolved = false
            ) THEN
                INSERT INTO service_credit_alerts (
                    service_org_id,
                    alert_type,
                    threshold_value,
                    current_value,
                    alert_message
                ) VALUES (
                    service_record.id,
                    'low_balance',
                    1000,
                    current_balance,
                    format('Service %s has low credit balance: %.2f credits remaining', service_record.name, current_balance)
                );
            END IF;
        END IF;

        -- Alert if balance exhausted (< 100 credits)
        IF current_balance < 100 THEN
            IF NOT EXISTS (
                SELECT 1 FROM service_credit_alerts
                WHERE service_org_id = service_record.id
                AND alert_type = 'exhausted'
                AND is_resolved = false
            ) THEN
                INSERT INTO service_credit_alerts (
                    service_org_id,
                    alert_type,
                    threshold_value,
                    current_value,
                    alert_message
                ) VALUES (
                    service_record.id,
                    'exhausted',
                    100,
                    current_balance,
                    format('URGENT: Service %s credit balance exhausted: %.2f credits remaining', service_record.name, current_balance)
                );
            END IF;
        END IF;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION check_service_credit_alerts IS
'Checks service credit balances and creates alerts if thresholds are breached';

-- ============================================================================
-- Step 7: Grant Permissions
-- ============================================================================

-- Grant read access to service tables for app users
GRANT SELECT ON organizations TO unicorn;
GRANT SELECT ON service_usage_log TO unicorn;
GRANT SELECT ON service_credit_balances TO unicorn;
GRANT SELECT ON service_credit_alerts TO unicorn;

-- Grant write access for credit deduction operations
GRANT INSERT, UPDATE ON service_usage_log TO unicorn;
GRANT UPDATE ON organizations TO unicorn;  -- For credit_balance updates
GRANT INSERT, UPDATE ON service_credit_alerts TO unicorn;

-- ============================================================================
-- Step 8: Verification Queries
-- ============================================================================

-- Verify service organizations were created
DO $$
DECLARE
    org_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO org_count
    FROM organizations
    WHERE is_service_account = true;

    IF org_count < 4 THEN
        RAISE WARNING 'Expected 4 service organizations, found %', org_count;
    ELSE
        RAISE NOTICE 'Successfully created % service organizations', org_count;
    END IF;
END $$;

-- Display service credit balances
SELECT
    service_name,
    credits_available || ' credits' AS balance,
    total_credits_used || ' credits' AS used,
    total_requests AS requests
FROM service_credit_balances
ORDER BY service_name;

COMMIT;

-- ============================================================================
-- Rollback Script (for testing or reverting)
-- ============================================================================
-- Uncomment and run if you need to rollback this migration:
--
-- BEGIN;
-- DROP VIEW IF EXISTS service_credit_balances;
-- DROP FUNCTION IF EXISTS check_service_credit_alerts();
-- DROP FUNCTION IF EXISTS log_service_usage(TEXT, TEXT, TEXT, DECIMAL, TEXT, TEXT, JSONB);
-- DROP TABLE IF EXISTS service_credit_alerts;
-- DROP TABLE IF EXISTS service_usage_log;
-- DELETE FROM organizations WHERE is_service_account = true;
-- ALTER TABLE organizations DROP COLUMN IF EXISTS is_service_account;
-- COMMIT;
