# Role-Based App Access - Architecture Diagrams

**Visual Guide to System Architecture**

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              PublicLanding.jsx (React)                     │  │
│  │                                                             │  │
│  │  1. User logs in via Authentik                             │  │
│  │  2. Loads landing page                                     │  │
│  │  3. Fetches /api/v1/apps                                   │  │
│  │  4. Renders filtered app cards                             │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                              ↓ HTTPS
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Ops-Center Backend (FastAPI)                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │            GET /api/v1/apps Endpoint                       │  │
│  │                                                             │  │
│  │  1. Authenticate user (JWT token)                          │  │
│  │  2. Extract role and tier from session                     │  │
│  │  3. Call AppAccessManager.get_user_apps()                  │  │
│  │  4. Return filtered apps JSON                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           AppAccessManager (Python Class)                  │  │
│  │                                                             │  │
│  │  • Loads apps_access.json config                           │  │
│  │  • Checks access for each app                              │  │
│  │  • Applies role and tier rules                             │  │
│  │  • Resolves URLs (auto → hostname:port)                    │  │
│  │  • Caches results (5 min TTL)                              │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              ↓                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │          apps_access.json Configuration File               │  │
│  │                                                             │  │
│  │  • Defines all available apps                              │  │
│  │  • Specifies access rules (roles/tiers)                    │  │
│  │  • Configures visibility settings                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Authentication Flow

```
┌─────────┐      ┌──────────┐      ┌───────────┐      ┌─────────────┐
│  User   │──1──▶│ Authentik│──2──▶│Ops-Center │──3──▶│ User Session│
└─────────┘      └──────────┘      └───────────┘      └─────────────┘
     │                                     │                   │
     │                                     │                   │
     │            OAuth Callback           │                   │
     │◀────────────────────────────────────┘                   │
     │                                                          │
     │                                                          │
     │            Request /api/v1/apps                          │
     │──────────────────────────────────────────────────────────▶
     │                                                          │
     │            JWT Token in Cookie                           │
     │◀─────────────────────────────────────────────────────────│
     │                                                          │
     │            Backend validates token                       │
     │            Extracts user role + tier                     │
     │            Filters apps based on access                  │
     │                                                          │
     │◀──────────────────────────────────────────────────────────
     │            Returns filtered app list                     │
     │                                                          │
     ▼                                                          │
Display apps                                                    │
on landing page                                                 │

Legend:
──1──▶  Login with credentials
──2──▶  Authenticate and issue token
──3──▶  Create session with role/tier
```

---

## 3. Access Control Decision Tree

```
                    ┌─────────────────┐
                    │   User Request  │
                    │  /api/v1/apps   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Authenticated?  │
                    └────────┬────────┘
                        Yes  │  No
                    ┌────────┴────────┐
                    ▼                 ▼
            ┌──────────────┐   ┌───────────┐
            │ Extract Role │   │Return 401 │
            │ Extract Tier │   └───────────┘
            └──────┬───────┘
                   │
                   ▼
         ┌──────────────────┐
         │  For each app in │
         │  configuration   │
         └──────┬───────────┘
                │
                ▼
       ┌────────────────────┐
       │  Check Access Mode │
       └──────┬─────────────┘
              │
      ┌───────┴───────┐
      │               │
      ▼               ▼
┌─────────┐    ┌──────────────┐
│any_role │    │role_and_tier │
└────┬────┘    └──────┬───────┘
     │                │
     ▼                ▼
Role in      Role in roles?
roles?       AND
     │       Tier in tiers?
     │                │
     ▼                ▼
 ┌───────┐      ┌─────────┐
 │Allowed│      │Allowed? │
 └───┬───┘      └────┬────┘
     │               │
     └───────┬───────┘
             │
             ▼
    ┌─────────────────┐
    │ Add to response │
    │ with access info│
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │Return app list  │
    │ to frontend     │
    └─────────────────┘
```

---

