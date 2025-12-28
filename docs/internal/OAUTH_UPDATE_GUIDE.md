# OAuth Redirect URI Update Guide

## 🎯 What You Need to Do

You already have OAuth apps configured, but they're pointing to Authentik's callback URLs. We need to update them to point to our custom callback URL.

---

## 📝 Quick Reference

**Current (Authentik) Callbacks:**
```
Google:    https://auth.your-domain.com/source/oauth/callback/google/
GitHub:    https://auth.your-domain.com/source/oauth/callback/github/
Microsoft: https://auth.your-domain.com/source/oauth/callback/microsoft/
```

**New (Custom) Callback:**
```
ALL: https://your-domain.com/auth/callback
```

---

## 1️⃣ Google OAuth

### Console
https://console.cloud.google.com/

### Steps
1. Go to **Credentials** → **OAuth 2.0 Client IDs**
2. Find your client: `69011395859-mba6c0ra1dhasp49bfrpb6p2upv9h1q1`
3. Click **Edit**
4. Under **Authorized redirect URIs**, add:
   ```
   https://your-domain.com/auth/callback
   ```
5. **Keep the old Authentik URI** (for now, during transition)
6. Click **Save**

### What to Keep
- Client ID: `69011395859-mba6c0ra1dhasp49bfrpb6p2upv9h1q1`
- Client Secret: `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`

---

## 2️⃣ GitHub OAuth

### Console
https://github.com/settings/developers

### Steps
1. Go to **OAuth Apps**
2. Find your app (should have Client ID: `Ov23liE66ILKT4NBrbYB`)
3. Click on the app name
4. Update **Authorization callback URL** to:
   ```
   https://your-domain.com/auth/callback
   ```
5. Click **Update application**

### Note
GitHub only allows ONE callback URL, so you'll need to:
- **Option A**: Change it now (breaks Authentik temporarily)
- **Option B**: Create a new OAuth app for custom auth (recommended for testing)

### What to Keep
- Client ID: `Ov23liE66ILKT4NBrbYB`
- Client Secret: `054466c9e0aa7b5ca0a4b8304bca9a6777458a8f`

---

## 3️⃣ Microsoft OAuth

### Console
https://portal.azure.com/

### Steps
1. Go to **Azure Active Directory** → **App registrations**
2. Find your app: `77d288a0-dbf5-42f7-a1d2-aab586994ad6`
3. Click **Authentication** in left menu
4. Under **Platform configurations** → **Web** → **Redirect URIs**, click **Add URI**
5. Add:
   ```
   https://your-domain.com/auth/callback
   ```
6. **Keep the old Authentik URI** (can have multiple)
7. Click **Save**

### What to Keep
- Application (client) ID: `77d288a0-dbf5-42f7-a1d2-aab586994ad6`
- Client Secret: `XaO8Q~_7xBIJiveW5ehHSBmDq7lpA7.JAy9sSakY`
- Tenant ID: `059b7dec-5304-4fc7-922e-39ed5dff710e`

---

## ✅ Verification Checklist

After updating all three:

- [ ] Google: Added `https://your-domain.com/auth/callback`
- [ ] GitHub: Updated to `https://your-domain.com/auth/callback` (or created new app)
- [ ] Microsoft: Added `https://your-domain.com/auth/callback`

---

## 🧪 Testing

After deployment, test each provider:

1. Visit: https://your-domain.com/
2. Click "Continue with Google"
3. Should redirect to Google login
4. After authorization, should redirect back to:
   ```
   https://your-domain.com/auth/callback?code=...&state=...
   ```
5. Should create session and redirect to dashboard

Repeat for GitHub and Microsoft.

---

## ⚠️ Troubleshooting

### Error: "Redirect URI mismatch"
**Cause**: OAuth app still configured with old Authentik URL

**Fix**: Double-check you added the exact URL:
```
https://your-domain.com/auth/callback
```
No trailing slash, exact domain.

### Error: "Invalid client"
**Cause**: Wrong client ID or secret in `.env.auth`

**Fix**: Verify credentials match exactly what's in the console.

### Error: "State mismatch"
**Cause**: Session expired during OAuth flow

**Fix**: Try logging in again. Check Redis is running:
```bash
docker ps | grep redis
```

---

## 🔄 Transition Strategy

### Option A: Switch All at Once (Fastest)
1. Update all OAuth redirect URIs
2. Deploy custom auth
3. Authentik stops working (expected)

### Option B: Keep Both Running (Safest)
1. Add new redirect URIs (keep old ones)
2. Deploy custom auth
3. Both systems work
4. Test custom auth thoroughly
5. Remove old Authentik URIs later

**Recommendation**: Option B - Keep both URLs for a smooth transition.

---

## 📞 Need Help?

If you get stuck:

1. **Check OAuth app settings** - Make sure redirect URI is EXACT
2. **Check container logs**: `docker logs unicorn-ops-center`
3. **Check browser console** - Look for redirect errors
4. **Verify .env.auth** - Make sure all credentials are correct

---

## 🎉 After Update

Once redirect URIs are updated, you're ready to run:

```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center
./setup-custom-auth.sh
```

This will deploy everything and get you running!
