# System Settings API Documentation

**Version**: 1.0.0
**Last Updated**: October 20, 2025
**Status**: Production Ready

---

## Overview

The System Settings API provides a secure, GUI-manageable interface for configuring environment variables and system configuration. All sensitive values are encrypted using Fernet symmetric encryption, cached in Redis for performance, and fully audited.

**Key Features**:
- Encrypted storage of sensitive values (API keys, passwords, secrets)
- Redis caching with 2-minute TTL for fast access
- Comprehensive audit logging with IP tracking
- Category-based organization (security, llm, billing, email, etc.)
- Masked display of sensitive values (show only last 8 characters)
- Hot-reload event emission for configuration changes
- Admin-only access with role-based authorization

---

## Authentication & Authorization

**Required Role**: `admin` or `moderator`

All endpoints require authentication via session cookie. The API checks for:
1. Valid session token in `session_token` cookie
2. User role includes `admin` or `moderator`

**Unauthorized Access**:
- `401 Unauthorized` - No valid session found
- `403 Forbidden` - User lacks admin privileges

---

## API Endpoints

Base URL: `/api/v1/system/settings`

### 1. List Categories

```http
GET /api/v1/system/settings/categories
```

**Description**: List all available setting categories with descriptions.

**Auth Required**: No (public endpoint)

**Response**:
```json
{
  "success": true,
  "categories": [
    {
      "value": "security",
      "label": "Security",
      "description": "Security and encryption settings"
    },
    {
      "value": "llm",
      "label": "LLM Providers",
      "description": "Language model provider API keys and settings"
    },
    {
      "value": "billing",
      "label": "Billing",
      "description": "Stripe and Lago billing configuration"
    },
    {
      "value": "email",
      "label": "Email",
      "description": "SMTP and email provider settings"
    },
    {
      "value": "storage",
      "label": "Storage",
      "description": "S3 and backup storage configuration"
    },
    {
      "value": "integration",
      "label": "Integrations",
      "description": "Third-party service integrations"
    },
    {
      "value": "monitoring",
      "label": "Monitoring",
      "description": "Monitoring and logging configuration"
    },
    {
      "value": "system",
      "label": "System",
      "description": "System-wide configuration"
    }
  ]
}
```

---

### 2. List Settings

```http
GET /api/v1/system/settings
```

**Description**: List all system settings with optional filtering.

**Auth Required**: Yes (admin/moderator)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | null | Filter by category (security, llm, billing, etc.) |
| `include_sensitive` | boolean | true | Include sensitive settings in response |
| `show_values` | boolean | false | Show decrypted values (default: masked) |

**Response**:
```json
{
  "success": true,
  "total": 45,
  "settings": [
    {
      "key": "OPENROUTER_API_KEY",
      "value": "********ey_abc123",
      "category": "llm",
      "description": "OpenRouter API key for LLM routing",
      "is_sensitive": true,
      "value_type": "string",
      "is_required": false,
      "is_editable": true,
      "default_value": null,
      "created_at": "2025-10-20T12:00:00Z",
      "updated_at": "2025-10-20T15:30:00Z",
      "updated_by": "admin@example.com"
    }
  ]
}
```

**Examples**:

```bash
# List all settings (values masked)
curl -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings

# List LLM settings with decrypted values
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings?category=llm&show_values=true"

# List only non-sensitive settings
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings?include_sensitive=false"
```

---

### 3. Get Setting

```http
GET /api/v1/system/settings/{key}
```

**Description**: Get a specific setting by key.

**Auth Required**: Yes (admin/moderator)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | string | Setting key (e.g., "OPENROUTER_API_KEY") |

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `show_value` | boolean | false | Show decrypted value (default: masked) |

**Response**:
```json
{
  "success": true,
  "setting": {
    "key": "SMTP_HOST",
    "value": "smtp.office365.com",
    "category": "email",
    "description": "SMTP server hostname",
    "is_sensitive": false,
    "value_type": "string",
    "is_required": false,
    "is_editable": true,
    "default_value": "smtp.office365.com",
    "created_at": "2025-10-20T12:00:00Z",
    "updated_at": "2025-10-20T12:00:00Z",
    "updated_by": "system"
  }
}
```

