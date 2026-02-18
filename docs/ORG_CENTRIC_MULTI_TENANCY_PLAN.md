# Org-Centric Multi-Tenancy Implementation Plan

**Status**: Planned
**Target**: Q1 2026
**Estimated Effort**: 8-10 hours
**Risk Level**: Low (additive changes, backward compatible)

---

## Executive Summary

Migrate from user-centric tiers to org-centric multi-tenancy where:
- **Organizations** are the billing and access control unit
- **Users** can belong to multiple organizations
- **Tiers** are assigned to organizations, not users
- **App access** is determined by org's tier
- **Resources** (leads, searches, credits) are scoped to org

---

## Current Architecture (User-Centric)

```
┌─────────────────────────────────────────────────────────────┐
│  USER (Keycloak)                                            │
│  └── subscription_tier: vip_founder (attribute)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  subscription_tiers → tier_features → add_ons               │
│  "What APPS can this USER access?"                          │
└─────────────────────────────────────────────────────────────┘
```

### Current Tables (Ops-Center DB: unicorn_db)

| Table | Purpose | Status |
|-------|---------|--------|
| `subscription_tiers` | Tier definitions | ✅ Exists |
| `tier_features` | Tier → feature_key mapping | ✅ Exists |
| `add_ons` | App registry with feature_keys | ✅ Exists |
| `organizations` | Org definitions | ✅ Exists |
| `organization_members` | User → Org mapping | ✅ Exists |
| `organization_subscriptions` | Org billing info | ✅ Exists (needs linking) |

### Current Issues

1. **Two tier systems not connected**: `organization_subscriptions.subscription_plan` vs `subscription_tiers.tier_code`
2. **User tier stored in Keycloak**: Hard to manage, doesn't support multi-org
3. **LoopNet has its own org tables**: Not synced with Ops-Center
4. **No org switcher UI**: Users can't switch between orgs

---

## Target Architecture (Org-Centric)

```
┌─────────────────────────────────────────────────────────────┐
│  USER (Keycloak)                                            │
│  └── No tier attribute (tier comes from org membership)     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  organization_members                                        │
│  └── user_id → organization_id (role: OWNER/ADMIN/MEMBER)   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  organizations                                               │
│  └── tier_id → subscription_tiers                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  tier_features → add_ons                                     │
│  "What APPS can this ORG access?"                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Changes

### 1. Add tier_id to organizations table

```sql
-- Add foreign key to subscription_tiers
ALTER TABLE organizations
ADD COLUMN tier_id INTEGER REFERENCES subscription_tiers(id);

-- Create index for performance
CREATE INDEX idx_organizations_tier_id ON organizations(tier_id);

-- Backfill existing orgs with default tier
UPDATE organizations
SET tier_id = (SELECT id FROM subscription_tiers WHERE tier_code = 'managed')
WHERE tier_id IS NULL;
```

### 2. Add org_id to apps' resource tables

Each app should scope its data by org_id:

```sql
-- LoopNet example (if not already done)
ALTER TABLE companies ADD COLUMN org_id VARCHAR(36) REFERENCES organizations(id);
ALTER TABLE contacts ADD COLUMN org_id VARCHAR(36) REFERENCES organizations(id);
ALTER TABLE uploads ADD COLUMN org_id VARCHAR(36) REFERENCES organizations(id);

-- Center Deep example
ALTER TABLE knowledge_projects ADD COLUMN org_id VARCHAR(36) REFERENCES organizations(id);
ALTER TABLE project_results ADD COLUMN org_id VARCHAR(36) REFERENCES organizations(id);
```

### 3. Create org_app_access view (optional, for performance)

```sql
CREATE OR REPLACE VIEW org_app_access AS
SELECT
    o.id as org_id,
    o.name as org_name,
    st.tier_code,
    tf.feature_key,
    ao.name as app_name,
    ao.launch_url
