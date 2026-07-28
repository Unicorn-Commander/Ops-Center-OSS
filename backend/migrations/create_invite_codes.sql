-- ============================================================
-- INVITE CODE SYSTEM MIGRATION
-- ============================================================
-- Creates invite code system for VIP Founder tier and others
-- Migration Date: 2025-11-12
-- ============================================================

BEGIN;

-- ============================================================
-- STEP 1: Create invite_codes table
-- ============================================================
CREATE TABLE IF NOT EXISTS invite_codes (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    tier_code VARCHAR(50) NOT NULL REFERENCES subscription_tiers(tier_code),
    max_uses INTEGER,  -- NULL = unlimited
    current_uses INTEGER DEFAULT 0 NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,  -- NULL = never expires
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_by VARCHAR(255),  -- Admin who created it
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    -- Constraints
    CONSTRAINT valid_max_uses CHECK (max_uses IS NULL OR max_uses > 0),
    CONSTRAINT valid_current_uses CHECK (current_uses >= 0),
    CONSTRAINT valid_usage CHECK (max_uses IS NULL OR current_uses <= max_uses)
);

-- ============================================================
-- STEP 2: Create invite_code_redemptions table
-- ============================================================
CREATE TABLE IF NOT EXISTS invite_code_redemptions (
    id SERIAL PRIMARY KEY,
    invite_code_id INTEGER NOT NULL REFERENCES invite_codes(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    user_email VARCHAR(255),  -- Email for reference
    redeemed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Prevent same user from redeeming same code twice
    CONSTRAINT unique_user_code UNIQUE (invite_code_id, user_id)
);

-- ============================================================
-- STEP 3: Create indexes for performance
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_invite_codes_code ON invite_codes(code);
CREATE INDEX IF NOT EXISTS idx_invite_codes_tier ON invite_codes(tier_code);
CREATE INDEX IF NOT EXISTS idx_invite_codes_active ON invite_codes(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_invite_codes_expires ON invite_codes(expires_at) WHERE expires_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_redemptions_code ON invite_code_redemptions(invite_code_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_user ON invite_code_redemptions(user_id);
CREATE INDEX IF NOT EXISTS idx_redemptions_date ON invite_code_redemptions(redeemed_at);

-- ============================================================
-- STEP 4: Create trigger to update updated_at timestamp
-- ============================================================
CREATE OR REPLACE FUNCTION update_invite_code_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_invite_codes_update
    BEFORE UPDATE ON invite_codes
    FOR EACH ROW
    EXECUTE FUNCTION update_invite_code_timestamp();

-- ============================================================
-- STEP 5: Create initial VIP Founder invite codes
-- ============================================================
INSERT INTO invite_codes (
    code,
    tier_code,
    max_uses,
    current_uses,
    expires_at,
    is_active,
    created_by,
    notes
) VALUES
    -- Unlimited use VIP Founder code (for internal team)
    (
        'VIP-FOUNDER-INTERNAL',
        'vip_founder',
        NULL,  -- Unlimited uses
        0,
        NULL,  -- Never expires
        TRUE,
        'system',
        'Internal team and founders - unlimited uses'
    ),
    -- Limited use VIP Founder codes (for early adopters)
    (
        'VIP-FOUNDER-EARLY100',
        'vip_founder',
        100,  -- 100 uses
        0,
        (CURRENT_TIMESTAMP + INTERVAL '90 days'),  -- Expires in 90 days
        TRUE,
        'system',
        'Early adopters program - 100 invites, expires in 90 days'
    ),
    (
        'VIP-FOUNDER-PARTNER50',
        'vip_founder',
        50,  -- 50 uses
        0,
        (CURRENT_TIMESTAMP + INTERVAL '180 days'),  -- Expires in 6 months
        TRUE,
        'system',
        'Partner organizations - 50 invites, expires in 6 months'
    )
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- STEP 6: Verification Queries
-- ============================================================

-- Show all invite codes
SELECT
    id,
    code,
    tier_code,
    max_uses,
    current_uses,
    CASE
        WHEN max_uses IS NULL THEN 'Unlimited'
        ELSE (max_uses - current_uses)::TEXT || ' remaining'
    END as remaining,
    expires_at,
    is_active,
    created_by,
    notes
FROM invite_codes
ORDER BY created_at DESC;

-- Show redemptions summary
SELECT
    ic.code,
    ic.tier_code,
    COUNT(icr.id) as redemption_count,
    ic.max_uses,
    CASE
        WHEN ic.max_uses IS NULL THEN 'Unlimited'
        ELSE (ic.max_uses - COUNT(icr.id))::TEXT || ' remaining'
    END as remaining
FROM invite_codes ic
LEFT JOIN invite_code_redemptions icr ON ic.id = icr.invite_code_id
GROUP BY ic.id, ic.code, ic.tier_code, ic.max_uses
ORDER BY ic.created_at DESC;

COMMIT;

-- ============================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================
-- To rollback this migration:
--
-- BEGIN;
-- DROP TABLE IF EXISTS invite_code_redemptions CASCADE;
-- DROP TABLE IF EXISTS invite_codes CASCADE;
-- DROP FUNCTION IF EXISTS update_invite_code_timestamp CASCADE;
-- COMMIT;

-- ============================================================
-- DEPLOYMENT INSTRUCTIONS
-- ============================================================
--
-- 1. Apply this migration to the database:
--    docker exec -i uchub-postgres psql -U unicorn -d unicorn_db < /path/to/create_invite_codes.sql
--
-- 2. Verify tables were created:
--    docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\d invite_codes"
--    docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "\d invite_code_redemptions"
--
-- 3. Verify initial codes were created:
--    docker exec uchub-postgres psql -U unicorn -d unicorn_db -c "SELECT * FROM invite_codes"
--
-- 4. Restart Ops-Center backend to load new API:
--    docker restart ops-center-direct
--
-- ============================================================
