-- Model Server Management Tables for UC-1 Pro Ops Center
-- Migration: 001_model_servers.sql
-- Created: 2025-01-19

-- Server configurations
CREATE TABLE IF NOT EXISTS model_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    server_type VARCHAR(50) NOT NULL, -- 'vllm', 'ollama', 'embedding', 'reranking'
    base_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(500), -- Will be encrypted
    is_active BOOLEAN DEFAULT true,
    capabilities JSONB DEFAULT '{}'::jsonb, -- {"inference": true, "training": false, ...}
    metadata JSONB DEFAULT '{}'::jsonb, -- Custom fields per server type
    last_health_check TIMESTAMP,
    health_status VARCHAR(50) DEFAULT 'unknown', -- 'online', 'offline', 'degraded', 'unknown'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Available models on servers
CREATE TABLE IF NOT EXISTS server_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID REFERENCES model_servers(id) ON DELETE CASCADE,
    model_id VARCHAR(500) NOT NULL,
    model_name VARCHAR(500),
    model_size BIGINT, -- Size in bytes
    quantization VARCHAR(50),
    context_length INTEGER,
    capabilities JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(50) DEFAULT 'available', -- 'loaded', 'available', 'downloading'
    last_used TIMESTAMP,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Model routing rules
CREATE TABLE IF NOT EXISTS model_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_pattern VARCHAR(500), -- Regex or exact match
    server_priorities JSONB DEFAULT '[]'::jsonb, -- [{"server_id": "...", "priority": 1}, ...]
    load_balancing_strategy VARCHAR(50) DEFAULT 'round_robin', -- 'round_robin', 'least_loaded'
    fallback_behavior VARCHAR(50) DEFAULT 'next_priority', -- 'next_priority', 'fail'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Server metrics history (for monitoring)
CREATE TABLE IF NOT EXISTS server_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID REFERENCES model_servers(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT NOW(),
    cpu_percent FLOAT,
    memory_percent FLOAT,
    gpu_percent FLOAT,
    gpu_memory_used BIGINT,
    gpu_memory_total BIGINT,
    active_requests INTEGER,
    total_requests BIGINT,
    avg_response_time FLOAT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_model_servers_type ON model_servers(server_type);
CREATE INDEX IF NOT EXISTS idx_model_servers_health ON model_servers(health_status);
CREATE INDEX IF NOT EXISTS idx_server_models_server ON server_models(server_id);
CREATE INDEX IF NOT EXISTS idx_server_models_status ON server_models(status);
CREATE INDEX IF NOT EXISTS idx_server_metrics_server_time ON server_metrics(server_id, timestamp DESC);

-- Create update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_model_servers_updated_at BEFORE UPDATE ON model_servers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_server_models_updated_at BEFORE UPDATE ON server_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_routes_updated_at BEFORE UPDATE ON model_routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();