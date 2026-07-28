import React from 'react';
import { useTheme } from '../../../contexts/ThemeContext';

/**
 * SettingsTab - Provider settings tab
 *
 * Third tab in create/edit provider dialog.
 * Allows configuration of:
 * - From email address (required)
 * - Advanced configuration (JSON)
 * - Enable/disable toggle
 *
 * @param {Object} props
 * @param {Object} props.formData - Form state
 * @param {Function} props.setFormData - Form state setter
 */
export default function SettingsTab({ formData, setFormData }) {
  const { currentTheme } = useTheme();

  return (
    <div className="space-y-4">
      <div>
        <label className={`block text-sm font-medium mb-2 ${
          currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
        }`}>
          From Email Address *
        </label>
        <input
          type="email"
          value={formData.from_email}
          onChange={(e) => setFormData({ ...formData, from_email: e.target.value })}
          placeholder="notifications@yourdomain.com"
          className={`w-full px-4 py-2 rounded-lg border ${
            currentTheme === 'unicorn'
              ? 'bg-purple-900/20 border-purple-500/30 text-white'
              : currentTheme === 'light'
              ? 'bg-white border-gray-300 text-gray-900'
              : 'bg-gray-800 border-gray-600 text-white'
          }`}
        />
        <p className={`text-xs mt-1 ${
          currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
        }`}>
          All emails will be sent from this address
        </p>
      </div>

      <div>
        <label className={`block text-sm font-medium mb-2 ${
          currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
        }`}>
          Advanced Configuration (JSON)
        </label>
        <textarea
          value={formData.config}
          onChange={(e) => setFormData({ ...formData, config: e.target.value })}
          rows={8}
          className={`w-full px-4 py-2 rounded-lg border font-mono text-sm ${
            currentTheme === 'unicorn'
              ? 'bg-purple-900/20 border-purple-500/30 text-white'
              : currentTheme === 'light'
              ? 'bg-white border-gray-300 text-gray-900'
              : 'bg-gray-800 border-gray-600 text-white'
          }`}
        />
      </div>

      <div className="flex items-center">
        <input
          type="checkbox"
          id="enabled"
          checked={formData.enabled}
          onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
          className="mr-3"
        />
        <label htmlFor="enabled" className={`text-sm font-medium ${
          currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
        }`}>
          Enable this provider
        </label>
      </div>
    </div>
  );
}
