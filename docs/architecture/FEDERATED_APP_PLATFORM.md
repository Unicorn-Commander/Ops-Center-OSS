# Federated App Platform - Implementation Summary

**Date**: November 2, 2025
**Status**: ✅ COMPLETED
**Architecture**: Federated app marketplace with centralized management

---

## Vision: AWS Marketplace for UC-Cloud

User subscribes to **unicorncommander.ai**, gets seamless access to apps hosted ANYWHERE:
- Same server
- Different subdomains
- Completely different domains (e.g., `search.centerdeep.online`)

**Centralized**:
- ✅ Authentication (Keycloak SSO)
- ✅ Billing (Lago + Stripe)
- ✅ Subscription management (Ops-Center)

**Federated**:
- ✅ Apps can be hosted anywhere
- ✅ Each app handles its own SSO integration
- ✅ `launch_url` is the source of truth

---

## Implementation Details

### 1. Updated AppsLauncher (`/admin/apps`)

**File**: `src/pages/AppsLauncher.jsx`

**Changes**:
- ✅ Changed API from `/api/v1/extensions/catalog` → `/api/v1/my-apps/authorized`
- ✅ Shows ONLY apps user's subscription tier includes
- ✅ Clean focus on "Launch App" action
- ✅ Added host badge (UC Hosted vs Federated)
- ✅ Empty state with CTA to browse marketplace

**Features**:
```javascript
// API call
const response = await fetch('/api/v1/my-apps/authorized');

// Host badge logic
const getHostBadge = (launch_url) => {
  if (host.includes('unicorncommander.ai')) {
    return { label: 'UC Hosted', icon: <BusinessIcon />, color: 'primary' };
  } else {
    return { label: 'Federated', icon: <PublicIcon />, color: 'secondary' };
  }
};
```

### 2. New AppMarketplace (`/admin/apps/marketplace`)

**File**: `src/pages/AppMarketplace.jsx` (NEW)

**Features**:
- ✅ Shows apps NOT in user's current tier
- ✅ Displays pricing for premium apps
- ✅ Shows "Upgrade Required" badge for higher-tier apps
- ✅ Host badge showing where app is hosted
- ✅ Two action types:
  - **Purchase** button for premium apps
  - **Upgrade Tier** button for tier-restricted apps

**API**:
```javascript
const response = await fetch('/api/v1/my-apps/marketplace');
```

**Response includes**:
- `access_type`: "premium_purchase" or "upgrade_required"
- `price`: Monthly cost for premium apps
- `billing_type`: "monthly" or "yearly"
- `launch_url`: Where app is hosted

### 3. Navigation Updates

**File**: `src/components/Layout.jsx`

**Changes**:
```javascript
// Added ShoppingBagIcon import
import { ShoppingBagIcon } from '@heroicons/react/24/outline';

// Two separate nav items
<NavigationItem name="Apps" href="/admin/apps" icon={CubeIcon} />
<NavigationItem name="Marketplace" href="/admin/apps/marketplace" icon={ShoppingBagIcon} badge="New" />
```

### 4. Router Updates

**File**: `src/App.jsx`

**Changes**:
```javascript
// Changed import
const AppMarketplace = lazy(() => import('./pages/AppMarketplace'));

// Routes
<Route path="apps" element={<AppsLauncher />} />
<Route path="apps/marketplace" element={<AppMarketplace />} />
```

---

## Backend API (Already Exists!)

The backend API was already implemented in `backend/my_apps_api.py`:

### Endpoint 1: `/api/v1/my-apps/authorized`

Returns apps user has access to based on:
- User's subscription tier
- Tier feature mappings in database
- Free apps with no restrictions

**Response**:
```json
[
  {
    "id": 1,
    "name": "Open-WebUI",
    "slug": "open-webui",
    "description": "AI-powered chat interface",
    "icon_url": "/assets/openwebui.png",
    "launch_url": "https://chat.unicorncommander.ai",
    "category": "ai-services",
    "feature_key": "open_webui_access",
    "access_type": "tier_included"
  }
]
```

### Endpoint 2: `/api/v1/my-apps/marketplace`

Returns apps user does NOT have access to:
- Premium apps available for purchase
- Apps requiring tier upgrade

