# QA Testing Strategy - Ops-Center Full Integration
**Project**: Ops-Center Galaxy Theme & Feature Integration
**QA Lead**: Team Lead 4 (Production Validator)
**Created**: October 21, 2025
**Target Completion**: 10-12 hours

---

## Overview

This document outlines the comprehensive testing strategy for Phase 1 of the Ops-Center Full Integration project. The goal is to ensure all new features (Galaxy Theme, Organization API, Profile API, Execution Servers UI, LLM/BYOK enhancements) are production-ready with 80%+ test coverage.

---

## Testing Pyramid

```
              ┌──────────────┐
              │   E2E Tests   │  (10% - Critical Journeys)
              │   ~15 tests   │
              └──────────────┘
            ┌──────────────────┐
            │Integration Tests │  (30% - API & Services)
            │    ~45 tests     │
            └──────────────────┘
        ┌────────────────────────┐
        │     Unit Tests          │  (60% - Components & Functions)
        │      ~120 tests         │
        └────────────────────────┘
```

**Total Test Count Target**: ~180 tests
**Coverage Target**: 80%+ overall
**Test Execution Time**: <5 minutes for full suite

---

## Phase 1: Testing Infrastructure Setup (2 hours)

### 1.1 Backend Testing (pytest)

**Tools**:
- pytest 7.4.0+
- pytest-cov (coverage)
- pytest-asyncio (async tests)
- httpx (API testing)
- freezegun (time mocking)

**Setup**:
```bash
cd /opt/ops-center/backend
pip install pytest pytest-cov pytest-asyncio httpx freezegun
```

**Configuration** (`pytest.ini`):
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --verbose --cov=. --cov-report=html --cov-report=term-missing
asyncio_mode = auto
```

### 1.2 Frontend Testing (Vitest + React Testing Library)

**Tools**:
- Vitest (Vite-native testing)
- @testing-library/react
- @testing-library/jest-dom
- @testing-library/user-event
- msw (API mocking)

**Setup**:
```bash
cd /opt/ops-center
npm install -D vitest @testing-library/react @testing-library/jest-dom \
  @testing-library/user-event jsdom @vitest/ui msw
```

**Configuration** (`vitest.config.js`):
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './tests/setup.js',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/**/*.{js,jsx}'],
      exclude: ['src/main.jsx', 'src/**/*.test.{js,jsx}']
    }
  }
});
```

### 1.3 E2E Testing (Playwright)

**Tools**:
- Playwright 1.40.0+
- playwright-test

**Setup**:
```bash
npm install -D @playwright/test
npx playwright install chromium
```

**Configuration** (`playwright.config.js`):
```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'https://unicorncommander.ai',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure'
  }
});
```

### 1.4 Test Data Fixtures

**Location**: `tests/fixtures/`

**Files to Create**:
- `users.json` - Mock user data (5 roles: admin, moderator, developer, analyst, viewer)
- `organizations.json` - Mock organization data (3 orgs with different sizes)
- `subscriptions.json` - Mock subscription data (4 tiers)
- `apiKeys.json` - Mock API keys data
- `themes.json` - Theme configuration data

---

## Phase 2: Unit Testing (3-4 hours)

### 2.1 Frontend Component Tests

**Priority**: HIGH
**Total Tests**: ~60

#### Galaxy Theme Components

**File**: `tests/unit/components/BackgroundEffects.test.jsx`
**Tests**: 8
- ✅ Renders without crashing
- ✅ Displays animated galaxy gradient
- ✅ Shows stars with twinkle effect
- ✅ Renders neural network nodes
- ✅ Animations run smoothly (no jank)
- ✅ Performance: <16ms per frame
- ✅ Cleanup on unmount (no memory leaks)
- ✅ Respects prefers-reduced-motion

