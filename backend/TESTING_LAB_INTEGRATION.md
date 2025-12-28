# Testing Lab API - Integration Guide

**Created**: October 27, 2025
**Module**: `backend/testing_lab_api.py`
**Status**: Production Ready

---

## Overview

The Testing Lab API provides interactive model testing with real-time streaming responses, cost tracking, and usage analytics. It supports all major LLM providers (OpenRouter, OpenAI, Anthropic) with built-in access control based on subscription tiers.

---

## Quick Start

### 1. Register the API in `server.py`

Add to your main FastAPI app:

```python
from testing_lab_api import router as testing_lab_router

# Register router
app.include_router(testing_lab_router)
```

### 2. Test the API

```bash
# Test with curl (streaming)
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Hello! How are you?"}],
    "temperature": 0.7,
    "max_tokens": 100,
    "stream": true
  }'
```

Expected output (SSE stream):
```
data: {"content": "Hello", "tokens": 1}
data: {"content": "!", "tokens": 2}
data: {"content": " I'm", "tokens": 3}
...
data: {"done": true, "input_tokens": 10, "output_tokens": 25, "total_tokens": 35, "cost": 0.000175, "latency_ms": 1250}
```

---

## API Endpoints

### POST `/api/v1/llm/test`

**Test any configured model with streaming response**

**Authentication**: Session cookie required

**Request Body**:
```json
{
  "model_id": "openrouter/anthropic/claude-3.5-sonnet",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "Explain quantum physics"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1.0,
  "stream": true
}
```

**Response**: Server-Sent Events (SSE) stream
```
data: {"content": "Quantum", "tokens": 1}
data: {"content": " physics", "tokens": 2}
...
data: {"done": true, "input_tokens": 10, "output_tokens": 150, "total_tokens": 160, "cost": 0.0045, "latency_ms": 2340}
```

**Access Control**:
- **Trial**: OpenRouter free models, local models only
- **Starter**: OpenRouter, Groq, Together models
- **Professional**: OpenRouter, OpenAI (GPT-3.5, GPT-4o-mini), Anthropic (Claude 3 Haiku)
- **Enterprise**: All models (including GPT-4, Claude 3 Opus)

**Error Responses**:
```json
// 401 Unauthorized
{"detail": "Not authenticated - no session token"}

// 403 Forbidden (tier upgrade required)
{
  "detail": {
    "error": "Premium models require Professional or Enterprise tier",
    "tier_required": "professional",
    "current_tier": "trial"
  }
}

// 503 Service Unavailable (API key not configured)
{"detail": "OpenRouter API key not configured. Please configure in LLM Settings or provide your own key (BYOK)."}

// Streaming errors (sent as SSE)
data: {"error": "Request timeout (60s limit)"}
data: {"error": "OpenRouter error: 429 - Rate limit exceeded"}
```

---

### GET `/api/v1/llm/test/history`

**Get user's recent test runs**

**Query Parameters**:
- `limit` (int, default 20, max 100): Number of records
- `offset` (int, default 0): Pagination offset

**Response**:
```json
{
  "total": 45,
  "limit": 20,
  "offset": 0,
  "tests": [
    {
      "id": "uuid",
      "model_id": "openrouter/anthropic/claude-3.5-sonnet",
      "prompt": "Explain quantum physics",
      "response": "Quantum physics is the branch of...",
      "tokens_used": 250,
      "input_tokens": 10,
      "output_tokens": 240,
      "cost": 0.0045,
      "latency_ms": 2340,
      "created_at": "2025-10-27T12:00:00Z",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 1000,
        "top_p": 1.0
      }
    }
  ]
}
```

---

### GET `/api/v1/llm/test/templates`

**Get pre-built test prompts**

