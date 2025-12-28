# Setting Up ops-center Client in UCHUB Realm

**Date**: October 13, 2025
**Status**: ⚠️ **MANUAL CONFIGURATION REQUIRED**

---

## 🔍 Current Situation

The `uchub` realm exists and is accessible at:
- URL: https://auth.your-domain.com/realms/uchub
- Realm is live and responding
- Identity providers (Google/GitHub/Microsoft) are configured in this realm

However, the `ops-center` OAuth client needs to be created manually in the uchub realm.

---

## ✅ What's Already Done

1. **Realm Configuration Updated**:
   - Changed `KEYCLOAK_REALM` from `master` to `uchub` in `docker-compose.direct.yml`
   - ops-center will now use the uchub realm for authentication

2. **SSO Endpoints Updated**:
   - All SSO buttons now redirect to: `https://auth.your-domain.com/realms/uchub/...`
   - Identity provider hints work correctly (google, github, microsoft)

3. **Client Configuration Ready**:
   - Client ID: `ops-center`
   - Client Secret: `your-keycloak-client-secret`
   - Redirect URIs prepared

---

## 📋 Manual Steps Required

### Step 1: Access Keycloak Admin Console
1. Go to: **https://auth.your-domain.com/admin**
2. Login with admin credentials
3. Select **"uchub"** realm from the dropdown (top-left corner)

### Step 2: Create ops-center Client
1. Navigate to: **Clients** → **Create client**

2. **General Settings**:
   - Client type: `OpenID Connect`
   - Client ID: `ops-center`
   - Name: `Ops Center`
   - Description: `UC Cloud Operations Center`
   - Click **Next**

3. **Capability config**:
   - Client authentication: **ON** (confidential client)
   - Authorization: OFF
   - Authentication flow:
     - ✅ Standard flow
     - ✅ Direct access grants
     - ❌ Implicit flow
     - ❌ Service accounts roles
   - Click **Next**

4. **Login settings**:
   - Root URL: `https://your-domain.com`
   - Home URL: `https://your-domain.com`
   - Valid redirect URIs:
     - `https://your-domain.com/*`
     - `https://your-domain.com/auth/callback`
   - Valid post logout redirect URIs: `https://your-domain.com/*`
   - Web origins: `https://your-domain.com`
   - Click **Save**

### Step 3: Set Client Secret
1. After creating the client, go to the **Credentials** tab
2. Set the Client Secret to: `your-keycloak-client-secret`
3. Click **Save**

### Step 4: Verify Identity Providers
While you're in the admin console:
1. Navigate to: **Identity providers**
2. Verify these exist and are enabled:
   - Google (alias: `google`)
   - GitHub (alias: `github`)
   - Microsoft (alias: `microsoft`)
3. Check that aliases match exactly (lowercase)

---

## 🧪 Testing After Setup

Once the client is created, test the SSO flow:

### Test 1: Google SSO
1. Visit: https://your-domain.com/login.html
2. Click "Sign in with Google"
3. Should redirect to Google login (not "Client not found")
4. After Google auth, should return to ops-center

### Test 2: Registration Flow
1. Visit: https://your-domain.com/signup.html
2. Fill in account details
3. Select Founder's Friend plan
4. Should proceed to Stripe checkout

### Test 3: Direct Login
1. Try logging in with username/password
2. Should authenticate against uchub realm
3. Session should include org context

---

## 🔧 Alternative: Command Line Setup

If you have the correct admin credentials, you can create the client via command line:

```bash
docker exec unicorn-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password [ADMIN_PASSWORD]

docker exec unicorn-keycloak /opt/keycloak/bin/kcadm.sh create clients -r uchub \
  -s clientId=ops-center \
  -s enabled=true \
  -s publicClient=false \
  -s 'redirectUris=["https://your-domain.com/*","https://your-domain.com/auth/callback"]' \
  -s 'webOrigins=["https://your-domain.com"]' \
  -s clientAuthenticatorType=client-secret \
  -s secret=your-keycloak-client-secret
```

Replace `[ADMIN_PASSWORD]` with the actual admin password.

---

## 📝 Notes

1. **Realm is Live**: The uchub realm is accessible and working at https://auth.your-domain.com/realms/uchub

2. **Identity Providers Ready**: Google/GitHub/Microsoft providers are already configured in the uchub realm (per user confirmation)

3. **Only Missing Piece**: The `ops-center` OAuth client needs to be registered in the uchub realm

4. **After Client Creation**: Everything should work immediately - SSO buttons will use the identity providers in the uchub realm

---

## ✅ Expected Result

After creating the ops-center client in the uchub realm:

- ✅ SSO with Google/GitHub/Microsoft will work
- ✅ No more "Client not found" errors
- ✅ Identity providers from uchub realm will be used
- ✅ User registration with SSO will create orgs correctly
- ✅ Manual signup and payment flow already works

---

*Generated: October 13, 2025*
*Version: 1.3.0*
*System: UC-Cloud Ops Center*
