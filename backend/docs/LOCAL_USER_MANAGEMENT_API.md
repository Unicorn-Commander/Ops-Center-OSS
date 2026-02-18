# Local User Management API

**Version**: 1.0.0
**Last Updated**: October 20, 2025
**Base Path**: `/api/v1/local-users`

## Overview

The Local User Management API provides secure management of Linux system users on the server. This API allows administrators to create, delete, and manage local users directly from the Ops-Center interface.

**Security**: All endpoints require the **admin** role. All operations are logged to the audit trail.

## Architecture

### Components

1. **local_user_manager.py** - Core module with Linux user operations
   - Uses Python `subprocess` to execute system commands (`useradd`, `userdel`, `passwd`, etc.)
   - Implements security validations and sanitization
   - Protects system users and critical accounts

2. **local_user_api.py** - FastAPI endpoints
   - Exposes RESTful API for user management
   - Enforces admin role requirement
   - Logs all operations to audit trail

3. **local_user_audit table** - PostgreSQL audit log
   - Records all operations (success and failures)
   - Stores metadata and error messages
   - Indexed for efficient querying

### Security Measures

1. **Input Validation**
   - Username must match pattern: `^[a-z_][a-z0-9_-]{0,31}$`
   - Maximum length: 32 characters
   - Only lowercase, digits, underscore, hyphen allowed

2. **Protected Users**
   - System users (UID < 1000) are protected
   - Hardcoded list of critical users (root, daemon, postgres, etc.)
   - Current server admin users (muut, ucadmin) are protected

3. **SSH Key Validation**
   - Keys must be valid public key format
   - Supports: ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp*
   - Proper permissions set on .ssh directory and authorized_keys

4. **Command Injection Prevention**
   - All arguments checked for shell metacharacters
   - Subprocess called with list arguments (no shell=True)
   - Timeout protection (30 seconds)

5. **Authorization**
   - Only users with **admin** role can access endpoints
   - All operations require Keycloak SSO authentication
   - Session validation via Redis-backed sessions

6. **Audit Logging**
   - Every operation logged with username, performer, timestamp
   - Success/failure status recorded
   - Error messages and metadata stored
   - Searchable and exportable audit trail

## API Endpoints

### List Users

**GET** `/api/v1/local-users`

List all local Linux users (excluding system users by default).

**Query Parameters**:
- `include_system` (boolean, optional): Include system users (UID < 1000). Default: false

**Response**: Array of UserResponse objects

```json
[
  {
    "username": "john",
    "uid": 1001,
    "gid": 1001,
    "full_name": "John Doe",
    "home_dir": "/home/john",
    "shell": "/bin/bash",
    "groups": ["users", "docker"],
    "has_sudo": false,
    "home_size_bytes": 1048576,
    "is_system_user": false
  }
]
```

**Errors**:
- 401: Unauthorized (not authenticated)
- 403: Forbidden (not admin role)
- 500: Internal server error

---

### Get User

**GET** `/api/v1/local-users/{username}`

Get detailed information about a specific user.

**Path Parameters**:
- `username` (string, required): Username to query

**Response**: UserResponse object

```json
{
  "username": "john",
  "uid": 1001,
  "gid": 1001,
  "full_name": "John Doe",
  "home_dir": "/home/john",
  "shell": "/bin/bash",
  "groups": ["users", "docker"],
  "has_sudo": false,
  "home_size_bytes": 1048576,
  "is_system_user": false
}
```

**Errors**:
- 401: Unauthorized
- 403: Forbidden
- 404: User not found
- 500: Internal server error

---

### Create User

**POST** `/api/v1/local-users`

Create a new local Linux user.

**Request Body**:
```json
{
  "username": "john",
  "full_name": "John Doe",
  "shell": "/bin/bash",
  "create_home": true,
  "groups": ["docker", "users"],
  "password": "SecurePassword123!"
}
```

**Fields**:
- `username` (string, required): Username (lowercase, alphanumeric + underscore/hyphen)
- `full_name` (string, optional): Full name for GECOS field
- `shell` (string, optional): Login shell. Default: /bin/bash. Valid: /bin/bash, /bin/sh, /bin/zsh, /bin/dash, /usr/bin/fish
- `create_home` (boolean, optional): Create home directory. Default: true
- `groups` (array, optional): Additional groups to add user to
- `password` (string, optional): Initial password (min 8 characters)

**Response**: UserResponse object

**Errors**:
- 400: Invalid username or validation error
- 403: Security violation (protected user or UID < 1000)
- 500: User creation failed

---

### Delete User

**DELETE** `/api/v1/local-users/{username}`

Delete a local Linux user.

**WARNING**: This operation cannot be undone!

**Path Parameters**:
- `username` (string, required): Username to delete

