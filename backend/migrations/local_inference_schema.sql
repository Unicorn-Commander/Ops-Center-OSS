-- ============================================================================
-- Local Inference Module Schema Migration
-- Version: 009
-- Created: January 24, 2026
-- Description: Create tables for local inference module supporting llama.cpp,
--              Ollama, and vLLM providers with GPU device tracking
-- ============================================================================

-- ============================================================================
-- Table: local_inference_config
-- Purpose: Store global configuration settings for the local inference module
-- ============================================================================

DROP TABLE IF EXISTS model_usage_log CASCADE;
DROP TABLE IF EXISTS local_models CASCADE;
DROP TABLE IF EXISTS gpu_devices CASCADE;
DROP TABLE IF EXISTS local_inference_providers CASCADE;
DROP TABLE IF EXISTS local_inference_config CASCADE;

CREATE TABLE IF NOT EXISTS local_inference_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,       -- Configuration key (e.g., 'module_enabled', 'llama_cpp_settings')
    config_value JSONB NOT NULL,                   -- JSON configuration value
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE local_inference_config IS 'Global configuration settings for the local inference module';
COMMENT ON COLUMN local_inference_config.config_key IS 'Unique configuration key identifier';
COMMENT ON COLUMN local_inference_config.config_value IS 'JSON configuration value - can store complex nested settings';

-- ============================================================================
-- Table: local_inference_providers
-- Purpose: Track supported inference providers and their connection status
-- ============================================================================