**Examples**:

```bash
# Get setting with masked value
curl -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings/OPENROUTER_API_KEY

# Get setting with decrypted value
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings/STRIPE_SECRET_KEY?show_value=true"
```

**Error Responses**:
- `404 Not Found` - Setting does not exist

---

### 4. Create/Update Setting

```http
POST /api/v1/system/settings
```

**Description**: Create a new setting or update existing one.

**Auth Required**: Yes (admin/moderator)

**Request Body**:
```json
{
  "key": "OPENAI_API_KEY",
  "value": "sk-proj-abc123...",
  "category": "llm",
  "description": "OpenAI API key for GPT models",
  "is_sensitive": true,
  "value_type": "string",
  "is_required": false,
  "is_editable": true,
  "default_value": null
}
```

**Field Descriptions**:
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `key` | string | Yes | Setting key (1-255 chars) |
| `value` | string | Yes | Setting value (will be encrypted) |
| `category` | enum | Yes | Category (security, llm, billing, email, storage, integration, monitoring, system) |
| `description` | string | No | Human-readable description |
| `is_sensitive` | boolean | No | Mark as sensitive (default: false) |
| `value_type` | enum | No | Type (string, number, boolean, url, email, json) |
| `is_required` | boolean | No | Required for system operation (default: false) |
| `is_editable` | boolean | No | Can be edited via GUI (default: true) |
| `default_value` | string | No | Default value for documentation |

**Response**:
```json
{
  "success": true,
  "setting": {
    "key": "OPENAI_API_KEY",
    "value": "sk-proj-abc123...",
    "category": "llm",
    "description": "OpenAI API key for GPT models",
    "is_sensitive": true,
    "value_type": "string",
    "is_required": false,
    "is_editable": true,
    "default_value": null,
    "created_at": "2025-10-20T16:00:00Z",
    "updated_at": "2025-10-20T16:00:00Z",
    "updated_by": "admin@example.com"
  }
}
```

**Examples**:

```bash
# Create new API key setting
curl -X POST \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "key": "COHERE_API_KEY",
    "value": "co_abc123...",
    "category": "llm",
    "description": "Cohere API key",
    "is_sensitive": true
  }' \
  http://localhost:8084/api/v1/system/settings

# Create system configuration
curl -X POST \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "key": "SYSTEM_TIMEZONE",
    "value": "America/New_York",
    "category": "system",
    "description": "System timezone",
    "is_sensitive": false,
    "value_type": "string"
  }' \
  http://localhost:8084/api/v1/system/settings
```

**Error Responses**:
- `400 Bad Request` - Category required for new settings
- `403 Forbidden` - Setting is read-only (is_editable=false)

---

### 5. Update Setting

```http
PUT /api/v1/system/settings/{key}
```

**Description**: Update an existing setting (key must exist).

**Auth Required**: Yes (admin/moderator)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | string | Setting key to update |

**Request Body**:
```json
{
  "value": "new-value",
  "description": "Updated description",
  "is_sensitive": true
}
```

**Response**: Same as Create/Update Setting

**Examples**:

```bash
# Update setting value
curl -X PUT \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{"value": "smtp-relay.gmail.com"}' \
  http://localhost:8084/api/v1/system/settings/SMTP_HOST

# Update sensitivity flag
curl -X PUT \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{"is_sensitive": true}' \
  http://localhost:8084/api/v1/system/settings/DATABASE_URL
```

**Error Responses**:
- `404 Not Found` - Setting does not exist
- `403 Forbidden` - Setting is read-only (is_editable=false)

---

### 6. Delete Setting

```http
DELETE /api/v1/system/settings/{key}
```

**Description**: Delete a setting (must be editable and not required).

**Auth Required**: Yes (admin/moderator)

**Path Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `key` | string | Setting key to delete |

**Response**: `204 No Content` (empty response on success)

**Examples**:

```bash
# Delete setting
curl -X DELETE \
  -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings/OLD_API_KEY
```

**Error Responses**:
- `404 Not Found` - Setting does not exist
- `403 Forbidden` - Setting is read-only or required

---

### 7. Get Audit Log

```http
GET /api/v1/system/settings/audit/log
```

**Description**: Get audit log of setting changes.

