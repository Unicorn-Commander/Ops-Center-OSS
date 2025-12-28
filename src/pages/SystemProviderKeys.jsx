/**
 * SystemProviderKeys Component - Admin System-Level API Key Management
 *
 * ADMIN ONLY: Configure system-level API keys used for metering users
 * Different from user BYOK - these keys are used to provide service to all users
 *
 * Providers:
 * - OpenRouter (recommended - universal proxy)
 * - OpenAI (direct GPT-4 access)
 * - Anthropic (Claude models)
 * - Google (Gemini models)
 *
 * Backend: /api/v1/llm/admin/system-keys/*
 * Storage: PostgreSQL (encrypted) with environment fallback
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  KeyIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  ServerIcon,
  XMarkIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function SystemProviderKeys() {
  const { theme, currentTheme } = useTheme();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [testingProvider, setTestingProvider] = useState(null);
  const [savingKey, setSavingKey] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [userInfo, setUserInfo] = useState(null);

  // Theme classes
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
      : 'bg-blue-600 hover:bg-blue-700 text-white',
    modal: currentTheme === 'unicorn'
      ? 'bg-purple-900/95 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-white border-gray-200'
      : 'bg-slate-800 border-slate-700'
  };

  // Provider information
  const providerInfo = {
    openrouter: {
      name: 'OpenRouter',
      icon: '🔀',
      color: 'from-blue-500 to-cyan-500',
      description: 'Universal proxy - 200+ models (GPT-4o, Claude 3.5, Gemini 2.0)',
      getKeyUrl: 'https://openrouter.ai/keys',
      keyFormat: 'sk-or-v1-...',
      recommended: true
    },
    openai: {
      name: 'OpenAI',
      icon: '🤖',
      color: 'from-green-500 to-emerald-500',
      description: 'GPT-4o, GPT-4o-mini, GPT-4-turbo, o1-preview, o1-mini',
      getKeyUrl: 'https://platform.openai.com/api-keys',
      keyFormat: 'sk-proj-...'
    },
    anthropic: {
      name: 'Anthropic',
      icon: '🧠',
      color: 'from-purple-500 to-pink-500',
      description: 'Claude 3.5 Sonnet (latest), Claude 3 Opus/Sonnet/Haiku',
      getKeyUrl: 'https://console.anthropic.com/settings/keys',
      keyFormat: 'sk-ant-...'
    },
    google: {
      name: 'Google AI',
      icon: '🔍',
      color: 'from-red-500 to-orange-500',
      description: 'Gemini 2.0 Flash, Gemini 1.5 Pro/Flash (2M context)',
      getKeyUrl: 'https://aistudio.google.com/apikey',
      keyFormat: 'AIza...'
    }
  };

  useEffect(() => {
    checkAdminAccess();
  }, []);

  const checkAdminAccess = async () => {
    try {
      // Check if user is logged in and is admin
      const storedUser = localStorage.getItem('userInfo');
      if (storedUser) {
        const user = JSON.parse(storedUser);
        setUserInfo(user);

        if (user.role !== 'admin') {
          showToast('error', 'Access denied. Admin privileges required.');
          setTimeout(() => navigate('/admin'), 2000);
          return;
        }

        await loadProviders();
      } else {
        navigate('/admin/login');
      }
    } catch (error) {
      console.error('Error checking admin access:', error);
      navigate('/admin/login');
    }
  };

  const loadProviders = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/llm/admin/system-keys', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers || []);
      } else if (response.status === 403) {
        showToast('error', 'Access denied. Admin privileges required.');
        setTimeout(() => navigate('/admin'), 2000);
      } else {
        showToast('error', 'Failed to load system providers');
      }
    } catch (error) {
      console.error('Error loading providers:', error);
      showToast('error', 'Network error loading providers');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  const handleSaveKey = async () => {
    if (!selectedProvider || !apiKeyInput.trim()) {
      showToast('error', 'Please enter an API key');
      return;
    }

    setSavingKey(true);
    try {
      const response = await fetch(`/api/v1/llm/admin/system-keys/${selectedProvider.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          api_key: apiKeyInput.trim()
        })
      });

      if (response.ok) {
        showToast('success', `${providerInfo[selectedProvider.provider_type]?.name || selectedProvider.name} system key updated successfully!`);
        setShowAddModal(false);
        setSelectedProvider(null);
        setApiKeyInput('');
        await loadProviders();
      } else {
        const error = await response.json();
        showToast('error', error.detail || 'Failed to save system key');
      }
    } catch (error) {
      console.error('Error saving key:', error);
      showToast('error', 'Network error. Please try again.');
    } finally {
      setSavingKey(false);
    }
  };

  const handleTestKey = async (providerId) => {
    setTestingProvider(providerId);
    try {
      const response = await fetch(`/api/v1/llm/admin/system-keys/${providerId}/test`, {
        method: 'POST',
        credentials: 'include'
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Use the backend's message which includes model count
        showToast('success', result.message || `${result.provider_name || 'Provider'} system key is valid!`);
        await loadProviders();
      } else {
        showToast('error', result.message || 'System key validation failed');
      }
    } catch (error) {
      console.error('Error testing key:', error);
      showToast('error', 'Network error during test');
    } finally {
      setTestingProvider(null);
    }
  };

  const handleDeleteKey = async (providerId) => {
    try {
      // Find provider to get the name
      const provider = providers.find(p => p.id === providerId);
      const providerName = provider ? (providerInfo[provider.provider_type]?.name || provider.name) : 'Provider';

      const response = await fetch(`/api/v1/llm/admin/system-keys/${providerId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        showToast('info', `${providerName} system key deleted. Will use environment fallback.`);
        setConfirmDelete(null);
        await loadProviders();
      } else {
        showToast('error', 'Failed to delete system key');
      }
    } catch (error) {
      console.error('Error deleting key:', error);
      showToast('error', 'Network error. Please try again.');
    }
  };

  const getStatusBadge = (provider) => {
    if (provider.key_source === 'database') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30 flex items-center gap-1">
          <CheckCircleIcon className="h-4 w-4" />
          Database
        </span>
      );
    } else if (provider.key_source === 'environment') {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 flex items-center gap-1">
          <ExclamationTriangleIcon className="h-4 w-4" />
          Environment
        </span>
      );
    } else {
      return (
        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1">
          <XCircleIcon className="h-4 w-4" />
          Not Set
        </span>
      );
    }
  };

  const getTestStatusIcon = (provider) => {
    if (!provider.last_tested) {
      return null;
    }

    if (provider.test_status === 'valid') {
      return <CheckCircleIcon className="h-5 w-5 text-green-400" />;
    } else if (provider.test_status === 'failed') {
      return <XCircleIcon className="h-5 w-5 text-red-400" />;
    }
    return null;
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${themeClasses.text}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-current mx-auto mb-4"></div>
          <p>Loading system provider keys...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={`text-3xl font-bold ${themeClasses.text}`}>System Provider Keys</h1>
        <p className={`mt-2 ${themeClasses.subtext}`}>
          Configure API keys used for metering all users
        </p>
      </div>

      {/* Toast Notification */}
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`rounded-lg p-4 ${
              toast.type === 'success'
                ? 'bg-green-500/20 border border-green-500/50'
                : toast.type === 'info'
                ? 'bg-blue-500/20 border border-blue-500/50'
                : 'bg-red-500/20 border border-red-500/50'
            }`}
          >
            <div className="flex items-center gap-2">
              {toast.type === 'success' ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
              ) : toast.type === 'info' ? (
                <InformationCircleIcon className="h-5 w-5 text-blue-400" />
              ) : (
                <XCircleIcon className="h-5 w-5 text-red-400" />
              )}
              <span className={
                toast.type === 'success' ? 'text-green-400' :
                toast.type === 'info' ? 'text-blue-400' : 'text-red-400'
              }>
                {toast.message}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Warning Card */}
      <div className={`rounded-xl border-2 p-6 ${
        currentTheme === 'unicorn'
          ? 'bg-orange-900/30 border-orange-500/50'
          : currentTheme === 'light'
          ? 'bg-orange-50 border-orange-300'
          : 'bg-orange-900/30 border-orange-500/50'
      }`}>
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 bg-orange-500/20 rounded-lg flex items-center justify-center flex-shrink-0">
            <ExclamationTriangleIcon className="h-6 w-6 text-orange-400" />
          </div>
          <div>
            <h3 className={`font-semibold ${themeClasses.text} mb-1`}>Important: System-Wide Impact</h3>
            <p className={themeClasses.subtext}>
              These API keys are used to provide service to <strong>all users</strong> on the platform.
              Changes here affect billing, metering, and service availability. Test keys before saving.
            </p>
          </div>
        </div>
      </div>

      {/* Provider Cards Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {providers.map((provider) => {
          const info = providerInfo[provider.id] || {
            name: provider.id,
            icon: '🔑',
            color: 'from-gray-500 to-gray-600',
            description: 'LLM Provider'
          };

          return (
            <motion.div
              key={provider.id}
              whileHover={{ scale: 1.01 }}
              className={`rounded-xl border p-6 ${themeClasses.card} ${
                info.recommended ? 'ring-2 ring-purple-500/50' : ''
              }`}
            >
              {info.recommended && (
                <div className="inline-block px-3 py-1 bg-purple-500/20 text-purple-400 text-xs font-semibold rounded-full mb-3">
                  ⭐ Recommended
                </div>
              )}

              {/* Provider Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 bg-gradient-to-br ${info.color} rounded-lg flex items-center justify-center text-2xl`}>
                    {info.icon}
                  </div>
                  <div>
                    <h3 className={`font-semibold ${themeClasses.text}`}>{info.name}</h3>
                    <p className={`text-sm ${themeClasses.subtext}`}>{info.description}</p>
                  </div>
                </div>
                {getStatusBadge(provider)}
              </div>

              {/* Key Information */}
              <div className={`rounded-lg border p-4 mb-4 ${
                currentTheme === 'light' ? 'bg-gray-50 border-gray-200' : 'bg-gray-800/30 border-gray-700'
              }`}>
                <div className="space-y-3">
                  {/* Key Preview */}
                  {provider.key_preview ? (
                    <div>
                      <span className={`text-xs font-medium ${themeClasses.subtext}`}>API Key:</span>
                      <code className={`text-sm ${themeClasses.text} font-mono block mt-1`}>
                        {provider.key_preview}
                      </code>
                    </div>
                  ) : (
                    <div>
                      <span className={`text-xs font-medium ${themeClasses.subtext}`}>API Key:</span>
                      <p className={`text-sm ${themeClasses.subtext} mt-1`}>Not configured</p>
                    </div>
                  )}

                  {/* Last Tested */}
                  {provider.last_tested && (
                    <div className="flex items-center justify-between">
                      <div>
                        <span className={`text-xs font-medium ${themeClasses.subtext}`}>Last tested:</span>
                        <p className={`text-sm ${themeClasses.text}`}>
                          {new Date(provider.last_tested).toLocaleString()}
                        </p>
                      </div>
                      {getTestStatusIcon(provider)}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2">
                {provider.key_source !== 'not_set' ? (
                  <>
                    <button
                      onClick={() => handleTestKey(provider.id)}
                      disabled={testingProvider === provider.id}
                      className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg ${themeClasses.button} disabled:opacity-50`}
                    >
                      {testingProvider === provider.id ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Testing...
                        </>
                      ) : (
                        <>
                          <ArrowPathIcon className="h-4 w-4" />
                          Test
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedProvider(provider);
                        setApiKeyInput('');
                        setShowAddModal(true);
                      }}
                      className="px-4 py-2 rounded-lg border border-blue-500/50 text-blue-400 hover:bg-blue-500/10"
                    >
                      <PencilIcon className="h-4 w-4" />
                    </button>
                    {provider.key_source === 'database' && (
                      <button
                        onClick={() => setConfirmDelete(provider.id)}
                        className="px-4 py-2 rounded-lg border border-red-500/50 text-red-400 hover:bg-red-500/10"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    )}
                  </>
                ) : (
                  <button
                    onClick={() => {
                      setSelectedProvider(provider);
                      setApiKeyInput('');
                      setShowAddModal(true);
                    }}
                    className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg ${themeClasses.button}`}
                  >
                    <KeyIcon className="h-4 w-4" />
                    Add Key
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Info Section */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4 flex items-center gap-2`}>
          <InformationCircleIcon className="h-6 w-6 text-blue-400" />
          About System Provider Keys
        </h3>
        <div className="space-y-4">
          <div>
            <h4 className={`font-semibold ${themeClasses.text} mb-2`}>Key Sources Priority</h4>
            <ol className={`list-decimal list-inside space-y-2 ${themeClasses.subtext}`}>
              <li><strong>Database</strong> (Preferred) - Keys configured through this interface, encrypted in PostgreSQL</li>
              <li><strong>Environment</strong> (Fallback) - Keys from environment variables (.env files)</li>
              <li><strong>Not Set</strong> - Provider unavailable until configured</li>
            </ol>
          </div>
          <div>
            <h4 className={`font-semibold ${themeClasses.text} mb-2`}>When to Use Each Provider</h4>
            <ul className={`space-y-2 ${themeClasses.subtext}`}>
              <li><strong>OpenRouter</strong> ⭐ - Best for most use cases (200+ models, auto-fallback, competitive pricing)</li>
              <li><strong>OpenAI</strong> - Latest GPT-4o models, DALL-E 3, o1 reasoning models</li>
              <li><strong>Anthropic</strong> - Claude 3.5 Sonnet (best coding), 200K context window</li>
              <li><strong>Google</strong> - Gemini 2.0 Flash (fastest), 1.5 Pro (2M token context)</li>
            </ul>
          </div>
          <div>
            <h4 className={`font-semibold ${themeClasses.text} mb-2`}>Security</h4>
            <p className={themeClasses.subtext}>
              All API keys are encrypted using Fernet symmetric encryption before storage.
              Keys are never logged or transmitted in plain text. Only system administrators can view or modify these keys.
            </p>
          </div>
        </div>
      </div>

      {/* Add/Edit Key Modal */}
      <AnimatePresence>
        {showAddModal && selectedProvider && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={`rounded-xl border p-6 max-w-lg w-full m-4 ${themeClasses.modal}`}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className={`text-xl font-bold ${themeClasses.text}`}>
                  {selectedProvider.key_source === 'not_set' ? 'Add' : 'Update'} System Key - {providerInfo[selectedProvider.provider_type]?.name || selectedProvider.name}
                </h3>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setSelectedProvider(null);
                    setApiKeyInput('');
                  }}
                  className={`p-2 rounded-lg ${themeClasses.subtext} hover:bg-gray-700/30`}
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                {/* Info Alert */}
                <div className={`p-4 rounded-lg ${
                  currentTheme === 'light' ? 'bg-blue-50 border border-blue-200' : 'bg-blue-500/10 border border-blue-500/30'
                }`}>
                  <p className={`text-sm ${themeClasses.text} mb-2`}>
                    Get your {providerInfo[selectedProvider.provider_type]?.name || selectedProvider.name} API key:
                  </p>
                  <a
                    href={providerInfo[selectedProvider.provider_type]?.getKeyUrl || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-400 hover:text-blue-300 underline break-all"
                  >
                    {providerInfo[selectedProvider.provider_type]?.getKeyUrl || 'Provider website'}
                  </a>
                </div>

                {/* API Key Input */}
                <div>
                  <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                    System API Key <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="password"
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    placeholder={providerInfo[selectedProvider.provider_type]?.keyFormat || 'Enter API key'}
                    className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono`}
                  />
                  <p className={`text-xs ${themeClasses.subtext} mt-2`}>
                    🔒 Key will be encrypted with Fernet before storage
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => {
                      setShowAddModal(false);
                      setSelectedProvider(null);
                      setApiKeyInput('');
                    }}
                    className={`flex-1 px-4 py-3 rounded-lg border ${
                      currentTheme === 'light'
                        ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
                        : 'border-slate-600 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveKey}
                    disabled={!apiKeyInput.trim() || savingKey}
                    className={`flex-1 px-4 py-3 rounded-lg ${themeClasses.button} disabled:opacity-50 font-medium`}
                  >
                    {savingKey ? (
                      <span className="flex items-center justify-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Saving...
                      </span>
                    ) : (
                      'Save System Key'
                    )}
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {confirmDelete && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={`rounded-xl border p-6 max-w-md w-full m-4 ${themeClasses.modal}`}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />
                </div>
                <div>
                  <h3 className={`text-xl font-bold ${themeClasses.text}`}>Delete System Key?</h3>
                  <p className={`text-sm ${themeClasses.subtext}`}>
                    {(() => {
                      const provider = providers.find(p => p.id === confirmDelete);
                      return provider ? (providerInfo[provider.provider_type]?.name || provider.name) : 'Provider';
                    })()}
                  </p>
                </div>
              </div>

              <p className={`${themeClasses.subtext} mb-6`}>
                Delete this system API key from the database? The system will fall back to the environment variable if available.
                This does not affect user BYOK keys.
              </p>

              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmDelete(null)}
                  className={`flex-1 px-4 py-2 rounded-lg border ${
                    currentTheme === 'light'
                      ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
                      : 'border-slate-600 text-slate-300 hover:bg-slate-700'
                  }`}
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDeleteKey(confirmDelete)}
                  className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-medium"
                >
                  Delete System Key
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
