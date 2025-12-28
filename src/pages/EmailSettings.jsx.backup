import React, { useState, useEffect } from 'react';
import {
  EnvelopeIcon,
  PlusIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  DocumentDuplicateIcon,
  PaperAirplaneIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
  XMarkIcon,
  CheckIcon,
  InformationCircleIcon,
  ClipboardDocumentIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import { motion, AnimatePresence } from 'framer-motion';

// Email Provider API helper
const emailProviderAPI = {
  async listProviders() {
    const response = await fetch('/api/v1/email-provider/providers', {
      credentials: 'include'
    });
    if (!response.ok) throw new Error('Failed to fetch providers');
    return response.json();
  },

  async getActiveProvider() {
    const response = await fetch('/api/v1/email-provider/providers/active', {
      credentials: 'include'
    });
    if (response.status === 404) return null;
    if (!response.ok) throw new Error('Failed to fetch active provider');
    return response.json();
  },

  async createProvider(providerData) {
    console.log('Creating provider with data:', providerData);
    const response = await fetch('/api/v1/email-provider/providers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(providerData),
      credentials: 'include'
    });
    if (!response.ok) {
      let errorMessage = 'Failed to create provider';
      try {
        const error = await response.json();
        console.error('Backend error response:', error);
        errorMessage = error.detail || error.message || JSON.stringify(error);
      } catch (e) {
        // Response isn't JSON
        const text = await response.text();
        console.error('Backend error text:', text);
        errorMessage = text || `HTTP ${response.status}: ${response.statusText}`;
      }
      throw new Error(errorMessage);
    }
    return response.json();
  },

  async updateProvider(providerId, providerData) {
    const response = await fetch(`/api/v1/email-provider/providers/${providerId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(providerData),
      credentials: 'include'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update provider');
    }
    return response.json();
  },

  async deleteProvider(providerId) {
    const response = await fetch(`/api/v1/email-provider/providers/${providerId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete provider');
    }
    return response.json();
  },

  async sendTestEmail(recipient, providerId = null) {
    const response = await fetch('/api/v1/email-provider/test-email', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient, provider_id: providerId }),
      credentials: 'include'
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send test email');
    }
    return response.json();
  },

  async getMicrosoftInstructions() {
    const response = await fetch('/api/v1/email-provider/oauth2/microsoft/setup-instructions', {
      credentials: 'include'
    });
    if (!response.ok) throw new Error('Failed to fetch instructions');
    return response.json();
  },

  async getEmailHistory(page = 1, perPage = 50, filters = {}) {
    const params = new URLSearchParams({
      page: page.toString(),
      per_page: perPage.toString(),
      ...filters
    });
    const response = await fetch(`/api/v1/email-provider/history?${params}`, {
      credentials: 'include'
    });
    if (!response.ok) throw new Error('Failed to fetch email history');
    return response.json();
  }
};

// Provider type definitions
const PROVIDER_TYPES = [
  {
    id: 'microsoft365',  // MUST match backend enum
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
    id: 'google',  // MUST match backend enum
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

// Status badge component
const StatusBadge = ({ status, enabled }) => {
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
};

// Copy to clipboard helper
const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text);
};

