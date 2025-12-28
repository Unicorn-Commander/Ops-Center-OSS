# Provider Keys API - Integration Guide

**Created**: October 27, 2025
**Author**: Backend Developer #2
**Purpose**: System-level provider key management for LLM Hub

---

## Overview

The Provider Keys API provides admin-only endpoints for managing system-level API keys for LLM providers (OpenRouter, OpenAI, Anthropic, Google, etc.). This powers the "Provider Keys" tab in the LLM Hub frontend.

**Key Features**:
- ✅ List all provider keys with masked values
- ✅ Add/update provider keys with Fernet encryption
- ✅ Test provider keys against their APIs
- ✅ Delete provider keys (falls back to environment)
- ✅ Rate limiting (10 tests/minute)
- ✅ Session-based admin authentication
- ✅ Comprehensive error handling

---

## Integration with server.py

### Step 1: Import the router

Add to the imports section of `backend/server.py`:

```python
# Add this line after other API router imports (around line 121)
from provider_keys_api import router as provider_keys_router
```

### Step 2: Register the router

Add to the router registration section of `backend/server.py`:

```python
# Add this line after other router registrations (around line 700+)
app.include_router(provider_keys_router)
logger.info("Provider Keys API endpoints registered at /api/v1/llm/providers")
```

### Step 3: Verify app.state dependencies

The API uses these from `app.state` (already initialized in `server.py`):
- ✅ `app.state.db_pool` - PostgreSQL connection pool (lines 374-382)
- ✅ `app.state.sessions` - Redis session manager (line 181)
- ✅ `BYOK_ENCRYPTION_KEY` - Environment variable (line 44 in litellm_api.py)

**No additional initialization required!**

---

## API Endpoints

### Base Path
```
/api/v1/llm/providers
```

### Endpoints

#### 1. List Provider Keys
```http
GET /api/v1/llm/providers/keys
```

**Authentication**: Session cookie (admin required)

**Response**:
```json
{
  "success": true,
  "providers": [
    {
      "id": "uuid",
      "name": "OpenRouter",
      "provider_type": "openrouter",
      "has_key": true,
      "key_source": "database",
      "enabled": true,
      "health_status": "healthy",
      "last_tested": "2025-10-27T12:00:00",
      "test_status": "success",
      "key_preview": "sk-or-v...1234",
      "config": {}
    }
  ],
  "total": 9
}
```

---

#### 2. Save Provider Key
```http
POST /api/v1/llm/providers/keys
```

**Authentication**: Session cookie (admin required)

**Request Body**:
```json
{
  "provider_type": "openrouter",
  "api_key": "sk-or-v1-abc123...",
  "name": "OpenRouter",
  "config": {
    "base_url": "https://openrouter.ai/api/v1"
  }
}
```

**Response**:
```json
{
  "success": true,
  "provider_id": "uuid",
  "name": "OpenRouter",
  "provider_type": "openrouter",
  "has_key": true,
  "enabled": true,
  "test_result": {
    "success": true,
    "latency_ms": 234,
    "models_found": 346,
    "error": null
  },
  "message": "API key saved successfully"
}
```

---

#### 3. Test Provider Key
```http
POST /api/v1/llm/providers/keys/test
```

**Authentication**: Session cookie (admin required)
**Rate Limit**: 10 tests per minute per user

**Request Body (Option 1 - Test stored key)**:
```json
{
  "provider_type": "openrouter",
  "api_key": null
}
```

**Request Body (Option 2 - Test new key)**:
```json
{
  "provider_type": "openai",
  "api_key": "sk-proj-new-key-to-test"
}
```

**Response**:
```json
{
  "success": true,
  "latency_ms": 234,
  "models_found": 346,
  "error": null
}
```

**Error Response**:
```json
{
  "success": false,
  "latency_ms": 0,
  "models_found": null,
  "error": "Invalid API key - authentication failed"
}
```

---

#### 4. Delete Provider Key
```http
DELETE /api/v1/llm/providers/keys/{provider_id}
```

**Authentication**: Session cookie (admin required)

**Response**:
```json
{
  "success": true,
  "provider_id": "uuid",
  "message": "API key deleted successfully (will fall back to environment variable if configured)"
}
```

---

#### 5. Get Provider Info
```http
GET /api/v1/llm/providers/info
```

**Authentication**: Session cookie (admin required)

**Response**:
```json
{
  "success": true,
  "providers": [
    {
      "provider_type": "openrouter",
      "display_name": "OpenRouter",
      "description": "Universal LLM proxy - 200+ models",
      "key_format": "sk-or-v1-...",
      "supports_test": true,
      "auth_type": "bearer"
    }
  ],
  "total": 9
}
```

---

## Supported Providers

