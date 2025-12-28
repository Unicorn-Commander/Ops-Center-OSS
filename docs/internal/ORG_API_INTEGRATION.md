# Organization API Integration Guide

## Overview

This document provides instructions for integrating the new Organization API (`org_api.py`) into the Ops-Center backend server.

**Created**: October 22, 2025
**File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/org_api.py`
**Status**: Ready for Integration

---

## 1. Import the Router

Add this import to `/home/muut/Production/UC-Cloud/services/ops-center/backend/server.py`:

```python
# Add this import near the top with other router imports (around line 70-80)
from org_api import router as org_router
```

**Location**: Add after the other router imports like `billing_router`, `subscription_router`, etc.

---

## 2. Register the Router

Add this line to register the router with the FastAPI app:

```python
# Add this with the other router registrations (around line 290-330)
# Organization API
app.include_router(org_router)
```

**Example Context** (based on existing pattern):
```python
# Existing router registrations
app.include_router(billing_router)
app.include_router(local_user_router)

# Add Organization API here
app.include_router(org_router)
```

---

## 3. API Endpoints Summary

The Organization API provides 9 endpoints:

### 1. List Available Roles
```
GET /api/v1/org/roles
```
**Authentication**: None required (public)
**Returns**: List of organization roles with descriptions

### 2. List Organization Members
```
GET /api/v1/org/{org_id}/members
```
**Authentication**: Required (member or higher)
**Returns**: List of all members in the organization

### 3. Add Organization Member
```
POST /api/v1/org/{org_id}/members
Body: {"user_id": "user@example.com", "role": "member"}
```
**Authentication**: Required (owner only)
**Returns**: Success confirmation

### 4. Update Member Role
```
PUT /api/v1/org/{org_id}/members/{user_id}/role
Body: {"role": "billing_admin"}
```
**Authentication**: Required (owner only)
**Returns**: Success confirmation

### 5. Remove Organization Member
```
DELETE /api/v1/org/{org_id}/members/{user_id}
```
**Authentication**: Required (owner only)
**Returns**: Success confirmation
**Protection**: Prevents removing last owner

### 6. Get Organization Statistics
```
GET /api/v1/org/{org_id}/stats
```
**Authentication**: Required (member or higher)
**Returns**: Member counts, role distribution, plan tier

### 7. Get Organization Billing
```
GET /api/v1/org/{org_id}/billing
```
**Authentication**: Required (billing_admin or owner)
**Returns**: Billing info including Lago/Stripe customer IDs

### 8. Get Organization Settings
```
GET /api/v1/org/{org_id}/settings
```
**Authentication**: Required (member or higher)
**Returns**: Organization configuration

### 9. Update Organization Settings
```
PUT /api/v1/org/{org_id}/settings
Body: {"settings": {...}}
```
**Authentication**: Required (owner only)
**Returns**: Updated settings

---

## 4. Authentication & Authorization

### Role Hierarchy

The API implements a role hierarchy for organizations:

```
owner           (Full control)
  └── billing_admin    (Billing + view)
      └── member           (View only)
