# LLM Configuration Management API

**Version**: 1.0.0
**Base Path**: `/api/v1/llm-config`
**Authentication**: Admin role required
**Status**: Production Ready

---

## Overview

The LLM Configuration Management API provides comprehensive endpoints for managing:

1. **AI Servers** - Self-hosted AI inference servers (vLLM, Ollama, llama.cpp, OpenAI-compatible)
2. **API Keys** - 3rd party provider API keys (OpenRouter, OpenAI, Anthropic, etc.) with encrypted storage
3. **Active Providers** - Configure which provider to use for each purpose (chat, embeddings, reranking)

**Key Features**:
- Secure API key storage with Fernet encryption
- Health checking for AI servers
- Automatic model discovery
- Active provider configuration with fallback support
- Comprehensive audit logging
- Admin-only access control

---

## Authentication

All endpoints require admin authentication via Keycloak SSO session cookies.

**Required Role**: `admin`

**Headers**:
```
Cookie: session_token=<keycloak-session-token>
```

**Unauthorized Response** (401):
```json
{
  "detail": "Not authenticated"
}
```

**Forbidden Response** (403):
```json
{
  "detail": "Admin role required"
}
```

---

## AI Server Management

### List AI Servers

**Endpoint**: `GET /api/v1/llm-config/servers`

**Query Parameters**:
- `enabled_only` (boolean, optional) - Only return enabled servers (default: false)

**Response** (200):
```json
[
  {
    "id": 1,
    "name": "Local vLLM Server",
    "server_type": "vllm",
    "base_url": "http://localhost:8000",
    "api_key": null,
    "model_path": "/models/Qwen2.5-32B-Instruct-AWQ",
    "enabled": true,
    "use_for_chat": true,
    "use_for_embeddings": false,
    "use_for_reranking": false,
    "last_health_check": "2025-10-20T10:30:00Z",
    "health_status": "healthy",
    "metadata": {
      "gpu_memory_utilization": 0.95,
      "tensor_parallel": 1
    },
    "created_by": "admin",
    "created_at": "2025-10-15T08:00:00Z",
    "updated_at": "2025-10-20T10:30:00Z"
  }
]
```

**Server Types**:
- `vllm` - vLLM inference server
- `ollama` - Ollama local server
- `llamacpp` - llama.cpp server
- `openai-compatible` - Any OpenAI API-compatible server

**Health Status Values**:
- `healthy` - Server is responding normally
- `degraded` - Server responding but with issues
- `down` - Server not responding
- `unknown` - Never tested or test pending

---

### Get AI Server

**Endpoint**: `GET /api/v1/llm-config/servers/{server_id}`

**Path Parameters**:
- `server_id` (integer) - Server ID

**Response** (200):
```json
{
  "id": 1,
  "name": "Local vLLM Server",
  "server_type": "vllm",
  "base_url": "http://localhost:8000",
  "enabled": true,
  "use_for_chat": true,
  "health_status": "healthy",
  ...
}
```

**Not Found** (404):
```json
{
  "detail": "Server 123 not found"
}
```

---

### Create AI Server

**Endpoint**: `POST /api/v1/llm-config/servers`

**Request Body**:
```json
{
  "name": "Local vLLM Server",
  "server_type": "vllm",
  "base_url": "http://localhost:8000",
  "api_key": null,
  "model_path": "/models/Qwen2.5-32B-Instruct-AWQ",
  "enabled": true,
  "use_for_chat": true,
  "use_for_embeddings": false,
  "use_for_reranking": false,
  "metadata": {
    "gpu_memory_utilization": 0.95,
    "tensor_parallel": 1,
    "max_model_len": 16384
  }
}
```

