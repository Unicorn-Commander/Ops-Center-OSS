/**
 * CriticalServicesCard - Compact horizontal row showing critical infrastructure service health
 * Displays PostgreSQL, Redis, Keycloak, vLLM, and Traefik status as pills/badges
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheckIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

// Critical services configuration with display names and API key patterns
// These patterns match against Docker container names
const CRITICAL_SERVICES = [
  { key: 'postgresql', name: 'PostgreSQL', patterns: ['postgresql', 'postgres'] },
  { key: 'redis', name: 'Redis', patterns: ['redis'] },
  { key: 'keycloak', name: 'Keycloak', patterns: ['keycloak'] },
  { key: 'litellm', name: 'LiteLLM', patterns: ['litellm', 'llm-'] },
  { key: 'traefik', name: 'Traefik', patterns: ['traefik'] },
  { key: 'openwebui', name: 'Open-WebUI', patterns: ['open-webui', 'openwebui'] },
  { key: 'qdrant', name: 'Qdrant', patterns: ['qdrant'] },
];

// Status dot colors
const STATUS_DOT_COLORS = {
  up: 'bg-green-500',
  healthy: 'bg-green-500',
  running: 'bg-green-500',
  down: 'bg-red-500',
  error: 'bg-red-500',
  stopped: 'bg-red-500',
  unknown: 'bg-gray-500',
};

// Status text colors
const STATUS_TEXT_COLORS = {
  up: 'text-green-400',
  healthy: 'text-green-400',
  running: 'text-green-400',
  down: 'text-red-400',
  error: 'text-red-400',
  stopped: 'text-red-400',
  unknown: 'text-gray-400',
};

/**
 * Format seconds ago as human readable
 */
function formatSecondsAgo(seconds) {
  if (seconds < 60) {
    return `${seconds} second${seconds !== 1 ? 's' : ''} ago`;
  }
  const minutes = Math.floor(seconds / 60);
  return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
}

/**
 * Service Pill - compact badge showing service name and status
 */
function ServicePill({ name, status }) {
  const dotColor = STATUS_DOT_COLORS[status] || STATUS_DOT_COLORS.unknown;
  const textColor = STATUS_TEXT_COLORS[status] || STATUS_TEXT_COLORS.unknown;
  const isHealthy = status === 'up' || status === 'healthy' || status === 'running';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.05 }}
      className={`
        inline-flex items-center gap-2 px-3 py-1.5 rounded-full
        backdrop-blur-sm border transition-all duration-200
        ${isHealthy
          ? 'bg-green-500/10 border-green-500/30 hover:bg-green-500/20'
          : status === 'unknown'
            ? 'bg-gray-500/10 border-gray-500/30 hover:bg-gray-500/20'
            : 'bg-red-500/10 border-red-500/30 hover:bg-red-500/20'
        }
      `}
    >
      {/* Status dot */}
      <span
        className={`w-2 h-2 rounded-full ${dotColor} ${isHealthy ? 'animate-pulse' : ''}`}
        title={status}
      />
      {/* Service name */}
      <span className={`text-sm font-medium ${textColor}`}>
        {name}
      </span>
    </motion.div>
  );
}

