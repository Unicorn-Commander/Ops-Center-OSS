# Organization Manager Module

Complete multi-tenant organization management system for UC-Cloud Operations Center.

## Overview

The Organization Manager provides a robust, thread-safe system for managing organizations (tenants), users, and billing integrations within UC-Cloud.

### Key Features

- **Multi-Tenant Architecture**: Each organization is an isolated tenant
- **User Management**: Flexible role-based user-organization relationships
- **Billing Integration**: Native support for Lago and Stripe
- **Thread-Safe Operations**: File locking ensures data consistency
- **Simple Storage**: JSON-based storage with easy backup/migration
- **Comprehensive API**: Full CRUD operations with search and filtering
- **Audit Logging**: All operations logged for compliance
- **Type Safety**: Pydantic models with validation

## Quick Start

```python
from org_manager import org_manager

# Create organization
org_id = org_manager.create_organization("Acme Corp")

# Add user as owner
org_manager.add_user_to_org(org_id, "user_123", role="owner")

# Link billing systems
org_manager.update_org_billing_ids(
    org_id,
    lago_id="lago_cust_abc",
    stripe_id="cus_xyz"
)

# Get user's organizations
user_orgs = org_manager.get_user_orgs("user_123")
```

## File Structure

```
backend/
├── org_manager.py                      # Main module (1,000+ lines)
├── data/                                # Storage directory
│   ├── organizations.json               # Organization records
│   └── org_users.json                   # User-org relationships
├── docs/
│   ├── ORG_MANAGER_README.md           # This file
│   ├── ORG_MANAGER_API.md              # Complete API reference
│   ├── ORG_MANAGER_INTEGRATION.md      # Integration guide
│   └── org_manager_examples.py          # Usage examples
└── tests/
    └── test_org_manager.py              # Test suite (50+ tests)
```

## Data Models

### Organization

```python
Organization(
    id="org_abc123...",                 # Auto-generated
    name="Acme Corporation",            # Required
    created_at=datetime.utcnow(),       # Auto-set
    plan_tier="founders_friend",        # Default
    lago_customer_id="lago_cust_123",   # Optional
    stripe_customer_id="cus_abc",       # Optional
    status="active"                     # active|suspended|deleted
)
```

### OrgUser

```python
OrgUser(
    org_id="org_abc123...",
    user_id="user_alice",               # From Keycloak/Authentik
    role="owner",                       # owner|member|billing_admin
    joined_at=datetime.utcnow()
)
```

## Core Operations

### Organization Management

```python
# Create
org_id = org_manager.create_organization("Company Name")

# Read
org = org_manager.get_org(org_id)

# Update
org_manager.update_org_plan(org_id, "professional")
org_manager.update_org_status(org_id, "suspended")
org_manager.update_org_billing_ids(org_id, lago_id="...", stripe_id="...")

# Query
all_orgs = org_manager.list_all_organizations()
results = org_manager.search_organizations("tech")
pro_orgs = org_manager.get_organizations_by_plan("professional")
```

### User Management

```python
# Add user
org_manager.add_user_to_org(org_id, user_id, role="member")

# Remove user
org_manager.remove_user_from_org(org_id, user_id)

# Update role
org_manager.update_user_role(org_id, user_id, "owner")

# Query
user_orgs = org_manager.get_user_orgs(user_id)
org_users = org_manager.get_org_users(org_id)
role = org_manager.get_user_role_in_org(org_id, user_id)
```

## Thread Safety

All operations use file locking (fcntl) to ensure thread safety:

```python
# Multiple threads can safely create organizations
import threading

def create_org(name):
    return org_manager.create_organization(name)

threads = [
    threading.Thread(target=create_org, args=(f"Corp {i}",))
    for i in range(10)
]

for t in threads:
    t.start()
for t in threads:
    t.join()

# All 10 organizations created safely without conflicts
```

## Integration Points

### 1. Authentication (Keycloak/Authentik)

```python
@app.get("/auth/callback")
async def auth_callback(code: str):
    user_info = await exchange_code(code)
    user_id = user_info['sub']

    # Check if user has organizations
    user_orgs = org_manager.get_user_orgs(user_id)

    if not user_orgs:
        # First login - create personal org
        org_id = org_manager.create_organization(
            f"{user_info['name']}'s Organization"
        )
        org_manager.add_user_to_org(org_id, user_id, role="owner")

    return RedirectResponse("/dashboard")
```

### 2. Billing (Lago & Stripe)

```python
async def setup_billing(org_id: str, org_name: str):
    # Create customers in billing systems
    lago_customer = await create_lago_customer(org_id, org_name)
    stripe_customer = create_stripe_customer(org_id, org_name)

    # Link to organization
    org_manager.update_org_billing_ids(
        org_id,
        lago_id=lago_customer['id'],
        stripe_id=stripe_customer.id
    )
```

