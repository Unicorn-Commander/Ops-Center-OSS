/**
 * Analytics Chart Wrapper Component
 * Provides a consistent wrapper for all chart types with theming
 */

import React from 'react';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import { useTheme } from '../../contexts/ThemeContext';
import { ArrowPathIcon } from '@heroicons/react/24/outline';

const AnalyticsChart = ({
  type = 'line',
  data,
  options = {},
  title,
  height = '300px',
  loading = false,
  error = null
}) => {
  const { theme } = useTheme();

  const chartColors = theme === 'dark' || theme === 'unicorn'
    ? {
        primary: 'rgb(139, 92, 246)',
        secondary: 'rgb(236, 72, 153)',
        success: 'rgb(34, 197, 94)',
        warning: 'rgb(251, 191, 36)',
        danger: 'rgb(239, 68, 68)',
        info: 'rgb(59, 130, 246)',
        grid: 'rgba(255, 255, 255, 0.1)',
        text: 'rgba(255, 255, 255, 0.7)'
      }
    : {
        primary: 'rgb(124, 58, 237)',
        secondary: 'rgb(219, 39, 119)',
        success: 'rgb(22, 163, 74)',
        warning: 'rgb(245, 158, 11)',
        danger: 'rgb(220, 38, 38)',
        info: 'rgb(37, 99, 235)',
        grid: 'rgba(0, 0, 0, 0.1)',
        text: 'rgba(0, 0, 0, 0.7)'
      };

  const defaultOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: chartColors.text
        }
      },
      tooltip: {
        backgroundColor: theme === 'dark' || theme === 'unicorn' ? '#1f2937' : '#ffffff',
        titleColor: chartColors.text,
        bodyColor: chartColors.text,
        borderColor: chartColors.grid,
        borderWidth: 1
      }
    },
    scales: type !== 'pie' && type !== 'doughnut' ? {
      x: {
        grid: {
          color: chartColors.grid
        },
        ticks: {
          color: chartColors.text
        }
      },
      y: {
        grid: {
          color: chartColors.grid
        },
        ticks: {
          color: chartColors.text
        }
      }
    } : undefined,
    ...options
  };

  const ChartComponent = {
    line: Line,
    bar: Bar,
    pie: Pie,
    doughnut: Doughnut
  }[type];

  if (loading) {
    return (
      <div style={{ height }} className="flex items-center justify-center">
        <ArrowPathIcon className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ height }} className="flex items-center justify-center">
        <p className="text-red-400">{error}</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ height }} className="flex items-center justify-center">
        <p className="text-gray-400">No data available</p>
      </div>
    );
  }

  return (
    <div>
      {title && (
        <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
      )}
      <div style={{ height }}>
        <ChartComponent data={data} options={defaultOptions} />
      </div>
    </div>
  );
};

export default AnalyticsChart;
