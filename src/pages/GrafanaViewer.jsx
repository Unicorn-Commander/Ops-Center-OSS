import React, { useState, useEffect } from 'react';
import {
  ChartBarIcon,
  ArrowsPointingOutIcon,
  ArrowsPointingInIcon,
  SunIcon,
  MoonIcon,
  ClockIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';
import GrafanaDashboard from '../components/GrafanaDashboard';

/**
 * GrafanaViewer - Full Grafana Dashboard Viewer Page
 *
 * Features:
 * - Dashboard selector dropdown
 * - Theme toggle (light/dark)
 * - Full-screen toggle
 * - Refresh interval selector
 * - Time range selector
 * - Direct link to Grafana
 */
export default function GrafanaViewer() {
  const [dashboards, setDashboards] = useState([]);
  const [selectedDashboard, setSelectedDashboard] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [fullscreen, setFullscreen] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(null);
  const [timeRange, setTimeRange] = useState({ from: 'now-6h', to: 'now' });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_BASE = 'http://localhost:8084/api/v1/monitoring/grafana';
  const GRAFANA_URL = 'http://localhost:3102';

  useEffect(() => {
    loadDashboards();
  }, []);

  const loadDashboards = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`${API_BASE}/dashboards`);

      if (response.data.success && response.data.dashboards.length > 0) {
        setDashboards(response.data.dashboards);
        // Auto-select first dashboard
        setSelectedDashboard(response.data.dashboards[0]);
      } else if (response.data.success && response.data.dashboards.length === 0) {
        setError('No dashboards found in Grafana. Please import dashboards first.');
      }
    } catch (err) {
      console.error('Failed to load dashboards:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load dashboards');
    } finally {
      setLoading(false);
    }
  };

  const handleDashboardChange = (event) => {
    const uid = event.target.value;
    const dashboard = dashboards.find(d => d.uid === uid);
    setSelectedDashboard(dashboard);
  };

  const toggleFullscreen = () => {
    if (!fullscreen) {
      document.documentElement.requestFullscreen?.();
    } else {
      document.exitFullscreen?.();
    }
    setFullscreen(!fullscreen);
  };

  const timeRangeOptions = [
    { label: 'Last 5 minutes', value: { from: 'now-5m', to: 'now' } },
    { label: 'Last 15 minutes', value: { from: 'now-15m', to: 'now' } },
    { label: 'Last 30 minutes', value: { from: 'now-30m', to: 'now' } },
    { label: 'Last 1 hour', value: { from: 'now-1h', to: 'now' } },
    { label: 'Last 6 hours', value: { from: 'now-6h', to: 'now' } },
    { label: 'Last 12 hours', value: { from: 'now-12h', to: 'now' } },
    { label: 'Last 24 hours', value: { from: 'now-24h', to: 'now' } },
    { label: 'Last 7 days', value: { from: 'now-7d', to: 'now' } }
  ];

  const refreshOptions = [
    { label: 'Off', value: null },
    { label: '30 seconds', value: 30 },
    { label: '1 minute', value: 60 },
    { label: '5 minutes', value: 300 },
    { label: '15 minutes', value: 900 }
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-6 flex items-center justify-center">
        <div className="text-center">
          <ChartBarIcon className="w-16 h-16 text-orange-400 animate-pulse mx-auto mb-4" />
          <p className="text-white text-lg">Loading Grafana dashboards...</p>
        </div>
      </div>
    );
  }

  if (error && !selectedDashboard) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-8 text-center">
            <ChartBarIcon className="w-16 h-16 text-red-400 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-red-300 mb-2">Dashboard Error</h3>
            <p className="text-gray-300 mb-4">{error}</p>
            <div className="flex gap-3 justify-center">
              <button
                onClick={loadDashboards}
                className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
              >
                Retry
              </button>
              <a
                href={GRAFANA_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="px-6 py-3 bg-orange-600 hover:bg-orange-500 text-white rounded-lg transition-colors inline-flex items-center gap-2"
              >
                Open Grafana
                <ArrowTopRightOnSquareIcon className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-screen p-6 ${fullscreen ? 'bg-black' : 'bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900'}`}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        {!fullscreen && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <ChartBarIcon className="w-8 h-8 text-orange-400" />
                <h1 className="text-3xl font-bold text-white">Grafana Dashboards</h1>
              </div>
              <a
                href={GRAFANA_URL}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg transition-colors inline-flex items-center gap-2"
              >
                Open Grafana
                <ArrowTopRightOnSquareIcon className="w-5 h-5" />
              </a>
            </div>
            <p className="text-gray-300">
              View and interact with Grafana monitoring dashboards
            </p>
          </div>
        )}

        {/* Controls */}
        {!fullscreen && (
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-4 border border-white/20 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {/* Dashboard Selector */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Dashboard
                </label>
                <select
                  value={selectedDashboard?.uid || ''}
                  onChange={handleDashboardChange}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  {dashboards.map(dashboard => (
                    <option key={dashboard.uid} value={dashboard.uid}>
                      {dashboard.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Time Range */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <ClockIcon className="w-4 h-4 inline mr-1" />
                  Time Range
                </label>
                <select
                  value={JSON.stringify(timeRange)}
                  onChange={(e) => setTimeRange(JSON.parse(e.target.value))}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  {timeRangeOptions.map((option, idx) => (
                    <option key={idx} value={JSON.stringify(option.value)}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Refresh Interval */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Auto Refresh
                </label>
                <select
                  value={refreshInterval || ''}
                  onChange={(e) => setRefreshInterval(e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                >
                  {refreshOptions.map((option, idx) => (
                    <option key={idx} value={option.value || ''}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Actions */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Display
                </label>
                <div className="flex gap-2">
                  {/* Theme Toggle */}
                  <button
                    onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                    className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                    title={theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme'}
                  >
                    {theme === 'dark' ? (
                      <SunIcon className="w-5 h-5" />
                    ) : (
                      <MoonIcon className="w-5 h-5" />
                    )}
                  </button>

                  {/* Fullscreen Toggle */}
                  <button
                    onClick={toggleFullscreen}
                    className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                    title={fullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
                  >
                    {fullscreen ? (
                      <ArrowsPointingInIcon className="w-5 h-5" />
                    ) : (
                      <ArrowsPointingOutIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Dashboard Viewer */}
        {selectedDashboard && (
          <div className={fullscreen ? 'h-screen' : ''}>
            <GrafanaDashboard
              dashboardUid={selectedDashboard.uid}
              height={fullscreen ? window.innerHeight : 800}
              theme={theme}
              refreshInterval={refreshInterval}
              timeRange={timeRange}
              kiosk="tv"
              onError={(err) => setError(err)}
            />
          </div>
        )}

        {/* Exit Fullscreen Button (only in fullscreen mode) */}
        {fullscreen && (
          <button
            onClick={toggleFullscreen}
            className="fixed top-4 right-4 px-4 py-2 bg-gray-900/90 hover:bg-gray-800/90 text-white rounded-lg transition-colors flex items-center gap-2 z-50"
          >
            <ArrowsPointingInIcon className="w-5 h-5" />
            Exit Fullscreen
          </button>
        )}
      </div>
    </div>
  );
}
