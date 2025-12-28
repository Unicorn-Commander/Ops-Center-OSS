# Apps Launcher Implementation

**Created**: November 2, 2025
**Status**: ✅ Complete and Deployed

## Overview

Implemented a super simple apps launcher for the Ops-Center dashboard that displays a clean grid of app tiles (like an iOS home screen). Users can click any tile to launch the app in a new tab.

## What Was Built

### 1. New Frontend Component

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/pages/AppsLauncher.jsx`

**Features**:
- Fetches apps from existing API: `GET /api/v1/extensions/catalog`
- Displays apps as Material-UI cards in a responsive grid
- Each tile shows:
  - App icon (or default icon if missing)
  - App name
  - App description (truncated to 80 chars)
  - "Launch" button
- Click anywhere on tile to open app in new tab
- Hover effect with elevation and border highlight
- Responsive grid layout:
  - Mobile (xs): 1 column
  - Tablet (sm): 2 columns
  - Desktop (md): 3 columns
  - Large desktop (lg): 4 columns
- Loading state with spinner
- Error handling with alert

**No Complicated Logic**:
- ❌ No tier restrictions
- ❌ No activation tracking
- ❌ No purchase flows
- ✅ Just shows apps and launches them

### 2. Database Changes

**Added Column**: `launch_url` to `add_ons` table

```sql
ALTER TABLE add_ons ADD COLUMN IF NOT EXISTS launch_url VARCHAR(500);
```

**Populated Launch URLs**:
```sql
UPDATE add_ons SET launch_url = 'https://chat.your-domain.com' WHERE name = 'Open-WebUI';
UPDATE add_ons SET launch_url = 'https://search.your-domain.com' WHERE name = 'Center-Deep Pro';
UPDATE add_ons SET launch_url = 'https://presentations.your-domain.com' WHERE name = 'Presenton';
UPDATE add_ons SET launch_url = 'https://bolt.your-domain.com' WHERE name = 'Bolt.DIY';
UPDATE add_ons SET launch_url = 'https://brigade.your-domain.com' WHERE name = 'Unicorn Brigade';
```

### 3. Routing Changes

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/src/App.jsx`

**Changes**:
1. Added lazy import for `AppsLauncher`
2. Changed default route from `/admin/` (DashboardPro) to AppsLauncher
3. Moved DashboardPro to `/admin/dashboard` (still accessible)
4. Updated apps route to use AppsLauncher

**New Route Structure**:
```javascript
/admin/                      → AppsLauncher (NEW DEFAULT)
/admin/dashboard             → DashboardPro (legacy)
/admin/apps                  → AppsLauncher
/admin/apps/marketplace      → AppsMarketplace (full marketplace)
/admin/apps/my               → MyApps (user's installed apps)
```

## Current App Catalog

**Active Apps** (7 total, 5 with launch URLs):

| App | Launch URL | Status |
|-----|-----------|--------|
| Open-WebUI | https://chat.your-domain.com | ✅ Active |
| Center-Deep Pro | https://search.your-domain.com | ✅ Active |
| Presenton | https://presentations.your-domain.com | ✅ Active |
| Bolt.DIY | https://bolt.your-domain.com | ✅ Active |
| Unicorn Brigade | https://brigade.your-domain.com | ✅ Active |
| Unicorn Amanuensis | (No URL yet) | ⚠️ Hidden (no launch_url) |
| Unicorn Orator | (No URL yet) | ⚠️ Hidden (no launch_url) |

**Note**: Apps without `launch_url` are automatically hidden by the filter: `app.is_active && app.launch_url`

## API Endpoint Used

**Endpoint**: `GET /api/v1/extensions/catalog`

**File**: `/home/muut/Production/UC-Cloud/services/ops-center/backend/extensions_catalog_api.py`

**Response** (example):
```json
[
  {
    "id": 16,
    "name": "Open-WebUI",
    "description": "Full-featured AI chat interface with multi-model support",
    "category": "AI & Chat",
    "base_price": 0.0,
    "billing_type": "monthly",
    "icon_url": "/assets/services/openwebui-icon.png",
    "is_active": true,
    "launch_url": "https://chat.your-domain.com",
    "features": {...},
    "created_at": "2025-11-01T22:45:34.478623"
  }
]
```

