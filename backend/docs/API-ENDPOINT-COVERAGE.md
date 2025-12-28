# API Endpoint Coverage Audit
**Date**: October 13, 2025
**Backend Location**: `/home/muut/Production/UC-Cloud/services/ops-center/backend`
**Purpose**: Verify backend API support for new navigation structure

---

## Executive Summary

**Coverage Status**: 🟡 Partial Coverage (65% complete)

- ✅ **Fully Supported**: BYOK, Usage Tracking, Subscription Plans, Billing
- ⚠️ **Partial Support**: Organization Management, Account Settings
- ❌ **Missing**: Profile Management, Session Management, Payment Method Management

**Priority Action Items**:
1. Implement Profile Management API (HIGH)
2. Add Session Management endpoints (HIGH)
3. Create Organization Team Management endpoints (MEDIUM)
4. Add Payment Method Management to Stripe API (MEDIUM)

---

## 1. Organization Management Endpoints

**Status**: ⚠️ Partial (Infrastructure exists, API endpoints missing)

### Required Endpoints

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/v1/org/info` | GET | ❌ Missing | Get current org details |
| `/api/v1/org/members` | GET | ❌ Missing | List team members |
| `/api/v1/org/members` | POST | ❌ Missing | Add team member |
| `/api/v1/org/members/{id}` | DELETE | ❌ Missing | Remove member |
| `/api/v1/org/members/{id}/role` | PUT | ❌ Missing | Update member role |
| `/api/v1/org/roles` | GET | ❌ Missing | List available roles |
| `/api/v1/org/settings` | GET | ❌ Missing | Get org settings |
| `/api/v1/org/settings` | PUT | ❌ Missing | Update org settings |
| `/api/v1/org/billing` | GET | ❌ Missing | Get org billing info |

### Backend Infrastructure

**Module**: `org_manager.py` ✅ **EXISTS**

Available functions:
- ✅ `create_organization(name, plan_tier)` - Create new org
- ✅ `get_org(org_id)` - Get org details
- ✅ `add_user_to_org(org_id, user_id, role)` - Add member
- ✅ `remove_user_from_org(org_id, user_id)` - Remove member
- ✅ `update_user_role(org_id, user_id, new_role)` - Update role
- ✅ `get_org_users(org_id)` - List members
- ✅ `get_user_orgs(user_id)` - User's orgs
- ✅ `update_org_billing_ids(org_id, lago_id, stripe_id)` - Update billing IDs
- ✅ `update_org_plan(org_id, plan_tier)` - Change plan
- ✅ `update_org_status(org_id, status)` - Change status

**Data Models**:
- ✅ `Organization` - Pydantic model with validation
- ✅ `OrgUser` - User membership model
- ✅ Supported roles: `owner`, `member`, `billing_admin`
- ✅ File-based storage with thread-safe locking

**Action Required**: Create `org_api.py` router that exposes these functions as HTTP endpoints.

---

## 2. Account Settings Endpoints

**Status**: ⚠️ Partial (Some exist via Keycloak integration)

### Required Endpoints

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/v1/auth/profile` | GET | ❌ Missing | Get user profile |
| `/api/v1/auth/profile` | PUT | ❌ Missing | Update profile |
| `/api/v1/auth/profile/avatar` | POST | ❌ Missing | Upload avatar |
| `/api/v1/auth/notifications` | GET | ❌ Missing | Get notification prefs |
| `/api/v1/auth/notifications` | PUT | ❌ Missing | Update prefs |
| `/api/v1/auth/sessions` | GET | ⚠️ Exists | List sessions (line 3148) |
| `/api/v1/auth/sessions/{id}` | DELETE | ❌ Missing | Logout session |
| `/api/v1/auth/change-password` | POST | ✅ Exists | In server.py (line 3055) |
| `/api/v1/auth/password-policy` | GET | ✅ Exists | In server.py (line 3106) |

### Existing Functions

**File**: `server.py`