## 4. Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                           Frontend                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              PublicLanding.jsx                          │    │
│  │  • Main landing page component                          │    │
│  │  • Uses useUserApps hook                                │    │
│  │  • Renders app grid                                     │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│                       │ imports                                  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────┐    │
│  │           useUserApps.js (React Hook)                   │    │
│  │  • Fetches apps from API                                │    │
│  │  • Manages loading/error state                          │    │
│  │  • Filters visible apps                                 │    │
│  └────────────────────┬───────────────────────────────────┘    │
│                       │                                          │
│                       │ calls                                    │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────┐    │
│  │              AppCard.jsx                                │    │
│  │  • Individual app card component                        │    │
│  │  • Shows lock overlay if locked                         │    │
│  │  • Handles click events                                 │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                     HTTP GET /api/v1/apps
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                            Backend                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           server.py (FastAPI Application)                │   │
│  │  • Defines API endpoints                                 │   │
│  │  • Handles authentication                                │   │
│  │  • Routes requests                                       │   │
│  └────────────────────┬────────────────────────────────────┘   │
│                       │                                          │
│                       │ uses                                     │
│                       │                                          │
│  ┌────────────────────▼────────────────────────────────────┐   │
│  │        app_access_manager.py (Python Module)             │   │
│  │  • AppAccessManager class                                │   │
│  │  • load_config()                                         │   │
│  │  • get_user_apps(role, tier, hostname)                   │   │
│  │  • _check_app_access(role, tier, app)                    │   │
│  │  • _resolve_urls(apps, hostname)                         │   │
│  └────────────────────┬────────────────────────────────────┘   │
│                       │                                          │
│                       │ reads                                    │
│                       │                                          │
│  ┌────────────────────▼────────────────────────────────────┐   │
│  │    config/apps_access.json (Configuration)               │   │
│  │  • App definitions                                       │   │
│  │  • Access rules                                          │   │
│  │  • Visibility settings                                   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Data Flow Diagram

```
┌──────────┐         ┌──────────┐         ┌──────────┐
│ User     │         │ Frontend │         │ Backend  │
└────┬─────┘         └────┬─────┘         └────┬─────┘
     │                    │                     │
     │  1. Visit Landing  │                     │
     │───────────────────▶│                     │
     │                    │                     │
     │                    │  2. Fetch Session   │
     │                    │────────────────────▶│
     │                    │                     │
     │                    │◀────────────────────│
     │                    │  3. Session Data    │
     │                    │  (role: admin)      │
     │                    │                     │
     │                    │  4. Fetch Apps      │
     │                    │────────────────────▶│
     │                    │                     │
     │                    │                     │──┐
     │                    │                     │  │ 5. Load Config
     │                    │                     │◀─┘
     │                    │                     │
     │                    │                     │──┐
     │                    │                     │  │ 6. Check Access
     │                    │                     │  │    for each app
     │                    │                     │◀─┘
     │                    │                     │
     │                    │                     │──┐
     │                    │                     │  │ 7. Resolve URLs
     │                    │                     │◀─┘
     │                    │                     │
     │                    │◀────────────────────│
     │                    │  8. Filtered Apps   │
     │                    │  [{id, name, url,   │
     │                    │    access:{allowed}}]│
     │                    │                     │
     │                    │──┐                  │
     │                    │  │ 9. Sort & Filter │
     │                    │◀─┘                  │
     │                    │                     │
     │◀───────────────────│                     │
     │ 10. Render Cards   │                     │
     │    (visible apps)  │                     │
     │                    │                     │
     │ 11. Click App      │                     │
     │───────────────────▶│                     │
     │                    │                     │
     │                    │──┐                  │
     │                    │  │ 12. Check Locked │
     │                    │◀─┘                  │
     │                    │                     │
     │◀───────────────────│                     │
     │ 13. Navigate to    │                     │
     │     App or Show    │                     │
     │     Upgrade Prompt │                     │
     │                    │                     │
```

---

## 6. Access Control Matrix

```
┌───────────────────┬────────┬────────────┬──────┬────────┐
│ Application       │ Admin  │ Power User │ User │ Viewer │
├───────────────────┼────────┼────────────┼──────┼────────┤
│ Open-WebUI        │   ✓    │     ✓      │  ✓   │   ✓    │
│ Center Deep       │   ✓    │     ✓      │  ✓   │   ✓    │
│ Presenton         │   ✓    │     ✓      │  ✓   │   ✓    │
│ User Docs         │   ✓    │     ✓      │  ✓   │   ✓    │
├───────────────────┼────────┼────────────┼──────┼────────┤
│ Bolt.diy          │   ✓    │     ✓      │  ✓   │   ✗    │
│                   │        │(+ Pro tier)│(+Pro)│        │
├───────────────────┼────────┼────────────┼──────┼────────┤
│ Grafana           │   ✓    │     ✓      │  ✗   │   ✗    │
│ Portainer         │   ✓    │     ✓      │  ✗   │   ✗    │
│                   │        │(+ Pro tier)│      │        │
├───────────────────┼────────┼────────────┼──────┼────────┤
│ Unicorn Orator    │   ✓    │     ✓      │  ✓   │   ✗    │
│                   │        │(+ Ent tier)│(+Ent)│        │
├───────────────────┼────────┼────────────┼──────┼────────┤
│ Admin Dashboard   │   ✓    │     ✗      │  ✗   │   ✗    │
└───────────────────┴────────┴────────────┴──────┴────────┘

Legend:
✓ = Access granted
✗ = Access denied
(+ tier) = Requires subscription tier upgrade
```