| Provider | Type | Key Format | Test Support |
|----------|------|------------|--------------|
| OpenRouter | openrouter | sk-or-v1-... | ✅ GET /v1/models |
| OpenAI | openai | sk-proj-... | ✅ GET /v1/models |
| Anthropic | anthropic | sk-ant-... | ✅ POST /v1/messages |
| Google AI | google | AIza... | ✅ GET /v1beta/models |
| Cohere | cohere | Bearer ... | ✅ GET /v1/models |
| Groq | groq | gsk_... | ✅ GET /openai/v1/models |
| Together AI | together | Bearer ... | ✅ GET /models |
| Mistral AI | mistral | Bearer ... | ✅ GET /v1/models |
| Custom | custom | Any | ✅ GET {base_url}/v1/models |

---

## Security Features

### 1. Authentication
- **Session-based**: Uses same pattern as `litellm_api.py`
- **Admin-only**: All endpoints require `role: admin`
- **Auto-expires**: Sessions expire after 2 hours

### 2. Encryption
- **Fernet encryption**: Industry-standard symmetric encryption
- **Key masking**: Shows only `sk-or-v...1234` in responses
- **Shared key**: Uses `BYOK_ENCRYPTION_KEY` environment variable

### 3. Rate Limiting
- **Test endpoint**: 10 tests per minute per user
- **Prevents abuse**: Blocks excessive API testing
- **Per-user tracking**: Separate limits for each admin

### 4. Error Handling
- **400**: Invalid provider type or key format
- **401**: Not authenticated (no session)
- **403**: Forbidden (not admin)
- **404**: Provider not found
- **429**: Rate limit exceeded
- **500**: Server error (DB/encryption failure)

---

## Database Schema

The API uses the existing `llm_providers` table (no migrations needed):

```sql
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL,
    api_key_encrypted TEXT,  -- Fernet encrypted
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 50,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    health_status VARCHAR(50) DEFAULT 'unknown',
    last_health_check TIMESTAMP,
    api_key_source VARCHAR(50) DEFAULT 'environment',
    api_key_updated_at TIMESTAMP,
    api_key_last_tested TIMESTAMP,
    api_key_test_status VARCHAR(20)
);
```

---

## Testing Guide

### Prerequisites

1. **Backend running**:
```bash
docker ps | grep ops-center-direct
```

2. **Admin session** (login as admin first):
- Visit: https://your-domain.com/auth/login
- Login as admin user

3. **Get session cookie**:
```bash
# Browser console
document.cookie
```

### Test 1: List Provider Keys

```bash
curl -X GET 'http://localhost:8084/api/v1/llm/providers/keys' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json'
```

**Expected**: List of providers with masked keys

---

### Test 2: Get Provider Info

```bash
curl -X GET 'http://localhost:8084/api/v1/llm/providers/info' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json'
```

**Expected**: List of 9 supported providers with descriptions

---

### Test 3: Save OpenRouter Key

```bash
curl -X POST 'http://localhost:8084/api/v1/llm/providers/keys' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider_type": "openrouter",
    "api_key": "sk-or-v1-YOUR-REAL-KEY-HERE",
    "name": "OpenRouter"
  }'
```

**Expected**: Success response with test results

---

### Test 4: Test Stored Key

```bash
curl -X POST 'http://localhost:8084/api/v1/llm/providers/keys/test' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider_type": "openrouter",
    "api_key": null
  }'
```

**Expected**: Test results with latency and model count

---

### Test 5: Test New Key (Before Saving)

```bash
curl -X POST 'http://localhost:8084/api/v1/llm/providers/keys/test' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider_type": "openai",
    "api_key": "sk-proj-YOUR-NEW-KEY-TO-TEST"
  }'
```

**Expected**: Test results without updating database

---

### Test 6: Delete Provider Key

```bash
curl -X DELETE 'http://localhost:8084/api/v1/llm/providers/keys/PROVIDER_UUID' \
  -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
  -H 'Content-Type: application/json'
```

**Expected**: Success message

---

### Test 7: Rate Limiting

```bash
# Run 11 test requests in quick succession
for i in {1..11}; do
  curl -X POST 'http://localhost:8084/api/v1/llm/providers/keys/test' \
    -H 'Cookie: session_token=YOUR_SESSION_TOKEN' \
    -H 'Content-Type: application/json' \
    -d '{"provider_type": "openrouter"}' &
done
wait
```

**Expected**: First 10 succeed, 11th returns 429 Rate Limit Exceeded

---

### Test 8: Unauthorized Access

```bash
curl -X GET 'http://localhost:8084/api/v1/llm/providers/keys' \
  -H 'Content-Type: application/json'
```

**Expected**: 401 Unauthorized (no session token)

---

## Frontend Integration

### Example: Fetch Provider Keys