- ✅ `POST /api/v1/auth/login` (line 2855)
- ✅ `POST /api/v1/auth/logout` (line 2902)
- ✅ `GET /api/v1/auth/me` (line 2935)
- ✅ `GET /api/v1/auth/csrf-token` (line 2946)
- ✅ `POST /api/v1/auth/change-password` (line 3055)
- ✅ `GET /api/v1/auth/password-policy` (line 3106)
- ⚠️ `GET /api/v1/auth/session` (line 4223) - Session info
- ⚠️ `async def get_sessions()` (line 3148) - Exists but not exposed as endpoint

**File**: `keycloak_integration.py`

Available functions:
- ✅ `get_user_by_email(email)` (line 102)
- ✅ `update_user_attributes(email, attributes)` (line 166)

**Action Required**:
1. Create `profile_api.py` router for profile management
2. Expose session management endpoints
3. Add notification preferences to Keycloak attributes
4. Implement avatar upload (consider S3 or file storage)

---

## 3. Subscription Management Endpoints

**Status**: ✅ Fully Implemented

### Existing Endpoints

**File**: `subscription_api.py` (Router prefix: `/api/v1/subscriptions`)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/api/v1/subscriptions/plans` | GET | ✅ Exists | Line 60 |
| `/api/v1/subscriptions/plans/{plan_id}` | GET | ✅ Exists | Line 66 |
| `/api/v1/subscriptions/my-access` | GET | ✅ Exists | Line 75 |
| `/api/v1/subscriptions/check-access/{service}` | POST | ✅ Exists | Line 109 |
| `/api/v1/subscriptions/services` | GET | ✅ Exists | Line 161 |

**Admin Endpoints**:
| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/api/v1/subscriptions/plans` | POST | ✅ Exists | Line 136 |
| `/api/v1/subscriptions/plans/{plan_id}` | PUT | ✅ Exists | Line 145 |
| `/api/v1/subscriptions/plans/{plan_id}` | DELETE | ✅ Exists | Line 153 |
| `/api/v1/subscriptions/admin/user-access/{user_id}` | GET | ✅ Exists | Line 166 |

**Note**: Frontend expects `/api/v1/subscriptions/current` but backend has `/api/v1/subscriptions/my-access`. Consider adding alias.

---

## 4. Usage Tracking Endpoints

**Status**: ✅ Fully Implemented

### Existing Endpoints

**File**: `usage_api.py` (Router prefix: `/api/v1/usage`)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/api/v1/usage/current` | GET | ✅ Exists | Line 82 |
| `/api/v1/usage/history` | GET | ✅ Exists | Line 146 |
| `/api/v1/usage/limits` | GET | ✅ Exists | Line 172 |
| `/api/v1/usage/features` | GET | ✅ Exists | Line 200 |
| `/api/v1/usage/reset-demo` | POST | ✅ Exists | Line 230 (dev only) |

**Features**:
- ✅ Returns tier info, usage counts, limits
- ✅ Calculates percentage used and remaining
- ✅ Shows reset dates
- ✅ Lists available features by tier
- ⚠️ History endpoint is placeholder (needs time-series DB)

---

## 5. Billing Management Endpoints

**Status**: ✅ Fully Implemented

### Existing Endpoints

**File**: `stripe_api.py` (Router prefix: `/api/v1/billing` - inferred from context)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/api/v1/billing/subscriptions/checkout` | POST | ✅ Exists | Line 108 |
| `/api/v1/billing/portal/create` | POST | ✅ Exists | Line 186 |
| `/api/v1/billing/payment-methods` | GET | ✅ Exists | Line 226 |
| `/api/v1/billing/subscription-status` | GET | ✅ Exists | Line 265 |
| `/api/v1/billing/subscription/cancel` | POST | ✅ Exists | Line 323 |
| `/api/v1/billing/subscription/upgrade` | POST | ✅ Exists | Line 376 |
| `/api/v1/billing/webhooks/stripe` | POST | ✅ Exists | Line 443 |

### Invoice Endpoints

