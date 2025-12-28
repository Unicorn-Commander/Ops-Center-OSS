import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  Cog6ToothIcon,
  BuildingOfficeIcon,
  PhotoIcon,
  PaintBrushIcon,
  GlobeAltIcon,
  ClockIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowUpTrayIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

export default function OrganizationSettings() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg } = useOrganization();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Organization settings
  const [settings, setSettings] = useState({
    name: '',
    displayName: '',
    description: '',
    logo: null,
    logoUrl: '',
    website: '',
    timezone: 'UTC',
    defaultRole: 'member',
    allowSelfRegistration: false,
    requireEmailVerification: true,
    branding: {
      primaryColor: '#667eea',
      accentColor: '#764ba2',
      theme: 'unicorn'
    },
    preferences: {
      language: 'en',
      dateFormat: 'YYYY-MM-DD',
      timeFormat: '24h'
    }
  });

  // Toast notification
  const [toast, setToast] = useState({
    show: false,
    message: '',
    type: 'success'
  });

  useEffect(() => {
    if (currentOrg) {
      fetchSettings();
    }
  }, [currentOrg]);

  const fetchSettings = async () => {
    if (!currentOrg) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/v1/org/${currentOrg.id}/settings`);
      if (!response.ok) throw new Error('Failed to fetch settings');

      const data = await response.json();
      setSettings({ ...settings, ...data });
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      showToast('Failed to load organization settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    if (!currentOrg) return;

    setSaving(true);
    try {
      const response = await fetch(`/api/v1/org/${currentOrg.id}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to save settings');
      }

      showToast('Settings saved successfully');
    } catch (error) {
      showToast(error.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        showToast('Logo file size must be less than 5MB', 'error');
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setSettings({
          ...settings,
          logo: file,
          logoUrl: reader.result
        });
      };
      reader.readAsDataURL(file);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type }), 5000);
  };

  const timezones = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney'
  ];

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                <Cog6ToothIcon className="h-6 w-6 text-white" />
              </div>
              Organization Settings
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>Manage your organization's preferences and branding</p>
          </div>
        </div>
      </motion.div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {/* Organization Information */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-6">
              <BuildingOfficeIcon className="h-6 w-6 text-blue-500" />
              <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Organization Information</h2>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Organization Name *</label>
                  <input
                    type="text"
                    value={settings.name}
                    onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    placeholder="Acme Corporation"
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Display Name</label>
                  <input
                    type="text"
                    value={settings.displayName}
                    onChange={(e) => setSettings({ ...settings, displayName: e.target.value })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    placeholder="Acme Corp"
                  />
                </div>
              </div>

              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Description</label>
                <textarea
                  value={settings.description}
                  onChange={(e) => setSettings({ ...settings, description: e.target.value })}
                  rows={3}
                  className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  placeholder="Brief description of your organization..."
                />
              </div>

              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Website</label>
                <div className="relative">
                  <GlobeAltIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                  <input
                    type="url"
                    value={settings.website}
                    onChange={(e) => setSettings({ ...settings, website: e.target.value })}
                    className={`w-full pl-10 pr-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    placeholder="https://example.com"
                  />
                </div>
              </div>
            </div>
          </motion.div>

          {/* Logo & Branding */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-6">
              <PaintBrushIcon className="h-6 w-6 text-purple-500" />
              <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Logo & Branding</h2>
            </div>

            <div className="space-y-6">
              {/* Logo Upload */}
              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Organization Logo</label>
                <div className="flex items-center gap-4">
                  <div className={`w-24 h-24 rounded-lg border-2 border-dashed ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} flex items-center justify-center overflow-hidden`}>
                    {settings.logoUrl ? (
                      <img src={settings.logoUrl} alt="Organization logo" className="w-full h-full object-cover" />
                    ) : (
                      <PhotoIcon className="h-8 w-8 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <label className={`inline-flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg cursor-pointer transition-colors`}>
                      <ArrowUpTrayIcon className="h-4 w-4" />
                      Upload Logo
                      <input
                        type="file"
                        accept="image/*"
                        onChange={handleLogoUpload}
                        className="hidden"
                      />
                    </label>
                    <p className={`text-xs ${theme.text.secondary} mt-2`}>
                      PNG, JPG or SVG. Maximum size 5MB. Recommended: 512x512px
                    </p>
                  </div>
                  {settings.logoUrl && (
                    <button
                      onClick={() => setSettings({ ...settings, logo: null, logoUrl: '' })}
                      className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  )}
                </div>
              </div>

              {/* Brand Colors */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Primary Color</label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={settings.branding.primaryColor}
                      onChange={(e) => setSettings({
                        ...settings,
                        branding: { ...settings.branding, primaryColor: e.target.value }
                      })}
                      className="w-12 h-10 rounded-lg border border-gray-600 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.branding.primaryColor}
                      onChange={(e) => setSettings({
                        ...settings,
                        branding: { ...settings.branding, primaryColor: e.target.value }
                      })}
                      className={`flex-1 px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Accent Color</label>
                  <div className="flex gap-2">
                    <input
                      type="color"
                      value={settings.branding.accentColor}
                      onChange={(e) => setSettings({
                        ...settings,
                        branding: { ...settings.branding, accentColor: e.target.value }
                      })}
                      className="w-12 h-10 rounded-lg border border-gray-600 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={settings.branding.accentColor}
                      onChange={(e) => setSettings({
                        ...settings,
                        branding: { ...settings.branding, accentColor: e.target.value }
                      })}
                      className={`flex-1 px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                    />
                  </div>
                </div>
              </div>

              {/* Theme Selection */}
              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Default Theme</label>
                <select
                  value={settings.branding.theme}
                  onChange={(e) => setSettings({
                    ...settings,
                    branding: { ...settings.branding, theme: e.target.value }
                  })}
                  className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                >
                  <option value="unicorn">Magic Unicorn</option>
                  <option value="dark">Professional Dark</option>
                  <option value="light">Professional Light</option>
                </select>
              </div>
            </div>
          </motion.div>

          {/* Preferences */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-6">
              <ClockIcon className="h-6 w-6 text-green-500" />
              <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Preferences</h2>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Timezone</label>
                  <select
                    value={settings.timezone}
                    onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    {timezones.map((tz) => (
                      <option key={tz} value={tz}>{tz}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Date Format</label>
                  <select
                    value={settings.preferences.dateFormat}
                    onChange={(e) => setSettings({
                      ...settings,
                      preferences: { ...settings.preferences, dateFormat: e.target.value }
                    })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                  </select>
                </div>

                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Time Format</label>
                  <select
                    value={settings.preferences.timeFormat}
                    onChange={(e) => setSettings({
                      ...settings,
                      preferences: { ...settings.preferences, timeFormat: e.target.value }
                    })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  >
                    <option value="24h">24-hour</option>
                    <option value="12h">12-hour</option>
                  </select>
                </div>
              </div>

              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Default Role for New Members</label>
                <select
                  value={settings.defaultRole}
                  onChange={(e) => setSettings({ ...settings, defaultRole: e.target.value })}
                  className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
              </div>

              {/* Toggle Settings */}
              <div className="space-y-3 pt-4 border-t border-gray-700/50">
                <label className="flex items-center justify-between cursor-pointer group">
                  <div>
                    <div className={`font-medium ${theme.text.primary}`}>Require Email Verification</div>
                    <div className={`text-sm ${theme.text.secondary}`}>New members must verify their email address</div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={settings.requireEmailVerification}
                      onChange={(e) => setSettings({ ...settings, requireEmailVerification: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </div>
                </label>

                <label className="flex items-center justify-between cursor-pointer group">
                  <div>
                    <div className={`font-medium ${theme.text.primary}`}>Allow Self Registration</div>
                    <div className={`text-sm ${theme.text.secondary}`}>Users can join without an invitation</div>
                  </div>
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={settings.allowSelfRegistration}
                      onChange={(e) => setSettings({ ...settings, allowSelfRegistration: e.target.checked })}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-800 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </div>
                </label>
              </div>
            </div>
          </motion.div>

          {/* Save Button */}
          <motion.div variants={itemVariants} className="flex justify-end gap-3">
            <button
              onClick={() => fetchSettings()}
              className="px-6 py-3 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              disabled={saving}
            >
              Reset Changes
            </button>
            <button
              onClick={handleSaveSettings}
              disabled={saving || !settings.name}
              className={`px-6 py-3 ${theme.button} rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2`}
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <CheckCircleIcon className="h-5 w-5" />
                  Save Settings
                </>
              )}
            </button>
          </motion.div>
        </>
      )}

      {/* Toast Notification */}
      {toast.show && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-4 right-4 z-50"
        >
          <div className={`flex items-center gap-3 px-6 py-4 rounded-lg shadow-lg ${
            toast.type === 'success'
              ? 'bg-green-500/20 border border-green-500/30 text-green-400'
              : 'bg-red-500/20 border border-red-500/30 text-red-400'
          }`}>
            {toast.type === 'success' ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <XMarkIcon className="h-5 w-5" />
            )}
            <span>{toast.message}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
