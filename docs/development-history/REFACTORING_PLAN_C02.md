# Refactoring Plan C02: CloudflareDNS Component Breakdown

**Date**: October 25, 2025
**Component**: `src/pages/network/CloudflareDNS.jsx`
**Current Size**: 1,480 lines
**Target**: 20-25 modular components
**Pattern Reference**: C01 (AIModelManagement) refactoring

---

## Executive Summary

CloudflareDNS.jsx is a **monolithic component** that manages Cloudflare zones, DNS records, and account settings. At 1,480 lines, it's **3x the recommended component size** and a critical blocker for maintainability.

**Goal**: Break into 20+ focused components organized by feature, following the successful C01 pattern.

**Expected Outcome**:
- Main coordinator: <400 lines (73% reduction)
- 20-25 specialized components
- Average component size: <100 lines
- Improved testability, maintainability, and extensibility

---

## Current Architecture Analysis

### State Management (23 useState hooks)

#### Zones Management (5 states)
```javascript
const [zones, setZones] = useState([]);
const [selectedZone, setSelectedZone] = useState(null);
const [loading, setLoading] = useState(true);
const [zoneDetailView, setZoneDetailView] = useState(false);
const [activeTab, setActiveTab] = useState(0);
```

#### DNS Records Management (3 states)
```javascript
const [dnsRecords, setDnsRecords] = useState([]);
const [loadingRecords, setLoadingRecords] = useState(false);
const [selectedRecord, setSelectedRecord] = useState(null);
```

#### Account Info (1 state)
```javascript
const [accountInfo, setAccountInfo] = useState({ zones: {}, rate_limit: {}, features: {} });
```

#### Dialogs (3 states)
```javascript
const [openCreateZone, setOpenCreateZone] = useState(false);
const [openAddRecord, setOpenAddRecord] = useState(false);
const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
const [deleteTarget, setDeleteTarget] = useState(null);
```

#### Pagination & Filtering - Zones (4 states)
```javascript
const [page, setPage] = useState(0);
const [rowsPerPage, setRowsPerPage] = useState(10);
const [searchQuery, setSearchQuery] = useState('');
const [statusFilter, setStatusFilter] = useState('all');
```

#### Pagination & Filtering - DNS Records (4 states)
```javascript
const [recordPage, setRecordPage] = useState(0);
const [recordRowsPerPage, setRecordRowsPerPage] = useState(10);
const [recordSearchQuery, setRecordSearchQuery] = useState('');
const [recordTypeFilter, setRecordTypeFilter] = useState('all');
```

#### Form State (3 states)
```javascript
const [newZone, setNewZone] = useState({ domain: '', jump_start: true, priority: 'normal' });
const [dnsRecord, setDnsRecord] = useState({ type: 'A', name: '', content: '', ttl: 1, proxied: false, priority: 10 });
const [formErrors, setFormErrors] = useState({});
```

#### Notifications (1 state)
```javascript
const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });
```

### Major Feature Sections

1. **Zone List View** (Lines 935-1477)
   - Header card with Cloudflare branding
   - Account info metrics (4 cards)
   - Rate limit warnings
   - Zone creation/refresh actions
   - Search and filter controls
   - Zones table with pagination

2. **Zone Detail View** (Lines 474-932)
   - Zone header with back button
   - 4 tabs: Overview, DNS Records, Nameservers, Settings
   - Tab 0: Overview (zone info + DNS summary)
   - Tab 1: DNS Records (table with CRUD operations)
   - Tab 2: Nameservers (display + copy functionality)
   - Tab 3: Settings (zone config + danger zone)

3. **Modals** (Lines 1174-1459)
   - Create Zone Dialog
   - Add/Edit DNS Record Dialog
   - Delete Confirmation Dialog

4. **Helper Components** (Lines 420-463)
   - StatusBadge component
   - NameserversDisplay component

5. **API Functions** (Lines 143-383)
   - fetchZones()
   - fetchAccountInfo()
   - fetchDnsRecords()
   - handleCreateZone()
   - handleDeleteZone()
   - handleCheckStatus()
   - validateDnsRecord()
   - handleAddDnsRecord()
   - handleDeleteDnsRecord()
   - handleToggleProxy()
   - handleCopyNameservers()
   - handleEditRecord()
   - resetDnsRecordForm()
   - openDeleteConfirmation()
   - showToast()

