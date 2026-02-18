# Keycloak User Profile Configuration Guide

**Last Updated**: November 29, 2025
**Status**: Required for Ops-Center user metrics persistence
**Keycloak Version**: 26.0+

---

## Overview

Keycloak User Profile must be configured to ensure custom user attributes (subscription tier, API usage, etc.) persist correctly across sessions. This is a **one-time manual setup** required for Ops-Center to function correctly.

## Why This Is Needed

**Problem**: User attributes may not persist across sessions without User Profile configuration.

**Impact**:
- User Management dashboard shows incorrect metrics (0 users, 0 active, etc.)
- Subscription tiers reset after logout/login
- API usage tracking not working
- Billing integration fails

**Solution**: Configure User Profile attributes in Keycloak Admin Console (one-time setup).

---

## Quick Check: Do I Need This?

Run this command to check if configuration is needed:

```bash
docker exec ops-center-direct python3 /app/scripts/configure_keycloak_user_profile.py
```

**If you see**: "✓ All attributes correct" → Configuration is complete
**If you see**: "✗ Some attributes incorrect" → Follow this guide

---

## Step-by-Step Configuration

### Step 1: Access Keycloak Admin Console

1. **Open Browser**: Navigate to https://auth.unicorncommander.ai/admin/uchub/console

2. **Login**:
   - Username: `admin`
   - Password: `your-admin-password`

3. **Verify Realm**: Ensure you're in the `uchub` realm (top-left dropdown)

### Step 2: Navigate to User Profile

1. **Click**: "Realm Settings" (left sidebar)
2. **Click**: "User Profile" tab (top menu)
3. **Verify**: "User Profile Enabled" toggle is ON

### Step 3: Add Custom Attributes

For each attribute below, click **"Add attribute"** button:

#### Attribute 1: subscription_tier

**Required Fields**:
- **Attribute name**: `subscription_tier`
- **Display name**: `Subscription Tier`
- **Attribute group**: Leave blank or create "Subscription" group

**Validators** (click "+ Add validator"):
- **Type**: Options
- **Options**:
  ```
  trial
  free
  starter
  professional
  enterprise
  vip_founder
  founder_friend
  byok
  managed
  ```

**Permissions**:
- **Who can view**: ✓ user, ✓ admin
- **Who can edit**: ✓ admin (uncheck user)

**Annotations** (optional):
- `description`: "User's subscription tier level"
- `userEditable`: `false`
- `adminEditable`: `true`

**Click**: "Create" to save

---

#### Attribute 2: subscription_status

**Required Fields**:
- **Attribute name**: `subscription_status`
- **Display name**: `Subscription Status`
- **Attribute group**: Subscription (if created above)

**Validators** (click "+ Add validator"):
- **Type**: Options
- **Options**:
  ```
  active
  inactive
  suspended
  cancelled
  pending
  ```

**Permissions**:
- **Who can view**: ✓ user, ✓ admin
- **Who can edit**: ✓ admin (uncheck user)

**Annotations** (optional):
- `description`: "Current subscription account status"

**Click**: "Create" to save

---

#### Attribute 3: api_calls_limit

**Required Fields**:
- **Attribute name**: `api_calls_limit`
- **Display name**: `API Calls Limit`
- **Attribute group**: Usage (create new group)

**Validators** (click "+ Add validator"):
- **Type**: Integer
- **Min**: `0`
- **Max**: `1000000`

**Permissions**:
- **Who can view**: ✓ user, ✓ admin
- **Who can edit**: ✓ admin (uncheck user)

**Annotations** (optional):
- `description`: "Maximum API calls per billing cycle"

**Click**: "Create" to save

---

#### Attribute 4: api_calls_used

**Required Fields**:
- **Attribute name**: `api_calls_used`
- **Display name**: `API Calls Used`
- **Attribute group**: Usage

**Validators** (click "+ Add validator"):
- **Type**: Integer
- **Min**: `0`
- **Max**: `1000000`

**Permissions**:
- **Who can view**: ✓ user, ✓ admin
- **Who can edit**: ✓ admin (uncheck user)

**Annotations** (optional):
- `description`: "Current API call usage in billing cycle"

**Click**: "Create" to save

---

#### Attribute 5: api_calls_reset_date

**Required Fields**:
- **Attribute name**: `api_calls_reset_date`
- **Display name**: `API Calls Reset Date`
- **Attribute group**: Usage

**Validators**:
- None (stores ISO 8601 date string like "2025-11-29")

**Permissions**:
- **Who can view**: ✓ user, ✓ admin
- **Who can edit**: ✓ admin (uncheck user)

**Annotations** (optional):
- `description`: "Date when API call quota resets (ISO 8601 format)"

**Click**: "Create" to save

---

### Step 4: Verify Configuration

After adding all 5 attributes, you should see them listed in the User Profile page:

```
✓ subscription_tier
✓ subscription_status
✓ api_calls_limit
✓ api_calls_used
✓ api_calls_reset_date
```

**Click**: "Save" button at the bottom of the page (if available)

---

### Step 5: Populate User Attributes