**Query Parameters**:
- `remove_home` (boolean, optional): Also remove home directory. Default: false

**Response**:
```json
{
  "success": true,
  "message": "User john deleted successfully"
}
```

**Errors**:
- 400: User doesn't exist
- 403: Protected user or security violation
- 500: Deletion failed

---

### Set Password

**POST** `/api/v1/local-users/{username}/password`

Set password for a local user.

**Path Parameters**:
- `username` (string, required): Username

**Request Body**:
```json
{
  "password": "NewSecurePassword123!"
}
```

**Fields**:
- `password` (string, required): New password (min 8 characters)

**Response**:
```json
{
  "success": true,
  "message": "Password set for user john"
}
```

**Errors**:
- 400: Invalid password or user doesn't exist
- 403: Protected user
- 500: Password change failed

---

### List SSH Keys

**GET** `/api/v1/local-users/{username}/ssh-keys`

List all SSH public keys for a user.

**Path Parameters**:
- `username` (string, required): Username

**Response**: Array of SSHKeyResponse objects

```json
[
  {
    "type": "ssh-rsa",
    "fingerprint": "16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48",
    "comment": "john@laptop"
  }
]
```

**Errors**:
- 400: User doesn't exist
- 403: Protected user
- 500: Failed to read SSH keys

---

### Add SSH Key

**POST** `/api/v1/local-users/{username}/ssh-keys`

Add SSH public key to user's authorized_keys.

**Path Parameters**:
- `username` (string, required): Username

**Request Body**:
```json
{
  "ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB... john@laptop",
  "key_title": "John's Laptop"
}
```

**Fields**:
- `ssh_key` (string, required): Valid SSH public key
- `key_title` (string, optional): Title/comment for the key

**Response**:
```json
{
  "username": "john",
  "key_added": true,
  "key_fingerprint": "16:27:ac:a5:76:28:2d:36:63:1b:56:4d:eb:df:a6:48",
  "key_title": "John's Laptop"
}
```

**Errors**:
- 400: Invalid SSH key format or user doesn't exist
- 403: Protected user
- 500: Failed to add SSH key

---

### Remove SSH Key

**DELETE** `/api/v1/local-users/{username}/ssh-keys/{key_fingerprint}`

Remove SSH public key from user's authorized_keys.

**Path Parameters**:
- `username` (string, required): Username
- `key_fingerprint` (string, required): Fingerprint of key to remove (format: xx:xx:xx:...)

**Response**:
```json
{
  "success": true,
  "message": "SSH key removed for user john"
}
```

**Errors**:
- 400: Key not found or user doesn't exist
- 403: Protected user
- 500: Failed to remove SSH key

---

### Grant Sudo

**POST** `/api/v1/local-users/{username}/sudo`

Grant sudo permissions to a user.

**WARNING**: This gives the user full system access via sudo!

**Path Parameters**:
- `username` (string, required): Username

**Response**:
```json
{
  "success": true,
  "message": "Sudo permissions granted to user john"
}
```

**Errors**:
- 400: User doesn't exist
- 403: Protected user
- 500: Failed to grant sudo

---

### Revoke Sudo

**DELETE** `/api/v1/local-users/{username}/sudo`

Revoke sudo permissions from a user.

**Path Parameters**:
- `username` (string, required): Username

**Response**:
```json
{
  "success": true,
  "message": "Sudo permissions revoked from user john"
}
```

**Errors**:
- 400: User doesn't exist
- 403: Protected user
- 500: Failed to revoke sudo

---

## Audit Logging

All operations are logged to the `local_user_audit` PostgreSQL table with the following information:

- **action**: Type of operation (create_user, delete_user, etc.)
- **username**: Username operated on
- **performed_by**: Email of admin who performed the operation
- **keycloak_user_id**: Keycloak user ID of performer
- **success**: Whether operation succeeded
- **error_message**: Error message if failed
- **metadata**: Additional context (JSON)
- **client_ip**: IP address of client
- **user_agent**: User agent string
- **timestamp**: When operation occurred

### Query Audit Logs

```sql
-- Recent operations
SELECT * FROM local_user_audit ORDER BY timestamp DESC LIMIT 20;

-- Operations on specific user
SELECT * FROM local_user_audit WHERE username = 'john' ORDER BY timestamp DESC;

-- Failed operations
SELECT * FROM local_user_audit WHERE success = false ORDER BY timestamp DESC;

-- Operations by specific admin
SELECT * FROM local_user_audit WHERE performed_by = 'admin@example.com' ORDER BY timestamp DESC;

-- Sudo grants
SELECT * FROM local_user_audit WHERE action = 'sudo_grant' ORDER BY timestamp DESC;
```

