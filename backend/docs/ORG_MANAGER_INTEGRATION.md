# Organization Manager - Integration Guide

Complete guide for integrating the Organization Manager into UC-Cloud Ops Center.

## Quick Reference

**Module Location**: `/opt/ops-center/backend/org_manager.py`

**Import**:
```python
from org_manager import org_manager, Organization, OrgUser
```

**Storage**: `/opt/ops-center/backend/data/`
- `organizations.json`
- `org_users.json`

---

## Installation Checklist

### 1. Dependencies

All required dependencies are already in `requirements.txt`:
- ✓ `pydantic==2.6.1` - Data models
- ✓ `fastapi==0.110.0` - API framework (if using REST endpoints)

### 2. File Structure

```
backend/
├── org_manager.py           # Main module
├── data/                     # Auto-created on first run
│   ├── organizations.json
│   └── org_users.json
├── docs/
│   ├── ORG_MANAGER_API.md
│   ├── ORG_MANAGER_INTEGRATION.md
│   └── org_manager_examples.py
└── tests/
    └── test_org_manager.py
```

### 3. Permissions

Ensure the application has write access to the data directory:
```bash
mkdir -p /opt/ops-center/backend/data
chmod 755 /opt/ops-center/backend/data
```

---

## Integration Steps

### Step 1: Import the Module

Add to your `server.py` or main application file:

```python
from org_manager import org_manager, Organization, OrgUser
```

### Step 2: Add API Endpoints (Optional)

If using FastAPI, add these endpoints to `server.py`:

```python
from fastapi import HTTPException
from pydantic import BaseModel

# Request models
class CreateOrgRequest(BaseModel):
    name: str
    plan_tier: str = "founders_friend"

class AddUserRequest(BaseModel):
    user_id: str
    role: str = "member"

class UpdateBillingRequest(BaseModel):
    lago_id: Optional[str] = None
    stripe_id: Optional[str] = None

# Endpoints
@app.post("/api/organizations")
async def create_organization(req: CreateOrgRequest, current_user: str = Depends(get_current_user)):
    """Create new organization"""
    try:
        org_id = org_manager.create_organization(req.name, req.plan_tier)
        # Add creator as owner
        org_manager.add_user_to_org(org_id, current_user, role="owner")
        return {"org_id": org_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/organizations/{org_id}")
async def get_organization(org_id: str):
    """Get organization details"""
    org = org_manager.get_org(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@app.get("/api/users/{user_id}/organizations")
async def get_user_organizations(user_id: str):
    """Get user's organizations"""
    orgs = org_manager.get_user_orgs(user_id)
    return {"organizations": orgs, "count": len(orgs)}

@app.post("/api/organizations/{org_id}/users")
async def add_user_to_organization(org_id: str, req: AddUserRequest):
    """Add user to organization"""
    try:
        success = org_manager.add_user_to_org(org_id, req.user_id, req.role)
        if not success:
            raise HTTPException(status_code=404, detail="Organization not found")
        return {"status": "added"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/organizations/{org_id}/users/{user_id}")
async def remove_user_from_organization(org_id: str, user_id: str):
    """Remove user from organization"""
    success = org_manager.remove_user_from_org(org_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User or organization not found")
    return {"status": "removed"}

@app.patch("/api/organizations/{org_id}/billing")
async def update_organization_billing(org_id: str, req: UpdateBillingRequest):
    """Update organization billing IDs"""
    success = org_manager.update_org_billing_ids(
        org_id,
        lago_id=req.lago_id,
        stripe_id=req.stripe_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "updated"}

@app.patch("/api/organizations/{org_id}/plan")
async def update_organization_plan(org_id: str, plan_tier: str):
    """Update organization plan"""
    success = org_manager.update_org_plan(org_id, plan_tier)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"status": "updated", "plan_tier": plan_tier}

@app.get("/api/organizations")
async def list_organizations(
    search: Optional[str] = None,
    plan: Optional[str] = None
):
    """List/search organizations"""
    if search:
        orgs = org_manager.search_organizations(search)
    elif plan:
        orgs = org_manager.get_organizations_by_plan(plan)
    else:
        orgs = org_manager.list_all_organizations()

    return {"organizations": orgs, "count": len(orgs)}
```