**Auth Required**: Yes (admin/moderator)

**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `key` | string | null | Filter by setting key |
| `limit` | integer | 100 | Max entries (1-1000) |
| `offset` | integer | 0 | Pagination offset |

**Response**:
```json
{
  "success": true,
  "total": 15,
  "logs": [
    {
      "id": 123,
      "setting_key": "OPENROUTER_API_KEY",
      "action": "UPDATE",
      "old_value": "encrypted_old_value...",
      "new_value": "encrypted_new_value...",
      "changed_by": "admin@example.com",
      "changed_at": "2025-10-20T16:30:00Z",
      "ip_address": "192.168.1.100",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

**Examples**:

```bash
# Get all audit logs
curl -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings/audit/log

# Get audit logs for specific setting
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings/audit/log?key=STRIPE_SECRET_KEY"

# Get recent 50 changes
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings/audit/log?limit=50&offset=0"
```

---

### 8. Bulk Update Settings

```http
POST /api/v1/system/settings/bulk
```

**Description**: Update multiple settings in a single request.

**Auth Required**: Yes (admin/moderator)

**Request Body**:
```json
{
  "settings": [
    {"key": "SMTP_HOST", "value": "smtp.office365.com"},
    {"key": "SMTP_PORT", "value": "587"},
    {"key": "SMTP_USE_TLS", "value": "true"}
  ]
}
```

**Response**:
```json
{
  "success": true,
  "updated": 3,
  "failed": 0,
  "errors": []
}
```

**Examples**:

```bash
# Bulk update email settings
curl -X POST \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "settings": [
      {"key": "SMTP_HOST", "value": "smtp.gmail.com"},
      {"key": "SMTP_PORT", "value": "587"},
      {"key": "SMTP_USERNAME", "value": "admin@example.com"}
    ]
  }' \
  http://localhost:8084/api/v1/system/settings/bulk
