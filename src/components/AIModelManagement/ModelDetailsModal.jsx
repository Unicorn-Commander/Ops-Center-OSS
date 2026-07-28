import React from 'react';
import { XCircleIcon, CloudArrowDownIcon } from '@heroicons/react/24/outline';

export default function ModelDetailsModal({
  selectedModel,
  setSelectedModel,
  activeTab,
  downloadVllmModel,
  downloadOllamaModel
}) {
  if (!selectedModel) return null;

  const handleDownload = () => {
    if (activeTab === 'vllm') {
      downloadVllmModel(selectedModel.modelId);
    } else {
      downloadOllamaModel(selectedModel.modelId);
    }
    setSelectedModel(null);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-start mb-4">
          <h3 className="text-xl font-semibold">{selectedModel.modelId}</h3>
          <button
            onClick={() => setSelectedModel(null)}
            className="text-gray-400 hover:text-gray-600"
          >
            <XCircleIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <h4 className="font-medium mb-2">Model Information</h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>Author: {selectedModel.author}</div>
              <div>Downloads: {selectedModel.downloads?.toLocaleString() || 0}</div>
              <div>Likes: {selectedModel.likes || 0}</div>
              <div>Task: {selectedModel.pipeline_tag || 'Unknown'}</div>
              {selectedModel.lastModified && (
                <div>Updated: {new Date(selectedModel.lastModified).toLocaleDateString()}</div>
              )}
              {selectedModel.library_name && (
                <div>Library: {selectedModel.library_name}</div>
              )}
            </div>
          </div>

          {selectedModel.tags && selectedModel.tags.length > 0 && (
            <div>
              <h4 className="font-medium mb-2">Tags</h4>
              <div className="flex flex-wrap gap-2">
                {selectedModel.tags.map((tag) => (
                  <span
                    key={tag}
                    className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-sm rounded"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2">
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-2"
            >
              <CloudArrowDownIcon className="h-5 w-5" />
              Download Model
            </button>
            <a
              href={`https://huggingface.co/${selectedModel.modelId}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
            >
              View on Hugging Face
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