**File**: `tests/unit/contexts/ThemeContext.test.jsx`
**Tests**: 12
- ✅ Initializes with default theme
- ✅ Loads theme from localStorage
- ✅ Switches to 'galaxy' theme
- ✅ Switches to 'dark' theme
- ✅ Switches to 'light' theme
- ✅ Switches to 'unicorn' theme
- ✅ Persists theme to localStorage
- ✅ Syncs theme with backend API
- ✅ Handles API sync failure gracefully
- ✅ Applies correct CSS classes
- ✅ Updates theme context value
- ✅ Notifies child components on change

#### New Frontend Components

**File**: `tests/unit/pages/ExecutionServers.test.jsx`
**Tests**: 10
- ✅ Renders server list
- ✅ Displays server status (active/inactive)
- ✅ Shows correct server metrics
- ✅ Handles add server action
- ✅ Handles edit server action
- ✅ Handles delete server action
- ✅ Validates server form inputs
- ✅ Shows loading state
- ✅ Handles API errors
- ✅ Filters servers by status

**File**: `tests/unit/pages/LLMManagement.test.jsx` (Enhanced)
**Tests**: 15
- ✅ Renders provider list
- ✅ Displays provider status
- ✅ Shows model list per provider
- ✅ Handles add provider action
- ✅ Handles configure provider action
- ✅ Handles test connection
- ✅ Shows connection status (success/failure)
- ✅ Validates provider credentials
- ✅ Displays usage statistics
- ✅ Shows rate limits
- ✅ Handles provider deletion
- ✅ Filters models by capability
- ✅ Sorts providers by usage
- ✅ Shows provider health status
- ✅ Handles real-time updates (WebSocket)

**File**: `tests/unit/pages/BYOKManagement.test.jsx` (Enhanced)
**Tests**: 12
- ✅ Renders BYOK key list
- ✅ Displays key usage statistics
- ✅ Shows key rotation status
- ✅ Handles add key action
- ✅ Handles rotate key action
- ✅ Handles revoke key action
- ✅ Validates key format
- ✅ Encrypts keys before storing
- ✅ Shows key expiration warnings
- ✅ Displays usage graphs
- ✅ Handles key quota limits
- ✅ Shows cost savings metrics

#### Data Files

**File**: `tests/unit/data/serviceDescriptions.test.js`
**Tests**: 3
- ✅ Contains all expected services
- ✅ Each service has required fields (name, description, icon)
- ✅ Descriptions are not empty

**File**: `tests/unit/data/roleDescriptions.test.js`
**Tests**: 3
- ✅ Contains all 5 roles
- ✅ Each role has permissions array
- ✅ Role hierarchy is correct

**File**: `tests/unit/data/tierFeatures.test.js`
**Tests**: 4
- ✅ Contains all 4 tiers
- ✅ Each tier has feature matrix
- ✅ Enterprise tier has most features
- ✅ Trial tier has basic features

**File**: `tests/unit/data/tooltipContent.test.js`
**Tests**: 2
- ✅ Contains tooltips for all major features
- ✅ Tooltip content is user-friendly

### 2.2 Backend Unit Tests

**Priority**: HIGH
**Total Tests**: ~60

#### Organization API

**File**: `tests/unit/test_org_api_http.py`
**Tests**: 14 (one per endpoint)
- ✅ GET /organizations - List organizations
- ✅ POST /organizations - Create organization
- ✅ GET /organizations/{id} - Get organization
- ✅ PUT /organizations/{id} - Update organization
- ✅ DELETE /organizations/{id} - Delete organization
- ✅ GET /organizations/{id}/members - List members
- ✅ POST /organizations/{id}/members - Add member
- ✅ DELETE /organizations/{id}/members/{user_id} - Remove member
- ✅ PUT /organizations/{id}/members/{user_id}/role - Update member role
- ✅ POST /organizations/{id}/invite - Send invitation
- ✅ GET /organizations/{id}/invitations - List invitations
- ✅ PUT /organizations/{id}/invitations/{invite_id}/accept - Accept invite
- ✅ DELETE /organizations/{id}/invitations/{invite_id} - Revoke invite
- ✅ GET /organizations/{id}/billing - Get organization billing

#### Profile API

