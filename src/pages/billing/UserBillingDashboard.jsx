import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import {
  CreditCardIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  PlusIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';

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

export default function UserBillingDashboard() {
  const { theme, currentTheme } = useTheme();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [billingData, setBillingData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadUserBillingData();
  }, []);

  const loadUserBillingData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/org-billing/billing/user', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load billing data');
      }

      const data = await response.json();
      setBillingData(data);

      // Set default selected org to first one
      if (data.organizations && data.organizations.length > 0 && !selectedOrg) {
        setSelectedOrg(data.organizations[0]);
      }
    } catch (err) {
      console.error('Failed to load user billing:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadUserBillingData();
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

  const calculateUsagePercent = (used, allocated) => {
    if (!allocated || allocated === 0) return 0;
    return Math.min((used / allocated) * 100, 100);
  };

  const getUsageColor = (percent) => {
    if (percent >= 90) return 'text-red-400';
    if (percent >= 75) return 'text-yellow-400';
    return 'text-green-400';
  };

  const getUsageColorBg = (percent) => {
    if (percent >= 90) return 'from-red-500 to-red-600';
    if (percent >= 75) return 'from-yellow-500 to-orange-500';
    return 'from-green-500 to-emerald-500';
  };

  const getTotalCredits = () => {
    if (!billingData?.organizations) return 0;
    return billingData.organizations.reduce((sum, org) => sum + (org.allocated_credits || 0), 0);
  };

  const getTotalUsed = () => {
    if (!billingData?.organizations) return 0;
    return billingData.organizations.reduce((sum, org) => sum + (org.used_credits || 0), 0);
  };

  const handleSelectOrg = (org) => {
    setSelectedOrg(org);
    loadOrgUsageBreakdown(org.org_id);
  };

  const loadOrgUsageBreakdown = async (orgId) => {
    try {
      const response = await fetch(`/api/v1/org-billing/credits/${orgId}/usage`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        const usageData = await response.json();
        setSelectedOrg(prev => ({ ...prev, usageBreakdown: usageData }));
      }
    } catch (err) {
      console.error('Failed to load usage breakdown:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`${theme.card} rounded-xl p-8 max-w-md w-full m-4 text-center`}
        >
          <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
            <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
          </div>
          <h2 className={`text-2xl font-bold ${theme.text.primary} mb-2`}>Error Loading Data</h2>
          <p className={`${theme.text.secondary} mb-6`}>{error}</p>
          <button
            onClick={loadUserBillingData}
            className={`px-6 py-2 ${theme.button} rounded-lg transition-colors`}
          >
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-600 rounded-lg flex items-center justify-center shadow-lg">
                <CreditCardIcon className="h-6 w-6 text-white" />
              </div>
              My Credits & Billing
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>
              View your credit allocations across all organizations
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`p-2 ${theme.button} rounded-lg transition-colors`}
          >
            <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </motion.div>

      {/* Total Credits Summary */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Total Available Credits</h2>
          <span className={`text-sm ${theme.text.secondary}`}>
            Across {billingData?.organizations?.length || 0} {billingData?.organizations?.length === 1 ? 'organization' : 'organizations'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <div className={`text-sm ${theme.text.secondary} mb-1`}>Total Allocated</div>
            <div className={`text-3xl font-bold ${theme.text.primary}`}>
              {formatCredits(getTotalCredits())}
            </div>
            <div className={`text-xs ${theme.text.secondary} mt-1`}>credits</div>
          </div>

          <div>
            <div className={`text-sm ${theme.text.secondary} mb-1`}>Total Used</div>
            <div className={`text-3xl font-bold ${theme.text.accent}`}>
              {formatCredits(getTotalUsed())}
            </div>
            <div className={`text-xs ${theme.text.secondary} mt-1`}>credits</div>
          </div>

          <div>
            <div className={`text-sm ${theme.text.secondary} mb-1`}>Total Remaining</div>
            <div className={`text-3xl font-bold text-green-400`}>
              {formatCredits(getTotalCredits() - getTotalUsed())}
            </div>
            <div className={`text-xs ${theme.text.secondary} mt-1`}>credits</div>
          </div>
        </div>
      </motion.div>

      {/* Organization Selector */}
      {billingData?.organizations && billingData.organizations.length > 1 && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>Select Organization</h3>
          <div className="flex flex-wrap gap-3">
            {billingData.organizations.map((org) => (
              <button
                key={org.org_id}
                onClick={() => handleSelectOrg(org)}
                className={`px-4 py-2 rounded-lg transition-all ${
                  selectedOrg?.org_id === org.org_id
                    ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/50'
                    : `${currentTheme === 'light' ? 'bg-gray-200 text-gray-800' : 'bg-gray-800 text-gray-300'} hover:bg-purple-500/20`
                }`}
              >
                <div className="flex items-center gap-2">
                  <BuildingOfficeIcon className="h-5 w-5" />
                  {org.org_name}
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      )}

      {/* Selected Organization Details */}
      {selectedOrg && (
        <>
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className={`text-2xl font-bold ${theme.text.primary} flex items-center gap-3`}>
                  <BuildingOfficeIcon className="h-8 w-8 text-blue-500" />
                  {selectedOrg.org_name}
                </h2>
                <div className="flex items-center gap-3 mt-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    selectedOrg.subscription_plan === 'platform'
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : selectedOrg.subscription_plan === 'byok'
                      ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                      : 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                  }`}>
                    {selectedOrg.subscription_plan?.toUpperCase() || 'UNKNOWN'} Plan
                  </span>
                  <span className={`text-sm ${theme.text.secondary}`}>
                    {formatCurrency(selectedOrg.monthly_price)}/month
                  </span>
                  {selectedOrg.role === 'admin' && (
                    <span className="px-2 py-1 rounded-full text-xs bg-green-500/20 text-green-400 border border-green-500/30">
                      Admin
                    </span>
                  )}
                </div>
              </div>
              {selectedOrg.role === 'admin' && (
                <button
                  onClick={() => navigate(`/admin/organization/${selectedOrg.org_id}/billing`)}
                  className={`px-4 py-2 ${theme.button} rounded-lg transition-colors flex items-center gap-2`}
                >
                  Manage Billing
                  <ArrowRightIcon className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* Your Allocation */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Your Allocation</h3>
                <span className={`text-2xl font-bold ${theme.text.accent}`}>
                  {formatCredits(selectedOrg.allocated_credits)} credits
                </span>
              </div>

              <div className="mb-2">
                <div className="flex justify-between text-sm mb-1">
                  <span className={theme.text.secondary}>Used</span>
                  <span className={getUsageColor(calculateUsagePercent(selectedOrg.used_credits, selectedOrg.allocated_credits))}>
                    {formatCredits(selectedOrg.used_credits)} / {formatCredits(selectedOrg.allocated_credits)}
                    ({calculateUsagePercent(selectedOrg.used_credits, selectedOrg.allocated_credits).toFixed(1)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-700/30 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full bg-gradient-to-r ${getUsageColorBg(calculateUsagePercent(selectedOrg.used_credits, selectedOrg.allocated_credits))}`}
                    style={{ width: `${calculateUsagePercent(selectedOrg.used_credits, selectedOrg.allocated_credits)}%` }}
                  ></div>
                </div>
              </div>

              <div className="flex justify-between mt-3">
                <span className={`text-sm ${theme.text.secondary}`}>Remaining</span>
                <span className={`text-lg font-bold text-green-400`}>
                  {formatCredits(selectedOrg.remaining_credits)} credits
                </span>
              </div>
            </div>
          </motion.div>

          {/* Usage Breakdown */}
          {selectedOrg.usageBreakdown && (
            <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
              <div className="flex items-center gap-3 mb-6">
                <ChartBarIcon className="h-6 w-6 text-purple-500" />
                <h3 className={`text-xl font-semibold ${theme.text.primary}`}>Usage This Month</h3>
              </div>

              <div className="space-y-3">
                {selectedOrg.usageBreakdown.by_service && Object.entries(selectedOrg.usageBreakdown.by_service).map(([service, credits]) => (
                  <div
                    key={service}
                    className={`flex items-center justify-between p-3 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-sm">{service.charAt(0).toUpperCase()}</span>
                      </div>
                      <span className={`font-medium ${theme.text.primary}`}>
                        {service.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </span>
                    </div>
                    <span className={`text-lg font-bold ${theme.text.accent}`}>
                      {formatCredits(credits)} credits
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* View All Organizations Link */}
      {billingData?.organizations && billingData.organizations.length > 1 && (
        <motion.div variants={itemVariants} className="flex justify-center">
          <button
            onClick={() => navigate('/admin/organization/list')}
            className={`px-6 py-3 ${theme.button} rounded-lg transition-colors flex items-center gap-2`}
          >
            <BuildingOfficeIcon className="h-5 w-5" />
            View All Organizations
          </button>
        </motion.div>
      )}

      {/* Request More Credits */}
      {selectedOrg && calculateUsagePercent(selectedOrg.used_credits, selectedOrg.allocated_credits) > 80 && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-yellow-500/20`}>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-yellow-500/20 rounded-full flex items-center justify-center">
              <ExclamationTriangleIcon className="h-6 w-6 text-yellow-400" />
            </div>
            <div className="flex-1">
              <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Running Low on Credits</h3>
              <p className={`text-sm ${theme.text.secondary} mt-1`}>
                You've used {calculateUsagePercent(selectedOrg.used_credits, selectedOrg.allocated_credits).toFixed(1)}% of your allocated credits.
                Contact your organization admin to request more.
              </p>
            </div>
            <button
              className="px-4 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30 transition-colors whitespace-nowrap"
            >
              Request More
            </button>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
