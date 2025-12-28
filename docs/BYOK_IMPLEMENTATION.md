# BYOK (Bring Your Own Key) Implementation Guide

## Overview

The BYOK system allows users to configure their own LLM provider API keys and execution environments for code execution. When a user sends a chat message through Ops-Center, the system automatically:

1. Checks if the user has BYOK configured
2. Uses their API key if available
3. Falls back to system default (OpenRouter or configured provider) if not
4. Executes code on their configured server if specified

## Architecture

### Components

1. **BYOK API** (`byok_api.py`)
   - Manages user API keys stored in Keycloak user attributes
   - Endpoints for adding, listing, testing, and deleting API keys
   - Requires Starter tier or above

2. **Execution Servers API** (`execution_servers_api.py`)
   - Manages user-configured execution environments
   - Supports SSH, Docker, Kubernetes, and local execution
   - Database-backed storage with encryption

3. **BYOK Service** (`byok_service.py`)
   - Business logic for provider selection
   - Handles fallback to system defaults
   - Retrieves execution server configuration

4. **LiteLLM Integration** (`litellm_integration.py`)
   - BYOK-aware LiteLLM client wrapper
   - Routes requests to user's provider or system default
   - Supports streaming and non-streaming responses

5. **Anthropic Proxy** (`anthropic_proxy.py`)
   - Updated to use BYOK configuration
   - Routes requests through Brigade with LLM config

6. **Brigade Adapter** (`brigade_adapter.py`)
   - Updated to include BYOK and execution server config
   - Passes configuration to Brigade for orchestration

## Database Schema

### User Execution Servers

```sql
CREATE TABLE user_execution_servers (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    server_type VARCHAR(50) NOT NULL,  -- 'ssh', 'local', 'docker', 'kubernetes'
    connection_config JSONB NOT NULL,  -- Encrypted credentials
    workspace_path VARCHAR(500),
    is_default BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT true,
    last_tested_at TIMESTAMP,
    test_status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints

### BYOK Providers

All endpoints are at `/api/v1/byok`

- `GET /providers` - List supported providers
- `GET /keys` - List user's configured API keys (masked)
- `POST /keys/add` - Add or update API key (requires Starter tier)
- `DELETE /keys/{provider}` - Remove API key
- `POST /keys/test/{provider}` - Test API key
- `GET /stats` - Get BYOK statistics

### Execution Servers

All endpoints are at `/api/v1/execution-servers`

- `GET /` - List user's execution servers
- `POST /` - Create execution server (requires Starter tier)
- `PUT /{server_id}` - Update execution server
- `DELETE /{server_id}` - Delete execution server
- `POST /{server_id}/test` - Test server connection
- `GET /default` - Get default execution server

## Supported Providers

1. **OpenAI**
   - API Key format: `sk-...`
   - Models: GPT-4, GPT-3.5-turbo

2. **Anthropic**
   - API Key format: `sk-ant-...`
   - Models: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku

3. **HuggingFace**
   - API Key format: `hf_...`
   - Models: Llama 2, Mixtral

4. **Cohere**
   - Models: Command R+, Command R

5. **Together AI**
   - Models: Mixtral, Llama 2

6. **Perplexity AI**
   - API Key format: `pplx-...`
   - Models: pplx-70b-online

7. **Groq**
   - API Key format: `gsk_...`
   - Models: Mixtral, Llama 2

8. **OpenRouter** (System Default)
   - Models: Various (Claude, GPT-4, Llama 3)

9. **Ollama** (Local)
   - Models: User-configured local models

10. **Custom**
    - User-provided endpoint

## Request Flow

### Non-BYOK User (Free Tier)

```
User Request
  → Anthropic Proxy
  → BYOK Service (no BYOK found)
  → System Default Provider (OpenRouter)
  → Brigade
  → LiteLLM with system API key
  → Response
