import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import {
  ShieldCheckIcon,
  ArrowPathIcon,
  UserGroupIcon,
  KeyIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ClockIcon,
  ComputerDesktopIcon,
  UserIcon,
  DocumentTextIcon,
  ShieldExclamationIcon,
  CommandLineIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 10, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 10
    }
  }
};

export default function Security() {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Audit logs state
  const [auditLogs, setAuditLogs] = useState([]);

  // Application Security State (existing functionality)
  const [users, setUsers] = useState([]);
  const [apiKeys, setApiKeys] = useState([]);
  const [sessions, setSessions] = useState([]);

  useEffect(() => {
    if (activeTab === 'overview') {
      loadAuditLogs();
    } else if (activeTab === 'users') {
      loadUsers();
    } else if (activeTab === 'apikeys') {
      loadApiKeys();
    } else if (activeTab === 'sessions') {
      loadSessions();
    }
  }, [activeTab]);

  // Audit Logs
  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/audit/logs?limit=50');
      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data.logs || []);
      }
    } catch (err) {
      console.error('Failed to load audit logs:', err);
      setError('Failed to load audit logs');
    } finally {
      setLoading(false);
    }
  };

  // Application Security Functions (existing)
  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/users');
      if (response.ok) {
        const data = await response.json();
        setUsers(data.users || []);
      }
    } catch (err) {
      setError('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadApiKeys = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/api-keys');
      if (response.ok) {
        const data = await response.json();
        setApiKeys(data.api_keys || []);
      }
    } catch (err) {
      setError('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  const loadSessions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (err) {
      setError('Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    if (activeTab === 'overview') {
      await loadAuditLogs();
    } else if (activeTab === 'users') {
      await loadUsers();
    } else if (activeTab === 'apikeys') {
      await loadApiKeys();
    } else if (activeTab === 'sessions') {
      await loadSessions();
    }
    setRefreshing(false);
  };

  const openKeycloakSettings = () => {
    window.open('https://auth.unicorncommander.ai/if/user/', '_blank');
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getAuditEventIcon = (eventType) => {
    switch (eventType) {
      case 'login':
        return <UserIcon className="h-5 w-5 text-green-500" />;
      case 'logout':
        return <UserIcon className="h-5 w-5 text-gray-500" />;
      case 'password_change':
        return <KeyIcon className="h-5 w-5 text-blue-500" />;
      case 'ssh_key_added':
      case 'ssh_key_removed':
        return <CommandLineIcon className="h-5 w-5 text-purple-500" />;
      case 'firewall_change':
        return <FireIcon className="h-5 w-5 text-orange-500" />;
      case 'failed_login':
        return <ShieldExclamationIcon className="h-5 w-5 text-red-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className={`text-4xl font-bold ${theme.text.primary} tracking-tight flex items-center gap-3`}>
            <ShieldCheckIcon className="h-10 w-10 text-green-500" />
            Security Center
          </h1>
          <p className={`${theme.text.secondary} mt-2`}>
            Security Overview & Access Management
          </p>
        </div>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={refreshData}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </motion.button>
      </motion.div>

      {/* Error/Success Messages */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`
              p-4 rounded-2xl
              bg-gradient-to-r from-red-500/10 to-rose-500/10
              border border-red-500/20 backdrop-blur-xl
            `}
          >
            <div className="flex items-center gap-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
              <p className="text-red-600 dark:text-red-400">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-600 hover:text-red-800"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </motion.div>
        )}

        {success && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`
              p-4 rounded-2xl
              bg-gradient-to-r from-green-500/10 to-emerald-500/10
              border border-green-500/20 backdrop-blur-xl
            `}
          >
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-5 w-5 text-green-500" />
              <p className="text-green-600 dark:text-green-400">{success}</p>
              <button
                onClick={() => setSuccess(null)}
                className="ml-auto text-green-600 hover:text-green-800"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Warning Banner */}
      <motion.div
        variants={itemVariants}
        className={`
          p-4 rounded-2xl
          bg-gradient-to-r from-blue-500/10 to-cyan-500/10
          border border-blue-500/20 backdrop-blur-xl
        `}
      >
        <div className="flex items-start gap-3">
          <InformationCircleIcon className="h-6 w-6 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-blue-400 font-semibold mb-1">Security Management via Keycloak</h3>
            <p className={`${theme.text.secondary} text-sm mb-3`}>
              For account security settings including password changes, two-factor authentication, and SSH keys, please use the Keycloak admin console.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={openKeycloakSettings}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm flex items-center gap-2"
            >
              <ShieldCheckIcon className="h-4 w-4" />
              Open Keycloak Admin Console
            </motion.button>
          </div>
        </div>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div
        variants={itemVariants}
        className={`
          p-2 rounded-2xl
          bg-gradient-to-br from-gray-800/40 to-gray-900/40
          border border-gray-700/50 backdrop-blur-xl
        `}
      >
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('overview')}
            className={`
              flex-1 py-3 px-4 rounded-xl font-medium text-sm transition-all
              ${activeTab === 'overview'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg'
                : `${theme.text.secondary} hover:bg-gray-700/50`
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <DocumentTextIcon className="h-5 w-5" />
              Audit Log
            </div>
          </button>

          <button
            onClick={() => setActiveTab('users')}
            className={`
              flex-1 py-3 px-4 rounded-xl font-medium text-sm transition-all
              ${activeTab === 'users'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg'
                : `${theme.text.secondary} hover:bg-gray-700/50`
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <UserGroupIcon className="h-5 w-5" />
              Users
            </div>
          </button>

          <button
            onClick={() => setActiveTab('apikeys')}
            className={`
              flex-1 py-3 px-4 rounded-xl font-medium text-sm transition-all
              ${activeTab === 'apikeys'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg'
                : `${theme.text.secondary} hover:bg-gray-700/50`
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <KeyIcon className="h-5 w-5" />
              API Keys
            </div>
          </button>

          <button
            onClick={() => setActiveTab('sessions')}
            className={`
              flex-1 py-3 px-4 rounded-xl font-medium text-sm transition-all
              ${activeTab === 'sessions'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-lg'
                : `${theme.text.secondary} hover:bg-gray-700/50`
              }
            `}
          >
            <div className="flex items-center justify-center gap-2">
              <ComputerDesktopIcon className="h-5 w-5" />
              Sessions
            </div>
          </button>
        </div>
      </motion.div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <motion.div
          variants={itemVariants}
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <div className="flex items-center gap-3 mb-6">
            <DocumentTextIcon className="h-6 w-6 text-cyan-500" />
            <h2 className={`text-xl font-bold ${theme.text.primary}`}>
              Security Audit Log
            </h2>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <ArrowPathIcon className="h-8 w-8 animate-spin mx-auto text-blue-500 mb-4" />
              <p className={theme.text.secondary}>Loading audit logs...</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[600px] overflow-y-auto">
              {auditLogs.length === 0 ? (
                <div className="text-center py-12">
                  <InformationCircleIcon className="h-12 w-12 mx-auto text-gray-500 mb-4" />
                  <p className={`${theme.text.secondary} text-sm`}>
                    No audit logs available
                  </p>
                  <p className={`${theme.text.secondary} text-xs mt-2`}>
                    Security events will appear here when they occur
                  </p>
                </div>
              ) : (
                auditLogs.map((log, idx) => (
                  <div
                    key={log.id || idx}
                    className="p-4 rounded-lg bg-gray-800/50 backdrop-blur-sm hover:bg-gray-800/70 transition-colors"
                  >
                    <div className="flex items-start gap-3">
                      {getAuditEventIcon(log.event_type || log.type)}
                      <div className="flex-1 min-w-0">
                        <div className={`text-sm font-medium ${theme.text.primary}`}>
                          {(log.event_type || log.type || 'event').replace(/_/g, ' ').toUpperCase()}
                        </div>
                        <div className={`text-xs ${theme.text.secondary} mt-1`}>
                          {log.description || log.message || 'No description'}
                        </div>
                        <div className={`text-xs ${theme.text.secondary} mt-1 opacity-60 flex items-center gap-2`}>
                          <ClockIcon className="h-3 w-3" />
                          {formatTimestamp(log.timestamp || log.created_at)}
                          {(log.user || log.username) && (
                            <>
                              <span>•</span>
                              <UserIcon className="h-3 w-3" />
                              {log.user || log.username}
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </motion.div>
      )}

      {activeTab === 'users' && (
        <motion.div
          variants={itemVariants}
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <div className="text-center py-12">
            <UserGroupIcon className="h-16 w-16 mx-auto text-gray-500 mb-4" />
            <h3 className={`${theme.text.primary} text-lg font-semibold mb-2`}>
              User Management
            </h3>
            <p className={`${theme.text.secondary} text-sm mb-6 max-w-md mx-auto`}>
              User accounts are managed through Keycloak. Access the Keycloak admin console to create, modify, or delete user accounts.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={openKeycloakSettings}
              className="px-6 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 text-sm inline-flex items-center gap-2"
            >
              <ShieldCheckIcon className="h-5 w-5" />
              Manage Users in Keycloak
            </motion.button>
          </div>
        </motion.div>
      )}

      {activeTab === 'apikeys' && (
        <motion.div
          variants={itemVariants}
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <div className="text-center py-12">
            <KeyIcon className="h-16 w-16 mx-auto text-gray-500 mb-4" />
            <h3 className={`${theme.text.primary} text-lg font-semibold mb-2`}>
              API Key Management
            </h3>
            <p className={`${theme.text.secondary} text-sm max-w-md mx-auto`}>
              API key management features are coming soon. You will be able to create and manage API keys for programmatic access to UC-1 Pro services.
            </p>
          </div>
        </motion.div>
      )}

      {activeTab === 'sessions' && (
        <motion.div
          variants={itemVariants}
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <div className="text-center py-12">
            <ComputerDesktopIcon className="h-16 w-16 mx-auto text-gray-500 mb-4" />
            <h3 className={`${theme.text.primary} text-lg font-semibold mb-2`}>
              Session Management
            </h3>
            <p className={`${theme.text.secondary} text-sm mb-6 max-w-md mx-auto`}>
              Active sessions are managed through Keycloak. View and manage your active sessions in the Keycloak account console.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={openKeycloakSettings}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white rounded-lg hover:from-blue-700 hover:to-cyan-700 text-sm inline-flex items-center gap-2"
            >
              <ShieldCheckIcon className="h-5 w-5" />
              View Sessions in Keycloak
            </motion.button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