FROM organizations o
JOIN subscription_tiers st ON o.tier_id = st.id
JOIN tier_features tf ON st.id = tf.tier_id AND tf.enabled = TRUE
JOIN add_ons ao ON tf.feature_key = ao.feature_key AND ao.is_active = TRUE;
```

---

## API Changes

### 1. New Endpoint: Get User's Organizations with App Access

**Endpoint**: `GET /api/v1/users/me/organizations`

**Response**:
```json
{
  "organizations": [
    {
      "id": "org-magic-unicorn",
      "name": "Magic Unicorn",
      "slug": "magic-unicorn",
      "role": "OWNER",
      "tier": {
        "code": "vip_founder",
        "name": "VIP / Founder"
      },
      "apps": [
        {"slug": "center-deep", "name": "Center Deep", "url": "https://search.centerdeep.online"},
        {"slug": "loopnet", "name": "LoopNet Leads", "url": "https://loopnet.centerdeep.online"},
        {"slug": "mandate-map", "name": "Mandate Map", "url": "https://mandatemap.centerdeep.online"}
      ],
      "credits": {
        "remaining": null,
        "limit": null,
        "unlimited": true
      }
    },
    {
      "id": "org-client-abc",
      "name": "Client ABC",
      "role": "MEMBER",
      "tier": {
        "code": "professional",
        "name": "Professional"
      },
      "apps": [
        {"slug": "center-deep", "name": "Center Deep", "url": "https://search.centerdeep.online"},
        {"slug": "loopnet", "name": "LoopNet Leads", "url": "https://loopnet.centerdeep.online"}
      ],
      "credits": {
        "remaining": 5000,
        "limit": 10000,
        "unlimited": false
      }
    }
  ],
  "default_org_id": "org-magic-unicorn"
}
```

**Backend Implementation** (`backend/org_access_api.py`):

```python
@router.get("/users/me/organizations")
async def get_user_organizations(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all organizations user belongs to with app access info."""
    user_id = await get_user_id_from_session(request)

    # Get user's org memberships
    memberships = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.is_active == True
    ).all()

    result = []
    for membership in memberships:
        org = membership.organization
        tier = org.subscription_tier  # via tier_id FK

        # Get apps for this tier
        apps = db.query(AddOn).join(
            TierFeature, AddOn.feature_key == TierFeature.feature_key
        ).filter(
            TierFeature.tier_id == tier.id,
            TierFeature.enabled == True,
            AddOn.is_active == True
        ).all()

        result.append({
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "role": membership.role.value,
            "tier": {
                "code": tier.tier_code,
                "name": tier.tier_name
            },
            "apps": [{"slug": a.slug, "name": a.name, "url": a.launch_url} for a in apps],
            "credits": {
                "remaining": org.credits_remaining,
                "limit": org.credits_limit,
                "unlimited": tier.tier_code == "vip_founder"
            }
        })

    return {"organizations": result, "default_org_id": result[0]["id"] if result else None}
```

### 2. Update my-apps API to use org context

**Endpoint**: `GET /api/v1/my-apps/authorized?org_id={org_id}`

```python
@router.get("/authorized")
async def get_my_apps(
    org_id: Optional[str] = Query(None),
    request: Request,
    db: Session = Depends(get_db)
):
    """Get apps user can access in the specified org context."""
    user_id = await get_user_id_from_session(request)

    if org_id:
        # Verify user is member of this org
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.organization_id == org_id,
            OrganizationMember.is_active == True
        ).first()

        if not membership:
            raise HTTPException(403, "Not a member of this organization")

        org = membership.organization
    else:
        # Get user's default org (first one)
        membership = db.query(OrganizationMember).filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.is_active == True
        ).first()

        if not membership:
            return []  # No orgs, no apps

        org = membership.organization

    # Get apps for org's tier
    tier = org.subscription_tier
    apps = db.query(AddOn).join(
        TierFeature, AddOn.feature_key == TierFeature.feature_key
    ).filter(
        TierFeature.tier_id == tier.id,
        TierFeature.enabled == True,
        AddOn.is_active == True
    ).all()

    return [AppResponse.from_orm(app) for app in apps]
```

### 3. New Endpoint: Switch Organization

**Endpoint**: `POST /api/v1/users/me/switch-org`

```python
@router.post("/users/me/switch-org")
async def switch_organization(
    org_id: str,
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Switch user's active organization context."""
    user_id = await get_user_id_from_session(request)

    # Verify membership
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id,
        OrganizationMember.organization_id == org_id,
        OrganizationMember.is_active == True
    ).first()

    if not membership:
        raise HTTPException(403, "Not a member of this organization")

    # Update session with current org
    session_manager.update_session(request, {"current_org_id": org_id})

    # Set cookie for frontend
    response.set_cookie("current_org_id", org_id, httponly=True, secure=True)

    return {"success": True, "org_id": org_id, "org_name": membership.organization.name}
