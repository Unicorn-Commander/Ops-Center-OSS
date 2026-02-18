# Admin API Quick Reference

**Base URL**: `/api/v1/admin`
**Auth**: Admin session cookie required
**Date**: October 8, 2025

---

## 🔐 Authentication

All endpoints require admin authentication via session cookie.

**Error Responses**:
- `401 Unauthorized` - Not authenticated or invalid session
- `403 Forbidden` - Authenticated but not admin user

---

## 📋 Endpoints

### Users

```bash
# List users
GET /api/v1/admin/users?search={query}&max={limit}

# Get user
GET /api/v1/admin/users/{user_id}

# Create user
POST /api/v1/admin/users
{
  "email": "user@example.com",
  "username": "username",
  "first_name": "First",
  "last_name": "Last",
  "password": "Password123!",
  "enabled": true
}

# Update user
PUT /api/v1/admin/users/{user_id}
{
  "email": "newemail@example.com",
  "enabled": false
}

# Delete user
DELETE /api/v1/admin/users/{user_id}
```

### Password

```bash
# Reset password
POST /api/v1/admin/users/{user_id}/reset-password
{
  "new_password": "NewPassword123!",
  "temporary": false
}
```

### Roles

```bash
# Get user roles
GET /api/v1/admin/users/{user_id}/roles

# Add role
POST /api/v1/admin/users/{user_id}/roles
{
  "role_name": "admin"
}

# Remove role
DELETE /api/v1/admin/users/{user_id}/roles/{role_name}

# List all roles
GET /api/v1/admin/roles
```

### Sessions

```bash
# Get sessions
GET /api/v1/admin/users/{user_id}/sessions

# Logout user
POST /api/v1/admin/users/{user_id}/logout
```

### Statistics

```bash
# Get realm stats
GET /api/v1/admin/stats
```

---

## 🔧 Environment Setup

```bash
# Required environment variable
export KEYCLOAK_ADMIN_PASSWORD="your-admin-password"

# Optional (use defaults if not set)
export KEYCLOAK_URL="https://auth.unicorncommander.ai"
export KEYCLOAK_REALM="uchub"
export KEYCLOAK_ADMIN_USERNAME="admin"
```

---

## 🧪 Testing

```bash
# Run test script
cd /home/deploy/Production/UC-1-Pro/services/ops-center
export KEYCLOAK_ADMIN_PASSWORD="your-password"
python3 test_admin_api.py
```

---

## 📖 Full Documentation

See `docs/ADMIN_API.md` for complete documentation with examples.

---

## 🚨 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 | Not authenticated | Login as admin user |
| 403 | Not admin | Verify user has admin role |
| 404 | User not found | Check user ID is correct |
| 409 | User exists | Email/username already taken |
| 500 | Server error | Check logs and Keycloak connectivity |

---

## 📊 Response Formats

### Success Response
```json
{
  "success": true,
  "message": "Operation completed",
  "user_id": "a1b2c3d4-...",
  "data": {}
}
```

### Error Response
```json
{
  "detail": "Error message with context"
}
```

---

## 🔍 Debugging

```bash
# View logs
docker logs unicorn-ops-center | grep "Admin"

# Check Keycloak connectivity
curl https://auth.unicorncommander.ai/realms/uchub/.well-known/openid-configuration

# Test admin auth
python3 -c "
import asyncio
from auth.keycloak_admin import KeycloakAdmin

async def test():
    admin = KeycloakAdmin()
    token = await admin._get_admin_token()
    print(f'Token: {token[:20]}...')

asyncio.run(test())
"
```

---

**Version**: 1.0.0
**Last Updated**: October 8, 2025
