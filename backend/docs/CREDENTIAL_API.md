# Credential Management API Documentation

**Version**: 1.0.0
**Last Updated**: October 23, 2025
**Epic**: 1.6/1.7 - Service Credential Management

---

## Overview

The Credential Management API provides secure storage and management of service API tokens and keys for:

- **Cloudflare** - DNS management API tokens
- **NameCheap** - Domain registration API keys
- **GitHub** - Repository management tokens
- **Stripe** - Payment processing secret keys

### Key Features

✅ **Fernet Encryption** - All credentials encrypted at rest using AES-128-CBC
✅ **Credential Masking** - Values never exposed in API responses
✅ **Environment Fallback** - Automatic fallback to environment variables
✅ **Credential Testing** - Built-in API validation for each service
✅ **Audit Logging** - Complete audit trail for all operations
✅ **User Isolation** - Credentials scoped to user accounts

---

## Authentication

All endpoints require **admin authentication** via Keycloak SSO.

### Required Headers

```http
Authorization: Bearer {JWT_TOKEN}
Cookie: session_token={SESSION_TOKEN}
```

### Role Requirements

- **Minimum Role**: `admin` or `moderator`
- **User Scope**: Admin sees only their own credentials

---

## API Endpoints

### Base URL

```
https://your-domain.com/api/v1/credentials
```

---

## 1. Create Credential

Create or update a service credential.

### Endpoint

```http
POST /api/v1/credentials
```

### Request Body

```json
{
  "service": "cloudflare",
  "credential_type": "api_token",
  "value": "<CLOUDFLARE_API_TOKEN_REDACTED>",
  "metadata": {
    "description": "Production Cloudflare API token",
    "environment": "production"
  }
}
```

### Request Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `service` | string | Yes | Service name (`cloudflare`, `namecheap`, `github`, `stripe`) |
| `credential_type` | string | Yes | Credential type (varies by service) |
| `value` | string | Yes | Plaintext credential value (min 10 chars) |
| `metadata` | object | No | Optional metadata (description, environment, etc.) |

### Supported Credential Types by Service

| Service | Credential Types |
|---------|------------------|
| `cloudflare` | `api_token` |
| `namecheap` | `api_key`, `api_user` |
| `github` | `api_token`, `personal_access_token` |
| `stripe` | `secret_key`, `publishable_key` |

### Response (201 Created)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "service": "cloudflare",
  "service_name": "Cloudflare",
  "credential_type": "api_token",
  "masked_value": "0LVXY***gC_",
  "metadata": {
    "description": "Production Cloudflare API token",
    "environment": "production"
  },
  "created_at": "2025-10-23T12:30:00.000Z"
}
```

### Error Responses

**400 Bad Request** - Invalid service or credential type
```json
{
  "detail": "Unsupported service. Supported services: cloudflare, namecheap, github, stripe"
}
```

**401 Unauthorized** - Not authenticated
```json
{
  "detail": "Not authenticated"
}
```

**500 Internal Server Error** - Encryption or database error
```json
{
  "detail": "Failed to create credential: {error_message}"
}
```

---

## 2. List Credentials

Get all credentials for authenticated user with masked values.

### Endpoint

```http
GET /api/v1/credentials
```

### Response (200 OK)

```json
[
  {
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "service": "cloudflare",
    "service_name": "Cloudflare",
    "credential_type": "api_token",
    "masked_value": "0LVXY***gC_",
    "metadata": {
      "description": "Production Cloudflare API token"
    },
    "created_at": "2025-10-23T12:30:00.000Z",
    "updated_at": "2025-10-23T12:30:00.000Z",
    "last_tested": "2025-10-23T13:00:00.000Z",
    "test_status": "success"
  },
  {
    "id": "b2c3d4e5-f6g7-8901-bcde-fg2345678901",
    "service": "namecheap",
    "service_name": "NameCheap",
    "credential_type": "api_key",
    "masked_value": "3bce***97bb",
    "metadata": {},
    "created_at": "2025-10-23T14:00:00.000Z",
    "updated_at": "2025-10-23T14:00:00.000Z",
    "last_tested": null,
    "test_status": null
  }
]
```

### Notes

- Returns empty array `[]` if no credentials configured
- Values are **always masked** (never returns plaintext)
- Ordered by service name, then credential type

---

## 3. Get Single Credential

Get details of a specific credential with masked value.

### Endpoint

```http
GET /api/v1/credentials/{service}/{credential_type}
```

### Path Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `service` | string | Service name | `cloudflare` |
| `credential_type` | string | Credential type | `api_token` |

### Example Request

```http
GET /api/v1/credentials/cloudflare/api_token
```

### Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "service": "cloudflare",
  "service_name": "Cloudflare",
  "credential_type": "api_token",
  "masked_value": "0LVXY***gC_",
  "metadata": {
    "description": "Production Cloudflare API token"
  },
  "created_at": "2025-10-23T12:30:00.000Z",
  "updated_at": "2025-10-23T12:30:00.000Z",
  "last_tested": "2025-10-23T13:00:00.000Z",
  "test_status": "success"
}
```

