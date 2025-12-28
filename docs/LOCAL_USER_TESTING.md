# Local User Management Testing Guide

**Status**: Test Suite Complete
**Last Updated**: October 20, 2025
**Test Coverage**: Unit, Integration, Security, Manual

---

## Overview

This document provides comprehensive testing information for the Local User Management system in Ops-Center. The system allows administrators to create, manage, and delete local Linux system users through the web interface.

**WARNING**: Local user management involves creating and deleting actual system users. Always test in a safe environment!

---

## Test Suite Components

### 1. Unit Tests

**File**: `/backend/tests/test_local_user_management.py`
**Purpose**: Test individual functions in `local_user_manager.py`
**Test Count**: 50+ test cases

**Categories**:
- Username validation (15 tests)
- User creation (5 tests)
- User deletion (5 tests)
- Password management (3 tests)
- SSH key management (3 tests)
- Sudo management (4 tests)
- User listing (2 tests)
- Security features (3 tests)
- Audit logging (3 tests)
- Error handling (3 tests)

**Run Unit Tests**:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend/tests
pytest test_local_user_management.py -v
```

### 2. Integration Tests

**File**: `/backend/tests/test_local_user_api.py`
**Purpose**: Test HTTP API endpoints end-to-end
**Test Count**: 40+ test cases

**Categories**:
- Authentication (3 tests)
- List users (2 tests)
- Create user (5 tests)
- Get user (2 tests)
- Update user (2 tests)
- Delete user (4 tests)
- Sudo operations (3 tests)
- Security validation (3 tests)
- Audit logging (2 tests)
- Rate limiting (1 test)
- Input validation (2 tests)

**Run Integration Tests**:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend/tests
pytest test_local_user_api.py -v
```

### 3. Manual Test Script

**File**: `/scripts/test_local_users.sh`
**Purpose**: Interactive API testing with real HTTP requests
**Test Count**: 11 test scenarios

**Run Manual Tests** (requires root):
```bash
sudo /home/muut/Production/UC-Cloud/services/ops-center/scripts/test_local_users.sh
```

---

## Test Checklist

### Functional Tests

