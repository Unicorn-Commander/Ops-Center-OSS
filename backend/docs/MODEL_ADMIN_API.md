# Model Admin API Documentation

**Version**: 1.0.0
**Base URL**: `/api/v1/models/admin`
**Authentication**: Admin or Moderator role required
**Created**: November 8, 2025

---

## Overview

The Model Admin API provides comprehensive CRUD (Create, Read, Update, Delete) operations for managing the LLM model catalog. This API is used by system administrators to control which models are available to users based on their subscription tier.

### Key Features

- ✅ Full CRUD operations for models
- ✅ Tier-based access control
- ✅ Provider management (OpenAI, Anthropic, OpenRouter, etc.)
- ✅ Pricing and markup configuration
- ✅ Advanced filtering and search
- ✅ Pagination support
- ✅ Redis caching (60s TTL)
- ✅ Comprehensive audit logging
- ✅ Input validation with Pydantic

### Database Table

All model data is stored in the `model_access_control` table in the `unicorn_db` PostgreSQL database.

**Schema**: See `/backend/sql/model_access_control_schema.sql`

---

## Authentication

All endpoints require authentication via session cookie with **admin** or **moderator** role.

**Session Cookie**: `session_token=<your_session_token>`

**Unauthorized Response** (401):
```json
{
  "detail": "Not authenticated"
}
```

**Forbidden Response** (403):
```json
{
  "detail": "Admin or moderator access required"
}
```

---

## Endpoints

### 1. List Models

**GET** `/api/v1/models/admin/models`

List all models with advanced filtering and pagination.

#### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `provider` | string | null | Filter by provider (e.g., openai, anthropic) |
| `enabled` | boolean | null | Filter by enabled status |
| `tier` | string | null | Filter by tier access (trial, starter, etc.) |
| `search` | string | null | Search model_id or display_name |
| `deprecated` | boolean | false | Include deprecated models |
| `page` | integer | 1 | Page number (min: 1) |
| `limit` | integer | 50 | Items per page (min: 1, max: 500) |

#### Response (200 OK)

```json
{
  "models": [
    {
      "id": "uuid-here",
      "model_id": "gpt-4o",
      "provider": "openai",
      "display_name": "GPT-4 Optimized",
      "description": "Latest GPT-4 model with improved performance",
      "enabled": true,
      "tier_access": ["professional", "enterprise"],
      "pricing": {
        "input_per_1k": 0.01,
        "output_per_1k": 0.03
      },
      "tier_markup": {
        "trial": 2.0,
        "starter": 1.5,
        "professional": 1.2,
        "enterprise": 1.0
      },
      "context_length": 128000,
      "max_output_tokens": 4096,
      "supports_vision": true,
      "supports_function_calling": true,
      "supports_streaming": true,
      "model_family": "gpt-4",
      "release_date": "2024-05-13",
      "deprecated": false,
      "replacement_model": null,
      "metadata": {},
      "created_at": "2025-11-01T10:00:00",
      "updated_at": "2025-11-08T15:30:00"
    }
  ],
  "total": 150,
  "page": 1,
  "limit": 50,
  "filters_applied": {
    "provider": "openai",
    "enabled": true
  }
}
```

#### Example Requests

```bash
# List all models (first 50)
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models?limit=50&page=1"

# Filter by provider
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models?provider=openrouter"

# Filter by tier access
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models?tier=professional"

# Search models
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models?search=claude"

# Multiple filters
curl -H "Cookie: session_token=xxx" \
  "http://localhost:8084/api/v1/models/admin/models?provider=anthropic&enabled=true&tier=enterprise"
```

---

### 2. Create Model

**POST** `/api/v1/models/admin/models`

Create a new model in the catalog.

#### Request Body

```json
{
  "model_id": "gpt-4o-2024-11-20",
  "provider": "openai",
  "display_name": "GPT-4 Optimized (Nov 2024)",
  "description": "Latest GPT-4 model with vision and function calling",
  "tier_access": ["professional", "enterprise"],
  "pricing": {
    "input_per_1k": 0.01,
    "output_per_1k": 0.03
  },
  "tier_markup": {
    "trial": 2.0,
    "starter": 1.5,
    "professional": 1.2,
    "enterprise": 1.0
  },
  "context_length": 128000,
  "max_output_tokens": 4096,
  "supports_vision": true,
  "supports_function_calling": true,
  "supports_streaming": true,
  "model_family": "gpt-4",
  "release_date": "2024-11-20",
  "enabled": true,
  "metadata": {
    "official": true,
    "recommended": true
  }
}
```

#### Response (201 Created)

```json
{
  "id": "uuid-here",
  "model_id": "gpt-4o-2024-11-20",
  "provider": "openai",
  ...
}
```

#### Validation Rules

- ✅ `model_id` must be unique
- ✅ `pricing.input_per_1k` must be >= 0
- ✅ `pricing.output_per_1k` must be >= 0
- ✅ `tier_access` must contain valid tier codes: `trial`, `starter`, `professional`, `enterprise`, `vip_founder`, `byok`, `managed`
- ✅ `provider` is required
- ✅ `display_name` is required