**Response**:
```json
[
  {
    "id": "explain-quantum",
    "name": "Explain Quantum Physics",
    "prompt": "Explain quantum physics in simple terms that a high school student could understand.",
    "category": "explanation",
    "description": "Test model's ability to explain complex scientific concepts",
    "suggested_models": [
      "openrouter/anthropic/claude-3.5-sonnet",
      "openai/gpt-4o",
      "openrouter/google/gemini-pro"
    ]
  },
  {
    "id": "write-poem",
    "name": "Write a Poem",
    "prompt": "Write a haiku about artificial intelligence...",
    "category": "creative",
    "description": "Test creative writing and poetry generation",
    "suggested_models": ["openrouter/anthropic/claude-3-opus"]
  }
]
```

**Categories**:
- `explanation` - Explaining complex concepts
- `creative` - Creative writing (poems, stories)
- `coding` - Code generation and best practices
- `analysis` - Analytical reasoning (sentiment, etc.)
- `reasoning` - Logic puzzles and problem-solving
- `summarization` - Text summarization
- `translation` - Multilingual translation
- `mathematics` - Math problem-solving
- `conversation` - Role-playing and dialogue
- `creative` - Brainstorming and ideation

---

### GET `/api/v1/llm/test/stats`

**Get user's testing statistics**

**Response**:
```json
{
  "total_tests": 45,
  "total_tokens": 125000,
  "total_cost": 2.45,
  "avg_latency_ms": 1850,
  "models_tested": [
    "openrouter/anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "openrouter/meta-llama/llama-3.1-70b"
  ],
  "last_test_at": "2025-10-27T12:00:00Z"
}
```

---

## Frontend Integration

### React/JavaScript Example (EventSource)

```javascript
// Testing Lab Component
import React, { useState } from 'react';

function TestingLab() {
  const [response, setResponse] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  const testModel = async (modelId, prompt) => {
    setLoading(true);
    setResponse('');
    setMetrics(null);

    try {
      const res = await fetch('/api/v1/llm/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include', // Include session cookie
        body: JSON.stringify({
          model_id: modelId,
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.7,
          max_tokens: 1000,
          stream: true
        })
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail?.error || error.detail || 'Test failed');
      }

      // Use EventSource for streaming
      const reader = res.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              console.error('Streaming error:', data.error);
              setLoading(false);
              return;
            }

            if (data.content) {
              setResponse(prev => prev + data.content);
            }

            if (data.done) {
              setMetrics({
                inputTokens: data.input_tokens,
                outputTokens: data.output_tokens,
                totalTokens: data.total_tokens,
                cost: data.cost,
                latencyMs: data.latency_ms
              });
              setLoading(false);
            }
          }
        }
      }
    } catch (error) {
      console.error('Test error:', error);
      alert(error.message);
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Testing Lab</h2>

      <button onClick={() => testModel('openrouter/anthropic/claude-3.5-sonnet', 'Hello!')}>
        Test Claude 3.5 Sonnet
      </button>

      {loading && <p>Generating...</p>}

      <div className="response">
        <h3>Response:</h3>
        <pre>{response}</pre>
      </div>

      {metrics && (
        <div className="metrics">
          <h3>Metrics:</h3>
          <p>Input Tokens: {metrics.inputTokens}</p>
          <p>Output Tokens: {metrics.outputTokens}</p>
          <p>Total Tokens: {metrics.totalTokens}</p>
          <p>Cost: ${metrics.cost.toFixed(6)}</p>
          <p>Latency: {metrics.latencyMs}ms</p>
        </div>
      )}
    </div>
  );
}

export default TestingLab;
```

### Using Test Templates

```javascript
// Fetch templates
const templates = await fetch('/api/v1/llm/test/templates').then(r => r.json());

// Use template
const template = templates.find(t => t.id === 'explain-quantum');
await testModel(template.suggested_models[0], template.prompt);
```

### Fetching Test History

```javascript
// Get recent tests
const history = await fetch('/api/v1/llm/test/history?limit=10')
  .then(r => r.json());

console.log(history.tests);
```

### Fetching Stats

