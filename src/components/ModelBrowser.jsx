import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from './Toast';
import {
  Search,
  Filter,
  DollarSign,
  Layers,
  ArrowUpDown,
  RefreshCw,
  Play,
  CheckCircle,
  XCircle
} from 'lucide-react';

const ModelBrowser = () => {
  const { theme } = useTheme();
  const { showToast } = useToast();

  // State
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('cost');
  const [maxCost, setMaxCost] = useState('');
  const [minContext, setMinContext] = useState('');
  const [showFilters, setShowFilters] = useState(false);
  const [testing, setTesting] = useState(null);

  // Fetch models from backend
  const fetchModels = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: 100,
        sort_by: sortBy
      });

      if (search) params.append('search', search);
      if (maxCost) params.append('max_cost', maxCost);
      if (minContext) params.append('min_context', minContext);

      const response = await fetch(`/api/v1/llm/models?${params}`);
      if (!response.ok) throw new Error('Failed to fetch models');

      const data = await response.json();
      setModels(data);
    } catch (error) {
      console.error('Error fetching models:', error);
      showToast('Failed to load models', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Test a model with chat completions
  const testModel = async (modelName) => {
    setTesting(modelName);
    try {
      const response = await fetch('/api/v1/llm/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-user@example.com' // TODO: Use real user token
        },
        body: JSON.stringify({
          model: modelName,
          messages: [{ role: 'user', content: 'Say "Hello" in one word' }],
          max_tokens: 10
        })
      });

      const data = await response.json();

      if (response.ok) {
        showToast(`✅ ${modelName} works! Response: ${data.choices[0].message.content}`, 'success');
      } else {
        showToast(`❌ Test failed: ${data.detail}`, 'error');
      }
    } catch (error) {
      showToast(`❌ Error: ${error.message}`, 'error');
    } finally {
      setTesting(null);
    }
  };

  // Fetch on mount and filter changes
  useEffect(() => {
    fetchModels();
  }, [search, sortBy, maxCost, minContext]);

  return (
    <div className="space-y-6">
      {/* Header with Stats */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold ${theme.text.primary}`}>
            Available Models
          </h2>
          <p className={`${theme.text.secondary} mt-1`}>
            {models.length} models loaded from OpenRouter
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-2 rounded-lg ${theme.button.secondary} flex items-center gap-2`}
          >
            <Filter className="h-4 w-4" />
            Filters
          </button>
          <button
            onClick={fetchModels}
            disabled={loading}
            className={`px-4 py-2 rounded-lg ${theme.button.primary} flex items-center gap-2`}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
          className={`${theme.card} rounded-xl p-6 border ${theme.border}`}
        >
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
            Filter Models
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Search */}
            <div>
              <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                Search by Name
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="e.g., gpt, claude, llama..."
                  className={`w-full pl-10 pr-4 py-2 rounded-lg border ${theme.border} ${theme.input}`}
                />
              </div>
            </div>

            {/* Max Cost */}
            <div>
              <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                Max Cost ($/1M tokens)
              </label>
              <div className="relative">
                <DollarSign className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="number"
                  step="0.1"
                  value={maxCost}
                  onChange={(e) => setMaxCost(e.target.value)}
                  placeholder="e.g., 5.0"
                  className={`w-full pl-10 pr-4 py-2 rounded-lg border ${theme.border} ${theme.input}`}
                />
              </div>
            </div>

            {/* Min Context */}
            <div>
              <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                Min Context (tokens)
              </label>
              <div className="relative">
                <Layers className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="number"
                  step="1000"
                  value={minContext}
                  onChange={(e) => setMinContext(e.target.value)}
                  placeholder="e.g., 100000"
                  className={`w-full pl-10 pr-4 py-2 rounded-lg border ${theme.border} ${theme.input}`}
                />
              </div>
            </div>
          </div>

          {/* Sort */}
          <div className="mt-4">
            <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
              Sort By
            </label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className={`w-full px-4 py-2 rounded-lg border ${theme.border} ${theme.input}`}
            >
              <option value="cost">Cost (Low to High)</option>
              <option value="context">Context Length (High to Low)</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>

          {/* Clear Filters */}
          <div className="mt-4 flex justify-end">
            <button
              onClick={() => {
                setSearch('');
                setMaxCost('');
                setMinContext('');
                setSortBy('cost');
              }}
              className={`px-4 py-2 rounded-lg ${theme.button.secondary}`}
            >
              Clear Filters
            </button>
          </div>
        </motion.div>
      )}

      {/* Models Table */}
      <div className={`${theme.card} rounded-xl border ${theme.border} overflow-hidden`}>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className={`${theme.glass} border-b ${theme.border}`}>
              <tr>
                <th className={`px-6 py-4 text-left text-sm font-semibold ${theme.text.primary}`}>
                  Model Name
                </th>
                <th className={`px-6 py-4 text-left text-sm font-semibold ${theme.text.primary}`}>
                  Cost per 1M
                </th>
                <th className={`px-6 py-4 text-left text-sm font-semibold ${theme.text.primary}`}>
                  Context
                </th>
                <th className={`px-6 py-4 text-left text-sm font-semibold ${theme.text.primary}`}>
                  Status
                </th>
                <th className={`px-6 py-4 text-right text-sm font-semibold ${theme.text.primary}`}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <RefreshCw className="h-8 w-8 animate-spin mx-auto text-purple-400 mb-2" />
                    <p className={theme.text.secondary}>Loading models...</p>
                  </td>
                </tr>
              ) : models.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center">
                    <p className={theme.text.secondary}>No models found matching filters</p>
                  </td>
                </tr>
              ) : (
                models.map((model) => {
                  const avgCost = (model.cost_per_1m_input + model.cost_per_1m_output) / 2;
                  const isFree = avgCost === 0;

                  return (
                    <tr key={model.id} className={`hover:${theme.glass} transition-colors`}>
                      <td className="px-6 py-4">
                        <div>
                          <div className={`font-medium ${theme.text.primary} text-sm`}>
                            {model.name}
                          </div>
                          <div className={`text-xs ${theme.text.secondary} mt-1`}>
                            {model.provider_name}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1">
                          {isFree ? (
                            <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-medium">
                              FREE
                            </span>
                          ) : (
                            <div className={`text-sm ${theme.text.primary}`}>
                              ${model.cost_per_1m_input.toFixed(2)} / ${model.cost_per_1m_output.toFixed(2)}
                              <div className={`text-xs ${theme.text.secondary}`}>
                                Avg: ${avgCost.toFixed(2)}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`text-sm ${theme.text.primary}`}>
                          {model.context_length.toLocaleString()}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        {model.enabled ? (
                          <span className="flex items-center gap-1 text-green-400 text-sm">
                            <CheckCircle className="h-4 w-4" />
                            Enabled
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-gray-400 text-sm">
                            <XCircle className="h-4 w-4" />
                            Disabled
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => testModel(model.name)}
                          disabled={testing === model.name}
                          className={`px-3 py-1 rounded-lg ${theme.button.primary} text-sm flex items-center gap-2 ml-auto`}
                        >
                          <Play className={`h-3 w-3 ${testing === model.name ? 'animate-pulse' : ''}`} />
                          {testing === model.name ? 'Testing...' : 'Test'}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer Summary */}
      {!loading && models.length > 0 && (
        <div className={`${theme.glass} rounded-lg p-4 border ${theme.border}`}>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            <div>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>{models.length}</p>
              <p className={`text-sm ${theme.text.secondary}`}>Models Loaded</p>
            </div>
            <div>
              <p className={`text-2xl font-bold text-green-400`}>
                {models.filter(m => (m.cost_per_1m_input + m.cost_per_1m_output) / 2 === 0).length}
              </p>
              <p className={`text-sm ${theme.text.secondary}`}>Free Models</p>
            </div>
            <div>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                {Math.max(...models.map(m => m.context_length)).toLocaleString()}
              </p>
              <p className={`text-sm ${theme.text.secondary}`}>Max Context</p>
            </div>
            <div>
              <p className={`text-2xl font-bold ${theme.text.primary}`}>
                ${Math.min(...models.map(m => (m.cost_per_1m_input + m.cost_per_1m_output) / 2).filter(c => c > 0)).toFixed(3)}
              </p>
              <p className={`text-sm ${theme.text.secondary}`}>Cheapest (non-free)</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ModelBrowser;
