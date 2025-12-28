# Routes Configuration Quick Reference

**Document Version:** 1.0
**Date:** October 13, 2025
**Purpose:** Quick reference for using the centralized route configuration

---

## Usage Guide

### Importing Routes

```javascript
// Import the entire routes object
import routes from './config/routes';

// Import helper functions
import {
  getAllRoutes,
  getNavigationStructure,
  getRedirects,
  findRedirect,
  hasRouteAccess,
  getAccessibleRoutes,
  getRoutesBySection
} from './config/routes';
```

---

## Helper Functions

### 1. getAllRoutes()

Returns flat array of all routes (useful for React Router).

```javascript
const allRoutes = getAllRoutes();
// Returns: [
//   { path: '/admin/', component: 'DashboardPro', roles: [...], name: 'Dashboard' },
//   { path: '/admin/account/profile', component: 'UserSettings', roles: [...], ... },
//   // ... all other routes
// ]
```

**Use Case**: Generate Route components in App.jsx

```javascript
<Routes>
  {getAllRoutes().map(route => (
    <Route
      key={route.path}
      path={route.path}
      element={<RouteComponent route={route} />}
    />
  ))}
</Routes>
```

---

### 2. getNavigationStructure()

Returns hierarchical navigation structure (useful for Layout.jsx).

```javascript
const nav = getNavigationStructure();
// Returns: {
//   personal: { dashboard: {...}, account: {...}, subscription: {...} },
//   organization: { section: 'Organization', children: {...} },
//   system: { section: 'System', children: {...} }
// }
```

**Use Case**: Build collapsible navigation menu

```javascript
const nav = getNavigationStructure();

return (
  <nav>
    {/* Personal Section */}
    <NavSection data={nav.personal} />

    {/* Organization Section */}
    {hasOrgRole(user) && <NavSection data={nav.organization} />}

    {/* System Section */}
    {isAdmin(user) && <NavSection data={nav.system} />}
  </nav>
);
```

---

### 3. getRedirects()

Returns array of redirect mappings.

```javascript
const redirects = getRedirects();
// Returns: [
//   { from: '/admin/models', to: '/admin/system/models', type: 'permanent' },
//   { from: '/admin/services', to: '/admin/system/services', type: 'permanent' },
//   // ... all redirects
// ]
```

**Use Case**: Setup redirect routes in App.jsx

```javascript
<Routes>
  {getRedirects().map(redirect => (
    <Route
      key={redirect.from}
      path={redirect.from}
      element={<Navigate to={redirect.to} replace />}
    />
  ))}
</Routes>
```

---

### 4. findRedirect(oldPath)

Find new route for a legacy path.

```javascript
const newPath = findRedirect('/admin/models');
// Returns: '/admin/system/models'

const nonExistent = findRedirect('/admin/nonexistent');
// Returns: null
```

**Use Case**: Manual redirect logic

```javascript
if (isOldRoute(path)) {
  const newPath = findRedirect(path);
  if (newPath) {
    navigate(newPath);
  }
}
```

---

### 5. hasRouteAccess(route, userRole, userOrgRole)

Check if user has access to a route.

```javascript
const route = { path: '/admin/system/models', roles: ['admin'] };
const userRole = 'user';

const canAccess = hasRouteAccess(route, userRole);
// Returns: false (user role doesn't have access)

// With org role check
const orgRoute = {
  path: '/admin/org/team',
  orgRoles: ['admin', 'owner']
};
const canAccessOrg = hasRouteAccess(orgRoute, 'user', 'admin');
// Returns: true (has org admin role)
```

**Use Case**: Conditional rendering in navigation

```javascript
{hasRouteAccess(route, user.role, user.orgRole) && (
  <NavItem route={route} />
)}
```

---

### 6. getAccessibleRoutes(userRole, userOrgRole)

Filter routes by user permissions.

```javascript
const userRole = 'power_user';
const userOrgRole = 'admin';

const accessible = getAccessibleRoutes(userRole, userOrgRole);
// Returns: Array of routes user can access
```

**Use Case**: Generate filtered navigation menu

