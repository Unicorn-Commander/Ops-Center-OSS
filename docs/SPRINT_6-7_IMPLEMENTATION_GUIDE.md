# Sprint 6-7 Implementation Guide
## Error Handling, Validation & Final Polish

**Date**: October 25, 2025
**Status**: Ready for Implementation
**Estimated Time**: 58-81 hours (3-4 days with parallel execution)

---

## CRITICAL: SSH Key Deletion Bug (H16) - IMMEDIATE FIX REQUIRED

### Security Vulnerability Analysis

**File**: `src/pages/LocalUsers.jsx`
**Lines**: 294-296, 832-845
**Severity**: CRITICAL - Can delete wrong SSH keys
**Impact**: User lockout, security breach

#### The Bug

```javascript
// Line 294-296: Function expects keyIndex
const handleDeleteSshKey = async (keyIndex) => {
  try {
    const response = await fetch(`/api/v1/local-users/${selectedUser.username}/ssh-keys/${keyIndex}`, {
      method: 'DELETE',
      // ...
    });
  }
}

// Line 832-845: Passes array index instead of key ID
{sshKeys.map((key, index) => (
  <ListItem key={index}>  // ❌ Uses index as React key
    <IconButton
      onClick={() => handleDeleteSshKey(index)}  // ❌ Passes array index
    >
      <DeleteIcon />
    </IconButton>
  </ListItem>
))}
```

#### Why This Is Dangerous

1. **Array Index ≠ Key ID**: If SSH keys are added/removed, array indices change but key IDs don't
2. **Race Condition**: If keys are fetched while deletion is in progress, indices shift
3. **User Impact**: Admin thinks they're deleting key 3, but actually deletes key 1
4. **Security**: Could accidentally delete the only remaining access method

#### The Fix

```javascript
// STEP 1: Update the key object structure
// Ensure SSH keys have unique identifiers from backend
// Backend should return: { id: "key_id_123", key: "ssh-rsa...", created_at: "..." }

// STEP 2: Fix the delete function to use key ID
const handleDeleteSshKey = async (keyId) => {  // ✅ Changed parameter name
  // Add confirmation dialog
  if (!window.confirm('Are you sure you want to delete this SSH key? This action cannot be undone.')) {
    return;
  }

  try {
    const response = await fetch(
      `/api/v1/local-users/${selectedUser.username}/ssh-keys/${keyId}`,  // ✅ Use keyId
      {
        method: 'DELETE',
        credentials: 'include',
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete SSH key');
    }

    showToast('SSH key deleted successfully', 'success');
    fetchSshKeys(selectedUser.username);
  } catch (err) {
    showToast('Failed to delete SSH key: ' + err.message, 'error');
  }
};

// STEP 3: Fix the map to use key.id
{sshKeys.map((key) => (  // ✅ No index needed
  <ListItem
    key={key.id}  // ✅ Use unique key ID for React key
    sx={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}
  >
    <ListItemText
      primary={
        <Typography variant="body2" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
          {key.key.substring(0, 60)}...
        </Typography>
      }
      secondary={`Added: ${new Date(key.created_at).toLocaleString()}`}
    />
    <ListItemSecondaryAction>
      <IconButton
        edge="end"
        color="error"
        onClick={() => handleDeleteSshKey(key.id)}  // ✅ Pass key.id
        title="Delete SSH key"
      >
        <DeleteIcon />
      </IconButton>
    </ListItemSecondaryAction>
  </ListItem>
))}
```

#### Backend Verification Required

Check `/home/muut/Production/UC-Cloud/services/ops-center/backend/local_users_api.py`:
- Ensure SSH keys have unique IDs
- Ensure DELETE endpoint accepts key ID, not index
- Add proper error handling for "key not found"

#### Testing Steps

1. Add 3 SSH keys to a user
2. Delete the middle key (key 2)
3. Verify that key 2 (not key 1 or 3) was actually deleted
4. Add another key
5. Delete the first key
6. Verify correct key was deleted

