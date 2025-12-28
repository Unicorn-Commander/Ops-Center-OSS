# Local User Management API - Implementation Complete

**Date**: October 23, 2025
**Status**: ✅ READY FOR INTEGRATION

---

## Overview

Created a comprehensive Local User Management backend API for the Ops-Center at `/home/muut/Production/UC-Cloud/services/ops-center/backend/local_users_api.py`.

This API provides full Linux system user management capabilities with security, validation, and audit logging.

---

## API Endpoints

### Base Path: `/api/v1/admin/system/local-users`

All endpoints require **admin role** authentication.

### 1. List Users
```
GET /api/v1/admin/system/local-users
```

**Query Parameters**:
- `include_system` (bool) - Include system users (UID < 1000). Default: false

**Response**:
```json
{
  "success": true,
  "users": [
    {
      "username": "muut",
      "uid": 1000,
      "gid": 1000,
      "home": "/home/muut",
      "shell": "/bin/bash",
      "groups": ["muut", "sudo", "docker"],
      "has_sudo": true,
      "last_login": "2025-10-23T02:00:00Z",
      "ssh_keys_count": 2,
      "gecos": "System Administrator"
    }
  ],
  "total": 1
}
```

**Features**:
- Filters out system users (UID < 1000) by default
- Includes sudo status, groups, SSH key count
- Shows last login timestamp
- Returns GECOS (full name) field

---

### 2. Create User
```
POST /api/v1/admin/system/local-users
```

**Request Body**:
```json
{
  "username": "testuser",
  "password": "SecureP@ssw0rd123",
  "shell": "/bin/bash",
  "groups": ["docker"],
  "sudo_access": false,
  "gecos": "Test User"
}
```

**Parameters**:
- `username` (required) - Alphanumeric, lowercase, starts with letter
- `password` (optional) - If not provided, generates secure password
- `shell` (optional) - Login shell. Default: /bin/bash
- `groups` (optional) - Additional groups to add user to
- `sudo_access` (optional) - Grant sudo access. Default: false
- `gecos` (optional) - Full name/description

**Password Requirements**:
- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character

**Response**:
```json
{
  "success": true,
  "user": { ... },
  "generated_password": "RandomSecureP@ss123"  // Only if auto-generated
}
```

**Operations**:
1. Validates username format
2. Creates user with `useradd`
3. Sets password with `chpasswd`
4. Adds to specified groups
5. Grants sudo if requested
6. Audits the action

---

### 3. Get User Details
```
GET /api/v1/admin/system/local-users/{username}
```

**Response**: Same as list users, but for single user

---

### 4. Update User
```
PUT /api/v1/admin/system/local-users/{username}
```

**Request Body**:
```json
{
  "password": "NewSecureP@ss456",
  "shell": "/bin/zsh",
  "groups": ["docker", "www-data"],
  "sudo_access": true,
  "gecos": "Updated Name"
}
```

**Notes**:
- All fields are optional
- Only provided fields will be updated
- Groups list REPLACES existing groups (except primary group)

---

### 5. Delete User
```
DELETE /api/v1/admin/system/local-users/{username}
```

**Query Parameters**:
- `remove_home` (bool) - Also remove home directory. Default: true

**Response**: 204 No Content

**Operations**:
- Uses `userdel` command
- Optionally removes home directory and mail spool

---

### 6. Reset Password
```
POST /api/v1/admin/system/local-users/{username}/password
```

**Request Body**:
```json
{
  "password": "NewSecureP@ss789"  // Optional
}
```

**Response**:
```json
{
  "success": true,
  "generated_password": "RandomSecureP@ss890"  // Only if auto-generated
}
```

**Notes**:
- If password not provided, generates secure random password
- Same complexity requirements as create user

---

### 7. List SSH Keys
```
GET /api/v1/admin/system/local-users/{username}/ssh-keys
```

**Response**:
```json
{
  "success": true,
  "keys": [
    {
      "id": 1,
      "key_type": "ssh-ed25519",
      "key_data": "AAAAC3NzaC1lZDI1NTE5AAAAIMl...",
      "comment": "user@hostname",
      "full_key": "ssh-ed25519 AAAAC3... user@hostname"
    }
  ],
  "total": 1
}
```

**Notes**:
- Reads from `~/.ssh/authorized_keys`
- `id` is the line number in the file
- Skips comment lines and blank lines

---

### 8. Add SSH Key
```
POST /api/v1/admin/system/local-users/{username}/ssh-keys
```

**Request Body**:
```json
{
  "ssh_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMl... user@hostname",
  "comment": "Work laptop key"
}
```

**Operations**:
1. Validates SSH key format (ssh-rsa, ssh-ed25519, ecdsa-*)
2. Creates `~/.ssh` directory if needed (mode 700)
3. Appends to `~/.ssh/authorized_keys` (mode 600)
4. Sets proper ownership (user:group)
5. Audits the action

