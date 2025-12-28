# Local User Management - Code Review Report

**Reviewer**: Code Review Agent
**Date**: October 20, 2025
**Session ID**: swarm-local-users
**Working Directory**: `/home/muut/Production/UC-Cloud/services/ops-center`

---

## Executive Summary

**STATUS**: ❌ **NOT IMPLEMENTED**

After thorough examination of the Ops-Center codebase, the Local User Management feature **has not been developed**. This was flagged as a planned feature but remains unimplemented.

---

## Review Findings

### 1. Documentation Review

**Sources Examined**:
- `SYSTEM_FEATURES_INVENTORY.md` (Lines 192-212)
- `MASTER_SECTION_CHECKLIST.md` (Lines 223-233)
- `services/ops-center/CLAUDE.md` (Ops-Center configuration)

**Findings from Documentation**:

From `SYSTEM_FEATURES_INVENTORY.md`:
```markdown
### Local User Management ⚠️ (PLANNED)

**Purpose**: Manage Linux system users on the server
**Use Cases**:
- Reset default user password after fresh install
- Create admin users for server access
- SSH key management
- Sudo permissions

**Routes** (planned):
- `/admin/system/local-users` - Local user management
- `/admin/system/ssh-keys` - SSH key management

**Backend** (planned):
- `local_user_manager.py` - Linux user CRUD
- `/api/v1/local-users/*` - User management APIs

**NOT YET IMPLEMENTED** ❌
```

From `MASTER_SECTION_CHECKLIST.md`:
```markdown
### 6.4 Local User Management ❌
**Status**: NOT IMPLEMENTED
**Route**: `/admin/system/local-users` (planned)
**Purpose**: Manage Linux system users on server
**Use Cases**:
- Reset default user password after fresh install
- Create admin users for server access
- SSH key management
- Sudo permissions
**Needs**: FULL IMPLEMENTATION (Priority)
```

### 2. Codebase Search Results

**Backend Search**:
- ❌ No `local_user*.py` files found
- ❌ No system user management commands (`useradd`, `userdel`, `usermod`) found in code
- ❌ No `/api/v1/local-users/` endpoints registered in `server.py`

**Frontend Search**:
- ❌ No `LocalUser*.jsx` components found
- ❌ No route for `/admin/system/local-users` in `App.jsx`
- ❌ No navigation links for local user management

**Files Examined**:
- `backend/server.py` - Main FastAPI application
- `src/App.jsx` - React routing configuration
- `src/components/Layout.jsx` - Navigation sidebar
- `src/pages/*.jsx` - All page components

**Only Related Finding**:
The term "local_user" appears in `backend/server.py` lines 3541-3887, but this refers to the **user creation workflow** (creating users in Keycloak/PostgreSQL), NOT Linux system user management.

```python
# This is NOT Linux user management - it's Keycloak user creation
local_user_created = False
local_user = auth_manager.create_user(user_create)  # Creates in Keycloak
```

### 3. Architecture Gap Analysis

**What Exists** (Keycloak User Management):
- ✅ User CRUD in Keycloak SSO
- ✅ Role-based access control
- ✅ API key management
- ✅ Session management
- ✅ OAuth/OIDC authentication

**What's Missing** (Linux System User Management):
- ❌ Linux user account creation (`useradd`)
- ❌ Password management (`passwd`, `chpasswd`)
- ❌ SSH key deployment to `~/.ssh/authorized_keys`
- ❌ Sudo configuration (`/etc/sudoers.d/`)
- ❌ User deletion (`userdel`)
- ❌ User modification (`usermod`, `gpasswd`)
- ❌ Home directory management

---

## Security Assessment

**GRADE**: N/A (Feature Not Implemented)

**Potential Security Risks** (If Implemented):

### CRITICAL Security Concerns for Future Implementation

1. **Command Injection** ⚠️⚠️⚠️
   - Risk: User inputs used directly in shell commands
   - Attack: `username="; rm -rf /"` could destroy system
   - Mitigation Required:
     - Use Python's `pwd` and `grp` modules instead of shell commands
     - Whitelist username characters (alphanumeric + underscore only)
     - Never concatenate user input into shell commands

2. **Privilege Escalation** ⚠️⚠️⚠️
   - Risk: Web service needs root access to create users
   - Attack: Compromise web service → root access
   - Mitigation Required:
     - Use `sudo` with specific commands only
     - Create dedicated service user with limited sudo privileges
     - Log all sudo operations
     - Example `/etc/sudoers.d/ops-center`:
       ```
       ops-center ALL=(ALL) NOPASSWD: /usr/sbin/useradd
       ops-center ALL=(ALL) NOPASSWD: /usr/sbin/userdel
       ops-center ALL=(ALL) NOPASSWD: /usr/sbin/usermod
       ```

3. **Path Traversal** ⚠️⚠️
   - Risk: SSH key uploads could write to arbitrary paths
   - Attack: Write SSH key to root's authorized_keys
   - Mitigation Required:
     - Validate home directory paths (`os.path.realpath()`)
     - Ensure paths start with `/home/`
     - Reject absolute paths in filenames

4. **System User Protection** ⚠️⚠️
   - Risk: Accidentally modify system users (uid < 1000)
   - Attack: Delete `root`, `postgres`, `docker` users
   - Mitigation Required:
     - Check UID before operations: `if uid < 1000: raise PermissionError`
     - Blacklist critical usernames: `root`, `daemon`, `bin`, etc.

5. **Authorization Bypass** ⚠️⚠️
   - Risk: Non-admin users could manage system users
   - Attack: Regular user creates admin account
   - Mitigation Required:
     - Enforce admin-only access at API level
     - Check Keycloak roles for every operation
     - Log all operations with user_id and IP address

6. **SSH Key Validation** ⚠️
   - Risk: Malformed SSH keys could break authentication
   - Attack: Upload invalid key → lock out legitimate users
   - Mitigation Required:
     - Validate SSH key format using `ssh-keygen -l -f`
     - Check key type (ed25519, rsa, ecdsa only)
     - Limit key size (RSA ≥ 2048 bits)

7. **Password Security** ⚠️
   - Risk: Weak passwords or password exposure
   - Mitigation Required:
     - Never log passwords (even hashed)
     - Use strong password requirements (zxcvbn)
     - Force password change on first login
     - Never return passwords in API responses

---

## Code Quality Assessment

**GRADE**: N/A (Not Implemented)

**Expected Code Structure** (If Implemented):

### Backend Module: `local_user_manager.py`

**Required Functions**:
```python
import pwd
import grp
import subprocess
from pathlib import Path
from typing import Optional, List, Dict
import re

class LocalUserManager:
    """Secure Linux system user management"""

    # Security constants
    MIN_UID = 1000  # Prevent system user modification
    USERNAME_PATTERN = re.compile(r'^[a-z_][a-z0-9_-]{0,31}$')
    SYSTEM_USERS = {'root', 'daemon', 'bin', 'sys', 'postgres', 'docker'}

    def validate_username(self, username: str) -> bool:
        """Validate username against security rules"""
        if username in self.SYSTEM_USERS:
            raise ValueError(f"Cannot modify system user: {username}")
        if not self.USERNAME_PATTERN.match(username):
            raise ValueError("Invalid username format")
        return True

    def get_user_uid(self, username: str) -> int:
        """Get UID safely using pwd module"""
        try:
            return pwd.getpwnam(username).pw_uid
        except KeyError:
            return -1

    def create_user(self, username: str, password: str,
                   ssh_key: Optional[str] = None,
                   sudo: bool = False) -> Dict:
        """
        Create Linux user with security checks

        SECURITY:
        - Validates username format
        - Uses subprocess with explicit args (no shell=True)
        - Logs all operations
        - Returns safe user info (no password)
        """
        self.validate_username(username)

        # Use explicit arguments - NEVER shell=True
        result = subprocess.run(
            ['/usr/sbin/useradd', '-m', '-s', '/bin/bash', username],
            capture_output=True,
            text=True,
            check=True
        )

        # Set password using chpasswd (stdin)
        subprocess.run(
            ['/usr/sbin/chpasswd'],
            input=f"{username}:{password}\n",
            text=True,
            check=True
        )

        if ssh_key:
            self._deploy_ssh_key(username, ssh_key)

        if sudo:
            self._grant_sudo(username)

        # Audit log
        audit_logger.log(
            action="user_created",
            user=username,
            metadata={"sudo": sudo, "ssh_key": bool(ssh_key)}
        )

        return {
            "username": username,
            "uid": self.get_user_uid(username),
            "home": f"/home/{username}",
            "sudo": sudo
            # NOTE: Never return password
        }

    def _deploy_ssh_key(self, username: str, ssh_key: str) -> None:
        """
        Deploy SSH key with path traversal protection

        SECURITY:
        - Validates home directory path
        - Creates .ssh with correct permissions (700)
        - authorized_keys with correct permissions (600)
        - Validates SSH key format
        """
        user_info = pwd.getpwnam(username)
        home_dir = Path(user_info.pw_dir)

        # Path traversal protection
        if not str(home_dir.resolve()).startswith('/home/'):
            raise ValueError("Invalid home directory")

        ssh_dir = home_dir / '.ssh'
        ssh_dir.mkdir(mode=0o700, exist_ok=True)

        # Validate SSH key format
        if not ssh_key.startswith(('ssh-rsa ', 'ssh-ed25519 ', 'ecdsa-')):
            raise ValueError("Invalid SSH key format")

        auth_keys = ssh_dir / 'authorized_keys'
        auth_keys.write_text(ssh_key + '\n')
        auth_keys.chmod(0o600)

        # Fix ownership
        subprocess.run(
            ['chown', '-R', f'{username}:{username}', str(ssh_dir)],
            check=True
        )
```

### Backend API: `local_user_api.py`

**Required Endpoints**:
```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, validator
import re

router = APIRouter(prefix="/api/v1/local-users", tags=["local-users"])

class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=32)
    password: str = Field(..., min_length=12)
    ssh_key: Optional[str] = None
    sudo: bool = False

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-z_][a-z0-9_-]{0,31}$', v):
            raise ValueError("Invalid username format")
        return v

    @validator('password')
    def validate_password(cls, v):
        # Use zxcvbn or similar
        if len(v) < 12:
            raise ValueError("Password must be ≥12 characters")
        return v

@router.post("/")
async def create_local_user(
    request: CreateUserRequest,
    current_user: User = Depends(require_admin)  # CRITICAL: Admin only
):
    """
    Create Linux system user

    SECURITY: Admin role required
    AUDIT: All operations logged
    """
    try:
        user_manager = LocalUserManager()
        result = user_manager.create_user(
            username=request.username,
            password=request.password,
            ssh_key=request.ssh_key,
            sudo=request.sudo
        )

        # Audit log
        audit_logger.log(
            action="create_local_user",
            user_id=current_user.id,
            metadata={
                "target_user": request.username,
                "sudo_granted": request.sudo
            }
        )

        return result
    except subprocess.CalledProcessError as e:
        raise HTTPException(500, f"User creation failed: {e.stderr}")
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.delete("/{username}")
async def delete_local_user(
    username: str,
    current_user: User = Depends(require_admin)
):
    """
    Delete Linux system user

    SECURITY:
    - Admin only
    - Prevents deletion of system users (uid < 1000)
    - Audit logged
    """
    user_manager = LocalUserManager()

    # Prevent system user deletion
    uid = user_manager.get_user_uid(username)
    if uid < 1000:
        raise HTTPException(403, "Cannot delete system user")

    subprocess.run(['/usr/sbin/userdel', '-r', username], check=True)

    audit_logger.log(
        action="delete_local_user",
        user_id=current_user.id,
        metadata={"target_user": username}
    )

    return {"message": f"User {username} deleted"}
```

### Frontend Component: `LocalUserManagement.jsx`

**Required Structure**:
```jsx
import React, { useState, useEffect } from 'react';
import {
  Box, Button, Table, TableHead, TableRow, TableCell,
  TableBody, IconButton, Dialog, DialogTitle, DialogContent,
  TextField, Switch, FormControlLabel, Alert
} from '@mui/material';
import { Delete, Edit, Key } from '@mui/icons-material';

export default function LocalUserManagement() {
  const [users, setUsers] = useState([]);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    sshKey: '',
    sudo: false
  });
  const [errors, setErrors] = useState({});

  useEffect(() => {
    fetchLocalUsers();
  }, []);

  const fetchLocalUsers = async () => {
    // GET /api/v1/local-users
    const response = await fetch('/api/v1/local-users', {
      credentials: 'include'
    });
    const data = await response.json();
    setUsers(data.users);
  };

  const validateForm = () => {
    const newErrors = {};

    // Username validation
    if (!/^[a-z_][a-z0-9_-]{0,31}$/.test(formData.username)) {
      newErrors.username = "Invalid username format";
    }

    // Password strength
    if (formData.password.length < 12) {
      newErrors.password = "Password must be ≥12 characters";
    }

    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords don't match";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreateUser = async () => {
    if (!validateForm()) return;

    const response = await fetch('/api/v1/local-users', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: formData.username,
        password: formData.password,
        ssh_key: formData.sshKey || null,
        sudo: formData.sudo
      })
    });

    if (response.ok) {
      setCreateDialogOpen(false);
      fetchLocalUsers();
      // Show success toast
    } else {
      const error = await response.json();
      // Show error toast
    }
  };

  const handleDeleteUser = async (username) => {
    if (!confirm(`Delete user ${username}? This cannot be undone.`)) return;

    await fetch(`/api/v1/local-users/${username}`, {
      method: 'DELETE',
      credentials: 'include'
    });

    fetchLocalUsers();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" mb={2}>
        <h2>Local User Management</h2>
        <Button
          variant="contained"
          onClick={() => setCreateDialogOpen(true)}
        >
          Create User
        </Button>
      </Box>

      <Alert severity="warning" sx={{ mb: 2 }}>
        Warning: This manages Linux system users on the server.
        Changes take effect immediately.
      </Alert>

      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Username</TableCell>
            <TableCell>UID</TableCell>
            <TableCell>Home Directory</TableCell>
            <TableCell>Sudo</TableCell>
            <TableCell>SSH Key</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {users.map(user => (
            <TableRow key={user.username}>
              <TableCell>{user.username}</TableCell>
              <TableCell>{user.uid}</TableCell>
              <TableCell>{user.home}</TableCell>
              <TableCell>{user.sudo ? 'Yes' : 'No'}</TableCell>
              <TableCell>{user.has_ssh_key ? 'Yes' : 'No'}</TableCell>
              <TableCell>
                <IconButton
                  size="small"
                  onClick={() => handleDeleteUser(user.username)}
                  disabled={user.uid < 1000}
                  title={user.uid < 1000 ? "Cannot delete system user" : "Delete user"}
                >
                  <Delete />
                </IconButton>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {/* Create User Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)}>
        <DialogTitle>Create Local User</DialogTitle>
        <DialogContent>
          {/* Form fields */}
        </DialogContent>
      </Dialog>
    </Box>
  );
}
```

---

## API Design Review

**GRADE**: N/A (Not Implemented)

**Expected Endpoints**:

```
POST   /api/v1/local-users                  # Create user
GET    /api/v1/local-users                  # List users
GET    /api/v1/local-users/{username}       # Get user details
DELETE /api/v1/local-users/{username}       # Delete user
PUT    /api/v1/local-users/{username}       # Update user (password, sudo)
POST   /api/v1/local-users/{username}/ssh   # Add SSH key
DELETE /api/v1/local-users/{username}/ssh   # Remove SSH key
POST   /api/v1/local-users/{username}/reset # Reset password
```

**Security Requirements**:
- ✅ All endpoints require `admin` role
- ✅ Prevent operations on system users (uid < 1000)
- ✅ Audit log all operations
- ✅ Never return passwords in responses
- ✅ Validate all inputs

---

## Integration Review

**GRADE**: N/A (Not Implemented)

**Required Integrations**:
1. Audit logging system (existing: `audit_logger.py`)
2. Role-based access control (existing: Keycloak integration)
3. Frontend routing (needs route in `App.jsx`)
4. Navigation menu (needs link in `Layout.jsx`)

---

## Recommendations

### BLOCKING ISSUES (Must Fix Before Implementation)

1. **Security Design** ⚠️⚠️⚠️ CRITICAL
   - [ ] Design privilege escalation strategy (sudo configuration)
   - [ ] Create service user with limited sudo permissions
   - [ ] Implement command injection prevention
   - [ ] Add system user protection (uid < 1000)

2. **Architecture Decision** ⚠️⚠️ HIGH
   - [ ] Decide: Run commands via `subprocess` or use system API?
   - [ ] Option A: Use Python `pwd`, `grp`, `spwd` modules (safer)
   - [ ] Option B: Use `subprocess` with sudo (requires careful design)
   - [ ] Recommendation: **Option A** (Python modules are safer)

3. **Audit Strategy** ⚠️⚠️ HIGH
   - [ ] Define what operations get logged
   - [ ] Design log retention policy
   - [ ] Implement alert for suspicious activity

### REQUIRED FEATURES

1. **Backend Module**: `backend/local_user_manager.py`
   - [ ] `create_user()` - Secure user creation
   - [ ] `delete_user()` - User deletion with safeguards
   - [ ] `update_user()` - Password/sudo changes
   - [ ] `list_users()` - Get non-system users (uid ≥ 1000)
   - [ ] `deploy_ssh_key()` - SSH key deployment
   - [ ] `remove_ssh_key()` - SSH key removal

2. **Backend API**: `backend/local_user_api.py`
   - [ ] 7 REST endpoints (create, read, update, delete, ssh, reset)
   - [ ] Pydantic models for request/response validation
   - [ ] Admin-only authorization middleware
   - [ ] Comprehensive error handling

3. **Frontend Page**: `src/pages/LocalUserManagement.jsx`
   - [ ] User list table
   - [ ] Create user modal with validation
   - [ ] Delete user confirmation dialog
   - [ ] SSH key upload/display
   - [ ] Password reset form

4. **Frontend Route**: Add to `src/App.jsx`
   - [ ] Route: `/admin/system/local-users`
   - [ ] Component: `LocalUserManagement`

5. **Navigation**: Add to `src/components/Layout.jsx`
   - [ ] Add "Local Users" link under System section
   - [ ] Icon: PersonAdd or similar

### NICE-TO-HAVES (Optional Enhancements)

1. **User Groups** (LOW priority)
   - Manage `/etc/group` and group membership
   - Useful for shared folder permissions

2. **Password Policies** (MEDIUM priority)
   - Enforce password complexity
   - Force password change on first login
   - Password expiration

3. **Batch Operations** (LOW priority)
   - Create multiple users from CSV
   - Bulk SSH key deployment

4. **Shell Selection** (LOW priority)
   - Allow choosing user shell (bash, zsh, sh)
   - Currently hardcoded to `/bin/bash`

5. **Home Directory Quotas** (LOW priority)
   - Set disk space quotas per user
   - Requires `quota` package

---

## Severity Assessment

| Category | Severity | Count | Items |
|----------|----------|-------|-------|
| Security | CRITICAL | 3 | Command injection, privilege escalation, path traversal |
| Security | HIGH | 2 | System user protection, authorization |
| Security | MEDIUM | 2 | SSH key validation, password security |
| Implementation | BLOCKING | 2 | Security design, architecture decision |
| Implementation | REQUIRED | 5 | Backend module, API, frontend, routing, navigation |

---

## Final Verdict

**Implementation Status**: ❌ **NOT IMPLEMENTED**

**Complexity**: HIGH (Security-critical feature requiring careful design)

**Estimated Effort**: 16-24 hours for complete implementation with security review

**Priority**: HIGH (Documented as critical missing feature in roadmap)

**Recommendation**:
1. **DO NOT rush implementation** - Security is paramount
2. Start with security architecture design document
3. Implement with code review by security expert
4. Test thoroughly in isolated environment before production
5. Consider whether this feature is truly needed (vs. manual SSH access)

**Alternative Consideration**:
Instead of implementing this feature, consider:
- Providing documentation for manual user creation
- Using configuration management tools (Ansible, Puppet)
- Relying on cloud provider IAM (if deployed on AWS/GCP/Azure)

This feature adds significant security risk and maintenance burden. Evaluate carefully whether the benefit outweighs the risk.

---

## Appendices

### Appendix A: Security Checklist for Implementation

- [ ] Input validation (username, password, SSH key)
- [ ] Command injection prevention (no `shell=True`)
- [ ] Path traversal prevention (validate home directories)
- [ ] System user protection (uid < 1000 check)
- [ ] Authorization enforcement (admin role required)
- [ ] Audit logging (who did what, when)
- [ ] Password handling (never logged, never returned)
- [ ] SSH key format validation
- [ ] Sudo configuration security
- [ ] Error message sanitization (don't leak system info)

### Appendix B: Testing Strategy

**Unit Tests**:
- Test username validation (valid/invalid formats)
- Test system user protection (reject uid < 1000)
- Test path traversal prevention
- Test SSH key validation
- Test password strength requirements

**Integration Tests**:
- Test user creation end-to-end
- Test SSH key deployment
- Test sudo privilege assignment
- Test audit log generation
- Test error handling

**Security Tests**:
- Test command injection attempts
- Test authorization bypass attempts
- Test path traversal attacks
- Test SQL injection (if database used)

**Manual Tests**:
- Create user and verify can SSH
- Delete user and verify cleanup
- Reset password and verify new password works
- Deploy SSH key and verify key-based login

### Appendix C: Related Documentation

- **System Features Inventory**: `/services/ops-center/SYSTEM_FEATURES_INVENTORY.md`
- **Master Section Checklist**: `/services/ops-center/MASTER_SECTION_CHECKLIST.md`
- **Ops-Center Configuration**: `/services/ops-center/CLAUDE.md`
- **UC-Cloud Overview**: `/home/muut/Production/UC-Cloud/CLAUDE.md`

---

**Review Complete**: October 20, 2025
**Reviewer**: Code Review Agent
**Conclusion**: Feature not implemented. Provided comprehensive implementation guide with security focus.
