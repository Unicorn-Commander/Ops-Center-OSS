import React from 'react';
import { motion } from 'framer-motion';
import { AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';
import VllmSettings from './VllmSettings';
import OllamaSettings from './OllamaSettings';
import EmbeddingsSettings from './EmbeddingsSettings';
import RerankerSettings from './RerankerSettings';

export default function GlobalSettingsPanel({
  activeTab,
  showSettings,
  setShowSettings,
  vllmSettings,
  setVllmSettings,
  ollamaSettings,
  setOllamaSettings,
  embeddingsSettings,
  setEmbeddingsSettings,
  rerankerSettings,
  setRerankerSettings,
  onSave
}) {
  const getServiceName = () => {
    switch (activeTab) {
      case 'vllm': return 'vLLM';
      case 'ollama': return 'Ollama';
      case 'embeddings': return 'Embeddings';
      case 'reranker': return 'Reranker';
      default: return '';
    }
  };

  return (
    <>
      {/* Settings Button */}
      <div className="flex justify-end">
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 flex items-center gap-2"
        >
          <AdjustmentsHorizontalIcon className="h-5 w-5" />
          Global {getServiceName()} Settings
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
        >
          <h3 className="text-lg font-semibold mb-4">
            Global {getServiceName()} Settings
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            These settings apply to all models unless overridden by model-specific settings.
          </p>

          {activeTab === 'vllm' && (
            <VllmSettings settings={vllmSettings} setSettings={setVllmSettings} />
          )}

          {activeTab === 'ollama' && (
            <OllamaSettings settings={ollamaSettings} setSettings={setOllamaSettings} />
          )}

          {activeTab === 'embeddings' && (
            <EmbeddingsSettings settings={embeddingsSettings} setSettings={setEmbeddingsSettings} />
          )}

          {activeTab === 'reranker' && (
            <RerankerSettings settings={rerankerSettings} setSettings={setRerankerSettings} />
          )}

          <div className="mt-6 flex justify-end gap-2">
            <button
              onClick={() => setShowSettings(false)}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Cancel
            </button>
            <button
              onClick={onSave}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Save Global Settings
            </button>
          </div>
        </motion.div>
      )}
    </>
  );
}