## Error Handling

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Error Categories**:

1. **Validation Errors (400)**
   - Invalid username format
   - Username too long
   - Invalid SSH key format
   - User doesn't exist
   - User already exists

2. **Security Errors (403)**
   - Protected user operation attempted
   - System user operation attempted (UID < 1000)
   - Non-admin role

3. **System Errors (500)**
   - Command execution failed
   - Filesystem operation failed
   - Subprocess timeout

## Example Usage

### Create User with SSH Key

```bash
# 1. Create user
curl -X POST https://unicorncommander.ai/api/v1/local-users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john",
    "full_name": "John Doe",
    "create_home": true,
    "groups": ["docker", "users"]
  }'

# 2. Set password
curl -X POST https://unicorncommander.ai/api/v1/local-users/john/password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "SecurePassword123!"
  }'

# 3. Add SSH key
curl -X POST https://unicorncommander.ai/api/v1/local-users/john/ssh-keys \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAAB... john@laptop",
    "key_title": "John'\''s Laptop"
  }'

# 4. Grant sudo (if needed)
curl -X POST https://unicorncommander.ai/api/v1/local-users/john/sudo \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### List Users and SSH Keys

```bash
# List all users
curl https://unicorncommander.ai/api/v1/local-users \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get specific user
curl https://unicorncommander.ai/api/v1/local-users/john \
  -H "Authorization: Bearer YOUR_TOKEN"

# List SSH keys
curl https://unicorncommander.ai/api/v1/local-users/john/ssh-keys \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Delete User

```bash
# Delete user (keep home directory)
curl -X DELETE https://unicorncommander.ai/api/v1/local-users/john \
  -H "Authorization: Bearer YOUR_TOKEN"

# Delete user and home directory
curl -X DELETE "https://unicorncommander.ai/api/v1/local-users/john?remove_home=true" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Security Recommendations

1. **Principle of Least Privilege**
   - Only grant sudo when absolutely necessary
   - Review sudo users regularly

2. **SSH Key Management**
   - Use SSH keys instead of passwords when possible
   - Regularly audit and rotate SSH keys
   - Remove keys for departed users immediately

3. **Password Policy**
   - Enforce strong passwords (min 8 characters)
   - Consider password complexity requirements
   - Use password managers

4. **Audit Trail**
   - Regularly review audit logs
   - Set up alerts for sensitive operations
   - Export audit logs to SIEM for analysis

5. **User Lifecycle**
   - Document user provisioning process
   - Implement deprovisioning checklist
   - Backup home directories before deletion

## Troubleshooting

### Permission Denied Errors

If operations fail with permission denied:

1. Ensure ops-center backend has sudo permissions:
   ```bash
   # Check if backend user is in sudoers
   sudo -l -U ops-center
   ```

2. Configure passwordless sudo for backend user:
   ```bash
   # Add to /etc/sudoers.d/ops-center
   ops-center ALL=(ALL) NOPASSWD: /usr/sbin/useradd, /usr/sbin/userdel, /usr/sbin/usermod, /usr/bin/chpasswd, /usr/bin/gpasswd
   ```

### SSH Keys Not Working

If SSH key authentication fails after adding keys:

1. Check file permissions:
   ```bash
   ls -la /home/john/.ssh/
   # Should show:
   # drwx------ .ssh/
   # -rw------- authorized_keys
   ```

2. Verify key format:
   ```bash
   ssh-keygen -lf /home/john/.ssh/authorized_keys
   ```

3. Check SSH daemon logs:
   ```bash
   sudo journalctl -u ssh -f
   ```

### Audit Log Not Recording

If audit logs aren't being written:

1. Check database connection:
   ```bash
   docker exec ops-center-direct python3 -c "import psycopg2; conn = psycopg2.connect('postgresql://unicorn:unicorn@unicorn-postgresql/unicorn_db'); print('Connected')"
   ```

2. Verify table exists:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt local_user_audit"
   ```

3. Check backend logs:
   ```bash
   docker logs ops-center-direct | grep -i audit
   ```

## Future Enhancements

Planned features for future versions:

- [ ] Bulk user creation from CSV
- [ ] User expiration dates
- [ ] Disk quota management
- [ ] Group management endpoints
- [ ] User template system
- [ ] LDAP/AD synchronization
- [ ] Two-factor authentication setup
- [ ] Login history tracking
- [ ] Resource usage monitoring per user

## Support

For issues or questions:
- Check audit logs for error details
- Review backend logs: `docker logs ops-center-direct`
- Verify admin role assignment in Keycloak
- Open issue on GitHub: https://github.com/Unicorn-Commander/UC-Cloud

---

**Last Updated**: October 20, 2025
**Maintainer**: Ops-Center Backend Team
