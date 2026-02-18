# Testing Lab API - Quick Reference

**Module**: `backend/testing_lab_api.py`
**Status**: Production Ready
**Created**: October 27, 2025

---

## What Is This?

The Testing Lab API enables **interactive model testing with streaming responses**. Users can test any configured LLM model (OpenRouter, OpenAI, Anthropic) with real-time cost tracking, latency monitoring, and usage analytics.

**Key Features**:
- ✅ **Streaming Responses**: Real-time SSE streaming for all providers
- ✅ **Cost Tracking**: Automatic cost calculation based on token usage
- ✅ **Access Control**: Tier-based model access (Trial → Enterprise)
- ✅ **Test Templates**: 10 pre-built prompts for different use cases
- ✅ **Test History**: Full audit trail of all tests
- ✅ **Usage Analytics**: Aggregate stats (tokens, cost, latency)

---

## Quick Start

### 1. Install

```bash
# API is already created at:
# /opt/ops-center/backend/testing_lab_api.py

# Register in server.py
vim /opt/ops-center/backend/server.py

# Add these lines:
from testing_lab_api import router as testing_lab_router
app.include_router(testing_lab_router)

# Restart backend
docker restart ops-center-direct
```

### 2. Test

```bash
# Get session token from browser cookies (unicorncommander.ai → DevTools → Application → Cookies)
export SESSION_TOKEN="your-session-token"

# Test streaming
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Say hello"}],
    "temperature": 0.7,
    "max_tokens": 50,
    "stream": true
  }'
```

---

## API Endpoints

### `POST /api/v1/llm/test`
Test model with streaming response

**Request**:
```json
{
  "model_id": "openrouter/anthropic/claude-3.5-sonnet",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": true
}
```

**Response**: SSE stream
```
data: {"content": "Hello", "tokens": 1}
data: {"done": true, "input_tokens": 5, "output_tokens": 25, "cost": 0.00015, "latency_ms": 1234}
```

---

### `GET /api/v1/llm/test/history?limit=20`
Get user's recent tests

**Response**:
```json
{
  "total": 45,
  "tests": [
    {
      "id": "uuid",
      "model_id": "openrouter/anthropic/claude-3.5-sonnet",
      "prompt": "Hello",
      "response": "Hi there!",
      "tokens_used": 30,
      "cost": 0.00015,
      "latency_ms": 1234,
      "created_at": "2025-10-27T12:00:00Z"
    }
  ]
}
```

---

### `GET /api/v1/llm/test/templates`
Get pre-built test prompts

**Response**:
```json
[
  {
    "id": "explain-quantum",
    "name": "Explain Quantum Physics",
    "prompt": "Explain quantum physics in simple terms...",
    "category": "explanation",
    "suggested_models": ["openrouter/anthropic/claude-3.5-sonnet"]
  }
]
```

**Categories**: explanation, creative, coding, analysis, reasoning, summarization, translation, mathematics, conversation

---

### `GET /api/v1/llm/test/stats`
Get user's testing statistics

**Response**:
```json
{
  "total_tests": 45,
  "total_tokens": 125000,
  "total_cost": 2.45,
  "avg_latency_ms": 1850,
  "models_tested": ["openrouter/anthropic/claude-3.5-sonnet", "openai/gpt-4o"],
  "last_test_at": "2025-10-27T12:00:00Z"
}
```

---

## Access Control

| Tier | Allowed Models | Limit |
|------|---------------|-------|
| **Trial** | OpenRouter free, local | 100/mo |
| **Starter** | OpenRouter, Groq, Together | 1,000/mo |
| **Professional** | OpenRouter, OpenAI (3.5, 4o-mini), Anthropic (Haiku) | 10,000/mo |
| **Enterprise** | All models (GPT-4, Claude 3 Opus) | Unlimited |

**Upgrade prompt** shown automatically if user tries premium model on lower tier.

---

## Frontend Integration

