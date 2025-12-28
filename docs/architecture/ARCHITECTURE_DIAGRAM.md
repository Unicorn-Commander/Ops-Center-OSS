# Federated App Platform Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        User's Browser                                    │
│                  https://your-domain.com                            │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Ops-Center Dashboard                             │
│                     /admin/apps (Apps Launcher)                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │ Open-WebUI │  │Center-Deep │  │  Bolt.DIY  │  │  Brigade   │       │
│  │  [UC Host] │  │  [UC Host] │  │  [UC Host] │  │  [UC Host] │       │
│  └────────────┘  └────────────┘  └────────────┘  └────────────┘       │
│                                                                          │
│                  /admin/apps/marketplace                                │
│  ┌────────────────────────────────────────────────────────────┐        │
│  │                  Presenton                                  │        │
│  │              [Premium Purchase]                             │        │
│  │            💰 Purchase Button                               │        │
│  └────────────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
        ┌─────────────────────┐   ┌──────────────────┐
        │   Backend APIs       │   │   Keycloak SSO   │
        │  /api/v1/my-apps/    │   │   (uchub realm)  │
        │   - authorized       │   │                  │
        │   - marketplace      │   │  Identity Flows  │
        └─────────────────────┘   └──────────────────┘
                    │
                    ▼
        ┌─────────────────────┐
        │   PostgreSQL DB      │
        │                      │
        │  Tables:             │
        │  - add_ons           │
        │  - subscription_tiers│
        │  - tier_features     │
        │  - user_add_ons      │
        └─────────────────────┘
```

---

## Federated Service Flow

### Same Domain App (Open-WebUI)

```
User at your-domain.com
         │
         ├─ Click "Open-WebUI"
         │
         ▼
  Opens: chat.your-domain.com
         │
         ├─ Keycloak session check
         │  (same domain .your-domain.com)
         │
         ▼
  ✅ Auto-authenticated
  User lands in Open-WebUI chat
```

### Federated Domain App (Center-Deep)

```
User at your-domain.com
         │
         ├─ Click "Center-Deep"
         │
         ▼
  Opens: search.centerdeep.online  ← DIFFERENT DOMAIN!
         │
         ├─ Center-Deep Keycloak checks UC Keycloak
         │  (OIDC Federation)
         │
         ├─ OAuth2 redirect flow
         │  1. Redirect to auth.your-domain.com
         │  2. User already has session
         │  3. Redirect back with token
         │
         ▼
  ✅ Auto-authenticated
  User lands in Center-Deep search
```

### Third-Party App (Hypothetical)

```
User at your-domain.com
         │
         ├─ Click "External Tool"
         │
         ▼
  Opens: awesome-tool.com/sso/unicorn  ← THIRD-PARTY!
         │
         ├─ Redirects to auth.your-domain.com
         │
         ├─ User authenticates (if not already)
         │
         ├─ UC Keycloak returns OAuth2 token
         │
         ├─ Redirect back to awesome-tool.com
         │
         ▼
  ✅ Authenticated
  User lands in External Tool
```

---

## Data Flow: Tier Filtering

```
┌─────────────────────────────────────────────────────────────┐
│  User Login → Keycloak Session                              │
│  JWT Token contains: user_id, tier_code, roles              │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  User navigates to /admin/apps                              │
│  Frontend calls: GET /api/v1/my-apps/authorized             │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend: my_apps_api.py                                    │
│  1. Extract user tier from session                          │
│  2. Query: SELECT feature_key FROM tier_features            │
│     WHERE tier_id = (SELECT id FROM subscription_tiers      │
│                      WHERE tier_code = 'managed')           │
│     AND enabled = TRUE                                      │
│                                                             │
│  3. Query: SELECT * FROM add_ons                            │
│     WHERE feature_key IN (user_features)                    │
│     AND is_active = TRUE                                    │
│     AND launch_url IS NOT NULL                              │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Response: JSON Array                                       │
│  [                                                          │
│    {                                                        │
│      "id": 16,                                              │
│      "name": "Open-WebUI",                                  │
│      "launch_url": "https://chat.your-domain.com",     │
│      "feature_key": "chat_access",                         │
│      "access_type": "tier_included"                        │
│    },                                                       │
│    { ... more apps ... }                                    │
│  ]                                                          │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Frontend: AppsLauncher.jsx                                 │
│  1. Render app cards                                        │
│  2. Add host badges (UC vs Federated)                       │
│  3. Handle click → window.open(app.launch_url)              │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Schema Relationships

