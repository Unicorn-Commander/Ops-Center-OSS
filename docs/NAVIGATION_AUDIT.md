# Ops-Center Navigation Audit Report

**Generated**: October 27, 2025
**Purpose**: Comprehensive audit of navigation structure, routes, and pages to identify gaps and improve RBAC organization
**Focus**: Ensure all users can access personal settings (including API Keys/BYOK)

---

## Executive Summary

### Current State
- **Navigation Menu Items**: 35+ menu items across 4 main sections
- **Route Definitions**: 60+ routes defined in `routes.js`
- **Existing Page Components**: 75+ React components
- **RBAC Levels**: System Admin, Org Admin, End User

### Key Issues Identified
1. ❌ **API Keys (BYOK) hidden in admin section** - Regular users cannot access personal API keys
2. ❌ **No unified "Account" section** - Personal settings scattered across navigation
3. ✅ **Subscription pages exist** - But not all integrated into navigation
4. ✅ **Organization pages exist** - Properly scoped to org admins
5. ⚠️ **Many orphaned pages** - 40+ components without menu items

### Recommendations
1. ✅ **CREATE** "Account" section for all users (Profile, Security, API Keys, Notifications)
2. ✅ **MOVE** API Keys from `/admin/account/api-keys` menu item from admin section to Account section
3. ✅ **INTEGRATE** existing subscription pages into navigation
4. ✅ **KEEP** organization pages as-is (org admins only)
5. ⚠️ **REVIEW** orphaned pages for archival or integration

---

## Section 1: Current Navigation Structure (Layout.jsx)

### 1.1 Dashboard (All Users)
**Menu Item**: Dashboard
**Path**: `/admin/`
**Component**: `DashboardPro`
**RBAC**: All authenticated users
**Status**: ✅ Active, works correctly

---

### 1.2 Infrastructure Section (System Admin Only)

#### Section Header: "Infrastructure"
**Visibility**: `userRole === 'admin'`
**Status**: ✅ Correct - only system admins

#### 1.2.1 Services
**Menu Item**: Services
**Path**: `/admin/services`
**Component**: `Services`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.2.2 Hardware Management
**Menu Item**: Hardware Management
**Path**: `/admin/infrastructure/hardware`
**Component**: `HardwareManagement`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.2.3 Monitoring
**Menu Item**: Monitoring
**Path**: `/admin/system`
**Component**: `System`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.2.4 LLM Management
**Menu Item**: LLM Management
**Path**: `/admin/llm-management`
**Component**: `LLMManagement` (not found - using `Models` instead)
**RBAC**: System admin only
**Status**: ⚠️ Component mismatch

#### 1.2.5 LLM Providers
**Menu Item**: LLM Providers
**Path**: `/admin/litellm-providers`
**Component**: `LiteLLMManagement`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.2.6 LLM Usage
**Menu Item**: LLM Usage
**Path**: `/admin/llm/usage`
**Component**: `LLMUsage`
**RBAC**: System admin only (should be all users?)
**Status**: ⚠️ Should all users see their own LLM usage?

#### 1.2.7 Cloudflare DNS
**Menu Item**: Cloudflare DNS
**Path**: `/admin/infrastructure/cloudflare`
**Component**: `CloudflareDNS`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.2.8 Traefik (Submenu)
**Menu Items**: Dashboard, Routes, Services, SSL Certificates, Metrics
**Paths**: `/admin/traefik/*`
**Components**: `TraefikDashboard`, `TraefikRoutes`, `TraefikServices`, `TraefikSSL`, `TraefikMetrics`
**RBAC**: System admin only
**Status**: ✅ Active

---

### 1.3 Users & Organizations Section (System Admin Only)

#### Section Header: "Users & Organizations"
**Visibility**: `userRole === 'admin'`
**Status**: ✅ Correct - only system admins

#### 1.3.1 User Management
**Menu Item**: User Management
**Path**: `/admin/system/users`
**Component**: `UserManagement`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.3.2 Local Users
**Menu Item**: Local Users
**Path**: `/admin/system/local-user-management`
**Component**: `LocalUserManagement`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.3.3 Organizations
**Menu Item**: Organizations
**Path**: `/admin/org/settings`
**Component**: `OrganizationSettings`
**RBAC**: System admin only
**Status**: ⚠️ Misleading - should go to organization list, not settings

