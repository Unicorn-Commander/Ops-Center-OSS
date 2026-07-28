import React from 'react';
import { MagnifyingGlassIcon, FunnelIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export default function SearchBar({
  activeTab,
  searchQuery,
  setSearchQuery,
  showFilters,
  setShowFilters,
  sortBy,
  setSortBy,
  searching
}) {
  const getPlaceholder = () => {
    switch (activeTab) {
      case 'vllm':
        return 'Search Hugging Face for text generation (AWQ/GPTQ quantized) models...';
      case 'ollama':
        return 'Search Hugging Face for GGUF format models...';
      case 'embeddings':
        return 'Search Hugging Face for sentence-transformers embedding models...';
      case 'reranker':
        return 'Search Hugging Face for cross-encoder reranking models...';
      default:
        return 'Search Hugging Face...';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="space-y-4">
        {/* Search Bar and Controls */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={getPlaceholder()}
              className="w-full px-4 py-2 pl-10 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 border rounded-lg flex items-center gap-2 ${
              showFilters ? 'bg-blue-50 border-blue-300 text-blue-700' : 'hover:bg-gray-50'
            }`}
          >
            <FunnelIcon className="h-5 w-5" />
            Filters
          </button>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
          >
            <option value="downloads">Sort by Downloads</option>
            <option value="likes">Sort by Likes</option>
            <option value="lastModified">Sort by Last Modified</option>
          </select>
        </div>

        {searching && (
          <div className="mt-4 text-center text-gray-500">
            <ArrowPathIcon className="h-6 w-6 animate-spin mx-auto" />
            Searching Hugging Face...
          </div>
        )}
      </div>
    </div>
  );
}
