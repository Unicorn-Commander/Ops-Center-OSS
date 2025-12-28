# Navigation Migration Guide - Developer Guide

**Version:** 1.0
**Date:** October 13, 2025
**Audience:** Developers, DevOps, System Integrators

---

## Overview

This guide covers technical changes to the Ops-Center navigation system, including component refactoring, route changes, API updates, and integration patterns for custom applications.

---

## Architecture Changes

### Before: Flat Navigation

```javascript
// Old structure (Layout.jsx)
const menuItems = [
  { path: '/admin/', label: 'Dashboard', icon: DashboardIcon },
  { path: '/admin/user-settings', label: 'User Settings', icon: PersonIcon },
  { path: '/admin/billing', label: 'Billing', icon: CreditCardIcon },
  { path: '/admin/models', label: 'Models & AI', icon: SmartToyIcon },
  // ... 10 more items
];
```

### After: Hierarchical Navigation

```javascript
// New structure (Layout.jsx)
const navigationSections = [
  {
    id: 'personal',
    label: 'PERSONAL',
    items: [
      { path: '/admin/', label: 'Dashboard', icon: DashboardIcon },
      {
        id: 'account',
        label: 'My Account',
        icon: PersonIcon,
        submenu: [
          { path: '/admin/account/profile', label: 'Profile' },
          { path: '/admin/account/notifications', label: 'Notifications' },
          { path: '/admin/account/security', label: 'Security' },
          { path: '/admin/account/api-keys', label: 'API Keys' },
        ]
      },
      {
        id: 'subscription',
        label: 'My Subscription',
        icon: CreditCardIcon,
        submenu: [
          { path: '/admin/subscription/plan', label: 'Current Plan' },
          { path: '/admin/subscription/usage', label: 'Usage & Limits' },
          { path: '/admin/subscription/billing', label: 'Billing History' },
          { path: '/admin/subscription/payment', label: 'Payment Methods' },
        ]
      }
    ]
  },
  {
    id: 'organization',
    label: 'ORGANIZATION',
    roles: ['owner', 'admin'], // org_role
    items: [
      {
        id: 'org',
        label: 'Organization',
        icon: BusinessIcon,
        submenu: [
          { path: '/admin/org/team', label: 'Team Members' },
          { path: '/admin/org/roles', label: 'Roles & Permissions' },
          { path: '/admin/org/settings', label: 'Organization Settings' },
          { path: '/admin/org/billing', label: 'Organization Billing', roles: ['owner'] },
        ]
      }
    ]
  },
  {
    id: 'system',
    label: 'SYSTEM ADMINISTRATION',
    roles: ['admin'], // platform role
    items: [
      {
        id: 'system',
        label: 'System',
        icon: SettingsIcon,
        submenu: [
          { path: '/admin/system/models', label: 'AI Models' },
          { path: '/admin/system/services', label: 'Services' },
          { path: '/admin/system/resources', label: 'Resources' },
          { path: '/admin/system/network', label: 'Network' },
          { path: '/admin/system/storage', label: 'Storage & Backup' },
          { path: '/admin/system/security', label: 'Security' },
          { path: '/admin/system/authentication', label: 'Authentication' },
          { path: '/admin/system/extensions', label: 'Extensions' },
          { path: '/admin/system/logs', label: 'System Logs' },
          { path: '/admin/system/landing', label: 'Landing Page' },
        ]
      }
    ]
  }
];
```

---

## Route Changes

### Complete Route Mapping