```

---

## Database Schema

### system_settings Table

```sql
CREATE TABLE system_settings (
    key VARCHAR(255) PRIMARY KEY,
    encrypted_value TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    is_sensitive BOOLEAN DEFAULT FALSE,
    value_type VARCHAR(20) DEFAULT 'string',
    is_required BOOLEAN DEFAULT FALSE,
    is_editable BOOLEAN DEFAULT TRUE,
    default_value TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(255)
);
```

### system_settings_audit Table

```sql
CREATE TABLE system_settings_audit (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255) NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address VARCHAR(45),
    user_agent TEXT
);
```

---

## Pre-populated Settings

The following settings are pre-populated on initial deployment:

### Security (4 settings)
- `BYOK_ENCRYPTION_KEY` - Master encryption key for BYOK system
- `JWT_SECRET_KEY` - Secret for JWT token generation
- `SESSION_SECRET` - Secret for session cookie encryption
- `CSRF_SECRET_KEY` - Secret for CSRF token generation

### LLM Providers (8 settings)
- `OPENROUTER_API_KEY` - OpenRouter API key
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `GOOGLE_AI_API_KEY` - Google AI API key
- `COHERE_API_KEY` - Cohere API key
- `LITELLM_MASTER_KEY` - LiteLLM proxy master key
- `DEFAULT_LLM_MODEL` - Default model (e.g., "openai/gpt-4")
- `LLM_REQUEST_TIMEOUT` - Request timeout in seconds

### Billing (6 settings)
- `STRIPE_SECRET_KEY` - Stripe secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret
- `LAGO_API_KEY` - Lago API key
- `LAGO_API_URL` - Lago API URL
- `LAGO_PUBLIC_URL` - Lago public URL

### Email (12 settings)
- `SMTP_HOST` - SMTP server hostname
- `SMTP_PORT` - SMTP server port
- `SMTP_USERNAME` - SMTP username
- `SMTP_PASSWORD` - SMTP password
- `SMTP_USE_TLS` - Use TLS (boolean)
- `SMTP_FROM_EMAIL` - Default "From" email
- `SMTP_FROM_NAME` - Default "From" name
- `EMAIL_PROVIDER_TYPE` - Provider type (smtp, oauth2, sendgrid)
- `OAUTH2_CLIENT_ID` - OAuth2 client ID
- `OAUTH2_CLIENT_SECRET` - OAuth2 client secret
- `OAUTH2_TENANT_ID` - OAuth2 tenant ID (Microsoft 365)
- `OAUTH2_REFRESH_TOKEN` - OAuth2 refresh token

### Storage (6 settings)
- `S3_ACCESS_KEY_ID` - AWS S3 access key
- `S3_SECRET_ACCESS_KEY` - AWS S3 secret key
- `S3_BUCKET_NAME` - S3 bucket name
- `S3_REGION` - S3 region
- `BACKUP_RETENTION_DAYS` - Backup retention days
- `BACKUP_SCHEDULE` - Cron schedule for backups

### Integrations (7 settings)
- `KEYCLOAK_CLIENT_SECRET` - Keycloak OAuth client secret
- `KEYCLOAK_ADMIN_PASSWORD` - Keycloak admin password
- `BRIGADE_API_KEY` - Unicorn Brigade API key
- `CENTERDEEP_API_KEY` - Center Deep API key
- `GITHUB_TOKEN` - GitHub personal access token
- `SLACK_BOT_TOKEN` - Slack bot token
- `SLACK_WEBHOOK_URL` - Slack webhook URL

### Monitoring (5 settings)
- `SENTRY_DSN` - Sentry DSN for error tracking
- `GRAFANA_API_KEY` - Grafana API key
- `PROMETHEUS_PUSH_GATEWAY` - Prometheus push gateway URL
- `LOG_LEVEL` - System log level (DEBUG, INFO, WARNING, ERROR)
- `ENABLE_METRICS` - Enable metrics collection (boolean)

### System (7 settings)
- `EXTERNAL_HOST` - External hostname/IP
- `EXTERNAL_PROTOCOL` - External protocol (http/https)
- `SYSTEM_NAME` - System display name
- `SYSTEM_TIMEZONE` - System timezone
- `MAINTENANCE_MODE` - Enable maintenance mode (boolean)
- `ALLOW_SIGNUPS` - Allow new user signups (boolean)
- `DEFAULT_USER_TIER` - Default subscription tier

---

## Security Considerations

### Encryption

All values are encrypted using **Fernet symmetric encryption** (AES-128 in CBC mode):
- Encryption key stored in `SYSTEM_SETTINGS_ENCRYPTION_KEY` environment variable
- Falls back to `BYOK_ENCRYPTION_KEY` if not set
- Generates temporary key if neither is set (data won't persist across restarts)

### Value Masking

Sensitive values are masked by default:
- Only last 8 characters shown (e.g., `********key_abc123`)
- Full decryption requires explicit `show_values=true` parameter
- Decryption only available to admin/moderator roles

### Audit Logging

Every change is logged with:
- User ID (email) of person making change
- IP address of request
- User agent (browser/client)
- Old and new encrypted values
- Timestamp

### Read-Only Settings

Settings with `is_editable=false` cannot be modified or deleted via API:
- Protects critical system configuration
- Prevents accidental deletion of required settings
- Can only be changed via direct database access

### Required Settings

Settings with `is_required=true` cannot be deleted:
- Ensures critical configuration always exists
- Prevents system malfunction from missing settings

---

## Redis Caching

**Cache Strategy**: Cache-Aside (Lazy Loading)

**TTL**: 2 minutes (120 seconds)

**Cache Keys**:
- Individual setting: `system_setting:{key}`
- All settings: `system_settings:all`
- Category-filtered: `system_settings:category:{category}`

**Cache Invalidation**:
- Automatic on create/update/delete operations
- All related cache keys invalidated simultaneously
- Event emitted to Redis pub/sub for hot-reload

---

## Event Emission

When settings change, events are published to Redis pub/sub channel `system_settings_changes`:

```json
{
  "type": "setting_changed",
  "key": "SMTP_HOST",
  "action": "updated",
  "timestamp": "2025-10-20T16:00:00Z"
}
```

**Use Cases**:
- Hot-reload configuration without restart
- Notify services to refresh their config
- Real-time UI updates via WebSocket

---

## Error Handling

### Common Error Responses

**400 Bad Request**:
```json
{
  "detail": "Category is required for new settings"
}
```

**401 Unauthorized**:
```json
{
  "authenticated": false,
  "detail": "No valid session"
}
```

**403 Forbidden**:
```json
{
  "detail": "Admin privileges required to manage system settings"
}
```

**404 Not Found**:
```json
{
  "detail": "Setting 'INVALID_KEY' not found"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Failed to encrypt value"
}
```

---

## Usage Examples

### Python Example

```python
import requests

