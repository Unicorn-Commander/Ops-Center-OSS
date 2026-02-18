# Admin User Management API

Complete REST API documentation for user management via Keycloak Admin API.

## Overview

The Admin User Management API provides comprehensive user administration capabilities through Keycloak. All endpoints require admin authentication and use the Keycloak Admin REST API.

**Base URL**: `https://unicorncommander.ai/api/v1/admin`

**Authentication**: Admin session cookie (`session_token`) required for all endpoints

**Error Handling**: All endpoints return detailed error messages with appropriate HTTP status codes

## Authentication

All admin endpoints check for:
1. Valid session token in cookies
2. Admin role (`is_admin: true`) in session

**Unauthorized Access**:
- `401`: No session token or invalid session
- `403`: Valid session but not admin user

## Environment Variables

Required environment variables:

```bash
KEYCLOAK_URL=https://auth.unicorncommander.ai
KEYCLOAK_REALM=uchub
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=<your-admin-password>  # REQUIRED
```

## API Endpoints

### 1. List Users

**GET** `/api/v1/admin/users`

List users with optional filtering and pagination.

**Query Parameters**:
- `search` (optional): Search query (searches username, email, first/last name)
- `first` (optional): Pagination offset (default: 0)
- `max` (optional): Maximum results to return (default: 100)
- `enabled` (optional): Filter by enabled status (true/false)

**Example Request**:
```bash
curl -X GET 'https://unicorncommander.ai/api/v1/admin/users?search=john&max=10' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "users": [
    {
      "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "username": "john.doe",
      "email": "john@example.com",
      "firstName": "John",
      "lastName": "Doe",
      "enabled": true,
      "emailVerified": true,
      "createdTimestamp": 1696339200000
    }
  ],
  "total": 1,
  "first": 0,
  "max": 10
}
```

---

### 2. Get User Details

**GET** `/api/v1/admin/users/{user_id}`

Get detailed information for a specific user.

**Path Parameters**:
- `user_id`: Keycloak user ID (UUID)

**Example Request**:
```bash
curl -X GET 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "username": "john.doe",
  "email": "john@example.com",
  "firstName": "John",
  "lastName": "Doe",
  "enabled": true,
  "emailVerified": true,
  "createdTimestamp": 1696339200000,
  "attributes": {}
}
```

---

### 3. Create User

**POST** `/api/v1/admin/users`

Create a new user in Keycloak.

**Request Body**:
```json
{
  "email": "jane@example.com",
  "username": "jane.doe",
  "first_name": "Jane",
  "last_name": "Doe",
  "password": "TemporaryPassword123!",
  "enabled": true,
  "email_verified": false
}
```

**Required Fields**:
- `email`: User email address
- `username`: Username (must be unique)

**Optional Fields**:
- `first_name`: First name
- `last_name`: Last name
- `password`: Initial password (if not provided, user must set via reset link)
- `enabled`: Enable user account (default: true)
- `email_verified`: Email verification status (default: false)

**Example Request**:
```bash
curl -X POST 'https://unicorncommander.ai/api/v1/admin/users' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: session_token=your-session-token' \
  -d '{
    "email": "jane@example.com",
    "username": "jane.doe",
    "first_name": "Jane",
    "last_name": "Doe",
    "password": "TemporaryPassword123!"
  }'
```

**Response**:
```json
{
  "success": true,
  "user_id": "b2c3d4e5-6789-01bc-def2-234567890abc",
  "message": "User jane.doe created successfully"
}
```

---

### 4. Update User

**PUT** `/api/v1/admin/users/{user_id}`

Update user information.

**Path Parameters**:
- `user_id`: Keycloak user ID

**Request Body** (all fields optional):
```json
{
  "email": "newemail@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "enabled": true,
  "email_verified": true
}
```

**Example Request**:
```bash
curl -X PUT 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: session_token=your-session-token' \
  -d '{
    "email": "newemail@example.com",
    "enabled": false
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "User updated successfully"
}
```

---

### 5. Delete User

**DELETE** `/api/v1/admin/users/{user_id}`

Delete a user from Keycloak.

**Path Parameters**:
- `user_id`: Keycloak user ID

**Example Request**:
```bash
curl -X DELETE 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "success": true,
  "message": "User john.doe deleted successfully"
}
```

**Warning**: This action cannot be undone!

---

### 6. Reset Password

**POST** `/api/v1/admin/users/{user_id}/reset-password`

Reset user's password.

**Path Parameters**:
- `user_id`: Keycloak user ID

**Request Body**:
```json
{
  "new_password": "NewSecurePassword123!",
  "temporary": false
}
```

**Fields**:
- `new_password`: New password for the user
- `temporary`: If true, user must change password on next login (default: false)

**Example Request**:
```bash
curl -X POST 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab/reset-password' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: session_token=your-session-token' \
  -d '{
    "new_password": "NewSecurePassword123!",
    "temporary": true
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Password reset successfully",
  "temporary": true
}
```

---

### 7. Get User Roles

**GET** `/api/v1/admin/users/{user_id}/roles`

Get user's assigned realm roles.

**Path Parameters**:
- `user_id`: Keycloak user ID

**Example Request**:
```bash
curl -X GET 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab/roles' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "user_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "roles": [
    {
      "id": "role-id-1",
      "name": "user",
      "description": "Default user role"
    },
    {
      "id": "role-id-2",
      "name": "admin",
      "description": "Administrator role"
    }
  ],
  "count": 2
}
```

---

### 8. Add Role to User

**POST** `/api/v1/admin/users/{user_id}/roles`

Add a role to a user.

**Path Parameters**:
- `user_id`: Keycloak user ID

