import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PuzzlePieceIcon,
  ArrowPathIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  ArrowDownTrayIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ChartBarIcon,
  CodeBracketIcon,
  PhotoIcon,
  CogIcon,
  ServerIcon,
  CloudIcon,
  WrenchScrewdriverIcon,
  EyeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';
import { getTooltip } from '../data/tooltipContent';
import HelpTooltip from '../components/HelpTooltip';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
};

// Extension metadata for better display
const extensionMetadata = {
  'comfyui': {
    displayName: 'ComfyUI',
    description: 'Powerful and modular stable diffusion GUI for AI image generation',
    category: 'AI Tools',
    icon: PhotoIcon,
    color: 'bg-purple-500',
    features: ['Stable Diffusion', 'Custom Workflows', 'Node-based UI'],
    port: 8188,
    docs: 'https://github.com/comfyanonymous/ComfyUI'
  },
  'monitoring': {
    displayName: 'Grafana Monitoring',
    description: 'Comprehensive system monitoring with Grafana dashboards and Prometheus metrics',
    category: 'Monitoring',
    icon: ChartBarIcon,
    color: 'bg-orange-500',
    features: ['GPU Monitoring', 'System Metrics', 'Custom Dashboards'],
    port: 3000,
    docs: 'Built-in monitoring stack'
  },
  'portainer': {
    displayName: 'Portainer',
    description: 'Docker container management interface for easy container administration',
    category: 'Management',
    icon: ServerIcon,
    color: 'bg-blue-500',
    features: ['Container Management', 'Volume Management', 'Network Management'],
    port: 9443,
    docs: 'https://docs.portainer.io'
  },
  'n8n': {
    displayName: 'n8n Workflows',
    description: 'Workflow automation tool for connecting different services and APIs',
    category: 'Automation',
    icon: CogIcon,
    color: 'bg-pink-500',
    features: ['Visual Workflows', '200+ Integrations', 'API Automation'],
    port: 5678,
    docs: 'https://docs.n8n.io'
  },
  'traefik': {
    displayName: 'Traefik Proxy',
    description: 'Modern HTTP reverse proxy and load balancer with automatic service discovery',
    category: 'Networking',
    icon: CloudIcon,
    color: 'bg-green-500',
    features: ['Reverse Proxy', 'SSL/TLS', 'Service Discovery'],
    port: 8080,
    docs: 'https://doc.traefik.io/traefik/'
  },
  'dev-tools': {
    displayName: 'Development Tools',
    description: 'Essential development utilities and debugging tools',
    category: 'Development',
    icon: CodeBracketIcon,
    color: 'bg-indigo-500',
    features: ['Code Editor', 'Debugging Tools', 'Git Integration'],
    port: null,
    docs: 'Built-in development tools'
  },
  'ollama': {
    displayName: 'Ollama',
    description: 'Local LLM server for running open-source language models',
    category: 'AI Tools',
    icon: ServerIcon,
    color: 'bg-yellow-500',
    features: ['Local LLMs', 'Model Management', 'API Access'],
    port: 11434,
    docs: 'https://ollama.ai/docs'
  },
  'bolt.diy': {
    displayName: 'Bolt.DIY',
    description: 'AI-powered development environment and code generation tools',
    category: 'Development',
    icon: WrenchScrewdriverIcon,
    color: 'bg-red-500',
    features: ['AI Code Generation', 'Project Templates', 'Smart Debugging'],
    port: 5173,
    docs: 'https://bolt.diy'
  }
};