| Old Route | New Route | Status |
|-----------|-----------|--------|
| `/admin/` | `/admin/` | ✅ Unchanged |
| `/admin/user-settings` | `/admin/account/profile` | 🔄 Redirect |
| `/admin/billing` | `/admin/subscription/plan` | 🔄 Redirect |
| `/admin/models` | `/admin/system/models` | 🔄 Redirect |
| `/admin/services` | `/admin/system/services` | 🔄 Redirect |
| `/admin/system` | `/admin/system/resources` | 🔄 Redirect |
| `/admin/network` | `/admin/system/network` | 🔄 Redirect |
| `/admin/storage` | `/admin/system/storage` | 🔄 Redirect |
| `/admin/logs` | `/admin/system/logs` | 🔄 Redirect |
| `/admin/security` | `/admin/system/security` | 🔄 Redirect |
| `/admin/authentication` | `/admin/system/authentication` | 🔄 Redirect |
| `/admin/extensions` | `/admin/system/extensions` | 🔄 Redirect |
| `/admin/landing` | `/admin/system/landing` | 🔄 Redirect |
| `/admin/settings` | `/admin/system/settings` | 🔄 Redirect |
| N/A | `/admin/account/notifications` | ✨ New |
| N/A | `/admin/account/security` | ✨ New |
| N/A | `/admin/account/api-keys` | ✨ New |
| N/A | `/admin/subscription/usage` | ✨ New |
| N/A | `/admin/subscription/billing` | ✨ New |
| N/A | `/admin/subscription/payment` | ✨ New |
| N/A | `/admin/org/team` | ✨ New (UserManagement) |
| N/A | `/admin/org/roles` | ✨ New |
| N/A | `/admin/org/settings` | ✨ New |
| N/A | `/admin/org/billing` | ✨ New |

---

## Component Changes

### New Components

#### NavigationSection.jsx
```javascript
import React, { useState } from 'react';
import { Collapse, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { ExpandLess, ExpandMore } from '@mui/icons-material';

const NavigationSection = ({ section, currentPath, userRole, orgRole }) => {
  const [open, setOpen] = useState(() => {
    // Load from localStorage or default to open
    return localStorage.getItem(`nav-section-${section.id}`) !== 'false';
  });

  const handleToggle = () => {
    const newState = !open;
    setOpen(newState);
    localStorage.setItem(`nav-section-${section.id}`, newState);
  };

  // Check role-based visibility
  if (section.roles && !section.roles.includes(userRole) && !section.roles.includes(orgRole)) {
    return null;
  }

  return (
    <>
      <ListItem button onClick={handleToggle}>
        <ListItemIcon>{section.icon}</ListItemIcon>
        <ListItemText primary={section.label} />
        {open ? <ExpandLess /> : <ExpandMore />}
      </ListItem>
      <Collapse in={open} timeout="auto" unmountOnExit>
        {section.submenu.map(item => (
          <NavigationItem key={item.path} item={item} currentPath={currentPath} />
        ))}
      </Collapse>
    </>
  );
};

export default NavigationSection;
```

#### NavigationItem.jsx
```javascript
import React from 'react';
import { ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Link } from 'react-router-dom';

const NavigationItem = ({ item, currentPath, nested = false }) => {
  const isActive = currentPath === item.path || currentPath.startsWith(item.path + '/');

  return (
    <ListItem
      button
      component={Link}
      to={item.path}
      selected={isActive}
      sx={{ pl: nested ? 4 : 2 }}
    >
      {item.icon && <ListItemIcon>{item.icon}</ListItemIcon>}
      <ListItemText primary={item.label} />
    </ListItem>
  );
};

export default NavigationItem;
```

### Modified Components

#### Layout.jsx Changes

**Before:**
```javascript
// Old flat navigation
const menuItems = [...];

return (
  <List>
    {menuItems.map(item => (
      <ListItem key={item.path} component={Link} to={item.path}>
        <ListItemIcon>{item.icon}</ListItemIcon>
        <ListItemText primary={item.label} />
      </ListItem>
    ))}
  </List>
);
```

**After:**
```javascript
// New hierarchical navigation
import NavigationSection from './NavigationSection';
import NavigationItem from './NavigationItem';

const navigationSections = [...]; // See above

return (
  <List>
    {navigationSections.map(section => (
      <React.Fragment key={section.id}>
        <ListSubheader>{section.label}</ListSubheader>
        {section.items.map(item =>
          item.submenu ? (
            <NavigationSection
              key={item.id}
              section={item}
              currentPath={location.pathname}
              userRole={userRole}
              orgRole={orgRole}
            />
          ) : (
            <NavigationItem
              key={item.path}
              item={item}
              currentPath={location.pathname}
            />
          )
        )}
      </React.Fragment>
    ))}
  </List>
);
```

---

## App.jsx Route Definitions

### Route Updates

