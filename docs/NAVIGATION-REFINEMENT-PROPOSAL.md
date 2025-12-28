# Ops-Center Navigation Refinement Proposal

**Date:** October 13, 2025
**Status:** Proposal - Awaiting Approval
**Purpose:** Reorganize Ops-Center navigation for better UX in multi-tenant SaaS context

---

## Executive Summary

The current Ops-Center navigation uses a flat list of 14 menu items mixing user-facing features, organization management, and system administration. This proposal reorganizes the navigation into a clear, hierarchical structure that aligns with the multi-tenant SaaS architecture and provides better user experience.

---

## Current State Analysis

### Current Navigation Structure (Layout.jsx:26-41)

**Flat list navigation (14 items):**
1. Dashboard - all roles (admin, power_user, user, viewer)
2. User Settings - all roles
3. Billing - all roles
4. Models & AI - admin, power_user
5. Services - admin
6. Resources (System) - admin
7. Network - admin
8. Storage - admin, power_user
9. Logs - admin, power_user, user
10. Security - admin
11. Authentication - admin
12. Extensions - admin, power_user
13. Landing Page - admin
14. Settings - admin, power_user, user

### Issues Identified

1. **Missing Critical Pages**
   - `UserManagement.jsx` exists but is NOT in navigation (serious oversight)
   - No organization management visible despite multi-tenant architecture
   - BYOK API keys mentioned but no clear UI path

2. **Lack of Hierarchy**
   - All items at same level creates visual clutter
   - No logical grouping by concern (user vs org vs system)
   - Difficult to scan and find relevant features

3. **Role Confusion**
   - "User Settings" (personal) vs "Settings" (system) - unclear distinction
   - "Billing" accessible to all but should differentiate user vs org context
   - No clear separation between tenant features and system admin

4. **Multi-Tenancy Not Reflected**
   - Backend has `get_user_org_context()` with org_id, org_name, org_role
   - Frontend navigation doesn't expose organization management
   - Team collaboration features (mentioned in requirements) not visible

---

## Proposed Navigation Structure

### Three-Tier Hierarchy

#### **TIER 1: Personal (All Users)**
Always visible to authenticated users, regardless of role.

**🏠 Dashboard**
- Main landing page after login
- Quick stats, recent activity
- Service status cards

**👤 My Account**
- Submenu with:
  - Profile & Preferences
  - Notifications
  - Security & Sessions
  - API Keys (BYOK)

**💳 My Subscription** (if user is org owner/admin)
- Submenu with:
  - Current Plan & Features
  - Usage & Limits
  - Billing History
  - Payment Methods
  - Upgrade/Downgrade

---

#### **TIER 2: Organization (Owner, Admin roles)**
Visible only to users with `org_role: owner` or `org_role: admin`.

**🏢 Organization**
- Submenu with:
  - **Team Members** (UserManagement page)
    - List all users in organization
    - Add/remove team members
    - Manage member roles
  - **Roles & Permissions**
    - Define custom roles
    - Set permission levels
  - **Organization Settings**
    - Org name, logo, branding
    - Shared preferences
  - **Organization Billing** (for owner only)
    - Organization-wide usage
    - Team seat management
    - Consolidated billing

---

#### **TIER 3: System Administration (Admin only)**
Visible only to users with `role: admin` (platform administrators, not org admins).

**⚙️ System**
- Submenu with:
  - **AI Models** (AIModelManagement)
    - Model registry
    - Model downloads
    - GPU allocation
  - **Services** (Services page)
    - Docker service management
    - Health monitoring
  - **Resources** (System page)
    - CPU, Memory, GPU, Disk
    - Performance graphs
  - **Network** (Network page)
    - Network configuration
    - Firewall rules
  - **Storage & Backup** (StorageBackup)
    - Volume management
    - Backup schedules
  - **Security** (Security page)
    - Security policies
    - Audit logs
    - Compliance
  - **Authentication** (Authentication page)
    - Keycloak/SSO configuration
    - Identity providers
  - **Extensions** (Extensions)
    - Plugin management
  - **System Logs** (Logs)
    - Service logs
    - Error tracking
  - **Landing Page** (LandingCustomization)
    - Customize public landing