**Filter Parameters** (optional):
- `category` - Filter by category
- `search` - Search in name and description
- `limit` - Max results (default 20, max 100)
- `offset` - Pagination offset

## User Experience

### Login Flow
1. User logs in via Keycloak SSO
2. Redirected to `/admin/` (Apps Launcher)
3. Sees grid of available apps
4. Clicks app tile → Opens in new tab

### Navigation
- Apps Launcher is the new "home page" after login
- Dashboard still accessible at `/admin/dashboard`
- Apps also accessible at `/admin/apps`

## Technical Details

### Component Structure

```jsx
AppsLauncher
├── Loading State (CircularProgress)
├── Error State (Alert)
└── Apps Grid (Material-UI Grid)
    └── App Tile (Card)
        ├── Icon Box
        │   └── CardMedia (app icon) or LaunchIcon (fallback)
        ├── CardContent
        │   ├── App Name (Typography h6)
        │   ├── Description (Typography body2, truncated)
        │   └── Launch Button (Button with LaunchIcon)
        └── onClick handler → window.open(launch_url)
```

### Styling

**Card Hover Effect**:
```css
&:hover {
  transform: translateY(-8px);
  boxShadow: 6;
  borderColor: primary.main;
  borderWidth: 2;
}
```

**Icon Box**:
- Gray background (`background.default`)
- Centered content
- Fixed height: 120px
- Icon size: 80x80px

**Responsive Grid**:
- xs (mobile): 12/12 = 1 column
- sm (tablet): 6/12 = 2 columns
- md (desktop): 4/12 = 3 columns
- lg (large): 3/12 = 4 columns

## Deployment

### Files Modified
1. `src/pages/AppsLauncher.jsx` - NEW
2. `src/App.jsx` - Updated routes
3. Database: `add_ons` table - Added `launch_url` column

### Build & Deploy Process
```bash
# Build frontend
npm run build

# Copy to public/
cp -r dist/* public/

# Restart container
docker restart ops-center-direct

# Verify
docker ps | grep ops-center
docker logs ops-center-direct --tail 20
```

### Verification Commands

```bash
# Check database
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT name, launch_url, is_active FROM add_ons WHERE is_active = true;"

# Test API
curl http://localhost:8084/api/v1/extensions/catalog | jq

# Access UI
# Navigate to: https://your-domain.com/admin/
```

## Future Enhancements (Optional)

1. **Add Launch URLs for Missing Apps**:
   - Unicorn Amanuensis: `https://stt.your-domain.com`
   - Unicorn Orator: `https://tts.your-domain.com`

2. **Category Filters**:
   - Add filter tabs at top (All, AI & Chat, Development, etc.)
   - Use existing `category` field from API

3. **Search Bar**:
   - Add search input to filter apps
   - Use existing `search` parameter from API

4. **App Stats**:
   - Show "Last used" timestamp
   - Display usage count
   - Requires new tracking in backend

5. **Favorites**:
   - Star/unstar apps
   - Show favorites first
   - Requires new user_favorites table

6. **App Details Modal**:
   - Click info icon for full details
   - Show all features, screenshots, etc.
   - Alternative to launching immediately

## Known Limitations

1. **No Tier Logic**: All apps shown regardless of user's subscription tier
2. **No Purchase Flow**: No way to activate paid apps from this page
3. **No Usage Tracking**: Launches not tracked in analytics
4. **Static Icons**: Icons from database, no dynamic loading from apps
5. **No App Status**: Doesn't check if app service is actually running

**Note**: These are intentional simplifications per the requirements. Use `/admin/apps/marketplace` for the full-featured marketplace with purchasing, tiers, etc.

## Files Reference

### Frontend
- `/home/muut/Production/UC-Cloud/services/ops-center/src/pages/AppsLauncher.jsx` - Main component
- `/home/muut/Production/UC-Cloud/services/ops-center/src/App.jsx` - Routing config

### Backend
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/extensions_catalog_api.py` - API endpoint
- `/home/muut/Production/UC-Cloud/services/ops-center/backend/server.py` - Router registration

### Database
- Table: `add_ons` (PostgreSQL `unicorn_db`)
- Migration: Column `launch_url VARCHAR(500)` added

---

**Summary**: Simple, clean, fast app launcher that gets users to their apps in 1 click. No bloat, no complexity, just works.
