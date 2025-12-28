# Provider Keys API - Quick Reference

**Created**: October 27, 2025
**Module**: `backend/provider_keys_api.py`
**Endpoints**: `/api/v1/llm/providers/*`

---

## Quick Start

### 1. Integration

Add to `backend/server.py`:

```python
# Import (after line 121)
from provider_keys_api import router as provider_keys_router

# Register (after line 700)
app.include_router(provider_keys_router)
logger.info("Provider Keys API endpoints registered at /api/v1/llm/providers")
```

Restart backend:
```bash
docker restart ops-center-direct
```

### 2. Test

Get admin session token:
```bash
# Login at: https://your-domain.com/auth/login
# Browser console: document.cookie
```

Run tests:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
./test_provider_keys_api.sh "YOUR_SESSION_TOKEN"
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/llm/providers/keys` | List all provider keys (masked) |
| POST | `/api/v1/llm/providers/keys` | Add/update provider key |
| POST | `/api/v1/llm/providers/keys/test` | Test provider key |
| DELETE | `/api/v1/llm/providers/keys/{id}` | Delete provider key |
| GET | `/api/v1/llm/providers/info` | Get provider information |

---

## Supported Providers

✅ **OpenRouter** - Universal LLM proxy (200+ models)
✅ **OpenAI** - GPT-4o, GPT-4-turbo, o1-preview
✅ **Anthropic** - Claude 3.5 Sonnet, Claude 3 Opus
✅ **Google AI** - Gemini 2.0 Flash, Gemini 1.5 Pro
✅ **Cohere** - Command R+, Embed models
✅ **Groq** - Ultra-fast inference (Llama 3, Mixtral)
✅ **Together AI** - Open-source models
✅ **Mistral AI** - Mistral Large, Medium, Small
✅ **Custom** - Any OpenAI-compatible endpoint

---

## Example Usage

### List Provider Keys

```bash
curl http://localhost:8084/api/v1/llm/providers/keys \
  -H 'Cookie: session_token=YOUR_TOKEN'
```

### Save OpenRouter Key

```bash
curl -X POST http://localhost:8084/api/v1/llm/providers/keys \
  -H 'Cookie: session_token=YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider_type": "openrouter",
    "api_key": "sk-or-v1-YOUR-KEY",
    "name": "OpenRouter"
  }'
```

### Test Stored Key

```bash
curl -X POST http://localhost:8084/api/v1/llm/providers/keys/test \
  -H 'Cookie: session_token=YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  -d '{
    "provider_type": "openrouter",
    "api_key": null
  }'
```

---

## Frontend Integration

```javascript
// List providers
const response = await fetch('/api/v1/llm/providers/keys', {
  credentials: 'include'
});
const { providers } = await response.json();

// Save key
await fetch('/api/v1/llm/providers/keys', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider_type: 'openrouter',
    api_key: 'sk-or-v1-...',
    name: 'OpenRouter'
  })
});

// Test key
const testResult = await fetch('/api/v1/llm/providers/keys/test', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    provider_type: 'openrouter',
    api_key: null  // Test stored key
  })
});
```

---

## Security

- ✅ **Admin-only**: Requires `role: admin` from session
- ✅ **Encrypted**: Fernet encryption for all API keys
- ✅ **Rate limited**: 10 tests per minute per user
- ✅ **Masked**: Keys shown as `sk-or-v...1234` in responses
- ✅ **Logged**: All operations logged for audit

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | Invalid provider type or key format |
| 401 | Not authenticated (no session) |
| 403 | Forbidden (not admin) |
| 404 | Provider not found |
| 429 | Rate limit exceeded (10/min) |
| 500 | Server error (DB/encryption) |

---

## Files

- **API**: `backend/provider_keys_api.py` (569 lines)
- **Integration Guide**: `backend/PROVIDER_KEYS_API_INTEGRATION.md`
- **Test Script**: `backend/test_provider_keys_api.sh`
- **Database**: `migrations/create_llm_management_tables_v2.sql`

---

## Dependencies

**Already available** (no installation needed):
- ✅ `app.state.db_pool` - PostgreSQL connection
- ✅ `app.state.sessions` - Redis session manager
- ✅ `BYOK_ENCRYPTION_KEY` - Environment variable
- ✅ `httpx` - HTTP client
- ✅ `cryptography` - Fernet encryption
- ✅ `pydantic` - Request/response models

---

## Testing Checklist

- [ ] Import router in `server.py`
- [ ] Register router in `server.py`
- [ ] Restart backend container
- [ ] Verify endpoints in logs
- [ ] Run `test_provider_keys_api.sh`
- [ ] Test with real API key
- [ ] Verify encryption (check database)
- [ ] Test rate limiting (11 requests)
- [ ] Test unauthorized access (no session)

---

## Logs

View API activity:
```bash
docker logs ops-center-direct -f | grep provider_keys_api
```

Example logs:
```
INFO:provider_keys_api:Admin admin@example.com retrieved 9 provider keys
INFO:provider_keys_api:Admin admin@example.com added new provider key: OpenRouter
INFO:provider_keys_api:Admin admin@example.com tested openrouter API key: success
```

---

## Troubleshooting

**Q: "Database connection not available"**
A: Check `app.state.db_pool` is initialized in `server.py` startup event

**Q: "BYOK_ENCRYPTION_KEY environment variable required"**
A: Add to `.env.auth` and restart container

**Q: "Invalid session"**
A: Re-login at `/auth/login` to get fresh session

**Q: "Rate limit exceeded"**
A: Wait 60 seconds between test batches

---

## Performance

- **List providers**: ~50ms (DB query + masking)
- **Save key**: ~300ms (encrypt + DB + API test)
- **Test key**: ~200-500ms (API roundtrip)
- **Delete key**: ~30ms (DB update)

---

## Next Steps

1. **Frontend UI**: Create "Provider Keys" tab in LLM Hub
2. **Health monitoring**: Add periodic background key testing
3. **Usage tracking**: Track which providers are used most
4. **Notifications**: Alert admins when keys fail tests

---

**Documentation**: See `PROVIDER_KEYS_API_INTEGRATION.md` for full details