#### 1.3.4 API Keys ❌ PROBLEM
**Menu Item**: API Keys
**Path**: `/admin/account/api-keys`
**Component**: `AccountAPIKeys` (exists!)
**RBAC**: System admin only
**Status**: ❌ **WRONG** - Should be accessible to ALL users for BYOK

**Issue**: This is a personal user feature (BYOK - Bring Your Own Key) hidden in the admin section. Regular users need to manage their own API keys for external services like OpenAI, Anthropic, etc.

**Solution**: Move to new "Account" section visible to all users

---

### 1.4 Billing & Usage Section (System Admin Only)

#### Section Header: "Billing & Usage"
**Visibility**: `userRole === 'admin'`
**Status**: ✅ Correct - platform-wide billing analytics

#### 1.4.1 Credits & Tiers
**Menu Item**: Credits & Tiers
**Path**: `/admin/credits`
**Component**: `CreditDashboard`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.4.2 Billing Dashboard
**Menu Item**: Billing Dashboard
**Path**: `/admin/system/billing`
**Component**: `BillingDashboard`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.4.3 Advanced Analytics
**Menu Item**: Advanced Analytics
**Path**: `/admin/system/analytics`
**Component**: `AdvancedAnalytics`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.4.4 Usage Metrics
**Menu Item**: Usage Metrics
**Path**: `/admin/system/usage-metrics`
**Component**: `UsageMetrics`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.4.5 Subscriptions
**Menu Item**: Subscriptions
**Path**: `/admin/billing`
**Component**: `SubscriptionManagement`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.4.6 Invoices
**Menu Item**: Invoices
**Path**: `/admin/system/billing#invoices`
**Component**: `BillingDashboard` (anchor link)
**RBAC**: System admin only
**Status**: ✅ Active

---

### 1.5 Platform Section (System Admin Only)

#### Section Header: "Platform"
**Visibility**: `userRole === 'admin'`
**Status**: ✅ Correct

#### 1.5.1 Unicorn Brigade
**Menu Item**: Unicorn Brigade
**Path**: `/admin/brigade`
**Component**: `Brigade`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.5.2 Center-Deep Search
**Menu Item**: Center-Deep Search
**Path**: `https://search.unicorncommander.ai` (external)
**Component**: External link
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.5.3 Email Settings
**Menu Item**: Email Settings
**Path**: `/admin/platform/email-settings`
**Component**: `EmailSettings`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.5.4 Platform Settings
**Menu Item**: Platform Settings
**Path**: `/admin/platform/settings`
**Component**: `PlatformSettings`
**RBAC**: System admin only
**Status**: ✅ Active

#### 1.5.5 API Documentation
**Menu Item**: API Documentation
**Path**: `/admin/platform/api-docs`
**Component**: `ApiDocumentation`
**RBAC**: System admin only
**Status**: ✅ Active

---

## Section 2: Route Definitions (routes.js)

### 2.1 Personal Section Routes

#### Dashboard
**Route**: `/admin/`
**Component**: `DashboardPro`
**Roles**: All authenticated users
**Status**: ✅ Has menu item

#### Account Submenu
**Section**: "My Account"
**Icon**: `UserCircleIcon`
**Status**: ⚠️ Defined in routes.js but NOT in navigation menu

**Sub-routes**:
1. **Profile & Preferences**
   - Path: `/admin/account/profile`
   - Component: `UserSettings` (needs refactor to `AccountProfile`)
   - Status: ✅ Component exists (`AccountProfile.jsx`)
   - Menu: ❌ Missing from navigation

2. **Notifications**
   - Path: `/admin/account/notifications`
   - Component: `AccountNotifications`
   - Status: ✅ Component exists (placeholder)
   - Menu: ❌ Missing from navigation

3. **Notification Preferences**
   - Path: `/admin/account/notification-settings`
   - Component: `NotificationSettings`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

