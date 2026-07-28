import React from 'react';
import { ClockIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../../contexts/ThemeContext';

/**
 * EmailHistoryTable - Recent emails table
 *
 * Displays a table of recently sent emails with status indicators,
 * recipient, subject, type, and timestamp.
 *
 * @param {Object} props
 * @param {Array} props.emailHistory - Array of email history objects
 */
export default function EmailHistoryTable({ emailHistory }) {
  const { currentTheme } = useTheme();

  if (emailHistory.length === 0) {
    return (
      <div className={`text-center py-12 ${
        currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
      }`}>
        <ClockIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
        <p>No emails sent yet</p>
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
              Date
            </th>
            <th className={`text-left py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Recipient
            </th>
            <th className={`text-left py-3 px-4 font-semibold ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
            }`}>
              Subject
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
          </tr>
        </thead>
        <tbody>
          {emailHistory.map((email, index) => (
            <tr
              key={index}
              className={`border-b ${
                currentTheme === 'unicorn'
                  ? 'border-purple-500/20'
                  : currentTheme === 'light'
                  ? 'border-gray-100'
                  : 'border-gray-700'
              }`}
            >
              <td className={`py-4 px-4 text-sm ${
                currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
              }`}>
                {new Date(email.created_at).toLocaleString()}
              </td>
              <td className={`py-4 px-4 ${
                currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
              }`}>
                {email.recipient}
              </td>
              <td className={`py-4 px-4 ${
                currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-300'
              }`}>
                {email.subject}
              </td>
              <td className="py-4 px-4">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  currentTheme === 'unicorn'
                    ? 'bg-purple-500/20 text-purple-300'
                    : currentTheme === 'light'
                    ? 'bg-gray-100 text-gray-700'
                    : 'bg-gray-700 text-gray-300'
                }`}>
                  {email.notification_type || 'Email'}
                </span>
              </td>
              <td className="py-4 px-4">
                {email.status === 'sent' ? (
                  <CheckCircleIcon className="w-5 h-5 text-green-500" />
                ) : email.status === 'failed' ? (
                  <ExclamationCircleIcon className="w-5 h-5 text-red-500" />
                ) : (
                  <ClockIcon className="w-5 h-5 text-yellow-500" />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
