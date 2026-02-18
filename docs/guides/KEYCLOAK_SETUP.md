# Keycloak OIDC Client Setup for Ops Center

**Date:** October 8, 2025
**Status:** Ready to Configure

## Overview

Ops Center has been migrated from direct OAuth to Keycloak SSO integration. This provides centralized authentication for all UC-1 Pro services.

## What's Been Done

✅ **OAuth archived** - Original OAuth code moved to `backend/auth/archived/`
✅ **Keycloak integration created** - New OIDC client in `backend/auth/keycloak_integration.py`
✅ **Server.py updated** - Uses Keycloak instead of direct OAuth
✅ **Login page updated** - Single SSO button redirects to Keycloak

## What's Needed: Create OIDC Client in Keycloak

### Step 1: Access Keycloak Admin Console

**URL:** https://auth.unicorncommander.ai/admin/uchub/console
**Username:** `admin`
**Password:** `your-admin-password`

### Step 2: Create New OIDC Client

1. **Navigate to Clients:**
   - Click "Clients" in left sidebar
   - Click "Create client" button

2. **General Settings:**
   - **Client type:** OpenID Connect
   - **Client ID:** `ops-center`
   - Click "Next"

3. **Capability Config:**
   - **Client authentication:** ON (confidential client)
   - **Authorization:** OFF (not needed)
   - **Authentication flow:**
     - ✅ Standard flow (authorization code)
     - ✅ Direct access grants
     - ❌ Implicit flow (not needed)
     - ❌ Service accounts (not needed for now)
   - Click "Next"

4. **Login Settings:**
   - **Root URL:** `https://unicorncommander.ai`
   - **Home URL:** `https://unicorncommander.ai`
   - **Valid redirect URIs:**
     ```
     https://unicorncommander.ai/auth/callback
     http://localhost:8000/auth/callback
     ```
   - **Valid post logout redirect URIs:**
     ```
     https://unicorncommander.ai
     http://localhost:8000
     ```
   - **Web origins:**
     ```
     https://unicorncommander.ai
     http://localhost:8000
     ```
   - Click "Save"

### Step 3: Get Client Secret

1. **Go to "Credentials" tab**
2. **Copy the Client Secret** (looks like: `a1b2c3d4-e5f6-7g8h-9i0j-k1l2m3n4o5p6`)
3. **Save it** - you'll need this for the environment variable

### Step 4: Configure Client Scopes (Optional but Recommended)

1. **Go to "Client scopes" tab**
2. **Ensure these are assigned:**
   - `openid` (required)
   - `email` (required)
   - `profile` (required)
   - `roles` (recommended - for admin detection)

### Step 5: Configure Role Mapping (For Admin Access)

1. **Create admin role if it doesn't exist:**
   - Go to "Realm roles" in left sidebar
   - Create role: `admin` or `uc-admin`

2. **Assign admin role to users:**
   - Go to "Users" → Select user
   - Go to "Role mapping" tab
   - Assign `admin` or `uc-admin` role

## Environment Configuration

After creating the client, set the environment variable:

```bash
# In /home/deploy/Production/UC-1-Pro/services/ops-center/.env or docker-compose
export KEYCLOAK_CLIENT_SECRET="<your-client-secret-from-step-3>"
```

Or add to docker run command:
```bash
-e KEYCLOAK_CLIENT_SECRET="<your-client-secret>"
```

## Testing the Setup

### 1. Manual Testing via Keycloak Admin UI

Before deploying, test the OIDC flow:

1. **Get Authorization URL:**
   ```bash
   curl "https://auth.unicorncommander.ai/realms/uchub/protocol/openid-connect/auth?client_id=ops-center&redirect_uri=https://unicorncommander.ai/auth/callback&response_type=code&scope=openid%20email%20profile"
   ```
   Should return HTML (Keycloak login page)

2. **Verify OIDC Discovery:**
   ```bash
   curl https://auth.unicorncommander.ai/realms/uchub/.well-known/openid-configuration
   ```
   Should return JSON with endpoints

### 2. Full Application Testing

After setting `KEYCLOAK_CLIENT_SECRET` and rebuilding:

1. **Visit:** https://unicorncommander.ai
2. **Expected:** Redirects to `/login.html` with SSO button
3. **Click "Sign In to UC Cloud"**
4. **Expected:** Redirects to Keycloak login page
5. **Login** with Google/GitHub/Microsoft or password
6. **Expected:** Redirects back to `/admin` (admin) or `/dashboard` (user)

## Current Configuration

**Keycloak Server:** https://auth.unicorncommander.ai
**Realm:** `uchub`
**Client ID:** `ops-center`
**Client Secret:** ❌ **NOT SET YET** - needs to be created in Keycloak

**Redirect URIs Configured in Code:**
- Production: `https://unicorncommander.ai/auth/callback`
- Local: `http://localhost:8000/auth/callback`

## Troubleshooting

### Issue: "Invalid redirect URI" error

**Fix:** Ensure redirect URI in Keycloak exactly matches what's in the code:
```
https://unicorncommander.ai/auth/callback
```

### Issue: "Invalid client credentials" error

**Fix:** Double-check `KEYCLOAK_CLIENT_SECRET` matches the secret from Keycloak credentials tab.

### Issue: User gets logged in but not redirected to /admin (admin users)

**Fix:** Ensure user has `admin` or `uc-admin` role assigned in Keycloak.

### Issue: "Failed to validate token signature"

**Fix:** This usually means the token is from a different realm or client. Verify:
- `KEYCLOAK_URL=https://auth.unicorncommander.ai`
- `KEYCLOAK_REALM=uchub`
- Client ID matches exactly: `ops-center`

## Next Steps After Setup

Once Keycloak client is configured and working:

1. ✅ **SSO Working** - Users can login via Keycloak
2. ⏭️ **Add User Management UI** - Build admin interface using Keycloak Admin API
3. ⏭️ **Integrate Billing Dashboard** - Show Stripe/Lago data in Ops Center
4. ⏭️ **Add Service Management** - Deploy/manage vLLM, Chat, Search from Ops Center

## Benefits of This Setup

✅ **Centralized Authentication** - One login for all UC-1 Pro services
✅ **Enterprise Security** - MFA, passkeys, password policies
✅ **Social Login** - Google, GitHub, Microsoft configured once in Keycloak
✅ **User Federation** - LDAP/AD integration available
✅ **Better Admin Tools** - Keycloak Admin API for user management
✅ **Scalable** - Ready for multi-tenant UC-Cloud platform

## Documentation

- **Keycloak Integration Module:** `backend/auth/keycloak_integration.py`
- **Migration Summary:** `backend/auth/KEYCLOAK_MIGRATION_SUMMARY.md`
- **Archived OAuth Code:** `backend/auth/archived/`

---

**Ready to configure?** Follow steps 1-5 above, then set the client secret and rebuild the container!
