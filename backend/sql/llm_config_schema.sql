-- LLM Configuration Database Schema
-- Manages AI servers and 3rd party API keys for Ops-Center

-- AI Server Configurations (vLLM, Ollama, llama.cpp, etc.)
CREATE TABLE IF NOT EXISTS ai_servers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    server_type TEXT NOT NULL,  -- vllm, ollama, llamacpp, openai-compatible
    base_url TEXT NOT NULL,
    api_key TEXT,  -- Optional, for protected endpoints
    model_path TEXT,  -- For vLLM/llama.cpp
    enabled BOOLEAN DEFAULT TRUE,
    use_for_chat BOOLEAN DEFAULT FALSE,
    use_for_embeddings BOOLEAN DEFAULT FALSE,
    use_for_reranking BOOLEAN DEFAULT FALSE,
    last_health_check TIMESTAMP,
    health_status TEXT,  -- healthy, degraded, down
    metadata JSONB DEFAULT '{}',  -- Additional config (tensor_parallel, gpu_memory, etc.)
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(name)
);

-- 3rd Party API Keys (encrypted with Fernet)
CREATE TABLE IF NOT EXISTS llm_api_keys (
    id SERIAL PRIMARY KEY,
    provider TEXT NOT NULL,  -- openrouter, openai, anthropic, google, cohere, etc.
    key_name TEXT NOT NULL,  -- Friendly name for UI
    encrypted_key TEXT NOT NULL,  -- Fernet encrypted API key
    enabled BOOLEAN DEFAULT TRUE,
    use_for_ops_center BOOLEAN DEFAULT FALSE,  -- Use for ops-center services
    last_used TIMESTAMP,
    requests_count INTEGER DEFAULT 0,
    tokens_used BIGINT DEFAULT 0,
    cost_usd NUMERIC(10, 4) DEFAULT 0,
    metadata JSONB DEFAULT '{}',  -- Rate limits, quotas, etc.
    created_by TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider, key_name)
);

-- Active Provider Configuration (which provider to use for each purpose)
CREATE TABLE IF NOT EXISTS active_providers (
    purpose TEXT PRIMARY KEY,  -- chat, embeddings, reranking
    provider_type TEXT NOT NULL,  -- ai_server, api_key
    provider_id INTEGER NOT NULL,  -- Reference to ai_servers.id or llm_api_keys.id
    fallback_provider_type TEXT,  -- Optional fallback
    fallback_provider_id INTEGER,
    updated_by TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit log for configuration changes
CREATE TABLE IF NOT EXISTS llm_config_audit (
    id SERIAL PRIMARY KEY,
    action TEXT NOT NULL,  -- add_server, update_server, delete_server, add_key, delete_key, set_active
    entity_type TEXT NOT NULL,  -- ai_server, api_key, active_provider
    entity_id INTEGER,
    user_id TEXT NOT NULL,
    changes JSONB,  -- What changed
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ai_servers_enabled ON ai_servers(enabled);
CREATE INDEX IF NOT EXISTS idx_ai_servers_type ON ai_servers(server_type);
CREATE INDEX IF NOT EXISTS idx_ai_servers_created_by ON ai_servers(created_by);
CREATE INDEX IF NOT EXISTS idx_llm_api_keys_provider ON llm_api_keys(provider);
CREATE INDEX IF NOT EXISTS idx_llm_api_keys_enabled ON llm_api_keys(enabled);
CREATE INDEX IF NOT EXISTS idx_llm_api_keys_created_by ON llm_api_keys(created_by);
CREATE INDEX IF NOT EXISTS idx_llm_config_audit_user ON llm_config_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_llm_config_audit_timestamp ON llm_config_audit(timestamp);

-- Comments for documentation
COMMENT ON TABLE ai_servers IS 'Self-hosted AI server configurations (vLLM, Ollama, llama.cpp)';
COMMENT ON TABLE llm_api_keys IS 'Encrypted 3rd party API keys (OpenRouter, OpenAI, Anthropic, etc.)';
COMMENT ON TABLE active_providers IS 'Which provider to use for each purpose (chat/embeddings/reranking)';
COMMENT ON TABLE llm_config_audit IS 'Audit trail for all LLM configuration changes';

COMMENT ON COLUMN ai_servers.server_type IS 'Type of AI server: vllm, ollama, llamacpp, openai-compatible';
COMMENT ON COLUMN ai_servers.health_status IS 'Current health status: healthy, degraded, down, unknown';
COMMENT ON COLUMN llm_api_keys.encrypted_key IS 'Fernet-encrypted API key (never stored in plaintext)';
COMMENT ON COLUMN active_providers.provider_type IS 'Which table to look up: ai_server or api_key';
