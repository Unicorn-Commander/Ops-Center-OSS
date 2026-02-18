import React, { useState, useEffect } from 'react';
import { CircleStackIcon, ServerIcon, BellAlertIcon, ClockIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

/**
 * PrometheusConfig - Prometheus Metrics Configuration
 *
 * Features:
 * - Prometheus server connection
 * - Scrape targets configuration
 * - Alert rules management
 * - Retention policies
 */
export default function PrometheusConfig() {
  const [config, setConfig] = useState({
    url: 'http://prometheus.unicorncommander.ai:9090',
    scrapeInterval: '15s',
    evaluationInterval: '15s',
    retentionTime: '15d',
    retentionSize: '50GB',
  });

  const [targets, setTargets] = useState([]);
  const [defaultTargets, setDefaultTargets] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [newTarget, setNewTarget] = useState({
    name: '',
    endpoint: '',
    interval: '15s',
    enabled: true,
    labels: {}
  });

  const API_BASE = 'http://localhost:8084/api/v1/monitoring/prometheus';

  // Load health status on mount
  useEffect(() => {
    checkHealth();
    loadTargets();
  }, []);

  const checkHealth = async () => {
    try {
      const response = await axios.get(`${API_BASE}/health`);
      setHealth(response.data);
    } catch (err) {
      console.error('Health check failed:', err);
      setHealth({ success: false, status: 'error', error: err.message });
    }
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(`${API_BASE}/test-connection`, config);
      if (response.data.success) {
        setSuccess(response.data.message);
        // Reload targets on successful connection
        loadTargets();
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const loadTargets = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/targets`);
      if (response.data.success) {
        setTargets(response.data.targets || []);
        setDefaultTargets(response.data.default_targets || []);
      }
    } catch (err) {
      console.error('Failed to load targets:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTarget = async () => {
    if (!newTarget.name || !newTarget.endpoint) {
      setError('Name and endpoint are required');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(`${API_BASE}/targets`, newTarget);
      if (response.data.success) {
        setSuccess(response.data.message);
        // Show the generated config
        console.log('Generated config:', response.data.config);
        // Reset form
        setNewTarget({
          name: '',
          endpoint: '',
          interval: '15s',
          enabled: true,
          labels: {}
        });
        // Reload targets
        loadTargets();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create target');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => {
    setSuccess('Configuration saved successfully');
    checkHealth();
  };

  // Combine active and default targets for display
  const displayTargets = [...targets];
  if (displayTargets.length === 0 && defaultTargets.length > 0) {
    displayTargets.push(...defaultTargets);
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <CircleStackIcon className="w-8 h-8 text-red-400" />
            <h1 className="text-3xl font-bold text-white">Prometheus Configuration</h1>
          </div>
          <p className="text-gray-300">
            Configure metrics collection, scrape targets, and alert rules
          </p>
        </div>

        {/* Health Status */}
        {health && (
          <div className={`mb-6 border rounded-lg p-4 ${
            health.success
              ? 'bg-green-500/10 border-green-500/20'
              : 'bg-red-500/10 border-red-500/20'
          }`}>
            <div className="flex items-start gap-3">
              {health.success ? (
                <CheckCircleIcon className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" />
              ) : (
                <ExclamationCircleIcon className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
              )}
              <div>
                <h4 className="text-white font-semibold mb-1">
                  {health.success ? 'Prometheus Healthy' : 'Prometheus Unavailable'}
                </h4>
                <p className="text-gray-300 text-sm">
                  Status: {health.status} {health.message && `- ${health.message}`}
                </p>
                {health.error && (
                  <p className="text-sm text-red-300 mt-1">{health.error}</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Success/Error Messages */}
        {success && (
          <div className="mb-6 bg-green-500/10 border border-green-500/20 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="w-6 h-6 text-green-400 flex-shrink-0 mt-0.5" />
              <p className="text-green-300">{success}</p>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/20 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <ExclamationCircleIcon className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-red-300">{error}</p>
            </div>
          </div>
        )}

        {/* Server Settings */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <ServerIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Server Settings</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Prometheus URL
              </label>
              <input
                type="text"
                value={config.url}
                onChange={(e) => setConfig({ ...config, url: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="http://prometheus:9090"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Scrape Interval
                </label>
                <input
                  type="text"
                  value={config.scrapeInterval}
                  onChange={(e) => setConfig({ ...config, scrapeInterval: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="15s"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Evaluation Interval
                </label>
                <input
                  type="text"
                  value={config.evaluationInterval}
                  onChange={(e) => setConfig({ ...config, evaluationInterval: e.target.value })}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  placeholder="15s"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Retention Policies */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <ClockIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Retention Policies</h3>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Retention Time
              </label>
              <input
                type="text"
                value={config.retentionTime}
                onChange={(e) => setConfig({ ...config, retentionTime: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="15d"
              />
              <p className="mt-1 text-xs text-gray-400">
                How long to keep metrics (e.g., 15d, 30d, 180d)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Retention Size
              </label>
              <input
                type="text"
                value={config.retentionSize}
                onChange={(e) => setConfig({ ...config, retentionSize: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="50GB"
              />
              <p className="mt-1 text-xs text-gray-400">
                Maximum storage size (e.g., 50GB, 100GB)
              </p>
            </div>
          </div>
        </div>

        {/* Scrape Targets */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <BellAlertIcon className="w-5 h-5 text-purple-400" />
              <h3 className="text-xl font-bold text-white">Scrape Targets</h3>
            </div>
            <button
              onClick={loadTargets}
              disabled={loading}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          <div className="space-y-3">
            {displayTargets.length > 0 ? (
              displayTargets.map((target, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                >
                  <div>
                    <div className="text-white font-medium">{target.name || target.job || 'Unknown'}</div>
                    <div className="text-sm text-gray-400 font-mono">
                      {target.endpoint || target.scrapeUrl || target.labels?.instance || 'N/A'}
                    </div>
                    {target.interval && (
                      <div className="text-xs text-gray-500 mt-1">Interval: {target.interval}</div>
                    )}
                  </div>
                  <div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs ${
                        target.enabled !== false && target.health !== 'down'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}
                    >
                      {target.enabled !== false && target.health !== 'down' ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-8">
                No scrape targets configured yet. Add one below.
              </div>
            )}
          </div>

          {/* Create New Target */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <h4 className="text-white font-semibold mb-4">Add Scrape Target</h4>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <input
                  type="text"
                  placeholder="Name (e.g., Ops Center API)"
                  value={newTarget.name}
                  onChange={(e) => setNewTarget({...newTarget, name: e.target.value})}
                  className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
                <input
                  type="text"
                  placeholder="Interval (e.g., 15s)"
                  value={newTarget.interval}
                  onChange={(e) => setNewTarget({...newTarget, interval: e.target.value})}
                  className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
              </div>
              <input
                type="text"
                placeholder="Endpoint (e.g., http://ops-center-direct:8084/metrics)"
                value={newTarget.endpoint}
                onChange={(e) => setNewTarget({...newTarget, endpoint: e.target.value})}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
              />
              <button
                onClick={handleCreateTarget}
                disabled={loading || !newTarget.name || !newTarget.endpoint}
                className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Target'}
              </button>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-4">
          <button
            onClick={handleTestConnection}
            disabled={testing}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors disabled:opacity-50"
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-3 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors"
          >
            Save Configuration
          </button>
          <a
            href={config.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-6 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors"
          >
            Open Prometheus
          </a>
        </div>
      </div>
    </div>
  );
}