**Response**:
```json
[
  {
    "id": 2,
    "name": "Center-Deep Pro",
    "slug": "center-deep",
    "description": "AI-powered metasearch",
    "icon_url": "/assets/centerdeep.png",
    "launch_url": "https://search.centerdeep.online",
    "category": "search",
    "feature_key": "center_deep_access",
    "access_type": "upgrade_required",
    "price": 19.00,
    "billing_type": "monthly"
  }
]
```

---

## Federated Architecture in Action

### Example 1: UC-Hosted App (Open-WebUI)

```json
{
  "name": "Open-WebUI",
  "launch_url": "https://chat.unicorncommander.ai",
  "badge": "UC Hosted"
}
```

**Flow**:
1. User clicks "Launch App"
2. Opens `https://chat.unicorncommander.ai` in new tab
3. Open-WebUI handles SSO via shared Keycloak
4. User is automatically logged in (same session domain)

### Example 2: Federated App (Center-Deep)

```json
{
  "name": "Center-Deep Pro",
  "launch_url": "https://search.centerdeep.online",
  "badge": "Federated Service"
}
```

**Flow**:
1. User clicks "Launch App"
2. Opens `https://search.centerdeep.online` in new tab
3. Center-Deep has its own Keycloak instance
4. Center-Deep's Keycloak federates with UC Keycloak
5. User logs in once, works everywhere

### Example 3: Third-Party App (Hypothetical)

```json
{
  "name": "Awesome SaaS Tool",
  "launch_url": "https://awesome-tool.io/sso/unicorn",
  "badge": "Federated Service"
}
```

**Flow**:
1. User clicks "Launch App"
2. Opens `https://awesome-tool.io/sso/unicorn`
3. Awesome Tool redirects to UC Keycloak for auth
4. User authenticates, gets redirected back
5. Session is established in Awesome Tool's domain

---

## Database Schema (Already Configured)

### Tables Used:

1. **`add_ons`** - Available apps
   - `id`, `name`, `slug`, `description`
   - `launch_url` (source of truth)
   - `icon_url`, `category`
   - `feature_key` (links to tier features)
   - `base_price`, `billing_type`

2. **`subscription_tiers`** - User tiers
   - `id`, `tier_code` (trial, starter, professional, enterprise)
   - `tier_name`, `monthly_price`

3. **`tier_features`** - Feature mapping
   - `tier_id`, `feature_key`, `enabled`
   - Maps which features each tier includes

4. **`user_add_ons`** - Individual purchases (future)
   - User-specific app purchases outside their tier

---

## User Experience Flow

### Scenario 1: User on Starter Tier

**Apps Dashboard** (`/admin/apps`):
- ✅ Shows: Open-WebUI, Basic Analytics (tier-included)
- ❌ Doesn't show: Center-Deep, Brigade (higher tiers)

**Marketplace** (`/admin/apps/marketplace`):
- Shows Center-Deep with "Upgrade to Professional - $49/mo"
- Shows Brigade with "Upgrade to Enterprise - $99/mo"

### Scenario 2: User on Professional Tier

**Apps Dashboard**:
- ✅ Shows: Open-WebUI, Analytics, Center-Deep, TTS, STT
- Badge shows "UC Hosted" for Open-WebUI
- Badge shows "Federated Service" for Center-Deep (different domain)

**Marketplace**:
- Shows Brigade with "Upgrade to Enterprise - $99/mo"
- Shows premium add-ons with "Purchase $19/mo" button

### Scenario 3: User on Enterprise Tier

**Apps Dashboard**:
- ✅ Shows ALL tier-included apps
- Clean, focused interface
- One-click launch to any service

**Marketplace**:
- Shows only premium add-ons (no tier upgrades needed)
- "You have access to all tier-based apps!"

---

## Key Benefits

### 1. **True Federation**
- Apps can be hosted ANYWHERE
- `launch_url` is the single source of truth
- No lock-in to UC infrastructure

### 2. **Centralized Management**
- One subscription at unicorncommander.ai
- One billing relationship (Lago + Stripe)
- One SSO identity (Keycloak)

### 3. **Seamless UX**
- User doesn't care where apps are hosted
- Click app card → App opens (SSO automatic)
- Badge shows hosting type (optional)

### 4. **Flexible Business Model**
- Tier-based bundles (Starter, Pro, Enterprise)
- Individual app purchases
- Third-party integrations