4. **Security & Sessions**
   - Path: `/admin/account/security`
   - Component: `AccountSecurity`
   - Status: ✅ Component exists (placeholder)
   - Menu: ❌ Missing from navigation

5. **API Keys (BYOK)** ❌ CRITICAL
   - Path: `/admin/account/api-keys`
   - Component: `AccountAPIKeys`
   - Status: ✅ Component exists
   - Menu: ❌ HIDDEN in admin section (should be in Account section)

#### Subscription Submenu
**Section**: "My Subscription"
**Icon**: `CreditCardIcon`
**Status**: ⚠️ Defined in routes.js but NOT in navigation menu

**Sub-routes**:
1. **Current Plan**
   - Path: `/admin/subscription/plan`
   - Component: `SubscriptionPlan`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

2. **Usage & Limits**
   - Path: `/admin/subscription/usage`
   - Component: `SubscriptionUsage`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

3. **Billing History**
   - Path: `/admin/subscription/billing`
   - Component: `SubscriptionBilling`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

4. **Payment Methods**
   - Path: `/admin/subscription/payment`
   - Component: `SubscriptionPayment`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

#### Credits & Usage
**Section**: "Credits & Usage"
**Status**: ⚠️ Defined in routes.js but not fully in navigation

**Sub-routes**:
1. **Credit Dashboard**
   - Path: `/admin/credits`
   - Component: `CreditDashboard`
   - Status: ✅ Component exists
   - Menu: ⚠️ In admin section (should be personal?)

2. **Pricing Tiers**
   - Path: `/admin/credits/tiers`
   - Component: `TierComparison`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

---

### 2.2 Organization Section Routes

**Section**: "Organization"
**Icon**: `BuildingOfficeIcon`
**Visibility**: `orgRoles: ['admin', 'owner']`
**Status**: ⚠️ Defined in routes.js but NOT in navigation menu

**Sub-routes**:
1. **Team Members**
   - Path: `/admin/org/team`
   - Component: `OrganizationTeam`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

2. **Roles & Permissions**
   - Path: `/admin/org/roles`
   - Component: `OrganizationRoles`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

3. **Organization Settings**
   - Path: `/admin/org/settings`
   - Component: `OrganizationSettings`
   - Status: ✅ Component exists
   - Menu: ✅ Present (but misleading - goes to settings, not list)

4. **Organization Billing**
   - Path: `/admin/org/billing`
   - Component: `OrganizationBilling`
   - Status: ✅ Component exists
   - Menu: ❌ Missing from navigation

---

### 2.3 System Section Routes

**Section**: "System"
**Icon**: `CogIcon`
**Visibility**: `roles: ['admin']`
**Status**: ✅ Fully implemented in navigation

All system admin routes are properly integrated into navigation menu.

---

## Section 3: Orphaned Pages (Components Without Menu Items)

### 3.1 Orphaned Account Pages
These exist but have no navigation menu items:

1. ✅ `AccountProfile.jsx` - User profile settings
2. ✅ `AccountSecurity.jsx` - Password/2FA settings
3. ✅ `AccountNotifications.jsx` - Notification preferences
4. ❌ `AccountAPIKeys.jsx` - API keys (HAS menu item but in WRONG section)

**Recommendation**: Create "Account" section in navigation for all users

---

### 3.2 Orphaned Subscription Pages
These exist but have no navigation menu items:

1. ✅ `SubscriptionPlan.jsx` - Current subscription plan
2. ✅ `SubscriptionUsage.jsx` - API usage tracking
3. ✅ `SubscriptionBilling.jsx` - Invoice history
4. ✅ `SubscriptionPayment.jsx` - Payment methods

**Recommendation**: Create "My Subscription" section in navigation for all users

---

### 3.3 Orphaned Organization Pages
These exist but have incomplete navigation:

1. ✅ `OrganizationTeam.jsx` - Team member management (MISSING)
2. ✅ `OrganizationRoles.jsx` - Role management (MISSING)
3. ⚠️ `OrganizationSettings.jsx` - Organization settings (HAS menu item)
4. ✅ `OrganizationBilling.jsx` - Org billing (MISSING)
5. ✅ `OrganizationsList.jsx` - List of organizations (NOT IN ROUTES.JS)

