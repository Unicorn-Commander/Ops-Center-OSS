/**
 * API Providers Tab
 *
 * Configure API keys for cloud LLM providers (OpenRouter, OpenAI, Anthropic, etc.)
 * or add custom OpenAI-compatible endpoints.
 *
 * Features:
 * - Add, edit, delete API keys for built-in providers
 * - Custom provider support with custom URL
 * - Test connection functionality
 * - Show/hide API key toggle
 * - Integration with Model Catalog (invalidates cache on change)
 */

import React from 'react';
import ProviderKeysSection from '../../components/ProviderKeysSection';
import { useQueryClient } from '@tanstack/react-query';

export default function APIProviders() {
  const queryClient = useQueryClient();

  const handleKeysChanged = () => {
    // Invalidate model catalog cache to refresh available models
    queryClient.invalidateQueries(['models']);
    queryClient.invalidateQueries(['modelCatalog']);
    console.log('Provider keys updated, model catalog cache invalidated');
  };

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="mb-4">
        <h2 className="text-2xl font-bold text-white">API Provider Configuration</h2>
        <p className="text-gray-400 mt-2">
          Configure API keys for cloud providers or add custom OpenAI-compatible endpoints.
        </p>
        <div className="mt-4 p-4 bg-blue-900/20 border border-blue-700 rounded-lg">
          <p className="text-sm text-blue-300">
            <span className="font-semibold">💡 Tip:</span> After adding or updating API keys, the Model Catalog will automatically refresh to show newly available models.
          </p>
        </div>
      </div>

      {/* Provider Keys Section */}
      <ProviderKeysSection
        onKeysChanged={handleKeysChanged}
        collapsible={false}
        defaultExpanded={true}
      />

      {/* Help Section */}
      <div className="mt-8 p-6 bg-gray-800/50 border border-gray-700 rounded-lg">
        <h3 className="text-lg font-semibold text-white mb-3">Getting Started</h3>
        <div className="space-y-3 text-sm text-gray-300">
          <div>
            <strong className="text-white">Built-in Providers:</strong> OpenRouter, OpenAI, Anthropic, Google, Cohere, Groq, Together AI, Mistral
          </div>
          <div>
            <strong className="text-white">Custom Providers:</strong> Add any OpenAI-compatible endpoint with a custom base URL
          </div>
          <div>
            <strong className="text-white">Testing:</strong> Use the "Test Connection" button to verify your API key works correctly
          </div>
          <div>
            <strong className="text-white">Security:</strong> API keys are stored securely and never exposed in frontend code
          </div>
        </div>
      </div>
    </div>
  );
}