6. **Filtering & Pagination Logic** (Lines 387-417)
   - Zone filtering and pagination
   - DNS record filtering and pagination

---

## Proposed Component Breakdown (24 components)

### Directory Structure

```
src/components/CloudflareDNS/
├── index.jsx                           # Main coordinator
├── ZoneListView/
│   ├── index.jsx                       # Zone list coordinator
│   ├── ZoneListHeader.jsx              # Header card with branding
│   ├── AccountMetrics.jsx              # 4 metric cards
│   ├── AccountWarnings.jsx             # Rate limit + pending warnings
│   ├── ZoneListToolbar.jsx             # Create/Refresh + Search/Filter
│   ├── ZonesTable.jsx                  # Zones table with pagination
│   └── ZoneTableRow.jsx                # Individual zone row
├── ZoneDetailView/
│   ├── index.jsx                       # Detail view coordinator
│   ├── ZoneDetailHeader.jsx            # Zone name, status, actions
│   ├── ZoneDetailTabs.jsx              # Tab navigation (4 tabs)
│   ├── tabs/
│   │   ├── OverviewTab.jsx             # Zone info + DNS summary
│   │   ├── DNSRecordsTab.jsx           # DNS records table
│   │   ├── NameserversTab.jsx          # Nameservers display
│   │   └── SettingsTab.jsx             # Zone settings + danger zone
├── DNSRecords/
│   ├── DNSRecordsTable.jsx             # DNS records table
│   ├── DNSRecordRow.jsx                # Individual record row
│   ├── DNSRecordToolbar.jsx            # Search/Filter + Add button
│   └── ProxyToggleButton.jsx           # Orange/Grey cloud toggle
├── Modals/
│   ├── CreateZoneModal.jsx             # Create zone dialog
│   ├── AddEditRecordModal.jsx          # Add/Edit DNS record dialog
│   └── DeleteConfirmationModal.jsx     # Delete confirmation (zone/record)
└── Shared/
    ├── StatusBadge.jsx                 # Zone status badge
    ├── NameserversDisplay.jsx          # Nameservers with copy
    ├── Toast.jsx                       # Toast notification wrapper
    └── constants.js                    # Record types, TTL options
```

---

## Component Specifications

### 1. Main Coordinator (index.jsx) - Target: <400 lines

**Responsibilities**:
- State management (all 23 states)
- API calls (fetch functions)
- Event handlers (CRUD operations)
- Coordinate between ZoneListView and ZoneDetailView

**Key Functions**:
- `fetchZones()` - Load zones from API
- `fetchAccountInfo()` - Load account limits
- `fetchDnsRecords(zoneId)` - Load DNS records for zone
- `handleCreateZone()` - Create new zone
- `handleDeleteZone()` - Delete zone
- `handleAddDnsRecord()` - Add/update DNS record
- `handleDeleteDnsRecord()` - Delete DNS record
- `handleToggleProxy()` - Toggle proxy status
- `validateDnsRecord()` - Form validation
- `showToast()` - Show notifications

**Props to Children**: Pass state + handlers via props

---

### 2. ZoneListView/ (6 components, ~400 lines total)

#### 2.1 ZoneListView (index.jsx) - 80 lines

**Responsibilities**:
- Coordinate zone list subcomponents
- Route props from main coordinator
- Handle filtering and pagination logic

**Props**:
- `zones` - Array of zones
- `loading` - Loading state
- `accountInfo` - Account metrics
- `searchQuery`, `setSearchQuery` - Search state
- `statusFilter`, `setStatusFilter` - Filter state
- `page`, `setPage` - Pagination state
- `rowsPerPage`, `setRowsPerPage` - Rows per page
- `onCreateZone`, `onRefresh` - Action handlers
- `onSelectZone` - Zone selection handler
- `onDeleteZone`, `onCheckStatus` - Zone actions
- `currentTheme` - Theme context

