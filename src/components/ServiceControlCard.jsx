import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  Cog6ToothIcon,
  GlobeAltIcon,
  CpuChipIcon,
  CircleStackIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';

const statusConfig = {
  healthy: {
    icon: CheckCircleIcon,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    label: 'Healthy'
  },
  starting: {
    icon: ClockIcon,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    label: 'Starting'
  },
  stopped: {
    icon: StopIcon,
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    border: 'border-gray-200 dark:border-gray-800',
    label: 'Stopped'
  },
  error: {
    icon: XCircleIcon,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    label: 'Error'
  },
  unknown: {
    icon: ExclamationTriangleIcon,
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    label: 'Unknown'
  }
};

// Service URLs will be passed as props or fetched dynamically
const defaultServiceUrls = {
  'vllm': { url: 'http://localhost:8000/docs', label: 'API Documentation' },
  'open-webui': { url: 'http://localhost:8080', label: 'Chat Interface' },
  'searxng': { url: 'http://localhost:8888', label: 'Search Interface' },
  'prometheus': { url: 'http://localhost:9090', label: 'Metrics Dashboard' },
  'admin-dashboard': { url: 'http://localhost:8084', label: 'Admin Dashboard' }
};

export default function ServiceControlCard({ 
  service, 
  loading, 
  onAction, 
  onViewLogs, 
  onConfigure, 
  systemStatus,
  serviceUrls = defaultServiceUrls
}) {
  const [expanded, setExpanded] = useState(false);
  
  const config = statusConfig[service.status] || statusConfig.unknown;
  const StatusIcon = config.icon;
  const serviceUrl = serviceUrls[service.name];

  const getActionButtons = () => {
    const buttons = [];
    
    if (service.status === 'healthy') {
      buttons.push({
        action: 'stop',
        icon: StopIcon,
        label: 'Stop',
        color: 'bg-red-600 hover:bg-red-700'
      });
      buttons.push({
        action: 'restart',
        icon: ArrowPathIcon,
        label: 'Restart',
        color: 'bg-yellow-600 hover:bg-yellow-700'
      });
    } else if (service.status === 'stopped') {
      buttons.push({
        action: 'start',
        icon: PlayIcon,
        label: 'Start',
        color: 'bg-green-600 hover:bg-green-700'
      });
    } else {
      buttons.push({
        action: 'restart',
        icon: ArrowPathIcon,
        label: 'Restart',
        color: 'bg-blue-600 hover:bg-blue-700'
      });
    }

    return buttons;
  };

  const formatUptime = (uptime) => {
    if (!uptime) return 'N/A';
    
    const seconds = parseInt(uptime);
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatMemory = (memoryMb) => {
    if (!memoryMb) return 'N/A';
    if (memoryMb > 1024) {
      return `${(memoryMb / 1024).toFixed(1)}GB`;
    }
    return `${memoryMb}MB`;
  };

  return (
    <motion.div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm border-2 ${config.border} overflow-hidden`}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.01 }}
    >
      {/* Main Card Content */}
      <div className="p-6">
        <div className="flex items-start justify-between">
          {/* Service Info */}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-2">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                {service.display_name || service.name}
              </h3>
              <div className={`flex items-center gap-1 px-2 py-1 rounded-full ${config.bg}`}>
                <StatusIcon className={`h-4 w-4 ${config.color}`} />
                <span className={`text-sm font-medium ${config.color}`}>
                  {config.label}
                </span>
              </div>
            </div>
            
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              {service.description || 'No description available'}
            </p>

            {/* Metrics Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="flex items-center gap-2">
                <CpuChipIcon className="h-4 w-4 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {service.cpu_percent ? `${service.cpu_percent.toFixed(1)}%` : '0%'}
                  </div>
                  <div className="text-xs text-gray-500">CPU</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <CircleStackIcon className="h-4 w-4 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatMemory(service.memory_mb)}
                  </div>
                  <div className="text-xs text-gray-500">Memory</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <ClockIcon className="h-4 w-4 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {formatUptime(service.uptime)}
                  </div>
                  <div className="text-xs text-gray-500">Uptime</div>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <GlobeAltIcon className="h-4 w-4 text-gray-400" />
                <div>
                  <div className="text-sm font-medium text-gray-900 dark:text-white">
                    {service.port || 'N/A'}
                  </div>
                  <div className="text-xs text-gray-500">Port</div>
                </div>
              </div>
            </div>

            {/* Health Check Info */}
            {service.health_check && (
              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="text-sm">
                  <span className="font-medium text-gray-900 dark:text-white">
                    Health: 
                  </span>
                  <span className={`ml-1 ${
                    service.health_check.status === 'healthy' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {service.health_check.status}
                  </span>
                  {service.health_check.message && (
                    <span className="ml-2 text-gray-600 dark:text-gray-400">
                      ({service.health_check.message})
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col gap-2 ml-6">
            {/* Service Control Buttons */}
            <div className="flex gap-2">
              {getActionButtons().map(button => {
                const ButtonIcon = button.icon;
                const isLoading = loading === button.action;
                
                return (
                  <button
                    key={button.action}
                    onClick={() => onAction(button.action)}
                    disabled={isLoading}
                    className={`flex items-center gap-1 px-3 py-2 text-white rounded-lg transition-colors disabled:opacity-50 ${button.color}`}
                  >
                    {isLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                    ) : (
                      <ButtonIcon className="h-4 w-4" />
                    )}
                    {button.label}
                  </button>
                );
              })}
            </div>

            {/* Secondary Actions */}
            <div className="flex gap-2">
              <button
                onClick={onViewLogs}
                className="flex items-center gap-1 px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                title="View Logs"
              >
                <DocumentTextIcon className="h-4 w-4" />
                Logs
              </button>
              
              <button
                onClick={onConfigure}
                className="flex items-center gap-1 px-3 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                title="Configure Service"
              >
                <Cog6ToothIcon className="h-4 w-4" />
                Config
              </button>
            </div>

            {/* Open UI Button */}
            {serviceUrl && service.status === 'healthy' && (
              <a
                href={serviceUrl.url || serviceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-center"
              >
                <GlobeAltIcon className="h-4 w-4" />
                Open UI
              </a>
            )}
          </div>
        </div>

        {/* Expandable Logs Section */}
        {service.logs && service.logs.length > 0 && (
          <div className="mt-4 border-t dark:border-gray-700 pt-4">
            <button
              onClick={() => setExpanded(!expanded)}
              className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <DocumentTextIcon className="h-4 w-4" />
              Recent Logs ({service.logs.length})
              <motion.div
                animate={{ rotate: expanded ? 180 : 0 }}
                transition={{ duration: 0.2 }}
              >
                ▼
              </motion.div>
            </button>
            
            <motion.div
              initial={false}
              animate={{
                height: expanded ? 'auto' : 0,
                opacity: expanded ? 1 : 0
              }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden"
            >
              <div className="mt-3 bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-x-auto max-h-48 overflow-y-auto">
                {service.logs.slice(-10).map((log, i) => (
                  <div key={i} className="text-green-400 mb-1">
                    {log}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        )}
      </div>
      
      {/* Loading Overlay */}
      {loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute inset-0 bg-black/10 flex items-center justify-center"
        >
          <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow-lg">
            <div className="flex items-center gap-3">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-blue-600 border-t-transparent" />
              <span className="text-gray-900 dark:text-white font-medium">
                {loading}ing service...
              </span>
            </div>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}