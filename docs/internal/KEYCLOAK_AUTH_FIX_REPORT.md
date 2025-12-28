# Keycloak 401 Authentication Error - Root Cause Analysis & Fix Report

**Report Date**: October 22, 2025
**Service**: Ops-Center (ops-center-direct)
**Issue**: ERROR: Failed to authenticate with Keycloak: 401
**Status**: ✅ ROOT CAUSE IDENTIFIED - FIX REQUIRED

---

## Executive Summary

The ops-center backend is experiencing 401 Unauthorized errors when attempting to authenticate with Keycloak. The root cause has been identified as a **configuration mismatch** in the authentication flow.

**Key Finding**: The admin user credentials are being sent to the **uchub realm** when they should be sent to the **master realm**.

---

## Root Cause Analysis

### Issue Description

The `keycloak_integration.py` file uses the `KEYCLOAK_REALM` environment variable for BOTH:
1. **Token Endpoint** (line 43) - Where admin authenticates
2. **Admin API Endpoints** (lines 83, 111, 143, etc.) - Where user operations are performed

### Current Problematic Code

**File**: `backend/keycloak_integration.py`
**Lines 14-20**:

```python
# Keycloak Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://auth.your-domain.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "master")  # ← Default is master, but env sets uchub
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
KEYCLOAK_CLIENT_SECRET = os.getenv("KEYCLOAK_CLIENT_SECRET", "")
KEYCLOAK_ADMIN_USERNAME = os.getenv("KEYCLOAK_ADMIN_USER", os.getenv("KEYCLOAK_ADMIN_USERNAME", "admin"))
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")
```

**Lines 42-50** (Token acquisition - PROBLEM AREA):

```python
async with httpx.AsyncClient(verify=False) as client:
    response = await client.post(
        f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",  # ← USES uchub
        data={
            "grant_type": "password",
            "client_id": KEYCLOAK_CLIENT_ID,
            "username": KEYCLOAK_ADMIN_USERNAME,
            "password": KEYCLOAK_ADMIN_PASSWORD
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=10.0
    )
```

**Lines 83-86** (Admin API calls - CORRECT):

```python
response = await client.get(
    f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",  # ← Correctly uses uchub for API
    headers={"Authorization": f"Bearer {token}"},
    params={"max": 1000},
```

### Environment Configuration

**Container**: `ops-center-direct`
**Environment Variables** (verified in running container):

```bash
KEYCLOAK_ADMIN_PASSWORD=your-admin-password
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_REALM=uchub                    # ← THIS IS THE PROBLEM
KEYCLOAK_URL=http://uchub-keycloak:8080
OAUTH_CLIENT_ID=ops-center
OPS_CENTER_OAUTH_CLIENT_SECRET=your-keycloak-client-secret
```

**Docker Compose**: `docker-compose.direct.yml` (line 18):

```yaml
environment:
  - KEYCLOAK_REALM=uchub  # ← Configured for user realm, not admin realm
```

### Why This Fails

1. **Admin User Location**: The `admin` user with password `your-admin-password` exists ONLY in the **master** realm, not in the **uchub** realm.

2. **Current Behavior**:
   ```
   POST http://uchub-keycloak:8080/realms/uchub/protocol/openid-connect/token
   Body: username=admin&password=your-admin-password

   Response: 401 Unauthorized
   Error: "Invalid user credentials"
   ```

3. **Reason**: There is no `admin` user in the `uchub` realm with those credentials.

### Test Results

**Test 1**: Master realm authentication ✅
```bash
curl -X POST "https://auth.your-domain.com/realms/master/protocol/openid-connect/token" \
  -d "grant_type=password&client_id=admin-cli&username=admin&password=your-admin-password"

Response: 200 OK
{
  "access_token": "eyJhbGc...",
  "expires_in": 60
}
```

