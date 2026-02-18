# Organization Manager API Documentation

Complete API reference for the Organization Manager module.

## Table of Contents
- [Overview](#overview)
- [Models](#models)
- [OrgManager Class](#orgmanager-class)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [Thread Safety](#thread-safety)
- [Error Handling](#error-handling)

---

## Overview

The Organization Manager provides a complete multi-tenant organization management system with:
- Thread-safe file-based storage with locking
- Organization lifecycle management
- User-organization relationship management
- Billing system integration (Lago & Stripe)
- Comprehensive audit logging

**Storage Location**: `/opt/ops-center/backend/data/`
- `organizations.json` - Organization records
- `org_users.json` - User-organization relationships

---

## Models

### Organization

Represents a tenant organization in the system.

```python
class Organization(BaseModel):
    id: str                           # Format: org_{uuid4}
    name: str                          # 1-200 characters
    created_at: datetime               # UTC timestamp
    plan_tier: str = "founders_friend" # Subscription plan
    lago_customer_id: Optional[str]    # Lago billing ID
    stripe_customer_id: Optional[str]  # Stripe billing ID
    status: str = "active"             # active|suspended|deleted
```

**Validations**:
- `id` must start with `org_`
- `name` must be 1-200 characters
- `status` must be one of: `active`, `suspended`, `deleted`

### OrgUser

Represents user membership in an organization.

```python
class OrgUser(BaseModel):
    org_id: str                    # Organization ID
    user_id: str                   # User ID from auth system
    role: str                      # owner|member|billing_admin
    joined_at: datetime            # UTC timestamp
```

**Validations**:
- `role` must be one of: `owner`, `member`, `billing_admin`

---

## OrgManager Class

### Initialization

```python
from org_manager import org_manager  # Use global singleton

# Or create custom instance
from org_manager import OrgManager
custom_manager = OrgManager(data_dir="/custom/path")
```

**Parameters**:
- `data_dir` (str): Directory for data files. Default: `/opt/ops-center/backend/data`

---

## Quick Start

```python
from org_manager import org_manager

# 1. Create organization
org_id = org_manager.create_organization("Acme Corp")

# 2. Add users
org_manager.add_user_to_org(org_id, "user_123", role="owner")
org_manager.add_user_to_org(org_id, "user_456", role="member")

# 3. Connect billing
org_manager.update_org_billing_ids(
    org_id,
    lago_id="lago_cust_abc",
    stripe_id="cus_xyz"
)

# 4. Upgrade plan
org_manager.update_org_plan(org_id, "professional")

# 5. Query user's organizations
user_orgs = org_manager.get_user_orgs("user_123")
```

---

## API Reference

### Organization Operations

#### create_organization()

Create a new organization.

```python
def create_organization(
    name: str,
    plan_tier: str = "founders_friend"
) -> str
```

**Parameters**:
- `name` (str): Organization name (required, 1-200 chars)
- `plan_tier` (str): Initial plan tier (default: "founders_friend")

**Returns**: `str` - The new organization ID (format: `org_{uuid}`)

**Raises**:
- `ValueError`: If name is empty or duplicate

**Example**:
```python
org_id = org_manager.create_organization("Tech Startup Inc")
# Returns: "org_abc123def456..."

# With custom plan
org_id = org_manager.create_organization(
    "Enterprise Corp",
    plan_tier="enterprise"
)
```

---

#### get_org()

Retrieve an organization by ID.

```python
def get_org(org_id: str) -> Optional[Organization]
```

**Parameters**:
- `org_id` (str): Organization ID to retrieve

**Returns**: `Organization` object or `None` if not found

**Example**:
```python
org = org_manager.get_org("org_123")
if org:
    print(f"Name: {org.name}")
    print(f"Plan: {org.plan_tier}")
    print(f"Status: {org.status}")
```

---

#### update_org_billing_ids()

Update organization's billing system IDs.

```python
def update_org_billing_ids(
    org_id: str,
    lago_id: Optional[str] = None,
    stripe_id: Optional[str] = None
) -> bool
```

**Parameters**:
- `org_id` (str): Organization ID
- `lago_id` (str, optional): Lago customer ID
- `stripe_id` (str, optional): Stripe customer ID

**Returns**: `bool` - True if successful, False if org not found

**Example**:
```python
# Update both IDs
success = org_manager.update_org_billing_ids(
    "org_123",
    lago_id="lago_cust_abc123",
    stripe_id="cus_xyz789"
)

# Update only Lago ID
org_manager.update_org_billing_ids(
    "org_123",
    lago_id="lago_cust_new"
)
```

---

#### update_org_plan()

Update organization's subscription plan.

```python
def update_org_plan(org_id: str, plan_tier: str) -> bool
```

**Parameters**:
- `org_id` (str): Organization ID
- `plan_tier` (str): New plan tier

**Returns**: `bool` - True if successful, False if org not found

**Example**:
```python
# Upgrade to professional
org_manager.update_org_plan("org_123", "professional")

# Downgrade to starter
org_manager.update_org_plan("org_123", "starter")
```

---

#### update_org_status()

Update organization status.

```python
def update_org_status(org_id: str, status: str) -> bool
```

**Parameters**:
- `org_id` (str): Organization ID
- `status` (str): New status (active|suspended|deleted)

**Returns**: `bool` - True if successful, False if org not found

**Example**:
```python
# Suspend organization
org_manager.update_org_status("org_123", "suspended")

# Reactivate
org_manager.update_org_status("org_123", "active")

# Soft delete
org_manager.update_org_status("org_123", "deleted")
```

---

### User-Organization Operations

#### add_user_to_org()

Add a user to an organization.

```python
def add_user_to_org(
    org_id: str,
    user_id: str,
    role: str = "member"
) -> bool
```

**Parameters**:
- `org_id` (str): Organization ID
- `user_id` (str): User ID from auth system
- `role` (str): User role (owner|member|billing_admin)

**Returns**: `bool` - True if successful, False if org not found

**Raises**:
- `ValueError`: If role is invalid or user already in org

**Example**:
```python
# Add as owner
org_manager.add_user_to_org("org_123", "user_alice", role="owner")

# Add as member
org_manager.add_user_to_org("org_123", "user_bob", role="member")

# Add as billing admin
org_manager.add_user_to_org("org_123", "user_carol", role="billing_admin")
```

---

#### remove_user_from_org()

Remove a user from an organization.

```python
def remove_user_from_org(org_id: str, user_id: str) -> bool
```

**Parameters**:
- `org_id` (str): Organization ID
- `user_id` (str): User ID to remove

**Returns**: `bool` - True if successful, False if not found

**Example**:
```python
org_manager.remove_user_from_org("org_123", "user_bob")
```

---

#### update_user_role()

Update a user's role in an organization.

```python
def update_user_role(
    org_id: str,
    user_id: str,
    new_role: str
) -> bool
```

**Parameters**:
- `org_id` (str): Organization ID
- `user_id` (str): User ID
- `new_role` (str): New role (owner|member|billing_admin)

**Returns**: `bool` - True if successful, False if not found

**Example**:
```python
# Promote member to owner
org_manager.update_user_role("org_123", "user_bob", "owner")

# Demote owner to member
org_manager.update_user_role("org_123", "user_alice", "member")
```

---

#### get_user_orgs()

Get all organizations a user belongs to.

```python
def get_user_orgs(user_id: str) -> List[Organization]
```

**Parameters**:
- `user_id` (str): User ID from auth system

**Returns**: List of `Organization` objects

**Example**:
```python
user_orgs = org_manager.get_user_orgs("user_123")
for org in user_orgs:
    role = org_manager.get_user_role_in_org(org.id, "user_123")
    print(f"{org.name} - {role}")
```

---

#### get_org_users()

Get all users in an organization.

```python
def get_org_users(org_id: str) -> List[OrgUser]
```

**Parameters**:
- `org_id` (str): Organization ID

**Returns**: List of `OrgUser` objects

**Example**:
```python
users = org_manager.get_org_users("org_123")
for user in users:
    print(f"{user.user_id}: {user.role} (joined {user.joined_at})")
```

---

#### get_user_role_in_org()

Get a user's role in a specific organization.

```python
def get_user_role_in_org(
    org_id: str,
    user_id: str
) -> Optional[str]
```

**Parameters**:
- `org_id` (str): Organization ID
- `user_id` (str): User ID

**Returns**: Role string or `None` if user not in org

**Example**:
```python
role = org_manager.get_user_role_in_org("org_123", "user_alice")
if role:
    print(f"Alice is a {role}")
else:
    print("Alice is not in this org")
```

---

### Query Operations

#### list_all_organizations()

Get all organizations in the system.

```python
def list_all_organizations() -> List[Organization]
```

**Returns**: List of all `Organization` objects

**Example**:
```python
all_orgs = org_manager.list_all_organizations()
print(f"Total organizations: {len(all_orgs)}")
```

---

#### search_organizations()

Search organizations by name.

```python
def search_organizations(query: str) -> List[Organization]
```

**Parameters**:
- `query` (str): Search query (case-insensitive)

**Returns**: List of matching `Organization` objects

**Example**:
```python
results = org_manager.search_organizations("tech")
for org in results:
    print(org.name)
# Output: Tech Startup Inc, TechCorp, etc.
```

---

#### get_organizations_by_plan()

Get organizations on a specific plan tier.

```python
def get_organizations_by_plan(plan_tier: str) -> List[Organization]
```

**Parameters**:
- `plan_tier` (str): Plan tier to filter by

**Returns**: List of matching `Organization` objects

**Example**:
```python
enterprise_orgs = org_manager.get_organizations_by_plan("enterprise")
print(f"Enterprise customers: {len(enterprise_orgs)}")
```

---

## Thread Safety

All operations are thread-safe using file locking (fcntl):

```python
# Multiple threads can safely create organizations
import threading

def create_org(name):
    org_id = org_manager.create_organization(name)
    return org_id

threads = [
    threading.Thread(target=create_org, args=(f"Corp {i}",))
    for i in range(10)
]

for thread in threads:
    thread.start()

for thread in threads:
    thread.join()

# All 10 organizations created safely
```

**Locking Mechanism**:
- Exclusive locks (LOCK_EX) on file operations
- Blocks until lock is available
- Automatic lock release on completion
- Works across processes and threads

---

## Error Handling

### Common Errors

#### ValueError Exceptions

```python
# 1. Duplicate organization name
try:
    org_manager.create_organization("Acme Corp")
    org_manager.create_organization("Acme Corp")  # Raises ValueError
except ValueError as e:
    print(f"Error: {e}")
    # Output: Organization with name 'Acme Corp' already exists

# 2. Invalid role
try:
    org_manager.add_user_to_org("org_123", "user_1", role="admin")
except ValueError as e:
    print(f"Error: {e}")
    # Output: Role must be one of: owner, member, billing_admin

# 3. User already in organization
try:
    org_manager.add_user_to_org("org_123", "user_1", role="member")
    org_manager.add_user_to_org("org_123", "user_1", role="owner")
except ValueError as e:
    print(f"Error: {e}")
    # Output: User user_1 already in organization org_123
```

#### False Returns (Resource Not Found)

Operations that return `bool` return `False` when resource not found:

```python
# Update non-existent organization
success = org_manager.update_org_plan("org_fake", "professional")
if not success:
    print("Organization not found")

# Add user to non-existent org
success = org_manager.add_user_to_org("org_fake", "user_1")
if not success:
    print("Organization not found")
```

#### None Returns (No Results)

Query operations return `None` or empty lists when no results:

```python
# Get non-existent organization
org = org_manager.get_org("org_fake")
if org is None:
    print("Organization not found")

# Get role for user not in org
role = org_manager.get_user_role_in_org("org_123", "user_nonexistent")
if role is None:
    print("User not in organization")

# Search with no results
results = org_manager.search_organizations("nonexistent")
if not results:
    print("No organizations found")
```

---

## Best Practices

### 1. Organization Creation Workflow

```python
# Complete organization setup
def setup_new_organization(name, owner_user_id, plan="founders_friend"):
    # 1. Create organization
    org_id = org_manager.create_organization(name, plan_tier=plan)

    # 2. Add owner
    org_manager.add_user_to_org(org_id, owner_user_id, role="owner")

    # 3. Create billing customers (pseudo-code)
    lago_id = create_lago_customer(org_id, name)
    stripe_id = create_stripe_customer(org_id, name)

    # 4. Link billing IDs
    org_manager.update_org_billing_ids(org_id, lago_id, stripe_id)

    return org_id
```

### 2. Multi-Org User Dashboard

```python
def get_user_dashboard(user_id):
    """Build user's organization dashboard"""
    orgs = org_manager.get_user_orgs(user_id)

    dashboard = []
    for org in orgs:
        role = org_manager.get_user_role_in_org(org.id, user_id)
        users = org_manager.get_org_users(org.id)

        dashboard.append({
            "org_id": org.id,
            "name": org.name,
            "plan": org.plan_tier,
            "role": role,
            "team_size": len(users),
            "status": org.status
        })

    return dashboard
```

### 3. Plan Upgrade Flow

```python
def upgrade_organization_plan(org_id, new_plan):
    """Handle plan upgrade with validation"""
    # 1. Get current org
    org = org_manager.get_org(org_id)
    if not org:
        raise ValueError("Organization not found")

    # 2. Validate upgrade path
    plan_hierarchy = ["founders_friend", "starter", "professional", "enterprise"]
    current_idx = plan_hierarchy.index(org.plan_tier)
    new_idx = plan_hierarchy.index(new_plan)

    if new_idx <= current_idx:
        raise ValueError("Can only upgrade to higher tier")

    # 3. Update in billing systems (pseudo-code)
    update_lago_subscription(org.lago_customer_id, new_plan)
    update_stripe_subscription(org.stripe_customer_id, new_plan)

    # 4. Update in org manager
    org_manager.update_org_plan(org_id, new_plan)

    return True
```

---

## Integration Examples

### With FastAPI

```python
from fastapi import FastAPI, HTTPException, Depends
from org_manager import org_manager

app = FastAPI()

@app.post("/organizations")
async def create_org(name: str, current_user: str = Depends(get_current_user)):
    """Create new organization"""
    try:
        org_id = org_manager.create_organization(name)
        org_manager.add_user_to_org(org_id, current_user, role="owner")
        return {"org_id": org_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/organizations/{org_id}")
async def get_org(org_id: str):
    """Get organization details"""
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.get("/users/{user_id}/organizations")
async def get_user_orgs(user_id: str):
    """Get user's organizations"""
    orgs = org_manager.get_user_orgs(user_id)
    return {"organizations": orgs}
```

### With Keycloak/Authentik

```python
def sync_keycloak_user_to_org(org_id, keycloak_user_id):
    """Sync Keycloak user to organization"""
    # Get user from Keycloak
    keycloak_user = get_keycloak_user(keycloak_user_id)

    # Add to organization
    org_manager.add_user_to_org(
        org_id,
        keycloak_user_id,
        role="member"
    )

    # Set organization in user attributes
    set_keycloak_user_attribute(
        keycloak_user_id,
        "organization_id",
        org_id
    )
```

---

## Logging

All operations are logged using Python's logging module:

```python
import logging

# Configure logging level
logging.basicConfig(level=logging.INFO)

# Operations will log:
# INFO: Created organization: org_abc123 - Tech Corp
# INFO: Added user user_123 to org org_abc123 with role owner
# INFO: Updated Lago ID for org_abc123: lago_cust_xyz
# WARNING: Organization not found: org_fake
```

---

## File Format

### organizations.json

```json
{
  "org_abc123def456": {
    "id": "org_abc123def456",
    "name": "Acme Corporation",
    "created_at": "2025-10-13T18:30:00",
    "plan_tier": "professional",
    "lago_customer_id": "lago_cust_xyz789",
    "stripe_customer_id": "cus_abc123",
    "status": "active"
  }
}
```

### org_users.json

```json
{
  "org_abc123def456": [
    {
      "org_id": "org_abc123def456",
      "user_id": "user_alice",
      "role": "owner",
      "joined_at": "2025-10-13T18:30:00"
    },
    {
      "org_id": "org_abc123def456",
      "user_id": "user_bob",
      "role": "member",
      "joined_at": "2025-10-13T18:35:00"
    }
  ]
}
```

---

## Support

For issues or questions:
1. Check the examples in `docs/org_manager_examples.py`
2. Run the test suite: `pytest tests/test_org_manager.py`
3. Review logs in the application output

---

## License

Part of UC-Cloud Operations Center
Copyright 2025 Unicorn Commander
