# LLM Provider Integration - Quick Start

**For Developers**: How to use the LLM Provider Integration in 5 minutes

---

## TL;DR

```python
# 1. Get the integration layer (from FastAPI app state)
integration = request.app.state.provider_integration

# 2. Get active provider for "chat"
config = await integration.get_active_llm_provider("chat")

# 3. Convert to LiteLLM config
litellm_config = config.to_litellm_config()

# 4. Make inference request
import litellm
response = litellm.completion(
    model=litellm_config['model'],
    messages=[{"role": "user", "content": "Hello"}],
    api_base=litellm_config['api_base'],
    api_key=litellm_config['api_key']
)
```

---

## What Is This?

The **LLM Provider Integration** connects:
- **LLM Configuration Manager** (manages AI servers and API keys in database)
- **Your inference code** (makes actual LLM requests)

It automatically:
- Fetches the active LLM provider from database
- Decrypts API keys if needed
- Converts config to LiteLLM format
- Handles fallback providers
- Tests provider health

---

## Quick Setup (3 steps)

### Step 1: Generate Encryption Key (one-time)

```bash
cd /opt/ops-center
python3 backend/scripts/generate_encryption_key.py
```

This creates `BYOK_ENCRYPTION_KEY` in `.env.auth`.

### Step 2: Restart Ops-Center

```bash
docker restart ops-center-direct
```

### Step 3: Verify Integration

```bash
docker exec ops-center-direct python3 /app/scripts/test_provider_integration.py
```

Should see:
```
✅ All core tests passed!
```

**Done!** The integration is ready to use.

---

## Usage in Your Code

### In server.py (FastAPI startup)

```python
from llm_config_manager import LLMConfigManager
from llm_provider_integration import LLMProviderIntegration

@app.on_event("startup")
async def startup():
    # Initialize database pool
    db_pool = await asyncpg.create_pool(
        host=os.getenv('POSTGRES_HOST'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
        database=os.getenv('POSTGRES_DB')
    )

    # Initialize LLM Config Manager
    encryption_key = os.getenv('BYOK_ENCRYPTION_KEY')
    llm_manager = LLMConfigManager(db_pool, encryption_key)

    # Pre-populate defaults (OpenRouter key)
    await llm_manager.initialize_defaults()

    # Create integration layer
    provider_integration = LLMProviderIntegration(llm_manager)

    # Store in app state
    app.state.llm_manager = llm_manager
    app.state.provider_integration = provider_integration
```

### In Your Inference Endpoint

```python
@app.post("/api/v1/llm/chat/completions")
async def chat_completion(request: ChatRequest, req: Request):
    # Get integration
    integration = req.app.state.provider_integration

    # Get active provider
    config = await integration.get_active_llm_provider("chat")

    if not config:
        raise HTTPException(503, "No LLM provider configured")

    # Convert to LiteLLM config
    litellm_config = config.to_litellm_config()

    # Make request
    import litellm
    response = litellm.completion(
        model=request.model or litellm_config['model'],
        messages=request.messages,
        api_base=litellm_config['api_base'],
        api_key=litellm_config['api_key']
    )

    return response
```

---

## Pre-configured Setup

The integration comes with **OpenRouter** pre-configured:

- **API Key ID**: 1
- **Provider**: openrouter
- **Status**: Active for "chat" purpose
- **API Key**: `sk-or-v1-your-openrouter-key`

This means **inference works out-of-the-box** with no additional setup!

---

## Common Patterns

### Pattern 1: Simple Inference

```python
async def simple_inference(integration, prompt: str):
    config = await integration.get_active_llm_provider("chat")
    litellm_config = config.to_litellm_config()

    import litellm
    return litellm.completion(
        model="gpt-3.5-turbo",  # or any model
        messages=[{"role": "user", "content": prompt}],
        **litellm_config
    )
```

### Pattern 2: With Fallback