---

## Error Handling Implementation (H09-H11, H12-H13)

### Pattern 1: API Call Error States

**Affected Files**:
- `src/pages/System.jsx` (H09)
- `src/pages/LLMManagement.jsx` (H10)
- `src/pages/LiteLLMManagement.jsx` (H11)
- All Traefik pages (H12)
- All Billing components (H13)

#### Standard Error Handling Pattern

```javascript
// 1. Add error state
const [error, setError] = useState(null);
const [loading, setLoading] = useState(false);

// 2. Wrap API calls with try-catch
const fetchData = async () => {
  setLoading(true);
  setError(null);  // Clear previous errors

  try {
    const response = await fetch('/api/v1/endpoint');

    if (!response.ok) {
      // Try to get error message from response
      let errorMessage = 'Request failed';
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorMessage;
      } catch {
        errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    setData(data);

  } catch (err) {
    console.error('Error fetching data:', err);
    setError(err.message);
  } finally {
    setLoading(false);
  }
};

// 3. Render error UI
{error && (
  <Alert
    severity="error"
    sx={{ mb: 2 }}
    action={
      <Button color="inherit" size="small" onClick={fetchData}>
        Retry
      </Button>
    }
  >
    {error}
  </Alert>
)}

{loading && <CircularProgress />}

{!loading && !error && data && (
  <DataDisplay data={data} />
)}
```

### Pattern 2: Error Boundaries for Components

Create `src/components/ErrorBoundary.jsx`:

```javascript
import React from 'react';
import { Alert, Button, Box, Typography } from '@mui/material';
import { ErrorOutline as ErrorIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({
      error,
      errorInfo
    });
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  render() {
    if (this.state.hasError) {
      return (
        <Box sx={{ p: 3 }}>
          <Alert
            severity="error"
            icon={<ErrorIcon />}
            action={
              <Button color="inherit" size="small" onClick={this.handleReset}>
                Reset
              </Button>
            }
          >
            <Typography variant="h6" gutterBottom>
              Something went wrong
            </Typography>
            <Typography variant="body2" sx={{ fontFamily: 'monospace', mt: 1 }}>
              {this.state.error?.toString()}
            </Typography>
            {process.env.NODE_ENV === 'development' && this.state.errorInfo && (
              <Typography
                variant="caption"
                component="pre"
                sx={{ mt: 2, fontSize: '0.75rem', overflow: 'auto' }}
              >
                {this.state.errorInfo.componentStack}
              </Typography>
            )}
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

#### Usage in App.jsx

```javascript
import ErrorBoundary from './components/ErrorBoundary';

// Wrap routes that need error boundaries
<Route
  path="/admin/llm/management"
  element={
    <ErrorBoundary onReset={() => window.location.reload()}>
      <LLMManagement />
    </ErrorBoundary>
  }
/>
```

### H09: System.jsx Error Handling

**Missing Error States**:
- Hardware monitoring (`/api/v1/system/hardware`) - Line ~100
- Disk I/O stats (`/api/v1/system/disk-io`) - Line ~150
- Network stats (`/api/v1/system/network`) - Line ~180

**Implementation**:

```javascript
// Add error states for each API
const [hardwareError, setHardwareError] = useState(null);
const [diskError, setDiskError] = useState(null);
const [networkError, setNetworkError] = useState(null);

// Fetch hardware with error handling
const fetchHardwareStats = async () => {
  try {
    setHardwareError(null);
    const response = await fetch('/api/v1/system/hardware', { credentials: 'include' });
    if (!response.ok) throw new Error('Failed to fetch hardware stats');
    const data = await response.json();
    setHardware(data);
  } catch (err) {
    console.error('Hardware stats error:', err);
    setHardwareError(err.message);
  }
};

