import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useToast } from '../components/Toast';
import LogsViewer from '../components/LogsViewer';
import ServiceDetailsModal from '../components/ServiceDetailsModal';
import ForgejoCard from '../components/ForgejoCard';
import { getServiceInfo, getGPUUsageSummary } from '../data/serviceDescriptions';
import { getTooltip, tooltipPresets } from '../data/tooltipContent';
import HelpTooltip from '../components/HelpTooltip';
// Safe utilities for defensive rendering (Phase 3 refactoring)
import { safeMap, safeFilter } from '../utils/safeArrayUtils';
import { safeToFixed } from '../utils/safeNumberUtils';
import {
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  DocumentTextIcon,
  GlobeAltIcon,
  CpuChipIcon,
  CircleStackIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  PauseIcon,
  ServerIcon,
  InformationCircleIcon,
  FireIcon,
  ComputerDesktopIcon
} from '@heroicons/react/24/outline';
import { CpuChipIcon as CpuChipSolid } from '@heroicons/react/24/solid';

// Service URLs will be fetched dynamically from the backend
const defaultServiceUrls = {
  'vllm': 'http://localhost:8000/docs',
  'open-webui': 'http://localhost:8080',
  'searxng': 'http://localhost:8888',
  'prometheus': 'http://localhost:9090',
  'grafana': 'http://localhost:3000',
  'portainer': 'http://localhost:9443',
  'comfyui': 'http://localhost:8188',
  'n8n': 'http://localhost:5678',
  'qdrant': 'http://localhost:6333/dashboard',
  'admin-dashboard': 'http://localhost:8084',
  'ollama': 'http://localhost:11434',
  'ollama-webui': 'http://localhost:11435'
};

// Helper functions
const getStatusConfig = (status) => {
  switch (status) {
    case 'healthy':
    case 'running':
      return {
        icon: CheckCircleIcon,
        color: 'text-green-500',
        bg: 'bg-green-50 dark:bg-green-900/20',
        border: 'border-green-200 dark:border-green-800',
        pulse: true,
        label: 'Running'
      };
    case 'starting':
    case 'restarting':
      return {
        icon: ClockIcon,
        color: 'text-blue-500',
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        border: 'border-blue-200 dark:border-blue-800',
        pulse: true,
        label: 'Starting'
      };
    case 'stopped':
    case 'exited':
      return {
        icon: XCircleIcon,
        color: 'text-gray-400',
        bg: 'bg-gray-50 dark:bg-gray-900/20',
        border: 'border-gray-200 dark:border-gray-800',
        pulse: false,
        label: 'Stopped'
      };
    case 'paused':
      return {
        icon: PauseIcon,
        color: 'text-yellow-500',
        bg: 'bg-yellow-50 dark:bg-yellow-900/20',
        border: 'border-yellow-200 dark:border-yellow-800',
        pulse: false,
        label: 'Paused'
      };
    default:
      return {
        icon: ExclamationTriangleIcon,
        color: 'text-red-500',
        bg: 'bg-red-50 dark:bg-red-900/20',
        border: 'border-red-200 dark:border-red-800',
        pulse: false,
        label: status || 'Unknown'
      };
  }
};

const formatMemory = (memoryMb) => {
  if (!memoryMb || memoryMb === 0) return '0 MB';
  if (memoryMb > 1024) {
    return `${(memoryMb / 1024).toFixed(1)} GB`;
  }
  return `${Math.round(memoryMb)} MB`;
};

const isRunning = (status) => {
  return status === 'healthy' || status === 'running';
};

