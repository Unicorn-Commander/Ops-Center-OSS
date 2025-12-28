# BYOK Frontend Fix Instructions
**Issue**: Frontend calling wrong API endpoints
**Priority**: 🔴 HIGH - User-facing feature broken
**Time to Fix**: 30 minutes

---

## Problem

The BYOK (Bring Your Own Key) feature is broken because the frontend is calling:
- `/api/v1/auth/byok/keys` ❌

But the backend router is at:
- `/api/v1/byok/` ✅

Result: **404 Not Found** errors when users try to manage API keys.

---

## Quick Fix (Search & Replace)

### File to Edit
`src/pages/account/AccountAPIKeys.jsx`

### Find and Replace

**Find**: `/api/v1/auth/byok/`
**Replace**: `/api/v1/byok/`

**Command (if using sed)**:
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
sed -i 's|/api/v1/auth/byok/|/api/v1/byok/|g' src/pages/account/AccountAPIKeys.jsx
```

### Rebuild and Deploy
```bash
npm run build
cp -r dist/* public/
docker restart ops-center-direct
```

---

## Detailed Changes

### Change 1: List API Keys (Line ~105)
```javascript
// BEFORE:
const response = await fetch('/api/v1/auth/byok/keys');

// AFTER:
const response = await fetch('/api/v1/byok/keys');
```

### Change 2: Add API Key (Line ~180)
```javascript
// BEFORE:
const response = await fetch('/api/v1/auth/byok/keys', {
  method: 'POST',
  ...
});

// AFTER:
const response = await fetch('/api/v1/byok/keys/add', {
  method: 'POST',
  ...
});
```

### Change 3: Test API Key (Line ~220)
```javascript
// BEFORE:
await fetch(`/api/v1/auth/byok/keys/${keyId}/test`, {
  method: 'POST'
});

// AFTER:
await fetch(`/api/v1/byok/keys/test/${provider}`, {
  method: 'POST'
});
```

### Change 4: Delete API Key (Line ~250)
```javascript
// BEFORE:
await fetch(`/api/v1/auth/byok/keys/${keyId}`, {
  method: 'DELETE'
});

// AFTER:
await fetch(`/api/v1/byok/keys/${provider}`, {
  method: 'DELETE'
});
```

---

## Testing After Fix

### 1. Test Backend Endpoints
```bash
# Should return provider list (after auth)
curl http://localhost:8084/api/v1/byok/providers

# Should require authentication
curl http://localhost:8084/api/v1/byok/keys
# Expected: {"detail":"Not authenticated"}
```

### 2. Test via UI

1. **Login** to https://your-domain.com
2. **Navigate** to Account → API Keys
3. **Click** "Add API Key" button
4. **Select** OpenAI as provider
5. **Enter** test key: `sk-test1234567890`
6. **Click** "Add Key"
7. **Expected**: Key added successfully (no 404 errors)
8. **Test** the key using "Test" button
9. **Delete** the key
10. **Expected**: All operations work without errors

### 3. Check Browser Console

Open browser dev tools (F12) and check for:
- ❌ No 404 errors
- ❌ No "Failed to fetch" errors
- ✅ Successful API calls to `/api/v1/byok/`

---

## Verification Checklist

- [ ] sed command executed successfully
- [ ] `npm run build` completed without errors
- [ ] Files copied to `public/` directory
- [ ] Container restarted
- [ ] Backend endpoints return correct responses
- [ ] UI loads without errors
- [ ] Can add API key
- [ ] Can test API key
- [ ] Can delete API key
- [ ] No 404 errors in browser console
- [ ] No JavaScript errors in browser console

---

## Rollback (if needed)

If the fix causes issues, rollback:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center
git checkout src/pages/account/AccountAPIKeys.jsx
npm run build
cp -r dist/* public/
docker restart ops-center-direct
```

---

## Root Cause

**Why did this happen?**

The backend router was defined with prefix `/api/v1/byok` (line 18 in `byok_api.py`):
```python
router = APIRouter(prefix="/api/v1/byok", tags=["byok"])
```

But the frontend was developed expecting `/api/v1/auth/byok` (likely copying from another auth endpoint pattern).

**Prevention**: Ensure frontend and backend teams align on API paths before implementation.

---

## Alternative Fix (NOT RECOMMENDED)

If changing the frontend is not possible, you could change the backend:

**File**: `backend/byok_api.py`
**Line 18**:
```python
# Change this:
router = APIRouter(prefix="/api/v1/byok", tags=["byok"])

# To this:
router = APIRouter(prefix="/api/v1/auth/byok", tags=["byok"])
```

**Why NOT RECOMMENDED**:
- Breaks existing API documentation
- Inconsistent with other admin endpoints
- Frontend fix is simpler and more correct

---

## Status After Fix

Once fixed, the BYOK feature will be:
- ✅ Fully operational
- ✅ Users can add their own API keys
- ✅ Keys stored encrypted in Keycloak
- ✅ Keys tested against provider APIs
- ✅ Keys properly masked in UI

---

**Created**: October 25, 2025
**Priority**: HIGH
**Estimated Fix Time**: 30 minutes
**Testing Time**: 1 hour
