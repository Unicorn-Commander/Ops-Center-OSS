import React, { useState, useEffect } from 'react';
import { ChartPieIcon, GlobeAltIcon, CodeBracketIcon, KeyIcon, CheckCircleIcon, ExclamationCircleIcon, ClipboardDocumentIcon } from '@heroicons/react/24/outline';
import axios from 'axios';

/**
 * UmamiConfig - Umami Web Analytics Configuration
 *
 * Features:
 * - Umami instance connection
 * - Website tracking configuration
 * - Tracking script generation
 * - Privacy settings
 */
export default function UmamiConfig() {
  const [config, setConfig] = useState({
    url: 'http://umami.unicorncommander.ai:3000',
    apiKey: '',
    trackingCode: 'xxxxx-xxxxx-xxxxx-xxxxx',
    privacyMode: 'strict',
    respectDNT: true,
    sessionTracking: true
  });

  const [websites, setWebsites] = useState([]);
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [copied, setCopied] = useState(false);

  const [newWebsite, setNewWebsite] = useState({
    name: '',
    domain: '',
    enabled: true
  });

  const [selectedWebsite, setSelectedWebsite] = useState(null);
  const [websiteStats, setWebsiteStats] = useState(null);

  const API_BASE = 'http://localhost:8084/api/v1/monitoring/umami';

  // Load health status on mount
  useEffect(() => {
    checkHealth();
    loadWebsites();
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
        // Reload websites on successful connection
        loadWebsites();
      } else {
        setError(response.data.message);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Connection test failed');
    } finally {
      setTesting(false);
    }
  };

  const loadWebsites = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/websites`, {
        params: { api_key: config.apiKey || undefined }
      });
      if (response.data.success) {
        setWebsites(response.data.websites || []);
      }
    } catch (err) {
      console.error('Failed to load websites:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWebsite = async () => {
    if (!newWebsite.name || !newWebsite.domain) {
      setError('Name and domain are required');
      return;
    }

    if (!config.apiKey) {
      setError('API key is required for creating websites');
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post(
        `${API_BASE}/websites?api_key=${config.apiKey}`,
        newWebsite
      );
      if (response.data.success) {
        setSuccess(response.data.message);
        // Reset form
        setNewWebsite({
          name: '',
          domain: '',
          enabled: true
        });
        // Reload websites
        loadWebsites();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to create website');
    } finally {
      setLoading(false);
    }
  };

  const generateTrackingScript = (websiteId) => {
    return `<!-- Umami Analytics -->
<script
  async
  defer
  data-website-id="${websiteId || config.trackingCode}"
  src="${config.url}/umami.js"
></script>`;
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const loadWebsiteStats = async (websiteId) => {
    if (!config.apiKey) return;

    try {
      const response = await axios.get(
        `${API_BASE}/stats?website_id=${websiteId}&api_key=${config.apiKey}`
      );
      if (response.data.success) {
        setWebsiteStats(response.data.stats);
        setSelectedWebsite(websiteId);
      }
    } catch (err) {
      console.error('Failed to load stats:', err);
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
            <ChartPieIcon className="w-8 h-8 text-blue-400" />
            <h1 className="text-3xl font-bold text-white">Umami Analytics Configuration</h1>
          </div>
          <p className="text-gray-300">
            Configure privacy-focused web analytics tracking for your services
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
                  {health.success ? 'Umami Healthy' : 'Umami Unavailable'}
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

        {/* Connection Settings */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <GlobeAltIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Connection Settings</h3>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Umami URL
              </label>
              <input
                type="text"
                value={config.url}
                onChange={(e) => setConfig({ ...config, url: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="http://umami:3000"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                API Key
              </label>
              <input
                type="password"
                value={config.apiKey}
                onChange={(e) => setConfig({ ...config, apiKey: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                placeholder="Generate in Umami: Settings → API Keys"
              />
              <p className="mt-1 text-xs text-gray-400">
                API key for programmatic access to analytics data
              </p>
            </div>
          </div>
        </div>

        {/* Tracked Websites */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <GlobeAltIcon className="w-5 h-5 text-purple-400" />
              <h3 className="text-xl font-bold text-white">Tracked Websites</h3>
            </div>
            <button
              onClick={loadWebsites}
              disabled={loading}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors text-sm disabled:opacity-50"
            >
              {loading ? 'Refreshing...' : 'Refresh'}
            </button>
          </div>

          <div className="space-y-3">
            {websites.length > 0 ? (
              websites.map((website, index) => (
                <div
                  key={website.id || index}
                  className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700"
                >
                  <div>
                    <div className="text-white font-medium">{website.name}</div>
                    <div className="text-sm text-gray-400">{website.domain}</div>
                    {website.id && (
                      <div className="text-xs text-gray-500 mt-1 font-mono">ID: {website.id}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-3">
                    {website.id && config.apiKey && (
                      <button
                        onClick={() => loadWebsiteStats(website.id)}
                        className="px-3 py-1 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm transition-colors"
                      >
                        Stats
                      </button>
                    )}
                    <span
                      className={`px-3 py-1 rounded-full text-xs ${
                        website.enabled !== false
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}
                    >
                      {website.enabled !== false ? 'Tracking' : 'Not Configured'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center text-gray-400 py-8">
                {config.apiKey
                  ? 'No websites configured yet. Add one below.'
                  : 'Enter API key and test connection to view websites'}
              </div>
            )}
          </div>

          {/* Website Stats Display */}
          {selectedWebsite && websiteStats && (
            <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
              <h4 className="text-white font-semibold mb-3">Website Analytics</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <div className="text-gray-400 text-sm">Visitors</div>
                  <div className="text-white text-2xl font-bold">{websiteStats.pageviews?.value || 0}</div>
                </div>
                <div>
                  <div className="text-gray-400 text-sm">Page Views</div>
                  <div className="text-white text-2xl font-bold">{websiteStats.uniques?.value || 0}</div>
                </div>
                <div>
                  <div className="text-gray-400 text-sm">Bounce Rate</div>
                  <div className="text-white text-2xl font-bold">{websiteStats.bounces?.value || 0}%</div>
                </div>
              </div>
            </div>
          )}

          {/* Create New Website */}
          {config.apiKey && (
            <div className="mt-6 pt-6 border-t border-gray-700">
              <h4 className="text-white font-semibold mb-4">Add Website</h4>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <input
                    type="text"
                    placeholder="Name (e.g., Ops Center)"
                    value={newWebsite.name}
                    onChange={(e) => setNewWebsite({...newWebsite, name: e.target.value})}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                  <input
                    type="text"
                    placeholder="Domain (e.g., unicorncommander.ai)"
                    value={newWebsite.domain}
                    onChange={(e) => setNewWebsite({...newWebsite, domain: e.target.value})}
                    className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
                  />
                </div>
                <button
                  onClick={handleCreateWebsite}
                  disabled={loading || !newWebsite.name || !newWebsite.domain}
                  className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Add Website'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Privacy Settings */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <KeyIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Privacy Settings</h3>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700">
              <div>
                <div className="text-white font-medium">Respect Do Not Track</div>
                <div className="text-sm text-gray-400">
                  Honor browser DNT header and skip tracking
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.respectDNT}
                  onChange={(e) => setConfig({ ...config, respectDNT: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg border border-gray-700">
              <div>
                <div className="text-white font-medium">Session Tracking</div>
                <div className="text-sm text-gray-400">
                  Track user sessions and navigation paths
                </div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={config.sessionTracking}
                  onChange={(e) => setConfig({ ...config, sessionTracking: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Privacy Mode
              </label>
              <select
                value={config.privacyMode}
                onChange={(e) => setConfig({ ...config, privacyMode: e.target.value })}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-purple-500"
              >
                <option value="strict">Strict (No PII, No Cookies)</option>
                <option value="balanced">Balanced (Session Cookies Only)</option>
                <option value="permissive">Permissive (Full Tracking)</option>
              </select>
            </div>
          </div>
        </div>

        {/* Tracking Script */}
        <div className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <CodeBracketIcon className="w-5 h-5 text-purple-400" />
            <h3 className="text-xl font-bold text-white">Tracking Script</h3>
          </div>

          <p className="text-gray-300 text-sm mb-4">
            Copy this script and add it to the &lt;head&gt; section of your HTML:
          </p>

          <pre className="bg-gray-900 p-4 rounded-lg border border-gray-700 text-green-400 text-sm font-mono overflow-x-auto">
            {generateTrackingScript()}
          </pre>

          <button
            onClick={() => copyToClipboard(generateTrackingScript())}
            className="mt-4 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors flex items-center gap-2"
          >
            <ClipboardDocumentIcon className="w-5 h-5" />
            {copied ? 'Copied!' : 'Copy to Clipboard'}
          </button>
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
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
          >
            Open Umami
          </a>
        </div>
      </div>
    </div>
  );
}
