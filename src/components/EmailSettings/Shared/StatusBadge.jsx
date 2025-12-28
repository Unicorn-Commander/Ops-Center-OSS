import React from 'react';
import { useTheme } from '../../../contexts/ThemeContext';

/**
 * StatusBadge - Provider status indicator
 *
 * Displays the current status and enabled state of an email provider
 * with theme-aware styling (unicorn/light/dark).
 *
 * @param {Object} props
 * @param {string} props.status - Provider status ('success', 'error', 'pending')
 * @param {boolean} props.enabled - Whether provider is enabled
 */
export default function StatusBadge({ status, enabled }) {
  const { currentTheme } = useTheme();

  if (!enabled) {
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
        currentTheme === 'unicorn'
          ? 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
          : currentTheme === 'light'
          ? 'bg-gray-200 text-gray-600 border border-gray-300'
          : 'bg-gray-700/50 text-gray-400 border border-gray-600'
      }`}>
        Disabled
      </span>
    );
  }

  const colors = {
    success: currentTheme === 'unicorn'
      ? 'bg-green-500/20 text-green-400 border-green-500/30'
      : currentTheme === 'light'
      ? 'bg-green-100 text-green-700 border-green-300'
      : 'bg-green-900/30 text-green-400 border-green-600',
    error: currentTheme === 'unicorn'
      ? 'bg-red-500/20 text-red-400 border-red-500/30'
      : currentTheme === 'light'
      ? 'bg-red-100 text-red-700 border-red-300'
      : 'bg-red-900/30 text-red-400 border-red-600',
    pending: currentTheme === 'unicorn'
      ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      : currentTheme === 'light'
      ? 'bg-yellow-100 text-yellow-700 border-yellow-300'
      : 'bg-yellow-900/30 text-yellow-400 border-yellow-600'
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${colors[status] || colors.pending}`}>
      {status === 'success' ? 'Active' : status === 'error' ? 'Error' : 'Pending'}
    </span>
  );
}
