import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ChartBarIcon,
  BanknotesIcon,
  UsersIcon,
  CpuChipIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  FunnelIcon,
  CalendarIcon,
  ArrowPathIcon,
  DocumentArrowDownIcon,
  SparklesIcon,
  ClockIcon,
  BoltIcon,
  ShieldCheckIcon,
  CogIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

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
    currency: 'USD'
  }).format(amount);
};

// Format percentage
const formatPercent = (value) => {
  return `${value.toFixed(1)}%`;
};

// Loading skeleton
const LoadingSkeleton = ({ theme }) => (
  <div className="space-y-6">
    {[1, 2, 3].map((i) => (
      <div key={i} className={`${theme.card} rounded-xl p-6 animate-pulse`}>
        <div className="h-4 bg-slate-700 rounded w-1/4 mb-4"></div>
        <div className="h-8 bg-slate-700 rounded w-1/2"></div>
      </div>
    ))}
  </div>
);

// Metric card component
const MetricCard = ({ icon: Icon, title, value, subtitle, trend, trendLabel, color = 'purple', theme }) => {
  const colorClasses = {
    purple: 'text-purple-400 bg-purple-500/10',
    green: 'text-green-400 bg-green-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    red: 'text-red-400 bg-red-500/10',
    cyan: 'text-cyan-400 bg-cyan-500/10'
  };

  return (
    <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
              <Icon className="w-5 h-5" />
            </div>
            <p className={`text-sm font-medium ${theme.text.secondary}`}>{title}</p>
          </div>
          <p className={`text-3xl font-bold ${theme.text.primary} mb-1`}>{value}</p>
          {subtitle && <p className={`text-sm ${theme.text.secondary}`}>{subtitle}</p>}
          {trend !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend >= 0 ? (
                <ArrowTrendingUpIcon className="w-4 h-4" />
              ) : (
                <ArrowTrendingDownIcon className="w-4 h-4" />
              )}
              <span>{Math.abs(trend).toFixed(1)}%</span>
              {trendLabel && <span className={theme.text.secondary}>• {trendLabel}</span>}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// KPI Status Badge
const KPIStatusBadge = ({ status }) => {
  const colors = {
    on_track: 'bg-green-500/20 text-green-400 border-green-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30'
  };

  const icons = {
    on_track: CheckCircleIcon,
    warning: ExclamationTriangleIcon,
    critical: ExclamationTriangleIcon
  };

  const Icon = icons[status] || CheckCircleIcon;

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border flex items-center gap-1 ${colors[status] || colors.on_track}`}>
      <Icon className="w-3 h-3" />
      {status.replace('_', ' ').toUpperCase()}
    </span>
  );
};

// Severity Badge
const SeverityBadge = ({ severity }) => {
  const colors = {
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${colors[severity] || colors.low}`}>
      {severity.toUpperCase()}
    </span>
  );
};

