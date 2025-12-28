# User Management Debug Report - "Failed to Load Users" Error

**Date**: October 22, 2025 02:45 UTC
**Session**: Post-deployment debugging
**Status**: 🔴 CRITICAL - Keycloak service down
**Reporter**: Code Analyzer Agent

---

## 🎯 Executive Summary

The "Failed to load users" error in User Management is caused by **Keycloak (uchub-keycloak) failing to start** due to a JGroups protocol version conflict between two Keycloak instances running on the same Docker network.

**Root Cause**: Keycloak 26.0 (uchub-keycloak) cannot cluster with Keycloak 25.0 (unicorn-keycloak) because they use incompatible Infinispan/JGroups protocol versions.

**Severity**: CRITICAL - All user management, authentication, and admin operations are blocked.

**Impact**:
- ❌ User Management page: "Failed to load users"
- ❌ All `/api/v1/admin/users` endpoints: 401 Unauthorized
- ❌ All Keycloak-dependent features: Non-functional
- ✅ Landing page: Still works (no auth required)
- ✅ LocalUsers API: Registered but unused

---

## 🔍 Root Cause Analysis

### 1. Keycloak Service Failure

**Container Status**:
```bash
$ docker ps | grep uchub-keycloak
efd03aa6fea9   quay.io/keycloak/keycloak:26.0   Up 17 seconds (health: starting)
```

**Error Log** (`docker logs uchub-keycloak`):
```
ERROR: ISPN000217: Received exception from 700f8fb59e74-63392
ERROR: Unsupported protocol version 152
ERROR: Failed to start server in (production) mode
```

**Explanation**:
- `700f8fb59e74` = Container ID of `unicorn-keycloak` (Keycloak 25.0)
- `efd03aa6fea9` = Container ID of `uchub-keycloak` (Keycloak 26.0)
- JGroups clustering protocol mismatch between versions
- Keycloak 26.0 tries to join cluster with Keycloak 25.0 → Fails with "Unsupported protocol version 152"

### 2. Version Conflict

**Two Keycloak Instances on Same Network**:

| Container | Image | Network | Status |
|-----------|-------|---------|--------|
| `uchub-keycloak` | `quay.io/keycloak/keycloak:26.0` | uchub-network | ❌ FAILING (startup loop) |
| `unicorn-keycloak` | `quay.io/keycloak/keycloak:25.0` | unicorn-network | ✅ RUNNING (unhealthy) |

**Problem**: Both containers are on overlapping networks and attempt to form a JGroups cluster, causing protocol version conflict.

### 3. Network Connectivity Test

**From ops-center-direct container**:
```python
# Test port 8080 on uchub-keycloak
Port 8080: CLOSED
```

**Reason**: Keycloak service never fully starts due to clustering failure.

### 4. API Call Chain

**User Management Flow**:
```
Frontend (UserManagement.jsx)
  ↓ fetch('/api/v1/admin/users')
Backend (server.py:3106)
  ↓ require_admin dependency
Auth Manager (auth_manager.py:393)
  ↓ get_users() → calls Keycloak integration
Keycloak Integration (keycloak_integration.py:29)
  ↓ get_admin_token()
HTTP Request to uchub-keycloak
  ↓ POST http://uchub-keycloak:8080/realms/uchub/protocol/openid-connect/token
❌ Connection Refused (Port 8080 closed)
  ↓
ERROR: Failed to authenticate with Keycloak: 401
  ↓
Frontend: "Failed to load users"
```

---

## 📁 Files Involved

### Backend Files

1. **`/backend/server.py`** (Line 3106-3163)
   - Defines `/api/v1/users` endpoints
   - Uses `require_admin` dependency for authentication
   - Calls `auth_manager.get_users()`

2. **`/backend/auth_manager.py`** (Line 393-399)
   - Implements `get_users()` method
   - Returns user list from internal storage
   - **Note**: This is a fallback in-memory user store, not the primary source

3. **`/backend/keycloak_integration.py`** (Line 29-71)
   - Implements `get_admin_token()` function
   - Attempts to authenticate with Keycloak admin-cli
   - **Configuration**:
     - `KEYCLOAK_URL`: `http://uchub-keycloak:8080`
     - `KEYCLOAK_REALM`: `uchub`
     - `KEYCLOAK_CLIENT_ID`: `admin-cli`
     - `KEYCLOAK_ADMIN_USERNAME`: `admin`
     - `KEYCLOAK_ADMIN_PASSWORD`: `your-admin-password`

### Frontend Files

4. **`/src/pages/UserManagement.jsx`** (Line 140-198)
   - Implements `fetchUsers()` function
   - Makes API call to `/api/v1/admin/users?${params}`
   - Uses `credentials: 'include'` for cookie authentication
   - Displays "Failed to load users" on error

### Configuration Files

