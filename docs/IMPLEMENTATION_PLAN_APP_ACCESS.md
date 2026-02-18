# Role-Based App Access - Implementation Plan

**Status**: Ready for Development
**Timeline**: 8-12 days
**Complexity**: Medium

---

## Quick Start

**Goal**: Filter landing page apps by user role (admin, power_user, user, viewer)

**Approach**: Configuration-driven with backend API validation

**Key Files**:
- Configuration: `backend/config/apps_access.json` (new)
- Backend: `backend/app_access_manager.py` (new)
- Backend API: `backend/server.py` (modify)
- Frontend: `src/pages/PublicLanding.jsx` (refactor)

---

## Implementation Phases

### Phase 1: Backend Foundation (2-3 days)

**Tasks**:
1. Create `apps_access.json` configuration file
2. Implement `AppAccessManager` class
3. Add `/api/v1/apps` endpoint to server.py
4. Update `/api/v1/auth/session` to include role and tier
5. Write unit tests for access logic

**Deliverables**:
- Working API endpoint that returns filtered apps
- Configuration file with all current services
- Unit tests with 90%+ coverage

### Phase 2: Frontend Integration (2-3 days)

**Tasks**:
1. Create `useUserApps` React hook
2. Refactor `PublicLanding.jsx` to use API
3. Remove hardcoded services array
4. Remove client-side access logic
5. Add loading and error states
6. Update app card rendering

**Deliverables**:
- Landing page loads apps from API
- Locked apps show upgrade prompts
- Smooth user experience with loading states

### Phase 3: Admin Dashboard Integration (1 day)

**Tasks**:
1. Add admin dashboard to `apps_access.json`
2. Configure admin-only access (roles: ["admin"])
3. Set visibility to hide from non-admins
4. Test admin and non-admin views
5. Update user dropdown menu

**Deliverables**:
- Admin dashboard only visible to admins
- Non-admins don't see dashboard link

### Phase 4: Testing & Validation (2-3 days)

**Tasks**:
1. Test with all user roles (admin, power_user, user, viewer)
2. Test with different subscription tiers
3. Test error handling (API failures, network issues)
4. Performance testing (load times, caching)
5. Security testing (access bypass attempts)
6. Integration testing (end-to-end flows)

**Deliverables**:
- Test coverage > 80%
- All user roles tested and working
- Performance within targets

### Phase 5: Documentation & Rollout (1-2 days)

**Tasks**:
1. Update ROLE_MAPPING.md with app access info
2. Create admin guide for managing apps
3. Document API endpoint
4. Deploy to staging
5. Test with real users
6. Deploy to production
7. Monitor for issues

**Deliverables**:
- Complete documentation
- Successful production deployment
- No critical issues

---

## Task Breakdown

### Backend Tasks

**File: `backend/config/apps_access.json`**
```
[ ] Create configuration file structure
[ ] Define schema for app objects
[ ] Add all current services from landing page
[ ] Add admin dashboard app
[ ] Configure access rules for each app
[ ] Validate JSON syntax
```

**File: `backend/app_access_manager.py`**
```
[ ] Create AppAccessManager class
[ ] Implement load_config() method
[ ] Implement get_user_apps() method
[ ] Implement _check_app_access() method
[ ] Implement _resolve_urls() method
[ ] Add caching with TTL
[ ] Add logging for debugging
```

**File: `backend/server.py`**
```
[ ] Import AppAccessManager
[ ] Add GET /api/v1/apps endpoint
[ ] Integrate with authentication middleware
[ ] Add error handling
[ ] Add logging
[ ] Add POST /api/v1/apps/reload endpoint (admin only)
```

**File: `backend/test_app_access.py`**
```
[ ] Write unit tests for AppAccessManager
[ ] Test all access modes (any_role, any_tier, role_and_tier)
[ ] Test role hierarchy
[ ] Test URL resolution
[ ] Test caching behavior
[ ] Test configuration reload
```

### Frontend Tasks

**File: `src/hooks/useUserApps.js`**
```
[ ] Create custom React hook
[ ] Implement API call to /api/v1/apps
[ ] Add loading state
[ ] Add error handling
[ ] Add filtering (visible vs available apps)
[ ] Cache results in session storage
```

**File: `src/pages/PublicLanding.jsx`**
```
[ ] Remove hardcoded services array
[ ] Remove serviceTiers mapping
[ ] Remove hasAccess() function
[ ] Remove handleServiceClick() function
[ ] Import useUserApps hook
[ ] Update useEffect to fetch apps
[ ] Update rendering logic
[ ] Update app card rendering
[ ] Add loading spinner
[ ] Add error message
```

**File: `src/components/AppCard.jsx`** (optional: extract component)
```
[ ] Create separate AppCard component
[ ] Handle locked state rendering
[ ] Implement upgrade modal/toast
[ ] Add accessibility attributes
[ ] Add animations
```

### Testing Tasks

**Unit Tests**
```
[ ] Test AppAccessManager with admin role
[ ] Test AppAccessManager with viewer role
[ ] Test role_and_tier mode
[ ] Test URL resolution
[ ] Test configuration validation
[ ] Test caching behavior
```

