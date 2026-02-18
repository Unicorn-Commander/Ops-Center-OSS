/**
 * BillingOverviewCard - Admin Dashboard billing and credits overview
 * Fetches data internally and displays platform credits balance, usage, and subscription tier
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  CreditCardIcon,
  BanknotesIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';

// Format credits with comma separators, no dollar sign
const formatCredits = (amount) => {
  if (amount === null || amount === undefined) return '0 credits';
  return `${Math.floor(parseFloat(amount)).toLocaleString()} credits`;
};

// Get usage bar color based on percentage
const getUsageBarColor = (percentage) => {
  if (percentage >= 80) return 'bg-red-500';
  if (percentage >= 50) return 'bg-yellow-500';
  return 'bg-green-500';
};

// Get usage text color based on percentage
const getUsageTextColor = (percentage) => {
  if (percentage >= 80) return 'text-red-400';
  if (percentage >= 50) return 'text-yellow-400';
  return 'text-green-400';
};

// Capitalize first letter of each word (handles underscore-separated tier names)
const capitalizeText = (str) => {
  if (!str) return '';
  return str.split('_').map(word =>
    word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
  ).join(' ');
};

// Low balance threshold (in credits)
const LOW_BALANCE_THRESHOLD = 1000;

// Tier display colors for badge
const TIER_COLORS = {
  trial: 'from-gray-500/20 to-gray-600/20 border-gray-500/30 text-gray-300',
  starter: 'from-blue-500/20 to-cyan-500/20 border-blue-500/30 text-blue-300',
  professional: 'from-purple-500/20 to-pink-500/20 border-purple-500/30 text-purple-300',
  enterprise: 'from-amber-500/20 to-orange-500/20 border-amber-500/30 text-amber-300',
  vip_founder: 'from-yellow-500/20 to-amber-500/20 border-yellow-500/30 text-yellow-300',
  byok: 'from-cyan-500/20 to-teal-500/20 border-cyan-500/30 text-cyan-300',
  managed: 'from-green-500/20 to-emerald-500/20 border-green-500/30 text-green-300',
  'n/a': 'from-gray-500/20 to-gray-600/20 border-gray-500/30 text-gray-400',
  unknown: 'from-gray-500/20 to-gray-600/20 border-gray-500/30 text-gray-400',
};

export default function BillingOverviewCard({
  glassStyles = {},
  className = ''
}) {
  const [billingData, setBillingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Normalize data from different API formats
  const normalizeData = useCallback((data, endpoint) => {
    // Handle different response structures based on endpoint
    if (endpoint.includes('dashboard')) {
      return {
        totalCredits: data.total_credits || data.totalCredits || data.balance || data.platform_balance || 0,
        usedCredits: data.used_credits || data.usedCredits || data.used || data.period_used || 0,
        tier: data.subscription_tier || data.tier || data.subscriptionTier || data.platform_tier || 'unknown',
        periodStart: data.period_start || data.periodStart || null,
        periodEnd: data.period_end || data.periodEnd || null
      };
    } else if (endpoint.includes('balance')) {
      return {
        totalCredits: data.balance || data.credits || data.total || 0,
        usedCredits: data.used || data.used_credits || 0,
        tier: data.tier || data.subscription_tier || 'unknown',
        periodStart: data.period_start || null,
        periodEnd: data.period_end || null
      };
    }

    // Generic fallback
    return {
      totalCredits: data.balance || data.total_credits || data.credits || 0,
      usedCredits: data.used || data.used_credits || 0,
      tier: data.tier || 'unknown',
      periodStart: null,
      periodEnd: null
    };
  }, []);

  // Fetch billing data from available endpoints
  const fetchBillingData = useCallback(async () => {
    setLoading(true);
    setError(null);

    // Try endpoints in order of preference
    // Note: /api/v1/credits/admin/stats was removed as it doesn't exist
    const endpoints = [
      '/api/v1/billing/analytics/dashboard',
      '/api/v1/credits/balance'
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await fetch(endpoint, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (response.ok) {
          const data = await response.json();

          // Normalize data from different endpoints
          const normalizedData = normalizeData(data, endpoint);
          setBillingData(normalizedData);
          setLastUpdated(new Date());
          setLoading(false);
          return;
        }
      } catch (err) {
        // Continue to next endpoint
        console.log(`Endpoint ${endpoint} failed:`, err.message);
      }
    }

    // All endpoints failed - show N/A state with graceful fallback
    console.debug('All billing endpoints unavailable - showing N/A state');
    setBillingData({
      totalCredits: 0,
      usedCredits: 0,
      tier: 'N/A',
      periodStart: null,
      periodEnd: null
    });
    setError(null); // Don't show error, just show N/A values
    setLoading(false);
  }, [normalizeData]);

  // Initial fetch and refresh interval
  useEffect(() => {
    fetchBillingData();

    // Refresh every 60 seconds
    const interval = setInterval(fetchBillingData, 60000);

    return () => clearInterval(interval);
  }, [fetchBillingData]);

  // Calculate usage percentage
  const usagePercentage = billingData
    ? Math.min(100, Math.round((billingData.usedCredits / Math.max(billingData.totalCredits, 1)) * 100))
    : 0;

  // Check for low balance
  const isLowBalance = billingData &&
    (billingData.totalCredits - billingData.usedCredits) < LOW_BALANCE_THRESHOLD;

  // Remaining credits
  const remainingCredits = billingData
    ? Math.max(0, billingData.totalCredits - billingData.usedCredits)
    : 0;

  // Get tier color classes
  const tierColorClasses = billingData?.tier
    ? TIER_COLORS[billingData.tier.toLowerCase()] || TIER_COLORS.trial
    : TIER_COLORS.trial;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg">
            <BanknotesIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Billing Overview</h3>
            <p className="text-sm text-gray-400">
              Platform credits & subscription
            </p>
          </div>
        </div>

        {/* Refresh button */}
        <button
          onClick={fetchBillingData}
          disabled={loading}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 transition-colors disabled:opacity-50"
          title="Refresh billing data"
        >
          <ArrowPathIcon className={`h-4 w-4 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Loading State */}
      {loading && !billingData && (
        <div className="space-y-4">
          <div className="h-8 bg-gray-700/30 rounded-lg animate-pulse" />
          <div className="h-4 bg-gray-700/30 rounded-lg animate-pulse w-3/4" />
          <div className="h-6 bg-gray-700/30 rounded-lg animate-pulse w-1/2" />
        </div>
      )}

      {/* Error State */}
      {error && !billingData && (
        <div className="text-center py-6">
          <CreditCardIcon className="h-10 w-10 mx-auto mb-2 text-gray-500 opacity-50" />
          <p className="text-sm text-gray-400">{error}</p>
          <p className="text-xs text-gray-500 mt-1">
            Check billing service connection
          </p>
        </div>
      )}

      {/* Content */}
      {billingData && (
        <div className="space-y-5">
          {/* Low Balance Warning */}
          {isLowBalance && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg"
            >
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 flex-shrink-0" />
              <div>
                <p className="text-sm text-yellow-300 font-medium">Low Balance Warning</p>
                <p className="text-xs text-yellow-400/70">
                  Credits below {formatCredits(LOW_BALANCE_THRESHOLD)}. Consider adding more.
                </p>
              </div>
            </motion.div>
          )}

          {/* Total Credits Balance */}
          <div>
            <p className="text-sm text-gray-400 mb-1">Total Platform Balance</p>
            <p className="text-3xl font-bold text-white">
              {formatCredits(billingData.totalCredits)}
            </p>
          </div>

          {/* Credits Used This Period */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-400">Used This Period</p>
              <p className={`text-sm font-medium ${getUsageTextColor(usagePercentage)}`}>
                {usagePercentage}%
              </p>
            </div>

            {/* Progress Bar */}
            <div className="h-2 bg-gray-700/50 rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${usagePercentage}%` }}
                transition={{ duration: 0.5, ease: 'easeOut' }}
                className={`h-full ${getUsageBarColor(usagePercentage)} rounded-full`}
              />
            </div>

            {/* Usage Details */}
            <div className="flex items-center justify-between mt-2">
              <p className="text-xs text-gray-500">
                {formatCredits(billingData.usedCredits)} used
              </p>
              <p className="text-xs text-gray-500">
                {formatCredits(remainingCredits)} remaining
              </p>
            </div>
          </div>

          {/* Subscription Tier */}
          <div className="flex items-center justify-between pt-3 border-t border-white/10">
            <p className="text-sm text-gray-400">Subscription Tier</p>
            <span className={`px-3 py-1 bg-gradient-to-r ${tierColorClasses} border rounded-full text-sm font-medium`}>
              {capitalizeText(billingData.tier)}
            </span>
          </div>

          {/* View Billing Dashboard Link */}
          <Link
            to="/admin/billing"
            className="flex items-center justify-center gap-2 w-full py-2.5 bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-300 rounded-lg text-sm font-medium hover:from-purple-500/30 hover:to-pink-500/30 transition-colors mt-2"
          >
            View Billing Dashboard
            <ArrowRightIcon className="h-4 w-4" />
          </Link>

          {/* Last Updated */}
          {lastUpdated && (
            <p className="text-xs text-gray-500 text-right">
              Updated {lastUpdated.toLocaleTimeString()}
            </p>
          )}
        </div>
      )}
    </motion.div>
  );
}