### 5. **Developer-Friendly**
- Add new apps by:
  1. Insert row in `add_ons` table
  2. Set `launch_url` to wherever app is hosted
  3. Configure SSO in app's Keycloak
  4. Done!

---

## Files Modified

### Frontend (4 files):
1. ✅ `src/pages/AppsLauncher.jsx` - Updated to use tier-filtered API
2. ✅ `src/pages/AppMarketplace.jsx` - NEW marketplace page
3. ✅ `src/components/Layout.jsx` - Added Marketplace nav item
4. ✅ `src/App.jsx` - Added AppMarketplace route

### Backend (0 files):
- ✅ API already existed in `backend/my_apps_api.py`
- ✅ Database schema already configured
- ✅ Tier filtering logic already implemented

---

## Testing Checklist

### Manual Testing:

1. **Apps Dashboard** (`/admin/apps`):
   - [ ] Page loads without errors
   - [ ] Shows only tier-included apps
   - [ ] Host badge displays correctly
   - [ ] Click app card → Opens in new tab
   - [ ] Empty state shows when no apps

2. **Marketplace** (`/admin/apps/marketplace`):
   - [ ] Page loads without errors
   - [ ] Shows apps NOT in user's tier
   - [ ] Pricing displays correctly
   - [ ] "Purchase" button for premium apps
   - [ ] "Upgrade Tier" button for restricted apps
   - [ ] Host badge displays

3. **Navigation**:
   - [ ] "Apps" nav item goes to `/admin/apps`
   - [ ] "Marketplace" nav item goes to `/admin/apps/marketplace`
   - [ ] Both items visible in sidebar

### API Testing:

```bash
# Test authorized apps
curl http://localhost:8084/api/v1/my-apps/authorized

# Test marketplace
curl http://localhost:8084/api/v1/my-apps/marketplace
```

---

## Next Steps (Future Enhancements)

### Phase 2: Purchase Flow
- [ ] Implement "Purchase" button logic
- [ ] Create checkout flow for individual apps
- [ ] Add `user_add_ons` table population
- [ ] Show purchased apps in Apps Dashboard

### Phase 3: App Management
- [ ] Admin interface to add/edit apps
- [ ] Upload app icons
- [ ] Configure tier availability
- [ ] Set pricing

### Phase 4: Analytics
- [ ] Track app launches
- [ ] Popular apps dashboard
- [ ] Revenue per app
- [ ] User engagement metrics

---

## Technical Notes

### SSO Architecture

**Ops-Center** doesn't handle SSO for federated apps. Each app is responsible for:
1. Configuring OIDC client in Keycloak
2. Handling OAuth2 redirect flow
3. Validating JWT tokens
4. Creating local sessions

**Ops-Center** provides:
- Central Keycloak identity provider
- User subscription tier in JWT claims
- Seamless navigation between apps

### launch_url Format

Supports any valid URL:
```javascript
// Same domain
"launch_url": "https://unicorncommander.ai/admin/services"

// Different subdomain
"launch_url": "https://chat.unicorncommander.ai"

// Different domain
"launch_url": "https://search.centerdeep.online"

// Third-party with SSO path
"launch_url": "https://external-app.com/sso/login?provider=unicorn"
```

### Tier Filtering Logic

```sql
-- Get user's tier features
SELECT feature_key FROM tier_features
WHERE tier_id = (
  SELECT id FROM subscription_tiers
  WHERE tier_code = 'professional'
) AND enabled = TRUE;

-- Filter apps
SELECT * FROM add_ons
WHERE feature_key IN (user_features)
  AND is_active = TRUE
  AND launch_url IS NOT NULL;
```

---

## Success Metrics

After deployment, we should see:
- ✅ Clean separation: Apps dashboard vs Marketplace
- ✅ Badge system showing federated architecture
- ✅ One-click app launches
- ✅ Clear upgrade paths for users
- ✅ Seamless cross-domain navigation

**Example Federation**:
- User at `unicorncommander.ai` clicks "Center-Deep"
- Opens `search.centerdeep.online` in new tab
- Already authenticated via federated Keycloak
- NO re-login required

This is the AWS Marketplace model working in UC-Cloud! 🎉

---

## Documentation Created

- ✅ `FEDERATED_APP_PLATFORM.md` - This document
- ✅ Code comments in all modified files
- ✅ API endpoint documentation in backend

**Status**: Ready for frontend build and deployment!
