/**
 * OrganizationCredits.jsx - Organization Credit Dashboard
 *
 * Main dashboard for organization credit pool management.
 * Shows credit balance, user allocations, usage charts, and top consumers.
 *
 * API: GET /api/v1/org-billing/credits/{org_id}
 * Created: November 15, 2025
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  CreditCardIcon,
  UserGroupIcon,
  ChartBarIcon,
  ArrowPathIcon,
  PlusIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  BanknotesIcon,
  CalendarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
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
import { Line, Bar, Doughnut } from 'react-chartjs-2';

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

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
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

export default function OrganizationCredits() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg } = useOrganization();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [creditData, setCreditData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (currentOrg) {
      loadCreditData();
    }
  }, [currentOrg]);

  const loadCreditData = async () => {
    if (!currentOrg) return;

    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/org-billing/credits/${currentOrg.id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (!response.ok) {
        throw new Error('Failed to load credit data');
      }

      const data = await response.json();
      setCreditData(data);
    } catch (err) {
      console.error('Failed to load credit data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadCreditData();
    setRefreshing(false);
  };

  const formatCredits = (amount) => {
    if (amount === null || amount === undefined) return '0';
    return Math.floor(parseFloat(amount)).toLocaleString();
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const calculatePercent = (value, total) => {
    if (!total || total === 0) return 0;
    return Math.min((value / total) * 100, 100);
  };

  const getColorForPercent = (percent) => {
    if (percent >= 90) return 'text-red-400';
    if (percent >= 75) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getGradientForPercent = (percent) => {
    if (percent >= 90) return 'from-red-500 to-red-600';
    if (percent >= 75) return 'from-yellow-500 to-orange-500';
    return 'from-green-500 to-emerald-500';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'critical': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <ArrowPathIcon className="h-12 w-12 animate-spin mx-auto mb-4 text-purple-500" />
          <p className="text-gray-400">Loading credit data...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <ExclamationTriangleIcon className="h-12 w-12 mx-auto mb-4 text-red-500" />
          <p className="text-red-400 mb-4">{error}</p>
          <button
            onClick={loadCreditData}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // No org selected
  if (!currentOrg) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <UserGroupIcon className="h-12 w-12 mx-auto mb-4 text-gray-500" />
          <p className="text-gray-400">Please select an organization</p>
        </div>
      </div>
    );
  }

  const pool = creditData?.credit_pool || {};
  const allocations = creditData?.allocations || [];
  const usage = creditData?.usage_last_30_days || [];
  const topConsumers = creditData?.top_consumers || [];

  const usedPercent = calculatePercent(pool.credits_used, pool.total_credits);
  const allocatedPercent = calculatePercent(pool.credits_allocated, pool.total_credits);
  const availablePercent = 100 - usedPercent - allocatedPercent;

  // Usage chart data
  const usageChartData = {
    labels: usage.map(u => u.date),
    datasets: [{
      label: 'Daily Credits Used',
      data: usage.map(u => u.credits_used),
      borderColor: 'rgb(168, 85, 247)',
      backgroundColor: 'rgba(168, 85, 247, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const usageChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: currentTheme.cardBackground,
        titleColor: currentTheme.text,
        bodyColor: currentTheme.textSecondary
      }
    },
    scales: {
      x: {
        ticks: { color: currentTheme.textSecondary },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      },
      y: {
        ticks: { color: currentTheme.textSecondary },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      }
    }
  };

  // Allocation breakdown chart
  const allocationChartData = {
    labels: ['Used', 'Allocated', 'Available'],
    datasets: [{
      data: [pool.credits_used, pool.credits_allocated - pool.credits_used, pool.total_credits - pool.credits_allocated],
      backgroundColor: [
        'rgba(239, 68, 68, 0.8)',
        'rgba(234, 179, 8, 0.8)',
        'rgba(34, 197, 94, 0.8)'
      ],
      borderColor: [
        'rgb(239, 68, 68)',
        'rgb(234, 179, 8)',
        'rgb(34, 197, 94)'
      ],
      borderWidth: 2
    }]
  };

  const allocationChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: currentTheme.text }
      },
      tooltip: {
        backgroundColor: currentTheme.cardBackground,
        titleColor: currentTheme.text,
        bodyColor: currentTheme.textSecondary
      }
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: currentTheme.text }}>
            Organization Credits
          </h1>
          <p className="text-sm mt-1" style={{ color: currentTheme.textSecondary }}>
            Manage your organization's credit pool and user allocations
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 rounded-lg border border-purple-500 text-purple-400 hover:bg-purple-500/10 disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => navigate('/admin/organization/purchase')}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700 flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Purchase Credits
          </button>
        </div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Credit Pool Overview */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Total Credits */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <BanknotesIcon className="h-8 w-8 text-purple-400" />
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {formatCredits(pool.total_credits)}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Total Credits
            </div>
            <div className="text-xs mt-2" style={{ color: currentTheme.textSecondary }}>
              {formatCurrency(pool.total_credits * 0.01)} value
            </div>
          </div>

          {/* Credits Used */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <ArrowTrendingDownIcon className="h-8 w-8 text-red-400" />
              <span className={`text-sm font-semibold ${getColorForPercent(usedPercent)}`}>
                {usedPercent.toFixed(1)}%
              </span>
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {formatCredits(pool.credits_used)}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Credits Used
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2 mt-3">
              <div
                className={`h-2 rounded-full bg-gradient-to-r ${getGradientForPercent(usedPercent)}`}
                style={{ width: `${usedPercent}%` }}
              />
            </div>
          </div>

          {/* Credits Allocated */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <UserGroupIcon className="h-8 w-8 text-yellow-400" />
              <span className="text-sm font-semibold text-yellow-400">
                {allocatedPercent.toFixed(1)}%
              </span>
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {formatCredits(pool.credits_allocated)}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Credits Allocated
            </div>
            <div className="text-xs mt-2" style={{ color: currentTheme.textSecondary }}>
              To {allocations.length} users
            </div>
          </div>

          {/* Available Credits */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <ArrowTrendingUpIcon className="h-8 w-8 text-green-400" />
              <span className="text-sm font-semibold text-green-400">
                {availablePercent.toFixed(1)}%
              </span>
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {formatCredits(pool.total_credits - pool.credits_allocated)}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Available to Allocate
            </div>
            <button
              onClick={() => navigate('/admin/organization/allocations')}
              className="text-xs mt-2 text-purple-400 hover:text-purple-300"
            >
              Allocate now →
            </button>
          </div>
        </motion.div>

        {/* Charts Row */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Usage Chart */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <ChartBarIcon className="h-6 w-6 text-purple-400" />
                <h3 className="text-lg font-semibold" style={{ color: currentTheme.text }}>
                  Usage Last 30 Days
                </h3>
              </div>
              <button
                onClick={() => navigate('/admin/organization/usage')}
                className="text-sm text-purple-400 hover:text-purple-300"
              >
                View Details →
              </button>
            </div>
            <div style={{ height: '300px' }}>
              <Line data={usageChartData} options={usageChartOptions} />
            </div>
          </div>

          {/* Allocation Breakdown */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <CreditCardIcon className="h-6 w-6 text-purple-400" />
                <h3 className="text-lg font-semibold" style={{ color: currentTheme.text }}>
                  Credit Allocation
                </h3>
              </div>
            </div>
            <div style={{ height: '300px' }}>
              <Doughnut data={allocationChartData} options={allocationChartOptions} />
            </div>
          </div>
        </motion.div>

        {/* Top Consumers */}
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <UserGroupIcon className="h-6 w-6 text-purple-400" />
              <h3 className="text-lg font-semibold" style={{ color: currentTheme.text }}>
                Top Credit Consumers
              </h3>
            </div>
            <button
              onClick={() => navigate('/admin/organization/usage')}
              className="text-sm text-purple-400 hover:text-purple-300"
            >
              View All Usage →
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: `1px solid ${currentTheme.border}` }}>
                  <th className="text-left py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    User
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    Allocated
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    Used
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    Remaining
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    Usage %
                  </th>
                </tr>
              </thead>
              <tbody>
                {topConsumers.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center py-8" style={{ color: currentTheme.textSecondary }}>
                      No usage data yet
                    </td>
                  </tr>
                ) : (
                  topConsumers.map((consumer, index) => {
                    const usagePercent = calculatePercent(consumer.credits_used, consumer.credits_allocated);
                    return (
                      <tr
                        key={index}
                        className="border-b hover:bg-white/5 transition-colors"
                        style={{ borderColor: currentTheme.border }}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                              {consumer.user_email?.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium" style={{ color: currentTheme.text }}>
                                {consumer.user_email}
                              </div>
                              <div className="text-xs" style={{ color: currentTheme.textSecondary }}>
                                {consumer.user_name || 'No name'}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                          {formatCredits(consumer.credits_allocated)}
                        </td>
                        <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                          {formatCredits(consumer.credits_used)}
                        </td>
                        <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                          {formatCredits(consumer.credits_allocated - consumer.credits_used)}
                        </td>
                        <td className="text-right py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <span className={`font-semibold ${getColorForPercent(usagePercent)}`}>
                              {usagePercent.toFixed(1)}%
                            </span>
                            <div className="w-24 bg-gray-700 rounded-full h-2">
                              <div
                                className={`h-2 rounded-full bg-gradient-to-r ${getGradientForPercent(usagePercent)}`}
                                style={{ width: `${Math.min(usagePercent, 100)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Quick Actions */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/admin/organization/purchase')}
            className="p-6 rounded-xl border border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/10 text-left transition-all"
          >
            <PlusIcon className="h-8 w-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold mb-2" style={{ color: currentTheme.text }}>
              Purchase Credits
            </h3>
            <p className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Add more credits to your organization's pool
            </p>
          </button>

          <button
            onClick={() => navigate('/admin/organization/allocations')}
            className="p-6 rounded-xl border border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/10 text-left transition-all"
          >
            <UserGroupIcon className="h-8 w-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold mb-2" style={{ color: currentTheme.text }}>
              Manage Allocations
            </h3>
            <p className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Allocate credits to team members
            </p>
          </button>

          <button
            onClick={() => navigate('/admin/organization/usage')}
            className="p-6 rounded-xl border border-purple-500/30 bg-purple-500/5 hover:bg-purple-500/10 text-left transition-all"
          >
            <ChartBarIcon className="h-8 w-8 text-purple-400 mb-3" />
            <h3 className="text-lg font-semibold mb-2" style={{ color: currentTheme.text }}>
              View Usage Reports
            </h3>
            <p className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Detailed usage analytics and attribution
            </p>
          </button>
        </motion.div>
      </motion.div>
    </div>
  );
}