// In hardware tab render:
{hardwareError && (
  <Alert severity="error" sx={{ mb: 2 }}>
    {hardwareError}
    <Button size="small" onClick={fetchHardwareStats}>Retry</Button>
  </Alert>
)}
```

### H10: LLMManagement.jsx Error Boundaries

Wrap the entire component in ErrorBoundary:

```javascript
// In App.jsx
<Route
  path="/admin/llm/management"
  element={
    <ErrorBoundary>
      <LLMManagement />
    </ErrorBoundary>
  }
/>
```

Add error states for model operations:
- Model loading
- Model downloading
- Model configuration

### H11: LiteLLMManagement.jsx Error States

Add error handling for:
- Provider list fetch
- Provider configuration
- BYOK key management

### H12: Traefik Pages Error Handling

**Files**:
- TraefikDashboard.jsx
- TraefikMetrics.jsx
- TraefikRoutes.jsx
- TraefikSSL.jsx
- TraefikServices.jsx
- TraefikConfig.jsx

All need:
1. Error states for API calls
2. Retry buttons
3. User-friendly error messages
4. Loading states

### H13: Billing Components Error Handling

**Files**:
- `src/components/billing/AdminBilling.jsx`
- `src/components/billing/UserAccount.jsx`
- `src/components/billing/UpgradePrompt.jsx`
- `src/components/billing/SubscriptionManagement.jsx`

Add error boundaries and payment error handling:

```javascript
// Payment-specific errors
const handlePaymentError = (error) => {
  let userMessage = 'Payment failed. Please try again.';

  if (error.message.includes('card_declined')) {
    userMessage = 'Your card was declined. Please use a different payment method.';
  } else if (error.message.includes('insufficient_funds')) {
    userMessage = 'Insufficient funds. Please try a different card.';
  } else if (error.message.includes('expired_card')) {
    userMessage = 'Your card has expired. Please update your payment method.';
  }

  setPaymentError(userMessage);
};
```

---

## Form Validation Implementation (H17-H19)

### H17: Email Settings Validation

**File**: `src/pages/EmailSettings.jsx`

#### SMTP Validation

```javascript
const validateSMTPForm = (formData) => {
  const errors = {};

  // Required fields
  if (!formData.smtp_host) {
    errors.smtp_host = 'SMTP host is required';
  }

  if (!formData.smtp_port) {
    errors.smtp_port = 'SMTP port is required';
  } else {
    const port = parseInt(formData.smtp_port);
    if (isNaN(port) || port < 1 || port > 65535) {
      errors.smtp_port = 'Port must be between 1 and 65535';
    }
  }

  if (!formData.smtp_username) {
    errors.smtp_username = 'Username is required';
  }

  if (!formData.smtp_password && !formData.existing_password) {
    errors.smtp_password = 'Password is required';
  }

  if (!formData.from_email) {
    errors.from_email = 'From email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.from_email)) {
    errors.from_email = 'Invalid email format';
  }

  // TLS/SSL validation
  if (formData.use_tls && formData.use_ssl) {
    errors.security = 'Cannot use both TLS and SSL. Choose one.';
  }

  return errors;
};

