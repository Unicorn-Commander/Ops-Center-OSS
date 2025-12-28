# Backend API Implementation Checklist

**Based on**: API Endpoint Coverage Audit (Oct 13, 2025)

---

## Priority 1: Core Missing Endpoints (HIGH)

### 1. Organization Management API (`org_api.py`)

**Status**: ❌ Not Started

**Required Endpoints** (10 total):

- [ ] `GET /api/v1/org/info` - Get current user's organization
  - Use: `org_manager.get_user_orgs(user_id)`
  - Returns: Organization details

- [ ] `GET /api/v1/org/members` - List team members
  - Use: `org_manager.get_org_users(org_id)`
  - Returns: List of OrgUser objects

- [ ] `POST /api/v1/org/members` - Add team member
  - Use: `org_manager.add_user_to_org(org_id, user_id, role)`
  - Body: `{email: str, role: str}`

- [ ] `DELETE /api/v1/org/members/{user_id}` - Remove member
  - Use: `org_manager.remove_user_from_org(org_id, user_id)`

- [ ] `PUT /api/v1/org/members/{user_id}/role` - Update member role
  - Use: `org_manager.update_user_role(org_id, user_id, new_role)`
  - Body: `{role: str}`

- [ ] `GET /api/v1/org/roles` - List available roles
  - Returns: `["owner", "member", "billing_admin"]`

- [ ] `GET /api/v1/org/settings` - Get org settings
  - Returns: Organization settings

- [ ] `PUT /api/v1/org/settings` - Update org settings
  - Use: `org_manager.update_org_status()` etc.

- [ ] `GET /api/v1/org/billing` - Get org billing info
  - Returns: Lago/Stripe integration data

- [ ] `GET /api/v1/org/stats` - Get org statistics
  - Returns: Member count, usage, etc.

**Implementation Notes**:
- Import `from org_manager import org_manager`
- Add authentication check: `get_current_user(request)`
- Add authorization: Verify user is org member
- Use audit logging for all mutations
- Apply rate limiting to POST/DELETE operations

**Estimated Time**: 4 hours

---

### 2. Profile Management API (`profile_api.py`)

**Status**: ❌ Not Started

**Required Endpoints** (5 total):

- [ ] `GET /api/v1/auth/profile` - Get user profile
  - Use: `keycloak_integration.get_user_by_email(email)`
  - Returns: User profile with attributes

- [ ] `PUT /api/v1/auth/profile` - Update profile
  - Use: `keycloak_integration.update_user_attributes(email, attrs)`
  - Body: `{display_name: str, bio: str}`

- [ ] `POST /api/v1/auth/profile/avatar` - Upload avatar
  - Store file (S3 or local storage)
  - Update Keycloak attribute: `avatar_url`

- [ ] `GET /api/v1/auth/notifications` - Get notification prefs
  - Read from Keycloak attributes: `notification_*`

- [ ] `PUT /api/v1/auth/notifications` - Update notification prefs
  - Update Keycloak attributes
  - Body: `{email: bool, sms: bool, push: bool}`

**Implementation Notes**:
- Import `from keycloak_integration import get_user_by_email, update_user_attributes`
- Profile fields stored as Keycloak attributes
- Avatar upload needs file storage setup
- Consider image validation and resizing

**Estimated Time**: 3 hours (5 hours with avatar upload)

---

### 3. Session Management Endpoints

**Status**: ⚠️ Partial (Function exists, needs HTTP exposure)

**Required Endpoints** (2 total):

- [ ] `GET /api/v1/auth/sessions` - List active sessions
  - Function exists at `server.py` line 3148: `get_sessions()`
  - Expose as HTTP endpoint

- [ ] `DELETE /api/v1/auth/sessions/{session_id}` - Logout session
  - Implement session deletion logic
  - Remove from session store

**Implementation Notes**:
- Session data stored in `request.app.state.sessions`
- Need to track session metadata (IP, user agent, created_at)
- Consider Redis session store for production

**Estimated Time**: 2 hours

---

## Priority 2: Enhanced Features (MEDIUM)

### 4. Payment Method Management

**Status**: ⚠️ Partial (GET exists, need POST/DELETE)

**File to Modify**: `stripe_api.py`

**Required Endpoints** (3 total):

- [ ] `POST /api/v1/billing/payment-methods` - Add payment method
  - Stripe API: `PaymentMethod.attach()`
  - Body: `{payment_method_id: str}`

- [ ] `DELETE /api/v1/billing/payment-methods/{pm_id}` - Remove payment method
  - Stripe API: `PaymentMethod.detach()`

- [ ] `PUT /api/v1/billing/payment-methods/{pm_id}/default` - Set default
  - Stripe API: `Customer.modify()`

**Implementation Notes**:
- Existing GET endpoint at line 226
- Use existing Stripe client setup
- Validate payment method ownership

**Estimated Time**: 2 hours

---

### 5. Invoice Management

**Status**: ⚠️ Backend function exists, needs HTTP wrapper

**File to Modify**: `stripe_api.py` or create `invoice_api.py`

**Required Endpoints** (3 total):

- [ ] `GET /api/v1/billing/invoices` - List invoices
  - Use: `lago_integration.get_invoices(org_id, limit=10)`
  - Currently at line 526 in lago_integration.py

- [ ] `GET /api/v1/billing/invoices/{invoice_id}` - Get invoice details
  - Fetch from Stripe or Lago

- [ ] `GET /api/v1/billing/invoices/{invoice_id}/download` - Download PDF
  - Generate or fetch PDF from billing system

**Implementation Notes**:
- Function exists in `lago_integration.py`
- Need to integrate with org_manager for org_id lookup
- Consider caching invoice data

