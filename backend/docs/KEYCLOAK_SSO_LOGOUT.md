# Keycloak SSO Logout Implementation

## Overview

The logout endpoint has been updated to properly clear Keycloak SSO sessions in addition to local session cleanup.

## Changes Made

### 1. Backend: `/api/v1/auth/logout` Endpoint Update

**File:** `/opt/ops-center/backend/server.py` (line 2836)

**Updated behavior:**
1. Clears local session via `auth_manager.logout()`
2. Generates Keycloak SSO logout URL
3. Returns both success message and SSO logout URL

**Response format:**
```json
{
  "message": "Logged out successfully",
  "sso_logout_url": "https://auth.unicorncommander.ai/realms/master/protocol/openid-connect/logout?redirect_uri=https://unicorncommander.ai"
}
```

### 2. Environment Configuration

The logout endpoint uses these environment variables:

```bash
KEYCLOAK_URL=https://auth.unicorncommander.ai
KEYCLOAK_REALM=master
FRONTEND_URL=https://unicorncommander.ai
```

**Default values:**
- `KEYCLOAK_URL`: `https://auth.unicorncommander.ai`
- `KEYCLOAK_REALM`: `master`
- `FRONTEND_URL`: `https://unicorncommander.ai`

## Frontend Integration

### JavaScript/TypeScript Implementation

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

### React Implementation

```typescript
import { useNavigate } from 'react-router-dom';

function LogoutButton() {
  const navigate = useNavigate();

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
        // Redirect to Keycloak logout
        window.location.href = data.sso_logout_url;
      } else {
        console.error('Logout failed');
        navigate('/');
      }
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/');
    }
  };

  return (
    <button onClick={handleLogout}>
      Logout
    </button>
  );
}
```

### Vue.js Implementation

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
          // Redirect to Keycloak logout
          window.location.href = data.sso_logout_url;
        } else {
          console.error('Logout failed');
          this.$router.push('/');
        }
      } catch (error) {
        console.error('Logout error:', error);
        this.$router.push('/');
      }
    }
  }
}
```

## Logout Flow

```
┌─────────────────┐
│   User clicks   │
│   Logout btn    │
└────────┬────────┘
         │
         v
┌─────────────────────────────────────┐
│ Frontend calls POST /api/v1/auth/logout │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ Backend:                             │
│ 1. Clears local session             │
│ 2. Logs audit event                 │
│ 3. Generates Keycloak logout URL    │
│ 4. Returns {message, sso_logout_url}│
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ Frontend redirects to sso_logout_url │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ Keycloak:                            │
│ 1. Ends SSO session                 │
│ 2. Clears cookies                   │
│ 3. Redirects to redirect_uri        │
└────────┬────────────────────────────┘
         │
         v
┌─────────────────────────────────────┐
│ User lands on frontend homepage     │
│ (Completely logged out)             │
└─────────────────────────────────────┘
```

## Testing

### Test Script

A test script is provided at:
`/opt/ops-center/backend/tests/test_keycloak_logout.py`

**Run tests:**
```bash
cd /opt/ops-center/backend
python3 tests/test_keycloak_logout.py
```

**What the test checks:**
1. Logout endpoint structure and response format
2. SSO logout URL format is correct
3. Keycloak endpoint is accessible
4. Environment configuration is correct

### Manual Testing

1. **Login to the application:**
   - Visit https://unicorncommander.ai
   - Login via Keycloak SSO

2. **Test logout:**
   - Click logout button
   - Verify you are redirected to Keycloak
   - Verify you are redirected back to homepage
   - Verify you cannot access protected pages

3. **Test SSO session is cleared:**
   - After logout, visit https://auth.unicorncommander.ai
   - Verify you are not logged in
   - Verify other apps using the same Keycloak realm also logged out

### Expected Behavior

**Before fix:**
- Local session cleared ✓
- Keycloak SSO session **NOT** cleared ✗
- User could revisit app and auto-login

**After fix:**
- Local session cleared ✓
- Keycloak SSO session cleared ✓
- User must re-authenticate completely

## Keycloak Configuration

### Required Keycloak Settings

1. **Valid Redirect URIs** for ops-center client:
   ```
   https://unicorncommander.ai
   https://unicorncommander.ai/*
   ```

2. **Valid Post Logout Redirect URIs**:
   ```
   https://unicorncommander.ai
   ```

3. **Client Settings** (in Keycloak Admin):
   - Client ID: `ops-center`
   - Realm: `master`
   - Access Type: `confidential`
   - Standard Flow Enabled: `ON`
   - Valid Redirect URIs: Configured above

### Verify Keycloak Configuration

```bash
# Check if Keycloak is accessible
curl https://auth.unicorncommander.ai/realms/master/.well-known/openid-configuration

# Test logout endpoint (will redirect)
curl -I "https://auth.unicorncommander.ai/realms/master/protocol/openid-connect/logout?redirect_uri=https://unicorncommander.ai"
```

## Troubleshooting

### Issue: "Invalid redirect_uri"

**Cause:** The `redirect_uri` is not configured in Keycloak client settings

**Solution:** Add `https://unicorncommander.ai` to Valid Post Logout Redirect URIs:
1. Login to Keycloak Admin: https://auth.unicorncommander.ai/admin
2. Navigate to: Clients → ops-center
3. Add to "Valid Post Logout Redirect URIs"
4. Save

### Issue: User stays logged in after logout

**Cause:** Frontend not redirecting to `sso_logout_url`

**Solution:** Verify frontend code redirects to the returned URL:
```javascript
window.location.href = data.sso_logout_url;
```

### Issue: Logout redirects to wrong URL

**Cause:** `FRONTEND_URL` environment variable incorrect

**Solution:** Update `.env` file:
```bash
FRONTEND_URL=https://unicorncommander.ai
```

### Issue: Logout fails with 500 error

**Cause:** Environment variables not loaded

**Solution:** Restart the backend server:
```bash
docker restart unicorn-ops-center
```

## Security Notes

1. **Always use HTTPS** in production for redirect URIs
2. **Validate redirect_uri** in Keycloak to prevent open redirects
3. **Clear local storage** in frontend after logout
4. **Invalidate API tokens** server-side during logout
5. **Audit log all logout events** for security monitoring

## Related Documentation

- **Keycloak Documentation**: https://www.keycloak.org/docs/latest/securing_apps/index.html#logout
- **OIDC Logout Specification**: https://openid.net/specs/openid-connect-session-1_0.html#RPLogout
- **Backend Server**: `/opt/ops-center/backend/server.py`
- **Keycloak Integration**: `/opt/ops-center/backend/keycloak_integration.py`

## Summary

✅ **Local session logout** - Clears backend session
✅ **Keycloak SSO logout** - Ends SSO session across all apps
✅ **Secure redirect** - Returns to configured frontend URL
✅ **Audit logging** - Tracks all logout events
✅ **Error handling** - Graceful fallback on errors
