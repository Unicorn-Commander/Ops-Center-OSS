/**
 * App Management Page
 * Admin interface for managing app definitions available for subscription tiers
 * Epic 4.4: Subscription Management - App Definitions
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
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  Category as CategoryIcon,
  Tune as TuneIcon,
  DragIndicator as DragIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

const AppManagement = () => {
  // State management
  const [apps, setApps] = useState([]);
  const [tierApps, setTierApps] = useState([]); // NEW: Tier-app associations
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  // Selected app for editing/deleting
  const [selectedApp, setSelectedApp] = useState(null);

  // Filter states
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  // Form data
  const [formData, setFormData] = useState({
    app_key: '',
    app_name: '',
    category: 'services',
    description: '',
    is_active: true,
    sort_order: 0
  });

  // ============================================
  // API Functions
  // ============================================

  const fetchApps = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/apps/?active_only=false', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch apps');
      const data = await response.json();
      setApps(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching apps:', err);
    } finally {
      setLoading(false);
    }
  };

  // NEW: Fetch tier-app associations
  const fetchTierApps = async () => {
    try {
      const response = await fetch('/api/v1/admin/tiers/apps/detailed', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch tier-app associations');
      const data = await response.json();
      setTierApps(data);
    } catch (err) {
      console.error('Error fetching tier-app associations:', err);
    }
  };

  const createApp = async () => {
    try {
      const response = await fetch('/api/v1/admin/apps/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create app');
      }

      setSuccess('App created successfully');
      setCreateDialogOpen(false);
      fetchApps();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error creating app:', err);
    }
  };

  const updateApp = async () => {
    if (!selectedApp) return;

    try {
      const response = await fetch(`/api/v1/admin/apps/${selectedApp.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update app');
      }

      setSuccess('App updated successfully');
      setEditDialogOpen(false);
      fetchApps();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error updating app:', err);
    }
  };

  const deleteApp = async () => {
    if (!selectedApp) return;

    try {
      const response = await fetch(`/api/v1/admin/apps/${selectedApp.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to delete app');

      setSuccess('App deleted successfully');
      setDeleteDialogOpen(false);
      fetchApps();
      setSelectedFeature(null);
    } catch (err) {
      setError(err.message);
      console.error('Error deleting app:', err);
    }
  };

  const toggleAppStatus = async (feature) => {
    try {
      const response = await fetch(`/api/v1/admin/apps/${feature.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ ...feature, is_active: !feature.is_active })
      });

      if (!response.ok) throw new Error('Failed to update app status');

      setSuccess(`App ${feature.is_active ? 'deactivated' : 'activated'} successfully`);
      fetchApps();
    } catch (err) {
      setError(err.message);
      console.error('Error toggling app status:', err);
    }
  };

  // ============================================
  // Form Handlers
  // ============================================

  const resetForm = () => {
    setFormData({
      app_key: '',
      app_name: '',
      category: 'services',
      description: '',
      is_active: true,
      sort_order: 0
    });
  };

  const handleEditApp = (feature) => {
    setSelectedFeature(feature);
    setFormData({
      app_key: feature.app_key,
      app_name: feature.app_name,
      category: feature.category,
      description: feature.description || '',
      is_active: feature.is_active,
      sort_order: feature.sort_order
    });
    setEditDialogOpen(true);
  };

  const handleDeleteApp = (feature) => {
    setSelectedFeature(feature);
    setDeleteDialogOpen(true);
  };

  const validateAppKey = (key) => {
    // Must be lowercase with underscores only
    const regex = /^[a-z_]+$/;
    return regex.test(key);
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    fetchApps();
    fetchTierApps(); // NEW: Also fetch tier associations
  }, []);

  // ============================================
  // Render Helpers
  // ============================================

  // NEW: Helper to get tiers for a feature
  const getTiersForApp = (featureKey) => {
    return tierApps
      .filter(tf => tf.app_key === featureKey && tf.enabled)
      .map(tf => ({
        tier_code: tf.tier_code,
        tier_name: tf.tier_name
      }));
  };

  // NEW: Get tier badge color
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

  const getCategoryColor = (category) => {
    switch (category) {
      case 'services':
        return { bg: 'rgba(33, 150, 243, 0.1)', color: '#2196f3', border: '#2196f3' };
      case 'support':
        return { bg: 'rgba(76, 175, 80, 0.1)', color: '#4caf50', border: '#4caf50' };
      case 'enterprise':
        return { bg: 'rgba(255, 193, 7, 0.1)', color: '#ffc107', border: '#ffc107' };
      default:
        return { bg: 'rgba(158, 158, 158, 0.1)', color: '#9e9e9e', border: '#9e9e9e' };
    }
  };

  const getCategoryStats = () => {
    const stats = {
      services: apps.filter(f => f.category === 'services').length,
      support: apps.filter(f => f.category === 'support').length,
      enterprise: apps.filter(f => f.category === 'enterprise').length
    };
    return stats;
  };

  const filteredApps = apps
    .filter(f => categoryFilter === 'all' || f.category === categoryFilter)
    .filter(f => statusFilter === 'all' || (statusFilter === 'active' ? f.is_active : !f.is_active))
    .sort((a, b) => a.sort_order - b.sort_order);

  // ============================================
  // Main Render
  // ============================================

  if (loading && apps.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const activeApps = apps.filter(f => f.is_active).length;
  const categoryStats = getCategoryStats();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <PageHeader
        title="App Management"
        subtitle="Define available apps for subscription tiers"
        actions={(
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              resetForm();
              setCreateDialogOpen(true);
            }}
          >
            Create App
          </Button>
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

      {/* Analytics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(102, 126, 234, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Total Apps
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {apps.length}
                  </Typography>
                </Box>
                <TuneIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(240, 147, 251, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Active Apps
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {activeApps}
                  </Typography>
                </Box>
                <CheckIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(79, 172, 254, 0.3)'
              }
            }}
          >
            <CardContent>
              <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                Services
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                {categoryStats.services}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(67, 233, 123, 0.3)'
              }
            }}
          >
            <CardContent>
              <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                Support
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                {categoryStats.support}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={2}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(250, 112, 154, 0.3)'
              }
            }}
          >
            <CardContent>
              <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                Enterprise
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                {categoryStats.enterprise}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2, borderRadius: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Category</InputLabel>
              <Select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                label="Category"
              >
                <MenuItem value="all">All Categories</MenuItem>
                <MenuItem value="services">Services</MenuItem>
                <MenuItem value="support">Support</MenuItem>
                <MenuItem value="enterprise">Enterprise</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={4}>
            <ToggleButtonGroup
              value={statusFilter}
              exclusive
              onChange={(e, newValue) => {
                if (newValue !== null) setStatusFilter(newValue);
              }}
              size="small"
              fullWidth
            >
              <ToggleButton value="all">All Status</ToggleButton>
              <ToggleButton value="active">Active</ToggleButton>
              <ToggleButton value="inactive">Inactive</ToggleButton>
            </ToggleButtonGroup>
          </Grid>
          <Grid item xs={12} md={4}>
            <Typography variant="body2" color="text.secondary" textAlign="right">
              Showing {filteredApps.length} of {apps.length} apps
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Apps Table */}
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
                <TableCell sx={{ fontWeight: 700 }}>App Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Key</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Subscription Tiers</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Sort Order</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredApps
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((feature) => {
                  const categoryStyle = getCategoryColor(feature.category);
                  return (
                    <TableRow
                      key={feature.id}
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
                          {feature.app_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={feature.app_key}
                          size="small"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '0.75rem'
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={feature.category}
                          size="small"
                          sx={{
                            backgroundColor: categoryStyle.bg,
                            color: categoryStyle.color,
                            border: `1px solid ${categoryStyle.border}`,
                            textTransform: 'capitalize',
                            fontWeight: 600
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            maxWidth: 300,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {feature.description || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {getTiersForApp(feature.app_key).length > 0 ? (
                            getTiersForApp(feature.app_key).map((tier) => {
                              const tierStyle = getTierBadgeColor(tier.tier_code);
                              return (
                                <Chip
                                  key={tier.tier_code}
                                  label={tier.tier_name}
                                  size="small"
                                  sx={{
                                    backgroundColor: tierStyle.bg,
                                    color: tierStyle.color,
                                    border: `1px solid ${tierStyle.border}`,
                                    fontWeight: 600,
                                    fontSize: '0.7rem'
                                  }}
                                />
                              );
                            })
                          ) : (
                            <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                              No tiers
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={feature.is_active ? 'Active' : 'Inactive'}
                          color={feature.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          icon={<DragIcon />}
                          label={feature.sort_order}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title={feature.is_active ? 'Deactivate' : 'Activate'}>
                          <IconButton
                            size="small"
                            onClick={() => toggleAppStatus(feature)}
                            sx={{
                              color: feature.is_active ? 'error.main' : 'success.main'
                            }}
                          >
                            {feature.is_active ? <CloseIcon /> : <CheckIcon />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => handleEditApp(feature)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteApp(feature)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 50]}
          component="div"
          count={filteredApps.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Create App Dialog */}
      <Dialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Feature</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="App Key"
                value={formData.app_key}
                onChange={(e) => setFormData({ ...formData, app_key: e.target.value.toLowerCase().replace(/[^a-z_]/g, '') })}
                helperText="Lowercase with underscores only (e.g., 'chat_access')"
                error={formData.app_key && !validateAppKey(formData.app_key)}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="App Name"
                value={formData.app_name}
                onChange={(e) => setFormData({ ...formData, app_name: e.target.value })}
                helperText="Display name (e.g., 'Open-WebUI Access')"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  label="Category"
                >
                  <MenuItem value="services">Services</MenuItem>
                  <MenuItem value="support">Support</MenuItem>
                  <MenuItem value="enterprise">Enterprise</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Sort Order"
                type="number"
                value={formData.sort_order}
                onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
                helperText="Lower numbers appear first"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
                helperText="Optional description of what this app provides"
              />
            </Grid>
            <Grid item xs={12}>
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
            onClick={createApp}
            variant="contained"
            disabled={!formData.app_key || !formData.app_name || !validateAppKey(formData.app_key)}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              },
              '&:disabled': {
                background: '#ccc'
              }
            }}
          >
            Create App
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit App Dialog */}
      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit App</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="App Key"
                value={formData.app_key}
                disabled
                helperText="Cannot change app key"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="App Name"
                value={formData.app_name}
                onChange={(e) => setFormData({ ...formData, app_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Category</InputLabel>
                <Select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  label="Category"
                >
                  <MenuItem value="services">Services</MenuItem>
                  <MenuItem value="support">Support</MenuItem>
                  <MenuItem value="enterprise">Enterprise</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Sort Order"
                type="number"
                value={formData.sort_order}
                onChange={(e) => setFormData({ ...formData, sort_order: parseInt(e.target.value) || 0 })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
              />
            </Grid>
            <Grid item xs={12}>
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
            onClick={updateApp}
            variant="contained"
            disabled={!formData.app_name}
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #5fbcff 0%, #10ffff 100%)'
              },
              '&:disabled': {
                background: '#ccc'
              }
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Delete App</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the app <strong>{selectedApp?.app_name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will remove it from all subscription tiers. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
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
            onClick={deleteApp}
            variant="contained"
            color="error"
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4
              }
            }}
          >
            Delete App
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AppManagement;
