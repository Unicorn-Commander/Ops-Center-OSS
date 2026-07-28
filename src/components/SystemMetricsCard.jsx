import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from '@heroicons/react/24/outline';

const colorSchemes = {
  green: {
    bg: 'bg-green-50 dark:bg-green-900/20',
    border: 'border-green-200 dark:border-green-800',
    icon: 'text-green-600 dark:text-green-400',
    value: 'text-green-900 dark:text-green-100',
    title: 'text-green-700 dark:text-green-300'
  },
  yellow: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    icon: 'text-yellow-600 dark:text-yellow-400',
    value: 'text-yellow-900 dark:text-yellow-100',
    title: 'text-yellow-700 dark:text-yellow-300'
  },
  red: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    icon: 'text-red-600 dark:text-red-400',
    value: 'text-red-900 dark:text-red-100',
    title: 'text-red-700 dark:text-red-300'
  },
  blue: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    icon: 'text-blue-600 dark:text-blue-400',
    value: 'text-blue-900 dark:text-blue-100',
    title: 'text-blue-700 dark:text-blue-300'
  }
};

export default function SystemMetricsCard({ title, value, icon: Icon, color = 'blue', trend = 0, details }) {
  const scheme = colorSchemes[color] || colorSchemes.blue;
  
  const getTrendIcon = () => {
    if (trend > 1) return ArrowUpIcon;
    if (trend < -1) return ArrowDownIcon;
    return MinusIcon;
  };
  
  const getTrendColor = () => {
    if (trend > 1) return 'text-red-500';
    if (trend < -1) return 'text-green-500';
    return 'text-gray-400';
  };
  
  const TrendIcon = getTrendIcon();
  
  return (
    <motion.div
      className={`relative overflow-hidden rounded-lg border-2 ${scheme.bg} ${scheme.border} p-6 shadow-sm hover:shadow-md transition-shadow duration-200`}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <p className={`text-sm font-medium ${scheme.title}`}>
              {title}
            </p>
            <div className="flex items-center gap-1">
              <TrendIcon className={`h-3 w-3 ${getTrendColor()}`} />
              <span className={`text-xs ${getTrendColor()}`}>
                {Math.abs(trend).toFixed(1)}%
              </span>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <Icon className={`h-8 w-8 ${scheme.icon}`} />
            <div>
              <p className={`text-2xl font-bold ${scheme.value}`}>
                {value}
              </p>
              {details && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {details}
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
      
      {/* Animated background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full animate-pulse opacity-0 hover:opacity-100 transition-opacity duration-500" />
    </motion.div>
  );
}