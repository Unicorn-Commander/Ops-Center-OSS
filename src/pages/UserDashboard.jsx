/**
 * User Dashboard - Personal dashboard for regular users
 *
 * Shows user-centric information:
 * - Credits remaining and usage
 * - Subscription tier and renewal
 * - API usage and costs
 * - Model usage breakdown
 * - Quick actions
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { getGlassmorphismStyles } from '../styles/glassmorphism';

// Icons
import {
  CurrencyDollarIcon,
  ChartBarIcon,
  CreditCardIcon,
  SparklesIcon,
  ArrowPathIcon,
  KeyIcon,
  DocumentTextIcon,
  ArrowUpCircleIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  CpuChipIcon,
  ChatBubbleLeftRightIcon,
  PhotoIcon,
  CalendarIcon
} from '@heroicons/react/24/outline';

// Animation variants
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

// Format credits with commas
const formatCredits = (amount) => {
  if (amount === null || amount === undefined) return '0';
  return Math.floor(parseFloat(amount)).toLocaleString();
};

// Format currency
const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return '$0.00';
  return `$${parseFloat(amount).toFixed(2)}`;
};

// Format date
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  } catch {
    return 'N/A';
  }
};

// Get usage color based on percentage
const getUsageColor = (percent) => {
  if (percent >= 90) return 'text-red-400';
  if (percent >= 75) return 'text-yellow-400';
  return 'text-green-400';
};

// Get usage bar color
const getUsageBarColor = (percent) => {
  if (percent >= 90) return 'from-red-500 to-red-600';
  if (percent >= 75) return 'from-yellow-500 to-orange-500';
  return 'from-green-500 to-emerald-500';
};

// Tier badge colors
const getTierColor = (tier) => {
  const colors = {
    'vip_founder': 'from-yellow-500 to-amber-600',
    'enterprise': 'from-purple-500 to-indigo-600',
    'professional': 'from-blue-500 to-cyan-600',
    'starter': 'from-green-500 to-teal-600',
    'trial': 'from-gray-500 to-slate-600',
    'byok': 'from-pink-500 to-rose-600',
  };
  return colors[tier?.toLowerCase()] || 'from-gray-500 to-slate-600';
};

// Format tier name
const formatTierName = (tier) => {
  if (!tier) return 'Free';
  return tier.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

export default function UserDashboard() {
  const { currentTheme } = useTheme();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  // State
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Data states
  const [balance, setBalance] = useState(null);
  const [usage, setUsage] = useState(null);
  const [subscription, setSubscription] = useState(null);
  const [usageByModel, setUsageByModel] = useState([]);
  const [usageByService, setUsageByService] = useState([]);
  const [recentTransactions, setRecentTransactions] = useState([]);

  // Fetch all dashboard data
  const fetchDashboardData = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    }

    try {
      // Fetch all data in parallel
      const [
        balanceRes,
        usageRes,
        subscriptionRes,
        modelUsageRes,
        serviceUsageRes,
        transactionsRes
      ] = await Promise.all([
        fetch('/api/v1/credits/balance', { credentials: 'include' }),
        fetch('/api/v1/credits/usage/summary', { credentials: 'include' }),
        fetch('/api/v1/subscriptions/current', { credentials: 'include' }),
        fetch('/api/v1/credits/usage/by-model', { credentials: 'include' }),
        fetch('/api/v1/credits/usage/by-service', { credentials: 'include' }),
        fetch('/api/v1/credits/transactions?limit=5', { credentials: 'include' })
      ]);

      // Parse responses
      if (balanceRes.ok) {
        setBalance(await balanceRes.json());
      }
      if (usageRes.ok) {
        setUsage(await usageRes.json());
      }
      if (subscriptionRes.ok) {
        setSubscription(await subscriptionRes.json());
      }
      if (modelUsageRes.ok) {
        const data = await modelUsageRes.json();
        setUsageByModel(Array.isArray(data) ? data.slice(0, 5) : []);
      }
      if (serviceUsageRes.ok) {
        const data = await serviceUsageRes.json();
        setUsageByService(Array.isArray(data) ? data : []);
      }
      if (transactionsRes.ok) {
        const data = await transactionsRes.json();
        setRecentTransactions(Array.isArray(data) ? data.slice(0, 5) :
          (data.transactions ? data.transactions.slice(0, 5) : []));
      }

      setError(null);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Calculate usage percentage
  const usagePercent = balance?.allocated_monthly && usage?.this_month
    ? Math.min((usage.this_month / balance.allocated_monthly) * 100, 100)
    : 0;

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen p-6 flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center gap-4"
        >
          <ArrowPathIcon className="h-8 w-8 text-purple-400 animate-spin" />
          <p className="text-gray-400">Loading your dashboard...</p>
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="min-h-screen p-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">My Dashboard</h1>
          <p className="text-gray-400 text-sm mt-1">
            Your credits, usage, and subscription overview
          </p>
        </div>
        <button
          onClick={() => fetchDashboardData(true)}
          disabled={refreshing}
          className={`${glassStyles.button} px-4 py-2 rounded-lg flex items-center gap-2
            hover:bg-white/10 transition-colors disabled:opacity-50`}
        >
          <ArrowPathIcon className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </motion.div>

      {/* Error Alert */}
      {error && (
        <motion.div
          variants={itemVariants}
          className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3"
        >
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
          <span className="text-red-400">{error}</span>
          <button
            onClick={() => fetchDashboardData()}
            className="ml-auto text-red-400 hover:text-red-300"
          >
            Retry
          </button>
        </motion.div>
      )}

      {/* Stats Cards Row */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Credits Balance */}
        <div className={`${glassStyles.card} rounded-2xl p-5`}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-indigo-600 rounded-xl flex items-center justify-center">
              <CurrencyDollarIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Credit Balance</p>
              <p className="text-xl font-bold text-white">{formatCredits(balance?.balance)}</p>
            </div>
          </div>
          <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${100 - usagePercent}%` }}
              transition={{ duration: 0.5 }}
              className={`h-full rounded-full bg-gradient-to-r ${getUsageBarColor(usagePercent)}`}
            />
          </div>
          <p className="text-xs text-gray-500 mt-2">
            {(100 - usagePercent).toFixed(1)}% remaining
          </p>
        </div>

        {/* Used This Month */}
        <div className={`${glassStyles.card} rounded-2xl p-5`}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-600 rounded-xl flex items-center justify-center">
              <ChartBarIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Used This Month</p>
              <p className="text-xl font-bold text-white">{formatCredits(usage?.this_month || 0)}</p>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            of {formatCredits(balance?.allocated_monthly)} monthly allocation
          </p>
          {usage?.projected_month_end && (
            <p className={`text-xs mt-1 ${getUsageColor(usagePercent)}`}>
              Projected: {formatCredits(usage.projected_month_end)} credits
            </p>
          )}
        </div>

        {/* Subscription Tier */}
        <div className={`${glassStyles.card} rounded-2xl p-5`}>
          <div className="flex items-center gap-3 mb-3">
            <div className={`w-10 h-10 bg-gradient-to-br ${getTierColor(balance?.tier)} rounded-xl flex items-center justify-center`}>
              <SparklesIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Subscription Tier</p>
              <p className="text-xl font-bold text-white">{formatTierName(balance?.tier || subscription?.plan_code)}</p>
            </div>
          </div>
          {balance?.next_reset_date && (
            <p className="text-xs text-gray-500 flex items-center gap-1">
              <ClockIcon className="h-3 w-3" />
              Resets {formatDate(balance.next_reset_date)}
            </p>
          )}
        </div>

        {/* Spending */}
        <div className={`${glassStyles.card} rounded-2xl p-5`}>
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center">
              <CreditCardIcon className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="text-xs text-gray-400">Spending This Period</p>
              <p className="text-xl font-bold text-white">
                {formatCurrency((usage?.this_month || 0) / 100)}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-500">
            ~{formatCredits(usage?.average_daily || 0)} credits/day
          </p>
        </div>
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Usage & Models */}
        <div className="lg:col-span-2 space-y-6">
          {/* Usage by Model */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <CpuChipIcon className="h-5 w-5 text-purple-400" />
                Model Usage
              </h3>
              <Link
                to="/admin/credits"
                className="text-sm text-purple-400 hover:text-purple-300"
              >
                View All →
              </Link>
            </div>

            {usageByModel.length > 0 ? (
              <div className="space-y-3">
                {usageByModel.map((model, idx) => {
                  const maxCredits = Math.max(...usageByModel.map(m => m.credits_used || m.total_credits || 0));
                  const credits = model.credits_used || model.total_credits || 0;
                  const percent = maxCredits > 0 ? (credits / maxCredits) * 100 : 0;

                  return (
                    <div key={idx} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-300 truncate max-w-[200px]">
                          {model.model_name || model.model || 'Unknown Model'}
                        </span>
                        <span className="text-gray-400">
                          {formatCredits(credits)} credits
                        </span>
                      </div>
                      <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percent}%` }}
                          transition={{ duration: 0.5, delay: idx * 0.1 }}
                          className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <CpuChipIcon className="h-10 w-10 mx-auto mb-2 opacity-50" />
                <p>No model usage yet this period</p>
                <Link
                  to="/admin/account/api-keys"
                  className={`${glassStyles.button} mt-4 inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm`}
                >
                  Create API Key
                </Link>
              </div>
            )}
          </motion.div>

          {/* Usage by Service */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
            <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
              <BoltIcon className="h-5 w-5 text-yellow-400" />
              Service Breakdown
            </h3>

            {usageByService.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {usageByService.map((service, idx) => {
                  const getServiceIcon = (name) => {
                    const n = (name || '').toLowerCase();
                    if (n.includes('chat') || n.includes('completion')) return ChatBubbleLeftRightIcon;
                    if (n.includes('image')) return PhotoIcon;
                    if (n.includes('embed')) return DocumentTextIcon;
                    return BoltIcon;
                  };
                  const Icon = getServiceIcon(service.service_name || service.service);

                  return (
                    <div
                      key={idx}
                      className="bg-white/5 rounded-xl p-4 border border-white/10"
                    >
                      <Icon className="h-6 w-6 text-gray-400 mb-2" />
                      <p className="text-sm text-gray-400 truncate">
                        {service.service_name || service.service || 'API'}
                      </p>
                      <p className="text-lg font-semibold text-white">
                        {formatCredits(service.credits_used || service.total_credits || 0)}
                      </p>
                      <p className="text-xs text-gray-500">
                        {service.request_count || service.calls || 0} calls
                      </p>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <BoltIcon className="h-10 w-10 mx-auto mb-2 opacity-50" />
                <p>No service usage yet this period</p>
                <Link
                  to="/admin/account/api-keys"
                  className={`${glassStyles.button} mt-4 inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm`}
                >
                  Make Your First API Call
                </Link>
              </div>
            )}
          </motion.div>
        </div>

        {/* Right Column - Actions & Transactions */}
        <div className="space-y-6">
          {/* Quick Actions */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
            <h3 className="text-lg font-semibold text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <Link
                to="/admin/account/api-keys"
                className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10
                  border border-white/10 transition-colors group"
              >
                <KeyIcon className="h-5 w-5 text-purple-400 group-hover:text-purple-300" />
                <div>
                  <p className="text-sm font-medium text-white">Get API Key</p>
                  <p className="text-xs text-gray-500">Access the API programmatically</p>
                </div>
              </Link>

              <Link
                to="/admin/subscription/plan"
                className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10
                  border border-white/10 transition-colors group"
              >
                <ArrowUpCircleIcon className="h-5 w-5 text-green-400 group-hover:text-green-300" />
                <div>
                  <p className="text-sm font-medium text-white">Upgrade Plan</p>
                  <p className="text-xs text-gray-500">Get more credits & features</p>
                </div>
              </Link>

              <Link
                to="/admin/subscription/billing"
                className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10
                  border border-white/10 transition-colors group"
              >
                <DocumentTextIcon className="h-5 w-5 text-blue-400 group-hover:text-blue-300" />
                <div>
                  <p className="text-sm font-medium text-white">View Invoices</p>
                  <p className="text-xs text-gray-500">Billing history & receipts</p>
                </div>
              </Link>

              <Link
                to="/admin/subscription/payment"
                className="flex items-center gap-3 p-3 rounded-xl bg-white/5 hover:bg-white/10
                  border border-white/10 transition-colors group"
              >
                <CreditCardIcon className="h-5 w-5 text-yellow-400 group-hover:text-yellow-300" />
                <div>
                  <p className="text-sm font-medium text-white">Payment Methods</p>
                  <p className="text-xs text-gray-500">Manage your cards</p>
                </div>
              </Link>
            </div>
          </motion.div>

          {/* Recent Transactions */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">Recent Activity</h3>
              <Link
                to="/admin/credits"
                className="text-sm text-purple-400 hover:text-purple-300"
              >
                View All →
              </Link>
            </div>

            {recentTransactions.length > 0 ? (
              <div className="space-y-3">
                {recentTransactions.map((tx, idx) => {
                  const isDebit = tx.transaction_type === 'debit' || tx.amount < 0;
                  const amount = Math.abs(tx.amount);

                  return (
                    <div
                      key={tx.id || idx}
                      className="flex items-center justify-between py-2 border-b border-white/5 last:border-0"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                          isDebit ? 'bg-red-500/20' : 'bg-green-500/20'
                        }`}>
                          {isDebit ? (
                            <ChartBarIcon className="h-4 w-4 text-red-400" />
                          ) : (
                            <CurrencyDollarIcon className="h-4 w-4 text-green-400" />
                          )}
                        </div>
                        <div>
                          <p className="text-sm text-gray-300">
                            {tx.service || tx.model || tx.description || 'API Usage'}
                          </p>
                          <p className="text-xs text-gray-500">
                            {formatDate(tx.created_at)}
                          </p>
                        </div>
                      </div>
                      <span className={`text-sm font-medium ${
                        isDebit ? 'text-red-400' : 'text-green-400'
                      }`}>
                        {isDebit ? '-' : '+'}{formatCredits(amount)}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-6 text-gray-500">
                <ClockIcon className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No recent activity</p>
                <Link
                  to="/admin/account/api-keys"
                  className={`${glassStyles.button} mt-4 inline-flex items-center justify-center px-4 py-2 rounded-lg text-sm`}
                >
                  Generate an API Key
                </Link>
              </div>
            )}
          </motion.div>

          {/* Subscription Status */}
          {subscription && (
            <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6`}>
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <CalendarIcon className="h-5 w-5 text-blue-400" />
                Subscription
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Status</span>
                  <span className={`flex items-center gap-1 text-sm ${
                    subscription.status === 'active' ? 'text-green-400' : 'text-yellow-400'
                  }`}>
                    <CheckCircleIcon className="h-4 w-4" />
                    {subscription.status || 'Active'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-400">Plan</span>
                  <span className="text-sm text-white font-medium">
                    {formatTierName(subscription.plan_code)}
                  </span>
                </div>
                {subscription.current_period_end && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Renews</span>
                    <span className="text-sm text-gray-300">
                      {formatDate(subscription.current_period_end)}
                    </span>
                  </div>
                )}
                {subscription.amount && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-400">Amount</span>
                    <span className="text-sm text-white font-medium">
                      {formatCurrency(subscription.amount / 100)}/mo
                    </span>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Usage Warning */}
      <AnimatePresence>
        {usagePercent >= 75 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`mt-6 p-4 rounded-xl flex items-center gap-4 ${
              usagePercent >= 90
                ? 'bg-red-500/10 border border-red-500/30'
                : 'bg-yellow-500/10 border border-yellow-500/30'
            }`}
          >
            <ExclamationTriangleIcon className={`h-6 w-6 flex-shrink-0 ${
              usagePercent >= 90 ? 'text-red-400' : 'text-yellow-400'
            }`} />
            <div className="flex-1">
              <p className={`font-medium ${usagePercent >= 90 ? 'text-red-400' : 'text-yellow-400'}`}>
                {usagePercent >= 90 ? 'Credit limit almost reached!' : 'High usage warning'}
              </p>
              <p className="text-sm text-gray-400">
                You've used {usagePercent.toFixed(1)}% of your monthly credits.
                {usagePercent >= 90
                  ? ' Consider upgrading to avoid interruptions.'
                  : ' Consider upgrading if you need more.'}
              </p>
            </div>
            <Link
              to="/admin/subscription/plan"
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                usagePercent >= 90
                  ? 'bg-red-500 hover:bg-red-600 text-white'
                  : 'bg-yellow-500 hover:bg-yellow-600 text-black'
              }`}
            >
              Upgrade
            </Link>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