### Step 3: Integrate with Authentication

Connect with Keycloak/Authentik user flow:

```python
@app.get("/auth/callback")
async def auth_callback(code: str):
    """Handle OAuth callback"""
    # Exchange code for token
    user_info = await exchange_code_for_user(code)
    user_id = user_info['sub']

    # Check if user has organizations
    user_orgs = org_manager.get_user_orgs(user_id)

    if not user_orgs:
        # First-time user - create personal organization
        org_id = org_manager.create_organization(
            f"{user_info['name']}'s Organization",
            plan_tier="founders_friend"
        )
        org_manager.add_user_to_org(org_id, user_id, role="owner")

    # Redirect to dashboard
    return RedirectResponse(url="/dashboard")
```

### Step 4: Integrate with Billing

Connect with Lago and Stripe:

```python
from billing_manager import create_lago_customer
from stripe_integration import create_stripe_customer

async def setup_organization_billing(org_id: str, org_name: str):
    """Set up billing for new organization"""
    # Create Lago customer
    lago_response = await create_lago_customer(
        external_id=org_id,
        name=org_name
    )

    # Create Stripe customer
    stripe_customer = create_stripe_customer(
        metadata={"org_id": org_id},
        name=org_name
    )

    # Link billing IDs to organization
    org_manager.update_org_billing_ids(
        org_id,
        lago_id=lago_response['customer']['id'],
        stripe_id=stripe_customer.id
    )

    return {
        "lago_id": lago_response['customer']['id'],
        "stripe_id": stripe_customer.id
    }
```

### Step 5: Add Middleware for Organization Context

Create middleware to inject organization context:

```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class OrganizationContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get user from session/token
        user_id = request.state.user_id if hasattr(request.state, 'user_id') else None

        if user_id:
            # Get user's organizations
            user_orgs = org_manager.get_user_orgs(user_id)

            # Get selected org from header or use first
            selected_org_id = request.headers.get('X-Organization-ID')

            if selected_org_id:
                org = org_manager.get_org(selected_org_id)
            elif user_orgs:
                org = user_orgs[0]
            else:
                org = None

            # Inject into request state
            request.state.organization = org
            request.state.user_orgs = user_orgs

        response = await call_next(request)
        return response

# Add to app
app.add_middleware(OrganizationContextMiddleware)
```

---

## Common Use Cases

### Use Case 1: User Registration Flow

```python
async def handle_new_user_registration(user_id: str, email: str, name: str):
    """Complete new user registration"""
    # 1. Create personal organization
    org_name = f"{name}'s Organization"
    org_id = org_manager.create_organization(org_name)

    # 2. Add user as owner
    org_manager.add_user_to_org(org_id, user_id, role="owner")

    # 3. Set up billing
    await setup_organization_billing(org_id, org_name)

    # 4. Send welcome email
    await send_welcome_email(email, org_id)

    return org_id
```

### Use Case 2: Team Invitation

```python
async def invite_user_to_org(org_id: str, inviter_id: str, invitee_email: str, role: str):
    """Invite user to organization"""
    # 1. Check inviter has permission
    inviter_role = org_manager.get_user_role_in_org(org_id, inviter_id)
    if inviter_role not in ['owner', 'billing_admin']:
        raise PermissionError("Only owners and billing admins can invite users")

    # 2. Check org exists
    org = org_manager.get_org(org_id)
    if not org:
        raise ValueError("Organization not found")

    # 3. Create invitation
    invitation_token = create_invitation_token(org_id, invitee_email, role)

    # 4. Send invitation email
    await send_invitation_email(invitee_email, org.name, invitation_token)

    return invitation_token

async def accept_invitation(invitation_token: str, user_id: str):
    """Accept organization invitation"""
    # 1. Validate token
    invitation = validate_invitation_token(invitation_token)

    # 2. Add user to organization
    org_manager.add_user_to_org(
        invitation['org_id'],
        user_id,
        role=invitation['role']
    )

    return invitation['org_id']
```