### Error Responses

**404 Not Found** - Credential doesn't exist
```json
{
  "detail": "Credential not found for service=cloudflare, type=api_token"
}
```

---

## 4. Update Credential

Update an existing credential with a new value.

### Endpoint

```http
PUT /api/v1/credentials/{service}/{credential_type}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `service` | string | Service name |
| `credential_type` | string | Credential type |

### Request Body

```json
{
  "value": "NEW_TOKEN_VALUE_HERE",
  "metadata": {
    "description": "Updated production token",
    "rotated_at": "2025-10-23"
  }
}
```

### Response (200 OK)

```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "service": "cloudflare",
  "service_name": "Cloudflare",
  "credential_type": "api_token",
  "masked_value": "NEW_T***ERE",
  "metadata": {
    "description": "Updated production token",
    "rotated_at": "2025-10-23"
  },
  "created_at": "2025-10-23T12:30:00.000Z",
  "updated_at": "2025-10-23T15:00:00.000Z"
}
```

### Notes

- Updates credential value (re-encrypts with new value)
- Resets `test_status` and `last_tested` (requires re-test)
- Preserves `created_at` timestamp
- Overwrites metadata if provided

---

## 5. Delete Credential

Soft delete a credential (sets `is_active = false`).

### Endpoint

```http
DELETE /api/v1/credentials/{service}/{credential_type}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `service` | string | Service name |
| `credential_type` | string | Credential type |

### Example Request

```http
DELETE /api/v1/credentials/cloudflare/api_token
```

### Response (204 No Content)

No response body on success.

### Error Responses

**404 Not Found** - Credential doesn't exist
```json
{
  "detail": "Credential not found for service=cloudflare, type=api_token"
}
```

### Notes

- **Soft delete** - Credential remains in database with `is_active = false`
- Audit trail preserved for compliance
- Deleted credentials excluded from list results
- Can be restored by creating new credential with same service/type

---

## 6. Test Credential

Test credential validity by calling the service API.

### Endpoint

```http
POST /api/v1/credentials/{service}/test
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `service` | string | Service name to test |

### Request Body (Optional)

```json
{
  "value": "CREDENTIAL_VALUE_TO_TEST"
}
```

**Note**: If `value` is omitted, uses stored credential from database.

### Response (200 OK)

**Success Response:**
```json
{
  "success": true,
  "status": "success",
  "message": "Cloudflare API token is valid",
  "details": {
    "id": "token_abc123",
    "status": "active",
    "expires_on": null
  }
}
```

**Failure Response:**
```json
{
  "success": false,
  "status": "failed",
  "message": "Invalid Cloudflare token (HTTP 401)"
}
```

**Error Response:**
```json
{
  "success": false,
  "status": "error",
  "message": "Request timeout - provider may be unreachable"
}
```

### Service-Specific Test Details

#### Cloudflare
- **Endpoint**: `https://api.cloudflare.com/client/v4/user/tokens/verify`
- **Method**: GET with `Authorization: Bearer {token}`
- **Validates**: Token permissions and expiry

#### GitHub
- **Endpoint**: `https://api.github.com/user`
- **Method**: GET with `Authorization: Bearer {token}`
- **Validates**: Token authentication and user access

#### Stripe
- **Endpoint**: `https://api.stripe.com/v1/balance`
- **Method**: GET with HTTP Basic Auth
- **Validates**: Secret key authentication

#### NameCheap
- **Validation**: Format check only (32-char hex)
- **Note**: Full API test requires username and IP whitelist

### Notes

- Test results stored in database (`last_tested`, `test_status`)
- Rate limited to prevent abuse
- Timeout after 15 seconds
- Audit log created for test operation