```javascript
const accessibleRoutes = getAccessibleRoutes(user.role, user.orgRole);

return (
  <nav>
    {accessibleRoutes.map(route => (
      <NavItem key={route.path} route={route} />
    ))}
  </nav>
);
```

---

### 7. getRoutesBySection(section)

Get routes for a specific section.

```javascript
const personalRoutes = getRoutesBySection('personal');
const orgRoutes = getRoutesBySection('organization');
const systemRoutes = getRoutesBySection('system');
```

**Use Case**: Build sectioned navigation

```javascript
const personalRoutes = getRoutesBySection('personal');

return (
  <NavSection title="Personal">
    {Object.entries(personalRoutes).map(([key, route]) => (
      <NavItem key={key} route={route} />
    ))}
  </NavSection>
);
```

---

## Route Object Structure

Each route object contains:

```javascript
{
  path: '/admin/system/models',           // URL path
  component: 'AIModelManagement',          // Component name (string)
  roles: ['admin', 'power_user'],          // Required platform roles
  orgRoles: ['admin', 'owner'],            // Required org roles (optional)
  name: 'AI Models',                       // Display name
  icon: 'CubeIcon',                        // Icon identifier
  description: 'Model registry...',        // Description
  status: 'planned'                        // Implementation status (optional)
}
```

---

## Accessing Specific Routes

### By Direct Path

```javascript
import routes from './config/routes';

// Dashboard
const dashboard = routes.personal.dashboard;

// Account Profile
const profile = routes.personal.account.children.profile;

// Organization Team
const team = routes.organization.children.team;

// System Models
const models = routes.system.children.models;
```

### By Section

```javascript
// All personal routes
const personal = routes.personal;

// All organization routes
const org = routes.organization.children;

// All system routes
const system = routes.system.children;

// All redirects
const redirects = routes.redirects;

// Legacy routes (for migration reference)
const legacy = routes.legacy;
```

---

## Role-Based Access Patterns

### Platform Roles

- **admin**: Full system access
- **power_user**: Extended user access (models, extensions, storage)
- **user**: Basic user access (dashboard, logs, personal settings)
- **viewer**: Read-only access (dashboard only)

### Organization Roles

- **owner**: Full org control (billing, team management)
- **admin**: Org administration (team management, settings)
- **member**: Basic org member (read-only org info)

### Access Check Examples

```javascript
// Check platform role
if (route.roles && route.roles.includes(userRole)) {
  // User has platform role access
}

// Check org role
if (route.orgRoles && route.orgRoles.includes(userOrgRole)) {
  // User has org role access
}

// Check both (use helper function)
if (hasRouteAccess(route, userRole, userOrgRole)) {
  // User has full access
}
```

---

## Navigation Menu Structure

### Expected Hierarchy

```
🏠 Dashboard
👤 My Account
   ├─ Profile & Preferences
   ├─ Notifications
   ├─ Security & Sessions
   └─ API Keys (BYOK)
💳 My Subscription
   ├─ Current Plan
   ├─ Usage & Limits
   ├─ Billing History
   └─ Payment Methods

─────────────────────
ORG MANAGEMENT
─────────────────────

🏢 Organization
   ├─ Team Members ⚠️
   ├─ Roles & Permissions
   ├─ Organization Settings
   └─ Organization Billing

─────────────────────
SYSTEM ADMINISTRATION
─────────────────────

⚙️ System
   ├─ AI Models
   ├─ Services
   ├─ Resources
   ├─ Network
   ├─ Storage & Backup
   ├─ Security
   ├─ Authentication
   ├─ Extensions
   ├─ System Logs
   └─ Landing Page
```

---

## Implementation Status

### ✅ Complete

- [x] routes.js configuration file
- [x] Helper functions
- [x] Route mappings
- [x] Redirect definitions

### 🚧 In Progress

- [ ] App.jsx route updates
- [ ] Layout.jsx navigation updates
- [ ] Component refactoring

### 📋 Planned

- [ ] AccountNotifications component
- [ ] AccountSecurity component
- [ ] AccountAPIKeys component
- [ ] SubscriptionUsage component
- [ ] SubscriptionBilling component
- [ ] SubscriptionPayment component
- [ ] OrganizationRoles component
- [ ] OrganizationSettings component
- [ ] OrganizationBilling component