**Recommendation**: Create "My Organization" section in navigation for org admins

---

### 3.4 Orphaned Analytics Pages
These exist as separate components:

1. `Analytics.jsx` - General analytics
2. `AdvancedAnalytics.jsx` - ✅ Has menu item (admin)
3. `RevenueAnalytics.jsx` - No menu item
4. `UsageAnalytics.jsx` - No menu item
5. `UsageMetrics.jsx` - ✅ Has menu item (admin)
6. `UserAnalytics.jsx` - No menu item

**Recommendation**: Keep in admin section, review for consolidation

---

### 3.5 Orphaned Settings Pages
Multiple settings pages exist:

1. `Settings.jsx` - Generic settings (deprecated?)
2. `SystemSettings.jsx` - System config (deprecated?)
3. `UserSettings.jsx` - ⚠️ Should be refactored to `AccountProfile`
4. `PlatformSettings.jsx` - ✅ Has menu item (admin)
5. `CloudflareSettings.jsx` - Cloudflare-specific
6. `CredentialsManagement.jsx` - Credentials vault
7. `NameCheapSettings.jsx` - NameCheap DNS

**Recommendation**: Consolidate or integrate into existing sections

---

### 3.6 Backup/Duplicate Pages
These appear to be backups or duplicates:

1. `Logs_backup.jsx` - Backup of Logs
2. `Security_backup.jsx` - Backup of Security
3. `UserManagement.integration.example.jsx` - Example file

**Recommendation**: Archive or delete

---

### 3.7 Specialized Pages Without Menu Items

#### Migration
- `MigrationWizard.jsx` - Database migration wizard

#### Permissions
- `PermissionManagement.jsx` - Permission editor
- `PermissionsManagement.jsx` - Duplicate?

#### Upgrade Flow
- `UpgradeFlow.jsx` - Subscription upgrade wizard

**Recommendation**: Keep as utility pages accessed via buttons/links, not navigation

---

## Section 4: Gap Analysis

### 4.1 Missing from Navigation (But Should Be Added)

#### For ALL Users:
1. ❌ **Account** section header (NEW)
   - Profile & Preferences
   - Security & Sessions
   - **API Keys (BYOK)** ← CRITICAL - Move from admin section
   - Notification Preferences

2. ❌ **My Subscription** section
   - Current Plan
   - Usage & Limits
   - Billing History
   - Payment Methods

3. ⚠️ **Credits & Tiers** - Currently in admin section, should be personal?

#### For Organization Members:
4. ❌ **My Organization** section header (NEW)
   - Team Members
   - Roles & Permissions
   - Organization Settings
   - Organization Billing (owner only)

#### For System Admins:
All properly integrated ✅

---

### 4.2 Incorrectly Placed in Navigation

1. ❌ **API Keys** - Currently in "Users & Organizations" (admin only)
   - **Should be**: "Account" section (all users)
   - **Reason**: BYOK is a personal user feature, not admin-only

2. ⚠️ **Organizations** menu item - Goes to settings instead of list
   - **Current**: `/admin/org/settings` (OrganizationSettings)
   - **Should be**: `/admin/organizations` (OrganizationsList)

3. ⚠️ **Credits & Tiers** - In admin billing section
   - **Current**: Admin only
   - **Should be**: Personal section or both?

---

### 4.3 Missing Components (Routes Defined But No Component)

All routes in `routes.js` have corresponding components ✅

---

### 4.4 Missing Routes (Components Exist But No Route)

1. `OrganizationsList.jsx` - No route defined
2. Various analytics pages without routes

**Recommendation**: Add routes or archive components

---

## Section 5: RBAC Analysis

### 5.1 Current RBAC Levels

#### System Admin (`role: admin`)
- Full access to all sections
- Infrastructure management
- User management
- Platform-wide billing and analytics
- System configuration

#### Organization Admin (`org_role: admin`)
- Should have access to organization management
- Currently missing navigation for org features