```javascript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

// Old routes (with redirects)
<Route path="/admin/user-settings" element={<Navigate to="/admin/account/profile" replace />} />
<Route path="/admin/billing" element={<Navigate to="/admin/subscription/plan" replace />} />
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

// New routes - Personal Section
<Route path="/admin/" element={<DashboardPro />} />
<Route path="/admin/account/profile" element={<AccountProfile />} />
<Route path="/admin/account/notifications" element={<AccountNotifications />} />
<Route path="/admin/account/security" element={<AccountSecurity />} />
<Route path="/admin/account/api-keys" element={<AccountAPIKeys />} />

<Route path="/admin/subscription/plan" element={<SubscriptionPlan />} />
<Route path="/admin/subscription/usage" element={<SubscriptionUsage />} />
<Route path="/admin/subscription/billing" element={<SubscriptionBilling />} />
<Route path="/admin/subscription/payment" element={<SubscriptionPayment />} />

// New routes - Organization Section (role-protected)
<Route path="/admin/org/team" element={<ProtectedRoute roles={['owner', 'admin']}><UserManagement /></ProtectedRoute>} />
<Route path="/admin/org/roles" element={<ProtectedRoute roles={['owner', 'admin']}><OrganizationRoles /></ProtectedRoute>} />
<Route path="/admin/org/settings" element={<ProtectedRoute roles={['owner', 'admin']}><OrganizationSettings /></ProtectedRoute>} />
<Route path="/admin/org/billing" element={<ProtectedRoute roles={['owner']}><OrganizationBilling /></ProtectedRoute>} />

// New routes - System Section (admin-only)
<Route path="/admin/system/models" element={<ProtectedRoute roles={['admin']}><AIModelManagement /></ProtectedRoute>} />
<Route path="/admin/system/services" element={<ProtectedRoute roles={['admin']}><Services /></ProtectedRoute>} />
<Route path="/admin/system/resources" element={<ProtectedRoute roles={['admin']}><System /></ProtectedRoute>} />
<Route path="/admin/system/network" element={<ProtectedRoute roles={['admin']}><Network /></ProtectedRoute>} />
<Route path="/admin/system/storage" element={<ProtectedRoute roles={['admin']}><StorageBackup /></ProtectedRoute>} />
<Route path="/admin/system/security" element={<ProtectedRoute roles={['admin']}><Security /></ProtectedRoute>} />
<Route path="/admin/system/authentication" element={<ProtectedRoute roles={['admin']}><Authentication /></ProtectedRoute>} />
<Route path="/admin/system/extensions" element={<ProtectedRoute roles={['admin']}><Extensions /></ProtectedRoute>} />
<Route path="/admin/system/logs" element={<ProtectedRoute roles={['admin']}><Logs /></ProtectedRoute>} />
<Route path="/admin/system/landing" element={<ProtectedRoute roles={['admin']}><LandingCustomization /></ProtectedRoute>} />
<Route path="/admin/system/settings" element={<ProtectedRoute roles={['admin']}><SystemSettings /></ProtectedRoute>} />
```

### ProtectedRoute Component

```javascript
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children, roles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div>Loading...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // Check role or org_role
  const hasRole = roles.some(role =>
    user.role === role || user.org_role === role
  );

  if (!hasRole) {
    return <Navigate to="/admin/" replace />;
  }

  return children;
};

export default ProtectedRoute;
```

---

## Component Refactoring

### UserSettings.jsx Split

**Old Component:**
```javascript
// UserSettings.jsx (monolithic)
const UserSettings = () => {
  return (
    <div>
      {/* Profile section */}
      {/* Notification section */}
      {/* Security section */}
      {/* API Keys section */}
    </div>
  );
};
```

**New Components:**

**AccountProfile.jsx**
```javascript
import React from 'react';

const AccountProfile = () => {
  return (
    <div>
      <h1>Profile & Preferences</h1>
      {/* Personal information form */}
      {/* Avatar upload */}
      {/* Email, name, timezone */}
    </div>
  );
};

export default AccountProfile;
```

**AccountNotifications.jsx**
```javascript
const AccountNotifications = () => {
  return (
    <div>
      <h1>Notification Preferences</h1>
      {/* Email notifications */}
      {/* Push notifications */}
      {/* Alert frequency */}
    </div>
  );
};
```

**AccountSecurity.jsx**
```javascript
const AccountSecurity = () => {
  return (
    <div>
      <h1>Security & Sessions</h1>
      {/* Change password */}
      {/* Two-factor authentication */}
      {/* Active sessions */}
      {/* Login history */}
    </div>
  );
};
```

