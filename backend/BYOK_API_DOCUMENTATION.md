# BYOK (Bring Your Own Key) REST API Documentation

**Date**: October 26, 2025
**Location**: `/services/ops-center/backend/litellm_api.py`
**Base URL**: `/api/v1/llm/byok`
**Status**: ✅ Production Ready

---

## Overview

The BYOK REST API allows users to securely store, manage, and use their own API keys for LLM providers (OpenRouter, OpenAI, Anthropic, Google). All keys are encrypted using Fernet symmetric encryption and stored in PostgreSQL.

**Key Features**:
- ✅ Secure encryption (Fernet) via `BYOKManager`
- ✅ API key format validation
- ✅ Provider API testing before storage
- ✅ Enable/disable keys without deletion
- ✅ Rate limiting (5 tests/minute)
- ✅ Usage statistics (Phase 2 placeholder)
- ✅ Comprehensive error handling

---

## API Endpoints

### 1. List Supported Providers

**Endpoint**: `GET /api/v1/llm/byok/providers`
**Authentication**: None required (public endpoint)
**Description**: Get list of all supported BYOK providers with signup info

**Response**:
```json
{
  "providers": [
    {
      "name": "openrouter",
      "display_name": "OpenRouter",
      "description": "Universal LLM proxy supporting 100+ models",
      "key_format": "sk-or-v1-...",
      "signup_url": "https://openrouter.ai",
      "docs_url": "https://openrouter.ai/docs",
      "supports_test": true
    },
    {
      "name": "openai",
      "display_name": "OpenAI",
      "description": "GPT-4, GPT-3.5, and other OpenAI models",
      "key_format": "sk-...",
      "signup_url": "https://platform.openai.com",
      "docs_url": "https://platform.openai.com/docs",
      "supports_test": true
    }
    // ... more providers
  ]
}
```

**Example**:
```bash
curl http://localhost:8084/api/v1/llm/byok/providers | jq
```

---

### 2. List User's BYOK Keys

**Endpoint**: `GET /api/v1/llm/byok/keys`
**Authentication**: Required (Bearer token)
**Description**: List all API keys for the authenticated user (keys are masked)

**Response**:
```json
{
  "providers": [
    {
      "id": "uuid",
      "provider": "openrouter",
      "enabled": true,
      "masked_key": "***...outer",
      "created_at": "2025-10-26T10:30:00Z",
      "updated_at": "2025-10-26T10:30:00Z",
      "metadata": {}
    }
  ],
  "total": 1
}
```

**Example**:
```bash
curl -H "Authorization: Bearer USER_TOKEN" \
  http://localhost:8084/api/v1/llm/byok/keys | jq
```

---

### 3. Add/Update BYOK Key

**Endpoint**: `POST /api/v1/llm/byok/keys`
**Authentication**: Required (Bearer token)
**Description**: Add or update an API key for a provider

**Request Body**:
```json
{
  "provider": "openrouter",
  "api_key": "sk-or-v1-...",
  "metadata": {
    "model_preference": "gpt-4",
    "notes": "Production key"
  }
}
```

**Response**:
```json
{
  "success": true,
  "key_id": "uuid",
  "provider": "openrouter",
  "message": "API key stored successfully",
  "test_result": {
    "success": true,
    "message": "Valid OpenRouter key. 150 models available.",
    "model_count": 150
  }
}
```

**Validation**:
- Provider must be one of: `openrouter`, `openai`, `anthropic`, `google`
- API key length must be at least 10 characters
- Key format is validated via `BYOKManager.validate_api_key()`
- Key is optionally tested against provider API (non-blocking)

**Example**:
```bash
curl -X POST http://localhost:8084/api/v1/llm/byok/keys \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openrouter",
    "api_key": "sk-or-v1-abc123...",
    "metadata": {"tier": "production"}
  }' | jq
```

**Error Codes**:
- `400`: Invalid provider or key format
- `401`: Authentication required
- `500`: Storage failed (encryption error)

---

### 4. Delete BYOK Key

**Endpoint**: `DELETE /api/v1/llm/byok/keys/{provider}`
**Authentication**: Required (Bearer token)
**Description**: Permanently delete an API key for a provider

**Path Parameters**:
- `provider`: Provider name (openrouter, openai, anthropic, google)

**Response**:
```json
{
  "success": true,
  "provider": "openrouter"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8084/api/v1/llm/byok/keys/openrouter \
  -H "Authorization: Bearer USER_TOKEN" | jq
```

**Error Codes**:
- `404`: Key not found for this provider
- `401`: Authentication required
- `500`: Delete failed

---

### 5. Toggle Enable/Disable

