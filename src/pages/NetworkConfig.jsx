import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import {
  WifiIcon,
  GlobeAltIcon,
  SignalIcon,
  ServerIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  PencilIcon,
  ExclamationTriangleIcon,
  ShieldCheckIcon,
  ChartBarIcon,
  CommandLineIcon,
  Cog6ToothIcon,
  ArrowTopRightOnSquareIcon,
  BoltIcon,
  CloudIcon
} from '@heroicons/react/24/outline';
import {
  CheckCircleIcon as CheckCircleIconSolid,
  ExclamationTriangleIcon as ExclamationTriangleIconSolid
} from '@heroicons/react/24/solid';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.02,
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

// Status Card Component
const StatusCard = ({ title, value, subtitle, icon: Icon, status, color = 'blue', theme }) => {
  const colorClasses = {
    blue: 'from-blue-500/10 to-cyan-500/10 border-blue-500/20 text-blue-400',
    green: 'from-emerald-500/10 to-green-500/10 border-emerald-500/20 text-emerald-400',
    purple: 'from-purple-500/10 to-indigo-500/10 border-purple-500/20 text-purple-400',
    yellow: 'from-yellow-500/10 to-amber-500/10 border-yellow-500/20 text-yellow-400',
    red: 'from-red-500/10 to-rose-500/10 border-red-500/20 text-red-400'
  };

  return (
    <motion.div
      variants={itemVariants}
      className={`
        relative p-6 rounded-2xl
        bg-gradient-to-br ${colorClasses[color]}
        border backdrop-blur-xl
        transition-all duration-300
        overflow-hidden group
      `}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[color]} backdrop-blur-sm`}>
            <Icon className="h-6 w-6" />
          </div>
          {status && (
            <div className="flex items-center gap-1">
              {status === 'connected' ? (
                <CheckCircleIconSolid className="h-5 w-5 text-green-400" />
              ) : (
                <XCircleIcon className="h-5 w-5 text-gray-500" />
              )}
            </div>
          )}
        </div>

        <div className="space-y-1">
          <p className={`text-sm font-medium ${theme.text.secondary}`}>{title}</p>
          <p className={`text-2xl font-bold ${theme.text.primary} font-mono`}>{value}</p>
          {subtitle && (
            <p className={`text-xs ${theme.text.secondary} opacity-80`}>{subtitle}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// Config Field Component
const ConfigField = ({ label, value, editable, onChange, placeholder, theme, type = "text" }) => {
  return (
    <div className="space-y-2">
      <label className={`text-sm font-medium ${theme.text.secondary}`}>
        {label}
      </label>
      {editable ? (
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`
            w-full px-4 py-3 rounded-xl font-mono text-sm
            bg-gray-800/50 border border-gray-700/50
            ${theme.text.primary}
            focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20
            transition-all duration-200
          `}
        />
      ) : (
        <div className={`
          px-4 py-3 rounded-xl font-mono text-sm
          bg-gray-800/30 border border-gray-700/30
          ${theme.text.primary}
        `}>
          {value || 'Not configured'}
        </div>
      )}
    </div>
  );
};

export default function NetworkConfig() {
  const { theme, currentTheme } = useTheme();
  const [networkConfig, setNetworkConfig] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [notification, setNotification] = useState(null);

  // Form state
  const [formData, setFormData] = useState({
    hostname: '',
    interface: 'eth0',
    method: 'dhcp',
    address: '',
    netmask: '255.255.255.0',
    gateway: '',
    dns_primary: '',
    dns_secondary: ''
  });

  useEffect(() => {
    fetchNetworkConfig();
  }, []);

  const fetchNetworkConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/system/network');
      if (!response.ok) throw new Error('Failed to fetch network configuration');
      const data = await response.json();
      setNetworkConfig(data);

      // Populate form with current values
      setFormData({
        hostname: data.hostname || '',
        interface: data.interface || 'eth0',
        method: data.method || 'dhcp',
        address: data.ip_address || '',
        netmask: data.netmask || '255.255.255.0',
        gateway: data.gateway || '',
        dns_primary: data.dns_servers?.[0] || '',
        dns_secondary: data.dns_servers?.[1] || ''
      });
    } catch (error) {
      console.error('Failed to fetch network config:', error);
      showNotification('Failed to load network configuration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const testConnectivity = async () => {
    setTesting(true);
    setTestResults(null);

    try {
      const response = await fetch('/api/v1/system/network/test', {
        method: 'POST'
      });

      if (!response.ok) throw new Error('Connectivity test failed');
      const data = await response.json();
      setTestResults(data);

      if (data.success) {
        showNotification('Connectivity test passed', 'success');
      } else {
        showNotification('Connectivity test failed', 'error');
      }
    } catch (error) {
      console.error('Connectivity test error:', error);
      setTestResults({ success: false, error: error.message });
      showNotification('Failed to run connectivity test', 'error');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (formData.method === 'static' && (!formData.address || !formData.gateway)) {
      showNotification('Please fill in all required fields for static IP', 'error');
      return;
    }

    setShowConfirm(true);
  };

  const confirmSave = async () => {
    setSaving(true);
    setShowConfirm(false);

    try {
      const payload = {
        hostname: formData.hostname,
        interface: formData.interface,
        method: formData.method,
        ...(formData.method === 'static' && {
          address: formData.address,
          netmask: formData.netmask,
          gateway: formData.gateway,
          dns_servers: [formData.dns_primary, formData.dns_secondary].filter(Boolean)
        })
      };

      const response = await fetch('/api/v1/system/network', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to update network configuration');
      }

      showNotification('Network configuration updated successfully', 'success');
      setEditMode(false);

      // Reload config after a short delay to allow changes to apply
      setTimeout(() => {
        fetchNetworkConfig();
      }, 2000);
    } catch (error) {
      console.error('Failed to save network config:', error);
      showNotification(error.message || 'Failed to save configuration', 'error');
    } finally {
      setSaving(false);
    }
  };

  const showNotification = (message, type = 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const cancelEdit = () => {
    setEditMode(false);
    // Reset form to current config
    if (networkConfig) {
      setFormData({
        hostname: networkConfig.hostname || '',
        interface: networkConfig.interface || 'eth0',
        method: networkConfig.method || 'dhcp',
        address: networkConfig.ip_address || '',
        netmask: networkConfig.netmask || '255.255.255.0',
        gateway: networkConfig.gateway || '',
        dns_primary: networkConfig.dns_servers?.[0] || '',
        dns_secondary: networkConfig.dns_servers?.[1] || ''
      });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <ArrowPathIcon className="h-12 w-12 text-purple-400 animate-spin mx-auto mb-4" />
          <p className={theme.text.secondary}>Loading network configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="relative">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-4xl font-bold ${theme.text.primary} tracking-tight`}>
              Network Settings
            </h1>
            <p className={`${theme.text.secondary} mt-2`}>
              Configure network interfaces and connectivity
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={testConnectivity}
              disabled={testing}
              className={`
                px-4 py-2 rounded-xl font-medium text-sm
                bg-gradient-to-r from-blue-600 to-cyan-600
                text-white shadow-lg
                hover:from-blue-700 hover:to-cyan-700
                disabled:opacity-50 disabled:cursor-not-allowed
                transition-all duration-200
                flex items-center gap-2
              `}
            >
              <ChartBarIcon className={`h-4 w-4 ${testing ? 'animate-spin' : ''}`} />
              {testing ? 'Testing...' : 'Test Connectivity'}
            </motion.button>

            {!editMode ? (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setEditMode(true)}
                className={`
                  px-4 py-2 rounded-xl font-medium text-sm
                  bg-gradient-to-r from-purple-600 to-indigo-600
                  text-white shadow-lg
                  hover:from-purple-700 hover:to-indigo-700
                  transition-all duration-200
                  flex items-center gap-2
                `}
              >
                <PencilIcon className="h-4 w-4" />
                Edit Settings
              </motion.button>
            ) : (
              <div className="flex gap-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={cancelEdit}
                  className="px-4 py-2 rounded-xl bg-gray-700 text-white font-medium text-sm hover:bg-gray-600"
                >
                  Cancel
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={handleSave}
                  disabled={saving}
                  className={`
                    px-4 py-2 rounded-xl font-medium text-sm
                    bg-gradient-to-r from-green-600 to-emerald-600
                    text-white shadow-lg
                    hover:from-green-700 hover:to-emerald-700
                    disabled:opacity-50 disabled:cursor-not-allowed
                    transition-all duration-200
                    flex items-center gap-2
                  `}
                >
                  <CheckCircleIcon className="h-4 w-4" />
                  {saving ? 'Saving...' : 'Save Changes'}
                </motion.button>
              </div>
            )}
          </div>
        </div>
      </motion.div>

      {/* Notification */}
      <AnimatePresence>
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`
              p-4 rounded-xl border backdrop-blur-xl
              ${notification.type === 'success'
                ? 'bg-green-500/10 border-green-500/20 text-green-400'
                : notification.type === 'error'
                ? 'bg-red-500/10 border-red-500/20 text-red-400'
                : 'bg-blue-500/10 border-blue-500/20 text-blue-400'
              }
            `}
          >
            <div className="flex items-center gap-3">
              {notification.type === 'success' ? (
                <CheckCircleIconSolid className="h-5 w-5" />
              ) : notification.type === 'error' ? (
                <ExclamationTriangleIconSolid className="h-5 w-5" />
              ) : (
                <ExclamationTriangleIcon className="h-5 w-5" />
              )}
              <span className="font-medium">{notification.message}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Warning Banner for Edit Mode */}
      {editMode && (
        <motion.div
          variants={itemVariants}
          className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/20 backdrop-blur-xl"
        >
          <div className="flex items-start gap-3">
            <ExclamationTriangleIconSolid className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-yellow-400">Warning: Network Configuration Changes</h3>
              <p className="text-sm text-yellow-300/80 mt-1">
                Changing network settings may interrupt your connection. Ensure you have physical or alternative access to the system before applying changes.
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Status Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="IP Address"
          value={networkConfig?.ip_address || 'Not Set'}
          subtitle={networkConfig?.interface || 'No Interface'}
          icon={GlobeAltIcon}
          status={networkConfig?.ip_address ? 'connected' : 'disconnected'}
          color="blue"
          theme={theme}
        />
        <StatusCard
          title="Gateway"
          value={networkConfig?.gateway || 'Not Set'}
          subtitle="Default Route"
          icon={ServerIcon}
          status={networkConfig?.gateway ? 'connected' : 'disconnected'}
          color="purple"
          theme={theme}
        />
        <StatusCard
          title="DNS Server"
          value={networkConfig?.dns_servers?.[0] || 'Not Set'}
          subtitle={networkConfig?.dns_servers?.[1] ? `Secondary: ${networkConfig.dns_servers[1]}` : 'No Secondary'}
          icon={CloudIcon}
          status={networkConfig?.dns_servers?.[0] ? 'connected' : 'disconnected'}
          color="green"
          theme={theme}
        />
        <StatusCard
          title="Hostname"
          value={networkConfig?.hostname || 'localhost'}
          subtitle={`Method: ${networkConfig?.method?.toUpperCase() || 'DHCP'}`}
          icon={CommandLineIcon}
          color="yellow"
          theme={theme}
        />
      </div>

      {/* Main Configuration Panel */}
      <motion.div
        variants={itemVariants}
        className={`
          p-6 rounded-2xl
          bg-gradient-to-br from-gray-800/40 to-gray-900/40
          border border-gray-700/50 backdrop-blur-xl
        `}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-xl font-bold ${theme.text.primary} flex items-center gap-2`}>
            <Cog6ToothIcon className="h-6 w-6" />
            Network Configuration
          </h2>
          {!editMode && (
            <span className={`text-sm ${theme.text.secondary} flex items-center gap-2`}>
              <ShieldCheckIcon className="h-4 w-4" />
              Read-Only Mode
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* System Settings */}
          <div className="space-y-4">
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
              System Settings
            </h3>

            <ConfigField
              label="Hostname"
              value={formData.hostname}
              editable={editMode}
              onChange={(val) => setFormData({...formData, hostname: val})}
              placeholder="unicorn-server"
              theme={theme}
            />

            <ConfigField
              label="Network Interface"
              value={formData.interface}
              editable={false}
              theme={theme}
            />

            <div className="space-y-2">
              <label className={`text-sm font-medium ${theme.text.secondary}`}>
                Configuration Method
              </label>
              {editMode ? (
                <select
                  value={formData.method}
                  onChange={(e) => setFormData({...formData, method: e.target.value})}
                  className={`
                    w-full px-4 py-3 rounded-xl font-mono text-sm
                    bg-gray-800/50 border border-gray-700/50
                    ${theme.text.primary}
                    focus:border-purple-500/50 focus:ring-2 focus:ring-purple-500/20
                    transition-all duration-200
                  `}
                >
                  <option value="dhcp">DHCP (Automatic)</option>
                  <option value="static">Static IP</option>
                </select>
              ) : (
                <div className={`
                  px-4 py-3 rounded-xl font-mono text-sm
                  bg-gray-800/30 border border-gray-700/30
                  ${theme.text.primary}
                `}>
                  {formData.method === 'dhcp' ? 'DHCP (Automatic)' : 'Static IP'}
                </div>
              )}
            </div>
          </div>

          {/* IP Configuration */}
          <div className="space-y-4">
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
              IP Configuration
            </h3>

            <ConfigField
              label="IP Address"
              value={formData.address}
              editable={editMode && formData.method === 'static'}
              onChange={(val) => setFormData({...formData, address: val})}
              placeholder="192.168.1.100"
              theme={theme}
            />

            <ConfigField
              label="Netmask"
              value={formData.netmask}
              editable={editMode && formData.method === 'static'}
              onChange={(val) => setFormData({...formData, netmask: val})}
              placeholder="255.255.255.0"
              theme={theme}
            />

            <ConfigField
              label="Gateway"
              value={formData.gateway}
              editable={editMode && formData.method === 'static'}
              onChange={(val) => setFormData({...formData, gateway: val})}
              placeholder="192.168.1.1"
              theme={theme}
            />
          </div>

          {/* DNS Configuration */}
          <div className="space-y-4 lg:col-span-2">
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
              DNS Configuration
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ConfigField
                label="Primary DNS"
                value={formData.dns_primary}
                editable={editMode && formData.method === 'static'}
                onChange={(val) => setFormData({...formData, dns_primary: val})}
                placeholder="8.8.8.8"
                theme={theme}
              />

              <ConfigField
                label="Secondary DNS"
                value={formData.dns_secondary}
                editable={editMode && formData.method === 'static'}
                onChange={(val) => setFormData({...formData, dns_secondary: val})}
                placeholder="8.8.4.4"
                theme={theme}
              />
            </div>
          </div>
        </div>

        {formData.method === 'dhcp' && editMode && (
          <div className="mt-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
            <p className={`text-sm ${theme.text.secondary}`}>
              <strong className="text-blue-400">DHCP Mode:</strong> Network settings will be obtained automatically from your DHCP server.
              IP Address, Gateway, and DNS settings are managed automatically.
            </p>
          </div>
        )}
      </motion.div>

      {/* Connectivity Test Results */}
      {testResults && (
        <motion.div
          variants={itemVariants}
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <h2 className={`text-xl font-bold ${theme.text.primary} mb-6 flex items-center gap-2`}>
            <ChartBarIcon className="h-6 w-6" />
            Connectivity Test Results
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`
              p-4 rounded-xl border
              ${testResults.gateway_ping
                ? 'bg-green-500/10 border-green-500/20'
                : 'bg-red-500/10 border-red-500/20'
              }
            `}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm font-medium ${theme.text.secondary}`}>Gateway Ping</span>
                {testResults.gateway_ping ? (
                  <CheckCircleIconSolid className="h-5 w-5 text-green-400" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-400" />
                )}
              </div>
              <p className={`text-xs ${testResults.gateway_ping ? 'text-green-300' : 'text-red-300'}`}>
                {testResults.gateway_ping ? 'Gateway reachable' : 'Gateway unreachable'}
              </p>
            </div>

            <div className={`
              p-4 rounded-xl border
              ${testResults.dns_resolution
                ? 'bg-green-500/10 border-green-500/20'
                : 'bg-red-500/10 border-red-500/20'
              }
            `}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm font-medium ${theme.text.secondary}`}>DNS Resolution</span>
                {testResults.dns_resolution ? (
                  <CheckCircleIconSolid className="h-5 w-5 text-green-400" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-400" />
                )}
              </div>
              <p className={`text-xs ${testResults.dns_resolution ? 'text-green-300' : 'text-red-300'}`}>
                {testResults.dns_resolution ? 'DNS working' : 'DNS not working'}
              </p>
            </div>

            <div className={`
              p-4 rounded-xl border
              ${testResults.internet_connectivity
                ? 'bg-green-500/10 border-green-500/20'
                : 'bg-red-500/10 border-red-500/20'
              }
            `}>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm font-medium ${theme.text.secondary}`}>Internet</span>
                {testResults.internet_connectivity ? (
                  <CheckCircleIconSolid className="h-5 w-5 text-green-400" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-red-400" />
                )}
              </div>
              <p className={`text-xs ${testResults.internet_connectivity ? 'text-green-300' : 'text-red-300'}`}>
                {testResults.internet_connectivity ? 'Internet accessible' : 'No internet access'}
              </p>
            </div>
          </div>

          {testResults.details && (
            <div className="mt-4 p-4 rounded-xl bg-gray-800/50 border border-gray-700/30">
              <pre className={`text-xs ${theme.text.secondary} font-mono overflow-x-auto`}>
                {JSON.stringify(testResults.details, null, 2)}
              </pre>
            </div>
          )}
        </motion.div>
      )}

      {/* Confirmation Modal */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => setShowConfirm(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6 max-w-md w-full shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 rounded-xl bg-yellow-500/10">
                  <ExclamationTriangleIconSolid className="h-6 w-6 text-yellow-400" />
                </div>
                <h3 className={`text-xl font-bold ${theme.text.primary}`}>
                  Confirm Changes
                </h3>
              </div>

              <p className={`${theme.text.secondary} mb-6`}>
                Are you sure you want to apply these network configuration changes? This may temporarily interrupt your connection.
              </p>

              <div className="bg-gray-900/50 rounded-xl p-4 mb-6 space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className={theme.text.secondary}>Hostname:</span>
                  <span className={theme.text.primary}>{formData.hostname}</span>
                </div>
                <div className="flex justify-between">
                  <span className={theme.text.secondary}>Method:</span>
                  <span className={theme.text.primary}>{formData.method.toUpperCase()}</span>
                </div>
                {formData.method === 'static' && (
                  <>
                    <div className="flex justify-between">
                      <span className={theme.text.secondary}>IP Address:</span>
                      <span className={`${theme.text.primary} font-mono`}>{formData.address}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className={theme.text.secondary}>Gateway:</span>
                      <span className={`${theme.text.primary} font-mono`}>{formData.gateway}</span>
                    </div>
                  </>
                )}
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => setShowConfirm(false)}
                  className="flex-1 px-4 py-2 rounded-xl bg-gray-700 text-white font-medium hover:bg-gray-600 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={confirmSave}
                  className="flex-1 px-4 py-2 rounded-xl bg-gradient-to-r from-green-600 to-emerald-600 text-white font-medium hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg"
                >
                  Apply Changes
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
