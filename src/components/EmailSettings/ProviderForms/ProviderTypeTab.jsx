import React from 'react';
import { useTheme } from '../../../contexts/ThemeContext';

// Provider type definitions
const PROVIDER_TYPES = [
  {
    id: 'microsoft365',
    name: 'Microsoft 365 (OAuth2)',
    description: 'Recommended for Microsoft accounts with multi-factor authentication',
    authType: 'oauth2',
    requiresFields: ['client_id', 'client_secret', 'tenant_id', 'from_email']
  },
  {
    id: 'microsoft365_app_password',
    name: 'Microsoft 365 (App Password)',
    description: 'For Microsoft accounts with app-specific passwords',
    authType: 'app_password',
    requiresFields: ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
  },
  {
    id: 'google',
    name: 'Google Workspace (OAuth2)',
    description: 'Recommended for Google Workspace accounts',
    authType: 'oauth2',
    requiresFields: ['client_id', 'client_secret', 'from_email']
  },
  {
    id: 'google_app_password',
    name: 'Google Workspace (App Password)',
    description: 'For Google accounts with app-specific passwords',
    authType: 'app_password',
    requiresFields: ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
  },
  {
    id: 'sendgrid',
    name: 'SendGrid',
    description: 'High-deliverability transactional email service',
    authType: 'api_key',
    requiresFields: ['api_key', 'from_email']
  },
  {
    id: 'postmark',
    name: 'Postmark',
    description: 'Fast and reliable transactional email',
    authType: 'api_key',
    requiresFields: ['api_key', 'from_email']
  },
  {
    id: 'aws_ses',
    name: 'AWS SES',
    description: 'Amazon Simple Email Service',
    authType: 'api_key',
    requiresFields: ['api_key', 'aws_region', 'from_email']
  },
  {
    id: 'custom_smtp',
    name: 'Custom SMTP',
    description: 'Any SMTP server with username/password',
    authType: 'app_password',
    requiresFields: ['smtp_host', 'smtp_port', 'smtp_username', 'smtp_password', 'from_email']
  }
];

/**
 * ProviderTypeTab - Provider type selection tab
 *
 * First tab in create/edit provider dialog.
 * Allows selection of provider type (8 options) and optional provider name.
 *
 * @param {Object} props
 * @param {Object} props.formData - Form state
 * @param {Function} props.setFormData - Form state setter
 */
export default function ProviderTypeTab({ formData, setFormData }) {
  const { currentTheme } = useTheme();

  return (
    <div className="space-y-4">
      <div>
        <label className={`block text-sm font-medium mb-2 ${
          currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
        }`}>
          Provider Type *
        </label>
        <div className="space-y-2">
          {PROVIDER_TYPES.map((type) => (
            <label
              key={type.id}
              className={`flex items-start p-4 rounded-lg border-2 cursor-pointer transition ${
                formData.provider_type === type.id
                  ? currentTheme === 'unicorn'
                    ? 'border-purple-500 bg-purple-500/10'
                    : currentTheme === 'light'
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-blue-500 bg-blue-900/20'
                  : currentTheme === 'unicorn'
                    ? 'border-purple-500/30 hover:border-purple-500/50'
                    : currentTheme === 'light'
                    ? 'border-gray-300 hover:border-gray-400'
                    : 'border-gray-600 hover:border-gray-500'
              }`}
            >
              <input
                type="radio"
                name="provider_type"
                value={type.id}
                checked={formData.provider_type === type.id}
                onChange={(e) => setFormData({ ...formData, provider_type: e.target.value })}
                className="mt-1 mr-3"
              />
              <div className="flex-1">
                <div className={`font-semibold ${
                  currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
                }`}>
                  {type.name}
                </div>
                <div className={`text-sm mt-1 ${
                  currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
                }`}>
                  {type.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className={`block text-sm font-medium mb-2 ${
          currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
        }`}>
          Provider Name (Optional)
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          placeholder="e.g., Main Email Server"
          className={`w-full px-4 py-2 rounded-lg border ${
            currentTheme === 'unicorn'
              ? 'bg-purple-900/20 border-purple-500/30 text-white placeholder-purple-300/50'
              : currentTheme === 'light'
              ? 'bg-white border-gray-300 text-gray-900'
              : 'bg-gray-800 border-gray-600 text-white'
          }`}
        />
      </div>
    </div>
  );
}

export { PROVIDER_TYPES };