**Required Fields**:
- `name` (string) - Friendly name
- `server_type` (string) - One of: vllm, ollama, llamacpp, openai-compatible
- `base_url` (string) - Server URL (must start with http:// or https://)

**Optional Fields**:
- `api_key` (string) - API key for protected endpoints
- `model_path` (string) - Model path for vLLM/llama.cpp
- `enabled` (boolean) - Enable immediately (default: true)
- `use_for_chat` (boolean) - Use for chat inference (default: false)
- `use_for_embeddings` (boolean) - Use for embeddings (default: false)
- `use_for_reranking` (boolean) - Use for reranking (default: false)
- `metadata` (object) - Additional configuration

**Response** (201):
```json
{
  "id": 2,
  "name": "Local vLLM Server",
  "server_type": "vllm",
  "created_at": "2025-10-20T11:00:00Z",
  ...
}
```

**Validation Errors** (422):
```json
{
  "detail": [
    {
      "loc": ["body", "server_type"],
      "msg": "server_type must be one of: vllm, ollama, llamacpp, openai-compatible",
      "type": "value_error"
    }
  ]
}
```

---

### Update AI Server

**Endpoint**: `PUT /api/v1/llm-config/servers/{server_id}`

**Path Parameters**:
- `server_id` (integer) - Server ID

**Request Body** (all fields optional):
```json
{
  "name": "Updated Server Name",
  "enabled": false,
  "use_for_chat": false,
  "metadata": {
    "notes": "Server undergoing maintenance"
  }
}
```

**Allowed Fields**:
- `name`, `server_type`, `base_url`, `api_key`, `model_path`
- `enabled`, `use_for_chat`, `use_for_embeddings`, `use_for_reranking`
- `metadata`

**Response** (200):
```json
{
  "id": 1,
  "name": "Updated Server Name",
  "updated_at": "2025-10-20T11:30:00Z",
  ...
}
```

**Not Found** (404):
```json
{
  "detail": "Server 123 not found"
}
```

---

### Delete AI Server

**Endpoint**: `DELETE /api/v1/llm-config/servers/{server_id}`

**Path Parameters**:
- `server_id` (integer) - Server ID

**Response** (204):
No content (success)

**In Use Error** (400):
```json
{
  "detail": "Cannot delete server in use for: chat, embeddings"
}
```

**Not Found** (404):
```json
{
  "detail": "Server 123 not found"
}
```

---

### Test AI Server Connection

**Endpoint**: `POST /api/v1/llm-config/servers/{server_id}/test`

**Path Parameters**:
- `server_id` (integer) - Server ID

**Response** (200):
```json
{
  "server_id": 1,
  "status": "healthy",
  "message": "Healthy - 5 models available",
  "timestamp": "2025-10-20T12:00:00Z"
}
```

**Status Values**:
- `healthy` - Server responding normally
- `degraded` - Server responding but with issues
- `down` - Server not responding
- `unknown` - Test failed unexpectedly

**Example Error Response**:
```json
{
  "server_id": 1,
  "status": "down",
  "message": "HTTP 500: Internal Server Error",
  "timestamp": "2025-10-20T12:00:00Z"
}
```

**Notes**:
- Updates `health_status` and `last_health_check` in database
- For vLLM/llama.cpp/OpenAI-compatible: Tests `/v1/models` endpoint
- For Ollama: Tests `/api/tags` endpoint

---

### Get Available Models

**Endpoint**: `GET /api/v1/llm-config/servers/{server_id}/models`

**Path Parameters**:
- `server_id` (integer) - Server ID

**Response** (200):
```json
[
  "Qwen/Qwen2.5-32B-Instruct-AWQ",
  "meta-llama/Llama-3.1-70B-Instruct",
  "mistralai/Mixtral-8x7B-Instruct-v0.1"
]
```

**Empty Response** (server down or no models):
```json
[]
```

**Notes**:
- Queries server's `/v1/models` endpoint (or `/api/tags` for Ollama)
- Returns list of model IDs/names
- Empty array if server unavailable or has no models

---

## API Key Management

### List API Keys

**Endpoint**: `GET /api/v1/llm-config/api-keys`

**Query Parameters**:
- `enabled_only` (boolean, optional) - Only return enabled keys (default: false)

**Response** (200):
```json
[
  {
    "id": 1,
    "provider": "openrouter",
    "key_name": "Default OpenRouter Key",
    "masked_key": "****e5d80",
    "enabled": true,
    "use_for_ops_center": true,
    "last_used": "2025-10-20T10:00:00Z",
    "requests_count": 1523,
    "tokens_used": 482756,
    "cost_usd": 12.45,
    "metadata": {
      "source": "pre-populated"
    },
    "created_by": "system",
    "created_at": "2025-10-15T08:00:00Z",
    "updated_at": "2025-10-20T10:00:00Z"
  }
]
```

**Security**:
- API keys are NEVER returned in plaintext
- Only masked versions shown (last 4 characters)

**Supported Providers**:
- `openrouter` - OpenRouter (100+ models)
- `openai` - OpenAI (GPT-4, GPT-3.5, etc.)
- `anthropic` - Anthropic (Claude)
- `google` - Google (Gemini)
- `cohere` - Cohere
- `together` - Together AI
- `fireworks` - Fireworks AI

---

### Get API Key

**Endpoint**: `GET /api/v1/llm-config/api-keys/{key_id}`

**Path Parameters**:
- `key_id` (integer) - API key ID

**Response** (200):
```json
{
  "id": 1,
  "provider": "openrouter",
  "key_name": "Default OpenRouter Key",
  "masked_key": "****e5d80",
  "enabled": true,
  ...
}
```

**Not Found** (404):
```json
{
  "detail": "API key 123 not found"
}
```

---

### Create API Key

**Endpoint**: `POST /api/v1/llm-config/api-keys`

**Request Body**:
```json
{
  "provider": "openrouter",
  "key_name": "Production OpenRouter Key",
  "api_key": "sk-or-v1-abc123...",
  "use_for_ops_center": true,
  "metadata": {
    "rate_limit": 10000,
    "cost_limit_usd": 100
  }
}
```

**Required Fields**:
- `provider` (string) - Provider name (openrouter, openai, anthropic, google, cohere, together, fireworks)
- `key_name` (string) - Friendly name for UI
- `api_key` (string) - Plaintext API key (will be encrypted)

**Optional Fields**:
- `use_for_ops_center` (boolean) - Use for ops-center services (default: false)
- `metadata` (object) - Rate limits, quotas, etc.

**Response** (201):
```json
{
  "id": 2,
  "provider": "openrouter",
  "key_name": "Production OpenRouter Key",
  "masked_key": "****abc123",
  "enabled": true,
  "created_at": "2025-10-20T11:00:00Z",
  ...
}
```

**Security**:
- API key is encrypted with Fernet before storage
- Plaintext key is NEVER stored in database
- Only masked version returned in response

**Validation Errors** (422):
```json
{
  "detail": [
    {
      "loc": ["body", "provider"],
      "msg": "provider must be one of: openrouter, openai, anthropic, google, cohere, together, fireworks",
      "type": "value_error"
    }
  ]
}
```

---

### Update API Key

**Endpoint**: `PUT /api/v1/llm-config/api-keys/{key_id}`

**Path Parameters**:
- `key_id` (integer) - API key ID

**Request Body** (all fields optional):
```json
{
  "key_name": "Updated Key Name",
  "api_key": "sk-or-v1-new-key...",
  "enabled": false,
  "use_for_ops_center": false,
  "metadata": {
    "notes": "Key rotated"
  }
}
```

**Allowed Fields**:
- `key_name` - Update friendly name
- `api_key` - Rotate key (will be re-encrypted)
- `enabled` - Enable/disable key
- `use_for_ops_center` - Toggle ops-center usage
- `metadata` - Update metadata

**Response** (200):
```json
{
  "id": 1,
  "key_name": "Updated Key Name",
  "masked_key": "****new-key",
  "updated_at": "2025-10-20T11:30:00Z",
  ...
}
```

**Security**:
- If `api_key` provided, old key is overwritten with new encrypted key
- No key rotation history is kept (security by design)

---

### Delete API Key

**Endpoint**: `DELETE /api/v1/llm-config/api-keys/{key_id}`

**Path Parameters**:
- `key_id` (integer) - API key ID

**Response** (204):
No content (success)

**In Use Error** (400):
```json
{
  "detail": "Cannot delete API key in use for: chat"
}
```

**Not Found** (404):
```json
{
  "detail": "API key 123 not found"
}
```

---

### Test API Key

**Endpoint**: `POST /api/v1/llm-config/api-keys/{key_id}/test`

**Path Parameters**:
- `key_id` (integer) - API key ID

**Response** (200):
```json
{
  "key_id": 1,
  "success": true,
  "message": "Valid - 248 models available",
  "timestamp": "2025-10-20T12:00:00Z"
}
```

**Failed Test**:
```json
{
  "key_id": 1,
  "success": false,
  "message": "HTTP 401: Invalid API key",
  "timestamp": "2025-10-20T12:00:00Z"
}
```

**Test Methods by Provider**:
- **OpenRouter**: GET `/api/v1/models`
- **OpenAI**: GET `/v1/models`
- **Anthropic**: POST `/v1/messages` (minimal request)

**Notes**:
- Makes minimal request to validate key
- Does NOT update usage statistics (tokens_used, requests_count, etc.)
- Useful for troubleshooting and key validation

---

## Active Provider Configuration

### Get All Active Providers

**Endpoint**: `GET /api/v1/llm-config/active`

**Response** (200):
```json
{
  "chat": {
    "purpose": "chat",
    "provider_type": "api_key",
    "provider_id": 1,
    "provider": {
      "id": 1,
      "provider": "openrouter",
      "key_name": "Default OpenRouter Key",
      "masked_key": "****e5d80",
      "enabled": true,
      ...
    },
    "fallback_provider_type": null,
    "fallback_provider_id": null,
    "updated_by": "admin",
    "updated_at": "2025-10-15T08:00:00Z"
  },
  "embeddings": {
    "purpose": "embeddings",
    "provider_type": "ai_server",
    "provider_id": 1,
    "provider": {
      "id": 1,
      "name": "Local vLLM Server",
      "server_type": "vllm",
      ...
    },
    "updated_by": "admin",
    "updated_at": "2025-10-16T09:00:00Z"
  }
}
```

**Empty Response** (no providers configured):
```json
{}
```

---

### Get Active Provider for Purpose

**Endpoint**: `GET /api/v1/llm-config/active/{purpose}`

**Path Parameters**:
- `purpose` (string) - One of: chat, embeddings, reranking

**Response** (200):
```json
{
  "purpose": "chat",
  "provider_type": "api_key",
  "provider_id": 1,
  "provider": {
    "id": 1,
    "provider": "openrouter",
    "key_name": "Default OpenRouter Key",
    ...
  },
  "fallback_provider_type": "ai_server",
  "fallback_provider_id": 2,
  "updated_by": "admin",
  "updated_at": "2025-10-15T08:00:00Z"
}
```

**Not Found** (404):
```json
{
  "detail": "No active provider for chat"
}
```

**Invalid Purpose** (400):
```json
{
  "detail": "Invalid purpose. Must be one of: chat, embeddings, reranking"
}
```

---

### Set Active Provider

**Endpoint**: `POST /api/v1/llm-config/active`

**Request Body**:
```json
{
  "purpose": "chat",
  "provider_type": "api_key",
  "provider_id": 1,
  "fallback_provider_type": "ai_server",
  "fallback_provider_id": 2
}
```

**Required Fields**:
- `purpose` (string) - One of: chat, embeddings, reranking
- `provider_type` (string) - One of: ai_server, api_key
- `provider_id` (integer) - ID of the provider

**Optional Fields**:
- `fallback_provider_type` (string) - Fallback provider type
- `fallback_provider_id` (integer) - Fallback provider ID

**Response** (200):
```json
{
  "message": "Active provider set for chat"
}
```

**Provider Not Found** (404):
```json
{
  "detail": "API key 123 not found"
}
```

**Example Use Cases**:

1. **Use OpenRouter for chat**:
```json
{
  "purpose": "chat",
  "provider_type": "api_key",
  "provider_id": 1
}
```

2. **Use local vLLM for embeddings with OpenRouter fallback**:
```json
{
  "purpose": "embeddings",
  "provider_type": "ai_server",
  "provider_id": 1,
  "fallback_provider_type": "api_key",
  "fallback_provider_id": 1
}
```

---

## Health Check

### API Health Check

**Endpoint**: `GET /api/v1/llm-config/health`

**Response** (200):
```json
{
  "status": "healthy",
  "service": "LLM Configuration API"
}
```

---

## Data Models

### AIServer

```typescript
{
  id: number
  name: string
  server_type: "vllm" | "ollama" | "llamacpp" | "openai-compatible"
  base_url: string
  api_key?: string
  model_path?: string
  enabled: boolean
  use_for_chat: boolean
  use_for_embeddings: boolean
  use_for_reranking: boolean
  last_health_check?: string (ISO 8601)
  health_status: "healthy" | "degraded" | "down" | "unknown"
  metadata: object
  created_by: string
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

### APIKey

```typescript
{
  id: number
  provider: "openrouter" | "openai" | "anthropic" | "google" | "cohere" | "together" | "fireworks"
  key_name: string
  masked_key: string  // "****abc123"
  enabled: boolean
  use_for_ops_center: boolean
  last_used?: string (ISO 8601)
  requests_count: number
  tokens_used: number
  cost_usd: number
  metadata: object
  created_by: string
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

### ActiveProvider

```typescript
{
  purpose: "chat" | "embeddings" | "reranking"
  provider_type: "ai_server" | "api_key"
  provider_id: number
  provider: AIServer | APIKey  // Full provider object
  fallback_provider_type?: "ai_server" | "api_key"
  fallback_provider_id?: number
  updated_by?: string
  updated_at?: string (ISO 8601)
}
```

---

## Error Responses

### Standard Error Format

All error responses follow this format:

```json
{
  "detail": "Error message"
}
```

### HTTP Status Codes

- **200 OK** - Success
- **201 Created** - Resource created
- **204 No Content** - Success with no response body
- **400 Bad Request** - Validation error or business logic error
- **401 Unauthorized** - Not authenticated
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation errors (Pydantic)
- **500 Internal Server Error** - Server error

### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "error_type"
    }
  ]
}
```

---

## Security

### Encryption

- **API keys** are encrypted using Fernet symmetric encryption
- **Encryption key** stored in `BYOK_ENCRYPTION_KEY` environment variable
- **Never stored** in plaintext in database
- **Never returned** in API responses (only masked versions)

### Audit Logging

All configuration changes are logged to `llm_config_audit` table:

```sql
SELECT * FROM llm_config_audit
WHERE user_id = 'admin'
ORDER BY timestamp DESC
LIMIT 10;
```

Logged actions:
- `add_server`, `update_server`, `delete_server`
- `add_key`, `update_key`, `delete_key`
- `set_active`

### Access Control

- **All endpoints** require admin role
- **Authentication** via Keycloak SSO session cookies
- **Authorization** checked on every request
- **No API key authentication** (session-based only)

---

## Database Schema

### Tables Created

```sql
-- AI server configurations
CREATE TABLE ai_servers (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  server_type TEXT NOT NULL,
  base_url TEXT NOT NULL,
  api_key TEXT,
  model_path TEXT,
  enabled BOOLEAN DEFAULT TRUE,
  use_for_chat BOOLEAN DEFAULT FALSE,
  use_for_embeddings BOOLEAN DEFAULT FALSE,
  use_for_reranking BOOLEAN DEFAULT FALSE,
  last_health_check TIMESTAMP,
  health_status TEXT,
  metadata JSONB DEFAULT '{}',
  created_by TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Encrypted API keys
CREATE TABLE llm_api_keys (
  id SERIAL PRIMARY KEY,
  provider TEXT NOT NULL,
  key_name TEXT NOT NULL,
  encrypted_key TEXT NOT NULL,
  enabled BOOLEAN DEFAULT TRUE,
  use_for_ops_center BOOLEAN DEFAULT FALSE,
  last_used TIMESTAMP,
  requests_count INTEGER DEFAULT 0,
  tokens_used BIGINT DEFAULT 0,
  cost_usd NUMERIC(10, 4) DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_by TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(provider, key_name)
);

-- Active provider configuration
CREATE TABLE active_providers (
  purpose TEXT PRIMARY KEY,
  provider_type TEXT NOT NULL,
  provider_id INTEGER NOT NULL,
  fallback_provider_type TEXT,
  fallback_provider_id INTEGER,
  updated_by TEXT,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Audit log
CREATE TABLE llm_config_audit (
  id SERIAL PRIMARY KEY,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id INTEGER,
  user_id TEXT NOT NULL,
  changes JSONB,
  timestamp TIMESTAMP DEFAULT NOW()
);
```

### Initialize Schema

Run on server startup:

```bash
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /app/sql/llm_config_schema.sql
```

Or manually:

```bash
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < backend/sql/llm_config_schema.sql
```

---

## Example Workflows

### Workflow 1: Set Up Local vLLM Server

```bash
# 1. Create AI server
curl -X POST http://localhost:8084/api/v1/llm-config/servers \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "name": "Local vLLM Server",
    "server_type": "vllm",
    "base_url": "http://localhost:8000",
    "enabled": true,
    "use_for_chat": true,
    "metadata": {
      "gpu_memory_utilization": 0.95,
      "tensor_parallel": 1
    }
  }'

# Response: {"id": 1, "name": "Local vLLM Server", ...}

# 2. Test connection
curl -X POST http://localhost:8084/api/v1/llm-config/servers/1/test \
  -H "Cookie: session_token=$SESSION_TOKEN"

# Response: {"status": "healthy", "message": "Healthy - 1 models available"}

# 3. Get available models
curl http://localhost:8084/api/v1/llm-config/servers/1/models \
  -H "Cookie: session_token=$SESSION_TOKEN"

# Response: ["Qwen/Qwen2.5-32B-Instruct-AWQ"]

# 4. Set as active provider for chat
curl -X POST http://localhost:8084/api/v1/llm-config/active \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "purpose": "chat",
    "provider_type": "ai_server",
    "provider_id": 1
  }'