CREATE TABLE IF NOT EXISTS local_inference_providers (
    id SERIAL PRIMARY KEY,
    provider_name VARCHAR(50) UNIQUE NOT NULL,     -- Provider identifier: 'llama_cpp', 'ollama', 'vllm'
    display_name VARCHAR(100) NOT NULL,            -- Human-readable name
    enabled BOOLEAN DEFAULT false,                 -- Whether this provider is active
    url VARCHAR(500),                              -- Provider API URL (e.g., http://localhost:11434 for Ollama)
    settings JSONB DEFAULT '{}',                   -- Provider-specific settings
    last_health_check TIMESTAMP,                   -- Last successful health check timestamp
    health_status VARCHAR(20),                     -- Status: 'healthy', 'unhealthy', 'unknown'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_health_status CHECK (health_status IN ('healthy', 'unhealthy', 'unknown'))
);

COMMENT ON TABLE local_inference_providers IS 'Supported local inference providers (llama.cpp, Ollama, vLLM)';
COMMENT ON COLUMN local_inference_providers.provider_name IS 'Unique provider identifier used in code';
COMMENT ON COLUMN local_inference_providers.display_name IS 'User-friendly display name';
COMMENT ON COLUMN local_inference_providers.url IS 'Base URL for the provider API';
COMMENT ON COLUMN local_inference_providers.settings IS 'Provider-specific configuration (threads, batch_size, etc.)';
COMMENT ON COLUMN local_inference_providers.health_status IS 'Current health status from last check';

-- ============================================================================
-- Table: gpu_devices
-- Purpose: Track available GPU devices for inference workloads
-- ============================================================================

CREATE TABLE IF NOT EXISTS gpu_devices (
    id SERIAL PRIMARY KEY,
    device_index INT NOT NULL,                     -- GPU index (0, 1, 2, etc.)
    device_name VARCHAR(255),                      -- GPU model name (e.g., 'NVIDIA Tesla P40')
    memory_total_mb INT,                           -- Total VRAM in MB
    compute_capability VARCHAR(20),                -- CUDA compute capability (e.g., '6.1')
    driver_version VARCHAR(50),                    -- NVIDIA driver version
    last_seen TIMESTAMP DEFAULT NOW(),             -- Last time device was detected
    metadata JSONB DEFAULT '{}',                   -- Additional device info (temperature, utilization, etc.)
    UNIQUE(device_index)
);

COMMENT ON TABLE gpu_devices IS 'Available GPU devices detected on the system';
COMMENT ON COLUMN gpu_devices.device_index IS 'Zero-based GPU index from nvidia-smi';
COMMENT ON COLUMN gpu_devices.device_name IS 'GPU model name from nvidia-smi';
COMMENT ON COLUMN gpu_devices.memory_total_mb IS 'Total video memory in megabytes';
COMMENT ON COLUMN gpu_devices.compute_capability IS 'CUDA compute capability for compatibility checks';
COMMENT ON COLUMN gpu_devices.metadata IS 'Extended device info: pcie_link, power_limit, etc.';

-- ============================================================================
-- Table: local_models
-- Purpose: Track locally available models and their configurations
-- ============================================================================

CREATE TABLE IF NOT EXISTS local_models (
    id SERIAL PRIMARY KEY,
    provider_id INT REFERENCES local_inference_providers(id) ON DELETE CASCADE,
    model_id VARCHAR(500) NOT NULL,                -- Model identifier from provider (e.g., 'llama2:7b')
    display_name VARCHAR(255),                     -- User-friendly model name
    file_path VARCHAR(1000),                       -- Path to model file (for llama.cpp GGUF files)
    size_bytes BIGINT,                             -- Model file size in bytes
    quantization VARCHAR(50),                      -- Quantization type (Q4_K_M, Q5_K_S, F16, etc.)
    parameters JSONB DEFAULT '{}',                 -- Model parameters: ctx_size, gpu_layers, rope_scaling, etc.
    auto_load BOOLEAN DEFAULT false,               -- Load this model on startup
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(provider_id, model_id)
);

COMMENT ON TABLE local_models IS 'Locally available models configured for inference';
COMMENT ON COLUMN local_models.provider_id IS 'Reference to the inference provider';
COMMENT ON COLUMN local_models.model_id IS 'Provider-specific model identifier';
COMMENT ON COLUMN local_models.file_path IS 'Filesystem path to model file (primarily for llama.cpp)';
COMMENT ON COLUMN local_models.size_bytes IS 'Model file size for disk space tracking';
COMMENT ON COLUMN local_models.quantization IS 'Quantization method (affects quality vs speed/memory)';
COMMENT ON COLUMN local_models.parameters IS 'Model config: ctx_size, gpu_layers, n_batch, rope_freq_base, etc.';
COMMENT ON COLUMN local_models.auto_load IS 'If true, model is loaded when provider starts';

-- ============================================================================
-- Table: model_usage_log
-- Purpose: Track model usage for analytics and debugging
-- ============================================================================

CREATE TABLE IF NOT EXISTS model_usage_log (
    id SERIAL PRIMARY KEY,
    model_id INT REFERENCES local_models(id) ON DELETE SET NULL,
    user_id VARCHAR(255),                          -- User who performed the action (Keycloak sub)
    action VARCHAR(50) NOT NULL,                   -- Action: 'load', 'unload', 'inference'
    details JSONB DEFAULT '{}',                    -- Action details: tokens, duration, error, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT valid_action CHECK (action IN ('load', 'unload', 'inference', 'error', 'config_change'))
);

COMMENT ON TABLE model_usage_log IS 'Audit log for model operations and inference tracking';
COMMENT ON COLUMN model_usage_log.model_id IS 'Reference to the model (nullable for deleted models)';
COMMENT ON COLUMN model_usage_log.user_id IS 'Keycloak user sub who performed the action';
COMMENT ON COLUMN model_usage_log.action IS 'Type of action: load, unload, inference, error, config_change';
COMMENT ON COLUMN model_usage_log.details IS 'Action-specific details: tokens_in, tokens_out, duration_ms, error_message, etc.';

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- local_inference_config indexes
CREATE INDEX IF NOT EXISTS idx_local_inference_config_key ON local_inference_config(config_key);

-- local_inference_providers indexes
CREATE INDEX IF NOT EXISTS idx_local_inference_providers_name ON local_inference_providers(provider_name);
CREATE INDEX IF NOT EXISTS idx_local_inference_providers_enabled ON local_inference_providers(enabled);
CREATE INDEX IF NOT EXISTS idx_local_inference_providers_health ON local_inference_providers(health_status);

-- gpu_devices indexes
CREATE INDEX IF NOT EXISTS idx_gpu_devices_index ON gpu_devices(device_index);
CREATE INDEX IF NOT EXISTS idx_gpu_devices_last_seen ON gpu_devices(last_seen);

-- local_models indexes
CREATE INDEX IF NOT EXISTS idx_local_models_provider ON local_models(provider_id);
CREATE INDEX IF NOT EXISTS idx_local_models_model_id ON local_models(model_id);
CREATE INDEX IF NOT EXISTS idx_local_models_auto_load ON local_models(auto_load);
CREATE INDEX IF NOT EXISTS idx_local_models_provider_model ON local_models(provider_id, model_id);

-- model_usage_log indexes (optimized for common queries)
CREATE INDEX IF NOT EXISTS idx_model_usage_log_model ON model_usage_log(model_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_log_user ON model_usage_log(user_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_log_action ON model_usage_log(action);
CREATE INDEX IF NOT EXISTS idx_model_usage_log_created ON model_usage_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_model_usage_log_model_created ON model_usage_log(model_id, created_at DESC);

-- ============================================================================
-- Trigger Function: Update updated_at Timestamp
-- ============================================================================

CREATE OR REPLACE FUNCTION update_local_inference_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers: Auto-update updated_at on Modification
-- ============================================================================

DROP TRIGGER IF EXISTS trigger_update_local_inference_config_timestamp ON local_inference_config;
CREATE TRIGGER trigger_update_local_inference_config_timestamp
    BEFORE UPDATE ON local_inference_config
    FOR EACH ROW
    EXECUTE FUNCTION update_local_inference_timestamp();

DROP TRIGGER IF EXISTS trigger_update_local_inference_providers_timestamp ON local_inference_providers;
CREATE TRIGGER trigger_update_local_inference_providers_timestamp
    BEFORE UPDATE ON local_inference_providers
    FOR EACH ROW
    EXECUTE FUNCTION update_local_inference_timestamp();

DROP TRIGGER IF EXISTS trigger_update_local_models_timestamp ON local_models;
CREATE TRIGGER trigger_update_local_models_timestamp
    BEFORE UPDATE ON local_models
    FOR EACH ROW
    EXECUTE FUNCTION update_local_inference_timestamp();

-- ============================================================================
-- Default Data: Providers
-- ============================================================================

INSERT INTO local_inference_providers (provider_name, display_name, enabled, url, settings, health_status) VALUES
    ('llama_cpp', 'llama.cpp Server', false, 'http://localhost:8080',
     '{"threads": 8, "batch_size": 512, "context_size": 4096, "gpu_layers": 99}',
     'unknown'),
    ('ollama', 'Ollama', false, 'http://localhost:11434',
     '{"num_parallel": 4, "max_loaded_models": 2}',
     'unknown'),
    ('vllm', 'vLLM', false, 'http://localhost:8000',
     '{"tensor_parallel_size": 1, "gpu_memory_utilization": 0.95, "max_model_len": 16384}',
     'unknown')
ON CONFLICT (provider_name) DO UPDATE SET
    display_name = EXCLUDED.display_name,
    settings = EXCLUDED.settings;

-- ============================================================================
-- Default Data: Configuration
-- ============================================================================

INSERT INTO local_inference_config (config_key, config_value) VALUES
    ('module_enabled', 'false'::jsonb),
    ('default_provider', '"llama_cpp"'::jsonb),
    ('auto_detect_gpus', 'true'::jsonb),
    ('health_check_interval_seconds', '30'::jsonb),
    ('llama_cpp_settings', '{
        "server_path": "/usr/local/bin/llama-server",
        "model_directory": "/models",
        "default_context_size": 4096,
        "default_gpu_layers": 99,
        "default_threads": 8
    }'::jsonb),
    ('ollama_settings', '{
        "auto_pull_models": false,
        "keep_alive": "5m"
    }'::jsonb),
    ('vllm_settings', '{
        "tensor_parallel_size": 1,
        "gpu_memory_utilization": 0.95,
        "dtype": "auto",
        "quantization": null
    }'::jsonb)
ON CONFLICT (config_key) DO UPDATE SET
    config_value = EXCLUDED.config_value;

-- ============================================================================
-- Grant Permissions
-- ============================================================================

-- Grant read access to application user
GRANT SELECT ON local_inference_config TO unicorn;
GRANT SELECT ON local_inference_providers TO unicorn;
GRANT SELECT ON local_models TO unicorn;
GRANT SELECT ON gpu_devices TO unicorn;
GRANT SELECT ON model_usage_log TO unicorn;

-- Grant write access for admin operations
GRANT INSERT, UPDATE, DELETE ON local_inference_config TO unicorn;
GRANT INSERT, UPDATE, DELETE ON local_inference_providers TO unicorn;
GRANT INSERT, UPDATE, DELETE ON local_models TO unicorn;
GRANT INSERT, UPDATE, DELETE ON gpu_devices TO unicorn;
GRANT INSERT, UPDATE, DELETE ON model_usage_log TO unicorn;

-- Grant sequence usage
GRANT USAGE, SELECT ON SEQUENCE local_inference_config_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE local_inference_providers_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE local_models_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE gpu_devices_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE model_usage_log_id_seq TO unicorn;

-- ============================================================================
-- Verification Queries (for testing)
-- ============================================================================

-- Uncomment to verify installation:
-- SELECT * FROM local_inference_config ORDER BY config_key;
-- SELECT * FROM local_inference_providers ORDER BY provider_name;
-- SELECT * FROM gpu_devices ORDER BY device_index;
-- SELECT COUNT(*) as config_count FROM local_inference_config;
-- SELECT COUNT(*) as provider_count FROM local_inference_providers;

-- ============================================================================
-- Migration Complete
-- ============================================================================
-- Created tables:
--   - local_inference_config (global settings)
--   - local_inference_providers (llama.cpp, Ollama, vLLM)
--   - gpu_devices (GPU hardware tracking)
--   - local_models (available models)
--   - model_usage_log (usage tracking)
--
-- Created indexes: 14 indexes for query performance
-- Created triggers: 3 triggers for updated_at timestamps
-- Seeded data: 3 providers (disabled), 7 config entries
-- ============================================================================