#### Organization Owner (`org_role: owner`)
- Same as org admin + billing access
- Currently missing navigation for org features

#### End User (`role: user`, `role: viewer`)
- Should have access to personal account settings
- Should have access to personal subscription
- Should have access to personal API keys (BYOK)
- **Currently missing all navigation for personal features**

---

### 5.2 RBAC Issues Identified

1. ❌ **API Keys accessible only to admins** - Should be accessible to ALL users
2. ❌ **No personal account section** - Users cannot manage profiles/security
3. ❌ **No subscription management for users** - Users cannot view/manage their plans
4. ❌ **No organization section** - Org admins cannot manage teams/settings
5. ⚠️ **LLM Usage in admin section** - Should users see their own usage?

---

## Section 6: Recommendations

### 6.1 High Priority (Immediate Action Required)

#### 1. Create "Account" Section for ALL Users ✅
**Location**: Top of navigation (after Dashboard)
**Visibility**: All authenticated users
**Items**:
- Profile & Preferences (`/admin/account/profile`)
- Security & Sessions (`/admin/account/security`)
- **API Keys (BYOK)** (`/admin/account/api-keys`) ← MOVE from admin section
- Notification Preferences (`/admin/account/notification-settings`)

**Components**: All exist, just need navigation integration

---

#### 2. Move API Keys from Admin Section ✅
**Current**: Users & Organizations → API Keys (admin only)
**New**: Account → API Keys (BYOK) (all users)
**Reason**: BYOK is a personal feature for users to bring their own OpenAI/Anthropic/etc keys

---

#### 3. Create "My Subscription" Section for ALL Users ✅
**Location**: Below Account section
**Visibility**: All authenticated users
**Items**:
- Current Plan (`/admin/subscription/plan`)
- Usage & Limits (`/admin/subscription/usage`)
- Billing History (`/admin/subscription/billing`)
- Payment Methods (`/admin/subscription/payment`) - owner only

**Components**: All exist, just need navigation integration

---

### 6.2 Medium Priority (Next Sprint)

#### 4. Create "My Organization" Section for Org Admins ✅
**Location**: Below My Subscription
**Visibility**: `org_role: admin` or `owner`
**Items**:
- Team Members (`/admin/org/team`)
- Roles & Permissions (`/admin/org/roles`)
- Organization Settings (`/admin/org/settings`)
- Organization Billing (`/admin/org/billing`) - owner only

**Components**: All exist, just need navigation integration

---

#### 5. Fix Organizations Menu Item
**Current**: Goes to `/admin/org/settings` (OrganizationSettings)
**New**: Goes to `/admin/organizations` (OrganizationsList)
**Add Route**: For `OrganizationsList.jsx`

---

### 6.3 Low Priority (Future Consideration)

#### 6. Review Credits & Tiers Placement
**Question**: Should "Credits & Tiers" be in personal section, admin section, or both?
**Current**: Admin only
**Consider**: Users might want to see available tiers for upgrade decisions

---

#### 7. Consolidate Analytics Pages
Multiple analytics components exist. Consider consolidating:
- `Analytics.jsx`
- `RevenueAnalytics.jsx`
- `UsageAnalytics.jsx`
- `UserAnalytics.jsx`

Into fewer, more comprehensive pages.

---

#### 8. Archive Backup Files
Remove or archive:
- `Logs_backup.jsx`
- `Security_backup.jsx`
- `UserManagement.integration.example.jsx`

---

#### 9. Review Orphaned Settings Pages
Consolidate or integrate:
- `Settings.jsx` (deprecated?)
- `SystemSettings.jsx` (deprecated?)
- `CloudflareSettings.jsx`
- `CredentialsManagement.jsx`
- `NameCheapSettings.jsx`

---

## Section 7: Proposed Navigation Structure

### NEW Navigation (After Changes)