# Response: {"message": "Active provider set for chat"}
```

### Workflow 2: Add OpenRouter API Key

```bash
# 1. Create API key
curl -X POST http://localhost:8084/api/v1/llm-config/api-keys \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "provider": "openrouter",
    "key_name": "Production OpenRouter Key",
    "api_key": "sk-or-v1-abc123...",
    "use_for_ops_center": true
  }'

# Response: {"id": 1, "masked_key": "****abc123", ...}

# 2. Test API key
curl -X POST http://localhost:8084/api/v1/llm-config/api-keys/1/test \
  -H "Cookie: session_token=$SESSION_TOKEN"

# Response: {"success": true, "message": "Valid - 248 models available"}

# 3. Set as active provider for chat with local vLLM fallback
curl -X POST http://localhost:8084/api/v1/llm-config/active \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "purpose": "chat",
    "provider_type": "api_key",
    "provider_id": 1,
    "fallback_provider_type": "ai_server",
    "fallback_provider_id": 1
  }'
```

### Workflow 3: Health Monitoring

```bash
# 1. List all servers with health status
curl http://localhost:8084/api/v1/llm-config/servers \
  -H "Cookie: session_token=$SESSION_TOKEN"

# 2. Test specific server
curl -X POST http://localhost:8084/api/v1/llm-config/servers/1/test \
  -H "Cookie: session_token=$SESSION_TOKEN"