```

---

## Frontend Changes

### 1. Org Switcher Component

**File**: `src/components/OrgSwitcher.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { useOrganization } from '../contexts/OrganizationContext';

export function OrgSwitcher() {
  const { organizations, currentOrg, switchOrg, loading } = useOrganization();

  if (loading || organizations.length <= 1) {
    return null; // Don't show if only one org
  }

  return (
    <select
      value={currentOrg?.id || ''}
      onChange={(e) => switchOrg(e.target.value)}
      className="org-switcher"
    >
      {organizations.map(org => (
        <option key={org.id} value={org.id}>
          {org.name} ({org.tier.name})
        </option>
      ))}
    </select>
  );
}
```

### 2. Organization Context

**File**: `src/contexts/OrganizationContext.jsx`

```jsx
import React, { createContext, useContext, useState, useEffect } from 'react';

const OrganizationContext = createContext(null);

export function OrganizationProvider({ children }) {
  const [organizations, setOrganizations] = useState([]);
  const [currentOrg, setCurrentOrg] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const fetchOrganizations = async () => {
    try {
      const res = await fetch('/api/v1/users/me/organizations');
      const data = await res.json();
      setOrganizations(data.organizations);

      // Set current org from cookie or default
      const savedOrgId = getCookie('current_org_id') || data.default_org_id;
      const org = data.organizations.find(o => o.id === savedOrgId);
      setCurrentOrg(org || data.organizations[0]);
    } finally {
      setLoading(false);
    }
  };

  const switchOrg = async (orgId) => {
    await fetch('/api/v1/users/me/switch-org', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ org_id: orgId })
    });

    const org = organizations.find(o => o.id === orgId);
    setCurrentOrg(org);

    // Reload page to refresh data in new org context
    window.location.reload();
  };

  return (
    <OrganizationContext.Provider value={{ organizations, currentOrg, switchOrg, loading }}>
      {children}
    </OrganizationContext.Provider>
  );
}

export const useOrganization = () => useContext(OrganizationContext);
```

### 3. Update App Navigation

Add org switcher to the main navigation/header in all apps:

```jsx
// In Layout.jsx or Header.jsx
import { OrgSwitcher } from './OrgSwitcher';

function Header() {
  return (
    <header>
      <Logo />
      <OrgSwitcher />
      <UserMenu />
    </header>
  );
}
```

---

## App Integration Changes

### Each App Needs To:

1. **Read org context from session/cookie**
2. **Scope all queries by org_id**
3. **Include org switcher in UI**
4. **Check app access via org's tier**

### LoopNet Example

```python
# middleware/org_context.py
async def get_current_org(request: Request) -> str:
    """Get current org from session or cookie."""
    org_id = request.cookies.get("current_org_id")

    if not org_id:
        # Fall back to user's default org via Ops-Center API
        user_id = await get_user_id_from_token(request)
        orgs = await ops_center_client.get_user_orgs(user_id)
        org_id = orgs[0]["id"] if orgs else None

    if not org_id:
        raise HTTPException(403, "No organization access")

    return org_id

# All queries scoped by org
@router.get("/companies")
async def list_companies(
    org_id: str = Depends(get_current_org),
    db: Session = Depends(get_db)
):
    return db.query(Company).filter(Company.org_id == org_id).all()
```

---

## Migration Strategy

### Phase 1: Database Schema (1 hour)
1. Add `tier_id` column to `organizations` table
2. Backfill existing orgs with appropriate tiers
3. Add indexes

### Phase 2: Backend APIs (2-3 hours)
1. Create `/users/me/organizations` endpoint
2. Update `/my-apps/authorized` to accept org_id
3. Create `/users/me/switch-org` endpoint
4. Add org context middleware

### Phase 3: Frontend (2-3 hours)
1. Create OrganizationContext
2. Create OrgSwitcher component
3. Integrate into all app layouts
4. Update app data fetching to include org_id

### Phase 4: App Updates (1-2 hours per app)
1. Add org context middleware
2. Scope queries by org_id
3. Test app isolation

### Phase 5: Testing & Verification (1-2 hours)
1. Test multi-org user scenarios
2. Verify app access isolation
3. Test org switching
4. Performance testing

---

## Backward Compatibility

### Fallback Logic

```python
async def get_user_tier(request: Request) -> str:
    """Get tier from org (new) or user attribute (legacy)."""

    # Try new org-centric approach first
    try:
        org_id = await get_current_org(request)
        org = await get_org_with_tier(org_id)
        return org.tier.tier_code
    except:
        pass

    # Fall back to legacy user attribute
    session = await get_session(request)
    return session.get("subscription_tier", "managed")