**Test 2**: UCHUB realm authentication ❌
```bash
curl -X POST "https://auth.your-domain.com/realms/uchub/protocol/openid-connect/token" \
  -d "grant_type=password&client_id=admin-cli&username=admin&password=your-admin-password"

Response: 401 Unauthorized
{
  "error": "invalid_grant",
  "error_description": "Invalid user credentials"
}
```

**Test 3**: Admin API access to uchub realm with master token ✅
```bash
TOKEN=$(curl -s "https://auth.your-domain.com/realms/master/..." | jq -r .access_token)
curl -H "Authorization: Bearer $TOKEN" \
  "https://auth.your-domain.com/admin/realms/uchub/users?max=1"

Response: 200 OK
[
  {
    "id": "...",
    "email": "admin@example.com",
    ...
  }
]
```

### Additional Finding: Keycloak Container State

**Current Status**: Container is in "starting" state, which may contribute to intermittent connection failures.

```bash
$ docker ps --filter "name=uchub-keycloak"
uchub-keycloak	Up About a minute (health: starting)	8080/tcp, 8443/tcp, 9000/tcp
```

**Impact**: Even with the correct configuration, authentication may fail if Keycloak hasn't fully started.

---

## The Fix

### Solution 1: Hardcode Master Realm for Admin Token (RECOMMENDED)

This is the **cleanest and most reliable** solution. Admin authentication should ALWAYS use the master realm, regardless of which realm you're managing.

**File**: `backend/keycloak_integration.py`
**Change**: Line 43

**BEFORE**:
```python
response = await client.post(
    f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
    ...
)
```

**AFTER**:
```python
response = await client.post(
    f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",  # ← Always use master
    ...
)
```

**Rationale**:
- Admin users exist in the master realm
- This is Keycloak's standard architecture
- Admin token works for managing ALL realms via Admin API
- Keeps existing Admin API calls unchanged (they correctly use `KEYCLOAK_REALM`)

### Solution 2: Create Separate Environment Variable (ALTERNATIVE)

If you want more flexibility, create a separate variable for the admin realm.

**File**: `backend/keycloak_integration.py`
**Changes**: Lines 14-20 and 43

**Add new variable**:
```python
# Keycloak Configuration
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://auth.your-domain.com")
KEYCLOAK_ADMIN_REALM = os.getenv("KEYCLOAK_ADMIN_REALM", "master")  # ← NEW
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "uchub")  # ← For user operations
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "admin-cli")
...
```

**Update token endpoint**:
```python
response = await client.post(
    f"{KEYCLOAK_URL}/realms/{KEYCLOAK_ADMIN_REALM}/protocol/openid-connect/token",  # ← Use admin realm
    ...
)
```

**Update docker-compose.direct.yml**:
```yaml
environment:
  - KEYCLOAK_ADMIN_REALM=master  # New variable
  - KEYCLOAK_REALM=uchub         # Existing
```

### Solution 3: Change KEYCLOAK_REALM to master (NOT RECOMMENDED)

**Why this is BAD**:
- Would break all Admin API calls that manage uchub realm users
- Would require changing all API endpoints from `uchub` to `master`
- Users are in uchub realm, not master realm

---

## Implementation Steps

### Step 1: Apply Code Fix (Solution 1 - Recommended)

```bash
# 1. Edit the file
cd /home/muut/Production/UC-Cloud/services/ops-center
vim backend/keycloak_integration.py

# 2. Change line 43 from:
f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"

# to:
f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token"

# 3. Save file
```

### Step 2: Restart Container

```bash
# Restart ops-center to load changes
docker restart ops-center-direct

# Wait for startup
sleep 10

# Check logs
docker logs ops-center-direct --tail 50 | grep -i keycloak
```

### Step 3: Verify Fix

```bash
# Test authentication from inside container
docker exec ops-center-direct python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from keycloak_integration import get_admin_token

async def test():
    try:
        token = await get_admin_token()
        print('✅ SUCCESS - Got admin token')
        print(f'Token: {token[:50]}...')
        return True
    except Exception as e:
        print(f'❌ FAILED - {e}')
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
"
```