**AccountAPIKeys.jsx**
```javascript
const AccountAPIKeys = () => {
  return (
    <div>
      <h1>API Keys (BYOK)</h1>
      {/* OpenAI API key */}
      {/* Anthropic API key */}
      {/* HuggingFace token */}
      {/* Custom endpoints */}
    </div>
  );
};
```

### BillingDashboard.jsx Split

**Old Component:**
```javascript
// BillingDashboard.jsx (monolithic)
const BillingDashboard = () => {
  return (
    <div>
      {/* Current plan */}
      {/* Usage stats */}
      {/* Invoices */}
      {/* Payment methods */}
    </div>
  );
};
```

**New Components:**

**SubscriptionPlan.jsx**
```javascript
const SubscriptionPlan = () => {
  return (
    <div>
      <h1>Current Plan</h1>
      {/* Plan details */}
      {/* Features list */}
      {/* Upgrade/downgrade buttons */}
    </div>
  );
};
```

**SubscriptionUsage.jsx**
```javascript
const SubscriptionUsage = () => {
  return (
    <div>
      <h1>Usage & Limits</h1>
      {/* API usage chart */}
      {/* Current vs limit */}
      {/* Service breakdown */}
    </div>
  );
};
```

**SubscriptionBilling.jsx**
```javascript
const SubscriptionBilling = () => {
  return (
    <div>
      <h1>Billing History</h1>
      {/* Invoice list */}
      {/* Download invoices */}
      {/* Billing contact */}
    </div>
  );
};
```

**SubscriptionPayment.jsx**
```javascript
const SubscriptionPayment = () => {
  return (
    <div>
      <h1>Payment Methods</h1>
      {/* Credit cards */}
      {/* Add payment method */}
      {/* Set default */}
    </div>
  );
};
```

---

## API Changes

### New Endpoints

**No breaking API changes.** All existing endpoints remain functional.

**New endpoints added:**

```javascript
// User account endpoints
GET    /api/v1/account/profile           // Get user profile
PUT    /api/v1/account/profile           // Update profile
GET    /api/v1/account/notifications     // Get notification preferences
PUT    /api/v1/account/notifications     // Update notification preferences
GET    /api/v1/account/security          // Get security settings
PUT    /api/v1/account/security          // Update security settings
GET    /api/v1/account/api-keys          // List BYOK keys
POST   /api/v1/account/api-keys          // Add BYOK key
DELETE /api/v1/account/api-keys/:id      // Remove BYOK key

// Subscription endpoints
GET    /api/v1/subscription/plan         // Get current plan
GET    /api/v1/subscription/usage        // Get usage stats
GET    /api/v1/subscription/invoices     // Get invoices
GET    /api/v1/subscription/payment      // Get payment methods
POST   /api/v1/subscription/payment      // Add payment method
DELETE /api/v1/subscription/payment/:id  // Remove payment method

// Organization endpoints (org admin only)
GET    /api/v1/org/team                  // List team members
POST   /api/v1/org/team                  // Add team member
DELETE /api/v1/org/team/:id              // Remove team member
PUT    /api/v1/org/team/:id              // Update member role
GET    /api/v1/org/roles                 // List custom roles
POST   /api/v1/org/roles                 // Create role
GET    /api/v1/org/settings              // Get org settings
PUT    /api/v1/org/settings              // Update org settings
GET    /api/v1/org/billing               // Get org billing (owner only)
```

### Response Format (Unchanged)

All APIs continue to use the same response format:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

---

## Breaking Changes

### ⚠️ Breaking Changes (Minimal)

1. **Route URLs Changed**
   - Old URLs redirect automatically (backwards compatible)
   - **Action Required:** Update hardcoded links in custom apps
   - **Redirect Duration:** 4 weeks minimum

2. **UserSettings Component Split**
   - Old `UserSettings` component no longer exists
   - **Action Required:** Import new components instead:
     ```javascript
     // Old
     import UserSettings from './pages/UserSettings';

     // New
     import AccountProfile from './pages/account/AccountProfile';
     import AccountNotifications from './pages/account/AccountNotifications';
     import AccountSecurity from './pages/account/AccountSecurity';
     import AccountAPIKeys from './pages/account/AccountAPIKeys';
     ```