**Response**:
```json
{
  "success": true,
  "message": "SSH key added successfully"
}
```

---

### 9. Remove SSH Key
```
DELETE /api/v1/admin/system/local-users/{username}/ssh-keys/{key_id}
```

**Parameters**:
- `key_id` (int) - Line number of key in authorized_keys file

**Response**: 204 No Content

**Notes**:
- Removes the specified line from authorized_keys
- Key IDs correspond to line numbers from the list endpoint

---

### 10. Manage Sudo Access
```
PUT /api/v1/admin/system/local-users/{username}/sudo
```

**Request Body**:
```json
{
  "enabled": true
}
```

**Operations**:
- If `enabled: true`: Adds user to `sudo` group (or `wheel` on RHEL/CentOS)
- If `enabled: false`: Removes user from sudo/wheel group
- Uses `usermod -aG` to add, `gpasswd -d` to remove

**Response**:
```json
{
  "success": true,
  "user": { ... }
}
```

---

### 11. List Available Groups
```
GET /api/v1/admin/system/local-users/groups
```

**Response**:
```json
{
  "success": true,
  "groups": [
    {
      "name": "sudo",
      "gid": 27,
      "members": ["muut", "aaron"]
    },
    {
      "name": "docker",
      "gid": 999,
      "members": ["muut"]
    }
  ]
}
```

**Notes**:
- Returns all system groups from `/etc/group`
- Sorted alphabetically by group name

---

## Security Features

### 1. Authentication & Authorization
- All endpoints require admin role via `check_admin_role()` dependency
- Checks session for `user_email` and `user_roles`
- Returns 401 Unauthorized if not authenticated
- Returns 403 Forbidden if not admin

### 2. Username Validation
- Must start with lowercase letter
- Only lowercase letters, digits, hyphens, underscores allowed
- Maximum 32 characters
- Regex: `^[a-z][-a-z0-9_]{0,31}$`

### 3. Password Complexity
- Minimum 12 characters (configurable via `PASSWORD_MIN_LENGTH`)
- Requires uppercase letter
- Requires lowercase letter
- Requires digit
- Requires special character
- Validated via `validate_password_strength()`

### 4. SSH Key Validation
- Validates key format against pattern
- Supports: ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp256/384/521
- Regex: `^(ssh-rsa|ssh-ed25519|ecdsa-sha2-nistp256|...) [A-Za-z0-9+/=]+( .+)?$`

### 5. Command Execution Safety
- All system commands run via `run_command()` wrapper
- 30-second timeout on all commands
- Captures stdout and stderr
- Never uses shell=True (prevents command injection)

### 6. Audit Logging
- All operations logged to audit system
- Includes: action, user, IP address, user agent, timestamp, result, metadata
- Failed operations logged with error messages
- Uses existing `audit_logger` instance

---

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful GET/PUT requests
- `201 Created` - User created successfully
- `204 No Content` - Successful DELETE requests
- `400 Bad Request` - Validation errors (invalid username, password, etc.)
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - Not admin or security violation
- `404 Not Found` - User/key not found
- `500 Internal Server Error` - System command failures

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Implementation Details

### File Location
```
/home/muut/Production/UC-Cloud/services/ops-center/backend/local_users_api.py
```

### Dependencies
- **FastAPI** - Web framework
- **Pydantic** - Request/response validation
- **pwd** - User database operations
- **grp** - Group database operations
- **subprocess** - Execute system commands
- **audit_logger** - Audit logging (from models.audit_log)

### System Commands Used
- `useradd` - Create user
- `userdel` - Delete user
- `usermod` - Modify user (shell, groups)
- `chpasswd` - Set password
- `gpasswd` - Manage group membership
- `lastlog` - Get last login timestamp

### Configuration Constants
```python
SYSTEM_UID_MIN = 1000           # Minimum UID for non-system users
PASSWORD_MIN_LENGTH = 12        # Minimum password length
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL = True
```

---

## Integration with server.py

### Current Status
There's already a `local_user_router` registered in server.py at line 337:

```python
from local_user_api import router as local_user_router
...
app.include_router(local_user_router)
logger.info("Local User Management API endpoints registered at /api/v1/local-users")
```

### Migration Path

**Option 1: Replace Existing Implementation**
1. Rename old `local_user_api.py` to `local_user_api_old.py`
2. Rename new `local_users_api.py` to `local_user_api.py`
3. Update import in server.py (already correct)
4. Restart backend

**Option 2: Run Both Implementations**
1. Keep existing `/api/v1/local-users` (old implementation)
2. Add new `/api/v1/admin/system/local-users` (new implementation)
3. Add to server.py:
   ```python
   from local_users_api import router as admin_local_users_router
   app.include_router(admin_local_users_router)
   ```

