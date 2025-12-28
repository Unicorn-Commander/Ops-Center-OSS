import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  UserCircleIcon,
  EnvelopeIcon,
  KeyIcon,
  BellIcon,
  ShieldCheckIcon,
  GlobeAltIcon,
  CheckCircleIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function UserSettings() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [userInfo, setUserInfo] = useState(null);
  const [saveStatus, setSaveStatus] = useState(null);

  const [settings, setSettings] = useState({
    email: '',
    name: '',
    username: '',
    role: '',
    notifications: {
      email: true,
      system: true,
      updates: false
    },
    preferences: {
      language: 'en',
      timezone: 'America/New_York'
    }
  });

  useEffect(() => {
    loadUserInfo();
  }, []);

  const loadUserInfo = async () => {
    try {
      const response = await fetch('/api/v1/auth/session');
      if (response.ok) {
        const data = await response.json();
        if (data.user) {
          setUserInfo(data.user);
          setSettings(prev => ({
            ...prev,
            email: data.user.email || '',
            name: data.user.name || '',
            username: data.user.username || '',
            role: data.user.role || 'viewer'
          }));
        }
      }
    } catch (error) {
      console.error('Failed to load user info:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaveStatus('saving');

    // Simulate save operation
    setTimeout(() => {
      setSaveStatus('success');
      setTimeout(() => setSaveStatus(null), 3000);
    }, 1000);
  };

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
        <h1 className={`text-3xl font-bold ${themeClasses.text}`}>User Settings</h1>
        <p className={`mt-2 ${themeClasses.subtext}`}>
          Manage your account settings and preferences
        </p>
      </div>

      {/* Save Status */}
      {saveStatus && (
        <div className={`rounded-lg p-4 ${
          saveStatus === 'success'
            ? 'bg-green-500/20 border border-green-500/50'
            : 'bg-blue-500/20 border border-blue-500/50'
        }`}>
          <div className="flex items-center gap-2">
            {saveStatus === 'success' ? (
              <>
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="text-green-400">Settings saved successfully</span>
              </>
            ) : (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-400"></div>
                <span className="text-blue-400">Saving...</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Profile Information */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <UserCircleIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>Profile Information</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
              Username
            </label>
            <input
              type="text"
              value={settings.username}
              disabled
              className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} opacity-60 cursor-not-allowed`}
            />
            <p className={`text-xs mt-1 ${themeClasses.subtext}`}>
              Username cannot be changed
            </p>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
              Full Name
            </label>
            <input
              type="text"
              value={settings.name}
              onChange={(e) => setSettings({...settings, name: e.target.value})}
              className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input}`}
            />
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
              Email Address
            </label>
            <input
              type="email"
              value={settings.email}
              onChange={(e) => setSettings({...settings, email: e.target.value})}
              className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input}`}
            />
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
              Role
            </label>
            <input
              type="text"
              value={settings.role.charAt(0).toUpperCase() + settings.role.slice(1)}
              disabled
              className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} opacity-60 cursor-not-allowed`}
            />
          </div>
        </div>
      </div>

      {/* Account Security */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheckIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>Security</h2>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className={`font-medium ${themeClasses.text}`}>Password</p>
              <p className={`text-sm ${themeClasses.subtext}`}>
                Manage your password via Auth settings
              </p>
            </div>
            <button
              onClick={() => window.open('https://auth.your-domain.com/if/user/', '_blank')}
              className={`px-4 py-2 rounded-lg ${themeClasses.button}`}
            >
              Change Password
            </button>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <p className={`font-medium ${themeClasses.text}`}>Two-Factor Authentication</p>
              <p className={`text-sm ${themeClasses.subtext}`}>
                Add an extra layer of security
              </p>
            </div>
            <button
              onClick={() => window.open('https://auth.your-domain.com/if/user/', '_blank')}
              className={`px-4 py-2 rounded-lg ${themeClasses.button}`}
            >
              Configure
            </button>
          </div>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <BellIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>Notifications</h2>
        </div>

        <div className="space-y-4">
          {Object.entries(settings.notifications).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between">
              <div>
                <p className={`font-medium ${themeClasses.text} capitalize`}>
                  {key} Notifications
                </p>
                <p className={`text-sm ${themeClasses.subtext}`}>
                  Receive notifications via {key}
                </p>
              </div>
              <button
                onClick={() => setSettings({
                  ...settings,
                  notifications: {
                    ...settings.notifications,
                    [key]: !value
                  }
                })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  value
                    ? 'bg-blue-600'
                    : currentTheme === 'light'
                    ? 'bg-gray-300'
                    : 'bg-slate-700'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    value ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Preferences */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <GlobeAltIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>Preferences</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
              Language
            </label>
            <select
              value={settings.preferences.language}
              onChange={(e) => setSettings({
                ...settings,
                preferences: {...settings.preferences, language: e.target.value}
              })}
              className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input}`}
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
            </select>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
              Timezone
            </label>
            <select
              value={settings.preferences.timezone}
              onChange={(e) => setSettings({
                ...settings,
                preferences: {...settings.preferences, timezone: e.target.value}
              })}
              className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input}`}
            >
              <option value="America/New_York">Eastern Time (ET)</option>
              <option value="America/Chicago">Central Time (CT)</option>
              <option value="America/Denver">Mountain Time (MT)</option>
              <option value="America/Los_Angeles">Pacific Time (PT)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saveStatus === 'saving'}
          className={`px-6 py-3 rounded-lg font-medium ${themeClasses.button} disabled:opacity-50`}
        >
          {saveStatus === 'saving' ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  );
}
