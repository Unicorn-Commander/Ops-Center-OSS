/**
 * StatusIndicator - Reusable status dot/pill component
 * Shows health status with color coding and optional animation
 */

import React from 'react';

const STATUS_COLORS = {
  healthy: 'bg-green-500',
  running: 'bg-green-500',
  active: 'bg-green-500',
  degraded: 'bg-yellow-500',
  warning: 'bg-yellow-500',
  starting: 'bg-yellow-500',
  error: 'bg-red-500',
  stopped: 'bg-red-500',
  critical: 'bg-red-500',
  unknown: 'bg-gray-500',
  loading: 'bg-blue-500',
};

// Background colors for pills (with transparency)
const STATUS_BG_COLORS = {
  healthy: 'bg-green-500/20',
  running: 'bg-green-500/20',
  active: 'bg-green-500/20',
  degraded: 'bg-yellow-500/20',
  warning: 'bg-yellow-500/20',
  starting: 'bg-yellow-500/20',
  error: 'bg-red-500/20',
  stopped: 'bg-red-500/20',
  critical: 'bg-red-500/20',
  unknown: 'bg-gray-500/20',
  loading: 'bg-blue-500/20',
};

const STATUS_LABELS = {
  healthy: 'Healthy',
  running: 'Running',
  active: 'Active',
  degraded: 'Degraded',
  warning: 'Warning',
  starting: 'Starting',
  error: 'Error',
  stopped: 'Stopped',
  critical: 'Critical',
  unknown: 'Unknown',
  loading: 'Loading',
};

export default function StatusIndicator({
  status = 'unknown',
  size = 'md',
  showLabel = false,
  animate = false,
  className = ''
}) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.unknown;
  const label = STATUS_LABELS[status] || 'Unknown';

  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const dotSize = sizeClasses[size] || sizeClasses.md;
  const pulseClass = animate && (status === 'healthy' || status === 'running' || status === 'active')
    ? 'animate-pulse'
    : '';

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div
        className={`${dotSize} ${color} rounded-full ${pulseClass} shadow-lg`}
        title={label}
      />
      {showLabel && (
        <span className={`text-sm font-medium ${
          status === 'healthy' || status === 'running' ? 'text-green-400' :
          status === 'degraded' || status === 'warning' ? 'text-yellow-400' :
          status === 'error' || status === 'critical' ? 'text-red-400' :
          'text-gray-400'
        }`}>
          {label}
        </span>
      )}
    </div>
  );
}

// Pill variant with background
export function StatusPill({
  status = 'unknown',
  label = null,
  size = 'md',
  className = ''
}) {
  const color = STATUS_COLORS[status] || STATUS_COLORS.unknown;
  const displayLabel = label || STATUS_LABELS[status] || 'Unknown';

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1 text-sm',
    lg: 'px-4 py-1.5 text-base',
  };

  const pillSize = sizeClasses[size] || sizeClasses.md;
  const bgColor = STATUS_BG_COLORS[status] || STATUS_BG_COLORS.unknown;

  return (
    <span className={`inline-flex items-center gap-1.5 ${pillSize} rounded-full font-medium ${bgColor} ${className}`}
    >
      <span className={`w-2 h-2 ${color} rounded-full`} />
      <span className={`${
        status === 'healthy' || status === 'running' ? 'text-green-400' :
        status === 'degraded' || status === 'warning' ? 'text-yellow-400' :
        status === 'error' || status === 'critical' ? 'text-red-400' :
        'text-gray-400'
      }`}>
        {displayLabel}
      </span>
    </span>
  );
}