# 3. Disable unhealthy server
curl -X PUT http://localhost:8084/api/v1/llm-config/servers/1 \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "enabled": false,
    "metadata": {"notes": "Server down for maintenance"}
  }'

# 4. Switch to fallback provider
curl -X POST http://localhost:8084/api/v1/llm-config/active \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "purpose": "chat",
    "provider_type": "api_key",
    "provider_id": 2
  }'
```

---

## Integration with Frontend

The frontend agent will build React components to consume these APIs:

**Components to Build**:
1. **AIServerList** - List/add/edit/delete AI servers
2. **APIKeyList** - List/add/edit/delete API keys (with masked display)
3. **ActiveProviderConfig** - Configure active providers per purpose
4. **HealthDashboard** - Monitor server health with auto-refresh
5. **ModelExplorer** - Browse available models from all sources

**UI Pages**:
- `/admin/llm-config/servers` - AI server management
- `/admin/llm-config/api-keys` - API key management
- `/admin/llm-config/active` - Active provider configuration

**State Management**:
- React Context for LLM configuration state
- Auto-refresh health status every 60 seconds
- Toast notifications for success/error
- Loading states during async operations

---

## Deployment Notes

### Environment Variables

```bash
# Required
BYOK_ENCRYPTION_KEY=<fernet-key>  # For API key encryption
DATABASE_URL=postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db
REDIS_HOST=unicorn-redis
REDIS_PORT=6379

