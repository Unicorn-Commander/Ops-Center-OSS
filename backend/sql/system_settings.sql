-- System Settings Schema
-- Stores environment variables and configuration that can be managed via GUI
-- Author: Backend API Developer
-- Date: October 20, 2025

-- Drop existing table if exists (for development)
DROP TABLE IF EXISTS system_settings CASCADE;

-- Create system_settings table
CREATE TABLE IF NOT EXISTS system_settings (
    -- Primary key
    key VARCHAR(255) PRIMARY KEY,

    -- Encrypted value (all values stored encrypted for security)
    encrypted_value TEXT NOT NULL,

    -- Category for grouping (security, billing, llm, email, storage, etc.)
    category VARCHAR(50) NOT NULL,

    -- Human-readable description
    description TEXT,

    -- Is this a sensitive value (API key, password, etc.)
    is_sensitive BOOLEAN DEFAULT FALSE,

    -- Validation type (optional: string, number, boolean, url, email, json)
    value_type VARCHAR(20) DEFAULT 'string',

    -- Is this setting required for system operation
    is_required BOOLEAN DEFAULT FALSE,

    -- Is this setting editable (some system settings may be read-only)
    is_editable BOOLEAN DEFAULT TRUE,

    -- Default value (unencrypted, for documentation purposes)
    default_value TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Who last modified this setting
    updated_by VARCHAR(255)
);

-- Create index on category for fast filtering
CREATE INDEX idx_system_settings_category ON system_settings(category);

-- Create index on is_sensitive for security filtering
CREATE INDEX idx_system_settings_sensitive ON system_settings(is_sensitive);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_system_settings_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER system_settings_updated_at
    BEFORE UPDATE ON system_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_system_settings_updated_at();