```
┌──────────────────────┐
│ subscription_tiers   │
│──────────────────────│
│ id (PK)              │◄───┐
│ tier_code            │    │
│ tier_name            │    │
│ monthly_price        │    │
└──────────────────────┘    │
                            │
                            │
┌──────────────────────┐    │
│   tier_features      │    │
│──────────────────────│    │
│ tier_id (FK) ────────┼────┘
│ feature_key          │◄───┐
│ enabled              │    │
└──────────────────────┘    │
                            │
                            │
┌──────────────────────┐    │
│     add_ons          │    │
│──────────────────────│    │
│ id (PK)              │    │
│ name                 │    │
│ slug                 │    │
│ description          │    │
│ icon_url             │    │
│ launch_url ★         │    │ ← SOURCE OF TRUTH!
│ category             │    │
│ feature_key ─────────┼────┘
│ base_price           │
│ billing_type         │
│ is_active            │
└──────────────────────┘


Example Data:
─────────────
add_ons WHERE id = 17:
  name: "Center-Deep Pro"
  launch_url: "https://search.your-domain.com"  ← Can be ANY URL!
  feature_key: "search_enabled"

tier_features WHERE feature_key = "search_enabled":
  tier_id: 3 (Managed)
  enabled: TRUE

Result: User on "Managed" tier → Gets Center-Deep Pro access
```

---

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        App.jsx                               │
│                  (React Router)                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Route: /admin/apps                                  │   │
│  │  Component: <AppsLauncher />                         │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Route: /admin/apps/marketplace                      │   │
│  │  Component: <AppMarketplace />                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│ AppsLauncher.jsx │          │AppMarketplace.jsx│
│──────────────────│          │──────────────────│
│ State:           │          │ State:           │
│ - apps[]         │          │ - apps[]         │
│ - loading        │          │ - loading        │
│ - error          │          │ - error          │
│                  │          │                  │
│ API:             │          │ API:             │
│ GET /api/v1/     │          │ GET /api/v1/     │
│  my-apps/        │          │  my-apps/        │
│  authorized      │          │  marketplace     │
│                  │          │                  │
│ Renders:         │          │ Renders:         │
│ - App cards      │          │ - App cards      │
│ - Host badges    │          │ - Pricing info   │
│ - Launch buttons │          │ - Purchase CTAs  │
└──────────────────┘          └──────────────────┘
```

---

## Navigation Structure

```
┌─────────────────────────────────────────────────────────────┐
│                      Layout.jsx                              │
│                    (Left Sidebar)                            │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  🏠 Dashboard                                        │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  📦 Apps                                             │   │
│  │     → /admin/apps                                    │   │
│  │     (Tier-filtered apps launcher)                    │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  🛍️ Marketplace [New]                               │   │
│  │     → /admin/apps/marketplace                        │   │
│  │     (Browse & purchase apps)                         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  👤 Account                                          │   │
│  │  💳 Subscription                                     │   │
│  │  🏢 Organization                                     │   │
│  │  ...                                                 │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Host Badge Logic

```javascript
// In AppsLauncher.jsx & AppMarketplace.jsx

const getHostBadge = (launch_url) => {
  try {
    const url = new URL(launch_url);
    const host = url.hostname;

    // UC-hosted apps
    if (host.includes('your-domain.com')) {
      return {
        label: 'UC Hosted',
        icon: <BusinessIcon />,
        color: 'primary'
      };
    }

    // Federated apps (different domain)
    else {
      return {
        label: 'Federated',
        icon: <PublicIcon />,
        color: 'secondary'
      };
    }
  } catch (e) {
    // Fallback for invalid URLs
    return {
      label: 'External',
      icon: <PublicIcon />,
      color: 'default'
    };
  }
};

// Examples:
// chat.your-domain.com → "UC Hosted" (blue)
// search.centerdeep.online → "Federated" (purple)
// awesome-tool.com         → "Federated" (purple)
```

---

## Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                   Authentication Flow                        │
└─────────────────────────────────────────────────────────────┘

User Login → Keycloak (uchub realm)
              │
              ├─ JWT Token issued
              │  Claims: user_id, email, tier_code, roles
              │
              ├─ Session cookie set
              │  Domain: .your-domain.com
              │
              └─ User navigates Ops-Center
                    │
                    ├─ Click "Open-WebUI"
                    │  → Opens chat.your-domain.com
                    │  → Same session domain → Auto-authenticated
                    │
                    ├─ Click "Center-Deep"
                    │  → Opens search.centerdeep.online
                    │  → Different domain
                    │  → OIDC Federation:
                    │     1. Check local session → None
                    │     2. Redirect to auth.your-domain.com
                    │     3. UC Keycloak validates → Already logged in
                    │     4. Return token to Center-Deep
                    │     5. Center-Deep creates local session
                    │  → User authenticated
                    │
                    └─ Click "External Tool"
                       → Opens awesome-tool.com/sso
                       → Standard OAuth2 flow
                       → Redirects to UC Keycloak
                       → Token exchange
                       → User authenticated

