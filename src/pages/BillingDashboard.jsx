import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CreditCardIcon,
  BanknotesIcon,
  UsersIcon,
  ChartBarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  DocumentArrowDownIcon,
  PlusCircleIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
  ArrowPathIcon,
  FunnelIcon,
  EllipsisVerticalIcon,
  PauseIcon,
  PlayIcon,
  PencilIcon,
  EnvelopeIcon,
  ArrowUpTrayIcon,
  CalendarIcon,
  ReceiptRefundIcon,
  CheckIcon,
  XMarkIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import MuiTooltip from '@mui/material/Tooltip';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import {
  PieChart,
  Pie,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell
} from 'recharts';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
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

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

// Format date
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

// Tier badge component
const TierBadge = ({ tier }) => {
  const colors = {
    trial: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    starter: 'bg-green-500/20 text-green-400 border-green-500/30',
    professional: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    enterprise: 'bg-amber-500/20 text-amber-400 border-amber-500/30'
  };

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${colors[tier] || colors.trial}`}>
      {tier ? tier.charAt(0).toUpperCase() + tier.slice(1) : 'Unknown'}
    </span>
  );
};

// Status badge component
const StatusBadge = ({ status }) => {
  const colors = {
    active: 'bg-green-500/20 text-green-400 border-green-500/30',
    trialing: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    canceled: 'bg-red-500/20 text-red-400 border-red-500/30',
    past_due: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    paid: 'bg-green-500/20 text-green-400 border-green-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30'
  };

  // Null-safe status formatting
  const displayStatus = status ? status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ') : 'Pending';

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${colors[status] || colors.pending}`}>
      {displayStatus}
    </span>
  );
};

// Loading skeleton
const LoadingSkeleton = ({ theme }) => (
  <div className="space-y-6">
    {[1, 2, 3].map((i) => (
      <div key={i} className={`${theme.card} rounded-xl p-6 animate-pulse`}>
        <div className="h-4 bg-slate-700 rounded w-1/4 mb-4"></div>
        <div className="h-8 bg-slate-700 rounded w-1/2"></div>
      </div>
    ))}
  </div>
);

// Empty state component
const EmptyState = ({ icon: Icon, title, description, action, theme }) => (
  <div className={`${theme.card} rounded-xl p-12 text-center`}>
    <Icon className="w-16 h-16 mx-auto mb-4 text-slate-500" />
    <h3 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>{title}</h3>
    <p className={`${theme.text.secondary} mb-6`}>{description}</p>
    {action && action}
  </div>
);

