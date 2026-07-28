import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  Chip,
  IconButton,
  InputAdornment,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Alert,
  Divider,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  Delete as DeleteIcon,
  Security as SecurityIcon,
  AdminPanelSettings as AdminIcon,
  Person as PersonIcon,
  Group as GroupIcon,
  Close as CloseIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import PermissionMatrix from './PermissionMatrix';

/**
 * Enhanced Role Management Modal
 * Dual-panel interface for managing user roles with permission visualization
 *
 * Props:
 * - open: Boolean to control modal visibility
 * - onClose: Function to close modal
 * - user: User object with roles
 * - availableRoles: Array of all available roles
 * - onRoleAssign: Function to assign role (userId, role)
 * - onRoleRemove: Function to remove role (userId, role)
 */
const RoleManagementModal = ({
  open,
  onClose,
  user,
  availableRoles = [],
  onRoleAssign,
  onRoleRemove,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [roleTypeFilter, setRoleTypeFilter] = useState('all');
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [actionToConfirm, setActionToConfirm] = useState(null);

  // Role hierarchy and grouping
  const roleHierarchy = {
    'brigade-platform-admin': {
      level: 5,
      type: 'admin',
      description: 'Full platform administration access',
      permissions: [
        'manage_users',
        'manage_organizations',
        'manage_billing',
        'manage_roles',
        'view_all_data',
      ],
    },
    'brigade-platform-moderator': {
      level: 4,
      type: 'moderator',
      description: 'Content moderation and user support',
      permissions: ['moderate_content', 'support_users', 'view_user_data'],
    },
    'brigade-platform-developer': {
      level: 3,
      type: 'developer',
      description: 'Agent development and API access',
      permissions: ['create_agents', 'api_access', 'webhook_access'],
    },
    'brigade-platform-analyst': {
      level: 2,
      type: 'analyst',
      description: 'Data analysis and reporting',
      permissions: ['view_analytics', 'export_data', 'generate_reports'],
    },
    'brigade-platform-viewer': {
      level: 1,
      type: 'viewer',
      description: 'Read-only access to platform',
      permissions: ['view_data'],
    },
  };

  // Role templates for quick assignment
  const roleTemplates = {
    'Admin User': ['brigade-platform-admin'],
    'Standard User': ['brigade-platform-developer', 'brigade-platform-viewer'],
    'Read-Only User': ['brigade-platform-viewer'],
    'Support User': ['brigade-platform-moderator', 'brigade-platform-viewer'],
  };

  // Initialize selected roles from user
  useEffect(() => {
    if (user && user.roles) {
      setSelectedRoles(user.roles.filter(r => r.startsWith('brigade-')));
    }
  }, [user]);

  // Filter available roles based on search and type
  const filteredRoles = availableRoles.filter(role => {
    // Filter by search query
    const matchesSearch =
      !searchQuery ||
      role.toLowerCase().includes(searchQuery.toLowerCase()) ||
      roleHierarchy[role]?.description?.toLowerCase().includes(searchQuery.toLowerCase());

    // Filter by role type
    const matchesType =
      roleTypeFilter === 'all' ||
      roleHierarchy[role]?.type === roleTypeFilter;

    // Exclude already selected roles
    const notSelected = !selectedRoles.includes(role);

    return matchesSearch && matchesType && notSelected;
  });

  // Get role icon based on type
  const getRoleIcon = (role) => {
    const type = roleHierarchy[role]?.type;
    switch (type) {
      case 'admin':
        return <AdminIcon color="error" />;
      case 'moderator':
        return <SecurityIcon color="warning" />;
      case 'developer':
      case 'analyst':
        return <GroupIcon color="primary" />;
      default:
        return <PersonIcon color="action" />;
    }
  };

  // Get role level badge color
  const getRoleLevelColor = (role) => {
    const level = roleHierarchy[role]?.level || 0;
    if (level >= 5) return 'error';
    if (level >= 4) return 'warning';
    if (level >= 3) return 'primary';
    if (level >= 2) return 'info';
    return 'default';
  };

  // Handle role assignment
  const handleAssignRole = async (role) => {
    // Check if role is admin role - require confirmation
    if (roleHierarchy[role]?.type === 'admin') {
      setActionToConfirm({ action: 'assign', role });
      setShowConfirmDialog(true);
      return;
    }

    await executeRoleAssignment(role);
  };

  const executeRoleAssignment = async (role) => {
    setLoading(true);
    setError(null);

    try {
      await onRoleAssign(user.id, role);
      setSelectedRoles([...selectedRoles, role]);
    } catch (err) {
      setError(`Failed to assign role: ${err.message}`);
    } finally {
      setLoading(false);
      setShowConfirmDialog(false);
      setActionToConfirm(null);
    }
  };

  // Handle role removal
  const handleRemoveRole = async (role) => {
    // Check if role is admin role - require confirmation
    if (roleHierarchy[role]?.type === 'admin') {
      setActionToConfirm({ action: 'remove', role });
      setShowConfirmDialog(true);
      return;
    }

    await executeRoleRemoval(role);
  };

  const executeRoleRemoval = async (role) => {
    setLoading(true);
    setError(null);

    try {
      await onRoleRemove(user.id, role);
      setSelectedRoles(selectedRoles.filter(r => r !== role));
    } catch (err) {
      setError(`Failed to remove role: ${err.message}`);
    } finally {
      setLoading(false);
      setShowConfirmDialog(false);
      setActionToConfirm(null);
    }
  };

  // Apply role template
  const handleApplyTemplate = async (templateName) => {
    const roles = roleTemplates[templateName];
    if (!roles) return;

    setLoading(true);
    setError(null);

    try {
      // Assign all roles in template
      for (const role of roles) {
        if (!selectedRoles.includes(role)) {
          await onRoleAssign(user.id, role);
        }
      }

      setSelectedRoles([...new Set([...selectedRoles, ...roles])]);
    } catch (err) {
      setError(`Failed to apply template: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Get effective permissions from selected roles
  const getRolePermissions = () => {
    const permissions = {};
    selectedRoles.forEach(role => {
      const roleInfo = roleHierarchy[role];
      if (roleInfo && roleInfo.permissions) {
        roleInfo.permissions.forEach(perm => {
          if (!permissions[perm]) {
            permissions[perm] = [];
          }
          permissions[perm].push(role);
        });
      }
    });
    return permissions;
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="lg"
        fullWidth
        PaperProps={{
          sx: { height: '90vh' }
        }}
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6">
                Manage Roles - {user?.username}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {user?.email}
              </Typography>
            </Box>
            <IconButton onClick={onClose} edge="end">
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent dividers>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {/* Role Templates */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Quick Templates
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {Object.keys(roleTemplates).map(template => (
                <Button
                  key={template}
                  size="small"
                  variant="outlined"
                  onClick={() => handleApplyTemplate(template)}
                  disabled={loading}
                >
                  Apply "{template}"
                </Button>
              ))}
            </Box>
          </Box>

          <Divider sx={{ mb: 3 }} />

          {/* Dual Panel Layout */}
          <Grid container spacing={2} sx={{ height: '400px' }}>
            {/* Left Panel - Available Roles */}
            <Grid item xs={12} md={5}>
              <Paper
                sx={{
                  p: 2,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  bgcolor: 'background.default'
                }}
              >
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Available Roles
                </Typography>

                {/* Search */}
                <TextField
                  size="small"
                  placeholder="Search roles..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  sx={{ mb: 1 }}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    ),
                  }}
                />

                {/* Filter by type */}
                <FormControl size="small" sx={{ mb: 2 }}>
                  <InputLabel>Filter by Type</InputLabel>
                  <Select
                    value={roleTypeFilter}
                    label="Filter by Type"
                    onChange={(e) => setRoleTypeFilter(e.target.value)}
                  >
                    <MenuItem value="all">All Roles</MenuItem>
                    <MenuItem value="admin">Admin</MenuItem>
                    <MenuItem value="moderator">Moderator</MenuItem>
                    <MenuItem value="developer">Developer</MenuItem>
                    <MenuItem value="analyst">Analyst</MenuItem>
                    <MenuItem value="viewer">Viewer</MenuItem>
                  </Select>
                </FormControl>

                {/* Available roles list */}
                <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                  <List dense>
                    {filteredRoles.map(role => (
                      <ListItem
                        key={role}
                        disablePadding
                        secondaryAction={
                          <IconButton
                            edge="end"
                            size="small"
                            onClick={() => handleAssignRole(role)}
                            disabled={loading}
                          >
                            <ArrowForwardIcon fontSize="small" />
                          </IconButton>
                        }
                      >
                        <ListItemButton onClick={() => handleAssignRole(role)} disabled={loading}>
                          <ListItemIcon>{getRoleIcon(role)}</ListItemIcon>
                          <ListItemText
                            primary={
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <Typography variant="body2">{typeof role === 'string' ? role.replace(/^brigade-(platform-)?/, '') : String(role || '')}</Typography>
                                <Chip
                                  label={roleHierarchy[role]?.level || 0}
                                  size="small"
                                  color={getRoleLevelColor(role)}
                                />
                              </Box>
                            }
                            secondary={roleHierarchy[role]?.description || 'No description'}
                          />
                        </ListItemButton>
                      </ListItem>
                    ))}
                    {filteredRoles.length === 0 && (
                      <Box sx={{ textAlign: 'center', py: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                          No roles available
                        </Typography>
                      </Box>
                    )}
                  </List>
                </Box>
              </Paper>
            </Grid>

            {/* Middle - Transfer Buttons */}
            <Grid
              item
              xs={12}
              md={2}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'center',
                alignItems: 'center',
                gap: 2,
              }}
            >
              <Typography variant="caption" color="text.secondary" align="center">
                Assign/Remove
              </Typography>
            </Grid>

            {/* Right Panel - Assigned Roles */}
            <Grid item xs={12} md={5}>
              <Paper
                sx={{
                  p: 2,
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  bgcolor: 'background.default'
                }}
              >
                <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
                  Assigned Roles ({selectedRoles.length})
                </Typography>

                {/* Assigned roles list */}
                <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
                  <List dense>
                    {selectedRoles.map(role => (
                      <ListItem
                        key={role}
                        secondaryAction={
                          <IconButton
                            edge="end"
                            size="small"
                            color="error"
                            onClick={() => handleRemoveRole(role)}
                            disabled={loading}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        }
                      >
                        <ListItemIcon>{getRoleIcon(role)}</ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body2">{typeof role === 'string' ? role.replace(/^brigade-(platform-)?/, '') : String(role || '')}</Typography>
                              <Chip
                                label={roleHierarchy[role]?.level || 0}
                                size="small"
                                color={getRoleLevelColor(role)}
                              />
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="caption">
                                {roleHierarchy[role]?.description || 'No description'}
                              </Typography>
                              <br />
                              <Typography variant="caption" color="primary">
                                {roleHierarchy[role]?.permissions?.length || 0} permissions
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                    ))}
                    {selectedRoles.length === 0 && (
                      <Box sx={{ textAlign: 'center', py: 3 }}>
                        <Typography variant="body2" color="text.secondary">
                          No roles assigned
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          Select roles from the left panel
                        </Typography>
                      </Box>
                    )}
                  </List>
                </Box>
              </Paper>
            </Grid>
          </Grid>

          {/* Permission Matrix */}
          <PermissionMatrix
            roles={selectedRoles}
            rolePermissions={getRolePermissions()}
            expanded={selectedRoles.length > 0}
          />
        </DialogContent>

        <DialogActions>
          <Button onClick={onClose} disabled={loading}>
            Close
          </Button>
          <Button
            variant="contained"
            onClick={onClose}
            disabled={loading}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              },
            }}
          >
            Done
          </Button>
        </DialogActions>
      </Dialog>

      {/* Confirmation Dialog for Admin Role Changes */}
      <Dialog
        open={showConfirmDialog}
        onClose={() => setShowConfirmDialog(false)}
        maxWidth="sm"
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WarningIcon color="warning" />
            Confirm Role Change
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography>
            {actionToConfirm?.action === 'assign' ? (
              <>
                You are about to assign the <strong>{actionToConfirm?.role}</strong> role.
                This role grants administrative privileges. Are you sure?
              </>
            ) : (
              <>
                You are about to remove the <strong>{actionToConfirm?.role}</strong> role.
                This will revoke administrative privileges. Are you sure?
              </>
            )}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowConfirmDialog(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={actionToConfirm?.action === 'assign' ? 'warning' : 'error'}
            onClick={() => {
              if (actionToConfirm?.action === 'assign') {
                executeRoleAssignment(actionToConfirm.role);
              } else {
                executeRoleRemoval(actionToConfirm.role);
              }
            }}
          >
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default RoleManagementModal;
