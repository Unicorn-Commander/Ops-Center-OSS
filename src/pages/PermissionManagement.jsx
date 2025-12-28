import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Checkbox,
  FormControlLabel,
  Card,
  CardContent,
  Grid,
  Menu,
  List,
  ListItem,
  ListItemText,
  Divider,
  Badge,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Check as CheckIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Shield as ShieldIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

/**
 * Permission Management Component
 * Comprehensive UI for managing the 5-level permission hierarchy
 * - System → Platform → Organization → Application → User
 */
export default function PermissionManagement() {
  const { currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data state
  const [hierarchy, setHierarchy] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [auditLog, setAuditLog] = useState([]);
  const [conflicts, setConflicts] = useState([]);

  // User search state (Tab 2)
  const [userSearchQuery, setUserSearchQuery] = useState('');
  const [selectedUser, setSelectedUser] = useState(null);
  const [userEffectivePerms, setUserEffectivePerms] = useState([]);
  const [users, setUsers] = useState([]);

  // Org state (Tab 3)
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [orgPermissions, setOrgPermissions] = useState([]);

  // Modal state
  const [openDialog, setOpenDialog] = useState(false);
  const [dialogType, setDialogType] = useState(''); // 'assign', 'revoke', 'template'
  const [dialogData, setDialogData] = useState({});

  // Toast state
  const [toast, setToast] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  // Permission levels
  const levels = ['system', 'platform', 'organization', 'application', 'user'];

  // Available resources
  const resources = [
    'users', 'billing', 'services', 'organizations', 'api_keys',
    'analytics', 'settings', 'logs', 'models', 'subscriptions'
  ];

  // Available actions
  const actions = ['read', 'write', 'admin', 'execute', 'delete'];

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        fetchHierarchy(),
        fetchTemplates(),
        fetchAuditLog(),
        fetchConflicts(),
        fetchUsers(),
        fetchOrganizations(),
      ]);
    } catch (err) {
      setError(err.message);
      showToast('Failed to load permission data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchHierarchy = async () => {
    try {
      const response = await fetch('/api/v1/permissions/hierarchy', {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch hierarchy');

      const data = await response.json();
      setHierarchy(data);
    } catch (err) {
      console.error('Error fetching hierarchy:', err);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/permissions/templates', {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch templates');

      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (err) {
      console.error('Error fetching templates:', err);
    }
  };

  const fetchAuditLog = async () => {
    try {
      const response = await fetch('/api/v1/permissions/audit?limit=100', {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch audit log');

      const data = await response.json();
      setAuditLog(data || []);
    } catch (err) {
      console.error('Error fetching audit log:', err);
    }
  };

  const fetchConflicts = async () => {
    try {
      const response = await fetch('/api/v1/permissions/conflicts', {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch conflicts');

      const data = await response.json();
      setConflicts(data || []);
    } catch (err) {
      console.error('Error fetching conflicts:', err);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await fetch('/api/v1/admin/users?limit=1000', {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch users');

      const data = await response.json();
      setUsers(data.users || []);
    } catch (err) {
      console.error('Error fetching users:', err);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('/api/v1/organizations', {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch organizations');

      const data = await response.json();
      setOrganizations(data.organizations || []);
    } catch (err) {
      console.error('Error fetching organizations:', err);
    }
  };

  const fetchUserEffectivePermissions = async (userId) => {
    try {
      const response = await fetch(`/api/v1/permissions/user/${userId}/effective`, {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch effective permissions');

      const data = await response.json();
      setUserEffectivePerms(data || []);
    } catch (err) {
      console.error('Error fetching effective permissions:', err);
      showToast('Failed to load user permissions', 'error');
    }
  };

  const handleUserSearch = (query) => {
    setUserSearchQuery(query);
  };

  const handleUserSelect = async (user) => {
    setSelectedUser(user);
    await fetchUserEffectivePermissions(user.id);
  };

  const handleAssignPermission = async (permissionData) => {
    try {
      const response = await fetch('/api/v1/permissions/assign', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(permissionData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to assign permission');
      }

      showToast('Permission assigned successfully', 'success');
      setOpenDialog(false);
      await loadData();

      // Refresh user effective permissions if user is selected
      if (selectedUser) {
        await fetchUserEffectivePermissions(selectedUser.id);
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleRevokePermission = async (permissionData) => {
    try {
      const response = await fetch('/api/v1/permissions/revoke', {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(permissionData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to revoke permission');
      }

      showToast('Permission revoked successfully', 'success');
      await loadData();

      // Refresh user effective permissions if user is selected
      if (selectedUser) {
        await fetchUserEffectivePermissions(selectedUser.id);
      }
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const getLevelColor = (level) => {
    const colors = {
      system: '#ef4444',
      platform: '#f59e0b',
      organization: '#10b981',
      application: '#3b82f6',
      user: '#8b5cf6',
    };
    return colors[level] || '#6b7280';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 400 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 3 }}>
        {error}
        <Button onClick={loadData} size="small" sx={{ ml: 2 }}>
          Retry
        </Button>
      </Alert>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            Permission Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage the 5-level permission hierarchy: System → Platform → Organization → Application → User
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setDialogType('assign');
              setDialogData({});
              setOpenDialog(true);
            }}
          >
            Assign Permission
          </Button>
        </Box>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Permission Matrix" />
          <Tab label="User Permissions" />
          <Tab label="Organization Permissions" />
          <Tab label="Role Templates" />
          <Tab label="Audit Log" />
          <Tab label={
            <Badge badgeContent={conflicts.length} color="error">
              Conflicts
            </Badge>
          } />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {activeTab === 0 && <PermissionMatrixTab hierarchy={hierarchy} levels={levels} getLevelColor={getLevelColor} />}
        {activeTab === 1 && (
          <UserPermissionsTab
            users={users}
            selectedUser={selectedUser}
            userEffectivePerms={userEffectivePerms}
            onUserSelect={handleUserSelect}
            onSearch={handleUserSearch}
            onAssign={(data) => {
              setDialogType('assign');
              setDialogData({ ...data, user_id: selectedUser?.id });
              setOpenDialog(true);
            }}
            onRevoke={handleRevokePermission}
            getLevelColor={getLevelColor}
          />
        )}
        {activeTab === 2 && (
          <OrganizationPermissionsTab
            organizations={organizations}
            selectedOrg={selectedOrg}
            onOrgSelect={setSelectedOrg}
            onAssign={(data) => {
              setDialogType('assign');
              setDialogData({ ...data, level: 'organization', scope_id: selectedOrg?.id });
              setOpenDialog(true);
            }}
            onRevoke={handleRevokePermission}
            getLevelColor={getLevelColor}
          />
        )}
        {activeTab === 3 && (
          <RoleTemplatesTab
            templates={templates}
            onRefresh={fetchTemplates}
            showToast={showToast}
          />
        )}
        {activeTab === 4 && <AuditLogTab auditLog={auditLog} getLevelColor={getLevelColor} />}
        {activeTab === 5 && (
          <ConflictsTab
            conflicts={conflicts}
            onResolve={async (conflict) => {
              // Handle conflict resolution
              showToast('Conflict resolution functionality coming soon', 'info');
            }}
            getLevelColor={getLevelColor}
          />
        )}
      </Box>

      {/* Assign/Revoke Dialog */}
      <AssignPermissionDialog
        open={openDialog && dialogType === 'assign'}
        onClose={() => setOpenDialog(false)}
        onSubmit={handleAssignPermission}
        initialData={dialogData}
        levels={levels}
        resources={resources}
        actions={actions}
      />

      {/* Toast Notifications */}
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
}

// ============================================================================
// TAB 1: Permission Matrix
// ============================================================================
function PermissionMatrixTab({ hierarchy, levels, getLevelColor }) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Permission Hierarchy Visualization
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Visual representation of the permission hierarchy from System level (highest) to User level (lowest).
      </Typography>

      {hierarchy ? (
        <Box sx={{ mt: 3 }}>
          <HierarchyTreeNode node={hierarchy} level={0} getLevelColor={getLevelColor} />
        </Box>
      ) : (
        <Alert severity="info">No permission hierarchy data available</Alert>
      )}
    </Paper>
  );
}

function HierarchyTreeNode({ node, level, getLevelColor }) {
  const [expanded, setExpanded] = useState(level < 2); // Expand first 2 levels by default

  return (
    <Box sx={{ ml: level * 3 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1,
          p: 1,
          borderLeft: `3px solid ${getLevelColor(node.level)}`,
          bgcolor: 'background.default',
          borderRadius: 1,
          mb: 1,
        }}
      >
        {node.children && node.children.length > 0 && (
          <IconButton size="small" onClick={() => setExpanded(!expanded)}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        )}
        <Box sx={{ flex: 1 }}>
          <Typography variant="body1" fontWeight="medium">
            {node.name}
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 0.5 }}>
            {node.permissions && node.permissions.map((perm, idx) => (
              <Chip
                key={idx}
                label={`${perm.resource}:${perm.action}`}
                size="small"
                color={perm.granted ? 'success' : 'default'}
              />
            ))}
          </Box>
        </Box>
        <Chip
          label={node.level}
          size="small"
          sx={{ bgcolor: getLevelColor(node.level), color: 'white' }}
        />
      </Box>

      {expanded && node.children && (
        <Box sx={{ mt: 1 }}>
          {node.children.map((child, idx) => (
            <HierarchyTreeNode
              key={idx}
              node={child}
              level={level + 1}
              getLevelColor={getLevelColor}
            />
          ))}
        </Box>
      )}
    </Box>
  );
}

// ============================================================================
// TAB 2: User Permissions
// ============================================================================
function UserPermissionsTab({ users, selectedUser, userEffectivePerms, onUserSelect, onSearch, onAssign, onRevoke, getLevelColor }) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredUsers = users.filter(user =>
    user.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.username?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <Grid container spacing={3}>
      {/* User Search */}
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Search Users
          </Typography>
          <TextField
            fullWidth
            placeholder="Search by email or username..."
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              onSearch(e.target.value);
            }}
            InputProps={{
              startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            }}
            sx={{ mb: 2 }}
          />

          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {filteredUsers.map(user => (
              <ListItem
                key={user.id}
                button
                selected={selectedUser?.id === user.id}
                onClick={() => onUserSelect(user)}
              >
                <ListItemText
                  primary={user.username || user.email}
                  secondary={user.email}
                />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      {/* User Effective Permissions */}
      <Grid item xs={12} md={8}>
        {selectedUser ? (
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="h6">
                  {selectedUser.username || selectedUser.email}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Effective Permissions with Inheritance Chain
                </Typography>
              </Box>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => onAssign({})}
              >
                Add Override
              </Button>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Resource</TableCell>
                    <TableCell>Action</TableCell>
                    <TableCell>Granted</TableCell>
                    <TableCell>Level</TableCell>
                    <TableCell>Inherited From</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {userEffectivePerms.map((perm, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{perm.resource}</TableCell>
                      <TableCell>{perm.action}</TableCell>
                      <TableCell>
                        <Chip
                          label={perm.granted ? 'Yes' : 'No'}
                          color={perm.granted ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={perm.effective_level}
                          size="small"
                          sx={{ bgcolor: getLevelColor(perm.effective_level), color: 'white' }}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {perm.inherited_from || 'Direct'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        {perm.can_override && (
                          <IconButton
                            size="small"
                            onClick={() => onRevoke({
                              user_id: selectedUser.id,
                              resource: perm.resource,
                              action: perm.action,
                              level: 'user',
                            })}
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {userEffectivePerms.length === 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                No effective permissions found for this user. Assign roles or permissions to grant access.
              </Alert>
            )}
          </Paper>
        ) : (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <ShieldIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              Select a user to view their permissions
            </Typography>
          </Paper>
        )}
      </Grid>
    </Grid>
  );
}

// ============================================================================
// TAB 3: Organization Permissions
// ============================================================================
function OrganizationPermissionsTab({ organizations, selectedOrg, onOrgSelect, onAssign, onRevoke, getLevelColor }) {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={4}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Organizations
          </Typography>
          <List>
            {organizations.map(org => (
              <ListItem
                key={org.id}
                button
                selected={selectedOrg?.id === org.id}
                onClick={() => onOrgSelect(org)}
              >
                <ListItemText primary={org.name} secondary={`${org.member_count || 0} members`} />
              </ListItem>
            ))}
          </List>
        </Paper>
      </Grid>

      <Grid item xs={12} md={8}>
        {selectedOrg ? (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              {selectedOrg.name} Permissions
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => onAssign({})}
              sx={{ mb: 2 }}
            >
              Add Permission
            </Button>
            <Alert severity="info">
              Organization permission management coming soon
            </Alert>
          </Paper>
        ) : (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Select an organization to manage permissions
            </Typography>
          </Paper>
        )}
      </Grid>
    </Grid>
  );
}

// ============================================================================
// TAB 4: Role Templates
// ============================================================================
function RoleTemplatesTab({ templates, onRefresh, showToast }) {
  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6">
          Permission Templates
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />}>
          Create Template
        </Button>
      </Box>

      <Grid container spacing={2}>
        {templates.map(template => (
          <Grid item xs={12} md={6} key={template.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {template.name}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  {template.description}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
                  {template.permissions?.map((perm, idx) => (
                    <Chip key={idx} label={`${perm.resource}:${perm.action}`} size="small" />
                  ))}
                </Box>
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button size="small" startIcon={<EditIcon />}>
                    Edit
                  </Button>
                  <Button size="small" color="error" startIcon={<DeleteIcon />}>
                    Delete
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {templates.length === 0 && (
        <Alert severity="info">
          No permission templates found. Create a template to reuse permission sets across users and organizations.
        </Alert>
      )}
    </Paper>
  );
}

// ============================================================================
// TAB 5: Audit Log
// ============================================================================
function AuditLogTab({ auditLog, getLevelColor }) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Permission Change Audit Log
      </Typography>

      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Resource</TableCell>
              <TableCell>Permission</TableCell>
              <TableCell>Scope</TableCell>
              <TableCell>Changed By</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {auditLog.map((entry, idx) => (
              <TableRow key={idx}>
                <TableCell>
                  <Typography variant="caption">
                    {new Date(entry.timestamp).toLocaleString()}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={entry.action}
                    size="small"
                    color={entry.action === 'assign' ? 'success' : 'error'}
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={entry.level}
                    size="small"
                    sx={{ bgcolor: getLevelColor(entry.level), color: 'white' }}
                  />
                </TableCell>
                <TableCell>{entry.resource}</TableCell>
                <TableCell>{entry.permission_action}</TableCell>
                <TableCell>
                  <Typography variant="caption">
                    {entry.scope_id || 'Global'}
                  </Typography>
                </TableCell>
                <TableCell>{entry.changed_by}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {auditLog.length === 0 && (
        <Alert severity="info" sx={{ mt: 2 }}>
          No audit log entries found
        </Alert>
      )}
    </Paper>
  );
}

// ============================================================================
// TAB 6: Conflicts
// ============================================================================
function ConflictsTab({ conflicts, onResolve, getLevelColor }) {
  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Permission Conflicts
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Conflicts occur when different levels grant conflicting permissions (allow vs deny).
      </Typography>

      {conflicts.map((conflict, idx) => (
        <Card key={idx} sx={{ mb: 2, borderLeft: '4px solid', borderLeftColor: 'error.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" gutterBottom>
                  {conflict.resource}:{conflict.action}
                </Typography>

                <Typography variant="body2" color="text.secondary" paragraph>
                  Resolution: {conflict.resolution}
                </Typography>

                <Typography variant="body2" fontWeight="medium" gutterBottom>
                  Conflicting Permissions:
                </Typography>

                <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 2 }}>
                  {conflict.conflicts.map((c, i) => (
                    <Chip
                      key={i}
                      label={`${c.level}: ${c.granted ? 'Allow' : 'Deny'}`}
                      color={c.granted ? 'success' : 'error'}
                      sx={{ bgcolor: getLevelColor(c.level), color: 'white' }}
                    />
                  ))}
                </Box>

                <Alert severity="warning" sx={{ mb: 2 }}>
                  Recommended: {conflict.recommended_action}
                </Alert>
              </Box>

              <Button
                variant="outlined"
                onClick={() => onResolve(conflict)}
              >
                Resolve
              </Button>
            </Box>
          </CardContent>
        </Card>
      ))}

      {conflicts.length === 0 && (
        <Alert severity="success">
          <Typography variant="body1" fontWeight="medium" gutterBottom>
            No permission conflicts detected
          </Typography>
          <Typography variant="body2">
            All permission levels are properly aligned with no conflicting rules.
          </Typography>
        </Alert>
      )}
    </Paper>
  );
}

// ============================================================================
// Assign Permission Dialog
// ============================================================================
function AssignPermissionDialog({ open, onClose, onSubmit, initialData, levels, resources, actions }) {
  const [formData, setFormData] = useState({
    level: 'user',
    resource: '',
    action: '',
    granted: true,
    scope_id: '',
    user_id: '',
    ...initialData,
  });

  useEffect(() => {
    setFormData({
      level: 'user',
      resource: '',
      action: '',
      granted: true,
      scope_id: '',
      user_id: '',
      ...initialData,
    });
  }, [initialData]);

  const handleSubmit = () => {
    onSubmit(formData);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Assign Permission</DialogTitle>
      <DialogContent>
        <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          <FormControl fullWidth>
            <InputLabel>Level</InputLabel>
            <Select
              value={formData.level}
              onChange={(e) => setFormData({ ...formData, level: e.target.value })}
              label="Level"
            >
              {levels.map(level => (
                <MenuItem key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Resource</InputLabel>
            <Select
              value={formData.resource}
              onChange={(e) => setFormData({ ...formData, resource: e.target.value })}
              label="Resource"
            >
              {resources.map(resource => (
                <MenuItem key={resource} value={resource}>
                  {resource}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl fullWidth>
            <InputLabel>Action</InputLabel>
            <Select
              value={formData.action}
              onChange={(e) => setFormData({ ...formData, action: e.target.value })}
              label="Action"
            >
              {actions.map(action => (
                <MenuItem key={action} value={action}>
                  {action}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Checkbox
                checked={formData.granted}
                onChange={(e) => setFormData({ ...formData, granted: e.target.checked })}
              />
            }
            label="Granted (Allow)"
          />

          {formData.level !== 'system' && (
            <TextField
              fullWidth
              label="Scope ID (optional)"
              placeholder="Organization ID, App ID, or User ID"
              value={formData.scope_id}
              onChange={(e) => setFormData({ ...formData, scope_id: e.target.value })}
              helperText="Leave empty for global scope at this level"
            />
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!formData.resource || !formData.action}
        >
          Assign
        </Button>
      </DialogActions>
    </Dialog>
  );
}