**File**: `tests/unit/test_profile_api.py`
**Tests**: 8
- ✅ GET /users/me - Get current user profile
- ✅ PUT /users/me - Update profile
- ✅ PUT /users/me/preferences - Update preferences
- ✅ PUT /users/me/password - Change password
- ✅ GET /users/me/activity - Get activity log
- ✅ GET /users/me/sessions - List sessions
- ✅ DELETE /users/me/sessions/{id} - Revoke session
- ✅ POST /users/me/2fa/enable - Enable 2FA

#### Database Functions

**File**: `tests/unit/test_database_helpers.py`
**Tests**: 10
- ✅ Database connection successful
- ✅ Transaction rollback on error
- ✅ Schema migration applies correctly
- ✅ Audit log table exists
- ✅ Organizations table has correct schema
- ✅ Foreign keys enforced
- ✅ Unique constraints work
- ✅ Index creation successful
- ✅ Query performance within limits
- ✅ Connection pool handles concurrent requests

---

## Phase 3: Integration Testing (4-5 hours)

### 3.1 API Integration Tests

**Priority**: CRITICAL
**Total Tests**: ~45

#### Organization API Integration

**File**: `tests/integration/test_org_api_integration.py`
**Tests**: 15
- ✅ Complete organization CRUD cycle
- ✅ Add member to organization
- ✅ Update member role (viewer → developer)
- ✅ Remove member from organization
- ✅ Send invitation email
- ✅ Accept invitation flow
- ✅ Reject/revoke invitation
- ✅ List organization members with pagination
- ✅ Filter members by role
- ✅ Organization billing integration with Lago
- ✅ Organization owner cannot be removed
- ✅ Deleting organization cascades to members
- ✅ Rate limiting on organization creation
- ✅ RBAC: Only admins can create organizations
- ✅ RBAC: Org owner can manage members

#### Profile API Integration

**File**: `tests/integration/test_profile_api_integration.py`
**Tests**: 10
- ✅ User can view their profile
- ✅ User can update profile fields
- ✅ User can change password (with validation)
- ✅ User can update preferences (theme persists)
- ✅ Activity log populates correctly
- ✅ Session management (list, revoke)
- ✅ 2FA enable/disable flow
- ✅ Profile updates sync with Keycloak
- ✅ Avatar upload and storage
- ✅ Email change requires verification

#### Frontend-Backend Integration

**File**: `tests/integration/test_frontend_backend_integration.py`
**Tests**: 20
- ✅ LocalUsers page loads data from API
- ✅ ExecutionServers page CRUD operations work
- ✅ LLM Management connects to real LiteLLM
- ✅ BYOK key encryption/decryption roundtrip
- ✅ Organization pages connect to new API
- ✅ Theme selection persists to backend
- ✅ Galaxy theme CSS loads correctly
- ✅ API error handling shows user-friendly messages
- ✅ Loading states display during API calls
- ✅ Toast notifications work for success/error
- ✅ Authentication flow (login → dashboard)
- ✅ Authorization (RBAC enforced on UI)
- ✅ Pagination works correctly
- ✅ Search/filter queries match API response
- ✅ Real-time updates via WebSocket
- ✅ File uploads (avatar, CSV import)
- ✅ CSV export downloads correctly
- ✅ Bulk operations complete successfully
- ✅ Form validation matches backend rules
- ✅ CSRF protection working

---

## Phase 4: End-to-End Testing (2-3 hours)

### 4.1 Critical User Journeys

**Priority**: CRITICAL
**Total Tests**: ~15

#### Journey 1: New User Signup → Payment → Features Unlocked

**File**: `tests/e2e/user_signup_flow.spec.js`
**Steps**:
1. Navigate to signup page
2. Click "Sign up with Google" (use test account)
3. Complete Google OAuth flow
4. Redirected to Stripe Checkout
5. Enter test card (4242 4242 4242 4242)
6. Payment succeeds
7. Redirected to dashboard
8. Subscription tier shows "Professional"
9. All Pro features unlocked
10. API calls quota shows correctly

