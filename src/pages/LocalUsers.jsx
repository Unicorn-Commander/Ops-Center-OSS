import React, { useState, useEffect } from 'react';
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
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  LinearProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  VpnKey as VpnKeyIcon,
  Security as SecurityIcon,
  Refresh as RefreshIcon,
  PersonAdd as PersonAddIcon,
  AdminPanelSettings as AdminIcon,
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Terminal as TerminalIcon,
  Folder as FolderIcon,
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Password as PasswordIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

const LocalUsers = () => {
  const { currentTheme } = useTheme();

  // State for user list
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Stats
  const [stats, setStats] = useState({
    total: 0,
    active_sessions: 0,
    sudo_users: 0,
  });

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Search/Filter
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [passwordModalOpen, setPasswordModalOpen] = useState(false);
  const [sshModalOpen, setSshModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);

  // Current user for modals
  const [selectedUser, setSelectedUser] = useState(null);

  // Create user form
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    sudo: false,
    home_directory: '',
    shell: '/bin/bash',
  });

  // Password reset form
  const [newPassword, setNewPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);

  // SSH key form
  const [sshKeys, setSshKeys] = useState([]);
  const [newSshKey, setNewSshKey] = useState('');

  // Toast notifications
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });

  // Theme-based styling
  const getThemeStyles = () => {
    if (currentTheme === 'unicorn') {
      return {
        background: 'bg-gradient-to-br from-purple-900/20 to-pink-900/20',
        paper: 'bg-white/10 backdrop-blur-md border border-purple-500/20',
        text: 'text-white',
        textSecondary: 'text-purple-200',
        button: 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white',
      };
    } else if (currentTheme === 'light') {
      return {
        background: 'bg-gray-50',
        paper: 'bg-white',
        text: 'text-gray-900',
        textSecondary: 'text-gray-600',
        button: 'bg-blue-600 hover:bg-blue-700 text-white',
      };
    } else {
      return {
        background: 'bg-slate-900',
        paper: 'bg-slate-800',
        text: 'text-white',
        textSecondary: 'text-gray-400',
        button: 'bg-blue-600 hover:bg-blue-700 text-white',
      };
    }
  };

  const themeStyles = getThemeStyles();

  // Fetch users
  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/local-users', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch local users');
      }

      const data = await response.json();
      setUsers(data.users || []);

      // Calculate stats
      const sudoCount = data.users.filter(u => u.sudo).length;
      const activeSessionsCount = data.users.filter(u => u.last_login &&
        new Date(u.last_login) > new Date(Date.now() - 24 * 60 * 60 * 1000)
      ).length;

      setStats({
        total: data.users.length,
        active_sessions: activeSessionsCount,
        sudo_users: sudoCount,
      });
    } catch (err) {
      setError(err.message);
      showToast('Failed to load users: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  // Create user
  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.password) {
      showToast('Username and password are required', 'error');
      return;
    }

    try {
      const response = await fetch('/api/v1/local-users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          username: newUser.username,
          password: newUser.password,
          sudo: newUser.sudo,
          home_directory: newUser.home_directory || undefined,
          shell: newUser.shell || '/bin/bash',
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create user');
      }

      showToast(`User ${newUser.username} created successfully`, 'success');
      setCreateModalOpen(false);
      setNewUser({ username: '', password: '', sudo: false, home_directory: '', shell: '/bin/bash' });
      fetchUsers();
    } catch (err) {
      showToast('Failed to create user: ' + err.message, 'error');
    }
  };

  // Reset password
  const handleResetPassword = async () => {
    if (!newPassword) {
      showToast('Password is required', 'error');
      return;
    }

    try {
      const response = await fetch(`/api/v1/local-users/${selectedUser.username}/password`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ password: newPassword }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to reset password');
      }

      showToast(`Password reset for ${selectedUser.username}`, 'success');
      setPasswordModalOpen(false);
      setNewPassword('');
      setSelectedUser(null);
    } catch (err) {
      showToast('Failed to reset password: ' + err.message, 'error');
    }
  };

  // Fetch SSH keys
  const fetchSshKeys = async (username) => {
    try {
      const response = await fetch(`/api/v1/local-users/${username}/ssh-keys`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch SSH keys');
      }

      const data = await response.json();
      setSshKeys(data.keys || []);
    } catch (err) {
      showToast('Failed to load SSH keys: ' + err.message, 'error');
    }
  };

  // Add SSH key
  const handleAddSshKey = async () => {
    if (!newSshKey.trim()) {
      showToast('SSH key is required', 'error');
      return;
    }

    try {
      const response = await fetch(`/api/v1/local-users/${selectedUser.username}/ssh-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ key: newSshKey }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add SSH key');
      }

      showToast('SSH key added successfully', 'success');
      setNewSshKey('');
      fetchSshKeys(selectedUser.username);
    } catch (err) {
      showToast('Failed to add SSH key: ' + err.message, 'error');
    }
  };

  // Delete SSH key
  const handleDeleteSshKey = async (keyIndex) => {
    try {
      const response = await fetch(`/api/v1/local-users/${selectedUser.username}/ssh-keys/${keyIndex}`, {
        method: 'DELETE',
        credentials: 'include',
      });

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

  // Grant/Revoke sudo
  const handleToggleSudo = async (user) => {
    try {
      const endpoint = user.sudo ? 'revoke-sudo' : 'grant-sudo';
      const response = await fetch(`/api/v1/local-users/${user.username}/${endpoint}`, {
        method: 'POST',
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${endpoint.replace('-', ' ')}`);
      }

      showToast(`Sudo ${user.sudo ? 'revoked from' : 'granted to'} ${user.username}`, 'success');
      fetchUsers();
    } catch (err) {
      showToast('Failed to modify sudo privileges: ' + err.message, 'error');
    }
  };

  // Delete user
  const handleDeleteUser = async () => {
    try {
      const response = await fetch(`/api/v1/local-users/${selectedUser.username}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete user');
      }

      showToast(`User ${selectedUser.username} deleted successfully`, 'success');
      setDeleteModalOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (err) {
      showToast('Failed to delete user: ' + err.message, 'error');
    }
  };

  // Open SSH modal
  const openSshModal = (user) => {
    setSelectedUser(user);
    setSshModalOpen(true);
    fetchSshKeys(user.username);
  };

  // Password strength calculation
  useEffect(() => {
    if (newPassword) {
      let strength = 0;
      if (newPassword.length >= 8) strength += 25;
      if (newPassword.length >= 12) strength += 25;
      if (/[a-z]/.test(newPassword) && /[A-Z]/.test(newPassword)) strength += 25;
      if (/[0-9]/.test(newPassword)) strength += 15;
      if (/[^a-zA-Z0-9]/.test(newPassword)) strength += 10;
      setPasswordStrength(Math.min(strength, 100));
    } else {
      setPasswordStrength(0);
    }
  }, [newPassword]);

  // Toast helper
  const showToast = (message, severity = 'info') => {
    setToast({ open: true, message, severity });
  };

  // Filter users
  const filteredUsers = users.filter(user =>
    user.username.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Paginate users
  const paginatedUsers = filteredUsers.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" sx={{ fontWeight: 600, mb: 1 }}>
            <PeopleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Local User Management
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage Linux users on the server
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchUsers}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PersonAddIcon />}
            onClick={() => setCreateModalOpen(true)}
          >
            Create User
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.total}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Users
                  </Typography>
                </Box>
                <PeopleIcon sx={{ fontSize: 48, color: 'primary.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.active_sessions}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Sessions (24h)
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" sx={{ fontWeight: 600 }}>
                    {stats.sudo_users}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Sudo Users
                  </Typography>
                </Box>
                <AdminIcon sx={{ fontSize: 48, color: 'warning.main', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search users by username..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <TerminalIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />
      </Paper>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* User Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Username</TableCell>
                <TableCell>UID</TableCell>
                <TableCell>Groups</TableCell>
                <TableCell>Sudo</TableCell>
                <TableCell>Home Directory</TableCell>
                <TableCell>Shell</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 8 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : paginatedUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      {searchQuery ? 'No users found matching your search' : 'No users found'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedUsers.map((user) => (
                  <TableRow key={user.username} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <TerminalIcon fontSize="small" color="action" />
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 500 }}>
                          {user.username}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Chip label={user.uid} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {user.groups?.join(', ') || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {user.sudo ? (
                        <Chip
                          icon={<AdminIcon />}
                          label="Sudo"
                          color="warning"
                          size="small"
                        />
                      ) : (
                        <Chip label="User" size="small" variant="outlined" />
                      )}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <FolderIcon fontSize="small" color="action" />
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                          {user.home_directory}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                        {user.shell}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {user.last_login || 'Never'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Reset Password">
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedUser(user);
                            setPasswordModalOpen(true);
                          }}
                        >
                          <PasswordIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Manage SSH Keys">
                        <IconButton
                          size="small"
                          onClick={() => openSshModal(user)}
                        >
                          <VpnKeyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={user.sudo ? 'Revoke Sudo' : 'Grant Sudo'}>
                        <IconButton
                          size="small"
                          color={user.sudo ? 'warning' : 'default'}
                          onClick={() => handleToggleSudo(user)}
                        >
                          <SecurityIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete User">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => {
                            setSelectedUser(user);
                            setDeleteModalOpen(true);
                          }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          component="div"
          count={filteredUsers.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>

      {/* Create User Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Create New User</Typography>
            <IconButton onClick={() => setCreateModalOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Username"
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              fullWidth
              required
              helperText="Linux username (lowercase, no spaces)"
            />
            <TextField
              label="Password"
              type={showPassword ? 'text' : 'password'}
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              fullWidth
              required
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                ),
              }}
            />
            <TextField
              label="Home Directory (optional)"
              value={newUser.home_directory}
              onChange={(e) => setNewUser({ ...newUser, home_directory: e.target.value })}
              fullWidth
              placeholder="/home/username"
              helperText="Leave empty for default /home/username"
            />
            <FormControl fullWidth>
              <InputLabel>Shell</InputLabel>
              <Select
                value={newUser.shell}
                onChange={(e) => setNewUser({ ...newUser, shell: e.target.value })}
                label="Shell"
              >
                <MenuItem value="/bin/bash">bash</MenuItem>
                <MenuItem value="/bin/sh">sh</MenuItem>
                <MenuItem value="/bin/zsh">zsh</MenuItem>
                <MenuItem value="/bin/fish">fish</MenuItem>
                <MenuItem value="/usr/sbin/nologin">nologin (service accounts)</MenuItem>
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={newUser.sudo}
                  onChange={(e) => setNewUser({ ...newUser, sudo: e.target.checked })}
                />
              }
              label="Grant sudo privileges"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateUser}
            disabled={!newUser.username || !newUser.password}
          >
            Create User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Password Reset Modal */}
      <Dialog
        open={passwordModalOpen}
        onClose={() => setPasswordModalOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Reset Password</Typography>
            <IconButton onClick={() => setPasswordModalOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <Alert severity="info">
              Resetting password for user: <strong>{selectedUser?.username}</strong>
            </Alert>
            <TextField
              label="New Password"
              type={showPassword ? 'text' : 'password'}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              fullWidth
              required
              InputProps={{
                endAdornment: (
                  <IconButton
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                ),
              }}
            />
            {newPassword && (
              <Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    Password Strength
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {passwordStrength}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={passwordStrength}
                  color={
                    passwordStrength < 40 ? 'error' :
                    passwordStrength < 70 ? 'warning' : 'success'
                  }
                />
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordModalOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleResetPassword}
            disabled={!newPassword}
            color="warning"
          >
            Reset Password
          </Button>
        </DialogActions>
      </Dialog>

      {/* SSH Key Management Modal */}
      <Dialog
        open={sshModalOpen}
        onClose={() => setSshModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">SSH Keys - {selectedUser?.username}</Typography>
            <IconButton onClick={() => setSshModalOpen(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* Existing Keys */}
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Current SSH Keys ({sshKeys.length})
              </Typography>
              {sshKeys.length === 0 ? (
                <Alert severity="info">No SSH keys configured</Alert>
              ) : (
                <List>
                  {sshKeys.map((key, index) => (
                    <ListItem
                      key={index}
                      sx={{
                        border: 1,
                        borderColor: 'divider',
                        borderRadius: 1,
                        mb: 1,
                      }}
                      secondaryAction={
                        <IconButton
                          edge="end"
                          color="error"
                          onClick={() => handleDeleteSshKey(index)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={
                          <Typography
                            variant="body2"
                            sx={{ fontFamily: 'monospace', fontSize: '0.75rem', wordBreak: 'break-all' }}
                          >
                            {key.substring(0, 60)}...
                          </Typography>
                        }
                        secondary={`Key ${index + 1}`}
                      />
                    </ListItem>
                  ))}
                </List>
              )}
            </Box>

            <Divider />

            {/* Add New Key */}
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Add New SSH Key
              </Typography>
              <TextField
                label="SSH Public Key"
                value={newSshKey}
                onChange={(e) => setNewSshKey(e.target.value)}
                fullWidth
                multiline
                rows={4}
                placeholder="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..."
                helperText="Paste the public key (starts with ssh-rsa, ssh-ed25519, etc.)"
              />
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddSshKey}
                disabled={!newSshKey.trim()}
                sx={{ mt: 2 }}
              >
                Add SSH Key
              </Button>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSshModalOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog
        open={deleteModalOpen}
        onClose={() => setDeleteModalOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DeleteIcon color="error" />
            <Typography variant="h6">Delete User</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              This action cannot be undone!
            </Typography>
          </Alert>
          <Typography variant="body1">
            Are you sure you want to delete the user{' '}
            <strong>{selectedUser?.username}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will remove the user account and may delete their home directory and files.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteModalOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteUser}
            startIcon={<DeleteIcon />}
          >
            Delete User
          </Button>
        </DialogActions>
      </Dialog>

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
};

export default LocalUsers;
