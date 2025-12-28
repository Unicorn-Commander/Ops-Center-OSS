import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  CogIcon, 
  BellIcon,
  ShieldCheckIcon,
  ClockIcon,
  ArrowDownTrayIcon,
  KeyIcon
} from '@heroicons/react/24/outline';

export default function Settings() {
  const [settings, setSettings] = useState({
    system: {
      idle_timeout: 300,
      auto_swap_enabled: true,
      max_memory_percent: 95,
      log_level: 'info',
    },
    notifications: {
      email_enabled: false,
      email_address: '',
      webhook_enabled: false,
      webhook_url: '',
      alert_on_errors: true,
      alert_on_updates: false,
    },
    security: {
      auth_enabled: true,
      session_timeout: 3600,
      api_keys: [],
    },
    backup: {
      auto_backup_enabled: true,
      backup_schedule: '0 2 * * *',
      retention_days: 7,
      backup_location: '/backups',
    },
  });

  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('system');

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('/api/v1/settings');
      if (!response.ok) throw new Error('Failed to fetch settings');
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Settings fetch error:', error);
    }
  };

  const saveSettings = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (!response.ok) throw new Error('Failed to save settings');
    } catch (error) {
      console.error('Settings save error:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateSetting = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
  };

  const tabs = [
    { id: 'system', name: 'System', icon: CogIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'security', name: 'Security', icon: ShieldCheckIcon },
    { id: 'backup', name: 'Backup', icon: ArrowDownTrayIcon },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Configure UC-1 Pro system settings and preferences
        </p>
      </div>

      {/* Tabs */}
      <div className="border-b dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`
                py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                ${activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
              `}
            >
              <tab.icon className="h-5 w-5" />
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Settings Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        {activeTab === 'system' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              System Settings
            </h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Model Idle Timeout
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.system.idle_timeout}
                  onChange={(e) => updateSetting('system', 'idle_timeout', parseInt(e.target.value))}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">seconds</span>
              </div>
              <p className="mt-1 text-sm text-gray-500">
                Time before idle models are swapped out
              </p>
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.system.auto_swap_enabled}
                  onChange={(e) => updateSetting('system', 'auto_swap_enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable automatic model swapping
                </span>
              </label>
              <p className="mt-1 text-sm text-gray-500 ml-6">
                Automatically swap models based on usage patterns
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Maximum GPU Memory Usage
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.system.max_memory_percent}
                  onChange={(e) => updateSetting('system', 'max_memory_percent', parseInt(e.target.value))}
                  min="50"
                  max="100"
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">%</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Log Level
              </label>
              <select
                value={settings.system.log_level}
                onChange={(e) => updateSetting('system', 'log_level', e.target.value)}
                className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              >
                <option value="debug">Debug</option>
                <option value="info">Info</option>
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>
          </motion.div>
        )}

        {activeTab === 'notifications' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Notification Settings
            </h2>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.notifications.email_enabled}
                  onChange={(e) => updateSetting('notifications', 'email_enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable email notifications
                </span>
              </label>
              {settings.notifications.email_enabled && (
                <input
                  type="email"
                  value={settings.notifications.email_address}
                  onChange={(e) => updateSetting('notifications', 'email_address', e.target.value)}
                  placeholder="admin@example.com"
                  className="mt-2 ml-6 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
              )}
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.notifications.webhook_enabled}
                  onChange={(e) => updateSetting('notifications', 'webhook_enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable webhook notifications
                </span>
              </label>
              {settings.notifications.webhook_enabled && (
                <input
                  type="url"
                  value={settings.notifications.webhook_url}
                  onChange={(e) => updateSetting('notifications', 'webhook_url', e.target.value)}
                  placeholder="https://example.com/webhook"
                  className="mt-2 ml-6 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white w-96"
                />
              )}
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.notifications.alert_on_errors}
                  onChange={(e) => updateSetting('notifications', 'alert_on_errors', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Alert on system errors
                </span>
              </label>
            </div>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.notifications.alert_on_updates}
                  onChange={(e) => updateSetting('notifications', 'alert_on_updates', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Alert on available updates
                </span>
              </label>
            </div>
          </motion.div>
        )}

        {activeTab === 'security' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Security Settings
            </h2>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.security.auth_enabled}
                  onChange={(e) => updateSetting('security', 'auth_enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable authentication
                </span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Session Timeout
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.security.session_timeout}
                  onChange={(e) => updateSetting('security', 'session_timeout', parseInt(e.target.value))}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">seconds</span>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                API Keys
              </h3>
              <div className="space-y-2">
                {settings.security.api_keys.map((key, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <KeyIcon className="h-4 w-4 text-gray-400" />
                    <code className="text-sm bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                      {key.masked}
                    </code>
                    <span className="text-sm text-gray-500">
                      Created: {new Date(key.created).toLocaleDateString()}
                    </span>
                  </div>
                ))}
                <button className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  Generate New API Key
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === 'backup' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Backup Settings
            </h2>

            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={settings.backup.auto_backup_enabled}
                  onChange={(e) => updateSetting('backup', 'auto_backup_enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Enable automatic backups
                </span>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Backup Schedule (Cron Expression)
              </label>
              <input
                type="text"
                value={settings.backup.backup_schedule}
                onChange={(e) => updateSetting('backup', 'backup_schedule', e.target.value)}
                className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              />
              <p className="mt-1 text-sm text-gray-500">
                Default: Daily at 2 AM (0 2 * * *)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Retention Period
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.backup.retention_days}
                  onChange={(e) => updateSetting('backup', 'retention_days', parseInt(e.target.value))}
                  className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                />
                <span className="text-sm text-gray-600 dark:text-gray-400">days</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Backup Location
              </label>
              <input
                type="text"
                value={settings.backup.backup_location}
                onChange={(e) => updateSetting('backup', 'backup_location', e.target.value)}
                className="px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white w-full"
              />
            </div>

            <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
              Run Backup Now
            </button>
          </motion.div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={saveSettings}
          disabled={saving}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      {/* Footer with Company Branding */}
      <div className="mt-12 pt-8 border-t dark:border-gray-700 text-center space-y-4">
        <div className="flex justify-center items-center gap-4">
          <img 
            src="/magic-unicorn-logo.png" 
            alt="Magic Unicorn" 
            className="w-8 h-8 object-contain"
          />
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Magic Unicorn Unconventional Technology & Stuff Inc.
          </p>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Unicorn Commander Pro © 2024 - v1.0.0
        </p>
      </div>
    </div>
  );
}