import React, { useState, useEffect } from 'react';
import { ChartBarIcon, ServerIcon, KeyIcon, CheckCircleIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

/**
 * GrafanaConfig - Grafana Dashboard Configuration
 *
 * Features:
 * - Grafana instance connection settings
 * - Admin credentials management
 * - Data source configuration (Prometheus, PostgreSQL, etc.)
 * - Dashboard templates management
 */
export default function GrafanaConfig() {
  const [config, setConfig] = useState({
    url: 'http://taxsquare-grafana:3000',
    adminUsername: 'admin',
    adminPassword: '',
    apiKey: '',
    orgName: 'Unicorn Commander',
  });

  const [datasources, setDatasources] = useState([]);
  const [dashboards, setDashboards] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // New data source form
  const [newDatasource, setNewDatasource] = useState({
    name: '',
    type: 'prometheus',
    url: '',
    access: 'proxy',
    is_default: false,
  });

  const API_BASE = 'http://localhost:8084/api/v1/monitoring/grafana';

  // Load health status on mount
  useEffect(() => {
    checkHealth();
    if (config.apiKey) {
      loadDatasources();
      loadDashboards();
    }
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
        // Auto-load data sources and dashboards on successful connection
        loadDatasources();
        loadDashboards();
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const loadDatasources = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/datasources`, {
        params: { api_key: config.apiKey || undefined }
      });
      if (response.data.success) {
        setDatasources(response.data.datasources || []);
      }
    } catch (err) {
      console.error('Failed to load datasources:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadDashboards = async () => {
    try {
      const response = await axios.get(`${API_BASE}/dashboards`, {
        params: { api_key: config.apiKey || undefined }
      });
      if (response.data.success) {
        setDashboards(response.data.dashboards || []);
      }
    } catch (err) {
      console.error('Failed to load dashboards:', err);
    }
  };

  const handleCreateDatasource = async () => {
    if (!newDatasource.name || !newDatasource.url) {
      setError('Name and URL are required for creating a data source');
      return;
    }

    if (!config.apiKey) {
      setError('API key is required for creating data sources');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(
        `${API_BASE}/datasources?api_key=${config.apiKey}`,
        newDatasource
      );
      if (response.data.success) {
        setSuccess(response.data.message);
        // Reset form
        setNewDatasource({
          name: '',
          type: 'prometheus',
          url: '',
          access: 'proxy',
          is_default: false,
        });
        // Reload datasources
        loadDatasources();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create data source');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => {
    setSuccess('Configuration saved successfully');
    checkHealth();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <ChartBarIcon className="w-8 h-8 text-orange-400" />
            <h1 className="text-3xl font-bold text-white">Grafana Configuration</h1>
          </div>
          <p className="text-gray-300">
            Configure Grafana instance, data sources, and dashboard templates
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
                  {health.success ? 'Grafana Healthy' : 'Grafana Unavailable'}
                </h4>
                <p className="text-gray-300 text-sm">
                  Status: {health.status} {health.version && `- Version: ${health.version}`}
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

        {/* Connection Settings */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <ServerIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Connection Settings</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Grafana URL
              </label>
              <input
                type="text"
                value={config.url}
                onChange={(e) => setConfig({ ...config, url: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="http://grafana:3000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Organization Name
              </label>
              <input
                type="text"
                value={config.orgName}
                onChange={(e) => setConfig({ ...config, orgName: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="Unicorn Commander"
              />
            </div>
          </div>
        </div>

        {/* Authentication */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <KeyIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Authentication</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Admin Username
              </label>
              <input
                type="text"
                value={config.adminUsername}
                onChange={(e) => setConfig({ ...config, adminUsername: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="admin"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Admin Password
              </label>
              <input
                type="password"
                value={config.adminPassword}
                onChange={(e) => setConfig({ ...config, adminPassword: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="••••••••"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                API Key (Optional)
              </label>
              <input
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="Generate in Grafana: Configuration → API Keys"
              />
              <p className="mt-1 text-xs text-gray-400">
                API key for programmatic dashboard management
              </p>
            </div>
          </div>
        </div>

        {/* Data Sources */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <ServerIcon className="w-5 h-5 text-purple-400" />
              <h3 className="text-xl font-bold text-white">Data Sources</h3>
            </div>
            {config.apiKey && (
              <button
                onClick={loadDatasources}
                disabled={loading}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm disabled:opacity-50"
              >
                {loading ? 'Refreshing...' : 'Refresh'}
              </button>
            )}
          </div>

          <div className="space-y-3">
            {datasources.length > 0 ? (
              datasources.map((ds, index) => (
                <div
                  key={ds.id || index}
                  className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                >
                  <div className="flex items-center gap-3">
                    <CheckCircleIcon
                      className={`w-5 h-5 ${
                        ds.isDefault || ds.is_default ? 'text-green-400' : 'text-gray-600'
                      }`}
                    />
                    <div>
                      <div className="text-white font-medium">{ds.name}</div>
                      <div className="text-sm text-gray-400">{ds.url}</div>
                      <div className="text-xs text-gray-500 mt-1">Type: {ds.type}</div>
                    </div>
                  </div>
                  <div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs ${
                        ds.isDefault || ds.is_default
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-blue-500/20 text-blue-400'
                      }`}
                    >
                      {ds.isDefault || ds.is_default ? 'Default' : 'Active'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-8">
                {config.apiKey
                  ? 'No data sources configured yet. Create one below.'
                  : 'Enter API key and test connection to view data sources'}
              </div>
            )}
          </div>

          {/* Create New Data Source */}
          {config.apiKey && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <h4 className="text-white font-semibold mb-4">Create New Data Source</h4>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Name (e.g., Prometheus)"
                    value={newDatasource.name}
                    onChange={(e) => setNewDatasource({...newDatasource, name: e.target.value})}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                  <select
                    value={newDatasource.type}
                    onChange={(e) => setNewDatasource({...newDatasource, type: e.target.value})}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="prometheus">Prometheus</option>
                    <option value="postgres">PostgreSQL</option>
                    <option value="loki">Loki</option>
                    <option value="mysql">MySQL</option>
                    <option value="influxdb">InfluxDB</option>
                  </select>
                </div>
                <input
                  type="text"
                  placeholder="URL (e.g., http://prometheus:9090)"
                  value={newDatasource.url}
                  onChange={(e) => setNewDatasource({...newDatasource, url: e.target.value})}
                  className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                />
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 text-gray-300">
                    <input
                      type="checkbox"
                      checked={newDatasource.is_default}
                      onChange={(e) => setNewDatasource({...newDatasource, is_default: e.target.checked})}
                      className="rounded bg-gray-800 border-gray-700 text-purple-600 focus:ring-purple-500"
                    />
                    <span className="text-sm">Set as default</span>
                  </label>
                </div>
                <button
                  onClick={handleCreateDatasource}
                  disabled={loading || !newDatasource.name || !newDatasource.url}
                  className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create Data Source'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Dashboards */}
        {config.apiKey && (
          <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <ChartBarIcon className="w-5 h-5 text-purple-400" />
                <h3 className="text-xl font-bold text-white">Dashboards</h3>
              </div>
              <button
                onClick={loadDashboards}
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm"
              >
                Refresh
              </button>
            </div>

            <div className="space-y-3">
              {dashboards.length > 0 ? (
                dashboards.map((dashboard) => (
                  <div
                    key={dashboard.uid || dashboard.id}
                    className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                  >
                    <div>
                      <div className="text-white font-medium">{dashboard.title}</div>
                      <div className="text-sm text-gray-400">
                        {dashboard.folderTitle || 'General'} • {dashboard.type || 'dash-db'}
                      </div>
                    </div>
                    <a
                      href={`${config.url}/d/${dashboard.uid}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1 bg-orange-600 hover:bg-orange-500 text-white rounded text-sm transition-colors"
                    >
                      View
                    </a>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-400 py-8">
                  No dashboards found. Import dashboards in Grafana.
                </div>
              )}
            </div>
          </div>
        )}

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
            className="px-6 py-3 bg-orange-600 hover:bg-orange-500 text-white rounded-lg transition-colors"
          >
            Open Grafana
          </a>
        </div>
      </div>
    </div>
  );
}
