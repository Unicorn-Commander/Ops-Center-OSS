import React from 'react';
import ModelCard from './ModelCard';

export default function InstalledModels({
  activeTab,
  installedModels,
  formatBytes,
  downloadProgress,
  setShowModelSettings,
  activateModel,
  deleteModel,
  embeddingsSettings,
  rerankerSettings
}) {
  const getServiceName = () => {
    switch (activeTab) {
      case 'vllm': return 'vLLM';
      case 'ollama': return 'Ollama';
      case 'embeddings': return 'Embedding';
      case 'reranker': return 'Reranker';
      default: return '';
    }
  };

  const models = installedModels?.[activeTab] || [];
  const hasModels = models && models.length > 0;

  const renderEmptyState = () => {
    if (activeTab === 'embeddings') {
      return (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Current embedding model: {embeddingsSettings.model_name}
          </p>
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg max-w-md mx-auto">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              The embedding service runs on Intel iGPU for optimal resource allocation.
              You can change the model in the Global Settings above.
            </p>
          </div>
        </div>
      );
    }

    if (activeTab === 'reranker') {
      return (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            Current reranker model: {rerankerSettings.model_name}
          </p>
          <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg max-w-md mx-auto">
            <p className="text-sm text-blue-800 dark:text-blue-200">
              The reranker service runs on Intel iGPU for optimal resource allocation.
              You can change the model in the Global Settings above.
            </p>
          </div>
        </div>
      );
    }

    return (
      <p className="text-gray-500 dark:text-gray-400 text-center py-8">
        No {getServiceName()} models installed yet. Search and download models above.
      </p>
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">
        Installed {getServiceName()} Models
      </h2>

      <div className="space-y-4">
        {!hasModels ? (
          renderEmptyState()
        ) : (
          models.map((model) => (
            <ModelCard
              key={model.id || model.name}
              model={model}
              activeTab={activeTab}
              formatBytes={formatBytes}
              downloadProgress={downloadProgress}
              setShowModelSettings={setShowModelSettings}
              activateModel={activateModel}
              deleteModel={deleteModel}
            />
          ))
        )}
      </div>
    </div>
  );
}
