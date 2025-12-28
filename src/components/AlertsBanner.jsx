import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ExclamationTriangleIcon, 
  XCircleIcon, 
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const alertConfig = {
  error: {
    icon: XCircleIcon,
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-800 dark:text-red-200',
    iconColor: 'text-red-600 dark:text-red-400'
  },
  warning: {
    icon: ExclamationTriangleIcon,
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    text: 'text-yellow-800 dark:text-yellow-200',
    iconColor: 'text-yellow-600 dark:text-yellow-400'
  },
  info: {
    icon: InformationCircleIcon,
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-800 dark:text-blue-200',
    iconColor: 'text-blue-600 dark:text-blue-400'
  }
};

export default function AlertsBanner({ alerts, onDismiss }) {
  if (!alerts || alerts.length === 0) return null;
  
  // Group alerts by type
  const groupedAlerts = alerts.reduce((acc, alert) => {
    const type = alert.type || 'info';
    if (!acc[type]) acc[type] = [];
    acc[type].push(alert);
    return acc;
  }, {});
  
  // Show most critical alerts first
  const priorityOrder = ['error', 'warning', 'info'];
  const sortedTypes = priorityOrder.filter(type => groupedAlerts[type]);
  
  return (
    <div className="space-y-3">
      <AnimatePresence>
        {sortedTypes.map(type => {
          const typeAlerts = groupedAlerts[type];
          const config = alertConfig[type];
          const AlertIcon = config.icon;
          
          return (
            <motion.div
              key={type}
              initial={{ opacity: 0, y: -20, height: 0 }}
              animate={{ opacity: 1, y: 0, height: 'auto' }}
              exit={{ opacity: 0, y: -20, height: 0 }}
              transition={{ duration: 0.3 }}
              className={`rounded-lg border-2 ${config.bg} ${config.border} p-4 shadow-sm`}
            >
              <div className="flex items-start gap-3">
                <AlertIcon className={`h-5 w-5 ${config.iconColor} mt-0.5 flex-shrink-0`} />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className={`font-medium ${config.text} capitalize`}>
                      {type} Alert{typeAlerts.length > 1 ? 's' : ''}
                      {typeAlerts.length > 1 && (
                        <span className="ml-1 text-sm font-normal">({typeAlerts.length})</span>
                      )}
                    </h3>
                  </div>
                  
                  <div className="space-y-2">
                    {typeAlerts.map((alert, index) => (
                      <div key={alert.id} className="flex items-center justify-between">
                        <div className="flex-1 min-w-0">
                          <p className={`text-sm ${config.text} font-medium`}>
                            {alert.title}
                          </p>
                          <p className={`text-xs ${config.text} opacity-80 mt-1`}>
                            {alert.message}
                          </p>
                          {alert.timestamp && (
                            <p className={`text-xs ${config.text} opacity-60 mt-1`}>
                              {alert.timestamp.toLocaleTimeString()}
                            </p>
                          )}
                        </div>
                        
                        <button
                          onClick={() => onDismiss(alert.id)}
                          className={`ml-3 flex-shrink-0 p-1 rounded-full ${config.iconColor} hover:bg-black/10 dark:hover:bg-white/10 transition-colors`}
                        >
                          <XMarkIcon className="h-4 w-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              
              {/* Progress bar for auto-dismiss */}
              <motion.div
                className={`mt-3 h-1 bg-black/10 dark:bg-white/10 rounded-full overflow-hidden`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 0.5 }}
              >
                <motion.div
                  className={`h-full ${config.iconColor.replace('text-', 'bg-')}`}
                  initial={{ width: '100%' }}
                  animate={{ width: '0%' }}
                  transition={{ duration: 10, ease: 'linear' }}
                  onAnimationComplete={() => {
                    // Auto-dismiss after 10 seconds
                    typeAlerts.forEach(alert => onDismiss(alert.id));
                  }}
                />
              </motion.div>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}