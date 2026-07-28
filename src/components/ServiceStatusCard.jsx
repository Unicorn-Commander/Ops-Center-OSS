import React from 'react';
import { motion } from 'framer-motion';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  ClockIcon
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
    icon: XCircleIcon,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    label: 'Stopped'
  },
  unknown: {
    icon: ExclamationTriangleIcon,
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-50 dark:bg-gray-900/20',
    border: 'border-gray-200 dark:border-gray-800',
    label: 'Unknown'
  }
};

export default function ServiceStatusCard({ service }) {
  const config = statusConfig[service.status] || statusConfig.unknown;
  const StatusIcon = config.icon;
  
  const handleServiceClick = () => {
    // If service has a URL, open it in a new tab
    const host = window.location.hostname;
    const serviceUrls = {
      'vllm': `http://${host}:8000/docs`,
      'open-webui': `http://${host}:8080`,
      'searxng': `http://${host}:8888`,
      'prometheus': `http://${host}:9090`
    };
    
    const url = serviceUrls[service.id];
    if (url) {
      window.open(url, '_blank');
    }
  };
  
  const hasUrl = ['vllm', 'open-webui', 'searxng', 'prometheus'].includes(service.id);
  
  return (
    <motion.div
      className={`relative overflow-hidden rounded-lg border-2 ${config.bg} ${config.border} p-4 shadow-sm transition-all duration-200 ${
        hasUrl ? 'cursor-pointer hover:shadow-md hover:scale-105' : ''
      }`}
      onClick={hasUrl ? handleServiceClick : undefined}
      whileHover={hasUrl ? { scale: 1.02 } : {}}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {service.isImage ? (
            <img 
              src={service.icon} 
              alt={service.name} 
              className="w-5 h-5 object-contain"
            />
          ) : (
            <span className="text-lg">{service.icon}</span>
          )}
          <h3 className="font-medium text-gray-900 dark:text-white">
            {service.name}
          </h3>
        </div>
        
        <div className="flex items-center gap-1">
          <StatusIcon className={`h-4 w-4 ${config.color}`} />
          <span className={`text-xs font-medium ${config.color}`}>
            {config.label}
          </span>
        </div>
      </div>
      
      <div className="space-y-1">
        {service.port && (
          <p className="text-xs text-gray-600 dark:text-gray-400">
            Port: {service.port}
          </p>
        )}
        
        {service.description && (
          <p className="text-xs text-gray-500 dark:text-gray-500">
            {service.description}
          </p>
        )}
        
        {service.critical && (
          <div className="flex items-center gap-1 mt-2">
            <div className="w-1 h-1 bg-red-500 rounded-full"></div>
            <span className="text-xs text-red-600 dark:text-red-400 font-medium">
              Critical Service
            </span>
          </div>
        )}
      </div>
      
      {hasUrl && (
        <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
        </div>
      )}
      
      {/* Animated background for interactive cards */}
      {hasUrl && (
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full opacity-0 hover:opacity-100 transition-opacity duration-500" />
      )}
    </motion.div>
  );
}