**Request Body**:
```json
{
  "role_name": "admin"
}
```

**Example Request**:
```bash
curl -X POST 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab/roles' \
  -H 'Content-Type: application/json' \
  -H 'Cookie: session_token=your-session-token' \
  -d '{
    "role_name": "admin"
  }'
```

**Response**:
```json
{
  "success": true,
  "message": "Role 'admin' added successfully"
}
```

---

### 9. Remove Role from User

**DELETE** `/api/v1/admin/users/{user_id}/roles/{role_name}`

Remove a role from a user.

**Path Parameters**:
- `user_id`: Keycloak user ID
- `role_name`: Name of the role to remove

**Example Request**:
```bash
curl -X DELETE 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab/roles/admin' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "success": true,
  "message": "Role 'admin' removed successfully"
}
```

---

### 10. Get User Sessions

**GET** `/api/v1/admin/users/{user_id}/sessions`

Get user's active sessions.

**Path Parameters**:
- `user_id`: Keycloak user ID

**Example Request**:
```bash
curl -X GET 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab/sessions' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "user_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "sessions": [
    {
      "id": "session-id-1",
      "username": "john.doe",
      "userId": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
      "ipAddress": "192.168.1.100",
      "start": 1696339200000,
      "lastAccess": 1696342800000,
      "clients": {
        "ops-center": {
          "clientId": "ops-center"
        }
      }
    }
  ],
  "count": 1
}
```

---

### 11. Logout User

**POST** `/api/v1/admin/users/{user_id}/logout`

Terminate all user sessions (force logout).

**Path Parameters**:
- `user_id`: Keycloak user ID

**Example Request**:
```bash
curl -X POST 'https://unicorncommander.ai/api/v1/admin/users/a1b2c3d4-5678-90ab-cdef-1234567890ab/logout' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "success": true,
  "message": "User john.doe logged out successfully"
}
```

---

### 12. Get Statistics

**GET** `/api/v1/admin/stats`

Get realm statistics and user counts.

**Example Request**:
```bash
curl -X GET 'https://unicorncommander.ai/api/v1/admin/stats' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "total_users": 150,
  "enabled_users": 145,
  "disabled_users": 5,
  "verified_emails": 120,
  "realm": "uchub",
  "timestamp": "2025-10-08T12:34:56.789Z"
}
```

---

### 13. Get Available Roles

**GET** `/api/v1/admin/roles`

Get all available realm roles.

**Example Request**:
```bash
curl -X GET 'https://unicorncommander.ai/api/v1/admin/roles' \
  -H 'Cookie: session_token=your-session-token'
```

**Response**:
```json
{
  "roles": [
    {
      "id": "role-id-1",
      "name": "admin",
      "description": "Administrator role",
      "composite": false,
      "clientRole": false
    },
    {
      "id": "role-id-2",
      "name": "user",
      "description": "Default user role",
      "composite": false,
      "clientRole": false
    }
  ],
  "count": 2
}
```

---

## Error Responses

All endpoints may return the following error responses:

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Admin access required"
}
```

### 404 Not Found
```json
{
  "detail": "User not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to create user: <error message>"
}
```

### 502 Bad Gateway
```json
{
  "detail": "Failed to connect to Keycloak: <error message>"
}
```

---

## Security Considerations

1. **Admin Authentication**: All endpoints require admin session with `is_admin: true`
2. **Audit Logging**: All admin actions are logged with admin email and timestamp
3. **Token Caching**: Admin tokens are cached for 30 seconds before expiry
4. **Error Handling**: Detailed errors are logged but sanitized for client response
5. **Rate Limiting**: Consider implementing rate limiting for admin endpoints

---

## Testing

Use the provided test script to verify functionality:

```bash
# Set admin password
export KEYCLOAK_ADMIN_PASSWORD="your-admin-password"

# Run tests
cd /home/deploy/Production/UC-1-Pro/services/ops-center
python3 test_admin_api.py
```

---

## Integration Examples

### JavaScript (Frontend)

```javascript
// List users
async function listUsers(search = '') {
  const response = await fetch(`/api/v1/admin/users?search=${search}`, {
    credentials: 'include'  // Include cookies
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${await response.text()}`);
  }

  return await response.json();
}

// Create user
async function createUser(userData) {
  const response = await fetch('/api/v1/admin/users', {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  });

  return await response.json();
}

// Reset password
async function resetPassword(userId, newPassword, temporary = false) {
  const response = await fetch(`/api/v1/admin/users/${userId}/reset-password`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ new_password: newPassword, temporary })
  });

  return await response.json();
}
```

### Python

```python
import httpx

class AdminAPIClient:
    def __init__(self, base_url, session_token):
        self.base_url = base_url
        self.cookies = {"session_token": session_token}

    async def list_users(self, search=None, max_results=100):
        params = {"max": max_results}
        if search:
            params["search"] = search

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/admin/users",
                params=params,
                cookies=self.cookies
            )
            response.raise_for_status()
            return response.json()

    async def create_user(self, email, username, **kwargs):
        user_data = {
            "email": email,
            "username": username,
            **kwargs
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/admin/users",
                json=user_data,
                cookies=self.cookies
            )
            response.raise_for_status()
            return response.json()
```

---

## Support

For issues or questions:
- Check logs: `docker logs unicorn-ops-center`
- Verify Keycloak Admin password is set correctly
- Ensure admin user has proper roles in Keycloak
- Test Keycloak connectivity: `curl https://auth.unicorncommander.ai/realms/uchub/.well-known/openid-configuration`

---

**Last Updated**: October 8, 2025
**Version**: 1.0.0