---

## Detailed Mapping

### Personal Section

| Menu Item | Route | Component | Roles | Notes |
|-----------|-------|-----------|-------|-------|
| Dashboard | `/admin/` | DashboardPro | all | Main dashboard |
| My Account → Profile | `/admin/account/profile` | UserSettings (refactored) | all | Personal info |
| My Account → Notifications | `/admin/account/notifications` | New component | all | Email/push preferences |
| My Account → Security | `/admin/account/security` | New component | all | Password, 2FA, sessions |
| My Account → API Keys | `/admin/account/api-keys` | BYOK component | all | Personal API keys |
| My Subscription → Plan | `/admin/subscription/plan` | BillingDashboard (refactored) | owner, admin | Current plan details |
| My Subscription → Usage | `/admin/subscription/usage` | Usage component | owner, admin | API usage stats |
| My Subscription → Billing | `/admin/subscription/billing` | Billing component | owner, admin | Invoices, payment |
| My Subscription → Payment | `/admin/subscription/payment` | Payment methods | owner | Credit cards |

### Organization Section

| Menu Item | Route | Component | Roles | Notes |
|-----------|-------|-----------|-------|-------|
| Organization → Team | `/admin/org/team` | UserManagement | owner, admin | ⚠️ Currently missing from nav! |
| Organization → Roles | `/admin/org/roles` | New component | owner, admin | Role definitions |
| Organization → Settings | `/admin/org/settings` | New component | owner, admin | Org preferences |
| Organization → Billing | `/admin/org/billing` | Org billing component | owner | Org-level billing |

### System Section (Admin Only)

| Menu Item | Route | Component | Roles | Notes |
|-----------|-------|-----------|-------|-------|
| System → AI Models | `/admin/system/models` | AIModelManagement | admin | Existing page |
| System → Services | `/admin/system/services` | Services | admin | Existing page |
| System → Resources | `/admin/system/resources` | System | admin | Existing page (rename route) |
| System → Network | `/admin/system/network` | Network | admin | Existing page |
| System → Storage | `/admin/system/storage` | StorageBackup | admin | Existing page |
| System → Security | `/admin/system/security` | Security | admin | Existing page |
| System → Authentication | `/admin/system/authentication` | Authentication | admin | Existing page |
| System → Extensions | `/admin/system/extensions` | Extensions | admin | Existing page |
| System → Logs | `/admin/system/logs` | Logs | admin | Existing page |
| System → Landing | `/admin/system/landing` | LandingCustomization | admin | Existing page |

---

## Implementation Plan

### Phase 1: Navigation Component Refactor
**Goal:** Update Layout.jsx with new hierarchical structure

**Tasks:**
1. Convert flat navigation array to nested structure with sections
2. Implement collapsible submenu components
3. Add role-based section visibility (personal, org, system)
4. Update active state detection for nested routes
5. Add section headers and dividers
6. Maintain theme compatibility (unicorn, dark, light)

**Files to modify:**
- `src/components/Layout.jsx` (main navigation)
- Create `src/components/NavigationSection.jsx` (collapsible section)
- Create `src/components/NavigationItem.jsx` (menu item with icon)

### Phase 2: Route Reorganization
**Goal:** Update App.jsx routes to match new structure

**Tasks:**
1. Update all routes from `/admin/models` → `/admin/system/models`
2. Create new routes for:
   - `/admin/account/*` (profile, notifications, security, api-keys)
   - `/admin/subscription/*` (plan, usage, billing, payment)
   - `/admin/org/*` (team, roles, settings, billing)
3. Add route redirects for backwards compatibility
4. Test all navigation paths

**Files to modify:**
- `src/App.jsx` (route definitions)

### Phase 3: Component Refactoring
**Goal:** Split existing components into focused sub-pages

**Tasks:**
1. **UserSettings.jsx** → Split into:
   - `AccountProfile.jsx` (personal info)
   - `AccountNotifications.jsx` (notification preferences)
   - `AccountSecurity.jsx` (password, 2FA, sessions)
   - `AccountAPIKeys.jsx` (BYOK keys)