```python
async def inference_with_fallback(integration, prompt: str):
    # Try primary
    config = await integration.get_active_llm_provider("chat")

    success, msg = await integration.test_provider(config)

    if not success:
        # Try fallback
        config = await integration.get_fallback_provider(config)

        if not config:
            raise Exception("No working provider available")

    # Make request
    litellm_config = config.to_litellm_config()
    # ... inference code
```

### Pattern 3: Check Provider Type

```python
async def check_provider(integration):
    config = await integration.get_active_llm_provider("chat")

    if config.provider_type == "api_key":
        print(f"Using API key: {config.provider_name}")
        print(f"Cost: Metered (user pays)")

    elif config.provider_type == "ai_server":
        print(f"Using local server: {config.server_type}")
        print(f"Cost: Free (local inference)")
```

---

## API Endpoints

### Get Active Provider

```bash
GET /api/v1/llm-config/active/chat
```

Response:
```json
{
  "purpose": "chat",
  "provider_type": "api_key",
  "provider_id": 1,
  "provider": {
    "provider": "openrouter",
    "key_name": "Default OpenRouter Key",
    "masked_key": "****5d80",
    "enabled": true
  }
}
```

### Set Active Provider

```bash
POST /api/v1/llm-config/active
Content-Type: application/json

{
  "purpose": "chat",
  "provider_type": "api_key",
  "provider_id": 1
}
```

### List API Keys

```bash
GET /api/v1/llm-config/api-keys
```

Response:
```json
[
  {
    "id": 1,
    "provider": "openrouter",
    "key_name": "Default OpenRouter Key",
    "masked_key": "****5d80",
    "enabled": true,
    "use_for_ops_center": true
  }
]
```

---

## Testing

### Test Active Provider

```bash
# Inside Docker container
docker exec ops-center-direct python3 /app/scripts/test_provider_integration.py
```

### Test API Endpoint

```bash
curl http://localhost:8084/api/v1/llm-config/active/chat | jq
```

### Test Inference (with litellm installed)

```bash
docker exec ops-center-direct python3 /app/scripts/test_provider_integration.py --test-inference
```

---

## Troubleshooting

### "No active provider configured"

**Fix**: Set active provider
```bash
curl -X POST http://localhost:8084/api/v1/llm-config/active \
  -H "Content-Type: application/json" \
  -d '{"purpose": "chat", "provider_type": "api_key", "provider_id": 1}'
```

### "BYOK_ENCRYPTION_KEY not set"

**Fix**: Generate encryption key
```bash
python3 backend/scripts/generate_encryption_key.py
docker restart ops-center-direct
```

### "Provider health check failed"

**Fix**: Test the API key manually
- Go to provider's website (OpenRouter, OpenAI, etc.)
- Verify API key is valid
- Check rate limits

---

## Security Notes

### ✅ Safe to Do

- Call `get_active_llm_provider()` from backend code
- Use decrypted keys for LiteLLM inference
- Log **masked** keys: `key[-4:]`

### ❌ Never Do

- Return decrypted keys in API responses
- Send keys to frontend
- Log full plaintext keys
- Change `BYOK_ENCRYPTION_KEY` after users add keys

---

## Files Reference

| File | Purpose |
|------|---------|
| `backend/llm_provider_integration.py` | Main integration module |
| `backend/llm_config_manager.py` | Database layer (manages tables) |
| `backend/llm_config_api.py` | FastAPI endpoints for management UI |
| `backend/scripts/generate_encryption_key.py` | Generate encryption key |
| `backend/scripts/test_provider_integration.py` | Test suite |
| `.env.auth` | Contains `BYOK_ENCRYPTION_KEY` |

---

## Next Steps

1. ✅ Integration is ready to use (OpenRouter pre-configured)
2. 🔧 Update your inference endpoints to use `integration.get_active_llm_provider()`
3. 🎨 Build frontend UI for LLM configuration (optional)
4. 📊 Add usage tracking and billing (optional)

---

**Questions?** See full documentation in `LLM_PROVIDER_INTEGRATION.md`