// In submit handler
const handleSMTPSubmit = async (e) => {
  e.preventDefault();

  const validationErrors = validateSMTPForm(formData);
  if (Object.keys(validationErrors).length > 0) {
    setErrors(validationErrors);
    return;
  }

  setErrors({});
  // Continue with submission...
};
```

#### OAuth2 Validation (Microsoft 365)

```javascript
const validateOAuthForm = (formData) => {
  const errors = {};

  if (!formData.client_id) {
    errors.client_id = 'Client ID is required';
  } else if (!/^[a-f0-9-]{36}$/i.test(formData.client_id)) {
    errors.client_id = 'Invalid Client ID format (should be a GUID)';
  }

  if (!formData.client_secret) {
    errors.client_secret = 'Client secret is required';
  }

  if (!formData.tenant_id) {
    errors.tenant_id = 'Tenant ID is required';
  } else if (!/^[a-f0-9-]{36}$/i.test(formData.tenant_id)) {
    errors.tenant_id = 'Invalid Tenant ID format (should be a GUID)';
  }

  if (!formData.from_email) {
    errors.from_email = 'From email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.from_email)) {
    errors.from_email = 'Invalid email format';
  }

  return errors;
};
```

### H18: Platform Settings Validation

**File**: `src/pages/PlatformSettings.jsx`

Add validation for each category:

#### System Settings

```javascript
const validateSystemSettings = (settings) => {
  const errors = {};

  if (settings.maintenance_mode !== undefined && typeof settings.maintenance_mode !== 'boolean') {
    errors.maintenance_mode = 'Must be true or false';
  }

  if (settings.max_upload_size) {
    const size = parseInt(settings.max_upload_size);
    if (isNaN(size) || size < 1 || size > 10240) {
      errors.max_upload_size = 'Must be between 1 MB and 10 GB (10240 MB)';
    }
  }

  return errors;
};
```

#### Security Settings

```javascript
const validateSecuritySettings = (settings) => {
  const errors = {};

  if (settings.session_timeout) {
    const timeout = parseInt(settings.session_timeout);
    if (isNaN(timeout) || timeout < 5 || timeout > 1440) {
      errors.session_timeout = 'Must be between 5 and 1440 minutes (24 hours)';
    }
  }

  if (settings.password_min_length) {
    const length = parseInt(settings.password_min_length);
    if (isNaN(length) || length < 8 || length > 128) {
      errors.password_min_length = 'Must be between 8 and 128 characters';
    }
  }

  if (settings.max_login_attempts) {
    const attempts = parseInt(settings.max_login_attempts);
    if (isNaN(attempts) || attempts < 3 || attempts > 10) {
      errors.max_login_attempts = 'Must be between 3 and 10 attempts';
    }
  }

  return errors;
};
```

### H19: Process Kill Warnings

**Files**: `src/pages/System.jsx`, `src/pages/PlatformSettings.jsx`

Add confirmation dialogs for critical processes:

```javascript
const CRITICAL_PROCESSES = [
  'ops-center',
  'keycloak',
  'postgresql',
  'redis',
  'traefik',
  'nginx',
];

const isCriticalProcess = (processName) => {
  return CRITICAL_PROCESSES.some(critical =>
    processName.toLowerCase().includes(critical.toLowerCase())
  );
};

const handleKillProcess = async (process) => {
  if (isCriticalProcess(process.name)) {
    const confirmed = window.confirm(
      `⚠️ WARNING: "${process.name}" is a CRITICAL process.\n\n` +
      `Killing this process may cause:\n` +
      `- Loss of access to the admin panel\n` +
      `- Service disruptions\n` +
      `- Data loss\n\n` +
      `Are you absolutely sure you want to kill this process?`
    );

    if (!confirmed) return;

    // Second confirmation for extra safety
    const doubleConfirm = window.confirm(
      `This is your last chance.\n\n` +
      `Type the process PID (${process.pid}) to confirm.`
    );

    const userInput = prompt(`Type ${process.pid} to confirm:`);
    if (userInput !== String(process.pid)) {
      showToast('Process kill cancelled', 'info');
      return;
    }
  }

  // Proceed with kill
  try {
    const response = await fetch(`/api/v1/system/processes/${process.pid}/kill`, {
      method: 'POST',
      credentials: 'include',
    });

    if (!response.ok) throw new Error('Failed to kill process');

    showToast(`Process ${process.name} (PID ${process.pid}) killed`, 'success');
    fetchProcesses();
  } catch (err) {
    showToast(`Failed to kill process: ${err.message}`, 'error');
  }
};
```

---

## Backend Verification Tasks (H20-H22)

### H20: Platform Settings Backend

**File**: `backend/platform_settings_api.py`

**Verify these endpoints exist**:

```python
# GET /api/v1/platform/settings
# GET /api/v1/platform/settings/{category}
# PUT /api/v1/platform/settings/{category}
# POST /api/v1/platform/settings/test-connection
```

**Test with curl**:

```bash
# Get all settings
curl http://localhost:8084/api/v1/platform/settings \
  -H "Cookie: session=..." \
  -H "Accept: application/json"

