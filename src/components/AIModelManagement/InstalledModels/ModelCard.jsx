import React from 'react';
import { motion } from 'framer-motion';
import {
  PlayIcon,
  TrashIcon,
  Cog6ToothIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

export default function ModelCard({
  model,
  activeTab,
  formatBytes,
  downloadProgress,
  setShowModelSettings,
  activateModel,
  deleteModel
}) {
  const hasDownloadProgress = downloadProgress[model.id || model.name] !== undefined;
  const modelId = model.id || model.name;

  return (
    <motion.div
      key={modelId}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="border dark:border-gray-700 rounded-lg p-4"
    >
      <div className="flex justify-between items-center">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-medium text-gray-900 dark:text-white">
              {model.name}
            </h4>
            {model.active && (
              <span className="px-2 py-1 bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 text-xs rounded-full">
                Active
              </span>
            )}
            {model.has_overrides && (
              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs rounded-full">
                Custom Settings
              </span>
            )}
            {activeTab === 'embeddings' && model.dimensions && (
              <span className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded-full">
                {model.dimensions} dimensions
              </span>
            )}
            {activeTab === 'reranker' && (
              <span className="px-2 py-1 bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 text-xs rounded-full">
                Cross-encoder
              </span>
            )}
            {hasDownloadProgress && (
              <div className="flex items-center gap-2">
                <ArrowPathIcon className="h-4 w-4 animate-spin text-blue-500" />
                <span className="text-xs text-blue-600 dark:text-blue-400">
                  Downloading: {Math.round(downloadProgress[modelId])}%
                </span>
              </div>
            )}
          </div>
          <div className="flex gap-4 mt-2 text-sm text-gray-500">
            {model.path && <span>Path: {model.path}</span>}
            <span>Size: {formatBytes(model.size)}</span>
            {model.device && <span>Device: {model.device || 'CPU (iGPU)'}</span>}
            {model.last_modified && (
              <span>Modified: {new Date(model.last_modified).toLocaleDateString()}</span>
            )}
            {model.last_used && (
              <span>Last used: {new Date(model.last_used).toLocaleDateString()}</span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {(activeTab === 'vllm' || activeTab === 'ollama') && (
            <button
              onClick={() => setShowModelSettings(modelId)}
              className="px-3 py-1 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-1"
              title="Model-specific settings"
            >
              <Cog6ToothIcon className="h-4 w-4" />
            </button>
          )}
          {!model.active && (
            <button
              onClick={() => activateModel(activeTab, modelId)}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
            >
              <PlayIcon className="h-4 w-4" />
              {activeTab === 'ollama' ? 'Run' : 'Activate'}
            </button>
          )}
          <button
            onClick={() => deleteModel(activeTab, modelId)}
            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}
