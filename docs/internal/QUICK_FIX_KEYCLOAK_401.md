# Quick Fix: Keycloak 401 Error

**Issue**: ops-center getting 401 errors when authenticating with Keycloak
**Root Cause**: Admin authentication sent to uchub realm instead of master realm
**Fix Time**: 5 minutes

## The One-Line Fix

**File**: `backend/keycloak_integration.py`
**Line**: 43

**Change from**:
```python
f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token",
```

**Change to**:
```python
f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
```

## Why This Works

- Admin user (`admin`) exists in **master** realm only
- Current code uses `KEYCLOAK_REALM=uchub` for authentication
- Admin doesn't have credentials in uchub realm → 401 error
- Fix: Always authenticate against master realm
- Master admin token works for managing ALL realms

## Apply Fix

```bash
# 1. Edit file
cd /home/muut/Production/UC-Cloud/services/ops-center
nano backend/keycloak_integration.py
# Change line 43 as shown above

# 2. Restart
docker restart ops-center-direct

# 3. Verify
docker logs ops-center-direct --tail 50 | grep -i "keycloak\|401"
```

## Verify Fix Works

```bash
docker exec ops-center-direct python3 -c "
import asyncio, sys
sys.path.insert(0, '/app')
from keycloak_integration import get_admin_token

async def test():
    try:
        token = await get_admin_token()
        print('✅ SUCCESS')
        return True
    except Exception as e:
        print(f'❌ FAILED: {e}')
        return False

result = asyncio.run(test())
"
```

## Full Report

See `KEYCLOAK_AUTH_FIX_REPORT.md` for complete analysis.
