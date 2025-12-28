/**
 * Date Range Selector Component
 * Provides quick selection for common time ranges
 */

import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';

const DateRangeSelector = ({ value, onChange, ranges = null }) => {
  const { currentTheme } = useTheme();

  const defaultRanges = ranges || [
    { label: 'Last 24 Hours', value: '24h' },
    { label: 'Last 7 Days', value: '7d' },
    { label: 'Last 30 Days', value: '30d' },
    { label: 'Last 90 Days', value: '90d' },
    { label: 'Custom', value: 'custom' },
  ];

  const selectClass = currentTheme === 'unicorn'
    ? 'bg-purple-900/20 border-purple-500/20 text-white'
    : currentTheme === 'light'
    ? 'bg-white border-gray-300 text-gray-900'
    : 'bg-gray-800 border-gray-700 text-white';

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className={`px-4 py-2 rounded-lg border ${selectClass} focus:ring-2 focus:ring-purple-500 focus:outline-none`}
    >
      {defaultRanges.map((range) => (
        <option key={range.value} value={range.value}>
          {range.label}
        </option>
      ))}
    </select>
  );
};

export default DateRangeSelector;
