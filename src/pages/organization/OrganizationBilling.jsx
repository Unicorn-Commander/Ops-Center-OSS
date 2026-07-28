import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  CreditCardIcon,
  UserGroupIcon,
  ChartBarIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  XMarkIcon,
  BanknotesIcon,
  CalendarIcon,
  ExclamationTriangleIcon
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
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [currentUser, setCurrentUser] = useState(null);

  // Billing data - starts empty; only ever populated from the real API.
  // (The old fabricated "Professional $49 / Visa •••• 4242" defaults are gone.)
  const [billing, setBilling] = useState(null);
  const [memberCount, setMemberCount] = useState(null);
  const [error, setError] = useState(null);
  const [portalLoading, setPortalLoading] = useState(false);

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
      const response = await fetch('/api/v1/auth/me', { credentials: 'include' });
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
    setError(null);
    try {
      // Real endpoint shape: { plan_tier, lago_customer_id, stripe_customer_id, status, created_at }
      const [billingRes, membersRes] = await Promise.all([
        fetch(`/api/v1/org/${currentOrg.id}/billing`, { credentials: 'include' }),
        fetch(`/api/v1/org/${currentOrg.id}/members?limit=1`, { credentials: 'include' })
      ]);

      if (!billingRes.ok) throw new Error('Failed to fetch billing data');
      const data = await billingRes.json();
      setBilling({
        planTier: data.plan_tier || null,
        status: data.status || null,
        stripeCustomerId: data.stripe_customer_id || null,
        createdAt: data.created_at || null,
        invoices: Array.isArray(data.invoices) ? data.invoices : []
      });

      if (membersRes.ok) {
        const membersData = await membersRes.json();
        setMemberCount(membersData.total ?? (membersData.members ? membersData.members.length : null));
      }
    } catch (error) {
      console.error('Failed to fetch billing:', error);
      setError('Failed to load billing information');
      setBilling(null);
    } finally {
      setLoading(false);
    }
  };

  // Opens the real Stripe customer portal for payment management
  const handleUpdatePayment = async () => {
    setPortalLoading(true);
    try {
      const res = await fetch('/api/v1/billing/portal/create', {
        method: 'POST',
        credentials: 'include'
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.portal_url) {
        throw new Error(data.detail || 'No billing portal available yet');
      }
      window.location.href = data.portal_url;
    } catch (err) {
      console.error('Failed to open billing portal:', err);
      showToast(err.message || 'Failed to open billing portal', 'error');
    } finally {
      setPortalLoading(false);
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
      ) : error ? (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-8 text-center border border-red-500/20`}>
          <ExclamationTriangleIcon className="h-10 w-10 text-red-400 mx-auto mb-3" />
          <p className={`${theme.text.primary} font-medium mb-1`}>{error}</p>
          <p className={`text-sm ${theme.text.secondary} mb-4`}>Billing details could not be loaded for this organization.</p>
          <button onClick={fetchBillingData} className={`px-6 py-2 ${theme.button} rounded-lg transition-colors`}>
            Try Again
          </button>
        </motion.div>
      ) : !billing ? (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-8 text-center`}>
          <CreditCardIcon className="h-10 w-10 text-gray-500 mx-auto mb-3" />
          <p className={`${theme.text.secondary}`}>No billing information available for this organization yet.</p>
        </motion.div>
      ) : (
        <>
          {/* Subscription Overview */}
          <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Current Plan */}
            <div className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
              <div className="flex items-center justify-between mb-4">
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Current Plan</h3>
                {billing.status && (
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    billing.status === 'active'
                      ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                      : 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
                  }`}>
                    {billing.status}
                  </span>
                )}
              </div>
              <div className={`text-3xl font-bold ${theme.text.primary} mb-2 capitalize`}>
                {billing.planTier || '—'}
              </div>
              <div className={`text-sm ${theme.text.secondary} mb-4`}>
                {/* Pricing is not exposed by the org billing API - never invent it */}
                Plan pricing is managed in the billing portal
              </div>
              <button onClick={() => navigate('/admin/subscription/plan')} className={`w-full px-4 py-2 ${theme.button} rounded-lg transition-colors`}>
                Change Plan
              </button>
            </div>

            {/* Team Seats */}
            <div className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
              <div className="flex items-center gap-3 mb-4">
                <UserGroupIcon className="h-6 w-6 text-purple-500" />
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Team Members</h3>
              </div>
              <div className="mb-4">
                <div className="flex justify-between mb-2">
                  <span className={`text-sm ${theme.text.secondary}`}>Members</span>
                  <span className={`text-sm font-semibold ${theme.text.primary}`}>
                    {memberCount != null ? memberCount : '—'}
                  </span>
                </div>
                <p className={`text-xs ${theme.text.secondary}`}>
                  Seat limits are not configured for this plan.
                </p>
              </div>
              <button
                disabled
                title="Not available yet"
                className="w-full px-4 py-2 bg-gray-600/30 text-gray-500 rounded-lg cursor-not-allowed"
              >
                Add Seats (not available yet)
              </button>
            </div>

            {/* Next Billing */}
            <div className={`${theme.card} rounded-xl p-6 border border-green-500/20`}>
              <div className="flex items-center gap-3 mb-4">
                <CalendarIcon className="h-6 w-6 text-green-500" />
                <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Next Billing Date</h3>
              </div>
              <div className={`text-2xl font-bold ${theme.text.primary} mb-2`}>—</div>
              <div className={`text-sm ${theme.text.secondary} mb-4`}>
                No billing date available. Upcoming charges appear once invoicing is active.
              </div>
            </div>
          </motion.div>

          {/* Usage Statistics - no per-org usage endpoint is wired yet */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center gap-3 mb-6">
              <ChartBarIcon className="h-6 w-6 text-blue-500" />
              <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Usage Statistics</h2>
              <span className={`ml-auto text-sm ${theme.text.secondary}`}>Current billing period</span>
            </div>
            <div className="py-8 text-center">
              <p className={`text-sm ${theme.text.secondary}`}>
                No usage data is available for this organization yet.
              </p>
            </div>
          </motion.div>

          {/* Payment Method - managed via the Stripe billing portal */}
          <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <BanknotesIcon className="h-6 w-6 text-green-500" />
                <h2 className={`text-xl font-semibold ${theme.text.primary}`}>Payment Method</h2>
              </div>
              <button
                onClick={handleUpdatePayment}
                disabled={portalLoading}
                className={`px-4 py-2 ${theme.button} rounded-lg transition-colors disabled:opacity-50`}
              >
                {portalLoading ? 'Opening portal…' : 'Update Payment'}
              </button>
            </div>

            <div className="flex items-center gap-4">
              <div className="w-16 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <CreditCardIcon className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <div className={`font-semibold ${theme.text.primary}`}>
                  {billing.stripeCustomerId ? 'Card on file with Stripe' : 'No payment method on file'}
                </div>
                <div className={`text-sm ${theme.text.secondary}`}>
                  {billing.stripeCustomerId
                    ? 'View or change card details in the billing portal.'
                    : 'Add one via "Update Payment" once billing is set up.'}
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
              <button onClick={() => navigate('/admin/subscription/billing')} className="text-blue-400 hover:text-blue-300 text-sm transition-colors">
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
                      {invoice.pdf_url ? (
                        <a
                          href={invoice.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-2 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 transition-colors text-sm"
                        >
                          Download
                        </a>
                      ) : (
                        <span className={`text-sm ${theme.text.secondary}`}>—</span>
                      )}
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
                <button onClick={() => navigate('/admin/subscription/cancel')} className="px-4 py-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30 transition-colors">
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