### Step 4: Test User Operations

```bash
# Test getting users from uchub realm
docker exec ops-center-direct python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from keycloak_integration import get_all_users

async def test():
    try:
        users = await get_all_users()
        print(f'✅ SUCCESS - Retrieved {len(users)} users from uchub realm')
        if users:
            print(f'Sample user: {users[0].get(\"email\", \"N/A\")}')
        return True
    except Exception as e:
        print(f'❌ FAILED - {e}')
        return False

result = asyncio.run(test())
sys.exit(0 if result else 1)
"
```

---

## Additional Recommendations

### 1. Wait for Keycloak Full Startup

**Current Issue**: Keycloak container shows `health: starting`, which means it's not fully ready.

**Fix**: Add health check wait in ops-center startup or add retry logic.

**Option A**: Add dependency wait in docker-compose.direct.yml:
```yaml
services:
  ops-center-direct:
    depends_on:
      uchub-keycloak:
        condition: service_healthy
```

**Option B**: Add retry logic to `get_admin_token()`:
```python
async def get_admin_token() -> str:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # ... existing code ...
            return access_token
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Token request failed (attempt {attempt+1}/{max_retries}), retrying...")
                await asyncio.sleep(2)
            else:
                raise
```

### 2. Add Better Error Logging

**Current**: Generic "Failed to authenticate" message
**Recommended**: Include response details

**Change in keycloak_integration.py** (line 66):
```python
else:
    error_msg = f"Failed to get admin token: {response.status_code} - {response.text}"
    logger.error(error_msg)
    logger.error(f"Request URL: {KEYCLOAK_URL}/realms/master/protocol/openid-connect/token")
    logger.error(f"Username: {KEYCLOAK_ADMIN_USERNAME}")
    raise Exception(error_msg)
```

### 3. Environment Variable Documentation

Add clear comments in docker-compose.direct.yml:

```yaml
environment:
  # Keycloak Configuration
  - KEYCLOAK_URL=http://uchub-keycloak:8080
  - KEYCLOAK_REALM=uchub                    # Target realm for user operations
  # NOTE: Admin authentication always uses 'master' realm (hardcoded in code)
  - KEYCLOAK_ADMIN_USER=admin               # Admin user (exists in master realm only)
  - KEYCLOAK_ADMIN_PASSWORD=your-admin-password
```

---

## Files Requiring Changes

### Primary Fix (Solution 1)

1. **backend/keycloak_integration.py** - Line 43
   - Change: `{KEYCLOAK_REALM}` → `master` (hardcoded)
   - Impact: Fixes 401 authentication errors
   - Risk: None (this is the correct approach)

### Optional Enhancements

2. **backend/keycloak_integration.py** - Lines 66-67
   - Change: Add detailed error logging
   - Impact: Easier debugging
   - Risk: None

3. **backend/keycloak_integration.py** - Lines 29-71
   - Change: Add retry logic for Keycloak startup
   - Impact: More resilient to Keycloak restarts
   - Risk: None

4. **docker-compose.direct.yml** - Environment section
   - Change: Add documentation comments
   - Impact: Clarity for future maintainers
   - Risk: None

---

## Testing Plan

### Pre-Deployment Tests

1. ✅ **Environment Variable Verification**
   ```bash
   docker exec ops-center-direct printenv | grep KEYCLOAK
   ```
   - Confirmed: KEYCLOAK_REALM=uchub
   - Confirmed: KEYCLOAK_ADMIN_PASSWORD=your-admin-password

2. ✅ **Master Realm Authentication**
   ```bash
   curl -X POST "https://auth.your-domain.com/realms/master/..."
   ```
   - Result: 200 OK
   - Conclusion: Admin credentials are correct

