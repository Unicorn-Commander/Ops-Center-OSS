import React from 'react';
import { motion } from 'framer-motion';

export default function SearchFilters({ filters, setFilters, showFilters }) {
  if (!showFilters) return null;

  const handleClearFilters = () => {
    setFilters({
      quantization: '',
      minSize: '',
      maxSize: '',
      license: '',
      task: '',
      language: ''
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      className="grid grid-cols-3 gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
    >
      <div>
        <label className="block text-sm font-medium mb-1">Quantization</label>
        <select
          value={filters.quantization}
          onChange={(e) => setFilters({ ...filters, quantization: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">Any</option>
          <option value="awq">AWQ</option>
          <option value="gptq">GPTQ</option>
          <option value="gguf">GGUF</option>
          <option value="fp8">FP8</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Model Size (B)</label>
        <div className="flex gap-2">
          <input
            type="number"
            placeholder="Min"
            value={filters.minSize}
            onChange={(e) => setFilters({ ...filters, minSize: e.target.value })}
            className="w-1/2 px-2 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
          />
          <input
            type="number"
            placeholder="Max"
            value={filters.maxSize}
            onChange={(e) => setFilters({ ...filters, maxSize: e.target.value })}
            className="w-1/2 px-2 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">License</label>
        <select
          value={filters.license}
          onChange={(e) => setFilters({ ...filters, license: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">Any</option>
          <option value="apache-2.0">Apache 2.0</option>
          <option value="mit">MIT</option>
          <option value="cc-by-sa-4.0">CC BY-SA 4.0</option>
          <option value="other">Other</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Task</label>
        <select
          value={filters.task}
          onChange={(e) => setFilters({ ...filters, task: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">Any</option>
          <option value="text-generation">Text Generation</option>
          <option value="text2text-generation">Text2Text Generation</option>
          <option value="conversational">Conversational</option>
          <option value="feature-extraction">Feature Extraction</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Language</label>
        <select
          value={filters.language}
          onChange={(e) => setFilters({ ...filters, language: e.target.value })}
          className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
        >
          <option value="">Any</option>
          <option value="en">English</option>
          <option value="zh">Chinese</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="multilingual">Multilingual</option>
        </select>
      </div>

      <div className="flex items-end">
        <button
          onClick={handleClearFilters}
          className="w-full px-3 py-2 text-sm bg-gray-600 text-white rounded-lg hover:bg-gray-700"
        >
          Clear Filters
        </button>
      </div>
    </motion.div>
  );
}
