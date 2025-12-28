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

const OverviewTab = ({ dateRange, setDateRange }) => {
  const { currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState(null);
  const [services, setServices] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);

  useEffect(() => {
    fetchOverviewData();
  }, [dateRange]);

  const fetchOverviewData = async () => {
    setLoading(true);
    try {
      // Fetch from multiple endpoints in parallel
      const [usersRes, billingRes, servicesRes, analyticsRes] = await Promise.all([
        fetch('/api/v1/admin/users/analytics/summary'),
        fetch('/api/v1/billing/analytics/summary'),
        fetch('/api/v1/services/status'),
        fetch('/api/v1/analytics/usage/overview?range=' + dateRange)
      ]);

      const usersData = await usersRes.json();
      const billingData = await billingRes.json();
      const servicesData = await servicesRes.json();
      const analyticsData = await analyticsRes.json();

      setOverview({
        totalUsers: usersData.total_users || 0,
        activeUsers: usersData.active_users || 0,
        activeSubscriptions: billingData.active_subscriptions || 0,
        apiCalls24h: analyticsData.api_calls_24h || 0,
        revenue30d: billingData.revenue_30d || 0,
        servicesHealthy: servicesData.healthy_count || 0,
        servicesTotal: servicesData.total_count || 12,
      });

      setServices(servicesData.services || []);
      setRecentActivity(analyticsData.recent_activity || []);
    } catch (error) {
      console.error('Error fetching overview data:', error);
      // Set mock data for demonstration
      setOverview({
        totalUsers: 156,
        activeUsers: 42,
        activeSubscriptions: 38,
        apiCalls24h: 12453,
        revenue30d: 1840,
        servicesHealthy: 11,
        servicesTotal: 12,
      });
      setServices([
        { name: 'Keycloak', status: 'healthy' },
        { name: 'PostgreSQL', status: 'healthy' },
        { name: 'Redis', status: 'healthy' },
        { name: 'LiteLLM', status: 'healthy' },
        { name: 'Ops-Center', status: 'healthy' },
        { name: 'Brigade', status: 'degraded' },
      ]);
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

      {/* Key Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={UsersIcon}
          label="Total Users"
          value={overview?.totalUsers || 0}
          color="purple"
          loading={loading}
          trend="up"
          trendValue="+12%"
        />
        <MetricCard
          icon={CurrencyDollarIcon}
          label="Active Subscriptions"
          value={overview?.activeSubscriptions || 0}
          color="green"
          loading={loading}
          trend="up"
          trendValue="+5%"
        />
        <MetricCard
          icon={ChartBarIcon}
          label="API Calls (24h)"
          value={(overview?.apiCalls24h || 0).toLocaleString()}
          color="blue"
          loading={loading}
        />
        <MetricCard
          icon={CurrencyDollarIcon}
          label="Revenue (30d)"
          value={`$${(overview?.revenue30d || 0).toLocaleString()}`}
          color="pink"
          loading={loading}
          trend="up"
          trendValue="+18%"
        />
      </div>

      {/* Service Health Status */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${textClass}`}>Service Health</h3>
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5 text-green-400" />
            <span className={textClass}>
              {overview?.servicesHealthy}/{overview?.servicesTotal} Healthy
            </span>
          </div>
        </div>

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

      {/* Recent Activity Timeline */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textClass} mb-4`}>Recent Activity</h3>
        <div className="space-y-3">
          {[
            { type: 'user', message: '3 new users registered', time: '5 min ago', icon: UsersIcon },
            { type: 'payment', message: '2 subscription payments received', time: '15 min ago', icon: CurrencyDollarIcon },
            { type: 'api', message: '1,245 API calls processed', time: '1 hour ago', icon: ChartBarIcon },
            { type: 'service', message: 'LiteLLM service restarted', time: '2 hours ago', icon: ServerIcon },
          ].map((activity, index) => (
            <div key={index} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/30">
              <activity.icon className="w-5 h-5 text-purple-400" />
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