# Update category
curl http://localhost:8084/api/v1/platform/settings/system \
  -X PUT \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{"maintenance_mode": false, "max_upload_size": 100}'
```

### H21: Local Users Backend

**File**: `backend/local_users_api.py`

**Verify these endpoints exist**:

```python
# GET /api/v1/local-users
# POST /api/v1/local-users
# DELETE /api/v1/local-users/{username}
# POST /api/v1/local-users/{username}/password
# GET /api/v1/local-users/{username}/ssh-keys
# POST /api/v1/local-users/{username}/ssh-keys
# DELETE /api/v1/local-users/{username}/ssh-keys/{key_id}  # ⚠️ Must use key_id not index!
# POST /api/v1/local-users/{username}/grant-sudo
# POST /api/v1/local-users/{username}/revoke-sudo
```

**Verify SSH key endpoint**:

```bash
# List SSH keys - should return array with IDs
curl http://localhost:8084/api/v1/local-users/testuser/ssh-keys

# Expected response:
# [
#   {
#     "id": "key_123abc",
#     "key": "ssh-rsa AAAAB3...",
#     "created_at": "2025-10-25T12:00:00Z"
#   }
# ]

# Delete by ID (not index!)
curl -X DELETE http://localhost:8084/api/v1/local-users/testuser/ssh-keys/key_123abc
```

### H22: BYOK API Endpoints

**File**: `backend/user_api_keys.py`

**Verify these endpoints exist**:

```python
# GET /api/v1/admin/users/{user_id}/api-keys
# POST /api/v1/admin/users/{user_id}/api-keys
# DELETE /api/v1/admin/users/{user_id}/api-keys/{key_id}
# GET /api/v1/account/api-keys  # User's own keys
# POST /api/v1/account/api-keys  # Create own key
# DELETE /api/v1/account/api-keys/{key_id}  # Delete own key
```

**Test with curl**:

```bash
# Admin endpoint
curl http://localhost:8084/api/v1/admin/users/user-123/api-keys \
  -H "Cookie: session=..."

# User endpoint
curl http://localhost:8084/api/v1/account/api-keys \
  -H "Cookie: session=..."

# Create new key
curl -X POST http://localhost:8084/api/v1/account/api-keys \
  -H "Cookie: session=..." \
  -H "Content-Type: application/json" \
  -d '{"name": "My API Key", "scopes": ["read", "write"]}'
```

---

## Organizations List Page (C07)

### Requirements

**File to Create**: `src/pages/OrganizationsList.jsx`

**Features Required**:
1. List all organizations with key metrics
2. Search and filter capabilities
3. Bulk operations (suspend, delete, change tier)
4. Create organization modal
5. Organization detail links
6. Admin-only access

### Component Structure

```javascript
import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Checkbox,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  Toolbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';