# Optional
OPENROUTER_API_KEY=<default-key>  # Pre-populated on first run
```

### Startup Sequence

1. Database pool created
2. Redis client connected
3. LLMConfigManager initialized with encryption key
4. Default configurations initialized (OpenRouter key)
5. Router registered at `/api/v1/llm-config`
6. Health check available

### Database Migration

```bash
# Run schema creation
docker exec -i unicorn-postgresql psql -U unicorn -d unicorn_db < backend/sql/llm_config_schema.sql

# Verify tables
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt llm*"

# Check default OpenRouter key
docker exec ops-center-direct python3 -c "
import asyncio
from llm_config_manager import LLMConfigManager
import asyncpg

async def check():
    pool = await asyncpg.create_pool('postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db')
    mgr = LLMConfigManager(pool, 'test-key')
    keys = await mgr.list_api_keys()
    print(f'Found {len(keys)} API keys')
    for k in keys:
        print(f'  - {k[\"provider\"]}/{k[\"key_name\"]}')
    await pool.close()

asyncio.run(check())
"
```

---

## Testing

### Manual Testing

```bash
# Set session token
export SESSION_TOKEN="your-keycloak-session-token"

# Test health check (no auth required)
curl http://localhost:8084/api/v1/llm-config/health

# List servers (requires auth)
curl http://localhost:8084/api/v1/llm-config/servers \
  -H "Cookie: session_token=$SESSION_TOKEN"