---

## 7. List Supported Services

Get list of all supported services and their configuration.

### Endpoint

```http
GET /api/v1/credentials/services
```

### Response (200 OK)

```json
[
  {
    "service": "cloudflare",
    "name": "Cloudflare",
    "credential_types": ["api_token"],
    "has_test": true,
    "configured": true
  },
  {
    "service": "namecheap",
    "name": "NameCheap",
    "credential_types": ["api_key", "api_user"],
    "has_test": true,
    "configured": false
  },
  {
    "service": "github",
    "name": "GitHub",
    "credential_types": ["api_token", "personal_access_token"],
    "has_test": true,
    "configured": false
  },
  {
    "service": "stripe",
    "name": "Stripe",
    "credential_types": ["secret_key", "publishable_key"],
    "has_test": true,
    "configured": false
  }
]
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `service` | string | Service identifier (lowercase) |
| `name` | string | Display name |
| `credential_types` | array | Supported credential types for this service |
| `has_test` | boolean | Whether test endpoint is available |
| `configured` | boolean | Whether user has configured this service |

---

## Security Considerations

### Encryption

- **Algorithm**: Fernet (AES-128-CBC with HMAC)
- **Key Storage**: Environment variable `ENCRYPTION_KEY` (never in database)
- **Key Rotation**: Supported via `SecretManager.rotate_encryption_key()`

### Credential Masking

Service-specific masking rules:

| Service | Format | Masked Example |
|---------|--------|----------------|
| Cloudflare | Show first 5 and last 3 chars | `0LVXY***gC_` |
| NameCheap | Show first 4 and last 4 chars | `3bce***97bb` |
| GitHub | Show first 7 and last 4 chars | `ghp_abc***xyz9` |
| Stripe | Show first 10 and last 4 chars | `sk_test_ab***xyz9` |

### Access Control

- ✅ Admin authentication required for all endpoints
- ✅ Users can only access their own credentials
- ✅ No plaintext credentials in API responses
- ✅ Audit logging for all operations

### Environment Variable Fallback

Priority order for credential retrieval:

1. **Database** - User's stored encrypted credential
2. **Environment Variable** - System-wide fallback (if enabled)

Example environment variables:
```bash
CLOUDFLARE_API_TOKEN=your_token_here
NAMECHEAP_API_KEY=your_key_here
NAMECHEAP_API_USER=your_username_here
GITHUB_API_TOKEN=your_token_here
STRIPE_SECRET_KEY=your_key_here
```

---

## Integration Guide

### Using Credentials in Other Services

**Example: Cloudflare API Integration**

```python
from cloudflare_credentials_integration import get_cloudflare_token
from cloudflare_manager import CloudflareManager
from database.connection import get_db_pool

@router.get("/zones")
async def list_zones(request: Request):
    # Get authenticated user
    admin = await require_admin(request)
    user_id = admin.get("user_id")

    # Get Cloudflare token from database or env
    db_pool = await get_db_pool()
    async with db_pool.acquire() as conn:
        token = await get_cloudflare_token(user_id, conn)

    # Use token with CloudflareManager
    manager = CloudflareManager(api_token=token)
    zones = await manager.list_zones()

    return zones
```

**Example: NameCheap API Integration**

```python
from cloudflare_credentials_integration import get_namecheap_credentials

@router.get("/domains")
async def list_domains(request: Request):
    admin = await require_admin(request)
    user_id = admin.get("user_id")

    db_pool = await get_db_pool()
    async with db_pool.acquire() as conn:
        credentials = await get_namecheap_credentials(user_id, conn)

    api_key = credentials["api_key"]
    api_user = credentials["api_user"]

    # Call NameCheap API
    ...
```

### Helper Functions

Located in `cloudflare_credentials_integration.py`:

- `get_cloudflare_token(user_id, db_connection)` → Returns Cloudflare API token
- `get_namecheap_credentials(user_id, db_connection)` → Returns dict with `api_key` and `api_user`
- `get_github_token(user_id, db_connection)` → Returns GitHub API token
- `get_stripe_secret_key(user_id, db_connection)` → Returns Stripe secret key

All functions:
- Return plaintext credentials (INTERNAL USE ONLY)
- Support environment variable fallback
- Raise `HTTPException(400)` if no credentials found

---

## Database Schema

### Table: `service_credentials`

```sql
CREATE TABLE service_credentials (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           VARCHAR(255) NOT NULL,
    service           VARCHAR(100) NOT NULL,
    credential_type   VARCHAR(50) NOT NULL,
    encrypted_value   TEXT NOT NULL,
    metadata          JSONB,
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_tested       TIMESTAMP WITH TIME ZONE,
    test_status       VARCHAR(20),
    is_active         BOOLEAN DEFAULT true,

    CONSTRAINT uq_user_service_credential
        UNIQUE (user_id, service, credential_type)
);