const OrganizationsList = () => {
  const navigate = useNavigate();
  const { currentTheme } = useTheme();

  // State
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [selected, setSelected] = useState([]);

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [bulkModalOpen, setBulkModalOpen] = useState(false);

  // Stats
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    suspended: 0,
    trial: 0,
    paid: 0,
  });

  // Fetch organizations
  const fetchOrganizations = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/organizations', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch organizations');
      }

      const data = await response.json();
      setOrganizations(data.organizations || []);

      // Calculate stats
      setStats({
        total: data.organizations.length,
        active: data.organizations.filter(o => o.status === 'active').length,
        suspended: data.organizations.filter(o => o.status === 'suspended').length,
        trial: data.organizations.filter(o => o.subscription_tier === 'trial').length,
        paid: data.organizations.filter(o => ['starter', 'professional', 'enterprise'].includes(o.subscription_tier)).length,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  // Filter organizations
  const filteredOrganizations = organizations.filter(org =>
    org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    org.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Pagination
  const paginatedOrganizations = filteredOrganizations.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Selection
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      setSelected(paginatedOrganizations.map(o => o.id));
    } else {
      setSelected([]);
    }
  };

  const handleSelectOne = (id) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected = [];

    if (selectedIndex === -1) {
      newSelected = newSelected.concat(selected, id);
    } else if (selectedIndex === 0) {
      newSelected = newSelected.concat(selected.slice(1));
    } else if (selectedIndex === selected.length - 1) {
      newSelected = newSelected.concat(selected.slice(0, -1));
    } else if (selectedIndex > 0) {
      newSelected = newSelected.concat(
        selected.slice(0, selectedIndex),
        selected.slice(selectedIndex + 1)
      );
    }

    setSelected(newSelected);
  };

  // Bulk operations
  const handleBulkSuspend = async () => {
    try {
      await fetch('/api/v1/organizations/bulk/suspend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ organization_ids: selected }),
      });

      setSelected([]);
      fetchOrganizations();
    } catch (err) {
      setError('Failed to suspend organizations');
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header with stats */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          Organizations
        </Typography>

        {/* Stats cards */}
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 2, mb: 3 }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="caption">Total</Typography>
            <Typography variant="h5">{stats.total}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="caption">Active</Typography>
            <Typography variant="h5" color="success.main">{stats.active}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="caption">Suspended</Typography>
            <Typography variant="h5" color="error.main">{stats.suspended}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="caption">Trial</Typography>
            <Typography variant="h5" color="warning.main">{stats.trial}</Typography>
          </Paper>
          <Paper sx={{ p: 2 }}>
            <Typography variant="caption">Paid</Typography>
            <Typography variant="h5" color="primary.main">{stats.paid}</Typography>
          </Paper>
        </Box>
      </Box>

      {/* Toolbar */}
      <Paper sx={{ mb: 2 }}>
        <Toolbar>
          <TextField
            placeholder="Search organizations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            size="small"
            sx={{ width: 300 }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
            }}
          />

          <Box sx={{ flexGrow: 1 }} />

          {selected.length > 0 && (
            <Box sx={{ mr: 2 }}>
              <Typography variant="body2">
                {selected.length} selected
              </Typography>
              <Button onClick={handleBulkSuspend} color="error" size="small">
                Suspend Selected
              </Button>
            </Box>
          )}

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateModalOpen(true)}
          >
            Create Organization
          </Button>

          <IconButton onClick={fetchOrganizations}>
            <RefreshIcon />
          </IconButton>
        </Toolbar>
      </Paper>

      {/* Error alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selected.length > 0 && selected.length < paginatedOrganizations.length}
                  checked={paginatedOrganizations.length > 0 && selected.length === paginatedOrganizations.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Members</TableCell>
              <TableCell>Tier</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedOrganizations.map((org) => (
              <TableRow
                key={org.id}
                hover
                onClick={() => navigate(`/admin/organizations/${org.id}`)}
                sx={{ cursor: 'pointer' }}
              >
                <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                  <Checkbox
                    checked={selected.indexOf(org.id) !== -1}
                    onChange={() => handleSelectOne(org.id)}
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon fontSize="small" />
                    {org.name}
                  </Box>
                </TableCell>
                <TableCell>{org.member_count || 0}</TableCell>
                <TableCell>
                  <Chip
                    label={org.subscription_tier}
                    size="small"
                    color={org.subscription_tier === 'enterprise' ? 'primary' : 'default'}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={org.status}
                    size="small"
                    color={org.status === 'active' ? 'success' : 'error'}
                  />
                </TableCell>
                <TableCell>
                  {new Date(org.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                  <IconButton size="small" onClick={() => navigate(`/admin/organizations/${org.id}`)}>
                    <EditIcon fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={filteredOrganizations.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => setRowsPerPage(parseInt(e.target.value, 10))}
        />
      </TableContainer>

      {/* Create Organization Modal */}
      <CreateOrganizationModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onSuccess={() => {
          setCreateModalOpen(false);
          fetchOrganizations();
        }}
      />
    </Box>
  );
};