```

### BYOK User (Starter+ Tier)

```
User Request
  → Anthropic Proxy
  → BYOK Service (retrieves user's API key from Keycloak)
  → User's Provider (e.g., OpenAI)
  → Brigade
  → LiteLLM with user's API key
  → Response
```

### With Custom Execution Server

```
User Request
  → Anthropic Proxy
  → BYOK Service (retrieves API key + execution server)
  → Brigade with execution server config
  → Code execution on user's SSH server
  → LiteLLM with user's API key
  → Response
```

## Security

### API Key Encryption

All API keys are encrypted using Fernet (AES-256) before storage:

```python
from key_encryption import get_encryption

encryption = get_encryption()
encrypted_key = encryption.encrypt_key(api_key)
decrypted_key = encryption.decrypt_key(encrypted_key)
```

Environment variable required: `ENCRYPTION_KEY`

### Execution Server Credentials

Sensitive fields in execution server configs are encrypted:
- SSH passwords
- SSH private keys
- Kubernetes service account tokens
- Kubernetes kubeconfig

### Storage

- **BYOK API Keys**: Stored in Keycloak user attributes (encrypted)
- **Execution Servers**: Stored in PostgreSQL (encrypted)

## Configuration

### Environment Variables

```bash
# Encryption key for BYOK (generate with: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
ENCRYPTION_KEY=your-encryption-key-here

# System default provider
DEFAULT_LLM_PROVIDER=openrouter
DEFAULT_LLM_API_KEY=your-system-api-key
DEFAULT_LLM_BASE_URL=https://openrouter.ai/api/v1

# Database for execution servers
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ops_center

# Keycloak for BYOK storage
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
```

## Usage Examples

### Add OpenAI API Key

```bash
curl -X POST https://your-domain.com/api/v1/byok/keys/add \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "provider": "openai",
    "key": "sk-...",
    "label": "My OpenAI Key"
  }'
```

### Add SSH Execution Server

```bash
curl -X POST https://your-domain.com/api/v1/execution-servers \
  -H "Content-Type: application/json" \
  -H "Cookie: session=..." \
  -d '{
    "name": "My Dev Server",
    "server_type": "ssh",
    "connection_config": {
      "host": "dev.example.com",
      "port": 22,
      "username": "developer",
      "auth_method": "key",
      "private_key": "-----BEGIN RSA PRIVATE KEY-----\n..."
    },
    "workspace_path": "/home/developer/workspace",
    "is_default": true
  }'
```

### Test API Key

```bash
curl -X POST https://your-domain.com/api/v1/byok/keys/test/openai \
  -H "Cookie: session=..."
```

### Test Execution Server

```bash
curl -X POST https://your-domain.com/api/v1/execution-servers/{server_id}/test \
  -H "Cookie: session=..."
```

## Frontend Integration

The frontend UI should:

1. Show BYOK configuration page (Starter tier+)
2. Display supported providers with icons
3. Allow adding/testing/removing API keys
4. Show execution servers with test status
5. Allow configuring SSH/Docker/K8s connections
6. Display "Using your OpenAI key" vs "Using system default" in chat

## Migration

To apply the database migration:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
psql -U postgres -d ops_center -f migrations/007_user_execution_servers.sql
```

## Monitoring

The system logs:
- BYOK usage per user
- Provider selection decisions
- Execution server usage
- API key test results
- Fallback to system defaults

Example log:
```
User aaron@example.com request routing: provider=openai, model=gpt-4, byok=True
User has execution server configured: My Dev Server
```

## Troubleshooting

### API Key Not Working

1. Test the key via API: `POST /api/v1/byok/keys/test/{provider}`
2. Check encryption key is set: `echo $ENCRYPTION_KEY`
3. Verify tier access: User must be Starter or above

### Execution Server Connection Failed

1. Test SSH connection: `POST /api/v1/execution-servers/{id}/test`
2. Check firewall rules
3. Verify SSH credentials
4. Check workspace path exists

### Falling Back to System Default

Check logs for:
- "User has no BYOK configured"
- Decryption errors
- Invalid API keys

## Future Enhancements

1. Support for more providers (Replicate, Cloudflare Workers AI)
2. Usage tracking per provider
3. Cost estimation and limits
4. Key rotation and expiration
5. Multi-key load balancing
6. Provider health monitoring
7. Automatic fallback on provider errors
