# Local User Management API - Quick Reference

**Base URL**: `/api/v1/admin/system/local-users`
**Authentication**: Admin role required
**File**: `/opt/ops-center/backend/local_users_api.py`

---

## Quick Integration

```bash
cd /opt/ops-center/backend
./INTEGRATE_LOCAL_USERS_API.sh
docker restart ops-center-direct
```

---

## Endpoints at a Glance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | List all local users |
| POST | `/` | Create new user |
| GET | `/{username}` | Get user details |
| PUT | `/{username}` | Update user |
| DELETE | `/{username}` | Delete user |
| POST | `/{username}/password` | Reset password |
| GET | `/{username}/ssh-keys` | List SSH keys |
| POST | `/{username}/ssh-keys` | Add SSH key |
| DELETE | `/{username}/ssh-keys/{key_id}` | Remove SSH key |
| PUT | `/{username}/sudo` | Set sudo access |
| GET | `/groups` | List available groups |

---

## Common Examples

### List All Users (excluding system users)
```bash
curl http://localhost:8084/api/v1/admin/system/local-users \
  -H "Cookie: session=..."
```

### Create User with Auto-Generated Password
```bash
curl -X POST http://localhost:8084/api/v1/admin/system/local-users \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer1",
    "gecos": "Developer Account",
    "groups": ["docker"],
    "sudo_access": false
  }'

# Response includes: "generated_password": "SecureP@ss123..."
```

### Grant Sudo Access
```bash
curl -X PUT http://localhost:8084/api/v1/admin/system/local-users/developer1/sudo \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

### Add SSH Key
```bash
curl -X POST http://localhost:8084/api/v1/admin/system/local-users/developer1/ssh-keys \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{
    "ssh_key": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAbc... dev@workstation",
    "comment": "Work laptop"
  }'
```

---

## Password Requirements

- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character

Example valid password: `SecureP@ssw0rd123`

---

## Username Requirements

- Must start with lowercase letter
- Only lowercase letters, digits, hyphens, underscores
- Maximum 32 characters
- Matches pattern: `^[a-z][-a-z0-9_]{0,31}$`

Examples:
- ✓ `developer1`
- ✓ `test-user`
- ✓ `app_service`
- ✗ `9user` (starts with digit)
- ✗ `User1` (uppercase)
- ✗ `user@host` (invalid character)

---

## Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success (GET, PUT) |
| 201 | Created (POST create user) |
| 204 | No Content (DELETE) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (not logged in) |
| 403 | Forbidden (not admin) |
| 404 | Not Found (user/key doesn't exist) |
| 500 | Server Error (system command failed) |

---

## Security Notes

1. All operations require admin role
2. All actions are audit logged
3. Passwords are never returned (except auto-generated ones)
4. SSH keys are validated before adding
5. System users (UID < 1000) are hidden by default
6. Command injection protected via subprocess

---

## Troubleshooting

### "Authentication required"
- Ensure you're logged in and have a valid session cookie
- Check: `request.session.get("user_email")` is set

### "Admin privileges required"
- Verify your user has 'admin' role
- Check: `request.session.get("user_roles")` includes "admin"

### "Failed to create user: permission denied"
- Backend must have sudo privileges
- Check container has proper permissions

### "Password does not meet complexity requirements"
- See password requirements above
- Use auto-generated passwords for simplicity

### "Invalid SSH public key format"
- Ensure key starts with: ssh-rsa, ssh-ed25519, or ecdsa-*
- Include the full key string, not just the filename

---

## Audit Log Actions

All operations log these action types:

- `user.create` - User created
- `user.update` - User modified
- `user.delete` - User deleted
- `auth.password.reset` - Password changed
- `user.ssh_key.add` - SSH key added
- `user.ssh_key.remove` - SSH key removed
- `user.sudo.update` - Sudo access changed

View audit logs: `/api/v1/audit/logs?resource_type=local_user`

---

## Comparison with Existing API

| Feature | Old API (`/api/v1/local-users`) | New API (`/api/v1/admin/system/local-users`) |
|---------|--------------------------------|---------------------------------------------|
| Path | `/api/v1/local-users` | `/api/v1/admin/system/local-users` |
| Admin only | Yes | Yes |
| Create user | ✓ | ✓ |
| Delete user | ✓ | ✓ |
| SSH keys | ✓ (by fingerprint) | ✓ (by line ID) |
| Sudo mgmt | ✓ (POST/DELETE) | ✓ (PUT with enabled flag) |
| Groups list | ✗ | ✓ |
| User update | ✗ | ✓ (PUT endpoint) |
| Statistics | ✓ | ✗ |
| Password gen | ✗ | ✓ (auto-generate option) |
| Last login | ✗ | ✓ |
| GECOS field | ✓ | ✓ |

**Recommendation**: Keep both APIs for backward compatibility

---

## File Locations

- **API Implementation**: `backend/local_users_api.py` (NEW)
- **Old API**: `backend/local_user_api.py` (EXISTING)
- **Manager**: `backend/local_user_manager.py` (EXISTING)
- **Integration Script**: `backend/INTEGRATE_LOCAL_USERS_API.sh`
- **Full Documentation**: `backend/LOCAL_USER_API_IMPLEMENTATION.md`
- **This Quick Reference**: `backend/LOCAL_USER_API_QUICK_REFERENCE.md`

---

## Next Steps

1. Run integration script to add to server.py
2. Restart backend container
3. Test with curl or Postman
4. Build frontend UI (optional)
5. Add to admin navigation menu

---

**Status**: ✅ Ready for Production Use
**Last Updated**: October 23, 2025
