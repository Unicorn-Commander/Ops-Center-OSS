import React from 'react';
import { EnvelopeIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../../contexts/ThemeContext';
import StatusBadge from '../Shared/StatusBadge';
import { PROVIDER_TYPES } from '../ProviderForms/ProviderTypeTab';

/**
 * ProviderList - Provider table display
 *
 * Displays all configured email providers in a table with:
 * - Provider name
 * - From email
 * - Type (OAuth2, SMTP, API Key)
 * - Status badge
 * - Edit/Delete actions
 *
 * @param {Object} props
 * @param {Array} props.providers - List of provider objects
 * @param {Function} props.onEdit - Edit handler
 * @param {Function} props.onDelete - Delete handler
 * @param {Function} props.onAdd - Add provider handler
 */
export default function ProviderList({ providers, onEdit, onDelete, onAdd }) {
  const { currentTheme } = useTheme();

  if (providers.length === 0) {
    return (
      <div className={`text-center py-12 ${
        currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
      }`}>
        <EnvelopeIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No email providers configured yet</p>
        <button
          onClick={onAdd}
          className={`mt-4 px-6 py-2 rounded-lg font-semibold ${
            currentTheme === 'unicorn'
              ? 'bg-purple-600 hover:bg-purple-700 text-white'
              : currentTheme === 'light'
              ? 'bg-blue-600 hover:bg-blue-700 text-white'
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
        >
          Add Your First Provider
        </button>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className={`border-b ${
            currentTheme === 'unicorn'
              ? 'border-purple-500/30'
              : currentTheme === 'light'
              ? 'border-gray-200'
              : 'border-gray-700'
          }`}>
            <th className={`text-left py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Provider
            </th>
            <th className={`text-left py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              From Email
            </th>
            <th className={`text-left py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Type
            </th>
            <th className={`text-left py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Status
            </th>
            <th className={`text-right py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {providers.map((provider) => (
            <tr
              key={provider.id}
              className={`border-b ${
                currentTheme === 'unicorn'
                  ? 'border-purple-500/20 hover:bg-purple-500/5'
                  : currentTheme === 'light'
                  ? 'border-gray-100 hover:bg-gray-50'
                  : 'border-gray-700 hover:bg-gray-700/50'
              }`}
            >
              <td className={`py-4 px-4 ${
                currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
              }`}>
                <div className="font-semibold">{provider.name}</div>
              </td>
              <td className={`py-4 px-4 ${
                currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
              }`}>
                {provider.from_email}
              </td>
              <td className="py-4 px-4">
                <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                  currentTheme === 'unicorn'
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : currentTheme === 'light'
                    ? 'bg-gray-100 text-gray-700 border border-gray-300'
                    : 'bg-gray-700 text-gray-300 border border-gray-600'
                }`}>
                  {PROVIDER_TYPES.find(p => p.id === provider.provider_type)?.authType || 'Unknown'}
                </span>
              </td>
              <td className="py-4 px-4">
                <StatusBadge status={provider.status || 'success'} enabled={provider.enabled} />
              </td>
              <td className="py-4 px-4 text-right">
                <div className="flex items-center justify-end gap-2">
                  <button
                    onClick={() => onEdit(provider)}
                    className={`p-2 rounded hover:bg-white/10 ${
                      currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-blue-600' : 'text-blue-400'
                    }`}
                    title="Edit provider"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                  <button
                    onClick={() => onDelete(provider.id)}
                    className="p-2 rounded hover:bg-red-500/20 text-red-500"
                    title="Delete provider"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
