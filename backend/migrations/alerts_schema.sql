-- Alerts Management Database Schema
-- Version: 1.0.0
-- Author: Ops-Center Backend Team
-- Date: January 31, 2026
--
-- Purpose: Database tables for alert management system with Prometheus integration
--
-- This schema provides:
-- - Alert rules configuration (thresholds, intervals, enabled state)
-- - Alert history tracking (active, acknowledged, resolved)
-- - Integration hooks for Prometheus alerting

-- =============================================================================
-- ALERT RULES TABLE
-- Stores configurable alert rule definitions
-- =============================================================================

CREATE TABLE IF NOT EXISTS alert_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    metric VARCHAR(100) NOT NULL,
    description TEXT,
    warning_threshold DECIMAL(10,2),
    critical_threshold DECIMAL(10,2),
    comparison_operator VARCHAR(10) DEFAULT '>',  -- '>', '<', '>=', '<=', '==', '!='
    unit VARCHAR(50),  -- e.g., 'percent', 'bytes', 'ms', 'count'
    enabled BOOLEAN DEFAULT true,
    check_interval_seconds INTEGER DEFAULT 60,
    notification_channels TEXT[] DEFAULT ARRAY['email'],  -- email, slack, webhook
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (check_interval_seconds >= 10 AND check_interval_seconds <= 86400),
    CHECK (comparison_operator IN ('>', '<', '>=', '<=', '==', '!='))
);

-- Create indexes for alert rules
CREATE INDEX IF NOT EXISTS idx_alert_rules_enabled ON alert_rules(enabled);
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric ON alert_rules(metric);
CREATE INDEX IF NOT EXISTS idx_alert_rules_name ON alert_rules(name);

-- Add comment
COMMENT ON TABLE alert_rules IS 'Alert rule configurations for monitoring thresholds';
COMMENT ON COLUMN alert_rules.metric IS 'Prometheus metric name or internal metric identifier';
COMMENT ON COLUMN alert_rules.comparison_operator IS 'Comparison operator for threshold evaluation';


-- =============================================================================
-- ALERTS TABLE
-- Stores active and historical alert instances
-- =============================================================================

CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER REFERENCES alert_rules(id) ON DELETE SET NULL,
    severity VARCHAR(20) NOT NULL,  -- 'info', 'warning', 'critical'
    name VARCHAR(255) NOT NULL,
    message TEXT,
    source VARCHAR(100) DEFAULT 'system',  -- 'prometheus', 'grafana', 'system', 'manual'
    labels JSONB DEFAULT '{}',  -- Additional metadata labels
    value DECIMAL(15,4),  -- The metric value that triggered the alert
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'acknowledged', 'resolved'
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    acknowledge_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(255),
    resolution_note TEXT,

    -- Constraints
    CHECK (severity IN ('info', 'warning', 'critical')),
    CHECK (status IN ('active', 'acknowledged', 'resolved')),
    CHECK (source IN ('prometheus', 'grafana', 'system', 'manual'))
);

-- Create indexes for alerts
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_alerts_rule_id ON alerts(rule_id);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_active ON alerts(status) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_alerts_source ON alerts(source);

-- Composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON alerts(status, severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_status ON alerts(created_at DESC, status);

-- Add comments
COMMENT ON TABLE alerts IS 'Alert instances (active and historical)';
COMMENT ON COLUMN alerts.labels IS 'Additional metadata labels in JSON format';
COMMENT ON COLUMN alerts.value IS 'The metric value that triggered this alert';


-- =============================================================================
-- ALERT NOTIFICATIONS TABLE
-- Tracks notification delivery for alerts
-- =============================================================================

CREATE TABLE IF NOT EXISTS alert_notifications (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,  -- email, slack, webhook
    recipient VARCHAR(255) NOT NULL,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'sent',  -- sent, failed, pending
    error_message TEXT,
    metadata JSONB DEFAULT '{}',

    CHECK (channel IN ('email', 'slack', 'webhook', 'pagerduty')),
    CHECK (status IN ('sent', 'failed', 'pending'))
);

CREATE INDEX IF NOT EXISTS idx_alert_notifications_alert_id ON alert_notifications(alert_id);
CREATE INDEX IF NOT EXISTS idx_alert_notifications_sent_at ON alert_notifications(sent_at DESC);

COMMENT ON TABLE alert_notifications IS 'Tracks notification delivery for alerts';


-- =============================================================================
-- UPDATE TIMESTAMP TRIGGER
-- =============================================================================

CREATE OR REPLACE FUNCTION update_alert_rules_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_alert_rules_timestamp ON alert_rules;
CREATE TRIGGER trigger_update_alert_rules_timestamp
    BEFORE UPDATE ON alert_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_alert_rules_timestamp();


-- =============================================================================
-- SEED DEFAULT ALERT RULES
-- Common monitoring rules for system health
-- =============================================================================

INSERT INTO alert_rules (name, metric, description, warning_threshold, critical_threshold, comparison_operator, unit, check_interval_seconds)
VALUES
    ('CPU Usage High', 'cpu_usage_percent', 'CPU utilization exceeds threshold', 70.00, 90.00, '>', 'percent', 60),
    ('Memory Usage High', 'memory_usage_percent', 'Memory utilization exceeds threshold', 80.00, 95.00, '>', 'percent', 60),
    ('Disk Usage High', 'disk_usage_percent', 'Disk space utilization exceeds threshold', 75.00, 90.00, '>', 'percent', 300),
    ('GPU Memory Usage High', 'gpu_memory_percent', 'GPU memory utilization exceeds threshold', 85.00, 95.00, '>', 'percent', 60),
    ('Service Response Time', 'response_time_ms', 'Service response time exceeds threshold', 1000.00, 5000.00, '>', 'ms', 30),
    ('Error Rate High', 'error_rate_percent', 'Error rate exceeds threshold', 1.00, 5.00, '>', 'percent', 60),
    ('API Latency High', 'api_latency_p99', 'API P99 latency exceeds threshold', 500.00, 2000.00, '>', 'ms', 60),
    ('Database Connection Pool', 'db_pool_usage_percent', 'Database connection pool utilization', 70.00, 90.00, '>', 'percent', 60),
    ('Redis Memory Usage', 'redis_memory_percent', 'Redis memory utilization', 75.00, 90.00, '>', 'percent', 120),
    ('Container Restarts', 'container_restarts', 'Container restart count in last hour', 3.00, 10.00, '>', 'count', 300)
ON CONFLICT (name) DO NOTHING;


-- =============================================================================
-- GRANT PERMISSIONS
-- =============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE ON alert_rules TO unicorn;
GRANT SELECT, INSERT, UPDATE, DELETE ON alerts TO unicorn;
GRANT SELECT, INSERT, UPDATE ON alert_notifications TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE alert_rules_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE alerts_id_seq TO unicorn;
GRANT USAGE, SELECT ON SEQUENCE alert_notifications_id_seq TO unicorn;


-- =============================================================================
-- VIEWS FOR COMMON QUERIES
-- =============================================================================

-- View for active alerts with rule information
CREATE OR REPLACE VIEW active_alerts_view AS
SELECT
    a.id,
    a.name,
    a.severity,
    a.message,
    a.source,
    a.status,
    a.value,
    a.labels,
    a.created_at,
    a.acknowledged_by,
    a.acknowledged_at,
    r.metric,
    r.warning_threshold,
    r.critical_threshold,
    r.unit
FROM alerts a
LEFT JOIN alert_rules r ON a.rule_id = r.id
WHERE a.status IN ('active', 'acknowledged')
ORDER BY
    CASE a.severity
        WHEN 'critical' THEN 1
        WHEN 'warning' THEN 2
        ELSE 3
    END,
    a.created_at DESC;

GRANT SELECT ON active_alerts_view TO unicorn;


-- View for alert statistics
CREATE OR REPLACE VIEW alert_statistics_view AS
SELECT
    COUNT(*) FILTER (WHERE status = 'active') AS active_count,
    COUNT(*) FILTER (WHERE status = 'acknowledged') AS acknowledged_count,
    COUNT(*) FILTER (WHERE status = 'resolved' AND resolved_at > NOW() - INTERVAL '24 hours') AS resolved_24h_count,
    COUNT(*) FILTER (WHERE severity = 'critical' AND status = 'active') AS critical_active,
    COUNT(*) FILTER (WHERE severity = 'warning' AND status = 'active') AS warning_active,
    COUNT(*) FILTER (WHERE severity = 'info' AND status = 'active') AS info_active,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '24 hours') AS total_24h,
    COUNT(*) FILTER (WHERE created_at > NOW() - INTERVAL '7 days') AS total_7d
FROM alerts;

GRANT SELECT ON alert_statistics_view TO unicorn;
