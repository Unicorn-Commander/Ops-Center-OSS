import React, { useState, useEffect } from 'react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

/**
 * GrafanaDashboard - Embeddable Grafana Dashboard Component
 *
 * Props:
 * - dashboardUid: Grafana dashboard UID (required)
 * - height: iframe height in pixels (default: 600)
 * - theme: 'light' or 'dark' (default: 'dark')
 * - refreshInterval: auto-refresh in seconds (optional, e.g., 30, 60, 300)
 * - timeRange: time range object { from: 'now-6h', to: 'now' }
 * - kiosk: kiosk mode - 'tv' (clean) or 'full' (fullscreen)
 * - onError: callback function for error handling
 * - onLoad: callback function when iframe loads
 */
export default function GrafanaDashboard({
  dashboardUid,
  height = 600,
  theme = 'dark',
  refreshInterval,
  timeRange = { from: 'now-6h', to: 'now' },
  kiosk = 'tv',
  onError,
  onLoad
}) {
  const [embedUrl, setEmbedUrl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [iframeKey, setIframeKey] = useState(0); // For forcing iframe reload

  const API_BASE = 'http://localhost:8084/api/v1/monitoring/grafana';

  useEffect(() => {
    fetchEmbedUrl();
  }, [dashboardUid, theme, refreshInterval, timeRange.from, timeRange.to, kiosk]);

  const fetchEmbedUrl = async () => {
    setLoading(true);
    setError(null);

    try {
      // Build query parameters
      const params = new URLSearchParams({
        theme,
        from_time: timeRange.from,
        to_time: timeRange.to,
        kiosk
      });

      if (refreshInterval) {
        params.append('refresh', `${refreshInterval}s`);
      }

      const response = await axios.get(
        `${API_BASE}/dashboards/${dashboardUid}/embed-url?${params.toString()}`
      );

      if (response.data.success) {
        // Use external_url for browser access (port 3102)
        setEmbedUrl(response.data.external_url);
        setLoading(false);
      } else {
        throw new Error('Failed to generate embed URL');
      }
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load dashboard';
      setError(errorMessage);
      setLoading(false);

      if (onError) {
        onError(errorMessage);
      }
    }
  };

  const handleIframeLoad = () => {
    if (onLoad) {
      onLoad();
    }
  };

  const handleRefresh = () => {
    setIframeKey(prev => prev + 1); // Force iframe reload
    fetchEmbedUrl();
  };

  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-gray-800/50 rounded-lg border border-gray-700"
        style={{ height: `${height}px` }}
      >
        <div className="text-center">
          <ArrowPathIcon className="w-8 h-8 text-purple-400 animate-spin mx-auto mb-2" />
          <p className="text-gray-300">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="flex items-center justify-center bg-red-500/10 border border-red-500/20 rounded-lg p-6"
        style={{ height: `${height}px` }}
      >
        <div className="text-center max-w-md">
          <ExclamationTriangleIcon className="w-12 h-12 text-red-400 mx-auto mb-3" />
          <h4 className="text-lg font-semibold text-red-300 mb-2">Dashboard Error</h4>
          <p className="text-gray-300 text-sm mb-4">{error}</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors text-sm"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="grafana-dashboard-wrapper relative">
      {/* Refresh button overlay */}
      <button
        onClick={handleRefresh}
        className="absolute top-2 right-2 z-10 px-3 py-1 bg-gray-800/90 hover:bg-gray-700/90 text-white rounded text-sm flex items-center gap-1 transition-colors"
        title="Refresh dashboard"
      >
        <ArrowPathIcon className="w-4 h-4" />
        Refresh
      </button>

      {/* Embedded Grafana iframe */}
      <iframe
        key={iframeKey}
        src={embedUrl}
        width="100%"
        height={height}
        frameBorder="0"
        onLoad={handleIframeLoad}
        className="rounded-lg border border-gray-700"
        title={`Grafana Dashboard ${dashboardUid}`}
        allow="fullscreen"
      />
    </div>
  );
}