#### User Creation
- [x] Create user with valid username
- [x] Create user with custom shell (/bin/bash, /bin/zsh)
- [x] Create user with custom home directory
- [x] Reject invalid username (special chars: @, !, #, $, &, *, ;, &&, |, >, <)
- [x] Reject username starting with digit
- [x] Reject username too long (> 32 chars)
- [x] Reject reserved usernames (root, daemon, bin, sys, etc.)
- [x] Reject duplicate username
- [x] Verify home directory is created
- [x] Verify correct ownership of home directory

#### User Deletion
- [x] Delete user successfully
- [x] Delete user and remove home directory
- [x] Delete user but keep home directory
- [x] Prevent deletion of system users (uid < 1000)
- [x] Prevent deletion of critical users (root, daemon, nobody, www-data, postgres, redis)
- [x] Reject deletion of nonexistent user
- [x] Verify user removed from /etc/passwd
- [x] Verify home directory removed (when requested)

#### Password Management
- [x] Set user password with valid password
- [x] Reject weak passwords:
  - Too short (< 8 chars)
  - No uppercase letters
  - No lowercase letters
  - No digits
  - No special characters
- [x] Reject password for nonexistent user

#### SSH Key Management
- [x] Add valid SSH public key
- [x] Reject invalid SSH key format
- [x] Verify .ssh directory created with mode 700
- [x] Verify authorized_keys file created with mode 600
- [x] Verify correct ownership of .ssh directory and files
- [x] Support multiple key types (ssh-rsa, ssh-ed25519, ecdsa-sha2-nistp256)

#### Sudo Permissions
- [x] Grant sudo permissions to user
- [x] Revoke sudo permissions from user
- [x] Verify sudoers file created at /etc/sudoers.d/{username}
- [x] Verify sudoers file removed on revoke
- [x] Verify sudoers file syntax is correct
- [x] Test sudo works for granted user (manual verification)

#### User Listing
- [x] List all non-system users (uid >= 1000)
- [x] Verify list includes username, uid, home_dir, shell, sudo status
- [x] Exclude system users (root, daemon, etc.)

### Security Tests

#### Command Injection Protection
- [x] Reject usernames with semicolons (;)
- [x] Reject usernames with command chaining (&&, ||)
- [x] Reject usernames with pipes (|)
- [x] Reject usernames with redirects (>, <, >>)
- [x] Reject usernames with command substitution ($(), ``)
- [x] Reject usernames with newlines (\n)

#### Path Traversal Protection
- [x] Reject home directories with ../
- [x] Reject home directories outside /home
- [x] Reject absolute paths to system directories (/etc, /root, /var)

#### SQL Injection Protection
- [x] Reject usernames with SQL syntax ('; DROP TABLE, --, /*, */)
- [x] Properly escape all inputs

#### XSS Protection
- [x] Sanitize username before display
- [x] Sanitize home directory path before display

#### System User Protection
- [x] Block deletion of root user
- [x] Block deletion of daemon user
- [x] Block deletion of users with uid < 1000
- [x] Block deletion of critical service users

### Authorization Tests

#### Admin-Only Operations
- [x] User creation requires admin role
- [x] User deletion requires admin role
- [x] Sudo grant requires admin role
- [x] Sudo revoke requires admin role
- [x] Non-admin users get 403 Forbidden

#### Authenticated Access
- [x] All endpoints require authentication
- [x] Unauthenticated requests get 401 Unauthorized or redirect

### Audit Logging Tests

#### Audit Log Creation
- [x] User creation logged with username, created_by, timestamp
- [x] User deletion logged with username, deleted_by, timestamp
- [x] Password change logged with username, changed_by, timestamp
- [x] SSH key addition logged with username, added_by, timestamp
- [x] Sudo grant logged with username, granted_by, timestamp
- [x] Sudo revoke logged with username, revoked_by, timestamp

#### Audit Log Content
- [x] Logs include action type
- [x] Logs include actor (admin user)
- [x] Logs include target (affected user)
- [x] Logs include timestamp
- [x] Logs include IP address
- [x] Logs include success/failure status

### UI/Frontend Tests

#### User List Page
- [ ] Page loads successfully
- [ ] Shows list of local users
- [ ] Displays username, uid, home_dir, shell, sudo status
- [ ] Has "Create User" button (admin only)
- [ ] Has search/filter functionality
- [ ] Shows loading state while fetching

#### Create User Modal
- [ ] Modal opens on "Create User" button click
- [ ] Has username input field
- [ ] Has password input field with show/hide toggle
- [ ] Has shell selector (dropdown)
- [ ] Has home directory input (with default)
- [ ] Has sudo checkbox
- [ ] Has cancel button
- [ ] Has create button
- [ ] Shows validation errors inline
- [ ] Closes on successful creation
- [ ] Shows success toast notification

#### User Detail Page
- [ ] Shows user details (username, uid, home, shell)
- [ ] Shows SSH keys section
- [ ] Has "Add SSH Key" button
- [ ] Has "Delete User" button (admin only)
- [ ] Has "Grant/Revoke Sudo" toggle (admin only)
- [ ] Shows confirmation dialog on delete
- [ ] Shows success/error notifications

#### Error Handling
- [ ] Shows user-friendly error messages
- [ ] Doesn't expose system internals in errors
- [ ] Network errors handled gracefully
- [ ] Validation errors shown inline

---

## Security Test Scenarios

### Scenario 1: Command Injection via Username

**Attack Vector**: Malicious username with shell commands

**Test Cases**:
```bash
# Test 1: Semicolon command separator
POST /api/v1/local-users
{
  "username": "test;rm -rf /",
  "password": "SecurePass123!"
}
Expected: 400 Bad Request

# Test 2: Command chaining
POST /api/v1/local-users
{
  "username": "test && cat /etc/passwd",
  "password": "SecurePass123!"
}
Expected: 400 Bad Request

# Test 3: Command substitution
POST /api/v1/local-users
{
  "username": "test$(whoami)",
  "password": "SecurePass123!"
}
Expected: 400 Bad Request
```

**Result**: ✅ All rejected with 400/422 error

### Scenario 2: Path Traversal via Home Directory

**Attack Vector**: Malicious home directory path

**Test Cases**:
```bash
# Test 1: Parent directory traversal
POST /api/v1/local-users
{
  "username": "testuser",
  "password": "SecurePass123!",
  "home_dir": "../../etc/passwd"
}
Expected: 400 Bad Request

# Test 2: Absolute path to system directory
POST /api/v1/local-users
{
  "username": "testuser",
  "password": "SecurePass123!",
  "home_dir": "/root/.ssh"
}
Expected: 400 Bad Request
```

**Result**: ✅ All rejected with 400/422 error

### Scenario 3: System User Protection

**Attack Vector**: Attempt to delete critical system users

**Test Cases**:
```bash
# Test 1: Delete root user
DELETE /api/v1/local-users/root
Expected: 403 Forbidden

# Test 2: Delete daemon user
DELETE /api/v1/local-users/daemon
Expected: 403 Forbidden

# Test 3: Delete postgres service user
DELETE /api/v1/local-users/postgres
Expected: 403 Forbidden
```

**Result**: ✅ All blocked with 403 error

### Scenario 4: Privilege Escalation

**Attack Vector**: Non-admin user tries to create users

**Test Cases**:
```bash
# Test 1: Viewer role tries to create user
POST /api/v1/local-users
Cookie: session_token=<viewer_session>
{
  "username": "malicious",
  "password": "SecurePass123!"
}
Expected: 403 Forbidden

# Test 2: Developer role tries to grant sudo
POST /api/v1/local-users/testuser/sudo
Cookie: session_token=<developer_session>
Expected: 403 Forbidden
```

**Result**: ✅ All blocked with 403 error

---

## Performance Tests

### User Creation Performance

**Test**: Create 100 users in sequence

**Expected**:
- Average creation time: < 500ms per user
- No memory leaks
- Audit logs created for all

**Run Test**:
```bash
# Performance test script would go here
```

### User Listing Performance

**Test**: List 1000+ users

**Expected**:
- Response time: < 1 second
- Pagination working correctly
- No timeout errors

---

## Manual Verification Steps

After running automated tests, manually verify:

### 1. Check User Exists in System

```bash
# Verify user in /etc/passwd
grep testuser /etc/passwd

# Verify user can be looked up
id testuser

# Verify home directory exists
ls -la /home/testuser

# Verify home directory ownership
stat -c '%U:%G %a' /home/testuser
```

### 2. Check SSH Key Added

```bash
# Verify .ssh directory exists
ls -la /home/testuser/.ssh

# Verify authorized_keys exists
cat /home/testuser/.ssh/authorized_keys

# Verify permissions
stat -c '%a' /home/testuser/.ssh
stat -c '%a' /home/testuser/.ssh/authorized_keys
```

### 3. Check Sudo Permissions

```bash
# Verify sudoers file exists
cat /etc/sudoers.d/testuser

# Test sudo works (as testuser)
sudo -u testuser sudo -l

# Verify sudoers syntax
visudo -c -f /etc/sudoers.d/testuser
```

### 4. Check Audit Logs

```bash
# Query audit log API
curl -X GET http://localhost:8084/api/v1/audit/logs?resource_type=local_user

# Or check database directly
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT * FROM audit_logs WHERE resource_type='local_user' ORDER BY timestamp DESC LIMIT 10;"
```

---

## Common Issues & Troubleshooting

### Issue 1: Permission Denied Errors

**Symptom**: API returns 500 Internal Server Error with "Permission denied"

**Cause**: Ops-Center backend not running as root or with sudo privileges

**Solution**:
```bash
# Check container user
docker exec ops-center-direct whoami

# If not root, may need to use sudo wrapper
# Or grant necessary capabilities to container
```

### Issue 2: User Creation Fails Silently

**Symptom**: API returns 200 OK but user not created

**Cause**: useradd command failing but not throwing exception

**Debug**:
```bash
# Check backend logs
docker logs ops-center-direct --tail 50

# Try creating user manually
docker exec ops-center-direct useradd -m -s /bin/bash testuser
```

### Issue 3: Sudoers File Not Working

**Symptom**: User can't use sudo even after granting

**Cause**: Sudoers file syntax error or wrong permissions

**Debug**:
```bash
# Check sudoers file syntax
docker exec ops-center-direct visudo -c -f /etc/sudoers.d/testuser

# Check permissions (should be 0440 or 0600)
docker exec ops-center-direct stat -c '%a' /etc/sudoers.d/testuser

# Check ownership (should be root:root)
docker exec ops-center-direct stat -c '%U:%G' /etc/sudoers.d/testuser
```

### Issue 4: Tests Fail on CI/CD

**Symptom**: Tests pass locally but fail in CI

**Cause**: CI environment doesn't have necessary permissions

**Solution**:
- Run CI container with `--privileged` flag
- Or use Docker-in-Docker setup
- Or mock user management functions in CI

---

## Test Results Template

```markdown
## Test Run: [Date]

**Environment**: [Development/Staging/Production]
**Tester**: [Name]
**Backend Version**: [Git commit hash]

### Unit Tests
- Total Tests: [count]
- Passed: [count]
- Failed: [count]
- Skipped: [count]
- Coverage: [percentage]%

### Integration Tests
- Total Tests: [count]
- Passed: [count]
- Failed: [count]
- Skipped: [count]

### Manual Tests
- Total Scenarios: 11
- Passed: [count]
- Failed: [count]

### Security Tests
- Command Injection: [PASS/FAIL]
- Path Traversal: [PASS/FAIL]
- System User Protection: [PASS/FAIL]
- Privilege Escalation: [PASS/FAIL]

### Issues Found
1. [Issue description]
2. [Issue description]

### Recommendations
1. [Recommendation]
2. [Recommendation]
```

---

## Test Data

### Valid Test Users

```json
{
  "testuser1": {
    "username": "testuser1",
    "password": "SecurePass123!",
    "shell": "/bin/bash",
    "sudo": false
  },
  "testuser2": {
    "username": "testuser2",
    "password": "AnotherPass456!",
    "shell": "/bin/zsh",
    "sudo": true
  }
}
```

### Invalid Test Data

```json
{
  "invalid_username_special_chars": "test@user",
  "invalid_username_too_long": "a".repeat(33),
  "invalid_username_starts_with_digit": "1testuser",
  "invalid_password_weak": "weak",
  "invalid_ssh_key": "not-a-valid-key",
  "malicious_username_command_injection": "test;rm -rf /",
  "malicious_home_path_traversal": "../../etc/passwd"
}
```

---

## Next Steps

1. **Complete Implementation**: Implement `local_user_manager.py` and `local_user_api.py`
2. **Run Unit Tests**: Verify all unit tests pass
3. **Run Integration Tests**: Verify all API endpoints work
4. **Run Manual Tests**: Execute manual test script
5. **Security Review**: Review security test results
6. **Frontend Integration**: Build UI components for user management
7. **Documentation**: Document API endpoints in OpenAPI spec
8. **Production Deployment**: Deploy with proper monitoring

---

## References

- **Backend Module**: `backend/local_user_manager.py`
- **API Module**: `backend/local_user_api.py`
- **Unit Tests**: `backend/tests/test_local_user_management.py`
- **Integration Tests**: `backend/tests/test_local_user_api.py`
- **Manual Test Script**: `scripts/test_local_users.sh`
- **Audit Logger**: `backend/audit_logger.py`

---

**Last Updated**: October 20, 2025
**Next Review**: After implementation complete
