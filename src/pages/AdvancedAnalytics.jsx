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
  ArrowPathIcon,
  SparklesIcon,
  ClockIcon,
  BoltIcon,
  ShieldCheckIcon
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

// Format currency (null-safe: the analytics endpoints may omit fields)
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(Number(amount) || 0);
};

// Format percentage (null-safe)
const formatPercent = (value) => {
  return `${(Number(value) || 0).toFixed(1)}%`;
};

// Coerce a possibly-missing series into an array
const asArray = (value) => (Array.isArray(value) ? value : []);

// Explicit, labeled empty state — rendered instead of a blank chart/table when
// the backend reports no_data:true or returns an empty series
const NoDataState = ({ theme, label = 'No data yet' }) => (
  <div className="flex flex-col items-center justify-center py-10 px-4 border border-dashed border-slate-600/60 rounded-lg text-center">
    <ChartBarIcon className="w-8 h-8 mb-2 text-slate-500" />
    <p className={`font-medium ${theme.text.primary}`}>{label}</p>
    <p className={`text-sm mt-1 ${theme.text.secondary}`}>
      No data has been reported for this metric yet.
    </p>
  </div>
);

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
      {String(status || 'unknown').replace('_', ' ').toUpperCase()}
    </span>
  );
};

// Severity Badge
const SeverityBadge = ({ severity }) => {
  const colors = {
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    // /metrics/alerts emits severity "warning" for expiring SSL certs
    warning: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    critical: 'bg-red-500/20 text-red-400 border-red-500/30'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-semibold border ${colors[severity] || colors.low}`}>
      {String(severity || 'low').toUpperCase()}
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
  // Raw /metrics/kpis payload — the endpoint returns grouped objects
  // (revenue_kpis / user_kpis / service_kpis), older payloads a `kpis` array
  const [kpiData, setKpiData] = useState(null);
  const [anomalyAlerts, setAnomalyAlerts] = useState([]);

  // Per-dataset no_data flags (backend sends no_data:true when a metric has
  // no backing data source / nothing recorded yet; failed fetches count too)
  const [noData, setNoData] = useState({});

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

      // Record each dataset's no_data flag while applying the payload; a
      // failed fetch is treated the same as "no data yet"
      const flags = {};
      const applyPayload = async (res, key, apply) => {
        if (res && res.ok) {
          const data = await res.json();
          flags[key] = data?.no_data === true;
          apply(data ?? {});
        } else {
          flags[key] = true;
        }
      };

      await applyPayload(mrrRes, 'mrr', (data) => setMrrTrend(asArray(data.mrr_trend ?? data.mrr_data)));
      await applyPayload(arrRes, 'arr', (data) => setArrProjection(data));
      await applyPayload(growthRes, 'growth', (data) => setMrrGrowth(data));
      await applyPayload(tierRevenueRes, 'revenueByTier', (data) => setRevenueByTier(asArray(data.tier_breakdown ?? data.tiers)));
      await applyPayload(forecastRes, 'forecast', (data) => setRevenueForecast(asArray(data.forecast)));
      await applyPayload(cohortsRes, 'cohorts', (data) => setCohortRetention(asArray(data.cohorts)));
      await applyPayload(churnRes, 'churn', (data) => setChurnRate(data));
      await applyPayload(ltvRes, 'ltv', (data) => setCustomerLTV(asArray(data.ltv_by_tier)));
      await applyPayload(funnelRes, 'funnel', (data) => setAcquisitionFunnel(asArray(data.funnel ?? data.acquisition_channels)));
      await applyPayload(engagementRes, 'engagement', (data) => setUserEngagement(data));
      await applyPayload(popularityRes, 'popularity', (data) => setServicePopularity(asArray(data.services)));
      await applyPayload(costRes, 'cost', (data) => setCostPerUser(data));
      await applyPayload(adoptionRes, 'adoption', (data) => setFeatureAdoption(asArray(data.features ?? data.services)));
      await applyPayload(healthRes, 'health', (data) => setServiceHealth(asArray(data.services)));
      await applyPayload(summaryRes, 'summary', (data) => setExecutiveSummary(data));
      await applyPayload(kpiRes, 'kpis', (data) => setKpiData(data));
      await applyPayload(alertsRes, 'alerts', (data) => setAnomalyAlerts(
        asArray(data.alerts ?? [
          ...asArray(data.critical_alerts),
          ...asArray(data.warning_alerts),
          ...asArray(data.info_alerts)
        ])
      ));

      setNoData(flags);

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

  if (loading) {
    return (
      <div className="p-6">
        <LoadingSkeleton theme={theme} />
      </div>
    );
  }

  const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b'];

  // Tolerant field access: these endpoints are being upgraded from no_data
  // empties to real data, so accept both the flat keys this page always read
  // and the nested keys the current payloads use. Missing values render '—'.
  const summary = executiveSummary || {};
  const summaryMrr = summary.mrr ?? summary.revenue?.mrr;
  const summaryArr = summary.arr ?? summary.revenue?.arr;
  const summaryTotalUsers = summary.total_users ?? summary.users?.total;
  const summaryActiveUsers = summary.active_users ?? summary.users?.active;
  const summaryArpu = summary.average_revenue_per_user;
  const summaryUptime = summary.platform_uptime ?? summary.services?.average_uptime;
  const summaryApiCalls = summary.total_api_calls_month ?? summary.api_calls?.this_month;
  const summaryGrowth = summary.growth_rate ?? summary.revenue?.change;
  const summaryNoData = noData.summary || !executiveSummary;

  const churnValue = churnRate?.churn_rate ?? churnRate?.monthly_churn_rate;
  const churnedUsers = churnRate?.churned_users ?? churnRate?.churned_this_month;

  const growthCurrentMrr = mrrGrowth?.current_mrr ?? mrrGrowth?.current_month_revenue;
  const growthAmount = mrrGrowth?.growth_amount;
  const growthRate = mrrGrowth?.growth_rate ?? mrrGrowth?.mom_growth;
  const currentArr = arrProjection?.current_arr ?? arrProjection?.arr;

  const costServices = asArray(costPerUser?.services ?? costPerUser?.cost_breakdown);
  const totalMonthlyCost = costPerUser?.total_monthly_cost ?? costPerUser?.total_cost;
  const totalCostPerUser = costPerUser?.total_cost_per_user ?? costPerUser?.cost_per_user;

  // /users/engagement (user_analytics.py) returns dau/wau/mau with a 0-1
  // dau_mau_ratio; older payloads used daily_active_users etc. Accept both.
  const engagementDau = userEngagement?.daily_active_users ?? userEngagement?.dau;
  const engagementWau = userEngagement?.weekly_active_users ?? userEngagement?.wau;
  const engagementMau = userEngagement?.monthly_active_users ?? userEngagement?.mau;
  const rawDauMau = userEngagement?.dau_mau_ratio;
  // A DAU/MAU ratio is <= 1 by definition; values above 1 are already percents
  const dauMauPercent = rawDauMau != null
    ? (Number(rawDauMau) > 1 ? Number(rawDauMau) : Number(rawDauMau) * 100)
    : null;

  // Each dataset in the Users grid keeps its own honest state: churn no_data
  // must not hide real engagement numbers (and vice versa)
  const churnHasData = !noData.churn && !!churnRate;
  const engagementHasData = !noData.engagement && !!userEngagement;

  // /metrics/kpis returns grouped scalar KPIs (revenue_kpis / user_kpis /
  // service_kpis). Flatten only the tracked values into display items with an
  // explicit format — status/target/change are NOT reported by the backend,
  // so they are simply not rendered (never invented). A legacy `kpis` array
  // (name/value/target/status/change_percent items) is passed through as-is.
  const kpiItems = (() => {
    if (Array.isArray(kpiData?.kpis) && kpiData.kpis.length > 0) return kpiData.kpis;
    const rev = kpiData?.revenue_kpis;
    const usr = kpiData?.user_kpis;
    const svc = kpiData?.service_kpis;
    if (!rev && !usr && !svc) return [];
    const items = [];
    // ltv / ltv_cac_ratio are documented as untracked (always 0) — omitted
    if (rev) {
      items.push({ name: 'MRR', value: rev.mrr, format: 'currency' });
      items.push({ name: 'ARR', value: rev.arr, format: 'currency' });
    }
    if (usr) {
      items.push({ name: 'Total Users', value: usr.total_users, format: 'count' });
      items.push({ name: 'Active Users (30d)', value: usr.active_users, format: 'count' });
      items.push({ name: 'Churn Rate', value: usr.churn_rate, format: 'percent' });
      items.push({ name: 'Retention Rate', value: usr.retention_rate, format: 'percent' });
    }
    if (svc) {
      items.push({ name: 'Uptime (30d)', value: svc.uptime, format: 'percent' });
      items.push({ name: 'Avg Response Time', value: svc.avg_response_time_ms, format: 'ms' });
      items.push({ name: 'LLM API Calls / Day', value: svc.api_calls_per_day, format: 'count' });
      items.push({ name: 'Error Rate', value: svc.error_rate, format: 'percent' });
    }
    return items.filter((item) => item.value != null);
  })();

  // Format a KPI value; `format` is explicit for grouped payloads, legacy
  // array items fall back to the historical name-based inference
  const formatKpiValue = (kpi) => {
    const value = Number(kpi.value) || 0;
    const name = String(kpi.name || '');
    const format = kpi.format
      || (name.includes('$') || name.includes('Cost') || name.includes('Revenue') ? 'currency'
        : name.includes('Rate') || name.includes('Uptime') ? 'percent'
        : name.includes('Score') ? 'count'
        : 'ms');
    if (format === 'currency') return formatCurrency(value);
    if (format === 'percent') return `${value}%`;
    if (format === 'ms') return `${value.toFixed(0)}ms`;
    return value.toLocaleString();
  };

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
            {/* Export CSV/PDF buttons removed — they were dead controls
                (console.log only); reintroduce when a real exporter exists */}
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
            {summaryNoData ? (
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Executive Summary</h3>
                <NoDataState theme={theme} label="No summary metrics yet" />
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <MetricCard
                  icon={BanknotesIcon}
                  title="MRR"
                  value={summaryMrr != null ? formatCurrency(summaryMrr) : '—'}
                  subtitle={summaryArr != null ? `ARR: ${formatCurrency(summaryArr)}` : undefined}
                  trend={typeof summaryGrowth === 'number' ? summaryGrowth : undefined}
                  trendLabel="vs last month"
                  color="purple"
                  theme={theme}
                />
                <MetricCard
                  icon={UsersIcon}
                  title="Total Users"
                  value={summaryTotalUsers != null ? summaryTotalUsers.toLocaleString() : '—'}
                  subtitle={summaryActiveUsers != null ? `${summaryActiveUsers} active` : undefined}
                  color="blue"
                  theme={theme}
                />
                <MetricCard
                  icon={ChartBarIcon}
                  title="ARPU"
                  value={summaryArpu != null ? formatCurrency(summaryArpu) : '—'}
                  subtitle="Average Revenue Per User"
                  color="green"
                  theme={theme}
                />
                <MetricCard
                  icon={BoltIcon}
                  title="Platform Uptime"
                  value={summaryUptime != null ? `${summaryUptime}%` : '—'}
                  subtitle={summaryApiCalls != null ? `${summaryApiCalls.toLocaleString()} API calls` : undefined}
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
              {noData.kpis || kpiItems.length === 0 ? (
                <NoDataState theme={theme} label="No KPI data yet" />
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {kpiItems.map((kpi, index) => {
                    const kpiValue = Number(kpi.value) || 0;
                    const hasChange = kpi.change_percent != null;
                    const kpiChange = Number(kpi.change_percent) || 0;
                    return (
                      <div
                        key={index}
                        className="bg-slate-700/30 rounded-lg p-4 border border-slate-600 hover:border-slate-500 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <p className={`text-sm font-medium ${theme.text.secondary}`}>{kpi.name}</p>
                          {/* Status is only reported by legacy array payloads —
                              never invent an on-track/warning badge */}
                          {kpi.status && <KPIStatusBadge status={kpi.status} />}
                        </div>
                        <p className={`text-2xl font-bold ${theme.text.primary} mb-2`}>
                          {formatKpiValue(kpi)}
                        </p>
                        {(kpi.target != null || hasChange) && (
                          <div className="flex items-center justify-between text-sm">
                            <span className={theme.text.secondary}>
                              {kpi.target != null
                                ? `Target: ${
                                    String(kpi.name || '').includes('$') || String(kpi.name || '').includes('Cost')
                                      ? formatCurrency(kpi.target)
                                      : String(kpi.name || '').includes('Rate') || String(kpi.name || '').includes('Score')
                                      ? `${kpi.target}%`
                                      : `${kpi.target}ms`
                                  }`
                                : ''}
                            </span>
                            {hasChange && (
                              <span className={kpiChange >= 0 ? 'text-green-400' : 'text-red-400'}>
                                {kpiChange >= 0 ? '+' : ''}{kpiChange.toFixed(1)}%
                              </span>
                            )}
                          </div>
                        )}
                        {kpi.target != null && (
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
                                width: `${Math.min((kpiValue / (Number(kpi.target) || 1)) * 100, 100)}%`
                              }}
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>

            {/* Anomaly Alerts */}
            <motion.div
              variants={itemVariants}
              className={`${theme.card} rounded-xl p-6 ${anomalyAlerts.length > 0 ? 'border-l-4 border-yellow-500' : ''}`}
            >
              <div className="flex items-center gap-2 mb-4">
                <ExclamationTriangleIcon className="w-6 h-6 text-yellow-400" />
                <h3 className={`text-xl font-bold ${theme.text.primary}`}>Anomaly Alerts</h3>
                {anomalyAlerts.length > 0 && (
                  <span className="px-2 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-medium rounded">
                    {anomalyAlerts.length} active
                  </span>
                )}
              </div>
              {noData.alerts ? (
                <NoDataState theme={theme} label="No anomaly data yet" />
              ) : anomalyAlerts.length === 0 ? (
                <p className={`text-sm ${theme.text.secondary}`}>No active anomaly alerts.</p>
              ) : (
                <div className="space-y-3">
                  {anomalyAlerts.map((alert, index) => {
                    // Uptime-monitor alerts carry type/service/url/error (down
                    // sites) or ssl_expiry/days_until_expiry (expiring certs);
                    // legacy anomaly items carried metric/description/values
                    const title = alert.metric ?? alert.service ?? alert.type ?? 'Alert';
                    const description = alert.description
                      ?? alert.error
                      ?? (alert.days_until_expiry != null
                        ? `SSL certificate expires in ${alert.days_until_expiry} day${alert.days_until_expiry === 1 ? '' : 's'}`
                        : alert.url);
                    const when = alert.detected_at ?? alert.ssl_expiry;
                    const hasValues = alert.current_value != null || alert.expected_value != null;
                    return (
                      <div
                        key={index}
                        className="bg-slate-700/30 rounded-lg p-4 border border-slate-600"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <p className={`font-semibold ${theme.text.primary}`}>{title}</p>
                            <SeverityBadge severity={alert.severity} />
                          </div>
                          <p className={`text-xs ${theme.text.secondary}`}>
                            {when ? new Date(when).toLocaleString() : '—'}
                          </p>
                        </div>
                        {description && (
                          <p className={`text-sm ${theme.text.secondary} ${hasValues ? 'mb-3' : ''}`}>{description}</p>
                        )}
                        {hasValues && (
                          <div className="flex items-center gap-4 text-sm">
                            <div>
                              <span className={theme.text.secondary}>Current: </span>
                              <span className="text-red-400 font-semibold">{(Number(alert.current_value) || 0).toFixed(1)}</span>
                            </div>
                            <div>
                              <span className={theme.text.secondary}>Expected: </span>
                              <span className="text-green-400 font-semibold">{(Number(alert.expected_value) || 0).toFixed(1)}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          </>
        )}

        {/* ============================= */}
        {/* SECTION 2: REVENUE */}
        {/* ============================= */}
        {activeSection === 'revenue' && (
          <>
            {/* Revenue Metrics */}
            {noData.growth || noData.arr || !mrrGrowth || !arrProjection ? (
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Revenue Metrics</h3>
                <NoDataState theme={theme} label="No revenue metrics yet" />
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <MetricCard
                  icon={BanknotesIcon}
                  title="Current MRR"
                  value={growthCurrentMrr != null ? formatCurrency(growthCurrentMrr) : '—'}
                  subtitle={growthAmount != null ? `Growth: ${formatCurrency(growthAmount)}` : undefined}
                  trend={typeof growthRate === 'number' ? growthRate : undefined}
                  trendLabel="month-over-month"
                  color="purple"
                  theme={theme}
                />
                <MetricCard
                  icon={ArrowTrendingUpIcon}
                  title="Current ARR"
                  value={currentArr != null ? formatCurrency(currentArr) : '—'}
                  subtitle="Annual Recurring Revenue"
                  color="green"
                  theme={theme}
                />
                <MetricCard
                  icon={SparklesIcon}
                  title="Projected ARR (12m)"
                  value={arrProjection.projected_arr_12m != null ? formatCurrency(arrProjection.projected_arr_12m) : '—'}
                  subtitle={arrProjection.projected_arr_6m != null ? `6m: ${formatCurrency(arrProjection.projected_arr_6m)}` : undefined}
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
              {noData.mrr || mrrTrend.length === 0 ? (
                <NoDataState theme={theme} label="No MRR history yet" />
              ) : (
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
                  {/* The MRR series reports churned_mrr (expansion is not tracked) */}
                  <Area type="monotone" dataKey="churned_mrr" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} name="Churned MRR" />
                </AreaChart>
              </ResponsiveContainer>
              )}
            </motion.div>

            {/* Revenue by Tier */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                  Revenue by Subscription Tier
                </h3>
                {noData.revenueByTier || revenueByTier.length === 0 ? (
                  <NoDataState theme={theme} label="No tier revenue data yet" />
                ) : (
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
                )}
              </motion.div>

              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                  6-Month Revenue Forecast
                </h3>
                {noData.forecast || revenueForecast.length === 0 ? (
                  <NoDataState theme={theme} label="No forecast data yet" />
                ) : (
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
                )}
              </motion.div>
            </div>
          </>
        )}

        {/* ============================= */}
        {/* SECTION 3: USERS */}
        {/* ============================= */}
        {activeSection === 'users' && (
          <>
            {/* User Metrics — churn and engagement come from different
                sources; each renders '—' when its own dataset is missing so
                one gap never hides the other's real numbers */}
            {!churnHasData && !engagementHasData ? (
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>User Metrics</h3>
                <NoDataState theme={theme} label="No user metrics yet" />
              </motion.div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <MetricCard
                  icon={UsersIcon}
                  title="Churn Rate"
                  value={churnHasData && churnValue != null ? formatPercent(churnValue) : '—'}
                  subtitle={churnHasData && churnedUsers != null ? `${churnedUsers} churned users` : undefined}
                  color={!churnHasData ? 'blue' : (Number(churnValue) || 0) < 5 ? 'green' : 'red'}
                  theme={theme}
                />
                <MetricCard
                  icon={BoltIcon}
                  title="Daily Active Users"
                  value={engagementHasData && engagementDau != null ? engagementDau.toLocaleString() : '—'}
                  subtitle={engagementHasData && dauMauPercent != null ? `${formatPercent(dauMauPercent)} DAU/MAU` : undefined}
                  color="blue"
                  theme={theme}
                />
                <MetricCard
                  icon={ClockIcon}
                  title="Weekly Active Users"
                  value={engagementHasData && engagementWau != null ? engagementWau.toLocaleString() : '—'}
                  color="cyan"
                  theme={theme}
                />
                <MetricCard
                  icon={CheckCircleIcon}
                  title="Monthly Active Users"
                  value={engagementHasData && engagementMau != null ? engagementMau.toLocaleString() : '—'}
                  subtitle={engagementHasData && userEngagement.engagement_score != null ? `Engagement: ${formatPercent(userEngagement.engagement_score)}` : undefined}
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
              {noData.ltv || customerLTV.length === 0 ? (
                <NoDataState theme={theme} label="No LTV data yet" />
              ) : (
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
              )}
            </motion.div>

            {/* Acquisition Funnel */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <div className="flex items-center gap-2 mb-4">
                <FunnelIcon className="w-6 h-6 text-purple-400" />
                <h3 className={`text-xl font-bold ${theme.text.primary}`}>User Acquisition Funnel</h3>
              </div>
              {noData.funnel || acquisitionFunnel.length === 0 ? (
                <NoDataState theme={theme} label="No acquisition data yet" />
              ) : (
              <div className="space-y-4">
                {acquisitionFunnel.map((stage, index) => (
                  <div key={index} className="relative">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`text-sm font-medium ${theme.text.primary}`}>{stage.stage}</span>
                      <div className="flex items-center gap-3">
                        <span className={`text-sm ${theme.text.secondary}`}>
                          {(stage.count ?? 0).toLocaleString()} users
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
                        style={{ width: `${Number(stage.percentage) || 0}%` }}
                      >
                        <span className="text-white text-xs font-semibold">
                          {formatPercent(stage.percentage)}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
              )}
            </motion.div>

            {/* Cohort Retention Heatmap */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                Cohort Retention Analysis
              </h3>
              {noData.cohorts || cohortRetention.length === 0 ? (
                <NoDataState theme={theme} label="No cohort data yet" />
              ) : (
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
                        <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>{cohort.size ?? '—'}</td>
                        {/* Cohort sizes are real; per-month retention is not
                            tracked yet, so missing months render '—' */}
                        {[0, 1, 2, 3, 4, 5, 6].map((monthIndex) => {
                          const rate = asArray(cohort.retention_rates)[monthIndex];
                          if (rate == null) {
                            return (
                              <td
                                key={monthIndex}
                                className={`py-3 px-4 text-center text-sm ${theme.text.secondary}`}
                              >
                                —
                              </td>
                            );
                          }
                          const rateValue = Number(rate) || 0;
                          const bgOpacity = rateValue / 100;
                          return (
                            <td
                              key={monthIndex}
                              className="py-3 px-4 text-center text-sm font-medium"
                              style={{
                                backgroundColor: `rgba(139, 92, 246, ${bgOpacity * 0.5})`,
                                color: rateValue > 50 ? '#fff' : '#cbd5e1'
                              }}
                            >
                              {rateValue.toFixed(0)}%
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              )}
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
              {noData.popularity || servicePopularity.length === 0 ? (
                <NoDataState theme={theme} label="No service usage data yet" />
              ) : (
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
                    {servicePopularity.map((service, index) => {
                      const errorRate = Number(service.error_rate) || 0;
                      return (
                        <tr key={index} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                          <td className={`py-3 px-4 text-sm font-bold ${theme.text.primary}`}>#{service.popularity_rank ?? index + 1}</td>
                          <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>{service.service_name}</td>
                          <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>
                            {(service.total_calls ?? 0).toLocaleString()}
                          </td>
                          <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>
                            {(service.unique_users ?? 0).toLocaleString()}
                          </td>
                          <td className={`py-3 px-4 text-sm text-center ${theme.text.secondary}`}>
                            {service.avg_response_time != null ? `${service.avg_response_time}ms` : '—'}
                          </td>
                          <td className="py-3 px-4 text-center">
                            <span
                              className={`px-2 py-1 rounded-full text-xs font-medium ${
                                errorRate < 1
                                  ? 'bg-green-500/20 text-green-400'
                                  : errorRate < 3
                                  ? 'bg-yellow-500/20 text-yellow-400'
                                  : 'bg-red-500/20 text-red-400'
                              }`}
                            >
                              {errorRate.toFixed(1)}%
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              )}
            </motion.div>

            {/* Cost Per User Analysis */}
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>
                Cost Efficiency Analysis
              </h3>
              {noData.cost || !costPerUser ? (
                <NoDataState theme={theme} label="No cost data yet" />
              ) : (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                      <p className={`text-sm ${theme.text.secondary} mb-1`}>Total Monthly Cost</p>
                      <p className={`text-3xl font-bold ${theme.text.primary}`}>
                        {totalMonthlyCost != null ? formatCurrency(totalMonthlyCost) : '—'}
                      </p>
                    </div>
                    <div className="bg-slate-700/30 rounded-lg p-4 border border-slate-600">
                      <p className={`text-sm ${theme.text.secondary} mb-1`}>Cost Per User</p>
                      <p className={`text-3xl font-bold ${theme.text.primary}`}>
                        {totalCostPerUser != null ? formatCurrency(totalCostPerUser) : '—'}
                      </p>
                    </div>
                  </div>
                  {costServices.length === 0 ? (
                    <NoDataState theme={theme} label="No per-service cost breakdown yet" />
                  ) : (
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
                          {costServices.map((service, index) => (
                            <tr key={index} className="border-b border-slate-800">
                              <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>{service.service ?? service.name}</td>
                              <td className={`py-3 px-4 text-sm text-right ${theme.text.secondary}`}>
                                {service.monthly_cost != null ? formatCurrency(service.monthly_cost) : '—'}
                              </td>
                              <td className={`py-3 px-4 text-sm text-right ${theme.text.secondary}`}>
                                {service.cost_per_user != null ? formatCurrency(service.cost_per_user) : '—'}
                              </td>
                              <td className={`py-3 px-4 text-sm text-right ${theme.text.secondary}`}>
                                {service.cost_per_call != null ? formatCurrency(service.cost_per_call) : '—'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </>
              )}
            </motion.div>

            {/* Feature Adoption & Service Health */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Feature Adoption */}
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Feature Adoption Rates</h3>
                {noData.adoption || featureAdoption.length === 0 ? (
                  <NoDataState theme={theme} label="No adoption data yet" />
                ) : (
                <div className="space-y-4">
                  {featureAdoption.map((feature, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-2">
                        {/* /services/adoption items use service + users */}
                        <span className={`text-sm font-medium ${theme.text.primary}`}>
                          {feature.feature ?? feature.service ?? feature.name}
                        </span>
                        <span className={`text-sm ${theme.text.secondary}`}>
                          {(feature.users_adopted ?? feature.users ?? 0).toLocaleString()} users ({formatPercent(feature.adoption_rate)})
                        </span>
                      </div>
                      <div className="w-full bg-slate-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                          style={{ width: `${Number(feature.adoption_rate) || 0}%` }}
                        />
                      </div>
                      {feature.avg_usage_per_user != null && (
                        <p className={`text-xs ${theme.text.secondary} mt-1`}>
                          Avg {feature.avg_usage_per_user} uses/user
                        </p>
                      )}
                    </div>
                  ))}
                </div>
                )}
              </motion.div>

              {/* Service Health */}
              <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-4`}>Service Health Scores</h3>
                {noData.health || serviceHealth.length === 0 ? (
                  <NoDataState theme={theme} label="No service health data yet" />
                ) : (
                <div className="space-y-4">
                  {serviceHealth.map((service, index) => {
                    const healthScore = Number(service.health_score) || 0;
                    return (
                      <div
                        key={index}
                        className="bg-slate-700/30 rounded-lg p-4 border border-slate-600"
                      >
                        <div className="flex items-center justify-between mb-3">
                          <p className={`font-semibold ${theme.text.primary}`}>{service.service ?? service.service_name}</p>
                          <div className="flex items-center gap-2">
                            <span
                              className={`text-2xl font-bold ${
                                healthScore >= 95
                                  ? 'text-green-400'
                                  : healthScore >= 85
                                  ? 'text-yellow-400'
                                  : 'text-red-400'
                              }`}
                            >
                              {healthScore}
                            </span>
                            <span className={`text-sm ${theme.text.secondary}`}>/100</span>
                          </div>
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-sm">
                          <div>
                            <p className={theme.text.secondary}>Uptime</p>
                            <p className="text-green-400 font-semibold">{service.uptime != null ? `${service.uptime}%` : '—'}</p>
                          </div>
                          <div>
                            <p className={theme.text.secondary}>Latency</p>
                            <p className="text-blue-400 font-semibold">{service.avg_latency != null ? `${service.avg_latency}ms` : '—'}</p>
                          </div>
                          <div>
                            <p className={theme.text.secondary}>Errors</p>
                            <p className="text-amber-400 font-semibold">{service.error_rate != null ? `${service.error_rate}%` : '—'}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
                )}
              </motion.div>
            </div>
          </>
        )}
      </motion.div>
    </div>
  );
}