// Main EmailSettings component
export default function EmailSettings() {
  const { currentTheme } = useTheme();
  const toast = useToast();
  const [providers, setProviders] = useState([]);
  const [activeProvider, setActiveProvider] = useState(null);
  const [emailHistory, setEmailHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showProviderDialog, setShowProviderDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [editingProvider, setEditingProvider] = useState(null);
  const [microsoftInstructions, setMicrosoftInstructions] = useState(null);
  const [testEmail, setTestEmail] = useState('');
  const [historyPage, setHistoryPage] = useState(1);
  const [historyFilters, setHistoryFilters] = useState({});

  // Form state
  const [formData, setFormData] = useState({
    provider_type: '',
    name: '',
    from_email: '',
    client_id: '',
    client_secret: '',
    tenant_id: '',
    smtp_host: '',
    smtp_port: '587',
    smtp_username: '',
    smtp_password: '',
    api_key: '',
    aws_region: 'us-east-1',
    enabled: true,
    config: '{}'
  });

  const [showSensitive, setShowSensitive] = useState({
    client_secret: false,
    smtp_password: false,
    api_key: false
  });

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [providersData, activeData, historyData] = await Promise.all([
        emailProviderAPI.listProviders(),
        emailProviderAPI.getActiveProvider().catch(() => null),
        emailProviderAPI.getEmailHistory(1, 50)
      ]);
      // Extract arrays from response objects (backend returns { success: true, providers: [...] })
      setProviders(providersData.providers || []);
      setActiveProvider(activeData?.provider || null);
      setEmailHistory(historyData.history || []);
    } catch (error) {
      console.error('Failed to load email settings:', error);
      toast.error('Failed to load email settings: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Open provider dialog for add/edit
  const openProviderDialog = async (provider = null) => {
    if (provider) {
      setEditingProvider(provider);
      setFormData({
        provider_type: provider.provider_type,
        name: provider.name,
        from_email: provider.from_email,
        client_id: provider.client_id || '',
        client_secret: '***HIDDEN***',
        tenant_id: provider.tenant_id || '',
        smtp_host: provider.smtp_host || '',
        smtp_port: provider.smtp_port || '587',
        smtp_username: provider.smtp_username || '',
        smtp_password: '***HIDDEN***',
        api_key: '***HIDDEN***',
        aws_region: provider.aws_region || 'us-east-1',
        enabled: provider.enabled,
        config: JSON.stringify(provider.config || {}, null, 2)
      });
    } else {
      setEditingProvider(null);
      setFormData({
        provider_type: '',
        name: '',
        from_email: '',
        client_id: '',
        client_secret: '',
        tenant_id: '',
        smtp_host: '',
        smtp_port: '587',
        smtp_username: '',
        smtp_password: '',
        api_key: '',
        aws_region: 'us-east-1',
        enabled: true,
        config: '{}'
      });
    }
    setCurrentTab(0);
    setShowProviderDialog(true);

    // Load Microsoft instructions if needed
    if (!microsoftInstructions) {
      try {
        const instructions = await emailProviderAPI.getMicrosoftInstructions();
        setMicrosoftInstructions(instructions);
      } catch (error) {
        console.error('Failed to load Microsoft instructions:', error);
      }
    }
  };

  const closeProviderDialog = () => {
    setShowProviderDialog(false);
    setEditingProvider(null);
    setCurrentTab(0);
  };

  const handleSaveProvider = async () => {
    try {
      // Validate required fields
      const selectedType = PROVIDER_TYPES.find(p => p.id === formData.provider_type);
      if (!selectedType) {
        toast.warning('Please select a provider type');
        return;
      }

      // Build provider data - MATCH BACKEND API SCHEMA
      const providerData = {
        provider_type: formData.provider_type,
        auth_method: selectedType.authType,  // REQUIRED field for backend
        enabled: formData.enabled,
        smtp_from: formData.from_email,  // Backend uses smtp_from not from_email
        provider_config: {}  // Backend uses provider_config not config
      };

      // Add auth fields based on type
      if (selectedType.authType === 'oauth2') {
        providerData.oauth2_client_id = formData.client_id;  // Backend prefix: oauth2_
        if (formData.client_secret && formData.client_secret !== '***HIDDEN***') {
          providerData.oauth2_client_secret = formData.client_secret;
        }
        if (formData.tenant_id) {
          providerData.oauth2_tenant_id = formData.tenant_id;
        }
      } else if (selectedType.authType === 'app_password') {
        providerData.smtp_host = formData.smtp_host;
        providerData.smtp_port = parseInt(formData.smtp_port) || 587;
        providerData.smtp_user = formData.smtp_username;  // Backend uses smtp_user not smtp_username
        if (formData.smtp_password && formData.smtp_password !== '***HIDDEN***') {
          providerData.smtp_password = formData.smtp_password;
        }
      } else if (selectedType.authType === 'api_key') {
        if (formData.api_key && formData.api_key !== '***HIDDEN***') {
          providerData.api_key = formData.api_key;
        }
        // AWS region goes in provider_config
        if (formData.aws_region) {
          providerData.provider_config.aws_region = formData.aws_region;
        }
      }

      // Parse and merge additional config
      try {
        if (formData.config && formData.config.trim()) {
          const parsedConfig = JSON.parse(formData.config);
          providerData.provider_config = { ...providerData.provider_config, ...parsedConfig };
        }
      } catch (e) {
        toast.error('Invalid JSON in configuration field');
        return;
      }

      // Create or update
      if (editingProvider) {
        await emailProviderAPI.updateProvider(editingProvider.id, providerData);
      } else {
        await emailProviderAPI.createProvider(providerData);
      }

      toast.success(editingProvider ? 'Provider updated successfully' : 'Provider created successfully');
      closeProviderDialog();
      loadData();
    } catch (error) {
      console.error('Failed to save provider:', error);
      // Better error display
      const errorMsg = error.message || String(error) || 'Unknown error';
      toast.error('Failed to save provider: ' + errorMsg);
    }
  };

  const handleDeleteProvider = async (providerId) => {
    try {
      await emailProviderAPI.deleteProvider(providerId);
      toast.success('Provider deleted successfully');
      setShowDeleteConfirm(null);
      loadData();
    } catch (error) {
      console.error('Failed to delete provider:', error);
      toast.error('Failed to delete provider: ' + error.message);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmail) {
      toast.warning('Please enter a recipient email address');
      return;
    }

    try {
      await emailProviderAPI.sendTestEmail(testEmail);
      toast.success('Test email sent successfully! Check your inbox.');
      setShowTestDialog(false);
      setTestEmail('');
      loadData(); // Refresh history
    } catch (error) {
      console.error('Failed to send test email:', error);
      toast.error('Failed to send test email: ' + error.message);
    }
  };

  const renderProviderTypeTab = () => (
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

  const renderAuthenticationTab = () => {
    const selectedType = PROVIDER_TYPES.find(p => p.id === formData.provider_type);
    if (!selectedType) {
      return (
        <div className={`text-center py-8 ${
          currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
        }`}>
          Please select a provider type first
        </div>
      );
    }

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
    } else if (selectedType.authType === 'app_password') {
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
    } else if (selectedType.authType === 'api_key') {
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
  };

  const renderSettingsTab = () => (
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

  const renderSetupHelpTab = () => {
    if (!formData.provider_type.startsWith('microsoft365_oauth') || !microsoftInstructions) {
      return (
        <div className={`text-center py-8 ${
          currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
        }`}>
          Setup instructions are available for Microsoft 365 OAuth2
        </div>
      );
    }

    return (
      <div className="space-y-4">
        <div className={`p-4 rounded-lg ${
          currentTheme === 'unicorn'
            ? 'bg-blue-500/10 border border-blue-500/30'
            : currentTheme === 'light'
            ? 'bg-blue-50 border border-blue-200'
            : 'bg-blue-900/20 border border-blue-600'
        }`}>
          <div className="flex items-start gap-3">
            <InformationCircleIcon className="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className={`font-semibold mb-2 ${
                currentTheme === 'unicorn' ? 'text-blue-300' : currentTheme === 'light' ? 'text-blue-900' : 'text-blue-300'
              }`}>
                Reuse Existing Azure AD Application
              </h3>
              <p className={`text-sm ${
                currentTheme === 'unicorn' ? 'text-blue-200' : currentTheme === 'light' ? 'text-blue-800' : 'text-blue-200'
              }`}>
                You can reuse the same Azure AD app that's configured for Keycloak SSO. Just add the Mail.Send permission.
              </p>
            </div>
          </div>
        </div>

        <div>
          <h3 className={`font-semibold mb-3 ${
            currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            Step-by-Step Setup Instructions
          </h3>
          <ol className="space-y-4">
            {microsoftInstructions.steps?.map((step, index) => (
              <li key={index} className="flex gap-3">
                <span className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  currentTheme === 'unicorn'
                    ? 'bg-purple-500 text-white'
                    : currentTheme === 'light'
                    ? 'bg-blue-500 text-white'
                    : 'bg-blue-600 text-white'
                }`}>
                  {index + 1}
                </span>
                <div className="flex-1">
                  <p className={currentTheme === 'unicorn' ? 'text-purple-100' : currentTheme === 'light' ? 'text-gray-800' : 'text-gray-200'}>
                    {step.text}
                  </p>
                  {step.copyable && (
                    <div className="mt-2">
                      <div className={`flex items-center gap-2 p-3 rounded font-mono text-sm ${
                        currentTheme === 'unicorn'
                          ? 'bg-purple-900/30 border border-purple-500/30'
                          : currentTheme === 'light'
                          ? 'bg-gray-100 border border-gray-300'
                          : 'bg-gray-800 border border-gray-600'
                      }`}>
                        <code className="flex-1 overflow-x-auto">{step.value}</code>
                        <button
                          onClick={() => {
                            copyToClipboard(step.value);
                            toast.success('Copied to clipboard!');
                          }}
                          className="p-1 hover:bg-white/10 rounded"
                        >
                          <ClipboardDocumentIcon className="w-5 h-5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ol>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${
            currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            Email Settings
          </h1>
          <p className={`mt-1 ${
            currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
          }`}>
            Configure email providers for sending notifications
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowTestDialog(true)}
            disabled={!activeProvider}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition ${
              activeProvider
                ? currentTheme === 'unicorn'
                  ? 'bg-purple-600 hover:bg-purple-700 text-white'
                  : currentTheme === 'light'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-400 text-gray-700 cursor-not-allowed'
            }`}
          >
            <PaperAirplaneIcon className="w-5 h-5" />
            Send Test Email
          </button>
          <button
            onClick={() => openProviderDialog()}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition ${
              currentTheme === 'unicorn'
                ? 'bg-purple-600 hover:bg-purple-700 text-white'
                : currentTheme === 'light'
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            <PlusIcon className="w-5 h-5" />
            Add Provider
          </button>
        </div>
      </div>

      {/* Active Provider Card */}
      {activeProvider && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-6 rounded-lg border-2 ${
            currentTheme === 'unicorn'
              ? 'bg-purple-500/10 border-purple-500'
              : currentTheme === 'light'
              ? 'bg-green-50 border-green-500'
              : 'bg-green-900/20 border-green-500'
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <CheckCircleIcon className="w-8 h-8 text-green-500" />
              <div>
                <h2 className={`text-xl font-bold ${
                  currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
                }`}>
                  Active Provider
                </h2>
                <p className={`text-sm ${
                  currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
                }`}>
                  {activeProvider.name} - {activeProvider.from_email}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <StatusBadge status="success" enabled={true} />
              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                  : currentTheme === 'light'
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-blue-900/30 text-blue-300 border border-blue-600'
              }`}>
                {PROVIDER_TYPES.find(p => p.id === activeProvider.provider_type)?.name || activeProvider.provider_type}
              </span>
            </div>
          </div>
        </motion.div>
      )}

      {/* Providers List */}
      <div className={`rounded-lg border ${
        currentTheme === 'unicorn'
          ? 'bg-purple-900/20 border-purple-500/30'
          : currentTheme === 'light'
          ? 'bg-white border-gray-200'
          : 'bg-gray-800 border-gray-700'
      }`}>
        <div className="p-6 border-b border-current">
          <h2 className={`text-xl font-bold ${
            currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            All Providers
          </h2>
        </div>
        <div className="p-6">
          {providers.length === 0 ? (
            <div className={`text-center py-12 ${
              currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`}>
              <EnvelopeIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No email providers configured yet</p>
              <button
                onClick={() => openProviderDialog()}
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
          ) : (
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
                            onClick={() => openProviderDialog(provider)}
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
                            onClick={() => setShowDeleteConfirm(provider.id)}
                            className="p-2 rounded hover:bg-red-500/20 text-red-500"
                            title="Delete provider"
                          >
                            <TrashIcon className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Email History */}
      <div className={`rounded-lg border ${
        currentTheme === 'unicorn'
          ? 'bg-purple-900/20 border-purple-500/30'
          : currentTheme === 'light'
          ? 'bg-white border-gray-200'
          : 'bg-gray-800 border-gray-700'
      }`}>
        <div className="p-6 border-b border-current">
          <h2 className={`text-xl font-bold ${
            currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
          }`}>
            Recent Emails
          </h2>
        </div>
        <div className="p-6">
          {emailHistory.length === 0 ? (
            <div className={`text-center py-12 ${
              currentTheme === 'unicorn' ? 'text-purple-300' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
            }`}>
              <ClockIcon className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No emails sent yet</p>
            </div>
          ) : (
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
          )}
        </div>
      </div>

      {/* Provider Dialog */}
      <AnimatePresence>
        {showProviderDialog && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-lg ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900 border border-purple-500/30'
                  : currentTheme === 'light'
                  ? 'bg-white border border-gray-200'
                  : 'bg-gray-800 border border-gray-700'
              }`}
            >
              {/* Dialog Header */}
              <div className="p-6 border-b border-current">
                <div className="flex items-center justify-between">
                  <h2 className={`text-2xl font-bold ${
                    currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
                  }`}>
                    {editingProvider ? 'Edit Provider' : 'Add Email Provider'}
                  </h2>
                  <button
                    onClick={closeProviderDialog}
                    className="p-2 rounded hover:bg-white/10"
                  >
                    <XMarkIcon className="w-6 h-6" />
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className={`flex border-b ${
                currentTheme === 'unicorn'
                  ? 'border-purple-500/30'
                  : currentTheme === 'light'
                  ? 'border-gray-200'
                  : 'border-gray-700'
              }`}>
                {['Provider Type', 'Authentication', 'Settings', 'Setup Help'].map((tab, index) => (
                  <button
                    key={tab}
                    onClick={() => setCurrentTab(index)}
                    className={`flex-1 px-4 py-3 font-semibold transition ${
                      currentTab === index
                        ? currentTheme === 'unicorn'
                          ? 'bg-purple-500/20 text-white border-b-2 border-purple-500'
                          : currentTheme === 'light'
                          ? 'bg-blue-50 text-blue-700 border-b-2 border-blue-500'
                          : 'bg-blue-900/20 text-blue-300 border-b-2 border-blue-500'
                        : currentTheme === 'unicorn'
                          ? 'text-purple-300 hover:bg-purple-500/10'
                          : currentTheme === 'light'
                          ? 'text-gray-600 hover:bg-gray-50'
                          : 'text-gray-400 hover:bg-gray-700/50'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
                {currentTab === 0 && renderProviderTypeTab()}
                {currentTab === 1 && renderAuthenticationTab()}
                {currentTab === 2 && renderSettingsTab()}
                {currentTab === 3 && renderSetupHelpTab()}
              </div>

              {/* Dialog Footer */}
              <div className="p-6 border-t border-current flex items-center justify-end gap-3">
                <button
                  onClick={closeProviderDialog}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30'
                      : currentTheme === 'light'
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveProvider}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : currentTheme === 'light'
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  {editingProvider ? 'Update Provider' : 'Create Provider'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Test Email Dialog */}
      <AnimatePresence>
        {showTestDialog && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`w-full max-w-md rounded-lg p-6 ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900 border border-purple-500/30'
                  : currentTheme === 'light'
                  ? 'bg-white border border-gray-200'
                  : 'bg-gray-800 border border-gray-700'
              }`}
            >
              <h2 className={`text-xl font-bold mb-4 ${
                currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
              }`}>
                Send Test Email
              </h2>
              <div className="mb-4">
                <label className={`block text-sm font-medium mb-2 ${
                  currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-700' : 'text-gray-200'
                }`}>
                  Recipient Email Address
                </label>
                <input
                  type="email"
                  value={testEmail}
                  onChange={(e) => setTestEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={`w-full px-4 py-2 rounded-lg border ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-900/20 border-purple-500/30 text-white'
                      : currentTheme === 'light'
                      ? 'bg-white border-gray-300 text-gray-900'
                      : 'bg-gray-700 border-gray-600 text-white'
                  }`}
                />
              </div>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => {
                    setShowTestDialog(false);
                    setTestEmail('');
                  }}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30'
                      : currentTheme === 'light'
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSendTestEmail}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : currentTheme === 'light'
                      ? 'bg-blue-600 hover:bg-blue-700 text-white'
                      : 'bg-blue-600 hover:bg-blue-700 text-white'
                  }`}
                >
                  Send Test
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className={`w-full max-w-md rounded-lg p-6 ${
                currentTheme === 'unicorn'
                  ? 'bg-purple-900 border border-red-500/50'
                  : currentTheme === 'light'
                  ? 'bg-white border border-red-300'
                  : 'bg-gray-800 border border-red-600'
              }`}
            >
              <div className="flex items-start gap-4 mb-4">
                <ExclamationCircleIcon className="w-8 h-8 text-red-500 flex-shrink-0" />
                <div>
                  <h2 className={`text-xl font-bold mb-2 ${
                    currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
                  }`}>
                    Delete Provider?
                  </h2>
                  <p className={`text-sm ${
                    currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
                  }`}>
                    This action cannot be undone. All configuration will be permanently deleted.
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setShowDeleteConfirm(null)}
                  className={`px-6 py-2 rounded-lg font-semibold transition ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30'
                      : currentTheme === 'light'
                      ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteProvider(showDeleteConfirm)}
                  className="px-6 py-2 rounded-lg font-semibold bg-red-600 hover:bg-red-700 text-white transition"
                >
                  Delete Provider
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
