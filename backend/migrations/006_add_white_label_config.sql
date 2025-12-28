-- White Label Configuration Table Migration
-- Version: 006
-- Created: 2025-11-09
-- Description: Add white-label branding configuration table for deployment-wide customization
-- This table stores global branding settings that admins can manage through the Ops-Center GUI

-- ==================== White Label Config Table ====================

-- Single-row configuration table for global white-label branding
-- Each deployment has exactly ONE row in this table (enforced by application logic)
CREATE TABLE IF NOT EXISTS white_label_config (
    id SERIAL PRIMARY KEY,

    -- Company Information
    company_name VARCHAR(255),                      -- e.g., "Acme Corp", "Finance AI Solutions"
    company_subtitle VARCHAR(500),                  -- e.g., "AI-Powered Enterprise Platform"

    -- Branding Assets
    logo_url VARCHAR(500),                          -- Full URL or relative path to logo
    favicon_url VARCHAR(500),                       -- Full URL or relative path to favicon

    -- Theme & Color Configuration
    theme_preset VARCHAR(50),                       -- Predefined theme: 'professional', 'unicorn', 'ocean'
    primary_color VARCHAR(7),                       -- Hex color code (e.g., '#2E5090')
    secondary_color VARCHAR(7),                     -- Hex color code for accents
    accent_color VARCHAR(7),                        -- Hex color code for interactive elements
    background_gradient TEXT,                       -- CSS gradient string: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'

    -- Service Configuration
    services_config JSONB DEFAULT '{}',             -- JSON array of service configurations
                                                    -- Example: [
                                                    --   {"service": "openwebui", "enabled": true, "label": "Chat"},
                                                    --   {"service": "centerdeep", "enabled": true, "label": "Search"}
                                                    -- ]

    -- Domain & Access
    custom_domain VARCHAR(255),                     -- Custom domain (e.g., "ai.acmecorp.com")

    -- Feature Flags
    hide_attribution BOOLEAN DEFAULT FALSE,         -- Hide "Powered by Magic Unicorn" attribution
    custom_css TEXT,                                -- Additional custom CSS for fine-tuning

    -- Template Selection
    template_base VARCHAR(50),                      -- Base template to customize: 'centerdeep', 'unicorncommander', 'default'

    -- Audit Trail
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID,                                -- Foreign key to users table (if exists)

    -- Status
    is_active BOOLEAN DEFAULT TRUE                  -- Activate/deactivate configuration without deleting
);

-- ==================== Indexes ====================

-- Index for active configuration lookup (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_white_label_config_is_active ON white_label_config(is_active);

-- Index for domain-based lookups if custom domain is used
CREATE INDEX IF NOT EXISTS idx_white_label_config_custom_domain ON white_label_config(custom_domain) WHERE is_active = TRUE;

-- ==================== Comments ====================

COMMENT ON TABLE white_label_config IS
'Global white-label branding configuration for the deployment.
Stores company branding (logo, colors, names) that can be customized via the Ops-Center GUI.
Typically contains only one active row per deployment (enforced by application logic).
This table enables complete UI customization for white-label and reseller deployments.';

COMMENT ON COLUMN white_label_config.company_name IS
'Display name for the company/deployment (shown in headers, titles, etc.)';

COMMENT ON COLUMN white_label_config.company_subtitle IS
'Tagline or description shown below company name in UI elements';

COMMENT ON COLUMN white_label_config.logo_url IS
'URL to company logo image. Supports absolute URLs (https://...) or relative paths (/assets/logo.png)';

COMMENT ON COLUMN white_label_config.favicon_url IS
'URL to favicon for browser tab. Supports absolute URLs or relative paths';

COMMENT ON COLUMN white_label_config.theme_preset IS
'Predefined theme preset: professional (blue/gray), unicorn (purple/gold), ocean (teal/white).
Choose one or leave NULL to use custom colors';

COMMENT ON COLUMN white_label_config.primary_color IS
'Primary brand color in hex format (e.g., #2E5090). Used for main buttons, links, headers';

COMMENT ON COLUMN white_label_config.secondary_color IS
'Secondary color for supporting UI elements. Used for sidebars, backgrounds, accents';

COMMENT ON COLUMN white_label_config.accent_color IS
'Accent color for important interactive elements. Used for hover states, focus indicators, badges';

COMMENT ON COLUMN white_label_config.background_gradient IS
'CSS gradient definition for page backgrounds. Example: linear-gradient(135deg, #667eea 0%, #764ba2 100%)';

COMMENT ON COLUMN white_label_config.services_config IS
'JSON configuration for enabled services and custom labels.
Allows per-service customization without code changes.
Example structure: [{"service": "openwebui", "enabled": true, "label": "Chat Assistant", "url": "/chat"}]';

COMMENT ON COLUMN white_label_config.custom_domain IS
'Custom domain for white-labeled deployment (e.g., "ai.acmecorp.com").
Used in email templates, documentation, and API responses';

COMMENT ON COLUMN white_label_config.hide_attribution IS
'If TRUE, hides "Powered by Magic Unicorn" attribution in footer and various UI elements.
Useful for complete white-label solutions where attribution is not desired';

COMMENT ON COLUMN white_label_config.custom_css IS
'Additional CSS rules to override or extend default styling.
Allows fine-tuning without modifying the base stylesheets.
Example: .navbar { background: linear-gradient(...); } .button-primary { padding: 12px 24px; }';

COMMENT ON COLUMN white_label_config.template_base IS
'Base template to use as foundation:
- centerdeep: Privacy-focused search UI template
- unicorncommander: Full-featured UC-Cloud UI template
- default: Minimal clean template (good starting point)';

COMMENT ON COLUMN white_label_config.created_at IS
'Timestamp when configuration was first created';

COMMENT ON COLUMN white_label_config.updated_at IS
'Timestamp when configuration was last modified (auto-updated by trigger)';

COMMENT ON COLUMN white_label_config.created_by IS
'UUID of admin user who created this configuration (for audit trail)';

COMMENT ON COLUMN white_label_config.is_active IS
'Boolean flag to activate/deactivate configuration. Set to FALSE to temporarily revert to defaults.
Application should use WHERE is_active = TRUE in queries';

-- ==================== Trigger for updated_at Column ====================

-- Automatically update the updated_at timestamp on modification
CREATE OR REPLACE FUNCTION update_white_label_config_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_white_label_config_updated_at ON white_label_config;
CREATE TRIGGER update_white_label_config_updated_at
    BEFORE UPDATE ON white_label_config
    FOR EACH ROW
    EXECUTE FUNCTION update_white_label_config_updated_at();

-- ==================== Migration Complete ====================

DO $$
BEGIN
    RAISE NOTICE 'White-label configuration table created successfully';
    RAISE NOTICE 'Table: white_label_config';
    RAISE NOTICE 'Columns: 17 (branding, colors, services, domain, custom CSS, audit trail)';
    RAISE NOTICE 'Indexes: 2 (is_active, custom_domain)';
    RAISE NOTICE 'Trigger: 1 (automatic updated_at)';
    RAISE NOTICE 'Note: Application must enforce single-row constraint via upsert operations';
END $$;
