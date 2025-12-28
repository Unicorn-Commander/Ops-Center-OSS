import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  PlayIcon,
  StopIcon,
  ArrowPathIcon,
  CubeIcon,
  CogIcon,
  ChartBarIcon,
  DocumentTextIcon,
  WifiIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

const quickActions = [
  {
    id: 'models',
    title: 'Manage Models',
    description: 'Browse and download AI models',
    icon: CubeIcon,
    color: 'bg-blue-500 hover:bg-blue-600',
    path: '/admin/models'
  },
  {
    id: 'services',
    title: 'Service Control',
    description: 'Start, stop, and manage services',
    icon: CogIcon,
    color: 'bg-green-500 hover:bg-green-600',
    path: '/admin/services'
  },
  {
    id: 'system',
    title: 'System Monitor',
    description: 'View detailed system metrics',
    icon: ChartBarIcon,
    color: 'bg-purple-500 hover:bg-purple-600',
    path: '/admin/system'
  },
  {
    id: 'network',
    title: 'Network Setup',
    description: 'Configure network and WiFi',
    icon: WifiIcon,
    color: 'bg-orange-500 hover:bg-orange-600',
    path: '/admin/network'
  },
  {
    id: 'logs',
    title: 'View Logs',
    description: 'Check system and service logs',
    icon: DocumentTextIcon,
    color: 'bg-gray-500 hover:bg-gray-600',
    action: 'logs'
  }
];

const serviceActions = [
  {
    id: 'restart-all',
    title: 'Restart All',
    description: 'Restart all critical services',
    icon: ArrowPathIcon,
    color: 'bg-yellow-500 hover:bg-yellow-600',
    action: 'restart-all'
  },
  {
    id: 'stop-all',
    title: 'Stop All',
    description: 'Stop all non-critical services',
    icon: StopIcon,
    color: 'bg-red-500 hover:bg-red-600',
    action: 'stop-all'
  },
  {
    id: 'start-all',
    title: 'Start All',
    description: 'Start all configured services',
    icon: PlayIcon,
    color: 'bg-green-500 hover:bg-green-600',
    action: 'start-all'
  }
];

export default function QuickActions({ systemStatus, services }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState({});
  
  const handleAction = async (action) => {
    if (action.path) {
      navigate(action.path);
      return;
    }
    
    if (action.url) {
      window.open(action.url, '_blank');
      return;
    }
    
    setLoading(prev => ({ ...prev, [action.id]: true }));
    
    try {
      switch (action.action) {
        case 'restart-all':
          // Restart critical services
          const criticalServices = ['vllm', 'open-webui'];
          for (const serviceName of criticalServices) {
            await fetch(`/api/v1/services/${serviceName}/action`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action: 'restart' })
            });
          }
          break;
          
        case 'stop-all':
          // Stop non-critical services
          const nonCriticalServices = services
            .filter(s => !['vllm', 'open-webui', 'postgres', 'redis'].includes(s.name))
            .map(s => s.name);
          
          for (const serviceName of nonCriticalServices) {
            await fetch(`/api/v1/services/${serviceName}/action`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ action: 'stop' })
            });
          }
          break;
          
        case 'start-all':
          // Start all services
          for (const service of services) {
            if (service.status !== 'healthy') {
              await fetch(`/api/v1/services/${service.name}/action`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'start' })
              });
            }
          }
          break;
          
        case 'logs':
          // Open logs in a new window or modal
          window.open('/logs', '_blank');
          break;
          
        default:
          console.log('Unknown action:', action.action);
      }
    } catch (error) {
      console.error('Action failed:', error);
    } finally {
      setLoading(prev => ({ ...prev, [action.id]: false }));
    }
  };
  
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
      opacity: 1
    }
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Quick Actions
        </h2>
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Click any action to execute
        </div>
      </div>
      
      {/* Navigation Actions */}
      <div className="mb-6">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Navigation
        </h3>
        <motion.div 
          className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {quickActions.map((action) => {
            const ActionIcon = action.icon;
            return (
              <motion.button
                key={action.id}
                variants={itemVariants}
                onClick={() => handleAction(action)}
                disabled={loading[action.id]}
                className={`relative overflow-hidden rounded-lg p-4 text-white transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${action.color}`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <div className="flex flex-col items-center text-center">
                  <ActionIcon className="h-6 w-6 mb-2" />
                  <div className="text-sm font-medium mb-1">
                    {action.title}
                  </div>
                  <div className="text-xs opacity-80">
                    {action.description}
                  </div>
                </div>
                
                {loading[action.id] && (
                  <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  </div>
                )}
                
                {/* Hover effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full transition-transform duration-700 group-hover:translate-x-full" />
              </motion.button>
            );
          })}
        </motion.div>
      </div>
      
      {/* Service Control Actions */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
          Service Control
        </h3>
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-3"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {serviceActions.map((action) => {
            const ActionIcon = action.icon;
            return (
              <motion.button
                key={action.id}
                variants={itemVariants}
                onClick={() => handleAction(action)}
                disabled={loading[action.id]}
                className={`relative overflow-hidden rounded-lg p-4 text-white transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed ${action.color}`}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <div className="flex items-center gap-3">
                  <ActionIcon className="h-5 w-5" />
                  <div className="text-left">
                    <div className="text-sm font-medium">
                      {action.title}
                    </div>
                    <div className="text-xs opacity-80">
                      {action.description}
                    </div>
                  </div>
                </div>
                
                {loading[action.id] && (
                  <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
                  </div>
                )}
                
                {/* Hover effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full transition-transform duration-700 group-hover:translate-x-full" />
              </motion.button>
            );
          })}
        </motion.div>
      </div>
    </div>
  );
}