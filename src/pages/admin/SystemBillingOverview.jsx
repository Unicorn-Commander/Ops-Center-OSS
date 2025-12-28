import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';
import {
  ChartBarIcon,
  BuildingOfficeIcon,
  CurrencyDollarIcon,
  ArrowTrendingUpIcon,
  ArrowPathIcon,
  MagnifyingGlassIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  BanknotesIcon,
  UsersIcon
} from '@heroicons/react/24/outline';

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

export default function SystemBillingOverview() {
  const { theme, currentTheme } = useTheme();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [systemData, setSystemData] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterPlan, setFilterPlan] = useState('all');

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load system-wide billing data
      const [systemRes, orgsRes] = await Promise.all([
        fetch('/api/v1/org-billing/billing/system', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch('/api/v1/organizations', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        })
      ]);

      if (!systemRes.ok) throw new Error('Failed to load system billing data');

      const systemBilling = await systemRes.json();
      const orgsData = orgsRes.ok ? await orgsRes.json() : [];

      setSystemData(systemBilling);
      setOrganizations(orgsData);
    } catch (err) {
      console.error('Failed to load system billing:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadSystemData();
    setRefreshing(false);
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const formatCredits = (amount) => {
    if (amount === null || amount === undefined) return '0';
    return Math.floor(parseFloat(amount)).toLocaleString();
  };

  const formatLargeNumber = (num) => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const calculateMRR = () => {
    if (!organizations) return 0;
    return organizations.reduce((sum, org) => sum + (org.monthly_price || 0), 0);
  };

  const calculateARR = () => {
    return calculateMRR() * 12;
  };

  const getSubscriptionDistribution = () => {
    if (!organizations) return {};

    const dist = {
      platform: 0,
      byok: 0,
      hybrid: 0
    };

    organizations.forEach(org => {
      const plan = org.subscription_plan || 'platform';
      dist[plan] = (dist[plan] || 0) + 1;
    });

    return dist;
  };

  const filteredOrgs = organizations.filter(org => {
    const matchesSearch = !searchTerm ||
      org.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      org.display_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesPlan = filterPlan === 'all' || org.subscription_plan === filterPlan;

    return matchesSearch && matchesPlan;
  });

  const exportData = () => {
    // Create CSV export
    const headers = ['Organization', 'Plan', 'Credits', 'MRR', 'Members', 'Status'];
    const rows = filteredOrgs.map(org => [
      org.display_name || org.name,
      org.subscription_plan || 'platform',
      org.total_credits || 0,
      formatCurrency(org.monthly_price || 0),
      org.member_count || 0,
      org.status || 'active'
    ]);

    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'system-billing-export.csv';
    a.click();
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
            onClick={loadSystemData}
            className={`px-6 py-2 ${theme.button} rounded-lg transition-colors`}
          >
            Try Again
          </button>
        </motion.div>
      </div>
    );
  }

  const distribution = getSubscriptionDistribution();

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
              <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg">
                <ChartBarIcon className="h-6 w-6 text-white" />
              </div>
              System-Wide Billing Overview
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>
              Monitor revenue, organizations, and subscription analytics
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

      {/* Revenue Metrics */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className={`${theme.card} rounded-xl p-6 border border-green-500/20`}>
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${theme.text.secondary}`}>MRR</div>
            <CurrencyDollarIcon className="h-5 w-5 text-green-500" />
          </div>
          <div className={`text-3xl font-bold ${theme.text.primary}`}>
            {formatCurrency(systemData?.mrr || calculateMRR())}
          </div>
          <div className="flex items-center gap-1 mt-2 text-green-400 text-sm">
            <ArrowTrendingUpIcon className="h-4 w-4" />
            {systemData?.mrr_growth || '+15'}%
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${theme.text.secondary}`}>ARR</div>
            <CurrencyDollarIcon className="h-5 w-5 text-blue-500" />
          </div>
          <div className={`text-3xl font-bold ${theme.text.primary}`}>
            {formatCurrency(systemData?.arr || calculateARR())}
          </div>
          <div className="flex items-center gap-1 mt-2 text-blue-400 text-sm">
            <ArrowTrendingUpIcon className="h-4 w-4" />
            {systemData?.arr_growth || '+15'}%
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${theme.text.secondary}`}>Active Organizations</div>
            <BuildingOfficeIcon className="h-5 w-5 text-purple-500" />
          </div>
          <div className={`text-3xl font-bold ${theme.text.primary}`}>
            {systemData?.active_orgs || organizations.length}
          </div>
          <div className="flex items-center gap-1 mt-2 text-purple-400 text-sm">
            <ArrowTrendingUpIcon className="h-4 w-4" />
            {systemData?.org_growth || '+3'} this month
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-yellow-500/20`}>
          <div className="flex items-center justify-between mb-2">
            <div className={`text-sm ${theme.text.secondary}`}>Total Credits</div>
            <BanknotesIcon className="h-5 w-5 text-yellow-500" />
          </div>
          <div className={`text-3xl font-bold ${theme.text.primary}`}>
            {formatLargeNumber(systemData?.total_credits || 2300000)}
          </div>
          <div className="flex items-center gap-1 mt-2 text-yellow-400 text-sm">
            outstanding
          </div>
        </div>
      </motion.div>

      {/* Subscription Distribution */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h2 className={`text-xl font-semibold ${theme.text.primary} mb-6`}>Subscription Distribution</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className={`p-4 rounded-lg border ${currentTheme === 'light' ? 'bg-gray-100 border-gray-300' : 'bg-gray-800/50 border-gray-700'}`}>
            <div className="flex items-center justify-between mb-3">
              <span className={`text-lg font-semibold ${theme.text.primary}`}>Platform</span>
              <span className="px-3 py-1 rounded-full text-sm bg-blue-500/20 text-blue-400 border border-blue-500/30">
                {distribution.platform || 0} orgs
              </span>
            </div>
            <div className={`text-2xl font-bold ${theme.text.accent} mb-2`}>
              {distribution.platform ? ((distribution.platform / organizations.length) * 100).toFixed(0) : 0}%
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-blue-600"
                style={{ width: `${distribution.platform ? (distribution.platform / organizations.length) * 100 : 0}%` }}
              ></div>
            </div>
          </div>

          <div className={`p-4 rounded-lg border ${currentTheme === 'light' ? 'bg-gray-100 border-gray-300' : 'bg-gray-800/50 border-gray-700'}`}>
            <div className="flex items-center justify-between mb-3">
              <span className={`text-lg font-semibold ${theme.text.primary}`}>BYOK</span>
              <span className="px-3 py-1 rounded-full text-sm bg-purple-500/20 text-purple-400 border border-purple-500/30">
                {distribution.byok || 0} orgs
              </span>
            </div>
            <div className={`text-2xl font-bold ${theme.text.accent} mb-2`}>
              {distribution.byok ? ((distribution.byok / organizations.length) * 100).toFixed(0) : 0}%
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-purple-600"
                style={{ width: `${distribution.byok ? (distribution.byok / organizations.length) * 100 : 0}%` }}
              ></div>
            </div>
          </div>

          <div className={`p-4 rounded-lg border ${currentTheme === 'light' ? 'bg-gray-100 border-gray-300' : 'bg-gray-800/50 border-gray-700'}`}>
            <div className="flex items-center justify-between mb-3">
              <span className={`text-lg font-semibold ${theme.text.primary}`}>Hybrid</span>
              <span className="px-3 py-1 rounded-full text-sm bg-gold-500/20 text-gold-400 border border-gold-500/30">
                {distribution.hybrid || 0} orgs
              </span>
            </div>
            <div className={`text-2xl font-bold ${theme.text.accent} mb-2`}>
              {distribution.hybrid ? ((distribution.hybrid / organizations.length) * 100).toFixed(0) : 0}%
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-2">
              <div
                className="h-2 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500"
                style={{ width: `${distribution.hybrid ? (distribution.hybrid / organizations.length) * 100 : 0}%` }}
              ></div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Organizations List */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Organizations</h2>
          <div className="flex items-center gap-3">
            <div className="relative">
              <MagnifyingGlassIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
              <input
                type="text"
                placeholder="Search organizations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className={`pl-10 pr-4 py-2 rounded-lg ${currentTheme === 'light' ? 'bg-gray-200 text-gray-800' : 'bg-gray-800 text-white'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
              />
            </div>
            <select
              value={filterPlan}
              onChange={(e) => setFilterPlan(e.target.value)}
              className={`px-4 py-2 rounded-lg ${currentTheme === 'light' ? 'bg-gray-200 text-gray-800' : 'bg-gray-800 text-white'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
            >
              <option value="all">All Plans</option>
              <option value="platform">Platform</option>
              <option value="byok">BYOK</option>
              <option value="hybrid">Hybrid</option>
            </select>
            <button
              onClick={exportData}
              className={`px-4 py-2 ${theme.button} rounded-lg transition-colors flex items-center gap-2`}
            >
              <ArrowDownTrayIcon className="h-5 w-5" />
              Export
            </button>
          </div>
        </div>

        {filteredOrgs.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className={`border-b ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-700'}`}>
                  <th className={`text-left py-3 px-4 ${theme.text.secondary} font-medium`}>Organization</th>
                  <th className={`text-center py-3 px-4 ${theme.text.secondary} font-medium`}>Plan</th>
                  <th className={`text-right py-3 px-4 ${theme.text.secondary} font-medium`}>Credits</th>
                  <th className={`text-right py-3 px-4 ${theme.text.secondary} font-medium`}>MRR</th>
                  <th className={`text-center py-3 px-4 ${theme.text.secondary} font-medium`}>Members</th>
                  <th className={`text-center py-3 px-4 ${theme.text.secondary} font-medium`}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrgs.map((org) => (
                  <tr
                    key={org.id}
                    className={`border-b ${currentTheme === 'light' ? 'border-gray-200' : 'border-gray-800'} hover:bg-gray-800/30 transition-colors cursor-pointer`}
                    onClick={() => navigate(`/admin/organization/${org.id}/billing`)}
                  >
                    <td className="py-3 px-4">
                      <div className={`font-medium ${theme.text.primary}`}>
                        {org.display_name || org.name}
                      </div>
                      <div className={`text-xs ${theme.text.secondary}`}>
                        {org.name}
                      </div>
                    </td>
                    <td className="text-center py-3 px-4">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                        org.subscription_plan === 'platform'
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : org.subscription_plan === 'byok'
                          ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                          : 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                      }`}>
                        {(org.subscription_plan || 'platform').toUpperCase()}
                      </span>
                    </td>
                    <td className={`text-right py-3 px-4 font-semibold ${theme.text.primary}`}>
                      {formatCredits(org.total_credits || 0)}
                    </td>
                    <td className={`text-right py-3 px-4 font-semibold ${theme.text.accent}`}>
                      {formatCurrency(org.monthly_price || 0)}
                    </td>
                    <td className="text-center py-3 px-4">
                      <div className="flex items-center justify-center gap-1">
                        <UsersIcon className="h-4 w-4 text-gray-500" />
                        <span className={theme.text.primary}>{org.member_count || 0}</span>
                      </div>
                    </td>
                    <td className="text-center py-3 px-4">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/admin/organization/${org.id}/billing`);
                        }}
                        className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <BuildingOfficeIcon className="h-16 w-16 mx-auto text-gray-500 mb-4" />
            <p className={`${theme.text.secondary}`}>No organizations found</p>
          </div>
        )}
      </motion.div>

      {/* Top 10 Organizations by Usage */}
      {systemData?.top_orgs && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h2 className={`text-xl font-semibold ${theme.text.primary} mb-6 flex items-center gap-3`}>
            <ChartBarIcon className="h-6 w-6 text-green-500" />
            Top 10 Organizations by Usage
          </h2>

          <div className="space-y-3">
            {systemData.top_orgs.map((org, index) => (
              <div
                key={org.org_id}
                className={`flex items-center justify-between p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'} hover:bg-gray-700/50 transition-colors`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                    index === 0 ? 'bg-gold-500/20' : index === 1 ? 'bg-silver-500/20' : index === 2 ? 'bg-bronze-500/20' : 'bg-gray-700/50'
                  }`}>
                    <span className={`font-bold ${theme.text.primary}`}>#{index + 1}</span>
                  </div>
                  <div>
                    <div className={`font-medium ${theme.text.primary}`}>
                      {org.org_name}
                    </div>
                    <div className={`text-sm ${theme.text.secondary}`}>
                      {org.subscription_plan?.toUpperCase() || 'PLATFORM'} Plan
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${theme.text.accent}`}>
                    {formatCredits(org.credits_used)} credits
                  </div>
                  <div className={`text-sm ${theme.text.secondary}`}>
                    this month
                  </div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