```javascript
// Get user's testing stats
const stats = await fetch('/api/v1/llm/test/stats')
  .then(r => r.json());

console.log(`Total tests: ${stats.total_tests}`);
console.log(`Total cost: $${stats.total_cost}`);
```

---

## Testing with curl

### Basic Test (Streaming)

```bash
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Write a haiku about AI"}],
    "temperature": 0.8,
    "max_tokens": 100
  }'
```

**Note**: `--no-buffer` is required to see streaming output in real-time.

### Test with Template

```bash
# Get templates
TEMPLATES=$(curl -s http://localhost:8084/api/v1/llm/test/templates)

# Extract a prompt
PROMPT=$(echo $TEMPLATES | jq -r '.[0].prompt')

# Test with template
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=YOUR_TOKEN" \
  --no-buffer \
  -d "{
    \"model_id\": \"openrouter/anthropic/claude-3.5-sonnet\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}],
    \"temperature\": 0.7,
    \"max_tokens\": 500
  }"
```

### Get Test History

```bash
curl http://localhost:8084/api/v1/llm/test/history?limit=5 \
  -H "Cookie: session_token=YOUR_TOKEN" | jq
```

### Get Stats

```bash
curl http://localhost:8084/api/v1/llm/test/stats \
  -H "Cookie: session_token=YOUR_TOKEN" | jq
```

---

## Access Control

### Tier-Based Model Access

| Tier | Allowed Models | Monthly Limit |
|------|---------------|---------------|
| **Trial** | OpenRouter free models, local models | 100 tests |
| **Starter** | OpenRouter, Groq, Together | 1,000 tests |
| **Professional** | OpenRouter, OpenAI (3.5, 4o-mini), Anthropic (Haiku) | 10,000 tests |
| **Enterprise** | All models (GPT-4, Claude 3 Opus, etc.) | Unlimited |

### Checking Access

The API automatically checks access based on:
1. User's `subscription_tier` attribute in session
2. Model prefix (`openrouter/`, `openai/`, `anthropic/`)
3. Specific model names (e.g., `gpt-4`, `claude-3-opus`)

If access is denied, response includes:
```json
{
  "detail": {
    "error": "Premium models require Professional or Enterprise tier",
    "tier_required": "professional",
    "current_tier": "trial"
  }
}
```

---

## Cost Tracking

### How Costs Are Calculated

1. **Token Counting**: Tokens are counted from provider response (when available)
2. **Pricing Lookup**: Costs fetched from `llm_models` table
3. **Fallback Pricing**: If not in DB, estimated at $0.50/1M input, $1.50/1M output
4. **Usage Logging**: All tests logged to `llm_usage_logs` table

### Cost Formula

```
input_cost = (input_tokens / 1,000,000) * cost_per_1m_input
output_cost = (output_tokens / 1,000,000) * cost_per_1m_output
total_cost = input_cost + output_cost
```

### Viewing Costs

```bash
# Get user's total testing cost
curl http://localhost:8084/api/v1/llm/test/stats \
  -H "Cookie: session_token=YOUR_TOKEN" | jq '.total_cost'
```

---

## Error Handling

### Common Errors

#### 401 Unauthorized
**Cause**: No session cookie or invalid session
**Solution**: Ensure user is logged in and session cookie is sent

#### 403 Forbidden
**Cause**: User's subscription tier doesn't allow this model
**Solution**: Display upgrade prompt or suggest alternative models

#### 503 Service Unavailable
**Cause**: Provider API key not configured
**Solution**: Admin must configure API key in LLM Settings, or user provides BYOK

#### Timeout (60s)
**Cause**: Provider taking too long to respond
**Solution**: Retry with shorter `max_tokens` or different model

#### Rate Limit (429)
**Cause**: Provider rate limit exceeded
**Solution**: Wait and retry, or use different provider

---

## Database Schema

### Required Tables

#### `llm_usage_logs`
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