---

## Examples

### Example 1: Generate All Routes in App.jsx

```javascript
import { getAllRoutes } from './config/routes';
import { lazy, Suspense } from 'react';

// Dynamically import components
const componentMap = {
  DashboardPro: lazy(() => import('./pages/DashboardPro')),
  AIModelManagement: lazy(() => import('./pages/AIModelManagement')),
  // ... other components
};

function AppRoutes() {
  const allRoutes = getAllRoutes();

  return (
    <Routes>
      {allRoutes.map(route => {
        const Component = componentMap[route.component];
        return (
          <Route
            key={route.path}
            path={route.path}
            element={
              <Suspense fallback={<LoadingScreen />}>
                <Component />
              </Suspense>
            }
          />
        );
      })}
    </Routes>
  );
}
```

### Example 2: Role-Based Navigation in Layout.jsx

```javascript
import { getNavigationStructure, hasRouteAccess } from './config/routes';

function Navigation({ user }) {
  const nav = getNavigationStructure();

  return (
    <nav>
      {/* Personal Section - always visible */}
      <NavSection title="Personal" data={nav.personal} user={user} />

      {/* Organization Section - org admins/owners only */}
      {hasRouteAccess(nav.organization, user.role, user.orgRole) && (
        <NavSection title="Organization" data={nav.organization} user={user} />
      )}

      {/* System Section - platform admins only */}
      {user.role === 'admin' && (
        <NavSection title="System" data={nav.system} user={user} />
      )}
    </nav>
  );
}
```

### Example 3: Setup Redirects

```javascript
import { getRedirects } from './config/routes';
import { Navigate } from 'react-router-dom';

function RedirectRoutes() {
  const redirects = getRedirects();

  return (
    <>
      {redirects.map(redirect => (
        <Route
          key={redirect.from}
          path={redirect.from}
          element={<Navigate to={redirect.to} replace />}
        />
      ))}
    </>
  );
}
```

---

## Best Practices

### 1. Always Use Helper Functions

❌ **Don't**: Manually filter routes
```javascript
const adminRoutes = routes.system.children.filter(r =>
  r.roles && r.roles.includes('admin')
);
```

✅ **Do**: Use helper function
```javascript
const adminRoutes = getAccessibleRoutes('admin');
```

### 2. Check Access Before Rendering

❌ **Don't**: Render and hide based on role
```javascript
<NavItem route={route} style={{ display: canAccess ? 'block' : 'none' }} />
```

✅ **Do**: Conditionally render
```javascript
{hasRouteAccess(route, user.role, user.orgRole) && (
  <NavItem route={route} />
)}
```

### 3. Use Redirects for Backwards Compatibility

❌ **Don't**: Change routes without redirects
```javascript
<Route path="/admin/system/models" element={<AIModelManagement />} />
// Old /admin/models route breaks
```

✅ **Do**: Add redirect for old route
```javascript
<Route path="/admin/system/models" element={<AIModelManagement />} />
<Route path="/admin/models" element={<Navigate to="/admin/system/models" />} />
```

---

## Troubleshooting

### Issue: Route not accessible

**Check**:
1. User has required `role` in route definition
2. User has required `orgRole` if specified
3. Route is in correct section (personal/organization/system)

### Issue: Redirect not working

**Check**:
1. Redirect is defined in `routes.redirects` array
2. `from` path matches exactly (including `/admin/` prefix)
3. `to` path points to valid new route

### Issue: Component not found

**Check**:
1. Component name matches exactly (case-sensitive)
2. Component is imported in App.jsx
3. Component exists in expected directory

---

## Related Documentation

- [Navigation Refinement Proposal](./NAVIGATION-REFINEMENT-PROPOSAL.md) - Full design proposal
- [Route Migration Map](./ROUTE-MIGRATION-MAP.md) - Detailed migration guide
- [Current App.jsx](../src/App.jsx) - Current route definitions
- [Current Layout.jsx](../src/components/Layout.jsx) - Current navigation

---

**Document Status**: ✅ Complete
**Last Updated**: October 13, 2025
