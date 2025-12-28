# Organization Manager - Quick Reference

One-page cheat sheet for common operations.

## Import

```python
from org_manager import org_manager, Organization, OrgUser
```

## Organizations

```python
# Create
org_id = org_manager.create_organization("Company Name")
org_id = org_manager.create_organization("Company", plan_tier="professional")

# Get
org = org_manager.get_org("org_123")  # Returns Organization or None

# Update Plan
org_manager.update_org_plan("org_123", "enterprise")  # Returns bool

# Update Status
org_manager.update_org_status("org_123", "suspended")  # active|suspended|deleted

# Update Billing
org_manager.update_org_billing_ids(
    "org_123",
    lago_id="lago_cust_xyz",
    stripe_id="cus_abc"
)

# List All
all_orgs = org_manager.list_all_organizations()  # Returns List[Organization]

# Search
results = org_manager.search_organizations("tech")  # Returns List[Organization]

# Filter by Plan
pro_orgs = org_manager.get_organizations_by_plan("professional")  # Returns List[Organization]
```

## Users

```python
# Add User
org_manager.add_user_to_org("org_123", "user_alice", role="owner")  # owner|member|billing_admin

# Remove User
org_manager.remove_user_from_org("org_123", "user_bob")  # Returns bool

# Update Role
org_manager.update_user_role("org_123", "user_alice", "billing_admin")  # Returns bool

# Get User's Organizations
user_orgs = org_manager.get_user_orgs("user_123")  # Returns List[Organization]

# Get Organization's Users
org_users = org_manager.get_org_users("org_123")  # Returns List[OrgUser]

# Get User's Role
role = org_manager.get_user_role_in_org("org_123", "user_alice")  # Returns str or None
```

## Models

```python
# Organization
Organization(
    id: str,                    # org_{uuid}
    name: str,                  # 1-200 chars
    created_at: datetime,
    plan_tier: str,             # Default: "founders_friend"
    lago_customer_id: str,      # Optional
    stripe_customer_id: str,    # Optional
    status: str                 # active|suspended|deleted
)

# OrgUser
OrgUser(
    org_id: str,
    user_id: str,
    role: str,                  # owner|member|billing_admin
    joined_at: datetime
)
```

## Common Patterns

### New User Registration

```python
def register_user(user_id: str, name: str):
    org_id = org_manager.create_organization(f"{name}'s Organization")
    org_manager.add_user_to_org(org_id, user_id, role="owner")
    return org_id
```

### User Dashboard

```python
def get_dashboard(user_id: str):
    orgs = org_manager.get_user_orgs(user_id)
    return [
        {
            "org_id": org.id,
            "name": org.name,
            "plan": org.plan_tier,
            "role": org_manager.get_user_role_in_org(org.id, user_id),
            "team_size": len(org_manager.get_org_users(org.id))
        }
        for org in orgs
    ]
```

### Billing Setup

```python
def setup_billing(org_id: str):
    lago_id = create_lago_customer(org_id)
    stripe_id = create_stripe_customer(org_id)
    org_manager.update_org_billing_ids(org_id, lago_id, stripe_id)
```

### Plan Upgrade

```python
def upgrade_plan(org_id: str, new_plan: str):
    org = org_manager.get_org(org_id)
    update_lago_subscription(org.lago_customer_id, new_plan)
    update_stripe_subscription(org.stripe_customer_id, new_plan)
    org_manager.update_org_plan(org_id, new_plan)
```

### Team Invitation

```python
def invite_to_org(org_id: str, inviter_id: str, invitee_id: str):
    inviter_role = org_manager.get_user_role_in_org(org_id, inviter_id)
    if inviter_role in ['owner', 'billing_admin']:
        org_manager.add_user_to_org(org_id, invitee_id, role="member")
        return True
    return False
```

## Error Handling

```python
# ValueError - Business logic errors
try:
    org_manager.create_organization("Duplicate")
    org_manager.create_organization("Duplicate")
except ValueError as e:
    print(f"Error: {e}")

# False - Resource not found
success = org_manager.update_org_plan("org_fake", "pro")
if not success:
    print("Organization not found")

# None - No results
org = org_manager.get_org("org_nonexistent")
if org is None:
    print("Not found")
```

## Return Types

```python
create_organization()           -> str (org_id)
get_org()                       -> Optional[Organization]
update_org_billing_ids()        -> bool
update_org_plan()               -> bool
update_org_status()             -> bool
add_user_to_org()               -> bool
remove_user_from_org()          -> bool
update_user_role()              -> bool
get_user_orgs()                 -> List[Organization]
get_org_users()                 -> List[OrgUser]
get_user_role_in_org()          -> Optional[str]
list_all_organizations()        -> List[Organization]
search_organizations()          -> List[Organization]
get_organizations_by_plan()     -> List[Organization]
```

## Storage Location

```
/home/muut/Production/UC-Cloud/services/ops-center/backend/data/
├── organizations.json
└── org_users.json
```

## Thread Safety

✅ All operations are thread-safe using file locking (fcntl)

## Testing

```bash
# Run tests
pytest tests/test_org_manager.py -v

# Run examples
python docs/org_manager_examples.py
```

## Documentation

- **README**: `docs/ORG_MANAGER_README.md`
- **API Reference**: `docs/ORG_MANAGER_API.md`
- **Integration Guide**: `docs/ORG_MANAGER_INTEGRATION.md`
- **Examples**: `docs/org_manager_examples.py`

## Valid Values

**Roles**: `owner`, `member`, `billing_admin`

**Statuses**: `active`, `suspended`, `deleted`

**Plans**: `founders_friend`, `starter`, `professional`, `enterprise`

---

**Quick Start in 3 Lines**:

```python
from org_manager import org_manager
org_id = org_manager.create_organization("My Company")
org_manager.add_user_to_org(org_id, "user_123", role="owner")
```
