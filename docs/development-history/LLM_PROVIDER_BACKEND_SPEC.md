# LLM Provider Management - Backend API Specification

**For**: Backend Developer
**Created**: October 20, 2025
**Priority**: High - Needed for LiteLLM integration testing

---

## Quick Summary

The frontend for LLM provider management is **100% complete**. You need to build the backend API to power it.

**What it does**: Allows admins to manage AI inference servers (vLLM, Ollama) and third-party API keys (OpenRouter, OpenAI, etc.) for use in Ops-Center.

**Frontend Files**:
- `src/pages/LLMProviderSettings.jsx` - Main page
- `src/components/llm/*.jsx` - 4 sub-components
- Already integrated into routing and navigation

**Access**: https://unicorncommander.ai/admin/system/llm-providers

---

## Database Schema

Create these tables in PostgreSQL (database: `unicorn_db`):

```sql
-- AI Servers (vLLM, Ollama, llama.cpp, etc.)
CREATE TABLE llm_servers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL CHECK (type IN ('vllm', 'ollama', 'llama.cpp', 'openai-compatible')),
  base_url VARCHAR(500) NOT NULL,
  api_key VARCHAR(500),
  model_path VARCHAR(500),
  enabled BOOLEAN DEFAULT true,
  use_for_chat BOOLEAN DEFAULT true,
  use_for_embeddings BOOLEAN DEFAULT false,
  use_for_reranking BOOLEAN DEFAULT false,
  status VARCHAR(50) DEFAULT 'unknown' CHECK (status IN ('healthy', 'degraded', 'error', 'unknown')),
  available_models JSONB,
  last_health_check TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Third-party API Keys (OpenRouter, OpenAI, Anthropic, etc.)
CREATE TABLE llm_api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  provider VARCHAR(50) NOT NULL CHECK (provider IN ('openrouter', 'openai', 'anthropic', 'google', 'cohere', 'huggingface', 'together', 'groq')),
  api_key VARCHAR(500) NOT NULL,
  key_name VARCHAR(255) NOT NULL,
  enabled BOOLEAN DEFAULT true,
  status VARCHAR(50) DEFAULT 'unknown' CHECK (status IN ('active', 'error', 'inactive')),
  usage_requests INTEGER DEFAULT 0,
  usage_tokens BIGINT DEFAULT 0,
  usage_cost DECIMAL(10,2) DEFAULT 0.00,
  last_used TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_llm_servers_enabled ON llm_servers(enabled);
CREATE INDEX idx_llm_servers_status ON llm_servers(status);
CREATE INDEX idx_llm_api_keys_provider ON llm_api_keys(provider);
CREATE INDEX idx_llm_api_keys_enabled ON llm_api_keys(enabled);
```

---

## API Endpoints to Implement

Create new file: `backend/llm_config_api.py`

### AI Servers Endpoints

#### 1. List All Servers
```python
GET /api/v1/llm-config/servers

Response 200:
{
  "servers": [
    {
      "id": "uuid",
      "name": "Production vLLM",
      "type": "vllm",
      "base_url": "http://unicorn-vllm:8000",
      "api_key": "optional",
      "model_path": "Qwen/Qwen2.5-32B-Instruct-AWQ",
      "enabled": true,
      "use_for_chat": true,
      "use_for_embeddings": false,
      "use_for_reranking": false,
      "status": "healthy",
      "available_models": ["model1", "model2"],
      "last_health_check": "2025-10-20T12:00:00Z"
    }
  ]
}
```

#### 2. Create Server
```python
POST /api/v1/llm-config/servers

Request Body:
{
  "name": "Production vLLM",
  "type": "vllm",
  "base_url": "http://unicorn-vllm:8000",
  "api_key": "optional",
  "model_path": "Qwen/Qwen2.5-32B-Instruct-AWQ",
  "enabled": true,
  "use_for_chat": true,
  "use_for_embeddings": false,
  "use_for_reranking": false
}

Response 201:
{
  "id": "uuid",
  "name": "Production vLLM",
  "type": "vllm",
  "base_url": "http://unicorn-vllm:8000",
  "model_path": "Qwen/Qwen2.5-32B-Instruct-AWQ",
  "enabled": true,
  "use_for_chat": true,
  "use_for_embeddings": false,
  "use_for_reranking": false,
  "status": "unknown",
  "available_models": [],
  "last_health_check": null
}
```