**Endpoint**: `POST /api/v1/llm/byok/keys/{provider}/toggle`
**Authentication**: Required (Bearer token)
**Description**: Enable or disable a key without deleting it

**Path Parameters**:
- `provider`: Provider name

**Request Body**:
```json
{
  "enabled": false
}
```

**Response**:
```json
{
  "success": true,
  "provider": "openrouter",
  "enabled": false,
  "message": "API key for openrouter disabled successfully"
}
```

**Example**:
```bash
curl -X POST http://localhost:8084/api/v1/llm/byok/keys/openrouter/toggle \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq
```

**Error Codes**:
- `404`: Key not found for this provider
- `401`: Authentication required
- `500`: Toggle failed

---

### 6. Test BYOK Key

**Endpoint**: `POST /api/v1/llm/byok/keys/{provider}/test`
**Authentication**: Required (Bearer token)
**Description**: Test if the stored API key is valid by making a test request to the provider

**Rate Limit**: 5 tests per minute per user

**Path Parameters**:
- `provider`: Provider name to test

**Response**:
```json
{
  "success": true,
  "provider": "openrouter",
  "message": "Valid OpenRouter key. 150 models available.",
  "details": {
    "model_count": 150
  }
}
```

**Test Methods by Provider**:
- **OpenRouter**: `GET /api/v1/models` (list available models)
- **OpenAI**: `GET /v1/models` (list models)
- **Anthropic**: `POST /v1/messages` (minimal test request)
- **Google**: `GET /v1beta/models` (list models)

**Example**:
```bash
curl -X POST http://localhost:8084/api/v1/llm/byok/keys/openrouter/test \
  -H "Authorization: Bearer USER_TOKEN" | jq
```

**Error Codes**:
- `404`: Key not found for this provider
- `429`: Rate limit exceeded (max 5 tests/minute)
- `401`: Authentication required
- `500`: Test failed

---

### 7. Get Usage Statistics

**Endpoint**: `GET /api/v1/llm/byok/keys/{provider}/usage`
**Authentication**: Required (Bearer token)
**Description**: Get usage statistics for a BYOK key (Phase 2 - currently placeholder)

**Path Parameters**:
- `provider`: Provider name

**Response** (Placeholder):
```json
{
  "provider": "openrouter",
  "total_requests": 0,
  "total_tokens": 0,
  "total_cost": 0.0,
  "last_used": null,
  "message": "Usage tracking integration coming in Phase 2"
}
```

**Example**:
```bash
curl -H "Authorization: Bearer USER_TOKEN" \
  http://localhost:8084/api/v1/llm/byok/keys/openrouter/usage | jq
```

**Note**: This endpoint currently returns placeholder data. Full integration with `usage_metering` table planned for Phase 2.

---

## Pydantic Models

### AddBYOKKeyRequest
```python
class AddBYOKKeyRequest(BaseModel):
    provider: str  # openrouter, openai, anthropic, google
    api_key: str   # min 10 characters
    metadata: Optional[Dict] = None
```

### ToggleBYOKRequest
```python
class ToggleBYOKRequest(BaseModel):
    enabled: bool  # True to enable, False to disable
```

---

## Security Features

### 1. Encryption
- All API keys encrypted using **Fernet symmetric encryption**
- Encryption key stored in `BYOK_ENCRYPTION_KEY` environment variable
- Keys encrypted before storage, decrypted only when needed

### 2. Authentication
- All endpoints require authentication (except `/providers`)
- User ID extracted from JWT bearer token via `get_user_id()` dependency
- Keys are scoped to individual users (no cross-user access)

### 3. Rate Limiting
- Test endpoint limited to **5 requests per minute per user**
- In-memory rate limiter (simple but effective)
- Prevents abuse of provider APIs

### 4. Validation
- API key format validated before storage
- Provider name validated against whitelist
- Optional API testing before storage (non-blocking)

### 5. Audit Logging
- All operations logged with user ID and provider
- Success/failure logged for troubleshooting
- Test results logged for monitoring

---

## Database Schema

**Table**: `user_provider_keys`

```sql
CREATE TABLE user_provider_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    metadata JSONB,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    UNIQUE(user_id, provider)
);
```

**Indexes**:
- Primary key on `id`
- Unique constraint on `(user_id, provider)`
- Index on `user_id` for fast lookups

---

## Integration with LiteLLM Routing

When a user makes an LLM chat completion request, the system checks for BYOK keys:

```python
# In chat_completions endpoint (litellm_api.py)
user_keys = await byok_manager.get_all_user_keys(user_id)

if 'openrouter' in user_keys:
    # User has OpenRouter BYOK - use it for ALL models
    using_byok = True
    user_byok_key = user_keys['openrouter']
    # NO CREDITS CHARGED - user pays provider directly
else:
    # Check for provider-specific BYOK
    detected_provider = detect_provider_from_model(request.model)
    if detected_provider in user_keys:
        using_byok = True
        user_byok_key = user_keys[detected_provider]
```

