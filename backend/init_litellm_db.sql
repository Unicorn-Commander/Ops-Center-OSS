-- LiteLLM Routing Database Tables
-- Create all tables for provider and routing management

-- 1. Providers table
CREATE TABLE IF NOT EXISTS llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- openrouter, openai, anthropic, together, huggingface, custom
    api_key_encrypted TEXT NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 50,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name)
);

-- 2. Models table
CREATE TABLE IF NOT EXISTS llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id UUID REFERENCES llm_providers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    cost_per_1m_tokens DECIMAL(10, 4) DEFAULT 0,
    context_length INTEGER DEFAULT 4096,
    enabled BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(provider_id, name)
);

-- 3. Routing rules table
CREATE TABLE IF NOT EXISTS llm_routing_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    strategy VARCHAR(50) DEFAULT 'balanced',  -- cost, latency, balanced, custom
    fallback_providers UUID[] DEFAULT '{}',
    model_aliases JSONB DEFAULT '{}',
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. User LLM settings table
CREATE TABLE IF NOT EXISTS user_llm_settings (
    user_id VARCHAR(255) PRIMARY KEY,
    power_level VARCHAR(50) DEFAULT 'balanced',  -- eco, balanced, precision
    byok_providers JSONB DEFAULT '{}',  -- encrypted user API keys
    credit_balance DECIMAL(10, 2) DEFAULT 0,
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Usage logs table (for analytics)
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),
    provider_id UUID REFERENCES llm_providers(id) ON DELETE SET NULL,
    model_name VARCHAR(255),
    request_tokens INTEGER DEFAULT 0,
    response_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,
    latency_ms INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_providers_enabled ON llm_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_providers_priority ON llm_providers(priority DESC);
CREATE INDEX IF NOT EXISTS idx_models_provider ON llm_models(provider_id);
CREATE INDEX IF NOT EXISTS idx_models_enabled ON llm_models(enabled);
CREATE INDEX IF NOT EXISTS idx_usage_user ON llm_usage_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_usage_provider ON llm_usage_logs(provider_id);
CREATE INDEX IF NOT EXISTS idx_usage_created ON llm_usage_logs(created_at DESC);

-- Insert default routing rule if none exists
INSERT INTO llm_routing_rules (strategy, config)
SELECT 'balanced', '{"weights": {"cost": 0.3, "latency": 0.3, "quality": 0.4}}'::jsonb
WHERE NOT EXISTS (SELECT 1 FROM llm_routing_rules LIMIT 1);

-- Grant permissions (adjust username if needed)
GRANT ALL PRIVILEGES ON TABLE llm_providers TO unicorn;
GRANT ALL PRIVILEGES ON TABLE llm_models TO unicorn;
GRANT ALL PRIVILEGES ON TABLE llm_routing_rules TO unicorn;
GRANT ALL PRIVILEGES ON TABLE user_llm_settings TO unicorn;
GRANT ALL PRIVILEGES ON TABLE llm_usage_logs TO unicorn;