#### 3. Update Server
```python
PUT /api/v1/llm-config/servers/{server_id}

Request Body: Same as POST

Response 200: Updated server object
```

#### 4. Delete Server
```python
DELETE /api/v1/llm-config/servers/{server_id}

Response 204: No content
```

#### 5. Test Server Connection
```python
POST /api/v1/llm-config/servers/{server_id}/test

Response 200 (success):
{
  "success": true,
  "message": "Connection successful! Found 1 model(s).",
  "models": ["Qwen/Qwen2.5-32B-Instruct-AWQ"]
}

Response 200 (failure):
{
  "success": false,
  "error": "Connection refused. Is the server running?"
}
```

#### 6. Test Connection (Before Saving)
```python
POST /api/v1/llm-config/servers/test-connection

Request Body:
{
  "base_url": "http://unicorn-vllm:8000",
  "api_key": "optional",
  "type": "vllm"
}

Response: Same as test endpoint above
```

### API Keys Endpoints

#### 1. List All Keys
```python
GET /api/v1/llm-config/api-keys

Response 200:
{
  "api_keys": [
    {
      "id": "uuid",
      "provider": "openrouter",
      "api_key": "sk-or-v1-...",
      "key_name": "Default OpenRouter Key",
      "enabled": true,
      "status": "active",
      "usage": {
        "requests": 1000,
        "tokens": 50000,
        "cost": 10.50
      },
      "last_used": "2025-10-20T11:30:00Z",
      "created_at": "2025-10-01T00:00:00Z"
    }
  ]
}
```

#### 2. Create API Key
```python
POST /api/v1/llm-config/api-keys

Request Body:
{
  "provider": "openrouter",
  "api_key": "sk-or-v1-...",
  "key_name": "Default OpenRouter Key",
  "enabled": true
}

Response 201: Created key object
```

#### 3. Update API Key
```python
PUT /api/v1/llm-config/api-keys/{key_id}

Request Body: Same as POST

Response 200: Updated key object
```

#### 4. Delete API Key
```python
DELETE /api/v1/llm-config/api-keys/{key_id}

Response 204: No content
```

#### 5. Test API Key
```python
POST /api/v1/llm-config/api-keys/{key_id}/test

Response 200 (success):
{
  "success": true,
  "message": "API key is valid!",
  "details": {
    "account": "user@example.com",
    "credits": 100.00
  }
}

Response 200 (failure):
{
  "success": false,
  "error": "Invalid API key or insufficient permissions"
}
```

#### 6. Test Key (Before Saving)
```python
POST /api/v1/llm-config/api-keys/test-key

Request Body:
{
  "provider": "openrouter",
  "api_key": "sk-or-v1-..."
}

Response: Same as test endpoint above
```

---

## Implementation Template

Create `backend/llm_config_api.py`:

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import asyncpg
import httpx
from keycloak_integration import get_current_user, require_admin

router = APIRouter()

# ============================================================================
# Pydantic Models
# ============================================================================

class AIServerCreate(BaseModel):
    name: str
    type: str  # vllm | ollama | llama.cpp | openai-compatible
    base_url: str
    api_key: Optional[str] = None
    model_path: Optional[str] = None
    enabled: bool = True
    use_for_chat: bool = True
    use_for_embeddings: bool = False
    use_for_reranking: bool = False

    @validator('type')
    def validate_type(cls, v):
        allowed = ['vllm', 'ollama', 'llama.cpp', 'openai-compatible']
        if v not in allowed:
            raise ValueError(f'Type must be one of: {allowed}')
        return v

class AIServerResponse(BaseModel):
    id: str
    name: str
    type: str
    base_url: str
    api_key: Optional[str]
    model_path: Optional[str]
    enabled: bool
    use_for_chat: bool
    use_for_embeddings: bool
    use_for_reranking: bool
    status: str
    available_models: List[str]
    last_health_check: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class APIKeyCreate(BaseModel):
    provider: str
    api_key: str
    key_name: str
    enabled: bool = True

    @validator('provider')
    def validate_provider(cls, v):
        allowed = ['openrouter', 'openai', 'anthropic', 'google', 'cohere', 'huggingface', 'together', 'groq']
        if v not in allowed:
            raise ValueError(f'Provider must be one of: {allowed}')
        return v