**Integration Tests**
```
[ ] Test /api/v1/apps endpoint with authentication
[ ] Test access control for each app
[ ] Test with different roles and tiers
[ ] Test error responses
```

**Frontend Tests**
```
[ ] Test useUserApps hook
[ ] Test PublicLanding component rendering
[ ] Test loading states
[ ] Test error states
[ ] Test locked app interaction
```

**End-to-End Tests**
```
[ ] Test admin user login and app access
[ ] Test viewer user login and limited access
[ ] Test role change scenario
[ ] Test app click and navigation
[ ] Test upgrade prompt interaction
```

### Documentation Tasks

```
[ ] Update ROLE_MAPPING.md with app access section
[ ] Create APP_CONFIGURATION_GUIDE.md for admins
[ ] Update API_QUICK_REFERENCE.md with /api/v1/apps
[ ] Create troubleshooting guide
[ ] Update README with new features
```

---

## Code Snippets

### 1. Configuration File Example

**File: `backend/config/apps_access.json`**

```json
{
  "version": "1.0",
  "apps": [
    {
      "id": "open-webui",
      "name": "Open-WebUI Chat",
      "description": "Advanced AI chat interface",
      "icon": "ChatBubbleLeftRightIcon",
      "color": "from-blue-500 to-blue-700",
      "textColor": "text-blue-100",
      "url": "auto",
      "port": 8080,
      "enabled": true,
      "order": 1,
      "access": {
        "roles": ["admin", "power_user", "user", "viewer"],
        "mode": "any_role"
      },
      "visibility": {
        "showWhenLocked": true,
        "upgradePrompt": false,
        "requiredFor": "Available to all users"
      }
    },
    {
      "id": "admin-dashboard",
      "name": "Admin Dashboard",
      "description": "System management and configuration",
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
      }
    }
  ]
}
```

### 2. API Endpoint Example

**File: `backend/server.py`**

```python
from app_access_manager import app_access_manager

@app.get("/api/v1/apps")
async def get_user_apps(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Get applications available to the authenticated user"""
    user_role = current_user.get("role", "viewer")
    user_tier = current_user.get("subscription_tier", "trial")
    hostname = request.url.hostname or "localhost"

    apps = app_access_manager.get_user_apps(user_role, user_tier, hostname)

    return {
        "apps": apps,
        "user": {
            "role": user_role,
            "tier": user_tier,
            "username": current_user.get("username")
        },
        "statistics": {
            "total_apps": len(apps),
            "available_apps": sum(1 for app in apps if app["access"]["allowed"]),
            "locked_apps": sum(1 for app in apps if not app["access"]["allowed"])
        }
    }
```

### 3. React Hook Example

**File: `src/hooks/useUserApps.js`**

```javascript
import { useState, useEffect } from 'react';

export function useUserApps() {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchApps = async () => {
      try {
        const response = await fetch('/api/v1/apps', {
          credentials: 'include'
        });

        if (response.ok) {
          const data = await response.json();
          setApps(data.apps.sort((a, b) => a.order - b.order));
        } else {
          throw new Error('Failed to fetch apps');
        }
      } catch (err) {
        setError(err.message);
        setApps([]);
      } finally {
        setLoading(false);
      }
    };

    fetchApps();
  }, []);

  const visibleApps = apps.filter(app =>
    app.access.allowed || app.visibility?.showWhenLocked
  );

  return { apps, visibleApps, loading, error };
}
```

### 4. Frontend Usage Example

**File: `src/pages/PublicLanding.jsx`**

```javascript
import { useUserApps } from '../hooks/useUserApps';

export default function PublicLanding() {
  const { visibleApps, loading, error } = useUserApps();
  const [currentHost, setCurrentHost] = useState('localhost');

  useEffect(() => {
    setCurrentHost(window.location.hostname);
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {visibleApps.map((app, index) => (
        <AppCard
          key={app.id}
          app={app}
          index={index}
          currentHost={currentHost}
        />
      ))}
    </div>
  );
}
```

---

## Configuration Examples

### Example 1: All Users Can Access

```json
{
  "id": "open-webui",
  "name": "Open-WebUI",
  "access": {
    "roles": ["admin", "power_user", "user", "viewer"],
    "mode": "any_role"
  }
}
```

### Example 2: Admin Only

```json
{
  "id": "admin-dashboard",
  "name": "Admin Dashboard",
  "access": {
    "roles": ["admin"],
    "mode": "any_role"
  },
  "visibility": {
    "showWhenLocked": false
  }
}
```

### Example 3: Requires Role AND Tier

```json
{
  "id": "bolt-diy",
  "name": "Bolt.diy",
  "access": {
    "roles": ["admin", "power_user", "user"],
    "tiers": ["professional", "enterprise"],
    "mode": "role_and_tier"
  },
  "visibility": {
    "showWhenLocked": true,
    "upgradePrompt": true,
    "requiredFor": "Professional tier + User role required"
  }
}
```

### Example 4: Tier-Based Only

