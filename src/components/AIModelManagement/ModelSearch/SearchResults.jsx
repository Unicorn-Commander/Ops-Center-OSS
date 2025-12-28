import React from 'react';
import { CloudArrowDownIcon } from '@heroicons/react/24/outline';

export default function SearchResults({
  searchResults,
  activeTab,
  downloadVllmModel,
  downloadOllamaModel,
  setSelectedModel
}) {
  if (searchResults.length === 0) return null;

  const handleDownload = (e, model) => {
    e.stopPropagation();
    if (activeTab === 'vllm') {
      downloadVllmModel(model.modelId);
    } else {
      downloadOllamaModel(model.modelId);
    }
  };

  return (
    <div className="mt-4 space-y-3 max-h-96 overflow-y-auto">
      {searchResults.map((model) => (
        <div
          key={model.modelId}
          className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer"
          onClick={() => setSelectedModel(model)}
        >
          <div className="flex justify-between items-start">
            <div className="flex-1">
              <h4 className="font-medium text-gray-900 dark:text-white">
                {model.modelId}
              </h4>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                {model.author} • {model.downloads?.toLocaleString() || 0} downloads • {model.likes || 0} likes
              </p>
              <div className="flex gap-2 mt-2">
                {model.pipeline_tag && (
                  <span className="inline-block px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs rounded">
                    {model.pipeline_tag}
                  </span>
                )}
                {model.tags?.slice(0, 3).map((tag) => (
                  <span
                    key={tag}
                    className="inline-block px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
            <button
              onClick={(e) => handleDownload(e, model)}
              className="ml-4 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700"
            >
              <CloudArrowDownIcon className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
