/**
 * Overview Tab - Key metrics from all systems
 * Provides high-level dashboard of total users, subscriptions, API calls, revenue
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  UsersIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ServerIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import MetricCard from '../../../components/analytics/MetricCard';
import DateRangeSelector from '../../../components/analytics/DateRangeSelector';
import { useTheme } from '../../../contexts/ThemeContext';

// Format an audit-log timestamp as a relative time string
const formatActivityTime = (timestamp) => {
  if (!timestamp) return '';
  try {
    const diffSec = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return `${Math.floor(diffSec / 86400)}d ago`;
  } catch (e) {
    return '';
  }
};

const OverviewTab = ({ dateRange, setDateRange }) => {
  const { currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [services, setServices] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOverviewData();
  }, [dateRange]);

  const fetchOverviewData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch from multiple real endpoints in parallel
      const [usersRes, billingRes, servicesRes, usageRes, auditRes] = await Promise.all([
        fetch('/api/v1/admin/users/analytics/summary', { credentials: 'include' }),
        // Real DB-backed billing metrics (the old /billing/analytics/summary route served hardcoded data)
        fetch('/api/v1/billing/analytics/dashboard?days=30', { credentials: 'include' }),
        fetch('/api/v1/services/status', { credentials: 'include' }),
        // Real log-derived API usage; days=1 matches the "API Calls (24h)" card
        fetch('/api/v1/analytics/usage/overview?days=1', { credentials: 'include' }),
        // Real audit log for the activity feed
        fetch('/api/v1/audit/recent?limit=5', { credentials: 'include' })
      ]);

      const usersData = usersRes.ok ? await usersRes.json() : null;
      const billingData = billingRes.ok ? await billingRes.json() : null;
      const servicesData = servicesRes.ok ? await servicesRes.json() : null;
      const usageData = usageRes.ok ? await usageRes.json() : null;
      const auditData = auditRes.ok ? await auditRes.json() : null;

      const serviceList = servicesData?.services || [];

      setOverview({
        totalUsers: usersData ? (usersData.total_users ?? 0) : null,
        activeUsers: usersData ? (usersData.active_users ?? 0) : null,
        activeSubscriptions: billingData ? (billingData.active_subscriptions?.total ?? 0) : null,
        apiCalls24h: usageData ? (usageData.total_api_calls ?? 0) : null,
        mrr: billingData ? (billingData.mrr ?? 0) : null,
        servicesHealthy: serviceList.filter(s => s.status === 'healthy').length,
        servicesTotal: serviceList.length,
      });

      setServices(serviceList);
      setRecentActivity((auditData?.logs || []).map(log => ({
        message: log.details || log.action || 'System event',
        time: formatActivityTime(log.timestamp),
        category: log.category || 'system'
      })));

      if (!usersRes.ok && !billingRes.ok && !servicesRes.ok && !usageRes.ok) {
        setError('Analytics data is unavailable right now.');
        setOverview(null);
      }
    } catch (error) {
      console.error('Error fetching overview data:', error);
      // Honest failure state - never demo numbers
      setOverview(null);
      setServices([]);
      setRecentActivity([]);
      setError('Analytics data is unavailable right now.');
    } finally {
      setLoading(false);
    }
  };

  const bgClass = currentTheme === 'unicorn'
    ? 'bg-purple-900/20 border border-purple-500/20'
    : currentTheme === 'light'
    ? 'bg-white border border-gray-200'
    : 'bg-gray-800 border border-gray-700';

  const textClass = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const subtextClass = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  return (
    <div className="space-y-6">
      {/* Date Range Selector */}
      <div className="flex justify-between items-center">
        <h3 className={`text-xl font-semibold ${textClass}`}>System Overview</h3>
        <DateRangeSelector value={dateRange} onChange={setDateRange} />
      </div>

      {/* Error banner */}
      {error && !loading && (
        <div className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/30">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Key Metrics Cards - real values only; "—" when a source is unavailable */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={UsersIcon}
          label="Total Users"
          value={overview?.totalUsers != null ? overview.totalUsers : '—'}
          color="purple"
          loading={loading}
        />
        <MetricCard
          icon={CurrencyDollarIcon}
          label="Active Subscriptions"
          value={overview?.activeSubscriptions != null ? overview.activeSubscriptions : '—'}
          color="green"
          loading={loading}
        />
        <MetricCard
          icon={ChartBarIcon}
          label="API Calls (24h)"
          value={overview?.apiCalls24h != null ? overview.apiCalls24h.toLocaleString() : '—'}
          color="blue"
          loading={loading}
        />
        <MetricCard
          icon={CurrencyDollarIcon}
          label="MRR"
          value={overview?.mrr != null ? `$${overview.mrr.toLocaleString()}` : '—'}
          color="pink"
          loading={loading}
        />
      </div>

      {/* Service Health Status */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${textClass}`}>Service Health</h3>
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5 text-green-400" />
            <span className={textClass}>
              {overview ? `${overview.servicesHealthy}/${overview.servicesTotal} Healthy` : '—'}
            </span>
          </div>
        </div>

        {services.length === 0 && !loading && (
          <p className={`text-sm ${subtextClass}`}>No service status available</p>
        )}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {services.slice(0, 12).map((service, index) => (
            <div
              key={index}
              className={`p-3 rounded-lg ${
                service.status === 'healthy'
                  ? 'bg-green-500/10 border border-green-500/30'
                  : service.status === 'degraded'
                  ? 'bg-yellow-500/10 border border-yellow-500/30'
                  : 'bg-red-500/10 border border-red-500/30'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className={`text-sm font-medium ${textClass}`}>{service.name}</span>
                <div
                  className={`w-2 h-2 rounded-full ${
                    service.status === 'healthy'
                      ? 'bg-green-400'
                      : service.status === 'degraded'
                      ? 'bg-yellow-400'
                      : 'bg-red-400'
                  }`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recent Activity Timeline - real audit-log entries */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textClass} mb-4`}>Recent Activity</h3>
        {recentActivity.length === 0 ? (
          <p className={`text-sm ${subtextClass}`}>No recent activity recorded yet</p>
        ) : (
          <div className="space-y-3">
            {recentActivity.map((activity, index) => (
              <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/30">
                <ServerIcon className="w-5 h-5 text-purple-400" />
                <div className="flex-1">
                  <p className={textClass}>{activity.message}</p>
                </div>
                <span className={`text-sm ${subtextClass}`}>
                  <ClockIcon className="w-4 h-4 inline mr-1" />
                  {activity.time}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button className="p-4 rounded-lg bg-purple-600 hover:bg-purple-700 text-white font-medium transition-colors">
          View All Users
        </button>
        <button className="p-4 rounded-lg bg-green-600 hover:bg-green-700 text-white font-medium transition-colors">
          Billing Dashboard
        </button>
        <button className="p-4 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-medium transition-colors">
          Service Management
        </button>
      </div>
    </div>
  );
};

export default OverviewTab;
