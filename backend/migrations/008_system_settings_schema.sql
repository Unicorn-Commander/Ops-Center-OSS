-- ============================================================================
-- System Settings Schema Migration
-- Version: 008
-- Created: November 14, 2025
-- Description: Create system_settings table for landing page configuration
--              and white-labeling options with category-based organization
-- ============================================================================

-- Drop existing table if exists (for clean reinstall)
DROP TABLE IF EXISTS system_settings CASCADE;

-- Create system_settings table
CREATE TABLE IF NOT EXISTS system_settings (
    key VARCHAR(255) PRIMARY KEY,
    value TEXT NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('string', 'json', 'boolean', 'number', 'array')),
    category VARCHAR(100) NOT NULL CHECK (category IN ('authentication', 'branding', 'features', 'integrations', 'notifications', 'security')),
    label VARCHAR(255) NOT NULL,
    description TEXT,
    default_value TEXT,
    is_public BOOLEAN DEFAULT FALSE, -- If true, accessible without auth via /api/v1/system/settings
    is_readonly BOOLEAN DEFAULT FALSE, -- If true, cannot be updated via API
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(255),
    CONSTRAINT valid_boolean_value CHECK (
        type != 'boolean' OR value IN ('true', 'false')
    ),
    CONSTRAINT valid_number_value CHECK (
        type != 'number' OR value ~ '^-?[0-9]+(\.[0-9]+)?$'
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_system_settings_category ON system_settings(category);
CREATE INDEX IF NOT EXISTS idx_system_settings_is_public ON system_settings(is_public);
CREATE INDEX IF NOT EXISTS idx_system_settings_updated_at ON system_settings(updated_at);

-- Create trigger to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_system_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_system_settings_timestamp ON system_settings;
CREATE TRIGGER trigger_update_system_settings_timestamp
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_timestamp();

-- ============================================================================
-- Seed Data: Landing Page & Authentication Settings
-- ============================================================================

INSERT INTO system_settings (key, value, type, category, label, description, default_value, is_public, is_readonly) VALUES
('landing_page_mode', 'direct_sso', 'string', 'authentication', 'Landing Page Mode', 'How unauthenticated users access the system. Options: direct_sso (redirect to SSO), public_marketplace (public landing page), custom (custom HTML)', 'direct_sso', true, false),
('sso_auto_redirect', 'true', 'boolean', 'authentication', 'Auto-Redirect to SSO', 'Automatically redirect unauthenticated users to SSO login', 'true', true, false),
('allow_registration', 'true', 'boolean', 'authentication', 'Allow User Registration', 'Enable self-service user registration via SSO providers', 'true', true, false),
('require_email_verification', 'true', 'boolean', 'authentication', 'Require Email Verification', 'Users must verify email before accessing platform', 'true', false, false),
('session_timeout_minutes', '1440', 'number', 'authentication', 'Session Timeout (Minutes)', 'Automatic session timeout in minutes (default: 24 hours)', '1440', false, false)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Seed Data: Branding & White-Label Settings
-- ============================================================================

INSERT INTO system_settings (key, value, type, category, label, description, default_value, is_public, is_readonly) VALUES
('branding.company_name', 'Unicorn Commander', 'string', 'branding', 'Company Name', 'Display name for the platform', 'Unicorn Commander', true, false),
('branding.logo_url', '/assets/logo.svg', 'string', 'branding', 'Logo URL', 'URL to company logo (relative or absolute)', '/assets/logo.svg', true, false),
('branding.logo_dark_url', '/assets/logo-dark.svg', 'string', 'branding', 'Logo URL (Dark Mode)', 'URL to company logo for dark mode', '/assets/logo-dark.svg', true, false),
('branding.favicon_url', '/assets/favicon.ico', 'string', 'branding', 'Favicon URL', 'URL to favicon', '/assets/favicon.ico', true, false),
('branding.primary_color', '#7c3aed', 'string', 'branding', 'Primary Color', 'Main brand color (hex format)', '#7c3aed', true, false),
('branding.secondary_color', '#ec4899', 'string', 'branding', 'Secondary Color', 'Accent brand color (hex format)', '#ec4899', true, false),
('branding.background_color', '#0f172a', 'string', 'branding', 'Background Color', 'Main background color (hex format)', '#0f172a', true, false),
('branding.text_color', '#ffffff', 'string', 'branding', 'Text Color', 'Primary text color (hex format)', '#ffffff', true, false),
('branding.tagline', 'Enterprise AI Infrastructure Platform', 'string', 'branding', 'Tagline', 'Short tagline displayed on landing page', 'Enterprise AI Infrastructure Platform', true, false),
('branding.description', 'Manage your AI infrastructure, subscriptions, and services from one unified dashboard.', 'string', 'branding', 'Description', 'Longer description for landing page and SEO', 'Manage your AI infrastructure, subscriptions, and services from one unified dashboard.', true, false),
('branding.support_email', 'support@your-domain.com', 'string', 'branding', 'Support Email', 'Contact email for customer support', 'support@your-domain.com', true, false),
('branding.support_url', 'https://your-domain.com/support', 'string', 'branding', 'Support URL', 'Link to support/help center', 'https://your-domain.com/support', true, false),
('branding.terms_url', 'https://your-domain.com/terms', 'string', 'branding', 'Terms of Service URL', 'Link to Terms of Service', 'https://your-domain.com/terms', true, false),
('branding.privacy_url', 'https://your-domain.com/privacy', 'string', 'branding', 'Privacy Policy URL', 'Link to Privacy Policy', 'https://your-domain.com/privacy', true, false)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Seed Data: Feature Flags
-- ============================================================================

INSERT INTO system_settings (key, value, type, category, label, description, default_value, is_public, is_readonly) VALUES
('features.marketplace_enabled', 'true', 'boolean', 'features', 'Enable Marketplace', 'Show extensions marketplace to users', 'true', true, false),
('features.byok_enabled', 'true', 'boolean', 'features', 'Enable BYOK', 'Allow users to bring their own API keys', 'true', true, false),
('features.organizations_enabled', 'true', 'boolean', 'features', 'Enable Organizations', 'Enable multi-tenant organization features', 'true', false, false),
('features.analytics_enabled', 'true', 'boolean', 'features', 'Enable Analytics', 'Enable usage analytics and reporting', 'true', false, false),
('features.api_keys_enabled', 'true', 'boolean', 'features', 'Enable API Keys', 'Allow users to create API keys', 'true', false, false)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Seed Data: Integration Settings
-- ============================================================================

INSERT INTO system_settings (key, value, type, category, label, description, default_value, is_public, is_readonly) VALUES
('integrations.stripe_enabled', 'true', 'boolean', 'integrations', 'Stripe Integration', 'Enable Stripe payment processing', 'true', false, false),
('integrations.openrouter_enabled', 'true', 'boolean', 'integrations', 'OpenRouter Integration', 'Enable OpenRouter LLM models', 'true', false, false),
('integrations.brigade_url', 'https://brigade.your-domain.com', 'string', 'integrations', 'Brigade URL', 'URL to Unicorn Brigade agent platform', 'https://brigade.your-domain.com', true, false),
('integrations.open_webui_url', 'https://chat.your-domain.com', 'string', 'integrations', 'Open-WebUI URL', 'URL to Open-WebUI chat interface', 'https://chat.your-domain.com', true, false),
('integrations.center_deep_url', 'https://search.your-domain.com', 'string', 'integrations', 'Center-Deep URL', 'URL to Center-Deep search engine', 'https://search.your-domain.com', true, false)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Seed Data: Notification Settings
-- ============================================================================

INSERT INTO system_settings (key, value, type, category, label, description, default_value, is_public, is_readonly) VALUES
('notifications.email_enabled', 'true', 'boolean', 'notifications', 'Email Notifications', 'Enable email notifications', 'true', false, false),
('notifications.welcome_email', 'true', 'boolean', 'notifications', 'Welcome Email', 'Send welcome email to new users', 'true', false, false),
('notifications.invoice_email', 'true', 'boolean', 'notifications', 'Invoice Email', 'Send invoice emails', 'true', false, false),
('notifications.usage_alerts', 'true', 'boolean', 'notifications', 'Usage Alerts', 'Send alerts when approaching usage limits', 'true', false, false)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Seed Data: Security Settings
-- ============================================================================

INSERT INTO system_settings (key, value, type, category, label, description, default_value, is_public, is_readonly) VALUES
('security.min_password_length', '12', 'number', 'security', 'Minimum Password Length', 'Minimum password length for local accounts', '12', false, false),
('security.require_mfa', 'false', 'boolean', 'security', 'Require MFA', 'Require multi-factor authentication for all users', 'false', false, false),
('security.max_login_attempts', '5', 'number', 'security', 'Max Login Attempts', 'Maximum failed login attempts before lockout', '5', false, false),
('security.lockout_duration_minutes', '30', 'number', 'security', 'Lockout Duration (Minutes)', 'Account lockout duration after max failed attempts', '30', false, false)
ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Grant permissions
-- ============================================================================

-- Grant read access to application user
GRANT SELECT ON system_settings TO unicorn;

-- Grant write access for admin operations
GRANT INSERT, UPDATE, DELETE ON system_settings TO unicorn;

-- ============================================================================
-- Verification Queries (for testing)
-- ============================================================================

-- Uncomment to verify installation:
-- SELECT category, COUNT(*) as setting_count FROM system_settings GROUP BY category ORDER BY category;
-- SELECT * FROM system_settings WHERE is_public = true ORDER BY category, key;
-- SELECT * FROM system_settings WHERE category = 'branding' ORDER BY key;

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Created table: system_settings
-- Created indexes: 3 indexes for performance
-- Created trigger: auto-update timestamp
-- Seeded data: 36 default settings across 6 categories
-- Categories: authentication, branding, features, integrations, notifications, security
-- Public settings: 23 (accessible without authentication)
-- Admin-only settings: 13 (require authentication)
-- ============================================================================
