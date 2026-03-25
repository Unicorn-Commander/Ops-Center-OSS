-- Federation Routing Audit Log
-- Records every routing decision for debugging and compliance

CREATE TABLE IF NOT EXISTS federation_routing_audit (
    id VARCHAR(36) PRIMARY KEY,
    request_id VARCHAR(36),
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    service_type VARCHAR(50) NOT NULL,
    model VARCHAR(255),
    user_id VARCHAR(255),
    user_tier VARCHAR(50),
    candidates_found INTEGER DEFAULT 0,
    candidates_after_constraints INTEGER DEFAULT 0,
    constraints JSONB,
    selected_target VARCHAR(50),  -- local, peer, cloud, cloud_gpu, none
    selected_node_id VARCHAR(255),
    selected_reason TEXT,
    routing_score FLOAT,
    latency_ms INTEGER,
    outcome VARCHAR(20) NOT NULL DEFAULT 'routed',  -- routed, no_capacity, error, provisioning
    error TEXT
);

CREATE INDEX IF NOT EXISTS idx_routing_audit_timestamp ON federation_routing_audit(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_routing_audit_service ON federation_routing_audit(service_type);
CREATE INDEX IF NOT EXISTS idx_routing_audit_outcome ON federation_routing_audit(outcome);
CREATE INDEX IF NOT EXISTS idx_routing_audit_user ON federation_routing_audit(user_tier);

-- Auto-cleanup: remove entries older than 30 days (run via cron or pg_cron)
-- DELETE FROM federation_routing_audit WHERE timestamp < NOW() - INTERVAL '30 days';