**Assertions**:
- ✅ User created in Keycloak
- ✅ Customer created in Lago
- ✅ Subscription active in Lago
- ✅ User attributes populated
- ✅ Dashboard accessible
- ✅ Features match tier

#### Journey 2: Admin User Management Flow

**File**: `tests/e2e/admin_user_management.spec.js`
**Steps**:
1. Login as admin
2. Navigate to User Management
3. Filter users by tier (Professional)
4. Click user row → User Detail page opens
5. Change user role (viewer → developer)
6. Verify permission matrix updates
7. Generate API key for user
8. Verify key appears in list
9. Revoke API key
10. View user activity timeline

**Assertions**:
- ✅ User list loads correctly
- ✅ Filtering works
- ✅ User detail page loads
- ✅ Role update successful
- ✅ API key created and bcrypt hashed
- ✅ API key revoked
- ✅ Activity timeline populated

#### Journey 3: Galaxy Theme Selection & Persistence

**File**: `tests/e2e/galaxy_theme_flow.spec.js`
**Steps**:
1. Login as any user
2. Navigate to account settings
3. Open theme selector
4. Select "Unicorn Galaxy"
5. Verify background effects render
6. Check localStorage has 'galaxy' theme
7. Reload page
8. Verify theme still "galaxy"
9. Navigate to different pages
10. Verify theme persists across navigation

**Assertions**:
- ✅ Theme selector shows all 4 themes
- ✅ Galaxy theme applies CSS correctly
- ✅ Animations running smoothly
- ✅ localStorage updated
- ✅ Backend API called to save preference
- ✅ Theme persists after reload
- ✅ No console errors

#### Journey 4: Organization Creation & Member Invitation

**File**: `tests/e2e/organization_flow.spec.js`
**Steps**:
1. Login as admin
2. Navigate to Organizations
3. Click "Create Organization"
4. Fill form (name, description)
5. Submit
6. Organization created successfully
7. Auto-switched to new organization
8. Click "Invite Member"
9. Enter email, select role (developer)
10. Send invitation
11. Check invitation email sent
12. Login as invited user
13. Accept invitation
14. Verify member added to org

**Assertions**:
- ✅ Organization created in database
- ✅ Auto-switch to new org
- ✅ Invitation created
- ✅ Email sent (check email service logs)
- ✅ Invitation accepted
- ✅ Member added with correct role

#### Journey 5: BYOK Key Management

**File**: `tests/e2e/byok_flow.spec.js`
**Steps**:
1. Login as developer user
2. Navigate to BYOK Management
3. Click "Add API Key"
4. Select provider (OpenAI)
5. Enter API key (test key)
6. Submit
7. Key encrypted and stored
8. View usage statistics (API calls made)
9. Click "Rotate Key"
10. Old key marked inactive
11. New key generated
12. Verify API calls use new key

**Assertions**:
- ✅ Key encrypted before storage
- ✅ Key validation successful
- ✅ Usage stats display correctly
- ✅ Key rotation works
- ✅ Old key deactivated
- ✅ New key active

---

## Phase 5: Performance Testing (1-2 hours)

### 5.1 Frontend Performance

**File**: `tests/performance/galaxy_theme_performance.test.js`
**Metrics**:
- ✅ Animation frame rate >60 FPS
- ✅ First Contentful Paint <1s
- ✅ Time to Interactive <2s
- ✅ Total Bundle Size <3MB
- ✅ Galaxy theme CSS <50KB
- ✅ Memory usage <100MB with theme active
- ✅ No memory leaks after 5 minutes

**File**: `tests/performance/api_response_times.test.js`
**Metrics**:
- ✅ GET /organizations - <100ms (p95)
- ✅ POST /organizations - <200ms (p95)
- ✅ GET /users/me - <50ms (p95)
- ✅ PUT /users/me/preferences - <100ms (p95)
- ✅ GET /admin/users - <150ms (p95)
- ✅ POST /llm/chat/completions - <500ms (p95)

### 5.2 Load Testing

