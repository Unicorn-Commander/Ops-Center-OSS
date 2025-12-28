import React, { useState } from 'react';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../../contexts/ThemeContext';
import { PROVIDER_TYPES } from './ProviderTypeTab';
import {
  validateRequired,
  validateGuid,
  validateHostname,
  validatePort
} from '../../../utils/validation';

/**
 * AuthenticationTab - Authentication configuration tab
 *
 * Second tab in create/edit provider dialog.
 * Renders different forms based on provider type:
 * - OAuth2: client_id, client_secret, tenant_id (Microsoft)
 * - App Password: SMTP host, port, username, password
 * - API Key: API key, AWS region (for AWS SES)
 *
 * @param {Object} props
 * @param {Object} props.formData - Form state
 * @param {Function} props.setFormData - Form state setter
 * @param {Object} props.showSensitive - Visibility state for sensitive fields
 * @param {Function} props.setShowSensitive - Visibility state setter
 */
export default function AuthenticationTab({ formData, setFormData, showSensitive, setShowSensitive }) {
  const { currentTheme } = useTheme();
  const [errors, setErrors] = useState({});

  const selectedType = PROVIDER_TYPES.find(p => p.id === formData.provider_type);

  // Validation helper
  const validateField = (name, value) => {
    let error = null;

    switch (name) {
      case 'client_id':
        error = validateRequired(value, 'Client ID') || validateGuid(value);
        break;
      case 'client_secret':
        if (value !== '***HIDDEN***') {
          error = validateRequired(value, 'Client Secret');
        }
        break;
      case 'tenant_id':
        error = validateRequired(value, 'Tenant ID') || validateGuid(value);
        break;
      case 'smtp_host':
        error = validateRequired(value, 'SMTP Host') || validateHostname(value);
        break;
      case 'smtp_port':
        error = validateRequired(value, 'SMTP Port') || validatePort(value);
        break;
      case 'smtp_username':
        error = validateRequired(value, 'Username');
        break;
      case 'smtp_password':
        if (value !== '***HIDDEN***') {
          error = validateRequired(value, 'Password');
        }
        break;
      case 'api_key':
        if (value !== '***HIDDEN***') {
          error = validateRequired(value, 'API Key');
        }
        break;
      default:
        break;
    }

    return error;
  };

  // Handle field change with validation
  const handleFieldChange = (name, value) => {
    setFormData({ ...formData, [name]: value });

    // Real-time validation
    const error = validateField(name, value);
    setErrors(prev => ({
      ...prev,
      [name]: error
    }));
  };

  if (!selectedType) {
    return (
      <div className={`text-center py-8 ${
        currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
      }`}>
        Please select a provider type first
      </div>
    );
  }

  // OAuth2 Form (Microsoft 365, Google)
  if (selectedType.authType === 'oauth2') {
    return (
      <div className="space-y-4">
        <div>
          <label className={`block text-sm font-medium mb-2 ${
            currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
          }`}>
            Client ID *
          </label>
          <input
            type="text"
            value={formData.client_id}
            onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
            className={`w-full px-4 py-2 rounded-lg border ${
              currentTheme === 'unicorn'
                ? 'bg-purple-900/20 border-purple-500/30 text-white'
                : currentTheme === 'light'
                ? 'bg-white border-gray-300 text-gray-900'
                : 'bg-gray-800 border-gray-600 text-white'
            }`}
          />
        </div>

        <div>
          <label className={`block text-sm font-medium mb-2 ${
            currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
          }`}>
            Client Secret *
          </label>
          <div className="relative">
            <input
              type={showSensitive.client_secret ? 'text' : 'password'}
              value={formData.client_secret}
              onChange={(e) => setFormData({ ...formData, client_secret: e.target.value })}
              className={`w-full px-4 py-2 pr-12 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            />
            <button
              type="button"
              onClick={() => setShowSensitive({ ...showSensitive, client_secret: !showSensitive.client_secret })}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              {showSensitive.client_secret ? (
                <EyeSlashIcon className="w-5 h-5 text-gray-400" />
              ) : (
                <EyeIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {formData.provider_type.startsWith('microsoft365') && (
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
            }`}>
              Tenant ID *
            </label>
            <input
              type="text"
              value={formData.tenant_id}
              onChange={(e) => setFormData({ ...formData, tenant_id: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            />
          </div>
        )}
      </div>
    );
  }

  // App Password Form (SMTP)
  if (selectedType.authType === 'app_password') {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
            }`}>
              SMTP Host *
            </label>
            <input
              type="text"
              value={formData.smtp_host}
              onChange={(e) => setFormData({ ...formData, smtp_host: e.target.value })}
              placeholder="smtp.office365.com"
              className={`w-full px-4 py-2 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            />
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
            }`}>
              SMTP Port *
            </label>
            <input
              type="number"
              value={formData.smtp_port}
              onChange={(e) => setFormData({ ...formData, smtp_port: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            />
          </div>
        </div>

        <div>
          <label className={`block text-sm font-medium mb-2 ${
            currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
          }`}>
            Username *
          </label>
          <input
            type="text"
            value={formData.smtp_username}
            onChange={(e) => setFormData({ ...formData, smtp_username: e.target.value })}
            className={`w-full px-4 py-2 rounded-lg border ${
              currentTheme === 'unicorn'
                ? 'bg-purple-900/20 border-purple-500/30 text-white'
                : currentTheme === 'light'
                ? 'bg-white border-gray-300 text-gray-900'
                : 'bg-gray-800 border-gray-600 text-white'
            }`}
          />
        </div>

        <div>
          <label className={`block text-sm font-medium mb-2 ${
            currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
          }`}>
            Password *
          </label>
          <div className="relative">
            <input
              type={showSensitive.smtp_password ? 'text' : 'password'}
              value={formData.smtp_password}
              onChange={(e) => setFormData({ ...formData, smtp_password: e.target.value })}
              className={`w-full px-4 py-2 pr-12 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            />
            <button
              type="button"
              onClick={() => setShowSensitive({ ...showSensitive, smtp_password: !showSensitive.smtp_password })}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              {showSensitive.smtp_password ? (
                <EyeSlashIcon className="w-5 h-5 text-gray-400" />
              ) : (
                <EyeIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
        </div>
      </div>
    );
  }

  // API Key Form (SendGrid, Postmark, AWS SES)
  if (selectedType.authType === 'api_key') {
    return (
      <div className="space-y-4">
        <div>
          <label className={`block text-sm font-medium mb-2 ${
            currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
          }`}>
            API Key *
          </label>
          <div className="relative">
            <input
              type={showSensitive.api_key ? 'text' : 'password'}
              value={formData.api_key}
              onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
              className={`w-full px-4 py-2 pr-12 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            />
            <button
              type="button"
              onClick={() => setShowSensitive({ ...showSensitive, api_key: !showSensitive.api_key })}
              className="absolute right-3 top-1/2 -translate-y-1/2"
            >
              {showSensitive.api_key ? (
                <EyeSlashIcon className="w-5 h-5 text-gray-400" />
              ) : (
                <EyeIcon className="w-5 h-5 text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {formData.provider_type === 'aws_ses' && (
          <div>
            <label className={`block text-sm font-medium mb-2 ${
              currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
            }`}>
              AWS Region *
            </label>
            <select
              value={formData.aws_region}
              onChange={(e) => setFormData({ ...formData, aws_region: e.target.value })}
              className={`w-full px-4 py-2 rounded-lg border ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900/20 border-purple-500/30 text-white'
                  : currentTheme === 'light'
                  ? 'bg-white border-gray-300 text-gray-900'
                  : 'bg-gray-800 border-gray-600 text-white'
              }`}
            >
              <option value="us-east-1">US East (N. Virginia)</option>
              <option value="us-west-2">US West (Oregon)</option>
              <option value="eu-west-1">EU (Ireland)</option>
              <option value="eu-central-1">EU (Frankfurt)</option>
              <option value="ap-southeast-1">Asia Pacific (Singapore)</option>
              <option value="ap-northeast-1">Asia Pacific (Tokyo)</option>
            </select>
          </div>
        )}
      </div>
    );
  }

  return null;
}