2. **BillingDashboard.jsx** → Split into:
   - `SubscriptionPlan.jsx` (current plan, features)
   - `SubscriptionUsage.jsx` (API usage tracking)
   - `SubscriptionBilling.jsx` (invoices, history)
   - `SubscriptionPayment.jsx` (payment methods)

3. **Settings.jsx** → Rename to `SystemSettings.jsx` (admin only)

4. **UserManagement.jsx**
   - Move to `/admin/org/team` route
   - Add to Organization section in navigation
   - Ensure Material UI components are styled consistently

**New components needed:**
- `OrganizationSettings.jsx`
- `OrganizationRoles.jsx`
- `OrganizationBilling.jsx`
- `AccountSecurity.jsx`
- `AccountNotifications.jsx`

### Phase 4: Testing & Validation
**Goal:** Ensure all navigation paths work correctly

**Tasks:**
1. Test navigation for each role (viewer, user, power_user, admin)
2. Verify role-based visibility of sections
3. Test org_role visibility (member, admin, owner)
4. Verify all routes resolve correctly
5. Test mobile navigation (responsive design)
6. Check keyboard navigation and accessibility
7. Verify theme switching maintains navigation state

---

## Visual Design Mockup

### Sidebar Structure (Desktop)

```
┌─────────────────────────────────────┐
│  🦄 Ops Center                      │
│     UC-1 Pro Control                │
│     v1.0.0                          │
├─────────────────────────────────────┤
│                                     │
│  🏠 Dashboard                       │
│                                     │
│  👤 My Account              ▼       │
│     ├─ Profile                      │
│     ├─ Notifications                │
│     ├─ Security                     │
│     └─ API Keys (BYOK)              │
│                                     │
│  💳 My Subscription         ▼       │
│     ├─ Current Plan                 │
│     ├─ Usage & Limits               │
│     ├─ Billing History              │
│     └─ Payment Methods              │
│                                     │
├─────────────────────────────────────┤
│  ORG MANAGEMENT                     │
├─────────────────────────────────────┤
│                                     │
│  🏢 Organization            ▼       │
│     ├─ Team Members         ⚠️      │
│     ├─ Roles & Permissions          │
│     ├─ Organization Settings        │
│     └─ Organization Billing         │
│                                     │
├─────────────────────────────────────┤
│  SYSTEM ADMINISTRATION              │
├─────────────────────────────────────┤
│                                     │
│  ⚙️ System                  ▼       │
│     ├─ AI Models                    │
│     ├─ Services                     │
│     ├─ Resources                    │
│     ├─ Network                      │
│     ├─ Storage & Backup             │
│     ├─ Security                     │
│     ├─ Authentication               │
│     ├─ Extensions                   │
│     ├─ System Logs                  │
│     └─ Landing Page                 │
│                                     │
├─────────────────────────────────────┤
│  ❓ Help & Documentation            │
│  👤 aaron (Owner)                   │
│  🚪 Logout                          │
│  🦄 ☀️ 🌙 (Theme)                   │
└─────────────────────────────────────┘
```

### Mobile Navigation

- **Hamburger menu** with same hierarchy
- **Bottom tabs** for frequently used items:
  - Dashboard
  - My Account
  - Organization
  - System (if admin)

---

## Benefits of New Structure

### 1. **Improved Discoverability**
- Clear sections reduce cognitive load
- Users can quickly find features in logical groups
- "Team Members" (UserManagement) now properly accessible

### 2. **Role-Based Clarity**
- Personal features always visible (Dashboard, My Account)
- Organization features visible only to org admins
- System features visible only to platform admins
- Eliminates confusion about "which settings?"

### 3. **Scalability**
- Easy to add new features to appropriate sections
- Can expand submenus without cluttering main nav
- Room for future features (workflows, integrations, etc.)

### 4. **Multi-Tenancy Support**
- Organization section makes multi-tenant nature clear
- Team collaboration features properly exposed
- Org-level vs user-level billing clearly separated

### 5. **Professional UX**
- Hierarchical navigation is industry standard (AWS, Azure, Salesforce)
- Collapsible sections reduce visual clutter
- Section headers provide context

---

## Migration Strategy