**Estimated Time**: 3 hours

---

### 6. Subscription Alias

**Status**: ⚠️ Simple addition needed

**File to Modify**: `subscription_api.py`

**Required**:

- [ ] Add alias endpoint `GET /api/v1/subscriptions/current`
  - Should return same data as `/my-access`
  - Frontend expects `/current` but backend has `/my-access`

**Implementation**:
```python
@router.get("/current")
async def get_current_subscription(request: Request):
    """Alias for my-access endpoint"""
    return await get_my_access(request)
```

**Estimated Time**: 15 minutes

---

## Priority 3: Infrastructure & Testing (LOW)

### 7. Router Verification

**Status**: ⚠️ Needs verification

**File to Check**: `server.py`

**Tasks**:

- [ ] Verify `byok_api` is mounted (expected line 63)
- [ ] Verify `subscription_api` is mounted (expected line 68)
- [ ] Verify `admin_subscriptions_api` is mounted (expected line 66)
- [ ] Verify `usage_api` is mounted
- [ ] Verify `stripe_api` is mounted
- [ ] Mount new `org_api` router
- [ ] Mount new `profile_api` router

**Implementation**:
```python
# In server.py
from byok_api import router as byok_router
from subscription_api import router as subscription_router
from org_api import router as org_router  # NEW
from profile_api import router as profile_router  # NEW

app.include_router(byok_router)
app.include_router(subscription_router)
app.include_router(org_router)  # NEW
app.include_router(profile_router)  # NEW
```

**Estimated Time**: 30 minutes

---

### 8. Unit Tests

**Status**: ❌ Not Started

**Required Test Files**:

- [ ] `test_org_api.py` - Organization CRUD
  - Test create, read, update, delete org
  - Test add/remove members
  - Test role updates
  - Test authorization checks

- [ ] `test_profile_api.py` - Profile management
  - Test get/update profile
  - Test notification preferences
  - Test avatar upload (if implemented)

- [ ] `test_session_api.py` - Session management
  - Test list sessions
  - Test logout session
  - Test current session protection

- [ ] `test_payment_methods.py` - Payment CRUD
  - Test add/remove payment methods
  - Test set default
  - Test Stripe integration

**Estimated Time**: 6 hours

---

### 9. Integration Tests

**Status**: ❌ Not Started

**Required Tests**:

- [ ] End-to-end organization creation with billing
- [ ] Profile update with Keycloak sync
- [ ] Multi-session logout flow
- [ ] Payment method update with Stripe sync
- [ ] Organization member invite flow

**Estimated Time**: 4 hours

---

## Summary

### Time Estimates

| Priority | Task | Time | Status |
|----------|------|------|--------|
| P1 | Organization API | 4h | ❌ |
| P1 | Profile API | 3-5h | ❌ |
| P1 | Session Management | 2h | ⚠️ |
| P2 | Payment Methods | 2h | ⚠️ |
| P2 | Invoice Management | 3h | ⚠️ |
| P2 | Subscription Alias | 15m | ⚠️ |
| P3 | Router Verification | 30m | ⚠️ |
| P3 | Unit Tests | 6h | ❌ |
| P3 | Integration Tests | 4h | ❌ |

**Total Core Development**: 9-11 hours
**Total with Testing**: 19-21 hours
**Total with All Features**: 24-26 hours

---

## Implementation Order

### Day 1 (8 hours)
1. ✅ Audit existing endpoints (COMPLETE)
2. Create `org_api.py` with 10 endpoints (4h)
3. Create `profile_api.py` with 5 endpoints (3h)
4. Add subscription alias (15m)
5. Verify router mounts (30m)

### Day 2 (8 hours)
1. Session management endpoints (2h)
2. Payment method management (2h)
3. Invoice management (3h)
4. Basic unit tests (1h)

### Day 3 (8 hours)
1. Complete unit tests (5h)
2. Integration tests (3h)

---

## Quick Start

### Create org_api.py
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
touch org_api.py
```

### Create profile_api.py
```bash
touch profile_api.py
```

### Test Files
```bash
cd tests
touch test_org_api.py test_profile_api.py test_session_api.py test_payment_methods.py
```

---

## Dependencies Checklist

Before starting implementation, verify:

- [ ] `org_manager.py` is working
- [ ] `keycloak_integration.py` is working
- [ ] `key_encryption.py` is available
- [ ] `tier_middleware.py` is configured
- [ ] `audit_endpoints.py` is logging
- [ ] `rate_limit.py` is active
- [ ] Session storage is set up (Redis or in-memory)
- [ ] Stripe API keys are configured
- [ ] Lago integration is active

---

## Success Criteria

### Phase 1: Core Endpoints
- [ ] All organization endpoints return 200 OK
- [ ] Profile CRUD operations work
- [ ] Session management functional
- [ ] Proper authentication/authorization on all endpoints

### Phase 2: Enhanced Features
- [ ] Payment methods can be added/removed via API
- [ ] Invoices can be listed and downloaded
- [ ] All endpoints have proper error handling

### Phase 3: Testing & Documentation
- [ ] 90%+ test coverage on new endpoints
- [ ] Integration tests pass
- [ ] API documentation updated
- [ ] OpenAPI/Swagger specs generated

---

**Last Updated**: October 13, 2025
**See Also**:
- Full Audit: `/home/muut/Production/UC-Cloud/services/ops-center/backend/docs/API-ENDPOINT-COVERAGE.md`
- Summary: `/home/muut/Production/UC-Cloud/services/ops-center/backend/tests/AUDIT-SUMMARY.md`