export default function Extensions() {
  const [activeTab, setActiveTab] = useState('installed');
  const [extensions, setExtensions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [selectedExtension, setSelectedExtension] = useState(null);

  // Mock marketplace extensions for now
  const [marketplaceExtensions] = useState([
    {
      id: 'jupyter',
      name: 'Jupyter Lab',
      description: 'Interactive computing environment for data science and machine learning',
      category: 'Development',
      icon: DocumentTextIcon,
      color: 'bg-orange-600',
      features: ['Python Notebooks', 'Data Analysis', 'Visualization'],
      port: 8888,
      installed: false,
      popular: true
    },
    {
      id: 'vscode',
      name: 'VS Code Server',
      description: 'Visual Studio Code in the browser for remote development',
      category: 'Development', 
      icon: CodeBracketIcon,
      color: 'bg-blue-600',
      features: ['Code Editor', 'Extensions', 'Git Integration'],
      port: 8443,
      installed: false,
      popular: true
    },
    {
      id: 'redis-commander',
      name: 'Redis Commander',
      description: 'Web-based Redis database management interface',
      category: 'Database',
      icon: ServerIcon,
      color: 'bg-red-600',
      features: ['Redis Management', 'Key Browser', 'Query Interface'],
      port: 8081,
      installed: false,
      popular: false
    }
  ]);

  useEffect(() => {
    loadExtensions();
  }, []);

  const loadExtensions = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/extensions');
      const data = await response.json();
      
      // Enhance extension data with metadata
      const enhancedExtensions = (data.extensions || []).map(ext => ({
        ...ext,
        ...extensionMetadata[ext.id] || {
          displayName: ext.id,
          description: `Extension: ${ext.id}`,
          category: 'Other',
          icon: PuzzlePieceIcon,
          color: 'bg-gray-500',
          features: [],
          port: null,
          docs: null
        }
      }));
      
      setExtensions(enhancedExtensions);
    } catch (error) {
      console.error('Failed to load extensions:', error);
      // Fallback to mock data
      setExtensions([]);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadExtensions();
    setRefreshing(false);
  };

  const handleExtensionAction = async (extensionId, action) => {
    try {
      const response = await fetch(`/api/v1/extensions/${extensionId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      
      if (response.ok) {
        console.log(`Extension ${extensionId} ${action} successful`);
        // Refresh extension status
        await loadExtensions();
      } else {
        const error = await response.json();
        console.error(`Failed to ${action} extension ${extensionId}:`, error.detail);
        alert(`Failed to ${action} extension: ${error.detail}`);
      }
    } catch (error) {
      console.error(`Error ${action}ing extension:`, error);
      alert(`Error ${action}ing extension`);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'text-green-600 dark:text-green-400';
      case 'stopped': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running': return CheckCircleIcon;
      case 'stopped': return ExclamationTriangleIcon;
      default: return InformationCircleIcon;
    }
  };

  const getCategoryColor = (category) => {
    const colors = {
      'AI Tools': 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200',
      'Monitoring': 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200',
      'Management': 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-200',
      'Automation': 'bg-pink-100 text-pink-800 dark:bg-pink-800 dark:text-pink-200',
      'Networking': 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200',
      'Development': 'bg-indigo-100 text-indigo-800 dark:bg-indigo-800 dark:text-indigo-200',
      'Database': 'bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200',
      'Other': 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
    };
    return colors[category] || colors['Other'];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <motion.div 
      className="space-y-6"
      variants={containerVariants}
      initial="hidden" 
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Extensions Marketplace
            </h1>
            <HelpTooltip 
              title={getTooltip('extensions', 'dockerContainer').title}
              content={getTooltip('extensions', 'dockerContainer').content}
              position="right"
            />
          </div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Extend UC-1 Pro functionality with powerful add-ons and integrations
          </p>
        </div>
        
        <button
          onClick={refreshData}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
          <HelpTooltip 
            title={getTooltip('ui', 'refreshButton').title}
            content={getTooltip('ui', 'refreshButton').content}
            position="bottom"
          />
        </button>
      </motion.div>

      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Extensions</p>
                <HelpTooltip 
                  title="Total Extensions"
                  content="Combined count of installed extensions and available marketplace extensions. Extensions add specialized functionality to UC-1 Pro."
                  position="top"
                />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {extensions.length + marketplaceExtensions.length}
              </p>
            </div>
            <PuzzlePieceIcon className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Installed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {extensions.length}
              </p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Running</p>
                <HelpTooltip 
                  title={getTooltip('extensions', 'extensionStatus').title}
                  content="Number of extensions currently running. Running extensions consume system resources but provide their functionality."
                  position="top"
                />
              </div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {extensions.filter(ext => ext.status === 'running').length}
              </p>
            </div>
            <PlayIcon className="h-8 w-8 text-yellow-500" />
          </div>
        </div>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div variants={itemVariants} className="border-b dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('installed')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'installed'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <CheckCircleIcon className="h-5 w-5" />
              Installed Extensions ({extensions.length})
            </div>
          </button>
          <button
            onClick={() => setActiveTab('marketplace')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'marketplace'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            <div className="flex items-center gap-2">
              <ArrowDownTrayIcon className="h-5 w-5" />
              Marketplace ({marketplaceExtensions.length})
            </div>
          </button>
        </nav>
      </motion.div>

      {/* Installed Extensions Tab */}
      {activeTab === 'installed' && (
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {extensions.map((extension) => {
            const StatusIcon = getStatusIcon(extension.status);
            const ExtensionIcon = extension.icon;
            
            return (
              <div
                key={extension.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${extension.color}`}>
                      <ExtensionIcon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {extension.displayName}
                      </h3>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(extension.category)}`}>
                        {extension.category}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <StatusIcon className={`h-5 w-5 ${getStatusColor(extension.status)}`} />
                    <span className={`text-sm font-medium capitalize ${getStatusColor(extension.status)}`}>
                      {extension.status}
                    </span>
                  </div>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {extension.description}
                </p>

                {extension.features && extension.features.length > 0 && (
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-1">
                      {extension.features.slice(0, 3).map((feature, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setSelectedExtension(extension);
                      setShowDetailsModal(true);
                    }}
                    className="flex-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 flex items-center justify-center gap-1"
                  >
                    <EyeIcon className="h-4 w-4" />
                    Details
                  </button>
                  
                  {extension.status === 'running' ? (
                    <button
                      onClick={() => handleExtensionAction(extension.id, 'stop')}
                      className="px-3 py-2 text-sm bg-red-600 text-white rounded hover:bg-red-700 flex items-center gap-1"
                    >
                      <StopIcon className="h-4 w-4" />
                      Stop
                    </button>
                  ) : (
                    <button
                      onClick={() => handleExtensionAction(extension.id, 'start')}
                      className="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-1"
                    >
                      <PlayIcon className="h-4 w-4" />
                      Start
                    </button>
                  )}
                </div>
              </div>
            );
          })}
          
          {extensions.length === 0 && (
            <div className="col-span-full text-center py-12">
              <PuzzlePieceIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">No extensions installed</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by installing extensions from the marketplace.</p>
            </div>
          )}
        </motion.div>
      )}

      {/* Marketplace Tab */}
      {activeTab === 'marketplace' && (
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {marketplaceExtensions.map((extension) => {
            const ExtensionIcon = extension.icon;
            
            return (
              <div
                key={extension.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow p-6"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${extension.color}`}>
                      <ExtensionIcon className="h-6 w-6 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {extension.name}
                      </h3>
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(extension.category)}`}>
                        {extension.category}
                      </span>
                    </div>
                  </div>
                  
                  {extension.popular && (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-200">
                      Popular
                    </span>
                  )}
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {extension.description}
                </p>

                {extension.features && (
                  <div className="mb-4">
                    <div className="flex flex-wrap gap-1">
                      {extension.features.slice(0, 3).map((feature, index) => (
                        <span
                          key={index}
                          className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                        >
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      setSelectedExtension(extension);
                      setShowDetailsModal(true);
                    }}
                    className="flex-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600 flex items-center justify-center gap-1"
                  >
                    <InformationCircleIcon className="h-4 w-4" />
                    Learn More
                  </button>
                  
                  <button
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/v1/extensions/install', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            id: extension.id,
                            name: extension.displayName || extension.name || extension.id,
                            source_url: extension.source_url || '',
                            version: extension.version || '1.0.0',
                            category: extension.category || 'other'
                          })
                        });
                        
                        if (response.ok) {
                          await loadExtensions();
                          alert(`${extension.displayName || extension.name || extension.id} installed successfully!`);
                        } else {
                          const error = await response.json();
                          alert(`Installation failed: ${error.detail || error.error}`);
                        }
                      } catch (error) {
                        alert(`Installation failed: ${error}`);
                      }
                    }}
                    className="px-3 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                  >
                    <ArrowDownTrayIcon className="h-4 w-4" />
                    Install
                  </button>
                </div>
              </div>
            );
          })}
        </motion.div>
      )}

      {/* Extension Details Modal */}
      {showDetailsModal && selectedExtension && (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          >
            <div className="p-6">
              <div className="flex justify-between items-start mb-6">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-lg ${selectedExtension.color}`}>
                    <selectedExtension.icon className="h-8 w-8 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                      {selectedExtension.displayName || selectedExtension.name}
                    </h2>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-sm font-medium ${getCategoryColor(selectedExtension.category)}`}>
                      {selectedExtension.category}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Description</h3>
                  <p className="text-gray-600 dark:text-gray-400">{selectedExtension.description}</p>
                </div>

                {selectedExtension.features && selectedExtension.features.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Features</h3>
                    <div className="grid grid-cols-2 gap-2">
                      {selectedExtension.features.map((feature, index) => (
                        <div key={index} className="flex items-center gap-2">
                          <CheckCircleIcon className="h-4 w-4 text-green-500" />
                          <span className="text-sm text-gray-600 dark:text-gray-400">{feature}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedExtension.port && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Access</h3>
                    <p className="text-gray-600 dark:text-gray-400">
                      Port: <span className="font-mono text-blue-600 dark:text-blue-400">{selectedExtension.port}</span>
                    </p>
                  </div>
                )}

                {selectedExtension.docs && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Documentation</h3>
                    <a 
                      href={selectedExtension.docs}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {selectedExtension.docs}
                    </a>
                  </div>
                )}

                {selectedExtension.status && (
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">Status</h3>
                    <div className="flex items-center gap-2">
                      {React.createElement(getStatusIcon(selectedExtension.status), {
                        className: `h-5 w-5 ${getStatusColor(selectedExtension.status)}`
                      })}
                      <span className={`font-medium capitalize ${getStatusColor(selectedExtension.status)}`}>
                        {selectedExtension.status}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex justify-end gap-3 mt-8">
                <button
                  onClick={() => setShowDetailsModal(false)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500 rounded-md"
                >
                  Close
                </button>
                {selectedExtension.status ? (
                  selectedExtension.status === 'running' ? (
                    <button
                      onClick={() => {
                        handleExtensionAction(selectedExtension.id, 'stop');
                        setShowDetailsModal(false);
                      }}
                      className="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-md"
                    >
                      Stop Extension
                    </button>
                  ) : (
                    <button
                      onClick={() => {
                        handleExtensionAction(selectedExtension.id, 'start');
                        setShowDetailsModal(false);
                      }}
                      className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md"
                    >
                      Start Extension
                    </button>
                  )
                ) : (
                  <button
                    onClick={async () => {
                      try {
                        const response = await fetch('/api/v1/extensions/install', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({
                            id: selectedExtension.id,
                            name: selectedExtension.displayName || selectedExtension.name || selectedExtension.id,
                            source_url: selectedExtension.source_url || '',
                            version: selectedExtension.version || '1.0.0',
                            category: selectedExtension.category || 'other'
                          })
                        });
                        
                        if (response.ok) {
                          await loadExtensions();
                          setShowDetailsModal(false);
                          alert(`${selectedExtension.displayName || selectedExtension.name || selectedExtension.id} installed successfully!`);
                        } else {
                          const error = await response.json();
                          alert(`Installation failed: ${error.detail || error.error}`);
                        }
                      } catch (error) {
                        alert(`Installation failed: ${error}`);
                      }
                    }}
                    className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
                  >
                    Install Extension
                  </button>
                )}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </motion.div>
  );
}