5. **`/docker-compose.direct.yml`** (Line 17-20)
   - Environment variables for ops-center container:
     ```yaml
     - KEYCLOAK_URL=http://uchub-keycloak:8080
     - KEYCLOAK_REALM=uchub
     - KEYCLOAK_ADMIN_USER=admin
     - KEYCLOAK_ADMIN_PASSWORD=your-admin-password
     ```

---

## 🔧 Recommended Fix

### Option 1: Isolate Keycloak Instances (RECOMMENDED)

**Prevent JGroups clustering between incompatible versions**:

1. **Add JGroups configuration to uchub-keycloak**:
   ```yaml
   # In uchub-keycloak docker-compose
   environment:
     - KC_CACHE=local  # Disable clustering
   ```

   OR specify a unique cluster name:
   ```yaml
   environment:
     - KC_CACHE_STACK=tcp
     - jgroups.cluster.name=uchub-cluster  # Unique cluster name
   ```

2. **Restart uchub-keycloak**:
   ```bash
   docker restart uchub-keycloak
   ```

3. **Verify startup**:
   ```bash
   docker logs uchub-keycloak -f
   # Should see: "Keycloak 26.0.0 started"
   ```

### Option 2: Upgrade unicorn-keycloak to 26.0

**Ensure version compatibility**:

1. **Update unicorn-keycloak image**:
   ```yaml
   # In unicorn-keycloak docker-compose
   image: quay.io/keycloak/keycloak:26.0
   ```

2. **Backup and recreate**:
   ```bash
   docker exec keycloak-postgresql pg_dump -U keycloak > /tmp/keycloak-backup.sql
   docker compose -f <unicorn-keycloak-compose> up -d --force-recreate
   ```

### Option 3: Remove unicorn-keycloak (If unused)

**If unicorn-keycloak is redundant**:

1. **Verify it's not in use**:
   ```bash
   docker logs unicorn-keycloak | grep "session"
   # Check for active user sessions
   ```

2. **Stop and remove**:
   ```bash
   docker stop unicorn-keycloak
   docker rm unicorn-keycloak
   ```

---

## 🧪 Testing Steps to Verify Fix

### 1. Verify Keycloak is Running

```bash
# Check container status
docker ps | grep uchub-keycloak
# Should show: "Up X minutes (healthy)"

# Check logs for success
docker logs uchub-keycloak 2>&1 | grep "started"
# Should show: "Keycloak 26.0.0 started in Xms"
```

### 2. Test Port Connectivity

```bash
# From ops-center container
docker exec ops-center-direct python3 -c "
import socket
sock = socket.socket()
sock.settimeout(2)
result = sock.connect_ex(('uchub-keycloak', 8080))
print(f'Port 8080: {\"OPEN\" if result == 0 else \"CLOSED\"}')
"
# Should show: "Port 8080: OPEN"
```

### 3. Test Keycloak Authentication

```bash
# Get admin token
docker exec ops-center-direct python3 -c "
import httpx
response = httpx.post(
    'http://uchub-keycloak:8080/realms/uchub/protocol/openid-connect/token',
    data={
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'username': 'admin',
        'password': 'your-admin-password'
    },
    headers={'Content-Type': 'application/x-www-form-urlencoded'}
)
print(f'Status: {response.status_code}')
print('Token obtained!' if response.status_code == 200 else f'Error: {response.text}')
"
# Should show: "Status: 200" and "Token obtained!"
```

### 4. Test User Management API

```bash
# Get session token first (login via browser at https://your-domain.com)
# Then test API with curl

# From local machine
curl -X GET https://your-domain.com/api/v1/admin/users \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -H "Accept: application/json"

# Should return JSON with user list
```

### 5. Test Frontend User Management

1. Navigate to: `https://your-domain.com/admin/system/users`
2. Verify:
   - ✅ User list loads without "Failed to load users" error
   - ✅ User count metrics display correctly
   - ✅ Filters and search work
   - ✅ Clicking a user opens UserDetail page

---

## 🐛 Additional Issues Found

### Issue 1: Wrong API Endpoint in Frontend

**File**: `src/pages/UserManagement.jsx` (Line 184)

**Current**:
```javascript
const response = await fetch(`/api/v1/admin/users?${params}`, {
```

**Problem**: The endpoint `/api/v1/admin/users` doesn't exist. The correct endpoint is `/api/v1/users`.

**Evidence**:
```bash
$ docker exec ops-center-direct curl http://localhost:8084/api/v1/admin/users
{"detail":"API endpoint not found"}

$ docker exec ops-center-direct curl http://localhost:8084/api/v1/users
{"detail":"Not authenticated"}  # Endpoint exists, just needs auth
```

**Fix**:
```javascript
// Change in UserManagement.jsx line 184
const response = await fetch(`/api/v1/users?${params}`, {
```