```json
{
  "id": "premium-feature",
  "name": "Premium Feature",
  "access": {
    "tiers": ["enterprise"],
    "mode": "any_tier"
  },
  "visibility": {
    "showWhenLocked": true,
    "upgradePrompt": true,
    "requiredFor": "Enterprise tier required"
  }
}
```

---

## Testing Checklist

### Manual Testing

**Admin User (role: admin, tier: enterprise)**
```
[ ] Login successful
[ ] All apps visible
[ ] Admin dashboard visible
[ ] All apps clickable
[ ] No locked apps
[ ] No upgrade prompts
```

**Power User (role: power_user, tier: professional)**
```
[ ] Login successful
[ ] Most apps visible
[ ] Admin dashboard NOT visible
[ ] Professional tier apps accessible
[ ] Enterprise apps locked
[ ] Upgrade prompts shown for locked apps
```

**Standard User (role: user, tier: trial)**
```
[ ] Login successful
[ ] Basic apps visible
[ ] Admin dashboard NOT visible
[ ] Trial tier apps accessible
[ ] Professional/Enterprise apps locked
[ ] Upgrade prompts shown
```

**Viewer (role: viewer, tier: trial)**
```
[ ] Login successful
[ ] Limited apps visible
[ ] Admin dashboard NOT visible
[ ] Only viewer-accessible apps available
[ ] Most apps locked
[ ] Upgrade prompts shown
```

### Automated Testing

**Unit Tests**
```
[ ] AppAccessManager.get_user_apps() with admin
[ ] AppAccessManager.get_user_apps() with viewer
[ ] AppAccessManager._check_app_access() for each mode
[ ] URL resolution with 'auto' URLs
[ ] Configuration validation
[ ] Cache hit/miss scenarios
```

**API Tests**
```
[ ] GET /api/v1/apps returns 401 without auth
[ ] GET /api/v1/apps returns 200 with auth
[ ] Response includes apps, user, statistics
[ ] Apps filtered correctly by role
[ ] Apps filtered correctly by tier
```

**Frontend Tests**
```
[ ] useUserApps hook fetches apps
[ ] useUserApps hook handles errors
[ ] PublicLanding renders loading state
[ ] PublicLanding renders apps
[ ] PublicLanding renders locked overlay
```

---

## Deployment Steps

### Pre-Deployment

1. **Create backup**
   ```bash
   mkdir -p /opt/backups/$(date +%Y%m%d)
   cp -r /home/deploy/Production/UC-1-Pro/services/ops-center/src \
      /opt/backups/$(date +%Y%m%d)/
   cp -r /home/deploy/Production/UC-1-Pro/services/ops-center/backend \
      /opt/backups/$(date +%Y%m%d)/
   ```

2. **Git commit**
   ```bash
   git add .
   git commit -m "feat: Implement role-based app access control"
   git tag -a v1.1-app-access -m "Role-based app access control"
   ```

### Deployment

1. **Deploy to staging**
   ```bash
   cd /home/deploy/Production/UC-1-Pro/services/ops-center
   git checkout staging
   git merge main
   npm run build
   docker restart unicorn-ops-center-staging
   ```

2. **Test in staging**
   - Test with all user roles
   - Verify no errors in logs
   - Check performance metrics
   - Get approval from team

3. **Deploy to production**
   ```bash
   git checkout main
   npm run build
   docker restart unicorn-ops-center
   ```

4. **Monitor**
   - Watch logs: `docker logs -f unicorn-ops-center`
   - Check Grafana dashboards
   - Monitor error rates
   - Gather user feedback

### Post-Deployment

1. **Verify deployment**
   ```bash
   curl -I https://unicorncommander.ai
   curl -H "Authorization: Bearer $TOKEN" https://unicorncommander.ai/api/v1/apps
   ```

2. **Update documentation**
   - Update changelog
   - Notify users of changes
   - Update admin guides

3. **Monitor for 24 hours**
   - Watch for errors
   - Check performance
   - Respond to issues quickly

---

## Rollback Plan

**If issues occur:**

1. **Quick rollback**
   ```bash
   cd /home/deploy/Production/UC-1-Pro/services/ops-center
   git checkout HEAD~1
   npm run build
   docker restart unicorn-ops-center
   ```

2. **Verify rollback**
   - Test landing page
   - Check logs
   - Verify apps load

3. **Investigate issue**
   - Review logs
   - Identify root cause
   - Create fix
   - Redeploy when ready

---

## Success Criteria

**Technical**:
- API response time < 500ms
- No errors in production
- All tests passing
- Code coverage > 80%

**Functional**:
- Admins see all apps
- Viewers see limited apps
- Locked apps show upgrade prompts
- No access bypass possible

**User Experience**:
- Smooth page load
- Clear access indicators
- Helpful upgrade messages
- No confusion about access

---

## Contact & Support

**Questions**: Development Team
**Issues**: GitHub Issues
**Documentation**: /docs folder
**Monitoring**: Grafana Dashboard

---

**Document Version**: 1.0
**Last Updated**: October 9, 2025
**Status**: Ready for Implementation