#### Error Responses

**400 Bad Request** (duplicate model_id):
```json
{
  "detail": "Model 'gpt-4o' already exists"
}
```

**400 Bad Request** (invalid tier):
```json
{
  "detail": "Invalid tier codes: {'invalid_tier'}"
}
```

**400 Bad Request** (negative pricing):
```json
{
  "detail": "Pricing values must be positive"
}
```

---

### 3. Get Model Details

**GET** `/api/v1/models/admin/models/{model_id}`

Get detailed information about a specific model.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_id` | string | The model identifier (e.g., gpt-4o) |

#### Response (200 OK)

```json
{
  "id": "uuid-here",
  "model_id": "gpt-4o",
  "provider": "openai",
  "display_name": "GPT-4 Optimized",
  ...
}
```

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Model 'invalid-model' not found"
}
```

---

### 4. Update Model

**PUT** `/api/v1/models/admin/models/{model_id}`

Update an existing model. Only provided fields will be updated (partial update).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_id` | string | The model identifier |

#### Request Body (Partial)

```json
{
  "display_name": "GPT-4 Optimized (Updated)",
  "description": "Updated description",
  "pricing": {
    "input_per_1k": 0.02,
    "output_per_1k": 0.04
  },
  "enabled": false
}
```

All fields are optional. Only include fields you want to update.

#### Response (200 OK)

```json
{
  "id": "uuid-here",
  "model_id": "gpt-4o",
  "display_name": "GPT-4 Optimized (Updated)",
  ...
}
```

#### Error Responses

**400 Bad Request** (no fields to update):
```json
{
  "detail": "No fields to update"
}
```

**404 Not Found**:
```json
{
  "detail": "Model 'invalid-model' not found"
}
```

---

### 5. Delete Model

**DELETE** `/api/v1/models/admin/models/{model_id}`

Permanently delete a model from the catalog.

⚠️ **Warning**: This action cannot be undone!

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_id` | string | The model identifier |

#### Response (200 OK)

```json
{
  "message": "Model 'gpt-4o' deleted successfully"
}
```

#### Error Responses

**404 Not Found**:
```json
{
  "detail": "Model 'invalid-model' not found"
}
```

---

### 6. Toggle Model Status

**PATCH** `/api/v1/models/admin/models/{model_id}/toggle`