3. **BillingDashboard Component Split**
   - Old `BillingDashboard` component no longer exists
   - **Action Required:** Import new components instead:
     ```javascript
     // Old
     import BillingDashboard from './pages/BillingDashboard';

     // New
     import SubscriptionPlan from './pages/subscription/SubscriptionPlan';
     import SubscriptionUsage from './pages/subscription/SubscriptionUsage';
     import SubscriptionBilling from './pages/subscription/SubscriptionBilling';
     import SubscriptionPayment from './pages/subscription/SubscriptionPayment';
     ```

4. **Settings → SystemSettings Rename**
   - Old `Settings` component renamed to `SystemSettings`
   - **Action Required:** Update imports:
     ```javascript
     // Old
     import Settings from './pages/Settings';

     // New
     import SystemSettings from './pages/system/SystemSettings';
     ```

---

## Backwards Compatibility

### Route Redirects (4 weeks minimum)

All old routes redirect to new routes automatically:

```javascript
// Implemented in App.jsx
const redirects = {
  '/admin/user-settings': '/admin/account/profile',
  '/admin/billing': '/admin/subscription/plan',
  '/admin/models': '/admin/system/models',
  '/admin/services': '/admin/system/services',
  '/admin/system': '/admin/system/resources',
  '/admin/network': '/admin/system/network',
  '/admin/storage': '/admin/system/storage',
  '/admin/logs': '/admin/system/logs',
  '/admin/security': '/admin/system/security',
  '/admin/authentication': '/admin/system/authentication',
  '/admin/extensions': '/admin/system/extensions',
  '/admin/landing': '/admin/system/landing',
  '/admin/settings': '/admin/system/settings',
};
```

### API Compatibility (Permanent)

All existing APIs remain functional:

- ✅ No endpoint URLs changed
- ✅ No request formats changed
- ✅ No response formats changed
- ✅ No authentication changes

---

## Updating Custom Links

### Internal Links (React Router)

**Old Code:**
```javascript
import { Link } from 'react-router-dom';

<Link to="/admin/models">Manage Models</Link>
<Link to="/admin/billing">View Billing</Link>
```

**New Code:**
```javascript
<Link to="/admin/system/models">Manage Models</Link>
<Link to="/admin/subscription/plan">View Billing</Link>
```

### External Links (HTML/Email)

**Old Links:**
```html
<a href="https://your-domain.com/admin/models">Manage Models</a>
<a href="https://your-domain.com/admin/billing">View Billing</a>
```

**New Links:**
```html
<a href="https://your-domain.com/admin/system/models">Manage Models</a>
<a href="https://your-domain.com/admin/subscription/plan">View Billing</a>
```

### Programmatic Navigation

**Old Code:**
```javascript
import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();
navigate('/admin/models');
```

**New Code:**
```javascript
navigate('/admin/system/models');
```

---

## Testing Checklist

### Unit Tests

- [ ] Test NavigationSection collapse/expand state
- [ ] Test NavigationItem active state detection
- [ ] Test role-based visibility logic
- [ ] Test localStorage persistence

### Integration Tests

- [ ] Test all route redirects
- [ ] Test ProtectedRoute with various roles
- [ ] Test navigation between all pages
- [ ] Test mobile navigation toggle

### E2E Tests

- [ ] Test user journey: Login → Dashboard → My Account → Profile
- [ ] Test org admin journey: Login → Organization → Team Members
- [ ] Test system admin journey: Login → System → AI Models
- [ ] Test role-based visibility (viewer, user, power_user, admin, owner)

### Accessibility Tests

- [ ] Keyboard navigation (Tab, Enter, Escape)
- [ ] Screen reader compatibility
- [ ] Focus management
- [ ] ARIA labels

---

## Migration Script

### Automated Link Update Script

```bash
#!/bin/bash
# update-navigation-links.sh
# Updates all hardcoded navigation links to new structure

echo "Updating navigation links in codebase..."

# Define replacements
declare -A replacements=(
  ["/admin/user-settings"]="/admin/account/profile"
  ["/admin/billing"]="/admin/subscription/plan"
  ["/admin/models"]="/admin/system/models"
  ["/admin/services"]="/admin/system/services"
  ["/admin/system"]="/admin/system/resources"
  ["/admin/network"]="/admin/system/network"
  ["/admin/storage"]="/admin/system/storage"
  ["/admin/logs"]="/admin/system/logs"
  ["/admin/security"]="/admin/system/security"
  ["/admin/authentication"]="/admin/system/authentication"
  ["/admin/extensions"]="/admin/system/extensions"
  ["/admin/landing"]="/admin/system/landing"
  ["/admin/settings"]="/admin/system/settings"
)

# Update files
for old in "${!replacements[@]}"; do
  new="${replacements[$old]}"
  echo "Replacing '$old' with '$new'..."

  # Update JSX/JS files
  find src -type f \( -name "*.jsx" -o -name "*.js" \) -exec sed -i "s|$old|$new|g" {} +

  # Update HTML files
  find public -type f -name "*.html" -exec sed -i "s|$old|$new|g" {} +

  # Update test files
  find tests -type f \( -name "*.test.js" -o -name "*.spec.js" \) -exec sed -i "s|$old|$new|g" {} +
done

echo "✅ Link update complete!"
echo "🔍 Review changes with: git diff"
```