export default OrganizationsList;
```

### Integration Steps

1. **Create the file**: `src/pages/OrganizationsList.jsx`
2. **Add route** in `src/App.jsx`:
   ```javascript
   import OrganizationsList from './pages/OrganizationsList';

   <Route path="/admin/organizations" element={<OrganizationsList />} />
   ```
3. **Update navigation** in `src/components/Layout.jsx`:
   ```javascript
   {
     label: 'Organizations',
     path: '/admin/organizations',
     icon: <BusinessIcon />,
     admin: true,
   }
   ```
4. **Test the page**:
   - Navigate to `/admin/organizations`
   - Verify organizations load
   - Test search, filter, pagination
   - Test bulk selection
   - Test create organization

---

## Implementation Checklist

### Priority 1: Security (Must fix immediately)
- [ ] H16: Fix SSH key deletion bug in LocalUsers.jsx
- [ ] H16: Add confirmation dialogs
- [ ] H16: Verify backend uses key IDs
- [ ] H16: Test SSH key deletion flow

### Priority 2: Error Handling
- [ ] H09: Add error states to System.jsx
- [ ] H10: Add error boundaries to LLMManagement.jsx
- [ ] H11: Add error states to LiteLLMManagement.jsx
- [ ] H12: Add error handling to all 6 Traefik pages
- [ ] H13: Add error boundaries to all 6 billing components
- [ ] Create ErrorBoundary.jsx component
- [ ] Update App.jsx with error boundaries

### Priority 3: Validation
- [ ] H17: Add SMTP validation to EmailSettings.jsx
- [ ] H17: Add OAuth validation to EmailSettings.jsx
- [ ] H18: Add validation to PlatformSettings.jsx (all categories)
- [ ] H19: Add process kill warnings to System.jsx
- [ ] H19: Add critical process checks

### Priority 4: Backend Verification
- [ ] H20: Verify Platform Settings API exists
- [ ] H20: Test all platform settings endpoints
- [ ] H21: Verify Local Users API exists
- [ ] H21: Verify SSH keys use IDs not indices
- [ ] H22: Verify BYOK API endpoints
- [ ] H22: Test API key creation/deletion

### Priority 5: Organizations List
- [ ] C07: Create OrganizationsList.jsx
- [ ] C07: Add route to App.jsx
- [ ] C07: Add navigation link
- [ ] C07: Implement search/filter
- [ ] C07: Implement bulk operations
- [ ] C07: Create organization modal
- [ ] C07: Test full workflow

---

## Testing Strategy

### Manual Testing

1. **SSH Key Deletion** (CRITICAL):
   - Add 3 SSH keys
   - Delete middle key
   - Verify correct key deleted
   - Try with empty list
   - Try with single key

2. **Error Handling**:
   - Disconnect backend
   - Try to load each page
   - Verify error messages appear
   - Verify retry buttons work

3. **Form Validation**:
   - Submit empty forms
   - Submit invalid data
   - Verify error messages
   - Verify validation prevents submission

4. **Backend APIs**:
   - Use curl to test each endpoint
   - Verify responses match expectations
   - Test error cases (404, 401, 500)

### Automated Testing (Future)

```javascript
// Example test for SSH key deletion
describe('SSH Key Deletion', () => {
  it('should use key ID not array index', async () => {
    const keys = [
      { id: 'key_1', key: 'ssh-rsa AAA...' },
      { id: 'key_2', key: 'ssh-rsa BBB...' },
      { id: 'key_3', key: 'ssh-rsa CCC...' },
    ];

    // Mock API
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => keys,
    });

    const { getByTestId } = render(<LocalUsers />);

    // Click delete on second key
    const deleteButton = getByTestId('delete-key-key_2');
    fireEvent.click(deleteButton);

    // Verify API called with key ID, not index
    expect(fetch).toHaveBeenCalledWith(
      '/api/v1/local-users/testuser/ssh-keys/key_2',
      expect.objectContaining({ method: 'DELETE' })
    );
  });
});
```

---

## Git Commit Strategy

Create atomic commits for each feature:

```bash
# 1. Security fix
git add src/pages/LocalUsers.jsx
git commit -m "fix(security): Use SSH key IDs instead of array indices

