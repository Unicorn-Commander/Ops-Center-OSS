# Role-Based App Access System - Architecture Design Document

**Project**: UC-1 Pro Operations Center
**Component**: Landing Page Service Access Control
**Version**: 1.0
**Author**: System Architecture Designer
**Date**: October 9, 2025

---

## 1. Executive Summary

This document provides a comprehensive architectural design for implementing role-based access control (RBAC) for application visibility and access on the UC-1 Pro landing page. The system will filter which applications users can see and access based on their assigned role (admin, power_user, user, viewer) while maintaining extensibility for future applications and services.

### Key Design Goals

1. **Security First**: Users only see apps they have permission to access
2. **Extensibility**: Easy to add new apps without code changes
3. **Performance**: Minimal overhead for role checking
4. **Maintainability**: Configuration-driven, not hardcoded
5. **User Experience**: Clear indication of access levels

---

## 2. Current State Analysis

### 2.1 Existing Landing Page Implementation

**File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/src/pages/PublicLanding.jsx`

**Current State**:
- **Subscription Tier System**: Currently uses a `serviceTiers` object (lines 48-56) that maps services to subscription tiers (trial, starter, professional, enterprise)
- **Tier-Based Access**: The `hasAccess()` function (lines 162-167) checks if user's subscription tier allows access to a service
- **Service Array**: Hardcoded services array (lines 179-238) with 7 services including Open-WebUI, Center-Deep, Bolt.diy, etc.
- **Session Fetching**: Fetches user session from `/api/v1/auth/session` (lines 71-110)
- **Lock Overlay**: Services show lock icon if user lacks required tier (lines 612-622)
- **Admin Section**: Separate admin dashboard link (lines 656-684)

**Key Findings**:
1. The system already has **TWO access control mechanisms**:
   - Role-based (admin, power_user, user, viewer) - from authentication
   - Tier-based (trial, starter, professional, enterprise) - for subscription
2. The landing page currently uses **tier-based** access, not role-based
3. The backend has comprehensive role mapping (`role_mapper.py`)
4. The session API returns both `role` and `subscription_tier`

### 2.2 Backend Infrastructure

**Role System** (`role_mapper.py`):
- 4-tier hierarchy: admin > power_user > user > viewer
- Maps Authentik/Keycloak groups to roles
- Special handling for admin users (akadmin, admin@example.com)
- Default fallback to 'viewer' role

**Service Access System** (`service_access.py`):
- Manages subscription tier access (trial, byok, professional, enterprise)
- SERVICE_ACCESS_MATRIX defines which tiers can access which services
- PROTECTED_SERVICES defines service URLs and minimum tier requirements

**Authentication** (`auth_manager.py`):
- JWT-based authentication
- Session management
- Role stored in user object (line 26: `role: str = "user"`)

### 2.3 Configuration System

**Landing Config** (`backend/config/landing_config.json`):
- Defines available services with metadata
- Uses "auto" URL resolution with port numbers
- Has `enabled` flag for each service
- Includes `apiOnly` flag for backend-only services

---

## 3. System Architecture Design

### 3.1 Architectural Approach

**Recommendation: Hybrid Configuration-Based System**

The design uses a **centralized configuration file** with **backend API support** for the following reasons:

**Why Configuration File?**
1. No database required for simple role-to-app mappings
2. Easy to version control and backup
3. Fast to read (loaded once at startup)
4. Simple to edit for administrators
5. Supports both role-based and tier-based access

**Why Backend API?**
1. Centralized access control logic
2. Consistent enforcement across frontend and backend
3. Audit trail for access checks
4. Dynamic updates without frontend rebuild
5. Future support for admin UI management

### 3.2 Data Model Design

#### 3.2.1 Application Definition Schema

```json
{
  "id": "string (unique identifier)",
  "name": "string (display name)",
  "description": "string (user-facing description)",
  "icon": "string (Heroicon name or emoji)",
  "iconImage": "string (optional: custom image path)",
  "color": "string (gradient classes: from-X to-Y)",
  "textColor": "string (text color classes)",
  "url": "string (service URL or 'auto')",
  "port": "number (for auto URL generation)",
  "enabled": "boolean (service availability)",
  "order": "number (display order)",

  "access": {
    "roles": ["array of role strings"],
    "tiers": ["array of tier strings"],
    "mode": "string (any_role, all_roles, any_tier, all_tiers, role_and_tier)"
  },

  "visibility": {
    "showWhenLocked": "boolean (show locked card or hide completely)",
    "upgradePrompt": "boolean (show upgrade message)",
    "requiredFor": "string (message: 'Available for {roles}' or 'Upgrade to {tier}')"
  },

  "metadata": {
    "category": "string (ai-tools, admin, monitoring, etc.)",
    "tags": ["array of strings"],
    "apiOnly": "boolean (backend service only)",
    "subdomain": "string (optional: for subdomain routing)",
    "path": "string (optional: URL path)"
  }
}
```

#### 3.2.2 Example Configuration

```json
{
  "version": "1.0",
  "apps": [
    {
      "id": "open-webui",
      "name": "Open-WebUI Chat",
      "description": "Advanced AI chat interface powered by state-of-the-art language models",
      "icon": "ChatBubbleLeftRightIcon",
      "color": "from-blue-500 to-blue-700",
      "textColor": "text-blue-100",
      "url": "auto",
      "port": 8080,
      "enabled": true,
      "order": 1,
      "access": {
        "roles": ["admin", "power_user", "user", "viewer"],
        "tiers": ["trial", "byok", "professional", "enterprise"],
        "mode": "any_role"
      },
      "visibility": {
        "showWhenLocked": true,
        "upgradePrompt": true,
        "requiredFor": "Available to all users"
      },
      "metadata": {
        "category": "ai-tools",
        "tags": ["chat", "ai", "llm"]
      }
    },
    {
      "id": "bolt-diy",
      "name": "Bolt.diy",
      "description": "AI-powered development environment for rapid prototyping",
      "icon": "CodeBracketIcon",
      "color": "from-purple-500 to-purple-700",
      "textColor": "text-purple-100",
      "url": "auto",
      "port": 5173,
      "enabled": true,
      "order": 3,
      "access": {
        "roles": ["admin", "power_user", "user"],
        "tiers": ["professional", "enterprise"],
        "mode": "role_and_tier"
      },
      "visibility": {
        "showWhenLocked": true,
        "upgradePrompt": true,
        "requiredFor": "Professional tier + User role required"
      },
      "metadata": {
        "category": "development",
        "tags": ["code", "ai", "development"]
      }
    },
    {
      "id": "admin-dashboard",
      "name": "Admin Dashboard",
      "description": "Full system management, configuration, and monitoring",
      "icon": "CpuChipIcon",
      "color": "from-red-500 to-red-700",
      "textColor": "text-red-100",
      "url": "/admin",
      "enabled": true,
      "order": 100,
      "access": {
        "roles": ["admin"],
        "mode": "any_role"
      },
      "visibility": {
        "showWhenLocked": false,
        "upgradePrompt": false,
        "requiredFor": "Administrators only"
      },
      "metadata": {
        "category": "admin",
        "tags": ["admin", "system", "management"],
        "apiOnly": false
      }
    },
    {
      "id": "presenton",
      "name": "Presenton",
      "description": "AI-powered presentation creation and editing",
      "icon": "DocumentTextIcon",
      "color": "from-green-500 to-green-700",
      "textColor": "text-green-100",
      "url": "auto",
      "port": 8091,
      "enabled": true,
      "order": 4,
      "access": {
        "roles": ["admin", "power_user", "user", "viewer"],
        "tiers": ["trial", "byok", "professional", "enterprise"],
        "mode": "any_role"
      },
      "visibility": {
        "showWhenLocked": true,
        "upgradePrompt": false,
        "requiredFor": "Available to all users"
      },
      "metadata": {
        "category": "productivity",
        "tags": ["presentations", "ai"]
      }
    }
  ],

  "accessModes": {
    "any_role": "User has ANY of the specified roles",
    "all_roles": "User has ALL of the specified roles",
    "any_tier": "User has ANY of the specified tiers",
    "all_tiers": "User has ALL of the specified tiers",
    "role_and_tier": "User has required role AND tier"
  },

  "roleHierarchy": ["admin", "power_user", "user", "viewer"],
  "tierHierarchy": ["trial", "byok", "professional", "enterprise"]
}
```

### 3.3 Backend API Design

#### 3.3.1 New API Endpoint: `/api/v1/apps`

**Purpose**: Return applications available to the authenticated user

**Method**: GET

**Authentication**: Required (JWT token)

**Request Headers**:
```
Authorization: Bearer <jwt_token>
```

**Response Schema**:
```json
{
  "apps": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "icon": "string",
      "iconImage": "string",
      "color": "string",
      "textColor": "string",
      "url": "string",
      "enabled": "boolean",
      "order": "number",
      "access": {
        "allowed": "boolean",
        "reason": "string"
      },
      "visibility": {
        "showWhenLocked": "boolean",
        "upgradePrompt": "boolean",
        "requiredFor": "string"
      },
      "metadata": {
        "category": "string",
        "tags": ["array"]
      }
    }
  ],
  "user": {
    "role": "string",
    "tier": "string",
    "username": "string"
  },
  "statistics": {
    "total_apps": "number",
    "available_apps": "number",
    "locked_apps": "number"
  }
}
```

**Response Examples**:

**Admin User**:
```json
{
  "apps": [
    {
      "id": "open-webui",
      "name": "Open-WebUI Chat",
      "url": "http://localhost:8080",
      "access": {
        "allowed": true,
        "reason": "Available to admin role"
      }
    },
    {
      "id": "admin-dashboard",
      "name": "Admin Dashboard",
      "url": "/admin",
      "access": {
        "allowed": true,
        "reason": "Admin access granted"
      }
    }
  ],
  "user": {
    "role": "admin",
    "tier": "enterprise",
    "username": "aaron"
  },
  "statistics": {
    "total_apps": 10,
    "available_apps": 10,
    "locked_apps": 0
  }
}
```

**Viewer User**:
```json
{
  "apps": [
    {
      "id": "open-webui",
      "name": "Open-WebUI Chat",
      "url": "http://localhost:8080",
      "access": {
        "allowed": true,
        "reason": "Available to all users"
      }
    },
    {
      "id": "bolt-diy",
      "name": "Bolt.diy",
      "url": "http://localhost:5173",
      "access": {
        "allowed": false,
        "reason": "Requires professional tier + user role"
      },
      "visibility": {
        "showWhenLocked": true,
        "upgradePrompt": true,
        "requiredFor": "Professional tier + User role required"
      }
    }
  ],
  "user": {
    "role": "viewer",
    "tier": "trial",
    "username": "guest"
  },
  "statistics": {
    "total_apps": 10,
    "available_apps": 3,
    "locked_apps": 7
  }
}
```

#### 3.3.2 Access Control Logic

**Algorithm**:
```python
def check_app_access(user_role, user_tier, app_config):
    """
    Check if user has access to an app based on role and tier

    Args:
        user_role: User's role (admin, power_user, user, viewer)
        user_tier: User's subscription tier (trial, byok, professional, enterprise)
        app_config: App configuration from JSON

    Returns:
        {
            "allowed": bool,
            "reason": str,
            "upgrade_path": str (optional)
        }
    """
    access_config = app_config.get("access", {})
    mode = access_config.get("mode", "any_role")
    required_roles = access_config.get("roles", [])
    required_tiers = access_config.get("tiers", [])

    # Check if app is enabled
    if not app_config.get("enabled", True):
        return {
            "allowed": False,
            "reason": "Service temporarily unavailable"
        }

    # Mode: any_role
    if mode == "any_role":
        if user_role in required_roles:
            return {
                "allowed": True,
                "reason": f"Available to {user_role} role"
            }
        else:
            return {
                "allowed": False,
                "reason": f"Requires one of: {', '.join(required_roles)}",
                "upgrade_path": "role"
            }

    # Mode: any_tier
    elif mode == "any_tier":
        if user_tier in required_tiers:
            return {
                "allowed": True,
                "reason": f"Available to {user_tier} tier"
            }
        else:
            return {
                "allowed": False,
                "reason": f"Requires one of: {', '.join(required_tiers)}",
                "upgrade_path": "tier"
            }

    # Mode: role_and_tier
    elif mode == "role_and_tier":
        role_ok = user_role in required_roles
        tier_ok = user_tier in required_tiers

        if role_ok and tier_ok:
            return {
                "allowed": True,
                "reason": f"Access granted: {user_role} + {user_tier}"
            }
        elif not role_ok and not tier_ok:
            return {
                "allowed": False,
                "reason": f"Requires role ({', '.join(required_roles)}) AND tier ({', '.join(required_tiers)})",
                "upgrade_path": "both"
            }
        elif not role_ok:
            return {
                "allowed": False,
                "reason": f"Requires role: {', '.join(required_roles)}",
                "upgrade_path": "role"
            }
        else:
            return {
                "allowed": False,
                "reason": f"Requires tier: {', '.join(required_tiers)}",
                "upgrade_path": "tier"
            }

    # Default: deny access
    return {
        "allowed": False,
        "reason": "Access mode not configured"
    }