# List API keys
curl http://localhost:8084/api/v1/llm-config/api-keys \
  -H "Cookie: session_token=$SESSION_TOKEN"

# Get active providers
curl http://localhost:8084/api/v1/llm-config/active \
  -H "Cookie: session_token=$SESSION_TOKEN"
```

### Automated Testing

Create test suite at `backend/tests/test_llm_config_api.py`:

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_list_servers(client: AsyncClient, admin_session):
    response = await client.get(
        "/api/v1/llm-config/servers",
        cookies={"session_token": admin_session}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_server(client: AsyncClient, admin_session):
    response = await client.post(
        "/api/v1/llm-config/servers",
        json={
            "name": "Test Server",
            "server_type": "vllm",
            "base_url": "http://localhost:8000",
            "enabled": True
        },
        cookies={"session_token": admin_session}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Server"
    assert "id" in data
```

---

## Support

**Documentation**: `/services/ops-center/backend/docs/LLM_CONFIG_API.md`
**Code**:
- Manager: `/services/ops-center/backend/llm_config_manager.py`
- API: `/services/ops-center/backend/llm_config_api.py`
- Schema: `/services/ops-center/backend/sql/llm_config_schema.sql`

**Contact**: Backend Developer Agent

---

**Status**: ✅ COMPLETE - Ready for frontend integration
