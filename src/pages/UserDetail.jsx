import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Avatar,
  Chip,
  Button,
  IconButton,
  Divider,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  LinearProgress,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Breadcrumbs,
  Link,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Badge,
  Skeleton,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Edit as EditIcon,
  Save as SaveIcon,
  Cancel as CancelIcon,
  VpnKey as VpnKeyIcon,
  Security as SecurityIcon,
  Block as BlockIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  VerifiedUser as VerifiedUserIcon,
  Business as BusinessIcon,
  History as HistoryIcon,
  Assessment as AssessmentIcon,
  Devices as DevicesIcon,
  Api as ApiIcon,
  AdminPanelSettings as AdminIcon,
  PersonOff as PersonOffIcon,
  NavigateNext as NavigateNextIcon,
} from '@mui/icons-material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

const UserDetail = () => {
  const { userId } = useParams();
  const navigate = useNavigate();

  // State
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [currentAction, setCurrentAction] = useState(null);

  // Fetch user profile
  const fetchProfile = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/profile`, {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch user profile');

      const data = await response.json();
      setProfile(data.profile);
      setEditData({
        first_name: data.profile.first_name,
        last_name: data.profile.last_name,
        email: data.profile.email,
      });
    } catch (err) {
      setError(err.message);
      showToast('Failed to load user profile', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [userId]);

  // Show toast notification
  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Handle edit mode
  const handleEditToggle = () => {
    setEditing(!editing);
    if (!editing) {
      setEditData({
        first_name: profile.first_name,
        last_name: profile.last_name,
        email: profile.email,
      });
    }
  };

  // Save user edits
  const handleSaveEdit = async () => {
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          firstName: editData.first_name,
          lastName: editData.last_name,
          email: editData.email,
        }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to update user');

      showToast('User updated successfully');
      setEditing(false);
      fetchProfile();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Handle user actions
  const handleAction = async (action) => {
    setCurrentAction(action);
    setActionDialogOpen(true);
  };

  const executeAction = async () => {
    try {
      let endpoint = '';
      let method = 'POST';
      let body = null;

      switch (currentAction) {
        case 'suspend':
          endpoint = `/api/v1/admin/users/${userId}/suspend`;
          body = JSON.stringify({ reason: 'Suspended by admin', notify_user: true });
          break;
        case 'activate':
          endpoint = `/api/v1/admin/users/${userId}/activate`;
          body = JSON.stringify({ reason: 'Activated by admin', notify_user: true });
          break;
        case 'reset_password':
          endpoint = `/api/v1/admin/users/${userId}/reset-password`;
          body = JSON.stringify({ temporary: true, send_email: true });
          break;
        case 'delete':
          endpoint = `/api/v1/admin/users/${userId}`;
          method = 'DELETE';
          break;
        case 'reset_usage':
          endpoint = `/api/v1/admin/users/${userId}/credits/add`;
          body = JSON.stringify({ credits: -profile.api_usage.calls_used, reason: 'Reset by admin' });
          break;
        case 'revoke_sessions':
          endpoint = `/api/v1/admin/users/${userId}/sessions`;
          method = 'DELETE';
          break;
        default:
          throw new Error('Unknown action');
      }

      const response = await fetch(endpoint, {
        method,
        headers: body ? { 'Content-Type': 'application/json' } : {},
        body,
        credentials: 'include',
      });

      if (!response.ok) throw new Error(`Failed to ${currentAction}`);

      const actionLabels = {
        suspend: 'suspended',
        activate: 'activated',
        reset_password: 'password reset',
        delete: 'deleted',
        reset_usage: 'usage reset',
        revoke_sessions: 'sessions revoked',
      };

      showToast(`User ${actionLabels[currentAction]} successfully`);
      setActionDialogOpen(false);
      setCurrentAction(null);

      if (currentAction === 'delete') {
        navigate('/admin/system/users');
      } else {
        fetchProfile();
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Get user initials
  const getUserInitials = () => {
    if (!profile) return '?';
    const first = profile.first_name?.[0] || '';
    const last = profile.last_name?.[0] || '';
    return (first + last).toUpperCase() || profile.username?.[0]?.toUpperCase() || '?';
  };

  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'suspended':
        return 'error';
      case 'expired':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Get tier badge color
  const getTierColor = (tier) => {
    switch (tier?.toLowerCase()) {
      case 'trial':
        return { bg: '#FFF3E0', text: '#E65100' };
      case 'starter':
        return { bg: '#E3F2FD', text: '#1565C0' };
      case 'professional':
        return { bg: '#F3E5F5', text: '#6A1B9A' };
      case 'enterprise':
        return { bg: '#E8F5E9', text: '#2E7D32' };
      default:
        return { bg: '#F5F5F5', text: '#616161' };
    }
  };

  // Format date
  const formatDate = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  // Format relative time
  const formatRelativeTime = (isoString) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 7) return date.toLocaleDateString();
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };

  // Get action icon
  const getActionIcon = (action) => {
    const icons = {
      auth: <SecurityIcon fontSize="small" />,
      user: <AdminIcon fontSize="small" />,
      role: <VerifiedUserIcon fontSize="small" />,
      subscription: <AssessmentIcon fontSize="small" />,
      api: <ApiIcon fontSize="small" />,
      session: <DevicesIcon fontSize="small" />,
    };
    const category = action.split('.')[0];
    return icons[category] || <HistoryIcon fontSize="small" />;
  };

  // Loading skeleton
  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Skeleton variant="rectangular" height={200} sx={{ mb: 2 }} />
        <Grid container spacing={3}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Grid item xs={12} md={6} key={i}>
              <Skeleton variant="rectangular" height={300} />
            </Grid>
          ))}
        </Grid>
      </Container>
    );
  }

  // Error state
  if (error || !profile) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error" action={
          <Button color="inherit" onClick={() => navigate('/admin/system/users')}>
            Go Back
          </Button>
        }>
          {error || 'User not found'}
        </Alert>
      </Container>
    );
  }

  const tierColor = getTierColor(profile.subscription.tier);

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} sx={{ mb: 2 }}>
        <Link
          underline="hover"
          color="inherit"
          href="#"
          onClick={() => navigate('/admin/dashboard')}
        >
          Dashboard
        </Link>
        <Link
          underline="hover"
          color="inherit"
          href="#"
          onClick={() => navigate('/admin/system/users')}
        >
          Users
        </Link>
        <Typography color="text.primary">{profile.username}</Typography>
      </Breadcrumbs>

      {/* Header Card */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item>
            <Avatar
              sx={{
                width: 100,
                height: 100,
                bgcolor: 'primary.main',
                fontSize: '2rem',
              }}
            >
              {getUserInitials()}
            </Avatar>
          </Grid>
          <Grid item xs>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
              <Typography variant="h4" fontWeight="bold">
                {profile.full_name || profile.username}
              </Typography>
              {profile.email_verified && (
                <Tooltip title="Email Verified">
                  <VerifiedUserIcon color="success" />
                </Tooltip>
              )}
              <Chip
                label={profile.enabled ? 'Active' : 'Suspended'}
                color={profile.enabled ? 'success' : 'error'}
                size="small"
              />
              <Chip
                label={profile.subscription.tier}
                sx={{
                  bgcolor: tierColor.bg,
                  color: tierColor.text,
                  fontWeight: 'bold',
                  textTransform: 'uppercase',
                }}
                size="small"
              />
            </Box>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {profile.email}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>User ID:</strong> {profile.user_id}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              <strong>Joined:</strong> {formatDate(profile.created_at)} ({formatRelativeTime(profile.created_at_iso)})
            </Typography>
          </Grid>
          <Grid item>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<ArrowBackIcon />}
                onClick={() => navigate('/admin/system/users')}
              >
                Back to Users
              </Button>
              <Button
                variant="contained"
                startIcon={editing ? <SaveIcon /> : <EditIcon />}
                onClick={editing ? handleSaveEdit : handleEditToggle}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                }}
              >
                {editing ? 'Save Changes' : 'Edit User'}
              </Button>
              {editing && (
                <Button
                  variant="outlined"
                  startIcon={<CancelIcon />}
                  onClick={handleEditToggle}
                >
                  Cancel
                </Button>
              )}
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Quick Actions */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom fontWeight="bold">
          Quick Actions
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Button
            size="small"
            variant="outlined"
            startIcon={<VpnKeyIcon />}
            onClick={() => handleAction('reset_password')}
          >
            Reset Password
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<DevicesIcon />}
            onClick={() => handleAction('revoke_sessions')}
            disabled={profile.sessions.active_count === 0}
          >
            Revoke Sessions ({profile.sessions.active_count})
          </Button>
          <Button
            size="small"
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => handleAction('reset_usage')}
            disabled={profile.api_usage.calls_used === 0}
          >
            Reset API Usage
          </Button>
          {profile.enabled ? (
            <Button
              size="small"
              variant="outlined"
              color="warning"
              startIcon={<BlockIcon />}
              onClick={() => handleAction('suspend')}
            >
              Suspend Account
            </Button>
          ) : (
            <Button
              size="small"
              variant="outlined"
              color="success"
              startIcon={<CheckCircleIcon />}
              onClick={() => handleAction('activate')}
            >
              Activate Account
            </Button>
          )}
          <Button
            size="small"
            variant="outlined"
            color="error"
            startIcon={<DeleteIcon />}
            onClick={() => handleAction('delete')}
          >
            Delete User
          </Button>
        </Box>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={handleTabChange} variant="scrollable" scrollButtons="auto">
          <Tab label="Overview" />
          <Tab label="Subscription & Billing" />
          <Tab label="Roles & Permissions" />
          <Tab label="Organizations" />
          <Tab label="Activity Timeline" />
          <Tab label="API Usage" />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      {/* Overview Tab */}
      {tabValue === 0 && (
        <Grid container spacing={3}>
          {/* Account Details */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Account Details
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {editing ? (
                  <Box component="form" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                    <TextField
                      label="First Name"
                      value={editData.first_name}
                      onChange={(e) => setEditData({ ...editData, first_name: e.target.value })}
                      fullWidth
                    />
                    <TextField
                      label="Last Name"
                      value={editData.last_name}
                      onChange={(e) => setEditData({ ...editData, last_name: e.target.value })}
                      fullWidth
                    />
                    <TextField
                      label="Email"
                      type="email"
                      value={editData.email}
                      onChange={(e) => setEditData({ ...editData, email: e.target.value })}
                      fullWidth
                    />
                  </Box>
                ) : (
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Username" secondary={profile.username} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Email" secondary={profile.email} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Full Name" secondary={profile.full_name || 'Not provided'} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Status" secondary={
                        <Chip label={profile.enabled ? 'Active' : 'Suspended'} color={profile.enabled ? 'success' : 'error'} size="small" />
                      } />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Email Verified" secondary={
                        <Chip label={profile.email_verified ? 'Yes' : 'No'} color={profile.email_verified ? 'success' : 'warning'} size="small" />
                      } />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Account Source" secondary={profile.account_source} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Created" secondary={formatDate(profile.created_at)} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Last Login" secondary={profile.last_login ? formatDate(profile.last_login) : 'Never'} />
                    </ListItem>
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* API Usage Summary */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  API Usage
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Box sx={{ mb: 3 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                    <Typography variant="body2">
                      {profile.api_usage.calls_used.toLocaleString()} / {profile.api_usage.calls_limit.toLocaleString()} calls
                    </Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {profile.api_usage.usage_percentage}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(profile.api_usage.usage_percentage, 100)}
                    sx={{
                      height: 10,
                      borderRadius: 5,
                      bgcolor: 'grey.200',
                      '& .MuiLinearProgress-bar': {
                        bgcolor: profile.api_usage.usage_percentage > 90 ? 'error.main' :
                          profile.api_usage.usage_percentage > 75 ? 'warning.main' : 'success.main',
                      },
                    }}
                  />
                </Box>
                <List dense>
                  <ListItem>
                    <ListItemText primary="Calls Used" secondary={profile.api_usage.calls_used.toLocaleString()} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Calls Limit" secondary={profile.api_usage.calls_limit.toLocaleString()} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Reset Date" secondary={profile.api_usage.reset_date || 'Not set'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="BYOK Enabled" secondary={
                      <Chip label={profile.api_usage.byok_enabled ? 'Yes' : 'No'} color={profile.api_usage.byok_enabled ? 'success' : 'default'} size="small" />
                    } />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Rate Limit (per minute)" secondary={profile.api_usage.rate_limits.per_minute} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Rate Limit (per day)" secondary={profile.api_usage.rate_limits.per_day} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Active Sessions */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Active Sessions ({profile.sessions.active_count})
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {profile.sessions.sessions.length === 0 ? (
                  <Alert severity="info">No active sessions</Alert>
                ) : (
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>IP Address</TableCell>
                          <TableCell>Started</TableCell>
                          <TableCell>Last Activity</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {profile.sessions.sessions.slice(0, 5).map((session, index) => (
                          <TableRow key={index}>
                            <TableCell>{session.ipAddress || 'Unknown'}</TableCell>
                            <TableCell>{formatRelativeTime(session.started)}</TableCell>
                            <TableCell>{formatRelativeTime(session.lastActivity)}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Recent Activity */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Recent Activity
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {profile.activity.recent_actions.length === 0 ? (
                  <Alert severity="info">No recent activity</Alert>
                ) : (
                  <List dense>
                    {profile.activity.recent_actions.map((action, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          {getActionIcon(action.action)}
                        </ListItemIcon>
                        <ListItemText
                          primary={action.action}
                          secondary={
                            <>
                              <Typography component="span" variant="body2">
                                {formatRelativeTime(action.timestamp)}
                              </Typography>
                              {' • '}
                              <Chip label={action.result} size="small" color={action.result === 'success' ? 'success' : 'error'} />
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Subscription & Billing Tab */}
      {tabValue === 1 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Subscription Details
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <List dense>
                  <ListItem>
                    <ListItemText primary="Current Tier" secondary={
                      <Chip
                        label={profile.subscription.tier}
                        sx={{
                          bgcolor: tierColor.bg,
                          color: tierColor.text,
                          fontWeight: 'bold',
                        }}
                      />
                    } />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Status" secondary={
                      <Chip label={profile.subscription.status} color={getStatusColor(profile.subscription.status)} />
                    } />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Billing Email" secondary={profile.subscription.billing_email} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Stripe Customer ID" secondary={profile.subscription.stripe_customer_id || 'Not set'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Lago Customer ID" secondary={profile.subscription.lago_customer_id || 'Not set'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Start Date" secondary={profile.subscription.start_date || 'Not set'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="End Date" secondary={profile.subscription.end_date || 'Ongoing'} />
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Billing History
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Alert severity="info">
                  Billing history coming soon
                </Alert>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Roles & Permissions Tab */}
      {tabValue === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Assigned Roles ({profile.roles.length})
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {profile.role_details.length === 0 ? (
                  <Alert severity="info">No roles assigned</Alert>
                ) : (
                  <Grid container spacing={2}>
                    {profile.role_details.map((role, index) => (
                      <Grid item xs={12} md={6} key={index}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                              <Typography variant="h6">
                                {role.display_name}
                              </Typography>
                              <Chip label={`Level ${role.level}`} size="small" color="primary" />
                            </Box>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                              {role.description}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              <strong>Role Key:</strong> {role.name}
                            </Typography>
                            {role.permissions && role.permissions.length > 0 && (
                              <Box sx={{ mt: 2 }}>
                                <Typography variant="caption" fontWeight="bold">Permissions:</Typography>
                                <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap', mt: 1 }}>
                                  {role.permissions.map((perm, i) => (
                                    <Chip key={i} label={perm} size="small" variant="outlined" />
                                  ))}
                                </Box>
                              </Box>
                            )}
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Organizations Tab */}
      {tabValue === 3 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Organization Memberships ({profile.organizations.length})
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {profile.organizations.length === 0 ? (
                  <Alert severity="info">Not a member of any organizations</Alert>
                ) : (
                  <Grid container spacing={2}>
                    {profile.organizations.map((org, index) => (
                      <Grid item xs={12} md={6} key={index}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                              <Avatar sx={{ bgcolor: 'primary.main' }}>
                                <BusinessIcon />
                              </Avatar>
                              <Box sx={{ flex: 1 }}>
                                <Typography variant="h6">{org.name}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {org.id}
                                </Typography>
                              </Box>
                            </Box>
                            <Box sx={{ display: 'flex', gap: 1 }}>
                              <Chip label={org.role} color="primary" size="small" />
                              <Chip label={org.plan_tier} size="small" />
                              <Chip label={org.status} color={getStatusColor(org.status)} size="small" />
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Activity Timeline Tab */}
      {tabValue === 4 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  Activity Timeline ({profile.activity.total_actions} actions)
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {profile.activity.timeline.length === 0 ? (
                  <Alert severity="info">No activity recorded</Alert>
                ) : (
                  <List dense>
                    {profile.activity.timeline.map((action, index) => (
                      <ListItem key={index} divider={index < profile.activity.timeline.length - 1}>
                        <ListItemIcon>
                          {getActionIcon(action.action)}
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1">{action.action}</Typography>
                              <Chip
                                label={action.result}
                                size="small"
                                color={action.result === 'success' ? 'success' : 'error'}
                              />
                            </Box>
                          }
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.secondary">
                                {formatDate(action.timestamp)} ({formatRelativeTime(action.timestamp)})
                              </Typography>
                              {action.ip_address && (
                                <>
                                  {' • '}
                                  <Typography component="span" variant="body2" color="text.secondary">
                                    IP: {action.ip_address}
                                  </Typography>
                                </>
                              )}
                              {action.resource_type && (
                                <>
                                  {' • '}
                                  <Typography component="span" variant="body2" color="text.secondary">
                                    Resource: {action.resource_type}
                                  </Typography>
                                </>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* API Usage Tab */}
      {tabValue === 5 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom fontWeight="bold">
                  API Usage Details
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h4" color="primary">
                          {profile.api_usage.calls_used.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Calls Used
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h4" color="success.main">
                          {profile.api_usage.calls_limit.toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Calls Limit
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h4" color={profile.api_usage.usage_percentage > 90 ? 'error.main' : 'warning.main'}>
                          {profile.api_usage.usage_percentage}%
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Usage Percentage
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                  <Grid item xs={12} sm={6} md={3}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h4" color="info.main">
                          {(profile.api_usage.calls_limit - profile.api_usage.calls_used).toLocaleString()}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Calls Remaining
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                </Grid>

                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" gutterBottom fontWeight="bold">
                    Rate Limits
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText primary="Per Minute" secondary={`${profile.api_usage.rate_limits.per_minute} requests`} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Per Hour" secondary={`${profile.api_usage.rate_limits.per_hour} requests`} />
                    </ListItem>
                    <ListItem>
                      <ListItemText primary="Per Day" secondary={`${profile.api_usage.rate_limits.per_day} requests`} />
                    </ListItem>
                  </List>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Action Confirmation Dialog */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)}>
        <DialogTitle>
          Confirm Action
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to {currentAction?.replace('_', ' ')} this user?
            {currentAction === 'delete' && (
              <Alert severity="warning" sx={{ mt: 2 }}>
                This action cannot be undone. All user data will be permanently deleted.
              </Alert>
            )}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>Cancel</Button>
          <Button onClick={executeAction} color={currentAction === 'delete' ? 'error' : 'primary'} variant="contained">
            Confirm
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
    </Container>
  );
};

export default UserDetail;