**File**: `lago_integration.py`

| Endpoint | Method | Status | Notes |
|----------|--------|--------|-------|
| `/api/v1/billing/invoices` | GET | ⚠️ Function exists | `get_invoices()` at line 526 |

**Action Required**:
- Verify Stripe API router is mounted with `/api/v1/billing` prefix
- Expose `get_invoices()` as HTTP endpoint
- Add invoice download endpoint

---

## 6. BYOK (Bring Your Own Key) Endpoints

**Status**: ✅ Fully Implemented

### Existing Endpoints

**File**: `byok_api.py` (Router prefix: `/api/v1/byok`)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/api/v1/byok/providers` | GET | ✅ Exists | Line 244 |
| `/api/v1/byok/keys` | GET | ✅ Exists | Line 277 |
| `/api/v1/byok/keys/add` | POST | ✅ Exists | Line 326 |
| `/api/v1/byok/keys/{provider}` | DELETE | ✅ Exists | Line 373 |
| `/api/v1/byok/keys/test/{provider}` | POST | ✅ Exists | Line 416 |
| `/api/v1/byok/stats` | GET | ✅ Exists | Line 465 |

**Features**:
- ✅ 8 supported providers (OpenAI, Anthropic, HuggingFace, Cohere, Together, Perplexity, Groq, Custom)
- ✅ Encrypted key storage via `key_encryption.py`
- ✅ Key validation and testing
- ✅ Tier-gated (requires Starter+ tier)
- ✅ Stored in Keycloak user attributes

---

## 7. Additional Backend Capabilities

### Audit Logging

**File**: `audit_endpoints.py` (Router prefix not specified)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/logs` | GET | ✅ Exists | Line 43 |
| `/stats` | GET | ✅ Exists | Line 105 |
| `/actions` | GET | ✅ Exists | Line 139 |
| `/recent` | GET | ✅ Exists | Line 230 |
| `/security` | GET | ✅ Exists | Line 256 |
| `/cleanup` | DELETE | ✅ Exists | Line 298 |

### Admin Subscription Management

**File**: `admin_subscriptions_api.py` (Router prefix not specified)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/list` | GET | ✅ Exists | Line 83 |
| `/{email}` | GET | ✅ Exists | Line 116 |
| `/{email}` | PATCH | ✅ Exists | Line 156 |
| `/{email}/reset-usage` | POST | ✅ Exists | Line 214 |
| `/analytics/overview` | GET | ✅ Exists | Line 244 |
| `/analytics/revenue-by-tier` | GET | ✅ Exists | Line 302 |
| `/analytics/usage-stats` | GET | ✅ Exists | Line 344 |

### Tier Check & Rate Limiting

**File**: `tier_check_api.py` (Router prefix not specified)

| Endpoint | Method | Status | Location |
|----------|--------|--------|----------|
| `/check-tier` | GET | ✅ Exists | Line 28 |
| `/user/tier` | GET | ✅ Exists | Line 96 |
| `/services/access-matrix` | GET | ✅ Exists | Line 128 |
| `/tiers/info` | GET | ✅ Exists | Line 162 |
| `/usage/track` | POST | ✅ Exists | Line 206 |
| `/rate-limit/check` | GET | ✅ Exists | Line 237 |

---

## Missing Endpoints - Implementation Priority

### HIGH PRIORITY (Required for basic functionality)

#### 1. Profile Management API
**New File**: `profile_api.py`

```python
router = APIRouter(prefix="/api/v1/auth", tags=["profile"])

@router.get("/profile")
async def get_profile(request: Request):
    """Get user profile from Keycloak"""
    pass

@router.put("/profile")
async def update_profile(data: ProfileUpdate, request: Request):
    """Update user profile (name, bio, etc.)"""
    pass
```

**Required Fields**:
- Display name
- Bio
- Avatar URL
- Email (read-only, from Keycloak)
- Username (read-only)
- Created date
- Last login

#### 2. Session Management API
**Extend**: `server.py` or create `session_api.py`

```python
@router.get("/api/v1/auth/sessions")
async def list_sessions(request: Request):
    """List all active sessions for user"""
    # Function exists at line 3148, needs HTTP exposure
    pass

