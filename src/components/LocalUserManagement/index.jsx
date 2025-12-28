import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';
import { Plus } from 'lucide-react';
import { useToast } from '../Toast';

// Import components
import StatisticsCards from './Shared/StatisticsCards';
import SearchBar from './Shared/SearchBar';
import UserTable from './UserTable/UserTable';
import CreateUserModal from './CreateUser/CreateUserModal';
import UserDetailModal from './UserDetail/UserDetailModal';
import DeleteUserDialog from './Dialogs/DeleteUserDialog';
import SudoToggleDialog from './Dialogs/SudoToggleDialog';

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

  // CRITICAL SECURITY FIX: Use key.id NOT array index
  // This was fixed in Sprint 2 - DO NOT CHANGE
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
      <StatisticsCards stats={stats} />

      {/* Search Bar */}
      <SearchBar searchTerm={searchTerm} setSearchTerm={setSearchTerm} />

      {/* User List Table */}
      <UserTable
        users={filteredUsers}
        loading={loading}
        formatLastLogin={formatLastLogin}
        onViewDetails={openUserDetail}
      />

      {/* Create User Modal */}
      <CreateUserModal
        open={createModalOpen}
        onClose={() => {
          setCreateModalOpen(false);
          resetNewUserForm();
        }}
        newUser={newUser}
        setNewUser={setNewUser}
        validationErrors={validationErrors}
        availableGroups={availableGroups}
        showPassword={showPassword}
        setShowPassword={setShowPassword}
        showConfirmPassword={showConfirmPassword}
        setShowConfirmPassword={setShowConfirmPassword}
        passwordStrength={passwordStrength}
        onGeneratePassword={generateRandomPassword}
        onCreate={handleCreateUser}
      />

      {/* User Detail Modal */}
      <UserDetailModal
        open={detailModalOpen}
        onClose={() => setDetailModalOpen(false)}
        user={selectedUser}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        sshKeys={userSSHKeys}
        newSSHKey={newSSHKey}
        setNewSSHKey={setNewSSHKey}
        copiedKey={copiedKey}
        onAddSSHKey={handleAddSSHKey}
        onCopyKey={handleCopyKey}
        onDeleteSSHKey={handleDeleteSSHKey}
        onSudoToggle={setSudoConfirm}
        onDeleteUser={setDeleteConfirm}
      />

      {/* Delete Confirmation Dialog */}
      <DeleteUserDialog
        open={!!deleteConfirm}
        username={deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDeleteUser}
      />

      {/* Sudo Toggle Confirmation Dialog */}
      <SudoToggleDialog
        open={!!sudoConfirm}
        sudoConfirm={sudoConfirm}
        onClose={() => setSudoConfirm(null)}
        onConfirm={handleToggleSudo}
      />
    </Box>
  );
};

export default LocalUserManagement;