**File**: `tests/performance/load_test.js` (using k6)
**Scenarios**:
- ✅ 100 concurrent users - Response time <500ms
- ✅ 500 concurrent users - No errors, <1s response
- ✅ 1000 concurrent users - Graceful degradation
- ✅ API rate limiting enforced correctly
- ✅ Database connection pool handles load
- ✅ Redis cache hit rate >80%

---

## Phase 6: Security Testing (2 hours)

### 6.1 Authentication & Authorization

**File**: `tests/security/auth_security.test.js`
**Tests**: 12
- ✅ Unauthenticated requests return 401
- ✅ Invalid JWT tokens rejected
- ✅ Expired tokens rejected
- ✅ Token refresh flow works
- ✅ RBAC: Viewer cannot access admin endpoints
- ✅ RBAC: Developer can access LLM endpoints
- ✅ RBAC: Moderator can manage users
- ✅ RBAC: Only admin can create organizations
- ✅ Session fixation attack prevented
- ✅ CSRF protection on state-changing requests
- ✅ XSS protection (input sanitization)
- ✅ SQL injection prevention

### 6.2 Input Validation

**File**: `tests/security/input_validation.test.js`
**Tests**: 8
- ✅ Email validation (invalid emails rejected)
- ✅ Password strength requirements enforced
- ✅ SQL injection strings sanitized
- ✅ XSS payloads sanitized (<script> tags removed)
- ✅ Path traversal attempts blocked (../)
- ✅ File upload: Only allowed extensions
- ✅ File upload: Max size enforced (10MB)
- ✅ Rate limiting on login attempts

### 6.3 API Security

**File**: `tests/security/api_security.test.js`
**Tests**: 6
- ✅ API keys encrypted at rest (bcrypt)
- ✅ Sensitive data not logged
- ✅ HTTPS enforced (HTTP redirects to HTTPS)
- ✅ CORS policy correctly configured
- ✅ Security headers present (CSP, X-Frame-Options)
- ✅ No sensitive info in error messages

---

## Phase 7: Accessibility Testing (1 hour)

### 7.1 WCAG AA Compliance

**File**: `tests/accessibility/wcag_compliance.test.js`
**Tools**: axe-core, pa11y
**Tests**: 10
- ✅ All images have alt text
- ✅ Form inputs have labels
- ✅ Color contrast ratio ≥4.5:1 (Galaxy theme)
- ✅ Keyboard navigation works (Tab, Enter, Esc)
- ✅ Focus indicators visible
- ✅ ARIA labels present on interactive elements
- ✅ Headings in logical order (h1 → h2 → h3)
- ✅ Skip to main content link
- ✅ Screen reader compatible
- ✅ Animations respect prefers-reduced-motion

### 7.2 Galaxy Theme Accessibility

**File**: `tests/accessibility/galaxy_theme_a11y.test.js`
**Tests**: 5
- ✅ Text contrast on galaxy background ≥4.5:1
- ✅ Animations can be disabled
- ✅ Focus indicators visible on dark background
- ✅ No flashing/strobing effects (seizure risk)
- ✅ Theme works with Windows High Contrast Mode

---

## Bug Tracking & Reporting

### Bug Tracking Log

**File**: `tests/reports/bug_tracking_log.md`

**Format**:
```markdown
## Bug #001
**Title**: Theme selection doesn't persist on logout
**Severity**: Medium
**Found**: Unit Testing - ThemeContext
**Status**: Fixed
**Fix**: Added localStorage sync on theme change
**Verified**: 2025-10-21
```

**Categories**:
- CRITICAL: Breaks core functionality
- HIGH: Significant impact, workaround exists
- MEDIUM: Moderate impact
- LOW: Minor cosmetic issue

### Test Coverage Report

**File**: `tests/reports/coverage_report.html`

**Target Coverage**:
- Overall: 80%+
- Frontend: 75%+
- Backend: 85%+
- Critical paths: 95%+

**Tools**:
- Backend: pytest-cov
- Frontend: Vitest coverage (v8)
- Report: HTML + terminal summary