### Use Case 3: Plan Upgrade Flow

```python
async def upgrade_organization_plan(org_id: str, new_plan: str, user_id: str):
    """Handle plan upgrade"""
    # 1. Check user has billing permissions
    user_role = org_manager.get_user_role_in_org(org_id, user_id)
    if user_role not in ['owner', 'billing_admin']:
        raise PermissionError("Only owners and billing admins can upgrade plans")

    # 2. Get organization
    org = org_manager.get_org(org_id)
    if not org:
        raise ValueError("Organization not found")

    # 3. Validate upgrade path
    plan_hierarchy = {
        "founders_friend": 0,
        "starter": 1,
        "professional": 2,
        "enterprise": 3
    }

    if plan_hierarchy[new_plan] <= plan_hierarchy[org.plan_tier]:
        raise ValueError("Can only upgrade to higher tier")

    # 4. Update in billing systems
    if org.lago_customer_id:
        await update_lago_subscription(org.lago_customer_id, new_plan)

    if org.stripe_customer_id:
        await update_stripe_subscription(org.stripe_customer_id, new_plan)

    # 5. Update in org manager
    org_manager.update_org_plan(org_id, new_plan)

    # 6. Notify team
    await notify_team_of_upgrade(org_id, new_plan)

    return {"status": "upgraded", "new_plan": new_plan}
```

### Use Case 4: Organization Dashboard

```python
@app.get("/api/dashboard")
async def get_dashboard(request: Request, user_id: str = Depends(get_current_user)):
    """Get user's dashboard with all organizations"""
    user_orgs = org_manager.get_user_orgs(user_id)

    dashboard_data = []
    for org in user_orgs:
        # Get user's role
        role = org_manager.get_user_role_in_org(org.id, user_id)

        # Get team size
        users = org_manager.get_org_users(org.id)

        # Get usage data (from other systems)
        usage = await get_organization_usage(org.id)

        dashboard_data.append({
            "org_id": org.id,
            "name": org.name,
            "plan": org.plan_tier,
            "status": org.status,
            "role": role,
            "team_size": len(users),
            "usage": usage,
            "created_at": org.created_at
        })

    return {
        "organizations": dashboard_data,
        "count": len(dashboard_data)
    }
```

### Use Case 5: Multi-Organization Selector

Frontend component to switch between organizations:

```python
@app.get("/api/organizations/selector")
async def get_organization_selector(user_id: str = Depends(get_current_user)):
    """Get organization selector data"""
    user_orgs = org_manager.get_user_orgs(user_id)

    selector_data = []
    for org in user_orgs:
        role = org_manager.get_user_role_in_org(org.id, user_id)

        selector_data.append({
            "id": org.id,
            "name": org.name,
            "plan": org.plan_tier,
            "role": role,
            "icon": get_org_icon(org.plan_tier)
        })

    return {
        "organizations": selector_data,
        "default": selector_data[0]['id'] if selector_data else None
    }
```

---

## Database Migration (Optional)

If you want to migrate to a database later, the file-based storage can be easily exported:

```python
import json
from org_manager import org_manager

def export_to_database():
    """Export organizations to database"""
    # Load all data
    orgs = org_manager.list_all_organizations()

    for org in orgs:
        # Insert into database
        db.organizations.insert({
            "id": org.id,
            "name": org.name,
            "created_at": org.created_at,
            "plan_tier": org.plan_tier,
            "lago_customer_id": org.lago_customer_id,
            "stripe_customer_id": org.stripe_customer_id,
            "status": org.status
        })

        # Insert users
        users = org_manager.get_org_users(org.id)
        for user in users:
            db.org_users.insert({
                "org_id": user.org_id,
                "user_id": user.user_id,
                "role": user.role,
                "joined_at": user.joined_at
            })

    print(f"Exported {len(orgs)} organizations")
```

