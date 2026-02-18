# Keycloak Groups Quick Start Guide

**TL;DR:** Migrate from hardcoded admin list to Keycloak groups in 5 steps.

---

## Quick Setup (5 Minutes)

### Step 1: Create Groups via Script

```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center

# Install httpx if not already installed
pip3 install httpx

# Create groups
python3 scripts/create-keycloak-groups.py
```

**Expected output:**
```
✓ Complete! Created 4 new groups
```

---

### Step 2: Add Admin User to Group

```bash
# Add yourself to admin group
python3 scripts/add-user-to-group.py aaron uc1-admins
```

**Expected output:**
```
✓ User 'aaron' added to group 'uc1-admins'
```

---

### Step 3: Configure Group Mapper in Keycloak UI

1. **Login to Keycloak Admin:**
   - URL: https://auth.unicorncommander.ai/admin/uchub/console
   - Username: `admin`
   - Password: `your-admin-password`

2. **Add Group Mapper to Client:**
   - Left sidebar → **Clients**
   - Click **ops-center**
   - Click **Client scopes** tab
   - Click **ops-center-dedicated** (or create dedicated scope if doesn't exist)
   - Click **Add mapper** → **By configuration**
   - Select **Group Membership**
   - Configure:
     - **Name:** `groups`
     - **Token Claim Name:** `groups`
     - **Full group path:** **ON**
     - **Add to ID token:** **ON**
     - **Add to access token:** **ON**
     - **Add to userinfo:** **ON**
   - Click **Save**

3. **Verify Mapper:**
   - Clients → **ops-center** → **Client scopes** → **Evaluate**
   - Select user: **aaron**
   - Click **Generated access token**
   - Look for `"groups": ["/uc1-admins"]` in the JSON

---

### Step 4: Update Code

**File:** `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/role_mapper.py`

**Add these lines to ROLE_MAPPINGS (around line 22):**

```python
ROLE_MAPPINGS = {
    "admin": [
        "uc1-admins",       # NEW
        "/uc1-admins",      # NEW (full path)
        "admins",           # Keep for backward compat
        "admin",
        "administrators",
        "ops-center-admin"
    ],
    "power_user": [
        "uc1-power-users",  # NEW
        "/uc1-power-users", # NEW (full path)
        "power_users",
        "power_user",
        "powerusers",
        "ops-center-poweruser"
    ],
    # ... rest stays the same
}
```

**Optional: Reduce hardcoded admin list (line 124):**

```python
# BEFORE:
admin_identifiers = ["akadmin", "admin", "administrator"]

# AFTER (keep only emergency access):
admin_identifiers_legacy = ["akadmin"]  # Emergency only
```

---

### Step 5: Restart Ops-Center

```bash
docker restart ops-center-direct
```

---

## Test It

### Test 1: Check Logs

```bash
docker logs ops-center-direct --tail 50 | grep "mapped to role"
```

**Expected:**
```
INFO: User 'aaron' mapped to role 'admin' via group/role 'uc1-admins'
```

### Test 2: Login via Browser

1. Visit https://unicorncommander.ai
2. Click "Sign In"
3. Login with Keycloak credentials
4. Should redirect to `/admin` dashboard

### Test 3: Check API

```bash
# Get your session token from browser cookies, then:
curl https://unicorncommander.ai/api/v1/auth/me \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" | jq .role

# Expected output: "admin"
```

---

## Add More Users

```bash
# Add regular users
python3 scripts/add-user-to-group.py john uc1-users
python3 scripts/add-user-to-group.py jane uc1-power-users

# Add more admins
python3 scripts/add-user-to-group.py alice uc1-admins
```

---

## Rollback (If Needed)

```bash
# Revert code changes
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend
git checkout HEAD -- role_mapper.py

# Restart
docker restart ops-center-direct
```

---

## Troubleshooting

### Problem: "User always gets viewer role"

**Check:**
```bash
# 1. Is user in group?
python3 scripts/list-user-groups.py aaron

# 2. Does token contain groups?
# (Use Keycloak Admin → Clients → ops-center → Evaluate → aaron)

# 3. Check logs
docker logs ops-center-direct 2>&1 | grep "Extracted groups"
```

**Fix:**
- Verify group mapper is configured (Step 3)
- Check group name spelling (case-insensitive but must match)
- Logout and login again (token needs refresh)

### Problem: "Groups not in token"

**Check:**
```bash
# Evaluate token in Keycloak
# Admin Console → Clients → ops-center → Client scopes → Evaluate
# Select user → Generated access token
# Look for "groups" claim
```

**Fix:**
- Add group mapper (Step 3)
- Make sure mapper is added to **ops-center-dedicated** scope
- Set "Add to userinfo" = ON

### Problem: "Cannot login after changes"

**Fix:**
```bash
# Rollback immediately
git checkout HEAD -- role_mapper.py
docker restart ops-center-direct

# Then debug:
docker logs ops-center-direct --tail 100
docker logs uchub-keycloak --tail 100
```

---

## Full Documentation

See complete research and implementation guide:
- `/home/deploy/Production/UC-1-Pro/services/ops-center/docs/KEYCLOAK_GROUPS_RESEARCH.md`

---

## Summary

**What you did:**
1. ✅ Created 4 groups in Keycloak
2. ✅ Added admin user to `uc1-admins` group
3. ✅ Configured group mapper for `ops-center` client
4. ✅ Updated `ROLE_MAPPINGS` to recognize new groups
5. ✅ Tested admin login

**Benefits:**
- ✅ Centralized user management
- ✅ No more hardcoded lists
- ✅ Instant role changes (no code deployment)
- ✅ Audit trail in Keycloak
- ✅ Self-service ready

**Next steps:**
- Migrate all users to appropriate groups
- Remove hardcoded admin list after testing
- Enable MFA for admin group (optional)
- Set up group approval workflow (optional)

---

**Done! 🎉**
