/**
 * LocalInferenceCard - Display local inference provider status
 * Shows detected providers (Ollama, vLLM, llama.cpp), health status, and loaded models
 * Fetches data internally with 30-second refresh interval
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ServerStackIcon,
  CubeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  CpuChipIcon,
  CircleStackIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

// Provider icons and colors
const PROVIDER_CONFIG = {
  ollama: {
    name: 'Ollama',
    color: 'from-blue-500 to-cyan-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
    icon: CubeIcon
  },
  vllm: {
    name: 'vLLM',
    color: 'from-purple-500 to-pink-500',
    textColor: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
    icon: SparklesIcon
  },
  'llama.cpp': {
    name: 'llama.cpp',
    color: 'from-orange-500 to-yellow-500',
    textColor: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    icon: CpuChipIcon
  },
  'llama-cpp': {
    name: 'llama.cpp',
    color: 'from-orange-500 to-yellow-500',
    textColor: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    icon: CpuChipIcon
  },
  llamacpp: {
    name: 'llama.cpp',
    color: 'from-orange-500 to-yellow-500',
    textColor: 'text-orange-400',
    bgColor: 'bg-orange-500/20',
    icon: CpuChipIcon
  }
};

// Status pill component
function StatusPill({ status }) {
  const normalizedStatus = status?.toLowerCase() || 'unknown';

  const config = {
    healthy: { color: 'bg-green-500', text: 'Healthy', Icon: CheckCircleIcon },
    up: { color: 'bg-green-500', text: 'Up', Icon: CheckCircleIcon },
    running: { color: 'bg-green-500', text: 'Running', Icon: CheckCircleIcon },
    active: { color: 'bg-green-500', text: 'Active', Icon: CheckCircleIcon },
    down: { color: 'bg-red-500', text: 'Down', Icon: XCircleIcon },
    error: { color: 'bg-red-500', text: 'Error', Icon: XCircleIcon },
    unhealthy: { color: 'bg-red-500', text: 'Unhealthy', Icon: XCircleIcon },
    stopped: { color: 'bg-gray-500', text: 'Stopped', Icon: ExclamationTriangleIcon },
    unknown: { color: 'bg-gray-500', text: 'Unknown', Icon: ExclamationTriangleIcon },
    not_detected: { color: 'bg-gray-500', text: 'Not Detected', Icon: ExclamationTriangleIcon }
  };

  const { color, text, Icon } = config[normalizedStatus] || config.unknown;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color} text-white`}>
      <Icon className="h-3 w-3" />
      {text}
    </span>
  );
}

// Format bytes to human readable
function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// Format VRAM usage
function formatVRAM(vram) {
  if (!vram) return null;
  if (typeof vram === 'number') {
    return formatBytes(vram);
  }
  if (typeof vram === 'string') {
    return vram;
  }
  return null;
}

// Check if provider is healthy
function isProviderHealthy(provider) {
  const status = (provider.status || provider.health || '').toLowerCase();
  return ['healthy', 'up', 'running', 'active'].includes(status);
}

// Provider card component
function ProviderRow({ provider, isExpanded, onToggle }) {
  const providerId = (provider.id || provider.type || provider.name || '').toLowerCase();
  const config = PROVIDER_CONFIG[providerId] || {
    name: provider.name || provider.type || provider.id || 'Unknown',
    color: 'from-gray-500 to-gray-600',
    textColor: 'text-gray-400',
    bgColor: 'bg-gray-500/20',
    icon: CubeIcon
  };

  const Icon = config.icon;
  const hasModels = provider.models && provider.models.length > 0;
  const modelCount = provider.models?.length || 0;
  const isHealthy = isProviderHealthy(provider);

  return (
    <div className={`border rounded-lg overflow-hidden ${
      isHealthy ? 'border-green-500/30 bg-green-500/5' : 'border-white/10 bg-white/5'
    }`}>
      {/* Provider header */}
      <div
        className={`flex items-center gap-3 px-4 py-3 ${hasModels ? 'cursor-pointer hover:bg-white/5' : ''} transition-colors`}
        onClick={() => hasModels && onToggle()}
      >
        {/* Provider icon */}
        <div className={`w-8 h-8 bg-gradient-to-br ${config.color} rounded-lg flex items-center justify-center shadow-lg flex-shrink-0`}>
          <Icon className="h-4 w-4 text-white" />
        </div>

        {/* Provider name */}
        <div className="flex-1 min-w-0">
          <span className="text-sm font-medium text-white">{config.name}</span>
          {provider.url && (
            <p className="text-xs text-gray-500 truncate">{provider.url}</p>
          )}
        </div>

        {/* Model count badge */}
        {modelCount > 0 && (
          <span className={`text-xs ${config.bgColor} ${config.textColor} px-2 py-0.5 rounded-full`}>
            {modelCount} model{modelCount !== 1 ? 's' : ''}
          </span>
        )}

        {/* Status */}
        <StatusPill status={provider.status || provider.health} />

        {/* Expand icon */}
        {hasModels && (
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.2 }}
          >
            <ChevronDownIcon className="h-4 w-4 text-gray-500" />
          </motion.div>
        )}
      </div>

      {/* Models list (expanded) */}
      <AnimatePresence>
        {isExpanded && hasModels && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="border-t border-white/5 bg-black/20"
          >
            <div className="p-3 space-y-2">
              {provider.models.map((model, idx) => (
                <div
                  key={model.id || model.name || idx}
                  className="flex items-center gap-3 px-3 py-2 rounded-lg bg-white/5"
                >
                  <CircleStackIcon className="h-4 w-4 text-gray-500 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{model.name || model.id}</p>
                    {model.context_length && (
                      <p className="text-xs text-gray-500">{model.context_length.toLocaleString()} ctx</p>
                    )}
                  </div>
                  {(model.vram || model.vram_usage) && (
                    <span className="text-xs text-gray-400 bg-gray-700/50 px-2 py-0.5 rounded">
                      {formatVRAM(model.vram || model.vram_usage)} VRAM
                    </span>
                  )}
                  {model.loaded && (
                    <span className="text-xs text-green-400 bg-green-500/20 px-2 py-0.5 rounded">
                      Loaded
                    </span>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function LocalInferenceCard({
  glassStyles = {},
  className = ''
}) {
  const [moduleStatus, setModuleStatus] = useState(null);
  const [providers, setProviders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notConfigured, setNotConfigured] = useState(false);
  const [expandedProviders, setExpandedProviders] = useState({});
  const [lastRefresh, setLastRefresh] = useState(null);

  // Fetch data from API
  const fetchData = useCallback(async () => {
    try {
      setError(null);

      // Fetch module status and providers in parallel
      const [statusRes, providersRes] = await Promise.allSettled([
        fetch('/api/v1/local-inference/status'),
        fetch('/api/v1/local-inference/providers')
      ]);

      // Handle status response
      if (statusRes.status === 'fulfilled') {
        if (statusRes.value.ok) {
          const statusData = await statusRes.value.json();
          setModuleStatus(statusData);
          setNotConfigured(false);
        } else if (statusRes.value.status === 404) {
          setNotConfigured(true);
          setModuleStatus(null);
        } else {
          // Non-404 error - module exists but returned error
          setNotConfigured(true);
        }
      } else {
        // Network error or module not available
        setNotConfigured(true);
      }

      // Handle providers response
      if (providersRes.status === 'fulfilled' && providersRes.value.ok) {
        const providersData = await providersRes.value.json();
        setProviders(Array.isArray(providersData) ? providersData : providersData.providers || []);
      } else if (providersRes.status === 'fulfilled' && providersRes.value.status === 404) {
        // Providers endpoint doesn't exist
        setProviders([]);
      } else {
        setProviders([]);
      }

      setLastRefresh(new Date());
    } catch (err) {
      console.error('Error fetching local inference data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch and refresh interval (30 seconds)
  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 30000);

    return () => clearInterval(interval);
  }, [fetchData]);

  // Toggle provider expansion
  const toggleProvider = (providerId) => {
    setExpandedProviders(prev => ({
      ...prev,
      [providerId]: !prev[providerId]
    }));
  };

  // Calculate stats
  const healthyCount = providers.filter(p => isProviderHealthy(p)).length;
  const totalModels = providers.reduce((sum, p) => sum + (p.models?.length || 0), 0);

  // Module enabled status
  const moduleEnabled = moduleStatus?.enabled ?? false;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
            <ServerStackIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Local Inference</h3>
            <p className="text-sm text-gray-400">
              {notConfigured ? (
                'Not configured'
              ) : loading ? (
                'Loading...'
              ) : (
                <>
                  {providers.length} provider{providers.length !== 1 ? 's' : ''}
                  {healthyCount > 0 && <span className="text-green-400 ml-1">({healthyCount} healthy)</span>}
                  {totalModels > 0 && <span className="text-gray-500 ml-1">- {totalModels} models</span>}
                </>
              )}
            </p>
          </div>
        </div>

        {/* Refresh button and module status */}
        <div className="flex items-center gap-2">
          {!notConfigured && moduleStatus && (
            <span className={`text-xs px-2 py-1 rounded-full ${moduleEnabled ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
              {moduleEnabled ? 'Enabled' : 'Disabled'}
            </span>
          )}
          <button
            onClick={fetchData}
            disabled={loading}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <ArrowPathIcon className={`h-4 w-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Loading State */}
      {loading && providers.length === 0 && !notConfigured && (
        <div className="space-y-3">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-700/30 rounded-lg animate-pulse" />
          ))}
        </div>
      )}

      {/* Not Configured State */}
      {!loading && notConfigured && (
        <div className="text-center py-8">
          <CpuChipIcon className="h-12 w-12 mx-auto mb-3 text-gray-600" />
          <p className="text-gray-400 text-sm mb-2">Local inference not configured</p>
          <p className="text-gray-500 text-xs">
            Enable local inference providers (Ollama, vLLM, llama.cpp) to see them here.
          </p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && !notConfigured && (
        <div className="text-center py-8">
          <XCircleIcon className="h-10 w-10 mx-auto mb-2 text-red-400 opacity-50" />
          <p className="text-sm text-red-400">{error}</p>
          <button
            onClick={fetchData}
            className="mt-3 text-xs text-blue-400 hover:text-blue-300"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty State (no providers detected) */}
      {!loading && !error && !notConfigured && providers.length === 0 && (
        <div className="text-center py-8">
          <ServerStackIcon className="h-10 w-10 mx-auto mb-2 text-gray-600" />
          <p className="text-gray-400 text-sm mb-1">No providers detected</p>
          <p className="text-gray-500 text-xs">
            Start Ollama, vLLM, or llama.cpp to see them here.
          </p>
        </div>
      )}

      {/* Providers List */}
      {!loading && !error && !notConfigured && providers.length > 0 && (
        <div className="space-y-2">
          <AnimatePresence>
            {providers.map((provider, index) => {
              const providerId = provider.id || provider.name || provider.type || `provider-${index}`;
              return (
                <motion.div
                  key={providerId}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <ProviderRow
                    provider={provider}
                    isExpanded={expandedProviders[providerId]}
                    onToggle={() => toggleProvider(providerId)}
                  />
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}

      {/* Last refresh timestamp */}
      {lastRefresh && !notConfigured && (
        <p className="text-xs text-gray-600 mt-4 text-center">
          Last updated: {lastRefresh.toLocaleTimeString()}
        </p>
      )}
    </motion.div>
  );
}
