import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useTheme } from '../contexts/ThemeContext';
import { 
  ChartBarIcon,
  ChartPieIcon, 
  CpuChipIcon,
  CircleStackIcon,
  ServerIcon,
  ClockIcon,
  FireIcon,
  ArrowPathIcon,
  CalendarIcon,
  DocumentChartBarIcon,
  ArrowDownTrayIcon,
  Cog6ToothIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BoltIcon
} from '@heroicons/react/24/outline';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  BarChart, 
  Bar, 
  PieChart, 
  Pie, 
  Cell, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  ComposedChart,
  Scatter,
  ScatterChart,
  RadialBarChart,
  RadialBar
} from 'recharts';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.3
    }
  }
};

export default function Analytics() {
  const { systemData, services } = useSystem();
  const { theme, currentTheme } = useTheme();
  const [timeRange, setTimeRange] = useState('1h'); // 1h, 6h, 24h, 7d, 30d
  const [selectedMetric, setSelectedMetric] = useState('overview'); // overview, cpu, memory, gpu, disk, network
  const [historicalData, setHistoricalData] = useState({
    cpu: [],
    memory: [],
    gpu: [],
    disk: [],
    network: [],
    services: []
  });
  const [systemMetrics, setSystemMetrics] = useState({
    uptime: 0,
    load_average: [0, 0, 0],
    process_count: 0,
    thread_count: 0,
    service_health_score: 0
  });
  const [alertSummary, setAlertSummary] = useState({
    critical: 0,
    warning: 0,
    info: 0,
    total_events: 0
  });
  const [performanceInsights, setPerformanceInsights] = useState([]);
  const [refreshInterval, setRefreshInterval] = useState(5000); // 5 seconds
  const [autoRefresh, setAutoRefresh] = useState(true);
  const dataRef = useRef(historicalData);
  const maxDataPoints = timeRange === '1h' ? 60 : timeRange === '6h' ? 360 : timeRange === '24h' ? 1440 : 720;

  useEffect(() => {
    fetchAnalyticsData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAnalyticsData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [timeRange, refreshInterval, autoRefresh]);

  const fetchAnalyticsData = async () => {
    try {
      // Fetch usage metrics (replaces /analytics/metrics)
      const metricsResponse = await fetch('/api/v1/analytics/usage/overview?days=30');
      if (metricsResponse.ok) {
        const metrics = await metricsResponse.json();
        setSystemMetrics({
          uptime: systemData?.uptime || 0,
          load_average: systemData?.load_average || [0, 0, 0],
          process_count: systemData?.process_count || 0,
          thread_count: systemData?.thread_count || 0,
          service_health_score: calculateServiceHealthScore(),
          total_api_calls: metrics.total_api_calls || 0,
          total_cost: metrics.total_cost || 0
        });
      }

      // Fetch user analytics for alerts (active users, churn, etc)
      const alertsResponse = await fetch('/api/v1/analytics/users/overview');
      if (alertsResponse.ok) {
        const alerts = await alertsResponse.json();
        setAlertSummary({
          critical: alerts.churned_users_30d > 10 ? alerts.churned_users_30d : 0,
          warning: alerts.growth_rate < 0 ? 1 : 0,
          info: alerts.new_users_30d || 0,
          total_events: alerts.total_users || 0
        });
      }

      // Fetch performance insights from usage analytics
      const insightsResponse = await fetch('/api/v1/analytics/usage/performance?days=7');
      if (insightsResponse.ok) {
        const insights = await insightsResponse.json();
        const generatedInsights = [];

        // Generate insights from performance data
        if (insights.error_rate > 5) {
          generatedInsights.push({
            level: 'critical',
            title: 'High Error Rate Detected',
            description: `Current error rate is ${insights.error_rate.toFixed(2)}%, exceeding the 5% threshold.`,
            recommendation: 'Review recent code changes and check service logs for recurring errors.'
          });
        }

        if (insights.p95_latency_ms > 1000) {
          generatedInsights.push({
            level: 'warning',
            title: 'High Latency Detected',
            description: `95th percentile latency is ${insights.p95_latency_ms.toFixed(0)}ms, which may impact user experience.`,
            recommendation: 'Review slow endpoints and consider caching or query optimization.'
          });
        }

        if (insights.success_rate >= 99) {
          generatedInsights.push({
            level: 'info',
            title: 'Excellent Service Reliability',
            description: `Success rate is ${insights.success_rate.toFixed(2)}% with low error rates.`,
            recommendation: 'Continue monitoring and maintain current best practices.'
          });
        }

        setPerformanceInsights(generatedInsights);
      }

      // Update historical data
      updateHistoricalData();
    } catch (error) {
      console.error('Failed to fetch analytics data:', error);
    }
  };

  const updateHistoricalData = () => {
    if (!systemData) return;

    const timestamp = new Date().toLocaleTimeString();
    
    // Update historical metrics
    const newData = {
      cpu: [...dataRef.current.cpu, {
        time: timestamp,
        usage: systemData.cpu?.percent || 0,
        temp: systemData.cpu?.temp || 0,
        load: systemData.load_average?.[0] || 0
      }].slice(-maxDataPoints),
      
      memory: [...dataRef.current.memory, {
        time: timestamp,
        used_percent: systemData.memory?.percent || 0,
        used_gb: ((systemData.memory?.used || 0) / (1024**3)).toFixed(2),
        available_gb: ((systemData.memory?.available || 0) / (1024**3)).toFixed(2),
        cached_gb: (((systemData.memory?.total || 0) - (systemData.memory?.used || 0) - (systemData.memory?.available || 0)) / (1024**3)).toFixed(2)
      }].slice(-maxDataPoints),
      
      gpu: [...dataRef.current.gpu, {
        time: timestamp,
        utilization: systemData.gpu?.[0]?.utilization || 0,
        memory_percent: systemData.gpu?.[0] ? (systemData.gpu[0].memory_used / systemData.gpu[0].memory_total * 100) : 0,
        temp: systemData.gpu?.[0]?.temperature || 0,
        power: systemData.gpu?.[0]?.power_draw || 0
      }].slice(-maxDataPoints),
      
      disk: [...dataRef.current.disk, {
        time: timestamp,
        usage_percent: systemData.disk?.percent || 0,
        read_mb: Math.random() * 100, // TODO: Get real disk I/O
        write_mb: Math.random() * 50
      }].slice(-maxDataPoints),
      
      network: [...dataRef.current.network, {
        time: timestamp,
        rx_mb: Math.random() * 10, // TODO: Get real network stats
        tx_mb: Math.random() * 5,
        connections: Math.floor(Math.random() * 100) + 50
      }].slice(-maxDataPoints),
      
      services: [...dataRef.current.services, {
        time: timestamp,
        running: services?.filter(s => s.status === 'running').length || 0,
        stopped: services?.filter(s => s.status === 'stopped').length || 0,
        total: services?.length || 0,
        health_score: calculateServiceHealthScore()
      }].slice(-maxDataPoints)
    };

    dataRef.current = newData;
    setHistoricalData(newData);
  };

  const calculateServiceHealthScore = () => {
    if (!services || services.length === 0) return 0;
    const runningCount = services.filter(s => s.status === 'running').length;
    return Math.round((runningCount / services.length) * 100);
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatUptime = (seconds) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${days}d ${hours}h ${minutes}m`;
  };

  const exportAnalytics = async () => {
    try {
      // Aggregate data from multiple analytics endpoints
      const days = timeRange === '1h' ? 1 : timeRange === '6h' ? 1 : timeRange === '24h' ? 1 : timeRange === '7d' ? 7 : 30;

      const [usageData, userData, revenueData] = await Promise.all([
        fetch(`/api/v1/analytics/usage/overview?days=${days}`).then(r => r.ok ? r.json() : {}),
        fetch('/api/v1/analytics/users/overview').then(r => r.ok ? r.json() : {}),
        fetch('/api/v1/analytics/revenue/overview').then(r => r.ok ? r.json() : {})
      ]);

      const exportData = {
        export_date: new Date().toISOString(),
        time_range: timeRange,
        usage_analytics: usageData,
        user_analytics: userData,
        revenue_analytics: revenueData,
        system_data: {
          cpu: systemData?.cpu,
          memory: systemData?.memory,
          gpu: systemData?.gpu,
          disk: systemData?.disk
        },
        services: services?.map(s => ({
          name: s.name,
          status: s.status,
          uptime: s.uptime
        }))
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `analytics-${timeRange}-${new Date().toISOString().split('T')[0]}.json`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const chartTheme = {
    backgroundColor: currentTheme === 'unicorn' ? 'transparent' : undefined,
    textColor: currentTheme === 'unicorn' ? '#fff' : '#374151',
    gridColor: currentTheme === 'unicorn' ? 'rgba(255,255,255,0.1)' : '#e5e7eb',
    tooltipBackground: currentTheme === 'unicorn' ? 'rgba(0,0,0,0.8)' : '#fff',
    tooltipBorder: currentTheme === 'unicorn' ? '#fff' : '#e5e7eb',
  };

  // Color schemes for charts
  const COLORS = {
    primary: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'],
    gradient: ['#06b6d4', '#3b82f6', '#8b5cf6', '#ec4899', '#f97316']
  };

  if (!systemData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 mb-4">
            <svg className={`animate-spin h-12 w-12 ${currentTheme === 'unicorn' ? 'text-unicorn-purple' : 'text-primary-600'}`} xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
          <h2 className={`text-xl font-semibold mb-2 ${currentTheme === 'unicorn' ? 'text-white' : 'text-gray-900 dark:text-white'}`}>Loading Analytics Data</h2>
          <p className={currentTheme === 'unicorn' ? 'text-purple-200/80' : 'text-gray-600 dark:text-gray-400'}>Gathering system metrics and performance data...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex justify-between items-start">
        <div>
          <h1 className={`text-3xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : 'text-gray-900 dark:text-white'} flex items-center gap-3`}>
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
              <ChartBarIcon className="h-6 w-6 text-white" />
            </div>
            System Analytics
          </h1>
          <p className={`${currentTheme === 'unicorn' ? 'text-purple-200/80' : 'text-gray-600 dark:text-gray-400'} mt-2`}>
            Comprehensive system performance monitoring and insights
          </p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* Time Range Selector */}
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className={`px-3 py-2 rounded-lg text-sm ${currentTheme === 'unicorn' ? 'bg-white/10 text-white border-white/20' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600'} border`}
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
          
          {/* Export Button */}
          <button
            onClick={exportAnalytics}
            className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 ${currentTheme === 'unicorn' ? 'bg-white/10 text-white hover:bg-white/20' : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'} transition-colors`}
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            Export
          </button>
          
          {/* Auto Refresh Toggle */}
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg text-sm flex items-center gap-2 ${autoRefresh ? 'bg-green-500/20 text-green-400' : currentTheme === 'unicorn' ? 'bg-white/10 text-white' : 'bg-gray-100 dark:bg-gray-700'} transition-colors`}
          >
            <ArrowPathIcon className={`h-4 w-4 ${autoRefresh ? 'animate-spin' : ''}`} />
            Auto Refresh
          </button>
        </div>
      </motion.div>

      {/* Key Metrics Overview */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* System Health Score */}
        <div className={`${theme.card} rounded-xl p-6 border border-green-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>System Health</p>
              <p className={`text-3xl font-bold ${theme.text.primary}`}>{calculateServiceHealthScore()}%</p>
              <p className={`text-xs ${theme.text.accent} mt-1`}>Overall Performance</p>
            </div>
            <div className={`w-16 h-16 rounded-full flex items-center justify-center ${calculateServiceHealthScore() > 80 ? 'bg-green-500/20' : 'bg-yellow-500/20'}`}>
              {calculateServiceHealthScore() > 80 ? (
                <CheckCircleIcon className="h-8 w-8 text-green-500" />
              ) : (
                <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500" />
              )}
            </div>
          </div>
        </div>

        {/* CPU Usage */}
        <div className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>CPU Usage</p>
              <p className={`text-3xl font-bold ${theme.text.primary}`}>{(systemData.cpu?.percent || 0).toFixed(1)}%</p>
              <p className={`text-xs ${theme.text.accent} mt-1`}>Load: {(systemData.load_average?.[0] || 0).toFixed(2)}</p>
            </div>
            <CpuChipIcon className="h-10 w-10 text-blue-500" />
          </div>
        </div>

        {/* Memory Usage */}
        <div className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Memory Usage</p>
              <p className={`text-3xl font-bold ${theme.text.primary}`}>{(systemData.memory?.percent || 0).toFixed(1)}%</p>
              <p className={`text-xs ${theme.text.accent} mt-1`}>
                {formatBytes(systemData.memory?.used || 0)} used
              </p>
            </div>
            <CircleStackIcon className="h-10 w-10 text-purple-500" />
          </div>
        </div>

        {/* Active Services */}
        <div className={`${theme.card} rounded-xl p-6 border border-orange-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Active Services</p>
              <p className={`text-3xl font-bold ${theme.text.primary}`}>
                {services?.filter(s => s.status === 'running').length || 0}
              </p>
              <p className={`text-xs ${theme.text.accent} mt-1`}>
                of {services?.length || 0} total
              </p>
            </div>
            <ServerIcon className="h-10 w-10 text-orange-500" />
          </div>
        </div>
      </motion.div>

      {/* Performance Charts Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CPU Performance Chart */}
        <div className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
            <CpuChipIcon className="h-5 w-5 text-blue-500" />
            CPU Performance Trends
          </h3>
          {historicalData.cpu.length > 0 && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={historicalData.cpu}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                  <XAxis dataKey="time" stroke={chartTheme.textColor} fontSize={12} />
                  <YAxis stroke={chartTheme.textColor} fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: chartTheme.tooltipBackground,
                      border: `1px solid ${chartTheme.tooltipBorder}`,
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="usage" fill="#3b82f6" fillOpacity={0.3} stroke="#3b82f6" name="Usage %" />
                  <Line type="monotone" dataKey="load" stroke="#10b981" strokeWidth={2} name="Load Average" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Memory Usage Chart */}
        <div className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
            <CircleStackIcon className="h-5 w-5 text-purple-500" />
            Memory Usage Breakdown
          </h3>
          {historicalData.memory.length > 0 && (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={historicalData.memory}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                  <XAxis dataKey="time" stroke={chartTheme.textColor} fontSize={12} />
                  <YAxis stroke={chartTheme.textColor} fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: chartTheme.tooltipBackground,
                      border: `1px solid ${chartTheme.tooltipBorder}`,
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="used_gb" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.7} name="Used GB" />
                  <Area type="monotone" dataKey="cached_gb" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.7} name="Cached GB" />
                  <Area type="monotone" dataKey="available_gb" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.7} name="Available GB" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </motion.div>

      {/* GPU and Disk Performance */}
      {systemData.gpu && systemData.gpu.length > 0 && (
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* GPU Performance */}
          <div className={`${theme.card} rounded-xl p-6`}>
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <FireIcon className="h-5 w-5 text-red-500" />
              GPU Performance (RTX 5090)
            </h3>
            {historicalData.gpu.length > 0 && (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={historicalData.gpu}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                    <XAxis dataKey="time" stroke={chartTheme.textColor} fontSize={12} />
                    <YAxis stroke={chartTheme.textColor} fontSize={12} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: chartTheme.tooltipBackground,
                        border: `1px solid ${chartTheme.tooltipBorder}`,
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Bar dataKey="utilization" fill="#ef4444" fillOpacity={0.7} name="GPU %" />
                    <Line type="monotone" dataKey="memory_percent" stroke="#f59e0b" strokeWidth={2} name="VRAM %" />
                    <Line type="monotone" dataKey="temp" stroke="#06b6d4" strokeWidth={2} name="Temp °C" />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {/* Service Health Timeline */}
          <div className={`${theme.card} rounded-xl p-6`}>
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <ServerIcon className="h-5 w-5 text-green-500" />
              Service Health Timeline
            </h3>
            {historicalData.services.length > 0 && (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={historicalData.services}>
                    <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                    <XAxis dataKey="time" stroke={chartTheme.textColor} fontSize={12} />
                    <YAxis stroke={chartTheme.textColor} fontSize={12} />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: chartTheme.tooltipBackground,
                        border: `1px solid ${chartTheme.tooltipBorder}`,
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Area type="monotone" dataKey="running" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.7} name="Running" />
                    <Area type="monotone" dataKey="stopped" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.7} name="Stopped" />
                    <Line type="monotone" dataKey="health_score" stroke="#3b82f6" strokeWidth={3} name="Health Score %" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Performance Insights */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
          <BoltIcon className="h-5 w-5 text-yellow-500" />
          Performance Insights & Recommendations
        </h3>
        <div className="space-y-4">
          {performanceInsights.length > 0 ? (
            performanceInsights.map((insight, index) => (
              <div key={index} className={`p-4 rounded-lg ${insight.level === 'critical' ? 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800' : insight.level === 'warning' ? 'bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800' : 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'}`}>
                <div className="flex items-start gap-3">
                  {insight.level === 'critical' ? (
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  ) : insight.level === 'warning' ? (
                    <ExclamationCircleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <InformationCircleIcon className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <h4 className={`font-medium ${insight.level === 'critical' ? 'text-red-800 dark:text-red-200' : insight.level === 'warning' ? 'text-yellow-800 dark:text-yellow-200' : 'text-blue-800 dark:text-blue-200'}`}>
                      {insight.title}
                    </h4>
                    <p className={`text-sm mt-1 ${insight.level === 'critical' ? 'text-red-700 dark:text-red-300' : insight.level === 'warning' ? 'text-yellow-700 dark:text-yellow-300' : 'text-blue-700 dark:text-blue-300'}`}>
                      {insight.description}
                    </p>
                    {insight.recommendation && (
                      <p className={`text-sm mt-2 font-medium ${insight.level === 'critical' ? 'text-red-900 dark:text-red-100' : insight.level === 'warning' ? 'text-yellow-900 dark:text-yellow-100' : 'text-blue-900 dark:text-blue-100'}`}>
                        💡 {insight.recommendation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8">
              <CheckCircleIcon className="h-12 w-12 text-green-500 mx-auto mb-3" />
              <p className={`${theme.text.primary} font-medium`}>All systems performing optimally</p>
              <p className={`${theme.text.secondary} text-sm mt-1`}>No performance issues detected</p>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}