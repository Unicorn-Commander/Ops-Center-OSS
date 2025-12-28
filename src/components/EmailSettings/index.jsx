import React, { useState, useEffect } from 'react';
import {
  EnvelopeIcon,
  PlusIcon,
  CheckCircleIcon,
  ArrowPathIcon,
  PaperAirplaneIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../Toast';
import { motion } from 'framer-motion';

// Component imports
import StatusBadge from './Shared/StatusBadge';
import DeleteConfirmModal from './Shared/DeleteConfirmModal';
import TestEmailModal from './TestEmail/TestEmailModal';
import EmailHistoryTable from './EmailHistory/EmailHistoryTable';
import ProviderList from './ProviderManagement/ProviderList';
import CreateProviderModal from './ProviderManagement/CreateProviderModal';
import { PROVIDER_TYPES } from './ProviderForms/ProviderTypeTab';

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

/**
 * EmailSettings - Main email settings coordinator
 *
 * Manages email provider configuration with:
 * - Provider list (create, edit, delete)
 * - Test email sending
 * - Email history tracking
 * - Microsoft 365 OAuth2 setup help
 *
 * Refactored from 1,550-line monolith to 11 modular components.
 */
export default function EmailSettings() {
  const { currentTheme } = useTheme();
  const toast = useToast();

  // Data state
  const [providers, setProviders] = useState([]);
  const [activeProvider, setActiveProvider] = useState(null);
  const [emailHistory, setEmailHistory] = useState([]);
  const [microsoftInstructions, setMicrosoftInstructions] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modal visibility state
  const [showProviderDialog, setShowProviderDialog] = useState(false);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(null);

  // Form state
  const [currentTab, setCurrentTab] = useState(0);
  const [editingProvider, setEditingProvider] = useState(null);
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
        auth_method: selectedType.authType,
        enabled: formData.enabled,
        smtp_from: formData.from_email,
        provider_config: {}
      };

      // Add auth fields based on type
      if (selectedType.authType === 'oauth2') {
        providerData.oauth2_client_id = formData.client_id;
        if (formData.client_secret && formData.client_secret !== '***HIDDEN***') {
          providerData.oauth2_client_secret = formData.client_secret;
        }
        if (formData.tenant_id) {
          providerData.oauth2_tenant_id = formData.tenant_id;
        }
      } else if (selectedType.authType === 'app_password') {
        providerData.smtp_host = formData.smtp_host;
        providerData.smtp_port = parseInt(formData.smtp_port) || 587;
        providerData.smtp_user = formData.smtp_username;
        if (formData.smtp_password && formData.smtp_password !== '***HIDDEN***') {
          providerData.smtp_password = formData.smtp_password;
        }
      } else if (selectedType.authType === 'api_key') {
        if (formData.api_key && formData.api_key !== '***HIDDEN***') {
          providerData.api_key = formData.api_key;
        }
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

  const handleSendTestEmail = async (recipient) => {
    if (!recipient) {
      toast.warning('Please enter a recipient email address');
      return;
    }

    try {
      await emailProviderAPI.sendTestEmail(recipient);
      toast.success('Test email sent successfully! Check your inbox.');
      setShowTestDialog(false);
      loadData(); // Refresh history
    } catch (error) {
      console.error('Failed to send test email:', error);
      toast.error('Failed to send test email: ' + error.message);
    }
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
          <ProviderList
            providers={providers}
            onEdit={openProviderDialog}
            onDelete={(id) => setShowDeleteConfirm(id)}
            onAdd={() => openProviderDialog()}
          />
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
          <EmailHistoryTable emailHistory={emailHistory} />
        </div>
      </div>

      {/* Modals */}
      <CreateProviderModal
        isOpen={showProviderDialog}
        onClose={closeProviderDialog}
        onSave={handleSaveProvider}
        formData={formData}
        setFormData={setFormData}
        showSensitive={showSensitive}
        setShowSensitive={setShowSensitive}
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        editingProvider={editingProvider}
        microsoftInstructions={microsoftInstructions}
      />

      <TestEmailModal
        isOpen={showTestDialog}
        onClose={() => setShowTestDialog(false)}
        onSend={handleSendTestEmail}
      />

      <DeleteConfirmModal
        isOpen={showDeleteConfirm !== null}
        onClose={() => setShowDeleteConfirm(null)}
        onConfirm={handleDeleteProvider}
        providerId={showDeleteConfirm}
      />
    </div>
  );
}