**BYOK Routing Priority**:
1. **OpenRouter BYOK** - If user has OpenRouter key, use it for ALL models (universal proxy)
2. **Provider-specific BYOK** - Use direct provider keys (openai, anthropic, google)
3. **System OpenRouter** - Fall back to system key (charge credits)

**Cost Implications**:
- **BYOK requests**: `actual_cost = 0.0` (user pays provider directly, no credit charge)
- **System key requests**: Credits deducted based on tier and usage

---

## Error Handling

### Comprehensive Error Responses

All endpoints follow consistent error response format:

```json
{
  "detail": "Human-readable error message"
}
```

**Common Error Codes**:
- `400 Bad Request`: Invalid provider, key format, or request data
- `401 Unauthorized`: Missing or invalid authentication token
- `404 Not Found`: Key not found for specified provider
- `429 Too Many Requests`: Rate limit exceeded (test endpoint)
- `500 Internal Server Error`: Database, encryption, or unexpected errors
- `503 Service Unavailable`: Provider API unreachable (test endpoint)

---

## Testing the API

### 1. List Providers (No Auth)
```bash
curl http://localhost:8084/api/v1/llm/byok/providers | jq
```

### 2. Add OpenRouter Key
```bash
curl -X POST http://localhost:8084/api/v1/llm/byok/keys \
  -H "Authorization: Bearer test_user_123" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openrouter",
    "api_key": "sk-or-v1-test123...",
    "metadata": {"tier": "prod"}
  }' | jq
```

### 3. List User's Keys
```bash
curl -H "Authorization: Bearer test_user_123" \
  http://localhost:8084/api/v1/llm/byok/keys | jq
```

### 4. Test Key
```bash
curl -X POST http://localhost:8084/api/v1/llm/byok/keys/openrouter/test \
  -H "Authorization: Bearer test_user_123" | jq
```

### 5. Disable Key
```bash
curl -X POST http://localhost:8084/api/v1/llm/byok/keys/openrouter/toggle \
  -H "Authorization: Bearer test_user_123" \
  -H "Content-Type: application/json" \
  -d '{"enabled": false}' | jq
```

### 6. Delete Key
```bash
curl -X DELETE http://localhost:8084/api/v1/llm/byok/keys/openrouter \
  -H "Authorization: Bearer test_user_123" | jq
```

---

## Future Enhancements (Phase 2)

### 1. Usage Tracking Integration
- Query `usage_metering` table for BYOK requests
- Return real usage stats (requests, tokens, cost, last_used)
- Per-provider usage analytics

### 2. Additional Providers
- Together AI
- Fireworks AI
- DeepInfra
- Groq
- HuggingFace

### 3. Enhanced Validation
- Regex patterns for each provider's key format
- Automatic key rotation warnings
- Expiration date tracking

### 4. Advanced Features
- API key health monitoring (daily tests)
- Usage alerts (approaching provider limits)
- Automatic failover (BYOK → system key)
- Multi-key support (multiple keys per provider)

### 5. Frontend Integration
- React component for BYOK management
- Key testing UI with real-time results
- Usage charts and analytics
- Provider signup links and documentation

---

## Files Modified

**Backend**:
- `/services/ops-center/backend/litellm_api.py` (enhanced with 4 new endpoints)
- `/services/ops-center/backend/byok_manager.py` (already existed, using as-is)

**Dependencies**:
- `httpx` - HTTP client for testing provider APIs
- `cryptography` - Fernet encryption
- `asyncpg` - PostgreSQL driver
- `pydantic` - Request/response validation

---

## Summary

✅ **Implemented 6 BYOK endpoints**:
1. `GET /byok/providers` - List supported providers
2. `GET /byok/keys` - List user's keys (masked)
3. `POST /byok/keys` - Add/update key with validation & testing
4. `DELETE /byok/keys/{provider}` - Delete key
5. `POST /byok/keys/{provider}/toggle` - Enable/disable key
6. `POST /byok/keys/{provider}/test` - Test key against provider API
7. `GET /byok/keys/{provider}/usage` - Get usage stats (Phase 2 placeholder)

✅ **Security Features**:
- Fernet encryption for all keys
- User-scoped access (no cross-user access)
- Rate limiting (5 tests/min)
- Comprehensive audit logging

✅ **Production Ready**:
- All endpoints tested and working
- Comprehensive error handling
- Pydantic validation
- Integration with existing LiteLLM routing

**Status**: Ready for frontend integration!