3. ✅ **UCHUB Realm Authentication**
   ```bash
   curl -X POST "https://auth.your-domain.com/realms/uchub/..."
   ```
   - Result: 401 Unauthorized
   - Conclusion: Admin user doesn't exist in uchub realm (expected)

4. ✅ **Admin API Access**
   ```bash
   curl -H "Authorization: Bearer <master-token>" \
     "https://auth.your-domain.com/admin/realms/uchub/users"
   ```
   - Result: 200 OK (when Keycloak is healthy)
   - Conclusion: Master token works for uchub realm management

### Post-Deployment Tests

After applying the fix, verify:

1. **Token Acquisition**
   ```bash
   # Should succeed
   docker exec ops-center-direct python3 -c "from keycloak_integration import get_admin_token; ..."
   ```

2. **User Listing**
   ```bash
   # Should return uchub realm users
   docker exec ops-center-direct python3 -c "from keycloak_integration import get_all_users; ..."
   ```

3. **User Operations**
   - Create user
   - Update user attributes
   - Assign roles
   - Delete user

4. **API Endpoint Tests**
   ```bash
   # Test from external
   curl http://localhost:8084/api/v1/admin/users/analytics/summary
   ```

---

## Risk Assessment

### Code Change Risk: LOW ✅

- **Impact**: Single line change (line 43)
- **Scope**: Only affects authentication, not user operations
- **Reversibility**: Easy to revert if needed
- **Testing**: Can be tested in container before deployment

### Deployment Risk: LOW ✅

- **Downtime**: Container restart (~10 seconds)
- **Dependencies**: No schema changes, no data migration
- **Rollback**: Simple container restart with old code

### Business Impact: HIGH ✅

- **Current State**: User management completely broken (401 errors)
- **Post-Fix**: Full user management functionality restored
- **User Experience**: Ops-Center admin panel becomes functional

---

## Success Criteria

The fix is successful when:

1. ✅ No 401 errors in container logs
2. ✅ `get_admin_token()` returns valid JWT token
3. ✅ `get_all_users()` returns uchub realm users
4. ✅ User management UI loads without errors
5. ✅ User operations (create, update, delete) work
6. ✅ API endpoints respond with 200 OK

---

## Timeline

### Immediate (5 minutes)
- Apply code fix (edit 1 line)
- Restart container
- Verify authentication works

### Short-term (30 minutes)
- Add error logging improvements
- Add retry logic for resilience
- Update documentation comments

### Long-term (optional)
- Consider implementing health check dependencies
- Add monitoring for Keycloak connectivity
- Create automated tests for authentication

---

## Summary

**Root Cause**: Admin authentication attempted against `uchub` realm instead of `master` realm

**Fix**: Change line 43 in `keycloak_integration.py` to hardcode `master` realm for token endpoint

**Impact**: Single line change, no other modifications needed

**Risk**: Minimal - this is the correct Keycloak architecture

**Testing**: Can verify immediately after container restart

**Recommendation**: Apply Solution 1 (hardcode master realm) - it's the cleanest, most reliable fix that aligns with Keycloak's standard architecture.

---

## Appendix: Code Change Diff

```diff
--- a/backend/keycloak_integration.py
+++ b/backend/keycloak_integration.py
@@ -40,7 +40,7 @@ async def get_admin_token() -> str:
     try:
         async with httpx.AsyncClient(verify=False) as client:
             response = await client.post(
-                f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
+                f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
                 data={
                     "grant_type": "password",
                     "client_id": KEYCLOAK_CLIENT_ID,
```

**Lines Changed**: 1
**Files Modified**: 1
**Complexity**: Trivial
**Testing Required**: Basic smoke test

---

**Report Generated**: October 22, 2025
**Analyst**: Security Agent (Claude Code)
**Confidence Level**: 100% (Root cause confirmed via testing)
**Recommended Action**: Apply fix immediately
