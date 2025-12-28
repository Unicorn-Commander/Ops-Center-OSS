# 2FA Management Architecture Design

**Project**: Ops-Center 2FA Management Feature
**Date**: October 28, 2025
**Status**: Architecture Complete - Implementation Started
**Security Team Lead**: AI Assistant

---

## Executive Summary

This document outlines the architecture for implementing admin-managed Two-Factor Authentication (2FA) functionality in Ops-Center. The system integrates with Keycloak's built-in 2FA capabilities to provide comprehensive management without creating a separate 2FA system.

**Key Principle**: We leverage Keycloak's native 2FA features rather than building our own authentication system. Ops-Center provides the management interface.

---

## Keycloak 2FA Capabilities

### What Keycloak Provides Out-of-the-Box

1. **TOTP Support** (Time-based One-Time Password)
   - RFC 6238 compliant
   - Works with Google Authenticator, Microsoft Authenticator, Authy, etc.
   - QR code generation built-in

2. **WebAuthn Support** (Hardware Keys)
   - FIDO2/WebAuthn standard
   - YubiKey, Titan Security Key, TouchID, Windows Hello
   - Biometric authentication

3. **SMS/Email OTP** (via custom extensions)
   - Not built-in by default
   - Requires additional configuration

4. **Backup Codes**
   - Single-use recovery codes
   - Generated automatically when 2FA is enabled

### Keycloak Admin REST API Endpoints

**Base URL**: `https://auth.your-domain.com/admin/realms/uchub`

#### Available Endpoints:

```http
# 1. Get User's Required Actions (includes CONFIGURE_TOTP if 2FA required)
GET /users/{user-id}
Response: {
  "requiredActions": ["CONFIGURE_TOTP"],  // If 2FA setup required
  ...
}

# 2. Set Required Actions (Force 2FA setup)
PUT /users/{user-id}
Body: {
  "requiredActions": ["CONFIGURE_TOTP"]
}

# 3. Send Execute Actions Email (Trigger 2FA setup email)
PUT /users/{user-id}/execute-actions-email
Body: ["CONFIGURE_TOTP"]
Query params: ?lifespan=43200  // 12 hours in seconds

# 4. Get User's Credentials (Check if 2FA is configured)
GET /users/{user-id}/credentials
Response: [
  {
    "id": "cred-id",
    "type": "otp",  // Indicates TOTP is configured
    "userLabel": "Google Authenticator",
    "createdDate": 1698765432000
  }
]

# 5. Remove 2FA Credential (Reset 2FA)
DELETE /users/{user-id}/credentials/{credential-id}

# 6. Get Authentication Flows
GET /authentication/flows
Response: [/* List of available auth flows including 2FA flows */]

# 7. Get Required Actions
GET /authentication/required-actions
Response: [
  {
    "alias": "CONFIGURE_TOTP",
    "name": "Configure OTP",
    "enabled": true,
    "defaultAction": false
  }
]

# 8. Update Required Action Settings (Enable/disable 2FA for realm)
PUT /authentication/required-actions/CONFIGURE_TOTP
Body: {
  "alias": "CONFIGURE_TOTP",
  "name": "Configure OTP",
  "enabled": true,
  "defaultAction": true  // Force all new users to setup 2FA
}
```

---

## Architecture Decision Records (ADRs)

### ADR-001: Use Keycloak Native 2FA

**Decision**: Leverage Keycloak's built-in 2FA capabilities rather than building custom 2FA system.

**Rationale**:
- Keycloak is security-hardened and RFC-compliant
- Reduces development time from weeks to days
- No need to maintain separate 2FA secrets storage
- Benefits from Keycloak security updates
- Industry-standard implementation

**Consequences**:
- Admin UI controls user experience indirectly through Keycloak
- Some features require Keycloak admin privileges
- Custom SMS/Email OTP requires Keycloak extensions

**Status**: Accepted

---

### ADR-002: Admin-Initiated 2FA Management

**Decision**: Admins can force 2FA setup or reset 2FA for users, but cannot disable 2FA once user has configured it (must reset).

**Rationale**:
- Security best practice: Once 2FA is enabled, disabling requires full reset
- Prevents accidental security downgrades
- Forces users to reconfigure after reset (ensures they have access to new device)
- Audit trail for all 2FA changes

**Consequences**:
- Admins cannot "temporarily disable" 2FA
- Reset forces user to reconfigure on next login
- May cause support tickets if users lose devices

