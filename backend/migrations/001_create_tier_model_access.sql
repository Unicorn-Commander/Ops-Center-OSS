-- ============================================================================
-- Migration: Create tier_model_access junction table
-- Date: November 6, 2025
-- Purpose: Replace JSONB tier_access with dynamic tier-model relationships
-- ============================================================================

-- 1. Create tier_model_access junction table
CREATE TABLE IF NOT EXISTS tier_model_access (
    id SERIAL PRIMARY KEY,
    tier_id INTEGER NOT NULL REFERENCES subscription_tiers(id) ON DELETE CASCADE,
    model_id UUID NOT NULL REFERENCES model_access_control(id) ON DELETE CASCADE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    markup_multiplier NUMERIC(4,2) NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT tier_model_access_unique UNIQUE (tier_id, model_id)
);

-- 2. Create indexes for performance
CREATE INDEX idx_tier_model_access_tier ON tier_model_access(tier_id) WHERE enabled = TRUE;
CREATE INDEX idx_tier_model_access_model ON tier_model_access(model_id) WHERE enabled = TRUE;
CREATE INDEX idx_tier_model_access_enabled ON tier_model_access(enabled);

-- 3. Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_tier_model_access_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_tier_model_access_update
    BEFORE UPDATE ON tier_model_access
    FOR EACH ROW
    EXECUTE FUNCTION update_tier_model_access_updated_at();

-- 4. Add comments for documentation
COMMENT ON TABLE tier_model_access IS 'Junction table mapping subscription tiers to available models with tier-specific pricing multipliers';
COMMENT ON COLUMN tier_model_access.tier_id IS 'Foreign key to subscription_tiers table';
COMMENT ON COLUMN tier_model_access.model_id IS 'Foreign key to model_access_control table';
COMMENT ON COLUMN tier_model_access.enabled IS 'Whether this model is currently accessible for this tier';
COMMENT ON COLUMN tier_model_access.markup_multiplier IS 'Tier-specific pricing multiplier (1.0 = base cost, 1.5 = 50% markup)';

-- 5. Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON tier_model_access TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE tier_model_access_id_seq TO unicorn;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration 001: tier_model_access table created successfully';
END $$;
