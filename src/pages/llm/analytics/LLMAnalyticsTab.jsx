/**
 * LLM Analytics Tab - Existing LLM metrics
 * Wraps the existing UsageAnalytics component for consistency
 */

import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import UsageAnalytics from '../../UsageAnalytics';
import DateRangeSelector from '../../../components/analytics/DateRangeSelector';
import { useTheme } from '../../../contexts/ThemeContext';

// Register Chart.js scales
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const LLMAnalyticsTab = ({ dateRange, setDateRange }) => {
  const { currentTheme } = useTheme();

  const textClass = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const subtextClass = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className={`text-xl font-semibold ${textClass}`}>LLM Usage Analytics</h3>
          <p className={subtextClass}>
            Track API usage, costs, and performance across all LLM models and providers
          </p>
        </div>
        <DateRangeSelector
          value={dateRange}
          onChange={setDateRange}
          ranges={[
            { label: 'Last 7 Days', value: '7d' },
            { label: 'Last 30 Days', value: '30d' },
            { label: 'Last 90 Days', value: '90d' },
          ]}
        />
      </div>

      {/* Existing UsageAnalytics Component */}
      <UsageAnalytics />
    </div>
  );
};

export default LLMAnalyticsTab;
