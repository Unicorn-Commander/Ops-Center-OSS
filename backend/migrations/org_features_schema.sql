-- ==============================================================================
-- Organization-Level Feature Grants Schema
-- ==============================================================================
-- Database: unicorn_db
-- Purpose: Store feature grants specific to organizations (independent of tiers)
--
-- This table allows granting features directly to organizations, enabling:
-- - Custom feature access beyond tier defaults
-- - Trial/beta feature access for specific orgs
-- - Partner/enterprise customizations
-- - Override tier restrictions for special cases
--
-- Use Case Examples:
-- - Grant "Open-WebUI" access to a specific partner organization
-- - Enable "beta-feature" for internal testing org
-- - Grant "priority-support" to a strategic customer
--
-- Created: 2026-01-31
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- TABLE: org_features
-- Purpose: Store feature grants specific to organizations
-- ==============================================================================

CREATE TABLE IF NOT EXISTS org_features (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Organization reference (CASCADE delete when org is deleted)
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Feature being granted (e.g., 'open_webui', 'forgejo', 'center_deep')
    feature_key VARCHAR(255) NOT NULL,

    -- Whether the feature is currently enabled for this org
    enabled BOOLEAN NOT NULL DEFAULT TRUE,

    -- Admin who granted this feature (for audit purposes)
    granted_by VARCHAR(255),

    -- When the feature was granted
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Optional notes explaining why the grant was made
    notes TEXT,

    -- Ensure each org can only have one record per feature
    CONSTRAINT unique_org_feature UNIQUE(org_id, feature_key)
);

-- ==============================================================================
-- INDEXES
-- ==============================================================================

-- Index for fast lookups by organization ID
-- Used when checking all features for a specific org
CREATE INDEX IF NOT EXISTS idx_org_features_org_id
    ON org_features(org_id);

-- Index for fast lookups by feature key
-- Used when finding all orgs with a specific feature
CREATE INDEX IF NOT EXISTS idx_org_features_feature_key
    ON org_features(feature_key);

-- Composite index for enabled features per org
-- Optimizes the common query: "What enabled features does this org have?"
CREATE INDEX IF NOT EXISTS idx_org_features_org_enabled
    ON org_features(org_id, enabled)
    WHERE enabled = TRUE;

-- Index for audit queries by granting admin
CREATE INDEX IF NOT EXISTS idx_org_features_granted_by
    ON org_features(granted_by);

-- Index for time-based queries (recently granted features)
CREATE INDEX IF NOT EXISTS idx_org_features_granted_at
    ON org_features(granted_at DESC);

-- ==============================================================================
-- COMMENTS
-- ==============================================================================

COMMENT ON TABLE org_features IS
    'Organization-level feature grants that override or supplement tier-based access. '
    'Allows admins to grant specific features to organizations independent of their subscription tier.';

COMMENT ON COLUMN org_features.id IS
    'Unique identifier for the feature grant record';

COMMENT ON COLUMN org_features.org_id IS
    'Reference to the organization receiving the feature grant';

COMMENT ON COLUMN org_features.feature_key IS
    'Identifier of the feature being granted (must match tier_features.feature_key or add_ons.feature_key)';

COMMENT ON COLUMN org_features.enabled IS
    'Whether this feature grant is currently active. Set to FALSE to disable without deleting.';

COMMENT ON COLUMN org_features.granted_by IS
    'Username or email of the admin who granted this feature (for audit trail)';

COMMENT ON COLUMN org_features.granted_at IS
    'Timestamp when the feature was originally granted';

COMMENT ON COLUMN org_features.notes IS
    'Optional explanation for why this feature was granted (e.g., "Partner deal Q1 2026", "Beta tester")';

-- ==============================================================================
-- GRANTS
-- ==============================================================================

-- Ensure the unicorn user can access this table
GRANT SELECT, INSERT, UPDATE, DELETE ON org_features TO unicorn;

-- ==============================================================================
-- HELPER FUNCTION: Check if org has a specific feature
-- ==============================================================================

CREATE OR REPLACE FUNCTION org_has_feature(p_org_id UUID, p_feature_key VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1
        FROM org_features
        WHERE org_id = p_org_id
          AND feature_key = p_feature_key
          AND enabled = TRUE
    );
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION org_has_feature IS
    'Check if an organization has a specific feature granted and enabled';

-- ==============================================================================
-- SAMPLE INSERT (COMMENTED OUT)
-- ==============================================================================
-- Example: Grant Open-WebUI access to the NDA-AutoPilot organization
--
-- INSERT INTO org_features (org_id, feature_key, enabled, granted_by, notes)
-- SELECT
--     id,                                    -- org_id from organizations table
--     'open_webui',                          -- feature key
--     TRUE,                                  -- enabled
--     'admin@example.com',             -- admin who granted it
--     'Custom grant for NDA-AutoPilot project - January 2026'  -- notes
-- FROM organizations
-- WHERE name = 'NDA-AutoPilot'
-- ON CONFLICT (org_id, feature_key) DO UPDATE SET
--     enabled = EXCLUDED.enabled,
--     granted_by = EXCLUDED.granted_by,
--     notes = EXCLUDED.notes;

-- ==============================================================================
-- VIEW: Convenient query for org features with org names
-- ==============================================================================

CREATE OR REPLACE VIEW v_org_features_with_names AS
SELECT
    of.id,
    of.org_id,
    o.name AS org_name,
    o.display_name AS org_display_name,
    of.feature_key,
    of.enabled,
    of.granted_by,
    of.granted_at,
    of.notes
FROM org_features of
JOIN organizations o ON of.org_id = o.id
ORDER BY o.name, of.feature_key;

COMMENT ON VIEW v_org_features_with_names IS
    'Convenience view joining org_features with organization names for admin queries';

GRANT SELECT ON v_org_features_with_names TO unicorn;

-- ==============================================================================
-- COMPLETION NOTICE
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE 'org_features schema created successfully';
    RAISE NOTICE 'Table: org_features';
    RAISE NOTICE 'View: v_org_features_with_names';
    RAISE NOTICE 'Function: org_has_feature(org_id, feature_key)';
    RAISE NOTICE 'Indexes: 5 (org_id, feature_key, org_enabled, granted_by, granted_at)';
END $$;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- To apply: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/org_features_schema.sql
-- To verify: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d org_features"
-- To check: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT * FROM org_features;"
