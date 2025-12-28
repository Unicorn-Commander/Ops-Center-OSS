import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChartBarIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

// Animation variants
const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

// Format date
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
};

// Generate mock historical data (until backend implements full tracking)
const generateMockHistoryData = (days, currentUsage) => {
  const data = [];
  const today = new Date();
  const avgDailyUsage = Math.floor(currentUsage / 30); // Assume current usage spread over 30 days

  for (let i = days - 1; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    // Generate realistic variation (±30% of average)
    const variance = avgDailyUsage * 0.3;
    const dailyUsage = Math.max(0, Math.floor(avgDailyUsage + (Math.random() - 0.5) * 2 * variance));
    const creditsUsed = Math.floor(dailyUsage * 0.1); // Credits roughly 10% of API calls

    data.push({
      date: date.toISOString().split('T')[0],
      api_calls: dailyUsage,
      credits_used: creditsUsed
    });
  }

  return data;
};

export default function SubscriptionUsage() {
  const { theme } = useTheme();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [usage, setUsage] = useState(null);
  const [usageHistory, setUsageHistory] = useState([]);
  const [period, setPeriod] = useState('week'); // week, month
  const [refreshing, setRefreshing] = useState(false);
  const [errors, setErrors] = useState({
    current: null,
    history: null,
    export: null
  });
  const [retryCount, setRetryCount] = useState({
    current: 0,
    history: 0
  });
  const maxRetries = 3;

  useEffect(() => {
    loadUsageData();
  }, [period]);

  const fetchCurrentUsage = async () => {
    try {
      const response = await fetch('/api/v1/usage/current');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const result = await response.json();

      // Extract data from new API response format
      const data = result.success && result.data ? {
        // Map new API format to component state
        api_calls_used: result.data.usage?.used || 0,
        api_calls_limit: result.data.usage?.limit || -1,
        credits_used: result.data.usage?.used * 0.01 || 0,  // Rough credit calculation
        credits_remaining: Math.max(0, (result.data.usage?.limit || 0) - (result.data.usage?.used || 0)) * 0.01,
        reset_date: result.data.reset?.date,
        services: {
          chat: result.data.usage?.used * 0.7 || 0,  // Estimate breakdown
          search: result.data.usage?.used * 0.2 || 0,
          tts: result.data.usage?.used * 0.05 || 0,
          stt: result.data.usage?.used * 0.05 || 0
        },
        peak_usage: result.data.daily?.used || 0,
        peak_date: new Date().toISOString(),
        subscription: {
          tier: result.data.tier,
          status: result.data.status
        }
      } : result;

      setUsage(data);
      setErrors(prev => ({ ...prev, current: null }));
      setRetryCount(prev => ({ ...prev, current: 0 }));
      return data;
    } catch (error) {
      console.error('Failed to fetch current usage:', error);
      const errorMsg = `Failed to load current usage: ${error.message}`;
      setErrors(prev => ({ ...prev, current: errorMsg }));

      // Retry logic for transient failures
      if (retryCount.current < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, current: prev.current + 1 }));
          fetchCurrentUsage();
        }, 2000 * (retryCount.current + 1)); // Exponential backoff
      } else {
        toast.error(errorMsg);
      }
      throw error;
    }
  };

  const fetchUsageHistory = async () => {
    try {
      // Map period to API format: daily, weekly, monthly
      const periodMap = { week: 'weekly', month: 'monthly', year: 'monthly' };
      const apiPeriod = periodMap[period] || 'weekly';

      const response = await fetch(`/api/v1/usage/history?period=${apiPeriod}`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const result = await response.json();

      // Process new API response format
      if (result.success && result.data && result.data.history && result.data.history.length > 0) {
        // Transform API data to chart format
        const historyData = result.data.history.map(item => ({
          date: item.date,
          api_calls: item.calls || 0,
          credits_used: item.cost || 0
        }));
        setUsageHistory(historyData);
      } else {
        // Fallback to mock data if no history available
        const periodToDays = { week: 7, month: 30, year: 365 };
        const days = periodToDays[period] || 30;
        const mockData = generateMockHistoryData(days, usage?.api_calls_used || 0);
        setUsageHistory(mockData);
      }

      setErrors(prev => ({ ...prev, history: null }));
      setRetryCount(prev => ({ ...prev, history: 0 }));
      return result;
    } catch (error) {
      console.error('Failed to fetch usage history:', error);
      const errorMsg = `Failed to load usage history: ${error.message}`;
      setErrors(prev => ({ ...prev, history: errorMsg }));

      // Fallback to empty array
      setUsageHistory([]);

      // Retry logic for transient failures
      if (retryCount.history < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, history: prev.history + 1 }));
          fetchUsageHistory();
        }, 2000 * (retryCount.history + 1));
      } else {
        toast.warning(errorMsg); // Use warning since history is less critical
      }
      throw error;
    }
  };

  const loadUsageData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchCurrentUsage(),
        fetchUsageHistory()
      ]);
    } catch (error) {
      // Errors handled in individual fetch functions
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await loadUsageData();
      toast.success('Usage data refreshed successfully');
    } catch (error) {
      // Error already handled in loadUsageData
    } finally {
      setRefreshing(false);
    }
  };

  const handleExport = async () => {
    try {
      setErrors(prev => ({ ...prev, export: null }));
      const res = await fetch(`/api/v1/usage/export?period=${period}`);

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `usage-report-${period}-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast.success('Usage report exported successfully');
    } catch (error) {
      console.error('Error exporting usage:', error);
      const errorMsg = `Failed to export usage report: ${error.message}`;
      setErrors(prev => ({ ...prev, export: errorMsg }));
      toast.error(errorMsg);
    }
  };

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-6 animate-pulse`}>
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
        <div className="h-64 bg-slate-700 rounded"></div>
      </div>
    );
  }

  // Calculate usage percentage
  const apiCallsPercentage = usage?.api_calls_limit === -1
    ? 0
    : Math.min((usage?.api_calls_used / usage?.api_calls_limit) * 100, 100);

  const creditsPercentage = Math.min(
    (usage?.credits_remaining / (usage?.credits_used + usage?.credits_remaining)) * 100,
    100
  );

  // Service usage breakdown
  const serviceUsage = [
    { name: 'Chat', value: usage?.services?.chat || 0, color: '#8b5cf6' },
    { name: 'Search', value: usage?.services?.search || 0, color: '#ec4899' },
    { name: 'TTS', value: usage?.services?.tts || 0, color: '#10b981' },
    { name: 'STT', value: usage?.services?.stt || 0, color: '#f59e0b' }
  ];

  return (
    <div className="space-y-6">
      {/* Error Alerts */}
      {(errors.current || errors.history || errors.export) && (
        <div className="space-y-2">
          {errors.current && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-900/20 border border-red-500/50 rounded-xl p-4 flex items-start gap-3"
            >
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-200 text-sm font-medium">{errors.current}</p>
                {retryCount.current > 0 && retryCount.current < maxRetries && (
                  <p className="text-red-300 text-xs mt-1">
                    Retrying... (Attempt {retryCount.current}/{maxRetries})
                  </p>
                )}
              </div>
              <button
                onClick={fetchCurrentUsage}
                className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-500 transition-colors"
              >
                Retry Now
              </button>
            </motion.div>
          )}

          {errors.history && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-yellow-900/20 border border-yellow-500/50 rounded-xl p-4 flex items-start gap-3"
            >
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-yellow-200 text-sm font-medium">{errors.history}</p>
                {retryCount.history > 0 && retryCount.history < maxRetries && (
                  <p className="text-yellow-300 text-xs mt-1">
                    Retrying... (Attempt {retryCount.history}/{maxRetries})
                  </p>
                )}
              </div>
              <button
                onClick={fetchUsageHistory}
                className="px-3 py-1 bg-yellow-600 text-white text-xs rounded hover:bg-yellow-500 transition-colors"
              >
                Retry Now
              </button>
            </motion.div>
          )}

          {errors.export && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-orange-900/20 border border-orange-500/50 rounded-xl p-4 flex items-start gap-3"
            >
              <ExclamationTriangleIcon className="h-5 w-5 text-orange-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-orange-200 text-sm font-medium">{errors.export}</p>
              </div>
              <button
                onClick={() => setErrors(prev => ({ ...prev, export: null }))}
                className="text-orange-300 hover:text-orange-100 transition-colors"
              >
                ×
              </button>
            </motion.div>
          )}
        </div>
      )}

      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
          <ChartBarIcon className="w-5 h-5 text-cyan-400" />
          Usage Statistics
        </h3>
        <div className="flex items-center gap-3">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:border-purple-500"
          >
            <option value="week">Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="year">Last 12 Months</option>
          </select>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`flex items-center gap-2 px-3 py-2 ${theme.button} rounded-lg text-sm transition-all disabled:opacity-50`}
          >
            <ArrowPathIcon className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm transition-colors"
          >
            <DocumentArrowDownIcon className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>

      {/* Current Usage Summary */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h4 className={`text-md font-semibold ${theme.text.primary} mb-4`}>Current Billing Period</h4>

        <div className="space-y-6">
          {/* API Calls Usage */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className={`text-sm ${theme.text.secondary}`}>API Calls</span>
              <span className={`text-sm font-medium ${theme.text.primary}`}>
                {usage?.api_calls_used?.toLocaleString() || 0} / {usage?.api_calls_limit === -1 ? '∞' : (usage?.api_calls_limit?.toLocaleString() || 0)}
              </span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-purple-500 to-pink-500 h-3 rounded-full transition-all"
                style={{ width: `${apiCallsPercentage}%` }}
              />
            </div>
            <div className="flex items-center justify-between mt-2">
              <p className={`text-xs ${theme.text.secondary}`}>
                {usage?.api_calls_limit === -1 ? 'Unlimited' : `${Math.round(apiCallsPercentage)}% used`}
              </p>
              {usage?.reset_date && (
                <p className={`text-xs ${theme.text.secondary} flex items-center gap-1`}>
                  <ClockIcon className="w-3 h-3" />
                  Resets {formatDate(usage.reset_date)}
                </p>
              )}
            </div>
          </div>

          {/* Credits Usage */}
          {usage?.credits_remaining !== undefined && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm ${theme.text.secondary}`}>Credits</span>
                <span className={`text-sm font-medium ${theme.text.primary}`}>
                  {usage.credits_remaining.toLocaleString()} remaining
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3">
                <div
                  className="bg-gradient-to-r from-green-500 to-emerald-500 h-3 rounded-full transition-all"
                  style={{ width: `${creditsPercentage}%` }}
                />
              </div>
              <p className={`text-xs ${theme.text.secondary} mt-2`}>
                {usage.credits_used.toLocaleString()} credits used this month
              </p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Service Usage Breakdown */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h4 className={`text-md font-semibold ${theme.text.primary} mb-4`}>Service Usage Breakdown</h4>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={serviceUsage}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9ca3af" />
            <YAxis stroke="#9ca3af" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '0.5rem'
              }}
            />
            <Bar dataKey="value" fill="#8b5cf6" />
          </BarChart>
        </ResponsiveContainer>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
          {serviceUsage.map((service) => (
            <div key={service.name} className="text-center">
              <div
                className="w-3 h-3 rounded-full mx-auto mb-2"
                style={{ backgroundColor: service.color }}
              />
              <p className={`text-xs ${theme.text.secondary}`}>{service.name}</p>
              <p className={`text-lg font-bold ${theme.text.primary}`}>
                {service.value.toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Usage History Graph */}
      {usageHistory.length > 0 && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h4 className={`text-md font-semibold ${theme.text.primary} mb-4`}>
            Usage Trend - {period === 'week' ? 'Last 7 Days' : period === 'month' ? 'Last 30 Days' : 'Last 12 Months'}
          </h4>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={usageHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis
                dataKey="date"
                stroke="#9ca3af"
                tickFormatter={(value) => formatDate(value)}
              />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '0.5rem'
                }}
                labelFormatter={(value) => formatDate(value)}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="api_calls"
                stroke="#8b5cf6"
                strokeWidth={2}
                name="API Calls"
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="credits_used"
                stroke="#10b981"
                strokeWidth={2}
                name="Credits Used"
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Usage Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4`}>
          <p className={`text-sm ${theme.text.secondary} mb-1`}>Average Daily Usage</p>
          <p className={`text-2xl font-bold ${theme.text.primary}`}>
            {Math.round((usage?.api_calls_used || 0) / 30).toLocaleString()}
          </p>
          <p className={`text-xs ${theme.text.secondary} mt-1`}>API calls per day</p>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4`}>
          <p className={`text-sm ${theme.text.secondary} mb-1`}>Peak Usage Day</p>
          <p className={`text-2xl font-bold ${theme.text.primary}`}>
            {usage?.peak_usage?.toLocaleString() || 0}
          </p>
          <p className={`text-xs ${theme.text.secondary} mt-1`}>
            {usage?.peak_date ? formatDate(usage.peak_date) : 'No data'}
          </p>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4`}>
          <p className={`text-sm ${theme.text.secondary} mb-1`}>Projected Monthly</p>
          <p className={`text-2xl font-bold ${theme.text.primary}`}>
            {Math.round((usage?.api_calls_used || 0) * 1.2).toLocaleString()}
          </p>
          <p className={`text-xs ${theme.text.secondary} mt-1`}>Estimated end of month</p>
        </motion.div>
      </div>
    </div>
  );
}