Enable or disable a model (convenience endpoint).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_id` | string | The model identifier |

#### Response (200 OK)

```json
{
  "model_id": "gpt-4o",
  "enabled": false,
  "message": "Model disabled successfully"
}
```

Or:

```json
{
  "model_id": "gpt-4o",
  "enabled": true,
  "message": "Model enabled successfully"
}
```

---

### 7. Model Statistics

**GET** `/api/v1/models/admin/models/stats/summary`

Get aggregate statistics about the model catalog.

#### Response (200 OK)

```json
{
  "total_models": 150,
  "enabled_models": 142,
  "disabled_models": 8,
  "deprecated_models": 5,
  "provider_distribution": {
    "openrouter": 85,
    "openai": 30,
    "anthropic": 20,
    "google": 10,
    "meta": 5
  },
  "tier_coverage": {
    "trial": 50,
    "starter": 80,
    "professional": 120,
    "enterprise": 150,
    "vip_founder": 150,
    "byok": 0,
    "managed": 150
  }
}
```

---

## Caching

The Model Admin API uses Redis caching to improve performance:

- **Cache TTL**: 60 seconds
- **Cache Keys**: `models:list:<filters_hash>`
- **Cache Invalidation**: Automatic on create/update/delete/toggle operations

Cached endpoints:
- ✅ `GET /models` (list with filters)

Non-cached endpoints:
- `GET /models/{model_id}` (single model)
- `GET /models/stats/summary` (real-time stats)

---

## Audit Logging

All operations are logged to the `audit_logs` table with:

- ✅ User ID
- ✅ Action (list_models, create_model, update_model, delete_model, toggle_model)
- ✅ Resource type (model)
- ✅ Resource ID (model_id)
- ✅ IP address
- ✅ User agent
- ✅ Timestamp
- ✅ Status (success/error)

Example audit log entry:
```json
{
  "id": "uuid-here",
  "timestamp": "2025-11-08T15:30:00",
  "user_id": "user-uuid",
  "action": "create_model",
  "resource_type": "model",
  "resource_id": "gpt-4o",
  "details": {
    "model_id": "gpt-4o",
    "provider": "openai",
    "ip": "192.168.1.1",
    "user_agent": "Mozilla/5.0..."
  },
  "status": "success"
}
```

---

## Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| 200 | OK | Successful GET/PUT/DELETE |
| 201 | Created | Successful POST |
| 400 | Bad Request | Validation error, duplicate model_id |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | Not admin/moderator |
| 404 | Not Found | Model not found |
| 500 | Internal Server Error | Database error, unexpected error |

---

## Best Practices

### 1. Creating Models

✅ **DO**:
- Use descriptive `model_id` values (e.g., `gpt-4o-2024-11-20`)
- Set accurate pricing based on provider costs
- Use tier markup multipliers for profit margin
- Include all supported capabilities (vision, function calling, etc.)
- Set appropriate context_length and max_output_tokens

❌ **DON'T**:
- Use generic model_id values (e.g., `model1`, `test`)
- Set negative pricing
- Include invalid tier codes
- Leave required fields empty

### 2. Updating Models

✅ **DO**:
- Use partial updates (only include fields you want to change)
- Update pricing when provider changes costs
- Deprecate old models instead of deleting them
- Set replacement_model when deprecating

❌ **DON'T**:
- Update pricing without checking provider cost changes
- Delete models that users might be actively using
- Change model_id (create new model instead)

### 3. Managing Tiers

✅ **DO**:
- Use tier_access to control which users see which models
- Set appropriate markup multipliers per tier
- Provide trial users access to basic models
- Reserve premium models for professional/enterprise tiers

❌ **DON'T**:
- Give trial users access to expensive models
- Use same markup for all tiers
- Forget to update tier_access when adding new tiers

### 4. Performance

✅ **DO**:
- Use filtering to reduce result sets
- Leverage Redis caching (responses are cached for 60s)
- Use pagination for large result sets
- Search instead of fetching all models

❌ **DON'T**:
- Fetch all models without pagination
- Make frequent updates that invalidate cache
- Perform full scans without filters

---

## Integration Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8084/api/v1/models/admin"
SESSION_COOKIE = "session_token=your_session_token"

# List models
response = requests.get(
    f"{BASE_URL}/models",
    headers={"Cookie": SESSION_COOKIE},
    params={
        "provider": "openai",
        "enabled": True,
        "limit": 50
    }
)
models = response.json()

# Create model
new_model = {
    "model_id": "gpt-4o-new",
    "provider": "openai",
    "display_name": "GPT-4 Latest",
    "tier_access": ["professional", "enterprise"],
    "pricing": {
        "input_per_1k": 0.01,
        "output_per_1k": 0.03
    }
}
response = requests.post(
    f"{BASE_URL}/models",
    headers={"Cookie": SESSION_COOKIE},
    json=new_model
)
created = response.json()

# Update model
updates = {
    "display_name": "GPT-4 Latest (Updated)",
    "pricing": {
        "input_per_1k": 0.02,
        "output_per_1k": 0.04
    }
}
response = requests.put(
    f"{BASE_URL}/models/gpt-4o-new",
    headers={"Cookie": SESSION_COOKIE},
    json=updates
)

# Toggle model
response = requests.patch(
    f"{BASE_URL}/models/gpt-4o-new/toggle",
    headers={"Cookie": SESSION_COOKIE}
)

# Delete model
response = requests.delete(
    f"{BASE_URL}/models/gpt-4o-new",
    headers={"Cookie": SESSION_COOKIE}
)
```

### JavaScript Example

```javascript
const BASE_URL = 'http://localhost:8084/api/v1/models/admin';
const SESSION_COOKIE = 'session_token=your_session_token';

// List models
const listModels = async () => {
  const response = await fetch(`${BASE_URL}/models?provider=openai&limit=50`, {
    headers: {
      'Cookie': SESSION_COOKIE
    }
  });
  const data = await response.json();
  console.log(data.models);
};

// Create model
const createModel = async () => {
  const newModel = {
    model_id: 'gpt-4o-new',
    provider: 'openai',
    display_name: 'GPT-4 Latest',
    tier_access: ['professional', 'enterprise'],
    pricing: {
      input_per_1k: 0.01,
      output_per_1k: 0.03
    }
  };

  const response = await fetch(`${BASE_URL}/models`, {
    method: 'POST',
    headers: {
      'Cookie': SESSION_COOKIE,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(newModel)
  });

  const data = await response.json();
  console.log(data);
};

// Update model
const updateModel = async (modelId) => {
  const updates = {
    display_name: 'GPT-4 Latest (Updated)'
  };

  const response = await fetch(`${BASE_URL}/models/${modelId}`, {
    method: 'PUT',
    headers: {
      'Cookie': SESSION_COOKIE,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(updates)
  });

  const data = await response.json();
  console.log(data);
};
```

---

## Changelog

### Version 1.0.0 (November 8, 2025)

**Initial Release**:
- ✅ Full CRUD operations
- ✅ Advanced filtering and search
- ✅ Pagination support
- ✅ Redis caching
- ✅ Audit logging
- ✅ Input validation
- ✅ Comprehensive documentation

---

## Support

**File Location**: `/backend/model_admin_api.py`
**Test Script**: `/backend/test_model_admin_api.sh`
**Database Schema**: `/backend/sql/model_access_control_schema.sql`

For issues or questions, contact the Backend API Team.