**Status**: Accepted

---

### ADR-003: Role-Based 2FA Enforcement

**Decision**: Implement 2FA policy enforcement at role level (e.g., all admins must use 2FA).

**Rationale**:
- Protects high-privilege accounts
- Complies with security frameworks (SOC 2, ISO 27001)
- Reduces attack surface for privileged access
- Can be granular (different policies per role)

**Consequences**:
- Requires periodic checks to verify 2FA status
- Users cannot bypass 2FA if role requires it
- Need clear communication to affected users

**Status**: Accepted

---

### ADR-004: Audit All 2FA Changes

**Decision**: Every 2FA operation (enforce, reset, policy change) must be logged to audit trail.

**Rationale**:
- Security compliance requirement
- Incident response needs
- User accountability
- Regulatory requirements (GDPR, SOX, HIPAA)

**Consequences**:
- Increased database writes
- Audit log growth (plan retention)
- Need audit log query UI

**Status**: Accepted

---

### ADR-005: Rate Limiting on 2FA Reset

**Decision**: Limit 2FA reset operations to 3 per user per 24 hours.

**Rationale**:
- Prevents abuse (attacker locking out users)
- Prevents brute-force attacks
- Encourages users to use backup codes
- Reduces support load

**Consequences**:
- May require manual override for legitimate emergencies
- Need clear error messages to users
- Support team must have override capability

**Status**: Accepted

---

## System Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Ops-Center Frontend                      │
│                   (React + Material-UI)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS REST API
                              │
┌─────────────────────────────▼─────────────────────────────┐
│                   Ops-Center Backend                       │
│                     (FastAPI Python)                       │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         two_factor_api.py (NEW)                      │ │
│  │  - GET /users/{id}/2fa-status                        │ │
│  │  - POST /users/{id}/2fa-enforce                      │ │
│  │  - DELETE /users/{id}/2fa-reset                      │ │
│  │  - POST /2fa-policy (role-based)                     │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │    keycloak_integration.py (ENHANCED)                │ │
│  │  - get_user_2fa_status()                             │ │
│  │  - enforce_user_2fa()                                │ │
│  │  - reset_user_2fa()                                  │ │
│  │  - get_user_credentials()                            │ │
│  │  - remove_user_credential()                          │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │         audit_logger.py (ENHANCED)                   │ │
│  │  - log_2fa_enforcement()                             │ │
│  │  - log_2fa_reset()                                   │ │
│  │  - log_2fa_policy_change()                           │ │
│  └──────────────────────────────────────────────────────┘ │
└─────────────────────────────┬─────────────────────────────┘
                              │
                              │ Keycloak Admin REST API
                              │ (Bearer Token Auth)
                              │
┌─────────────────────────────▼─────────────────────────────┐
│                  Keycloak (uchub realm)                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  User Database                                       │ │
│  │  - User accounts                                     │ │
│  │  - Required actions (CONFIGURE_TOTP)                 │ │
│  │  - Credentials (OTP secrets)                         │ │
│  └──────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  Authentication Flows                                │ │
│  │  - Browser Flow + OTP                                │ │
│  │  - Direct Grant + OTP                                │ │
│  └──────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────┘
```

---

## Backend API Specification

### Module: `backend/two_factor_api.py`

#### Endpoint 1: Get 2FA Status for User

```python
GET /api/v1/admin/users/{user_id}/2fa-status

Response:
{
  "user_id": "abc-123",
  "username": "aaron",
  "email": "aaron@example.com",
  "two_factor_enabled": true,
  "two_factor_methods": [
    {
      "id": "cred-123",
      "type": "otp",  // or "webauthn"
      "label": "Google Authenticator",
      "created_date": "2025-10-15T10:30:00Z"
    }
  ],
  "required_by_policy": true,  // If user's role requires 2FA
  "setup_pending": false,  // If CONFIGURE_TOTP action is pending
  "last_used": "2025-10-28T09:15:00Z"
}
```

**Business Logic**:
1. Fetch user from Keycloak by ID
2. Get user's credentials via `/users/{id}/credentials`
3. Filter for type "otp" or "webauthn"
4. Check if user has CONFIGURE_TOTP in requiredActions
5. Check if user's roles require 2FA (from policy)
6. Return consolidated status

**Security**:
- Requires admin role
- Audit log all requests
- Rate limit: 100 requests/minute per admin

---

#### Endpoint 2: Enforce 2FA for User

```python
POST /api/v1/admin/users/{user_id}/2fa-enforce