```

### 3.4 Frontend Implementation Design

#### 3.4.1 React Component Structure

**Approach**: Refactor PublicLanding.jsx to use API-driven app list

**Key Changes**:
1. Replace hardcoded `services` array with API call to `/api/v1/apps`
2. Remove client-side access logic (move to backend)
3. Render apps based on backend response
4. Add loading state for API call
5. Handle errors gracefully

**Component Flow**:
```
PublicLanding Component Mount
    ↓
Fetch /api/v1/auth/session (existing)
    ↓
Fetch /api/v1/apps (new)
    ↓
Render App Cards:
    - Available apps: Full interaction
    - Locked apps: Show with lock overlay (if showWhenLocked = true)
    - Hidden apps: Don't render at all (if showWhenLocked = false)
```

#### 3.4.2 State Management

```jsx
// New state for apps
const [apps, setApps] = useState([]);
const [appsLoading, setAppsLoading] = useState(true);
const [appsError, setAppsError] = useState(null);

// Fetch apps
useEffect(() => {
  const fetchApps = async () => {
    try {
      setAppsLoading(true);
      const response = await fetch('/api/v1/apps', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setApps(data.apps);
      } else {
        throw new Error('Failed to fetch apps');
      }
    } catch (error) {
      console.error('Error fetching apps:', error);
      setAppsError(error.message);
      // Fallback to default apps or show error
    } finally {
      setAppsLoading(false);
    }
  };

  fetchApps();
}, []);
```

#### 3.4.3 App Card Rendering

```jsx
// Render apps
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
  {appsLoading ? (
    <LoadingSpinner />
  ) : appsError ? (
    <ErrorMessage message={appsError} />
  ) : (
    apps
      .filter(app =>
        // Show if allowed OR if locked but should be shown
        app.access.allowed || app.visibility.showWhenLocked
      )
      .sort((a, b) => a.order - b.order)
      .map((app, index) => (
        <AppCard
          key={app.id}
          app={app}
          index={index}
          currentHost={currentHost}
          currentTheme={currentTheme}
        />
      ))
  )}
