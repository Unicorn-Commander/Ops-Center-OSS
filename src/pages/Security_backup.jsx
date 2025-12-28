import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheckIcon,
  ArrowPathIcon,
  UserGroupIcon,
  KeyIcon,
  LockClosedIcon,
  LockOpenIcon,
  EyeIcon,
  EyeSlashIcon,
  TrashIcon,
  PlusIcon,
  PencilIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ClockIcon,
  ComputerDesktopIcon,
  DevicePhoneMobileIcon,
  GlobeAltIcon,
  UserIcon,
  CogIcon,
  BellIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
};

export default function Security() {
  const [activeTab, setActiveTab] = useState('users');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showAddApiKeyModal, setShowAddApiKeyModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [loginAttempts, setLoginAttempts] = useState([]);
  const [securitySettings, setSecuritySettings] = useState({});

  // Mock data for demonstration
  const [mockUsers] = useState([
    {
      id: 1,
      username: 'admin',
      email: 'admin@your-domain.com',
      role: 'Administrator',
      status: 'active',
      lastLogin: '2025-01-28T10:30:00Z',
      lastLoginIp: '192.168.1.100',
      createdAt: '2025-01-20T08:00:00Z',
      permissions: ['read', 'write', 'admin', 'delete'],
      twoFactorEnabled: true,
      loginAttempts: 0
    },
    {
      id: 2,
      username: 'operator',
      email: 'operator@your-domain.com',
      role: 'Operator',
      status: 'active',
      lastLogin: '2025-01-28T09:15:00Z',
      lastLoginIp: '192.168.1.101',
      createdAt: '2025-01-22T10:30:00Z',
      permissions: ['read', 'write'],
      twoFactorEnabled: false,
      loginAttempts: 0
    },
    {
      id: 3,
      username: 'viewer',
      email: 'viewer@your-domain.com',
      role: 'Viewer',
      status: 'active',
      lastLogin: '2025-01-27T16:45:00Z',
      lastLoginIp: '192.168.1.102',
      createdAt: '2025-01-25T14:20:00Z',
      permissions: ['read'],
      twoFactorEnabled: false,
      loginAttempts: 1
    },
    {
      id: 4,
      username: 'suspended_user',
      email: 'suspended@example.com',
      role: 'Operator',
      status: 'suspended',
      lastLogin: '2025-01-26T12:00:00Z',
      lastLoginIp: '192.168.1.103',
      createdAt: '2025-01-23T09:00:00Z',
      permissions: ['read'],
      twoFactorEnabled: false,
      loginAttempts: 5
    }
  ]);

  const [mockApiKeys] = useState([
    {
      id: 1,
      name: 'Production API Key',
      keyPreview: 'uk_prod_***...***abc123',
      permissions: ['models:read', 'models:write', 'services:read'],
      createdAt: '2025-01-20T08:00:00Z',
      lastUsed: '2025-01-28T10:30:00Z',
      usageCount: 1502,
      status: 'active',
      expiresAt: '2025-07-28T00:00:00Z'
    },
    {
      id: 2,
      name: 'Development API Key',
      keyPreview: 'uk_dev_***...***def456',
      permissions: ['models:read', 'services:read'],
      createdAt: '2025-01-22T10:30:00Z',
      lastUsed: '2025-01-28T08:15:00Z',
      usageCount: 847,
      status: 'active',
      expiresAt: '2025-04-28T00:00:00Z'
    },
    {
      id: 3,
      name: 'Analytics Key',
      keyPreview: 'uk_analytics_***...***ghi789',
      permissions: ['metrics:read', 'logs:read'],
      createdAt: '2025-01-25T14:20:00Z',
      lastUsed: '2025-01-27T22:00:00Z',
      usageCount: 234,
      status: 'active',
      expiresAt: '2025-12-31T00:00:00Z'
    },
    {
      id: 4,
      name: 'Legacy Integration',
      keyPreview: 'uk_legacy_***...***jkl012',
      permissions: ['models:read'],
      createdAt: '2025-01-15T12:00:00Z',
      lastUsed: '2025-01-20T15:30:00Z',
      usageCount: 45,
      status: 'expired',
      expiresAt: '2025-01-25T00:00:00Z'
    }
  ]);

  const [mockLoginAttempts] = useState([
    {
      id: 1,
      username: 'admin',
      ip: '192.168.1.100',
      timestamp: '2025-01-28T10:30:00Z',
      success: true,
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      location: 'Local Network'
    },
    {
      id: 2,
      username: 'operator',
      ip: '192.168.1.101',
      timestamp: '2025-01-28T09:15:00Z',
      success: true,
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
      location: 'Local Network'
    },
    {
      id: 3,
      username: 'admin',
      ip: '203.0.113.45',
      timestamp: '2025-01-28T08:45:00Z',
      success: false,
      userAgent: 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
      location: 'External IP (Blocked)'
    },
    {
      id: 4,
      username: 'unknown_user',
      ip: '198.51.100.23',
      timestamp: '2025-01-28T07:30:00Z',
      success: false,
      userAgent: 'curl/7.68.0',
      location: 'External IP (Blocked)'
    },
    {
      id: 5,
      username: 'suspended_user',
      ip: '192.168.1.103',
      timestamp: '2025-01-28T06:15:00Z',
      success: false,
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
      location: 'Local Network (Account Suspended)'
    }
  ]);

  const [mockSecuritySettings] = useState({
    sessionTimeout: 3600, // 1 hour
    maxLoginAttempts: 5,
    lockoutDuration: 900, // 15 minutes
    passwordMinLength: 8,
    passwordRequireSpecialChars: true,
    passwordRequireNumbers: true,
    passwordRequireUppercase: true,
    twoFactorRequired: false,
    allowExternalConnections: false,
    apiRateLimit: 1000, // requests per hour
    auditLogging: true,
    securityNotifications: true,
    autoLogoutEnabled: true
  });

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    setLoading(true);
    try {
      // TODO: Replace with actual API calls
      // const [usersRes, apiKeysRes, attemptsRes, settingsRes] = await Promise.all([
      //   fetch('/api/v1/security/users'),
      //   fetch('/api/v1/security/api-keys'),
      //   fetch('/api/v1/security/login-attempts'),
      //   fetch('/api/v1/security/settings')
      // ]);
      
      // For now, use mock data
      await new Promise(resolve => setTimeout(resolve, 500));
      setUsers(mockUsers);
      setApiKeys(mockApiKeys);
      setLoginAttempts(mockLoginAttempts);
      setSecuritySettings(mockSecuritySettings);
    } catch (error) {
      console.error('Failed to load security data:', error);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadSecurityData();
    setRefreshing(false);
  };

  const getRoleColor = (role) => {
    const colors = {
      'Administrator': 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200',
      'Operator': 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200',
      'Viewer': 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200'
    };
    return colors[role] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
  };

  const getStatusColor = (status) => {
    const colors = {
      'active': 'text-green-600 dark:text-green-400',
      'suspended': 'text-red-600 dark:text-red-400',
      'expired': 'text-yellow-600 dark:text-yellow-400'
    };
    return colors[status] || 'text-gray-600 dark:text-gray-400';
  };

  const getStatusIcon = (status) => {
    const icons = {
      'active': CheckCircleIcon,
      'suspended': ExclamationTriangleIcon,
      'expired': ClockIcon
    };
    return icons[status] || InformationCircleIcon;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const handleUserAction = (userId, action) => {
    // TODO: Implement user management actions
    console.log(`User ${userId} action: ${action}`);
    alert(`User action "${action}" will be implemented in the backend`);
  };

  const handleApiKeyAction = (keyId, action) => {
    // TODO: Implement API key management actions
    console.log(`API Key ${keyId} action: ${action}`);
    alert(`API key action "${action}" will be implemented in the backend`);
  };

  const getDeviceIcon = (userAgent) => {
    if (userAgent.includes('Mobile') || userAgent.includes('Android') || userAgent.includes('iPhone')) {
      return DevicePhoneMobileIcon;
    }
    return ComputerDesktopIcon;
  };

  const getSecurityStats = () => {
    return {
      totalUsers: users.length,
      activeUsers: users.filter(u => u.status === 'active').length,
      suspendedUsers: users.filter(u => u.status === 'suspended').length,
      totalApiKeys: apiKeys.length,
      activeApiKeys: apiKeys.filter(k => k.status === 'active').length,
      expiredApiKeys: apiKeys.filter(k => k.status === 'expired').length,
      failedLogins: loginAttempts.filter(a => !a.success).length,
      successfulLogins: loginAttempts.filter(a => a.success).length
    };
  };

  const stats = getSecurityStats();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <motion.div 
      className="space-y-6"
      variants={containerVariants}
      initial="hidden" 
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Security & Access Management
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Manage users, API keys, authentication, and security settings
          </p>
        </div>
        
        <button
          onClick={refreshData}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Active Users</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.activeUsers}</p>
            </div>
            <UserIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">API Keys</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.activeApiKeys}</p>
            </div>
            <KeyIcon className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Failed Logins</p>
              <p className="text-2xl font-bold text-red-600">{stats.failedLogins}</p>
            </div>
            <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Success Logins</p>
              <p className="text-2xl font-bold text-green-600">{stats.successfulLogins}</p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div variants={itemVariants} className="border-b dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'users', name: 'Users', icon: UserGroupIcon },
            { id: 'api-keys', name: 'API Keys', icon: KeyIcon },
            { id: 'access-logs', name: 'Access Logs', icon: DocumentTextIcon },
            { id: 'settings', name: 'Security Settings', icon: CogIcon }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <tab.icon className="h-5 w-5" />
                {tab.name}
              </div>
            </button>
          ))}
        </nav>
      </motion.div>

      {/* Users Tab */}
      {activeTab === 'users' && (
        <motion.div variants={itemVariants} className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">User Management</h2>
            <button
              onClick={() => setShowAddUserModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <PlusIcon className="h-5 w-5" />
              Add User
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Role
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Last Login
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    2FA
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {users.map((user) => {
                  const StatusIcon = getStatusIcon(user.status);
                  return (
                    <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="flex-shrink-0 h-10 w-10">
                            <div className="h-10 w-10 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
                              <UserIcon className="h-6 w-6 text-gray-500 dark:text-gray-400" />
                            </div>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {user.username}
                            </div>
                            <div className="text-sm text-gray-500 dark:text-gray-400">
                              {user.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                          {user.role}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <StatusIcon className={`h-5 w-5 mr-2 ${getStatusColor(user.status)}`} />
                          <span className={`text-sm font-medium capitalize ${getStatusColor(user.status)}`}>
                            {user.status}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        <div>{formatDate(user.lastLogin)}</div>
                        <div className="text-xs">{user.lastLoginIp}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {user.twoFactorEnabled ? (
                          <CheckCircleIcon className="h-5 w-5 text-green-500" />
                        ) : (
                          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex justify-end gap-2">
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowEditModal(true);
                            }}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleUserAction(user.id, user.status === 'active' ? 'suspend' : 'activate')}
                            className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300"
                          >
                            {user.status === 'active' ? <LockClosedIcon className="h-4 w-4" /> : <LockOpenIcon className="h-4 w-4" />}
                          </button>
                          <button
                            onClick={() => handleUserAction(user.id, 'delete')}
                            className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* API Keys Tab */}
      {activeTab === 'api-keys' && (
        <motion.div variants={itemVariants} className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">API Key Management</h2>
            <button
              onClick={() => setShowAddApiKeyModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              <PlusIcon className="h-5 w-5" />
              Generate API Key
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {apiKeys.map((apiKey) => {
              const StatusIcon = getStatusIcon(apiKey.status);
              return (
                <div key={apiKey.id} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                        {apiKey.name}
                      </h3>
                      <div className="flex items-center mt-1">
                        <StatusIcon className={`h-4 w-4 mr-1 ${getStatusColor(apiKey.status)}`} />
                        <span className={`text-sm font-medium capitalize ${getStatusColor(apiKey.status)}`}>
                          {apiKey.status}
                        </span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleApiKeyAction(apiKey.id, 'revoke')}
                        className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <label className="text-sm font-medium text-gray-500 dark:text-gray-400">API Key</label>
                      <div className="flex items-center gap-2 mt-1">
                        <code className="bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded text-sm font-mono">
                          {apiKey.keyPreview}
                        </code>
                        <button className="text-blue-600 hover:text-blue-800 dark:text-blue-400">
                          <EyeIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-500 dark:text-gray-400">Permissions</label>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {apiKey.permissions.map((permission, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200"
                          >
                            {permission}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <label className="font-medium text-gray-500 dark:text-gray-400">Usage</label>
                        <p className="text-gray-900 dark:text-white">{apiKey.usageCount.toLocaleString()} requests</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-500 dark:text-gray-400">Last Used</label>
                        <p className="text-gray-900 dark:text-white">{formatDate(apiKey.lastUsed)}</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-500 dark:text-gray-400">Created</label>
                        <p className="text-gray-900 dark:text-white">{formatDate(apiKey.createdAt)}</p>
                      </div>
                      <div>
                        <label className="font-medium text-gray-500 dark:text-gray-400">Expires</label>
                        <p className="text-gray-900 dark:text-white">{formatDate(apiKey.expiresAt)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Access Logs Tab */}
      {activeTab === 'access-logs' && (
        <motion.div variants={itemVariants} className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Access Logs</h2>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    User
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Device
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Location
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {loginAttempts.map((attempt) => {
                  const DeviceIcon = getDeviceIcon(attempt.userAgent);
                  return (
                    <tr key={attempt.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {attempt.username}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900 dark:text-white font-mono">
                          {attempt.ip}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {formatDate(attempt.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          {attempt.success ? (
                            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
                          ) : (
                            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
                          )}
                          <span className={`text-sm font-medium ${
                            attempt.success ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                          }`}>
                            {attempt.success ? 'Success' : 'Failed'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <DeviceIcon className="h-5 w-5 text-gray-500" />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {attempt.location}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Security Settings Tab */}
      {activeTab === 'settings' && (
        <motion.div variants={itemVariants} className="space-y-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Security Settings</h2>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Authentication Settings */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <LockClosedIcon className="h-5 w-5" />
                Authentication
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Session Timeout (minutes)
                  </label>
                  <input
                    type="number"
                    value={securitySettings.sessionTimeout / 60}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Max Login Attempts
                  </label>
                  <input
                    type="number"
                    value={securitySettings.maxLoginAttempts}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="twoFactorRequired"
                    checked={securitySettings.twoFactorRequired}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="twoFactorRequired" className="ml-2 block text-sm text-gray-900 dark:text-white">
                    Require 2FA for all users
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="autoLogout"
                    checked={securitySettings.autoLogoutEnabled}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="autoLogout" className="ml-2 block text-sm text-gray-900 dark:text-white">
                    Enable automatic logout
                  </label>
                </div>
              </div>
            </div>

            {/* Password Policy */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <KeyIcon className="h-5 w-5" />
                Password Policy
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Minimum Length
                  </label>
                  <input
                    type="number"
                    value={securitySettings.passwordMinLength}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="requireUppercase"
                      checked={securitySettings.passwordRequireUppercase}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="requireUppercase" className="ml-2 block text-sm text-gray-900 dark:text-white">
                      Require uppercase letters
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="requireNumbers"
                      checked={securitySettings.passwordRequireNumbers}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="requireNumbers" className="ml-2 block text-sm text-gray-900 dark:text-white">
                      Require numbers
                    </label>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="requireSpecialChars"
                      checked={securitySettings.passwordRequireSpecialChars}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="requireSpecialChars" className="ml-2 block text-sm text-gray-900 dark:text-white">
                      Require special characters
                    </label>
                  </div>
                </div>
              </div>
            </div>

            {/* Network Security */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <GlobeAltIcon className="h-5 w-5" />
                Network Security
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    API Rate Limit (requests/hour)
                  </label>
                  <input
                    type="number"
                    value={securitySettings.apiRateLimit}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="allowExternal"
                    checked={securitySettings.allowExternalConnections}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="allowExternal" className="ml-2 block text-sm text-gray-900 dark:text-white">
                    Allow external connections
                  </label>
                </div>
              </div>
            </div>

            {/* Audit & Monitoring */}
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <BellIcon className="h-5 w-5" />
                Audit & Monitoring
              </h3>
              <div className="space-y-4">
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="auditLogging"
                    checked={securitySettings.auditLogging}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="auditLogging" className="ml-2 block text-sm text-gray-900 dark:text-white">
                    Enable audit logging
                  </label>
                </div>
                <div className="flex items-center">
                  <input
                    type="checkbox"
                    id="securityNotifications"
                    checked={securitySettings.securityNotifications}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <label htmlFor="securityNotifications" className="ml-2 block text-sm text-gray-900 dark:text-white">
                    Enable security notifications
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <button
              onClick={() => alert('Security settings will be saved via API')}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save Security Settings
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}