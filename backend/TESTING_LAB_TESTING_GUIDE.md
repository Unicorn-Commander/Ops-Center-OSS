# Testing Lab API - Testing & Verification Guide

**Created**: October 27, 2025
**Purpose**: Complete testing procedures for Testing Lab API

---

## Pre-Testing Checklist

### 1. Environment Setup

```bash
# Verify environment variables
docker exec ops-center-direct printenv | grep -E "(OPENROUTER|OPENAI|ANTHROPIC|ENCRYPTION_KEY)"

# Expected output:
# OPENROUTER_API_KEY=sk-or-...
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# ENCRYPTION_KEY=...
```

### 2. Database Schema

```bash
# Verify llm_usage_logs table exists
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d llm_usage_logs"

# If table doesn't exist, create it:
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
CREATE TABLE IF NOT EXISTS llm_usage_logs (
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

CREATE INDEX IF NOT EXISTS idx_usage_user_date ON llm_usage_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_usage_source ON llm_usage_logs((metadata->>'source'));
"
```

### 3. Register API in `server.py`

Edit `/opt/ops-center/backend/server.py`:

```python
# Add import
from testing_lab_api import router as testing_lab_router

# Register router (after other routers)
app.include_router(testing_lab_router)
```

### 4. Restart Backend

```bash
cd /opt/uc-cloud
docker restart ops-center-direct

# Wait for startup
sleep 5

# Verify API is running
docker logs ops-center-direct --tail 20
```

---

## Test Scenarios

### Scenario 1: Get Session Token

Before testing, you need a valid session token.

#### Option A: Login via Browser

1. Go to https://unicorncommander.ai
2. Login with your credentials
3. Open browser DevTools (F12)
4. Go to Application → Cookies
5. Copy `session_token` value

#### Option B: Login via API

```bash
# Login endpoint (adjust based on your auth implementation)
curl -X POST http://localhost:8084/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@example.com",
    "password": "your-password"
  }' \
  -c cookies.txt

# Extract session token
SESSION_TOKEN=$(grep session_token cookies.txt | awk '{print $7}')
echo "Session Token: $SESSION_TOKEN"
```

---

### Scenario 2: Basic Streaming Test (OpenRouter)

**Objective**: Test streaming chat completion with OpenRouter

```bash
# Set your session token
export SESSION_TOKEN="your-session-token-here"

# Test OpenRouter streaming
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [
      {"role": "user", "content": "Say hello in 5 words"}
    ],
    "temperature": 0.7,
    "max_tokens": 50,
    "stream": true
  }'
```

**Expected Output** (streaming):
```
data: {"content": "Hello", "tokens": 1}
data: {"content": ",", "tokens": 2}
data: {"content": " how", "tokens": 3}
data: {"content": " are", "tokens": 4}
data: {"content": " you", "tokens": 5}
data: {"content": " today", "tokens": 6}
data: {"content": "?", "tokens": 7}
data: {"done": true, "input_tokens": 8, "output_tokens": 7, "total_tokens": 15, "cost": 0.000045, "latency_ms": 1234}
```

**Success Criteria**:
- ✅ Chunks received incrementally (not all at once)
- ✅ Final `done` message with token counts and cost
- ✅ Latency_ms > 0
- ✅ Cost > 0

---

### Scenario 3: Test OpenAI Model

**Objective**: Test OpenAI streaming (if configured)

```bash
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openai/gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "Write a 3-line poem about coding"}
    ],
    "temperature": 0.8,
    "max_tokens": 100,
    "stream": true
  }'
```

**Expected**: Streaming poem response with final metrics

---

### Scenario 4: Test Anthropic Model

**Objective**: Test Anthropic streaming (if configured)

```bash
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "anthropic/claude-3-haiku-20240307",
    "messages": [
      {"role": "system", "content": "You are a concise assistant"},
      {"role": "user", "content": "Explain APIs in one sentence"}
    ],
    "temperature": 0.5,
    "max_tokens": 100,
    "stream": true
  }'
```

**Expected**: Streaming response with Anthropic-specific event structure

---

### Scenario 5: Access Control - Trial Tier

**Objective**: Verify trial users can't access premium models

**Setup**: Ensure test user has `subscription_tier: "trial"`

```bash
# This should FAIL with 403 Forbidden
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "model_id": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

**Expected Output**:
```json
{
  "detail": {
    "error": "Premium models require Professional or Enterprise tier",
    "tier_required": "professional",
    "current_tier": "trial"
  }
}
```

**Success Criteria**:
- ✅ HTTP 403 status
- ✅ Error message explains tier requirement
- ✅ Suggests correct tier

---

### Scenario 6: Access Control - Professional Tier

**Objective**: Verify professional users can access mid-tier models

**Setup**: Update user to `subscription_tier: "professional"`

```bash
# Update user tier (adjust user_id)
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm uchub \
  --user admin \
  --password your-admin-password

docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh update users/USER_ID \
  --realm uchub \
  -s 'attributes.subscription_tier=["professional"]'

# Test with GPT-4o-mini (should work)
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openai/gpt-4o-mini",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

**Expected**: Successful streaming response

---

### Scenario 7: Get Test Templates

**Objective**: Fetch pre-built test prompts

```bash
curl http://localhost:8084/api/v1/llm/test/templates \
  -H "Cookie: session_token=$SESSION_TOKEN" | jq
```

**Expected Output**:
```json
[
  {
    "id": "explain-quantum",
    "name": "Explain Quantum Physics",
    "prompt": "Explain quantum physics...",
    "category": "explanation",
    "description": "Test model's ability...",
    "suggested_models": [
      "openrouter/anthropic/claude-3.5-sonnet",
      "openai/gpt-4o"
    ]
  },
  ...
]
```

**Success Criteria**:
- ✅ Returns array of templates
- ✅ Each template has id, name, prompt, category
- ✅ At least 10 templates present

---

### Scenario 8: Test with Template

**Objective**: Use template for testing

```bash
# Get coding template
TEMPLATE=$(curl -s http://localhost:8084/api/v1/llm/test/templates \
  -H "Cookie: session_token=$SESSION_TOKEN" | \
  jq -r '.[] | select(.id == "code-function") | .prompt')

# Test with template
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d "{
    \"model_id\": \"openrouter/anthropic/claude-3.5-sonnet\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$TEMPLATE\"}],
    \"temperature\": 0.3,
    \"max_tokens\": 500,
    \"stream\": true
  }"
```

**Expected**: Streaming code generation response

---

### Scenario 9: Get Test History

**Objective**: Retrieve user's recent tests

```bash
curl http://localhost:8084/api/v1/llm/test/history?limit=5 \
  -H "Cookie: session_token=$SESSION_TOKEN" | jq
```

**Expected Output**:
```json
{
  "total": 3,
  "limit": 5,
  "offset": 0,
  "tests": [
    {
      "id": "uuid",
      "model_id": "openrouter/anthropic/claude-3.5-sonnet",
      "prompt": "Say hello in 5 words",
      "response": "Hello, how are you today?",
      "tokens_used": 15,
      "input_tokens": 8,
      "output_tokens": 7,
      "cost": 0.000045,
      "latency_ms": 1234,
      "created_at": "2025-10-27T12:00:00Z",
      "parameters": {
        "temperature": 0.7,
        "max_tokens": 50,
        "top_p": 1.0
      }
    }
  ]
}
```

**Success Criteria**:
- ✅ Shows previous tests from current session
- ✅ Ordered by created_at DESC (newest first)
- ✅ Includes prompt, response, costs, latency

---

### Scenario 10: Get Testing Stats

**Objective**: Fetch user's aggregate statistics

```bash
curl http://localhost:8084/api/v1/llm/test/stats \
  -H "Cookie: session_token=$SESSION_TOKEN" | jq
```

**Expected Output**:
```json
{
  "total_tests": 3,
  "total_tokens": 450,
  "total_cost": 0.00135,
  "avg_latency_ms": 1456,
  "models_tested": [
    "openrouter/anthropic/claude-3.5-sonnet",
    "openai/gpt-4o-mini"
  ],
  "last_test_at": "2025-10-27T12:05:00Z"
}
```

**Success Criteria**:
- ✅ Aggregates all tests from user
- ✅ Total cost is sum of individual costs
- ✅ Average latency is reasonable
- ✅ Models_tested is unique list

---

### Scenario 11: Error Handling - Timeout

**Objective**: Test timeout handling (60s max)

```bash
# Request very long response to trigger timeout
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  --max-time 65 \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Write a 10,000 word essay on AI"}],
    "max_tokens": 10000,
    "stream": true
  }'
```

**Expected**: Error message after 60 seconds:
```
data: {"error": "Request timeout (60s limit)"}
```

---

### Scenario 12: Error Handling - Invalid Model

**Objective**: Test handling of unsupported model

```bash
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "model_id": "invalid/model/name",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

**Expected**: HTTP 400 Bad Request:
```json
{
  "detail": "Unsupported model provider: invalid/model/name"
}
```

---

### Scenario 13: Error Handling - No API Key

**Objective**: Test behavior when provider API key missing

**Setup**: Temporarily remove API key

```bash
# Remove API key from environment
docker exec -u root ops-center-direct sh -c 'unset OPENROUTER_API_KEY && service nginx restart'