```

This ensures existing users continue to work while new users use the org-centric model.

---

## Auto-Provisioning

### On First Login (JIT Provisioning)

```python
async def ensure_user_has_org(user_id: str, user_email: str, db: Session):
    """Create personal org if user has no orgs."""

    # Check if user has any org memberships
    membership = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == user_id
    ).first()

    if membership:
        return  # Already has org

    # Get default tier for new users
    default_tier = db.query(SubscriptionTier).filter(
        SubscriptionTier.tier_code == "starter"
    ).first()

    # Create personal org
    org_name = user_email.split("@")[0].replace(".", " ").title()
    org = Organization(
        name=f"{org_name}'s Organization",
        slug=slugify(org_name),
        tier_id=default_tier.id
    )
    db.add(org)
    db.flush()

    # Add user as owner
    member = OrganizationMember(
        organization_id=org.id,
        user_id=user_id,
        role=OrganizationRole.OWNER
    )
    db.add(member)
    db.commit()

    return org
```

---

## Testing Checklist

### Functional Tests

- [ ] User with single org sees their apps
- [ ] User with multiple orgs can switch between them
- [ ] App data is isolated per org
- [ ] Org admin can invite members
- [ ] Invited members get org's tier access
- [ ] Removing member revokes access
- [ ] Org tier upgrade reflects immediately

### Edge Cases

- [ ] User with no orgs gets prompted to create one
- [ ] User removed from all orgs loses all access
- [ ] Org with no tier defaults to starter
- [ ] Invalid org_id returns 403

### Performance Tests

- [ ] Org switching < 500ms
- [ ] My-apps API < 100ms
- [ ] Organizations list API < 200ms

---

## Files to Create/Modify

### New Files

| File | Purpose |
|------|---------|
| `backend/org_access_api.py` | New org-centric endpoints |
| `backend/org_context_middleware.py` | Org context extraction |
| `src/contexts/OrganizationContext.jsx` | Frontend org state |
| `src/components/OrgSwitcher.jsx` | Org dropdown component |
| `docs/ORG_CENTRIC_MULTI_TENANCY_PLAN.md` | This document |

### Modified Files

| File | Changes |
|------|---------|
| `backend/my_apps_api.py` | Add org_id parameter |
| `backend/server.py` | Register new router |
| `src/App.jsx` | Wrap with OrganizationProvider |
| `src/components/Layout.jsx` | Add OrgSwitcher |

---

## Rollout Plan

### Stage 1: Ops-Center Only
- Deploy org-centric APIs
- Test with internal users
- Keep legacy tier system working

### Stage 2: New Apps First
- LoopNet uses org-centric (fresh, no migration)
- Center Deep uses org-centric for new features

### Stage 3: Full Migration
- Migrate existing users to orgs
- Deprecate user-level tier attributes
- Remove legacy fallback code

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Org switch latency | < 500ms |
| API response time | < 100ms |
| User confusion reports | 0 |
| Data isolation bugs | 0 |

---

## Appendix: Tier Definitions (Current)

| Tier Code | Name | Apps |
|-----------|------|------|
| `vip_founder` | VIP / Founder | All apps |
| `byok` | BYOK | Center Deep, LoopNet, Brigade, TTS, STT |
| `managed` | Managed | Center Deep, LoopNet, Bolt, Billing |
| `human_interest` | Human Interest | Mandate Map, CA Retirement Leads |
| `loopnet_starter` | LoopNet Starter | LoopNet (limited) |
| `loopnet_professional` | LoopNet Professional | LoopNet (full) |

---

**Document Version**: 1.0
**Created**: January 2026
**Author**: Claude Code Assistant
**Last Updated**: 2026-01-11