---

## 7. Caching Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   Cache Layers                          │
└─────────────────────────────────────────────────────────┘

Layer 1: Configuration Cache (Backend)
┌─────────────────────────────────────────┐
│  apps_access.json loaded at startup     │
│  TTL: Until file modification           │
│  Scope: All users                       │
└─────────────────────────────────────────┘
              │
              │ File loaded once
              ▼

Layer 2: Access Results Cache (Backend)
┌─────────────────────────────────────────┐
│  Filtered apps per role:tier combo      │
│  TTL: 5 minutes                         │
│  Scope: Per role/tier combination       │
│  Key: "admin:enterprise"                │
└─────────────────────────────────────────┘
              │
              │ Computed on first request
              ▼

Layer 3: API Response Cache (Backend)
┌─────────────────────────────────────────┐
│  Full JSON response                     │
│  TTL: 5 minutes                         │
│  Scope: Per user                        │
└─────────────────────────────────────────┘
              │
              │ Sent to frontend
              ▼

Layer 4: Frontend Cache (Browser)
┌─────────────────────────────────────────┐
│  Apps array in component state          │
│  TTL: Until page refresh                │
│  Scope: Current session                 │
└─────────────────────────────────────────┘


Cache Invalidation:
• Layer 1: File watcher triggers reload
• Layer 2: TTL expiration or manual reload
• Layer 3: TTL expiration or logout
• Layer 4: Page refresh or logout
```

---

## 8. Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                    Defense in Depth                          │
└─────────────────────────────────────────────────────────────┘

Layer 1: Frontend Visibility
┌─────────────────────────────────────────┐
│  • Hide apps user cannot access         │
│  • Show lock overlay for locked apps    │
│  • Prevent navigation to locked apps    │
│                                         │
│  Purpose: User Experience               │
│  Security Level: LOW (bypassable)       │
└─────────────────────────────────────────┘
              │
              │ User might bypass
              ▼

Layer 2: Backend API Validation
┌─────────────────────────────────────────┐
│  • Validate JWT token                   │
│  • Check role from session              │
│  • Filter apps before sending           │
│  • Log access attempts                  │
│                                         │
│  Purpose: Access Control                │
│  Security Level: HIGH                   │
└─────────────────────────────────────────┘
              │
              │ Authorized API response
              ▼

Layer 3: Service-Level Authentication
┌─────────────────────────────────────────┐
│  • Services require Authentik SSO       │
│  • Traefik enforces authentication      │
│  • Services validate OAuth tokens       │
│  • Session management                   │
│                                         │
│  Purpose: Deep Security                 │
│  Security Level: VERY HIGH              │
└─────────────────────────────────────────┘


Attack Scenarios & Mitigations:

Scenario 1: User modifies frontend to show admin dashboard
┌─────────────────────────────────────────┐
│  Attack: Modify React state             │
│  Mitigation: Backend checks role        │
│  Result: 403 Forbidden                  │
└─────────────────────────────────────────┘

Scenario 2: User directly accesses service URL
┌─────────────────────────────────────────┐
│  Attack: http://localhost:9444 (Portainer)│
│  Mitigation: Traefik + Authentik SSO    │
│  Result: Redirect to auth page          │
└─────────────────────────────────────────┘

Scenario 3: User forges JWT token
┌─────────────────────────────────────────┐
│  Attack: Create fake JWT with admin role│
│  Mitigation: JWT signature validation   │
│  Result: 401 Unauthorized               │
└─────────────────────────────────────────┘
```

---

## 9. Configuration Schema

