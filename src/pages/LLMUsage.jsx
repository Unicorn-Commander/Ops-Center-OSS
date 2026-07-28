/**
 * LLMUsage Page
 *
 * Analytics dashboard for LLM API usage and costs
 *
 * Features:
 * - Usage statistics by provider and power level
 * - Cost breakdown and spending trends
 * - API call volume charts (Chart.js)
 * - Current month spending vs limits
 * - Export usage data (CSV/JSON)
 *
 * API Endpoints:
 * - GET /api/v1/llm/usage/summary - Overview stats
 * - GET /api/v1/llm/usage/by-provider - Provider breakdown
 * - GET /api/v1/llm/usage/by-power-level - Power level breakdown
 * - GET /api/v1/llm/usage/timeseries - Historical data
 * - GET /api/v1/llm/usage/export - Export data
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Line, Bar, Pie } from 'react-chartjs-2';
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
import {
  CurrencyDollarIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowDownTrayIcon,
  ClockIcon,
  SparklesIcon,
  ServerIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import PowerLevelSelector from '../components/PowerLevelSelector';

// Register Chart.js components
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

export default function LLMUsage() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('month');
  const [usageData, setUsageData] = useState(null);
  const [powerLevel, setPowerLevel] = useState('balanced');
  const [providerData, setProviderData] = useState(null);
  const [powerLevelData, setPowerLevelData] = useState(null);

  const getThemeClasses = () => ({
    card: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-white border-gray-200'
      : 'bg-slate-800 border-slate-700',
    text: currentTheme === 'unicorn'
      ? 'text-purple-100'
      : currentTheme === 'light'
      ? 'text-gray-900'
      : 'text-slate-100',
    subtext: currentTheme === 'unicorn'
      ? 'text-purple-300'
      : currentTheme === 'light'
      ? 'text-gray-600'
      : 'text-slate-400',
    button: currentTheme === 'unicorn'
      ? 'bg-purple-600 hover:bg-purple-700 text-white'
      : currentTheme === 'light'
      ? 'bg-blue-600 hover:bg-blue-700 text-white'
      : 'bg-blue-600 hover:bg-blue-700 text-white'
  });

  const themeClasses = getThemeClasses();

  useEffect(() => {
    loadUsageData();
  }, [timeRange]);

  const loadUsageData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Load summary stats
      const summaryResponse = await fetch(`/api/v1/llm/usage/summary?range=${timeRange}`, {
        credentials: 'include'
      });

      if (!summaryResponse.ok) {
        throw new Error(`Failed to load usage summary: ${summaryResponse.status} ${summaryResponse.statusText}`);
      }

      const summaryData = await summaryResponse.json();
      setUsageData(summaryData);

      // Load provider breakdown
      const providerResponse = await fetch('/api/v1/llm/usage/by-provider', {
        credentials: 'include'
      });

      if (!providerResponse.ok) {
        throw new Error(`Failed to load provider data: ${providerResponse.status} ${providerResponse.statusText}`);
      }

      const providerDataResult = await providerResponse.json();
      setProviderData(providerDataResult);

      // Load power level breakdown
      const powerLevelResponse = await fetch('/api/v1/llm/usage/by-power-level', {
        credentials: 'include'
      });

      if (!powerLevelResponse.ok) {
        throw new Error(`Failed to load power level data: ${powerLevelResponse.status} ${powerLevelResponse.statusText}`);
      }

      const powerLevelDataResult = await powerLevelResponse.json();
      setPowerLevelData(powerLevelDataResult);

    } catch (error) {
      console.error('Failed to load usage data:', error);
      setError(error.message || 'Failed to load usage data. Please try again later.');
      setUsageData(null);
      setProviderData(null);
      setPowerLevelData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      window.location.href = `/api/v1/llm/usage/export?format=${format}&range=${timeRange}`;
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  // Chart colors
  const chartColors = {
    primary: currentTheme === 'unicorn' ? '#9333ea' : '#3b82f6',
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    purple: '#a855f7',
    blue: '#3b82f6',
    green: '#10b981'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-purple-500 mx-auto mb-4"></div>
          <p className={themeClasses.text}>Loading usage data...</p>
        </div>
      </div>
    );
  }

  // Show error state if data failed to load
  if (error || !usageData) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${themeClasses.text}`}>
              LLM Usage & Analytics
            </h1>
            <p className={`mt-2 ${themeClasses.subtext}`}>
              Track API usage, costs, and optimize spending
            </p>
          </div>
        </div>

        {/* Error Alert */}
        <div className={`rounded-xl border-2 border-red-500 p-6 ${
          currentTheme === 'unicorn'
            ? 'bg-red-900/30 backdrop-blur-xl'
            : currentTheme === 'light'
            ? 'bg-red-50'
            : 'bg-red-900/20'
        }`}>
          <div className="flex items-start gap-4">
            <ExclamationCircleIcon className="h-8 w-8 text-red-500 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-red-500 mb-2">
                Failed to Load Usage Data
              </h3>
              <p className={`mb-4 ${
                currentTheme === 'light' ? 'text-gray-700' : 'text-slate-300'
              }`}>
                {error || 'Unable to retrieve LLM usage data from the server. Please ensure the backend API is running and accessible.'}
              </p>
              <button
                onClick={loadUsageData}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          </div>
        </div>

        {/* Troubleshooting Information */}
        <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
            Troubleshooting Steps
          </h3>
          <ul className={`space-y-2 ${themeClasses.subtext}`}>
            <li className="flex items-start gap-2">
              <span className="font-bold">1.</span>
              <span>Verify the backend API is running: <code className="bg-slate-700 px-2 py-1 rounded text-sm">docker ps | grep ops-center</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">2.</span>
              <span>Check backend logs: <code className="bg-slate-700 px-2 py-1 rounded text-sm">docker logs ops-center-direct --tail 50</code></span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">3.</span>
              <span>Ensure the LLM usage API endpoints are implemented in the backend</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="font-bold">4.</span>
              <span>Verify database connectivity and that usage data is being tracked</span>
            </li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${themeClasses.text}`}>
            LLM Usage & Analytics
          </h1>
          <p className={`mt-2 ${themeClasses.subtext}`}>
            Track API usage, costs, and optimize spending
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => handleExport('csv')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg ${themeClasses.button}`}
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Export CSV
          </button>
          <button
            onClick={() => handleExport('json')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg border ${
              currentTheme === 'light'
                ? 'border-gray-300 text-gray-700 hover:bg-gray-50'
                : 'border-slate-600 text-slate-300 hover:bg-slate-700'
            }`}
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Export JSON
          </button>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="flex gap-2">
        {['week', 'month', 'quarter', 'year'].map(range => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-lg ${
              timeRange === range
                ? themeClasses.button
                : `border ${
                    currentTheme === 'light'
                      ? 'border-gray-300 text-gray-700'
                      : 'border-slate-600 text-slate-300'
                  }`
            }`}
          >
            {range.charAt(0).toUpperCase() + range.slice(1)}
          </button>
        ))}
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`rounded-xl border p-6 ${themeClasses.card}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${themeClasses.subtext}`}>API Calls</div>
            <ChartBarIcon className="h-5 w-5 text-blue-400" />
          </div>
          <div className={`text-3xl font-bold ${themeClasses.text}`}>
            {(usageData.total_calls / 1000).toFixed(1)}K
          </div>
          <div className={`text-xs mt-1 ${usageData.growth.calls >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {usageData.growth.calls >= 0 ? '+' : ''}{usageData.growth.calls}% from last {timeRange}
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`rounded-xl border p-6 ${themeClasses.card}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${themeClasses.subtext}`}>Total Cost</div>
            <CurrencyDollarIcon className="h-5 w-5 text-green-400" />
          </div>
          <div className={`text-3xl font-bold ${themeClasses.text}`}>
            ${usageData.total_cost.toFixed(2)}
          </div>
          <div className={`text-xs mt-1 ${usageData.growth.cost >= 0 ? 'text-yellow-400' : 'text-green-400'}`}>
            {usageData.growth.cost >= 0 ? '+' : ''}{usageData.growth.cost}% from last {timeRange}
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`rounded-xl border p-6 ${themeClasses.card}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${themeClasses.subtext}`}>Avg Cost/Call</div>
            <SparklesIcon className="h-5 w-5 text-purple-400" />
          </div>
          <div className={`text-3xl font-bold ${themeClasses.text}`}>
            ${usageData.avg_cost_per_call.toFixed(4)}
          </div>
          <div className={`text-xs mt-1 ${usageData.growth.avg_cost <= 0 ? 'text-green-400' : 'text-yellow-400'}`}>
            {usageData.growth.avg_cost >= 0 ? '+' : ''}{usageData.growth.avg_cost}% efficiency
          </div>
        </motion.div>

        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`rounded-xl border p-6 ${themeClasses.card}`}
        >
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${themeClasses.subtext}`}>Quota Used</div>
            <ClockIcon className="h-5 w-5 text-orange-400" />
          </div>
          <div className={`text-3xl font-bold ${themeClasses.text}`}>
            {usageData.quota_used_percent}%
          </div>
          <div className="w-full bg-gray-700 rounded-full h-2 mt-3">
            <div
              className={`h-2 rounded-full ${
                usageData.quota_used_percent > 90 ? 'bg-red-500' :
                usageData.quota_used_percent > 75 ? 'bg-yellow-500' : 'bg-green-500'
              }`}
              style={{ width: `${usageData.quota_used_percent}%` }}
            />
          </div>
        </motion.div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* API Calls Over Time */}
        <div className="lg:col-span-2">
          <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
            <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
              API Calls Over Time
            </h3>
            <div className="h-80">
              <Line
                data={{
                  labels: usageData.timeline.map(d => d.date),
                  datasets: [{
                    label: 'API Calls',
                    data: usageData.timeline.map(d => d.calls),
                    borderColor: chartColors.purple,
                    backgroundColor: `${chartColors.purple}20`,
                    fill: true,
                    tension: 0.4
                  }]
                }}
                options={{
                  responsive: true,
                  maintainAspectRatio: false,
                  plugins: {
                    legend: { display: false },
                    tooltip: {
                      backgroundColor: currentTheme === 'light' ? 'white' : '#1e293b',
                      titleColor: currentTheme === 'light' ? '#1e293b' : 'white',
                      bodyColor: currentTheme === 'light' ? '#1e293b' : 'white',
                      borderColor: '#a855f7',
                      borderWidth: 1
                    }
                  },
                  scales: {
                    y: {
                      beginAtZero: true,
                      ticks: { color: currentTheme === 'light' ? '#6b7280' : '#94a3b8' },
                      grid: { color: currentTheme === 'light' ? '#e5e7eb' : '#334155' }
                    },
                    x: {
                      ticks: { color: currentTheme === 'light' ? '#6b7280' : '#94a3b8' },
                      grid: { color: currentTheme === 'light' ? '#e5e7eb' : '#334155' }
                    }
                  }
                }}
              />
            </div>
          </div>
        </div>

        {/* Power Level Selector */}
        <div>
          <PowerLevelSelector
            value={powerLevel}
            onChange={setPowerLevel}
            showEstimates={true}
          />
        </div>
      </div>

      {/* Provider & Power Level Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Usage by Provider */}
        <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
            Usage by Provider
          </h3>
          <div className="h-64 mb-4">
            <Pie
              data={{
                labels: providerData?.providers.map(p => p.name) || [],
                datasets: [{
                  data: providerData?.providers.map(p => p.percentage) || [],
                  backgroundColor: [
                    chartColors.purple,
                    chartColors.blue,
                    chartColors.green,
                    chartColors.warning
                  ]
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: { color: currentTheme === 'light' ? '#6b7280' : '#94a3b8' }
                  },
                  tooltip: {
                    backgroundColor: currentTheme === 'light' ? 'white' : '#1e293b',
                    titleColor: currentTheme === 'light' ? '#1e293b' : 'white',
                    bodyColor: currentTheme === 'light' ? '#1e293b' : 'white',
                    borderColor: '#a855f7',
                    borderWidth: 1
                  }
                }
              }}
            />
          </div>
          <div className="space-y-2">
            {providerData?.providers.map((provider, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <ServerIcon className="h-4 w-4 text-purple-400" />
                  <span className={themeClasses.text}>{provider.name}</span>
                </div>
                <span className={themeClasses.subtext}>
                  {provider.calls.toLocaleString()} calls (${provider.cost.toFixed(2)})
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Cost by Power Level */}
        <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
          <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
            Cost by Power Level
          </h3>
          <div className="h-64">
            <Bar
              data={{
                labels: powerLevelData?.levels.map(l => l.level.charAt(0).toUpperCase() + l.level.slice(1)) || [],
                datasets: [{
                  label: 'Cost ($)',
                  data: powerLevelData?.levels.map(l => l.cost) || [],
                  backgroundColor: [
                    chartColors.green,
                    chartColors.blue,
                    chartColors.purple
                  ]
                }]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { display: false },
                  tooltip: {
                    backgroundColor: currentTheme === 'light' ? 'white' : '#1e293b',
                    titleColor: currentTheme === 'light' ? '#1e293b' : 'white',
                    bodyColor: currentTheme === 'light' ? '#1e293b' : 'white',
                    borderColor: '#a855f7',
                    borderWidth: 1
                  }
                },
                scales: {
                  y: {
                    beginAtZero: true,
                    ticks: { color: currentTheme === 'light' ? '#6b7280' : '#94a3b8' },
                    grid: { color: currentTheme === 'light' ? '#e5e7eb' : '#334155' }
                  },
                  x: {
                    ticks: { color: currentTheme === 'light' ? '#6b7280' : '#94a3b8' },
                    grid: { color: currentTheme === 'light' ? '#e5e7eb' : '#334155' }
                  }
                }
              }}
            />
          </div>
        </div>
      </div>

      {/* Recent Requests Table */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <h3 className={`text-lg font-semibold ${themeClasses.text} mb-4`}>
          Recent Requests (Last 10)
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className={`border-b ${currentTheme === 'light' ? 'border-gray-200' : 'border-slate-700'}`}>
                <th className={`text-left py-3 px-4 ${themeClasses.subtext} text-sm font-medium`}>Timestamp</th>
                <th className={`text-left py-3 px-4 ${themeClasses.subtext} text-sm font-medium`}>Model</th>
                <th className={`text-left py-3 px-4 ${themeClasses.subtext} text-sm font-medium`}>Power Level</th>
                <th className={`text-left py-3 px-4 ${themeClasses.subtext} text-sm font-medium`}>Cost</th>
                <th className={`text-left py-3 px-4 ${themeClasses.subtext} text-sm font-medium`}>Latency</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan="5" className="py-12 text-center">
                  <div className="flex flex-col items-center justify-center gap-3">
                    <ExclamationCircleIcon className="h-12 w-12 text-slate-400" />
                    <p className={themeClasses.text}>No recent requests available</p>
                    <p className={`text-sm ${themeClasses.subtext}`}>
                      Request history will appear here once the backend API is connected
                    </p>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
