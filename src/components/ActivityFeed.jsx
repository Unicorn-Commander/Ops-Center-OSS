import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ClockIcon,
  UserIcon
} from '@heroicons/react/24/outline';

const activityTypes = {
  service_started: {
    icon: CheckCircleIcon,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-50 dark:bg-green-900/20'
  },
  service_stopped: {
    icon: XCircleIcon,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-50 dark:bg-red-900/20'
  },
  alert_generated: {
    icon: ExclamationTriangleIcon,
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20'
  },
  system_info: {
    icon: InformationCircleIcon,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-50 dark:bg-blue-900/20'
  },
  user_action: {
    icon: UserIcon,
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-50 dark:bg-purple-900/20'
  }
};

export default function ActivityFeed({ alerts, services }) {
  const [activities, setActivities] = useState([]);
  const [previousServices, setPreviousServices] = useState([]);
  
  // Generate activities from alerts and service changes
  useEffect(() => {
    const newActivities = [];
    
    // Add alert activities
    alerts.forEach(alert => {
      newActivities.push({
        id: `alert-${alert.id}`,
        type: 'alert_generated',
        title: alert.title,
        description: alert.message,
        timestamp: alert.timestamp || new Date(),
        metadata: { alertType: alert.type }
      });
    });
    
    // Detect service state changes (only for relevant changes)
    if (previousServices.length > 0) {
      services.forEach(service => {
        const prevService = previousServices.find(s => s.name === service.name);
        if (prevService && prevService.status !== service.status) {
          // Skip "not_created" status changes for extensions
          if (service.status === 'not_created' || prevService.status === 'not_created') {
            return;
          }
          
          const isHealthy = service.status === 'healthy' || service.status === 'running';
          const wasHealthy = prevService.status === 'healthy' || prevService.status === 'running';
          
          // Only track actual state changes
          if (isHealthy !== wasHealthy) {
            newActivities.push({
              id: `service-${service.name}-${Date.now()}`,
              type: isHealthy ? 'service_started' : 'service_stopped',
              title: `Service ${isHealthy ? 'Started' : 'Stopped'}`,
              description: `${service.display_name || service.name} is now ${service.status}`,
              timestamp: new Date(),
              metadata: { 
                serviceName: service.name, 
                status: service.status,
                category: service.category 
              }
            });
          }
        }
      });
    }
    
    // Add system info activities periodically
    const now = new Date();
    if (activities.length === 0 || (now - activities[0]?.timestamp) > 300000) { // 5 minutes
      const runningServices = services.filter(s => s.status === 'healthy' || s.status === 'running');
      const coreServices = services.filter(s => s.category === 'core' && s.status !== 'not_created');
      const runningCore = coreServices.filter(s => s.status === 'healthy' || s.status === 'running');
      
      newActivities.push({
        id: `system-info-${now.getTime()}`,
        type: 'system_info',
        title: 'System Health Check',
        description: `${runningCore.length}/${coreServices.length} core services running • ${runningServices.length} total services active`,
        timestamp: now,
        metadata: { 
          serviceCount: services.length,
          runningCount: runningServices.length,
          coreCount: coreServices.length
        }
      });
    }
    
    if (newActivities.length > 0) {
      setActivities(prev => {
        const combined = [...newActivities, ...prev];
        // Keep only last 50 activities and sort by timestamp
        return combined
          .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
          .slice(0, 50);
      });
    }
    
    setPreviousServices(services);
  }, [alerts, services, previousServices, activities]);
  
  // Add user action activities
  const addUserActivity = (title, description) => {
    const activity = {
      id: `user-action-${Date.now()}`,
      type: 'user_action',
      title,
      description,
      timestamp: new Date(),
      metadata: { userGenerated: true }
    };
    
    setActivities(prev => [activity, ...prev].slice(0, 50));
  };
  
  const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const diff = now - new Date(timestamp);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (days > 0) return `${days}d ago`;
    if (hours > 0) return `${hours}h ago`;
    if (minutes > 0) return `${minutes}m ago`;
    return 'Just now';
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          Activity Feed
        </h2>
        
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span className="text-sm text-gray-600 dark:text-gray-400">Live</span>
        </div>
      </div>
      
      <div className="space-y-4 max-h-96 overflow-y-auto">
        <AnimatePresence initial={false}>
          {activities.length === 0 ? (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <ClockIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No recent activity</p>
              <p className="text-sm mt-1">System activities will appear here</p>
            </div>
          ) : (
            activities.map((activity, index) => {
              const config = activityTypes[activity.type] || activityTypes.system_info;
              const ActivityIcon = config.icon;
              
              return (
                <motion.div
                  key={activity.id}
                  initial={{ opacity: 0, x: -20, height: 0 }}
                  animate={{ opacity: 1, x: 0, height: 'auto' }}
                  exit={{ opacity: 0, x: 20, height: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  className={`flex items-start gap-3 p-3 rounded-lg ${config.bg} border border-gray-200 dark:border-gray-700`}
                >
                  <div className="flex-shrink-0">
                    <ActivityIcon className={`h-5 w-5 ${config.color} mt-0.5`} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        {activity.title}
                      </h3>
                      <span className="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
                        {formatTimeAgo(activity.timestamp)}
                      </span>
                    </div>
                    
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {activity.description}
                    </p>
                    
                    {activity.metadata && (
                      <div className="mt-2 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-500">
                        {activity.metadata.serviceName && (
                          <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                            {activity.metadata.serviceName}
                          </span>
                        )}
                        {activity.metadata.alertType && (
                          <span className={`px-2 py-1 rounded ${
                            activity.metadata.alertType === 'error' ? 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400' :
                            activity.metadata.alertType === 'warning' ? 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400' :
                            'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400'
                          }`}>
                            {activity.metadata.alertType}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>
      
      {activities.length > 10 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <button 
            onClick={() => setActivities(prev => prev.slice(0, 10))}
            className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors"
          >
            Show fewer activities
          </button>
        </div>
      )}
    </div>
  );
}