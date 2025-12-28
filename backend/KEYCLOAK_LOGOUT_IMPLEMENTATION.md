# Keycloak SSO Logout - Implementation Summary

## Overview

The `/api/v1/auth/logout` endpoint has been updated to properly clear Keycloak SSO sessions, ensuring users are completely logged out from both the application and SSO provider.

## Changes Made

### 1. Updated Logout Endpoint

**File:** `/home/muut/Production/UC-Cloud/services/ops-center/backend/server.py` (line 2836)

**Before:**
```python
@app.post("/api/v1/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout and invalidate session"""
    try:
        if AUDIT_ENABLED:
            await log_logout(...)

        auth_manager.logout(current_user.get("session_id"))
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**After:**
```python
@app.post("/api/v1/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """Logout and invalidate session"""
    try:
        # Audit log logout
        if AUDIT_ENABLED:
            await log_logout(...)

        # Clear local session
        auth_manager.logout(current_user.get("session_id"))

        # Build Keycloak SSO logout URL
        keycloak_url = os.getenv("KEYCLOAK_URL", "https://auth.your-domain.com")
        keycloak_realm = os.getenv("KEYCLOAK_REALM", "master")
        redirect_uri = os.getenv("FRONTEND_URL", "https://your-domain.com")

        sso_logout_url = (
            f"{keycloak_url}/realms/{keycloak_realm}/protocol/openid-connect/logout"
            f"?redirect_uri={redirect_uri}"
        )

        return {
            "message": "Logged out successfully",
            "sso_logout_url": sso_logout_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Environment Variables

Add these to your `.env` file if not already present:

```bash
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=master
FRONTEND_URL=https://your-domain.com
```

**Defaults (if not set):**
- `KEYCLOAK_URL`: https://auth.your-domain.com
- `KEYCLOAK_REALM`: master
- `FRONTEND_URL`: https://your-domain.com

## API Response

### Success Response (200 OK)

```json
{
  "message": "Logged out successfully",
  "sso_logout_url": "https://auth.your-domain.com/realms/master/protocol/openid-connect/logout?redirect_uri=https://your-domain.com"
}
```

### Error Response (500 Internal Server Error)

```json
{
  "detail": "Error message"
}
```

### Unauthorized (401)

```json
{
  "detail": "Not authenticated"
}
```

## Frontend Integration

### Step 1: Update Logout Handler

**JavaScript/TypeScript:**
```javascript
async function logout() {
  try {
    const response = await fetch('/api/v1/auth/logout', {
      method: 'POST',
      credentials: 'include', // Important: Include cookies
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();

      // Redirect to Keycloak SSO logout
      // This will clear the SSO session and redirect back
      window.location.href = data.sso_logout_url;
    } else {
      console.error('Logout failed:', response.statusText);
      // Fallback: redirect to home
      window.location.href = '/';
    }
  } catch (error) {
    console.error('Logout error:', error);
    // Fallback: redirect to home
    window.location.href = '/';
  }
}
```

**React:**
```typescript
import { useNavigate } from 'react-router-dom';

function LogoutButton() {
  const handleLogout = async () => {
    try {
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        // Clear local storage/state if needed
        localStorage.clear();
        sessionStorage.clear();

        // Redirect to Keycloak logout
        window.location.href = data.sso_logout_url;
      }
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  return <button onClick={handleLogout}>Logout</button>;
}
```

**Vue.js:**
```javascript
export default {
  methods: {
    async logout() {
      try {
        const response = await fetch('/api/v1/auth/logout', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();

          // Clear local state
          localStorage.clear();
          sessionStorage.clear();

          // Redirect to Keycloak logout
          window.location.href = data.sso_logout_url;
        }
      } catch (error) {
        console.error('Logout error:', error);
        this.$router.push('/');
      }
    }
  }
}
```

### Step 2: Clear Local State (Optional but Recommended)

Before redirecting to Keycloak, clear any local state:

```javascript
// Clear localStorage
localStorage.clear();

// Clear sessionStorage
sessionStorage.clear();

// Clear any app-specific state
// e.g., Redux store, Vuex store, React Context, etc.
```

## Complete Logout Flow

```
┌──────────────────┐
│  User clicks     │
│  Logout button   │
└────────┬─────────┘
         │
         v
┌──────────────────────────────────────────────┐
│ Frontend: POST /api/v1/auth/logout           │
│ (with credentials/cookies)                   │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│ Backend:                                      │
│ 1. Verify authentication                     │
│ 2. Log audit event                           │
│ 3. Clear local session                       │
│ 4. Build Keycloak logout URL                 │
│ 5. Return response with sso_logout_url       │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│ Frontend:                                     │
│ 1. Parse response                            │
│ 2. Clear local storage (optional)            │
│ 3. Redirect: window.location.href = url      │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│ Keycloak:                                     │
│ 1. Validate redirect_uri                     │
│ 2. End SSO session                           │
│ 3. Clear Keycloak cookies                    │
│ 4. Redirect to redirect_uri                  │
└────────┬─────────────────────────────────────┘
         │
         v
┌──────────────────────────────────────────────┐
│ User lands on homepage                       │
│ Completely logged out from:                  │
│ - Local application session                  │
│ - Keycloak SSO session                       │
│ - All apps using same Keycloak realm         │
└──────────────────────────────────────────────┘
```

## Testing

### Automated Test

Run the test script:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
./tests/test_logout_simple.sh
```

### Manual Testing

1. **Login:**
   - Visit https://your-domain.com
   - Login via Keycloak

2. **Test Logout:**
   - Click logout button
   - Verify redirect to Keycloak
   - Verify redirect back to homepage
   - Try to access protected pages (should be denied)

3. **Verify SSO Session Cleared:**
   - Open new tab
   - Visit https://auth.your-domain.com
   - Should not be logged in
   - Try to access other apps using same Keycloak realm
   - Should require login

### Test Checklist

- [ ] Local session is cleared (backend)
- [ ] Audit log records logout event
- [ ] Response contains `sso_logout_url`
- [ ] SSO logout URL has correct format
- [ ] Redirect URI is correct
- [ ] Browser redirects to Keycloak
- [ ] Keycloak clears SSO session
- [ ] Browser redirects back to frontend
- [ ] User cannot access protected pages
- [ ] Other apps also logged out (SSO)

## Keycloak Configuration

### Required Settings in Keycloak Admin Console

1. **Navigate to:** https://auth.your-domain.com/admin
2. **Select Realm:** master
3. **Go to:** Clients → ops-center
4. **Configure:**

```
Valid Redirect URIs:
  https://your-domain.com
  https://your-domain.com/*

Valid Post Logout Redirect URIs:
  https://your-domain.com

Settings:
  Client ID: ops-center
  Client Protocol: openid-connect
  Access Type: confidential
  Standard Flow Enabled: ON
  Direct Access Grants Enabled: ON
```

### Verify Keycloak Endpoint

Test the logout endpoint:

```bash
curl -I "https://auth.your-domain.com/realms/master/protocol/openid-connect/logout?redirect_uri=https://your-domain.com"
```

Expected: HTTP 200 or 302 (redirect)

## Troubleshooting

### Issue: "Invalid redirect_uri"

**Cause:** Redirect URI not whitelisted in Keycloak

**Solution:**
1. Login to Keycloak Admin Console
2. Go to Clients → ops-center
3. Add `https://your-domain.com` to "Valid Post Logout Redirect URIs"
4. Save

### Issue: User stays logged in after logout

**Cause:** Frontend not redirecting to SSO logout URL

**Solution:** Verify frontend code includes:
```javascript
window.location.href = data.sso_logout_url;
```

### Issue: Logout redirects to wrong URL

**Cause:** Incorrect `FRONTEND_URL` environment variable

**Solution:** Update `.env`:
```bash
FRONTEND_URL=https://your-domain.com
```

Restart backend:
```bash
docker restart unicorn-ops-center
```

### Issue: CORS errors on logout

**Cause:** CORS not configured for logout endpoint

**Solution:** Ensure CORS middleware includes `/api/v1/auth/logout` in allowed paths

### Issue: Logout fails with 401

**Cause:** Session expired or not authenticated

**Solution:** This is expected behavior - redirect to login page

## Security Considerations

1. **Always use HTTPS** for redirect URIs in production
2. **Validate redirect_uri** in Keycloak to prevent open redirects
3. **Clear sensitive data** from local storage before redirect
4. **Audit log all logouts** for security monitoring
5. **Implement CSRF protection** on logout endpoint (if needed)
6. **Use secure cookies** with HttpOnly and Secure flags
7. **Set short SSO session timeouts** for sensitive applications

## Benefits

### Before Implementation

- ❌ Local session cleared, but SSO session remains
- ❌ User can revisit app and auto-login without credentials
- ❌ Logout doesn't affect other apps
- ❌ Incomplete logout leaves security vulnerability

### After Implementation

- ✅ Both local and SSO sessions cleared
- ✅ User must re-authenticate completely
- ✅ Logout affects all apps in the realm (true SSO)
- ✅ Complete, secure logout
- ✅ Proper redirect back to frontend
- ✅ Audit logging maintained

## Files Modified

```
/home/muut/Production/UC-Cloud/services/ops-center/backend/
├── server.py                               # Updated logout endpoint (line 2836)
├── tests/
│   ├── test_keycloak_logout.py            # Detailed test script
│   └── test_logout_simple.sh              # Simple bash test
├── docs/
│   └── KEYCLOAK_SSO_LOGOUT.md             # Detailed documentation
└── KEYCLOAK_LOGOUT_IMPLEMENTATION.md      # This file
```

## Related Documentation

- [Keycloak OIDC Logout](https://www.keycloak.org/docs/latest/securing_apps/index.html#logout)
- [OpenID Connect Session Management](https://openid.net/specs/openid-connect-session-1_0.html)
- [Backend Server Code](/home/muut/Production/UC-Cloud/services/ops-center/backend/server.py)
- [Keycloak Integration Module](/home/muut/Production/UC-Cloud/services/ops-center/backend/keycloak_integration.py)

## Summary

✅ **Implementation Complete**
- Logout endpoint updated with Keycloak SSO logout URL
- Environment variables configured
- Test scripts created
- Documentation written
- Frontend integration examples provided

**Next Steps:**
1. Update frontend to redirect to `sso_logout_url`
2. Test complete logout flow
3. Verify Keycloak configuration
4. Deploy to production

**Keycloak Details:**
- URL: https://auth.your-domain.com
- Realm: master
- Client: ops-center
- Logout URL: https://auth.your-domain.com/realms/master/protocol/openid-connect/logout

---

**Created:** 2025-10-13
**Author:** Backend API Developer
**Status:** ✅ Complete