</div>
```

#### 3.4.4 App Card Component

```jsx
function AppCard({ app, index, currentHost, currentTheme }) {
  const isLocked = !app.access.allowed;

  const handleClick = (e) => {
    if (isLocked) {
      e.preventDefault();

      if (app.visibility.upgradePrompt) {
        // Show modal or toast with upgrade information
        showUpgradeModal({
          appName: app.name,
          requiredFor: app.visibility.requiredFor,
          reason: app.access.reason
        });
      }
    }
  };

  // Resolve URL (handle 'auto' URLs)
  const resolvedUrl = app.url === 'auto'
    ? `http://${currentHost}:${app.port}`
    : app.url;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 * index }}
    >
      <a
        href={resolvedUrl}
        target={app.url.startsWith('http') ? '_blank' : '_self'}
        rel="noopener noreferrer"
        className={`block group ${isLocked ? 'cursor-not-allowed' : ''}`}
        onClick={handleClick}
        title={isLocked ? app.access.reason : app.description}
      >
        <div className={`bg-gradient-to-br ${app.color} rounded-2xl shadow-xl transition-all duration-300 border border-white/10 backdrop-blur-sm overflow-hidden relative ${
          isLocked
            ? 'opacity-60 hover:opacity-70'
            : 'hover:shadow-2xl transform hover:scale-105'
        }`}>
          {/* Lock Overlay */}
          {isLocked && (
            <div className="absolute inset-0 bg-black/40 backdrop-blur-[2px] z-10 flex items-center justify-center">
              <div className="text-center">
                <LockClosedIcon className="h-12 w-12 text-white/90 mx-auto mb-2" />
                <div className="text-white font-semibold text-sm px-4">
                  <div>{app.visibility.requiredFor}</div>
                  {app.visibility.upgradePrompt && (
                    <div className="text-xs mt-1 opacity-90">
                      Click for details
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          <div className="p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="flex-shrink-0">
                {app.iconImage ? (
                  <img src={app.iconImage} alt={app.name} className="h-16 w-16 object-contain rounded-lg bg-white/10 p-2" />
                ) : (
                  <div className="h-16 w-16 rounded-lg bg-white/10 flex items-center justify-center">
                    <DynamicIcon name={app.icon} className="h-10 w-10 text-white" />
                  </div>
                )}
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                  {app.name}
                  {!isLocked && (
                    <ArrowRightIcon className="h-4 w-4 text-white/70 group-hover:text-white group-hover:translate-x-1 transition-all duration-200" />
                  )}
                </h3>
                <p className={`${app.textColor} text-sm mt-1 leading-relaxed`}>
                  {app.description}
                </p>
              </div>
            </div>
          </div>
        </div>
      </a>
    </motion.div>
  );
}
```

### 3.5 Configuration File Location

**Recommendation**: Extend existing configuration

**File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/config/apps_access.json`

**Why New File?**
1. Separates app access configuration from landing page styling
2. Can be used by other components (admin panel, billing page)
3. Easier to manage access control independently
4. Supports future admin UI for access management

**Alternative**: Extend `landing_config.json` with access control fields

---

## 4. Implementation Plan

### Phase 1: Backend Foundation (Priority: High)

**Step 1.1: Create App Access Configuration**
- File: `backend/config/apps_access.json`
- Define initial app configurations with role/tier access
- Include all current services from landing page
- Add admin dashboard as admin-only app

**Step 1.2: Create App Access Manager**
- File: `backend/app_access_manager.py`
- Implement `AppAccessManager` class
- Methods:
  - `load_apps_config()` - Load JSON configuration
  - `get_user_apps(user_role, user_tier)` - Get filtered apps
  - `check_app_access(user_role, user_tier, app_id)` - Check single app
  - `resolve_app_url(app_config, hostname)` - Handle 'auto' URLs

**Step 1.3: Create API Endpoint**
- File: `backend/server.py`
- Add `GET /api/v1/apps` endpoint
- Integrate with existing authentication
- Use `AppAccessManager` to filter apps
- Return formatted JSON response

**Step 1.4: Update Session Endpoint**
- Ensure `/api/v1/auth/session` returns both `role` and `subscription_tier`
- Add `tier` field if missing

### Phase 2: Frontend Integration (Priority: High)

**Step 2.1: Refactor PublicLanding.jsx**
- Remove hardcoded `services` array
- Remove client-side `hasAccess()` function
- Remove `serviceTiers` mapping
- Add state for apps from API

**Step 2.2: Add API Integration**
- Create `fetchApps()` function
- Add loading and error states
- Handle API failures gracefully

**Step 2.3: Update Rendering Logic**
- Filter apps based on `showWhenLocked` visibility
- Sort by `order` field
- Pass app data to card component

**Step 2.4: Create AppCard Component**
- Extract app card to separate component
- Handle locked state rendering
- Implement upgrade modal/toast

### Phase 3: Admin Dashboard Link (Priority: High)

**Step 3.1: Add Admin Dashboard to Apps Config**
- Define admin dashboard as an app with `roles: ["admin"]`
- Set `showWhenLocked: false` to hide from non-admins
- Use internal route `/admin`

**Step 3.2: Update User Dropdown**
- Keep "Admin Dashboard" link in dropdown for admins
- Filter based on user role

**Step 3.3: Remove Separate Admin Section**
- Remove hardcoded admin section (lines 656-684)
- Admin dashboard now appears as an app card (for admins only)

### Phase 4: Testing & Validation (Priority: High)

**Step 4.1: Backend Testing**
- Test `/api/v1/apps` endpoint with different roles
- Verify access control logic for each mode
- Test URL resolution (auto vs static)
- Test with role combinations

**Step 4.2: Frontend Testing**
- Test with admin user (should see all apps)
- Test with power_user (should see most apps)
- Test with user (should see standard apps)
- Test with viewer (should see limited apps)

**Step 4.3: Integration Testing**
- Test login flow with different users
- Verify apps update after login
- Test locked app interaction
- Test upgrade prompts

### Phase 5: Documentation & Rollout (Priority: Medium)

**Step 5.1: Documentation**
- Update ROLE_MAPPING.md with app access information
- Create APPS_ACCESS_CONFIGURATION.md guide
- Document API endpoint in API_QUICK_REFERENCE.md

**Step 5.2: Admin Guide**
- How to add new apps
- How to modify access rules
- How to test access changes

**Step 5.3: Rollout**
- Deploy to staging
- Test with real users
- Collect feedback
- Deploy to production

---

## 5. Access Control Matrix

### 5.1 Recommended App Access Configuration

| Application | Admin | Power User | User | Viewer | Tier Requirement |
|-------------|-------|------------|------|--------|------------------|
| Open-WebUI | Yes | Yes | Yes | Yes | Trial+ |
| Center Deep | Yes | Yes | Yes | Yes | Trial+ |
| Presenton | Yes | Yes | Yes | Yes | Trial+ |
| Bolt.diy | Yes | Yes | Yes | No | Professional+ |
| User Documentation | Yes | Yes | Yes | Yes | Trial+ |
| Grafana Monitoring | Yes | Yes | No | No | Professional+ |
| Portainer | Yes | Yes | No | No | Professional+ |
| Unicorn Orator | Yes | Yes | Yes | No | Enterprise+ |
| Admin Dashboard | Yes | No | No | No | Any tier |

### 5.2 Rationale

**Open-WebUI, Center Deep, Presenton**:
- Core functionality for all users
- Available to all roles
- Trial tier sufficient

**Bolt.diy**:
- Development tool requiring basic technical knowledge
- Excluded from viewer (read-only) role
- Professional tier (advanced users)

**Grafana Monitoring, Portainer**:
- System management tools
- Requires user or power_user role (not viewer)
- Professional tier (system administrators)

**Unicorn Orator**:
- Premium TTS service
- Requires user+ role (not viewer)
- Enterprise tier (high resource usage)

**Admin Dashboard**:
- System administration
- Admin role only
- Any tier (role-based, not tier-based)

---

## 6. Security Considerations

### 6.1 Access Control Enforcement

**Defense in Depth**:
1. **Frontend Filtering**: Hide apps user cannot access (UX)
2. **Backend Validation**: Verify access on every API call (Security)
3. **Service-Level Auth**: Services authenticate via SSO (Deep Security)

**Attack Scenarios**:

**Scenario 1**: User modifies API response to show admin dashboard
- **Mitigation**: Backend validates role before serving `/admin` routes
- **Protection**: Admin routes require role check via middleware

**Scenario 2**: User directly accesses service URL
- **Mitigation**: Services use Authentik SSO for authentication
- **Protection**: Service redirects to auth.unicorncommander.ai

**Scenario 3**: User guesses internal service ports
- **Mitigation**: Traefik reverse proxy enforces authentication
- **Protection**: Internal ports not exposed externally

### 6.2 Role Escalation Prevention

**Principle**: Never trust client-provided role information

**Implementation**:
1. Role stored server-side in session (not in client cookies)
2. Role extracted from Authentik JWT token (signed, cannot be forged)
3. Role re-validated on every sensitive operation
4. Role changes require new authentication (logout/login)

### 6.3 Audit Trail

**Requirements**:
1. Log all app access attempts (success and failure)
2. Log role-based access denials
3. Track which users access which apps
4. Alert on suspicious access patterns

**Implementation**:
- Use existing audit_logger.py
- Add app access events to audit log
- Create audit dashboard for admins

---

## 7. Extensibility & Future Enhancements

### 7.1 Admin UI for App Management

**Feature**: Web UI to manage app configurations

**Location**: `/admin/apps`

**Capabilities**:
- Add new apps via form
- Edit app metadata (name, description, icon)
- Configure access rules (roles, tiers)
- Enable/disable apps
- Reorder apps
- Test access for specific users

**Implementation**:
- React admin page
- API endpoints: POST /api/v1/apps, PUT /api/v1/apps/{id}, DELETE /api/v1/apps/{id}
- Real-time preview of changes

### 7.2 Dynamic Service Discovery

**Feature**: Automatically discover running Docker services

**Approach**:
- Scan Docker labels for UC-1 Pro apps
- Auto-register services in app configuration
- Health check integration
- Auto-hide unhealthy services

**Docker Labels**:
```yaml
labels:
  - "uc1.app.enabled=true"
  - "uc1.app.name=My Service"
  - "uc1.app.category=custom"
  - "uc1.app.roles=admin,power_user"
  - "uc1.app.port=8080"
```

### 7.3 App Categories & Filtering

**Feature**: Group apps by category

**Categories**:
- AI Tools (chat, search, generation)
- Development (Bolt.diy, code tools)
- Monitoring (Grafana, logs)
- Administration (admin dashboard, Portainer)
- Productivity (Presenton, docs)

**UI Enhancement**:
- Tab-based navigation
- Filter by category
- Search apps by name/description

### 7.4 App Usage Analytics

**Feature**: Track app usage per user

**Metrics**:
- Most accessed apps
- User engagement per app
- Access denial patterns (which apps are locked most)
- User journey (which apps are used together)

**Use Cases**:
- Optimize app placement
- Identify popular features
- Guide subscription tier design
- Improve user experience

### 7.5 Time-Based Access

**Feature**: Grant temporary access to apps

**Use Cases**:
- Trial periods for premium apps
- Temporary admin access
- Time-limited feature unlocks
- Scheduled maintenance windows

**Configuration**:
```json
{
  "access": {
    "roles": ["user"],
    "schedule": {
      "start": "2025-01-01T00:00:00Z",
      "end": "2025-01-31T23:59:59Z"
    }
  }
}
```

### 7.6 Conditional Access

**Feature**: Advanced access rules based on conditions

**Conditions**:
- IP address/network
- Time of day
- Device type
- MFA status
- Custom attributes

**Example**:
```json
{
  "access": {
    "roles": ["admin"],
    "conditions": {
      "require_mfa": true,
      "allowed_networks": ["10.0.0.0/8"],
      "blocked_countries": ["XX"]
    }
  }
}
```

---

## 8. Migration Strategy

### 8.1 Backward Compatibility

**Goal**: Ensure existing functionality continues to work during migration

**Approach**:
1. **Phase 1**: Add new API alongside existing code
2. **Phase 2**: Frontend consumes both (fallback to hardcoded)
3. **Phase 3**: Remove hardcoded services after validation
4. **Phase 4**: Clean up old code

### 8.2 Configuration Migration

**Existing**: Hardcoded services in PublicLanding.jsx

**New**: JSON configuration in backend

**Migration Script**:
```bash
#!/bin/bash
# Extract services from PublicLanding.jsx
# Generate apps_access.json
# Validate configuration
# Backup original file
```

### 8.3 User Communication

**Changes**:
- No visible changes for existing users
- Same apps appear in same order
- Admin users may see additional apps
- Viewer users may see fewer apps

**Communication**:
- Changelog entry: "Enhanced role-based access control"
- Admin notification: "App access now configurable via config file"
- User documentation update

---

## 9. Performance Considerations

### 9.1 Caching Strategy

**Problem**: Loading apps on every page load could be slow

**Solution**: Multi-level caching

**Level 1: Backend Config Cache**
- Load JSON file once at startup
- Reload on file modification (file watcher)
- Keep in memory for fast access

**Level 2: API Response Cache**
- Cache filtered apps per role/tier combination
- TTL: 5 minutes
- Invalidate on config change

**Level 3: Frontend Cache**
- Cache API response in session storage
- Reuse on page refresh
- Invalidate on logout

**Implementation**:
```python
from functools import lru_cache
from datetime import datetime, timedelta

class AppAccessManager:
    def __init__(self):
        self.config_loaded = None
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)

    @lru_cache(maxsize=128)
    def get_user_apps(self, user_role, user_tier):
        cache_key = f"{user_role}:{user_tier}"

        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_data

        # Compute and cache
        apps = self._compute_user_apps(user_role, user_tier)
        self.cache[cache_key] = (apps, datetime.now())
        return apps
```

### 9.2 Load Time Optimization

**Metrics**:
- Target: < 500ms for /api/v1/apps
- Current: N/A (new endpoint)

**Optimizations**:
1. Load JSON config at startup (not per request)
2. Pre-compute access matrix
3. Use efficient data structures (dict lookups)
4. Minimize JSON serialization overhead

### 9.3 Scalability

**Considerations**:
- 100+ apps in configuration
- 1000+ concurrent users
- 10,000+ requests/minute

**Architecture**:
- Stateless API (can scale horizontally)
- Configuration loaded from file (no DB bottleneck)
- Caching reduces computation
- CDN for static assets (app icons)

---

## 10. Code Examples

### 10.1 Backend: App Access Manager

**File**: `backend/app_access_manager.py`

```python
"""
App Access Manager for UC-1 Pro
Manages role-based and tier-based access to applications
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from functools import lru_cache
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AppAccessManager:
    """Manages application access control based on user roles and tiers"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config" / "apps_access.json"

        self.config_path = Path(config_path)
        self.config = None
        self.role_hierarchy = ["admin", "power_user", "user", "viewer"]
        self.tier_hierarchy = ["trial", "byok", "professional", "enterprise"]
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)

        self.load_config()

    def load_config(self):
        """Load app access configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)

            # Validate configuration
            if "apps" not in self.config:
                raise ValueError("Configuration missing 'apps' key")

            logger.info(f"Loaded {len(self.config['apps'])} apps from configuration")

            # Clear cache on config reload
            self.cache.clear()

        except Exception as e:
            logger.error(f"Failed to load app configuration: {e}")
            # Fallback to empty config
            self.config = {"apps": [], "version": "1.0"}

    def reload_config(self):
        """Reload configuration from file"""
        self.load_config()

    def get_user_apps(self, user_role: str, user_tier: str, hostname: str = "localhost") -> List[Dict[str, Any]]:
        """
        Get list of applications available to user

        Args:
            user_role: User's role (admin, power_user, user, viewer)
            user_tier: User's subscription tier
            hostname: Current hostname for URL resolution

        Returns:
            List of app configurations with access information
        """
        cache_key = f"{user_role}:{user_tier}"

        # Check cache
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                logger.debug(f"Returning cached apps for {cache_key}")
                return self._resolve_urls(cached_data, hostname)

        # Get all apps
        all_apps = self.config.get("apps", [])

        # Filter and process apps
        user_apps = []
        for app in all_apps:
            # Check if app is enabled
            if not app.get("enabled", True):
                continue

            # Check access
            access_result = self._check_app_access(user_role, user_tier, app)

            # Create app entry
            app_entry = {
                "id": app.get("id"),
                "name": app.get("name"),
                "description": app.get("description"),
                "icon": app.get("icon"),
                "iconImage": app.get("iconImage"),
                "color": app.get("color"),
                "textColor": app.get("textColor"),
                "url": app.get("url"),
                "port": app.get("port"),
                "enabled": app.get("enabled", True),
                "order": app.get("order", 999),
                "access": access_result,
                "visibility": app.get("visibility", {}),
                "metadata": app.get("metadata", {})
            }

            user_apps.append(app_entry)

        # Cache result (without resolved URLs)
        self.cache[cache_key] = (user_apps, datetime.now())

        # Resolve URLs and return
        return self._resolve_urls(user_apps, hostname)

    def _check_app_access(self, user_role: str, user_tier: str, app: Dict) -> Dict[str, Any]:
        """
        Check if user has access to an app

        Returns:
            {
                "allowed": bool,
                "reason": str,
                "upgrade_path": str (optional)
            }
        """
        access_config = app.get("access", {})
        mode = access_config.get("mode", "any_role")
        required_roles = access_config.get("roles", [])
        required_tiers = access_config.get("tiers", [])

        # Mode: any_role
        if mode == "any_role":
            if user_role in required_roles:
                return {
                    "allowed": True,
                    "reason": f"Available to {user_role} role"
                }
            else:
                return {
                    "allowed": False,
                    "reason": f"Requires one of: {', '.join(required_roles)}",
                    "upgrade_path": "role"
                }

        # Mode: any_tier
        elif mode == "any_tier":
            if user_tier in required_tiers:
                return {
                    "allowed": True,
                    "reason": f"Available to {user_tier} tier"
                }
            else:
                return {
                    "allowed": False,
                    "reason": f"Requires upgrade to: {', '.join(required_tiers)}",
                    "upgrade_path": "tier"
                }

        # Mode: role_and_tier
        elif mode == "role_and_tier":
            role_ok = user_role in required_roles
            tier_ok = user_tier in required_tiers

            if role_ok and tier_ok:
                return {
                    "allowed": True,
                    "reason": f"Access granted: {user_role} + {user_tier}"
                }
            elif not role_ok and not tier_ok:
                return {
                    "allowed": False,
                    "reason": f"Requires role ({', '.join(required_roles)}) AND tier ({', '.join(required_tiers)})",
                    "upgrade_path": "both"
                }
            elif not role_ok:
                return {
                    "allowed": False,
                    "reason": f"Requires role: {', '.join(required_roles)}",
                    "upgrade_path": "role"
                }
            else:
                return {
                    "allowed": False,
                    "reason": f"Requires tier: {', '.join(required_tiers)}",
                    "upgrade_path": "tier"
                }

        # Default: deny
        return {
            "allowed": False,
            "reason": "Access mode not configured"
        }

    def _resolve_urls(self, apps: List[Dict], hostname: str) -> List[Dict]:
        """Resolve 'auto' URLs to actual URLs"""
        resolved_apps = []

        for app in apps:
            app_copy = app.copy()

            if app_copy.get("url") == "auto" and app_copy.get("port"):
                app_copy["url"] = f"http://{hostname}:{app_copy['port']}"

            resolved_apps.append(app_copy)

        return resolved_apps

    def get_app_by_id(self, app_id: str) -> Optional[Dict]:
        """Get app configuration by ID"""
        for app in self.config.get("apps", []):
            if app.get("id") == app_id:
                return app
        return None

    def check_access(self, user_role: str, user_tier: str, app_id: str) -> Dict[str, Any]:
        """Check if user has access to a specific app"""
        app = self.get_app_by_id(app_id)
        if not app:
            return {
                "allowed": False,
                "reason": "App not found"
            }

        return self._check_app_access(user_role, user_tier, app)


# Singleton instance
app_access_manager = AppAccessManager()
```

### 10.2 Backend: API Endpoint

**File**: `backend/server.py` (add to existing file)

```python
from app_access_manager import app_access_manager

@app.get("/api/v1/apps")
async def get_user_apps(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Get applications available to the authenticated user

    Returns apps filtered by user's role and subscription tier
    """
    try:
        # Get user info
        user_role = current_user.get("role", "viewer")
        user_tier = current_user.get("subscription_tier", "trial")
        username = current_user.get("username", "unknown")

        # Get current hostname
        hostname = request.url.hostname or "localhost"

        # Get apps for user
        apps = app_access_manager.get_user_apps(user_role, user_tier, hostname)

        # Calculate statistics
        total_apps = len(apps)
        available_apps = sum(1 for app in apps if app["access"]["allowed"])
        locked_apps = total_apps - available_apps

        # Log access
        logger.info(f"User '{username}' ({user_role}/{user_tier}) accessed apps: {available_apps}/{total_apps} available")

        return {
            "apps": apps,
            "user": {
                "role": user_role,
                "tier": user_tier,
                "username": username
            },
            "statistics": {
                "total_apps": total_apps,
                "available_apps": available_apps,
                "locked_apps": locked_apps
            }
        }

    except Exception as e:
        logger.error(f"Error fetching apps: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch applications")


@app.post("/api/v1/apps/reload")
async def reload_apps_config(current_user: dict = Depends(require_admin)):
    """
    Reload app access configuration (admin only)
    """
    try:
        app_access_manager.reload_config()
        logger.info(f"Admin '{current_user.get('username')}' reloaded app configuration")
        return {"status": "success", "message": "Configuration reloaded"}
    except Exception as e:
        logger.error(f"Error reloading config: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload configuration")
```

### 10.3 Frontend: React Hook

**File**: `src/hooks/useUserApps.js`

```javascript
import { useState, useEffect } from 'react';

/**
 * Custom hook to fetch and manage user apps
 */
export function useUserApps() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statistics, setStatistics] = useState(null);

  useEffect(() => {
    const fetchApps = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/v1/apps', {
          credentials: 'include',
          headers: {
            'Accept': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        // Sort apps by order
        const sortedApps = data.apps.sort((a, b) => a.order - b.order);

        setApps(sortedApps);
        setStatistics(data.statistics);

      } catch (err) {
        console.error('Error fetching apps:', err);
        setError(err.message);

        // Fallback to empty array (or could use default apps)
        setApps([]);
      } finally {
        setLoading(false);
      }
    };

    fetchApps();
  }, []);

  // Filter visible apps
  const visibleApps = apps.filter(app =>
    app.access.allowed || app.visibility?.showWhenLocked
  );

  // Get available apps only
  const availableApps = apps.filter(app => app.access.allowed);

  // Get locked apps
  const lockedApps = apps.filter(app => !app.access.allowed);

  return {
    apps,
    visibleApps,
    availableApps,
    lockedApps,
    loading,
    error,
    statistics
  };
}
```

---

## 11. Testing Strategy

### 11.1 Unit Tests

**Backend Tests**:

```python
# test_app_access_manager.py

import pytest
from app_access_manager import AppAccessManager

def test_admin_sees_all_apps():
    manager = AppAccessManager()
    apps = manager.get_user_apps("admin", "enterprise", "localhost")

    assert len(apps) > 0
    assert all(app["access"]["allowed"] for app in apps)

def test_viewer_sees_limited_apps():
    manager = AppAccessManager()
    apps = manager.get_user_apps("viewer", "trial", "localhost")

    # Viewer should see some apps but not all
    available = [app for app in apps if app["access"]["allowed"]]
    assert len(available) < len(apps)

def test_role_and_tier_mode():
    manager = AppAccessManager()

    # User with role but not tier
    result = manager._check_app_access("user", "trial", {
        "access": {
            "mode": "role_and_tier",
            "roles": ["user", "power_user"],
            "tiers": ["professional", "enterprise"]
        }
    })

    assert result["allowed"] == False
    assert "tier" in result["reason"].lower()

def test_url_resolution():
    manager = AppAccessManager()
    apps = [{"url": "auto", "port": 8080}]
    resolved = manager._resolve_urls(apps, "example.com")

    assert resolved[0]["url"] == "http://example.com:8080"
```

### 11.2 Integration Tests

**API Tests**:

```python
# test_apps_api.py

import pytest
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_apps_endpoint_requires_auth():
    response = client.get("/api/v1/apps")
    assert response.status_code == 401

def test_apps_endpoint_returns_apps_for_admin():
    # Mock authentication
    response = client.get("/api/v1/apps", headers={
        "Authorization": "Bearer admin_token"
    })

    assert response.status_code == 200
    data = response.json()
    assert "apps" in data
    assert "user" in data
    assert "statistics" in data
    assert data["user"]["role"] == "admin"

def test_apps_filtered_by_role():
    # Mock viewer authentication
    response = client.get("/api/v1/apps", headers={
        "Authorization": "Bearer viewer_token"
    })

    data = response.json()
    available = [app for app in data["apps"] if app["access"]["allowed"]]

    # Viewer should not see admin dashboard
    admin_apps = [app for app in available if app["id"] == "admin-dashboard"]
    assert len(admin_apps) == 0
```

### 11.3 Frontend Tests

**Component Tests**:

```javascript
// PublicLanding.test.jsx

import { render, screen, waitFor } from '@testing-library/react';
import { PublicLanding } from './PublicLanding';

describe('PublicLanding', () => {
  test('shows loading state initially', () => {
    render(<PublicLanding />);
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test('displays apps after loading', async () => {
    // Mock API
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          apps: [
            { id: 'test-app', name: 'Test App', access: { allowed: true } }
          ]
        })
      })
    );

    render(<PublicLanding />);

    await waitFor(() => {
      expect(screen.getByText('Test App')).toBeInTheDocument();
    });
  });

  test('shows locked overlay for unavailable apps', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({
          apps: [
            {
              id: 'locked-app',
              name: 'Locked App',
              access: { allowed: false },
              visibility: { showWhenLocked: true }
            }
          ]
        })
      })
    );

    render(<PublicLanding />);

    await waitFor(() => {
      expect(screen.getByText(/upgrade/i)).toBeInTheDocument();
    });
  });
});
```

### 11.4 End-to-End Tests

**User Scenarios**:

1. **Admin User Login**:
   - Login as admin
   - Verify all apps are visible
   - Verify admin dashboard is accessible
   - Click on each app, verify opens correctly

2. **Viewer User Login**:
   - Login as viewer
   - Verify limited apps shown
   - Verify admin dashboard NOT visible
   - Try to access locked app, verify upgrade prompt

3. **Role Change**:
   - Login as user
   - Note available apps
   - Admin changes user to power_user
   - User logs out and back in
   - Verify more apps are available

---

## 12. Rollback Plan

### 12.1 Rollback Triggers

**When to Rollback**:
1. Critical bugs preventing app access
2. Performance degradation (>2s load time)
3. Authentication failures
4. Data loss or corruption
5. Security vulnerabilities discovered

### 12.2 Rollback Procedure

**Step 1**: Identify the issue
- Check logs: `docker logs unicorn-ops-center`
- Check user reports
- Verify with test users

**Step 2**: Quick fix or rollback?
- If quick fix available (< 30 min): Apply patch
- If complex issue: Proceed with rollback

**Step 3**: Rollback frontend
```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
git checkout HEAD~1 src/pages/PublicLanding.jsx
npm run build
docker restart unicorn-ops-center
```

**Step 4**: Rollback backend
```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend
git checkout HEAD~1 server.py
rm app_access_manager.py
docker restart unicorn-ops-center
```

**Step 5**: Verify rollback
- Test with admin user
- Test with viewer user
- Check logs for errors
- Monitor for 30 minutes

**Step 6**: Post-mortem
- Document issue
- Identify root cause
- Create fix
- Test thoroughly
- Re-deploy

### 12.3 Backup Strategy

**Before Deployment**:
1. Git commit all changes
2. Tag release: `git tag -a v1.0-app-access`
3. Backup configuration files
4. Document current state

**Backup Files**:
```bash
# Create backup directory
mkdir -p /opt/backups/$(date +%Y%m%d)

# Backup files
cp src/pages/PublicLanding.jsx /opt/backups/$(date +%Y%m%d)/
cp backend/server.py /opt/backups/$(date +%Y%m%d)/
cp backend/config/*.json /opt/backups/$(date +%Y%m%d)/
```

---

## 13. Recommendations & Best Practices

### 13.1 Configuration Management

**DO**:
- Use JSON schema validation for configuration files
- Version control all configuration changes
- Document each configuration field
- Test configuration changes in staging first
- Keep configuration DRY (Don't Repeat Yourself)

**DON'T**:
- Hardcode app configurations in frontend
- Store sensitive data in configuration files
- Make configuration changes directly in production
- Skip validation of configuration syntax
- Use inconsistent naming conventions

### 13.2 Access Control

**DO**:
- Default to least privilege (viewer role)
- Validate access on both frontend and backend
- Log all access control decisions
- Use role hierarchy (admin > power_user > user > viewer)
- Separate role-based and tier-based access concerns

**DON'T**:
- Trust client-side access checks
- Grant broad permissions by default
- Mix authentication and authorization logic
- Skip audit logging for sensitive operations
- Hardcode role names in multiple places

### 13.3 User Experience

**DO**:
- Show clear upgrade paths for locked apps
- Provide descriptive access denial messages
- Use loading states for async operations
- Handle errors gracefully with fallbacks
- Maintain consistent UI/UX patterns

**DON'T**:
- Show apps that users can never access
- Use generic error messages ("Access Denied")
- Block UI during long operations
- Hide functionality without explanation
- Surprise users with sudden access changes

### 13.4 Performance

**DO**:
- Cache configuration at application startup
- Use efficient data structures (O(1) lookups)
- Minimize API calls (batch operations)
- Implement proper cache invalidation
- Monitor API response times

**DON'T**:
- Load configuration on every request
- Use nested loops for filtering
- Make redundant API calls
- Cache indefinitely without TTL
- Ignore performance metrics

---

## 14. Success Metrics

### 14.1 Key Performance Indicators (KPIs)

**Technical Metrics**:
- API response time: < 500ms (p95)
- Page load time: < 2s (full page)
- Error rate: < 0.1%
- Uptime: > 99.9%

**User Experience Metrics**:
- Time to first app interaction: < 3s
- Number of access denials per user: < 2/session
- User satisfaction score: > 4/5
- Feature discovery rate: > 80%

**Business Metrics**:
- Upgrade conversion rate: Track locked app clicks
- App engagement: Which apps are most used
- User retention: Do users return
- Support tickets: Decrease in access-related issues

### 14.2 Monitoring & Alerting

**What to Monitor**:
1. `/api/v1/apps` response times
2. Access denial patterns
3. Configuration load failures
4. Cache hit/miss rates
5. User session errors

**Alerts**:
- Critical: API errors > 5%
- Warning: Response time > 1s
- Info: Configuration reloaded
- Debug: Access denied for specific apps

**Tools**:
- Grafana dashboards for metrics
- Audit logs for security events
- User feedback forms
- Analytics for app usage

---

## 15. Conclusion

### 15.1 Summary

This architecture design provides a comprehensive, secure, and extensible solution for implementing role-based app access control on the UC-1 Pro landing page. The design:

1. **Separates Concerns**: Role-based and tier-based access are distinct but complementary
2. **Configuration-Driven**: Easy to add new apps without code changes
3. **Secure by Default**: Backend validation, principle of least privilege
4. **User-Friendly**: Clear communication of access levels
5. **Extensible**: Supports future features (admin UI, analytics, etc.)
6. **Performant**: Caching, efficient algorithms, minimal overhead

### 15.2 Next Steps

**Immediate Actions**:
1. Review and approve this design document
2. Create implementation tasks in project management tool
3. Set up development environment
4. Create initial configuration file
5. Begin Phase 1 implementation

**Timeline Estimate**:
- Phase 1 (Backend): 2-3 days
- Phase 2 (Frontend): 2-3 days
- Phase 3 (Admin Integration): 1 day
- Phase 4 (Testing): 2-3 days
- Phase 5 (Documentation & Rollout): 1-2 days
- **Total**: 8-12 days (1.5-2 weeks)

### 15.3 Questions & Discussion

**Open Questions**:
1. Should we migrate existing tier-based system or run both in parallel?
2. Do we need an admin UI for app management in Phase 1?
3. Should app access be cached in user session or fetched on every page load?
4. What should be the default behavior for apps with no access configuration?

**Areas for Feedback**:
- Data model structure
- API endpoint design
- Frontend rendering approach
- Performance optimization strategy
- Rollout timeline

---

## 16. Appendix

### 16.1 Glossary

**Terms**:
- **Role**: User's permission level (admin, power_user, user, viewer)
- **Tier**: Subscription level (trial, byok, professional, enterprise)
- **App**: Service or application accessible from landing page
- **Access Mode**: Rule for how roles/tiers combine (any_role, role_and_tier, etc.)
- **Lock Overlay**: UI element showing app is unavailable
- **Upgrade Path**: Steps user needs to take to access locked app

### 16.2 Related Documents

- [ROLE_MAPPING.md](/home/deploy/Production/UC-1-Pro/services/ops-center/backend/ROLE_MAPPING.md)
- [AUTHENTIK_SETUP.md](/home/deploy/Production/UC-1-Pro/services/ops-center/backend/AUTHENTIK_SETUP.md)
- [API_QUICK_REFERENCE.md](/home/deploy/Production/UC-1-Pro/services/ops-center/docs/ADMIN_API_QUICK_REFERENCE.md)
- [OPS_CENTER_DESIGN.md](/home/deploy/Production/UC-1-Pro/services/ops-center/OPS_CENTER_DESIGN.md)

### 16.3 References

- UC-1 Pro GitHub: https://github.com/Unicorn-Commander/UC-1-Pro
- Authentik Documentation: https://goauthentik.io/docs/
- React Router: https://reactrouter.com/
- FastAPI: https://fastapi.tiangolo.com/
- JWT: https://jwt.io/

---

**Document Version**: 1.0
**Last Updated**: October 9, 2025
**Status**: Draft - Awaiting Review
**Author**: System Architecture Designer
**Reviewers**: Development Team, Security Team, Product Owner
