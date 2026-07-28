/**
 * User Analytics Tab - User growth, activity, engagement
 * Displays user registration trends, tier distribution, activity patterns
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
  UsersIcon,
  UserPlusIcon,
  UserGroupIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import MetricCard from '../../../components/analytics/MetricCard';
import AnalyticsChart from '../../../components/analytics/AnalyticsChart';
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

const UserAnalyticsTab = ({ dateRange, setDateRange }) => {
  const { currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [userMetrics, setUserMetrics] = useState(null);
  const [growthData, setGrowthData] = useState(null);
  const [tierData, setTierData] = useState(null);
  const [activityData, setActivityData] = useState(null);

  useEffect(() => {
    fetchUserAnalytics();
  }, [dateRange]);

  const fetchUserAnalytics = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/admin/users/analytics/summary', { credentials: 'include' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();

      setUserMetrics({
        totalUsers: data.total_users ?? 0,
        activeUsers: data.active_users ?? 0,
        // Not provided by any real endpoint yet - rendered as "—", never invented
        newUsers30d: null,
        avgSessionTime: null,
      });

      // Real tier distribution from Keycloak
      const tiers = data.tier_distribution || {};
      const tierValues = [tiers.trial || 0, tiers.starter || 0, tiers.professional || 0, tiers.enterprise || 0];
      setTierData(tierValues.some(v => v > 0) ? {
        labels: ['Trial', 'Starter', 'Professional', 'Enterprise'],
        datasets: [
          {
            data: tierValues,
            backgroundColor: [
              'rgba(59, 130, 246, 0.8)',
              'rgba(34, 197, 94, 0.8)',
              'rgba(168, 85, 247, 0.8)',
              'rgba(251, 191, 36, 0.8)',
            ],
            borderWidth: 2,
            borderColor: currentTheme === 'light' ? '#ffffff' : '#1f2937',
          },
        ],
      } : null);

      // No real signup-history or per-hour-activity endpoints exist yet.
      // Leave these charts empty ("No data available yet") instead of
      // rendering an invented series.
      setGrowthData(null);
      setActivityData(null);
    } catch (error) {
      console.error('Error fetching user analytics:', error);
      // Honest failure state - never demo numbers
      setUserMetrics(null);
      setGrowthData(null);
      setTierData(null);
      setActivityData(null);
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className={`text-xl font-semibold ${textClass}`}>User Analytics</h3>
        <DateRangeSelector value={dateRange} onChange={setDateRange} />
      </div>

      {/* Metric Cards - real values only; "—" when a metric is not tracked yet */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={UsersIcon}
          label="Total Users"
          value={userMetrics?.totalUsers != null ? userMetrics.totalUsers : '—'}
          color="purple"
          loading={loading}
        />
        <MetricCard
          icon={UserPlusIcon}
          label="New Users (30d)"
          value={userMetrics?.newUsers30d != null ? userMetrics.newUsers30d : '—'}
          color="green"
          loading={loading}
        />
        <MetricCard
          icon={UserGroupIcon}
          label="Active Users"
          value={userMetrics?.activeUsers != null ? userMetrics.activeUsers : '—'}
          color="blue"
          loading={loading}
        />
        <MetricCard
          icon={ClockIcon}
          label="Avg Session Time"
          value={userMetrics?.avgSessionTime != null ? userMetrics.avgSessionTime : '—'}
          color="pink"
          loading={loading}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth Chart */}
        <div className={`${bgClass} rounded-xl p-6`}>
          <AnalyticsChart
            type="line"
            title="User Growth Trend"
            data={growthData}
            loading={loading}
            height="300px"
          />
        </div>

        {/* Tier Distribution */}
        <div className={`${bgClass} rounded-xl p-6`}>
          <AnalyticsChart
            type="doughnut"
            title="Users by Subscription Tier"
            data={tierData}
            loading={loading}
            height="300px"
          />
        </div>
      </div>

      {/* Activity Heatmap */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <AnalyticsChart
          type="bar"
          title="User Activity by Hour of Day"
          data={activityData}
          loading={loading}
          height="300px"
        />
      </div>

      {/* User Engagement Metrics - DAU/WAU/MAU are not tracked yet, so show an
          honest empty state instead of invented figures */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textClass} mb-4`}>Engagement Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[
            'Daily Active Users (DAU)',
            'Weekly Active Users (WAU)',
            'Monthly Active Users (MAU)'
          ].map((label) => (
            <div key={label}>
              <p className="text-gray-400 text-sm mb-2">{label}</p>
              <p className={`text-2xl font-bold ${textClass}`}>—</p>
              <p className="text-xs text-gray-500 mt-2">Not tracked yet</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default UserAnalyticsTab;
