# Route Migration Map - Ops-Center Navigation Reorganization

**Document Version:** 1.0
**Date:** October 13, 2025
**Status:** 🟡 Planning Phase
**Purpose:** Map old routes to new hierarchical structure

---

## Table of Contents

1. [Overview](#overview)
2. [Route Changes Summary](#route-changes-summary)
3. [Detailed Route Mapping](#detailed-route-mapping)
4. [New Routes (Not Previously Accessible)](#new-routes-not-previously-accessible)
5. [Component Changes](#component-changes)
6. [Breaking Changes](#breaking-changes)
7. [Redirect Strategy](#redirect-strategy)
8. [Implementation Checklist](#implementation-checklist)

---

## Overview

This document maps the migration from the current flat route structure to the new hierarchical organization aligned with the NAVIGATION-REFINEMENT-PROPOSAL.md. All existing routes will be redirected to maintain backwards compatibility.

### Migration Goals

- ✅ **Zero Downtime**: All existing routes redirect to new locations
- ✅ **Backwards Compatibility**: External links continue working
- ✅ **Clear Organization**: Routes reflect logical hierarchy (Personal, Org, System)
- ✅ **Role Clarity**: Route paths indicate permission requirements

---

## Route Changes Summary

### Statistics

- **Total Existing Routes**: 14
- **Routes Moved**: 11
- **Routes Split**: 2 (UserSettings, BillingDashboard)
- **Routes Added**: 8 (new sub-pages)
- **Routes Unchanged**: 1 (Dashboard at `/admin/`)

### Change Categories

| Category | Count | Description |
|----------|-------|-------------|
| System Routes | 10 | Moved to `/admin/system/*` namespace |
| Personal Routes | 1 | Moved to `/admin/account/*` namespace |
| Billing Routes | 1 | Moved to `/admin/subscription/*` namespace |
| Organization Routes | 4 | **NEW** - Previously missing from navigation |
| Account Sub-pages | 4 | **NEW** - Split from UserSettings |
| Subscription Sub-pages | 4 | **NEW** - Split from BillingDashboard |

---

## Detailed Route Mapping

### System Administration Routes (Admin Only)

All system administration routes moved to `/admin/system/*` namespace.

| Old Route | New Route | Component | Status | Notes |
|-----------|-----------|-----------|--------|-------|
| `/admin/models` | `/admin/system/models` | AIModelManagement | ✅ Redirect | AI model management |
| `/admin/services` | `/admin/system/services` | Services | ✅ Redirect | Docker services |
| `/admin/system` | `/admin/system/resources` | System | ✅ Redirect | CPU/GPU/Memory metrics |
| `/admin/network` | `/admin/system/network` | Network | ✅ Redirect | Network config |
| `/admin/storage` | `/admin/system/storage` | StorageBackup | ✅ Redirect | Volume management |
| `/admin/logs` | `/admin/system/logs` | Logs | ✅ Redirect | System logs |
| `/admin/security` | `/admin/system/security` | Security | ✅ Redirect | Security policies |
| `/admin/authentication` | `/admin/system/authentication` | Authentication | ✅ Redirect | Keycloak/SSO |
| `/admin/extensions` | `/admin/system/extensions` | Extensions | ✅ Redirect | Plugin management |
| `/admin/landing` | `/admin/system/landing` | LandingCustomization | ✅ Redirect | Landing page editor |
| `/admin/settings` | `/admin/system/settings` | Settings (rename to SystemSettings) | ⚠️ Redirect + Rename | System-wide settings |

### Personal/Account Routes (All Users)

Personal user settings moved to `/admin/account/*` namespace.

| Old Route | New Route | Component | Status | Notes |
|-----------|-----------|-----------|--------|-------|
| `/admin/user-settings` | `/admin/account/profile` | UserSettings → AccountProfile | ✅ Redirect + Refactor | Personal info |
| `/admin/user-settings` | `/admin/account/notifications` | AccountNotifications (new) | 🆕 New | Notification preferences |
| `/admin/user-settings` | `/admin/account/security` | AccountSecurity (new) | 🆕 New | Password, 2FA, sessions |
| `/admin/user-settings` | `/admin/account/api-keys` | AccountAPIKeys (new) | 🆕 New | BYOK personal keys |

### Subscription/Billing Routes (All Users)

Billing routes moved to `/admin/subscription/*` namespace.

| Old Route | New Route | Component | Status | Notes |
|-----------|-----------|-----------|--------|-------|
| `/admin/billing` | `/admin/subscription/plan` | BillingDashboard → SubscriptionPlan | ✅ Redirect + Refactor | Current plan details |
| `/admin/billing` | `/admin/subscription/usage` | SubscriptionUsage (new) | 🆕 New | API usage tracking |
| `/admin/billing` | `/admin/subscription/billing` | SubscriptionBilling (new) | 🆕 New | Invoice history |
| `/admin/billing` | `/admin/subscription/payment` | SubscriptionPayment (new) | 🆕 New | Payment methods (owner only) |

### Organization Routes (Org Admin/Owner)

**NEW SECTION** - Organization management routes (previously missing).

| Old Route | New Route | Component | Status | Notes |
|-----------|-----------|-----------|--------|-------|
| ❌ Not in nav | `/admin/org/team` | UserManagement | 🚨 CRITICAL | **Page exists but missing from nav!** |
| N/A | `/admin/org/roles` | OrganizationRoles (new) | 🆕 New | Role definitions |
| N/A | `/admin/org/settings` | OrganizationSettings (new) | 🆕 New | Org preferences |
| N/A | `/admin/org/billing` | OrganizationBilling (new) | 🆕 New | Org-wide billing (owner only) |

### Unchanged Routes

| Route | Component | Status | Notes |
|-------|-----------|--------|-------|
| `/admin/` | DashboardPro | ✅ No change | Main dashboard remains at root |
| `/` | PublicLanding | ✅ No change | Public landing page |
| `/admin/login` | Login | ✅ No change | Login page |

---

## New Routes (Not Previously Accessible)

### High Priority

These routes represent existing functionality that was inaccessible:

1. **`/admin/org/team`** → UserManagement
   - **Status**: 🚨 CRITICAL - Page exists, missing from navigation
   - **Component**: Already built, just needs to be added to nav
   - **Impact**: Users cannot currently access team management

### Medium Priority

These routes require new components but are logical splits:

2. **`/admin/account/notifications`** → AccountNotifications
   - Extract from UserSettings or create new
   - Email/push notification preferences

3. **`/admin/account/security`** → AccountSecurity
   - Extract from UserSettings or create new
   - Password change, 2FA setup, active sessions

4. **`/admin/account/api-keys`** → AccountAPIKeys
   - BYOK (Bring Your Own Key) management
   - Personal API keys for external services

5. **`/admin/subscription/usage`** → SubscriptionUsage
   - API usage tracking and limits
   - Usage graphs and quota monitoring

6. **`/admin/subscription/billing`** → SubscriptionBilling
   - Invoice history
   - Download invoices as PDF

7. **`/admin/subscription/payment`** → SubscriptionPayment
   - Payment method management
   - Credit card CRUD operations

### Lower Priority

These routes represent organization-level features:

8. **`/admin/org/roles`** → OrganizationRoles
   - Define custom roles within organization
   - Set granular permissions

9. **`/admin/org/settings`** → OrganizationSettings
   - Organization name, logo, branding
   - Shared team preferences

10. **`/admin/org/billing`** → OrganizationBilling
    - Organization-wide billing dashboard
    - Team seat management
    - Consolidated usage across team

---

## Component Changes

### Components to Refactor

#### 1. UserSettings.jsx → Split into 4 components

**Current**: Single page with all user settings
**New**: Split into focused sub-pages

```javascript
// OLD (single component)
UserSettings.jsx → All personal settings in one page

// NEW (4 focused components)
AccountProfile.jsx       → Personal info, preferences
AccountNotifications.jsx → Email/push notification settings
AccountSecurity.jsx      → Password, 2FA, active sessions
AccountAPIKeys.jsx       → BYOK personal API keys
```

**Migration Path**:
1. Create new directory: `src/pages/Account/`
2. Extract sections from UserSettings.jsx into separate files
3. Create shared components for common UI patterns
4. Update imports in App.jsx

#### 2. BillingDashboard.jsx → Split into 4 components

**Current**: Single page with all billing information
**New**: Split into focused sub-pages

```javascript
// OLD (single component)
BillingDashboard.jsx → All billing in one page

// NEW (4 focused components)
SubscriptionPlan.jsx    → Current plan, features, upgrade/downgrade
SubscriptionUsage.jsx   → API usage tracking, limits, graphs
SubscriptionBilling.jsx → Invoice history, download PDFs
SubscriptionPayment.jsx → Payment methods (owner only)
```

**Migration Path**:
1. Create new directory: `src/pages/Subscription/`
2. Extract sections from BillingDashboard.jsx
3. Add Stripe payment method management
4. Add usage tracking with graphs
5. Update imports in App.jsx

#### 3. Settings.jsx → Rename to SystemSettings.jsx

**Current**: Generic "Settings" name (confusing)
**New**: "SystemSettings" (admin-only, system-wide settings)

```javascript
// OLD
Settings.jsx → Ambiguous name

// NEW
SystemSettings.jsx → Clear it's system-wide, admin-only
```

**Migration Path**:
1. Rename file: `Settings.jsx` → `SystemSettings.jsx`
2. Update imports in App.jsx
3. Route: `/admin/settings` → `/admin/system/settings`

### New Components to Create

#### Organization Management

All new components for organization features:

```javascript
src/pages/Organization/
├── OrganizationTeam.jsx      → Wrapper for UserManagement
├── OrganizationRoles.jsx     → Custom role definitions
├── OrganizationSettings.jsx  → Org name, logo, branding
└── OrganizationBilling.jsx   → Org-wide billing (owner only)
```

**Design Notes**:
- Follow Material UI design patterns (matching UserManagement.jsx)
- Share theme context with rest of app (Unicorn, Dark, Light themes)
- Use existing API patterns from backend

---

## Breaking Changes

### ⚠️ Potential Breaking Changes

1. **Direct Links to Old Routes**
   - **Impact**: External bookmarks, documentation links
   - **Mitigation**: Permanent redirects (301) from old to new routes
   - **Duration**: Keep redirects for minimum 6 months

2. **API Endpoint Changes**
   - **Impact**: If frontend route changes affect backend endpoints
   - **Status**: ✅ No impact - Backend endpoints unchanged
   - **Note**: All API endpoints use `/api/v1/*` prefix, separate from UI routes

3. **Role-Based Access Changes**
   - **Impact**: Some routes now require org_role in addition to role
   - **Example**: `/admin/org/*` requires `org_role: admin` or `org_role: owner`
   - **Mitigation**: Backend already returns org_role, frontend needs to check it

4. **Component Import Paths**
   - **Impact**: Internal - developers only
   - **Files Affected**: App.jsx, Layout.jsx
   - **Migration**: Update import statements during implementation

### ✅ Non-Breaking Changes

1. **Dashboard Route** - Remains at `/admin/`
2. **API Endpoints** - No changes to backend routes
3. **Authentication Flow** - No changes to login/logout
4. **Existing Pages** - All current pages continue to work

---

## Redirect Strategy

### Permanent Redirects (301)

All old routes will use permanent redirects to new locations:

```javascript
// Redirect implementation in App.jsx

import { Navigate } from 'react-router-dom';

// System admin redirects
<Route path="/admin/models" element={<Navigate to="/admin/system/models" replace />} />
<Route path="/admin/services" element={<Navigate to="/admin/system/services" replace />} />
<Route path="/admin/system" element={<Navigate to="/admin/system/resources" replace />} />
<Route path="/admin/network" element={<Navigate to="/admin/system/network" replace />} />
<Route path="/admin/storage" element={<Navigate to="/admin/system/storage" replace />} />
<Route path="/admin/logs" element={<Navigate to="/admin/system/logs" replace />} />
<Route path="/admin/security" element={<Navigate to="/admin/system/security" replace />} />
<Route path="/admin/authentication" element={<Navigate to="/admin/system/authentication" replace />} />
<Route path="/admin/extensions" element={<Navigate to="/admin/system/extensions" replace />} />
<Route path="/admin/landing" element={<Navigate to="/admin/system/landing" replace />} />
<Route path="/admin/settings" element={<Navigate to="/admin/system/settings" replace />} />

// Personal redirects
<Route path="/admin/user-settings" element={<Navigate to="/admin/account/profile" replace />} />

// Billing redirects
<Route path="/admin/billing" element={<Navigate to="/admin/subscription/plan" replace />} />
```

### Redirect Timing

| Phase | Duration | Action |
|-------|----------|--------|
| **Phase 1** | Week 1 | Deploy redirects, update internal links |
| **Phase 2** | Week 2-4 | Monitor analytics, gather feedback |
| **Phase 3** | Month 2 | Update documentation, external links |
| **Phase 4** | Month 6+ | Consider removing redirects (optional) |

**Recommendation**: Keep redirects indefinitely (negligible performance impact).

---

## Implementation Checklist

### Pre-Implementation

- [ ] Review this migration map with team
- [ ] Approve route changes
- [ ] Create backup of current codebase
- [ ] Document any custom modifications

### Phase 1: Route Configuration (Day 1)

- [x] Create `src/config/routes.js` with new structure
- [x] Document all route mappings
- [ ] Review and approve routes.js

### Phase 2: Component Preparation (Days 2-3)

- [ ] Create new directories:
  - [ ] `src/pages/Account/`
  - [ ] `src/pages/Subscription/`
  - [ ] `src/pages/Organization/`
- [ ] Stub out new components (placeholder content)
- [ ] Rename `Settings.jsx` → `SystemSettings.jsx`

### Phase 3: App.jsx Route Updates (Day 4)

- [ ] Update imports in App.jsx
- [ ] Add all new routes
- [ ] Add redirect routes
- [ ] Test all routes load correctly
- [ ] Verify redirects work

### Phase 4: Layout.jsx Navigation Updates (Days 5-6)

- [ ] Update Layout.jsx with hierarchical navigation
- [ ] Create NavigationSection component (collapsible)
- [ ] Create NavigationItem component
- [ ] Add role-based section visibility
- [ ] Test navigation with different user roles

### Phase 5: Component Refactoring (Days 7-10)

- [ ] Split UserSettings.jsx:
  - [ ] AccountProfile.jsx
  - [ ] AccountNotifications.jsx
  - [ ] AccountSecurity.jsx
  - [ ] AccountAPIKeys.jsx
- [ ] Split BillingDashboard.jsx:
  - [ ] SubscriptionPlan.jsx
  - [ ] SubscriptionUsage.jsx
  - [ ] SubscriptionBilling.jsx
  - [ ] SubscriptionPayment.jsx
- [ ] Create Organization components:
  - [ ] Integrate UserManagement at `/admin/org/team`
  - [ ] OrganizationRoles.jsx
  - [ ] OrganizationSettings.jsx
  - [ ] OrganizationBilling.jsx

### Phase 6: Testing (Days 11-12)

- [ ] Test all routes as admin role
- [ ] Test all routes as power_user role
- [ ] Test all routes as user role
- [ ] Test all routes as viewer role
- [ ] Test org_role: owner permissions
- [ ] Test org_role: admin permissions
- [ ] Test org_role: member permissions
- [ ] Verify redirects work
- [ ] Test mobile navigation
- [ ] Test keyboard navigation
- [ ] Test theme switching
- [ ] Accessibility audit

### Phase 7: Documentation Updates (Day 13)

- [ ] Update internal documentation
- [ ] Update user guides
- [ ] Update API documentation (if needed)
- [ ] Create changelog
- [ ] Update README.md

### Phase 8: Deployment (Days 14-15)

- [ ] Deploy to staging environment
- [ ] User acceptance testing
- [ ] Monitor error logs
- [ ] Deploy to production
- [ ] Monitor analytics
- [ ] Gather user feedback

---

## Risk Assessment

### Low Risk

- ✅ Redirects maintain backwards compatibility
- ✅ No database schema changes
- ✅ No API endpoint changes
- ✅ Gradual rollout possible

### Medium Risk

- ⚠️ Users may be confused by new navigation initially
- ⚠️ External documentation links may be outdated
- ⚠️ Browser bookmarks will redirect but update slowly

### Mitigation Strategies

1. **User Communication**
   - Announce navigation changes in advance
   - Show in-app notification on first visit after update
   - Provide changelog with visual comparison

2. **Monitoring**
   - Track redirect usage (which old routes still being used)
   - Monitor 404 errors for any missed routes
   - Track navigation patterns in analytics

3. **Rollback Plan**
   - Keep git branch with old navigation
   - Can revert routes in App.jsx quickly
   - Redirects work bidirectionally if needed

---

## Success Metrics

### Quantitative

- [ ] Zero 404 errors on old routes (redirects working)
- [ ] 100% of routes accessible based on role
- [ ] 100% test coverage on route access control
- [ ] < 5% increase in support tickets about navigation

### Qualitative

- [ ] Users can find features faster (user testing)
- [ ] Navigation structure is intuitive (user feedback)
- [ ] Organization features are discoverable
- [ ] Role-based access is clear and logical

---

## References

- **Proposal**: [NAVIGATION-REFINEMENT-PROPOSAL.md](./NAVIGATION-REFINEMENT-PROPOSAL.md)
- **Route Config**: [src/config/routes.js](../src/config/routes.js)
- **Current Layout**: [src/components/Layout.jsx](../src/components/Layout.jsx)
- **Current Routes**: [src/App.jsx](../src/App.jsx) lines 165-180

---

## Questions & Decisions Log

### Q1: Should we remove redirects eventually?

**Decision**: Keep indefinitely. Redirects have negligible performance impact and provide better UX.

### Q2: What happens to old bookmarks?

**Answer**: They will automatically redirect to new routes. Browser will update URL in address bar.

### Q3: Do we need database migrations?

**Answer**: No. Routes are frontend-only. Backend API endpoints unchanged.

### Q4: How to handle role-based redirects?

**Example**: If a `user` role tries to access `/admin/system/models` (admin-only), redirect to `/admin/` with error message.

### Q5: Should `/admin/org/team` use existing UserManagement or create new component?

**Decision**: Use existing UserManagement.jsx initially, may refactor later to OrganizationTeam.jsx for consistency.

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Planning | Day 1 | Route config & documentation |
| Setup | Days 2-3 | Component stubs and directory structure |
| Routes | Day 4 | App.jsx updated with new routes |
| Navigation | Days 5-6 | Layout.jsx hierarchical navigation |
| Components | Days 7-10 | Refactored and new components |
| Testing | Days 11-12 | Full QA across all roles |
| Docs | Day 13 | Updated documentation |
| Deploy | Days 14-15 | Staging → Production |

**Total Estimated Time**: 15 working days (3 weeks)

---

**Document Status**: ✅ Complete - Ready for Implementation
**Next Step**: Review route configuration and approve for Phase 2
**Last Updated**: October 13, 2025