class APIKeyResponse(BaseModel):
    id: str
    provider: str
    api_key: str
    key_name: str
    enabled: bool
    status: str
    usage: dict
    last_used: Optional[datetime]
    created_at: datetime

# ============================================================================
# Database Helper
# ============================================================================

async def get_db_connection():
    return await asyncpg.connect(
        host="unicorn-postgresql",
        port=5432,
        user="unicorn",
        password="unicorn",
        database="unicorn_db"
    )

# ============================================================================
# AI Servers Endpoints
# ============================================================================

@router.get("/servers")
async def list_servers(current_user: dict = Depends(require_admin)):
    """List all AI servers"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT * FROM llm_servers ORDER BY created_at DESC
        """)

        servers = []
        for row in rows:
            servers.append({
                "id": str(row['id']),
                "name": row['name'],
                "type": row['type'],
                "base_url": row['base_url'],
                "api_key": row['api_key'],
                "model_path": row['model_path'],
                "enabled": row['enabled'],
                "use_for_chat": row['use_for_chat'],
                "use_for_embeddings": row['use_for_embeddings'],
                "use_for_reranking": row['use_for_reranking'],
                "status": row['status'],
                "available_models": row['available_models'] or [],
                "last_health_check": row['last_health_check']
            })

        return {"servers": servers}
    finally:
        await conn.close()

@router.post("/servers", status_code=201)
async def create_server(
    server: AIServerCreate,
    current_user: dict = Depends(require_admin)
):
    """Create new AI server"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO llm_servers
            (name, type, base_url, api_key, model_path, enabled,
             use_for_chat, use_for_embeddings, use_for_reranking)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *
        """, server.name, server.type, server.base_url, server.api_key,
            server.model_path, server.enabled, server.use_for_chat,
            server.use_for_embeddings, server.use_for_reranking)

        return {
            "id": str(row['id']),
            "name": row['name'],
            "type": row['type'],
            "base_url": row['base_url'],
            "api_key": row['api_key'],
            "model_path": row['model_path'],
            "enabled": row['enabled'],
            "use_for_chat": row['use_for_chat'],
            "use_for_embeddings": row['use_for_embeddings'],
            "use_for_reranking": row['use_for_reranking'],
            "status": row['status'],
            "available_models": [],
            "last_health_check": None
        }
    finally:
        await conn.close()

@router.put("/servers/{server_id}")
async def update_server(
    server_id: str,
    server: AIServerCreate,
    current_user: dict = Depends(require_admin)
):
    """Update AI server"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            UPDATE llm_servers SET
                name = $1, type = $2, base_url = $3, api_key = $4,
                model_path = $5, enabled = $6, use_for_chat = $7,
                use_for_embeddings = $8, use_for_reranking = $9,
                updated_at = NOW()
            WHERE id = $10
            RETURNING *
        """, server.name, server.type, server.base_url, server.api_key,
            server.model_path, server.enabled, server.use_for_chat,
            server.use_for_embeddings, server.use_for_reranking, server_id)

        if not row:
            raise HTTPException(status_code=404, detail="Server not found")

        return {
            "id": str(row['id']),
            "name": row['name'],
            "type": row['type'],
            "base_url": row['base_url'],
            "api_key": row['api_key'],
            "model_path": row['model_path'],
            "enabled": row['enabled'],
            "use_for_chat": row['use_for_chat'],
            "use_for_embeddings": row['use_for_embeddings'],
            "use_for_reranking": row['use_for_reranking'],
            "status": row['status'],
            "available_models": row['available_models'] or [],
            "last_health_check": row['last_health_check']
        }
    finally:
        await conn.close()