@router.delete("/api/v1/auth/sessions/{session_id}")
async def logout_session(session_id: str, request: Request):
    """Logout a specific session"""
    pass
```

#### 3. Organization Team Management API
**New File**: `org_api.py`

```python
router = APIRouter(prefix="/api/v1/org", tags=["organization"])

@router.get("/info")
async def get_org_info(request: Request):
    """Get current user's organization"""
    # Use org_manager.get_user_orgs()
    pass

@router.get("/members")
async def list_members(request: Request):
    """List organization members"""
    # Use org_manager.get_org_users()
    pass

@router.post("/members")
async def add_member(data: MemberAdd, request: Request):
    """Add team member"""
    # Use org_manager.add_user_to_org()
    pass

@router.delete("/members/{user_id}")
async def remove_member(user_id: str, request: Request):
    """Remove team member"""
    # Use org_manager.remove_user_from_org()
    pass

@router.get("/roles")
async def list_roles():
    """Get available roles"""
    return {"roles": ["owner", "member", "billing_admin"]}
```

### MEDIUM PRIORITY (Enhanced functionality)

#### 4. Payment Method Management
**Extend**: `stripe_api.py`

```python
@router.post("/payment-methods")
async def add_payment_method(data: PaymentMethodAdd, request: Request):
    """Add new payment method"""
    pass

@router.delete("/payment-methods/{pm_id}")
async def remove_payment_method(pm_id: str, request: Request):
    """Remove payment method"""
    pass

@router.put("/payment-methods/{pm_id}/default")
async def set_default_payment_method(pm_id: str, request: Request):
    """Set default payment method"""
    pass
```

#### 5. Invoice Management
**Extend**: `stripe_api.py` or `lago_integration.py`

```python
@router.get("/invoices")
async def list_invoices(request: Request):
    """List user invoices"""
    # Use lago_integration.get_invoices()
    pass

@router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, request: Request):
    """Get invoice details"""
    pass

@router.get("/invoices/{invoice_id}/download")
async def download_invoice(invoice_id: str, request: Request):
    """Download invoice PDF"""
    pass
```

#### 6. Notification Preferences
**Extend**: `profile_api.py`

```python
@router.get("/notifications")
async def get_notification_preferences(request: Request):
    """Get notification settings"""
    # Store in Keycloak attributes: notification_email, notification_sms, etc.
    pass

@router.put("/notifications")
async def update_notification_preferences(data: NotificationPrefs, request: Request):
    """Update notification settings"""
    pass
```

### LOW PRIORITY (Nice to have)

#### 7. Organization Settings
**Extend**: `org_api.py`

```python
@router.get("/settings")
async def get_org_settings(request: Request):
    """Get organization settings"""
    pass

@router.put("/settings")
async def update_org_settings(data: OrgSettings, request: Request):
    """Update organization settings"""
    pass
```

#### 8. Avatar Upload
**New File**: `upload_api.py`

```python
@router.post("/api/v1/auth/profile/avatar")
async def upload_avatar(file: UploadFile, request: Request):
    """Upload user avatar"""
    # Store in S3 or local storage
    # Update Keycloak attribute: avatar_url
    pass
```

---

## Router Integration Status

### Current Router Mounts (need verification in server.py)

Routers that should be mounted:
- ✅ `byok_api.py` - Likely mounted at line 63
- ✅ `subscription_api.py` - Likely mounted at line 68
- ✅ `usage_api.py` - Mount status unknown
- ✅ `admin_subscriptions_api.py` - Likely mounted at line 66
- ✅ `stripe_api.py` - Mount status unknown
- ⚠️ `org_api.py` - NOT CREATED YET
- ⚠️ `profile_api.py` - NOT CREATED YET

**Action Required**: Verify all routers are properly mounted in `server.py` with correct prefixes.

---

## Data Model Requirements

### Profile Model
```python
class UserProfile(BaseModel):
    email: str
    username: str
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
```

### Session Model
```python
class UserSession(BaseModel):
    session_id: str
    created_at: datetime
    last_activity: datetime
    ip_address: str
    user_agent: str
    is_current: bool