CREATE INDEX idx_usage_user_source ON llm_usage_logs(user_id, (metadata->>'source'));
```

#### `llm_models` (optional, for pricing)
```sql
CREATE TABLE llm_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(200),
    cost_per_1m_input_tokens DECIMAL(10, 4),
    cost_per_1m_output_tokens DECIMAL(10, 4),
    context_length INTEGER,
    enabled BOOLEAN DEFAULT true,
    metadata JSONB
);
```

---

## Performance Considerations

### Streaming Optimization

- **Buffering**: No buffering - chunks sent immediately
- **Timeout**: 60-second timeout per request
- **Concurrency**: Multiple tests can run in parallel (per user)
- **Memory**: Minimal - streaming doesn't accumulate full response in memory

### Caching

- **Templates**: Cached in Redis for 5 minutes (if Redis available)
- **Stats**: Cached in Redis for 60 seconds per user
- **History**: No caching (always fresh from DB)

### Database Optimization

```sql
-- Recommended indexes
CREATE INDEX idx_usage_user_date ON llm_usage_logs(user_id, created_at DESC);
CREATE INDEX idx_usage_source ON llm_usage_logs((metadata->>'source'));
```

---

## Security

### API Key Encryption

All provider API keys (system and BYOK) are encrypted using Fernet (symmetric encryption):

```python
from cryptography.fernet import Fernet

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# Encrypt
encrypted = cipher_suite.encrypt(api_key.encode()).decode()

# Decrypt
api_key = cipher_suite.decrypt(encrypted.encode()).decode()
```

### Session Security

- Session tokens stored in HTTP-only cookies
- Sessions validated on every request
- No API keys exposed in responses or logs

### Access Control

- Tier-based model access enforced server-side
- No client-side bypass possible
- All requests audited in `llm_usage_logs`

---

## Troubleshooting

### Streaming Not Working

**Symptom**: Response received all at once instead of streaming

**Causes**:
1. Missing `--no-buffer` flag in curl
2. Frontend not using `ReadableStream` reader
3. Proxy buffering responses (nginx, Traefik)

**Solutions**:
```bash
# curl: Add --no-buffer
curl --no-buffer ...

# nginx: Disable buffering
proxy_buffering off;

# JavaScript: Use reader.read() loop
const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  // Process chunk
}
```

### Cost Calculation Incorrect

**Symptom**: Cost showing $0.00 or incorrect amount

**Causes**:
1. Model not in `llm_models` table
2. Pricing data outdated
3. Token counts not provided by provider

**Solutions**:
1. Populate `llm_models` table with pricing data
2. Update pricing: `UPDATE llm_models SET cost_per_1m_input_tokens = 3.0 WHERE name = 'gpt-4'`
3. Check provider response for usage data

### High Latency

**Symptom**: Tests taking >10 seconds

**Causes**:
1. Provider API slow
2. Large `max_tokens` setting
3. Complex prompts

**Solutions**:
1. Try different provider
2. Reduce `max_tokens` to 500-1000
3. Simplify prompt or use streaming UI feedback

---

## Future Enhancements

### Planned Features (Phase 2)

- [ ] **BYOK Integration**: Allow users to test with their own API keys
- [ ] **Model Comparison**: Side-by-side comparison of multiple models
- [ ] **Custom Templates**: Users can save their own test templates
- [ ] **A/B Testing**: Compare responses from different models
- [ ] **Quality Scoring**: Automatic evaluation of response quality
- [ ] **Export Results**: Export test history as CSV/JSON
- [ ] **Scheduled Tests**: Automated testing on schedule
- [ ] **Webhooks**: Notify external services of test results

---

## Support

**Questions?** Check:
- Main Ops-Center docs: `/services/ops-center/CLAUDE.md`
- API reference: `/services/ops-center/backend/api_docs.py`
- UC-Cloud docs: `/CLAUDE.md`

**Issues?** Create ticket in project management system with:
- Test request JSON
- Expected vs actual behavior
- Error messages
- User's subscription tier