**Renders**:
```jsx
<Box>
  <ZoneListHeader currentTheme={currentTheme} />
  <AccountMetrics accountInfo={accountInfo} />
  <AccountWarnings accountInfo={accountInfo} />
  <ZoneListToolbar {...toolbarProps} />
  <ZonesTable {...tableProps} />
</Box>
```

#### 2.2 ZoneListHeader.jsx - 50 lines

**Responsibilities**:
- Display Cloudflare DNS branding header
- Gradient background based on theme

**Props**:
- `currentTheme` - Theme context

**UI**:
- CloudIcon + title
- Gradient card (purple for unicorn, blue for others)

#### 2.3 AccountMetrics.jsx - 80 lines

**Responsibilities**:
- Display 4 metric cards (Total, Active, Pending, Plan)
- Responsive grid layout

**Props**:
- `accountInfo` - Account data object

**Metrics**:
1. Total Zones
2. Active Zones (green)
3. Pending Zones (yellow, with limit)
4. Plan (FREE/PRO)

#### 2.4 AccountWarnings.jsx - 60 lines

**Responsibilities**:
- Display rate limit warning (if >80% used)
- Display pending limit warning (if at limit)

**Props**:
- `accountInfo` - Account data

**Conditions**:
- Rate limit: Show if `rate_limit.percent_used > 80`
- Pending limit: Show if `zones.at_limit === true`

#### 2.5 ZoneListToolbar.jsx - 80 lines

**Responsibilities**:
- Create Zone + Refresh buttons
- Search input
- Status filter dropdown

**Props**:
- `onCreateZone` - Create handler
- `onRefresh` - Refresh handler
- `searchQuery`, `setSearchQuery` - Search state
- `statusFilter`, `setStatusFilter` - Filter state
- `currentTheme` - For gradient button

#### 2.6 ZonesTable.jsx - 100 lines

**Responsibilities**:
- Table with headers
- Map zones to ZoneTableRow components
- Pagination controls
- Empty state handling

**Props**:
- `zones` - Filtered & paginated zones
- `page`, `onPageChange` - Pagination
- `rowsPerPage`, `onRowsPerPageChange` - Rows
- `totalCount` - For pagination
- `onSelectZone` - Click handler
- `onDeleteZone`, `onCheckStatus` - Actions

#### 2.7 ZoneTableRow.jsx - 60 lines

**Responsibilities**:
- Display single zone row
- Click to open detail view
- Action buttons (Check Status, Delete)

**Props**:
- `zone` - Zone object
- `onSelect` - Row click handler
- `onDelete` - Delete handler
- `onCheckStatus` - Check status handler

**Columns**:
1. Domain (name + zone_id)
2. Status (StatusBadge)
3. Nameservers (NameserversDisplay)
4. Created date
5. Actions (icons)

---

### 3. ZoneDetailView/ (8 components, ~500 lines total)

#### 3.1 ZoneDetailView (index.jsx) - 100 lines

**Responsibilities**:
- Coordinate detail view subcomponents
- Tab state management
- Route props to tabs

**Props**:
- `zone` - Selected zone object
- `onBack` - Back to list handler
- `dnsRecords` - DNS records array
- `loadingRecords` - Loading state
- All DNS record handlers
- `onDeleteZone`, `onCheckStatus` - Zone actions

**Renders**:
```jsx
<Box>
  <ZoneDetailHeader {...headerProps} />
  <ZoneDetailTabs activeTab={activeTab} onChange={setActiveTab} />
  {activeTab === 0 && <OverviewTab {...overviewProps} />}
  {activeTab === 1 && <DNSRecordsTab {...dnsProps} />}
  {activeTab === 2 && <NameserversTab {...nsProps} />}
  {activeTab === 3 && <SettingsTab {...settingsProps} />}
</Box>
```

#### 3.2 ZoneDetailHeader.jsx - 80 lines

**Responsibilities**:
- Back button
- Zone name + domain icon
- Status badge + plan chip
- Action buttons (Check Status, Delete Zone)

**Props**:
- `zone` - Zone object
- `onBack` - Back handler
- `onDelete` - Delete handler
- `onCheckStatus` - Check status handler

#### 3.3 ZoneDetailTabs.jsx - 40 lines

