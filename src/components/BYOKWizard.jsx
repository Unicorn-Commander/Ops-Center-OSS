/**
 * BYOKWizard Component
 *
 * 4-step wizard for adding BYOK (Bring Your Own Key) LLM providers
 *
 * Steps:
 * 1. Select Provider - Choose from OpenAI, Anthropic, Google, Cohere, etc.
 * 2. Enter API Key - Masked input with validation
 * 3. Test Connection - Verify API key works
 * 4. Confirm & Save - Final confirmation
 *
 * Props:
 * - onClose: () => void - Close wizard without saving
 * - onComplete: () => void - Called after successful save
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CheckCircleIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  XMarkIcon,
  SparklesIcon,
  KeyIcon,
  ExclamationTriangleIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function BYOKWizard({ onClose, onComplete }) {
  const { theme, currentTheme } = useTheme();
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedProvider, setSelectedProvider] = useState('');
  const [providerName, setProviderName] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const providers = [
    {
      id: 'openai',
      name: 'OpenAI',
      placeholder: 'sk-proj-...',
      icon: '🤖',
      description: 'GPT-4, GPT-3.5, and embeddings',
      pattern: /^sk-proj-[a-zA-Z0-9_-]{40,}$/
    },
    {
      id: 'anthropic',
      name: 'Anthropic',
      placeholder: 'sk-ant-...',
      icon: '🧠',
      description: 'Claude 3.5 Sonnet, Opus, and Haiku',
      pattern: /^sk-ant-api[a-zA-Z0-9_-]{40,}$/
    },
    {
      id: 'google',
      name: 'Google AI',
      placeholder: 'AIza...',
      icon: '🔍',
      description: 'Gemini Pro and Ultra models',
      pattern: /^AIza[a-zA-Z0-9_-]{30,}$/
    },
    {
      id: 'cohere',
      name: 'Cohere',
      placeholder: 'co_...',
      icon: '💬',
      description: 'Command and Embed models',
      pattern: /^co_[a-zA-Z0-9_-]{40,}$/
    },
    {
      id: 'together',
      name: 'Together AI',
      placeholder: 'together_...',
      icon: '🚀',
      description: 'Open-source model hosting',
      pattern: /^[a-zA-Z0-9_-]{40,}$/
    },
    {
      id: 'openrouter',
      name: 'OpenRouter',
      placeholder: 'sk-or-...',
      icon: '🔀',
      description: 'Multi-provider routing service',
      pattern: /^sk-or-[a-zA-Z0-9_-]{40,}$/
    }
  ];

  const getThemeClasses = () => ({
    modal: currentTheme === 'unicorn'
      ? 'bg-purple-900/95 backdrop-blur-xl border-white/20'
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
    card: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-gray-50 border-gray-200'
      : 'bg-slate-900 border-slate-700'
  });

  const themeClasses = getThemeClasses();

  const validateCurrentStep = () => {
    switch (currentStep) {
      case 1:
        return selectedProvider !== '';
      case 2:
        const provider = providers.find(p => p.id === selectedProvider);
        return apiKey.trim() !== '' && provider?.pattern?.test(apiKey);
      case 3:
        return testResult?.success === true;
      case 4:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep === 3 && !testResult) {
      handleTestConnection();
      return;
    }
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1);
      setError(null);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
      setError(null);
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setError(null);
    setTestResult(null);

    try {
      const response = await fetch('/api/v1/llm/providers/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          provider: selectedProvider,
          api_key: apiKey
        })
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setTestResult({ success: true, message: data.message || 'API key is valid!' });
      } else {
        setTestResult({ success: false, message: data.error || 'Connection test failed' });
        setError(data.error || 'Connection test failed');
      }
    } catch (err) {
      console.error('Test connection error:', err);
      setTestResult({ success: false, message: 'Network error during test' });
      setError('Network error. Please check your connection.');
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/llm/providers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          provider_type: selectedProvider,
          name: providerName || `${providers.find(p => p.id === selectedProvider)?.name} (BYOK)`,
          api_key: apiKey,
          byok: true
        })
      });

      if (response.ok) {
        onComplete();
      } else {
        const data = await response.json();
        setError(data.error || 'Failed to save provider');
      }
    } catch (err) {
      console.error('Save error:', err);
      setError('Network error. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        className={`rounded-xl border p-8 max-w-2xl w-full m-4 ${themeClasses.modal}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-violet-600 rounded-lg flex items-center justify-center">
              <SparklesIcon className="h-6 w-6 text-white" />
            </div>
            <div>
              <h2 className={`text-2xl font-bold ${themeClasses.text}`}>
                Add Provider (BYOK)
              </h2>
              <p className={`text-sm ${themeClasses.subtext}`}>
                Bring your own API key for LLM providers
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg ${themeClasses.subtext} hover:bg-gray-700/50`}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-8">
          {[1, 2, 3, 4].map((step) => (
            <React.Fragment key={step}>
              <div className="flex flex-col items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
                  step === currentStep
                    ? 'bg-purple-600 text-white'
                    : step < currentStep
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-700 text-gray-400'
                }`}>
                  {step < currentStep ? <CheckIcon className="h-6 w-6" /> : step}
                </div>
                <span className={`text-xs mt-2 ${
                  step === currentStep ? themeClasses.text : themeClasses.subtext
                }`}>
                  {['Select', 'API Key', 'Test', 'Confirm'][step - 1]}
                </span>
              </div>
              {step < 4 && (
                <div className={`flex-1 h-1 mx-2 ${
                  step < currentStep ? 'bg-green-600' : 'bg-gray-700'
                }`} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg flex items-center gap-3">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0" />
            <span className="text-red-400 text-sm">{error}</span>
          </div>
        )}

        {/* Step Content */}
        <AnimatePresence mode="wait">
          {/* Step 1: Select Provider */}
          {currentStep === 1 && (
            <motion.div
              key="step1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="min-h-[300px]"
            >
              <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
                Select Provider
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {providers.map((provider) => (
                  <button
                    key={provider.id}
                    onClick={() => setSelectedProvider(provider.id)}
                    className={`p-6 rounded-xl border-2 text-left transition-all ${
                      selectedProvider === provider.id
                        ? 'border-purple-500 bg-purple-500/10'
                        : `border-gray-700 ${themeClasses.card} hover:border-purple-500/50`
                    }`}
                  >
                    <div className="text-4xl mb-3">{provider.icon}</div>
                    <div className={`font-semibold ${themeClasses.text} mb-1`}>
                      {provider.name}
                    </div>
                    <div className={`text-sm ${themeClasses.subtext}`}>
                      {provider.description}
                    </div>
                  </button>
                ))}
              </div>
            </motion.div>
          )}

          {/* Step 2: Enter API Key */}
          {currentStep === 2 && (
            <motion.div
              key="step2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="min-h-[300px]"
            >
              <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
                Enter API Key for {providers.find(p => p.id === selectedProvider)?.name}
              </h3>

              <div className="space-y-4">
                <div>
                  <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                    Provider Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={providerName}
                    onChange={(e) => setProviderName(e.target.value)}
                    placeholder={`${providers.find(p => p.id === selectedProvider)?.name} Production`}
                    className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                  />
                </div>

                <div>
                  <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                    API Key <span className="text-red-400">*</span>
                  </label>
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder={providers.find(p => p.id === selectedProvider)?.placeholder}
                    className={`w-full px-4 py-3 rounded-lg border ${themeClasses.input} focus:outline-none focus:ring-2 focus:ring-purple-500 font-mono`}
                  />
                  <p className={`text-xs ${themeClasses.subtext} mt-2`}>
                    Your API key will be encrypted and stored securely
                  </p>
                </div>

                {apiKey && !providers.find(p => p.id === selectedProvider)?.pattern?.test(apiKey) && (
                  <div className="p-3 bg-yellow-500/20 border border-yellow-500/50 rounded-lg flex items-center gap-2">
                    <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                    <span className="text-yellow-400 text-sm">
                      This doesn't look like a valid {providers.find(p => p.id === selectedProvider)?.name} API key
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Step 3: Test Connection */}
          {currentStep === 3 && (
            <motion.div
              key="step3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="min-h-[300px]"
            >
              <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
                Test Connection
              </h3>

              {!testResult && !testing && (
                <div className={`p-8 rounded-xl border-2 border-dashed ${themeClasses.card} text-center`}>
                  <KeyIcon className="h-16 w-16 mx-auto mb-4 text-purple-400" />
                  <p className={`${themeClasses.text} mb-2`}>
                    Ready to test your API key
                  </p>
                  <p className={`text-sm ${themeClasses.subtext} mb-6`}>
                    We'll make a simple API call to verify your key works correctly
                  </p>
                  <button
                    onClick={handleTestConnection}
                    className={`px-6 py-3 rounded-lg ${themeClasses.button} font-medium`}
                  >
                    Test Connection
                  </button>
                </div>
              )}

              {testing && (
                <div className={`p-8 rounded-xl ${themeClasses.card} text-center`}>
                  <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
                  <p className={`${themeClasses.text}`}>Testing connection...</p>
                </div>
              )}

              {testResult && (
                <div className={`p-8 rounded-xl ${themeClasses.card} text-center`}>
                  {testResult.success ? (
                    <>
                      <CheckCircleIcon className="h-16 w-16 mx-auto mb-4 text-green-400" />
                      <p className={`text-xl font-semibold ${themeClasses.text} mb-2`}>
                        Connection Successful!
                      </p>
                      <p className={`text-sm ${themeClasses.subtext}`}>
                        {testResult.message}
                      </p>
                    </>
                  ) : (
                    <>
                      <XMarkIcon className="h-16 w-16 mx-auto mb-4 text-red-400" />
                      <p className={`text-xl font-semibold ${themeClasses.text} mb-2`}>
                        Connection Failed
                      </p>
                      <p className={`text-sm ${themeClasses.subtext} mb-4`}>
                        {testResult.message}
                      </p>
                      <button
                        onClick={handleTestConnection}
                        className={`px-6 py-2 rounded-lg ${themeClasses.button}`}
                      >
                        Try Again
                      </button>
                    </>
                  )}
                </div>
              )}
            </motion.div>
          )}

          {/* Step 4: Confirm */}
          {currentStep === 4 && (
            <motion.div
              key="step4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="min-h-[300px]"
            >
              <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
                Confirm & Save
              </h3>

              <div className={`p-6 rounded-xl ${themeClasses.card} space-y-4`}>
                <div className="flex items-center justify-between">
                  <span className={themeClasses.subtext}>Provider:</span>
                  <span className={`font-semibold ${themeClasses.text}`}>
                    {providers.find(p => p.id === selectedProvider)?.name}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={themeClasses.subtext}>Name:</span>
                  <span className={`font-semibold ${themeClasses.text}`}>
                    {providerName || `${providers.find(p => p.id === selectedProvider)?.name} (BYOK)`}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className={themeClasses.subtext}>API Key:</span>
                  <code className={`font-mono text-sm ${themeClasses.text}`}>
                    {apiKey.substring(0, 8)}••••••••
                  </code>
                </div>
                <div className="flex items-center justify-between">
                  <span className={themeClasses.subtext}>Status:</span>
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400 border border-green-500/30">
                    Verified
                  </span>
                </div>
              </div>

              <div className={`mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg`}>
                <p className={`text-sm ${themeClasses.text}`}>
                  This provider will be added to your account and can be used for LLM routing.
                  You can manage it from the LLM Providers page.
                </p>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-700">
          <button
            onClick={handleBack}
            disabled={currentStep === 1}
            className={`flex items-center gap-2 px-6 py-3 rounded-lg ${
              currentStep === 1
                ? 'opacity-50 cursor-not-allowed text-gray-500'
                : `${themeClasses.subtext} hover:bg-gray-700/50`
            }`}
          >
            <ArrowLeftIcon className="h-5 w-5" />
            Back
          </button>

          <div className="flex items-center gap-3">
            <button
              onClick={onClose}
              className={`px-6 py-3 rounded-lg border ${
                currentTheme === 'light'
                  ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  : 'border-slate-600 text-slate-300 hover:bg-slate-700'
              }`}
            >
              Cancel
            </button>

            {currentStep < 4 ? (
              <button
                onClick={handleNext}
                disabled={!validateCurrentStep()}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg ${themeClasses.button} disabled:opacity-50 disabled:cursor-not-allowed font-medium`}
              >
                {currentStep === 3 && !testResult ? 'Test & Continue' : 'Next'}
                <ArrowRightIcon className="h-5 w-5" />
              </button>
            ) : (
              <button
                onClick={handleSave}
                disabled={saving}
                className={`flex items-center gap-2 px-6 py-3 rounded-lg ${themeClasses.button} disabled:opacity-50 font-medium`}
              >
                {saving ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Saving...
                  </>
                ) : (
                  <>
                    <CheckCircleIcon className="h-5 w-5" />
                    Save Provider
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}
