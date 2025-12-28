/**
 * AccountNotifications Component
 *
 * Notification preferences management
 * - Email notification toggles
 * - System notification toggles
 * - Update notification toggles
 * - Real-time updates via API
 *
 * API Endpoints:
 * - GET /api/v1/auth/session - Load current notification settings
 * - PUT /api/v1/auth/notifications - Update notification preferences
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BellIcon,
  EnvelopeIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ComputerDesktopIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

export default function AccountNotifications() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(null);
  const [message, setMessage] = useState(null);

  const [notifications, setNotifications] = useState({
    email: true,
    system: true,
    updates: false,
    security: true,
    billing: true,
    marketing: false
  });

  // Theme classes matching UserSettings pattern
  const themeClasses = {
    card: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-white border-gray-200'
      : 'bg-slate-800 border-slate-700',
    text: currentTheme === 'unicorn'
      ? 'text-purple-100'
      : currentTheme === 'light'
      ? 'text-gray-900'
      : 'text-slate-100',
    subtext: currentTheme === 'unicorn'
      ? 'text-purple-300'
      : currentTheme === 'light'
      ? 'text-gray-600'
      : 'text-slate-400',
    input: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 border-white/20 text-purple-100'
      : currentTheme === 'light'
      ? 'bg-gray-50 border-gray-300 text-gray-900'
      : 'bg-slate-900 border-slate-600 text-slate-100',
    button: currentTheme === 'unicorn'
      ? 'bg-purple-600 hover:bg-purple-700 text-white'
      : currentTheme === 'light'
      ? 'bg-blue-600 hover:bg-blue-700 text-white'
      : 'bg-blue-600 hover:bg-blue-700 text-white'
  };

  useEffect(() => {
    loadNotificationSettings();
  }, []);

  const loadNotificationSettings = async () => {
    try {
      const response = await fetch('/api/v1/auth/session');
      if (response.ok) {
        const data = await response.json();
        if (data.user && data.user.notifications) {
          setNotifications({
            ...notifications,
            ...data.user.notifications
          });
        }
      }
    } catch (error) {
      console.error('Failed to load notification settings:', error);
      setMessage({ type: 'error', text: 'Failed to load notification settings' });
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (key) => {
    const newValue = !notifications[key];
    const oldNotifications = { ...notifications };

    // Optimistic update
    setNotifications({ ...notifications, [key]: newValue });
    setSaving(key);

    try {
      const response = await fetch('/api/v1/auth/notifications', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          [key]: newValue
        })
      });

      if (response.ok) {
        setMessage({
          type: 'success',
          text: `${key.charAt(0).toUpperCase() + key.slice(1)} notifications ${newValue ? 'enabled' : 'disabled'}`
        });
        setTimeout(() => setMessage(null), 2000);
      } else {
        // Revert on error
        setNotifications(oldNotifications);
        setMessage({ type: 'error', text: 'Failed to update notification settings' });
      }
    } catch (error) {
      console.error('Failed to update notification:', error);
      // Revert on error
      setNotifications(oldNotifications);
      setMessage({ type: 'error', text: 'An error occurred while updating settings' });
    } finally {
      setSaving(null);
    }
  };

  const notificationTypes = [
    {
      key: 'email',
      title: 'Email Notifications',
      description: 'Receive notifications via email',
      icon: EnvelopeIcon,
      color: 'text-blue-500'
    },
    {
      key: 'system',
      title: 'System Notifications',
      description: 'Receive in-app system notifications',
      icon: ComputerDesktopIcon,
      color: 'text-green-500'
    },
    {
      key: 'updates',
      title: 'Update Notifications',
      description: 'Get notified about platform updates',
      icon: ArrowPathIcon,
      color: 'text-purple-500'
    },
    {
      key: 'security',
      title: 'Security Alerts',
      description: 'Important security notifications',
      icon: BellIcon,
      color: 'text-red-500'
    },
    {
      key: 'billing',
      title: 'Billing Notifications',
      description: 'Payment and subscription updates',
      icon: BellIcon,
      color: 'text-yellow-500'
    },
    {
      key: 'marketing',
      title: 'Marketing Communications',
      description: 'News, tips, and promotional content',
      icon: BellIcon,
      color: 'text-indigo-500'
    }
  ];

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${themeClasses.text}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-current"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={`text-3xl font-bold ${themeClasses.text}`}>
          Notification Preferences
        </h1>
        <p className={`mt-2 ${themeClasses.subtext}`}>
          Manage how and when you receive notifications
        </p>
      </div>

      {/* Status Message */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-lg p-4 ${
            message.type === 'success'
              ? 'bg-green-500/20 border border-green-500/50'
              : 'bg-red-500/20 border border-red-500/50'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <>
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="text-green-400">{message.text}</span>
              </>
            ) : (
              <>
                <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                <span className="text-red-400">{message.text}</span>
              </>
            )}
          </div>
        </motion.div>
      )}

      {/* Notification Settings */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <BellIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
            Notification Settings
          </h2>
        </div>

        <div className="space-y-4">
          {notificationTypes.map(({ key, title, description, icon: Icon, color }) => (
            <motion.div
              key={key}
              whileHover={{ scale: 1.01 }}
              className={`flex items-center justify-between p-4 rounded-lg ${
                currentTheme === 'light' ? 'bg-gray-50' : 'bg-gray-700/20'
              } border ${
                notifications[key]
                  ? 'border-blue-500/30'
                  : currentTheme === 'light'
                  ? 'border-gray-200'
                  : 'border-gray-700'
              }`}
            >
              <div className="flex items-start gap-3 flex-1">
                <div className={`mt-1 ${color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div>
                  <p className={`font-medium ${themeClasses.text}`}>
                    {title}
                  </p>
                  <p className={`text-sm ${themeClasses.subtext} mt-1`}>
                    {description}
                  </p>
                </div>
              </div>

              <button
                onClick={() => handleToggle(key)}
                disabled={saving === key}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  notifications[key]
                    ? 'bg-blue-600'
                    : currentTheme === 'light'
                    ? 'bg-gray-300'
                    : 'bg-slate-700'
                } disabled:opacity-50`}
              >
                {saving === key ? (
                  <span className="inline-block h-4 w-4 transform rounded-full bg-white translate-x-1 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                  </span>
                ) : (
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifications[key] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                )}
              </button>
            </motion.div>
          ))}
        </div>

        {/* Important Note */}
        <div className={`mt-6 p-4 rounded-lg ${
          currentTheme === 'light' ? 'bg-yellow-50' : 'bg-yellow-500/10'
        } border border-yellow-500/30`}>
          <div className="flex gap-3">
            <ExclamationCircleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className={`text-sm font-medium ${themeClasses.text}`}>
                Important Security Notifications
              </p>
              <p className={`text-sm ${themeClasses.subtext} mt-1`}>
                Critical security alerts will always be sent regardless of your notification settings
                to ensure your account security.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
