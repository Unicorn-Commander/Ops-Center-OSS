/**
 * MetricCard - Compact metric display with optional trend indicator
 */

import React from 'react';
import { motion } from 'framer-motion';
import {
  ArrowUpIcon,
  ArrowDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';

export default function MetricCard({
  title,
  value,
  subtitle = null,
  trend = null, // 'up', 'down', 'neutral', or number (percentage change)
  trendLabel = null,
  icon: Icon = null,
  iconColor = 'from-blue-500 to-cyan-500',
  size = 'md',
  className = ''
}) {
  // Determine trend display
  const getTrendInfo = () => {
    if (trend === null) return null;

    if (typeof trend === 'number') {
      return {
        direction: trend > 0 ? 'up' : trend < 0 ? 'down' : 'neutral',
        value: Math.abs(trend).toFixed(1),
        color: trend > 0 ? 'text-green-400' : trend < 0 ? 'text-red-400' : 'text-gray-400'
      };
    }

    return {
      direction: trend,
      value: trendLabel || '',
      color: trend === 'up' ? 'text-green-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'
    };
  };

  const trendInfo = getTrendInfo();

  const sizeClasses = {
    sm: {
      container: 'p-3',
      title: 'text-xs',
      value: 'text-lg',
      icon: 'w-8 h-8',
      iconInner: 'h-4 w-4'
    },
    md: {
      container: 'p-4',
      title: 'text-sm',
      value: 'text-2xl',
      icon: 'w-10 h-10',
      iconInner: 'h-5 w-5'
    },
    lg: {
      container: 'p-6',
      title: 'text-base',
      value: 'text-3xl',
      icon: 'w-12 h-12',
      iconInner: 'h-6 w-6'
    }
  };

  const sizes = sizeClasses[size] || sizeClasses.md;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl ${sizes.container} ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        {Icon && (
          <div className={`${sizes.icon} bg-gradient-to-br ${iconColor} rounded-xl flex items-center justify-center shadow-lg flex-shrink-0`}>
            <Icon className={`${sizes.iconInner} text-white`} />
          </div>
        )}
        <div className="flex-1 min-w-0">
          <p className={`${sizes.title} font-medium text-gray-400 mb-1 truncate`}>{title}</p>
          <p className={`${sizes.value} font-bold text-white truncate`}>{value}</p>
          {subtitle && (
            <p className="text-xs text-gray-500 mt-1 truncate">{subtitle}</p>
          )}
        </div>
        {trendInfo && (
          <div className={`flex items-center gap-1 ${trendInfo.color}`}>
            {trendInfo.direction === 'up' && <ArrowUpIcon className="w-4 h-4" />}
            {trendInfo.direction === 'down' && <ArrowDownIcon className="w-4 h-4" />}
            {trendInfo.direction === 'neutral' && <MinusIcon className="w-4 h-4" />}
            {trendInfo.value && (
              <span className="text-xs font-medium">{trendInfo.value}%</span>
            )}
          </div>
        )}
      </div>
    </motion.div>
  );
}

// Inline metric for compact displays
export function InlineMetric({
  label,
  value,
  className = ''
}) {
  return (
    <div className={`flex items-center justify-between ${className}`}>
      <span className="text-sm text-gray-400">{label}</span>
      <span className="text-sm font-medium text-white">{value}</span>
    </div>
  );
}