Security Features:
- ✅ JWT tokens signed by Keycloak
- ✅ Session cookies HTTP-only, secure
- ✅ CORS policies enforced
- ✅ OIDC standard compliance
- ✅ Token refresh handled
```

---

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Docker Infrastructure                          │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────┐
│  ops-center-direct       │ Port 8084
│  (FastAPI + React)       │
│  - Backend: /api/v1/     │
│  - Frontend: /admin/     │
└──────────────────────────┘
         │
         ├── Networks: unicorn-network, web, uchub-network
         │
         └── Volumes:
             - public/     (Built React app)
             - backend/    (Python FastAPI)

┌──────────────────────────┐
│  uchub-keycloak          │ Port 8080
│  (Authentication)        │
│  Realm: uchub            │
│  Client: ops-center      │
└──────────────────────────┘

┌──────────────────────────┐
│  unicorn-postgresql      │ Port 5432
│  Database: unicorn_db    │
│  Tables: add_ons, etc.   │
└──────────────────────────┘

┌──────────────────────────┐
│  traefik                 │ Ports 80, 443
│  (Reverse Proxy)         │
│  SSL/TLS termination     │
│  Routes:                 │
│  - your-domain.com   │
│  - chat.unicorncommander │
│  - search.centerdeep     │
└──────────────────────────┘
```

---

## Build Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    Build Process                             │
└─────────────────────────────────────────────────────────────┘

Source Files (src/):
- AppsLauncher.jsx
- AppMarketplace.jsx
- Layout.jsx
- App.jsx
    │
    ├─ npm run build
    │   │
    │   └─ Vite Build:
    │       - Bundle JavaScript
    │       - Process JSX → JS
    │       - Optimize assets
    │       - Tree shake unused code
    │       - Minify & gzip
    │
    ├─ Build Output (dist/):
    │   ├─ index.html
    │   ├─ assets/
    │   │   ├─ AppsLauncher-CPt5glaO.js (2.99 kB)
    │   │   ├─ AppMarketplace-DW30pHq8.js (3.75 kB)
    │   │   └─ ... (all other chunks)
    │   ├─ manifest.webmanifest
    │   └─ sw.js (Service Worker)
    │
    ├─ Deploy:
    │   cp -r dist/* public/
    │
    └─ Restart Container:
        docker restart ops-center-direct

Result:
✅ Frontend served from public/
✅ Backend serves static files + API
✅ Users access via https://your-domain.com
```

---

## Future Expansion

```
┌─────────────────────────────────────────────────────────────┐
│             Phase 2: Purchase Flow                           │
└─────────────────────────────────────────────────────────────┘

User clicks "Purchase" on Presenton
    │
    ├─ Navigate to Stripe Checkout
    │   - Create checkout session
    │   - Pass user_id, app_id, price
    │
    ├─ User completes payment
    │
    ├─ Stripe webhook → Ops-Center
    │   - Insert into user_add_ons table
    │   - Grant feature_key to user
    │
    ├─ User returns to Ops-Center
    │
    └─ Presenton now appears in Apps Dashboard
        (moved from Marketplace → My Apps)

┌─────────────────────────────────────────────────────────────┐
│             Phase 3: Third-Party Integrations                │
└─────────────────────────────────────────────────────────────┘

Add third-party app:
    │
    ├─ Insert into add_ons:
    │   name: "Awesome SaaS Tool"
    │   launch_url: "https://awesome-tool.com/sso/unicorn"
    │   feature_key: "awesome_tool_access"
    │
    ├─ Configure OIDC in Awesome Tool:
    │   - Provider: your-domain.com Keycloak
    │   - Client ID: awesome-tool
    │   - Client Secret: <generated>
    │   - Redirect URI: awesome-tool.com/callback
    │
    └─ User clicks app in Ops-Center
        → Redirects to UC Keycloak
        → OAuth2 flow completes
        → User lands in Awesome Tool
        → Authenticated!
```

---

## Success Criteria ✅

1. ✅ **Federation Works**
   - Apps can be hosted anywhere
   - launch_url determines location
   - SSO works across domains

2. ✅ **Tier Filtering Works**
   - User sees only their tier's apps
   - Marketplace shows upgrade options
   - Premium apps purchasable (UI ready)

3. ✅ **UX is Seamless**
   - One-click launch
   - Host badges visible
   - Clean, focused interface
   - No confusion about hosting

4. ✅ **Architecture is Scalable**
   - Easy to add new apps
   - Support for any domain
   - Third-party integration ready
   - Flexible business models

5. ✅ **Implementation is Clean**
   - Minimal code changes
   - Reused existing APIs
   - Clear separation of concerns
   - Well-documented

---

**Status**: FULLY OPERATIONAL 🎉
**Architecture**: PROVEN 💪
**Federation**: WORKING ✨

This is the AWS Marketplace model, live in UC-Cloud!