CREATE INDEX idx_service_creds_user ON service_credentials(user_id);
CREATE INDEX idx_service_creds_service ON service_credentials(service);
CREATE INDEX idx_service_creds_active ON service_credentials(is_active);
CREATE INDEX idx_service_creds_user_service ON service_credentials(user_id, service);
```

### Alembic Migration

Migration file: `alembic/versions/20251023_1230_create_service_credentials_table.py`

**Apply migration:**
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
alembic upgrade head
```

**Rollback migration:**
```bash
alembic downgrade -1
```

---

## Testing

### Manual Testing with cURL

**1. Create Cloudflare Credential:**
```bash
curl -X POST "https://your-domain.com/api/v1/credentials" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "cloudflare",
    "credential_type": "api_token",
    "value": "YOUR_CLOUDFLARE_TOKEN",
    "metadata": {"description": "Production API token"}
  }'
```

**2. List Credentials:**
```bash
curl "https://your-domain.com/api/v1/credentials" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

**3. Test Cloudflare Credential:**
```bash
curl -X POST "https://your-domain.com/api/v1/credentials/cloudflare/test" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**4. Update Credential:**
```bash
curl -X PUT "https://your-domain.com/api/v1/credentials/cloudflare/api_token" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "value": "NEW_TOKEN_VALUE",
    "metadata": {"description": "Rotated token", "rotated_at": "2025-10-23"}
  }'
```

**5. Delete Credential:**
```bash
curl -X DELETE "https://your-domain.com/api/v1/credentials/cloudflare/api_token" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Error Handling

### Common Error Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 400 | Bad Request | Invalid service, invalid credential type, validation error |
| 401 | Unauthorized | Missing authentication, invalid token |
| 403 | Forbidden | Insufficient permissions (not admin) |
| 404 | Not Found | Credential doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Encryption error, database error, service unavailable |

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

---

## Rate Limiting

| Operation | Limit | Window |
|-----------|-------|--------|
| Create/Update | 20 requests | 1 minute |
| List/Get | 100 requests | 1 minute |
| Delete | 10 requests | 1 minute |
| Test | 10 requests | 1 minute |

Exceeding rate limits returns `429 Too Many Requests`.

---

## Audit Logging

All credential operations are logged to the `audit_logs` table:

| Action | Event Type |
|--------|------------|
| Create credential | `credential.create` |
| Update credential | `credential.update` |
| Delete credential | `credential.delete` |
| Test credential | `credential.test` |

Audit logs include:
- User ID
- Timestamp
- Action type
- Service and credential type
- Success/failure status
- IP address and user agent

---

## Troubleshooting

### Issue: "No credentials configured" error

**Cause**: Credential not in database and no environment variable fallback

**Solution**:
1. Add credential via API: `POST /api/v1/credentials`
2. Or set environment variable (e.g., `CLOUDFLARE_API_TOKEN`)

### Issue: Credential test fails with "timeout"

**Cause**: Network connectivity or service API unavailable

**Solution**:
- Check network connectivity
- Verify service API status
- Retry after delay

### Issue: "Encryption key not set" error

**Cause**: `ENCRYPTION_KEY` environment variable not configured

**Solution**:
```bash
# Generate new encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Add to .env.auth
echo "ENCRYPTION_KEY=YOUR_GENERATED_KEY" >> .env.auth

# Restart ops-center
docker restart ops-center-direct
```

---

## Related Documentation

- **Secret Manager**: `/backend/secret_manager.py` - Encryption implementation
- **Cloudflare API**: `/backend/cloudflare_api.py` - DNS management
- **Migration API**: `/backend/migration_api.py` - Domain migration
- **Admin API**: `/backend/admin_subscriptions_api.py` - Authentication

---

**Last Updated**: October 23, 2025
**Maintainer**: Backend Development Team Lead
**Epic**: 1.6/1.7 - Service Credential Management
