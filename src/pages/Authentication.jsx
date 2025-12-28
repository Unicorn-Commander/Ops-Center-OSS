import React, { useState, useEffect } from 'react';
import { Shield, Users, Key, Settings, Server, Globe, CheckCircle, XCircle, AlertCircle, Eye, EyeOff, ExternalLink, RefreshCw } from 'lucide-react';

const Authentication = () => {
  const [keycloakStatus, setKeycloakStatus] = useState(null);
  const [oauthClients, setOauthClients] = useState([]);
  const [apiCredentials, setApiCredentials] = useState(null);
  const [sessionConfig, setSessionConfig] = useState(null);
  const [sslStatus, setSslStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showSecret, setShowSecret] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [services, setServices] = useState([]);

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchKeycloakStatus(),
        fetchOAuthClients(),
        fetchSessionConfig(),
        fetchSSLStatus(),
        fetchServices()
      ]);
    } catch (error) {
      console.error('Failed to fetch authentication data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchKeycloakStatus = async () => {
    try {
      const response = await fetch('/api/v1/system/keycloak/status');
      const data = await response.json();
      setKeycloakStatus(data);
    } catch (error) {
      console.error('Failed to fetch Keycloak status:', error);
    }
  };

  const fetchOAuthClients = async () => {
    try {
      const response = await fetch('/api/v1/system/keycloak/clients');
      const data = await response.json();
      setOauthClients(data.clients || []);
    } catch (error) {
      console.error('Failed to fetch OAuth clients:', error);
    }
  };

  const fetchAPICredentials = async () => {
    try {
      const response = await fetch('/api/v1/system/keycloak/api-credentials');
      const data = await response.json();
      setApiCredentials(data);
    } catch (error) {
      console.error('Failed to fetch API credentials:', error);
    }
  };

  const fetchSessionConfig = async () => {
    try {
      const response = await fetch('/api/v1/system/keycloak/session-config');
      const data = await response.json();
      setSessionConfig(data);
    } catch (error) {
      console.error('Failed to fetch session config:', error);
    }
  };

  const fetchSSLStatus = async () => {
    try {
      const response = await fetch('/api/v1/system/keycloak/ssl-status');
      const data = await response.json();
      setSslStatus(data);
    } catch (error) {
      console.error('Failed to fetch SSL status:', error);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await fetch('/api/v1/services');
      const data = await response.json();
      setServices(data);
    } catch (error) {
      console.error('Failed to fetch services:', error);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    try {
      const response = await fetch('/api/v1/system/keycloak/test-connection', {
        method: 'POST'
      });
      const result = await response.json();

      if (result.success) {
        alert('✅ Connection successful!\n\n' + result.message);
      } else {
        alert('❌ Connection failed!\n\n' + result.message);
      }
    } catch (error) {
      alert('❌ Connection test failed!\n\n' + error.message);
    } finally {
      setTestingConnection(false);
    }
  };

  const openKeycloakAdmin = () => {
    if (keycloakStatus?.admin_url) {
      window.open(keycloakStatus.admin_url, '_blank');
    }
  };

  const openManageUsers = () => {
    window.location.href = '/admin/system/users';
  };

  const getProviderIcon = (providerName) => {
    const name = providerName.toLowerCase();
    if (name.includes('google')) return '🔵'; // Google blue
    if (name.includes('github')) return '⚫'; // GitHub black
    if (name.includes('microsoft')) return '🟦'; // Microsoft blue
    return '🔑'; // Generic key
  };

  const formatDuration = (seconds) => {
    if (seconds >= 86400) return `${Math.floor(seconds / 86400)} days`;
    if (seconds >= 3600) return `${Math.floor(seconds / 3600)} hours`;
    if (seconds >= 60) return `${Math.floor(seconds / 60)} minutes`;
    return `${seconds} seconds`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  const isKeycloakRunning = keycloakStatus?.status === 'running';

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-500" />
            Authentication & SSO
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Keycloak SSO configuration and identity provider management
          </p>
        </div>
        <button
          onClick={fetchAllData}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      {/* SSO Status Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
            Keycloak SSO Status
          </h2>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${
            isKeycloakRunning
              ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
              : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
          }`}>
            {isKeycloakRunning ? (
              <>
                <CheckCircle className="w-4 h-4" />
                Running
              </>
            ) : (
              <>
                <XCircle className="w-4 h-4" />
                Stopped
              </>
            )}
          </div>
        </div>

        {!isKeycloakRunning ? (
          <div className="text-center py-8">
            <Shield className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Keycloak Not Running
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
              The Keycloak container (uchub-keycloak) is not running. Start the container to enable SSO.
            </p>
            <code className="text-sm bg-gray-100 dark:bg-gray-700 px-3 py-1 rounded">
              docker start uchub-keycloak
            </code>
          </div>
        ) : (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <Users className="w-8 h-8 text-blue-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {keycloakStatus?.users || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Total Users</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <Key className="w-8 h-8 text-green-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {keycloakStatus?.identity_providers?.length || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Identity Providers</div>
              </div>
              <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <Server className="w-8 h-8 text-purple-500 mx-auto mb-2" />
                <div className="text-2xl font-bold text-gray-900 dark:text-white">
                  {keycloakStatus?.active_sessions || 0}
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400">Active Sessions</div>
              </div>
            </div>

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Realm:</span>
                <span className="font-mono font-medium text-gray-900 dark:text-white">{keycloakStatus?.realm}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Admin Console:</span>
                <a
                  href={keycloakStatus?.admin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-500 hover:text-blue-600 flex items-center gap-1"
                >
                  Open Console <ExternalLink className="w-3 h-3" />
                </a>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600 dark:text-gray-400">Container Health:</span>
                <span className={`font-medium ${
                  keycloakStatus?.health === 'healthy' ? 'text-green-600' : 'text-yellow-600'
                }`}>
                  {keycloakStatus?.health || 'unknown'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Identity Providers */}
      {isKeycloakRunning && keycloakStatus?.identity_providers && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Identity Providers
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {keycloakStatus.identity_providers.map((provider) => (
              <div key={provider.alias} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="text-3xl">
                    {getProviderIcon(provider.name)}
                  </div>
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900 dark:text-white">{provider.name}</h3>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{provider.provider_id}</p>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    provider.enabled
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                  }`}>
                    {provider.enabled ? 'Enabled' : 'Disabled'}
                  </div>
                </div>
                <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                  {provider.users} users authenticated
                </div>
                <button
                  onClick={openKeycloakAdmin}
                  className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  Configure
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* OAuth Clients */}
      {isKeycloakRunning && oauthClients.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            OAuth Clients
          </h2>

          <div className="space-y-3">
            {oauthClients.map((client) => (
              <div key={client.client_id} className="border border-gray-200 dark:border-gray-600 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <Globe className="w-5 h-5 text-blue-500" />
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">{client.name || client.client_id}</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400 font-mono">{client.client_id}</p>
                    </div>
                  </div>
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    client.status === 'active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                  }`}>
                    {client.status}
                  </div>
                </div>
                <div className="text-sm space-y-1">
                  <div className="text-gray-600 dark:text-gray-400">
                    <span className="font-medium">Redirect URIs:</span>
                    <div className="mt-1 ml-4">
                      {client.redirect_uris.map((uri, idx) => (
                        <div key={idx} className="font-mono text-xs">{uri}</div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* API Credentials */}
      {isKeycloakRunning && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              API Credentials
            </h2>
            {!apiCredentials && (
              <button
                onClick={fetchAPICredentials}
                className="text-sm px-3 py-1 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
              >
                Show Credentials
              </button>
            )}
          </div>

          {apiCredentials ? (
            <div className="space-y-3">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600 dark:text-gray-400">Service Account</label>
                  <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded font-mono text-sm">
                    {apiCredentials.service_account}
                  </div>
                </div>
                <div>
                  <label className="text-sm text-gray-600 dark:text-gray-400">Client ID</label>
                  <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded font-mono text-sm">
                    {apiCredentials.client_id}
                  </div>
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Client Secret</label>
                <div className="mt-1 flex gap-2">
                  <div className="flex-1 p-2 bg-gray-50 dark:bg-gray-700 rounded font-mono text-sm">
                    {showSecret ? apiCredentials.client_secret : '••••••••••••••••••••••••••••••••'}
                  </div>
                  <button
                    onClick={() => setShowSecret(!showSecret)}
                    className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded transition-colors"
                  >
                    {showSecret ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Token Endpoint</label>
                <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded font-mono text-xs break-all">
                  {apiCredentials.token_endpoint}
                </div>
              </div>

              <div>
                <label className="text-sm text-gray-600 dark:text-gray-400">Permissions</label>
                <div className="mt-1 flex gap-2 flex-wrap">
                  {apiCredentials.permissions?.map((perm, idx) => (
                    <span key={idx} className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded text-xs">
                      {perm}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-gray-600 dark:text-gray-400 text-sm">
              Click "Show Credentials" to display API credentials. Only visible to system administrators.
            </p>
          )}
        </div>
      )}

      {/* SSL/Certificate Status */}
      {isKeycloakRunning && sslStatus && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            SSL/TLS Configuration
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">SSL Mode</label>
              <div className="mt-1 flex items-center gap-2">
                <div className={`px-3 py-1 rounded font-medium ${
                  sslStatus.ssl_enabled
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                }`}>
                  {sslStatus.ssl_mode}
                </div>
              </div>
            </div>
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Certificate Provider</label>
              <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                {sslStatus.certificate_provider}
              </div>
            </div>
          </div>

          <div className="mt-4">
            <label className="text-sm text-gray-600 dark:text-gray-400">Protected Domains</label>
            <div className="mt-1 space-y-1">
              {sslStatus.domains?.map((domain, idx) => (
                <div key={idx} className="flex items-center gap-2 text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500" />
                  <span className="font-mono">{domain}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-gray-600 dark:text-gray-400">Auto-renewal enabled</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-green-500" />
              <span className="text-gray-600 dark:text-gray-400">HTTPS redirect active</span>
            </div>
          </div>
        </div>
      )}

      {/* Session Configuration */}
      {isKeycloakRunning && sessionConfig && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Session Configuration
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Session Timeout</label>
              <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                {formatDuration(sessionConfig.sso_session_idle_timeout)}
              </div>
            </div>
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Max Session Lifespan</label>
              <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                {formatDuration(sessionConfig.sso_session_max_lifespan)}
              </div>
            </div>
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Remember Me Duration</label>
              <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                {formatDuration(sessionConfig.offline_session_idle_timeout)}
              </div>
            </div>
            <div>
              <label className="text-sm text-gray-600 dark:text-gray-400">Access Token Lifespan</label>
              <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-700 rounded">
                {formatDuration(sessionConfig.access_token_lifespan)}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Service Integration Status */}
      {isKeycloakRunning && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Service Integration
          </h2>

          <div className="space-y-3">
            {['Open-WebUI', 'Ops Center', 'Brigade', 'Center-Deep'].map((service) => {
              const serviceData = services.find(s => s.display_name?.includes(service.split(' ')[0]));
              const isRunning = serviceData?.status === 'running';
              const isProtected = oauthClients.some(c =>
                c.client_id.toLowerCase().includes(service.toLowerCase().replace(/[^a-z]/g, ''))
              );

              return (
                <div key={service} className="flex items-center justify-between py-2 border-b border-gray-200 dark:border-gray-700 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      isRunning ? 'bg-green-500' : 'bg-gray-400'
                    }`} />
                    <span className="font-medium text-gray-900 dark:text-white">{service}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {isProtected && isRunning ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span className="text-sm text-green-600 dark:text-green-400">SSO Enabled</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          {isRunning ? 'No SSO' : 'Not Running'}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Quick Actions */}
      {isKeycloakRunning && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            Quick Actions
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={openKeycloakAdmin}
              className="flex items-center justify-center gap-2 p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Settings className="w-5 h-5" />
              <span>Keycloak Admin</span>
            </button>
            <button
              onClick={openManageUsers}
              className="flex items-center justify-center gap-2 p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Users className="w-5 h-5" />
              <span>Manage Users</span>
            </button>
            <button
              onClick={fetchAPICredentials}
              className="flex items-center justify-center gap-2 p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              <Key className="w-5 h-5" />
              <span>API Credentials</span>
            </button>
            <button
              onClick={handleTestConnection}
              disabled={testingConnection}
              className="flex items-center justify-center gap-2 p-4 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Server className="w-5 h-5" />
              <span>{testingConnection ? 'Testing...' : 'Test SSO Login'}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Authentication;