```
apps_access.json Structure
│
├── version: "1.0"
│
├── roleHierarchy: ["admin", "power_user", "user", "viewer"]
│
├── tierHierarchy: ["trial", "byok", "professional", "enterprise"]
│
├── accessModes: {
│       "any_role": "Description",
│       "role_and_tier": "Description"
│   }
│
├── apps: [
│   │
│   ├── App Object:
│   │   ├── id: "unique-app-id"
│   │   ├── name: "Display Name"
│   │   ├── description: "User-facing description"
│   │   ├── icon: "HeroIcon name"
│   │   ├── iconImage: "/path/to/image.png" (optional)
│   │   ├── color: "gradient classes"
│   │   ├── textColor: "text color classes"
│   │   ├── url: "auto" or "http://..." or "/path"
│   │   ├── port: 8080 (if url is "auto")
│   │   ├── enabled: true/false
│   │   ├── order: 1
│   │   │
│   │   ├── access: {
│   │   │   ├── roles: ["admin", "user"]
│   │   │   ├── tiers: ["professional"]
│   │   │   └── mode: "role_and_tier"
│   │   │   }
│   │   │
│   │   ├── visibility: {
│   │   │   ├── showWhenLocked: true/false
│   │   │   ├── upgradePrompt: true/false
│   │   │   └── requiredFor: "Message to user"
│   │   │   }
│   │   │
│   │   └── metadata: {
│   │       ├── category: "ai-tools"
│   │       ├── tags: ["tag1", "tag2"]
│   │       ├── apiOnly: false
│   │       ├── subdomain: "app"
│   │       └── path: "/web"
│   │       }
│   │
│   └── ... more apps
│   ]
│
├── categories: {
│       "category-id": {
│           name: "Display Name",
│           description: "Description",
│           icon: "Icon",
│           order: 1
│       }
│   }
│
└── settings: {
        cacheEnabled: true,
        cacheTTL: 300,
        enableAuditLog: true
    }
```

---

## 10. Deployment Workflow

```
Development → Testing → Staging → Production
     │            │          │          │
     │            │          │          │
     ▼            ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌──────┐ ┌──────────┐
│ Feature │ │  Unit   │ │ UAT  │ │ Monitor  │
│ Branch  │ │ Tests   │ │ Test │ │ + Logs   │
└─────────┘ └─────────┘ └──────┘ └──────────┘
     │            │          │          │
     │            │          │          │
     ▼            ▼          ▼          ▼
   Code      Integration   Real      Health
   Review    Tests Pass    Users     Checks
     │            │          │          │
     └────────────┴──────────┴──────────┘
                  │
                  ▼
         ┌──────────────────┐
         │   Production     │
         │   Deployment     │
         └──────────────────┘


Rollback Strategy:
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│  Issue       │──────▶│  Detect      │──────▶│  Rollback    │
│  Detected    │       │  Severity    │       │  if Critical │
└──────────────┘       └──────────────┘       └──────────────┘
                              │
                              │ If Non-Critical
                              ▼
                       ┌──────────────┐
                       │  Quick Fix   │
                       │  & Deploy    │
                       └──────────────┘
```

---

## 11. Performance Optimization

```
Optimization Points:

1. Configuration Loading
   ┌─────────────────────────────────┐
   │ Load at Startup    (Slow)       │
   │      ↓                           │
   │ Parse JSON         (Fast)       │
   │      ↓                           │
   │ Validate Schema    (Fast)       │
   │      ↓                           │
   │ Keep in Memory     (Very Fast)  │
   └─────────────────────────────────┘
   Time: < 100ms once

2. Access Check
   ┌─────────────────────────────────┐
   │ Get User Role/Tier (Fast)       │
   │      ↓                           │
   │ Check Cache        (Very Fast)  │
   │      ↓                           │
   │ If Miss:                         │
   │   For each app:                 │
   │     Check access   (Fast)       │
   │     O(n) where n = apps         │
   │      ↓                           │
   │ Cache Result       (Fast)       │
   └─────────────────────────────────┘
   Time: < 50ms (cached)
         < 200ms (uncached)

3. API Response
   ┌─────────────────────────────────┐
   │ Get Cached Apps    (Very Fast)  │
   │      ↓                           │
   │ Resolve URLs       (Fast)       │
   │      ↓                           │
   │ Serialize JSON     (Fast)       │
   │      ↓                           │
   │ Send Response      (Fast)       │
   └─────────────────────────────────┘
   Time: < 50ms

Total API Response Time: < 300ms (p95)
```

---

**Document Version**: 1.0
**Last Updated**: October 9, 2025
**Format**: ASCII Diagrams