@router.delete("/servers/{server_id}", status_code=204)
async def delete_server(
    server_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete AI server"""
    conn = await get_db_connection()
    try:
        result = await conn.execute("""
            DELETE FROM llm_servers WHERE id = $1
        """, server_id)

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Server not found")
    finally:
        await conn.close()

@router.post("/servers/{server_id}/test")
async def test_server(
    server_id: str,
    current_user: dict = Depends(require_admin)
):
    """Test server connection"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            SELECT * FROM llm_servers WHERE id = $1
        """, server_id)

        if not row:
            raise HTTPException(status_code=404, detail="Server not found")

        # Test connection logic here
        return await _test_server_connection(
            row['base_url'],
            row['api_key'],
            row['type']
        )
    finally:
        await conn.close()

@router.post("/servers/test-connection")
async def test_connection(
    data: dict,
    current_user: dict = Depends(require_admin)
):
    """Test connection before saving"""
    return await _test_server_connection(
        data['base_url'],
        data.get('api_key'),
        data['type']
    )

async def _test_server_connection(base_url: str, api_key: Optional[str], server_type: str):
    """Helper to test server connection"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {}
            if api_key:
                headers['Authorization'] = f'Bearer {api_key}'

            # Try to fetch models list
            if server_type == 'vllm':
                response = await client.get(f'{base_url}/v1/models', headers=headers)
            elif server_type == 'ollama':
                response = await client.get(f'{base_url}/api/tags', headers=headers)
            else:
                response = await client.get(f'{base_url}/v1/models', headers=headers)

            if response.status_code == 200:
                data = response.json()
                models = []

                if server_type == 'vllm':
                    models = [m['id'] for m in data.get('data', [])]
                elif server_type == 'ollama':
                    models = [m['name'] for m in data.get('models', [])]
                else:
                    models = [m['id'] for m in data.get('data', [])]

                return {
                    "success": True,
                    "message": f"Connection successful! Found {len(models)} model(s).",
                    "models": models
                }
            else:
                return {
                    "success": False,
                    "error": f"Server returned status code {response.status_code}"
                }

    except httpx.ConnectError:
        return {
            "success": False,
            "error": "Connection refused. Is the server running?"
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "Connection timeout. Server not responding."
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ============================================================================
# API Keys Endpoints
# ============================================================================

@router.get("/api-keys")
async def list_api_keys(current_user: dict = Depends(require_admin)):
    """List all API keys"""
    conn = await get_db_connection()
    try:
        rows = await conn.fetch("""
            SELECT * FROM llm_api_keys ORDER BY created_at DESC
        """)

        keys = []
        for row in rows:
            keys.append({
                "id": str(row['id']),
                "provider": row['provider'],
                "api_key": row['api_key'],
                "key_name": row['key_name'],
                "enabled": row['enabled'],
                "status": row['status'],
                "usage": {
                    "requests": row['usage_requests'],
                    "tokens": row['usage_tokens'],
                    "cost": float(row['usage_cost'])
                },
                "last_used": row['last_used'],
                "created_at": row['created_at']
            })

        return {"api_keys": keys}
    finally:
        await conn.close()

@router.post("/api-keys", status_code=201)
async def create_api_key(
    key: APIKeyCreate,
    current_user: dict = Depends(require_admin)
):
    """Create new API key"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            INSERT INTO llm_api_keys (provider, api_key, key_name, enabled)
            VALUES ($1, $2, $3, $4)
            RETURNING *
        """, key.provider, key.api_key, key.key_name, key.enabled)

        return {
            "id": str(row['id']),
            "provider": row['provider'],
            "api_key": row['api_key'],
            "key_name": row['key_name'],
            "enabled": row['enabled'],
            "status": row['status'],
            "usage": {
                "requests": 0,
                "tokens": 0,
                "cost": 0.00
            },
            "last_used": None,
            "created_at": row['created_at']
        }
    finally:
        await conn.close()

@router.put("/api-keys/{key_id}")
async def update_api_key(
    key_id: str,
    key: APIKeyCreate,
    current_user: dict = Depends(require_admin)
):
    """Update API key"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            UPDATE llm_api_keys SET
                provider = $1, api_key = $2, key_name = $3,
                enabled = $4, updated_at = NOW()
            WHERE id = $5
            RETURNING *
        """, key.provider, key.api_key, key.key_name, key.enabled, key_id)

        if not row:
            raise HTTPException(status_code=404, detail="API key not found")

        return {
            "id": str(row['id']),
            "provider": row['provider'],
            "api_key": row['api_key'],
            "key_name": row['key_name'],
            "enabled": row['enabled'],
            "status": row['status'],
            "usage": {
                "requests": row['usage_requests'],
                "tokens": row['usage_tokens'],
                "cost": float(row['usage_cost'])
            },
            "last_used": row['last_used'],
            "created_at": row['created_at']
        }
    finally:
        await conn.close()