### Usage

```bash
chmod +x update-navigation-links.sh
./update-navigation-links.sh
git diff  # Review changes
git add -A
git commit -m "chore: Update navigation links to new structure"
```

---

## Troubleshooting

### Issue: Navigation not rendering

**Cause:** Missing role or org_role in user object

**Solution:**
```javascript
// Ensure AuthContext provides role and org_role
const user = {
  id: '123',
  email: 'user@example.com',
  role: 'user',           // Platform role: viewer, user, power_user, admin
  org_role: 'admin',      // Organization role: member, admin, owner
  org_id: 'org-abc-123',
  org_name: 'My Organization'
};
```

---

### Issue: Submenu not expanding

**Cause:** localStorage key collision or state management

**Solution:**
```javascript
// Clear navigation state
localStorage.removeItem('nav-section-account');
localStorage.removeItem('nav-section-subscription');
localStorage.removeItem('nav-section-org');
localStorage.removeItem('nav-section-system');

// Or clear all
localStorage.clear();
```

---

### Issue: Active route not highlighted

**Cause:** Route matching logic not detecting nested routes

**Solution:**
```javascript
// Use startsWith() for nested route detection
const isActive =
  currentPath === item.path ||
  currentPath.startsWith(item.path + '/');
```

---

### Issue: Redirect loop

**Cause:** Circular redirects or missing base route

**Solution:**
```javascript
// Ensure Dashboard route exists
<Route path="/admin/" element={<DashboardPro />} />

// Don't redirect Dashboard
// ❌ Bad
<Route path="/admin/" element={<Navigate to="/admin/dashboard" />} />
<Route path="/admin/dashboard" element={<Navigate to="/admin/" />} />
```

---

## Performance Considerations

### Lazy Loading

Implement code splitting for better performance:

```javascript
import React, { lazy, Suspense } from 'react';

// Lazy load page components
const AccountProfile = lazy(() => import('./pages/account/AccountProfile'));
const SubscriptionPlan = lazy(() => import('./pages/subscription/SubscriptionPlan'));
const UserManagement = lazy(() => import('./pages/org/UserManagement'));

// Wrap routes in Suspense
<Suspense fallback={<div>Loading...</div>}>
  <Route path="/admin/account/profile" element={<AccountProfile />} />
  <Route path="/admin/subscription/plan" element={<SubscriptionPlan />} />
  <Route path="/admin/org/team" element={<UserManagement />} />
</Suspense>
```

### Memoization

Optimize navigation rendering:

```javascript
import React, { memo, useMemo } from 'react';

const NavigationSection = memo(({ section, currentPath, userRole, orgRole }) => {
  const isVisible = useMemo(() => {
    if (!section.roles) return true;
    return section.roles.includes(userRole) || section.roles.includes(orgRole);
  }, [section.roles, userRole, orgRole]);

  if (!isVisible) return null;

  // ... rest of component
});
```

---

## Support & Resources

### Documentation
- User Guide: `/docs/NAVIGATION-MIGRATION-GUIDE.md`
- Release Notes: `/docs/RELEASE-NOTES-NAV-UPDATE.md`
- API Documentation: `/docs/ADMIN_API.md`

### Contact
- Email: dev@magicunicorn.tech
- GitHub Issues: https://github.com/Unicorn-Commander/UC-1-Pro/issues
- Slack: #ops-center-dev

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Oct 13, 2025 | Initial developer migration guide |

---

**Document Maintained By:** Magic Unicorn Unconventional Technology & Stuff Inc
**Last Updated:** October 13, 2025
**Questions?** dev@magicunicorn.tech