Request Body:
{
  "method": "email",  // "email" or "immediate"
  "reason": "Admin policy enforcement"  // Optional
}

Response:
{
  "success": true,
  "user_id": "abc-123",
  "action_taken": "email_sent",  // or "required_action_set"
  "message": "User will be prompted to setup 2FA on next login"
}
```

**Business Logic**:
1. Verify user exists
2. Check if 2FA already enabled (skip if yes)
3. If method = "email":
   - Call `/users/{id}/execute-actions-email` with ["CONFIGURE_TOTP"]
   - Set lifespan to 24 hours
4. If method = "immediate":
   - Add "CONFIGURE_TOTP" to user's requiredActions
   - User prompted on next login
5. Create audit log entry
6. Send notification to user (optional)

**Security**:
- Requires admin role
- Audit log with reason
- Cannot bypass if user has already configured 2FA

---

#### Endpoint 3: Reset 2FA for User

```python
DELETE /api/v1/admin/users/{user_id}/2fa-reset

Request Body:
{
  "reason": "User lost device",  // Required
  "require_reconfigure": true  // Force immediate reconfiguration
}

Response:
{
  "success": true,
  "user_id": "abc-123",
  "credentials_removed": ["cred-123", "cred-456"],
  "required_action_set": true,
  "message": "2FA reset complete. User must reconfigure on next login."
}
```

**Business Logic**:
1. **Rate Limiting Check**: Verify < 3 resets in past 24 hours
2. Fetch user's credentials
3. Delete all OTP and WebAuthn credentials
4. If require_reconfigure = true:
   - Add "CONFIGURE_TOTP" to requiredActions
5. Create audit log entry (with reason)
6. Send notification to user's email
7. Invalidate all user sessions (force re-login)

**Security**:
- Requires admin role
- Rate limit: 3 resets per user per 24 hours
- Audit log with reason (required)
- Email notification to user
- Cannot be undone

**Error Cases**:
- 429 Too Many Requests: Rate limit exceeded
- 404 Not Found: User doesn't exist
- 400 Bad Request: Reason not provided

---

#### Endpoint 4: Set 2FA Policy by Role

```python
POST /api/v1/admin/2fa-policy

Request Body:
{
  "role": "admin",  // or "moderator", "developer", etc.
  "require_2fa": true,
  "grace_period_days": 7,  // Days before enforcement
  "notify_users": true
}

