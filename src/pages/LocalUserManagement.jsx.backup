import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Checkbox,
  FormControlLabel,
  InputAdornment,
  LinearProgress,
  Alert,
  Grid,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  OutlinedInput,
  CircularProgress,
} from '@mui/material';
import {
  User,
  Shield,
  Key,
  Terminal,
  Trash2,
  Plus,
  Eye,
  EyeOff,
  Search,
  Copy,
  Check,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { alpha } from '@mui/material/styles';
import { useToast } from '../components/Toast';

const LocalUserManagement = () => {
  // Toast notifications
  const toast = useToast();

  // State management
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [availableGroups, setAvailableGroups] = useState([]);
  const [stats, setStats] = useState({
    totalUsers: 0,
    sudoUsers: 0,
    activeSessions: 0,
    sshKeysConfigured: 0,
  });

  // Create user form state
  const [newUser, setNewUser] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    shell: '/bin/bash',
    groups: [],
    grantSudo: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [validationErrors, setValidationErrors] = useState({});

  // User detail state
  const [activeTab, setActiveTab] = useState(0);
  const [userSSHKeys, setUserSSHKeys] = useState([]);
  const [newSSHKey, setNewSSHKey] = useState('');
  const [copiedKey, setCopiedKey] = useState(null);

  // Confirmation dialogs
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [sudoConfirm, setSudoConfirm] = useState(null);

  // Fetch users on mount
  useEffect(() => {
    fetchUsers();
    fetchGroups();
  }, []);

  // Calculate password strength
  useEffect(() => {
    if (newUser.password) {
      const strength = calculatePasswordStrength(newUser.password);
      setPasswordStrength(strength);
    } else {
      setPasswordStrength(0);
    }
  }, [newUser.password]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/admin/system/local-users');
      const data = await response.json();

      if (data.success) {
        setUsers(data.users || []);

        // Calculate stats
        const totalUsers = data.users.filter(u => u.uid >= 1000).length;
        const sudoUsers = data.users.filter(u => u.groups?.includes('sudo')).length;
        const sshKeysConfigured = data.users.filter(u => u.ssh_keys_count > 0).length;

        setStats({
          totalUsers,
          sudoUsers,
          activeSessions: data.active_sessions || 0,
          sshKeysConfigured,
        });
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGroups = async () => {
    try {
      const response = await fetch('/api/v1/admin/system/local-users/groups');
      const data = await response.json();
      if (data.success) {
        setAvailableGroups(data.groups || []);
      }
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    }
  };

  const fetchUserSSHKeys = async (username) => {
    try {
      const response = await fetch(`/api/v1/admin/system/local-users/${username}/ssh-keys`);
      const data = await response.json();
      if (data.success) {
        setUserSSHKeys(data.keys || []);
      }
    } catch (error) {
      console.error('Failed to fetch SSH keys:', error);
    }
  };

  const calculatePasswordStrength = (password) => {
    let strength = 0;

    if (password.length >= 12) strength += 25;
    if (password.length >= 16) strength += 15;
    if (/[a-z]/.test(password)) strength += 15;
    if (/[A-Z]/.test(password)) strength += 15;
    if (/[0-9]/.test(password)) strength += 15;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 15;

    return Math.min(strength, 100);
  };

  const getPasswordStrengthLabel = (strength) => {
    if (strength < 40) return { label: 'Weak', color: 'error' };
    if (strength < 70) return { label: 'Medium', color: 'warning' };
    return { label: 'Strong', color: 'success' };
  };

  const validateUsername = (username) => {
    return /^[a-z_][a-z0-9_-]*$/.test(username);
  };

  const validatePassword = (password) => {
    const hasUppercase = /[A-Z]/.test(password);
    const hasLowercase = /[a-z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    const hasSpecial = /[^a-zA-Z0-9]/.test(password);
    const isLongEnough = password.length >= 12;

    return hasUppercase && hasLowercase && hasNumber && hasSpecial && isLongEnough;
  };

  const validateSSHKey = (key) => {
    const keyTypes = ['ssh-rsa', 'ssh-ed25519', 'ecdsa-sha2-nistp256', 'ecdsa-sha2-nistp384', 'ecdsa-sha2-nistp521'];
    return keyTypes.some(type => key.trim().startsWith(type));
  };

  const generateRandomPassword = () => {
    const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const lowercase = 'abcdefghijklmnopqrstuvwxyz';
    const numbers = '0123456789';
    const special = '!@#$%^&*()_+-=[]{}|;:,.<>?';

    const all = uppercase + lowercase + numbers + special;
    let password = '';

    // Ensure at least one of each type
    password += uppercase[Math.floor(Math.random() * uppercase.length)];
    password += lowercase[Math.floor(Math.random() * lowercase.length)];
    password += numbers[Math.floor(Math.random() * numbers.length)];
    password += special[Math.floor(Math.random() * special.length)];

    // Fill remaining characters
    for (let i = password.length; i < 16; i++) {
      password += all[Math.floor(Math.random() * all.length)];
    }

    // Shuffle password
    password = password.split('').sort(() => Math.random() - 0.5).join('');

    setNewUser({ ...newUser, password, confirmPassword: password });
  };

  const handleCreateUser = async () => {
    const errors = {};

    if (!validateUsername(newUser.username)) {
      errors.username = 'Username must be alphanumeric with hyphens/underscores only';
    }

    if (!validatePassword(newUser.password)) {
      errors.password = 'Password must be at least 12 characters with uppercase, lowercase, number, and special character';
    }

    if (newUser.password !== newUser.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setValidationErrors(errors);

    if (Object.keys(errors).length > 0) {
      return;
    }

    try {
      const response = await fetch('/api/v1/admin/system/local-users', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newUser),
      });

      const data = await response.json();

      if (data.success) {
        setCreateModalOpen(false);
        resetNewUserForm();
        fetchUsers();
      } else {
        setValidationErrors({ general: data.error || 'Failed to create user' });
      }
    } catch (error) {
      setValidationErrors({ general: 'Network error: ' + error.message });
    }
  };

  const handleDeleteUser = async (username) => {
    try {
      const response = await fetch(`/api/v1/admin/system/local-users/${username}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        setDeleteConfirm(null);
        setDetailModalOpen(false);
        fetchUsers();
      }
    } catch (error) {
      console.error('Failed to delete user:', error);
    }
  };

  const handleToggleSudo = async (username, currentHasSudo) => {
    try {
      const response = await fetch(`/api/v1/admin/system/local-users/${username}/sudo`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grant_sudo: !currentHasSudo }),
      });

      const data = await response.json();

      if (data.success) {
        setSudoConfirm(null);
        fetchUsers();
        if (selectedUser) {
          const updatedUser = { ...selectedUser };
          if (!currentHasSudo) {
            updatedUser.groups = [...(updatedUser.groups || []), 'sudo'];
          } else {
            updatedUser.groups = (updatedUser.groups || []).filter(g => g !== 'sudo');
          }
          setSelectedUser(updatedUser);
        }
      }
    } catch (error) {
      console.error('Failed to toggle sudo:', error);
    }
  };

  const handleAddSSHKey = async () => {
    if (!validateSSHKey(newSSHKey)) {
      toast.error('Invalid SSH key format. Key must start with ssh-rsa, ssh-ed25519, or ecdsa-sha2-nistp*');
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/system/local-users/${selectedUser.username}/ssh-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ key: newSSHKey }),
      });

      const data = await response.json();

      if (data.success) {
        setNewSSHKey('');
        fetchUserSSHKeys(selectedUser.username);
      }
    } catch (error) {
      console.error('Failed to add SSH key:', error);
    }
  };

  const handleDeleteSSHKey = async (keyId) => {
    try {
      const response = await fetch(`/api/v1/admin/system/local-users/${selectedUser.username}/ssh-keys/${keyId}`, {
        method: 'DELETE',
      });

      const data = await response.json();

      if (data.success) {
        toast.success('SSH key deleted successfully');
        await fetchUserSSHKeys(selectedUser.username);
      } else {
        toast.error(`Failed to delete SSH key: ${data.error || 'Unknown error'}`);
      }
    } catch (error) {
      console.error('Failed to delete SSH key:', error);
      toast.error('Failed to delete SSH key. Please try again.');
    }
  };

  const handleCopyKey = (key) => {
    navigator.clipboard.writeText(key);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const resetNewUserForm = () => {
    setNewUser({
      username: '',
      password: '',
      confirmPassword: '',
      shell: '/bin/bash',
      groups: [],
      grantSudo: false,
    });
    setValidationErrors({});
  };

  const openUserDetail = (user) => {
    setSelectedUser(user);
    setDetailModalOpen(true);
    setActiveTab(0);
    fetchUserSSHKeys(user.username);
  };

  const filteredUsers = users.filter(user => {
    if (!searchTerm) return true;
    return user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
           user.groups?.some(g => g.toLowerCase().includes(searchTerm.toLowerCase()));
  });

  const formatLastLogin = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getSSHKeyType = (key) => {
    if (key.startsWith('ssh-rsa')) return 'RSA';
    if (key.startsWith('ssh-ed25519')) return 'Ed25519';
    if (key.startsWith('ecdsa-')) return 'ECDSA';
    return 'Unknown';
  };

  const truncateSSHKey = (key) => {
    if (key.length <= 70) return key;
    return key.substring(0, 50) + '...' + key.substring(key.length - 20);
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ mb: 1, fontWeight: 600 }}>
          Local User Management
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Manage Linux system users, SSH keys, and sudo permissions
        </Typography>

        <Button
          variant="contained"
          startIcon={<Plus size={20} />}
          onClick={() => setCreateModalOpen(true)}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #5568d3 0%, #654093 100%)',
            },
          }}
        >
          Create User
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: alpha('#667eea', 0.1),
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: alpha('#667eea', 0.2),
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <User size={24} color="#667eea" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {stats.totalUsers}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Total Users
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: alpha('#f093fb', 0.1),
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: alpha('#f093fb', 0.2),
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Shield size={24} color="#f093fb" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {stats.sudoUsers}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Sudo Users
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: alpha('#4facfe', 0.1),
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: alpha('#4facfe', 0.2),
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Terminal size={24} color="#4facfe" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {stats.activeSessions}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                Active Sessions
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{
            background: alpha('#43e97b', 0.1),
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: alpha('#43e97b', 0.2),
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Key size={24} color="#43e97b" />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {stats.sshKeysConfigured}
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                SSH Keys Configured
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search Bar */}
      <Card sx={{ mb: 3, backdropFilter: 'blur(10px)' }}>
        <CardContent>
          <TextField
            fullWidth
            placeholder="Search by username or group..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <Search size={20} />
                </InputAdornment>
              ),
            }}
          />
        </CardContent>
      </Card>

      {/* User List Table */}
      <Card sx={{ backdropFilter: 'blur(10px)' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Username</TableCell>
                <TableCell>UID</TableCell>
                <TableCell>Groups</TableCell>
                <TableCell>Shell</TableCell>
                <TableCell align="center">Sudo</TableCell>
                <TableCell align="center">SSH Keys</TableCell>
                <TableCell>Last Login</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} align="center">
                    No users found
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((user) => (
                  <TableRow
                    key={user.username}
                    hover
                    onClick={() => openUserDetail(user)}
                    sx={{ cursor: 'pointer' }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <User size={16} style={{ marginRight: 8 }} />
                        {user.username}
                      </Box>
                    </TableCell>
                    <TableCell>{user.uid}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {user.groups?.slice(0, 3).map(group => (
                          <Chip key={group} label={group} size="small" />
                        ))}
                        {user.groups?.length > 3 && (
                          <Chip label={`+${user.groups.length - 3}`} size="small" />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <code style={{ fontSize: '0.875rem' }}>{user.shell}</code>
                    </TableCell>
                    <TableCell align="center">
                      {user.groups?.includes('sudo') ? (
                        <Shield size={16} color="#f093fb" />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell align="center">
                      {user.ssh_keys_count > 0 ? (
                        <Chip
                          label={user.ssh_keys_count}
                          size="small"
                          color="primary"
                          icon={<Key size={14} />}
                        />
                      ) : (
                        '-'
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatLastLogin(user.last_login)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="View Details">
                        <IconButton size="small" onClick={(e) => {
                          e.stopPropagation();
                          openUserDetail(user);
                        }}>
                          <Eye size={16} />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>

      {/* Create User Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          resetNewUserForm();
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          {validationErrors.general && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {validationErrors.general}
            </Alert>
          )}

          <TextField
            fullWidth
            label="Username"
            value={newUser.username}
            onChange={(e) => setNewUser({ ...newUser, username: e.target.value.toLowerCase() })}
            error={!!validationErrors.username}
            helperText={validationErrors.username || 'Lowercase alphanumeric with hyphens/underscores'}
            sx={{ mb: 2, mt: 1 }}
          />

          <TextField
            fullWidth
            label="Password"
            type={showPassword ? 'text' : 'password'}
            value={newUser.password}
            onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
            error={!!validationErrors.password}
            helperText={validationErrors.password}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 1 }}
          />

          <Box sx={{ mb: 2 }}>
            <LinearProgress
              variant="determinate"
              value={passwordStrength}
              color={getPasswordStrengthLabel(passwordStrength).color}
              sx={{ mb: 0.5 }}
            />
            <Typography variant="caption" color="text.secondary">
              Password Strength: {getPasswordStrengthLabel(passwordStrength).label}
            </Typography>
          </Box>

          <Button
            variant="outlined"
            size="small"
            startIcon={<RefreshCw size={16} />}
            onClick={generateRandomPassword}
            sx={{ mb: 2 }}
          >
            Generate Random Password
          </Button>

          <TextField
            fullWidth
            label="Confirm Password"
            type={showConfirmPassword ? 'text' : 'password'}
            value={newUser.confirmPassword}
            onChange={(e) => setNewUser({ ...newUser, confirmPassword: e.target.value })}
            error={!!validationErrors.confirmPassword}
            helperText={validationErrors.confirmPassword}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={() => setShowConfirmPassword(!showConfirmPassword)} edge="end">
                    {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Shell</InputLabel>
            <Select
              value={newUser.shell}
              onChange={(e) => setNewUser({ ...newUser, shell: e.target.value })}
              label="Shell"
            >
              <MenuItem value="/bin/bash">/bin/bash</MenuItem>
              <MenuItem value="/bin/zsh">/bin/zsh</MenuItem>
              <MenuItem value="/bin/sh">/bin/sh</MenuItem>
              <MenuItem value="/bin/dash">/bin/dash</MenuItem>
            </Select>
          </FormControl>

          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>Groups</InputLabel>
            <Select
              multiple
              value={newUser.groups}
              onChange={(e) => setNewUser({ ...newUser, groups: e.target.value })}
              input={<OutlinedInput label="Groups" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip key={value} label={value} size="small" />
                  ))}
                </Box>
              )}
            >
              {availableGroups.map((group) => (
                <MenuItem key={group} value={group}>
                  {group}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControlLabel
            control={
              <Checkbox
                checked={newUser.grantSudo}
                onChange={(e) => setNewUser({ ...newUser, grantSudo: e.target.checked })}
              />
            }
            label={
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Shield size={16} style={{ marginRight: 8 }} />
                Grant sudo access
              </Box>
            }
          />

          {newUser.grantSudo && (
            <Alert severity="warning" sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AlertTriangle size={16} style={{ marginRight: 8 }} />
                Granting sudo access gives this user administrative privileges
              </Box>
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setCreateModalOpen(false);
            resetNewUserForm();
          }}>
            Cancel
          </Button>
          <Button variant="contained" onClick={handleCreateUser}>
            Create User
          </Button>
        </DialogActions>
      </Dialog>

      {/* User Detail Modal */}
      <Dialog
        open={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedUser && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <User size={24} style={{ marginRight: 12 }} />
                  {selectedUser.username}
                  {selectedUser.groups?.includes('sudo') && (
                    <Chip
                      icon={<Shield size={14} />}
                      label="Sudo"
                      size="small"
                      color="secondary"
                      sx={{ ml: 2 }}
                    />
                  )}
                </Box>
                <IconButton
                  onClick={() => setDeleteConfirm(selectedUser.username)}
                  color="error"
                  disabled={selectedUser.username === 'muut'} // Protect current user
                >
                  <Trash2 size={20} />
                </IconButton>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
                <Tab label="Overview" />
                <Tab label="Groups" />
                <Tab label="SSH Keys" />
                <Tab label="Sudo" />
              </Tabs>

              <Box sx={{ mt: 3 }}>
                {/* Overview Tab */}
                {activeTab === 0 && (
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Username</Typography>
                      <Typography variant="body1">{selectedUser.username}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">UID</Typography>
                      <Typography variant="body1">{selectedUser.uid}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">GID</Typography>
                      <Typography variant="body1">{selectedUser.gid}</Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="text.secondary">Shell</Typography>
                      <Typography variant="body1">
                        <code>{selectedUser.shell}</code>
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Home Directory</Typography>
                      <Typography variant="body1">
                        <code>{selectedUser.home}</code>
                      </Typography>
                    </Grid>
                    <Grid item xs={12}>
                      <Typography variant="body2" color="text.secondary">Last Login</Typography>
                      <Typography variant="body1">{formatLastLogin(selectedUser.last_login)}</Typography>
                    </Grid>
                  </Grid>
                )}

                {/* Groups Tab */}
                {activeTab === 1 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Member of {selectedUser.groups?.length || 0} groups
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {selectedUser.groups?.map(group => (
                        <Chip
                          key={group}
                          label={group}
                          onDelete={group !== 'sudo' ? () => {} : undefined}
                          color={group === 'sudo' ? 'secondary' : 'default'}
                        />
                      ))}
                    </Box>
                  </Box>
                )}

                {/* SSH Keys Tab */}
                {activeTab === 2 && (
                  <Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {userSSHKeys.length} SSH key(s) configured
                    </Typography>

                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      placeholder="Paste SSH public key here..."
                      value={newSSHKey}
                      onChange={(e) => setNewSSHKey(e.target.value)}
                      sx={{ mb: 2 }}
                    />
                    <Button
                      variant="contained"
                      startIcon={<Plus size={16} />}
                      onClick={handleAddSSHKey}
                      disabled={!newSSHKey.trim()}
                      sx={{ mb: 3 }}
                    >
                      Add SSH Key
                    </Button>

                    <List>
                      {userSSHKeys.map((key, index) => {
                        // Generate a stable fingerprint from the key for use as unique identifier
                        // Use the key itself as the ID (will be URL-encoded in the API call)
                        const keyId = typeof key === 'object' && key.id
                          ? key.id
                          : typeof key === 'object' && key.fingerprint
                            ? key.fingerprint
                            : index;

                        return (
                          <React.Fragment key={keyId}>
                            <ListItem>
                              <ListItemText
                                primary={
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                    <Chip label={getSSHKeyType(typeof key === 'string' ? key : key.key || key)} size="small" />
                                    <code style={{ fontSize: '0.75rem' }}>
                                      {truncateSSHKey(typeof key === 'string' ? key : key.key || key)}
                                    </code>
                                  </Box>
                                }
                              />
                              <ListItemSecondaryAction>
                                <Tooltip title={copiedKey === (typeof key === 'string' ? key : key.key) ? 'Copied!' : 'Copy'}>
                                  <IconButton
                                    onClick={() => handleCopyKey(typeof key === 'string' ? key : key.key || key)}
                                    size="small"
                                    sx={{ mr: 1 }}
                                  >
                                    {copiedKey === (typeof key === 'string' ? key : key.key) ? <Check size={16} /> : <Copy size={16} />}
                                  </IconButton>
                                </Tooltip>
                                <IconButton
                                  onClick={() => handleDeleteSSHKey(keyId)}
                                  size="small"
                                  color="error"
                                >
                                  <Trash2 size={16} />
                                </IconButton>
                              </ListItemSecondaryAction>
                            </ListItem>
                            {index < userSSHKeys.length - 1 && <Divider />}
                          </React.Fragment>
                        );
                      })}
                    </List>

                    {userSSHKeys.length === 0 && (
                      <Alert severity="info">
                        No SSH keys configured for this user
                      </Alert>
                    )}
                  </Box>
                )}

                {/* Sudo Tab */}
                {activeTab === 3 && (
                  <Box>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={selectedUser.groups?.includes('sudo')}
                          onChange={(e) => {
                            if (e.target.checked || selectedUser.groups?.includes('sudo')) {
                              setSudoConfirm({
                                username: selectedUser.username,
                                currentHasSudo: selectedUser.groups?.includes('sudo'),
                              });
                            }
                          }}
                        />
                      }
                      label={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Shield size={16} style={{ marginRight: 8 }} />
                          Grant sudo access
                        </Box>
                      }
                    />

                    {selectedUser.groups?.includes('sudo') ? (
                      <Alert severity="warning" sx={{ mt: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <AlertTriangle size={16} style={{ marginRight: 8 }} />
                          This user has administrative privileges via sudo
                        </Box>
                      </Alert>
                    ) : (
                      <Alert severity="info" sx={{ mt: 2 }}>
                        This user does not have sudo access
                      </Alert>
                    )}
                  </Box>
                )}
              </Box>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailModalOpen(false)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
      >
        <DialogTitle>Confirm Delete User</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AlertTriangle size={16} style={{ marginRight: 8 }} />
              This action cannot be undone
            </Box>
          </Alert>
          <Typography>
            Are you sure you want to delete user <strong>{deleteConfirm}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            This will remove the user account and all associated data.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirm(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => handleDeleteUser(deleteConfirm)}
          >
            Delete User
          </Button>
        </DialogActions>
      </Dialog>

      {/* Sudo Toggle Confirmation Dialog */}
      <Dialog
        open={!!sudoConfirm}
        onClose={() => setSudoConfirm(null)}
      >
        <DialogTitle>
          {sudoConfirm?.currentHasSudo ? 'Remove Sudo Access' : 'Grant Sudo Access'}
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AlertTriangle size={16} style={{ marginRight: 8 }} />
              {sudoConfirm?.currentHasSudo
                ? 'Removing sudo access will revoke administrative privileges'
                : 'Granting sudo access gives administrative privileges'}
            </Box>
          </Alert>
          <Typography>
            Are you sure you want to {sudoConfirm?.currentHasSudo ? 'remove' : 'grant'} sudo access for{' '}
            <strong>{sudoConfirm?.username}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSudoConfirm(null)}>Cancel</Button>
          <Button
            variant="contained"
            color={sudoConfirm?.currentHasSudo ? 'error' : 'primary'}
            onClick={() => handleToggleSudo(sudoConfirm.username, sudoConfirm.currentHasSudo)}
          >
            {sudoConfirm?.currentHasSudo ? 'Remove Access' : 'Grant Access'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LocalUserManagement;