// Confirmation Dialog Component
const ConfirmDialog = ({ isOpen, onClose, onConfirm, title, description, confirmText, confirmColor = 'red', theme }) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          className={`${theme.card} rounded-xl p-6 max-w-md w-full shadow-2xl border border-slate-700`}
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className={`text-xl font-bold mb-3 ${theme.text.primary}`}>{title}</h3>
          <p className={`${theme.text.secondary} mb-6`}>{description}</p>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                confirmColor === 'red'
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-purple-600 hover:bg-purple-700 text-white'
              }`}
            >
              {confirmText}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

// Toast Notification Component
const Toast = ({ message, type = 'success', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgColor = type === 'success' ? 'bg-green-600' : type === 'error' ? 'bg-red-600' : 'bg-blue-600';
  const Icon = type === 'success' ? CheckCircleIcon : type === 'error' ? XCircleIcon : ExclamationTriangleIcon;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className={`fixed top-4 right-4 z-50 ${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 max-w-md`}
    >
      <Icon className="w-6 h-6 flex-shrink-0" />
      <p className="flex-1">{message}</p>
      <button onClick={onClose} className="hover:bg-white/20 rounded p-1 transition-colors">
        <XMarkIcon className="w-5 h-5" />
      </button>
    </motion.div>
  );
};

// Action Menu Component
const ActionMenu = ({ isOpen, onClose, actions, theme }) => {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className={`absolute right-0 top-8 ${theme.card} rounded-lg shadow-xl border border-slate-700 py-2 min-w-48 z-10`}
      >
        {actions.map((action, index) => (
          <button
            key={index}
            onClick={() => {
              action.onClick();
              onClose();
            }}
            disabled={action.disabled}
            className={`w-full px-4 py-2 text-left text-sm flex items-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
              action.danger
                ? 'text-red-400 hover:bg-red-500/10'
                : `${theme.text.primary} hover:bg-slate-700/50`
            }`}
          >
            {action.icon && <action.icon className="w-4 h-4" />}
            {action.label}
          </button>
        ))}
      </motion.div>
    </AnimatePresence>
  );
};

// User View Component
const UserView = ({ theme }) => {
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [usage, setUsage] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadUserBillingData();
  }, []);

  const loadUserBillingData = async () => {
    setLoading(true);
    try {
      const [subRes, invRes, pmRes, usageRes, creditsRes] = await Promise.all([
        fetch('/api/v1/billing/subscription-status', { credentials: 'include' }), // Real: Stripe-backed tier/price/period
        fetch('/api/v1/billing/invoices?limit=10', { credentials: 'include' }),
        fetch('/api/v1/billing/payment-methods', { credentials: 'include' }),
        fetch('/api/v1/usage/current', { credentials: 'include' }), // Real: per-user API call usage
        fetch('/api/v1/credits/balance', { credentials: 'include' }) // Real: per-user credit balance
      ]);

      if (subRes.ok) {
        const subData = await subRes.json();
        const activeSub = subData.subscriptions?.[0];
        // Only render a subscription when one actually exists - otherwise the
        // honest "No Active Subscription" empty state shows.
        setSubscription(subData.has_subscription && activeSub ? {
          tier: (activeSub.tier_name && activeSub.tier_name !== 'unknown')
            ? activeSub.tier_name
            : subData.current_tier,
          price: activeSub.amount,
          status: activeSub.status || subData.status,
          next_billing_date: activeSub.current_period_end
        } : null);
      }
      if (invRes.ok) {
        const invData = await invRes.json();
        setInvoices(Array.isArray(invData) ? invData : (invData.invoices || []));
      }
      if (pmRes.ok) {
        const pmData = await pmRes.json();
        setPaymentMethods(Array.isArray(pmData) ? pmData : (pmData.payment_methods || []));
      }

      // Build usage from real per-user endpoints; leave fields unset (section
      // hidden / "0 of limit") rather than estimating anything.
      const usageData = {};
      if (usageRes.ok) {
        const result = await usageRes.json();
        const u = result?.data?.usage;
        if (u) {
          usageData.api_calls_used = u.used ?? 0;
          usageData.api_calls_limit = u.limit ?? 0;
        }
        if (result?.data?.reset?.date) usageData.reset_date = result.data.reset.date;
      }
      if (creditsRes.ok) {
        const credits = await creditsRes.json();
        if (credits && credits.balance != null) {
          usageData.credits_remaining = Number(credits.balance);
          usageData.credits_allocated = Number(credits.allocated_monthly ?? 0);
        }
      }
      setUsage(Object.keys(usageData).length > 0 ? usageData : null);
    } catch (error) {
      console.error('Error loading billing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadUserBillingData();
    setRefreshing(false);
  };

  if (loading) {
    return <LoadingSkeleton theme={theme} />;
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header with Refresh */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold ${theme.text.primary}`}>Billing & Subscription</h2>
          <p className={`${theme.text.secondary} text-sm mt-1`}>Manage your subscription and billing information</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className={`flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg transition-all disabled:opacity-50`}
        >
          <ArrowPathIcon className={`w-5 h-5 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Current Subscription */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
            <SparklesIcon className="w-5 h-5 text-purple-400" />
            Current Subscription
          </h3>
          {subscription && <TierBadge tier={subscription.tier} />}
        </div>

        {subscription ? (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Plan</p>
                <p className={`text-xl font-bold ${theme.text.primary}`}>
                  {subscription.tier ? subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1) : 'Unknown'}
                </p>
              </div>
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Price</p>
                <p className={`text-xl font-bold ${theme.text.primary}`}>
                  {formatCurrency(subscription.price)}/mo
                </p>
              </div>
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Status</p>
                <div className="mt-1">
                  <StatusBadge status={subscription.status} />
                </div>
              </div>
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>Next Billing Date</p>
                <p className={`text-sm font-medium ${theme.text.primary} mt-1`}>
                  {formatDate(subscription.next_billing_date)}
                </p>
              </div>
            </div>

            <div className="flex gap-3 pt-4 border-t border-slate-700">
              <button className={`flex-1 ${theme.button} rounded-lg py-2 px-4 text-sm font-medium`}>
                <ArrowUpIcon className="w-4 h-4 inline mr-2" />
                Upgrade Plan
              </button>
              <button className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-2 px-4 text-sm font-medium transition-colors">
                Change Plan
              </button>
            </div>
          </div>
        ) : (
          <EmptyState
            icon={CreditCardIcon}
            title="No Active Subscription"
            description="Start your subscription to access premium features"
            action={
              <button className={`${theme.button} rounded-lg py-2 px-6 text-sm font-medium`}>
                View Plans
              </button>
            }
            theme={theme}
          />
        )}
      </motion.div>

      {/* Usage Statistics */}
      {usage && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
            <ChartBarIcon className="w-5 h-5 text-cyan-400" />
            Usage Statistics
          </h3>

          <div className="space-y-4">
            {/* API Calls */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className={`text-sm ${theme.text.secondary}`}>
                  API Calls
                  <MuiTooltip title="Requests used this billing cycle against your plan's monthly quota; hitting the limit can pause access until reset or upgrade." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
                </span>
                <span className={`text-sm font-medium ${theme.text.primary}`}>
                  {(usage?.api_calls_used ?? 0).toLocaleString()} / {usage?.api_calls_limit === -1 ? '∞' : (usage?.api_calls_limit ?? 0).toLocaleString()}
                </span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all"
                  style={{
                    width: `${usage?.api_calls_limit === -1 ? 0 : Math.min(((usage?.api_calls_used ?? 0) / (usage?.api_calls_limit ?? 1)) * 100, 100)}%`
                  }}
                />
              </div>
              <p className={`text-xs ${theme.text.secondary} mt-1`}>
                {usage?.api_calls_limit === -1 ? 'Unlimited' : `${Math.round(((usage?.api_calls_used ?? 0) / (usage?.api_calls_limit ?? 1)) * 100)}% used`}
              </p>
            </div>

            {/* Credits - only rendered when the credits API returned a real balance */}
            {usage?.credits_remaining !== undefined && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-sm ${theme.text.secondary}`}>
                    Credits
                    <MuiTooltip title="Your prepaid usage pool (1 credit roughly equals $0.001 of API usage); metered services like LLM and image generation draw down this balance." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
                  </span>
                  <span className={`text-sm font-medium ${theme.text.primary}`}>
                    {(usage?.credits_remaining ?? 0).toLocaleString()} remaining
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-green-500 to-emerald-500 h-2 rounded-full transition-all"
                    style={{
                      width: `${Math.min(((usage?.credits_remaining ?? 0) / ((usage?.credits_allocated || 0) > 0 ? usage.credits_allocated : ((usage?.credits_remaining ?? 0) || 1))) * 100, 100)}%`
                    }}
                  />
                </div>
                <p className={`text-xs ${theme.text.secondary} mt-1`}>
                  {(usage?.credits_allocated ?? 0) > 0
                    ? `of ${usage.credits_allocated.toLocaleString()} monthly credits`
                    : 'No monthly credit allocation'}
                </p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Invoice History */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
          <DocumentArrowDownIcon className="w-5 h-5 text-blue-400" />
          Invoice History
        </h3>

        {invoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Date</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Amount</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Status</th>
                  <th className={`text-right py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {formatDate(invoice.issued_date || invoice.date)}
                    </td>
                    <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>
                      {formatCurrency(invoice.amount)}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={invoice.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      {invoice.pdf_url ? (
                        <a
                          href={invoice.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors"
                        >
                          <DocumentArrowDownIcon className="w-4 h-4 inline mr-1" />
                          Download PDF
                        </a>
                      ) : (
                        <span className={`text-sm ${theme.text.secondary}`}>—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={DocumentArrowDownIcon}
            title="No Invoices Yet"
            description="Your invoice history will appear here once you have active charges"
            theme={theme}
          />
        )}
      </motion.div>

      {/* Payment Methods */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
            <CreditCardIcon className="w-5 h-5 text-green-400" />
            Payment Methods
          </h3>
          <button className="flex items-center gap-2 text-sm font-medium text-purple-400 hover:text-purple-300 transition-colors">
            <PlusCircleIcon className="w-5 h-5" />
            Add Payment Method
          </button>
        </div>

        {paymentMethods.length > 0 ? (
          <div className="space-y-3">
            {paymentMethods.map((method) => (
              <div
                key={method.id}
                className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <CreditCardIcon className="w-8 h-8 text-slate-400" />
                  <div>
                    <p className={`font-medium ${theme.text.primary}`}>
                      {method.brand} •••• {method.last4}
                    </p>
                    <p className={`text-sm ${theme.text.secondary}`}>
                      Expires {method.exp_month}/{method.exp_year}
                    </p>
                  </div>
                  {method.is_default && (
                    <span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs font-medium rounded">
                      Default
                    </span>
                  )}
                </div>
                <button className="text-red-400 hover:text-red-300 transition-colors">
                  <TrashIcon className="w-5 h-5" />
                </button>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            icon={CreditCardIcon}
            title="No Payment Methods"
            description="Add a payment method to manage your subscription"
            action={
              <button className={`${theme.button} rounded-lg py-2 px-6 text-sm font-medium`}>
                <PlusCircleIcon className="w-4 h-4 inline mr-2" />
                Add Card
              </button>
            }
            theme={theme}
          />
        )}
      </motion.div>
    </motion.div>
  );
};

// Admin View Component
const AdminView = ({ theme }) => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [revenueChartData, setRevenueChartData] = useState([]);
  const [userGrowthData, setUserGrowthData] = useState([]);
  const [tierDistribution, setTierDistribution] = useState([]);
  const [recentPayments, setRecentPayments] = useState([]);
  const [failedPayments, setFailedPayments] = useState([]);
  const [upcomingRenewals, setUpcomingRenewals] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterTier, setFilterTier] = useState('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [chartPeriod, setChartPeriod] = useState('monthly');
  const [error, setError] = useState(null);
  const [selectedItems, setSelectedItems] = useState([]);
  const [toast, setToast] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({ isOpen: false });
  const [activeMenu, setActiveMenu] = useState(null);

  useEffect(() => {
    loadAdminData();
  }, []);

  useEffect(() => {
    loadChartData();
  }, [chartPeriod]);

  const loadAdminData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, usersRes, paymentsRes] = await Promise.all([
        // Real admin metrics: MRR/ARR/growth/churn/active subs from the DB
        fetch('/api/v1/billing/analytics/dashboard?days=30', { credentials: 'include' }),
        // Real tier distribution + trial-user count from Keycloak
        fetch('/api/v1/admin/users/analytics/summary', { credentials: 'include' }),
        // Real invoice list (Lago); failed payments are derived from it below
        fetch('/api/v1/billing/invoices?limit=20', { credentials: 'include' })
      ]);

      if (summaryRes.ok) {
        const data = await summaryRes.json();
        setStats(prev => ({
          ...(prev || {}),
          mrr: data.mrr,
          arr: data.arr,
          active_subscriptions: data.active_subscriptions?.total ?? 0,
          growth_rate: data.growth_rate,
          churn_rate: data.churn_rate
        }));
      } else {
        console.error('Billing analytics request failed:', summaryRes.status);
      }

      if (usersRes.ok) {
        const data = await usersRes.json();
        // Real shape: { total_users, active_users, tier_distribution: {trial, starter, professional, enterprise} }
        const tiers = data.tier_distribution || {};
        setTierDistribution([
          { name: 'Trial', value: tiers.trial || 0, color: '#3b82f6' },
          { name: 'Starter', value: tiers.starter || 0, color: '#10b981' },
          { name: 'Professional', value: tiers.professional || 0, color: '#8b5cf6' },
          { name: 'Enterprise', value: tiers.enterprise || 0, color: '#f59e0b' }
        ]);
        setStats(prev => ({ ...(prev || {}), trial_users: tiers.trial ?? null }));
      } else {
        console.error('User analytics request failed:', usersRes.status);
      }

      if (paymentsRes.ok) {
        const data = await paymentsRes.json();
        // Backend returns a bare array of invoices:
        // { id, invoice_number, amount, status, issued_date, pdf_url, ... }
        const invoiceList = Array.isArray(data) ? data : (data.payments || data.invoices || []);
        const payments = invoiceList.map(inv => ({
          invoice_id: inv.invoice_number || String(inv.id ?? ''),
          lago_id: inv.id || null, // Lago's internal invoice id — required by the retry/PDF endpoints
          date: inv.issued_date || inv.date,
          customer_email: inv.customer_email || null,
          plan_name: inv.plan_name || null,
          amount: inv.amount,
          status: inv.status,
          // Lago separates invoice lifecycle (status: draft/finalized/voided)
          // from payment state (payment_status: pending/succeeded/failed). Use
          // payment_status when the API provides it; fall back to status.
          payment_status: inv.payment_status || null,
          pdf_url: inv.pdf_url || null
        }));
        setRecentPayments(payments);
        // Derived from real data (the API has no ?status=failed filter)
        setFailedPayments(payments.filter(p => (p.payment_status || p.status) === 'failed'));
      } else {
        console.error('Payments request failed:', paymentsRes.status);
      }

      // No real "upcoming renewals" endpoint exists yet; the section stays
      // hidden rather than showing invented renewals.
      setUpcomingRenewals([]);
    } catch (error) {
      console.error('Error loading admin data:', error);
      setError('Failed to load billing data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadChartData = async () => {
    try {
      // Real DB-backed revenue trends (the old /api/v1/analytics/revenue/trends
      // and /api/v1/analytics/users/growth routes served fabricated data).
      const periodMap = { daily: 'day', weekly: 'week', monthly: 'month' };
      const period = periodMap[chartPeriod] || 'month';
      const revenueRes = await fetch(
        `/api/v1/billing/analytics/revenue/trends?period=${period}&limit=12`,
        { credentials: 'include' }
      );

      if (revenueRes.ok) {
        const data = await revenueRes.json();
        // Real shape: { period, data: [{ period, new_subscriptions, revenue }] }
        setRevenueChartData((data.data || []).map(item => ({
          name: String(item.period || '').slice(0, 10),
          revenue: item.revenue ?? 0
        })));
      } else {
        setRevenueChartData([]);
      }

      // There is no real signups-vs-cancellations time series endpoint yet, so
      // the User Growth & Churn chart shows an honest "Not enough data yet"
      // placeholder instead of an invented series.
      setUserGrowthData([]);
    } catch (error) {
      console.error('Error loading chart data:', error);
      setRevenueChartData([]);
      setUserGrowthData([]);
    }
  };

  // ============================================
  // Management Action Handlers
  // ============================================

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  const handleUpgradeSubscription = async (subscriptionId, newTier) => {
    try {
      const res = await fetch(`/api/v1/subscriptions/${subscriptionId}/upgrade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ new_tier: newTier })
      });

      if (res.ok) {
        showToast('Subscription upgraded successfully', 'success');
        loadAdminData();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to upgrade subscription', 'error');
      }
    } catch (error) {
      showToast('Network error upgrading subscription', 'error');
    }
  };

  const handleCancelSubscription = (subscriptionId, userEmail) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Cancel Subscription',
      description: `Are you sure you want to cancel the subscription for ${userEmail}? This action cannot be undone.`,
      confirmText: 'Cancel Subscription',
      confirmColor: 'red',
      onConfirm: async () => {
        try {
          const res = await fetch(`/api/v1/subscriptions/${subscriptionId}/cancel`, {
            method: 'POST',
            credentials: 'include'
          });

          if (res.ok) {
            showToast('Subscription cancelled successfully', 'success');
            loadAdminData();
          } else {
            const error = await res.json();
            showToast(error.detail || 'Failed to cancel subscription', 'error');
          }
        } catch (error) {
          showToast('Network error cancelling subscription', 'error');
        }
        setConfirmDialog({ isOpen: false });
      }
    });
  };

  // NOTE: subscription pause/resume is NOT offered in the UI. The billing
  // backend (Lago) has no native pause API — POST /api/v1/billing/
  // subscriptions/{id}/pause|resume exists but returns 501 with the reason.
  // These handlers stay unrendered until the billing stack supports a real
  // pause; wiring a button to a fake pause would be a lie to the admin.
  const handlePauseSubscription = async (subscriptionId) => {
    try {
      const res = await fetch(`/api/v1/billing/subscriptions/${subscriptionId}/pause`, {
        method: 'POST',
        credentials: 'include'
      });

      if (res.ok) {
        showToast('Subscription paused successfully', 'success');
        loadAdminData();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to pause subscription', 'error');
      }
    } catch (error) {
      showToast('Network error pausing subscription', 'error');
    }
  };

  const handleResumeSubscription = async (subscriptionId) => {
    try {
      const res = await fetch(`/api/v1/billing/subscriptions/${subscriptionId}/resume`, {
        method: 'POST',
        credentials: 'include'
      });

      if (res.ok) {
        showToast('Subscription resumed successfully', 'success');
        loadAdminData();
      } else {
        const error = await res.json();
        showToast(error.detail || 'Failed to resume subscription', 'error');
      }
    } catch (error) {
      showToast('Network error resuming subscription', 'error');
    }
  };

  const handleDownloadInvoice = async (invoiceId) => {
    try {
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/pdf`, {
        credentials: 'include'
      });

      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `invoice-${invoiceId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        showToast('Invoice downloaded successfully', 'success');
      } else {
        showToast('Failed to download invoice', 'error');
      }
    } catch (error) {
      showToast('Network error downloading invoice', 'error');
    }
  };

  const handleResendInvoice = async (invoiceId, userEmail) => {
    try {
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/resend`, {
        method: 'POST',
        credentials: 'include'
      });

      if (res.ok) {
        showToast(`Invoice resent to ${userEmail}`, 'success');
      } else {
        showToast('Failed to resend invoice', 'error');
      }
    } catch (error) {
      showToast('Network error resending invoice', 'error');
    }
  };

  const handleVoidInvoice = (invoiceId) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Void Invoice',
      description: 'Are you sure you want to void this invoice? This action cannot be undone.',
      confirmText: 'Void Invoice',
      confirmColor: 'red',
      onConfirm: async () => {
        try {
          const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/void`, {
            method: 'POST',
            credentials: 'include'
          });

          if (res.ok) {
            showToast('Invoice voided successfully', 'success');
            loadAdminData();
          } else {
            showToast('Failed to void invoice', 'error');
          }
        } catch (error) {
          showToast('Network error voiding invoice', 'error');
        }
        setConfirmDialog({ isOpen: false });
      }
    });
  };

  const handleRetryPayment = async (payment) => {
    // The retry endpoint is keyed by Lago's invoice id, not the display number
    const lagoId = payment.lago_id;
    if (!lagoId) {
      showToast('Cannot retry: no Lago invoice id for this payment', 'error');
      return;
    }
    try {
      const res = await fetch(`/api/v1/billing/invoices/${lagoId}/retry`, {
        method: 'POST',
        credentials: 'include'
      });

      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showToast(data.detail || 'Payment retry requested', 'success');
        loadAdminData();
      } else {
        showToast(data.detail || 'Failed to retry payment', 'error');
      }
    } catch (error) {
      showToast('Network error retrying payment', 'error');
    }
  };

  const handleRefundPayment = (paymentId, amount) => {
    setConfirmDialog({
      isOpen: true,
      title: 'Refund Payment',
      description: `Are you sure you want to refund ${formatCurrency(amount)}? This action cannot be undone.`,
      confirmText: 'Issue Refund',
      confirmColor: 'red',
      onConfirm: async () => {
        try {
          const res = await fetch(`/api/v1/billing/payments/${paymentId}/refund`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ reason: 'Customer request' })
          });

          if (res.ok) {
            showToast('Refund processed successfully', 'success');
            loadAdminData();
          } else {
            const error = await res.json();
            showToast(error.detail || 'Failed to process refund', 'error');
          }
        } catch (error) {
          showToast('Network error processing refund', 'error');
        }
        setConfirmDialog({ isOpen: false });
      }
    });
  };

  const handleBulkExport = () => {
    const csvData = filteredPayments.map(payment => ({
      Date: formatDate(payment.date),
      Customer: payment.customer_email,
      Plan: payment.plan_name,
      Amount: payment.amount,
      Status: payment.status,
      Invoice: payment.invoice_id || 'N/A'
    }));

    const headers = Object.keys(csvData[0]).join(',');
    const rows = csvData.map(obj => Object.values(obj).join(','));
    const csv = [headers, ...rows].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `billing-export-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
    showToast('Data exported successfully', 'success');
  };

  const handleSelectAll = () => {
    if (selectedItems.length === filteredPayments.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(filteredPayments.map(p => p.invoice_id));
    }
  };

  const toggleSelectItem = (invoiceId) => {
    if (selectedItems.includes(invoiceId)) {
      setSelectedItems(selectedItems.filter(id => id !== invoiceId));
    } else {
      setSelectedItems([...selectedItems, invoiceId]);
    }
  };

  if (loading) {
    return <LoadingSkeleton theme={theme} />;
  }

  // Chart colors
  const COLORS = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b'];

  // Filter recent payments with advanced filters
  const filteredPayments = recentPayments.filter((payment) => {
    // Search filter
    const matchesSearch = searchTerm === '' ||
      payment.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      payment.invoice_id?.toLowerCase().includes(searchTerm.toLowerCase());

    // Status filter
    const matchesStatus = filterStatus === 'all' || payment.status === filterStatus;

    // Tier filter
    const matchesTier = filterTier === 'all' || payment.plan_name?.toLowerCase().includes(filterTier);

    // Date range filter
    let matchesDateRange = true;
    if (dateRange.start && dateRange.end) {
      const paymentDate = new Date(payment.date);
      const startDate = new Date(dateRange.start);
      const endDate = new Date(dateRange.end);
      matchesDateRange = paymentDate >= startDate && paymentDate <= endDate;
    }

    return matchesSearch && matchesStatus && matchesTier && matchesDateRange;
  });

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-center gap-3">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0" />
          <p className="text-red-400 text-sm">{error}</p>
          <button
            onClick={loadAdminData}
            className="ml-auto text-red-400 hover:text-red-300 text-sm font-medium"
          >
            Retry
          </button>
        </div>
      )}

      {/* Toast Notifications */}
      <AnimatePresence>
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </AnimatePresence>

      {/* Confirmation Dialog */}
      <ConfirmDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog({ isOpen: false })}
        onConfirm={confirmDialog.onConfirm}
        title={confirmDialog.title}
        description={confirmDialog.description}
        confirmText={confirmDialog.confirmText}
        confirmColor={confirmDialog.confirmColor}
        theme={theme}
      />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className={`text-2xl font-bold ${theme.text.primary}`}>Admin Billing Dashboard</h2>
          <p className={`${theme.text.secondary} text-sm mt-1`}>Monitor revenue, subscriptions, and customer activity</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={chartPeriod}
            onChange={(e) => setChartPeriod(e.target.value)}
            className="px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:outline-none focus:border-purple-500 text-sm"
          >
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
          <button
            onClick={loadAdminData}
            className={`flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg transition-all`}
          >
            <ArrowPathIcon className="w-5 h-5" />
            Refresh
          </button>
        </div>
      </div>

      {/* Advanced Filters */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <div className="flex items-center gap-2 mb-4">
          <FunnelIcon className="w-5 h-5 text-purple-400" />
          <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Filters & Search</h3>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Search */}
          <div>
            <label className={`block text-sm ${theme.text.secondary} mb-2`}>Search</label>
            <div className="relative">
              <MagnifyingGlassIcon className="w-5 h-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Email or invoice ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm placeholder-slate-400 focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <label className={`block text-sm ${theme.text.secondary} mb-2`}>Status</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
            >
              <option value="all">All Statuses</option>
              <option value="paid">Paid</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="refunded">Refunded</option>
            </select>
          </div>

          {/* Tier Filter */}
          <div>
            <label className={`block text-sm ${theme.text.secondary} mb-2`}>
              Subscription Tier
              <MuiTooltip title="The plan level a customer is on (Trial, Starter, Professional, Enterprise), which sets their price and feature access." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
            </label>
            <select
              value={filterTier}
              onChange={(e) => setFilterTier(e.target.value)}
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
            >
              <option value="all">All Tiers</option>
              <option value="trial">Trial</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label className={`block text-sm ${theme.text.secondary} mb-2`}>Date Range</label>
            <div className="flex gap-2">
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
              />
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                className="flex-1 px-3 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:border-purple-500"
              />
            </div>
          </div>
        </div>

        {/* Active Filters Display */}
        {(searchTerm || filterStatus !== 'all' || filterTier !== 'all' || dateRange.start) && (
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-700">
            <p className={`text-sm ${theme.text.secondary}`}>Active filters:</p>
            {searchTerm && (
              <span className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-xs flex items-center gap-1">
                Search: {searchTerm}
                <button onClick={() => setSearchTerm('')} className="hover:bg-purple-500/30 rounded-full">
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            )}
            {filterStatus !== 'all' && (
              <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs flex items-center gap-1">
                Status: {filterStatus}
                <button onClick={() => setFilterStatus('all')} className="hover:bg-blue-500/30 rounded-full">
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            )}
            {filterTier !== 'all' && (
              <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-xs flex items-center gap-1">
                Tier: {filterTier}
                <button onClick={() => setFilterTier('all')} className="hover:bg-green-500/30 rounded-full">
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </span>
            )}
            <button
              onClick={() => {
                setSearchTerm('');
                setFilterStatus('all');
                setFilterTier('all');
                setDateRange({ start: '', end: '' });
              }}
              className="ml-auto text-sm text-red-400 hover:text-red-300 transition-colors"
            >
              Clear all filters
            </button>
          </div>
        )}
      </motion.div>

      {/* Revenue Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>
                Monthly Recurring Revenue
                <MuiTooltip title="Monthly Recurring Revenue: the predictable subscription revenue normalized to a monthly amount; the core SaaS growth metric." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
              </p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-2`}>
                {stats?.mrr != null ? formatCurrency(stats.mrr) : '—'}
              </p>
              <div className="flex items-center gap-1 mt-2 text-sm">
                <p className={`text-xs ${theme.text.secondary}`}>
                  ARR
                  <MuiTooltip title="Annual Recurring Revenue: MRR projected over a year (roughly MRR x 12); shows the run-rate value of active subscriptions." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
                  : {stats?.arr != null ? formatCurrency(stats.arr) : '—'}
                </p>
              </div>
            </div>
            <BanknotesIcon className="w-12 h-12 text-purple-400 opacity-20" />
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>
                Active Subscriptions
                <MuiTooltip title="Count of paying customers with a live subscription right now; the base that generates recurring revenue." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
              </p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-2`}>
                {stats?.active_subscriptions ?? '—'}
              </p>
              {/* Growth badge only when the API reports it - never an invented delta */}
              {stats?.growth_rate != null && (
                <div className="flex items-center gap-1 mt-2 text-sm">
                  {stats.growth_rate >= 0 ? (
                    <span className="text-green-400 flex items-center gap-1">
                      <ArrowUpIcon className="w-4 h-4" />
                      +{stats.growth_rate.toFixed(1)}% growth (30d)
                    </span>
                  ) : (
                    <span className="text-red-400 flex items-center gap-1">
                      <ArrowDownIcon className="w-4 h-4" />
                      {stats.growth_rate.toFixed(1)}% growth (30d)
                    </span>
                  )}
                </div>
              )}
            </div>
            <CheckCircleIcon className="w-12 h-12 text-green-400 opacity-20" />
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>
                Trial Users
                <MuiTooltip title="People currently on a free or trial plan who haven't paid yet; your pipeline of potential conversions to paid tiers." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
              </p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-2`}>
                {stats?.trial_users ?? '—'}
              </p>
              {/* No user-growth time series exists yet; show nothing rather than a fake delta */}
              {stats?.user_growth != null && (
                <div className="flex items-center gap-1 mt-2 text-sm">
                  {stats.user_growth >= 0 ? (
                    <span className="text-blue-400 flex items-center gap-1">
                      <ArrowUpIcon className="w-4 h-4" />
                      +{stats.user_growth.toFixed(1)}% growth
                    </span>
                  ) : (
                    <span className="text-red-400 flex items-center gap-1">
                      <ArrowDownIcon className="w-4 h-4" />
                      {stats.user_growth.toFixed(1)}% growth
                    </span>
                  )}
                </div>
              )}
            </div>
            <ClockIcon className="w-12 h-12 text-yellow-400 opacity-20" />
          </div>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>
                Churn Rate
                <MuiTooltip title="Share of customers who cancel in a given period; lower is better since churn directly erodes recurring revenue (under ~5% is healthy)." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
              </p>
              <p className={`text-3xl font-bold ${theme.text.primary} mt-2`}>
                {stats?.churn_rate != null ? `${stats.churn_rate.toFixed(1)}%` : '—'}
              </p>
              {stats?.churn_rate != null && (
                <div className="flex items-center gap-1 mt-2 text-sm">
                  {stats.churn_rate <= 5 ? (
                    <span className="text-green-400 flex items-center gap-1">
                      <CheckCircleIcon className="w-4 h-4" />
                      Healthy
                    </span>
                  ) : (
                    <span className="text-yellow-400 flex items-center gap-1">
                      <ExclamationTriangleIcon className="w-4 h-4" />
                      Monitor
                    </span>
                  )}
                </div>
              )}
            </div>
            <UsersIcon className="w-12 h-12 text-blue-400 opacity-20" />
          </div>
        </motion.div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Subscription Breakdown Pie Chart */}
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
            Subscription Tier Distribution
            <MuiTooltip title="How your customers are split across plan tiers (Trial, Starter, Professional, Enterprise); shows where revenue and upgrade potential concentrate." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
          </h3>
          {tierDistribution.some(t => t.value > 0) ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={tierDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {tierDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '0.5rem'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center">
              <p className={`text-sm ${theme.text.secondary}`}>No tier data yet</p>
            </div>
          )}
        </motion.div>

        {/* Revenue Chart */}
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>New-Subscription Revenue Over Time</h3>
          {revenueChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={revenueChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="name" stroke="#9ca3af" />
                <YAxis stroke="#9ca3af" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #334155',
                    borderRadius: '0.5rem'
                  }}
                  formatter={(value) => formatCurrency(value)}
                />
                <Legend />
                <Line type="monotone" dataKey="revenue" stroke="#8b5cf6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[300px] flex items-center justify-center">
              <p className={`text-sm ${theme.text.secondary}`}>Not enough data yet</p>
            </div>
          )}
        </motion.div>
      </div>

      {/* User Growth Chart */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
          User Growth & Churn
          <MuiTooltip title="New signups versus cancellations over time; when signups outpace cancellations the customer base (and recurring revenue) grows." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
        </h3>
        {userGrowthData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={userGrowthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9ca3af" />
              <YAxis stroke="#9ca3af" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #334155',
                  borderRadius: '0.5rem'
                }}
              />
              <Legend />
              <Bar dataKey="signups" fill="#10b981" name="New Signups" />
              <Bar dataKey="cancellations" fill="#ef4444" name="Cancellations" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center">
            <p className={`text-sm ${theme.text.secondary}`}>Not enough data yet — signup and cancellation history is not tracked</p>
          </div>
        )}
      </motion.div>

      {/* Recent Payments with Management */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
            <BanknotesIcon className="w-5 h-5 text-emerald-400" />
            Recent Payments
            <span className={`text-sm font-normal ${theme.text.secondary}`}>
              ({filteredPayments.length} {filteredPayments.length === 1 ? 'payment' : 'payments'})
            </span>
          </h3>
          <div className="flex items-center gap-2">
            {selectedItems.length > 0 && (
              <button
                onClick={handleBulkExport}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
              >
                <ArrowUpTrayIcon className="w-4 h-4" />
                Export Selected ({selectedItems.length})
              </button>
            )}
            <button
              onClick={handleBulkExport}
              className={`flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg text-sm font-medium`}
            >
              <ArrowUpTrayIcon className="w-4 h-4" />
              Export All
            </button>
          </div>
        </div>
        {filteredPayments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="py-3 px-4 text-left">
                    <input
                      type="checkbox"
                      checked={selectedItems.length === filteredPayments.length}
                      onChange={handleSelectAll}
                      className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-purple-600 focus:ring-purple-500"
                    />
                  </th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Date</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Customer</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Plan</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Amount</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Status</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Invoice</th>
                  <th className={`text-right py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredPayments.map((payment, index) => (
                  <tr key={payment.invoice_id || index} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                    <td className="py-3 px-4">
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(payment.invoice_id)}
                        onChange={() => toggleSelectItem(payment.invoice_id)}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-purple-600 focus:ring-purple-500"
                      />
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.secondary}`}>
                      {formatDate(payment.date)}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {payment.customer_email || '—'}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {payment.plan_name ? <TierBadge tier={payment.plan_name.toLowerCase()} /> : '—'}
                    </td>
                    <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>
                      {formatCurrency(payment.amount)}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={payment.status} />
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.secondary}`}>
                      {payment.invoice_id || 'N/A'}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="relative">
                        <button
                          onClick={() => setActiveMenu(activeMenu === payment.invoice_id ? null : payment.invoice_id)}
                          className="p-2 hover:bg-slate-700 rounded transition-colors"
                        >
                          <EllipsisVerticalIcon className="w-5 h-5 text-slate-400" />
                        </button>
                        {activeMenu === payment.invoice_id && (
                          <ActionMenu
                            isOpen={true}
                            onClose={() => setActiveMenu(null)}
                            theme={theme}
                            actions={[
                              {
                                label: 'Download PDF',
                                icon: DocumentArrowDownIcon,
                                onClick: () => handleDownloadInvoice(payment.invoice_id)
                              },
                              {
                                label: 'Resend Invoice',
                                icon: EnvelopeIcon,
                                onClick: () => handleResendInvoice(payment.invoice_id, payment.customer_email)
                              },
                              (payment.payment_status || payment.status) === 'failed' && {
                                label: 'Retry Payment',
                                icon: ArrowPathIcon,
                                disabled: !payment.lago_id,
                                onClick: () => handleRetryPayment(payment)
                              },
                              payment.status === 'paid' && {
                                label: 'Issue Refund',
                                icon: ReceiptRefundIcon,
                                onClick: () => handleRefundPayment(payment.invoice_id, payment.amount),
                                danger: true
                              },
                              {
                                label: 'Void Invoice',
                                icon: XCircleIcon,
                                onClick: () => handleVoidInvoice(payment.invoice_id),
                                danger: true
                              }
                            ].filter(Boolean)}
                          />
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={BanknotesIcon}
            title={searchTerm ? "No Matching Payments" : "No Recent Payments"}
            description={searchTerm ? "No payments match your search" : "Recent payment activity will appear here"}
            theme={theme}
          />
        )}
      </motion.div>

      {/* Failed Payments */}
      {failedPayments.length > 0 && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border-l-4 border-red-500`}>
          <div className="flex items-center gap-2 mb-4">
            <ExclamationTriangleIcon className="w-6 h-6 text-red-400" />
            <h3 className={`text-lg font-semibold ${theme.text.primary}`}>
              Failed Payments
              <MuiTooltip title="Charges that didn't go through (expired card, insufficient funds, etc.); unrecovered failures become involuntary churn and lost revenue." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
            </h3>
            <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs font-medium rounded">
              {failedPayments.length} requiring attention
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Date</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Customer</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Plan</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Amount</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Status</th>
                </tr>
              </thead>
              <tbody>
                {failedPayments.map((payment, index) => (
                  <tr key={payment.invoice_id || index} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                    <td className={`py-3 px-4 text-sm ${theme.text.secondary}`}>
                      {formatDate(payment.date)}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {payment.customer_email || '—'}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {payment.plan_name || '—'}
                    </td>
                    <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>
                      {formatCurrency(payment.amount)}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={payment.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Upcoming Renewals */}
      {upcomingRenewals.length > 0 && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border-l-4 border-blue-500`}>
          <div className="flex items-center gap-2 mb-4">
            <ClockIcon className="w-6 h-6 text-blue-400" />
            <h3 className={`text-lg font-semibold ${theme.text.primary}`}>
              Upcoming Renewals
              <MuiTooltip title="Subscriptions due to auto-renew and re-bill within the next 30 days; the recurring revenue you expect to collect soon." arrow><InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} /></MuiTooltip>
            </h3>
            <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs font-medium rounded">
              Next 30 days
            </span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Renewal Date</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Customer</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Plan</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Amount</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Days Until</th>
                </tr>
              </thead>
              <tbody>
                {upcomingRenewals.map((renewal, index) => (
                  <tr key={renewal.subscription_id || index} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                    <td className={`py-3 px-4 text-sm ${theme.text.secondary}`}>
                      {formatDate(renewal.renewal_date)}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {renewal.user_email}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {renewal.plan_name}
                    </td>
                    <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>
                      {formatCurrency(renewal.amount)}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.secondary}`}>
                      {renewal.days_until} days
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

// Main Component
export default function BillingDashboard() {
  const { theme } = useTheme();
  const [isAdmin, setIsAdmin] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkUserRole();
  }, []);

  const checkUserRole = async () => {
    try {
      const res = await fetch('/api/v1/auth/me', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setIsAdmin(data.is_admin || data.role === 'admin');
      }
    } catch (error) {
      console.error('Error checking user role:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {isAdmin ? <AdminView theme={theme} /> : <UserView theme={theme} />}
    </div>
  );
}