```javascript
const response = await fetch('/api/v1/llm/providers/keys', {
  method: 'GET',
  credentials: 'include', // Include session cookie
  headers: {
    'Content-Type': 'application/json'
  }
});

const data = await response.json();
console.log(data.providers);
```

### Example: Save Provider Key

```javascript
const response = await fetch('/api/v1/llm/providers/keys', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    provider_type: 'openrouter',
    api_key: 'sk-or-v1-...',
    name: 'OpenRouter'
  })
});

const data = await response.json();
if (data.test_result?.success) {
  console.log('✅ Key tested successfully!');
}
```

### Example: Test Provider Key

```javascript
const response = await fetch('/api/v1/llm/providers/keys/test', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    provider_type: 'openrouter',
    api_key: null // Test stored key
  })
});

const result = await response.json();
console.log(`Latency: ${result.latency_ms}ms`);
console.log(`Models: ${result.models_found}`);
```

---

## Deployment Checklist

### Pre-deployment

- [ ] `BYOK_ENCRYPTION_KEY` environment variable set
- [ ] PostgreSQL connection pool initialized (`app.state.db_pool`)
- [ ] Redis session manager running (`app.state.sessions`)
- [ ] Admin users have `role: admin` in Keycloak

### Integration Steps

1. **Add import to server.py**:
```python
from provider_keys_api import router as provider_keys_router
```

2. **Register router in server.py**:
```python
app.include_router(provider_keys_router)
logger.info("Provider Keys API endpoints registered at /api/v1/llm/providers")
```

3. **Restart backend**:
```bash
docker restart ops-center-direct
```

4. **Verify endpoints**:
```bash
docker logs ops-center-direct | grep "Provider Keys API"
```

5. **Test with curl** (see Testing Guide above)

### Post-deployment

- [ ] List providers endpoint works
- [ ] Save key endpoint encrypts and stores correctly
- [ ] Test key endpoint validates against provider APIs
- [ ] Delete key endpoint removes from database
- [ ] Rate limiting blocks excessive tests
- [ ] Non-admin users get 403 Forbidden
- [ ] Unauthenticated requests get 401 Unauthorized

---

## Troubleshooting

### Error: "Database connection not available"

**Cause**: `app.state.db_pool` not initialized

**Fix**:
```bash
# Check server.py startup event (lines 350-410)
docker logs ops-center-direct | grep "PostgreSQL connection pool"
```

---

### Error: "BYOK_ENCRYPTION_KEY environment variable required"

**Cause**: Encryption key not set

**Fix**:
```bash
# Add to .env.auth
BYOK_ENCRYPTION_KEY=<your-32-byte-base64-key>

# Restart container
docker restart ops-center-direct
```

---

### Error: "Invalid session - please login again"

**Cause**: Session expired or invalid

**Fix**: Login again at `/auth/login` to get new session

---

### Error: "Rate limit exceeded"

**Cause**: More than 10 test requests in 60 seconds

**Fix**: Wait 60 seconds and try again

---

### Error: "No API key configured for provider"

**Cause**: Provider has no database key and no environment variable

**Fix**: Save a key first using POST `/api/v1/llm/providers/keys`

---

## Logging

The API logs all operations at INFO level:

```
INFO:provider_keys_api:Admin admin@example.com retrieved 9 provider keys
INFO:provider_keys_api:Admin admin@example.com added new provider key: OpenRouter
INFO:provider_keys_api:Admin admin@example.com tested openrouter API key: success
INFO:provider_keys_api:Admin admin@example.com deleted API key for provider: OpenAI
```

View logs:
```bash
docker logs ops-center-direct -f | grep provider_keys_api
```

---

## Performance

- **List providers**: ~50ms (database query + masking)
- **Save key**: ~300ms (encrypt + database + API test)
- **Test key**: ~200-500ms (API roundtrip)
- **Delete key**: ~30ms (database update)

**Caching**: Not implemented (admin operations, low frequency)

---

## Future Enhancements

1. **Bulk operations**: Add/test multiple keys at once
2. **Health monitoring**: Periodic background testing of all keys
3. **Usage tracking**: Track which providers are used most
4. **Cost estimation**: Show estimated costs per provider
5. **Webhook notifications**: Alert admins when keys fail
6. **Key rotation**: Automated key rotation reminders
7. **Multi-region**: Support provider-specific regions/endpoints

---

## Related Files

- **API Implementation**: `backend/provider_keys_api.py`
- **Existing System Key Manager**: `backend/litellm_api.py` (lines 222-378)
- **Database Schema**: `backend/migrations/create_llm_management_tables_v2.sql`
- **Frontend (TBD)**: `src/pages/LLMManagement.jsx` (Provider Keys tab)

---

**Questions?** Contact the Backend Development Team or see:
- LLM API docs: `backend/litellm_api.py`
- BYOK docs: `backend/byok_api.py`
- Ops-Center docs: `services/ops-center/CLAUDE.md`