### React Example (Streaming)

```javascript
const testModel = async (modelId, prompt) => {
  const response = await fetch('/api/v1/llm/test', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // Send session cookie
    body: JSON.stringify({
      model_id: modelId,
      messages: [{ role: 'user', content: prompt }],
      temperature: 0.7,
      max_tokens: 1000,
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (data.content) {
          // Append content to UI
          setResponse(prev => prev + data.content);
        }

        if (data.done) {
          // Show final metrics
          setMetrics({
            tokens: data.total_tokens,
            cost: data.cost,
            latency: data.latency_ms
          });
        }
      }
    }
  }
};
```

---

## Database Schema

### Required Table

```sql
CREATE TABLE llm_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(100) NOT NULL,
    model_name VARCHAR(200),
    input_tokens INTEGER,
    output_tokens INTEGER,
    total_tokens INTEGER,
    cost DECIMAL(10, 6),
    latency_ms INTEGER,
    success BOOLEAN,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_user_date ON llm_usage_logs(user_id, created_at DESC);
CREATE INDEX idx_usage_source ON llm_usage_logs((metadata->>'source'));
```

Run this if table doesn't exist:
```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/schema.sql
```

---

## Environment Variables

Required in `.env.auth`:

```bash
# Provider API Keys (at least one required)
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Encryption (for BYOK)
ENCRYPTION_KEY=...

# Database
POSTGRES_HOST=unicorn-postgresql
POSTGRES_DB=unicorn_db
POSTGRES_USER=unicorn
POSTGRES_PASSWORD=...

# Redis (optional, for caching)
REDIS_HOST=unicorn-redis
REDIS_PORT=6379
```

---

## Testing

### Quick Test

```bash
export SESSION_TOKEN="your-token"

# Test OpenRouter
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 20,
    "stream": true
  }'

# Should see streaming chunks and final metrics
```

### Automated Tests

Run full test suite:
```bash
export SESSION_TOKEN="your-token"
bash /path/to/test_testing_lab.sh
```

---

## Documentation

- **Integration Guide**: `TESTING_LAB_INTEGRATION.md` - Complete API reference
- **Testing Guide**: `TESTING_LAB_TESTING_GUIDE.md` - 16 test scenarios + benchmarks
- **This File**: `TESTING_LAB_README.md` - Quick reference

---

## Troubleshooting

### Streaming not working
**Fix**: Add `--no-buffer` to curl, use `ReadableStream` reader in JavaScript

### "Not authenticated" error
**Fix**: Get session token from browser cookies, send in `Cookie` header

### "API key not configured" error
**Fix**: Add provider API key to `.env.auth`, restart container

### Cost showing $0.00
**Fix**: Populate `llm_models` table with pricing or use fallback estimation

---

## Next Steps

### Phase 1: Backend Complete ✅
- ✅ Streaming API for all providers
- ✅ Cost tracking and analytics
- ✅ Test history and templates
- ✅ Access control

### Phase 2: Frontend Integration
- [ ] Create React Testing Lab page
- [ ] Add to Ops-Center navigation
- [ ] Implement streaming UI
- [ ] Show real-time metrics

### Phase 3: Enhancements
- [ ] BYOK integration (user API keys)
- [ ] Model comparison (side-by-side)
- [ ] Custom templates
- [ ] Export results (CSV/JSON)

---

## Support

**Questions?**
- Read `TESTING_LAB_INTEGRATION.md` for detailed docs
- Check `TESTING_LAB_TESTING_GUIDE.md` for test scenarios
- Review main Ops-Center docs: `/services/ops-center/CLAUDE.md`

**Found a bug?**
- Check logs: `docker logs ops-center-direct --tail 100`
- Verify DB schema: `docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_usage_logs"`
- Test with curl first before blaming frontend

---

**Status**: Production Ready - Backend Complete
**Next**: Frontend integration in Testing Lab tab
