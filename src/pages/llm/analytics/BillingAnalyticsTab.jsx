/**
 * Billing Analytics Tab - Revenue, subscriptions, usage costs
 * Displays revenue trends, subscription breakdown, payment metrics
 */

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import {
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  CreditCardIcon,
  ChartPieIcon
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
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const BillingAnalyticsTab = ({ dateRange, setDateRange }) => {
  const { currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [billingMetrics, setBillingMetrics] = useState(null);
  const [revenueData, setRevenueData] = useState(null);
  const [subscriptionData, setSubscriptionData] = useState(null);
  const [mrr, setMrr] = useState(null);
  const [topCustomer, setTopCustomer] = useState(null);

  useEffect(() => {
    fetchBillingAnalytics();
  }, [dateRange]);

  const fetchBillingAnalytics = async () => {
    setLoading(true);
    try {
      // Real DB-backed endpoints (the old /billing/analytics/summary route
      // served hardcoded numbers)
      const [dashRes, trendsRes, topRes] = await Promise.all([
        fetch('/api/v1/billing/analytics/dashboard?days=30', { credentials: 'include' }),
        fetch('/api/v1/billing/analytics/revenue/trends?period=month&limit=12', { credentials: 'include' }),
        fetch('/api/v1/billing/analytics/customers/top?limit=1&metric=spend', { credentials: 'include' })
      ]);

      if (dashRes.ok) {
        const data = await dashRes.json();
        setBillingMetrics({
          mrr: data.mrr ?? 0,
          arr: data.arr ?? 0,
          activeSubscriptions: data.active_subscriptions?.total ?? 0,
          churnRate: data.churn_rate,
        });

        // Real subscription plan breakdown (platform / BYOK / hybrid)
        const subs = data.active_subscriptions || {};
        const planValues = [subs.platform || 0, subs.byok || 0, subs.hybrid || 0];
        setSubscriptionData(planValues.some(v => v > 0) ? {
          labels: ['Platform', 'BYOK', 'Hybrid'],
          datasets: [
            {
              data: planValues,
              backgroundColor: [
                'rgba(59, 130, 246, 0.8)',
                'rgba(168, 85, 247, 0.8)',
                'rgba(251, 191, 36, 0.8)',
              ],
              borderWidth: 2,
              borderColor: currentTheme === 'light' ? '#ffffff' : '#1f2937',
            },
          ],
        } : null);
      } else {
        setBillingMetrics(null);
        setSubscriptionData(null);
      }

      if (trendsRes.ok) {
        const trends = await trendsRes.json();
        const points = trends.data || [];
        setRevenueData(points.length > 0 ? {
          labels: points.map(p => String(p.period || '').slice(0, 7)),
          datasets: [
            {
              label: 'New-subscription revenue',
              data: points.map(p => p.revenue ?? 0),
              borderColor: 'rgb(34, 197, 94)',
              backgroundColor: 'rgba(34, 197, 94, 0.1)',
              tension: 0.4,
              fill: true,
            },
          ],
        } : null);
      } else {
        setRevenueData(null);
      }

      if (topRes.ok) {
        const top = await topRes.json();
        setTopCustomer(top.customers?.[0] || null);
      } else {
        setTopCustomer(null);
      }

      // Historical MRR is not tracked yet - show "No data available yet"
      // instead of an invented growth curve.
      setMrr(null);
    } catch (error) {
      console.error('Error fetching billing analytics:', error);
      // Honest failure state - never demo numbers
      setBillingMetrics(null);
      setRevenueData(null);
      setSubscriptionData(null);
      setMrr(null);
      setTopCustomer(null);
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
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className={`text-xl font-semibold ${textClass}`}>Billing & Revenue Analytics</h3>
        <DateRangeSelector value={dateRange} onChange={setDateRange} />
      </div>

      {/* Metric Cards - real values only; "—" when a source is unavailable */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={ArrowTrendingUpIcon}
          label="Monthly Recurring Revenue"
          value={billingMetrics?.mrr != null ? `$${billingMetrics.mrr.toLocaleString()}` : '—'}
          color="yellow"
          loading={loading}
        />
        <MetricCard
          icon={CurrencyDollarIcon}
          label="Annual Recurring Revenue"
          value={billingMetrics?.arr != null ? `$${billingMetrics.arr.toLocaleString()}` : '—'}
          color="green"
          loading={loading}
        />
        <MetricCard
          icon={ChartPieIcon}
          label="Active Subscriptions"
          value={billingMetrics?.activeSubscriptions != null ? billingMetrics.activeSubscriptions : '—'}
          color="purple"
          loading={loading}
        />
        <MetricCard
          icon={CreditCardIcon}
          label="Churn Rate (30d)"
          value={billingMetrics?.churnRate != null ? `${billingMetrics.churnRate}%` : '—'}
          color="blue"
          loading={loading}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Revenue Trends */}
        <div className={`${bgClass} rounded-xl p-6`}>
          <AnalyticsChart
            type="line"
            title="Revenue Trends"
            data={revenueData}
            loading={loading}
            height="300px"
          />
        </div>

        {/* Subscription Breakdown */}
        <div className={`${bgClass} rounded-xl p-6`}>
          <AnalyticsChart
            type="pie"
            title="Subscription Plan Distribution"
            data={subscriptionData}
            loading={loading}
            height="300px"
          />
        </div>
      </div>

      {/* MRR Growth */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <AnalyticsChart
          type="line"
          title="Monthly Recurring Revenue Growth"
          data={mrr}
          loading={loading}
          height="300px"
        />
      </div>

      {/* Key Metrics Table - no per-tier revenue endpoint exists yet */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textClass} mb-4`}>Revenue Breakdown</h3>
        <div className="py-8 text-center">
          <p className={`text-sm ${subtextClass}`}>
            Per-tier revenue breakdown is not available yet.
          </p>
        </div>
      </div>

      {/* Churn Analysis - real values or an explicit "—" */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`${bgClass} rounded-xl p-6`}>
          <h4 className={`text-sm ${subtextClass} mb-2`}>Churn Rate (30d)</h4>
          <p className={`text-3xl font-bold ${textClass}`}>
            {billingMetrics?.churnRate != null ? `${billingMetrics.churnRate}%` : '—'}
          </p>
        </div>
        <div className={`${bgClass} rounded-xl p-6`}>
          <h4 className={`text-sm ${subtextClass} mb-2`}>Avg Customer LTV</h4>
          <p className={`text-3xl font-bold ${textClass}`}>—</p>
          <p className="text-sm text-gray-500 mt-2">Not tracked yet</p>
        </div>
        <div className={`${bgClass} rounded-xl p-6`}>
          <h4 className={`text-sm ${subtextClass} mb-2`}>Top Customer by Spend</h4>
          {topCustomer ? (
            <>
              <p className={`text-2xl font-bold ${textClass} truncate`} title={topCustomer.org_name}>
                {topCustomer.org_name || '—'}
              </p>
              <p className="text-sm text-gray-400 mt-2">
                {topCustomer.monthly_spend != null ? `$${Number(topCustomer.monthly_spend).toLocaleString()}/mo` : ''}
              </p>
            </>
          ) : (
            <p className={`text-3xl font-bold ${textClass}`}>—</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default BillingAnalyticsTab;