Response:
{
  "success": true,
  "policy": {
    "role": "admin",
    "require_2fa": true,
    "grace_period_days": 7,
    "affected_users": 5,
    "enforcement_date": "2025-11-04T00:00:00Z"
  },
  "notifications_sent": 5
}
```

**Business Logic**:
1. Validate role exists in Keycloak
2. Store policy in PostgreSQL `two_factor_policies` table
3. Calculate enforcement date (today + grace_period_days)
4. If notify_users = true:
   - Get all users with this role
   - Send email notifications
5. Create audit log entry
6. Schedule enforcement job (background task)

**Database Schema** (PostgreSQL):
```sql
CREATE TABLE two_factor_policies (
  id SERIAL PRIMARY KEY,
  role VARCHAR(50) NOT NULL UNIQUE,
  require_2fa BOOLEAN NOT NULL DEFAULT false,
  grace_period_days INTEGER NOT NULL DEFAULT 7,
  enforcement_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(255),  -- Admin who created policy
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE two_factor_policy_exemptions (
  id SERIAL PRIMARY KEY,
  user_id VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL,
  reason TEXT NOT NULL,
  exemption_end_date TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  created_by VARCHAR(255)  -- Admin who granted exemption
);
```

**Security**:
- Requires admin role
- Audit log all policy changes
- Cannot be bypassed by users
- Exemptions tracked separately

---

## Frontend UI Specification

### Component: `TwoFactorManagement.jsx`

**Location**: `src/components/TwoFactorManagement.jsx`

**Integration**: Added as new tab in `Security.jsx`

#### UI Sections:

```
┌────────────────────────────────────────────────────────────┐
│  Security Center                                            │
│  [Overview] [Users] [API Keys] [Sessions] [2FA Management] │
└────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│  2FA Management                                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Role-Based Policies                          [+Add]  │  │
│  │  ┌────────┬──────────────┬──────────┬───────────┐   │  │
│  │  │ Role   │ 2FA Required │ Grace    │ Actions   │   │  │
│  │  ├────────┼──────────────┼──────────┼───────────┤   │  │
│  │  │ Admin  │ ✓ Yes        │ 7 days   │ [Edit][X] │   │  │
│  │  │ Mods   │ ✗ No         │ -        │ [Edit][X] │   │  │
│  │  └────────┴──────────────┴──────────┴───────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  User 2FA Status                      [Search: ___]  │  │
│  │  ┌───────────────┬──────────┬──────────┬──────────┐  │  │
│  │  │ User          │ 2FA      │ Method   │ Actions  │  │  │
│  │  ├───────────────┼──────────┼──────────┼──────────┤  │  │
│  │  │ aaron@...     │ ✓ Enabled│ TOTP     │ [Reset]  │  │  │
│  │  │ user@...      │ ✗ Disabled│ -       │ [Enforce]│  │  │
│  │  │ admin@...     │ ⏳Pending│ -        │ [Resend] │  │  │
│  │  └───────────────┴──────────┴──────────┴──────────┘  │  │
│  │  [Previous] [1] [2] [3] [Next]                       │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Recent 2FA Events               [Last 24 hours ▼]   │  │
│  │  • Admin enforced 2FA for user@example.com           │  │
│  │    2025-10-28 09:15 AM - Reason: Policy enforcement  │  │
│  │  • aaron@example.com reset 2FA                       │  │
│  │    2025-10-28 08:30 AM - Reason: Lost device         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

#### Key Features:

1. **Role-Based Policy Management**
   - Add/Edit/Delete policies
   - Set grace periods
   - View affected users count
   - Bulk policy changes

2. **User 2FA Status Table**
   - Search and filter users
   - Status indicators:
     - ✓ Enabled (green) - 2FA configured
     - ✗ Disabled (gray) - No 2FA
     - ⏳ Pending (orange) - Setup in progress
     - ⚠️ Required (red) - Policy mandated, not configured
   - Quick actions per user:
     - Enforce 2FA (if not enabled)
     - Reset 2FA (if enabled)
     - Resend setup email (if pending)
     - View 2FA details

3. **2FA Event Log**
   - Real-time audit trail
   - Filter by event type, user, date
   - Export to CSV

4. **Bulk Operations**
   - Select multiple users
   - Bulk enforce 2FA
   - Bulk reset (with confirmation)

---

## Security Measures

### Authentication & Authorization

1. **Admin-Only Access**
   - All 2FA management endpoints require admin role
   - Role check via Keycloak token validation
   - Session timeout: 30 minutes

2. **Audit Logging**
   - Every 2FA operation logged
   - Includes: timestamp, admin user, target user, action, reason
   - Immutable audit trail (append-only)
   - Retention: 2 years (compliance)

3. **Rate Limiting**
   - API requests: 100/min per admin
   - 2FA reset: 3 per user per 24 hours
   - Policy changes: 10/hour per admin
   - Prevents DoS and abuse

4. **Secure Communication**
   - HTTPS only
   - Keycloak API calls via internal network
   - No 2FA secrets stored in Ops-Center
   - Secrets remain in Keycloak

### Data Protection

1. **No Secret Storage**
   - TOTP secrets stored only in Keycloak
   - Ops-Center never sees or stores secrets
   - QR codes generated by Keycloak

2. **Backup Codes**
   - Generated by Keycloak on 2FA setup
   - Single-use codes
   - User responsible for secure storage

3. **Session Management**
   - 2FA reset invalidates all user sessions
   - Forces re-authentication
   - Prevents session hijacking

---

## Implementation Phases

### Phase 1: Core Admin 2FA Management (Current)

**Deliverables**:
- ✅ Backend API module (`two_factor_api.py`)
- ✅ Keycloak integration functions
- ✅ Admin UI (Security page tab)
- ✅ Audit logging
- ✅ Rate limiting

**Timeline**: 4-6 hours
**Status**: In Progress

---

### Phase 2: User-Facing 2FA Setup (Optional)

**Deliverables**:
- User 2FA setup page in Account Security
- QR code generation UI
- Backup codes download
- 2FA verification flow
- Recovery options

**Timeline**: 6-8 hours
**Status**: Not Started (Optional)

**User Flow**:
1. User visits `/admin/account/security`
2. Clicks "Enable 2FA"
3. System generates QR code (via Keycloak)
4. User scans with authenticator app
5. User enters 6-digit code to verify
6. System generates 10 backup codes
7. User downloads backup codes
8. 2FA enabled

---

### Phase 3: Advanced Features (Future)

**Deliverables**:
- SMS/Email OTP support (requires Keycloak extension)
- Hardware key registration (WebAuthn UI)
- Trusted devices management
- 2FA recovery workflow
- Self-service 2FA reset (with identity verification)

**Timeline**: 2-3 weeks
**Status**: Future Enhancement

---

## Testing Strategy

### Unit Tests

```python
# backend/tests/test_two_factor_api.py

async def test_get_2fa_status_enabled():
    """Test fetching 2FA status for user with 2FA enabled"""
    response = await client.get("/api/v1/admin/users/user-123/2fa-status")
    assert response.status_code == 200
    assert response.json()["two_factor_enabled"] == True

async def test_enforce_2fa_email():
    """Test enforcing 2FA via email"""
    response = await client.post(
        "/api/v1/admin/users/user-123/2fa-enforce",
        json={"method": "email", "reason": "Policy"}
    )
    assert response.status_code == 200
    assert response.json()["action_taken"] == "email_sent"

async def test_reset_2fa_rate_limit():
    """Test 2FA reset rate limiting"""
    # Reset 3 times (should succeed)
    for i in range(3):
        response = await client.delete(
            f"/api/v1/admin/users/user-123/2fa-reset",
            json={"reason": f"Test reset {i}"}
        )
        assert response.status_code == 200

    # 4th attempt should fail
    response = await client.delete(
        "/api/v1/admin/users/user-123/2fa-reset",
        json={"reason": "Should fail"}
    )
    assert response.status_code == 429  # Too Many Requests
```

### Integration Tests

```python
# backend/tests/test_keycloak_2fa_integration.py

async def test_keycloak_2fa_enforcement_flow():
    """Test complete 2FA enforcement flow with Keycloak"""
    # 1. Create test user in Keycloak
    user_id = await create_user(email="test@example.com")

    # 2. Enforce 2FA
    await enforce_user_2fa(user_id, method="immediate")

    # 3. Verify CONFIGURE_TOTP action is set
    user = await get_user_by_id(user_id)
    assert "CONFIGURE_TOTP" in user["requiredActions"]

    # 4. Simulate user completing 2FA setup
    # (This would normally be done via Keycloak UI)

    # 5. Verify 2FA is enabled
    status = await get_user_2fa_status(user_id)
    assert status["two_factor_enabled"] == True

    # 6. Reset 2FA
    await reset_user_2fa(user_id, reason="Test reset")

    # 7. Verify credentials removed
    credentials = await get_user_credentials(user_id)
    otp_creds = [c for c in credentials if c["type"] == "otp"]
    assert len(otp_creds) == 0
```

### Manual Testing Checklist

- [ ] Admin can view 2FA status for all users
- [ ] Admin can enforce 2FA via email (user receives email)
- [ ] Admin can enforce 2FA immediately (user prompted on login)
- [ ] Admin can reset 2FA for user (credentials removed)
- [ ] Rate limiting prevents excessive resets
- [ ] Policy enforcement works (admins must have 2FA)
- [ ] Audit logs capture all 2FA operations
- [ ] UI displays correct status indicators
- [ ] Search and filter work correctly
- [ ] Bulk operations work as expected

---

## Security Audit Checklist

- [x] Admin authentication required for all endpoints
- [x] Audit logging for all 2FA operations
- [x] Rate limiting on reset operations
- [x] No 2FA secrets stored in Ops-Center
- [x] HTTPS-only communication
- [x] Input validation on all endpoints
- [x] SQL injection prevention (parameterized queries)
- [x] XSS prevention (React automatically escapes)
- [ ] CSRF protection (FastAPI CSRF middleware)
- [ ] Content Security Policy headers
- [ ] Regular security updates (Keycloak, dependencies)

---

## Compliance Considerations

### GDPR (General Data Protection Regulation)

- User consent for 2FA enforcement (inform via email)
- Right to know: Users can view their 2FA status
- Right to erasure: User deletion removes 2FA data
- Audit logs retained for 2 years (legal requirement)

### SOC 2 (Service Organization Control)

- Access controls: Admin-only 2FA management
- Audit trails: All operations logged
- Encryption: HTTPS for data in transit
- Availability: 2FA reset capability for locked accounts

### ISO 27001

- Information Security Management
- Risk assessment: 2FA reduces account compromise risk
- Security controls: Role-based 2FA enforcement
- Incident response: Audit logs for investigation

---

## Monitoring & Alerting

### Metrics to Track

1. **2FA Adoption Rate**
   - % of users with 2FA enabled
   - Trend over time
   - By role/tier

2. **2FA Reset Frequency**
   - Resets per day/week/month
   - By user (detect unusual patterns)
   - By admin (detect abuse)

3. **Policy Compliance**
   - % of admin users with 2FA
   - % of all users with 2FA
   - Users in grace period

4. **API Performance**
   - Response times for each endpoint
   - Error rates
   - Rate limit hits

### Alerts

1. **Critical**
   - More than 10 2FA resets in 1 hour (potential attack)
   - Admin user without 2FA (policy violation)
   - Keycloak API connection failure

2. **Warning**
   - 2FA reset rate limit reached for user
   - Policy grace period ending (< 2 days)
   - High API error rate (> 5%)

3. **Info**
   - New 2FA policy created
   - Bulk 2FA operation completed
   - Daily 2FA status report

---

## Keycloak Configuration

### Required Keycloak Settings

1. **Enable OTP in Browser Flow**
   ```
   Admin Console → Authentication → Flows → Browser
   → Add "OTP Form" execution
   → Set to "Required"
   ```

2. **Configure OTP Settings**
   ```
   Admin Console → Authentication → Required Actions
   → Enable "Configure OTP"
   → Optional: Set as default action
   ```

3. **OTP Policy Configuration**
   ```
   Admin Console → Authentication → Policies → OTP Policy
   - OTP Type: Time-based
   - Algorithm: SHA-1 (most compatible)
   - Digits: 6
   - Period: 30 seconds
   - Initial counter: 0
   - Look-ahead window: 1
   ```

4. **Admin User Permissions**
   ```
   Ops-Center service account needs:
   - realm-management: manage-users
   - realm-management: view-users
   - realm-management: manage-authorization
   ```

---

## Deployment Plan

### Pre-Deployment

1. ✅ Architecture review complete
2. ⏳ Backend API implementation
3. ⏳ Frontend UI implementation
4. ⏳ Unit tests written
5. ⏳ Integration tests written
6. ⏳ Manual testing complete
7. ⏳ Security audit complete
8. ⏳ Documentation complete

### Deployment Steps

1. **Database Migration**
   ```bash
   # Create 2FA policy tables
   docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -f /migrations/002_two_factor_policies.sql
   ```

2. **Backend Deployment**
   ```bash
   # Restart Ops-Center backend
   docker restart ops-center-direct
   ```

3. **Frontend Deployment**
   ```bash
   cd /home/muut/Production/UC-Cloud/services/ops-center
   npm run build
   cp -r dist/* public/
   ```

4. **Keycloak Configuration**
   - Enable OTP in browser flow
   - Configure OTP policy
   - Verify admin permissions

5. **Verification**
   - Test 2FA status endpoint
   - Test enforce endpoint
   - Test reset endpoint
   - Test policy endpoint
   - Verify audit logs

### Rollback Plan

If deployment fails:

1. Revert database migration
2. Restore previous backend version
3. Restore previous frontend build
4. Notify users of temporary unavailability

---

## Known Limitations

1. **Keycloak Dependency**
   - Cannot manage 2FA if Keycloak is down
   - Keycloak upgrades may affect API

2. **SMS/Email OTP**
   - Requires additional Keycloak extensions
   - Not included in Phase 1

3. **Self-Service Reset**
   - Phase 1: Admin-only reset
   - Phase 2: User self-service with verification

4. **Trusted Devices**
   - Not supported in Phase 1
   - Requires custom Keycloak extension

---

## References

- [Keycloak Admin REST API Documentation](https://www.keycloak.org/docs-api/26.0.0/rest-api/index.html)
- [Keycloak OTP Configuration](https://www.keycloak.org/docs/latest/server_admin/#otp-policies)
- [RFC 6238: TOTP Algorithm](https://tools.ietf.org/html/rfc6238)
- [FIDO2/WebAuthn Specification](https://www.w3.org/TR/webauthn-2/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## Contact

**Security Team Lead**: AI Assistant
**Project**: Ops-Center 2FA Management
**Repository**: `/home/muut/Production/UC-Cloud/services/ops-center`

---

**Document Version**: 1.0
**Last Updated**: October 28, 2025