**Responsibilities**:
- Tab navigation UI (4 tabs)
- Icons for each tab

**Props**:
- `activeTab` - Current tab index
- `onChange` - Tab change handler

**Tabs**:
1. Overview (InfoIcon)
2. DNS Records (DnsIcon)
3. Nameservers (StorageIcon)
4. Settings (SettingsIcon)

#### 3.4 OverviewTab.jsx - 120 lines

**Responsibilities**:
- Zone information card (ID, status, plan, dates)
- DNS records summary card (total, proxied, DNS-only)
- Action required alert

**Props**:
- `zone` - Zone object
- `dnsRecords` - DNS records array

**Layout**:
- 2 columns: Zone Info + DNS Summary
- Full-width alert below

#### 3.5 DNSRecordsTab.jsx - 120 lines

**Responsibilities**:
- DNS record toolbar (search, filter, add button)
- DNS records table
- Loading state

**Props**:
- `zone` - Zone object
- `dnsRecords` - Records array
- `loadingRecords` - Loading state
- `onAddRecord` - Add handler
- `onEditRecord` - Edit handler
- `onDeleteRecord` - Delete handler
- `onToggleProxy` - Proxy toggle handler
- Search/filter state + handlers
- `currentTheme` - For gradient button

**Renders**:
```jsx
<Box>
  <DNSRecordToolbar {...toolbarProps} />
  {loadingRecords ? <CircularProgress /> : <DNSRecordsTable {...tableProps} />}
</Box>
```

#### 3.6 NameserversTab.jsx - 120 lines

**Responsibilities**:
- Nameservers card (list + copy button)
- Update instructions card (4-step guide)
- Propagation status alert

**Props**:
- `zone` - Zone object
- `onCopyNameservers` - Copy handler

**Layout**:
- 2 columns: Nameservers + Instructions
- Full-width alert below

#### 3.7 SettingsTab.jsx - 100 lines

**Responsibilities**:
- Zone settings card (disabled switches for now)
- Danger zone card (delete button)
- "Coming soon" alert

**Props**:
- `zone` - Zone object
- `onDeleteZone` - Delete handler

**Settings** (all disabled for now):
- Development Mode
- Auto HTTPS Rewrites
- Always Use HTTPS

---

### 4. DNSRecords/ (4 components, ~250 lines total)

#### 4.1 DNSRecordsTable.jsx - 100 lines

**Responsibilities**:
- Table with headers
- Map records to DNSRecordRow
- Pagination controls
- Empty state

**Props**:
- `records` - Filtered & paginated records
- `page`, `onPageChange` - Pagination
- `rowsPerPage`, `onRowsPerPageChange` - Rows
- `totalCount` - For pagination
- `onEditRecord`, `onDeleteRecord` - Actions
- `onToggleProxy` - Proxy toggle
- `searchQuery`, `typeFilter` - For empty state

#### 4.2 DNSRecordRow.jsx - 70 lines

**Responsibilities**:
- Display single DNS record row
- Type chip
- Name, content, TTL display
- Proxy toggle button
- Edit/Delete actions

**Props**:
- `record` - DNS record object
- `onEdit` - Edit handler
- `onDelete` - Delete handler
- `onToggleProxy` - Proxy toggle handler

**Columns**:
1. Type (chip)
2. Name (monospace)
3. Content (monospace, with priority if MX/SRV)
4. TTL (Auto or seconds)
5. Proxy (toggle button)
6. Actions (Edit, Delete icons)

#### 4.3 DNSRecordToolbar.jsx - 60 lines

**Responsibilities**:
- Search input
- Record type filter dropdown
- Add Record button

**Props**:
- `searchQuery`, `setSearchQuery` - Search state
- `typeFilter`, `setTypeFilter` - Filter state
- `onAddRecord` - Add handler
- `currentTheme` - For gradient button

#### 4.4 ProxyToggleButton.jsx - 40 lines

**Responsibilities**:
- Display proxy status icon (orange/grey cloud)
- Toggle on click (for A, AAAA, CNAME only)
- Tooltip with status

**Props**:
- `record` - DNS record object
- `onToggle` - Toggle handler