export default function AdvancedAnalytics() {
  const { theme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState('12m');
  const [activeSection, setActiveSection] = useState('overview');

  // Revenue data
  const [mrrTrend, setMrrTrend] = useState([]);
  const [arrProjection, setArrProjection] = useState(null);
  const [mrrGrowth, setMrrGrowth] = useState(null);
  const [revenueByTier, setRevenueByTier] = useState([]);
  const [revenueForecast, setRevenueForecast] = useState([]);

  // User data
  const [cohortRetention, setCohortRetention] = useState([]);
  const [churnRate, setChurnRate] = useState(null);
  const [customerLTV, setCustomerLTV] = useState([]);
  const [acquisitionFunnel, setAcquisitionFunnel] = useState([]);
  const [userEngagement, setUserEngagement] = useState(null);

  // Service data
  const [servicePopularity, setServicePopularity] = useState([]);
  const [costPerUser, setCostPerUser] = useState(null);
  const [featureAdoption, setFeatureAdoption] = useState([]);
  const [serviceHealth, setServiceHealth] = useState([]);

  // Business metrics
  const [executiveSummary, setExecutiveSummary] = useState(null);
  const [kpis, setKPIs] = useState([]);
  const [anomalyAlerts, setAnomalyAlerts] = useState([]);

  useEffect(() => {
    loadAnalyticsData();
  }, [selectedPeriod]);

  const loadAnalyticsData = async () => {
    setLoading(true);
    try {
      // Fetch all analytics data in parallel
      const [
        mrrRes,
        arrRes,
        growthRes,
        tierRevenueRes,
        forecastRes,
        cohortsRes,
        churnRes,
        ltvRes,
        funnelRes,
        engagementRes,
        popularityRes,
        costRes,
        adoptionRes,
        healthRes,
        summaryRes,
        kpiRes,
        alertsRes
      ] = await Promise.all([
        fetch(`/api/v1/analytics/revenue/mrr?months=12`, { credentials: 'include' }),
        fetch('/api/v1/analytics/revenue/arr', { credentials: 'include' }),
        fetch('/api/v1/analytics/revenue/growth', { credentials: 'include' }),
        fetch('/api/v1/analytics/revenue/by-tier', { credentials: 'include' }),
        fetch('/api/v1/analytics/revenue/forecast?months_ahead=6', { credentials: 'include' }),
        fetch('/api/v1/analytics/users/cohorts', { credentials: 'include' }),
        fetch('/api/v1/analytics/users/churn', { credentials: 'include' }),
        fetch('/api/v1/analytics/users/ltv', { credentials: 'include' }),
        fetch('/api/v1/analytics/users/acquisition', { credentials: 'include' }),
        fetch('/api/v1/analytics/users/engagement', { credentials: 'include' }),
        fetch('/api/v1/analytics/services/popularity', { credentials: 'include' }),
        fetch('/api/v1/analytics/services/cost-per-user', { credentials: 'include' }),
        fetch('/api/v1/analytics/services/adoption', { credentials: 'include' }),
        fetch('/api/v1/analytics/services/performance', { credentials: 'include' }),
        fetch('/api/v1/analytics/metrics/summary', { credentials: 'include' }),
        fetch('/api/v1/analytics/metrics/kpis', { credentials: 'include' }),
        fetch('/api/v1/analytics/metrics/alerts', { credentials: 'include' })
      ]);

      if (mrrRes.ok) {
        const data = await mrrRes.json();
        setMrrTrend(data.mrr_trend || []);
      }

      if (arrRes.ok) {
        const data = await arrRes.json();
        setArrProjection(data);
      }

      if (growthRes.ok) {
        const data = await growthRes.json();
        setMrrGrowth(data);
      }

      if (tierRevenueRes.ok) {
        const data = await tierRevenueRes.json();
        setRevenueByTier(data.tier_breakdown || []);
      }

      if (forecastRes.ok) {
        const data = await forecastRes.json();
        setRevenueForecast(data.forecast || []);
      }

      if (cohortsRes.ok) {
        const data = await cohortsRes.json();
        setCohortRetention(data.cohorts || []);
      }

      if (churnRes.ok) {
        const data = await churnRes.json();
        setChurnRate(data);
      }

      if (ltvRes.ok) {
        const data = await ltvRes.json();
        setCustomerLTV(data.ltv_by_tier || []);
      }

      if (funnelRes.ok) {
        const data = await funnelRes.json();
        setAcquisitionFunnel(data.funnel || []);
      }

      if (engagementRes.ok) {
        const data = await engagementRes.json();
        setUserEngagement(data);
      }

      if (popularityRes.ok) {
        const data = await popularityRes.json();
        setServicePopularity(data.services || []);
      }

      if (costRes.ok) {
        const data = await costRes.json();
        setCostPerUser(data);
      }

      if (adoptionRes.ok) {
        const data = await adoptionRes.json();
        setFeatureAdoption(data.features || []);
      }

      if (healthRes.ok) {
        const data = await healthRes.json();
        setServiceHealth(data.services || []);
      }

      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setExecutiveSummary(data);
      }

      if (kpiRes.ok) {
        const data = await kpiRes.json();
        setKPIs(data.kpis || []);
      }

      if (alertsRes.ok) {
        const data = await alertsRes.json();
        setAnomalyAlerts(data.alerts || []);
      }

    } catch (error) {
      console.error('Error loading analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadAnalyticsData();
    setRefreshing(false);
  };

  const exportToPDF = () => {
    // Use jsPDF or similar library
    console.log('Export to PDF triggered');
    // Future: Implement PDF export functionality
  };

  const exportToCSV = () => {
    // Generate CSV from current data
    console.log('Export to CSV triggered');
    // Future: Implement CSV export functionality
  };

  if (loading) {
    return (
      <div className="p-6">
        <LoadingSkeleton theme={theme} />
      </div>
    );
  }

  const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b'];

  return (
    <div className="p-6">
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-2`}>
              <ChartBarIcon className="w-8 h-8 text-purple-400" />
              Advanced Analytics
            </h1>
            <p className={`${theme.text.secondary} mt-2`}>
              Executive-level business intelligence and performance metrics
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedPeriod}
              onChange={(e) => setSelectedPeriod(e.target.value)}
              className="px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-purple-500 text-sm"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="12m">Last 12 months</option>
            </select>
            <button
              onClick={exportToCSV}
              className="flex items-center gap-2 px-4 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
            >
              <DocumentArrowDownIcon className="w-4 h-4" />
              Export CSV
            </button>
            <button
              onClick={exportToPDF}
              className="flex items-center gap-2 px-4 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
            >
              <DocumentArrowDownIcon className="w-4 h-4" />
              Export PDF
            </button>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className={`flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg transition-all disabled:opacity-50`}
            >
              <ArrowPathIcon className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>

        {/* Section Navigation */}
        <div className={`${theme.card} rounded-xl p-2 flex gap-2`}>
          {[
            { id: 'overview', label: 'Overview', icon: SparklesIcon },
            { id: 'revenue', label: 'Revenue', icon: BanknotesIcon },
            { id: 'users', label: 'Users', icon: UsersIcon },
            { id: 'services', label: 'Services', icon: CpuChipIcon }
          ].map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`flex-1 flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all ${
                activeSection === section.id
                  ? 'bg-purple-600 text-white'
                  : `${theme.text.secondary} hover:bg-slate-700/50`
              }`}
            >
              <section.icon className="w-4 h-4" />
              {section.label}
            </button>
          ))}
        </div>

        {/* ============================= */}
        {/* SECTION 1: OVERVIEW */}
        {/* ============================= */}
        {activeSection === 'overview' && (
          <>
            {/* Executive Summary Cards */}
            {executiveSummary && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  icon={BanknotesIcon}
                  title="MRR"
                  value={formatCurrency(executiveSummary.mrr)}
                  subtitle={`ARR: ${formatCurrency(executiveSummary.arr)}`}
                  trend={executiveSummary.growth_rate}
                  trendLabel="vs last month"
                  color="purple"
                  theme={theme}
                />
                <MetricCard
                  icon={UsersIcon}
                  title="Total Users"
                  value={executiveSummary.total_users.toLocaleString()}
                  subtitle={`${executiveSummary.active_users} active`}
                  trend={12.5}
                  trendLabel="vs last month"
                  color="blue"
                  theme={theme}
                />
                <MetricCard
                  icon={ChartBarIcon}
                  title="ARPU"
                  value={formatCurrency(executiveSummary.average_revenue_per_user)}
                  subtitle="Average Revenue Per User"
                  trend={5.2}
                  trendLabel="vs last month"
                  color="green"
                  theme={theme}
                />
                <MetricCard
                  icon={BoltIcon}
                  title="Platform Uptime"
                  value={`${executiveSummary.platform_uptime}%`}
                  subtitle={`${executiveSummary.total_api_calls_month.toLocaleString()} API calls`}
                  trend={0.2}
                  trendLabel="vs last month"
                  color="cyan"
                  theme={theme}
                />
              </div>
            )}

            {/* KPIs */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4 flex items-center gap-2`}>
                <ShieldCheckIcon className="w-6 h-6 text-green-400" />
                Key Performance Indicators
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {kpis.map((kpi, index) => (
                  <div
                    key={index}
                    className="bg-slate-700/30 rounded-lg p-4 border border-slate-600 hover:border-slate-500 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <p className={`text-sm font-medium ${theme.text.secondary}`}>{kpi.name}</p>
                      <KPIStatusBadge status={kpi.status} />
                    </div>
                    <p className={`text-2xl font-bold ${theme.text.primary} mb-2`}>
                      {kpi.name.includes('$') || kpi.name.includes('Cost') || kpi.name.includes('Revenue')
                        ? formatCurrency(kpi.value)
                        : kpi.name.includes('Rate') || kpi.name.includes('Score') || kpi.name.includes('Uptime')
                        ? `${kpi.value}${kpi.name.includes('Score') || kpi.name.includes('Uptime') ? '' : '%'}`
                        : `${kpi.value.toFixed(0)}ms`}
                    </p>
                    <div className="flex items-center justify-between text-sm">
                      <span className={theme.text.secondary}>
                        Target: {kpi.target ? (
                          kpi.name.includes('$') || kpi.name.includes('Cost')
                            ? formatCurrency(kpi.target)
                            : kpi.name.includes('Rate') || kpi.name.includes('Score')
                            ? `${kpi.target}%`
                            : `${kpi.target}ms`
                        ) : 'N/A'}
                      </span>
                      <span className={kpi.change_percent >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {kpi.change_percent >= 0 ? '+' : ''}{kpi.change_percent.toFixed(1)}%
                      </span>
                    </div>
                    {kpi.target && (
                      <div className="w-full bg-slate-700 rounded-full h-2 mt-3">
                        <div
                          className={`h-2 rounded-full transition-all ${
                            kpi.status === 'on_track'
                              ? 'bg-green-500'
                              : kpi.status === 'warning'
                              ? 'bg-yellow-500'
                              : 'bg-red-500'
                          }`}
                          style={{
                            width: `${Math.min((kpi.value / kpi.target) * 100, 100)}%`
                          }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Anomaly Alerts */}
            {anomalyAlerts.length > 0 && (
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border-l-4 border-yellow-500`}>
                <div className="flex items-center gap-2 mb-4">
                  <ExclamationTriangleIcon className="w-6 h-6 text-yellow-400" />
                  <h3 className={`text-xl font-bold ${theme.text.primary}`}>Anomaly Alerts</h3>
                  <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-medium rounded">
                    {anomalyAlerts.length} active
                  </span>
                </div>
                <div className="space-y-3">
                  {anomalyAlerts.map((alert, index) => (
                    <div
                      key={index}
                      className="bg-slate-700/30 rounded-lg p-4 border border-slate-600"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <p className={`font-semibold ${theme.text.primary}`}>{alert.metric}</p>
                          <SeverityBadge severity={alert.severity} />
                        </div>
                        <p className={`text-xs ${theme.text.secondary}`}>
                          {new Date(alert.detected_at).toLocaleString()}
                        </p>
                      </div>
                      <p className={`text-sm ${theme.text.secondary} mb-3`}>{alert.description}</p>
                      <div className="flex items-center gap-4 text-sm">
                        <div>
                          <span className={theme.text.secondary}>Current: </span>
                          <span className="text-red-400 font-semibold">{alert.current_value.toFixed(1)}</span>
                        </div>
                        <div>
                          <span className={theme.text.secondary}>Expected: </span>
                          <span className="text-green-400 font-semibold">{alert.expected_value.toFixed(1)}</span>
                        </div>
                        <div className="ml-auto">
                          <button className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium rounded transition-colors">
                            Investigate
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </>
        )}

        {/* ============================= */}
        {/* SECTION 2: REVENUE */}
        {/* ============================= */}
        {activeSection === 'revenue' && (
          <>
            {/* Revenue Metrics */}
            {mrrGrowth && arrProjection && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  icon={BanknotesIcon}
                  title="Current MRR"
                  value={formatCurrency(mrrGrowth.current_mrr)}
                  subtitle={`Growth: ${formatCurrency(mrrGrowth.growth_amount)}`}
                  trend={mrrGrowth.growth_rate}
                  trendLabel="month-over-month"
                  color="purple"
                  theme={theme}
                />
                <MetricCard
                  icon={ArrowTrendingUpIcon}
                  title="Current ARR"
                  value={formatCurrency(arrProjection.current_arr)}
                  subtitle="Annual Recurring Revenue"
                  color="green"
                  theme={theme}
                />
                <MetricCard
                  icon={SparklesIcon}
                  title="Projected ARR (12m)"
                  value={formatCurrency(arrProjection.projected_arr_12m)}
                  subtitle={`6m: ${formatCurrency(arrProjection.projected_arr_6m)}`}
                  color="blue"
                  theme={theme}
                />
              </div>
            )}

            {/* MRR Trend Chart */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                Monthly Recurring Revenue Trend
              </h3>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={mrrTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="month" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '0.5rem'
                    }}
                    formatter={(value) => formatCurrency(value)}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="mrr" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.3} name="Total MRR" />
                  <Area type="monotone" dataKey="new_mrr" stroke="#10b981" fill="#10b981" fillOpacity={0.2} name="New MRR" />
                  <Area type="monotone" dataKey="expansion_mrr" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} name="Expansion" />
                </AreaChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Revenue by Tier */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                  Revenue by Subscription Tier
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={revenueByTier}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="tier" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '0.5rem'
                      }}
                      formatter={(value) => formatCurrency(value)}
                    />
                    <Legend />
                    <Bar dataKey="mrr" fill="#8b5cf6" name="MRR" />
                    <Bar dataKey="avg_revenue_per_user" fill="#10b981" name="Avg per User" />
                  </BarChart>
                </ResponsiveContainer>
              </motion.div>

              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                  6-Month Revenue Forecast
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={revenueForecast}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis dataKey="month" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '0.5rem'
                      }}
                      formatter={(value) => formatCurrency(value)}
                    />
                    <Legend />
                    <Line type="monotone" dataKey="projected_mrr" stroke="#8b5cf6" strokeWidth={2} name="Projected MRR" />
                    <Line type="monotone" dataKey="confidence" stroke="#10b981" strokeWidth={2} strokeDasharray="5 5" name="Confidence %" />
                  </LineChart>
                </ResponsiveContainer>
              </motion.div>
            </div>
          </>
        )}

        {/* ============================= */}
        {/* SECTION 3: USERS */}
        {/* ============================= */}
        {activeSection === 'users' && (
          <>
            {/* User Metrics */}
            {churnRate && userEngagement && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                  icon={UsersIcon}
                  title="Churn Rate"
                  value={formatPercent(churnRate.churn_rate)}
                  subtitle={`${churnRate.churned_users} churned users`}
                  trend={-16.7}
                  trendLabel="improvement"
                  color={churnRate.churn_rate < 5 ? 'green' : 'red'}
                  theme={theme}
                />
                <MetricCard
                  icon={BoltIcon}
                  title="Daily Active Users"
                  value={userEngagement.daily_active_users.toLocaleString()}
                  subtitle={`${formatPercent(userEngagement.dau_mau_ratio)} DAU/MAU`}
                  color="blue"
                  theme={theme}
                />
                <MetricCard
                  icon={ClockIcon}
                  title="Weekly Active Users"
                  value={userEngagement.weekly_active_users.toLocaleString()}
                  color="cyan"
                  theme={theme}
                />
                <MetricCard
                  icon={CheckCircleIcon}
                  title="Monthly Active Users"
                  value={userEngagement.monthly_active_users.toLocaleString()}
                  subtitle={`Engagement: ${formatPercent(userEngagement.engagement_score)}`}
                  color="green"
                  theme={theme}
                />
              </div>
            )}

            {/* Customer LTV by Tier */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                Customer Lifetime Value by Tier
              </h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={customerLTV}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="tier" stroke="#9ca3af" />
                  <YAxis stroke="#9ca3af" />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '0.5rem'
                    }}
                    formatter={(value, name) =>
                      name === 'avg_lifetime_months' ? `${value} months` : formatCurrency(value)
                    }
                  />
                  <Legend />
                  <Bar dataKey="ltv" fill="#8b5cf6" name="LTV" />
                  <Bar dataKey="avg_monthly_revenue" fill="#10b981" name="Avg Monthly Revenue" />
                </BarChart>
              </ResponsiveContainer>
            </motion.div>

            {/* Acquisition Funnel */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <div className="flex items-center gap-2 mb-4">
                <FunnelIcon className="w-6 h-6 text-purple-400" />
                <h3 className={`text-xl font-bold ${theme.text.primary}`}>User Acquisition Funnel</h3>
              </div>
              <div className="space-y-4">
                {acquisitionFunnel.map((stage, index) => (
                  <div key={index} className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-sm font-medium ${theme.text.primary}`}>{stage.stage}</span>
                      <div className="flex items-center gap-3">
                        <span className={`text-sm ${theme.text.secondary}`}>
                          {stage.count.toLocaleString()} users
                        </span>
                        <span className="text-sm font-semibold text-purple-400">
                          {formatPercent(stage.percentage)}
                        </span>
                        {index > 0 && (
                          <span className="text-sm text-green-400">
                            {formatPercent(stage.conversion_rate)} conv.
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-8">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-pink-500 h-8 rounded-full transition-all flex items-center justify-end pr-3"
                        style={{ width: `${stage.percentage}%` }}
                      >
                        <span className="text-white text-xs font-semibold">
                          {formatPercent(stage.percentage)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Cohort Retention Heatmap */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                Cohort Retention Analysis
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Cohort</th>
                      <th className={`text-center py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Size</th>
                      {[0, 1, 2, 3, 4, 5, 6].map((month) => (
                        <th key={month} className={`text-center py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>
                          M{month}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {cohortRetention.slice(0, 6).map((cohort, index) => (
                      <tr key={index} className="border-b border-slate-800">
                        <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>{cohort.cohort}</td>
                        <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>{cohort.size}</td>
                        {cohort.retention_rates.slice(0, 7).map((rate, monthIndex) => {
                          const bgOpacity = rate / 100;
                          return (
                            <td
                              key={monthIndex}
                              className="py-3 px-4 text-center text-sm font-medium"
                              style={{
                                backgroundColor: `rgba(139, 92, 246, ${bgOpacity * 0.5})`,
                                color: rate > 50 ? '#fff' : '#cbd5e1'
                              }}
                            >
                              {rate.toFixed(0)}%
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          </>
        )}

        {/* ============================= */}
        {/* SECTION 4: SERVICES */}
        {/* ============================= */}
        {activeSection === 'services' && (
          <>
            {/* Service Popularity Ranking */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4 flex items-center gap-2`}>
                <CpuChipIcon className="w-6 h-6 text-cyan-400" />
                Service Popularity Ranking
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-700">
                      <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Rank</th>
                      <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Service</th>
                      <th className={`text-center py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Total Calls</th>
                      <th className={`text-center py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Unique Users</th>
                      <th className={`text-center py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Avg Response</th>
                      <th className={`text-center py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Error Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {servicePopularity.map((service, index) => (
                      <tr key={index} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                        <td className={`py-3 px-4 text-sm font-bold ${theme.text.primary}`}>#{service.popularity_rank}</td>
                        <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>{service.service_name}</td>
                        <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>
                          {service.total_calls.toLocaleString()}
                        </td>
                        <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>
                          {service.unique_users.toLocaleString()}
                        </td>
                        <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>
                          {service.avg_response_time}ms
                        </td>
                        <td className="py-3 px-4 text-center">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${
                              service.error_rate < 1
                                ? 'bg-green-500/20 text-green-400'
                                : service.error_rate < 3
                                ? 'bg-yellow-500/20 text-yellow-400'
                                : 'bg-red-500/20 text-red-400'
                            }`}
                          >
                            {service.error_rate.toFixed(1)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>

            {/* Cost Per User Analysis */}
            {costPerUser && (
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                  Cost Efficiency Analysis
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <p className={`text-sm ${theme.text.secondary} mb-1`}>Total Monthly Cost</p>
                    <p className={`text-3xl font-bold ${theme.text.primary}`}>
                      {formatCurrency(costPerUser.total_monthly_cost)}
                    </p>
                  </div>
                  <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                    <p className={`text-sm ${theme.text.secondary} mb-1`}>Cost Per User</p>
                    <p className={`text-3xl font-bold ${theme.text.primary}`}>
                      {formatCurrency(costPerUser.total_cost_per_user)}
                    </p>
                  </div>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-slate-700">
                        <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Service</th>
                        <th className={`text-right py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Monthly Cost</th>
                        <th className={`text-right py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Cost/User</th>
                        <th className={`text-right py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Cost/Call</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costPerUser.services.map((service, index) => (
                        <tr key={index} className="border-b border-slate-800">
                          <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>{service.service}</td>
                          <td className={`py-3 px-4 text-sm text-right ${theme.text.secondary}`}>
                            {formatCurrency(service.monthly_cost)}
                          </td>
                          <td className={`py-3 px-4 text-sm text-right ${theme.text.secondary}`}>
                            {formatCurrency(service.cost_per_user)}
                          </td>
                          <td className={`py-3 px-4 text-sm text-right ${theme.text.secondary}`}>
                            {formatCurrency(service.cost_per_call)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}

            {/* Feature Adoption & Service Health */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Feature Adoption */}
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Feature Adoption Rates</h3>
                <div className="space-y-4">
                  {featureAdoption.map((feature, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-sm font-medium ${theme.text.primary}`}>{feature.feature}</span>
                        <span className={`text-sm ${theme.text.secondary}`}>
                          {feature.users_adopted.toLocaleString()} users ({formatPercent(feature.adoption_rate)})
                        </span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                          style={{ width: `${feature.adoption_rate}%` }}
                        />
                      </div>
                      <p className={`text-xs ${theme.text.secondary} mt-1`}>
                        Avg {feature.avg_usage_per_user} uses/user
                      </p>
                    </div>
                  ))}
                </div>
              </motion.div>

              {/* Service Health */}
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Service Health Scores</h3>
                <div className="space-y-4">
                  {serviceHealth.map((service, index) => (
                    <div
                      key={index}
                      className="bg-slate-700/30 rounded-lg p-4 border border-slate-600"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <p className={`font-semibold ${theme.text.primary}`}>{service.service}</p>
                        <div className="flex items-center gap-2">
                          <span
                            className={`text-2xl font-bold ${
                              service.health_score >= 95
                                ? 'text-green-400'
                                : service.health_score >= 85
                                ? 'text-yellow-400'
                                : 'text-red-400'
                            }`}
                          >
                            {service.health_score}
                          </span>
                          <span className={`text-sm ${theme.text.secondary}`}>/100</span>
                        </div>
                      </div>
                      <div className="grid grid-cols-3 gap-3 text-sm">
                        <div>
                          <p className={theme.text.secondary}>Uptime</p>
                          <p className="text-green-400 font-semibold">{service.uptime}%</p>
                        </div>
                        <div>
                          <p className={theme.text.secondary}>Latency</p>
                          <p className="text-blue-400 font-semibold">{service.avg_latency}ms</p>
                        </div>
                        <div>
                          <p className={theme.text.secondary}>Errors</p>
                          <p className="text-amber-400 font-semibold">{service.error_rate}%</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
