/**
 * Reusable Metric Card Component
 * Displays a single metric with icon, value, label, and optional trend
 */

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

const MetricCard = ({
  icon: Icon,
  label,
  value,
  trend,
  trendValue,
  color = 'purple',
  suffix = '',
  loading = false
}) => {
  const { currentTheme } = useTheme();

  const colorClasses = {
    purple: 'text-purple-400 bg-purple-500/10',
    green: 'text-green-400 bg-green-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
    pink: 'text-pink-400 bg-pink-500/10',
    yellow: 'text-yellow-400 bg-yellow-500/10',
    red: 'text-red-400 bg-red-500/10',
  };

  const bgClass = currentTheme === 'unicorn'
    ? 'bg-purple-900/20 border border-purple-500/20'
    : currentTheme === 'light'
    ? 'bg-white border border-gray-200'
    : 'bg-gray-800 border border-gray-700';

  const textClass = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const subtextClass = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  if (loading) {
    return (
      <div className={`${bgClass} rounded-xl p-6 animate-pulse`}>
        <div className="h-8 w-8 bg-gray-700 rounded-lg mb-4"></div>
        <div className="h-8 bg-gray-700 rounded w-3/4 mb-2"></div>
        <div className="h-4 bg-gray-700 rounded w-1/2"></div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${bgClass} rounded-xl p-6`}
    >
      <div className="flex items-center justify-between mb-4">
        <div className={`${colorClasses[color]} p-2 rounded-lg`}>
          <Icon className="w-6 h-6" />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-sm ${
            trend === 'up' ? 'text-green-400' : 'text-red-400'
          }`}>
            {trend === 'up' ? (
              <ArrowTrendingUpIcon className="w-4 h-4" />
            ) : (
              <ArrowTrendingDownIcon className="w-4 h-4" />
            )}
            <span>{trendValue}</span>
          </div>
        )}
      </div>
      <h3 className={`text-3xl font-bold ${textClass} mb-1`}>
        {value}{suffix}
      </h3>
      <p className={`text-sm ${subtextClass}`}>{label}</p>
    </motion.div>
  );
};

export default MetricCard;