Now that User Profile is configured, populate existing users with default values:

```bash
docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
```

**Expected Output**:
```
Processing user: admin@example.com
  ✓ Updated subscription_tier: vip_founder
  ✓ Updated subscription_status: active
  ✓ Updated api_calls_limit: 10000
  ✓ Updated api_calls_used: 0
  ✓ Updated api_calls_reset_date: 2025-11-29

✓ Updated 9 users successfully
```

---

### Step 6: Verify Persistence

Run the automated verification script:

```bash
docker exec ops-center-direct python3 /app/scripts/verify_user_attributes.py
```

**Expected Output**:
```
✓ SUCCESS: All attributes persist correctly across sessions!
```

**If verification fails**:
1. Double-check attribute names match exactly (case-sensitive)
2. Verify permissions are set correctly
3. Clear browser cache and re-login to Keycloak Admin Console
4. Try the verification script again

---

## Troubleshooting

### Issue: Attributes Don't Persist After Logout

**Symptoms**:
- User metrics show 0 after logout/login
- Subscription tier resets to default
- API usage counters disappear

**Solution**:
1. Verify User Profile is enabled:
   - Realm Settings → User Profile
   - Toggle should be ON

2. Check attribute configuration:
   - All 5 attributes should be listed
   - Permissions should allow admin edit
   - Validators should be configured

3. Re-run population script:
   ```bash
   docker exec ops-center-direct python3 /app/scripts/quick_populate_users.py
   ```

4. Test with a single user:
   ```bash
   # Get user attributes
   docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password your-admin-password

   docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users -r uchub --fields id,username,attributes --limit 1
   ```

---

### Issue: Validators Not Working

**Symptoms**:
- Can save invalid tier values (e.g., "invalid-tier")
- Integer fields accept text values

**Solution**:
1. Re-add validators through Web UI:
   - User Profile → Click attribute name
   - Validators section → "+ Add validator"
   - Select correct type (Options or Integer)
   - Enter values
   - Save

2. Test validator:
   - Users → Select a user
   - Attributes tab
   - Try setting invalid value
   - Should show error message

---

### Issue: Permissions Not Applied

**Symptoms**:
- Users can edit their own subscription tier
- Attributes not visible in user profile

**Solution**:
1. Check permission configuration:
   - User Profile → Click attribute name
   - Permissions section
   - View: user, admin (both checked)
   - Edit: admin only (user unchecked)

2. Clear user sessions:
   ```bash
   docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:8080 --realm master --user admin --password your-admin-password

   # Get user ID
   USER_ID=$(docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users -r uchub --query username=aaron --fields id | grep '"id"' | cut -d'"' -f4)

   # Logout all sessions
   docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh create users/$USER_ID/logout -r uchub
   ```

3. Have user logout and login again

---

## Alternative: CLI Configuration (Advanced)

If Web UI is not accessible, you can configure via Keycloak Admin CLI:

```bash
# Authenticate
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password your-admin-password

# Enable User Profile (if not already enabled)
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh update realms/uchub \
  -s 'attributes.userProfileEnabled=true'

# Note: Individual attribute configuration via CLI is complex
# Web UI is recommended for attribute setup
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] User Profile feature is enabled
- [ ] All 5 attributes are listed in User Profile page
- [ ] Validators are configured for each attribute
- [ ] Permissions are set correctly (view: user+admin, edit: admin only)
- [ ] Population script ran successfully
- [ ] Verification script shows all attributes persist
- [ ] User Management dashboard shows correct metrics
- [ ] Metrics persist after logout/login cycle

---

## Impact on Ops-Center

Once configured, these features will work correctly:

**User Management**:
- ✓ User metrics dashboard (total users, active users, etc.)
- ✓ Subscription tier filtering
- ✓ User detail page with tier information

**Billing Integration**:
- ✓ Subscription tier enforcement
- ✓ API usage tracking and limits
- ✓ Billing cycle management

**API Management**:
- ✓ Rate limiting based on tier
- ✓ Usage analytics
- ✓ Quota reset automation

**Organization Management**:
- ✓ Tier-based feature access
- ✓ Usage reporting
- ✓ Billing allocation

---

## Additional Resources

- **Keycloak User Profile Documentation**: https://www.keycloak.org/docs/latest/server_admin/#user-profile
- **Ops-Center User Management**: `/opt/ops-center/docs/`
- **Configuration Scripts**: `/opt/ops-center/backend/scripts/`

---

## Support

If you encounter issues:

1. **Check Logs**:
   ```bash
   docker logs uchub-keycloak --tail 100
   docker logs ops-center-direct --tail 100
   ```

2. **Re-run Configuration Script**:
   ```bash
   docker exec ops-center-direct python3 /app/scripts/configure_keycloak_user_profile.py
   ```

3. **Verify Database**:
   ```bash
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT * FROM users LIMIT 1;"
   ```

4. **Contact**: Ops-Center DevOps Team

---

**Configuration Status**: Follow this guide to complete one-time setup
**Estimated Time**: 10-15 minutes
**Difficulty**: Beginner (Web UI) / Intermediate (CLI)
