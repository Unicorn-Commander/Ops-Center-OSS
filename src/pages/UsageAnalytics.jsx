import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChartBarIcon,
  CurrencyDollarIcon,
  ClockIcon,
  UsersIcon,
  ServerIcon,
  LightBulbIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ArrowPathIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
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
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';

// Register ChartJS components
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

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

// Format number with commas
const formatNumber = (num) => {
  return new Intl.NumberFormat('en-US').format(num);
};

// Priority badge component
const PriorityBadge = ({ priority }) => {
  const colors = {
    high: 'bg-red-500/20 text-red-400 border-red-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-green-500/20 text-green-400 border-green-500/30'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${colors[priority] || colors.medium}`}>
      {priority.toUpperCase()}
    </span>
  );
};

// Service icon component
const ServiceIcon = ({ service }) => {
  const icons = {
    llm: '🤖',
    embeddings: '🔤',
    search: '🔍',
    tts: '🗣️',
    stt: '👂',
    admin: '⚙️'
  };

  return <span className="text-2xl">{icons[service] || '📊'}</span>;
};

const UsageAnalytics = () => {
  const { theme } = useTheme();

  // State
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState(7); // days
  const [serviceFilter, setServiceFilter] = useState('all');

  // Data state
  const [overview, setOverview] = useState(null);
  const [patterns, setPatterns] = useState(null);
  const [byUser, setByUser] = useState([]);
  const [byService, setByService] = useState([]);
  const [costs, setCosts] = useState(null);
  const [optimization, setOptimization] = useState(null);
  const [performance, setPerformance] = useState(null);
  const [quotas, setQuotas] = useState(null);

  // Auto-refresh
  useEffect(() => {
    fetchAllData();

    // Refresh every 60 seconds
    const interval = setInterval(() => {
      fetchAllData(true);
    }, 60000);

    return () => clearInterval(interval);
  }, [timeRange, serviceFilter]);

  // Fetch all analytics data
  const fetchAllData = async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const baseUrl = '/api/v1/analytics/usage';
      const params = new URLSearchParams({ days: timeRange });

      // Fetch all endpoints in parallel
      const [
        overviewRes,
        patternsRes,
        byUserRes,
        byServiceRes,
        costsRes,
        optimizationRes,
        performanceRes,
        quotasRes
      ] = await Promise.all([
        fetch(`${baseUrl}/overview?${params}`),
        fetch(`${baseUrl}/patterns?${params}`),
        fetch(`${baseUrl}/by-user?${params}`),
        fetch(`${baseUrl}/by-service?${params}`),
        fetch(`${baseUrl}/costs?${params}`),
        fetch(`${baseUrl}/optimization?${params}`),
        fetch(`${baseUrl}/performance?${params}`),
        fetch(`${baseUrl}/quotas?${params}`)
      ]);

      // Parse responses
      const overviewData = await overviewRes.json();
      const patternsData = await patternsRes.json();
      const byUserData = await byUserRes.json();
      const byServiceData = await byServiceRes.json();
      const costsData = await costsRes.json();
      const optimizationData = await optimizationRes.json();
      const performanceData = await performanceRes.json();
      const quotasData = await quotasRes.json();

      // Update state
      setOverview(overviewData);
      setPatterns(patternsData);
      setByUser(byUserData);
      setByService(byServiceData);
      setCosts(costsData);
      setOptimization(optimizationData);
      setPerformance(performanceData);
      setQuotas(quotasData);
    } catch (error) {
      console.error('Error fetching analytics data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Export recommendations to CSV
  const exportRecommendations = () => {
    if (!optimization || !optimization.recommendations) return;

    const csv = [
      ['Priority', 'Type', 'Current', 'Recommended', 'Potential Savings', 'Impact', 'Effort'].join(','),
      ...optimization.recommendations.map(rec =>
        [
          rec.priority,
          rec.type,
          `"${rec.current}"`,
          `"${rec.recommended}"`,
          rec.potential_savings,
          `"${rec.impact}"`,
          rec.implementation_effort
        ].join(',')
      )
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cost_optimization_recommendations_${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Chart colors for dark/light theme
  const chartColors = theme === 'dark'
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

  // Service usage bar chart data
  const serviceChartData = byService ? {
    labels: byService.map(s => s.service_name),
    datasets: [
      {
        label: 'API Calls',
        data: byService.map(s => s.total_calls),
        backgroundColor: chartColors.primary,
        borderRadius: 8
      }
    ]
  } : null;

  // Peak hours heatmap data (simplified as bar chart)
  const peakHoursData = patterns?.peak_hours ? {
    labels: patterns.peak_hours.map(h => `${h.hour}:00`),
    datasets: [
      {
        label: 'API Calls',
        data: patterns.peak_hours.map(h => h.calls),
        backgroundColor: chartColors.secondary,
        borderRadius: 8
      }
    ]
  } : null;

  // Cost trends area chart data
  const costTrendsData = costs?.cost_trends ? {
    labels: costs.cost_trends.map(t => t.date),
    datasets: [
      {
        label: 'Daily Cost',
        data: costs.cost_trends.map(t => t.cost),
        borderColor: chartColors.warning,
        backgroundColor: theme === 'dark' ? 'rgba(251, 191, 36, 0.1)' : 'rgba(245, 158, 11, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  } : null;

  // Service cost distribution pie chart
  const costDistributionData = costs?.cost_breakdown ? {
    labels: Object.keys(costs.cost_breakdown),
    datasets: [
      {
        data: Object.values(costs.cost_breakdown),
        backgroundColor: [
          chartColors.primary,
          chartColors.secondary,
          chartColors.success,
          chartColors.warning,
          chartColors.danger,
          chartColors.info
        ],
        borderWidth: 2,
        borderColor: theme === 'dark' ? '#1f2937' : '#ffffff'
      }
    ]
  } : null;

  // Performance metrics line chart
  const performanceChartData = performance ? {
    labels: ['Avg', 'P50', 'P95', 'P99'],
    datasets: [
      {
        label: 'Latency (ms)',
        data: [
          performance.avg_latency_ms,
          performance.p50_latency_ms,
          performance.p95_latency_ms,
          performance.p99_latency_ms
        ],
        borderColor: chartColors.info,
        backgroundColor: theme === 'dark' ? 'rgba(59, 130, 246, 0.1)' : 'rgba(37, 99, 235, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  } : null;

  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: chartColors.text
        }
      },
      tooltip: {
        backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
        titleColor: chartColors.text,
        bodyColor: chartColors.text,
        borderColor: chartColors.grid,
        borderWidth: 1
      }
    },
    scales: {
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
    }
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          color: chartColors.text,
          padding: 15
        }
      },
      tooltip: {
        backgroundColor: theme === 'dark' ? '#1f2937' : '#ffffff',
        titleColor: chartColors.text,
        bodyColor: chartColors.text,
        borderColor: chartColors.grid,
        borderWidth: 1
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <ArrowPathIcon className="w-12 h-12 mx-auto mb-4 animate-spin text-purple-500" />
          <p className="text-gray-400">Loading usage analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="p-6 space-y-6"
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Usage Analytics</h1>
          <p className="text-gray-400">
            API usage patterns, cost optimization, and performance insights
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Time range selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(parseInt(e.target.value))}
            className="px-4 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white focus:ring-2 focus:ring-purple-500"
          >
            <option value={7}>Last 7 days</option>
            <option value={30}>Last 30 days</option>
            <option value={90}>Last 90 days</option>
          </select>

          {/* Refresh button */}
          <button
            onClick={() => fetchAllData(true)}
            disabled={refreshing}
            className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-700 text-white flex items-center gap-2 disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      {overview && (
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Total API Calls */}
          <div className="glassmorphism rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <ChartBarIcon className="w-8 h-8 text-purple-400" />
              <span className="text-sm text-gray-400">Total</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">
              {formatNumber(overview.total_api_calls)}
            </h3>
            <p className="text-gray-400 text-sm">API Calls</p>
          </div>

          {/* Total Cost */}
          <div className="glassmorphism rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <CurrencyDollarIcon className="w-8 h-8 text-green-400" />
              <span className="text-sm text-gray-400">Period</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">
              {formatCurrency(overview.total_cost)}
            </h3>
            <p className="text-gray-400 text-sm">Total Cost</p>
          </div>

          {/* Cost per Call */}
          <div className="glassmorphism rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <ServerIcon className="w-8 h-8 text-blue-400" />
              <span className="text-sm text-gray-400">Average</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">
              ${overview.cost_per_call.toFixed(6)}
            </h3>
            <p className="text-gray-400 text-sm">Per Call</p>
          </div>

          {/* Active Users */}
          <div className="glassmorphism rounded-xl p-6">
            <div className="flex items-center justify-between mb-4">
              <UsersIcon className="w-8 h-8 text-pink-400" />
              <span className="text-sm text-gray-400">Active</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">
              {formatNumber(overview.by_user_count)}
            </h3>
            <p className="text-gray-400 text-sm">Users</p>
          </div>
        </motion.div>
      )}

      {/* Service Usage and Peak Hours */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Usage Bar Chart */}
        {serviceChartData && (
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">API Calls by Service</h2>
            <div style={{ height: '300px' }}>
              <Bar data={serviceChartData} options={chartOptions} />
            </div>
          </motion.div>
        )}

        {/* Peak Hours */}
        {peakHoursData && (
          <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
            <h2 className="text-xl font-semibold text-white mb-4">Peak Usage Hours</h2>
            <div style={{ height: '300px' }}>
              <Bar data={peakHoursData} options={chartOptions} />
            </div>
          </motion.div>
        )}
      </div>

      {/* Cost Analysis */}
      {costs && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Cost Trends */}
          {costTrendsData && (
            <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Cost Trends</h2>
              <div style={{ height: '300px' }}>
                <Line data={costTrendsData} options={chartOptions} />
              </div>
              <div className="mt-4 grid grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-400 text-sm">Projected Monthly</p>
                  <p className="text-xl font-bold text-white">
                    {formatCurrency(costs.projected_monthly_cost)}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-sm">Cost per User</p>
                  <p className="text-xl font-bold text-white">
                    {formatCurrency(costs.cost_per_user)}
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Cost Distribution */}
          {costDistributionData && (
            <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
              <h2 className="text-xl font-semibold text-white mb-4">Cost Distribution</h2>
              <div style={{ height: '300px' }}>
                <Doughnut data={costDistributionData} options={pieOptions} />
              </div>
            </motion.div>
          )}
        </div>
      )}

      {/* Performance Metrics */}
      {performance && (
        <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Performance Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-6 mb-6">
            <div>
              <p className="text-gray-400 text-sm mb-1">Avg Latency</p>
              <p className="text-2xl font-bold text-white">{performance.avg_latency_ms.toFixed(0)}ms</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">P95 Latency</p>
              <p className="text-2xl font-bold text-white">{performance.p95_latency_ms.toFixed(0)}ms</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">P99 Latency</p>
              <p className="text-2xl font-bold text-white">{performance.p99_latency_ms.toFixed(0)}ms</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Success Rate</p>
              <p className="text-2xl font-bold text-green-400">{performance.success_rate.toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-gray-400 text-sm mb-1">Error Rate</p>
              <p className="text-2xl font-bold text-red-400">{performance.error_rate.toFixed(1)}%</p>
            </div>
          </div>
          {performanceChartData && (
            <div style={{ height: '200px' }}>
              <Line data={performanceChartData} options={chartOptions} />
            </div>
          )}
        </motion.div>
      )}

      {/* Cost Optimization Recommendations */}
      {optimization && (
        <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <LightBulbIcon className="w-6 h-6 text-yellow-400" />
              <h2 className="text-xl font-semibold text-white">Cost Optimization Recommendations</h2>
            </div>
            <button
              onClick={exportRecommendations}
              className="px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 text-white flex items-center gap-2"
            >
              <ArrowDownTrayIcon className="w-5 h-5" />
              Export CSV
            </button>
          </div>

          <div className="mb-6 flex items-center gap-6">
            <div>
              <p className="text-gray-400 text-sm">Total Potential Savings</p>
              <p className="text-3xl font-bold text-green-400">
                {formatCurrency(optimization.total_potential_savings)}/month
              </p>
            </div>
            <div>
              <p className="text-gray-400 text-sm">Implementation Time</p>
              <p className="text-xl font-semibold text-white">{optimization.estimated_implementation_time}</p>
            </div>
          </div>

          <div className="space-y-4">
            {optimization.recommendations.map((rec, index) => (
              <div
                key={index}
                className="bg-gray-800/50 rounded-lg p-4 border border-gray-700 hover:border-purple-500/50 transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <PriorityBadge priority={rec.priority} />
                    <span className="text-sm font-medium text-gray-400">
                      {rec.type.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <span className="text-lg font-bold text-green-400">
                    {rec.potential_savings}
                  </span>
                </div>

                <div className="space-y-2">
                  <div>
                    <span className="text-sm text-gray-500">Current:</span>
                    <span className="ml-2 text-white">{rec.current}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Recommended:</span>
                    <span className="ml-2 text-white">{rec.recommended}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Impact:</span>
                    <span className="ml-2 text-gray-300">{rec.impact}</span>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-gray-500">
                      Effort: <span className="text-white font-medium">{rec.implementation_effort}</span>
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Quota Usage by Plan Tier */}
      {quotas && (
        <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Quota Usage by Plan Tier</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {Object.entries(quotas).map(([tier, data]) => (
              <div key={tier} className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
                <h3 className="text-lg font-semibold text-white capitalize mb-3">{tier}</h3>
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between text-sm mb-1">
                      <span className="text-gray-400">API Calls</span>
                      <span className="text-white font-medium">{data.percentage.toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all ${
                          data.percentage > 80 ? 'bg-red-500' :
                          data.percentage > 60 ? 'bg-yellow-500' :
                          'bg-green-500'
                        }`}
                        style={{ width: `${Math.min(data.percentage, 100)}%` }}
                      />
                    </div>
                  </div>
                  <div className="text-sm">
                    <span className="text-white font-medium">{formatNumber(data.used)}</span>
                    <span className="text-gray-400"> / </span>
                    <span className="text-gray-400">
                      {data.limit === 'unlimited' ? 'unlimited' : formatNumber(data.limit)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Top Users Table */}
      {byUser.length > 0 && (
        <motion.div variants={itemVariants} className="glassmorphism rounded-xl p-6">
          <h2 className="text-xl font-semibold text-white mb-4">Top Users by Usage</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">User</th>
                  <th className="text-left py-3 px-4 text-gray-400 font-medium">Tier</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">API Calls</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Cost</th>
                  <th className="text-right py-3 px-4 text-gray-400 font-medium">Quota Used</th>
                </tr>
              </thead>
              <tbody>
                {byUser.slice(0, 10).map((user, index) => (
                  <tr key={user.user_id} className="border-b border-gray-800 hover:bg-gray-800/30">
                    <td className="py-3 px-4">
                      <div>
                        <p className="text-white font-medium">{user.username}</p>
                        <p className="text-gray-400 text-sm">{user.user_id}</p>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        user.subscription_tier === 'enterprise' ? 'bg-amber-500/20 text-amber-400' :
                        user.subscription_tier === 'professional' ? 'bg-purple-500/20 text-purple-400' :
                        user.subscription_tier === 'starter' ? 'bg-green-500/20 text-green-400' :
                        'bg-blue-500/20 text-blue-400'
                      }`}>
                        {user.subscription_tier}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-white font-medium">
                      {formatNumber(user.total_calls)}
                    </td>
                    <td className="py-3 px-4 text-right text-white font-medium">
                      {formatCurrency(user.total_cost)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className={`font-medium ${
                        user.quota_used_percent > 90 ? 'text-red-400' :
                        user.quota_used_percent > 75 ? 'text-yellow-400' :
                        'text-green-400'
                      }`}>
                        {user.quota_used_percent.toFixed(1)}%
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default UsageAnalytics;
