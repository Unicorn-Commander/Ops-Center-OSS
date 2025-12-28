/**
 * AccountAPIKeys Component - BYOK (Bring Your Own Key) Management
 *
 * Comprehensive API key management for users to bring their own provider keys
 * - OpenRouter (recommended - 348 models)
 * - OpenAI (direct API access)
 * - Anthropic (Claude models)
 * - Google (Gemini models)
 * - Plus 4 more providers
 *
 * Backend: /api/v1/byok/* (Keycloak user attributes + Fernet encryption)
 * Storage: Encrypted in Keycloak user attributes (no database)
 */

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  KeyIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ShieldCheckIcon,
  ServerIcon,
  SparklesIcon,
  CurrencyDollarIcon,
  LockClosedIcon,
  BoltIcon,
  UserGroupIcon,
  XMarkIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  ClipboardDocumentIcon,
  CodeBracketIcon,
  PencilIcon,
  BeakerIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

export default function AccountAPIKeys() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [byokKeys, setBYOKKeys] = useState([]);
  const [providers, setProviders] = useState([]);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [labelInput, setLabelInput] = useState('');
  const [testingProvider, setTestingProvider] = useState(null);
  const [savingKey, setSavingKey] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState({});
  const [toast, setToast] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [stats, setStats] = useState(null);

  // UC API Keys state
  const [ucApiKeys, setUcApiKeys] = useState([]);
  const [loadingUcKeys, setLoadingUcKeys] = useState(false);
  const [showCodeSnippet, setShowCodeSnippet] = useState(false);

  // Platform keys state (admin only)
  const [platformKeys, setPlatformKeys] = useState(null);
  const [loadingPlatformKeys, setLoadingPlatformKeys] = useState(false);
  const [editingPlatformKey, setEditingPlatformKey] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);

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

  // Provider information with benefits
  const providerInfo = {
    openrouter: {
      name: 'OpenRouter',
      icon: '🔀',
      color: 'from-blue-500 to-cyan-500',
      models: 348,
      recommended: true,
      benefits: [
        'Access to 348+ models from all providers',
        'Automatic fallback and load balancing',
        'Often 50-70% cheaper than direct APIs',
        'Single API key for everything'
      ],
      getKeyUrl: 'https://openrouter.ai/keys',
      keyFormat: 'sk-or-v1-...',
      description: 'Universal proxy for all LLM providers'
    },
    openai: {
      name: 'OpenAI',
      icon: '🤖',
      color: 'from-green-500 to-emerald-500',
      models: 15,
      benefits: [
        'Direct access to GPT-4, GPT-4 Turbo',
        'Access to o1 reasoning models',
        'DALL-E image generation',
        'Whisper and TTS models'
      ],
      getKeyUrl: 'https://platform.openai.com/api-keys',
      keyFormat: 'sk-proj-...',
      description: 'GPT-4, o1, DALL-E, Whisper'
    },
    anthropic: {
      name: 'Anthropic',
      icon: '🧠',
      color: 'from-purple-500 to-pink-500',
      models: 8,
      benefits: [
        'Direct access to Claude 3.5 Sonnet',
        'Claude 3 Opus for complex tasks',
        'Claude 3 Haiku for speed',
        '200K context window'
      ],
      getKeyUrl: 'https://console.anthropic.com/settings/keys',
      keyFormat: 'sk-ant-...',
      description: 'Claude 3.5 Sonnet, Opus, Haiku'
    },
    google: {
      name: 'Google AI',
      icon: '🔍',
      color: 'from-red-500 to-orange-500',
      models: 5,
      benefits: [
        'Gemini 1.5 Pro and Flash',
        'Generous free tier',
        'Multimodal capabilities',
        '1M token context (Pro)'
      ],
      getKeyUrl: 'https://makersuite.google.com/app/apikey',
      keyFormat: 'AIza...',
      description: 'Gemini 1.5 Pro and Flash'
    },
    cohere: {
      name: 'Cohere',
      icon: '💬',
      color: 'from-violet-500 to-purple-500',
      models: 6,
      benefits: [
        'Command R+ for RAG',
        'Excellent embeddings',
        'Specialized for enterprise',
        'Strong multilingual support'
      ],
      getKeyUrl: 'https://dashboard.cohere.com/api-keys',
      keyFormat: 'co-...',
      description: 'Command R+, enterprise embeddings'
    },
    together: {
      name: 'Together AI',
      icon: '🚀',
      color: 'from-cyan-500 to-blue-500',
      models: 50,
      benefits: [
        'Open-source model hosting',
        'Llama 3, Mixtral, Qwen',
        'Fast inference',
        'Cost-effective'
      ],
      getKeyUrl: 'https://api.together.xyz/settings/api-keys',
      keyFormat: 'together_...',
      description: 'Open-source models (Llama, Mixtral)'
    },
    groq: {
      name: 'Groq',
      icon: '⚡',
      color: 'from-yellow-500 to-orange-500',
      models: 8,
      benefits: [
        'Fastest inference in the world',
        'Llama 3, Mixtral, Gemma',
        'Free tier available',
        'Ultra-low latency'
      ],
      getKeyUrl: 'https://console.groq.com/keys',
      keyFormat: 'gsk_...',
      description: 'Ultra-fast inference for open models'
    },
    perplexity: {
      name: 'Perplexity AI',
      icon: '🔎',
      color: 'from-indigo-500 to-purple-500',
      models: 4,
      benefits: [
        'Perplexity Sonar models',
        'Built-in web search',
        'Citation support',
        'Real-time information'
      ],
      getKeyUrl: 'https://www.perplexity.ai/settings/api',
      keyFormat: 'pplx-...',
      description: 'AI search with citations'
    },
    unicorncommander: {
      name: 'Unicorn Commander',
      icon: '🦄',
      color: 'from-purple-500 to-pink-500',
      models: 100,
      recommended: false,
      benefits: [
        'Access to 100+ LLM models',
        'Centralized billing and usage tracking',
        'OpenAI-compatible API',
        'Perfect for multi-server deployments'
      ],
      getKeyUrl: 'https://your-domain.com/admin/account/api-keys',
      keyFormat: 'uc_sk_...',
      description: 'Unicorn Commander API (this platform or remote instance)'
    },
    ollama: {
      name: 'Ollama',
      icon: '🏠',
      color: 'from-gray-700 to-gray-900',
      models: 50,
      benefits: [
        'Run models locally on your hardware',
        'Privacy-first (no data leaves your machine)',
        'Free and open source',
        'Supports Llama, Mistral, Gemma, etc.'
      ],
      getKeyUrl: 'http://localhost:11434 (no key needed)',
      keyFormat: 'Not required',
      description: 'Local model hosting'
    },
    ollamacloud: {
      name: 'Ollama Cloud',
      icon: '☁️',
      color: 'from-sky-500 to-blue-600',
      models: 50,
      benefits: [
        'Hosted Ollama models in the cloud',
        'No local GPU required',
        'Same API as local Ollama',
        'Managed infrastructure'
      ],
      getKeyUrl: 'https://ollama.com/cloud/keys',
      keyFormat: 'ollama-...',
      description: 'Hosted Ollama service'
    },
    huggingface: {
      name: 'Hugging Face',
      icon: '🤗',
      color: 'from-yellow-500 to-amber-600',
      models: 1000,
      benefits: [
        'Access to 1000+ open-source models',
        'Model inference API',
        'Free tier available',
        'Cutting-edge research models'
      ],
      getKeyUrl: 'https://huggingface.co/settings/tokens',
      keyFormat: 'hf_...',
      description: 'Open-source model hub'
    },
    custom: {
      name: 'Custom OpenAI-Compatible',
      icon: '⚙️',
      color: 'from-slate-500 to-zinc-600',
      models: null,
      benefits: [
        'Connect to any OpenAI-compatible API',
        'Use with vLLM, LocalAI, text-generation-webui',
        'Self-hosted or third-party endpoints',
        'Full control over your infrastructure'
      ],
      getKeyUrl: 'Your custom endpoint',
      keyFormat: 'Depends on your API',
      description: 'Custom OpenAI-compatible endpoint'
    }
  };

  useEffect(() => {
    loadData();
    loadUcApiKeys();
    checkAdminRole();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadProviders(),
        loadKeys(),
        loadStats()
      ]);
    } catch (error) {
      console.error('Error loading BYOK data:', error);
      showToast('error', 'Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  const checkAdminRole = async () => {
    try {
      const response = await fetch('/api/v1/auth/user', {
        credentials: 'include'
      });
      if (response.ok) {
        const user = await response.json();
        const roles = user.roles || [];
        setIsAdmin(roles.includes('admin'));
        if (roles.includes('admin')) {
          loadPlatformKeys();
        }
      }
    } catch (error) {
      console.error('Error checking admin role:', error);
    }
  };

  const loadUcApiKeys = async () => {
    setLoadingUcKeys(true);
    try {
      const response = await fetch('/api/v1/account/uc-api-keys', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setUcApiKeys(data);
      }
    } catch (error) {
      console.error('Error loading UC API keys:', error);
    } finally {
      setLoadingUcKeys(false);
    }
  };

  const handleGenerateUcKey = async () => {
    setLoadingUcKeys(true);
    try {
      const response = await fetch('/api/v1/account/uc-api-keys', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name: 'API Key ' + new Date().toLocaleDateString()
        })
      });
      if (response.ok) {
        const data = await response.json();
        showToast('success', 'API key generated successfully!');
        // Show the full key in an alert since it won't be shown again
        if (data.key) {
          alert(`Your new API key (copy it now!):\n\n${data.key}\n\nThis is the only time you'll see the full key.`);
        }
        await loadUcApiKeys();
      } else {
        showToast('error', 'Failed to generate API key');
      }
    } catch (error) {
      console.error('Error generating UC API key:', error);
      showToast('error', 'Failed to generate API key');
    } finally {
      setLoadingUcKeys(false);
    }
  };

  const loadPlatformKeys = async () => {
    setLoadingPlatformKeys(true);
    try {
      const response = await fetch('/api/v1/admin/platform-keys', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setPlatformKeys(data);
      }
    } catch (error) {
      console.error('Error loading platform keys:', error);
    } finally {
      setLoadingPlatformKeys(false);
    }
  };

  const loadProviders = async () => {
    try {
      const response = await fetch('/api/v1/byok/providers', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setProviders(data);
      }
    } catch (error) {
      console.error('Error loading providers:', error);
    }
  };

  const loadKeys = async () => {
    try {
      const response = await fetch('/api/v1/byok/keys', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setBYOKKeys(data);
      }
    } catch (error) {
      console.error('Error loading keys:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await fetch('/api/v1/byok/stats', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const showToast = (type, message) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 4000);
  };

  const handleAddKey = async () => {
    if (!selectedProvider || !apiKeyInput.trim()) {
      showToast('error', 'Please select a provider and enter an API key');
      return;
    }

    setSavingKey(true);
    try {
      const response = await fetch('/api/v1/byok/keys/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          provider: selectedProvider,
          key: apiKeyInput.trim(),
          label: labelInput.trim() || null
        })
      });

      if (response.ok) {
        showToast('success', `${providerInfo[selectedProvider].name} API key added successfully!`);
        setShowAddModal(false);
        setSelectedProvider(null);
        setApiKeyInput('');
        setLabelInput('');
        await loadData();
      } else {
        const error = await response.json();
        showToast('error', error.detail || 'Failed to add API key');
      }
    } catch (error) {
      console.error('Error adding key:', error);
      showToast('error', 'Network error. Please try again.');
    } finally {
      setSavingKey(false);
    }
  };

  const handleTestKey = async (provider) => {
    setTestingProvider(provider);
    try {
      const response = await fetch(`/api/v1/byok/keys/test/${provider}`, {
        method: 'POST',
        credentials: 'include'
      });

      const result = await response.json();

      if (response.ok && result.status === 'valid') {
        showToast('success', `${providerInfo[provider].name} API key is valid!`);
        await loadKeys(); // Reload to update test status
      } else {
        showToast('error', result.message || 'API key validation failed');
      }
    } catch (error) {
      console.error('Error testing key:', error);
      showToast('error', 'Network error during test');
    } finally {
      setTestingProvider(null);
    }
  };

  const handleDeleteKey = async (provider) => {
    try {
      const response = await fetch(`/api/v1/byok/keys/${provider}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        showToast('success', `${providerInfo[provider].name} API key removed`);
        setConfirmDelete(null);
        await loadData();
      } else {
        showToast('error', 'Failed to remove API key');
      }
    } catch (error) {
      console.error('Error deleting key:', error);
      showToast('error', 'Network error. Please try again.');
    }
  };

  const toggleKeyVisibility = (provider) => {
    setVisibleKeys(prev => ({ ...prev, [provider]: !prev[provider] }));
  };

  const getProviderStatus = (providerId) => {
    return byokKeys.find(k => k.provider === providerId);
  };

  const handleRegenerateUcKey = async (keyId) => {
    try {
      const response = await fetch(`/api/v1/account/uc-api-keys/${keyId}/regenerate`, {
        method: 'POST',
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        if (data.key) {
          alert(`Your regenerated API key (copy it now!):\n\n${data.key}\n\nThis is the only time you'll see the full key.`);
        }
        showToast('success', 'API key regenerated successfully');
        await loadUcApiKeys();
      } else {
        showToast('error', 'Failed to regenerate API key');
      }
    } catch (error) {
      console.error('Error regenerating UC API key:', error);
      showToast('error', 'Network error. Please try again.');
    }
  };

  const handleCopyToClipboard = (text, label = 'API key') => {
    navigator.clipboard.writeText(text);
    showToast('success', `${label} copied to clipboard!`);
  };

  const handleTestPlatformKey = async (keyType) => {
    try {
      const response = await fetch(`/api/v1/admin/platform-keys/${keyType}/test`, {
        method: 'POST',
        credentials: 'include'
      });
      const result = await response.json();
      if (response.ok && result.valid) {
        showToast('success', `${keyType} key is valid!`);
      } else {
        showToast('error', result.message || 'Key validation failed');
      }
    } catch (error) {
      console.error('Error testing platform key:', error);
      showToast('error', 'Network error during test');
    }
  };

  const getCodeSnippet = (apiKey) => {
    return {
      python: `import requests

# Unicorn Commander API
BASE_URL = "https://api.your-domain.com"
API_KEY = "${apiKey}"

# Example: Chat completion
response = requests.post(
    f"{BASE_URL}/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello!"}]
    }
)
print(response.json())`,
      javascript: `// Unicorn Commander API
const BASE_URL = "https://api.your-domain.com";
const API_KEY = "${apiKey}";

// Example: Chat completion
fetch(\`\${BASE_URL}/v1/chat/completions\`, {
  method: "POST",
  headers: {
    "Authorization": \`Bearer \${API_KEY}\`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    model: "gpt-4",
    messages: [{role: "user", content: "Hello!"}]
  })
})
.then(res => res.json())
.then(data => console.log(data));`
    };
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${themeClasses.text}`}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-current mx-auto mb-4"></div>
          <p>Loading BYOK configuration...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${themeClasses.text}`}>API Keys (BYOK)</h1>
          <p className={`mt-2 ${themeClasses.subtext}`}>
            Bring Your Own Key - Use your API keys for LLM providers
          </p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${themeClasses.button} shadow-lg`}
        >
          <PlusIcon className="h-5 w-5" />
          Add API Key
        </button>
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
                : 'bg-red-500/20 border border-red-500/50'
            }`}
          >
            <div className="flex items-center gap-2">
              {toast.type === 'success' ? (
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
              ) : (
                <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
              )}
              <span className={toast.type === 'success' ? 'text-green-400' : 'text-red-400'}>
                {toast.message}
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* UC API Keys Section */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className={`text-2xl font-bold ${themeClasses.text} flex items-center gap-2`}>
              <KeyIcon className="h-6 w-6" />
              Your Unicorn Commander API Keys
            </h2>
            <p className={`mt-2 ${themeClasses.subtext}`}>
              Use these keys to call our API from other systems
            </p>
          </div>
        </div>

        {loadingUcKeys ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-current mx-auto"></div>
          </div>
        ) : (
          <>
            {/* Base URL - Always show */}
            <div className={`rounded-lg border p-4 mb-4 ${currentTheme === 'light' ? 'bg-blue-50 border-blue-200' : 'bg-blue-500/10 border-blue-500/30'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm font-medium ${themeClasses.text} mb-1`}>Base URL:</p>
                  <code className={`text-sm ${themeClasses.text} font-mono`}>https://api.your-domain.com</code>
                </div>
                <button
                  onClick={() => handleCopyToClipboard('https://api.your-domain.com', 'Base URL')}
                  className={`p-2 rounded-lg ${themeClasses.subtext} hover:bg-gray-700/30`}
                >
                  <ClipboardDocumentIcon className="h-5 w-5" />
                </button>
              </div>
            </div>

            {ucApiKeys.length === 0 ? (
              <div className={`rounded-lg border-2 border-dashed p-8 text-center ${themeClasses.card}`}>
                <KeyIcon className={`h-12 w-12 mx-auto mb-3 ${themeClasses.subtext}`} />
                <p className={`${themeClasses.subtext} mb-4`}>No API keys yet. Generate your first key to get started.</p>
                <button
                  onClick={handleGenerateUcKey}
                  disabled={loadingUcKeys}
                  className={`px-4 py-2 rounded-lg ${themeClasses.button} flex items-center gap-2 mx-auto`}
                >
                  {loadingUcKeys ? (
                    <ArrowPathIcon className="h-5 w-5 animate-spin" />
                  ) : (
                    <PlusIcon className="h-5 w-5" />
                  )}
                  Generate API Key
                </button>
              </div>
            ) : (
          <div className="space-y-4">
            {/* API Keys List */}
            {ucApiKeys.map((key) => (
              <div key={key.id} className={`rounded-lg border p-4 ${currentTheme === 'light' ? 'bg-gray-50 border-gray-200' : 'bg-gray-800/30 border-gray-700'}`}>
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-sm font-medium ${themeClasses.text}`}>API Key:</span>
                      <code className={`text-sm ${themeClasses.text} font-mono`}>
                        {key.key_preview || 'uc_sk_••••••••••••••••'}
                      </code>
                    </div>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className={`${themeClasses.subtext}`}>Created:</span>
                        <span className={`ml-2 ${themeClasses.text}`}>
                          {key.created_at ? new Date(key.created_at).toLocaleDateString() : 'Nov 3, 2025'}
                        </span>
                      </div>
                      <div>
                        <span className={`${themeClasses.subtext}`}>Last Used:</span>
                        <span className={`ml-2 ${themeClasses.text}`}>
                          {key.last_used ? new Date(key.last_used).toLocaleDateString() : 'Never'}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleCopyToClipboard(key.key || 'uc_sk_example', 'API key')}
                      className={`p-2 rounded-lg ${themeClasses.button} text-sm`}
                      title="Copy API key"
                    >
                      <ClipboardDocumentIcon className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleRegenerateUcKey(key.id)}
                      className="p-2 rounded-lg border border-orange-500/50 text-orange-400 hover:bg-orange-500/10 text-sm"
                      title="Regenerate key"
                    >
                      <ArrowPathIcon className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {/* Quick Start Code Snippet */}
                <button
                  onClick={() => setShowCodeSnippet(showCodeSnippet === key.id ? null : key.id)}
                  className={`flex items-center gap-2 text-sm ${themeClasses.subtext} hover:${themeClasses.text}`}
                >
                  <CodeBracketIcon className="h-4 w-4" />
                  {showCodeSnippet === key.id ? 'Hide' : 'Show'} Quick Start
                </button>

                {showCodeSnippet === key.id && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4"
                  >
                    <div className="space-y-3">
                      {/* Python Example */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs font-semibold ${themeClasses.text}`}>Python</span>
                          <button
                            onClick={() => handleCopyToClipboard(getCodeSnippet(key.key || 'uc_sk_your_key_here').python, 'Python code')}
                            className={`text-xs ${themeClasses.subtext} hover:${themeClasses.text}`}
                          >
                            Copy
                          </button>
                        </div>
                        <pre className={`text-xs p-3 rounded-lg overflow-x-auto ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-900'}`}>
                          <code className={themeClasses.text}>{getCodeSnippet(key.key || 'uc_sk_your_key_here').python}</code>
                        </pre>
                      </div>

                      {/* JavaScript Example */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <span className={`text-xs font-semibold ${themeClasses.text}`}>JavaScript</span>
                          <button
                            onClick={() => handleCopyToClipboard(getCodeSnippet(key.key || 'uc_sk_your_key_here').javascript, 'JavaScript code')}
                            className={`text-xs ${themeClasses.subtext} hover:${themeClasses.text}`}
                          >
                            Copy
                          </button>
                        </div>
                        <pre className={`text-xs p-3 rounded-lg overflow-x-auto ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-900'}`}>
                          <code className={themeClasses.text}>{getCodeSnippet(key.key || 'uc_sk_your_key_here').javascript}</code>
                        </pre>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            ))}
          </div>
          )}
          </>
        )}
      </div>

      {/* Benefits Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className={`rounded-xl border p-4 ${themeClasses.card}`}>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
              <CurrencyDollarIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className={`font-semibold ${themeClasses.text}`}>No Credit Charges</h3>
              <p className={`text-xs ${themeClasses.subtext}`}>Use your own API keys</p>
            </div>
          </div>
        </div>

        <div className={`rounded-xl border p-4 ${themeClasses.card}`}>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-violet-500 rounded-lg flex items-center justify-center">
              <LockClosedIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className={`font-semibold ${themeClasses.text}`}>Secure Storage</h3>
              <p className={`text-xs ${themeClasses.subtext}`}>Fernet encrypted at rest</p>
            </div>
          </div>
        </div>

        <div className={`rounded-xl border p-4 ${themeClasses.card}`}>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <BoltIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className={`font-semibold ${themeClasses.text}`}>Universal Proxy</h3>
              <p className={`text-xs ${themeClasses.subtext}`}>OpenRouter = 348 models</p>
            </div>
          </div>
        </div>

        <div className={`rounded-xl border p-4 ${themeClasses.card}`}>
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
              <UserGroupIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h3 className={`font-semibold ${themeClasses.text}`}>Organization Shared</h3>
              <p className={`text-xs ${themeClasses.subtext}`}>Enterprise feature (soon)</p>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Card */}
      {stats && (
        <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>Your BYOK Status</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <p className={`text-2xl font-bold ${themeClasses.text}`}>{stats.configured_providers}</p>
              <p className={`text-sm ${themeClasses.subtext}`}>Configured Providers</p>
            </div>
            <div>
              <p className={`text-2xl font-bold ${themeClasses.text}`}>{stats.tested_providers}</p>
              <p className={`text-sm ${themeClasses.subtext}`}>Tested</p>
            </div>
            <div>
              <p className={`text-2xl font-bold ${themeClasses.text}`}>{stats.valid_providers}</p>
              <p className={`text-sm ${themeClasses.subtext}`}>Valid Keys</p>
            </div>
            <div>
              <p className={`text-2xl font-bold ${themeClasses.text}`}>{stats.total_providers}</p>
              <p className={`text-sm ${themeClasses.subtext}`}>Available Providers</p>
            </div>
          </div>
        </div>
      )}

      {/* Provider Cards */}
      <div>
        <h2 className={`text-2xl font-bold ${themeClasses.text} mb-4`}>Providers</h2>

        {byokKeys.length === 0 ? (
          /* Empty State */
          <div className={`rounded-xl border-2 border-dashed p-12 text-center ${themeClasses.card}`}>
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-violet-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <KeyIcon className="h-10 w-10 text-white" />
            </div>
            <h3 className={`text-xl font-semibold ${themeClasses.text} mb-2`}>No API Keys Added Yet</h3>
            <p className={`${themeClasses.subtext} mb-4 max-w-md mx-auto`}>
              Add your first API key to start using BYOK. We recommend starting with OpenRouter for access to all 348 models.
            </p>
            <button
              onClick={() => {
                setSelectedProvider('openrouter');
                setShowAddModal(true);
              }}
              className={`px-6 py-3 rounded-lg ${themeClasses.button} font-medium shadow-lg`}
            >
              Add OpenRouter Key (Recommended)
            </button>
          </div>
        ) : (
          /* Provider Grid */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {Object.entries(providerInfo).map(([providerId, info]) => {
              const status = getProviderStatus(providerId);
              const isConnected = !!status;

              return (
                <motion.div
                  key={providerId}
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

                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className={`w-12 h-12 bg-gradient-to-br ${info.color} rounded-lg flex items-center justify-center text-2xl`}>
                        {info.icon}
                      </div>
                      <div>
                        <h3 className={`font-semibold ${themeClasses.text}`}>{info.name}</h3>
                        <p className={`text-sm ${themeClasses.subtext}`}>{info.description}</p>
                        <p className={`text-xs ${themeClasses.subtext} mt-1`}>{info.models} models available</p>
                      </div>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-semibold ${
                      isConnected
                        ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                        : 'bg-gray-500/20 text-gray-400 border border-gray-500/30'
                    }`}>
                      {isConnected ? 'Connected' : 'Not Connected'}
                    </div>
                  </div>

                  {/* Benefits List */}
                  <ul className={`space-y-1 mb-4 text-sm ${themeClasses.subtext}`}>
                    {info.benefits.map((benefit, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <CheckCircleIcon className="h-4 w-4 text-green-400 flex-shrink-0 mt-0.5" />
                        <span>{benefit}</span>
                      </li>
                    ))}
                  </ul>

                  {/* Connected Key Display */}
                  {isConnected && status && (
                    <div className={`rounded-lg border p-3 mb-4 ${
                      currentTheme === 'light' ? 'bg-gray-50 border-gray-200' : 'bg-gray-800/30 border-gray-700'
                    }`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-xs font-medium ${themeClasses.subtext}`}>API Key:</span>
                        <button
                          onClick={() => toggleKeyVisibility(providerId)}
                          className={`p-1 rounded ${themeClasses.subtext} hover:bg-gray-700/30`}
                        >
                          {visibleKeys[providerId] ? (
                            <EyeSlashIcon className="h-4 w-4" />
                          ) : (
                            <EyeIcon className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                      <code className={`text-xs ${themeClasses.text} font-mono block`}>
                        {visibleKeys[providerId] ? '(decrypted view not available for security)' : status.key_preview}
                      </code>
                      {status.last_tested && (
                        <p className={`text-xs ${themeClasses.subtext} mt-2`}>
                          Last tested: {new Date(status.last_tested).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-2">
                    {isConnected ? (
                      <>
                        <button
                          onClick={() => handleTestKey(providerId)}
                          disabled={testingProvider === providerId}
                          className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg ${themeClasses.button} disabled:opacity-50`}
                        >
                          {testingProvider === providerId ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              Testing...
                            </>
                          ) : (
                            <>
                              <CheckCircleIcon className="h-4 w-4" />
                              Test Connection
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => setConfirmDelete(providerId)}
                          className="px-4 py-2 rounded-lg border border-red-500/50 text-red-400 hover:bg-red-500/10"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => {
                          setSelectedProvider(providerId);
                          setShowAddModal(true);
                        }}
                        className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg ${themeClasses.button}`}
                      >
                        <PlusIcon className="h-4 w-4" />
                        Add Key
                      </button>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>

      {/* What is BYOK? Section */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4 flex items-center gap-2`}>
          <InformationCircleIcon className="h-6 w-6 text-blue-400" />
          What is BYOK?
        </h3>
        <div className="space-y-4">
          <div>
            <h4 className={`font-semibold ${themeClasses.text} mb-2`}>How it Saves Money</h4>
            <p className={`${themeClasses.subtext}`}>
              When you use your own API keys, you pay providers directly at their rates. For example:
              OpenRouter charges ~$0.002/1K tokens vs our bundled rate of $0.005/1K tokens - that's 60% savings!
              Plus, you avoid our platform fees entirely.
            </p>
          </div>
          <div>
            <h4 className={`font-semibold ${themeClasses.text} mb-2`}>Security Guarantees</h4>
            <p className={`${themeClasses.subtext}`}>
              All API keys are encrypted using Fernet symmetric encryption with 256-bit keys. Keys are stored
              in your Keycloak user profile (not in our database) and are never logged or transmitted in plain text.
              Only you can decrypt and use your keys.
            </p>
          </div>
          <div>
            <h4 className={`font-semibold ${themeClasses.text} mb-2`}>Getting Started</h4>
            <ol className={`list-decimal list-inside space-y-2 ${themeClasses.subtext}`}>
              <li>Click "Add API Key" and choose a provider (we recommend OpenRouter first)</li>
              <li>Get your API key from the provider's website (click the provider card for link)</li>
              <li>Paste your key and test the connection</li>
              <li>Start using Brigade, Open-WebUI, and other services with your own keys!</li>
            </ol>
          </div>
        </div>
      </div>

      {/* Add Key Modal */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className={`rounded-xl border p-6 max-w-lg w-full m-4 ${themeClasses.modal}`}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className={`text-xl font-bold ${themeClasses.text}`}>
                  Add API Key - {selectedProvider && providerInfo[selectedProvider]?.name}
                </h3>
                <button
                  onClick={() => {
                    setShowAddModal(false);
                    setSelectedProvider(null);
                    setApiKeyInput('');
                    setLabelInput('');
                  }}
                  className={`p-2 rounded-lg ${themeClasses.subtext} hover:bg-gray-700/30`}
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {!selectedProvider ? (
                <div>
                  <p className={`${themeClasses.subtext} mb-4`}>Select a provider:</p>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(providerInfo).map(([id, info]) => (
                      <button
                        key={id}
                        onClick={() => setSelectedProvider(id)}
                        className={`p-4 rounded-lg border text-left transition-all ${
                          info.recommended
                            ? 'border-purple-500 bg-purple-500/10'
                            : `border-gray-700 hover:border-purple-500/50 ${themeClasses.card}`
                        }`}
                      >
                        <div className="text-3xl mb-2">{info.icon}</div>
                        <div className={`font-semibold ${themeClasses.text} text-sm`}>{info.name}</div>
                        {info.recommended && (
                          <div className="text-xs text-purple-400 mt-1">Recommended</div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className={`p-4 rounded-lg ${
                    currentTheme === 'light' ? 'bg-blue-50 border border-blue-200' : 'bg-blue-500/10 border border-blue-500/30'
                  }`}>
                    <p className={`text-sm ${themeClasses.text} mb-2`}>
                      Get your {providerInfo[selectedProvider].name} API key:
                    </p>
                    <a
                      href={providerInfo[selectedProvider].getKeyUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-400 hover:text-blue-300 underline"
                    >
                      {providerInfo[selectedProvider].getKeyUrl}
                    </a>
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                      Label (Optional)
                    </label>
                    <input
                      type="text"
                      value={labelInput}
                      onChange={(e) => setLabelInput(e.target.value)}
                      placeholder={`${providerInfo[selectedProvider].name} Production Key`}
                      className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                    />
                  </div>

                  <div>
                    <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                      API Key <span className="text-red-400">*</span>
                    </label>
                    <input
                      type="password"
                      value={apiKeyInput}
                      onChange={(e) => setApiKeyInput(e.target.value)}
                      placeholder={providerInfo[selectedProvider].keyFormat}
                      className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono`}
                    />
                    <p className={`text-xs ${themeClasses.subtext} mt-2`}>
                      Your API key will be encrypted with Fernet and stored securely
                    </p>
                  </div>

                  <div className="flex gap-3 pt-4">
                    <button
                      onClick={() => setSelectedProvider(null)}
                      className={`flex-1 px-4 py-3 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
                          : 'border-slate-600 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      Back
                    </button>
                    <button
                      onClick={handleAddKey}
                      disabled={!apiKeyInput.trim() || savingKey}
                      className={`flex-1 px-4 py-3 rounded-lg ${themeClasses.button} disabled:opacity-50 font-medium`}
                    >
                      {savingKey ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Saving...
                        </span>
                      ) : (
                        'Add Key'
                      )}
                    </button>
                  </div>
                </div>
              )}
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
                  <ExclamationCircleIcon className="h-6 w-6 text-red-400" />
                </div>
                <div>
                  <h3 className={`text-xl font-bold ${themeClasses.text}`}>Remove API Key?</h3>
                  <p className={`text-sm ${themeClasses.subtext}`}>
                    {providerInfo[confirmDelete]?.name}
                  </p>
                </div>
              </div>

              <p className={`${themeClasses.subtext} mb-6`}>
                Are you sure you want to remove this API key? This action cannot be undone.
                You'll need to add the key again to use this provider.
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
                  Remove Key
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