-- Create audit log for system settings changes
CREATE TABLE IF NOT EXISTS system_settings_audit (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL, -- CREATE, UPDATE, DELETE
    old_value TEXT, -- Encrypted old value (for UPDATE/DELETE)
    new_value TEXT, -- Encrypted new value (for CREATE/UPDATE)
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Create index on setting_key and changed_at for audit queries
CREATE INDEX idx_settings_audit_key ON system_settings_audit(setting_key, changed_at DESC);
CREATE INDEX idx_settings_audit_changed_by ON system_settings_audit(changed_by);

-- Pre-populate common settings (encrypted values will be set via API)
-- Note: These are placeholders - actual values set via GUI or API

-- Security Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('BYOK_ENCRYPTION_KEY', '', 'security', 'Master encryption key for BYOK (Bring Your Own Key) system', TRUE, 'string', TRUE, NULL),
    ('JWT_SECRET_KEY', '', 'security', 'Secret key for JWT token generation', TRUE, 'string', TRUE, NULL),
    ('SESSION_SECRET', '', 'security', 'Secret for session cookie encryption', TRUE, 'string', TRUE, NULL),
    ('CSRF_SECRET_KEY', '', 'security', 'Secret key for CSRF token generation', TRUE, 'string', FALSE, NULL)
ON CONFLICT (key) DO NOTHING;

-- LLM Provider Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('OPENROUTER_API_KEY', '', 'llm', 'OpenRouter API key for LLM routing', TRUE, 'string', FALSE, NULL),
    ('OPENAI_API_KEY', '', 'llm', 'OpenAI API key (optional if using BYOK)', TRUE, 'string', FALSE, NULL),
    ('ANTHROPIC_API_KEY', '', 'llm', 'Anthropic API key (optional if using BYOK)', TRUE, 'string', FALSE, NULL),
    ('GOOGLE_AI_API_KEY', '', 'llm', 'Google AI API key (optional if using BYOK)', TRUE, 'string', FALSE, NULL),
    ('COHERE_API_KEY', '', 'llm', 'Cohere API key (optional if using BYOK)', TRUE, 'string', FALSE, NULL),
    ('LITELLM_MASTER_KEY', '', 'llm', 'LiteLLM proxy master key', TRUE, 'string', TRUE, NULL),
    ('DEFAULT_LLM_MODEL', '', 'llm', 'Default LLM model to use', FALSE, 'string', FALSE, 'openai/gpt-4'),
    ('LLM_REQUEST_TIMEOUT', '', 'llm', 'LLM request timeout in seconds', FALSE, 'number', FALSE, '120')
ON CONFLICT (key) DO NOTHING;

-- Billing Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('STRIPE_SECRET_KEY', '', 'billing', 'Stripe secret key for payment processing', TRUE, 'string', TRUE, NULL),
    ('STRIPE_PUBLISHABLE_KEY', '', 'billing', 'Stripe publishable key (public, but stored here for convenience)', FALSE, 'string', TRUE, NULL),
    ('STRIPE_WEBHOOK_SECRET', '', 'billing', 'Stripe webhook secret for signature verification', TRUE, 'string', TRUE, NULL),
    ('LAGO_API_KEY', '', 'billing', 'Lago API key for billing management', TRUE, 'string', TRUE, NULL),
    ('LAGO_API_URL', '', 'billing', 'Lago API URL', FALSE, 'url', TRUE, 'http://unicorn-lago-api:3000'),
    ('LAGO_PUBLIC_URL', '', 'billing', 'Lago public URL for webhooks', FALSE, 'url', TRUE, 'https://billing-api.unicorncommander.ai')
ON CONFLICT (key) DO NOTHING;

-- Email Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('SMTP_HOST', '', 'email', 'SMTP server hostname', FALSE, 'string', FALSE, 'smtp.office365.com'),
    ('SMTP_PORT', '', 'email', 'SMTP server port', FALSE, 'number', FALSE, '587'),
    ('SMTP_USERNAME', '', 'email', 'SMTP username (email address)', FALSE, 'email', FALSE, NULL),
    ('SMTP_PASSWORD', '', 'email', 'SMTP password or app-specific password', TRUE, 'string', FALSE, NULL),
    ('SMTP_USE_TLS', '', 'email', 'Use TLS for SMTP connection', FALSE, 'boolean', FALSE, 'true'),
    ('SMTP_FROM_EMAIL', '', 'email', 'Default "From" email address', FALSE, 'email', FALSE, NULL),
    ('SMTP_FROM_NAME', '', 'email', 'Default "From" name', FALSE, 'string', FALSE, 'UC-Cloud Admin'),
    ('EMAIL_PROVIDER_TYPE', '', 'email', 'Email provider type (smtp, oauth2, sendgrid, etc.)', FALSE, 'string', FALSE, 'smtp'),
    ('OAUTH2_CLIENT_ID', '', 'email', 'OAuth2 Client ID for email (Microsoft 365, Gmail)', FALSE, 'string', FALSE, NULL),
    ('OAUTH2_CLIENT_SECRET', '', 'email', 'OAuth2 Client Secret for email', TRUE, 'string', FALSE, NULL),
    ('OAUTH2_TENANT_ID', '', 'email', 'OAuth2 Tenant ID (Microsoft 365 only)', FALSE, 'string', FALSE, NULL),
    ('OAUTH2_REFRESH_TOKEN', '', 'email', 'OAuth2 Refresh Token for email', TRUE, 'string', FALSE, NULL)
ON CONFLICT (key) DO NOTHING;

-- Storage Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('S3_ACCESS_KEY_ID', '', 'storage', 'AWS S3 Access Key ID (optional)', TRUE, 'string', FALSE, NULL),
    ('S3_SECRET_ACCESS_KEY', '', 'storage', 'AWS S3 Secret Access Key (optional)', TRUE, 'string', FALSE, NULL),
    ('S3_BUCKET_NAME', '', 'storage', 'AWS S3 Bucket Name (optional)', FALSE, 'string', FALSE, NULL),
    ('S3_REGION', '', 'storage', 'AWS S3 Region (optional)', FALSE, 'string', FALSE, 'us-east-1'),
    ('BACKUP_RETENTION_DAYS', '', 'storage', 'Number of days to retain backups', FALSE, 'number', FALSE, '7'),
    ('BACKUP_SCHEDULE', '', 'storage', 'Cron schedule for automated backups', FALSE, 'string', FALSE, '0 2 * * *')
ON CONFLICT (key) DO NOTHING;

-- Integration Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('KEYCLOAK_CLIENT_SECRET', '', 'integration', 'Keycloak OAuth client secret', TRUE, 'string', TRUE, NULL),
    ('KEYCLOAK_ADMIN_PASSWORD', '', 'integration', 'Keycloak admin password', TRUE, 'string', TRUE, NULL),
    ('BRIGADE_API_KEY', '', 'integration', 'Unicorn Brigade API key', TRUE, 'string', FALSE, NULL),
    ('CENTERDEEP_API_KEY', '', 'integration', 'Center Deep API key', TRUE, 'string', FALSE, NULL),
    ('GITHUB_TOKEN', '', 'integration', 'GitHub personal access token for integrations', TRUE, 'string', FALSE, NULL),
    ('SLACK_BOT_TOKEN', '', 'integration', 'Slack bot token for notifications', TRUE, 'string', FALSE, NULL),
    ('SLACK_WEBHOOK_URL', '', 'integration', 'Slack webhook URL for alerts', TRUE, 'url', FALSE, NULL)
ON CONFLICT (key) DO NOTHING;

-- Monitoring Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('SENTRY_DSN', '', 'monitoring', 'Sentry DSN for error tracking', TRUE, 'url', FALSE, NULL),
    ('GRAFANA_API_KEY', '', 'monitoring', 'Grafana API key for metrics', TRUE, 'string', FALSE, NULL),
    ('PROMETHEUS_PUSH_GATEWAY', '', 'monitoring', 'Prometheus Push Gateway URL', FALSE, 'url', FALSE, NULL),
    ('LOG_LEVEL', '', 'monitoring', 'System log level (DEBUG, INFO, WARNING, ERROR)', FALSE, 'string', FALSE, 'INFO'),
    ('ENABLE_METRICS', '', 'monitoring', 'Enable Prometheus metrics collection', FALSE, 'boolean', FALSE, 'true')
ON CONFLICT (key) DO NOTHING;

-- System Settings
INSERT INTO system_settings (key, encrypted_value, category, description, is_sensitive, value_type, is_required, default_value)
VALUES
    ('EXTERNAL_HOST', '', 'system', 'External hostname or IP address', FALSE, 'string', TRUE, 'unicorncommander.ai'),
    ('EXTERNAL_PROTOCOL', '', 'system', 'External protocol (http or https)', FALSE, 'string', TRUE, 'https'),
    ('SYSTEM_NAME', '', 'system', 'System display name', FALSE, 'string', FALSE, 'UC-Cloud Operations Center'),
    ('SYSTEM_TIMEZONE', '', 'system', 'System timezone', FALSE, 'string', FALSE, 'UTC'),
    ('MAINTENANCE_MODE', '', 'system', 'Enable maintenance mode', FALSE, 'boolean', FALSE, 'false'),
    ('ALLOW_SIGNUPS', '', 'system', 'Allow new user signups', FALSE, 'boolean', FALSE, 'true'),
    ('DEFAULT_USER_TIER', '', 'system', 'Default subscription tier for new users', FALSE, 'string', FALSE, 'trial')
ON CONFLICT (key) DO NOTHING;

-- Comments
COMMENT ON TABLE system_settings IS 'System configuration settings manageable via GUI';
COMMENT ON COLUMN system_settings.key IS 'Unique setting key (matches environment variable name)';
COMMENT ON COLUMN system_settings.encrypted_value IS 'Encrypted value using Fernet symmetric encryption';
COMMENT ON COLUMN system_settings.category IS 'Setting category for grouping (security, billing, llm, email, storage, integration, monitoring, system)';
COMMENT ON COLUMN system_settings.is_sensitive IS 'Whether this is a sensitive value (API key, password) - affects UI display';
COMMENT ON COLUMN system_settings.value_type IS 'Data type for validation (string, number, boolean, url, email, json)';
COMMENT ON COLUMN system_settings.is_required IS 'Whether this setting is required for system operation';
COMMENT ON COLUMN system_settings.is_editable IS 'Whether this setting can be edited via GUI (some may be read-only)';
COMMENT ON COLUMN system_settings.default_value IS 'Default value for documentation (unencrypted, may be NULL)';

COMMENT ON TABLE system_settings_audit IS 'Audit log for all system settings changes';