@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete API key"""
    conn = await get_db_connection()
    try:
        result = await conn.execute("""
            DELETE FROM llm_api_keys WHERE id = $1
        """, key_id)

        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="API key not found")
    finally:
        await conn.close()

@router.post("/api-keys/{key_id}/test")
async def test_api_key(
    key_id: str,
    current_user: dict = Depends(require_admin)
):
    """Test API key validation"""
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow("""
            SELECT * FROM llm_api_keys WHERE id = $1
        """, key_id)

        if not row:
            raise HTTPException(status_code=404, detail="API key not found")

        return await _test_api_key_validation(row['provider'], row['api_key'])
    finally:
        await conn.close()

@router.post("/api-keys/test-key")
async def test_key(
    data: dict,
    current_user: dict = Depends(require_admin)
):
    """Test key before saving"""
    return await _test_api_key_validation(data['provider'], data['api_key'])

async def _test_api_key_validation(provider: str, api_key: str):
    """Helper to test API key validation"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Provider-specific validation endpoints
            if provider == 'openrouter':
                response = await client.get(
                    'https://openrouter.ai/api/v1/auth/key',
                    headers={'Authorization': f'Bearer {api_key}'}
                )
            elif provider == 'openai':
                response = await client.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {api_key}'}
                )
            elif provider == 'anthropic':
                response = await client.get(
                    'https://api.anthropic.com/v1/models',
                    headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01'}
                )
            # Add more providers as needed
            else:
                return {
                    "success": False,
                    "error": f"Validation not implemented for provider: {provider}"
                }

            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "API key is valid!",
                    "details": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"Invalid API key (status {response.status_code})"
                }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

---

## Integration Steps

1. **Create the file**:
   ```bash
   touch /opt/ops-center/backend/llm_config_api.py
   # Copy the template above into it
   ```

2. **Create the database tables**:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /path/to/schema.sql
   ```

3. **Register the router** in `backend/server.py`:
   ```python
   from llm_config_api import router as llm_config_router

   app.include_router(
       llm_config_router,
       prefix="/api/v1/llm-config",
       tags=["LLM Configuration"]
   )
   ```

4. **Restart the backend**:
   ```bash
   docker restart ops-center-direct
   ```

5. **Test the endpoints**:
   ```bash
   # List servers (should return empty array)
   curl http://localhost:8084/api/v1/llm-config/servers

   # List keys (should return empty array)
   curl http://localhost:8084/api/v1/llm-config/api-keys
   ```

6. **Test the UI**:
   - Navigate to: https://unicorncommander.ai/admin/system/llm-providers
   - Try adding a server
   - Try adding an API key
   - Test the OpenRouter pre-populate button

---

## Testing Checklist

- [ ] Database tables created
- [ ] API endpoints registered
- [ ] Backend restarted
- [ ] List servers endpoint works
- [ ] Create server endpoint works
- [ ] Update server endpoint works
- [ ] Delete server endpoint works
- [ ] Test connection endpoint works
- [ ] List keys endpoint works
- [ ] Create key endpoint works
- [ ] Update key endpoint works
- [ ] Delete key endpoint works
- [ ] Test key validation works
- [ ] UI loads without errors
- [ ] Can add/edit/delete servers
- [ ] Can add/edit/delete keys
- [ ] Toast notifications appear
- [ ] Metrics update correctly

---

## Notes

1. **Authentication**: All endpoints require admin role (use `require_admin` dependency)

2. **Error Handling**: Return proper HTTP status codes:
   - 200: Success
   - 201: Created
   - 204: Deleted (no content)
   - 400: Bad request (validation error)
   - 401: Unauthorized
   - 403: Forbidden (not admin)
   - 404: Not found
   - 500: Internal server error

3. **Validation**: Use Pydantic models for request validation

4. **Security**:
   - Don't log API keys
   - Consider encrypting API keys at rest
   - Rate limit test endpoints

5. **Performance**:
   - Add Redis caching for server/key lists
   - Use connection pooling for PostgreSQL
   - Consider background jobs for health checks

---

## Questions?

If anything is unclear, check:
- Frontend implementation: `LLM_PROVIDER_UI_COMPLETE.md`
- Component files: `src/components/llm/*.jsx`
- Main page: `src/pages/LLMProviderSettings.jsx`

The frontend is fully functional and just needs the backend API to work!
