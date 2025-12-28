# Model Admin API - Quick Reference

**Base URL**: `/api/v1/models/admin`
**Auth**: Admin/Moderator role required

---

## Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models` | List models with filters |
| POST | `/models` | Create new model |
| GET | `/models/{model_id}` | Get model details |
| PUT | `/models/{model_id}` | Update model |
| DELETE | `/models/{model_id}` | Delete model |
| PATCH | `/models/{model_id}/toggle` | Enable/disable model |
| GET | `/models/stats/summary` | Model statistics |

---

## Quick Examples

### List Models (with filters)
```bash
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models?provider=openai&enabled=true&limit=50"
```

### Create Model
```bash
curl -X POST -H "Cookie: session_token=xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-4o",
    "provider": "openai",
    "display_name": "GPT-4 Optimized",
    "tier_access": ["professional", "enterprise"],
    "pricing": {
      "input_per_1k": 0.01,
      "output_per_1k": 0.03
    }
  }' \
  "http://localhost:8084/api/v1/models/admin/models"
```

### Update Model
```bash
curl -X PUT -H "Cookie: session_token=xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "GPT-4 (Updated)",
    "pricing": {"input_per_1k": 0.02, "output_per_1k": 0.04}
  }' \
  "http://localhost:8084/api/v1/models/admin/models/gpt-4o"
```

### Toggle Model
```bash
curl -X PATCH -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models/gpt-4o/toggle"
```

### Delete Model
```bash
curl -X DELETE -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models/gpt-4o"
```

### Get Statistics
```bash
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models/stats/summary"
```

---

## Filter Parameters

| Parameter | Type | Example | Description |
|-----------|------|---------|-------------|
| `provider` | string | `openai` | Filter by provider |
| `enabled` | boolean | `true` | Filter by enabled status |
| `tier` | string | `professional` | Filter by tier access |
| `search` | string | `gpt` | Search model_id or display_name |
| `deprecated` | boolean | `false` | Include deprecated models |
| `page` | integer | `1` | Page number |
| `limit` | integer | `50` | Items per page (max 500) |

---

## Valid Tier Codes

- `trial` - Trial tier
- `starter` - Starter tier ($19/mo)
- `professional` - Professional tier ($49/mo)
- `enterprise` - Enterprise tier ($99/mo)
- `vip_founder` - VIP Founder tier
- `byok` - Bring Your Own Key tier
- `managed` - Managed tier

---

## Required Fields (Create)

```json
{
  "model_id": "unique-identifier",          // Required, unique
  "provider": "openai",                     // Required
  "display_name": "User-friendly name",    // Required
  "tier_access": ["professional"],          // Required (valid tier codes)
  "pricing": {                              // Required
    "input_per_1k": 0.01,                   // >= 0
    "output_per_1k": 0.03                   // >= 0
  }
}
```

---

## Optional Fields

- `description` - Model description
- `tier_markup` - Pricing markup per tier (default: trial=2.0, starter=1.5, pro=1.2, ent=1.0)
- `context_length` - Max context length
- `max_output_tokens` - Max output tokens
- `supports_vision` - Vision support (default: false)
- `supports_function_calling` - Function calling support (default: false)
- `supports_streaming` - Streaming support (default: true)
- `model_family` - Model family (e.g., gpt-4, claude-3)
- `release_date` - Release date (YYYY-MM-DD)
- `enabled` - Enabled status (default: true)
- `metadata` - Additional metadata (JSON object)

---

## Response Format

### Success (List)
```json
{
  "models": [...],
  "total": 150,
  "page": 1,
  "limit": 50,
  "filters_applied": {...}
}
```

### Success (Single)
```json
{
  "id": "uuid",
  "model_id": "gpt-4o",
  "provider": "openai",
  "display_name": "GPT-4 Optimized",
  "enabled": true,
  "tier_access": ["professional", "enterprise"],
  "pricing": {...},
  "created_at": "2025-11-08T10:00:00",
  "updated_at": "2025-11-08T15:30:00"
}
```

### Error
```json
{
  "detail": "Error message"
}
```

---

## HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation error |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Not admin/moderator |
| 404 | Not Found | Model not found |
| 500 | Internal Server Error | Database/unexpected error |

---

## Caching

- **Cached**: `GET /models` (60s TTL)
- **Cache Invalidation**: Automatic on create/update/delete/toggle
- **Cache Key**: `models:list:<filters_hash>`

---

## Audit Logging

All operations logged to `audit_logs` table:
- Action: `list_models`, `create_model`, `update_model`, `delete_model`, `toggle_model`
- User ID, IP address, user agent
- Resource type: `model`
- Resource ID: `model_id`
- Status: `success` or `error`

---

## Testing

**Test Script**: `/backend/test_model_admin_api.sh`

```bash
# Set your session token
export SESSION_COOKIE="session_token=your_token_here"

# Run tests
bash /home/muut/Production/UC-Cloud/services/ops-center/backend/test_model_admin_api.sh
```

---

## Full Documentation

See `/backend/docs/MODEL_ADMIN_API.md` for comprehensive documentation.
