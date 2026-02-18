# API Key Encryption - Quick Start Guide

## TL;DR

Encrypted API key storage is now implemented. Users can securely store their API keys (OpenAI, Anthropic, etc.) in Authentik user attributes.

---

## Quick Test

### 1. Restart Service
```bash
docker-compose restart unicorn-ops-center
```

### 2. Check Logs
```bash
docker logs unicorn-ops-center | grep "API Keys router"
# Expected: "✓ API Keys router registered at /api/v1/user/api-keys"
```

### 3. Test UI
1. Open: https://unicorncommander.ai/admin/settings
2. Click "API Keys (BYOK)" tab
3. Click "+ Add API Key"
4. Add a test key
5. Verify it appears (masked)

---

## Key Files

| File | Purpose |
|------|---------|
| `backend/key_encryption.py` | Fernet encryption/decryption |
| `backend/authentik_keys.py` | Authentik user attributes storage |
| `backend/api_keys_router.py` | REST API endpoints |
| `src/pages/UserSettings.jsx` | Frontend UI |

---

## API Endpoints

```bash
# Save key
POST /api/v1/user/api-keys

# List keys (masked)
GET /api/v1/user/api-keys

# Get decrypted key
GET /api/v1/user/api-keys/{provider}

# Update key
PUT /api/v1/user/api-keys/{provider}

# Delete key
DELETE /api/v1/user/api-keys/{provider}
```

---

## Environment Variables

Required in `.env`:
```bash
ENCRYPTION_KEY=pXfS-0VwQPilpOvRaQOivJIBFUOrgT9toMtjyr2NZqo=
AUTHENTIK_API_TOKEN=your-authentik-api-token
AUTHENTIK_URL=http://authentik-server:9000
```

---

## Security Features

- ✅ Fernet symmetric encryption (AES-128 + HMAC)
- ✅ Stored in Authentik user attributes
- ✅ Keys only decrypted on explicit request
- ✅ Masked display by default
- ✅ HTTPS transport in production
- ✅ Session-based authentication

---

## Supported Providers

- OpenAI (`sk-...`)
- Anthropic (`sk-ant-...`)
- Cohere (`cohere-...`)
- HuggingFace (`hf_...`)
- OpenRouter (`sk-or-...`)
- Together AI (`together-...`)
- Replicate (`r8_...`)
- Custom Endpoint (`http://...`)

---

## Troubleshooting

### Keys not saving?
1. Check Authentik API token is valid
2. Verify ENCRYPTION_KEY is set
3. Restart ops-center container
4. Check container logs

### Can't decrypt keys?
1. Verify ENCRYPTION_KEY hasn't changed
2. Check Authentik user attributes in admin panel
3. Test Authentik connectivity

### Frontend errors?
1. Clear browser cache (Ctrl+F5)
2. Check browser console for errors
3. Verify frontend build succeeded
4. Restart nginx/traefik if needed

---

## Full Documentation

See `/docs/API_KEY_ENCRYPTION.md` for complete documentation including:
- Architecture details
- API reference with examples
- Testing procedures
- Security considerations
- Migration guide

---

## Support

Container logs:
```bash
docker logs unicorn-ops-center
docker logs authentik-server
```

Test Authentik API:
```bash
docker exec unicorn-ops-center curl http://authentik-server:9000/api/v3/core/users/
```

Generate new encryption key:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
