import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import ModelBrowser from '../components/ModelBrowser';
import {
  Key,
  Save,
  Eye,
  EyeOff,
  CheckCircle,
  XCircle,
  RefreshCw,
  ExternalLink,
  AlertCircle,
  Zap
} from 'lucide-react';

const OpenRouterSettings = () => {
  const { theme } = useTheme();
  const { showToast } = useToast();

  // State
  const [provider, setProvider] = useState(null);
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // Fetch OpenRouter provider
  const fetchProvider = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/llm/providers');
      if (!response.ok) throw new Error('Failed to fetch providers');

      const data = await response.json();
      const openrouter = data.find(p => p.type === 'openrouter');

      if (openrouter) {
        setProvider(openrouter);
        setApiKey(openrouter.api_key_encrypted || '');
      }
    } catch (error) {
      console.error('Error fetching provider:', error);
      showToast('Failed to load OpenRouter settings', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Save API key
  const saveApiKey = async () => {
    if (!apiKey.trim()) {
      showToast('Please enter an API key', 'error');
      return;
    }

    setSaving(true);
    try {
      const response = await fetch(`/api/v1/llm/providers/${provider.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key_encrypted: apiKey,
          enabled: true
        })
      });

      if (!response.ok) throw new Error('Failed to save settings');

      showToast('✅ OpenRouter API key saved successfully!', 'success');
      fetchProvider(); // Refresh
    } catch (error) {
      console.error('Error saving API key:', error);
      showToast('Failed to save API key', 'error');
    } finally {
      setSaving(false);
    }
  };

  // Test API key with a simple call
  const testApiKey = async () => {
    if (!apiKey.trim()) {
      showToast('Please enter an API key first', 'error');
      return;
    }

    setTesting(true);
    setTestResult(null);

    try {
      const response = await fetch('/api/v1/llm/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-user@example.com'
        },
        body: JSON.stringify({
          model: 'openai/gpt-4o-mini',
          messages: [{ role: 'user', content: 'Say "Test successful" in 2 words' }],
          max_tokens: 10
        })
      });

      const data = await response.json();

      if (response.ok) {
        setTestResult({
          success: true,
          message: 'API key is valid and working!',
          response: data.choices[0].message.content,
          cost: data._metadata?.cost_incurred || 0
        });
        showToast('✅ API key test successful!', 'success');
      } else {
        setTestResult({
          success: false,
          message: data.detail || 'Test failed',
          error: JSON.stringify(data, null, 2)
        });
        showToast('❌ API key test failed', 'error');
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error.message,
        error: error.toString()
      });
      showToast('❌ Test error: ' + error.message, 'error');
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    fetchProvider();
  }, []);

  return (
    <div className="min-h-screen p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className={`text-3xl font-bold ${theme.text.primary} mb-2`}>
          OpenRouter Settings
        </h1>
        <p className={`${theme.text.secondary}`}>
          Manage your OpenRouter API key and browse 348 available models
        </p>
      </div>

      {/* Provider Status Card */}
      {loading ? (
        <div className={`${theme.card} rounded-xl p-12 text-center border ${theme.border}`}>
          <RefreshCw className="h-12 w-12 animate-spin mx-auto text-purple-400 mb-4" />
          <p className={theme.text.secondary}>Loading provider settings...</p>
        </div>
      ) : !provider ? (
        <div className={`${theme.card} rounded-xl p-12 text-center border border-yellow-500/30`}>
          <AlertCircle className="h-12 w-12 mx-auto text-yellow-400 mb-4" />
          <h3 className={`text-xl font-semibold ${theme.text.primary} mb-2`}>
            OpenRouter Provider Not Found
          </h3>
          <p className={`${theme.text.secondary} mb-4`}>
            OpenRouter provider hasn't been configured yet.
          </p>
          <button
            onClick={fetchProvider}
            className={`px-6 py-3 rounded-lg ${theme.button.primary}`}
          >
            Retry
          </button>
        </div>
      ) : (
        <>
          {/* API Key Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className={`${theme.card} rounded-xl p-6 border ${theme.border}`}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-purple-500/20 rounded-lg">
                  <Key className="h-6 w-6 text-purple-400" />
                </div>
                <div>
                  <h2 className={`text-xl font-semibold ${theme.text.primary}`}>
                    API Configuration
                  </h2>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    OpenRouter API Key - Access to 348 models
                  </p>
                </div>
              </div>
              {provider.enabled && (
                <span className="flex items-center gap-2 px-3 py-1 bg-green-500/20 text-green-400 rounded-lg text-sm">
                  <CheckCircle className="h-4 w-4" />
                  Active
                </span>
              )}
            </div>

            {/* API Key Input */}
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                  OpenRouter API Key
                </label>
                <div className="flex gap-3">
                  <div className="relative flex-1">
                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <input
                      type={showKey ? 'text' : 'password'}
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      placeholder="sk-or-v1-..."
                      className={`w-full pl-10 pr-12 py-3 rounded-lg border ${theme.border} ${theme.input} font-mono text-sm`}
                    />
                    <button
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-300"
                    >
                      {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <button
                    onClick={saveApiKey}
                    disabled={saving}
                    className={`px-6 py-3 rounded-lg ${theme.button.primary} flex items-center gap-2 whitespace-nowrap`}
                  >
                    <Save className={`h-4 w-4 ${saving ? 'animate-pulse' : ''}`} />
                    {saving ? 'Saving...' : 'Save'}
                  </button>
                  <button
                    onClick={testApiKey}
                    disabled={testing}
                    className={`px-6 py-3 rounded-lg ${theme.button.secondary} flex items-center gap-2 whitespace-nowrap`}
                  >
                    <Zap className={`h-4 w-4 ${testing ? 'animate-pulse' : ''}`} />
                    {testing ? 'Testing...' : 'Test'}
                  </button>
                </div>
              </div>

              {/* Test Result */}
              {testResult && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className={`p-4 rounded-lg border ${
                    testResult.success
                      ? 'bg-green-500/10 border-green-500/30'
                      : 'bg-red-500/10 border-red-500/30'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    {testResult.success ? (
                      <CheckCircle className="h-5 w-5 text-green-400 mt-0.5" />
                    ) : (
                      <XCircle className="h-5 w-5 text-red-400 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className={`font-medium ${testResult.success ? 'text-green-400' : 'text-red-400'}`}>
                        {testResult.message}
                      </p>
                      {testResult.response && (
                        <p className={`text-sm ${theme.text.secondary} mt-1`}>
                          Response: "{testResult.response}"
                        </p>
                      )}
                      {testResult.cost !== undefined && (
                        <p className={`text-sm ${theme.text.secondary} mt-1`}>
                          Cost: ${testResult.cost.toFixed(6)} credits
                        </p>
                      )}
                      {testResult.error && (
                        <pre className={`text-xs ${theme.text.secondary} mt-2 p-2 bg-black/20 rounded overflow-x-auto`}>
                          {testResult.error}
                        </pre>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}

              {/* Help Text */}
              <div className={`p-4 rounded-lg ${theme.glass} border ${theme.border}`}>
                <p className={`text-sm ${theme.text.secondary}`}>
                  Don't have an API key?{' '}
                  <a
                    href="https://openrouter.ai/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-purple-400 hover:text-purple-300 inline-flex items-center gap-1"
                  >
                    Get one from OpenRouter
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </p>
              </div>
            </div>
          </motion.div>

          {/* Model Browser */}
          <ModelBrowser />
        </>
      )}
    </div>
  );
};

export default OpenRouterSettings;
