-- Colonel AI Agent Schema
-- Phase 1: Core tables for colonel configuration, sessions, and audit

-- ─── Colonel Instances ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS colonels (
    id VARCHAR(64) PRIMARY KEY DEFAULT 'default',
    config_json JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMENT ON TABLE colonels IS 'Colonel AI agent instances and their configuration';

-- Insert default colonel if not exists
INSERT INTO colonels (id, config_json)
VALUES ('default', '{
    "name": "Col. Corelli",
    "server_name": "Yoda",
    "mission": "devops",
    "personality": {"formality": 7, "verbosity": 5, "humor": 4},
    "model": "anthropic/claude-sonnet-4-5-20250929",
    "enabled_skills": ["docker-management", "bash-execution", "system-status", "service-health", "log-viewer"],
    "admin_only": true,
    "onboarded": false
}')
ON CONFLICT (id) DO NOTHING;


-- ─── Colonel Sessions (metadata only, messages in Redis) ──────────────────

CREATE TABLE IF NOT EXISTS colonel_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    colonel_id VARCHAR(64) REFERENCES colonels(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(255),
    message_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_colonel_sessions_user ON colonel_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_colonel_sessions_activity ON colonel_sessions(last_activity DESC);

COMMENT ON TABLE colonel_sessions IS 'Colonel chat session metadata (messages stored in Redis)';


-- ─── Colonel Audit Log ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS colonel_audit_log (
    id BIGSERIAL PRIMARY KEY,
    colonel_id VARCHAR(64) NOT NULL DEFAULT 'default',
    session_id VARCHAR(255),
    user_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,  -- 'skill_exec', 'config_change', 'chat', 'error'
    skill_name VARCHAR(100),
    action_name VARCHAR(100),
    parameters JSONB,
    result_summary TEXT,
    success BOOLEAN DEFAULT TRUE,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_colonel_audit_time ON colonel_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_colonel_audit_user ON colonel_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_colonel_audit_type ON colonel_audit_log(action_type);
CREATE INDEX IF NOT EXISTS idx_colonel_audit_skill ON colonel_audit_log(skill_name);

COMMENT ON TABLE colonel_audit_log IS 'Immutable audit log of all Colonel actions';


-- ─── Grant permissions ────────────────────────────────────────────────────

-- Ensure the unicorn user has access (matches existing DB setup)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unicorn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO unicorn;
