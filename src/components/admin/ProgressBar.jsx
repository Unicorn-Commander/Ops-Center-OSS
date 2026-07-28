/**
 * ProgressBar - Themed progress bar with gradient colors
 * Supports different color schemes based on usage level
 */

import React from 'react';
import { motion } from 'framer-motion';

export default function ProgressBar({
  value = 0,
  max = 100,
  type = 'default', // default, vram, storage, cpu, memory
  height = 'md',
  showLabel = true,
  label = null,
  animated = true,
  className = ''
}) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));

  // Height variants
  const heightClasses = {
    sm: 'h-2',
    md: 'h-3',
    lg: 'h-4',
  };

  // Get gradient based on type and percentage
  const getGradient = () => {
    if (type === 'vram') {
      if (percent > 90) return 'from-red-500 to-red-600';
      if (percent > 70) return 'from-yellow-500 to-orange-500';
      return 'from-blue-500 to-cyan-500';
    }
    if (type === 'storage') {
      if (percent > 90) return 'from-red-500 to-red-600';
      if (percent > 70) return 'from-yellow-500 to-orange-500';
      return 'from-purple-500 to-indigo-500';
    }
    // Default (cpu, memory, etc.)
    if (percent > 90) return 'from-red-500 to-red-600';
    if (percent > 70) return 'from-yellow-500 to-orange-500';
    return 'from-green-500 to-emerald-500';
  };

  const barHeight = heightClasses[height] || heightClasses.md;
  const gradient = getGradient();

  return (
    <div className={`w-full ${className}`}>
      {showLabel && label && (
        <div className="flex justify-between mb-1">
          <span className="text-sm font-medium text-gray-300">{label}</span>
          <span className="text-sm font-medium text-white">{percent.toFixed(1)}%</span>
        </div>
      )}
      <div className={`w-full bg-gray-700/50 rounded-full ${barHeight} shadow-inner overflow-hidden`}>
        {animated ? (
          <motion.div
            className={`${barHeight} rounded-full bg-gradient-to-r ${gradient} relative`}
            initial={{ width: 0 }}
            animate={{ width: `${percent}%` }}
            transition={{ duration: 1, ease: "easeOut" }}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent" />
          </motion.div>
        ) : (
          <div
            className={`${barHeight} rounded-full bg-gradient-to-r ${gradient} relative`}
            style={{ width: `${percent}%` }}
          >
            <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent" />
          </div>
        )}
      </div>
    </div>
  );
}

// Compact version for inline use
export function CompactProgressBar({
  value = 0,
  max = 100,
  type = 'default',
  className = ''
}) {
  const percent = Math.min(100, Math.max(0, (value / max) * 100));

  const getColor = () => {
    if (percent > 90) return 'bg-red-500';
    if (percent > 70) return 'bg-yellow-500';
    if (type === 'vram') return 'bg-blue-500';
    if (type === 'storage') return 'bg-purple-500';
    return 'bg-green-500';
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className="flex-1 h-2 bg-gray-700/50 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor()} rounded-full transition-all duration-300`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs font-medium text-gray-400 w-12 text-right">
        {percent.toFixed(0)}%
      </span>
    </div>
  );
}
