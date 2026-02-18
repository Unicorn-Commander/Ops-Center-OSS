/**
 * Subscription Management Page
 * Admin interface for managing subscription tiers, apps, and user migrations
 * Epic 4.4: Subscription Management GUI
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  History as HistoryIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  AttachMoney as MoneyIcon,
  People as PeopleIcon,
  TrendingUp as TrendingUpIcon,
  Sync as SyncIcon,
  ExpandMore as ExpandMoreIcon,
  LocalOffer as TagIcon,
  ContentCopy as CloneIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';
import AdminBreadcrumbs from '../../components/admin/AdminBreadcrumbs';
import LoadingOverlay from '../../components/admin/LoadingOverlay';
import EmptyState from '../../components/admin/EmptyState';
import StatsCard from '../../components/admin/StatsCard';
import { TagIcon as TagIconHero, UsersIcon, CurrencyDollarIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

const SubscriptionManagement = () => {
  // State management
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false);
  const [appsDialogOpen, setAppsDialogOpen] = useState(false);
  const [migrationDialogOpen, setMigrationDialogOpen] = useState(false);
  const [auditLogDialogOpen, setAuditLogDialogOpen] = useState(false);

  // Selected tier for editing
  const [selectedTier, setSelectedTier] = useState(null);

  // Form data
  const [formData, setFormData] = useState({
    tier_code: '',
    tier_name: '',
    description: '',
    price_monthly: 0,
    price_yearly: 0,
    is_active: true,
    is_invite_only: false,
    sort_order: 0,
    api_calls_limit: 1000,
    team_seats: 1,
    byok_enabled: false,
    priority_support: false,
    lago_plan_code: '',
    stripe_price_monthly: '',
    stripe_price_yearly: ''
  });

  // Features data
  const [apps, setApps] = useState([]);
  const [appDefinitions, setAppDefinitions] = useState([]);

  // Migration data
  const [migrationData, setMigrationData] = useState({
    user_id: '',
    new_tier_code: '',
    reason: '',
    send_notification: true
  });

  // Audit log data
  const [auditLog, setAuditLog] = useState([]);
  const [auditPage, setAuditPage] = useState(0);
  const [auditRowsPerPage, setAuditRowsPerPage] = useState(10);

  // Tab state
  const [tabValue, setTabValue] = useState(0);

  // ============================================
  // API Functions
  // ============================================

  const fetchTiers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/tiers/', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch tiers');
      const data = await response.json();
      setTiers(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching tiers:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchFeatureDefinitions = async () => {
    try {
      const response = await fetch('/api/v1/admin/apps/?active_only=true', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch app definitions');
      const data = await response.json();
      setAppDefinitions(data.map(f => ({
        key: f.app_key,
        name: f.app_name,
        category: f.category
      })));
    } catch (err) {
      console.error('Error fetching app definitions:', err);
      // Keep empty array if fetch fails
    }
  };

  const fetchTierFeatures = async (tierCode) => {
    try {
      const response = await fetch(`/api/v1/tiers/${tierCode}/apps`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch apps');
      const data = await response.json();
      // API returns { tier_id, tier_code, tier_name, apps: [...] }
      return data.apps || [];
    } catch (err) {
      setError(err.message);
      console.error('Error fetching apps:', err);
      return [];
    }
  };

  const fetchFeatureCounts = async () => {
    try {
      // Fetch all tier-app associations
      const response = await fetch('/api/v1/tiers/apps', { credentials: 'include' });
      if (!response.ok) return; // Fail silently, counts will show 0

      const data = await response.json();

      // Count enabled features per tier
      const counts = {};
      data.forEach(tierData => {
        counts[tierData.tier_code] = tierData.apps ? tierData.apps.length : 0;
      });

      // Update tiers with feature counts
      setTiers(prev => prev.map(t => ({
        ...t,
        feature_count: counts[t.tier_code] || 0
      })));
    } catch (err) {
      console.error('Error fetching feature counts:', err);
      // Don't show error to user, just keep counts at 0
    }
  };

  const fetchAuditLog = async () => {
    try {
      const response = await fetch('/api/v1/admin/tiers/migrations', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch audit log');
      const data = await response.json();
      setAuditLog(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching audit log:', err);
    }
  };

  const createTier = async () => {
    try {
      const response = await fetch('/api/v1/admin/tiers/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create tier');
      }

      setSuccess('Tier created successfully');
      setCreateDialogOpen(false);
      fetchTiers();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error creating tier:', err);
    }
  };

  const updateTier = async () => {
    if (!selectedTier) return;

    try {
      const response = await fetch(`/api/v1/admin/tiers/${selectedTier.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update tier');
      }

      setSuccess('Tier updated successfully');
      setEditDialogOpen(false);
      fetchTiers();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error updating tier:', err);
    }
  };

  const deleteTier = async (tierId, tierCode) => {
    if (!confirm(`Are you sure you want to deactivate tier '${tierCode}'? This will mark it as inactive.`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/tiers/${tierId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to delete tier');

      setSuccess('Tier deactivated successfully');
      fetchTiers();
    } catch (err) {
      setError(err.message);
      console.error('Error deleting tier:', err);
    }
  };

  const cloneTier = async () => {
    if (!selectedTier) return;

    try {
      const params = new URLSearchParams({
        new_tier_code: formData.tier_code,
        new_tier_name: formData.tier_name,
        price_monthly: formData.price_monthly.toString()
      });

      const response = await fetch(`/api/v1/admin/tiers/${selectedTier.tier_code}/clone?${params}`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to clone tier');
      }

      setSuccess(`Tier cloned successfully as '${formData.tier_code}'`);
      setCloneDialogOpen(false);
      fetchTiers();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error cloning tier:', err);
    }
  };

  const updateTierFeatures = async () => {
    if (!selectedTier) return;

    try {
      // Format apps for the new API: array of { app_key, enabled }
      const updates = apps.map(f => ({
        app_key: f.app_key,
        enabled: f.enabled
      }));

      const response = await fetch(`/api/v1/admin/tiers/${selectedTier.tier_code}/apps`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates)
      });

      if (!response.ok) throw new Error('Failed to update apps');

      const result = await response.json();
      setSuccess(result.message || 'Apps updated successfully');
      setAppsDialogOpen(false);
      fetchTiers();
      fetchFeatureCounts(); // Update feature counts after saving
    } catch (err) {
      setError(err.message);
      console.error('Error updating apps:', err);
    }
  };

  const migrateUser = async () => {
    try {
      const response = await fetch(`/api/v1/admin/tiers/users/${migrationData.user_id}/migrate-tier`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(migrationData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to migrate user');
      }

      const result = await response.json();
      setSuccess(`User migrated successfully: ${result.message}`);
      setMigrationDialogOpen(false);
      resetMigrationForm();
    } catch (err) {
      setError(err.message);
      console.error('Error migrating user:', err);
    }
  };

  // ============================================
  // Form Handlers
  // ============================================

  const resetForm = () => {
    setFormData({
      tier_code: '',
      tier_name: '',
      description: '',
      price_monthly: 0,
      price_yearly: 0,
      is_active: true,
      is_invite_only: false,
      sort_order: 0,
      api_calls_limit: 1000,
      team_seats: 1,
      byok_enabled: false,
      priority_support: false,
      lago_plan_code: '',
      stripe_price_monthly: '',
      stripe_price_yearly: ''
    });
  };

  const resetMigrationForm = () => {
    setMigrationData({
      user_id: '',
      new_tier_code: '',
      reason: '',
      send_notification: true
    });
  };

  const handleEditTier = (tier) => {
    setSelectedTier(tier);
    setFormData({
      tier_code: tier.tier_code,
      tier_name: tier.tier_name,
      description: tier.description || '',
      price_monthly: tier.price_monthly,
      price_yearly: tier.price_yearly || 0,
      is_active: tier.is_active,
      is_invite_only: tier.is_invite_only,
      sort_order: tier.sort_order,
      api_calls_limit: tier.api_calls_limit,
      team_seats: tier.team_seats,
      byok_enabled: tier.byok_enabled,
      priority_support: tier.priority_support,
      lago_plan_code: tier.lago_plan_code || '',
      stripe_price_monthly: tier.stripe_price_monthly || '',
      stripe_price_yearly: tier.stripe_price_yearly || ''
    });
    setEditDialogOpen(true);
  };

  const handleCloneTier = (tier) => {
    setSelectedTier(tier);
    setFormData({
      tier_code: `${tier.tier_code}_v2`,
      tier_name: `${tier.tier_name} V2`,
      description: tier.description || '',
      price_monthly: tier.price_monthly,
      price_yearly: tier.price_yearly || 0,
      is_active: tier.is_active,
      is_invite_only: tier.is_invite_only,
      sort_order: tier.sort_order,
      api_calls_limit: tier.api_calls_limit,
      team_seats: tier.team_seats,
      byok_enabled: tier.byok_enabled,
      priority_support: tier.priority_support,
      lago_plan_code: '',
      stripe_price_monthly: '',
      stripe_price_yearly: ''
    });
    setCloneDialogOpen(true);
  };

  const handleManageFeatures = async (tier) => {
    setSelectedTier(tier);

    // Fetch currently enabled features for this tier
    const enabledFeatures = await fetchTierFeatures(tier.tier_code);

    // Initialize features with all definitions, marking which ones are enabled
    const initialFeatures = appDefinitions.map(def => {
      const isEnabled = enabledFeatures.some(f => f.app_key === def.key);
      return {
        app_key: def.key,
        enabled: isEnabled
      };
    });

    setApps(initialFeatures);
    setAppsDialogOpen(true);
  };

  const toggleFeature = (featureKey) => {
    setApps(prev => prev.map(f =>
      f.app_key === featureKey ? { ...f, enabled: !f.enabled } : f
    ));
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    fetchTiers();
    fetchFeatureDefinitions();
    fetchFeatureCounts();
  }, []);

  // ============================================
  // Render Helpers
  // ============================================

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(price);
  };

  const formatApiLimit = (limit) => {
    if (limit === -1) return 'Unlimited';
    return limit.toLocaleString();
  };

  // Get tier badge color styling (VIP Founder = Gold)
  const getTierBadgeColor = (tierCode) => {
    switch (tierCode) {
      case 'vip_founder':
        return { bg: 'rgba(255, 215, 0, 0.15)', color: '#FFD700', border: '#FFD700' };
      case 'byok':
        return { bg: 'rgba(124, 58, 237, 0.15)', color: '#7c3aed', border: '#7c3aed' };
      case 'managed':
        return { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: '#3b82f6' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: '#94a3b8' };
    }
  };

  // ============================================
  // Main Render
  // ============================================

  if (loading && tiers.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <AdminBreadcrumbs />
        <PageHeader
          title="Subscription Management"
          subtitle="Manage subscription tiers, apps, and user migrations"
        />
        <LoadingOverlay loading={true} message="Loading subscription tiers..." />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Breadcrumbs */}
      <AdminBreadcrumbs />

      {/* Header */}
      <PageHeader
        title="Subscription Management"
        subtitle="Manage subscription tiers, apps, and user migrations"
        actions={(
          <>
            <Button
              variant="outlined"
              startIcon={<HistoryIcon />}
              onClick={() => {
                fetchAuditLog();
                setAuditLogDialogOpen(true);
              }}
            >
              Audit Log
            </Button>
            <Button
              variant="outlined"
              startIcon={<PeopleIcon />}
              onClick={() => setMigrationDialogOpen(true)}
            >
              Migrate User
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                resetForm();
                setCreateDialogOpen(true);
              }}
            >
              Create Tier
            </Button>
          </>
        )}
      />

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Analytics Cards - Using standardized StatsCard component */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Tiers"
            value={tiers.length}
            subtitle="Subscription plans"
            icon={TagIconHero}
            color="primary"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Active Tiers"
            value={tiers.filter(t => t.is_active).length}
            subtitle="Currently available"
            icon={CheckCircleIcon}
            color="success"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Total Users"
            value={tiers.reduce((sum, t) => sum + t.active_user_count, 0).toLocaleString()}
            subtitle="Across all tiers"
            icon={UsersIcon}
            color="info"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatsCard
            title="Monthly Revenue"
            value={formatPrice(tiers.reduce((sum, t) => sum + t.monthly_revenue, 0))}
            subtitle="Estimated total"
            icon={CurrencyDollarIcon}
            color="warning"
          />
        </Grid>
      </Grid>

      {/* Tier Table */}
      <Paper
        sx={{
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: 2
        }}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Code</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Price (Monthly)</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Price (Yearly)</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Invite Only</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>API Limit</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Seats</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Users</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Revenue</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Apps</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tiers
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((tier) => (
                  <TableRow
                    key={tier.id}
                    hover
                    sx={{
                      transition: 'all 0.2s',
                      '&:hover': {
                        backgroundColor: 'rgba(102, 126, 234, 0.04)',
                        transform: 'scale(1.002)'
                      }
                    }}
                  >
                    <TableCell>
                      <Typography variant="body1" fontWeight="bold">
                        {tier.tier_name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={tier.tier_code}
                        size="small"
                        sx={{
                          ...getTierBadgeColor(tier.tier_code),
                          backgroundColor: getTierBadgeColor(tier.tier_code).bg,
                          borderColor: getTierBadgeColor(tier.tier_code).border,
                          color: getTierBadgeColor(tier.tier_code).color,
                          fontWeight: 600,
                          border: `1px solid ${getTierBadgeColor(tier.tier_code).border}`
                        }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" fontWeight="bold">
                        {formatPrice(tier.price_monthly)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      {tier.price_yearly ? formatPrice(tier.price_yearly) : '-'}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={tier.is_active ? 'Active' : 'Inactive'}
                        color={tier.is_active ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell align="center">
                      {tier.is_invite_only ? (
                        <CheckIcon color="primary" />
                      ) : (
                        <CloseIcon color="disabled" />
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {formatApiLimit(tier.api_calls_limit)}
                    </TableCell>
                    <TableCell align="right">{tier.team_seats}</TableCell>
                    <TableCell align="right">{tier.active_user_count}</TableCell>
                    <TableCell align="right">
                      {formatPrice(tier.monthly_revenue)}
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={`${tier.feature_count} apps`}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="Manage Apps">
                        <IconButton
                          size="small"
                          onClick={() => handleManageFeatures(tier)}
                        >
                          <SyncIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Clone">
                        <IconButton
                          size="small"
                          onClick={() => handleCloneTier(tier)}
                        >
                          <CloneIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleEditTier(tier)}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Deactivate">
                        <IconButton
                          size="small"
                          onClick={() => deleteTier(tier.id, tier.tier_code)}
                          disabled={!tier.is_active}
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
          rowsPerPageOptions={[5, 10, 25]}
          component="div"
          count={tiers.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Create Tier Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Subscription Tier</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tier Code"
                value={formData.tier_code}
                onChange={(e) => setFormData({ ...formData, tier_code: e.target.value.toLowerCase() })}
                helperText="Lowercase, no spaces (e.g., 'vip_founder')"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tier Name"
                value={formData.tier_name}
                onChange={(e) => setFormData({ ...formData, tier_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Monthly Price ($)"
                type="number"
                value={formData.price_monthly}
                onChange={(e) => setFormData({ ...formData, price_monthly: parseFloat(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Yearly Price ($)"
                type="number"
                value={formData.price_yearly}
                onChange={(e) => setFormData({ ...formData, price_yearly: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="API Calls Limit"
                type="number"
                value={formData.api_calls_limit}
                onChange={(e) => setFormData({ ...formData, api_calls_limit: parseInt(e.target.value) })}
                helperText="-1 for unlimited"
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Team Seats"
                type="number"
                value={formData.team_seats}
                onChange={(e) => setFormData({ ...formData, team_seats: parseInt(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Sort Order"
                type="number"
                value={formData.sort_order}
                onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Lago Plan Code"
                value={formData.lago_plan_code}
                onChange={(e) => setFormData({ ...formData, lago_plan_code: e.target.value })}
                helperText="For Lago integration"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Stripe Price ID (Monthly)"
                value={formData.stripe_price_monthly}
                onChange={(e) => setFormData({ ...formData, stripe_price_monthly: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Plan Attributes
                </Typography>
              </Divider>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_invite_only}
                    onChange={(e) => setFormData({ ...formData, is_invite_only: e.target.checked })}
                  />
                }
                label="Invite Only"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.byok_enabled}
                    onChange={(e) => setFormData({ ...formData, byok_enabled: e.target.checked })}
                  />
                }
                label="BYOK"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.priority_support}
                    onChange={(e) => setFormData({ ...formData, priority_support: e.target.checked })}
                  />
                }
                label="Priority Support"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setCreateDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={createTier}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              }
            }}
          >
            Create Tier
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Tier Dialog (similar to Create) */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Subscription Tier</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tier Code"
                value={formData.tier_code}
                disabled
                helperText="Cannot change tier code"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Tier Name"
                value={formData.tier_name}
                onChange={(e) => setFormData({ ...formData, tier_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Monthly Price ($)"
                type="number"
                value={formData.price_monthly}
                onChange={(e) => setFormData({ ...formData, price_monthly: parseFloat(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Yearly Price ($)"
                type="number"
                value={formData.price_yearly}
                onChange={(e) => setFormData({ ...formData, price_yearly: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="API Calls Limit"
                type="number"
                value={formData.api_calls_limit}
                onChange={(e) => setFormData({ ...formData, api_calls_limit: parseInt(e.target.value) })}
                helperText="-1 for unlimited"
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Team Seats"
                type="number"
                value={formData.team_seats}
                onChange={(e) => setFormData({ ...formData, team_seats: parseInt(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Sort Order"
                type="number"
                value={formData.sort_order}
                onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <Divider sx={{ my: 2 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Plan Attributes
                </Typography>
              </Divider>
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_invite_only}
                    onChange={(e) => setFormData({ ...formData, is_invite_only: e.target.checked })}
                  />
                }
                label="Invite Only"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.byok_enabled}
                    onChange={(e) => setFormData({ ...formData, byok_enabled: e.target.checked })}
                  />
                }
                label="BYOK"
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.priority_support}
                    onChange={(e) => setFormData({ ...formData, priority_support: e.target.checked })}
                  />
                }
                label="Priority Support"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setEditDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={updateTier}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #5fbcff 0%, #10ffff 100%)'
              }
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Clone Tier Dialog */}
      <Dialog
        open={cloneDialogOpen}
        onClose={() => setCloneDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Clone Subscription Tier: {selectedTier?.tier_name}</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This will create a copy of "{selectedTier?.tier_name}" with all its settings and app associations.
          </Alert>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="New Tier Code"
                value={formData.tier_code}
                onChange={(e) => setFormData({ ...formData, tier_code: e.target.value.toLowerCase() })}
                helperText="Lowercase, no spaces (e.g., 'vip_founder_v2')"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="New Tier Name"
                value={formData.tier_name}
                onChange={(e) => setFormData({ ...formData, tier_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Monthly Price ($)"
                type="number"
                value={formData.price_monthly}
                onChange={(e) => setFormData({ ...formData, price_monthly: parseFloat(e.target.value) })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary">
                All other settings (API limits, team seats, BYOK, etc.) will be copied from the source tier.
                Lago and Stripe integration IDs will NOT be copied - you must configure these separately.
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setCloneDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={cloneTier}
            variant="contained"
            startIcon={<CloneIcon />}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              }
            }}
          >
            Clone Tier
          </Button>
        </DialogActions>
      </Dialog>

      {/* Apps Dialog */}
      <Dialog
        open={appsDialogOpen}
        onClose={() => setAppsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Manage Apps: {selectedTier?.tier_name}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mt: 2 }}>
            {['services', 'support', 'enterprise'].map(category => (
              <Accordion key={category} defaultExpanded={category === 'services'}>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6" textTransform="capitalize">
                    {category}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Grid container spacing={2}>
                    {appDefinitions
                      .filter(def => def.category === category)
                      .map(def => {
                        const feature = apps.find(f => f.app_key === def.key);
                        return (
                          <Grid item xs={12} md={6} key={def.key}>
                            <FormControlLabel
                              control={
                                <Checkbox
                                  checked={feature?.enabled || false}
                                  onChange={() => toggleFeature(def.key)}
                                />
                              }
                              label={def.name}
                            />
                          </Grid>
                        );
                      })}
                  </Grid>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setAppsDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={updateTierFeatures}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #ff9fff 0%, #ff677c 100%)'
              }
            }}
          >
            Save Apps
          </Button>
        </DialogActions>
      </Dialog>

      {/* User Migration Dialog */}
      <Dialog
        open={migrationDialogOpen}
        onClose={() => setMigrationDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Migrate User Tier</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="User ID or Email"
                value={migrationData.user_id}
                onChange={(e) => setMigrationData({ ...migrationData, user_id: e.target.value })}
                helperText="Keycloak user ID or email address"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth required>
                <InputLabel>New Tier</InputLabel>
                <Select
                  value={migrationData.new_tier_code}
                  onChange={(e) => setMigrationData({ ...migrationData, new_tier_code: e.target.value })}
                  label="New Tier"
                >
                  {tiers
                    .filter(t => t.is_active)
                    .map(tier => (
                      <MenuItem key={tier.tier_code} value={tier.tier_code}>
                        {tier.tier_name} - {formatPrice(tier.price_monthly)}/mo
                      </MenuItem>
                    ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Reason for Change"
                value={migrationData.reason}
                onChange={(e) => setMigrationData({ ...migrationData, reason: e.target.value })}
                multiline
                rows={3}
                helperText="Minimum 10 characters required"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={migrationData.send_notification}
                    onChange={(e) => setMigrationData({ ...migrationData, send_notification: e.target.checked })}
                  />
                }
                label="Send email notification to user"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setMigrationDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={migrateUser}
            variant="contained"
            disabled={!migrationData.user_id || !migrationData.new_tier_code || migrationData.reason.length < 10}
            sx={{
              background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #ff80aa 0%, #fff150 100%)'
              },
              '&:disabled': {
                background: '#ccc'
              }
            }}
          >
            Migrate User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Audit Log Dialog */}
      <Dialog
        open={auditLogDialogOpen}
        onClose={() => setAuditLogDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Tier Migration Audit Log</DialogTitle>
        <DialogContent>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Timestamp</TableCell>
                  <TableCell>User Email</TableCell>
                  <TableCell>Old Tier</TableCell>
                  <TableCell>New Tier</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Changed By</TableCell>
                  <TableCell align="right">API Limit Change</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {auditLog
                  .slice(auditPage * auditRowsPerPage, auditPage * auditRowsPerPage + auditRowsPerPage)
                  .map((entry) => (
                    <TableRow key={entry.id}>
                      <TableCell>
                        {new Date(entry.change_timestamp).toLocaleString()}
                      </TableCell>
                      <TableCell>{entry.user_email || '-'}</TableCell>
                      <TableCell>
                        <Chip
                          label={entry.old_tier_code || 'none'}
                          size="small"
                          sx={entry.old_tier_code ? {
                            ...getTierBadgeColor(entry.old_tier_code),
                            backgroundColor: getTierBadgeColor(entry.old_tier_code).bg,
                            color: getTierBadgeColor(entry.old_tier_code).color,
                            fontWeight: 600,
                            border: `1px solid ${getTierBadgeColor(entry.old_tier_code).border}`
                          } : {}}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={entry.new_tier_code}
                          size="small"
                          sx={{
                            ...getTierBadgeColor(entry.new_tier_code),
                            backgroundColor: getTierBadgeColor(entry.new_tier_code).bg,
                            color: getTierBadgeColor(entry.new_tier_code).color,
                            fontWeight: 600,
                            border: `1px solid ${getTierBadgeColor(entry.new_tier_code).border}`
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Tooltip title={entry.change_reason}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                            {entry.change_reason}
                          </Typography>
                        </Tooltip>
                      </TableCell>
                      <TableCell>{entry.changed_by}</TableCell>
                      <TableCell align="right">
                        {entry.old_api_limit !== null && entry.new_api_limit !== null ? (
                          <Chip
                            label={`${formatApiLimit(entry.old_api_limit)} → ${formatApiLimit(entry.new_api_limit)}`}
                            size="small"
                            color={entry.new_api_limit > entry.old_api_limit ? 'success' : 'warning'}
                          />
                        ) : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
              </TableBody>
            </Table>
          </TableContainer>
          <TablePagination
            rowsPerPageOptions={[5, 10, 25]}
            component="div"
            count={auditLog.length}
            rowsPerPage={auditRowsPerPage}
            page={auditPage}
            onPageChange={(e, newPage) => setAuditPage(newPage)}
            onRowsPerPageChange={(e) => {
              setAuditRowsPerPage(parseInt(e.target.value, 10));
              setAuditPage(0);
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button
            onClick={() => setAuditLogDialogOpen(false)}
            variant="outlined"
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 2
              }
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SubscriptionManagement;
