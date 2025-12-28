import React from 'react';
import { CubeIcon } from '@heroicons/react/24/outline';

export default function ServiceTabs({ activeTab, setActiveTab }) {
  const tabs = [
    { id: 'vllm', label: 'vLLM Models' },
    { id: 'ollama', label: 'Ollama Models' },
    { id: 'embeddings', label: 'iGPU Embeddings' },
    { id: 'reranker', label: 'iGPU Reranker' }
  ];

  return (
    <div className="border-b dark:border-gray-700">
      <nav className="-mb-px flex space-x-8">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === tab.id
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <CubeIcon className="h-5 w-5" />
              {tab.label}
            </div>
          </button>
        ))}
      </nav>
    </div>
  );
}