# Login and get session cookie
session = requests.Session()
# ... perform login to get session_token cookie ...

# List all LLM settings
response = session.get(
    "http://localhost:8084/api/v1/system/settings",
    params={"category": "llm", "show_values": False}
)
settings = response.json()["settings"]

# Update OpenRouter API key
response = session.post(
    "http://localhost:8084/api/v1/system/settings",
    json={
        "key": "OPENROUTER_API_KEY",
        "value": "sk-or-v1-abc123...",
        "category": "llm",
        "description": "OpenRouter API key for LLM routing",
        "is_sensitive": True
    }
)
print(response.json())

# Get audit log
response = session.get(
    "http://localhost:8084/api/v1/system/settings/audit/log",
    params={"key": "OPENROUTER_API_KEY", "limit": 10}
)
audit_logs = response.json()["logs"]
```

### JavaScript Example

```javascript
// Fetch settings
const response = await fetch('/api/v1/system/settings?category=email', {
  credentials: 'include' // Include session cookie
});
const { settings } = await response.json();

// Update setting
const updateResponse = await fetch('/api/v1/system/settings', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    key: 'SMTP_HOST',
    value: 'smtp.gmail.com',
    category: 'email',
    is_sensitive: false
  })
});

// Bulk update
const bulkResponse = await fetch('/api/v1/system/settings/bulk', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    settings: [
      { key: 'SMTP_HOST', value: 'smtp.office365.com' },
      { key: 'SMTP_PORT', value: '587' }
    ]
  })
});
```

---

## Deployment Checklist

Before deploying to production:

1. **Set Encryption Key**:
   ```bash
   # Generate secure encryption key
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

   # Add to .env.auth
   echo "SYSTEM_SETTINGS_ENCRYPTION_KEY=<generated-key>" >> .env.auth
   ```

2. **Run Database Migration**:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /app/sql/system_settings.sql
   ```

3. **Verify Tables Created**:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d system_settings"
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\d system_settings_audit"
   ```

4. **Restart Ops-Center**:
   ```bash
   docker restart ops-center-direct
   ```

5. **Test API Access**:
   ```bash
   # Should return categories
   curl http://localhost:8084/api/v1/system/settings/categories
   ```

---

## Troubleshooting

### Settings Not Persisting

**Symptom**: Settings disappear after container restart

**Cause**: No encryption key set in environment

**Fix**:
```bash
# Add encryption key to .env.auth
echo "SYSTEM_SETTINGS_ENCRYPTION_KEY=<key>" >> /services/ops-center/.env.auth
docker restart ops-center-direct
```

### Decryption Errors

**Symptom**: "Failed to decrypt value" errors

**Cause**: Encryption key changed or values encrypted with different key

**Fix**:
- Restore original encryption key, OR
- Delete and recreate affected settings

### Cache Issues

**Symptom**: Old values returned after update

**Cause**: Redis cache not invalidating

**Fix**:
```bash
# Flush cache manually
docker exec unicorn-redis redis-cli FLUSHDB

# Or restart Redis
docker restart unicorn-redis
```

### Permission Denied

**Symptom**: "Admin privileges required" error

**Cause**: User lacks admin/moderator role

**Fix**:
- Assign admin role in Keycloak
- Or login with admin account

---

## Related Documentation

- **BYOK System**: `/docs/BYOK_IMPLEMENTATION.md`
- **Keycloak Integration**: `/docs/KEYCLOAK_SETUP.md`
- **API Authentication**: `/docs/API_AUTHENTICATION.md`
- **Audit Logging**: `/docs/AUDIT_LOGGING.md`

---

## Support

For issues or questions:
- Check logs: `docker logs ops-center-direct -f`
- Review audit logs: `GET /api/v1/system/settings/audit/log`
- Contact: ops-center-support@magicunicorn.tech