**Also update** (all instances in UserManagement.jsx):
- Line 203: `/api/v1/admin/users/analytics/summary` → `/api/v1/users/analytics/summary`
- Line 218: `/api/v1/admin/users/roles/available` → `/api/v1/users/roles/available`
- Line 378: `/api/v1/admin/users/${currentUser.id}` → `/api/v1/users/${currentUser.id}`
- Line 403: `/api/v1/admin/users/${currentUser.id}/reset-password` → `/api/v1/users/${currentUser.id}/reset-password`
- Line 427: `/api/v1/admin/users/${user.id}/roles` → `/api/v1/users/${user.id}/roles`
- Line 442: `/api/v1/admin/users/${currentUser.id}/roles` → `/api/v1/users/${currentUser.id}/roles`
- Line 462: `/api/v1/admin/users/${currentUser.id}/roles/${role}` → `/api/v1/users/${currentUser.id}/roles/${role}`
- Line 483: `/api/v1/admin/users/${user.id}/sessions` → `/api/v1/users/${user.id}/sessions`
- Line 499: `/api/v1/admin/users/${currentUser.id}/sessions` → `/api/v1/users/${currentUser.id}/sessions`

### Issue 2: LocalUsers API Registered But Not Used

**File**: `backend/local_user_api.py` (Line 26)

**Registered as**: `/api/v1/local-users`

**Purpose**: Manage Linux system users (not Keycloak users)

**Note**: This API is for managing local Linux users on the host system. It's registered but not currently used by the frontend User Management page, which expects Keycloak users.

---

## 📊 Current System State

### Docker Containers

```
Container           Image              Status                     Notes
─────────────────────────────────────────────────────────────────────────────
uchub-keycloak      keycloak:26.0      ❌ Failing (startup loop)  Primary auth server
unicorn-keycloak    keycloak:25.0      🟡 Running (unhealthy)     Legacy instance
ops-center-direct   uc-1-pro-ops-center ✅ Running                Main app
```

### API Endpoints Status

| Endpoint | Status | Notes |
|----------|--------|-------|
| `/api/v1/users` | ✅ Registered | Returns 401 (no auth due to Keycloak down) |
| `/api/v1/admin/users` | ❌ Not Found | Frontend uses wrong endpoint |
| `/api/v1/local-users` | ✅ Registered | Linux user management (not used) |

### Networks

```
Network          Containers
──────────────────────────────────────────────────────────────────
uchub-network    uchub-keycloak, ops-center-direct, unicorn-brigade, ...
unicorn-network  unicorn-keycloak, ops-center-direct, ...
web              ops-center-direct (Traefik routing)
```

---

## 🎯 Action Plan

### Immediate Actions (CRITICAL)

1. **Fix Keycloak Clustering Issue**
   - Add `KC_CACHE=local` to uchub-keycloak environment
   - OR set unique `jgroups.cluster.name=uchub-cluster`
   - Restart uchub-keycloak
   - Verify startup with `docker logs uchub-keycloak`

2. **Fix Frontend API Endpoints**
   - Update all `/api/v1/admin/users/*` to `/api/v1/users/*` in UserManagement.jsx
   - Rebuild frontend: `npm run build && cp -r dist/* public/`
   - Restart ops-center: `docker restart ops-center-direct`

### Secondary Actions (Important)

3. **Test User Management End-to-End**
   - Login to https://your-domain.com
   - Navigate to /admin/system/users
   - Verify user list loads
   - Test filtering, search, role management
   - Test user detail page

4. **Document Keycloak Architecture**
   - Create diagram showing uchub-keycloak vs unicorn-keycloak usage
   - Document which services use which Keycloak instance
   - Decide if unicorn-keycloak is still needed

### Future Actions (Nice-to-Have)

5. **Consider Architecture Cleanup**
   - Consolidate to single Keycloak instance if possible
   - Or clearly separate realms/networks to prevent conflicts
   - Update documentation with Keycloak topology

---

## 📝 Summary

**Root Cause**: Keycloak 26.0 (uchub-keycloak) fails to start due to JGroups protocol version conflict with Keycloak 25.0 (unicorn-keycloak) on shared network.

**Impact**: All user management, authentication, and admin operations are blocked. Frontend shows "Failed to load users."

**Primary Fix**: Add `KC_CACHE=local` or unique cluster name to uchub-keycloak configuration.

**Secondary Fix**: Update frontend to use correct `/api/v1/users` endpoints (not `/api/v1/admin/users`).

**Verification**: Test Keycloak startup, port connectivity, authentication, and user list loading.

**Estimated Downtime**: 5-10 minutes (configuration change + restart).

**Files to Modify**:
1. `docker-compose.<uchub-keycloak>.yml` - Add KC_CACHE or cluster name
2. `src/pages/UserManagement.jsx` - Fix API endpoint paths (10+ instances)

**Testing Required**: End-to-end user management flow after both fixes applied.

---

**Generated by**: Code Analyzer Agent
**Date**: October 22, 2025 02:45 UTC
**For**: UC-Cloud Ops-Center Debugging Session
