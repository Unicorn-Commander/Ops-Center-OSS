import React, { useState, useCallback, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import {
  Brain,
  Search,
  Filter,
  DollarSign,
  Eye,
  EyeOff,
  RefreshCw,
  CheckCircle,
  XCircle,
  Zap,
  MessageSquare,
  Image as ImageIcon,
  Code2,
  Sparkles,
  ChevronDown,
  ChevronUp,
  LayoutGrid,
  List as ListIcon,
  Download
} from 'lucide-react';

// Utility to format pricing
const formatPrice = (price) => {
  if (price === 0) return 'Free';
  if (price < 0.01) return `$${price.toFixed(6)}`;
  if (price < 1) return `$${price.toFixed(4)}`;
  return `$${price.toFixed(2)}`;
};

// Model Row Component (simple version without animations)
const ModelRow = ({ model, theme, onToggle }) => {
  if (!model) return null;

  return (
    <div className={`border-b ${theme?.border || 'border-gray-700'} hover:bg-gray-800/50 transition-all`}
    >
      <div className="flex items-center gap-4 p-4">
        {/* Toggle Switch */}
        <div className="flex-shrink-0">
          <button
            onClick={() => onToggle(model.id)}
            className={`relative w-12 h-6 rounded-full transition-all ${
              model.is_active
                ? 'bg-green-500 hover:bg-green-600'
                : 'bg-gray-600 hover:bg-gray-500'
            }`}
          >
            <div
              className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-lg transition-all ${
                model.is_active ? 'left-7' : 'left-1'
              }`}
            />
          </button>
        </div>

        {/* Model Name & Provider */}
        <div className="flex-1 min-w-0">
          <div className={`font-medium ${theme?.text?.primary || 'text-white'} truncate`}>
            {model.name}
          </div>
          <div className={`text-xs ${theme?.text?.secondary || 'text-gray-400'} truncate mt-0.5`}>
            {model.id}
          </div>
        </div>

        {/* Capabilities */}
        <div className="flex items-center gap-2 flex-shrink-0">
          {model.supports_streaming && (
            <div className="p-1.5 rounded-lg bg-blue-500/20 text-blue-400" title="Streaming">
              <Zap className="h-3.5 w-3.5" />
            </div>
          )}
          {model.supports_function_calling && (
            <div className="p-1.5 rounded-lg bg-purple-500/20 text-purple-400" title="Function Calling">
              <Code2 className="h-3.5 w-3.5" />
            </div>
          )}
          {model.supports_vision && (
            <div className="p-1.5 rounded-lg bg-pink-500/20 text-pink-400" title="Vision">
              <ImageIcon className="h-3.5 w-3.5" />
            </div>
          )}
        </div>

        {/* Context Length */}
        <div className="text-right flex-shrink-0 min-w-[80px]">
          <div className={`text-sm ${theme?.text?.primary || 'text-white'}`}>
            {((model.context_length || 0) / 1000).toFixed(0)}K
          </div>
          <div className={`text-xs ${theme?.text?.secondary || 'text-gray-400'}`}>tokens</div>
        </div>

        {/* Pricing */}
        <div className="text-right flex-shrink-0 min-w-[100px]">
          <div className={`text-sm font-medium ${theme?.text?.primary || 'text-white'}`}>
            {formatPrice(model.pricing?.prompt_per_1m || 0)}
          </div>
          <div className={`text-xs ${theme?.text?.secondary || 'text-gray-400'}`}>per 1M in</div>
        </div>
        <div className="text-right flex-shrink-0 min-w-[100px]">
          <div className={`text-sm font-medium ${theme?.text?.primary || 'text-white'}`}>
            {formatPrice(model.pricing?.completion_per_1m || 0)}
          </div>
          <div className={`text-xs ${theme?.text?.secondary || 'text-gray-400'}`}>per 1M out</div>
        </div>

        {/* Status Indicator */}
        <div className="flex-shrink-0">
          {model.is_active ? (
            <CheckCircle className="h-5 w-5 text-green-500" />
          ) : (
            <XCircle className="h-5 w-5 text-gray-500" />
          )}
        </div>
      </div>
    </div>
  );
};

// Main Component
export default function LLMManagementUnified() {
  const { theme } = useTheme();
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  // State
  const [searchTerm, setSearchTerm] = useState('');
  const [filterActive, setFilterActive] = useState('all'); // all, enabled, disabled
  const [sortBy, setSortBy] = useState('name'); // name, price_asc, price_desc, context
  const [showFilters, setShowFilters] = useState(false);

  // Fetch models from API
  const { data: modelsData, isLoading, error, refetch } = useQuery({
    queryKey: ['openrouter-models'],
    queryFn: async () => {
      const response = await fetch('/api/v1/llm/admin/models/openrouter', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }

      const data = await response.json();
      console.log('API Response:', data);
      console.log('Models array:', data?.models);
      console.log('First model:', data?.models?.[0]);
      return data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000 // 10 minutes
  });

  // Toggle model status mutation
  const toggleMutation = useMutation({
    mutationFn: async (modelId) => {
      const response = await fetch(`/api/v1/llm/admin/models/${encodeURIComponent(modelId)}/toggle`, {
        method: 'PUT',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to toggle model');
      }

      return response.json();
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries(['openrouter-models']);
      showToast('success', data.message || 'Model status updated');
    },
    onError: (error) => {
      showToast('error', error.message || 'Failed to update model');
    }
  });

  // Handle toggle
  const handleToggle = useCallback((modelId) => {
    toggleMutation.mutate(modelId);
  }, [toggleMutation]);

  // Filter and sort models
  const filteredAndSortedModels = useMemo(() => {
    try {
      if (!modelsData?.models) return [];

      console.log('Processing models, count:', modelsData.models.length);

      let filtered = [...modelsData.models];

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(m =>
        m.name?.toLowerCase().includes(search) ||
        m.id?.toLowerCase().includes(search) ||
        m.description?.toLowerCase().includes(search)
      );
    }

    // Apply active/disabled filter
    if (filterActive === 'enabled') {
      filtered = filtered.filter(m => m.is_active);
    } else if (filterActive === 'disabled') {
      filtered = filtered.filter(m => !m.is_active);
    }

    // Apply sorting
    console.log('Sorting models...');
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'name':
          return (a.name || '').localeCompare(b.name || '');
        case 'price_asc':
          return (a.pricing?.prompt_per_1m || 0) - (b.pricing?.prompt_per_1m || 0);
        case 'price_desc':
          return (b.pricing?.prompt_per_1m || 0) - (a.pricing?.prompt_per_1m || 0);
        case 'context':
          return (b.context_length || 0) - (a.context_length || 0);
        default:
          return 0;
      }
    });

    console.log('Filtered and sorted:', filtered.length, 'models');
    return filtered;
    } catch (error) {
      console.error('Error in filteredAndSortedModels:', error);
      console.error('Error stack:', error.stack);
      return [];
    }
  }, [modelsData, searchTerm, filterActive, sortBy]);

  // Statistics
  const stats = useMemo(() => {
    try {
      if (!modelsData?.models || modelsData.models.length === 0) {
        return { total: 0, enabled: 0, disabled: 0, avgPrice: 0 };
      }

      console.log('Calculating stats...');
      const total = modelsData.models.length;
      const enabled = modelsData.models.filter(m => m.is_active).length;
      const disabled = total - enabled;
      const avgPrice = modelsData.models.reduce((sum, m) => sum + (m.pricing?.prompt_per_1m || 0), 0) / total;

      console.log('Stats:', { total, enabled, disabled, avgPrice });
      return { total, enabled, disabled, avgPrice };
    } catch (error) {
      console.error('Error in stats calculation:', error);
      return { total: 0, enabled: 0, disabled: 0, avgPrice: 0 };
    }
  }, [modelsData]);

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
            <div className="p-2 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
              <Brain className="h-8 w-8 text-white" />
            </div>
            LLM Model Catalog
          </h1>
          <p className={`mt-2 ${theme.text.secondary}`}>
            Manage and configure LLM models from OpenRouter
          </p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isLoading}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg ${theme.button.secondary} transition-all ${
            isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:opacity-80'
          }`}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Total Models</p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-1`}>{stats.total}</p>
            </div>
            <div className="p-3 rounded-lg bg-purple-500/20">
              <Brain className="h-6 w-6 text-purple-400" />
            </div>
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-green-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Enabled</p>
              <p className={`text-3xl font-bold text-green-400 mt-1`}>{stats.enabled}</p>
            </div>
            <div className="p-3 rounded-lg bg-green-500/20">
              <CheckCircle className="h-6 w-6 text-green-400" />
            </div>
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-gray-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Disabled</p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-1`}>{stats.disabled}</p>
            </div>
            <div className="p-3 rounded-lg bg-gray-500/20">
              <XCircle className="h-6 w-6 text-gray-400" />
            </div>
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Avg Price</p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-1`}>
                {formatPrice(stats.avgPrice)}
              </p>
              <p className={`text-xs ${theme.text.secondary} mt-1`}>per 1M tokens</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/20">
              <DollarSign className="h-6 w-6 text-blue-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className={`${theme.card} rounded-xl p-4 space-y-4`}>
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search models by name, ID, or description..."
              className={`w-full pl-10 pr-4 py-2 rounded-lg ${theme.input} border ${theme.border} focus:outline-none focus:ring-2 focus:ring-purple-500`}
            />
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg ${theme.button.secondary} transition-all`}
          >
            <Filter className="h-4 w-4" />
            <span>Filters</span>
            {showFilters ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>

        {/* Filter Options */}
        {showFilters && (
          <div className="overflow-hidden">
            <div className="flex items-center gap-4 pt-4 border-t ${theme.border}">
              {/* Status Filter */}
              <div className="flex items-center gap-2">
                <span className={`text-sm ${theme.text.secondary}`}>Status:</span>
                <select
                  value={filterActive}
                  onChange={(e) => setFilterActive(e.target.value)}
                  className={`px-3 py-1.5 rounded-lg ${theme.input} border ${theme.border} text-sm`}
                >
                  <option value="all">All Models</option>
                  <option value="enabled">Enabled Only</option>
                  <option value="disabled">Disabled Only</option>
                </select>
              </div>

              {/* Sort */}
              <div className="flex items-center gap-2">
                <span className={`text-sm ${theme.text.secondary}`}>Sort by:</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value)}
                  className={`px-3 py-1.5 rounded-lg ${theme.input} border ${theme.border} text-sm`}
                >
                  <option value="name">Name (A-Z)</option>
                  <option value="price_asc">Price (Low to High)</option>
                  <option value="price_desc">Price (High to Low)</option>
                  <option value="context">Context Length</option>
                </select>
              </div>

              {/* Results Count */}
              <div className="ml-auto">
                <span className={`text-sm ${theme.text.secondary}`}>
                  Showing {filteredAndSortedModels.length} of {stats.total} models
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Models Table */}
      <div className={`${theme.card} rounded-xl overflow-hidden`}>
        {/* Table Header */}
        <div className={`${theme.card} border-b ${theme.border} p-4 font-medium`}>
          <div className="flex items-center gap-4">
            <div className="w-12 flex-shrink-0">
              <span className={`text-xs ${theme.text.secondary}`}>Status</span>
            </div>
            <div className="flex-1 min-w-0">
              <span className={`text-xs ${theme.text.secondary}`}>Model Name</span>
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              <span className={`text-xs ${theme.text.secondary}`}>Features</span>
            </div>
            <div className="text-right flex-shrink-0 min-w-[80px]">
              <span className={`text-xs ${theme.text.secondary}`}>Context</span>
            </div>
            <div className="text-right flex-shrink-0 min-w-[100px]">
              <span className={`text-xs ${theme.text.secondary}`}>Input Cost</span>
            </div>
            <div className="text-right flex-shrink-0 min-w-[100px]">
              <span className={`text-xs ${theme.text.secondary}`}>Output Cost</span>
            </div>
            <div className="flex-shrink-0 w-5"></div>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className={`h-8 w-8 ${theme.text.secondary} animate-spin`} />
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="flex flex-col items-center justify-center py-12">
            <XCircle className="h-12 w-12 text-red-500 mb-4" />
            <p className={`text-lg ${theme.text.primary} mb-2`}>Failed to load models</p>
            <p className={`text-sm ${theme.text.secondary} mb-4`}>{error.message}</p>
            <button
              onClick={() => refetch()}
              className={`px-4 py-2 rounded-lg ${theme.button.primary}`}
            >
              Try Again
            </button>
          </div>
        )}

        {/* Models List (Simple Scrolling) */}
        {!isLoading && !error && filteredAndSortedModels.length > 0 && (
          <div className="max-h-[600px] overflow-y-auto">
            {filteredAndSortedModels.map((model) => (
              <ModelRow
                key={model.id}
                model={model}
                theme={theme}
                onToggle={handleToggle}
              />
            ))}
          </div>
        )}

        {/* Empty State */}
        {!isLoading && !error && filteredAndSortedModels.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12">
            <Search className={`h-12 w-12 ${theme.text.secondary} mb-4`} />
            <p className={`text-lg ${theme.text.primary} mb-2`}>No models found</p>
            <p className={`text-sm ${theme.text.secondary}`}>
              Try adjusting your search or filters
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
