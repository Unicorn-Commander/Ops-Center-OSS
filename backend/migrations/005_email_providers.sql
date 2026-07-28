-- Email provider configurations table
CREATE TABLE IF NOT EXISTS email_providers (
    id SERIAL PRIMARY KEY,
    provider_type VARCHAR(50) NOT NULL,  -- microsoft365, google, sendgrid, postmark, aws_ses, custom_smtp
    auth_method VARCHAR(50) NOT NULL,    -- app_password, oauth2, api_key
    enabled BOOLEAN DEFAULT true,

    -- Basic SMTP settings
    smtp_host VARCHAR(255),
    smtp_port INTEGER,
    smtp_user VARCHAR(255),
    smtp_from VARCHAR(255),

    -- Encrypted secrets
    smtp_password TEXT,              -- Base64 encoded (TODO: proper encryption)
    api_key TEXT,                    -- For SendGrid, Postmark, SES
    oauth2_client_id VARCHAR(255),
    oauth2_client_secret TEXT,       -- Encrypted
    oauth2_tenant_id VARCHAR(255),   -- For Microsoft 365
    oauth2_refresh_token TEXT,       -- Encrypted

    -- Provider-specific config (JSON)
    provider_config JSONB DEFAULT '{}',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_email_providers_enabled ON email_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_email_providers_type ON email_providers(provider_type);

-- Ensure only one provider is enabled at a time (trigger)
CREATE OR REPLACE FUNCTION ensure_single_active_provider()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.enabled = true THEN
        UPDATE email_providers SET enabled = false WHERE id != NEW.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_single_active_provider ON email_providers;
CREATE TRIGGER trigger_single_active_provider
    BEFORE INSERT OR UPDATE ON email_providers
    FOR EACH ROW
    EXECUTE FUNCTION ensure_single_active_provider();

-- Default provider (Microsoft 365 OAuth2 - user will configure)
INSERT INTO email_providers (
    provider_type, auth_method, enabled,
    smtp_from, provider_config
) VALUES (
    'microsoft365',
    'oauth2',
    false,  -- Disabled by default until configured
    'noreply@magicunicorn.tech',
    '{"description": "Default Microsoft 365 provider - configure OAuth2 credentials"}'::jsonb
) ON CONFLICT DO NOTHING;
