import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  CreditCardIcon,
  UserGroupIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  BanknotesIcon,
  CalendarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
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

export default function OrganizationBilling() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg } = useOrganization();
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);

  // Billing data
  const [billing, setBilling] = useState({
    subscription: {
      plan: 'Professional',
      status: 'active',
      seats: 5,
      seatsUsed: 3,
      amount: 49.00,
      currency: 'USD',
      interval: 'month',
      nextBillingDate: '2025-11-13',
      cancelAtPeriodEnd: false
    },
    usage: {
      apiCalls: 8547,
      apiCallsLimit: 10000,
      storage: 2.4,
      storageLimit: 100,
      bandwidth: 45.6,
      bandwidthLimit: 1000
    },
    invoices: [],
    paymentMethod: {
      type: 'card',
      last4: '4242',
      brand: 'Visa',
      expiryMonth: '12',
      expiryYear: '2026'
    }
  });

  // Toast notification
  const [toast, setToast] = useState({
    show: false,
    message: '',
    type: 'success'
  });

  useEffect(() => {
    if (currentOrg) {
      fetchBillingData();
    }
    fetchCurrentUser();
  }, [currentOrg]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('/api/v1/user');
      if (!response.ok) throw new Error('Failed to fetch user');

      const data = await response.json();
      setCurrentUser(data);
    } catch (error) {
      console.error('Failed to fetch user:', error);
    }
  };

  const fetchBillingData = async () => {
    if (!currentOrg) return;

    setLoading(true);
    try {
      // Note: Organization billing endpoint might not exist yet in backend
      // This will need to be created or map to subscription API
      const response = await fetch(`/api/v1/org/${currentOrg.id}/billing`);
      if (!response.ok) throw new Error('Failed to fetch billing data');

      const data = await response.json();
      setBilling({ ...billing, ...data });
    } catch (error) {
      console.error('Failed to fetch billing:', error);
      showToast('Failed to load billing information', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type }), 5000);
  };

  const formatCurrency = (amount, currency = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getUsagePercentage = (used, limit) => {
    return (used / limit) * 100;
  };

  const getUsageColor = (percentage) => {
    if (percentage >= 90) return 'text-red-400';
    if (percentage >= 70) return 'text-yellow-400';
    return 'text-green-400';
  };

  const isOwner = currentUser?.org_role === 'owner';

  // Show access denied if not owner
  if (!loading && !isOwner) {
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
          <h2 className={`text-2xl font-bold ${theme.text.primary} mb-2`}>Access Denied</h2>
          <p className={`${theme.text.secondary} mb-6`}>
            Only organization owners can access billing information. Please contact your organization owner for billing-related inquiries.
          </p>
          <button
            onClick={() => window.history.back()}
            className={`px-6 py-2 ${theme.button} rounded-lg transition-colors`}
          >
            Go Back
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
      className="space-y-6"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                <CreditCardIcon className="h-6 w-6 text-white" />
              </div>
              Organization Billing
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>Manage your organization's subscription and billing</p>
          </div>
        </div>
      </motion.div>

      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <>
          {/* Subscription Overview */}
          <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Current Plan */}
            <div className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Current Plan</h3>
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                  billing.subscription.status === 'active'
                    ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                    : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                }`}>
                  {billing.subscription.status}
                </span>
              </div>
              <div className={`text-3xl font-bold ${theme.text.primary} mb-2`}>
                {billing.subscription.plan}
              </div>
              <div className={`text-2xl font-semibold ${theme.text.accent} mb-4`}>
                {formatCurrency(billing.subscription.amount)}
                <span className={`text-sm ${theme.text.secondary}`}>/{billing.subscription.interval}</span>
              </div>
              <button className={`w-full px-4 py-2 ${theme.button} rounded-lg transition-colors`}>
                Change Plan
              </button>
            </div>

            {/* Team Seats */}
            <div className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
              <div className="flex items-center gap-3 mb-4">
                <UserGroupIcon className="h-6 w-6 text-purple-500" />
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Team Seats</h3>
              </div>
              <div className="mb-4">
                <div className="flex justify-between mb-2">
                  <span className={`text-sm ${theme.text.secondary}`}>Seats Used</span>
                  <span className={`text-sm font-semibold ${theme.text.primary}`}>
                    {billing.subscription.seatsUsed} / {billing.subscription.seats}
                  </span>
                </div>
                <div className="w-full bg-gray-700/30 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-indigo-500"
                    style={{ width: `${(billing.subscription.seatsUsed / billing.subscription.seats) * 100}%` }}
                  ></div>
                </div>
              </div>
              <button className="w-full px-4 py-2 bg-purple-500/20 text-purple-400 rounded-lg hover:bg-purple-500/30 transition-colors">
                Add Seats
              </button>
            </div>

            {/* Next Billing */}
            <div className={`${theme.card} rounded-xl p-6 border border-green-500/20`}>
              <div className="flex items-center gap-3 mb-4">
                <CalendarIcon className="h-6 w-6 text-green-500" />
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Next Billing Date</h3>
              </div>
              <div className={`text-2xl font-bold ${theme.text.primary} mb-2`}>
                {formatDate(billing.subscription.nextBillingDate)}
              </div>
              <div className={`text-sm ${theme.text.secondary} mb-4`}>
                You will be charged {formatCurrency(billing.subscription.amount)}
              </div>
              {billing.subscription.cancelAtPeriodEnd && (
                <div className="flex items-center gap-2 px-3 py-2 bg-yellow-500/20 text-yellow-400 rounded-lg text-sm">
                  <ExclamationTriangleIcon className="h-4 w-4" />
                  Subscription will cancel on this date
                </div>
              )}
            </div>
          </motion.div>

          {/* Usage Statistics */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-6">
              <ChartBarIcon className="h-6 w-6 text-blue-500" />
              <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Usage Statistics</h2>
              <span className={`ml-auto text-sm ${theme.text.secondary}`}>Current billing period</span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* API Calls */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className={`text-sm ${theme.text.secondary}`}>API Calls</span>
                  <span className={`text-sm font-semibold ${getUsageColor(getUsagePercentage(billing.usage.apiCalls, billing.usage.apiCallsLimit))}`}>
                    {billing.usage.apiCalls.toLocaleString()} / {billing.usage.apiCallsLimit.toLocaleString()}
                  </span>
                </div>
                <div className="w-full bg-gray-700/30 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      getUsagePercentage(billing.usage.apiCalls, billing.usage.apiCallsLimit) >= 90
                        ? 'bg-gradient-to-r from-red-500 to-red-600'
                        : getUsagePercentage(billing.usage.apiCalls, billing.usage.apiCallsLimit) >= 70
                        ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                        : 'bg-gradient-to-r from-green-500 to-emerald-500'
                    }`}
                    style={{ width: `${getUsagePercentage(billing.usage.apiCalls, billing.usage.apiCallsLimit)}%` }}
                  ></div>
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  {(100 - getUsagePercentage(billing.usage.apiCalls, billing.usage.apiCallsLimit)).toFixed(1)}% remaining
                </div>
              </div>

              {/* Storage */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className={`text-sm ${theme.text.secondary}`}>Storage</span>
                  <span className={`text-sm font-semibold ${getUsageColor(getUsagePercentage(billing.usage.storage, billing.usage.storageLimit))}`}>
                    {billing.usage.storage} GB / {billing.usage.storageLimit} GB
                  </span>
                </div>
                <div className="w-full bg-gray-700/30 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      getUsagePercentage(billing.usage.storage, billing.usage.storageLimit) >= 90
                        ? 'bg-gradient-to-r from-red-500 to-red-600'
                        : getUsagePercentage(billing.usage.storage, billing.usage.storageLimit) >= 70
                        ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                        : 'bg-gradient-to-r from-blue-500 to-cyan-500'
                    }`}
                    style={{ width: `${getUsagePercentage(billing.usage.storage, billing.usage.storageLimit)}%` }}
                  ></div>
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  {(billing.usage.storageLimit - billing.usage.storage).toFixed(1)} GB remaining
                </div>
              </div>

              {/* Bandwidth */}
              <div>
                <div className="flex justify-between mb-2">
                  <span className={`text-sm ${theme.text.secondary}`}>Bandwidth</span>
                  <span className={`text-sm font-semibold ${getUsageColor(getUsagePercentage(billing.usage.bandwidth, billing.usage.bandwidthLimit))}`}>
                    {billing.usage.bandwidth} GB / {billing.usage.bandwidthLimit} GB
                  </span>
                </div>
                <div className="w-full bg-gray-700/30 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${
                      getUsagePercentage(billing.usage.bandwidth, billing.usage.bandwidthLimit) >= 90
                        ? 'bg-gradient-to-r from-red-500 to-red-600'
                        : getUsagePercentage(billing.usage.bandwidth, billing.usage.bandwidthLimit) >= 70
                        ? 'bg-gradient-to-r from-yellow-500 to-orange-500'
                        : 'bg-gradient-to-r from-purple-500 to-indigo-500'
                    }`}
                    style={{ width: `${getUsagePercentage(billing.usage.bandwidth, billing.usage.bandwidthLimit)}%` }}
                  ></div>
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  {(billing.usage.bandwidthLimit - billing.usage.bandwidth).toFixed(1)} GB remaining
                </div>
              </div>
            </div>
          </motion.div>

          {/* Payment Method */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <BanknotesIcon className="h-6 w-6 text-green-500" />
                <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Payment Method</h2>
              </div>
              <button className={`px-4 py-2 ${theme.button} rounded-lg transition-colors`}>
                Update Payment
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-16 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <CreditCardIcon className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <div className={`font-semibold ${theme.text.primary}`}>
                  {billing.paymentMethod.brand} •••• {billing.paymentMethod.last4}
                </div>
                <div className={`text-sm ${theme.text.secondary}`}>
                  Expires {billing.paymentMethod.expiryMonth}/{billing.paymentMethod.expiryYear}
                </div>
              </div>
            </div>
          </motion.div>

          {/* Invoice History */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <DocumentTextIcon className="h-6 w-6 text-purple-500" />
                <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Invoice History</h2>
              </div>
              <button className="text-blue-400 hover:text-blue-300 text-sm transition-colors">
                View All Invoices
              </button>
            </div>

            {billing.invoices && billing.invoices.length > 0 ? (
              <div className="space-y-3">
                {billing.invoices.map((invoice) => (
                  <div
                    key={invoice.id}
                    className={`flex items-center justify-between p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'} hover:bg-gray-700/50 transition-colors`}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        invoice.status === 'paid' ? 'bg-green-500/20' : 'bg-yellow-500/20'
                      }`}>
                        <DocumentTextIcon className={`h-5 w-5 ${
                          invoice.status === 'paid' ? 'text-green-400' : 'text-yellow-400'
                        }`} />
                      </div>
                      <div>
                        <div className={`font-medium ${theme.text.primary}`}>
                          Invoice #{invoice.number}
                        </div>
                        <div className={`text-sm ${theme.text.secondary}`}>
                          {formatDate(invoice.date)}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className={`font-semibold ${theme.text.primary}`}>
                          {formatCurrency(invoice.amount)}
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          invoice.status === 'paid'
                            ? 'bg-green-500/20 text-green-400'
                            : 'bg-yellow-500/20 text-yellow-400'
                        }`}>
                          {invoice.status}
                        </span>
                      </div>
                      <button className="px-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors text-sm">
                        Download
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <DocumentTextIcon className="h-16 w-16 mx-auto text-gray-500 mb-4" />
                <p className={`${theme.text.secondary}`}>No invoices yet</p>
              </div>
            )}
          </motion.div>

          {/* Danger Zone */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-red-500/20`}>
            <div className="flex items-center gap-3 mb-6">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />
              <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Danger Zone</h2>
            </div>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 border border-red-500/30 rounded-lg">
                <div>
                  <div className={`font-medium ${theme.text.primary}`}>Cancel Subscription</div>
                  <div className={`text-sm ${theme.text.secondary} mt-1`}>
                    Your subscription will remain active until the end of the current billing period
                  </div>
                </div>
                <button className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
                  Cancel Plan
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}

      {/* Toast Notification */}
      {toast.show && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-4 right-4 z-50"
        >
          <div className={`flex items-center gap-3 px-6 py-4 rounded-lg shadow-lg ${
            toast.type === 'success'
              ? 'bg-green-500/20 border border-green-500/30 text-green-400'
              : 'bg-red-500/20 border border-red-500/30 text-red-400'
          }`}>
            {toast.type === 'success' ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <XMarkIcon className="h-5 w-5" />
            )}
            <span>{toast.message}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
