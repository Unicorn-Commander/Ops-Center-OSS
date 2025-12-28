/**
 * ProviderKeysSection Component - Reusable Provider API Key Management
 *
 * Extracted from SystemProviderKeys.jsx to be reusable across different contexts
 *
 * Features:
 * - Add, edit, delete, test API keys for multiple LLM providers
 * - Built-in providers: OpenRouter, OpenAI, Anthropic, Google, Cohere, Groq, Together AI, Mistral
 * - Custom provider support with custom URL
 * - Show/hide API key toggle
 * - Test connection functionality
 * - Collapsible section
 * - Theme-aware (unicorn, light, dark)
 *
 * Backend API (already exists):
 * - GET /api/v1/llm/admin/system-keys - List all provider keys
 * - PUT /api/v1/llm/admin/system-keys/{provider} - Add/update key
 * - DELETE /api/v1/llm/admin/system-keys/{provider} - Delete key
 * - POST /api/v1/llm/admin/system-keys/{provider}/test - Test key
 */

import React, { useState, useEffect } from 'react';
import {
  KeyIcon,
  CheckCircleIcon,
  XCircleIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function ProviderKeysSection({
  onKeysChanged,  // Callback when keys updated
  collapsible = true,  // Can collapse section
  defaultExpanded = true  // Start expanded or collapsed
}) {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [providers, setProviders] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [customProviderName, setCustomProviderName] = useState('');
  const [customProviderUrl, setCustomProviderUrl] = useState('');
  const [testingProvider, setTestingProvider] = useState(null);
  const [savingKey, setSavingKey] = useState(false);
  const [toast, setToast] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [expanded, setExpanded] = useState(defaultExpanded);

  // Theme classes with null safety
  const themeClasses = {
    card: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-white border-gray-200'
      : 'bg-slate-800 border-slate-700',
    text: theme?.text?.primary || (currentTheme === 'unicorn'
      ? 'text-purple-100'
      : currentTheme === 'light'
      ? 'text-gray-900'
      : 'text-slate-100'),
    subtext: theme?.text?.secondary || (currentTheme === 'unicorn'
      ? 'text-purple-300'
      : currentTheme === 'light'
      ? 'text-gray-600'
      : 'text-slate-400'),
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

  // Provider information (includes new providers)
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
    },
    cohere: {
      name: 'Cohere',
      icon: '🌐',
      color: 'from-pink-500 to-rose-500',
      description: 'Command R+, Command R, Embed v3, Rerank',
      getKeyUrl: 'https://dashboard.cohere.com/api-keys',
      keyFormat: 'co-...'
    },
    groq: {
      name: 'Groq',
      icon: '⚡',
      color: 'from-orange-500 to-yellow-500',
      description: 'Ultra-fast inference - Llama 3, Mixtral, Gemma (500+ tok/s)',
      getKeyUrl: 'https://console.groq.com/keys',
      keyFormat: 'gsk_...'
    },
    together: {
      name: 'Together AI',
      icon: '🤝',
      color: 'from-teal-500 to-cyan-500',
      description: 'Open source models - Llama 3, Mistral, Qwen, DeepSeek',
      getKeyUrl: 'https://api.together.xyz/settings/api-keys',
      keyFormat: 'together-...'
    },
    mistral: {
      name: 'Mistral AI',
      icon: '🌪️',
      color: 'from-indigo-500 to-purple-500',
      description: 'Mistral Large 2, Mixtral 8x7B, Codestral (code generation)',
      getKeyUrl: 'https://console.mistral.ai/api-keys',
      keyFormat: 'mistral-...'
    },
    ollama: {
      name: 'Ollama (Local)',
      icon: '🦙',
      color: 'from-green-500 to-lime-500',
      description: 'Local Ollama instance - Llama 3, Mistral, Gemma (localhost:11434)',
      getKeyUrl: 'https://ollama.com/download',
      keyFormat: 'No key needed (local)',
      customUrl: false
    },
    ollama_cloud: {
      name: 'Ollama Cloud',
      icon: '☁️',
      color: 'from-sky-500 to-blue-500',
      description: 'Ollama Cloud - Hosted models with API access',
      getKeyUrl: 'https://ollama.com/cloud',
      keyFormat: 'API key from Ollama Cloud',
      customUrl: false
    },
    custom: {
      name: 'Custom Provider',
      icon: '⚙️',
      color: 'from-gray-500 to-slate-500',
      description: 'Self-hosted or custom LLM endpoint',
      getKeyUrl: null,
      keyFormat: 'Custom API key format',
      customUrl: true
    }
  };

  useEffect(() => {
    loadProviders();
  }, []);

  const loadProviders = async () => {
    setLoading(true);
    try {
      // Add timestamp to prevent caching
      const timestamp = new Date().getTime();

      // Fetch all supported providers (including unconfigured ones)
      const providersResponse = await fetch(`/api/v1/byok/providers?_t=${timestamp}`, {
        credentials: 'include',
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });

      if (!providersResponse.ok) {
        const errorData = await providersResponse.json().catch(() => ({}));
        console.error('Failed to load providers:', providersResponse.status, errorData);
        setProviders([]);
        showToast('error', `Failed to load providers: ${errorData.detail || providersResponse.statusText}`);
        return;
      }

      const allProviders = await providersResponse.json();

      // Fetch configured keys for details (key preview, test status)
      const keysResponse = await fetch(`/api/v1/byok/keys?_t=${timestamp}`, {
        credentials: 'include',
        cache: 'no-cache',
        headers: {
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache'
        }
      });

      const configuredKeys = keysResponse.ok ? await keysResponse.json() : [];

      // Merge providers with key details
      const providersWithStatus = allProviders.map(provider => {
        const keyDetails = Array.isArray(configuredKeys)
          ? configuredKeys.find(k => k.provider === provider.id)
          : null;

        return {
          id: provider.id,
          provider_type: provider.id,
          name: provider.name,
          key_source: provider.configured ? 'database' : 'not_set',
          key_preview: keyDetails?.key_preview || null,
          last_tested: keyDetails?.last_tested || null,
          test_status: keyDetails?.test_status || null,
          configured: provider.configured
        };
      });

      setProviders(providersWithStatus);
    } catch (error) {
      console.error('Error loading providers:', error);
      setProviders([]);
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
    if (!selectedProvider) {
      showToast('error', 'Please select a provider');
      return;
    }

    // For custom provider, validate custom fields
    if (selectedProvider.id === 'custom') {
      if (!customProviderName.trim()) {
        showToast('error', 'Please enter a custom provider name');
        return;
      }
      if (!customProviderUrl.trim()) {
        showToast('error', 'Please enter a custom API URL');
        return;
      }
    }

    if (!apiKeyInput.trim()) {
      showToast('error', 'Please enter an API key');
      return;
    }

    setSavingKey(true);
    try {
      const requestBody = {
        provider: selectedProvider.id,
        key: apiKeyInput.trim()
      };

      // Add custom provider fields if applicable
      if (selectedProvider.id === 'custom') {
        requestBody.label = customProviderName.trim();
        requestBody.endpoint = customProviderUrl.trim();
      }

      const response = await fetch(`/api/v1/byok/keys/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(requestBody)
      });

      if (response.ok) {
        const providerName = selectedProvider.id === 'custom'
          ? customProviderName.trim()
          : (providerInfo[selectedProvider.provider_type]?.name || selectedProvider.name);

        showToast('success', `${providerName} key updated successfully!`);
        setShowAddModal(false);
        setSelectedProvider(null);
        setApiKeyInput('');
        setCustomProviderName('');
        setCustomProviderUrl('');
        await loadProviders();

        // Notify parent component
        if (onKeysChanged) {
          onKeysChanged();
        }
      } else {
        const error = await response.json();
        showToast('error', error.detail || 'Failed to save key');
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
      const response = await fetch(`/api/v1/byok/keys/test/${providerId}`, {
        method: 'POST',
        credentials: 'include'
      });

      const result = await response.json();

      if (response.ok && result.success) {
        showToast('success', result.message || `${result.provider_name || 'Provider'} key is valid!`);
        await loadProviders();
      } else {
        showToast('error', result.message || 'Key validation failed');
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
      const provider = providers.find(p => p.id === providerId);
      const providerName = provider ? (providerInfo[provider.provider_type]?.name || provider.name) : 'Provider';

      const response = await fetch(`/api/v1/byok/keys/${providerId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        showToast('info', `${providerName} key deleted. Will use environment fallback.`);
        setConfirmDelete(null);
        await loadProviders();

        // Notify parent component
        if (onKeysChanged) {
          onKeysChanged();
        }
      } else {
        showToast('error', 'Failed to delete key');
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
      <div className={`flex items-center justify-center py-8 ${themeClasses.text}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-current mx-auto mb-4"></div>
          <p className="text-sm">Loading provider keys...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Section Header (collapsible) */}
      {collapsible ? (
        <div
          onClick={() => setExpanded(!expanded)}
          className={`flex items-center justify-between cursor-pointer ${themeClasses.card} rounded-lg border p-4 hover:bg-opacity-80 transition-colors`}
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <KeyIcon className="h-6 w-6 text-purple-400" />
            </div>
            <div>
              <h3 className={`text-lg font-semibold ${themeClasses.text}`}>Provider API Keys</h3>
              <p className={`text-sm ${themeClasses.subtext}`}>
                {Array.isArray(providers) ? providers.filter(p => p.key_source !== 'not_set').length : 0} providers configured
              </p>
            </div>
          </div>
          {expanded ? (
            <ChevronUpIcon className={`h-5 w-5 ${themeClasses.subtext}`} />
          ) : (
            <ChevronDownIcon className={`h-5 w-5 ${themeClasses.subtext}`} />
          )}
        </div>
      ) : (
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
            <KeyIcon className="h-6 w-6 text-purple-400" />
          </div>
          <div>
            <h3 className={`text-lg font-semibold ${themeClasses.text}`}>Provider API Keys</h3>
            <p className={`text-sm ${themeClasses.subtext}`}>
              Configure LLM provider credentials
            </p>
          </div>
        </div>
      )}

      {/* Collapsible Content */}
      {(!collapsible || expanded) && (
        <>
          {/* Toast Notification */}
          {toast && (
            <div
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
            </div>
          )}

          {/* Provider Cards Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Array.isArray(providers) && providers.length > 0 ? providers.map((provider) => {
              const info = providerInfo[provider.id] || {
                name: provider.id,
                icon: '🔑',
                color: 'from-gray-500 to-gray-600',
                description: 'LLM Provider'
              };

              return (
                <div
                  key={provider.id}
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
                </div>
              );
            }) : (
              <div className={`col-span-2 text-center py-8 ${themeClasses.card} rounded-lg border`}>
                <p className={themeClasses.subtext}>No providers found. Please check your configuration.</p>
              </div>
            )}
          </div>

          {/* Info Section */}
          <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
            <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4 flex items-center gap-2`}>
              <InformationCircleIcon className="h-6 w-6 text-blue-400" />
              About Provider Keys
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
                <h4 className={`font-semibold ${themeClasses.text} mb-2`}>Security</h4>
                <p className={themeClasses.subtext}>
                  All API keys are encrypted using Fernet symmetric encryption before storage.
                  Keys are never logged or transmitted in plain text.
                </p>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Add/Edit Key Modal */}
      {showAddModal && selectedProvider && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className={`rounded-xl border p-6 max-w-lg w-full m-4 ${themeClasses.modal}`}>
            <div className="flex items-center justify-between mb-6">
              <h3 className={`text-xl font-bold ${themeClasses.text}`}>
                {selectedProvider.key_source === 'not_set' ? 'Add' : 'Update'} Key - {providerInfo[selectedProvider.provider_type]?.name || selectedProvider.name}
              </h3>
              <button
                onClick={() => {
                  setShowAddModal(false);
                  setSelectedProvider(null);
                  setApiKeyInput('');
                  setCustomProviderName('');
                  setCustomProviderUrl('');
                }}
                className={`p-2 rounded-lg ${themeClasses.subtext} hover:bg-gray-700/30`}
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="space-y-4">
              {/* Info Alert */}
              {providerInfo[selectedProvider.provider_type]?.getKeyUrl && (
                <div className={`p-4 rounded-lg ${
                  currentTheme === 'light' ? 'bg-blue-50 border border-blue-200' : 'bg-blue-500/10 border border-blue-500/30'
                }`}>
                  <p className={`text-sm ${themeClasses.text} mb-2`}>
                    Get your {providerInfo[selectedProvider.provider_type]?.name || selectedProvider.name} API key:
                  </p>
                  <a
                    href={providerInfo[selectedProvider.provider_type]?.getKeyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-blue-400 hover:text-blue-300 underline break-all"
                  >
                    {providerInfo[selectedProvider.provider_type]?.getKeyUrl}
                  </a>
                </div>
              )}

              {/* Custom Provider Fields */}
              {selectedProvider.id === 'custom' && (
                <>
                  <div>
                    <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                      Provider Name <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="text"
                      value={customProviderName}
                      onChange={(e) => setCustomProviderName(e.target.value)}
                      placeholder="My Custom LLM Provider"
                      className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                      API Base URL <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="url"
                      value={customProviderUrl}
                      onChange={(e) => setCustomProviderUrl(e.target.value)}
                      placeholder="https://api.example.com/v1"
                      className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono text-sm`}
                    />
                    <p className={`text-xs ${themeClasses.subtext} mt-2`}>
                      Enter the base URL for your custom LLM provider
                    </p>
                  </div>
                </>
              )}

              {/* API Key Input */}
              <div>
                <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                  API Key <span className="text-red-400">*</span>
                </label>
                <div className="relative">
                  <input
                    type={showApiKey ? 'text' : 'password'}
                    value={apiKeyInput}
                    onChange={(e) => setApiKeyInput(e.target.value)}
                    placeholder={providerInfo[selectedProvider.provider_type]?.keyFormat || 'Enter API key'}
                    className={`w-full px-4 py-3 pr-12 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowApiKey(!showApiKey)}
                    className={`absolute right-3 top-1/2 -translate-y-1/2 ${themeClasses.subtext} hover:text-purple-400`}
                  >
                    {showApiKey ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </button>
                </div>
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
                    setCustomProviderName('');
                    setCustomProviderUrl('');
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
                  disabled={!apiKeyInput.trim() || savingKey || (selectedProvider.id === 'custom' && (!customProviderName.trim() || !customProviderUrl.trim()))}
                  className={`flex-1 px-4 py-3 rounded-lg ${themeClasses.button} disabled:opacity-50 font-medium`}
                >
                  {savingKey ? (
                    <span className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Saving...
                    </span>
                  ) : (
                    'Save Key'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {confirmDelete && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className={`rounded-xl border p-6 max-w-md w-full m-4 ${themeClasses.modal}`}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />
              </div>
              <div>
                <h3 className={`text-xl font-bold ${themeClasses.text}`}>Delete Key?</h3>
                <p className={`text-sm ${themeClasses.subtext}`}>
                  {(() => {
                    const provider = providers.find(p => p.id === confirmDelete);
                    return provider ? (providerInfo[provider.provider_type]?.name || provider.name) : 'Provider';
                  })()}
                </p>
              </div>
            </div>

            <p className={`${themeClasses.subtext} mb-6`}>
              Delete this API key from the database? The system will fall back to the environment variable if available.
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
                Delete Key
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
