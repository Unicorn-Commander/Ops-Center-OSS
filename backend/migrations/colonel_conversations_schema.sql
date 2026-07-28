-- Colonel Conversations Persistence Schema
-- Adds durable PostgreSQL storage for Colonel chat conversations.
-- Redis remains the primary fast store; PostgreSQL is the durable backup.
--
-- Run: docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/this/file.sql

-- ─── Conversations Table ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS colonel_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL UNIQUE,
    user_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    colonel_name VARCHAR(100) DEFAULT 'Col. Corelli',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'
);

COMMENT ON TABLE colonel_conversations IS 'Durable storage for Colonel chat conversations (Redis is the fast primary store)';

CREATE INDEX IF NOT EXISTS idx_colonel_conversations_user ON colonel_conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_colonel_conversations_session ON colonel_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_colonel_conversations_updated ON colonel_conversations(updated_at DESC);


-- ─── Messages Table ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS colonel_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES colonel_conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,
    message_index INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',  -- tool_call_id, tool_calls, name, token counts, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE colonel_messages IS 'Individual messages within Colonel conversations';

CREATE INDEX IF NOT EXISTS idx_colonel_messages_conversation ON colonel_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_colonel_messages_index ON colonel_messages(conversation_id, message_index);


-- ─── Grant Permissions ──────────────────────────────────────────────────────

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO unicorn;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO unicorn;