**Icons**:
- ProxiedIcon (orange) - Proxied
- DNSOnlyIcon (grey) - DNS Only
- "-" for non-proxiable types (MX, TXT, NS, SRV, CAA)

---

### 5. Modals/ (3 components, ~300 lines total)

#### 5.1 CreateZoneModal.jsx - 120 lines

**Responsibilities**:
- Dialog for creating new zone
- Domain input field
- Priority dropdown
- Jump Start toggle
- Queue warning (if at limit)

**Props**:
- `open` - Modal open state
- `onClose` - Close handler
- `onSubmit` - Create handler
- `newZone`, `setNewZone` - Form state
- `accountInfo` - For queue warning

**Form Fields**:
1. Domain Name (text input)
2. Priority (dropdown: critical, high, normal, low)
3. Jump Start (switch)

**Validation**:
- Domain required
- Show queue warning if `accountInfo.zones.at_limit`

#### 5.2 AddEditRecordModal.jsx - 140 lines

**Responsibilities**:
- Dialog for adding/editing DNS record
- Dynamic form based on record type
- Validation

**Props**:
- `open` - Modal open state
- `onClose` - Close handler
- `onSubmit` - Add/Update handler
- `dnsRecord`, `setDnsRecord` - Form state
- `formErrors` - Validation errors
- `selectedRecord` - For edit mode (null for add)
- `zone` - Current zone (for full domain display)

**Form Fields**:
1. Type (dropdown, disabled in edit mode)
2. Name (text input, with full domain helper)
3. Content (text input, with type-specific placeholder)
4. TTL (dropdown: Auto, 1min, 5min, 10min, 1hr, 1day)
5. Priority (number, only for MX/SRV)
6. Proxied (switch, only for A/AAAA/CNAME)

**Validation**:
- Name required
- Content required
- IPv4 format for A records
- IPv6 format for AAAA records
- Priority 0-65535 for MX/SRV

#### 5.3 DeleteConfirmationModal.jsx - 80 lines

**Responsibilities**:
- Confirmation dialog for zone or DNS record deletion
- Warning alerts
- Display deletion target details

**Props**:
- `open` - Modal open state
- `onClose` - Close handler
- `onConfirm` - Delete handler
- `deleteTarget` - Zone or DNS record object
- `isZone` - Boolean flag

**Warnings**:
- Zone deletion: "⚠️ WARNING: This will delete the entire zone!"
- Email record deletion: "⚠️ Email-Related Record" (for MX, SPF, DMARC, DKIM)

**Display**:
- Zone: Domain name
- DNS Record: Type, Name, Content

---

### 6. Shared/ (4 components, ~100 lines total)

#### 6.1 StatusBadge.jsx - 30 lines

**Responsibilities**:
- Display zone status with icon + color
- Status types: active, pending, deactivated, deleted

**Props**:
- `status` - Status string

**Variants**:
- active: green chip, ActiveIcon
- pending: yellow chip, PendingIcon
- deactivated: red chip, InactiveIcon
- deleted: grey chip, InactiveIcon

#### 6.2 NameserversDisplay.jsx - 40 lines

**Responsibilities**:
- Display nameservers list
- Copy button

**Props**:
- `nameservers` - Array of nameserver strings
- `onCopy` - Copy handler

**Layout**:
- Nameservers in monospace font (one per line)
- Copy icon button next to list

#### 6.3 Toast.jsx - 30 lines

**Responsibilities**:
- Toast notification wrapper
- Snackbar with Alert

**Props**:
- `toast` - Toast object { open, message, severity }
- `onClose` - Close handler

**Position**: Bottom-right
**Auto-hide**: 6 seconds

#### 6.4 constants.js - 20 lines

**Exports**:
```javascript
export const RECORD_TYPES = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA'];

export const TTL_OPTIONS = [
  { value: 1, label: 'Auto' },
  { value: 60, label: '1 minute' },
  { value: 300, label: '5 minutes' },
  { value: 600, label: '10 minutes' },
  { value: 3600, label: '1 hour' },
  { value: 86400, label: '1 day' }
];

export const ZONE_PRIORITIES = [
  { value: 'critical', label: 'Critical - Add First' },
  { value: 'high', label: 'High Priority' },
  { value: 'normal', label: 'Normal Priority' },
  { value: 'low', label: 'Low Priority' }
];
```

