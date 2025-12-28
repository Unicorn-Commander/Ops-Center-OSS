import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Divider,
  Stack,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Close as CloseIcon,
  Check as CheckIcon,
  Block as BlockIcon,
  Security as SecurityIcon,
  Shield as ShieldIcon,
  VerifiedUser as VerifiedUserIcon,
  PlayArrow as ExecuteIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

/**
 * Permission Management UI
 *
 * Comprehensive interface for managing the 5-layer permission hierarchy:
 * - System → Platform → Organization → Application → User
 *
 * Features:
 * - Permission table with advanced filtering
 * - Create/Edit permission modal with JSON metadata editor
 * - Delete confirmation dialog
 * - Permission checker tool for testing access
 *
 * Backend Integration:
 * - GET /api/v1/permissions - List permissions
 * - POST /api/v1/permissions - Create/update permission
 * - DELETE /api/v1/permissions/:id - Delete permission
 * - POST /api/v1/permissions/check - Check user permission
 * - GET /api/v1/permissions/resources - List resources
 * - GET /api/v1/permissions/actions - List actions
 */
const PermissionsManagement = () => {
  const navigate = useNavigate();
  const { currentTheme } = useTheme();

  // State for permission list
  const [permissions, setPermissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [totalPermissions, setTotalPermissions] = useState(0);

  // Filter state
  const [filters, setFilters] = useState({
    level: '',
    resource: '',
    action: '',
    granted: null,
    scope_id: ''
  });

  // Modal states
  const [createEditModalOpen, setCreateEditModalOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [checkerModalOpen, setCheckerModalOpen] = useState(false);
  const [selectedPermission, setSelectedPermission] = useState(null);

  // Form state for create/edit
  const [formData, setFormData] = useState({
    level: '',
    resource: '',
    action: '',
    granted: true,
    scope_id: '',
    metadata: '{}'
  });
  const [formErrors, setFormErrors] = useState({});

  // Checker form state
  const [checkerData, setCheckerData] = useState({
    user_id: '',
    resource: '',
    action: '',
    context: '{}'
  });
  const [checkerResult, setCheckerResult] = useState(null);
  const [checkerLoading, setCheckerLoading] = useState(false);

  // Resources and actions from backend
  const [resources, setResources] = useState([]);
  const [actions, setActions] = useState([]);

  // Toast notification
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  // Template states
  const [templates, setTemplates] = useState([]);
  const [templateDetailsModalOpen, setTemplateDetailsModalOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateLoading, setTemplateLoading] = useState(false);
  const [applyTemplateData, setApplyTemplateData] = useState({
    scope_type: 'user',
    scope_id: '',
    level: ''
  });
  const [saveAsTemplateModalOpen, setSaveAsTemplateModalOpen] = useState(false);
  const [customTemplateName, setCustomTemplateName] = useState('');
  const [customTemplateDescription, setCustomTemplateDescription] = useState('');

  // Theme-aware styles
  const isDark = currentTheme === 'dark' || currentTheme === 'unicorn';
  const bgColor = isDark ? '#1e293b' : '#ffffff';
  const textColor = isDark ? '#e2e8f0' : '#1e293b';
  const borderColor = isDark ? '#334155' : '#e2e8f0';

  // Fetch permissions on mount and when filters change
  useEffect(() => {
    fetchPermissions();
  }, [page, rowsPerPage, filters]);

  // Fetch resources and actions on mount
  useEffect(() => {
    fetchResources();
    fetchActions();
    fetchTemplates();
  }, []);

  /**
   * Fetch permissions from backend
   */
  const fetchPermissions = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams();
      params.append('limit', rowsPerPage);
      params.append('offset', page * rowsPerPage);

      if (filters.level) params.append('level', filters.level);
      if (filters.resource) params.append('resource', filters.resource);
      if (filters.action) params.append('action', filters.action);
      if (filters.scope_id) params.append('scope_id', filters.scope_id);
      if (filters.granted !== null) params.append('granted', filters.granted);

      const response = await fetch(`/api/v1/permissions?${params}`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch permissions');
      }

      const data = await response.json();
      setPermissions(data);
      setTotalPermissions(data.length); // In real pagination, this would come from headers

    } catch (err) {
      setError(err.message);
      showToast('Error loading permissions: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  /**
   * Fetch available resources
   */
  const fetchResources = async () => {
    try {
      const response = await fetch('/api/v1/permissions/resources', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setResources(data);
      }
    } catch (err) {
      console.error('Error fetching resources:', err);
    }
  };

  /**
   * Fetch available actions
   */
  const fetchActions = async () => {
    try {
      const response = await fetch('/api/v1/permissions/actions', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setActions(data);
      }
    } catch (err) {
      console.error('Error fetching actions:', err);
    }
  };

  /**
   * Handle create permission button
   */
  const handleCreateClick = () => {
    setSelectedPermission(null);
    setFormData({
      level: '',
      resource: '',
      action: '',
      granted: true,
      scope_id: '',
      metadata: '{}'
    });
    setFormErrors({});
    setCreateEditModalOpen(true);
  };

  /**
   * Handle edit permission button
   */
  const handleEditClick = (permission) => {
    setSelectedPermission(permission);
    setFormData({
      level: permission.level,
      resource: permission.resource,
      action: permission.action,
      granted: permission.granted,
      scope_id: permission.scope_id || '',
      metadata: JSON.stringify(permission.metadata || {}, null, 2)
    });
    setFormErrors({});
    setCreateEditModalOpen(true);
  };

  /**
   * Handle delete permission button
   */
  const handleDeleteClick = (permission) => {
    setSelectedPermission(permission);
    setDeleteDialogOpen(true);
  };

  /**
   * Validate form data
   */
  const validateForm = () => {
    const errors = {};

    if (!formData.level) errors.level = 'Level is required';
    if (!formData.resource) errors.resource = 'Resource is required';
    if (!formData.action) errors.action = 'Action is required';

    // Validate JSON metadata
    try {
      JSON.parse(formData.metadata);
    } catch (e) {
      errors.metadata = 'Invalid JSON format';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Handle form submission (create/update)
   */
  const handleFormSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    try {
      const payload = {
        level: formData.level,
        resource: formData.resource,
        action: formData.action,
        granted: formData.granted,
        scope_id: formData.scope_id || null,
        metadata: JSON.parse(formData.metadata)
      };

      const response = await fetch('/api/v1/permissions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save permission');
      }

      showToast(selectedPermission ? 'Permission updated successfully' : 'Permission created successfully', 'success');
      setCreateEditModalOpen(false);
      fetchPermissions();

    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  };

  /**
   * Handle permission deletion
   */
  const handleDeleteConfirm = async () => {
    if (!selectedPermission) return;

    try {
      const response = await fetch(`/api/v1/permissions/${selectedPermission.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete permission');
      }

      showToast('Permission deleted successfully', 'success');
      setDeleteDialogOpen(false);
      fetchPermissions();

    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    }
  };

  /**
   * Handle permission check
   */
  const handlePermissionCheck = async () => {
    setCheckerLoading(true);
    setCheckerResult(null);

    try {
      const payload = {
        user_id: checkerData.user_id,
        resource: checkerData.resource,
        action: checkerData.action,
        context: JSON.parse(checkerData.context)
      };

      const response = await fetch('/api/v1/permissions/check', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to check permission');
      }

      const result = await response.json();
      setCheckerResult(result);

    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setCheckerLoading(false);
    }
  };

  /**
   * Show toast notification
   */
  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  /**
   * Handle filter change
   */
  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPage(0); // Reset to first page
  };

  /**
   * Clear all filters
   */
  const handleClearFilters = () => {
    setFilters({
      level: '',
      resource: '',
      action: '',
      granted: null,
      scope_id: ''
    });
    setPage(0);
  };

  /**
   * Get level badge color
   */
  const getLevelColor = (level) => {
    const colors = {
      system: 'error',
      platform: 'warning',
      organization: 'info',
      application: 'success',
      user: 'default'
    };
    return colors[level] || 'default';
  };

  /**
   * Get action icon
   */
  const getActionIcon = (action) => {
    const icons = {
      read: <SearchIcon fontSize="small" />,
      write: <EditIcon fontSize="small" />,
      delete: <DeleteIcon fontSize="small" />,
      admin: <ShieldIcon fontSize="small" />,
      execute: <ExecuteIcon fontSize="small" />
    };
    return icons[action] || null;
  };

  /**
   * Fetch templates from backend
   */
  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/permissions/templates', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setTemplates(data);
      }
    } catch (err) {
      console.error('Error fetching templates:', err);
    }
  };

  /**
   * Handle template card click - open details modal
   */
  const handleTemplateClick = async (templateId) => {
    setTemplateLoading(true);
    try {
      const response = await fetch(`/api/v1/permissions/templates/${templateId}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedTemplate(data);
        setTemplateDetailsModalOpen(true);
      }
    } catch (err) {
      showToast('Error loading template details: ' + err.message, 'error');
    } finally {
      setTemplateLoading(false);
    }
  };

  /**
   * Apply template to scope
   */
  const handleApplyTemplate = async () => {
    if (!selectedTemplate || !applyTemplateData.scope_id) {
      showToast('Please fill in all required fields', 'error');
      return;
    }

    setTemplateLoading(true);
    try {
      const response = await fetch(`/api/v1/permissions/templates/${selectedTemplate.id}/apply`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(applyTemplateData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to apply template');
      }

      const result = await response.json();
      showToast(`Template applied successfully! Created ${result.permissions_created} permissions.`, 'success');
      setTemplateDetailsModalOpen(false);
      setApplyTemplateData({ scope_type: 'user', scope_id: '', level: '' });
      fetchPermissions();

    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setTemplateLoading(false);
    }
  };

  /**
   * Save current filters as custom template
   */
  const handleSaveAsTemplate = async () => {
    if (!customTemplateName || !customTemplateDescription) {
      showToast('Please provide name and description', 'error');
      return;
    }

    // Get current filtered permissions to use as template
    const templatePermissions = permissions
      .filter(p => p.granted) // Only include granted permissions
      .map(p => ({
        resource: p.resource,
        action: p.action,
        granted: true
      }));

    if (templatePermissions.length === 0) {
      showToast('No granted permissions to save as template', 'error');
      return;
    }

    setTemplateLoading(true);
    try {
      const response = await fetch('/api/v1/permissions/templates/custom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          name: customTemplateName,
          description: customTemplateDescription,
          permissions: templatePermissions,
          icon: 'custom'
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save template');
      }

      showToast('Custom template created successfully!', 'success');
      setSaveAsTemplateModalOpen(false);
      setCustomTemplateName('');
      setCustomTemplateDescription('');
      fetchTemplates();

    } catch (err) {
      showToast('Error: ' + err.message, 'error');
    } finally {
      setTemplateLoading(false);
    }
  };

  /**
   * Get template icon component
   */
  const getTemplateIcon = (icon) => {
    const icons = {
      shield: <ShieldIcon />,
      'user-check': <VerifiedUserIcon />,
      code: <SecurityIcon />,
      'chart-bar': <SecurityIcon />,
      eye: <SearchIcon />,
      custom: <AddIcon />
    };
    return icons[icon] || <ShieldIcon />;
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 1, color: textColor, fontWeight: 600 }}>
          Permission Management
        </Typography>
        <Typography variant="body2" sx={{ color: isDark ? '#94a3b8' : '#64748b' }}>
          Manage 5-layer permission hierarchy: System → Platform → Organization → Application → User
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
            <CardContent>
              <Typography variant="body2" color="textSecondary">
                Total Permissions
              </Typography>
              <Typography variant="h4" sx={{ color: textColor }}>
                {totalPermissions}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
            <CardContent>
              <Typography variant="body2" color="textSecondary">
                Granted
              </Typography>
              <Typography variant="h4" sx={{ color: '#10b981' }}>
                {permissions.filter(p => p.granted).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
            <CardContent>
              <Typography variant="body2" color="textSecondary">
                Denied
              </Typography>
              <Typography variant="h4" sx={{ color: '#ef4444' }}>
                {permissions.filter(p => !p.granted).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
            <CardContent>
              <Typography variant="body2" color="textSecondary">
                Resources
              </Typography>
              <Typography variant="h4" sx={{ color: textColor }}>
                {resources.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Template Gallery Section */}
      <Paper sx={{ p: 3, mb: 3, bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ color: textColor, fontWeight: 600 }}>
              Quick Setup with Templates
            </Typography>
            <Typography variant="body2" sx={{ color: isDark ? '#94a3b8' : '#64748b' }}>
              Apply pre-configured permission sets in one click
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => setSaveAsTemplateModalOpen(true)}
            disabled={permissions.filter(p => p.granted).length === 0}
          >
            Save Current as Template
          </Button>
        </Box>

        <Divider sx={{ my: 2 }} />

        <Grid container spacing={2}>
          {templates.map((template) => (
            <Grid item xs={12} sm={6} md={4} lg={2.4} key={template.id}>
              <Card
                sx={{
                  bgcolor: isDark ? '#0f172a' : '#f8fafc',
                  border: `1px solid ${borderColor}`,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 3,
                    borderColor: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6'
                  }
                }}
                onClick={() => handleTemplateClick(template.id)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Box
                      sx={{
                        p: 1,
                        borderRadius: 1,
                        bgcolor: currentTheme === 'unicorn' ? 'rgba(147, 51, 234, 0.1)' : 'rgba(59, 130, 246, 0.1)',
                        color: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
                        mr: 1
                      }}
                    >
                      {getTemplateIcon(template.icon)}
                    </Box>
                    {template.is_custom && (
                      <Chip label="Custom" size="small" color="warning" />
                    )}
                  </Box>

                  <Typography variant="subtitle1" sx={{ color: textColor, fontWeight: 600, mb: 0.5 }}>
                    {template.name}
                  </Typography>

                  <Typography
                    variant="body2"
                    sx={{
                      color: isDark ? '#94a3b8' : '#64748b',
                      mb: 1,
                      minHeight: '40px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}
                  >
                    {template.description}
                  </Typography>

                  <Chip
                    label={`${template.permissions_count} permissions`}
                    size="small"
                    variant="outlined"
                    sx={{ mt: 1 }}
                  />
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {templates.length === 0 && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" sx={{ color: isDark ? '#94a3b8' : '#64748b' }}>
              No templates available
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Filters and Actions */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Level</InputLabel>
              <Select
                value={filters.level}
                onChange={(e) => handleFilterChange('level', e.target.value)}
                label="Level"
              >
                <MenuItem value="">All Levels</MenuItem>
                <MenuItem value="system">System</MenuItem>
                <MenuItem value="platform">Platform</MenuItem>
                <MenuItem value="organization">Organization</MenuItem>
                <MenuItem value="application">Application</MenuItem>
                <MenuItem value="user">User</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Resource</InputLabel>
              <Select
                value={filters.resource}
                onChange={(e) => handleFilterChange('resource', e.target.value)}
                label="Resource"
              >
                <MenuItem value="">All Resources</MenuItem>
                {resources.map(r => (
                  <MenuItem key={r.name} value={r.name}>{r.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Action</InputLabel>
              <Select
                value={filters.action}
                onChange={(e) => handleFilterChange('action', e.target.value)}
                label="Action"
              >
                <MenuItem value="">All Actions</MenuItem>
                {actions.map(a => (
                  <MenuItem key={a.name} value={a.name}>{a.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.granted === null ? '' : filters.granted ? 'granted' : 'denied'}
                onChange={(e) => handleFilterChange('granted', e.target.value === '' ? null : e.target.value === 'granted')}
                label="Status"
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="granted">Granted</MenuItem>
                <MenuItem value="denied">Denied</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              size="small"
              label="Scope ID"
              value={filters.scope_id}
              onChange={(e) => handleFilterChange('scope_id', e.target.value)}
              placeholder="Filter by scope"
            />
          </Grid>

          <Grid item xs={12} md={2}>
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                onClick={handleClearFilters}
                fullWidth
              >
                Clear
              </Button>
            </Stack>
          </Grid>
        </Grid>

        <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateClick}
            sx={{
              bgcolor: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
              '&:hover': { bgcolor: currentTheme === 'unicorn' ? '#7e22ce' : '#2563eb' }
            }}
          >
            Create Permission
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchPermissions}
          >
            Refresh
          </Button>
          <Button
            variant="outlined"
            startIcon={<VerifiedUserIcon />}
            onClick={() => setCheckerModalOpen(true)}
          >
            Check Permission
          </Button>
        </Box>
      </Paper>

      {/* Permissions Table */}
      <Paper sx={{ bgcolor: bgColor, border: `1px solid ${borderColor}` }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Level</TableCell>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Resource</TableCell>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Action</TableCell>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Granted</TableCell>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Scope ID</TableCell>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Metadata</TableCell>
                <TableCell sx={{ color: textColor, fontWeight: 600 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 8 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : permissions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 8, color: isDark ? '#94a3b8' : '#64748b' }}>
                    No permissions found
                  </TableCell>
                </TableRow>
              ) : (
                permissions.map((permission) => (
                  <TableRow key={permission.id} hover>
                    <TableCell>
                      <Chip
                        label={permission.level}
                        color={getLevelColor(permission.level)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell sx={{ color: textColor }}>{permission.resource}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getActionIcon(permission.action)}
                        <span style={{ color: textColor }}>{permission.action}</span>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {permission.granted ? (
                        <Chip icon={<CheckIcon />} label="Granted" color="success" size="small" />
                      ) : (
                        <Chip icon={<BlockIcon />} label="Denied" color="error" size="small" />
                      )}
                    </TableCell>
                    <TableCell sx={{ color: textColor }}>
                      {permission.scope_id || <em style={{ color: isDark ? '#94a3b8' : '#64748b' }}>None</em>}
                    </TableCell>
                    <TableCell>
                      {Object.keys(permission.metadata || {}).length > 0 ? (
                        <Tooltip title={JSON.stringify(permission.metadata, null, 2)}>
                          <Chip label={`${Object.keys(permission.metadata).length} fields`} size="small" variant="outlined" />
                        </Tooltip>
                      ) : (
                        <em style={{ color: isDark ? '#94a3b8' : '#64748b' }}>None</em>
                      )}
                    </TableCell>
                    <TableCell>
                      <IconButton size="small" onClick={() => handleEditClick(permission)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteClick(permission)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={totalPermissions}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[25, 50, 100]}
        />
      </Paper>

      {/* Create/Edit Permission Modal */}
      <Dialog
        open={createEditModalOpen}
        onClose={() => setCreateEditModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedPermission ? 'Edit Permission' : 'Create Permission'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth error={!!formErrors.level}>
                  <InputLabel>Level *</InputLabel>
                  <Select
                    value={formData.level}
                    onChange={(e) => setFormData({ ...formData, level: e.target.value })}
                    label="Level *"
                  >
                    <MenuItem value="system">System</MenuItem>
                    <MenuItem value="platform">Platform</MenuItem>
                    <MenuItem value="organization">Organization</MenuItem>
                    <MenuItem value="application">Application</MenuItem>
                    <MenuItem value="user">User</MenuItem>
                  </Select>
                  {formErrors.level && (
                    <Typography variant="caption" color="error">{formErrors.level}</Typography>
                  )}
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth error={!!formErrors.resource}>
                  <InputLabel>Resource *</InputLabel>
                  <Select
                    value={formData.resource}
                    onChange={(e) => setFormData({ ...formData, resource: e.target.value })}
                    label="Resource *"
                  >
                    {resources.map(r => (
                      <MenuItem key={r.name} value={r.name}>{r.name}</MenuItem>
                    ))}
                  </Select>
                  {formErrors.resource && (
                    <Typography variant="caption" color="error">{formErrors.resource}</Typography>
                  )}
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth error={!!formErrors.action}>
                  <InputLabel>Action *</InputLabel>
                  <Select
                    value={formData.action}
                    onChange={(e) => setFormData({ ...formData, action: e.target.value })}
                    label="Action *"
                  >
                    {actions.map(a => (
                      <MenuItem key={a.name} value={a.name}>{a.name}</MenuItem>
                    ))}
                  </Select>
                  {formErrors.action && (
                    <Typography variant="caption" color="error">{formErrors.action}</Typography>
                  )}
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.granted}
                      onChange={(e) => setFormData({ ...formData, granted: e.target.checked })}
                    />
                  }
                  label={formData.granted ? 'Granted' : 'Denied'}
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Scope ID (Optional)"
                  value={formData.scope_id}
                  onChange={(e) => setFormData({ ...formData, scope_id: e.target.value })}
                  placeholder="User ID, Org ID, etc."
                  helperText="Leave empty for level-wide permission"
                />
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Metadata (JSON)"
                  value={formData.metadata}
                  onChange={(e) => setFormData({ ...formData, metadata: e.target.value })}
                  error={!!formErrors.metadata}
                  helperText={formErrors.metadata || 'Enter valid JSON object'}
                  placeholder='{"key": "value"}'
                  sx={{ fontFamily: 'monospace' }}
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateEditModalOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleFormSubmit}
            sx={{
              bgcolor: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
              '&:hover': { bgcolor: currentTheme === 'unicorn' ? '#7e22ce' : '#2563eb' }
            }}
          >
            {selectedPermission ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete Permission</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Are you sure you want to delete this permission?
          </Alert>
          {selectedPermission && (
            <Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Level:</strong> {selectedPermission.level}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Resource:</strong> {selectedPermission.resource}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Action:</strong> {selectedPermission.action}
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Granted:</strong> {selectedPermission.granted ? 'Yes' : 'No'}
              </Typography>
              {selectedPermission.scope_id && (
                <Typography variant="body2">
                  <strong>Scope ID:</strong> {selectedPermission.scope_id}
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleDeleteConfirm}>
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Permission Checker Modal */}
      <Dialog
        open={checkerModalOpen}
        onClose={() => setCheckerModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <SecurityIcon />
            Permission Checker
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="User ID"
                  value={checkerData.user_id}
                  onChange={(e) => setCheckerData({ ...checkerData, user_id: e.target.value })}
                  placeholder="Enter user ID to check"
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Resource</InputLabel>
                  <Select
                    value={checkerData.resource}
                    onChange={(e) => setCheckerData({ ...checkerData, resource: e.target.value })}
                    label="Resource"
                  >
                    {resources.map(r => (
                      <MenuItem key={r.name} value={r.name}>{r.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Action</InputLabel>
                  <Select
                    value={checkerData.action}
                    onChange={(e) => setCheckerData({ ...checkerData, action: e.target.value })}
                    label="Action"
                  >
                    {actions.map(a => (
                      <MenuItem key={a.name} value={a.name}>{a.name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  label="Context (JSON)"
                  value={checkerData.context}
                  onChange={(e) => setCheckerData({ ...checkerData, context: e.target.value })}
                  placeholder='{"org_id": "org-123", "app_id": "app-456"}'
                  sx={{ fontFamily: 'monospace' }}
                  helperText="Optional: Add context like org_id, app_id, platform"
                />
              </Grid>

              <Grid item xs={12}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handlePermissionCheck}
                  disabled={checkerLoading || !checkerData.user_id || !checkerData.resource || !checkerData.action}
                  sx={{
                    bgcolor: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
                    '&:hover': { bgcolor: currentTheme === 'unicorn' ? '#7e22ce' : '#2563eb' }
                  }}
                >
                  {checkerLoading ? <CircularProgress size={24} /> : 'Check Permission'}
                </Button>
              </Grid>

              {checkerResult && (
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Alert severity={checkerResult.allowed ? 'success' : 'error'} sx={{ mb: 2 }}>
                    <Typography variant="h6">
                      {checkerResult.allowed ? 'Permission Allowed' : 'Permission Denied'}
                    </Typography>
                  </Alert>
                  <Box>
                    <Typography variant="body2" sx={{ mb: 1 }}>
                      <strong>Reason:</strong> {checkerResult.reason}
                    </Typography>
                    {checkerResult.effective_level && (
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        <strong>Effective Level:</strong> <Chip label={checkerResult.effective_level} size="small" color={getLevelColor(checkerResult.effective_level)} />
                      </Typography>
                    )}
                    {checkerResult.metadata && Object.keys(checkerResult.metadata).length > 0 && (
                      <Box sx={{ mt: 2 }}>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          <strong>Metadata:</strong>
                        </Typography>
                        <Paper sx={{ p: 2, bgcolor: isDark ? '#0f172a' : '#f8fafc' }}>
                          <pre style={{ margin: 0, fontSize: '0.875rem', overflow: 'auto' }}>
                            {JSON.stringify(checkerResult.metadata, null, 2)}
                          </pre>
                        </Paper>
                      </Box>
                    )}
                  </Box>
                </Grid>
              )}
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCheckerModalOpen(false);
            setCheckerResult(null);
          }}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Template Details Modal */}
      <Dialog
        open={templateDetailsModalOpen}
        onClose={() => setTemplateDetailsModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {selectedTemplate && getTemplateIcon(selectedTemplate.icon)}
            <Box>
              <Typography variant="h6">{selectedTemplate?.name}</Typography>
              <Typography variant="body2" color="textSecondary">
                {selectedTemplate?.description}
              </Typography>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedTemplate && (
            <Box sx={{ pt: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                Permissions Included ({selectedTemplate.permissions.length})
              </Typography>

              <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 600 }}>Resource</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Action</TableCell>
                      <TableCell sx={{ fontWeight: 600 }}>Granted</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedTemplate.permissions.map((perm, idx) => (
                      <TableRow key={idx}>
                        <TableCell>{perm.resource}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {getActionIcon(perm.action)}
                            {perm.action}
                          </Box>
                        </TableCell>
                        <TableCell>
                          {perm.granted ? (
                            <Chip icon={<CheckIcon />} label="Yes" color="success" size="small" />
                          ) : (
                            <Chip icon={<BlockIcon />} label="No" color="error" size="small" />
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                Apply Template
              </Typography>

              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Scope Type</InputLabel>
                    <Select
                      value={applyTemplateData.scope_type}
                      onChange={(e) => setApplyTemplateData({ ...applyTemplateData, scope_type: e.target.value })}
                      label="Scope Type"
                    >
                      <MenuItem value="user">User</MenuItem>
                      <MenuItem value="organization">Organization</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>

                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Scope ID"
                    value={applyTemplateData.scope_id}
                    onChange={(e) => setApplyTemplateData({ ...applyTemplateData, scope_id: e.target.value })}
                    placeholder={applyTemplateData.scope_type === 'user' ? 'User ID or email' : 'Organization ID'}
                    helperText={`Enter ${applyTemplateData.scope_type} identifier`}
                  />
                </Grid>

                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Permission Level (Optional)</InputLabel>
                    <Select
                      value={applyTemplateData.level}
                      onChange={(e) => setApplyTemplateData({ ...applyTemplateData, level: e.target.value })}
                      label="Permission Level (Optional)"
                    >
                      <MenuItem value="">Auto (based on scope type)</MenuItem>
                      <MenuItem value="system">System</MenuItem>
                      <MenuItem value="platform">Platform</MenuItem>
                      <MenuItem value="organization">Organization</MenuItem>
                      <MenuItem value="application">Application</MenuItem>
                      <MenuItem value="user">User</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>

              <Alert severity="info" sx={{ mt: 2 }}>
                This will create {selectedTemplate.permissions.length} permissions for the specified {applyTemplateData.scope_type}.
                Existing permissions will be updated.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setTemplateDetailsModalOpen(false);
            setApplyTemplateData({ scope_type: 'user', scope_id: '', level: '' });
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleApplyTemplate}
            disabled={templateLoading || !applyTemplateData.scope_id}
            sx={{
              bgcolor: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
              '&:hover': { bgcolor: currentTheme === 'unicorn' ? '#7e22ce' : '#2563eb' }
            }}
          >
            {templateLoading ? <CircularProgress size={24} /> : 'Apply Template'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Save As Template Modal */}
      <Dialog
        open={saveAsTemplateModalOpen}
        onClose={() => setSaveAsTemplateModalOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Save as Custom Template</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              This will save the current <strong>{permissions.filter(p => p.granted).length} granted permissions</strong> as a reusable template.
            </Alert>

            <TextField
              fullWidth
              label="Template Name"
              value={customTemplateName}
              onChange={(e) => setCustomTemplateName(e.target.value)}
              placeholder="e.g., Content Manager"
              sx={{ mb: 2 }}
              required
            />

            <TextField
              fullWidth
              multiline
              rows={3}
              label="Description"
              value={customTemplateDescription}
              onChange={(e) => setCustomTemplateDescription(e.target.value)}
              placeholder="Describe what this template is for and when to use it"
              required
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setSaveAsTemplateModalOpen(false);
            setCustomTemplateName('');
            setCustomTemplateDescription('');
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleSaveAsTemplate}
            disabled={templateLoading || !customTemplateName || !customTemplateDescription}
            sx={{
              bgcolor: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
              '&:hover': { bgcolor: currentTheme === 'unicorn' ? '#7e22ce' : '#2563eb' }
            }}
          >
            {templateLoading ? <CircularProgress size={24} /> : 'Save Template'}
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

export default PermissionsManagement;