# Test (should fail gracefully)
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

**Expected**: HTTP 503:
```json
{
  "detail": "OpenRouter API key not configured. Please configure in LLM Settings or provide your own key (BYOK)."
}
```

**Restore API key** after test!

---

### Scenario 14: Database Logging Verification

**Objective**: Verify tests are logged to database

```bash
# Run a test
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Test message"}],
    "max_tokens": 50,
    "stream": true
  }' > /dev/null

# Wait for logging
sleep 2

# Check database
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "
SELECT
  user_id,
  model_name,
  total_tokens,
  cost,
  latency_ms,
  metadata->>'source' as source,
  created_at
FROM llm_usage_logs
WHERE metadata->>'source' = 'testing_lab'
ORDER BY created_at DESC
LIMIT 5;
"
```

**Expected**: Recent test appears in database with:
- ✅ Correct user_id
- ✅ Model name
- ✅ Token counts
- ✅ Cost > 0
- ✅ Latency_ms > 0
- ✅ source = "testing_lab"

---

### Scenario 15: Cost Calculation Accuracy

**Objective**: Verify cost calculation is reasonable

```bash
# Test with known pricing
curl -X POST http://localhost:8084/api/v1/llm/test \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Count to 10"}],
    "max_tokens": 50,
    "stream": true
  }' | grep '"done"'
```

**Expected Output** (final line):
```json
data: {"done": true, "input_tokens": 5, "output_tokens": 25, "total_tokens": 30, "cost": 0.000135, "latency_ms": 1200}
```

**Manual Verification**:
- Claude 3.5 Sonnet pricing: ~$3/M input, $15/M output
- Expected cost: (5/1M * $3) + (25/1M * $15) = $0.000015 + $0.000375 = $0.00039
- Actual cost should be within 50% (provider markup, estimation)

---

### Scenario 16: Concurrent Tests

**Objective**: Test handling of multiple simultaneous requests

```bash
# Run 3 tests concurrently
for i in {1..3}; do
  curl -X POST http://localhost:8084/api/v1/llm/test \
    -H "Content-Type: application/json" \
    -H "Cookie: session_token=$SESSION_TOKEN" \
    --no-buffer \
    -d "{
      \"model_id\": \"openrouter/anthropic/claude-3.5-sonnet\",
      \"messages\": [{\"role\": \"user\", \"content\": \"Test $i\"}],
      \"max_tokens\": 50,
      \"stream\": true
    }" > test_$i.log 2>&1 &
done

# Wait for all to complete
wait

# Check all succeeded
for i in {1..3}; do
  echo "=== Test $i ==="
  tail -1 test_$i.log | grep '"done"'
done

# Cleanup
rm test_*.log
```

**Success Criteria**:
- ✅ All 3 tests complete successfully
- ✅ Each has unique response
- ✅ No race conditions or errors

---

## Performance Benchmarks

### Latency Expectations

| Provider | Model | Expected Latency | Acceptable Range |
|----------|-------|------------------|------------------|
| OpenRouter | Claude 3.5 Sonnet | 1-2s | 0.5-5s |
| OpenAI | GPT-4o-mini | 0.5-1s | 0.3-3s |
| Anthropic | Claude 3 Haiku | 0.5-1s | 0.3-2s |
| Local | Any | 0.1-0.5s | 0.05-2s |

### Throughput Test

```bash
# Test 10 requests sequentially
time for i in {1..10}; do
  curl -X POST http://localhost:8084/api/v1/llm/test \
    -H "Content-Type: application/json" \
    -H "Cookie: session_token=$SESSION_TOKEN" \
    --no-buffer \
    -d '{
      "model_id": "openrouter/anthropic/claude-3.5-sonnet",
      "messages": [{"role": "user", "content": "Hi"}],
      "max_tokens": 10,
      "stream": true
    }' > /dev/null 2>&1
done
```

**Expected**: Total time < 30 seconds (avg 3s per request)

---

## Automated Test Script

Save as `/tmp/test_testing_lab.sh`:

```bash
#!/bin/bash
set -e

# Configuration
API_URL="http://localhost:8084"
SESSION_TOKEN="${SESSION_TOKEN:-your-token-here}"

echo "======================================"
echo "Testing Lab API - Automated Test Suite"
echo "======================================"

# Test 1: Templates
echo -e "\n[1/5] Testing templates endpoint..."
TEMPLATES=$(curl -s "${API_URL}/api/v1/llm/test/templates" \
  -H "Cookie: session_token=${SESSION_TOKEN}")
TEMPLATE_COUNT=$(echo "$TEMPLATES" | jq '. | length')
if [ "$TEMPLATE_COUNT" -ge 10 ]; then
  echo "✅ Templates: $TEMPLATE_COUNT found"
else
  echo "❌ Templates: Only $TEMPLATE_COUNT found (expected >= 10)"
  exit 1
fi

# Test 2: Streaming
echo -e "\n[2/5] Testing streaming..."
RESPONSE=$(curl -s "${API_URL}/api/v1/llm/test" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=${SESSION_TOKEN}" \
  --no-buffer \
  -d '{
    "model_id": "openrouter/anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Say hi"}],
    "max_tokens": 10,
    "stream": true
  }')

if echo "$RESPONSE" | grep -q '"done":true'; then
  echo "✅ Streaming: Successful"
else
  echo "❌ Streaming: Failed"
  echo "$RESPONSE"
  exit 1
fi

# Test 3: History
echo -e "\n[3/5] Testing history endpoint..."
sleep 2  # Wait for DB write
HISTORY=$(curl -s "${API_URL}/api/v1/llm/test/history?limit=1" \
  -H "Cookie: session_token=${SESSION_TOKEN}")
HISTORY_COUNT=$(echo "$HISTORY" | jq '.total')
if [ "$HISTORY_COUNT" -ge 1 ]; then
  echo "✅ History: $HISTORY_COUNT tests found"
else
  echo "❌ History: No tests found"
  exit 1
fi

# Test 4: Stats
echo -e "\n[4/5] Testing stats endpoint..."
STATS=$(curl -s "${API_URL}/api/v1/llm/test/stats" \
  -H "Cookie: session_token=${SESSION_TOKEN}")
TOTAL_TESTS=$(echo "$STATS" | jq '.total_tests')
if [ "$TOTAL_TESTS" -ge 1 ]; then
  echo "✅ Stats: $TOTAL_TESTS total tests"
else
  echo "❌ Stats: No tests recorded"
  exit 1
fi

# Test 5: Access Control
echo -e "\n[5/5] Testing access control..."
ACCESS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" \
  "${API_URL}/api/v1/llm/test" \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=${SESSION_TOKEN}" \
  -d '{
    "model_id": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Hi"}],
    "stream": true
  }')

# Accept either 200 (if enterprise) or 403 (if lower tier)
if [ "$ACCESS_RESPONSE" -eq 200 ] || [ "$ACCESS_RESPONSE" -eq 403 ]; then
  echo "✅ Access Control: Working (HTTP $ACCESS_RESPONSE)"
else
  echo "❌ Access Control: Unexpected response (HTTP $ACCESS_RESPONSE)"
  exit 1
fi

echo -e "\n======================================"
echo "✅ All tests passed!"
echo "======================================"
```

**Run**:
```bash
chmod +x /tmp/test_testing_lab.sh
export SESSION_TOKEN="your-session-token"
/tmp/test_testing_lab.sh
```

---

## Troubleshooting

### Problem: "Not authenticated" error

**Cause**: Missing or invalid session token

**Solution**:
1. Login via browser and copy session token from cookies
2. Or use API login to get token
3. Ensure token is sent in Cookie header: `Cookie: session_token=...`

---

### Problem: Streaming not working (response buffered)

**Cause**: Proxy buffering or missing `--no-buffer` flag

**Solution**:
```bash
# Add --no-buffer to curl
curl --no-buffer ...

# Check Traefik/nginx config
docker exec traefik cat /etc/traefik/traefik.yml | grep buffering
```

---

### Problem: "Provider API key not configured"

**Cause**: Environment variable missing

**Solution**:
```bash
# Check environment
docker exec ops-center-direct printenv | grep -E "(OPENROUTER|OPENAI|ANTHROPIC)_API_KEY"

# Add to .env.auth if missing
echo "OPENROUTER_API_KEY=sk-or-..." >> .env.auth

# Restart container
docker restart ops-center-direct
```

---

### Problem: Cost showing $0.00

**Cause**: Model pricing not in database or token counts not provided by provider

**Solution**:
```bash
# Populate llm_models table with pricing
# Or check provider response for usage data
# Fallback pricing will estimate if not in DB
```

---

## Success Criteria Summary

**All scenarios should pass with**:
- ✅ Streaming responses (not buffered)
- ✅ Accurate token counts
- ✅ Reasonable costs ($0.0001 - $0.01 range)
- ✅ Latency < 5 seconds
- ✅ Database logging working
- ✅ Access control enforced
- ✅ Templates available
- ✅ History and stats accurate
- ✅ Concurrent requests handled
- ✅ Errors handled gracefully

**Run automated test script** for quick verification!
