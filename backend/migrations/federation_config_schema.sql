-- Federation Configuration Schema
-- Stores GUI-configurable federation settings (replaces env-var-only config)
-- Created: March 2026

-- Ensure uuid extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Federation configuration table (single-row settings)
CREATE TABLE IF NOT EXISTS federation_config (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    enabled BOOLEAN DEFAULT false,

    -- Node Identity
    node_id VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    endpoint_url VARCHAR(512),
    region VARCHAR(100),
    roles JSONB DEFAULT '["inference"]',
    is_billing_node BOOLEAN DEFAULT false,
    routing_priority VARCHAR(20) DEFAULT 'cost',

    -- Security
    federation_key_hash VARCHAR(255),  -- bcrypt hash
    federation_key_prefix VARCHAR(20), -- first 8 chars for identification

    -- Branding (per-node identity in federation)
    branding JSONB DEFAULT '{}',
    -- Contains: theme_id, logo_url, company_name, company_subtitle, accent_color, favicon_url

    -- Preferences
    heartbeat_interval INTEGER DEFAULT 30,
    auto_discover_services BOOLEAN DEFAULT true,

    -- Service toggles (which local services to advertise)
    advertised_services JSONB DEFAULT '{}',
    -- Contains: {"llm": true, "tts": true, "stt": false, ...}

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Configured peers (separate from federation_nodes which tracks ALL known nodes)
CREATE TABLE IF NOT EXISTS federation_configured_peers (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    peer_url VARCHAR(512) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    federation_key_override VARCHAR(255),  -- encrypted, if different from default
    trust_level VARCHAR(20) DEFAULT 'full',
    auto_connect BOOLEAN DEFAULT true,
    last_test_at TIMESTAMP,
    last_test_result JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_federation_config_node_id ON federation_config(node_id);
CREATE INDEX IF NOT EXISTS idx_federation_peers_auto_connect ON federation_configured_peers(auto_connect) WHERE auto_connect = true;