---

## Implementation Plan

### Phase 1: Directory Setup (5 minutes)

```bash
cd /opt/ops-center

# Create directory structure
mkdir -p src/components/CloudflareDNS/ZoneListView
mkdir -p src/components/CloudflareDNS/ZoneDetailView/tabs
mkdir -p src/components/CloudflareDNS/DNSRecords
mkdir -p src/components/CloudflareDNS/Modals
mkdir -p src/components/CloudflareDNS/Shared
```

### Phase 2: Extract Shared Components (10 minutes)

**Priority**: These are used by multiple parts

1. `StatusBadge.jsx` - Used in zone list, zone detail
2. `NameserversDisplay.jsx` - Used in zone list, nameservers tab
3. `Toast.jsx` - Used by main coordinator
4. `constants.js` - Used by modals, forms

### Phase 3: Extract Modals (20 minutes)

**Priority**: Clean separation, easy to extract

1. `CreateZoneModal.jsx` - Lines 1174-1251
2. `AddEditRecordModal.jsx` - Lines 1253-1381
3. `DeleteConfirmationModal.jsx` - Lines 1383-1459

### Phase 4: Extract DNSRecords Components (25 minutes)

**Priority**: Used in DNSRecordsTab

1. `DNSRecordToolbar.jsx` - Search/filter/add controls
2. `ProxyToggleButton.jsx` - Proxy toggle logic
3. `DNSRecordRow.jsx` - Individual record row
4. `DNSRecordsTable.jsx` - Table coordinator

### Phase 5: Extract ZoneListView Components (30 minutes)

**Priority**: Main landing page

1. `ZoneListHeader.jsx` - Branding header
2. `AccountMetrics.jsx` - 4 metric cards
3. `AccountWarnings.jsx` - Rate limit warnings
4. `ZoneListToolbar.jsx` - Create/Refresh/Search/Filter
5. `ZoneTableRow.jsx` - Individual zone row
6. `ZonesTable.jsx` - Table with pagination
7. `ZoneListView/index.jsx` - List coordinator

### Phase 6: Extract ZoneDetailView Components (30 minutes)

**Priority**: Detail view

1. `ZoneDetailHeader.jsx` - Header with back button
2. `ZoneDetailTabs.jsx` - Tab navigation
3. `OverviewTab.jsx` - Tab 0
4. `DNSRecordsTab.jsx` - Tab 1
5. `NameserversTab.jsx` - Tab 2
6. `SettingsTab.jsx` - Tab 3
7. `ZoneDetailView/index.jsx` - Detail coordinator

### Phase 7: Create Main Coordinator (20 minutes)

1. Move all state management to `index.jsx`
2. Keep all API functions
3. Keep all event handlers
4. Route between ZoneListView and ZoneDetailView
5. Pass props to child components

### Phase 8: Update App.jsx (5 minutes)

```javascript
// Before
import CloudflareDNS from './pages/network/CloudflareDNS';

// After
import CloudflareDNS from './components/CloudflareDNS';
```

### Phase 9: Testing & Verification (15 minutes)

1. Build frontend: `npm run build`
2. Deploy: `cp -r dist/* public/`
3. Test zone list view
4. Test zone detail view (all 4 tabs)
5. Test create zone modal
6. Test add/edit DNS record modal
7. Test delete confirmations
8. Test search/filter functionality

### Phase 10: Documentation (10 minutes)

Create `REFACTORING_SUMMARY_C02.md` documenting:
- Before/after structure
- Component breakdown
- Line count metrics
- Testing results
- Lessons learned

---

## Success Criteria

### Metrics

| Metric | Before | Target | Change |
|--------|--------|--------|--------|
| **Main File Lines** | 1,480 | <400 | **-73%** ⬇️ |
| **Components** | 1 | 24 | **+2,300%** ⬆️ |
| **Largest Component** | 1,480 | ~140 | **-91%** ⬇️ |
| **Average Component Size** | 1,480 | ~70 | **-95%** ⬇️ |

### Functionality Checklist