### 3. REST API (FastAPI)

```python
@app.post("/api/organizations")
async def create_org(name: str, user: str = Depends(get_current_user)):
    org_id = org_manager.create_organization(name)
    org_manager.add_user_to_org(org_id, user, role="owner")
    return {"org_id": org_id}

@app.get("/api/users/{user_id}/organizations")
async def get_user_orgs(user_id: str):
    orgs = org_manager.get_user_orgs(user_id)
    return {"organizations": orgs}
```

## Testing

Comprehensive test suite with 50+ tests:

```bash
# Run all tests
pytest tests/test_org_manager.py -v

# Run specific test categories
pytest tests/test_org_manager.py -k "test_create" -v
pytest tests/test_org_manager.py -k "test_concurrent" -v
```

Test coverage:
- ✓ Organization CRUD operations
- ✓ User management
- ✓ Billing integration
- ✓ Query operations
- ✓ Thread safety
- ✓ Data persistence
- ✓ Error handling
- ✓ Edge cases

## Examples

Run the examples script to see all features in action:

```bash
python docs/org_manager_examples.py
```

Examples include:
1. Creating organizations
2. Adding users
3. Managing roles
4. Billing integration
5. Plan upgrades
6. User's organizations
7. Searching & filtering
8. Organization lifecycle
9. Error handling
10. Multi-org workflows

## Storage Format

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
    }
  ]
}
```

## Error Handling

The module provides clear error messages:

```python
# ValueError for business logic errors
try:
    org_manager.create_organization("Duplicate Name")
    org_manager.create_organization("Duplicate Name")
except ValueError as e:
    print(e)  # "Organization with name 'Duplicate Name' already exists"

# False return for not found
success = org_manager.update_org_plan("org_fake", "pro")
if not success:
    print("Organization not found")

# None return for no results
org = org_manager.get_org("org_nonexistent")
if org is None:
    print("Organization not found")
```

## Performance

**Current Capacity**:
- ✓ Up to 10,000 organizations
- ✓ Up to 100,000 user-org relationships
- ✓ < 100 writes/second
- ✓ Thread-safe concurrent operations

**Optimization Options**:
1. Add Redis caching layer for reads
2. Migrate to PostgreSQL for larger scale
3. Implement read replicas for high read loads

## Backup & Migration

### Backup

```bash
# Simple file backup
cp data/organizations.json data/organizations.backup.json
cp data/org_users.json data/org_users.backup.json

# Automated backup script provided in integration guide
```

### Migration to Database

```python
# Export function provided in integration guide
def export_to_database():
    orgs = org_manager.list_all_organizations()
    for org in orgs:
        db.organizations.insert(org.dict())
        users = org_manager.get_org_users(org.id)
        for user in users:
            db.org_users.insert(user.dict())
```

## Logging

All operations are logged:

```
2025-10-13 18:30:00 - org_manager - INFO - OrgManager initialized with data_dir: /path/to/data
2025-10-13 18:30:15 - org_manager - INFO - Created organization: org_abc123 - Tech Corp
2025-10-13 18:30:20 - org_manager - INFO - Added user user_123 to org org_abc123 with role owner
2025-10-13 18:30:25 - org_manager - INFO - Updated Lago ID for org_abc123: lago_cust_xyz
```

## Security Considerations

1. **File Permissions**: Ensure data directory is not world-readable
2. **User Validation**: Always validate user_id comes from authenticated session
3. **Role Checks**: Implement permission checks in API layer
4. **Audit Trail**: All operations are logged with timestamps
5. **Backup**: Regular backups of data files

## Roadmap

Future enhancements:
- [ ] PostgreSQL backend adapter
- [ ] Redis caching layer
- [ ] GraphQL API
- [ ] Organization settings/preferences
- [ ] Team management features
- [ ] Audit log export
- [ ] Webhooks for org events
- [ ] Multi-org analytics

## Documentation

- **[API Reference](ORG_MANAGER_API.md)**: Complete API documentation with all methods
- **[Integration Guide](ORG_MANAGER_INTEGRATION.md)**: Step-by-step integration instructions
- **[Examples](org_manager_examples.py)**: 10 complete usage examples
- **[Tests](../tests/test_org_manager.py)**: Comprehensive test suite

## Dependencies

All dependencies already in `requirements.txt`:
- `pydantic==2.6.1` - Data validation and models
- `python-dateutil==2.8.2` - Date handling

No additional dependencies required!

## Support

For questions or issues:
1. Check the [API documentation](ORG_MANAGER_API.md)
2. Review [examples](org_manager_examples.py)
3. Run the test suite
4. Check application logs

## License

Part of UC-Cloud Operations Center
Copyright 2025 Unicorn Commander

---

**Module Status**: ✅ Production Ready

**Version**: 1.0.0

**Last Updated**: October 13, 2025