```

### Access Control

- **Admin Users**: System admins bypass all org checks (full access to all orgs)
- **Organization Members**: Access based on role hierarchy
- **Non-Members**: No access (403 Forbidden)

### Permission Levels

| Endpoint | Required Role |
|----------|--------------|
| List roles | None (public) |
| List members | member+ |
| Add member | owner |
| Update role | owner |
| Remove member | owner |
| View stats | member+ |
| View billing | billing_admin+ |
| View settings | member+ |
| Update settings | owner |

---

## 5. Testing the Integration

### Step 1: Restart the Backend

```bash
cd /home/muut/Production/UC-Cloud
docker restart ops-center-direct
```

### Step 2: Check Container Logs

```bash
docker logs ops-center-direct -f
```

Look for:
```
INFO:     Application startup complete.
```

### Step 3: Test Endpoints

#### Test 1: List Available Roles (Public)
```bash
curl http://localhost:8084/api/v1/org/roles
```

**Expected Response**:
```json
{
  "roles": [
    {
      "id": "owner",
      "name": "Owner",
      "description": "Full organization control...",
      "permissions": ["manage_members", "manage_billing", ...]
    },
    ...
  ]
}
```

#### Test 2: List Organization Members (Authenticated)
```bash
# First, get session token by logging in
curl -X POST http://localhost:8084/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Use session token in cookie
curl http://localhost:8084/api/v1/org/org_12345/members \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"
```

**Expected Response**:
```json
{
  "members": [
    {
      "user_id": "user@example.com",
      "role": "owner",
      "joined_at": "2025-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### Test 3: Get Organization Stats
```bash
curl http://localhost:8084/api/v1/org/org_12345/stats \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN"
```

**Expected Response**:
```json
{
  "total_members": 5,
  "members_by_role": {"owner": 1, "member": 4},
  "created_at": "2025-01-01T00:00:00Z",
  "plan_tier": "professional",
  "status": "active",
  "organization_name": "Acme Corp"
}
```

---

## 6. Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid data, user already exists, etc.)
- **401**: Not authenticated (no session token)
- **403**: Forbidden (insufficient permissions)
- **404**: Not found (organization or user doesn't exist)
- **500**: Internal server error

### Common Error Responses

#### 401 Not Authenticated
```json
{"detail": "Not authenticated"}
```

#### 403 Forbidden
```json
{"detail": "Role 'owner' or higher required"}
```

#### 404 Not Found
```json
{"detail": "Organization not found"}
```

#### 400 Bad Request
```json
{"detail": "User user@example.com already in organization org_12345"}
```

---

## 7. Dependencies

The Organization API requires:

1. **org_manager.py** - Organization management logic (already exists)
2. **Redis Sessions** - For session management (already configured)
3. **PostgreSQL** - For organization data storage (already configured)

No additional dependencies need to be installed.

---

## 8. Frontend Integration

The frontend expects these endpoints at `/api/v1/org/*`. Once integrated:

### Update Frontend API Calls

The frontend should already be configured to call these endpoints. Verify in:

- `src/pages/organization/OrganizationTeam.jsx` - Uses `/members` endpoints
- `src/pages/organization/OrganizationRoles.jsx` - Uses `/roles` and role management
- `src/pages/organization/OrganizationSettings.jsx` - Uses `/settings` endpoints
- `src/pages/organization/OrganizationBilling.jsx` - Uses `/billing` endpoint

### Example Frontend Usage

```javascript
// Fetch organization members
const response = await fetch(`/api/v1/org/${orgId}/members`, {
  credentials: 'include'  // Include session cookie
});
const data = await response.json();
console.log(data.members);  // Array of members

// Add a new member
await fetch(`/api/v1/org/${orgId}/members`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  credentials: 'include',
  body: JSON.stringify({
    user_id: 'newuser@example.com',
    role: 'member'
  })
});
```

---

## 9. Known Limitations

1. **Settings Storage**: The `PUT /settings` endpoint currently only returns success but doesn't persist settings. Settings storage needs to be implemented in `org_manager.py` in a future update.

2. **Member Invitations**: Invitation system is referenced in database schema but not yet implemented in the API. This can be added in Phase 2.

3. **Audit Logging**: Organization operations are logged via `logger.info()` but not yet integrated with the audit_logger system. Consider adding audit trail in future.

---

## 10. Verification Checklist

After integration, verify:

- [ ] Backend starts without errors
- [ ] `/api/v1/org/roles` returns roles (public endpoint)
- [ ] `/api/v1/org/{org_id}/members` requires authentication
- [ ] Adding a member works (owner role required)
- [ ] Updating member role works (owner role required)
- [ ] Removing a member works (owner role required)
- [ ] Cannot remove last owner (protection works)
- [ ] Stats endpoint returns accurate data
- [ ] Billing endpoint requires billing_admin or owner
- [ ] Settings endpoints work

---

## 11. Deployment Steps

### Complete Integration Process

```bash
# 1. Navigate to ops-center directory
cd /home/muut/Production/UC-Cloud/services/ops-center

# 2. Edit server.py to add the two lines above
vim backend/server.py

# 3. Rebuild the container (if needed)
docker compose -f docker-compose.direct.yml build

# 4. Restart the service
docker restart ops-center-direct

# 5. Check logs for errors
docker logs ops-center-direct --tail 50

# 6. Test the endpoints
curl http://localhost:8084/api/v1/org/roles
```

---

## 12. Troubleshooting

### Issue: Import Error

**Error**: `ModuleNotFoundError: No module named 'org_api'`

**Solution**: Ensure `org_api.py` is in the `/app/` directory inside the container:
```bash
docker exec ops-center-direct ls -l /app/org_api.py
```

If missing, copy it:
```bash
docker cp backend/org_api.py ops-center-direct:/app/
docker restart ops-center-direct
```

### Issue: 404 Not Found on Endpoints

**Error**: All `/api/v1/org/*` endpoints return 404

**Solution**: Verify router is registered in `server.py`:
```bash
docker exec ops-center-direct grep "org_router" /app/server.py
```

Should show:
```python
from org_api import router as org_router
app.include_router(org_router)
```

### Issue: Organization Not Found

**Error**: `{"detail": "Organization not found"}`

**Solution**: Create a test organization:
```bash
docker exec ops-center-direct python3 -c "
from org_manager import org_manager
org_id = org_manager.create_organization('Test Org', 'professional')
print(f'Created organization: {org_id}')
"
```

### Issue: User Has No Organization

**Error**: `{"detail": "User has no organization"}`

**Solution**: Add user to an organization:
```bash
docker exec ops-center-direct python3 -c "
from org_manager import org_manager
org_manager.add_user_to_org('org_12345', 'user@example.com', 'owner')
print('User added to organization')
"
```

---

## 13. Next Steps

After successful integration:

1. **Test all 9 endpoints** - Verify each endpoint works correctly
2. **Frontend Integration** - Connect frontend pages to these endpoints
3. **Audit Logging** - Add organization operations to audit log
4. **Settings Persistence** - Implement settings storage in org_manager
5. **Invitation System** - Implement email invitations for new members
6. **Documentation** - Update API documentation with these endpoints

---

## Support

For issues or questions:
- Check container logs: `docker logs ops-center-direct`
- Review `org_manager.py` for available methods
- Test endpoints with curl before frontend integration

---

**File Location**: `/home/muut/Production/UC-Cloud/services/ops-center/ORG_API_INTEGRATION.md`
**API File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/org_api.py`
**Status**: Ready for Integration