---

## Testing

Run the test suite:

```bash
cd /opt/ops-center/backend
python -m pytest tests/test_org_manager.py -v
```

Run examples:

```bash
cd /opt/ops-center/backend
python docs/org_manager_examples.py
```

---

## Monitoring & Logging

The module logs all operations. Configure logging in your application:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ops-center/org_manager.log'),
        logging.StreamHandler()
    ]
)

# Operations will be logged automatically:
# 2025-10-13 18:30:00 - org_manager - INFO - Created organization: org_abc123 - Tech Corp
# 2025-10-13 18:30:15 - org_manager - INFO - Added user user_123 to org org_abc123 with role owner
```

---

## Backup Strategy

```bash
# Backup organizations data
#!/bin/bash
BACKUP_DIR="/backups/org_manager"
DATA_DIR="/opt/ops-center/backend/data"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Copy files
cp "$DATA_DIR/organizations.json" "$BACKUP_DIR/organizations_$TIMESTAMP.json"
cp "$DATA_DIR/org_users.json" "$BACKUP_DIR/org_users_$TIMESTAMP.json"

# Keep last 30 days
find "$BACKUP_DIR" -name "*.json" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

---

## Performance Considerations

1. **File Locking**: File operations block until lock is available. For high concurrency, consider:
   - Implementing a cache layer (Redis)
   - Moving to database (PostgreSQL)
   - Using queue system for writes

2. **Read Optimization**: For read-heavy workloads:
   ```python
   from functools import lru_cache
   from datetime import datetime, timedelta

   # Cache organization reads
   org_cache = {}
   cache_ttl = timedelta(minutes=5)

   def get_org_cached(org_id: str):
       if org_id in org_cache:
           cached_org, cached_time = org_cache[org_id]
           if datetime.utcnow() - cached_time < cache_ttl:
               return cached_org

       org = org_manager.get_org(org_id)
       org_cache[org_id] = (org, datetime.utcnow())
       return org
   ```

3. **Scaling**: The current implementation is suitable for:
   - Up to 10,000 organizations
   - Up to 100,000 user-org relationships
   - Moderate write frequency (< 100 writes/sec)

---

## Troubleshooting

### Issue: "Permission denied" on data files

**Solution**:
```bash
sudo chown -R $USER:$USER /opt/ops-center/backend/data
chmod 755 /opt/ops-center/backend/data
```

### Issue: "Organization with name already exists"

**Solution**: This is expected behavior. Use unique names or search before creating:
```python
# Check if org exists first
existing = org_manager.search_organizations("Acme Corp")
if not existing:
    org_id = org_manager.create_organization("Acme Corp")
```

### Issue: Slow file operations

**Solution**: Implement caching or migrate to database:
```python
# Use Redis for caching
import redis

redis_client = redis.Redis(host='localhost', port=6379)

def get_org_with_cache(org_id: str):
    # Try cache first
    cached = redis_client.get(f"org:{org_id}")
    if cached:
        return Organization(**json.loads(cached))

    # Load from file
    org = org_manager.get_org(org_id)
    if org:
        redis_client.setex(
            f"org:{org_id}",
            300,  # 5 min TTL
            json.dumps(org.dict())
        )

    return org
```

---

## Next Steps

1. **Add API endpoints** to `server.py`
2. **Integrate with authentication** flow
3. **Connect billing systems** (Lago/Stripe)
4. **Implement frontend** organization selector
5. **Add team management** UI
6. **Set up monitoring** and alerts

---

## Support

- API Documentation: `docs/ORG_MANAGER_API.md`
- Usage Examples: `docs/org_manager_examples.py`
- Test Suite: `tests/test_org_manager.py`

For questions or issues, check the documentation or run the examples.