**Option 3: Update Existing Implementation Path**
1. Edit `local_user_api.py` to change router prefix
2. Update from `/api/v1/local-users` to `/api/v1/admin/system/local-users`

### Recommended Approach: Option 2
Run both implementations in parallel:
- Old implementation for backward compatibility
- New implementation for explicit admin-scoped endpoints

Add to server.py around line 340:
```python
from local_users_api import router as admin_local_users_router
app.include_router(admin_local_users_router)
logger.info("Admin Local User Management API endpoints registered at /api/v1/admin/system/local-users")
```

---

## Testing

### Manual Testing Commands

#### 1. List Users
```bash
curl http://localhost:8084/api/v1/admin/system/local-users \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json"
```

#### 2. Create User
```bash
curl -X POST http://localhost:8084/api/v1/admin/system/local-users \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "shell": "/bin/bash",
    "groups": ["docker"],
    "sudo_access": false,
    "gecos": "Test User"
  }'
```

#### 3. Reset Password
```bash
curl -X POST http://localhost:8084/api/v1/admin/system/local-users/testuser/password \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{}' # Auto-generates password
```

#### 4. Add SSH Key
```bash
curl -X POST http://localhost:8084/api/v1/admin/system/local-users/testuser/ssh-keys \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{
    "ssh_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKxyz... test@example.com",
    "comment": "Test key"
  }'
```

#### 5. Grant Sudo
```bash
curl -X PUT http://localhost:8084/api/v1/admin/system/local-users/testuser/sudo \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

#### 6. Delete User
```bash
curl -X DELETE http://localhost:8084/api/v1/admin/system/local-users/testuser?remove_home=true \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json"
```

### Verification

After creating/modifying users, verify with system commands:

```bash
# Check user exists
id testuser

# Check groups
groups testuser

# Check sudo access
sudo -l -U testuser

# Check SSH keys
cat ~testuser/.ssh/authorized_keys
```

---

## Audit Log Examples

All operations are logged to the audit system. Example entries:

```json
{
  "action": "user.create",
  "result": "success",
  "user_id": "admin@example.com",
  "username": "admin@example.com",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "resource_type": "local_user",
  "resource_id": "testuser",
  "timestamp": "2025-10-23T14:30:00Z",
  "metadata": {
    "shell": "/bin/bash",
    "groups": ["docker"],
    "sudo_access": false,
    "password_generated": true
  }
}
```

Failed operations example:
```json
{
  "action": "user.create",
  "result": "failure",
  "error_message": "Username must start with lowercase letter",
  "resource_id": "9testuser",
  "timestamp": "2025-10-23T14:31:00Z"
}
```

---

## Known Limitations

1. **Password Storage**: Passwords are set via `chpasswd`, not returned to client for security
2. **Last Login**: Parsing `lastlog` output is simplified, may not work on all systems
3. **Sudo Detection**: Checks `sudo`/`wheel` group membership, not full sudoers file parsing
4. **Command Timeout**: All system commands timeout after 30 seconds
5. **No Email Notifications**: User creation doesn't send welcome emails
6. **No Home Directory Templates**: Uses system default `/etc/skel`

---

## Future Enhancements

1. **User Groups Management**: Create/delete/modify groups
2. **Bulk Operations**: Create multiple users from CSV
3. **User Quotas**: Set disk quotas per user
4. **SSH Key Comments**: Auto-add admin email to SSH keys
5. **Password Expiration**: Set password expiry policies
6. **Account Locking**: Temporary account suspension
7. **Login History**: Detailed login tracking
8. **Shell Restrictions**: Restrict available shells per user
9. **Home Directory Backup**: Auto-backup before deletion
10. **Email Notifications**: Welcome emails and password resets

---

## Security Considerations

1. **Sudo Operations**: All commands run as the user running the backend (should have sudo privileges)
2. **Session Security**: Relies on existing session middleware for authentication
3. **Audit Trail**: All actions logged for compliance and forensics
4. **Input Validation**: Extensive validation prevents injection attacks
5. **File Permissions**: Properly sets permissions on .ssh directories and authorized_keys
6. **Error Messages**: Doesn't leak sensitive information in error messages
7. **Rate Limiting**: Consider adding rate limiting for brute-force protection (future enhancement)

---

## Documentation

- **API Reference**: This document
- **OpenAPI Schema**: Auto-generated at `/docs` endpoint
- **Code Documentation**: Inline docstrings in `local_users_api.py`
- **Audit Logging**: See `models/audit_log.py` for audit action types

---

## Support

For issues or questions:
1. Check audit logs: `/api/v1/audit/logs`
2. Review container logs: `docker logs ops-center-direct`
3. Verify permissions: Backend must have sudo access for user management
4. Test authentication: Ensure admin role is properly set in session

---

**Status**: ✅ Implementation Complete - Ready for Integration
**Next Steps**: Choose integration option and update server.py
