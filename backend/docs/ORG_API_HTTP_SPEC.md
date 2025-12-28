# Organization HTTP API Specification

**File**: `backend/org_api_http.py`
**Purpose**: FastAPI router for organization management operations
**Base Path**: `/api/v1/organizations`
**Authentication**: Required (Keycloak SSO)
**Authorization**: Role-based (admin, moderator, user)

## Dependencies

- **Business Logic**: `org_manager.py` (OrgManager class)
- **Authentication**: Keycloak session validation
- **Audit Logging**: `audit_logger.py`
- **Models**: Pydantic models from `org_manager.py` (Organization, OrgUser)

## Endpoints (14 total)

### 1. Organization CRUD (6 endpoints)

#### GET /api/v1/organizations
**Purpose**: List organizations accessible to user
**Auth**: User role
**Logic**:
- Admin/Moderator: Returns all organizations
- Regular user: Returns only organizations they're members of
**Returns**: `{"organizations": [...]}`

#### POST /api/v1/organizations
**Purpose**: Create new organization
**Auth**: Any authenticated user
**Request Body**:
```json
{
  "name": "Acme Corp",
  "plan_tier": "professional"  // optional, defaults to "trial"
}
```
**Logic**:
- Calls `org_manager.create_organization(name, plan_tier)`
- Automatically adds creator as owner
- Returns org_id
**Returns**: `{"org_id": "org_12345", "name": "Acme Corp", ...}`

#### GET /api/v1/organizations/{org_id}
**Purpose**: Get organization details
**Auth**: Organization member or admin
**Returns**: Full Organization object

#### PUT /api/v1/organizations/{org_id}
**Purpose**: Update organization details
**Auth**: Org owner or admin
**Request Body**:
```json
{
  "name": "Updated Name",  // optional
  "plan_tier": "enterprise",  // optional
  "status": "active"  // optional
}
```
**Logic**: Calls `org_manager.update_org_plan()`, `org_manager.update_org_status()`

#### DELETE /api/v1/organizations/{org_id}
**Purpose**: Delete (soft delete) organization
**Auth**: Org owner or admin
**Logic**: Sets status to "deleted" via `org_manager.update_org_status()`

#### POST /api/v1/organizations/{org_id}/switch
**Purpose**: Switch user's active organization
**Auth**: Organization member
**Logic**: Updates session with new active org_id

---

### 2. Member Management (5 endpoints)

#### GET /api/v1/organizations/{org_id}/members
**Purpose**: List organization members
**Auth**: Organization member
**Returns**:
```json
{
  "members": [
    {
      "user_id": "abc123",
      "email": "user@example.com",
      "role": "owner",
      "joined_at": "2025-10-15T12:00:00Z"
    }
  ]
}
```

#### POST /api/v1/organizations/{org_id}/invite
**Purpose**: Invite user to organization
**Auth**: Org owner or admin
**Request Body**:
```json
{
  "email": "newuser@example.com",
  "role": "member"  // owner, member, billing_admin
}
```
**Logic**:
- Lookup user by email in Keycloak
- Call `org_manager.add_user_to_org(org_id, user_id, role)`
- Send invitation email (TODO: email system integration)

#### DELETE /api/v1/organizations/{org_id}/members/{user_id}
**Purpose**: Remove user from organization
**Auth**: Org owner or admin
**Logic**: Calls `org_manager.remove_user_from_org()`

#### PUT /api/v1/organizations/{org_id}/members/{user_id}/role
**Purpose**: Update member role
**Auth**: Org owner or admin
**Request Body**:
```json
{
  "role": "billing_admin"
}
```
**Logic**: Calls `org_manager.update_user_role()`

#### GET /api/v1/organizations/{org_id}/invitations
**Purpose**: List pending invitations
**Auth**: Org owner or admin
**Returns**: List of pending invitations (TODO: requires invitation table)

---

### 3. Organization Settings (3 endpoints)

#### GET /api/v1/organizations/{org_id}/settings
**Purpose**: Get organization settings
**Auth**: Organization member
**Returns**:
```json
{
  "org_id": "org_123",
  "name": "Acme Corp",
  "plan_tier": "professional",
  "status": "active",
  "lago_customer_id": "lago_abc",
  "stripe_customer_id": "cus_xyz"
}
```

#### PUT /api/v1/organizations/{org_id}/settings
**Purpose**: Update organization settings
**Auth**: Org owner or admin
**Request Body**: Partial updates allowed

#### GET /api/v1/organizations/{org_id}/billing
**Purpose**: Get organization billing information
**Auth**: Org owner or billing_admin
**Integration**: Calls Lago API to get subscription details
**Returns**: Current subscription, usage, invoices

---

## Pydantic Models

```python
class OrganizationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    plan_tier: str = Field(default="trial")

class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    plan_tier: Optional[str] = None
    status: Optional[str] = None

class MemberInvite(BaseModel):
    email: str = Field(..., regex=r"^[\w\.-]+@[\w\.-]+\.\w+$")
    role: str = Field(..., regex="^(owner|member|billing_admin)$")

class MemberRoleUpdate(BaseModel):
    role: str = Field(..., regex="^(owner|member|billing_admin)$")

class OrganizationResponse(BaseModel):
    id: str
    name: str
    created_at: datetime
    plan_tier: str
    status: str
    lago_customer_id: Optional[str]
    stripe_customer_id: Optional[str]

class MemberResponse(BaseModel):
    user_id: str
    email: str
    role: str
    joined_at: datetime
```

---

## Authorization Logic

```python
async def check_org_access(
    org_id: str,
    user_id: str,
    required_role: Optional[str] = None
) -> bool:
    """
    Check if user has access to organization.

    Args:
        org_id: Organization ID
        user_id: User ID
        required_role: Required role (owner, member, billing_admin) or None

    Returns:
        True if user has access, raises HTTPException otherwise
    """
    # Admin/moderator bypass
    if user_role in ['admin', 'moderator']:
        return True

    # Check membership
    user_role_in_org = org_manager.get_user_role_in_org(org_id, user_id)
    if not user_role_in_org:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    # Check required role
    if required_role:
        if user_role_in_org != required_role and user_role_in_org != 'owner':
            raise HTTPException(status_code=403, detail=f"Role {required_role} required")

    return True
```

---

## Audit Logging

All operations should log to `audit_logger`:

```python
await audit_logger.log_custom(
    user_id=user_id,
    action="create_organization",
    resource_type="organization",
    resource_id=org_id,
    details={
        "org_name": name,
        "plan_tier": plan_tier
    }
)
```

---

## Error Handling

- **401 Unauthorized**: Not authenticated
- **403 Forbidden**: Not authorized (wrong role)
- **404 Not Found**: Organization not found
- **400 Bad Request**: Invalid input data
- **409 Conflict**: Duplicate organization name
- **500 Internal Server Error**: Server error

---

## Integration Points

1. **Keycloak**: User lookup by email for invitations
2. **Lago**: Billing information retrieval
3. **PostgreSQL**: May need migration from file storage (future)
4. **Email**: Send invitation emails (future)

---

## Testing Checklist

- [ ] Create organization as regular user
- [ ] List organizations (admin sees all, user sees only theirs)
- [ ] Get organization details (member can view)
- [ ] Update organization (only owner can update)
- [ ] Delete organization (only owner/admin can delete)
- [ ] Add member to organization
- [ ] Remove member from organization
- [ ] Update member role
- [ ] List organization members
- [ ] Get organization billing info
- [ ] Switch active organization
- [ ] Non-member cannot access organization
- [ ] Non-owner cannot update/delete organization
- [ ] Audit logs created for all operations