export default function CriticalServicesCard({
  glassStyles = {},
  className = ''
}) {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastChecked, setLastChecked] = useState(null);
  const [secondsAgo, setSecondsAgo] = useState(0);
  const [error, setError] = useState(null);

  /**
   * Match a service from API response to our critical service definitions
   */
  const getServiceStatus = useCallback((serviceConfig, apiServices) => {
    // Try to find a matching service from the API response
    const matchedService = apiServices.find(s => {
      if (!s?.name) return false;
      const serviceName = s.name.toLowerCase();
      return serviceConfig.patterns.some(p => serviceName.includes(p));
    });

    if (!matchedService) return 'unknown';

    // Normalize status values
    const status = matchedService.status?.toLowerCase() || 'unknown';
    if (status === 'running' || status === 'healthy' || status === 'up') return 'up';
    if (status === 'stopped' || status === 'exited' || status === 'down' || status === 'error') return 'down';
    return 'unknown';
  }, []);

  /**
   * Fetch service status from API
   */
  const fetchServiceStatus = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch from /api/v1/services which returns Docker container statuses
      const response = await fetch('/api/v1/services', {
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      // The /api/v1/services endpoint returns an array directly
      const apiServices = Array.isArray(data) ? data : (data.services || data.docker_services || data.containers || []);

      // Map critical services to their statuses - only include services that are found
      const serviceStatuses = CRITICAL_SERVICES
        .map(config => ({
          ...config,
          status: getServiceStatus(config, apiServices),
        }))
        .filter(s => s.status !== 'unknown'); // Only show services that are actually detected

      setServices(serviceStatuses);
      setLastChecked(new Date());
      setSecondsAgo(0);
    } catch (err) {
      console.error('Failed to fetch service status:', err);
      setError(err.message);
      // Set all services to unknown on error
      setServices(CRITICAL_SERVICES.map(config => ({
        ...config,
        status: 'unknown',
      })));
    } finally {
      setLoading(false);
    }
  }, [getServiceStatus]);

  // Initial fetch and 10-second refresh interval
  useEffect(() => {
    fetchServiceStatus();

    const refreshInterval = setInterval(() => {
      fetchServiceStatus();
    }, 10000);

    return () => clearInterval(refreshInterval);
  }, [fetchServiceStatus]);

  // Update seconds ago counter every second
  useEffect(() => {
    if (!lastChecked) return;

    const ticker = setInterval(() => {
      const now = new Date();
      const diff = Math.floor((now - lastChecked) / 1000);
      setSecondsAgo(diff);
    }, 1000);

    return () => clearInterval(ticker);
  }, [lastChecked]);

  // Calculate overall health stats
  const healthyCount = services.filter(s => s.status === 'up').length;
  const totalCount = services.length;
  const allHealthy = healthyCount === totalCount && totalCount > 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`
        ${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'}
        rounded-xl p-4 shadow-lg
        ${className}
      `}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className={`
            w-8 h-8 rounded-lg flex items-center justify-center shadow-md
            ${allHealthy
              ? 'bg-gradient-to-br from-green-500 to-emerald-500'
              : 'bg-gradient-to-br from-yellow-500 to-orange-500'
            }
          `}>
            <ShieldCheckIcon className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Infrastructure</h3>
            <p className="text-xs text-gray-400">
              {healthyCount}/{totalCount} healthy
            </p>
          </div>
        </div>

        {/* Refresh button */}
        <button
          onClick={fetchServiceStatus}
          disabled={loading}
          className="p-1.5 rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50"
          title="Refresh status"
        >
          <ArrowPathIcon
            className={`h-4 w-4 text-gray-400 hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`}
          />
        </button>
      </div>

      {/* Services row - horizontal scroll on mobile, wraps on larger screens */}
      <div className="flex flex-wrap gap-2">
        {services.map((service) => (
          <ServicePill
            key={service.key}
            name={service.name}
            status={service.status}
          />
        ))}

        {/* Loading state */}
        {loading && services.length === 0 && (
          <>
            {CRITICAL_SERVICES.map((s) => (
              <div
                key={s.key}
                className="h-8 w-24 bg-gray-700/30 rounded-full animate-pulse"
              />
            ))}
          </>
        )}
      </div>

      {/* Error message */}
      {error && (
        <p className="text-xs text-red-400 mt-2">
          Failed to fetch: {error}
        </p>
      )}

      {/* Last checked timestamp */}
      {lastChecked && (
        <p className="text-xs text-gray-500 mt-3 text-center">
          Last checked: {formatSecondsAgo(secondsAgo)}
        </p>
      )}
    </motion.div>
  );
}
