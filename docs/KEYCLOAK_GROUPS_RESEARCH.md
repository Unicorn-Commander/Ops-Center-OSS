# Keycloak Groups Research for UC-1 Pro Role Management

**Date:** October 9, 2025
**Status:** Research Complete - Ready for Implementation
**Researcher:** Claude (Research Agent)

---

## Executive Summary

This document provides comprehensive research on migrating UC-1 Pro Ops Center from hardcoded username/email-based role assignment to proper Keycloak group-based role management. The current system uses a hardcoded list of admin identifiers in `role_mapper.py` which is not scalable or secure.

**Current State:**
- Hardcoded admin list: `["akadmin", "admin", "administrator", "aaron"]`
- Email whitelist: `["admin@example.com"]`
- Keycloak at: `https://auth.your-domain.com`
- Realm: `uchub`
- Admin credentials: `admin` / `your-admin-password`

**Recommended Solution:**
- Use Keycloak Groups (NOT realm roles) for role assignment
- Group naming: `uc1-admins`, `uc1-power-users`, `uc1-users`, `uc1-viewers`
- Groups appear in OIDC token's `groups` claim as string arrays
- Flat group structure (no hierarchy needed)

---

## Table of Contents

1. [Keycloak Architecture Overview](#keycloak-architecture-overview)
2. [Groups vs Roles in Keycloak](#groups-vs-roles-in-keycloak)
3. [OIDC Token Claims Analysis](#oidc-token-claims-analysis)
4. [Proposed Group Structure](#proposed-group-structure)
5. [Keycloak Admin API Access](#keycloak-admin-api-access)
6. [Implementation Plan](#implementation-plan)
7. [Testing Strategy](#testing-strategy)
8. [Migration Checklist](#migration-checklist)
9. [Rollback Plan](#rollback-plan)
10. [Security Considerations](#security-considerations)

---

## 1. Keycloak Architecture Overview

### Current Keycloak Setup

**Container:** `uchub-keycloak` (Running, but unhealthy status)
**Image:** Keycloak 26.0.8 on Quarkus 3.15.1
**Database:** PostgreSQL (`uchub-postgres:5432/keycloak_db`)
**URL:** https://auth.your-domain.com
**Realm:** `uchub`

**Environment Configuration:**
```bash
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=your-admin-password
KC_HOSTNAME_URL=https://auth.your-domain.com
KC_DB=postgres
KC_DB_URL=jdbc:postgresql://uchub-postgres:5432/keycloak_db
KC_FEATURES=token-exchange,admin-fine-grained-authz
KC_PROXY_HEADERS=xforwarded
KC_HEALTH_ENABLED=true
KC_METRICS_ENABLED=true
```

**OIDC Client Configured:**
- Client ID: `ops-center`
- Client Type: Confidential (server-side)
- Redirect URIs:
  - `https://your-domain.com/auth/callback`
  - `http://localhost:8000/auth/callback`
- Default Scopes: `openid`, `email`, `profile`, `roles`

### Current Role Mapper Implementation

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/role_mapper.py`

**Current Logic:**
1. Check hardcoded username list (lines 124-131)
2. Extract groups from OIDC token (function `extract_groups_from_user_info`)
3. Map groups to roles using `ROLE_MAPPINGS` dictionary
4. Default to `viewer` role if no match

**Token Claims Checked (in priority order):**
1. `groups` - Standard OIDC groups claim
2. `ak_groups` - Authentik-specific (not relevant for Keycloak)
3. `realm_access.roles` - Keycloak realm-level roles
4. `resource_access.[client].roles` - Client-specific roles

---

## 2. Groups vs Roles in Keycloak

### Understanding the Difference

| Feature | Groups | Roles |
|---------|--------|-------|
| **Purpose** | Organize users into logical collections | Define permissions and access levels |
| **Token Claim** | `groups` (array of strings) | `realm_access.roles` or `resource_access.[client].roles` |
| **Hierarchy** | Supports parent/child relationships | Flat structure |
| **Composites** | Can contain roles | Can contain other roles |
| **Best Use** | User organization, team structure | Permission assignment |
| **OIDC Standard** | Standard `groups` claim | Keycloak-specific claims |

### Recommendation: Use Groups

**Why Groups are Better for UC-1 Pro:**

1. **Standard OIDC Claim**: Groups appear in the standard `groups` claim, making the implementation more portable
2. **User Organization**: Groups represent organizational structure better than roles
3. **Simpler Token**: Groups = simple string array, roles = nested objects
4. **Future-Proof**: If you migrate to another OIDC provider, groups are more likely to work
5. **Explicit Membership**: Users explicitly join groups, making audit easier

**Example Token Comparison:**

**With Groups:**
```json
{
  "sub": "00a665e2-8703-4c06-a6b1-ec25cfcb98ef",
  "email": "admin@example.com",
  "preferred_username": "aaron",
  "groups": [
    "/uc1-admins",
    "/uc1-power-users"
  ]
}
```

**With Realm Roles:**
```json
{
  "sub": "00a665e2-8703-4c06-a6b1-ec25cfcb98ef",
  "email": "admin@example.com",
  "preferred_username": "aaron",
  "realm_access": {
    "roles": [
      "admin",
      "power_user",
      "default-roles-uchub",
      "offline_access",
      "uma_authorization"
    ]
  }
}
```

**Groups are cleaner and easier to parse.**

---

## 3. OIDC Token Claims Analysis

### How Groups Appear in Tokens

When you create groups in Keycloak and assign users to them, the groups appear in the OIDC token automatically **IF** you configure the client scope correctly.

**Default Behavior:**
- Groups are **NOT** included in tokens by default
- You must add a "groups" mapper to the client scope

**How to Include Groups in Tokens:**

1. **Option A: Use Built-in Groups Client Scope**
   - Go to Client Scopes → `groups`
   - Ensure it's set as **Default** scope for your client
   - This automatically includes groups in the token

2. **Option B: Create Custom Mapper** (if groups scope doesn't exist)
   - Client → `ops-center` → Client Scopes → Add mapper
   - Mapper Type: **Group Membership**
   - Token Claim Name: `groups`
   - Full group path: **ON** (to get `/uc1-admins` instead of `uc1-admins`)
   - Add to ID token: **ON**
   - Add to access token: **ON**
   - Add to userinfo: **ON**

### Expected Token Structure

**After Group Mapper is Configured:**

```json
{
  "sub": "00a665e2-8703-4c06-a6b1-ec25cfcb98ef",
  "email": "admin@example.com",
  "email_verified": true,
  "preferred_username": "aaron",
  "given_name": "Aaron",
  "family_name": "Admin",
  "groups": [
    "/uc1-admins"
  ]
}
```

**Note the forward slash:** Groups appear as `/groupname` when "Full group path" is enabled. Our role mapper already handles this with `.lower()` normalization.

---

## 4. Proposed Group Structure

### Group Naming Convention

**Recommended Pattern:** `uc1-{role}`

| Group Name | Maps to Role | Purpose | Members |
|------------|--------------|---------|---------|
| `uc1-admins` | `admin` | Full system access | Platform administrators |
| `uc1-power-users` | `power_user` | Advanced features | DevOps, senior engineers |
| `uc1-users` | `user` | Standard access | Regular users |
| `uc1-viewers` | `viewer` | Read-only access | Auditors, stakeholders |

**Why This Naming:**
- `uc1-` prefix: Avoids collision with other systems
- Lowercase + hyphens: Standard Keycloak convention
- Descriptive: Clear what each group represents

### Group Hierarchy Decision

**Recommendation: Flat Structure**

**Flat Structure:**
```
/uc1-admins
/uc1-power-users
/uc1-users
/uc1-viewers
```

**Hierarchical Alternative (NOT recommended):**
```
/uc1-pro
  /uc1-pro/admins
  /uc1-pro/power-users
  /uc1-pro/users
  /uc1-pro/viewers
```

**Why Flat is Better:**
- Simpler to manage
- Easier token parsing
- No need to handle nested groups in code
- More explicit membership

### Role Mapper Updates Needed

**Current Mappings in `role_mapper.py` (lines 21-46):**

```python
ROLE_MAPPINGS = {
    "admin": [
        "admins",           # Generic
        "admin",            # Role name
        "administrators",   # Alternative
        "ops-center-admin"  # Old naming
    ],
    # ... (similar for other roles)
}
```

**Updated Mappings (RECOMMENDED):**

```python
ROLE_MAPPINGS = {
    "admin": [
        "uc1-admins",       # NEW: Primary group name
        "/uc1-admins",      # NEW: Full path version
        "admins",           # Keep for backward compat
        "admin",            # Keep for backward compat
        "administrators",   # Keep for backward compat
    ],
    "power_user": [
        "uc1-power-users",  # NEW: Primary group name
        "/uc1-power-users", # NEW: Full path version
        "power_users",      # Keep for backward compat
        "power_user",       # Keep for backward compat
        "powerusers",       # Keep for backward compat
    ],
    "user": [
        "uc1-users",        # NEW: Primary group name
        "/uc1-users",       # NEW: Full path version
        "users",            # Keep for backward compat
        "user",             # Keep for backward compat
    ],
    "viewer": [
        "uc1-viewers",      # NEW: Primary group name
        "/uc1-viewers",     # NEW: Full path version
        "viewers",          # Keep for backward compat
        "viewer",           # Keep for backward compat
    ]
}
```

**Note:** Including both `/uc1-admins` and `uc1-admins` handles different group path configurations.

---

## 5. Keycloak Admin API Access

### Verification of Admin Access

**Admin Credentials Confirmed:**
- Username: `admin`
- Password: `your-admin-password`
- Access: Keycloak Admin CLI available in container

**Admin CLI Command (inside container):**
```bash
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh \
  config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password "your-admin-password"
```

**REST API Authentication:**
```bash
# Get admin token
curl -X POST https://auth.your-domain.com/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=your-admin-password"
```

### Available Admin Scripts

**1. Client Setup Script (VERIFIED):**
File: `/home/muut/Production/UC-1-Pro/services/ops-center/setup-keycloak-client.py`

**Features:**
- Uses `httpx` for REST API calls
- Authenticates with admin-cli
- Creates/updates OIDC clients
- Retrieves client secrets
- Already has KeycloakAdmin class

**2. Admin API Test Script (VERIFIED):**
File: `/home/muut/Production/UC-1-Pro/services/ops-center/test_admin_api.py`

**Features:**
- Tests admin authentication
- Lists users
- Gets user roles
- Retrieves realm stats
- **Uses:** `auth.keycloak_admin.KeycloakAdmin` class

**NOTE:** The `keycloak_admin.py` module is referenced but **NOT found** in the current codebase. This suggests it may need to be created or is in a different location.

### Python Admin API Library Options

**Option 1: Use existing `setup-keycloak-client.py` pattern**
- Pros: Already working, no new dependencies
- Cons: Limited to what's implemented

**Option 2: Use `python-keycloak` library**
- Install: `pip install python-keycloak`
- Pros: Full-featured, well-maintained
- Cons: New dependency

**Option 3: Direct REST API calls with `httpx`**
- Pros: No dependencies, full control
- Cons: More code to write

**RECOMMENDATION:** Extend the existing `setup-keycloak-client.py` KeycloakAdmin class to include group management methods.

---

## 6. Implementation Plan

### Phase 1: Configure Keycloak (Manual UI Steps)

**Step 1.1: Create Groups in Keycloak UI**

1. Login to Keycloak Admin Console
   - URL: https://auth.your-domain.com/admin/uchub/console
   - Username: `admin`
   - Password: `your-admin-password`

2. Navigate to Groups
   - Left sidebar → **Groups**

3. Create each group:
   - Click **Create group** button
   - Name: `uc1-admins`
   - Click **Create**
   - Repeat for: `uc1-power-users`, `uc1-users`, `uc1-viewers`

**Step 1.2: Configure Groups Mapper for ops-center Client**

1. Navigate to Client
   - Left sidebar → **Clients**
   - Click on **ops-center**

2. Go to Client Scopes tab
   - Click **Client scopes** tab
   - Check if `groups` is in **Default** or **Optional** scopes

3. If `groups` scope doesn't exist:
   - Go to **Client scopes** (main left sidebar)
   - Create new scope named `groups`
   - Add mapper:
     - Protocol: **openid-connect**
     - Mapper type: **Group Membership**
     - Name: `groups`
     - Token Claim Name: `groups`
     - Full group path: **ON**
     - Add to ID token: **ON**
     - Add to access token: **ON**
     - Add to userinfo: **ON**

4. Assign `groups` scope to `ops-center` client
   - Clients → ops-center → Client scopes
   - Click **Add client scope**
   - Select `groups`
   - Set as **Default** scope

**Step 1.3: Add User to uc1-admins Group**

1. Navigate to Users
   - Left sidebar → **Users**
   - Search for: `aaron`
   - Click on user `aaron` (admin@example.com)

2. Assign to Group
   - Click **Groups** tab
   - Click **Join Group** button
   - Select `uc1-admins`
   - Click **Join**

3. Verify Membership
   - User should now show `/uc1-admins` in Groups section

**Step 1.4: Test Group in Token**

Use Keycloak's built-in token evaluation:

1. Go to Clients → ops-center
2. Click **Client scopes** tab
3. Click **Evaluate** sub-tab
4. Select user: `aaron`
5. Click **Generated access token**
6. Look for `groups` claim in the JSON:
   ```json
   "groups": [
     "/uc1-admins"
   ]
   ```

If `groups` claim is present → SUCCESS!
If not → Check group mapper configuration

---

### Phase 2: Update Code

**Step 2.1: Update role_mapper.py**

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/backend/role_mapper.py`

**Changes:**

1. **Update ROLE_MAPPINGS (lines 21-46):**

```python
ROLE_MAPPINGS = {
    "admin": [
        "uc1-admins",       # PRIMARY: New group name
        "/uc1-admins",      # Full path version
        "admins",           # Backward compatibility
        "admin",
        "administrators",
        "ops-center-admin"
    ],
    "power_user": [
        "uc1-power-users",  # PRIMARY: New group name
        "/uc1-power-users", # Full path version
        "power_users",
        "power_user",
        "powerusers",
        "ops-center-poweruser"
    ],
    "user": [
        "uc1-users",        # PRIMARY: New group name
        "/uc1-users",       # Full path version
        "users",
        "user",
        "standard_users",
        "ops-center-user"
    ],
    "viewer": [
        "uc1-viewers",      # PRIMARY: New group name
        "/uc1-viewers",     # Full path version
        "viewers",
        "viewer",
        "read_only",
        "ops-center-viewer"
    ]
}
```

2. **Remove Hardcoded Admin List (lines 124-131):**

**BEFORE:**
```python
# Special handling for admin usernames and emails
admin_identifiers = ["akadmin", "admin", "administrator", "aaron"]
admin_emails = ["admin@example.com"]

email = user_info.get("email", "").lower()

if username.lower() in admin_identifiers or email in admin_emails:
    logger.info(f"User '{username}' ({email}) is a special admin account, granting admin role")
    return "admin"
```

**AFTER:**
```python
# Legacy admin identifiers (DEPRECATED - use uc1-admins group instead)
# This is kept temporarily for emergency access only
# TODO: Remove after confirming all admins are in uc1-admins group
admin_identifiers_legacy = ["akadmin"]  # ONLY akadmin for emergency access
admin_emails_legacy = []  # No email-based admin access

email = user_info.get("email", "").lower()

if username.lower() in admin_identifiers_legacy or email in admin_emails_legacy:
    logger.warning(f"User '{username}' ({email}) using LEGACY admin access - migrate to uc1-admins group!")
    return "admin"
```

**Step 2.2: Add Logging for Group Detection**

Add more detailed logging in `extract_groups_from_user_info` (lines 49-101):

```python
def extract_groups_from_user_info(user_info: Dict) -> List[str]:
    """
    Extract groups from Keycloak/Authentik user info response.

    ... (existing docstring) ...
    """
    groups = []

    # Check for standard 'groups' claim (PRIMARY for Keycloak)
    if "groups" in user_info:
        raw_groups = user_info["groups"]
        logger.debug(f"Found 'groups' claim: {raw_groups}")
        if isinstance(raw_groups, list):
            for group in raw_groups:
                if isinstance(group, str):
                    # Normalize: remove leading slash, lowercase
                    normalized = group.lstrip('/').lower()
                    groups.append(normalized)
                    logger.debug(f"  Added group: {normalized} (from: {group})")
                elif isinstance(group, dict) and "name" in group:
                    normalized = group["name"].lstrip('/').lower()
                    groups.append(normalized)
                    logger.debug(f"  Added group: {normalized} (from dict)")

    # ... (rest of function remains the same) ...

    # Log final group list
    logger.info(f"Extracted groups: {groups}")

    # Remove duplicates
    return list(set(groups))
```

**Step 2.3: Update Documentation**

Update `ROLE_MAPPING.md` to reflect new group-based approach.

---

### Phase 3: Create Admin API Scripts (Optional but Recommended)

**Script 1: Create Groups via API**

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/scripts/create-keycloak-groups.py`

```python
#!/usr/bin/env python3
"""
Create UC-1 Pro role groups in Keycloak
"""
import httpx
import sys

KEYCLOAK_URL = "https://auth.your-domain.com"
REALM = "uchub"
ADMIN_USER = "admin"
ADMIN_PASS = "your-admin-password"

GROUPS = [
    {"name": "uc1-admins", "path": "/uc1-admins"},
    {"name": "uc1-power-users", "path": "/uc1-power-users"},
    {"name": "uc1-users", "path": "/uc1-users"},
    {"name": "uc1-viewers", "path": "/uc1-viewers"}
]

def get_admin_token():
    """Get admin access token"""
    response = httpx.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": ADMIN_PASS
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]

def create_group(token, group_name):
    """Create a group in Keycloak"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Check if group exists
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/groups",
        headers=headers,
        params={"search": group_name}
    )
    response.raise_for_status()
    existing = response.json()

    if any(g["name"] == group_name for g in existing):
        print(f"✓ Group '{group_name}' already exists")
        return False

    # Create group
    response = httpx.post(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/groups",
        headers=headers,
        json={"name": group_name}
    )
    response.raise_for_status()
    print(f"✓ Created group '{group_name}'")
    return True

def main():
    print("Creating UC-1 Pro role groups in Keycloak...")
    print(f"Keycloak: {KEYCLOAK_URL}")
    print(f"Realm: {REALM}")
    print()

    try:
        token = get_admin_token()
        print("✓ Authenticated as admin")
        print()

        created_count = 0
        for group in GROUPS:
            if create_group(token, group["name"]):
                created_count += 1

        print()
        print(f"✓ Complete! Created {created_count} new groups")

    except httpx.HTTPStatusError as e:
        print(f"✗ HTTP Error: {e.response.status_code}")
        print(f"  {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python3 scripts/create-keycloak-groups.py
```

**Script 2: Add User to Group via API**

**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/scripts/add-user-to-group.py`

```python
#!/usr/bin/env python3
"""
Add a user to a Keycloak group
Usage: python3 add-user-to-group.py <username> <groupname>
"""
import httpx
import sys

KEYCLOAK_URL = "https://auth.your-domain.com"
REALM = "uchub"
ADMIN_USER = "admin"
ADMIN_PASS = "your-admin-password"

def get_admin_token():
    """Get admin access token"""
    response = httpx.post(
        f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": ADMIN_USER,
            "password": ADMIN_PASS
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]

def find_user(token, username):
    """Find user by username"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users",
        headers=headers,
        params={"username": username, "exact": "true"}
    )
    response.raise_for_status()
    users = response.json()
    return users[0] if users else None

def find_group(token, groupname):
    """Find group by name"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/groups",
        headers=headers,
        params={"search": groupname}
    )
    response.raise_for_status()
    groups = response.json()
    return next((g for g in groups if g["name"] == groupname), None)

def add_user_to_group(token, user_id, group_id):
    """Add user to group"""
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.put(
        f"{KEYCLOAK_URL}/admin/realms/{REALM}/users/{user_id}/groups/{group_id}",
        headers=headers
    )
    response.raise_for_status()

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 add-user-to-group.py <username> <groupname>")
        print("Example: python3 add-user-to-group.py aaron uc1-admins")
        sys.exit(1)

    username = sys.argv[1]
    groupname = sys.argv[2]

    print(f"Adding user '{username}' to group '{groupname}'...")

    try:
        token = get_admin_token()
        print("✓ Authenticated")

        user = find_user(token, username)
        if not user:
            print(f"✗ User '{username}' not found")
            sys.exit(1)
        print(f"✓ Found user: {user['username']} ({user['email']})")

        group = find_group(token, groupname)
        if not group:
            print(f"✗ Group '{groupname}' not found")
            sys.exit(1)
        print(f"✓ Found group: {group['name']}")

        add_user_to_group(token, user["id"], group["id"])
        print(f"✓ User '{username}' added to group '{groupname}'")

    except httpx.HTTPStatusError as e:
        print(f"✗ HTTP Error: {e.response.status_code}")
        print(f"  {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**Usage:**
```bash
python3 scripts/add-user-to-group.py aaron uc1-admins
python3 scripts/add-user-to-group.py john uc1-users
```

---

## 7. Testing Strategy

### Test Case 1: Admin User with uc1-admins Group

**Setup:**
1. User `aaron` is added to `uc1-admins` group in Keycloak
2. Login to https://your-domain.com

**Expected Results:**
- User redirected to Keycloak login
- After successful login, redirected to `/admin` dashboard
- User role in session: `"role": "admin"`
- Logs show: `User 'aaron' mapped to role 'admin' via group/role 'uc1-admins'`

**Verification:**
```bash
# Check ops-center logs
docker logs ops-center-direct 2>&1 | grep "mapped to role"

# Expected output:
# INFO: User 'aaron' mapped to role 'admin' via group/role 'uc1-admins'
```

### Test Case 2: Regular User with uc1-users Group

**Setup:**
1. Create test user in Keycloak (e.g., `testuser`)
2. Add user to `uc1-users` group
3. Login to https://your-domain.com

**Expected Results:**
- User role: `"role": "user"`
- User can access `/dashboard` but NOT `/admin`
- Accessing `/admin` returns 403 Forbidden

**Verification:**
```bash
# Try to access admin endpoint
curl -H "Cookie: session_token=..." https://your-domain.com/api/v1/auth/users

# Expected: 403 Forbidden
```

### Test Case 3: User with No Groups (Default to Viewer)

**Setup:**
1. Create user in Keycloak without any group assignment
2. Login to https://your-domain.com

**Expected Results:**
- User role: `"role": "viewer"`
- User has read-only access
- Logs show: `No role mapping found for user '...', defaulting to 'viewer'`

### Test Case 4: User with Multiple Groups (Highest Priority Wins)

**Setup:**
1. User is in both `uc1-users` AND `uc1-admins` groups
2. Login to https://your-domain.com

**Expected Results:**
- User role: `"role": "admin"` (admin has higher priority)
- User has full admin access

### Test Case 5: Legacy Admin Username (Emergency Access)

**Setup:**
1. User `akadmin` (legacy admin)
2. NOT in any groups
3. Login to https://your-domain.com

**Expected Results:**
- User role: `"role": "admin"` (from legacy hardcoded list)
- Logs show WARNING: `User 'akadmin' using LEGACY admin access`

### Test Case 6: Token Contains Groups Claim

**Setup:**
1. Use Keycloak token evaluation tool
2. Generate token for user in `uc1-admins` group

**Expected Token:**
```json
{
  "groups": ["/uc1-admins"],
  "email": "admin@example.com",
  "preferred_username": "aaron"
}
```

**Verification:**
```bash
# Decode JWT token
curl -s https://auth.your-domain.com/realms/uchub/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer <ACCESS_TOKEN>" | jq .groups
```

---

## 8. Migration Checklist

### Pre-Migration

- [ ] **Backup Current Configuration**
  - [ ] Export current Keycloak realm: `uchub`
  - [ ] Backup role_mapper.py
  - [ ] Backup server.py
  - [ ] Document all current admin users

- [ ] **Verify Admin Access**
  - [ ] Can login to Keycloak Admin Console
  - [ ] Admin credentials work: `admin` / `your-admin-password`
  - [ ] Can access Keycloak Admin REST API

- [ ] **Review Current Users**
  - [ ] List all users with admin access
  - [ ] Identify which users need which roles
  - [ ] Create user-to-group mapping plan

### Phase 1: Keycloak Configuration

- [ ] **Create Groups**
  - [ ] Create `uc1-admins` group
  - [ ] Create `uc1-power-users` group
  - [ ] Create `uc1-users` group
  - [ ] Create `uc1-viewers` group

- [ ] **Configure Group Mapper**
  - [ ] Verify `groups` client scope exists
  - [ ] Add Group Membership mapper if needed
  - [ ] Set mapper to include full group path
  - [ ] Add `groups` scope to ops-center client as default
  - [ ] Test token contains `groups` claim

- [ ] **Assign Users to Groups**
  - [ ] Add `admin@example.com` to `uc1-admins`
  - [ ] Add other admin users to `uc1-admins`
  - [ ] Add regular users to appropriate groups

### Phase 2: Code Updates

- [ ] **Update role_mapper.py**
  - [ ] Add `uc1-admins` to ROLE_MAPPINGS["admin"]
  - [ ] Add `uc1-power-users` to ROLE_MAPPINGS["power_user"]
  - [ ] Add `uc1-users` to ROLE_MAPPINGS["user"]
  - [ ] Add `uc1-viewers` to ROLE_MAPPINGS["viewer"]
  - [ ] Update hardcoded admin list (reduce to emergency only)
  - [ ] Add detailed logging for group detection

- [ ] **Update Documentation**
  - [ ] Update ROLE_MAPPING.md
  - [ ] Update KEYCLOAK_SETUP.md
  - [ ] Add this research doc to docs folder
  - [ ] Update README if applicable

- [ ] **Create Admin Scripts (Optional)**
  - [ ] Create create-keycloak-groups.py
  - [ ] Create add-user-to-group.py
  - [ ] Test scripts in non-production environment

### Phase 3: Testing

- [ ] **Unit Tests**
  - [ ] Run role_mapper.py test suite
  - [ ] Verify group extraction logic works
  - [ ] Test token parsing with groups claim

- [ ] **Integration Tests**
  - [ ] Test admin user login (in uc1-admins group)
  - [ ] Test regular user login (in uc1-users group)
  - [ ] Test user with no groups (default to viewer)
  - [ ] Test user with multiple groups (priority check)
  - [ ] Test legacy admin access (akadmin)

- [ ] **End-to-End Tests**
  - [ ] Login via browser as admin user
  - [ ] Verify redirect to /admin dashboard
  - [ ] Check user role in API responses
  - [ ] Test accessing admin-only endpoints
  - [ ] Test accessing user-level endpoints
  - [ ] Test logout and re-login

### Phase 4: Deployment

- [ ] **Deploy to Staging (if available)**
  - [ ] Update role_mapper.py in staging
  - [ ] Test all scenarios
  - [ ] Monitor logs for issues

- [ ] **Deploy to Production**
  - [ ] Create backup of production
  - [ ] Update role_mapper.py
  - [ ] Restart ops-center container
  - [ ] Monitor logs for errors
  - [ ] Test admin login immediately

### Phase 5: Post-Deployment

- [ ] **Monitor Logs**
  - [ ] Check for role mapping errors
  - [ ] Verify group detection working
  - [ ] Check for legacy admin access warnings

- [ ] **User Communication**
  - [ ] Notify admins of new group-based access
  - [ ] Provide instructions for checking group membership
  - [ ] Document how to request group changes

- [ ] **Cleanup (After 2-4 Weeks)**
  - [ ] Remove legacy admin hardcoded list entirely
  - [ ] Remove backward-compatible group names
  - [ ] Archive old documentation

---

## 9. Rollback Plan

### If Issues Occur After Deployment

**Symptoms that Require Rollback:**
- Admin users cannot login
- All users getting "viewer" role
- Groups not appearing in tokens
- 403 errors for legitimate admin users

**Rollback Procedure:**

**Step 1: Revert Code Changes**
```bash
cd /home/muut/Production/UC-1-Pro/services/ops-center/backend
git checkout HEAD -- role_mapper.py
# Or restore from backup
cp role_mapper.py.backup role_mapper.py
```

**Step 2: Restart Container**
```bash
docker restart ops-center-direct
# Or
cd /home/muut/Production/UC-1-Pro/services/ops-center
docker-compose -f docker-compose.direct.yml restart
```

**Step 3: Verify Rollback**
```bash
# Test admin login
curl -I https://your-domain.com

# Check logs
docker logs ops-center-direct --tail 50 | grep "mapped to role"
```

**Step 4: Investigate Issues**
- Check if groups appear in token (use Keycloak token evaluation)
- Verify group mapper is configured correctly
- Check for typos in group names
- Review logs for specific errors

**Permanent Backup Strategy:**
```bash
# Before any changes
cp role_mapper.py role_mapper.py.backup.$(date +%Y%m%d)
git add role_mapper.py
git commit -m "Backup before Keycloak groups migration"
```

---

## 10. Security Considerations

### Current Security Issues (Hardcoded List)

**Problems with Hardcoded Admin List:**
1. **No Audit Trail:** Changes require code deployment
2. **No Centralization:** Each service might have different lists
3. **Username-Based:** Usernames can be guessed or leaked
4. **No Revocation:** Removing admin access requires code change
5. **No Self-Service:** Users can't manage their own access

### Security Benefits of Groups

**Improvements with Keycloak Groups:**
1. **Centralized Management:** One place to manage all access
2. **Audit Trail:** Keycloak logs all group membership changes
3. **Instant Revocation:** Remove user from group immediately
4. **Self-Service Ready:** Can enable user self-service portals later
5. **MFA Integration:** Can require MFA for admin group membership
6. **Time-Based Access:** Can grant temporary group membership
7. **Group Policies:** Can add approval workflows for admin group

### Additional Security Recommendations

**1. Require MFA for Admin Group:**

In Keycloak:
- Go to Authentication → Required Actions
- Enable "Configure OTP" for all users
- Create authentication flow that requires OTP for uc1-admins group

**2. Enable Group Membership Approval:**

- Install Keycloak Group Approval extension (if available)
- Require admin approval for uc1-admins group membership

**3. Audit Group Changes:**

Enable Keycloak event logging:
```bash
# In Keycloak Admin Console
Realm Settings → Events → Event Listeners
- Enable "admin-event-listener"
- Enable "jboss-logging"

Event Types to Log:
- GROUP_MEMBERSHIP_ADDED
- GROUP_MEMBERSHIP_REMOVED
- USER_LOGIN
- USER_LOGIN_ERROR
```

**4. Set Session Timeout for Admin Role:**

In ops-center code, add role-based session timeout:
```python
# In server.py
if user_role == "admin":
    session["expires_at"] = time.time() + (30 * 60)  # 30 min for admins
else:
    session["expires_at"] = time.time() + (24 * 60 * 60)  # 24 hours for others
```

**5. IP Whitelisting for Admin Access (Optional):**

```python
# In server.py, require_admin function
async def require_admin(current_user: dict = Depends(get_current_user), request: Request):
    """Require admin role with optional IP whitelist"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Optional: IP whitelist for admin access
    admin_ip_whitelist = os.environ.get("ADMIN_IP_WHITELIST", "").split(",")
    if admin_ip_whitelist and admin_ip_whitelist[0]:
        client_ip = get_client_ip(request)
        if client_ip not in admin_ip_whitelist:
            logger.warning(f"Admin access denied for IP: {client_ip}")
            raise HTTPException(status_code=403, detail="Admin access from this IP not allowed")

    return current_user
```

---

## Appendix A: Keycloak REST API Quick Reference

### Authentication

```bash
# Get admin token
curl -X POST https://auth.your-domain.com/realms/master/protocol/openid-connect/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=your-admin-password"
```

### Groups

```bash
# List all groups
curl https://auth.your-domain.com/admin/realms/uchub/groups \
  -H "Authorization: Bearer $TOKEN"

# Create group
curl -X POST https://auth.your-domain.com/admin/realms/uchub/groups \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "uc1-admins"}'

# Get group by name
curl "https://auth.your-domain.com/admin/realms/uchub/groups?search=uc1-admins" \
  -H "Authorization: Bearer $TOKEN"

# Delete group
curl -X DELETE https://auth.your-domain.com/admin/realms/uchub/groups/$GROUP_ID \
  -H "Authorization: Bearer $TOKEN"
```

### Users

```bash
# List users
curl https://auth.your-domain.com/admin/realms/uchub/users \
  -H "Authorization: Bearer $TOKEN"

# Search user by username
curl "https://auth.your-domain.com/admin/realms/uchub/users?username=aaron&exact=true" \
  -H "Authorization: Bearer $TOKEN"

# Get user by ID
curl https://auth.your-domain.com/admin/realms/uchub/users/$USER_ID \
  -H "Authorization: Bearer $TOKEN"

# Add user to group
curl -X PUT https://auth.your-domain.com/admin/realms/uchub/users/$USER_ID/groups/$GROUP_ID \
  -H "Authorization: Bearer $TOKEN"

# Remove user from group
curl -X DELETE https://auth.your-domain.com/admin/realms/uchub/users/$USER_ID/groups/$GROUP_ID \
  -H "Authorization: Bearer $TOKEN"

# Get user's groups
curl https://auth.your-domain.com/admin/realms/uchub/users/$USER_ID/groups \
  -H "Authorization: Bearer $TOKEN"
```

---

## Appendix B: Troubleshooting Common Issues

### Issue 1: Groups Not Appearing in Token

**Symptoms:**
- Login successful
- User assigned to group in Keycloak
- But `groups` claim is empty or missing in token

**Diagnosis:**
```bash
# Check token content
curl -s https://auth.your-domain.com/realms/uchub/protocol/openid-connect/userinfo \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq .

# Look for "groups" field
```

**Solutions:**
1. Check if `groups` client scope is assigned to `ops-center` client as **Default** scope
2. Verify Group Membership mapper is configured correctly
3. Check if mapper is added to ID token, access token, AND userinfo
4. Try regenerating token (logout and login again)
5. Check Keycloak logs for errors:
   ```bash
   docker logs uchub-keycloak 2>&1 | grep -i error
   ```

### Issue 2: User Always Gets "Viewer" Role

**Symptoms:**
- User is in `uc1-admins` group in Keycloak
- But ops-center assigns "viewer" role

**Diagnosis:**
```bash
# Check ops-center logs
docker logs ops-center-direct 2>&1 | grep "Extracted groups"

# Should show: Extracted groups: ['uc1-admins'] or similar
```

**Solutions:**
1. Verify group name matches exactly (case-insensitive, but check spelling)
2. Check if group appears with leading slash `/uc1-admins` - update ROLE_MAPPINGS to include both versions
3. Verify user_info contains groups:
   - Add debug logging in `extract_groups_from_user_info`
   - Print raw `user_info` dict
4. Check ROLE_MAPPINGS includes the group name
5. Restart ops-center container after code changes

### Issue 3: "Invalid Code" Error During Login

**Symptoms:**
- Redirected to Keycloak
- Login successful
- But redirect back to ops-center fails
- Error in logs: `type="CODE_TO_TOKEN_ERROR", error="invalid_code"`

**Diagnosis:**
```bash
# Check Keycloak logs
docker logs uchub-keycloak 2>&1 | grep "CODE_TO_TOKEN_ERROR"
```

**Solutions:**
1. Verify redirect URI matches EXACTLY in Keycloak client config
2. Check if ops-center is accessible from internet (for production URLs)
3. Check if EXTERNAL_HOST and EXTERNAL_PROTOCOL are set correctly
4. Try clearing browser cookies and cache
5. Check if Keycloak and ops-center clocks are synchronized (NTP)

### Issue 4: Admin Cannot Access Admin Endpoints

**Symptoms:**
- User is in `uc1-admins` group
- Login successful
- But accessing `/admin` returns 403 Forbidden

**Diagnosis:**
```bash
# Check user's role in session
curl https://your-domain.com/api/v1/auth/me \
  -H "Cookie: session_token=$SESSION_TOKEN" | jq .role

# Should return: "admin"
```

**Solutions:**
1. Check if role is correctly set in session
2. Verify `get_current_user` function returns correct role
3. Check `require_admin` dependency is used on admin routes
4. Clear session and re-login (role is cached in session)
5. Check if session is expired (default 24 hours)

### Issue 5: Keycloak Container Unhealthy

**Symptoms:**
- `docker ps` shows `uchub-keycloak (unhealthy)`
- Cannot access Keycloak UI

**Diagnosis:**
```bash
# Check health status
docker inspect uchub-keycloak --format='{{.State.Health.Status}}'

# Check health logs
docker inspect uchub-keycloak --format='{{range .State.Health.Log}}{{.Output}}{{end}}'

# Check container logs
docker logs uchub-keycloak --tail 100
```

**Solutions:**
1. Check database connection (PostgreSQL must be running)
2. Verify database credentials in environment variables
3. Check if Keycloak is still starting up (can take 1-2 minutes)
4. Check for port conflicts (8080, 9000)
5. Restart Keycloak:
   ```bash
   docker restart uchub-keycloak
   ```

---

## Appendix C: Testing Commands Cheatsheet

```bash
# === Keycloak Admin Token ===
export KC_ADMIN_TOKEN=$(curl -s -X POST \
  https://auth.your-domain.com/realms/master/protocol/openid-connect/token \
  -d "grant_type=password" \
  -d "client_id=admin-cli" \
  -d "username=admin" \
  -d "password=your-admin-password" \
  | jq -r .access_token)

# === List Groups ===
curl -s https://auth.your-domain.com/admin/realms/uchub/groups \
  -H "Authorization: Bearer $KC_ADMIN_TOKEN" | jq .

# === Find User ===
export USER_ID=$(curl -s "https://auth.your-domain.com/admin/realms/uchub/users?username=aaron&exact=true" \
  -H "Authorization: Bearer $KC_ADMIN_TOKEN" | jq -r '.[0].id')

# === Find Group ===
export GROUP_ID=$(curl -s "https://auth.your-domain.com/admin/realms/uchub/groups?search=uc1-admins" \
  -H "Authorization: Bearer $KC_ADMIN_TOKEN" | jq -r '.[0].id')

# === Add User to Group ===
curl -X PUT \
  https://auth.your-domain.com/admin/realms/uchub/users/$USER_ID/groups/$GROUP_ID \
  -H "Authorization: Bearer $KC_ADMIN_TOKEN"

# === Get User's Groups ===
curl -s https://auth.your-domain.com/admin/realms/uchub/users/$USER_ID/groups \
  -H "Authorization: Bearer $KC_ADMIN_TOKEN" | jq .

# === Test Login and Get Token ===
# (Use ops-center's OAuth flow in browser, or use admin token for testing)

# === Check Ops-Center Logs ===
docker logs ops-center-direct --tail 100 | grep -E "role|group|auth"

# === Check Keycloak Logs ===
docker logs uchub-keycloak --tail 100 | grep -E "ERROR|WARN"
```

---

## Conclusion

**Migration from hardcoded admin list to Keycloak groups is straightforward and provides significant benefits:**

✅ **Recommended Approach:**
- Use Keycloak **Groups** (not realm roles)
- Group naming: `uc1-admins`, `uc1-power-users`, `uc1-users`, `uc1-viewers`
- Configure group mapper to include `groups` claim in tokens
- Update `ROLE_MAPPINGS` in `role_mapper.py` to recognize new group names
- Keep legacy admin list for emergency access initially, remove after testing

✅ **Implementation Effort:**
- Keycloak UI configuration: **30 minutes**
- Code updates: **15 minutes**
- Testing: **1 hour**
- Total: **~2 hours**

✅ **Risk Level:** **Low**
- Rollback is simple (revert code changes)
- Can test in staging first
- Legacy admin list provides fallback
- No database migrations needed

✅ **Next Steps:**
1. Follow Phase 1: Configure Keycloak (manual UI steps)
2. Test group appears in token using token evaluation
3. Update role_mapper.py code
4. Test with existing admin user (aaron)
5. Gradually migrate other users to groups
6. Remove legacy hardcoded list after 2-4 weeks

**Questions or Issues?**
- Check Keycloak logs: `docker logs uchub-keycloak`
- Check ops-center logs: `docker logs ops-center-direct`
- Review Appendix B: Troubleshooting
- Use Appendix C: Testing Commands

---

**Document Version:** 1.0
**Last Updated:** October 9, 2025
**Author:** Claude (Research Agent)
**File:** `/home/muut/Production/UC-1-Pro/services/ops-center/docs/KEYCLOAK_GROUPS_RESEARCH.md`
