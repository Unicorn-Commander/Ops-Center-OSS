-- ==============================================================================
-- Federation Schema
-- ==============================================================================
-- Database: unicorn_db
-- Purpose: Multi-node federation for distributed inference routing,
--          service discovery, and cross-node usage tracking.
--
-- Tables:
--   federation_nodes       - UC-Cloud instances in the federation mesh
--   federation_services    - Inference services available on each node
--   federation_usage       - Cross-node request tracking for billing/analytics
--   federation_peers       - Optional trust relationships between nodes
--
-- Created: 2026-03-20
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==============================================================================
-- ENUM TYPES
-- ==============================================================================

DO $$ BEGIN
    CREATE TYPE federation_node_status AS ENUM ('online', 'offline', 'degraded');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE inference_service_type AS ENUM (
        'llm', 'tts', 'stt', 'embeddings', 'image_gen', 'music_gen', 'reranker'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Add agents type to existing enum (idempotent)
DO $$
BEGIN
    ALTER TYPE inference_service_type ADD VALUE IF NOT EXISTS 'agents';
EXCEPTION WHEN duplicate_object THEN
    NULL;
END $$;

-- ==============================================================================
-- TABLE: federation_nodes
-- Purpose: Each row represents a UC-Cloud instance in the federation mesh.
--          One row should have is_self=true to identify the local node.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS federation_nodes (
    -- Primary key (UUID)
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::VARCHAR(36),

    -- Unique human-readable slug (e.g. "yoda", "tensor-01")
    node_id VARCHAR(255) NOT NULL UNIQUE,

    -- Display name shown in admin UI
    display_name VARCHAR(255) NOT NULL,

    -- Base URL for API calls to this node
    endpoint_url VARCHAR(512) NOT NULL,

    -- Authentication method: jwt, mtls, or api_key
    auth_method VARCHAR(50) NOT NULL DEFAULT 'api_key',

    -- Encrypted credential material (JWT secret, mTLS cert, API key)
    auth_credential TEXT,

    -- Hardware profile: GPUs, CPU cores, RAM, NPU info (JSON)
    hardware_profile JSONB,

    -- Array of role values: inference, gateway, billing, full (JSON)
    roles JSONB,

    -- Current node status
    status federation_node_status NOT NULL DEFAULT 'offline',

    -- Human-readable status detail
    status_message TEXT,

    -- Last successful heartbeat timestamp
    last_heartbeat TIMESTAMP,

    -- When this node was first registered
    registered_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Last modification timestamp
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Region hint for latency-based routing (e.g. "us-west", "eu-central")
    region VARCHAR(100),

    -- True for the local node entry
    is_self BOOLEAN NOT NULL DEFAULT FALSE
);

COMMENT ON TABLE federation_nodes IS
    'UC-Cloud instances participating in the federation mesh. '
    'Each node advertises its hardware, roles, and available services.';

COMMENT ON COLUMN federation_nodes.node_id IS
    'Unique human-readable slug identifying this node (e.g. "yoda", "tensor-01")';

COMMENT ON COLUMN federation_nodes.auth_credential IS
    'Encrypted credential material for authenticating to this node. '
    'Content depends on auth_method (JWT secret, mTLS certificate, or API key).';

COMMENT ON COLUMN federation_nodes.hardware_profile IS
    'JSON object describing hardware: {"gpus": [...], "cpu": "...", "ram_gb": 128, "npu": null}';

COMMENT ON COLUMN federation_nodes.roles IS
    'JSON array of roles this node serves: ["inference", "gateway", "billing", "full"]';

COMMENT ON COLUMN federation_nodes.is_self IS
    'Marks the row that represents the local node. Exactly one row should have is_self=true.';

-- ==============================================================================
-- TABLE: federation_services
-- Purpose: Inference services available on each federation node.
--          Used for service discovery and intelligent routing.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS federation_services (
    -- Primary key (UUID)
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::VARCHAR(36),

    -- Parent node (CASCADE on delete)
    node_id VARCHAR(36) NOT NULL REFERENCES federation_nodes(id) ON DELETE CASCADE,

    -- Type of inference service
    service_type inference_service_type NOT NULL,

    -- Array of model IDs this service can run (JSON)
    models JSONB,

    -- Relative endpoint path (e.g. "/v1/chat/completions")
    endpoint_path VARCHAR(512),

    -- Service status: running, stopped, error, unknown
    status VARCHAR(50) NOT NULL DEFAULT 'unknown',

    -- Capabilities: batch_size, max_context, quantization, etc. (JSON)
    capabilities JSONB,

    -- Expected cold start time in seconds
    cold_start_seconds INTEGER,

    -- Rolling average response latency in milliseconds
    avg_latency_ms INTEGER,

    -- Estimated cost in USD for metered cross-node routing
    cost_usd DOUBLE PRECISION,

    -- Last modification timestamp
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE federation_services IS
    'Inference services available on federation nodes. '
    'Each service describes its type, supported models, and performance characteristics.';

COMMENT ON COLUMN federation_services.models IS
    'JSON array of model IDs this service supports, e.g. ["Qwen3.5-27B-Q4_K_M", "bge-m3"]';

COMMENT ON COLUMN federation_services.capabilities IS
    'JSON object with service capabilities: {"max_context": 49152, "batch_size": 8, "quantization": "Q4_K_M"}';

COMMENT ON COLUMN federation_services.cost_usd IS
    'Optional per-request cost in USD. Used for cost-aware routing decisions.';

-- ==============================================================================
-- TABLE: federation_usage
-- Purpose: Tracks cross-node inference requests for billing reconciliation
--          and federation analytics.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS federation_usage (
    -- Primary key (UUID)
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::VARCHAR(36),

    -- Node that originated the request
    source_node_id VARCHAR(255) NOT NULL,

    -- Node that served the request
    target_node_id VARCHAR(255) NOT NULL,

    -- Type of inference service used
    service_type inference_service_type NOT NULL,

    -- Model identifier used for the request
    model VARCHAR(255),

    -- Input token count
    tokens_in INTEGER,

    -- Output token count
    tokens_out INTEGER,

    -- Total request duration in milliseconds
    duration_ms INTEGER,

    -- Computed cost in USD
    cost_usd DOUBLE PRECISION,

    -- Keycloak user ID, if known
    user_id VARCHAR(255),

    -- When this usage event occurred
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE federation_usage IS
    'Audit log of cross-node inference requests. '
    'Used for billing reconciliation, capacity planning, and federation analytics.';

COMMENT ON COLUMN federation_usage.source_node_id IS
    'Node ID (slug) of the node that originated the request';

COMMENT ON COLUMN federation_usage.target_node_id IS
    'Node ID (slug) of the node that served the request';

-- ==============================================================================
-- TABLE: federation_peers
-- Purpose: Bidirectional trust relationships between federation nodes.
--          Controls what operations a remote node is allowed to perform.
-- ==============================================================================

CREATE TABLE IF NOT EXISTS federation_peers (
    -- Primary key (UUID)
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4()::VARCHAR(36),

    -- Local side of the peering relationship
    local_node_id VARCHAR(36) NOT NULL REFERENCES federation_nodes(id) ON DELETE CASCADE,

    -- Remote side of the peering relationship
    remote_node_id VARCHAR(36) NOT NULL REFERENCES federation_nodes(id) ON DELETE CASCADE,

    -- Trust level: full, inference_only, read_only
    trust_level VARCHAR(50) NOT NULL DEFAULT 'read_only',

    -- When the peering was established
    established_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Last time this peering was cryptographically verified
    last_verified TIMESTAMP,

    -- Whether this peering is currently active
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE federation_peers IS
    'Trust relationships between federation nodes. '
    'trust_level controls what the remote node may do: '
    'full (all operations), inference_only (send inference requests), read_only (service discovery only).';

-- ==============================================================================
-- INDEXES
-- ==============================================================================

-- federation_nodes
CREATE INDEX IF NOT EXISTS idx_federation_nodes_node_id
    ON federation_nodes(node_id);

CREATE INDEX IF NOT EXISTS idx_federation_nodes_status
    ON federation_nodes(status);

CREATE INDEX IF NOT EXISTS idx_federation_nodes_last_heartbeat
    ON federation_nodes(last_heartbeat DESC);

-- federation_services
CREATE INDEX IF NOT EXISTS idx_federation_services_node_id
    ON federation_services(node_id);

CREATE INDEX IF NOT EXISTS idx_federation_services_service_type
    ON federation_services(service_type);

CREATE INDEX IF NOT EXISTS idx_federation_services_status
    ON federation_services(status);

-- Composite index for routing queries: find running services of a given type
CREATE INDEX IF NOT EXISTS idx_federation_services_type_status
    ON federation_services(service_type, status)
    WHERE status = 'running';

-- federation_usage
CREATE INDEX IF NOT EXISTS idx_federation_usage_created_at
    ON federation_usage(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_federation_usage_source_node
    ON federation_usage(source_node_id);

CREATE INDEX IF NOT EXISTS idx_federation_usage_target_node
    ON federation_usage(target_node_id);

CREATE INDEX IF NOT EXISTS idx_federation_usage_service_type
    ON federation_usage(service_type);

-- federation_peers
CREATE INDEX IF NOT EXISTS idx_federation_peers_local_node
    ON federation_peers(local_node_id);

CREATE INDEX IF NOT EXISTS idx_federation_peers_remote_node
    ON federation_peers(remote_node_id);

CREATE INDEX IF NOT EXISTS idx_federation_peers_active
    ON federation_peers(is_active)
    WHERE is_active = TRUE;

-- ==============================================================================
-- GRANTS
-- ==============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON federation_nodes TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON federation_services TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON federation_usage TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON federation_peers TO unicorn;

-- ==============================================================================
-- COMPLETION NOTICE
-- ==============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Federation schema created successfully';
    RAISE NOTICE 'Tables: federation_nodes, federation_services, federation_usage, federation_peers';
    RAISE NOTICE 'Enums: federation_node_status, inference_service_type';
    RAISE NOTICE 'Indexes: 12 total';
END $$;

-- ==============================================================================
-- MIGRATION COMPLETE
-- ==============================================================================
-- To apply: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/federation_schema.sql
-- To verify: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d federation_nodes"
-- To check: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT * FROM federation_nodes;"