```
┌─────────────────────────────────────────────────────────────┐
│                    ALL AUTHENTICATED USERS                   │
└─────────────────────────────────────────────────────────────┘

📊 Dashboard                           [All Users]

👤 Account                             [All Users - NEW SECTION]
├─ Profile & Preferences
├─ Security & Sessions
├─ API Keys (BYOK)                     ← MOVED from admin section
└─ Notification Preferences

💳 My Subscription                     [All Users - NEW SECTION]
├─ Current Plan
├─ Usage & Limits
├─ Billing History
└─ Payment Methods                     [Owner only]

┌─────────────────────────────────────────────────────────────┐
│                   ORGANIZATION MEMBERS ONLY                  │
└─────────────────────────────────────────────────────────────┘

🏢 My Organization                     [org_role: admin/owner - NEW SECTION]
├─ Team Members
├─ Roles & Permissions
├─ Organization Settings
└─ Organization Billing                [Owner only]

┌─────────────────────────────────────────────────────────────┐
│                      SYSTEM ADMINS ONLY                      │
└─────────────────────────────────────────────────────────────┘

🖥️  Infrastructure                    [role: admin]
├─ Services
├─ Hardware Management
├─ Monitoring
├─ LLM Management
├─ LLM Providers
├─ LLM Usage
├─ Cloudflare DNS
└─ Traefik
   ├─ Dashboard
   ├─ Routes
   ├─ Services
   ├─ SSL Certificates
   └─ Metrics

👥 Users & Organizations               [role: admin]
├─ User Management
├─ Local Users
└─ Organizations                       ← Fix: should go to org list

💰 Billing & Usage                     [role: admin]
├─ Credits & Tiers
├─ Billing Dashboard
├─ Advanced Analytics
├─ Usage Metrics
├─ Subscriptions
└─ Invoices

⚙️  Platform                           [role: admin]
├─ Unicorn Brigade
├─ Center-Deep Search (external)
├─ Email Settings
├─ Platform Settings
└─ API Documentation
```

---

## Section 8: Implementation Checklist

### Phase 1: Account Section & API Keys (CRITICAL)
- [ ] Update `Layout.jsx`:
  - [ ] Add "Account" section header (after Dashboard, before admin sections)
  - [ ] Add section divider styling for Account
  - [ ] Add menu items:
    - [ ] Profile & Preferences → `/admin/account/profile`
    - [ ] Security & Sessions → `/admin/account/security`
    - [ ] API Keys (BYOK) → `/admin/account/api-keys`
    - [ ] Notification Preferences → `/admin/account/notification-settings`
  - [ ] Remove "API Keys" from "Users & Organizations" section
  - [ ] Add visibility condition: All authenticated users (no role check)

- [ ] Update `routes.js`:
  - [ ] Verify all account routes are correctly defined
  - [ ] Update descriptions if needed

- [ ] Test:
  - [ ] Login as regular user (non-admin)
  - [ ] Verify Account section is visible
  - [ ] Verify API Keys is accessible
  - [ ] Verify all account pages load correctly

---

### Phase 2: Subscription Section
- [ ] Update `Layout.jsx`:
  - [ ] Add "My Subscription" section header (below Account)
  - [ ] Add section divider styling
  - [ ] Add menu items:
    - [ ] Current Plan → `/admin/subscription/plan`
    - [ ] Usage & Limits → `/admin/subscription/usage`
    - [ ] Billing History → `/admin/subscription/billing`
    - [ ] Payment Methods → `/admin/subscription/payment`
  - [ ] Add visibility condition: All authenticated users
  - [ ] Add special condition for Payment Methods: owner only

- [ ] Test:
  - [ ] Login as regular user
  - [ ] Verify subscription section is visible
  - [ ] Verify all pages load correctly

---

### Phase 3: Organization Section
- [ ] Update `Layout.jsx`:
  - [ ] Add "My Organization" section header (below Subscription, before admin sections)
  - [ ] Add section divider styling
  - [ ] Add menu items:
    - [ ] Team Members → `/admin/org/team`
    - [ ] Roles & Permissions → `/admin/org/roles`
    - [ ] Organization Settings → `/admin/org/settings`
    - [ ] Organization Billing → `/admin/org/billing`
  - [ ] Add visibility condition: `userOrgRole === 'admin' || userOrgRole === 'owner'`
  - [ ] Fix "Organizations" menu item in admin section to go to org list