### Backwards Compatibility

**Route Redirects:**
```javascript
// Old routes → New routes
'/admin/models'         → '/admin/system/models'
'/admin/services'       → '/admin/system/services'
'/admin/system'         → '/admin/system/resources'
'/admin/user-settings'  → '/admin/account/profile'
'/admin/billing'        → '/admin/subscription/plan'
```

**Gradual Rollout:**
1. **Week 1:** Deploy new navigation with redirects (no breaking changes)
2. **Week 2:** Update all internal links to use new routes
3. **Week 3:** Monitor analytics for user navigation patterns
4. **Week 4:** Remove redirects, finalize structure

---

## Success Metrics

**Pre-Implementation Baseline:**
- Average time to find "User Management": N/A (not in nav)
- Average time to find "Billing": ~5 seconds
- Average time to find "System Logs": ~8 seconds

**Post-Implementation Goals:**
- Reduce average navigation time by 30%
- Increase feature discovery (track visits to previously hidden pages)
- Reduce support tickets about "where is...?" by 50%
- Maintain or improve user satisfaction scores

---

## Open Questions for Discussion

1. **Should "Dashboard" remain at `/admin/` or move to `/admin/dashboard`?**
   - Pros of `/admin/`: Shorter URL, less typing
   - Cons: Inconsistent with rest of structure

2. **Should we combine "My Account" and "My Subscription" into one section?**
   - Pros: Fewer top-level items
   - Cons: Less clear distinction between profile and billing

3. **Should viewers have access to Logs page?**
   - Current: No (logs requires user+ role)
   - Question: Should viewers see their own activity logs?

4. **How to handle "Settings" page?**
   - Current: General settings accessible to admin, power_user, user
   - Proposal: Rename to "System Settings" (admin only), move user prefs to "My Account"

5. **Should we add a "Help" section with sub-items?**
   - Documentation
   - API Reference
   - Support/Contact
   - What's New / Changelog

---

## Implementation Checklist

### Pre-Implementation
- [ ] Review proposal with team
- [ ] Approve navigation structure
- [ ] Resolve open questions
- [ ] Create detailed design mockups
- [ ] Get user feedback on prototype

### Phase 1: Navigation Component (Week 1)
- [ ] Create NavigationSection component
- [ ] Create NavigationItem component
- [ ] Update Layout.jsx with new structure
- [ ] Implement collapsible sections
- [ ] Add role-based visibility
- [ ] Test theme compatibility

### Phase 2: Route Reorganization (Week 2)
- [ ] Update App.jsx route definitions
- [ ] Add route redirects
- [ ] Test all navigation paths
- [ ] Update any hardcoded links

### Phase 3: Component Refactoring (Week 3-4)
- [ ] Split UserSettings into sub-components
- [ ] Split BillingDashboard into sub-components
- [ ] Create new Organization components
- [ ] Add UserManagement to navigation
- [ ] Test all new pages

### Phase 4: Testing & Validation (Week 5)
- [ ] Test all roles (viewer, user, power_user, admin)
- [ ] Test org roles (member, admin, owner)
- [ ] Test mobile navigation
- [ ] Test keyboard navigation
- [ ] Accessibility audit
- [ ] Performance testing

### Phase 5: Deployment (Week 6)
- [ ] Deploy to staging
- [ ] User acceptance testing
- [ ] Deploy to production
- [ ] Monitor analytics
- [ ] Gather user feedback

---

## Conclusion

This navigation refinement addresses critical usability issues in the current Ops-Center interface, particularly the missing UserManagement page and lack of multi-tenant organization management. The proposed hierarchical structure aligns with industry standards and the platform's multi-tenant SaaS architecture.

**Next Steps:**
1. Review this proposal with stakeholders
2. Get approval on proposed structure
3. Begin Phase 1 implementation
4. Iterate based on feedback

**Estimated Timeline:** 6 weeks for full implementation
**Risk Level:** Low (backwards compatible, gradual rollout)
**Impact:** High (major UX improvement)

---

**Document Version:** 1.0
**Last Updated:** October 13, 2025
**Author:** Claude (AI Assistant)
**Status:** 🟡 Awaiting Approval
