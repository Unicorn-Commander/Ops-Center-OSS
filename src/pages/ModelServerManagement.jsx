import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ServerIcon,
  PlusCircleIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  CogIcon,
  CloudIcon,
  CpuChipIcon,
  ChartBarIcon,
  BeakerIcon,
  GlobeAltIcon,
  LockClosedIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import axios from 'axios';

const SERVER_TYPES = {
  vllm: {
    name: 'vLLM',
    icon: CpuChipIcon,
    color: 'blue',
    description: 'High-performance LLM inference server (OpenAI-compatible)'
  },
  ollama: {
    name: 'Ollama',
    icon: CloudIcon,
    color: 'green',
    description: 'Local LLM runner with model library'
  },
  embedding: {
    name: 'Embeddings',
    icon: ChartBarIcon,
    color: 'purple',
    description: 'Text embedding server for vector operations'
  },
  reranking: {
    name: 'Reranker',
    icon: BeakerIcon,
    color: 'orange',
    description: 'Document reranking server for search optimization'
  }
};

const HEALTH_STATUS_STYLES = {
  online: 'bg-green-500',
  offline: 'bg-red-500',
  degraded: 'bg-yellow-500',
  unknown: 'bg-gray-400'
};

export default function ModelServerManagement() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddServer, setShowAddServer] = useState(false);
  const [selectedServer, setSelectedServer] = useState(null);
  const [serverModels, setServerModels] = useState({});
  const [serverMetrics, setServerMetrics] = useState({});
  const [testingConnection, setTestingConnection] = useState({});

  // Form state for adding new server
  const [newServer, setNewServer] = useState({
    name: '',
    server_type: 'vllm',
    base_url: '',
    api_key: ''
  });

  // Load servers on mount
  useEffect(() => {
    loadServers();
  }, []);

  // Auto-refresh health status every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      servers.forEach(server => {
        if (server.is_active) {
          checkServerHealth(server.id);
        }
      });
    }, 30000);

    return () => clearInterval(interval);
  }, [servers]);

  const loadServers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/model-servers');
      setServers(response.data);

      // Load models for each server
      for (const server of response.data) {
        if (server.is_active && server.health_status === 'online') {
          loadServerModels(server.id);
        }
      }
    } catch (error) {
      console.error('Error loading servers:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadServerModels = async (serverId) => {
    try {
      const response = await axios.get(`/api/v1/model-servers/${serverId}/models`);
      setServerModels(prev => ({
        ...prev,
        [serverId]: response.data
      }));
    } catch (error) {
      console.error(`Error loading models for server ${serverId}:`, error);
    }
  };

  const loadServerMetrics = async (serverId) => {
    try {
      const response = await axios.get(`/api/v1/model-servers/${serverId}/metrics`);
      setServerMetrics(prev => ({
        ...prev,
        [serverId]: response.data
      }));
    } catch (error) {
      console.error(`Error loading metrics for server ${serverId}:`, error);
    }
  };

  const addServer = async () => {
    try {
      const response = await axios.post('/api/v1/model-servers', newServer);
      setServers([...servers, response.data]);
      setShowAddServer(false);
      setNewServer({ name: '', server_type: 'vllm', base_url: '', api_key: '' });

      // Test connection immediately
      testConnection(response.data.id);
    } catch (error) {
      console.error('Error adding server:', error);
      alert('Failed to add server: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteServer = async (serverId) => {
    if (!confirm('Are you sure you want to delete this server?')) return;

    try {
      await axios.delete(`/api/v1/model-servers/${serverId}`);
      setServers(servers.filter(s => s.id !== serverId));
      if (selectedServer?.id === serverId) {
        setSelectedServer(null);
      }
    } catch (error) {
      console.error('Error deleting server:', error);
      alert('Failed to delete server');
    }
  };

  const testConnection = async (serverId) => {
    setTestingConnection(prev => ({ ...prev, [serverId]: true }));

    try {
      const response = await axios.post(`/api/v1/model-servers/${serverId}/test`);

      // Reload server to get updated health status
      const serverResponse = await axios.get(`/api/v1/model-servers/${serverId}`);
      setServers(servers.map(s => s.id === serverId ? serverResponse.data : s));

      if (response.data.connected) {
        loadServerModels(serverId);
      }
    } catch (error) {
      console.error('Error testing connection:', error);
    } finally {
      setTestingConnection(prev => ({ ...prev, [serverId]: false }));
    }
  };

  const checkServerHealth = async (serverId) => {
    try {
      const response = await axios.get(`/api/v1/model-servers/${serverId}/health`);
      setServers(servers.map(s =>
        s.id === serverId
          ? { ...s, health_status: response.data.health_status }
          : s
      ));
    } catch (error) {
      console.error(`Error checking health for server ${serverId}:`, error);
    }
  };

  const runHealthCheckAll = async () => {
    try {
      const response = await axios.post('/api/v1/model-servers/health-check-all');
      loadServers(); // Reload to get updated statuses
    } catch (error) {
      console.error('Error running health checks:', error);
    }
  };

  const ServerCard = ({ server }) => {
    const ServerType = SERVER_TYPES[server.server_type];
    const Icon = ServerType.icon;
    const isLoading = testingConnection[server.id];

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`
          bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6
          border-2 ${selectedServer?.id === server.id ? 'border-blue-500' : 'border-transparent'}
          hover:shadow-xl transition-all cursor-pointer
        `}
        onClick={() => setSelectedServer(server)}
      >
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg bg-${ServerType.color}-100 dark:bg-${ServerType.color}-900`}>
              <Icon className={`h-6 w-6 text-${ServerType.color}-600 dark:text-${ServerType.color}-400`} />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                {server.name}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {ServerType.name}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <div className={`h-3 w-3 rounded-full ${HEALTH_STATUS_STYLES[server.health_status]} animate-pulse`} />
            <span className="text-sm text-gray-500 dark:text-gray-400 capitalize">
              {server.health_status}
            </span>
          </div>
        </div>

        <div className="space-y-2 mb-4">
          <div className="text-sm text-gray-600 dark:text-gray-300">
            <span className="font-medium">URL:</span> {server.base_url}
          </div>

          {serverModels[server.id] && (
            <div className="text-sm text-gray-600 dark:text-gray-300">
              <span className="font-medium">Models:</span> {serverModels[server.id].length} available
            </div>
          )}

          {server.last_health_check && (
            <div className="text-sm text-gray-500 dark:text-gray-400">
              Last checked: {new Date(server.last_health_check).toLocaleString()}
            </div>
          )}
        </div>

        <div className="flex space-x-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              testConnection(server.id);
            }}
            disabled={isLoading}
            className="flex-1 px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <ArrowPathIcon className="h-4 w-4 mx-auto animate-spin" />
            ) : (
              'Test Connection'
            )}
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              loadServerMetrics(server.id);
            }}
            className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 transition-colors"
          >
            <ChartBarIcon className="h-4 w-4" />
          </button>

          <button
            onClick={(e) => {
              e.stopPropagation();
              deleteServer(server.id);
            }}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 transition-colors"
          >
            <TrashIcon className="h-4 w-4" />
          </button>
        </div>
      </motion.div>
    );
  };

  const AddServerModal = () => (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
    >
      <motion.div
        initial={{ scale: 0.9 }}
        animate={{ scale: 1 }}
        className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-md w-full p-6"
      >
        <h2 className="text-2xl font-bold mb-4 text-gray-900 dark:text-white">
          Add Model Server
        </h2>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Server Name
            </label>
            <input
              type="text"
              value={newServer.name}
              onChange={(e) => setNewServer({ ...newServer, name: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600
                       dark:text-white focus:ring-2 focus:ring-blue-500"
              placeholder="My vLLM Server"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Server Type
            </label>
            <select
              value={newServer.server_type}
              onChange={(e) => setNewServer({ ...newServer, server_type: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600
                       dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(SERVER_TYPES).map(([key, type]) => (
                <option key={key} value={key}>
                  {type.name} - {type.description}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Server URL
            </label>
            <input
              type="text"
              value={newServer.base_url}
              onChange={(e) => setNewServer({ ...newServer, base_url: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600
                       dark:text-white focus:ring-2 focus:ring-blue-500"
              placeholder="http://192.168.1.100:8000"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              API Key (Optional)
            </label>
            <input
              type="password"
              value={newServer.api_key}
              onChange={(e) => setNewServer({ ...newServer, api_key: e.target.value })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600
                       dark:text-white focus:ring-2 focus:ring-blue-500"
              placeholder="Leave empty if not required"
            />
          </div>
        </div>

        <div className="flex space-x-3 mt-6">
          <button
            onClick={addServer}
            className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Add Server
          </button>
          <button
            onClick={() => setShowAddServer(false)}
            className="flex-1 px-4 py-2 bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300
                     rounded-lg hover:bg-gray-400 dark:hover:bg-gray-600 transition-colors"
          >
            Cancel
          </button>
        </div>
      </motion.div>
    </motion.div>
  );

  const ServerDetails = ({ server }) => {
    const models = serverModels[server.id] || [];
    const metrics = serverMetrics[server.id];

    return (
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
          Server Details: {server.name}
        </h3>

        {/* Server Info */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Type:</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {SERVER_TYPES[server.server_type].name}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Status:</span>
            <p className="font-medium capitalize text-gray-900 dark:text-white">
              {server.health_status}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">URL:</span>
            <p className="font-medium text-gray-900 dark:text-white break-all">
              {server.base_url}
            </p>
          </div>
          <div>
            <span className="text-sm text-gray-500 dark:text-gray-400">Created:</span>
            <p className="font-medium text-gray-900 dark:text-white">
              {new Date(server.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>

        {/* Metrics */}
        {metrics && (
          <div className="mb-6">
            <h4 className="font-medium mb-2 text-gray-900 dark:text-white">Metrics</h4>
            <div className="grid grid-cols-3 gap-3">
              {metrics.cpu_percent !== null && (
                <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded">
                  <span className="text-xs text-gray-500 dark:text-gray-400">CPU</span>
                  <p className="font-bold text-gray-900 dark:text-white">{metrics.cpu_percent}%</p>
                </div>
              )}
              {metrics.memory_percent !== null && (
                <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded">
                  <span className="text-xs text-gray-500 dark:text-gray-400">Memory</span>
                  <p className="font-bold text-gray-900 dark:text-white">{metrics.memory_percent}%</p>
                </div>
              )}
              {metrics.gpu_percent !== null && (
                <div className="bg-gray-100 dark:bg-gray-700 p-2 rounded">
                  <span className="text-xs text-gray-500 dark:text-gray-400">GPU</span>
                  <p className="font-bold text-gray-900 dark:text-white">{metrics.gpu_percent}%</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Models */}
        <div>
          <h4 className="font-medium mb-2 text-gray-900 dark:text-white">
            Available Models ({models.length})
          </h4>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {models.map((model, index) => (
              <div
                key={index}
                className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-700 rounded"
              >
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">{model.name || model.id}</p>
                  {model.quantization && (
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {model.quantization}
                    </span>
                  )}
                </div>
                {model.loaded && (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Model Server Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage distributed AI inference servers across your network
          </p>
        </div>

        <div className="flex space-x-3">
          <button
            onClick={runHealthCheckAll}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600
                     transition-colors flex items-center space-x-2"
          >
            <ArrowPathIcon className="h-5 w-5" />
            <span>Check All</span>
          </button>

          <button
            onClick={() => setShowAddServer(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600
                     transition-colors flex items-center space-x-2"
          >
            <PlusCircleIcon className="h-5 w-5" />
            <span>Add Server</span>
          </button>
        </div>
      </div>

      {/* Server Grid and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Server List */}
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {servers.map(server => (
              <ServerCard key={server.id} server={server} />
            ))}

            {servers.length === 0 && (
              <div className="col-span-2 text-center py-12">
                <ServerIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">
                  No servers configured yet
                </p>
                <button
                  onClick={() => setShowAddServer(true)}
                  className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Add Your First Server
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Server Details Panel */}
        <div className="lg:col-span-1">
          {selectedServer ? (
            <ServerDetails server={selectedServer} />
          ) : (
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-6 text-center">
              <InformationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-500 dark:text-gray-400">
                Select a server to view details
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Add Server Modal */}
      {showAddServer && <AddServerModal />}
    </div>
  );
}