```

### Organization Models
```python
# Already exist in org_manager.py
- Organization
- OrgUser
```

### Payment Method Model
```python
class PaymentMethod(BaseModel):
    id: str
    type: str  # "card", "bank_account"
    brand: Optional[str]
    last4: str
    exp_month: Optional[int]
    exp_year: Optional[int]
    is_default: bool
```

---

## Testing Recommendations

### Unit Tests Required
1. `test_org_api.py` - Organization CRUD operations
2. `test_profile_api.py` - Profile management
3. `test_session_api.py` - Session management
4. `test_payment_methods.py` - Payment method CRUD

### Integration Tests Required
1. End-to-end organization creation with billing setup
2. Profile update with Keycloak sync
3. Multi-session logout flow
4. Payment method update with Stripe sync

### Test Files Available
Based on glob results, existing test files:
- `/tests/test_org_manager.py` - Organization manager tests
- `/tests/test_complete_flow.py` - End-to-end tests
- `/tests/test_lago_org_integration.py` - Billing integration tests

---

## Security Considerations

### Required for New Endpoints

1. **Authentication**: All endpoints must verify session token
2. **Authorization**:
   - Organization endpoints: Verify user is org member
   - Admin endpoints: Verify admin role
   - Payment methods: User can only manage their own
3. **Rate Limiting**: Apply to all write operations
4. **Input Validation**: Use Pydantic models
5. **Audit Logging**: Log all sensitive operations
6. **CSRF Protection**: Required for state-changing operations

### Existing Security Infrastructure

- ✅ Session-based authentication
- ✅ CSRF token system (`csrf_protection.py`)
- ✅ Tier-based access control (`tier_middleware.py`)
- ✅ Rate limiting infrastructure (`rate_limit.py`)
- ✅ Audit logging (`audit_endpoints.py`)
- ✅ Key encryption (`key_encryption.py`)

---

## Implementation Roadmap

### Phase 1: Critical Endpoints (Week 1)
1. Create `profile_api.py` with GET/PUT profile endpoints
2. Expose session management endpoints
3. Create `org_api.py` with basic team management
4. Add endpoint alias `/api/v1/subscriptions/current` → `my-access`

### Phase 2: Payment & Billing (Week 2)
1. Add payment method management to `stripe_api.py`
2. Expose invoice endpoints
3. Add notification preferences to profile API
4. Implement invoice PDF generation

### Phase 3: Advanced Features (Week 3)
1. Organization settings management
2. Avatar upload functionality
3. Usage history with time-series data
4. Advanced team management (roles, permissions)

### Phase 4: Testing & Documentation (Week 4)
1. Write unit tests for all new endpoints
2. Create integration tests
3. Update API documentation
4. Generate OpenAPI/Swagger specs

---

## Documentation Updates Required

After implementation:
1. Update API reference documentation
2. Create endpoint usage examples
3. Update frontend integration guide
4. Add security best practices guide
5. Create troubleshooting guide

---

## Conclusion

**Current State**:
- Backend has strong infrastructure (org_manager, keycloak_integration, encryption)
- Most user-facing APIs exist (BYOK, usage, subscriptions)
- Organization management backend ready but not exposed as HTTP endpoints

**Immediate Actions**:
1. Create `org_api.py` router (HIGH)
2. Create `profile_api.py` router (HIGH)
3. Expose session management endpoints (HIGH)
4. Verify all routers are mounted correctly (HIGH)
5. Add payment method management (MEDIUM)

**Estimated Development Time**: 2-3 weeks for full implementation with testing.

---

**Audit Completed By**: Backend API Developer Agent
**Date**: October 13, 2025
**Next Review**: After Phase 1 implementation