- [ ] Update `routes.js`:
  - [ ] Add route for `OrganizationsList.jsx`

- [ ] Test:
  - [ ] Login as org admin
  - [ ] Verify organization section is visible
  - [ ] Verify all pages load correctly
  - [ ] Login as non-org-member, verify section is hidden

---

### Phase 4: Polish & Cleanup
- [ ] Update section header styling to match existing admin sections
- [ ] Ensure icon consistency across all menu items
- [ ] Test collapsed sidebar behavior with new sections
- [ ] Test mobile navigation with new sections
- [ ] Update documentation
- [ ] Archive backup files

---

## Section 9: Testing Matrix

### Test Case 1: Regular User (Non-Admin)
**User**: `role: user`, `org_role: null`

**Expected Visible Sections**:
- ✅ Dashboard
- ✅ Account (NEW)
  - ✅ Profile & Preferences
  - ✅ Security & Sessions
  - ✅ API Keys (BYOK)
  - ✅ Notification Preferences
- ✅ My Subscription (NEW)
  - ✅ Current Plan
  - ✅ Usage & Limits
  - ✅ Billing History
  - ⚠️ Payment Methods (if owner)
- ❌ My Organization (not visible - not org member)
- ❌ Infrastructure (not visible)
- ❌ Users & Organizations (not visible)
- ❌ Billing & Usage (not visible)
- ❌ Platform (not visible)

---

### Test Case 2: Organization Admin
**User**: `role: user`, `org_role: admin`

**Expected Visible Sections**:
- ✅ Dashboard
- ✅ Account (all items)
- ✅ My Subscription (all items)
- ✅ My Organization (NEW)
  - ✅ Team Members
  - ✅ Roles & Permissions
  - ✅ Organization Settings
  - ❌ Organization Billing (owner only)
- ❌ Infrastructure (not visible)
- ❌ Users & Organizations (not visible)
- ❌ Billing & Usage (not visible)
- ❌ Platform (not visible)

---

### Test Case 3: Organization Owner
**User**: `role: user`, `org_role: owner`

**Expected Visible Sections**:
- ✅ Dashboard
- ✅ Account (all items)
- ✅ My Subscription (all items including Payment Methods)
- ✅ My Organization (all items including Organization Billing)
- ❌ Infrastructure (not visible)
- ❌ Users & Organizations (not visible)
- ❌ Billing & Usage (not visible)
- ❌ Platform (not visible)

---

### Test Case 4: System Admin
**User**: `role: admin`, `org_role: null`

**Expected Visible Sections**:
- ✅ Dashboard
- ✅ Account (all items)
- ✅ My Subscription (all items)
- ❌ My Organization (not visible - not org member)
- ✅ Infrastructure (all items)
- ✅ Users & Organizations (all items EXCEPT API Keys - moved to Account)
- ✅ Billing & Usage (all items)
- ✅ Platform (all items)

---

### Test Case 5: System Admin + Org Owner
**User**: `role: admin`, `org_role: owner`

**Expected Visible Sections**:
- ✅ Dashboard
- ✅ Account (all items)
- ✅ My Subscription (all items)
- ✅ My Organization (all items)
- ✅ Infrastructure (all items)
- ✅ Users & Organizations (all items EXCEPT API Keys)
- ✅ Billing & Usage (all items)
- ✅ Platform (all items)

---

## Conclusion

This audit reveals that the Ops-Center has excellent infrastructure and admin capabilities, but lacks proper navigation for personal user features. The primary issue is that **API Keys (BYOK)** is incorrectly placed in the admin section, preventing regular users from managing their own API keys for external services.

**Immediate Action Required**:
1. Create "Account" section for all users
2. Move API Keys from admin section to Account section
3. Integrate existing subscription pages into navigation
4. Create "My Organization" section for org admins

**Impact**: These changes will significantly improve the user experience for non-admin users and properly implement RBAC principles where personal settings are accessible to all users, not just admins.

**Estimated Effort**: 4-6 hours for complete implementation and testing

---

**Next Steps**: Proceed with Phase 1 implementation (Account section + API Keys fix)