export default function Services() {
  const toast = useToast();
  const [services, setServices] = useState([]);
  const [systemResources, setSystemResources] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [loading, setLoading] = useState({});
  const [logsViewerOpen, setLogsViewerOpen] = useState(false);
  const [selectedContainer, setSelectedContainer] = useState(null);
  const [detailsModalOpen, setDetailsModalOpen] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [viewMode, setViewMode] = useState('cards'); // cards, table
  const [filterStatus, setFilterStatus] = useState('all'); // all, running, stopped
  const [sortBy, setSortBy] = useState('name'); // name, status, cpu, memory
  const [serviceUrls, setServiceUrls] = useState(defaultServiceUrls);
  const [actionInProgress, setActionInProgress] = useState({});
  const [initialLoading, setInitialLoading] = useState(true);

  // Fetch services from API
  const fetchServices = async () => {
    try {
      const response = await fetch('/api/v1/services', {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();

      // API returns array of services directly
      // REFACTORED: Using safeMap to prevent crashes on malformed service data
      const transformedServices = safeMap((Array.isArray(data) ? data : []), (service) => ({
        name: service.name,
        display_name: service.display_name || (service.name ? service.name.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown Service'),
        container_name: service.container_name || service.name,
        status: service.status,
        port: service.port,
        cpu_percent: service.cpu_percent || 0,
        memory_mb: service.memory_mb || 0,
        uptime: service.uptime,
        health: service.health,
        image: service.image,
        type: service.type || 'core'
      }));

      setServices(transformedServices);
      setWsConnected(true); // Set connected status after successful fetch
    } catch (error) {
      console.error('Failed to fetch services:', error);
      toast.error('Failed to load services');
      setWsConnected(false);
    } finally {
      setInitialLoading(false);
    }
  };

  // Fetch system resources
  const fetchSystemResources = async () => {
    try {
      const response = await fetch('/api/v1/system/status', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setSystemResources(data);
      }
    } catch (error) {
      console.error('Failed to fetch system resources:', error);
    }
  };

  // Fetch service URLs on component mount
  useEffect(() => {
    const fetchServiceUrls = async () => {
      try {
        const response = await fetch('/api/v1/service-urls', {
          credentials: 'include'
        });
        if (response.ok) {
          const data = await response.json();
          setServiceUrls(data.service_urls);
        }
      } catch (error) {
        console.error('Failed to fetch service URLs:', error);
        // Keep using default URLs if fetch fails
      }
    };

    fetchServiceUrls();
  }, []);

  // Initial data fetch
  useEffect(() => {
    fetchServices();
    fetchSystemResources();
  }, []);

  // Auto-refresh services every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!refreshing) {
        fetchServices();
        fetchSystemResources();
      }
    }, 10000);

    return () => clearInterval(interval);
  }, [refreshing]);

  const handleServiceAction = async (containerName, action) => {
    const loadingKey = `${containerName}-${action}`;

    // Prevent multiple simultaneous actions on the same service
    if (actionInProgress[containerName]) {
      toast.warning('Another action is already in progress for this service');
      return;
    }

    // Set loading state and mark action in progress
    setLoading(prev => ({ ...prev, [loadingKey]: true }));
    setActionInProgress(prev => ({ ...prev, [containerName]: true }));

    try {
      // Call the service control API
      const response = await fetch(`/api/v1/services/${containerName}/action`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ action: action })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      // Show success notification
      const actionText = action.charAt(0).toUpperCase() + action.slice(1);
      toast.success(`${actionText} command sent successfully`);

      // Wait a moment for the Docker operation to begin
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Refetch services to get updated status
      await fetchServices();

    } catch (error) {
      console.error(`Failed to ${action} service ${containerName}:`, error);

      // Show error notification
      const actionText = action.charAt(0).toUpperCase() + action.slice(1);
      toast.error(`Failed to ${action} service: ${error.message || 'Unknown error'}`);

      // Refetch services anyway to ensure we have correct state
      await fetchServices();
    } finally {
      // Clear loading state
      setLoading(prev => ({ ...prev, [loadingKey]: false }));
      setActionInProgress(prev => ({ ...prev, [containerName]: false }));
    }
  };


  const handleViewLogs = (containerName) => {
    setSelectedContainer(containerName);
    setLogsViewerOpen(true);
  };

  const handleViewDetails = (service) => {
    setSelectedService(service);
    setDetailsModalOpen(true);
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchServices();
      await fetchSystemResources();
      toast.success('Services refreshed');
    } catch (error) {
      console.error('Failed to refresh:', error);
    } finally {
      setRefreshing(false);
    }
  };
  
  // Filter and sort services
  // REFACTORED: Using safeFilter for defensive service filtering
  const filteredServices = safeFilter(services, (service) => {
    if (filterStatus === 'running') return isRunning(service.status);
    if (filterStatus === 'stopped') return !isRunning(service.status);
    return true;
  });

  const sortedServices = [...filteredServices].sort((a, b) => {
    switch (sortBy) {
      case 'status':
        return isRunning(b.status) - isRunning(a.status);
      case 'cpu':
        return (b.cpu_percent || 0) - (a.cpu_percent || 0);
      case 'memory':
        return (b.memory_mb || 0) - (a.memory_mb || 0);
      case 'name':
      default:
        return (a.display_name || a.name || '').localeCompare(b.display_name || b.name || '');
    }
  });

  // Group services by type - using safeFilter for safety
  const coreServices = safeFilter(sortedServices, s => s.type === 'core' || !s.type);
  const extensionServices = safeFilter(sortedServices, s => s.type === 'extension');

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Service Management
          </h1>
          <div className="flex items-center gap-4 mt-2 text-sm">
            <span className="text-gray-600 dark:text-gray-400">
              {services.length} Total Services
            </span>
            <span className="text-green-600 dark:text-green-400">
              {services.filter(s => isRunning(s.status)).length} Running
            </span>
            <div className="flex items-center gap-1">
              <div className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
              <span className="text-gray-600 dark:text-gray-400">
                {wsConnected ? 'Live Updates' : 'Disconnected'}
              </span>
              <HelpTooltip 
                title={getTooltip('ui', 'liveUpdates').title}
                content={getTooltip('ui', 'liveUpdates').content}
              />
            </div>
          </div>
        </div>

        <div className="flex gap-2 items-center">
          {/* Filter Controls */}
          <div className="flex items-center gap-1">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
            >
              <option value="all">All Services</option>
              <option value="running">Running Only</option>
              <option value="stopped">Stopped Only</option>
            </select>
            <HelpTooltip 
              title={getTooltip('ui', 'filterControls').title}
              content={getTooltip('ui', 'filterControls').content}
              position="bottom"
            />
          </div>
          
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
          >
            <option value="name">Sort by Name</option>
            <option value="status">Sort by Status</option>
            <option value="cpu">Sort by CPU</option>
            <option value="memory">Sort by Memory</option>
          </select>
          
          {/* View Toggle */}
          <div className="flex items-center gap-2">
            <div className="flex gap-1 p-1 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <button
                onClick={() => setViewMode('cards')}
                className={`px-3 py-1 text-sm rounded-md transition-all ${
                  viewMode === 'cards' 
                    ? 'bg-blue-500 text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Cards
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-3 py-1 text-sm rounded-md transition-all ${
                  viewMode === 'table' 
                    ? 'bg-blue-500 text-white shadow-sm' 
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                Table
              </button>
            </div>
            <HelpTooltip 
              title={getTooltip('ui', 'viewMode').title}
              content={getTooltip('ui', 'viewMode').content}
              position="bottom"
            />
          </div>
          
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
            <HelpTooltip 
              title={getTooltip('ui', 'refreshButton').title}
              content={getTooltip('ui', 'refreshButton').content}
              position="bottom"
            />
          </button>
        </div>
      </div>

      {/* Services Content */}
      {sortedServices.length > 0 ? (
        <div className="space-y-8">
          {viewMode === 'cards' ? (
            <>
              {/* Core Services Section */}
              {coreServices.length > 0 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
                    <ServerIcon className="h-6 w-6 text-blue-500" />
                    Core Services
                    <span className="text-sm font-normal text-gray-500">({coreServices.length})</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {coreServices.map((service, index) => (
                      <ServiceCard
                        key={service.container_name || service.name}
                        service={service}
                        index={index}
                        loading={loading}
                        onAction={handleServiceAction}
                        onViewLogs={handleViewLogs}
                        onViewDetails={handleViewDetails}
                        serviceUrls={serviceUrls}
                      />
                    ))}
                  </div>
                </div>
              )}
  
              {/* Extension Services Section */}
              {extensionServices.length > 0 && (
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
                    <Cog6ToothIcon className="h-6 w-6 text-purple-500" />
                    Extension Services
                    <span className="text-sm font-normal text-gray-500">({extensionServices.length})</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                    {extensionServices.map((service, index) => (
                      <ServiceCard
                        key={service.container_name || service.name}
                        service={service}
                        index={index + coreServices.length}
                        loading={loading}
                        onAction={handleServiceAction}
                        onViewLogs={handleViewLogs}
                        onViewDetails={handleViewDetails}
                        serviceUrls={serviceUrls}
                      />
                    ))}

                    {/* Forgejo Git Server Card */}
                    <ForgejoCard />
                  </div>
                </div>
              )}
            </>
          ) : (
            /* Table View */
            <ServiceTable
              services={sortedServices}
              loading={loading}
              onAction={handleServiceAction}
              onViewLogs={handleViewLogs}
              onViewDetails={handleViewDetails}
              serviceUrls={serviceUrls}
            />
          )}
        </div>
      ) : (

        /* Enhanced Empty State */
        <div className="text-center py-12">
          <div className="bg-gray-100 dark:bg-gray-800 rounded-full w-24 h-24 flex items-center justify-center mx-auto mb-6">
            <ServerIcon className="h-12 w-12 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            {services.length === 0 ? 'No Docker services detected. Make sure Docker is running.' : `No ${filterStatus} services found`}
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            {services.length === 0 
              ? 'Docker services may not be running or accessible'
              : `Try adjusting your filter settings`}
          </p>
          
          {services.length === 0 && (
            <div className="flex flex-col gap-3 max-w-md mx-auto">
              <button
                onClick={handleRefresh}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
              >
                <ArrowPathIcon className="h-4 w-4" />
                Retry Service Detection
              </button>
              
              <div className="text-left bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
                <h4 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">Troubleshooting:</h4>
                <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                  <li>• Check Docker daemon is running</li>
                  <li>• Verify UC-1 Pro services are started</li>
                  <li>• Run: docker-compose ps</li>
                  <li>• Check container logs for errors</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Modals */}
      <LogsViewer 
        containerName={selectedContainer}
        isOpen={logsViewerOpen}
        onClose={() => {
          setLogsViewerOpen(false);
          setSelectedContainer(null);
        }}
      />
      
      <ServiceDetailsModal
        service={selectedService}
        isOpen={detailsModalOpen}
        onClose={() => {
          setDetailsModalOpen(false);
          setSelectedService(null);
        }}
        onViewLogs={handleViewLogs}
      />
    </div>
  );
}

function ServiceCard({ service, index, loading, onAction, onViewLogs, onViewDetails, serviceUrls }) {
  const statusConfig = getStatusConfig(service.status);
  const StatusIcon = statusConfig.icon;
  const serviceUrl = serviceUrls[service.name];
  const containerName = service.container_name || service.name;
  const isServiceRunning = service.status === 'healthy' || service.status === 'running';

  // Check if any action is in progress for this service
  const isLoading = Object.keys(loading).some(key =>
    key.startsWith(`${containerName}-`) && loading[key]
  );

  // Get service description and metadata (with null safety)
  const serviceInfo = getServiceInfo(service.name) || { gpu: null, port: null, category: 'Unknown', description: 'No description available' };
  const hasGPU = service.gpu_enabled || serviceInfo?.gpu?.enabled || false;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`relative bg-white dark:bg-gray-800 rounded-xl shadow-sm border ${statusConfig.border} p-6 hover:shadow-md transition-shadow ${isLoading ? 'opacity-75' : ''}`}
    >
      {/* Loading Overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-white/50 dark:bg-gray-900/50 rounded-xl flex items-center justify-center z-10">
          <div className="flex flex-col items-center gap-2">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-500 border-t-transparent" />
            <span className="text-xs font-medium text-gray-600 dark:text-gray-300">Processing...</span>
          </div>
        </div>
      )}
      {/* Status Indicator */}
      <div className="absolute top-4 right-4">
        <div className={`flex items-center gap-2 px-2 py-1 rounded-full ${statusConfig.bg}`}>
          <StatusIcon className={`h-4 w-4 ${statusConfig.color} ${statusConfig.pulse ? 'animate-pulse' : ''}`} />
          <span className={`text-xs font-medium ${statusConfig.color}`}>
            {statusConfig.label}
          </span>
          <HelpTooltip 
            title={getTooltip('services', 'serviceStatus', service.status === 'healthy' || service.status === 'running' ? 'running' : service.status === 'starting' || service.status === 'restarting' ? 'starting' : 'stopped')?.title || 'Service Status'}
            content={getTooltip('services', 'serviceStatus', service.status === 'healthy' || service.status === 'running' ? 'running' : service.status === 'starting' || service.status === 'restarting' ? 'starting' : 'stopped')?.content || 'Current service operational status'}
            position="left"
          />
        </div>
      </div>

      {/* Service Icon and Name */}
      <div className="mb-4">
        <div className={`h-12 w-12 rounded-lg ${hasGPU ? 'bg-gradient-to-br from-red-500 to-orange-500' : 'bg-gradient-to-br from-blue-500 to-purple-600'} flex items-center justify-center mb-3 relative`}>
          {hasGPU ? (
            <FireIcon className="h-6 w-6 text-white" />
          ) : (
            <ServerIcon className="h-6 w-6 text-white" />
          )}
          {hasGPU && (
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-pulse"></div>
          )}
        </div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {serviceInfo?.name || service.display_name || service.name}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 leading-tight">
          {(serviceInfo?.description || 'No description available').slice(0, 80)}...
        </p>
        <div className="flex items-center gap-2 mt-2">
          <div className="flex items-center gap-1">
            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
              serviceInfo?.category === 'AI Core' ? 'bg-purple-100 text-purple-800 dark:bg-purple-800 dark:text-purple-200' :
              serviceInfo?.category === 'AI Processing' ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-800 dark:text-indigo-200' :
              serviceInfo?.category === 'Speech Processing' ? 'bg-pink-100 text-pink-800 dark:bg-pink-800 dark:text-pink-200' :
              serviceInfo?.category === 'Database' ? 'bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-200' :
              serviceInfo?.category === 'Monitoring' ? 'bg-orange-100 text-orange-800 dark:bg-orange-800 dark:text-orange-200' :
              'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
            }`}>
              {serviceInfo?.category || 'Unknown'}
            </span>
            <HelpTooltip 
              title={getTooltip('services', 'categoryBadge').title}
              content={getTooltip('services', 'categoryBadge').content}
              position="top"
            />
          </div>
          {hasGPU && (
            <div className="flex items-center gap-1">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-200">
                <ComputerDesktopIcon className="h-3 w-3 mr-1" />
                {serviceInfo?.gpu?.type || 'N/A'}
              </span>
              <HelpTooltip 
                title={getTooltip('services', 'gpuIndicator').title}
                content={getTooltip('services', 'gpuIndicator').content}
                position="top"
              />
            </div>
          )}
        </div>
      </div>

      {/* Metrics */}
      <div className="space-y-2 mb-4">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <CpuChipIcon className="h-4 w-4" />
            <span className="text-gray-500 dark:text-gray-400">CPU</span>
            <HelpTooltip 
              title={getTooltip('services', 'cpuMetric').title}
              content={getTooltip('services', 'cpuMetric').content}
              position="left"
            />
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {/* REFACTORED: Using safeToFixed for safe number formatting */}
            {service.cpu_percent ? `${safeToFixed(service.cpu_percent, 1)}%` : '0%'}
          </span>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-1">
            <CircleStackIcon className="h-4 w-4" />
            <span className="text-gray-500 dark:text-gray-400">RAM</span>
            <HelpTooltip 
              title={getTooltip('services', 'ramMetric').title}
              content={getTooltip('services', 'ramMetric').content}
              position="left"
            />
          </div>
          <span className="font-medium text-gray-900 dark:text-white">
            {formatMemory(service.memory_mb)}
          </span>
        </div>
        {(service.port || serviceInfo?.port) && (
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1">
              <GlobeAltIcon className="h-4 w-4" />
              <span className="text-gray-500 dark:text-gray-400">Port</span>
              <HelpTooltip 
                title={getTooltip('services', 'portNumber').title}
                content={getTooltip('services', 'portNumber').content}
                position="left"
              />
            </div>
            <span className="font-medium text-gray-900 dark:text-white">
              {service.port || serviceInfo?.port}
            </span>
          </div>
        )}
        {hasGPU && serviceInfo?.gpu?.vram && (
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-1">
              <FireIcon className="h-4 w-4" />
              <span className="text-gray-500 dark:text-gray-400">VRAM</span>
              <HelpTooltip 
                title={getTooltip('services', 'vramIndicator').title}
                content={getTooltip('services', 'vramIndicator').content}
                position="left"
              />
            </div>
            <span className="font-medium text-gray-900 dark:text-white">
              {serviceInfo?.gpu?.vram || 'N/A'}
            </span>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-3 gap-2">
        {!isServiceRunning ? (
          <button
            onClick={() => onAction(containerName, 'start')}
            disabled={isLoading || loading[`${containerName}-start`]}
            className="flex items-center justify-center gap-1 px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            {loading[`${containerName}-start`] ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            ) : (
              <>
                <PlayIcon className="h-4 w-4" />
                Start
              </>
            )}
          </button>
        ) : (
          <button
            onClick={() => onAction(containerName, 'stop')}
            disabled={isLoading || loading[`${containerName}-stop`]}
            className="flex items-center justify-center gap-1 px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
          >
            {loading[`${containerName}-stop`] ? (
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
            ) : (
              <>
                <StopIcon className="h-4 w-4" />
                Stop
              </>
            )}
          </button>
        )}

        <button
          onClick={() => onAction(containerName, 'restart')}
          disabled={isLoading || loading[`${containerName}-restart`] || !isServiceRunning}
          className="flex items-center justify-center gap-1 px-3 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
        >
          {loading[`${containerName}-restart`] ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
          ) : (
            <>
              <ArrowPathIcon className="h-4 w-4" />
              Restart
            </>
          )}
        </button>

        {serviceUrl && isServiceRunning && (
          <a
            href={serviceUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
          >
            <GlobeAltIcon className="h-4 w-4" />
            Open
          </a>
        )}
      </div>

      {/* Additional Actions */}
      <div className="mt-3 pt-3 border-t dark:border-gray-700 flex gap-2">
        <button
          onClick={() => onViewLogs(containerName)}
          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <DocumentTextIcon className="h-3.5 w-3.5" />
          Logs
        </button>
        <button
          onClick={() => onViewDetails(service)}
          className="flex-1 flex items-center justify-center gap-1 px-2 py-1.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
        >
          <InformationCircleIcon className="h-3.5 w-3.5" />
          Details
        </button>
      </div>
    </motion.div>
  );
}