---

## Final QA Sign-Off Checklist

**File**: `tests/reports/QA_SIGN_OFF.md`

### Functional Requirements ✅
- [ ] Galaxy theme selectable
- [ ] All 4 themes working
- [ ] LocalUsers page functional
- [ ] Organization API complete (14 endpoints)
- [ ] Profile API complete (8 endpoints)
- [ ] Execution Servers UI complete
- [ ] LLM Management enhanced
- [ ] BYOK enhanced
- [ ] All data files created

### Quality Requirements ✅
- [ ] 80%+ test coverage achieved
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Performance benchmarks met
- [ ] Security audit passed
- [ ] Accessibility audit passed
- [ ] No critical bugs outstanding

### Documentation ✅
- [ ] API documentation updated
- [ ] User guide for Galaxy theme
- [ ] Test reports generated
- [ ] Bug tracking log complete
- [ ] Deployment notes ready

### Production Readiness ✅
- [ ] Build successful (no errors)
- [ ] Docker container starts
- [ ] All services healthy
- [ ] Database migrations applied
- [ ] Environment variables set
- [ ] Monitoring configured
- [ ] Rollback plan documented

**Sign-Off**:
- QA Lead: ___________________ Date: ___________
- Tech Lead: _________________ Date: ___________
- Project Manager: ___________ Date: ___________

---

## Test Execution Timeline

### Day 1 (6 hours)
- **Hour 1-2**: Infrastructure setup
- **Hour 3-4**: Unit tests (Galaxy theme)
- **Hour 5-6**: Unit tests (frontend components)

### Day 2 (8 hours)
- **Hour 1-3**: Backend unit tests
- **Hour 4-6**: Integration tests
- **Hour 7-8**: E2E tests (critical journeys)

### Day 3 (4 hours)
- **Hour 1-2**: Performance + Security testing
- **Hour 3**: Accessibility testing
- **Hour 4**: Reports + Sign-off

**Total**: 18 hours (can run in parallel with development)

---

## Continuous Testing Strategy

### On Every Commit
- ✅ Run unit tests (fast, <2 min)
- ✅ Lint checks
- ✅ Type checks

### On Every PR
- ✅ Full test suite
- ✅ Coverage report
- ✅ Security scan

### Daily (CI/CD)
- ✅ Integration tests
- ✅ E2E smoke tests
- ✅ Performance regression tests

### Weekly
- ✅ Full E2E suite
- ✅ Accessibility audit
- ✅ Security penetration testing

---

## Success Metrics

1. **Test Coverage**: 80%+ overall
2. **Test Pass Rate**: 95%+ (allow 5% flaky tests)
3. **Bug Escape Rate**: <5% (bugs found in production)
4. **Mean Time to Detect (MTTD)**: <1 hour
5. **Mean Time to Repair (MTTR)**: <4 hours
6. **Test Execution Time**: <5 minutes (unit+integration)
7. **E2E Test Reliability**: >90% (no false failures)

---

## Tools & Dependencies

### Backend
- pytest==7.4.0
- pytest-cov==4.1.0
- pytest-asyncio==0.21.0
- httpx==0.24.0
- freezegun==1.2.2

### Frontend
- vitest==1.0.0
- @testing-library/react==14.0.0
- @testing-library/jest-dom==6.1.0
- @testing-library/user-event==14.5.0
- jsdom==22.0.0
- msw==2.0.0

### E2E
- @playwright/test==1.40.0

### Performance
- k6==0.47.0
- lighthouse==11.0.0

### Security
- bandit==1.7.5
- safety==2.3.0
- snyk==1.1200.0

### Accessibility
- axe-core==4.8.0
- pa11y==7.0.0

---

**Next Steps**:
1. Install testing dependencies
2. Create test fixtures
3. Spawn sub-agents for each testing category
4. Begin rolling QA as features complete
5. Track bugs in centralized log
6. Generate final reports

**Remember**: Quality is not an afterthought. Test early, test often! 🧪