- [ ] Zone list loads and displays correctly
- [ ] Zone search/filter works
- [ ] Zone creation modal opens and submits
- [ ] Zone deletion works
- [ ] Zone detail view opens on click
- [ ] All 4 tabs render correctly
- [ ] DNS records load in detail view
- [ ] DNS record search/filter works
- [ ] Add DNS record modal works
- [ ] Edit DNS record modal works
- [ ] Delete DNS record works
- [ ] Proxy toggle works
- [ ] Nameservers copy works
- [ ] Toast notifications appear
- [ ] Pagination works (zones + records)
- [ ] All icons display correctly
- [ ] Theme gradients work (unicorn vs default)

---

## Risk Assessment

### Low Risk

- ✅ Shared components (StatusBadge, NameserversDisplay) - No dependencies
- ✅ Constants extraction - Pure data
- ✅ Modals - Clean boundaries

### Medium Risk

- ⚠️ Table components - Complex props, pagination logic
- ⚠️ Tab components - State management, data loading
- ⚠️ Toolbar components - Multiple handlers

### High Risk

- 🔴 Main coordinator - Many states, API calls, event handlers
- 🔴 ZoneListView coordinator - Filtering/pagination logic
- 🔴 ZoneDetailView coordinator - Tab state, data loading

### Mitigation Strategies

1. **Extract in order**: Shared → Modals → Tables → Coordinators
2. **Test frequently**: Build + deploy after each major extraction
3. **Preserve all state**: Keep state in main coordinator initially
4. **Props over context**: Use clear prop drilling for predictability
5. **Keep axios**: Don't change API calls or endpoints
6. **Backup first**: Create backup of original file before refactoring

---

## Technical Notes

### Axios Usage

This component uses **axios** (not fetch). Preserve all axios calls:

```javascript
// ✅ Keep these as-is
await axios.get('/api/v1/cloudflare/zones');
await axios.post('/api/v1/cloudflare/zones', payload);
await axios.delete(`/api/v1/cloudflare/zones/${zoneId}`);
```

### Theme Context

Component uses `useTheme()` for gradient colors:

```javascript
const { currentTheme } = useTheme();

// Used for gradient backgrounds
background: currentTheme === 'unicorn'
  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
  : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
```

### Material-UI Components

Heavy use of MUI components - preserve all imports:
- Box, Card, CardContent
- Table, TableBody, TableCell, TableContainer, TableHead, TableRow
- Dialog, DialogTitle, DialogContent, DialogActions
- TextField, Select, MenuItem, FormControl, InputLabel
- Button, IconButton, Tooltip
- Alert, Snackbar
- Tabs, Tab
- Switch, FormControlLabel
- Grid, Divider
- CircularProgress, LinearProgress
- Chip, Typography

### State Considerations

**23 useState hooks** - Consider future refactoring to useReducer:

```javascript
// Potential future enhancement
const [state, dispatch] = useReducer(cloudflareReducer, initialState);

// Instead of 23 separate useState calls
```

But for now: **Keep all useState** in main coordinator.

---

## Estimated Time

| Phase | Time | Cumulative |
|-------|------|------------|
| Directory Setup | 5 min | 5 min |
| Shared Components | 10 min | 15 min |
| Modals | 20 min | 35 min |
| DNSRecords Components | 25 min | 60 min |
| ZoneListView Components | 30 min | 90 min |
| ZoneDetailView Components | 30 min | 120 min |
| Main Coordinator | 20 min | 140 min |
| Update App.jsx | 5 min | 145 min |
| Testing | 15 min | 160 min |
| Documentation | 10 min | 170 min |

**Total Estimated Time**: **2 hours 50 minutes**

---

## Next Steps

1. **Read this plan carefully**
2. **Create directory structure**
3. **Start with Phase 2** (Shared components)
4. **Extract incrementally** (don't try to do everything at once)
5. **Test after each phase** (build + deploy)
6. **Document as you go** (take notes for summary)
7. **Backup original file** (before deletion)

---

**Ready to begin refactoring!** 🚀

---

**Prepared by**: Claude (System Architecture Designer)
**Date**: October 25, 2025
**Reference Pattern**: REFACTORING_SUMMARY_C01.md