function ServiceTable({ services, loading, onAction, onViewLogs, onViewDetails, serviceUrls }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">All Services</h2>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Service
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Resources
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Port
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {services.map((service, index) => {
              const statusConfig = getStatusConfig(service.status);
              const StatusIcon = statusConfig.icon;
              const containerName = service.container_name || service.name;
              const isServiceRunning = service.status === 'healthy' || service.status === 'running';
              const serviceUrl = serviceUrls[service.name];

              // Check if any action is in progress for this service
              const isLoading = Object.keys(loading).some(key =>
                key.startsWith(`${containerName}-`) && loading[key]
              );
              
              return (
                <motion.tr
                  key={containerName}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: index * 0.02 }}
                  className={`hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${isLoading ? 'opacity-50' : ''}`}
                >
                  {/* Service Name */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mr-3">
                        {service.gpu_enabled ? (
                          <CpuChipSolid className="h-5 w-5 text-white" />
                        ) : (
                          <ServerIcon className="h-5 w-5 text-white" />
                        )}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {service.display_name}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {service.name}
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  {/* Status */}
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm ${statusConfig.bg}`}>
                      <StatusIcon className={`h-4 w-4 ${statusConfig.color} ${statusConfig.pulse ? 'animate-pulse' : ''}`} />
                      <span className={`font-medium ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </div>
                  </td>
                  
                  {/* Resources */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <CpuChipIcon className="h-3 w-3 text-gray-400" />
                        {/* REFACTORED: Using safeToFixed for safe formatting */}
                        <span>CPU: {service.cpu_percent ? `${safeToFixed(service.cpu_percent, 1)}%` : '0%'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <CircleStackIcon className="h-3 w-3 text-gray-400" />
                        <span>RAM: {formatMemory(service.memory_mb)}</span>
                      </div>
                    </div>
                  </td>
                  
                  {/* Port */}
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                    {service.port ? (
                      <div className="flex items-center gap-1">
                        <GlobeAltIcon className="h-3 w-3 text-gray-400" />
                        {service.port}
                      </div>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  
                  {/* Actions */}
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end gap-2">
                      {isLoading && (
                        <div className="inline-flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 mr-2">
                          <div className="animate-spin rounded-full h-3 w-3 border border-blue-500 border-t-transparent" />
                          Processing...
                        </div>
                      )}
                      {!isServiceRunning ? (
                        <button
                          onClick={() => onAction(containerName, 'start')}
                          disabled={isLoading || loading[`${containerName}-start`]}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors disabled:opacity-50 text-xs"
                        >
                          {loading[`${containerName}-start`] ? (
                            <div className="animate-spin rounded-full h-3 w-3 border border-white border-t-transparent" />
                          ) : (
                            <PlayIcon className="h-3 w-3" />
                          )}
                          Start
                        </button>
                      ) : (
                        <button
                          onClick={() => onAction(containerName, 'stop')}
                          disabled={isLoading || loading[`${containerName}-stop`]}
                          className="inline-flex items-center gap-1 px-3 py-1 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:opacity-50 text-xs"
                        >
                          {loading[`${containerName}-stop`] ? (
                            <div className="animate-spin rounded-full h-3 w-3 border border-white border-t-transparent" />
                          ) : (
                            <StopIcon className="h-3 w-3" />
                          )}
                          Stop
                        </button>
                      )}

                      <button
                        onClick={() => onAction(containerName, 'restart')}
                        disabled={isLoading || loading[`${containerName}-restart`] || !isServiceRunning}
                        className="inline-flex items-center gap-1 px-3 py-1 bg-yellow-600 text-white rounded-md hover:bg-yellow-700 transition-colors disabled:opacity-50 text-xs"
                      >
                        {loading[`${containerName}-restart`] ? (
                          <div className="animate-spin rounded-full h-3 w-3 border border-white border-t-transparent" />
                        ) : (
                          <ArrowPathIcon className="h-3 w-3" />
                        )}
                        Restart
                      </button>
                      
                      {serviceUrl && isServiceRunning && (
                        <a
                          href={serviceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-xs"
                        >
                          <GlobeAltIcon className="h-3 w-3" />
                          Open
                        </a>
                      )}
                      
                      <button
                        onClick={() => onViewLogs(containerName)}
                        className="inline-flex items-center gap-1 px-2 py-1 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-xs"
                      >
                        <DocumentTextIcon className="h-3 w-3" />
                        Logs
                      </button>
                      
                      <button
                        onClick={() => onViewDetails(service)}
                        className="inline-flex items-center gap-1 px-2 py-1 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors text-xs"
                      >
                        <InformationCircleIcon className="h-3 w-3" />
                        Details
                      </button>
                    </div>
                  </td>
                </motion.tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}