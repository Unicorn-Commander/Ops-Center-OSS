# BYOK API Quick Reference

**Base URL**: `/api/v1/llm/byok`

---

## Endpoints

### List Providers (Public)
```bash
GET /api/v1/llm/byok/providers
```
No auth required. Returns supported providers with signup info.

---

### List User's Keys
```bash
GET /api/v1/llm/byok/keys
Authorization: Bearer {token}
```
Returns masked keys for authenticated user.

---

### Add/Update Key
```bash
POST /api/v1/llm/byok/keys
Authorization: Bearer {token}
Content-Type: application/json

{
  "provider": "openrouter",
  "api_key": "sk-or-v1-...",
  "metadata": {}
}
```
Validates format, tests key (optional), stores encrypted.

---

### Delete Key
```bash
DELETE /api/v1/llm/byok/keys/{provider}
Authorization: Bearer {token}
```
Permanently removes API key.

---

### Toggle Enable/Disable
```bash
POST /api/v1/llm/byok/keys/{provider}/toggle
Authorization: Bearer {token}
Content-Type: application/json

{
  "enabled": false
}
```
Enables or disables key without deleting.

---

### Test Key
```bash
POST /api/v1/llm/byok/keys/{provider}/test
Authorization: Bearer {token}
```
Tests stored key against provider API.
**Rate limit**: 5 tests/minute.

---

### Get Usage Stats (Placeholder)
```bash
GET /api/v1/llm/byok/keys/{provider}/usage
Authorization: Bearer {token}
```
Returns usage statistics (Phase 2).

---

## Supported Providers

| Provider | Key Format | Prefix |
|----------|------------|--------|
| **OpenRouter** | 64 chars | `sk-or-v1-` |
| **OpenAI** | 48+ chars | `sk-` |
| **Anthropic** | 95+ chars | `sk-ant-` |
| **Google** | 39 chars | alphanumeric |

---

## Quick Start (Frontend)

```javascript
// List providers
const providers = await fetch('/api/v1/llm/byok/providers').then(r => r.json());

// Add key
const result = await fetch('/api/v1/llm/byok/keys', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    provider: 'openrouter',
    api_key: 'sk-or-v1-...',
    metadata: {}
  })
}).then(r => r.json());

// Test key
const testResult = await fetch('/api/v1/llm/byok/keys/openrouter/test', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
}).then(r => r.json());
```

---

**Status**: ✅ Production Ready | **Version**: 1.0 | **Date**: October 26, 2025