CRITICAL: Fix SSH key deletion bug that could delete wrong keys.

- Change handleDeleteSshKey to accept key ID instead of index
- Update map to pass key.id instead of array index
- Add confirmation dialog for SSH key deletion
- Fixes H16

Resolves: #H16"

# 2. Error boundaries
git add src/components/ErrorBoundary.jsx src/App.jsx
git commit -m "feat(error-handling): Add error boundaries to critical components

- Create ErrorBoundary component
- Wrap LLM Management, Billing, Traefik pages
- Add error recovery options
- Fixes H10

Resolves: #H10"

# 3. Error states - Monitoring
git add src/pages/System.jsx
git commit -m "feat(error-handling): Add error states to System monitoring

- Add error handling for hardware stats API
- Add error handling for disk I/O API
- Add error handling for network stats API
- Add retry buttons
- Fixes H09

Resolves: #H09"

# Continue for each feature...
```

---

## Success Metrics

### Code Quality
- ✅ No console errors on any page
- ✅ All error states handled gracefully
- ✅ All forms validated before submission
- ✅ No security vulnerabilities (SSH bug fixed)

### User Experience
- ✅ Clear error messages (no technical jargon)
- ✅ Retry buttons for network errors
- ✅ Loading states for all async operations
- ✅ Confirmation dialogs for destructive actions

### Backend Health
- ✅ All API endpoints return correct status codes
- ✅ All endpoints handle errors properly
- ✅ No 500 errors in production

### Documentation
- ✅ All changes documented in commit messages
- ✅ Complex logic commented
- ✅ API contracts documented

---

## Timeline (With Single Developer)

### Day 1 (8-10 hours)
- Morning: Fix SSH key bug (H16) - 2 hours
- Late Morning: Create ErrorBoundary component - 1 hour
- Afternoon: Add error states to System.jsx (H09) - 2 hours
- Late Afternoon: Add error states to LLM pages (H10-H11) - 3 hours

### Day 2 (8-10 hours)
- Morning: Add error handling to Traefik pages (H12) - 4 hours
- Afternoon: Add error handling to Billing pages (H13) - 4 hours

### Day 3 (8-10 hours)
- Morning: Add validation to Email Settings (H17) - 3 hours
- Afternoon: Add validation to Platform Settings (H18) - 2 hours
- Late Afternoon: Add process warnings (H19) - 1 hour
- Evening: Backend verification (H20-H22) - 2 hours

### Day 4 (10-14 hours)
- All day: Create Organizations List page (C07) - 10-12 hours
- Evening: Final testing - 2 hours

### Day 5 (4-6 hours)
- Morning: Bug fixes - 2 hours
- Afternoon: Git commits and documentation - 2 hours
- Final review - 2 hours

**Total**: 38-50 hours

---

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: Test each page thoroughly after adding error handling

### Risk 2: Backend APIs Don't Exist
**Mitigation**: Create minimal stub implementations if needed

### Risk 3: Time Overruns
**Mitigation**: Prioritize security fix (H16) first, then error handling

### Risk 4: Merge Conflicts
**Mitigation**: Work on one file at a time, commit frequently

---

**Status**: Ready for Implementation
**Next Step**: Start with H16 (SSH key bug) - CRITICAL PRIORITY
