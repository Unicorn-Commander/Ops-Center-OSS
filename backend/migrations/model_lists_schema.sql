-- Model List Management Schema
-- Created: November 19, 2025
-- Purpose: Enable admin GUI management of per-app curated model lists

-- ============================================================================
-- 1. App-specific curated model list definitions
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_model_lists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'bolt-diy', 'presenton', 'global'
    description TEXT,
    app_identifier VARCHAR(100),  -- The app this list is for (null for global)
    is_default BOOLEAN DEFAULT FALSE,  -- Is this the default list for the app?
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255)  -- User ID who created this list
);

-- Partial unique index to ensure only one default per app
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_default_per_app
ON app_model_lists(app_identifier) WHERE is_default = TRUE;

-- ============================================================================
-- 2. Models in each curated list
-- ============================================================================
CREATE TABLE IF NOT EXISTS app_model_list_items (
    id SERIAL PRIMARY KEY,
    list_id INTEGER NOT NULL REFERENCES app_model_lists(id) ON DELETE CASCADE,
    model_id VARCHAR(255) NOT NULL,  -- e.g., 'qwen/qwen3-coder:free'
    display_name VARCHAR(255),  -- Custom display name (optional)
    description TEXT,  -- Custom description for this model in this list
    category VARCHAR(50) DEFAULT 'general',  -- coding, reasoning, general, fast, creative
    sort_order INTEGER DEFAULT 0,  -- For custom ordering
    is_free BOOLEAN DEFAULT FALSE,  -- Is this a free model?
    context_length INTEGER,  -- Override context length if needed

    -- Tier access control (which tiers can see this model)
    tier_trial BOOLEAN DEFAULT TRUE,
    tier_starter BOOLEAN DEFAULT TRUE,
    tier_professional BOOLEAN DEFAULT TRUE,
    tier_enterprise BOOLEAN DEFAULT TRUE,
    tier_vip_founder BOOLEAN DEFAULT TRUE,
    tier_byok BOOLEAN DEFAULT TRUE,

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_model_per_list UNIQUE (list_id, model_id)
);

-- ============================================================================
-- 3. User preferences for models (favorites, hidden)
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_model_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user ID
    model_id VARCHAR(255) NOT NULL,
    is_favorite BOOLEAN DEFAULT FALSE,
    is_hidden BOOLEAN DEFAULT FALSE,
    custom_label VARCHAR(255),  -- User's custom label for this model
    notes TEXT,  -- User's notes about this model
    last_used_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT unique_user_model_pref UNIQUE (user_id, model_id)
);

-- ============================================================================
-- 4. Audit trail for model list changes
-- ============================================================================
CREATE TABLE IF NOT EXISTS model_access_audit (
    id SERIAL PRIMARY KEY,
    list_id INTEGER REFERENCES app_model_lists(id) ON DELETE SET NULL,
    model_id VARCHAR(255),
    action VARCHAR(50) NOT NULL,  -- 'created', 'updated', 'deleted', 'reordered', 'tier_changed'
    actor_id VARCHAR(255) NOT NULL,  -- User who made the change
    actor_email VARCHAR(255),
    old_value JSONB,  -- Previous state
    new_value JSONB,  -- New state
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- Indexes for performance
-- ============================================================================

-- app_model_lists indexes
CREATE INDEX IF NOT EXISTS idx_app_model_lists_slug ON app_model_lists(slug);
CREATE INDEX IF NOT EXISTS idx_app_model_lists_app ON app_model_lists(app_identifier);
CREATE INDEX IF NOT EXISTS idx_app_model_lists_active ON app_model_lists(is_active);

-- app_model_list_items indexes
CREATE INDEX IF NOT EXISTS idx_model_list_items_list ON app_model_list_items(list_id);
CREATE INDEX IF NOT EXISTS idx_model_list_items_model ON app_model_list_items(model_id);
CREATE INDEX IF NOT EXISTS idx_model_list_items_category ON app_model_list_items(category);
CREATE INDEX IF NOT EXISTS idx_model_list_items_sort ON app_model_list_items(list_id, sort_order);

-- user_model_preferences indexes
CREATE INDEX IF NOT EXISTS idx_user_prefs_user ON user_model_preferences(user_id);
CREATE INDEX IF NOT EXISTS idx_user_prefs_model ON user_model_preferences(model_id);
CREATE INDEX IF NOT EXISTS idx_user_prefs_favorite ON user_model_preferences(user_id, is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX IF NOT EXISTS idx_user_prefs_hidden ON user_model_preferences(user_id, is_hidden) WHERE is_hidden = TRUE;

-- model_access_audit indexes
CREATE INDEX IF NOT EXISTS idx_audit_list ON model_access_audit(list_id);
CREATE INDEX IF NOT EXISTS idx_audit_actor ON model_access_audit(actor_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON model_access_audit(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON model_access_audit(created_at);

-- ============================================================================
-- Trigger for updated_at timestamps
-- ============================================================================

CREATE OR REPLACE FUNCTION update_model_lists_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to tables with updated_at
DROP TRIGGER IF EXISTS trigger_app_model_lists_updated ON app_model_lists;
CREATE TRIGGER trigger_app_model_lists_updated
    BEFORE UPDATE ON app_model_lists
    FOR EACH ROW EXECUTE FUNCTION update_model_lists_updated_at();

DROP TRIGGER IF EXISTS trigger_model_list_items_updated ON app_model_list_items;
CREATE TRIGGER trigger_model_list_items_updated
    BEFORE UPDATE ON app_model_list_items
    FOR EACH ROW EXECUTE FUNCTION update_model_lists_updated_at();

DROP TRIGGER IF EXISTS trigger_user_prefs_updated ON user_model_preferences;
CREATE TRIGGER trigger_user_prefs_updated
    BEFORE UPDATE ON user_model_preferences
    FOR EACH ROW EXECUTE FUNCTION update_model_lists_updated_at();

-- ============================================================================
-- Initial seed data - Global default list
-- ============================================================================

-- Create global default list
INSERT INTO app_model_lists (name, slug, description, app_identifier, is_default, created_by)
VALUES (
    'Global Default',
    'global',
    'Default curated list available to all apps when no app-specific list exists',
    NULL,
    TRUE,
    'system'
) ON CONFLICT (slug) DO NOTHING;

-- Note: Actual model seeding will be done via a separate Python script
-- that can fetch current model data from OpenRouter

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE app_model_lists IS 'Stores app-specific curated model list definitions';
COMMENT ON TABLE app_model_list_items IS 'Models included in each curated list with tier access control';
COMMENT ON TABLE user_model_preferences IS 'User-specific model preferences (favorites, hidden, custom labels)';
COMMENT ON TABLE model_access_audit IS 'Audit trail for all model list changes';

COMMENT ON COLUMN app_model_list_items.tier_trial IS 'Can Trial tier users see this model?';
COMMENT ON COLUMN app_model_list_items.tier_starter IS 'Can Starter tier users see this model?';
COMMENT ON COLUMN app_model_list_items.tier_professional IS 'Can Professional tier users see this model?';
COMMENT ON COLUMN app_model_list_items.tier_enterprise IS 'Can Enterprise tier users see this model?';
COMMENT ON COLUMN app_model_list_items.tier_vip_founder IS 'Can VIP Founder tier users see this model?';
COMMENT ON COLUMN app_model_list_items.tier_byok IS 'Can BYOK tier users see this model?';
