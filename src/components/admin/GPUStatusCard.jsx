/**
 * GPUStatusCard - Display GPU status with memory bars, utilization, and temperature
 * Designed for 2x NVIDIA Tesla P40 GPUs (24GB each) but works with any NVIDIA GPU
 * Fetches data internally with 5-second refresh interval
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CpuChipIcon,
  FireIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import ProgressBar from './ProgressBar';
import StatusIndicator from './StatusIndicator';

// API endpoint for GPU info
// Use the main status endpoint which includes gpu_info and handles missing GPUs gracefully
const GPU_API_ENDPOINT = '/api/v1/gpu-services/status';

// Refresh interval in milliseconds (5 seconds)
const REFRESH_INTERVAL = 5000;

// Format bytes to human readable
const formatMB = (mb) => {
  if (!mb && mb !== 0) return 'N/A';
  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(1)} GB`;
  }
  return `${mb} MB`;
};

// Get color based on usage percentage
const getUsageColor = (percent) => {
  if (percent > 90) return 'text-red-400';
  if (percent > 70) return 'text-yellow-400';
  return 'text-green-400';
};

// Get temperature color
const getTemperatureColor = (temp) => {
  if (!temp && temp !== 0) return 'text-gray-400';
  if (temp > 80) return 'text-red-400';
  if (temp > 65) return 'text-yellow-400';
  return 'text-green-400';
};

// Get temperature icon color gradient
const getTemperatureGradient = (temp) => {
  if (!temp && temp !== 0) return 'from-gray-500 to-gray-600';
  if (temp > 80) return 'from-red-500 to-red-600';
  if (temp > 65) return 'from-yellow-500 to-orange-500';
  return 'from-blue-500 to-cyan-500';
};

export default function GPUStatusCard({
  glassStyles = {},
  className = ''
}) {
  const [gpuInfo, setGpuInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Fetch GPU data from API
  const fetchGPUData = useCallback(async (isManualRefresh = false) => {
    if (isManualRefresh) {
      setIsRefreshing(true);
    }

    try {
      const response = await fetch(GPU_API_ENDPOINT, {
        credentials: 'include', // Include session cookies
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // No GPU available
          setGpuInfo(null);
          setError(null);
        } else if (response.status === 401) {
          setError('Authentication required');
        } else {
          const errorData = await response.json().catch(() => ({}));
          setError(errorData.detail || `HTTP ${response.status}`);
        }
        return;
      }

      const data = await response.json();
      // The /status endpoint returns { gpu_info: {...}, ... }
      // Extract gpu_info if present, otherwise use the data directly (for /gpu endpoint)
      const gpuData = data.gpu_info !== undefined ? data.gpu_info : data;
      setGpuInfo(gpuData);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch GPU data:', err);
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  // Initial fetch and interval setup
  useEffect(() => {
    fetchGPUData();

    const intervalId = setInterval(() => {
      fetchGPUData();
    }, REFRESH_INTERVAL);

    return () => clearInterval(intervalId);
  }, [fetchGPUData]);

  // Manual refresh handler
  const handleRefresh = () => {
    fetchGPUData(true);
  };

  // Error state
  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
            <ExclamationTriangleIcon className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white">GPU Status</h3>
            <p className="text-sm text-red-400">{error}</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
            title="Retry"
          >
            <ArrowPathIcon className={`h-4 w-4 text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <p className="text-sm text-gray-500">
          Unable to retrieve GPU information. Check server connectivity.
        </p>
      </motion.div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
            <CpuChipIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">GPU Status</h3>
            <p className="text-sm text-gray-400">Loading...</p>
          </div>
        </div>
        <div className="space-y-4">
          <div className="h-20 bg-gray-700/30 rounded-lg animate-pulse" />
          <div className="h-20 bg-gray-700/30 rounded-lg animate-pulse" />
        </div>
      </motion.div>
    );
  }

  // No GPU detected
  if (!gpuInfo || !gpuInfo.gpus || gpuInfo.gpus.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-gray-500 to-gray-600 rounded-xl flex items-center justify-center shadow-lg">
            <CpuChipIcon className="h-5 w-5 text-white" />
          </div>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-white">GPU Status</h3>
            <p className="text-sm text-gray-400">No GPU detected</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <ArrowPathIcon className={`h-4 w-4 text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
        <p className="text-sm text-gray-500">
          nvidia-smi may not be accessible or no NVIDIA GPU is installed.
        </p>
      </motion.div>
    );
  }

  const { gpus, total_memory_mb, used_memory_mb, free_memory_mb } = gpuInfo;
  const totalPercent = total_memory_mb > 0 ? (used_memory_mb / total_memory_mb) * 100 : 0;

  // Determine overall status
  const getOverallStatus = () => {
    const anyHighUtil = gpus.some(g => g.utilization_percent > 90);
    const anyHighMem = gpus.some(g => (g.memory_used_mb / g.memory_total_mb) * 100 > 95);
    const anyHighTemp = gpus.some(g => g.temperature && g.temperature > 80);

    if (anyHighTemp || anyHighMem) return 'critical';
    if (anyHighUtil || totalPercent > 80) return 'warning';
    return 'healthy';
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-xl flex items-center justify-center shadow-lg">
            <CpuChipIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">GPU Status</h3>
            <p className="text-sm text-gray-400">
              {gpus.length}x {gpus[0]?.name || 'NVIDIA GPU'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <StatusIndicator
            status={getOverallStatus()}
            showLabel
            animate
          />
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
            title="Refresh"
          >
            <ArrowPathIcon className={`h-4 w-4 text-gray-400 ${isRefreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Per-GPU Status */}
      <div className="space-y-4">
        <AnimatePresence mode="wait">
          {gpus.map((gpu, index) => {
            const usagePercent = gpu.memory_total_mb > 0
              ? (gpu.memory_used_mb / gpu.memory_total_mb) * 100
              : 0;

            return (
              <motion.div
                key={gpu.index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="backdrop-blur-sm bg-white/5 rounded-xl p-4 border border-white/10"
              >
                {/* GPU Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-white">
                      GPU {gpu.index}
                    </span>
                    <span className="text-xs text-gray-400 truncate max-w-[180px]">
                      {gpu.name}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    {/* Utilization */}
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs text-gray-500">Util:</span>
                      <span className={`text-xs font-medium ${getUsageColor(gpu.utilization_percent || 0)}`}>
                        {gpu.utilization_percent !== undefined ? `${gpu.utilization_percent}%` : 'N/A'}
                      </span>
                    </div>
                    {/* Temperature */}
                    {gpu.temperature !== undefined && (
                      <div className="flex items-center gap-1.5">
                        <FireIcon className={`h-3.5 w-3.5 ${getTemperatureColor(gpu.temperature)}`} />
                        <span className={`text-xs font-medium ${getTemperatureColor(gpu.temperature)}`}>
                          {gpu.temperature}°C
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Memory Bar */}
                <ProgressBar
                  value={gpu.memory_used_mb}
                  max={gpu.memory_total_mb}
                  type="vram"
                  height="sm"
                  showLabel={false}
                  animated={true}
                />

                {/* Memory Details */}
                <div className="flex justify-between mt-2 text-xs">
                  <span className={getUsageColor(usagePercent)}>
                    {formatMB(gpu.memory_used_mb)} used
                  </span>
                  <span className="text-gray-400">
                    {formatMB(gpu.memory_free_mb)} free
                  </span>
                  <span className="text-gray-500">
                    {formatMB(gpu.memory_total_mb)} total
                  </span>
                </div>

                {/* Utilization Bar (smaller, below memory) */}
                {gpu.utilization_percent !== undefined && (
                  <div className="mt-3 pt-3 border-t border-white/5">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs text-gray-500">GPU Compute</span>
                      <span className={`text-xs font-medium ${getUsageColor(gpu.utilization_percent)}`}>
                        {gpu.utilization_percent}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-700/50 rounded-full h-1.5 overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full ${
                          gpu.utilization_percent > 90 ? 'bg-red-500' :
                          gpu.utilization_percent > 70 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${gpu.utilization_percent}%` }}
                        transition={{ duration: 0.5 }}
                      />
                    </div>
                  </div>
                )}
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Total Summary (for multiple GPUs) */}
      {gpus.length > 1 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mt-4 pt-4 border-t border-white/10"
        >
          <div className="flex items-center justify-between">
            <span className="text-sm text-gray-400">Total VRAM</span>
            <span className={`text-sm font-medium ${getUsageColor(totalPercent)}`}>
              {formatMB(used_memory_mb)} / {formatMB(total_memory_mb)} ({totalPercent.toFixed(1)}%)
            </span>
          </div>
          <div className="mt-2">
            <ProgressBar
              value={used_memory_mb}
              max={total_memory_mb}
              type="vram"
              height="sm"
              showLabel={false}
              animated={true}
            />
          </div>
        </motion.div>
      )}

      {/* Last Updated */}
      {lastUpdated && (
        <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between">
          <span className="text-xs text-gray-500">
            Auto-refresh every 5s
          </span>
          <span className="text-xs text-gray-500">
            Updated: {lastUpdated.toLocaleTimeString()}
          </span>
        </div>
      )}
    </motion.div>
  );
}
