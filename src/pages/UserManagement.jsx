import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// Safe utilities for defensive rendering (Phase 3 refactoring)
import { safeMap, safeFilter } from '../utils/safeArrayUtils';
import { safeToFixed, safeNumber } from '../utils/safeNumberUtils';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Avatar,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  FormControlLabel,
  Switch,
  Grid,
  Card,
  CardContent,
  MenuItem,
  Select,
  InputLabel,
  Checkbox,
  List,
  ListItem,
  ListItemText,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Collapse,
  Badge,
  OutlinedInput,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  VpnKey as VpnKeyIcon,
  Security as SecurityIcon,
  ExitToApp as LogoutIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  People as PeopleIcon,
  PersonAdd as PersonAddIcon,
  VerifiedUser as VerifiedUserIcon,
  AdminPanelSettings as AdminIcon,
  FilterList as FilterListIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  CalendarToday as CalendarIcon,
  Visibility as VisibilityIcon,
} from '@mui/icons-material';
import CreateUserModal from '../components/CreateUserModal';
import RoleManagementModal from '../components/RoleManagementModal';

const UserManagement = () => {
  const navigate = useNavigate();

  // State for user list
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalUsers, setTotalUsers] = useState(0);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // all, enabled, disabled
  const [advancedFiltersOpen, setAdvancedFiltersOpen] = useState(false);
  const [filters, setFilters] = useState({
    tiers: [],
    roles: [],
    statuses: [],
    org_id: '',
    created_from: '',
    created_to: '',
    last_login_from: '',
    last_login_to: '',
    email_verified: null,
    byok_enabled: null,
  });

  // Modal states
  const [createEditModalOpen, setCreateEditModalOpen] = useState(false);
  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [sessionModalOpen, setSessionModalOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [resetPasswordOpen, setResetPasswordOpen] = useState(false);

  // Current user/action data
  const [currentUser, setCurrentUser] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  const [userSessions, setUserSessions] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);
  const [userRoles, setUserRoles] = useState([]);

  // Statistics
  const [stats, setStats] = useState({
    total_users: 0,
    active_users: 0,
    suspended_users: 0,
    tier_distribution: {},
    status_distribution: {},
  });

  // Form data
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    firstName: '',
    lastName: '',
    password: '',
    enabled: true,
    emailVerified: false,
  });

  // Toast notification
  const [toast, setToast] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  // Fetch users with advanced filters
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: (page + 1).toString(),
        limit: rowsPerPage.toString(),
      });

      if (searchQuery) {
        params.append('search', searchQuery);
      }

      // Add advanced filters
      if (filters.tiers.length > 0) {
        params.append('tier', filters.tiers.join(','));
      }
      if (filters.roles.length > 0) {
        params.append('role', filters.roles.join(','));
      }
      if (filters.statuses.length > 0) {
        params.append('status', filters.statuses.join(','));
      }
      if (filters.org_id) {
        params.append('org_id', filters.org_id);
      }
      if (filters.created_from) {
        params.append('created_from', filters.created_from);
      }
      if (filters.created_to) {
        params.append('created_to', filters.created_to);
      }
      if (filters.last_login_from) {
        params.append('last_login_from', filters.last_login_from);
      }
      if (filters.last_login_to) {
        params.append('last_login_to', filters.last_login_to);
      }
      if (filters.email_verified !== null) {
        params.append('email_verified', filters.email_verified.toString());
      }
      if (filters.byok_enabled !== null) {
        params.append('byok_enabled', filters.byok_enabled.toString());
      }

      const response = await fetch(`/api/v1/admin/users?${params}`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch users');

      const data = await response.json();
      setUsers(data.users || []);
      setTotalUsers(data.pagination?.total || 0);
    } catch (err) {
      setError(err.message);
      showToast('Failed to load users', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Fetch statistics
  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/admin/users/analytics/summary', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch stats');

      const data = await response.json();
      setStats(data.summary || data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  // Fetch available roles
  const fetchRoles = async () => {
    try {
      const response = await fetch('/api/v1/admin/users/roles/available', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch roles');

      const data = await response.json();
      setAvailableRoles(data.roles || []);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    }
  };

  useEffect(() => {
    fetchUsers();
    fetchStats();
    fetchRoles();
  }, [page, rowsPerPage, searchQuery, statusFilter, filters]);

  // Show toast notification
  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  // Handle search with debouncing
  const handleSearch = (event) => {
    setSearchQuery(event.target.value);
    setPage(0); // Reset to first page
  };

  // Count active filters
  const getActiveFilterCount = () => {
    let count = 0;
    if (filters.tiers.length > 0) count++;
    if (filters.roles.length > 0) count++;
    if (filters.statuses.length > 0) count++;
    if (filters.org_id) count++;
    if (filters.created_from || filters.created_to) count++;
    if (filters.last_login_from || filters.last_login_to) count++;
    if (filters.email_verified !== null) count++;
    if (filters.byok_enabled !== null) count++;
    return count;
  };

  // Clear all filters
  const handleClearFilters = () => {
    setFilters({
      tiers: [],
      roles: [],
      statuses: [],
      org_id: '',
      created_from: '',
      created_to: '',
      last_login_from: '',
      last_login_to: '',
      email_verified: null,
      byok_enabled: null,
    });
    setSearchQuery('');
    setPage(0);
  };

  // Apply filter preset
  const applyFilterPreset = (preset) => {
    switch (preset) {
      case 'active':
        setFilters({
          ...filters,
          statuses: ['active'],
        });
        break;
      case 'trial':
        setFilters({
          ...filters,
          tiers: ['trial'],
        });
        break;
      case 'admins':
        setFilters({
          ...filters,
          roles: ['brigade-platform-admin'],
        });
        break;
      case 'inactive':
        setFilters({
          ...filters,
          statuses: ['suspended', 'trial_expired'],
        });
        break;
      default:
        break;
    }
    setPage(0);
  };

  // Handle pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Open create user modal
  const handleCreateUser = () => {
    setIsEditMode(false);
    setCurrentUser(null);
    setCreateEditModalOpen(true);
  };

  // Open edit user modal
  const handleEditUser = (user) => {
    setIsEditMode(true);
    setCurrentUser(user);
    setFormData({
      email: user.email || '',
      username: user.username || '',
      firstName: user.firstName || '',
      lastName: user.lastName || '',
      password: '', // Don't show existing password
      enabled: user.enabled !== false,
      emailVerified: user.emailVerified || false,
    });
    setCreateEditModalOpen(true);
  };

  // Save user (create or update)
  const handleSaveUser = async () => {
    try {
      const url = isEditMode
        ? `/api/v1/admin/users/${currentUser.id}`
        : '/api/v1/admin/users';

      const method = isEditMode ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save user');
      }

      showToast(isEditMode ? 'User updated successfully' : 'User created successfully');
      setCreateEditModalOpen(false);
      fetchUsers();
      fetchStats();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Delete user
  const handleDeleteUser = async () => {
    try {
      const response = await fetch(`/api/v1/admin/users/${currentUser.id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete user (${response.status})`);
      }

      const data = await response.json();
      showToast(data.message || 'User deleted successfully', 'success');
      setDeleteConfirmOpen(false);
      setCurrentUser(null);
      await fetchUsers();
      await fetchStats();
    } catch (err) {
      console.error('Delete user error:', err);
      showToast(err.message || 'Failed to delete user', 'error');
    }
  };

  // Reset password
  const handleResetPassword = async () => {
    try {
      const response = await fetch(`/api/v1/admin/users/${currentUser.id}/reset-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ temporary: true }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to reset password');

      const data = await response.json();
      showToast(`Password reset. Temporary password: ${data.temporaryPassword || 'sent to email'}`);
      setResetPasswordOpen(false);
      setCurrentUser(null);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Manage roles
  const handleManageRoles = async (user) => {
    setCurrentUser(user);
    setRoleModalOpen(true);

    try {
      const response = await fetch(`/api/v1/admin/users/${user.id}/roles`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch user roles');

      const data = await response.json();
      setUserRoles(data.roles || []);
    } catch (err) {
      showToast('Failed to load user roles', 'error');
    }
  };

  // Add role to user
  const handleAddRole = async (role) => {
    try {
      const response = await fetch(`/api/v1/admin/users/${currentUser.id}/roles`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to add role');

      setUserRoles([...userRoles, role]);
      showToast('Role added successfully');
      fetchUsers(); // Refresh user list to show updated roles
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Remove role from user
  const handleRemoveRole = async (role) => {
    try {
      const response = await fetch(`/api/v1/admin/users/${currentUser.id}/roles/${role}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to remove role');

      setUserRoles(userRoles.filter(r => r !== role));
      showToast('Role removed successfully');
      fetchUsers(); // Refresh user list to show updated roles
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // View sessions
  const handleViewSessions = async (user) => {
    setCurrentUser(user);
    setSessionModalOpen(true);

    try {
      const response = await fetch(`/api/v1/admin/users/${user.id}/sessions`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch sessions');

      const data = await response.json();
      setUserSessions(data.sessions || []);
    } catch (err) {
      showToast('Failed to load sessions', 'error');
      setUserSessions([]);
    }
  };

  // Logout user (all sessions)
  const handleLogoutUser = async () => {
    try {
      const response = await fetch(`/api/v1/admin/users/${currentUser.id}/sessions`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to logout user');

      showToast('User logged out successfully');
      setSessionModalOpen(false);
      setCurrentUser(null);
      setUserSessions([]);
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Get user initials for avatar
  const getUserInitials = (user) => {
    const first = user.firstName?.[0] || '';
    const last = user.lastName?.[0] || '';
    return (first + last).toUpperCase() || user.username?.[0]?.toUpperCase() || '?';
  };

  // Get status chip color
  const getStatusColor = (enabled) => {
    return enabled ? 'success' : 'error';
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.total_users || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Users
                  </Typography>
                </Box>
                <PeopleIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.active_users || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Active Users
                  </Typography>
                </Box>
                <PersonAddIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.suspended_users || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Suspended Users
                  </Typography>
                </Box>
                <VerifiedUserIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'warning.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {Object.values(stats.tier_distribution || {}).reduce((a, b) => a + b, 0)}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Subscribed Users
                  </Typography>
                </Box>
                <AdminIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" fontWeight="bold">
            User Management
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateUser}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              },
            }}
          >
            Create User
          </Button>
        </Box>

        {/* Search and Filter Controls */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={5}>
            <TextField
              fullWidth
              placeholder="Search by name, email, or username"
              value={searchQuery}
              onChange={handleSearch}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={6} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={
                <Badge badgeContent={getActiveFilterCount()} color="error">
                  <FilterListIcon />
                </Badge>
              }
              endIcon={advancedFiltersOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              onClick={() => setAdvancedFiltersOpen(!advancedFiltersOpen)}
              sx={{ height: '56px' }}
            >
              Filters
            </Button>
          </Grid>
          <Grid item xs={6} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => {
                fetchUsers();
                fetchStats();
              }}
              sx={{ height: '56px' }}
            >
              Refresh
            </Button>
          </Grid>
          <Grid item xs={12} md={3}>
            {getActiveFilterCount() > 0 && (
              <Button
                fullWidth
                variant="outlined"
                color="error"
                startIcon={<CloseIcon />}
                onClick={handleClearFilters}
                sx={{ height: '56px' }}
              >
                Clear Filters ({getActiveFilterCount()})
              </Button>
            )}
          </Grid>
        </Grid>

        {/* Filter Presets */}
        {getActiveFilterCount() === 0 && (
          <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Chip
              label="Active Users"
              icon={<PersonAddIcon />}
              onClick={() => applyFilterPreset('active')}
              clickable
            />
            <Chip
              label="Trial Users"
              icon={<PeopleIcon />}
              onClick={() => applyFilterPreset('trial')}
              clickable
            />
            <Chip
              label="Admins"
              icon={<AdminIcon />}
              onClick={() => applyFilterPreset('admins')}
              clickable
            />
            <Chip
              label="Inactive Users"
              icon={<SecurityIcon />}
              onClick={() => applyFilterPreset('inactive')}
              clickable
            />
          </Box>
        )}

        {/* Advanced Filters Panel */}
        <Collapse in={advancedFiltersOpen}>
          <Paper sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Typography variant="h6" gutterBottom>
              Advanced Filters
            </Typography>
            <Grid container spacing={2}>
              {/* Subscription Tier */}
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Subscription Tier</InputLabel>
                  <Select
                    multiple
                    value={filters.tiers}
                    onChange={(e) =>
                      setFilters({ ...filters, tiers: e.target.value })
                    }
                    label="Subscription Tier"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    <MenuItem value="trial">Trial</MenuItem>
                    <MenuItem value="starter">Starter</MenuItem>
                    <MenuItem value="professional">Professional</MenuItem>
                    <MenuItem value="enterprise">Enterprise</MenuItem>
                    <MenuItem value="founders">Founders Friend</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Brigade Roles */}
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Brigade Roles</InputLabel>
                  <Select
                    multiple
                    value={filters.roles}
                    onChange={(e) =>
                      setFilters({ ...filters, roles: e.target.value })
                    }
                    label="Brigade Roles"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {Array.isArray(selected) && selected.map((value) => (
                          <Chip
                            key={value}
                            label={typeof value === 'string' ? value.replace(/^brigade-(platform-)?/, '') : String(value || '')}
                            size="small"
                          />
                        ))}
                      </Box>
                    )}
                  >
                    {availableRoles.map((role) => (
                      <MenuItem key={role} value={role}>
                        <Checkbox checked={filters.roles.indexOf(role) > -1} />
                        <ListItemText primary={typeof role === 'string' ? role.replace(/^brigade-(platform-)?/, '') : String(role || '')} />
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              {/* Account Status */}
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Account Status</InputLabel>
                  <Select
                    multiple
                    value={filters.statuses}
                    onChange={(e) =>
                      setFilters({ ...filters, statuses: e.target.value })
                    }
                    label="Account Status"
                    renderValue={(selected) => (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                        {selected.map((value) => (
                          <Chip key={value} label={value} size="small" />
                        ))}
                      </Box>
                    )}
                  >
                    <MenuItem value="active">
                      <Checkbox checked={filters.statuses.indexOf('active') > -1} />
                      <ListItemText primary="Active" />
                    </MenuItem>
                    <MenuItem value="suspended">
                      <Checkbox checked={filters.statuses.indexOf('suspended') > -1} />
                      <ListItemText primary="Suspended" />
                    </MenuItem>
                    <MenuItem value="trial_expired">
                      <Checkbox checked={filters.statuses.indexOf('trial_expired') > -1} />
                      <ListItemText primary="Trial Expired" />
                    </MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* Registration Date Range */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Registration Date Range
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="date"
                      label="From"
                      value={filters.created_from}
                      onChange={(e) =>
                        setFilters({ ...filters, created_from: e.target.value })
                      }
                      InputLabelProps={{ shrink: true }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <CalendarIcon fontSize="small" />
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="date"
                      label="To"
                      value={filters.created_to}
                      onChange={(e) =>
                        setFilters({ ...filters, created_to: e.target.value })
                      }
                      InputLabelProps={{ shrink: true }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <CalendarIcon fontSize="small" />
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                </Grid>
              </Grid>

              {/* Last Login Date Range */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Last Login Date Range
                </Typography>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="date"
                      label="From"
                      value={filters.last_login_from}
                      onChange={(e) =>
                        setFilters({ ...filters, last_login_from: e.target.value })
                      }
                      InputLabelProps={{ shrink: true }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <CalendarIcon fontSize="small" />
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={6}>
                    <TextField
                      fullWidth
                      type="date"
                      label="To"
                      value={filters.last_login_to}
                      onChange={(e) =>
                        setFilters({ ...filters, last_login_to: e.target.value })
                      }
                      InputLabelProps={{ shrink: true }}
                      InputProps={{
                        startAdornment: (
                          <InputAdornment position="start">
                            <CalendarIcon fontSize="small" />
                          </InputAdornment>
                        ),
                      }}
                    />
                  </Grid>
                </Grid>
              </Grid>

              {/* Organization ID */}
              <Grid item xs={12} md={4}>
                <TextField
                  fullWidth
                  label="Organization ID"
                  value={filters.org_id}
                  onChange={(e) =>
                    setFilters({ ...filters, org_id: e.target.value })
                  }
                  placeholder="Filter by org ID"
                />
              </Grid>

              {/* Email Verified */}
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>Email Verified</InputLabel>
                  <Select
                    value={filters.email_verified ?? ''}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        email_verified: e.target.value === '' ? null : e.target.value === 'true',
                      })
                    }
                    label="Email Verified"
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="true">Verified Only</MenuItem>
                    <MenuItem value="false">Unverified Only</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              {/* BYOK Enabled */}
              <Grid item xs={12} md={4}>
                <FormControl fullWidth>
                  <InputLabel>BYOK Enabled</InputLabel>
                  <Select
                    value={filters.byok_enabled ?? ''}
                    onChange={(e) =>
                      setFilters({
                        ...filters,
                        byok_enabled: e.target.value === '' ? null : e.target.value === 'true',
                      })
                    }
                    label="BYOK Enabled"
                  >
                    <MenuItem value="">All</MenuItem>
                    <MenuItem value="true">BYOK Enabled</MenuItem>
                    <MenuItem value="false">BYOK Disabled</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            {/* Active Filters Display */}
            {getActiveFilterCount() > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Active Filters:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {filters.tiers.map((tier) => (
                    <Chip
                      key={tier}
                      label={`Tier: ${tier}`}
                      onDelete={() =>
                        setFilters({
                          ...filters,
                          tiers: filters.tiers.filter((t) => t !== tier),
                        })
                      }
                      size="small"
                      color="primary"
                    />
                  ))}
                  {Array.isArray(filters.roles) && filters.roles.map((role) => (
                    <Chip
                      key={role}
                      label={`Role: ${typeof role === 'string' ? role.replace(/^brigade-(platform-)?/, '') : String(role || '')}`}
                      onDelete={() =>
                        setFilters({
                          ...filters,
                          roles: filters.roles.filter((r) => r !== role),
                        })
                      }
                      size="small"
                      color="secondary"
                    />
                  ))}
                  {filters.statuses.map((status) => (
                    <Chip
                      key={status}
                      label={`Status: ${status}`}
                      onDelete={() =>
                        setFilters({
                          ...filters,
                          statuses: filters.statuses.filter((s) => s !== status),
                        })
                      }
                      size="small"
                      color="info"
                    />
                  ))}
                  {filters.org_id && (
                    <Chip
                      label={`Org: ${filters.org_id.substring(0, 8)}...`}
                      onDelete={() => setFilters({ ...filters, org_id: '' })}
                      size="small"
                    />
                  )}
                  {(filters.created_from || filters.created_to) && (
                    <Chip
                      label={`Registered: ${filters.created_from || '...'} to ${filters.created_to || '...'}`}
                      onDelete={() =>
                        setFilters({ ...filters, created_from: '', created_to: '' })
                      }
                      size="small"
                    />
                  )}
                  {(filters.last_login_from || filters.last_login_to) && (
                    <Chip
                      label={`Last Login: ${filters.last_login_from || '...'} to ${filters.last_login_to || '...'}`}
                      onDelete={() =>
                        setFilters({ ...filters, last_login_from: '', last_login_to: '' })
                      }
                      size="small"
                    />
                  )}
                  {filters.email_verified !== null && (
                    <Chip
                      label={`Email: ${filters.email_verified ? 'Verified' : 'Unverified'}`}
                      onDelete={() => setFilters({ ...filters, email_verified: null })}
                      size="small"
                    />
                  )}
                  {filters.byok_enabled !== null && (
                    <Chip
                      label={`BYOK: ${filters.byok_enabled ? 'Enabled' : 'Disabled'}`}
                      onDelete={() => setFilters({ ...filters, byok_enabled: null })}
                      size="small"
                    />
                  )}
                </Box>
              </Box>
            )}
          </Paper>
        </Collapse>

        {/* Results Count */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Showing {users.length} users {getActiveFilterCount() > 0 && `(${getActiveFilterCount()} filter${getActiveFilterCount() !== 1 ? 's' : ''} applied)`}
          {totalUsers > 0 && ` of ${totalUsers} total`}
        </Typography>

        {/* User Table */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Avatar</TableCell>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Username</TableCell>
                    <TableCell>Roles</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {/* REFACTORED: Using safeMap for defensive rendering */}
                  {safeMap(users, (user) => (
                    <TableRow
                      key={user.id}
                      hover
                      onClick={() => navigate(`/admin/people/users/${user.user_id || user.id}`)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Avatar sx={{ bgcolor: 'primary.main' }}>
                          {getUserInitials(user)}
                        </Avatar>
                      </TableCell>
                      <TableCell>
                        {user.firstName} {user.lastName}
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {user.email}
                          {user.emailVerified && (
                            <Tooltip title="Email Verified">
                              <VerifiedUserIcon color="success" fontSize="small" />
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>{user.username}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {/* REFACTORED: Using safeMap to prevent crashes on missing roles */}
                          {safeMap(user.roles, (role) => (
                            <Chip
                              key={role}
                              label={role}
                              size="small"
                              color={role.includes('admin') ? 'error' : 'default'}
                            />
                          ))}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={user.enabled ? 'Enabled' : 'Disabled'}
                          color={getStatusColor(user.enabled)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/admin/people/users/${user.user_id || user.id}`);
                            }}
                            color="primary"
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleEditUser(user);
                            }}
                            color="primary"
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Manage Roles">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleManageRoles(user);
                            }}
                            color="info"
                          >
                            <SecurityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Reset Password">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              setCurrentUser(user);
                              setResetPasswordOpen(true);
                            }}
                            color="warning"
                          >
                            <VpnKeyIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Sessions">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewSessions(user);
                            }}
                            color="success"
                          >
                            <LogoutIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              setCurrentUser(user);
                              setDeleteConfirmOpen(true);
                            }}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              count={totalUsers}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[5, 10, 25, 50]}
            />
          </>
        )}
      </Paper>

      {/* Create User Modal (Comprehensive) */}
      {!isEditMode && (
        <CreateUserModal
          open={createEditModalOpen}
          onClose={() => setCreateEditModalOpen(false)}
          onSuccess={() => {
            setCreateEditModalOpen(false);
            fetchUsers();
            fetchStats();
            showToast('User created successfully');
          }}
        />
      )}

      {/* Edit User Modal (Simple) */}
      {isEditMode && (
        <Dialog
          open={createEditModalOpen}
          onClose={() => setCreateEditModalOpen(false)}
          maxWidth="sm"
          fullWidth
        >
          <DialogTitle>Edit User</DialogTitle>
          <DialogContent>
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    value={formData.firstName}
                    onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    value={formData.lastName}
                    onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Username"
                    required
                    value={formData.username}
                    onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.enabled}
                        onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                      />
                    }
                    label="Enabled"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={formData.emailVerified}
                        onChange={(e) => setFormData({ ...formData, emailVerified: e.target.checked })}
                      />
                    }
                    label="Email Verified"
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateEditModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="contained"
              onClick={handleSaveUser}
              disabled={!formData.email || !formData.username}
            >
              Update
            </Button>
          </DialogActions>
        </Dialog>
      )}

      {/* Enhanced Role Management Modal */}
      <RoleManagementModal
        open={roleModalOpen}
        onClose={() => {
          setRoleModalOpen(false);
          setCurrentUser(null);
          setUserRoles([]);
        }}
        user={currentUser ? { ...currentUser, roles: userRoles } : null}
        availableRoles={availableRoles}
        onRoleAssign={async (userId, role) => {
          await handleAddRole(role);
        }}
        onRoleRemove={async (userId, role) => {
          await handleRemoveRole(role);
        }}
      />

      {/* Session Management Modal */}
      <Dialog
        open={sessionModalOpen}
        onClose={() => setSessionModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Active Sessions - {currentUser?.username}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            {userSessions.length === 0 ? (
              <Alert severity="info">No active sessions</Alert>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>IP Address</TableCell>
                      <TableCell>Started</TableCell>
                      <TableCell>Last Activity</TableCell>
                      <TableCell>Client</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {/* REFACTORED: Using safeMap for session list */}
                    {safeMap(userSessions, (session, index) => (
                      <TableRow key={index}>
                        <TableCell>{session.ipAddress || 'Unknown'}</TableCell>
                        <TableCell>
                          {session.started ? new Date(session.started).toLocaleString() : 'Unknown'}
                        </TableCell>
                        <TableCell>
                          {session.lastActivity ? new Date(session.lastActivity).toLocaleString() : 'Unknown'}
                        </TableCell>
                        <TableCell>{session.client || 'Unknown'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSessionModalOpen(false)}>
            Close
          </Button>
          {userSessions.length > 0 && (
            <Button
              variant="contained"
              color="error"
              startIcon={<LogoutIcon />}
              onClick={handleLogoutUser}
            >
              Logout All Sessions
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user <strong>{currentUser?.username}</strong>?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteUser}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Password Confirmation Modal */}
      <Dialog
        open={resetPasswordOpen}
        onClose={() => setResetPasswordOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Reset Password</DialogTitle>
        <DialogContent>
          <Typography>
            Reset password for user <strong>{currentUser?.username}</strong>?
            A temporary password will be generated and sent to their email.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResetPasswordOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="warning"
            onClick={handleResetPassword}
          >
            Reset Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notification */}
      <Snackbar
        open={toast.open}
        autoHideDuration={6000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setToast({ ...toast, open: false })}
          severity={toast.severity}
          sx={{ width: '100%' }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default UserManagement;
