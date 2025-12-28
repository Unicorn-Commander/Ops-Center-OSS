import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DocumentArrowDownIcon,
  ArrowPathIcon,
  CalendarIcon,
  CreditCardIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';

// Animation variants
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

// Status badge component
const StatusBadge = ({ status }) => {
  const colors = {
    paid: 'bg-green-500/20 text-green-400 border-green-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    draft: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    void: 'bg-slate-500/20 text-slate-400 border-slate-500/30'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${colors[status] || colors.pending}`}>
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
};

// Empty state component
const EmptyState = ({ theme }) => (
  <div className="text-center py-12">
    <DocumentArrowDownIcon className="w-16 h-16 mx-auto mb-4 text-slate-500" />
    <h3 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>No Invoices Yet</h3>
    <p className={`${theme.text.secondary}`}>Your invoice history will appear here once you have active charges</p>
  </div>
);

export default function SubscriptionBilling() {
  const { theme } = useTheme();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [invoices, setInvoices] = useState([]);
  const [billingCycle, setBillingCycle] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all'); // all, paid, pending, failed
  const [retryCount, setRetryCount] = useState({
    invoices: 0,
    cycle: 0,
    download: 0,
    retry: 0
  });
  const maxRetries = 3;

  useEffect(() => {
    loadBillingData();
  }, []);

  const loadBillingData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [invoicesRes, cycleRes] = await Promise.all([
        fetch('/api/v1/billing/invoices?limit=50'),
        fetch('/api/v1/billing/cycle')
      ]);

      // Handle invoices response
      if (invoicesRes.ok) {
        const data = await invoicesRes.json();
        setInvoices(data);
        setRetryCount(prev => ({ ...prev, invoices: 0 }));
      } else {
        const errorText = await invoicesRes.text();
        throw new Error(`Failed to load invoices: ${invoicesRes.status} ${errorText}`);
      }

      // Handle billing cycle response (non-critical)
      if (cycleRes.ok) {
        const data = await cycleRes.json();
        setBillingCycle(data);
        setRetryCount(prev => ({ ...prev, cycle: 0 }));
      } else {
        console.warn('Billing cycle data not available');
        // Don't set error for non-critical data
      }
    } catch (error) {
      console.error('Error loading billing data:', error);
      const errorMsg = error.message || 'Failed to load billing data';
      setError(errorMsg);

      // Retry logic for transient failures
      if (retryCount.invoices < maxRetries) {
        const delay = 2000 * (retryCount.invoices + 1); // Exponential backoff
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, invoices: prev.invoices + 1 }));
          loadBillingData();
        }, delay);
      } else {
        toast.error('Unable to load billing data. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setRetryCount({ invoices: 0, cycle: 0, download: 0, retry: 0 }); // Reset retry counters
    try {
      await loadBillingData();
      toast.success('Billing data refreshed successfully');
    } catch (error) {
      console.error('Error refreshing billing data:', error);
      toast.error('Failed to refresh billing data');
    } finally {
      setRefreshing(false);
    }
  };

  const handleDownloadInvoice = async (invoiceId) => {
    try {
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/pdf`);

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`HTTP ${res.status}: ${errorText || res.statusText}`);
      }

      const blob = await res.blob();

      // Verify blob has content
      if (blob.size === 0) {
        throw new Error('Invoice PDF is empty');
      }

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `invoice-${invoiceId}.pdf`;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 100);

      toast.success('Invoice downloaded successfully');
      setRetryCount(prev => ({ ...prev, download: 0 }));
    } catch (error) {
      console.error('Error downloading invoice:', error);
      const errorMsg = `Failed to download invoice: ${error.message}`;

      // Retry logic for download failures
      if (retryCount.download < maxRetries) {
        toast.warning(`Download failed. Retrying... (${retryCount.download + 1}/${maxRetries})`);
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, download: prev.download + 1 }));
          handleDownloadInvoice(invoiceId);
        }, 2000 * (retryCount.download + 1));
      } else {
        toast.error(errorMsg);
        setRetryCount(prev => ({ ...prev, download: 0 })); // Reset for next attempt
      }
    }
  };

  const handleRetryPayment = async (invoiceId) => {
    if (!confirm('Retry payment for this invoice? Your default payment method will be charged.')) {
      return;
    }

    try {
      const res = await fetch(`/api/v1/billing/invoices/${invoiceId}/retry`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `HTTP ${res.status}: ${res.statusText}`);
      }

      const result = await res.json();

      // Show success and reload data
      toast.success('Payment retry initiated successfully');
      await loadBillingData();
      setRetryCount(prev => ({ ...prev, retry: 0 }));
    } catch (error) {
      console.error('Error retrying payment:', error);
      const errorMsg = `Failed to retry payment: ${error.message}`;

      // Retry logic for payment failures
      if (retryCount.retry < maxRetries) {
        toast.warning(`Payment retry failed. Attempting again... (${retryCount.retry + 1}/${maxRetries})`);
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, retry: prev.retry + 1 }));
          handleRetryPayment(invoiceId);
        }, 2000 * (retryCount.retry + 1));
      } else {
        toast.error(errorMsg);
        setRetryCount(prev => ({ ...prev, retry: 0 })); // Reset for next attempt
      }
    }
  };

  // Filter invoices
  const filteredInvoices = invoices.filter((invoice) => {
    if (filter === 'all') return true;
    return invoice.status === filter;
  });

  // Calculate totals
  const totalPaid = invoices
    .filter((inv) => inv.status === 'paid')
    .reduce((sum, inv) => sum + inv.amount, 0);

  const totalPending = invoices
    .filter((inv) => inv.status === 'pending')
    .reduce((sum, inv) => sum + inv.amount, 0);

  const totalFailed = invoices
    .filter((inv) => inv.status === 'failed')
    .reduce((sum, inv) => sum + inv.amount, 0);

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-6 animate-pulse`}>
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
        <div className="h-64 bg-slate-700 rounded"></div>
      </div>
    );
  }

  if (error) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${theme.card} rounded-xl p-6 border border-red-500/30`}
      >
        <div className="flex items-start gap-3">
          <ExclamationTriangleIcon className="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className={`text-lg font-semibold mb-2 ${theme.text.primary}`}>
              Unable to Load Billing Data
            </h3>
            <p className={`text-sm mb-4 ${theme.text.secondary}`}>{error}</p>
            {retryCount.invoices > 0 && retryCount.invoices < maxRetries && (
              <p className="text-yellow-400 text-sm mb-4">
                Retrying... (Attempt {retryCount.invoices}/{maxRetries})
              </p>
            )}
            <button
              onClick={() => {
                setError(null);
                setRetryCount({ invoices: 0, cycle: 0, download: 0, retry: 0 });
                loadBillingData();
              }}
              className={`flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg text-sm transition-all`}
            >
              <ArrowPathIcon className="w-4 h-4" />
              Retry Now
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
          <DocumentArrowDownIcon className="w-5 h-5 text-blue-400" />
          Invoice History
        </h3>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className={`flex items-center gap-2 px-3 py-2 ${theme.button} rounded-lg text-sm transition-all disabled:opacity-50`}
        >
          <ArrowPathIcon className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Billing Cycle Info */}
      {billingCycle && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center gap-2 mb-2">
                <CalendarIcon className="w-5 h-5 text-purple-400" />
                <p className={`text-sm ${theme.text.secondary}`}>Current Billing Period</p>
              </div>
              <p className={`text-lg font-semibold ${theme.text.primary}`}>
                {formatDate(billingCycle.period_start)} - {formatDate(billingCycle.period_end)}
              </p>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <CreditCardIcon className="w-5 h-5 text-green-400" />
                <p className={`text-sm ${theme.text.secondary}`}>Next Billing Date</p>
              </div>
              <p className={`text-lg font-semibold ${theme.text.primary}`}>
                {formatDate(billingCycle.next_billing_date)}
              </p>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-2">
                <DocumentArrowDownIcon className="w-5 h-5 text-blue-400" />
                <p className={`text-sm ${theme.text.secondary}`}>Current Period Amount</p>
              </div>
              <p className={`text-lg font-semibold ${theme.text.primary}`}>
                {formatCurrency(billingCycle.current_amount)}
              </p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4`}>
          <p className={`text-sm ${theme.text.secondary} mb-1`}>Total Paid</p>
          <p className={`text-2xl font-bold text-green-400`}>{formatCurrency(totalPaid)}</p>
          <p className={`text-xs ${theme.text.secondary} mt-1`}>
            {invoices.filter((inv) => inv.status === 'paid').length} invoices
          </p>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4`}>
          <p className={`text-sm ${theme.text.secondary} mb-1`}>Pending</p>
          <p className={`text-2xl font-bold text-yellow-400`}>{formatCurrency(totalPending)}</p>
          <p className={`text-xs ${theme.text.secondary} mt-1`}>
            {invoices.filter((inv) => inv.status === 'pending').length} invoices
          </p>
        </motion.div>

        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4`}>
          <p className={`text-sm ${theme.text.secondary} mb-1`}>Failed</p>
          <p className={`text-2xl font-bold text-red-400`}>{formatCurrency(totalFailed)}</p>
          <p className={`text-xs ${theme.text.secondary} mt-1`}>
            {invoices.filter((inv) => inv.status === 'failed').length} invoices
          </p>
        </motion.div>
      </div>

      {/* Failed Invoices Warning */}
      {totalFailed > 0 && (
        <motion.div
          variants={itemVariants}
          className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 flex items-start gap-3"
        >
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className={`font-medium ${theme.text.primary} mb-1`}>Payment Failed</p>
            <p className={`text-sm ${theme.text.secondary}`}>
              You have {invoices.filter((inv) => inv.status === 'failed').length} failed payment(s).
              Please update your payment method or retry the payment.
            </p>
          </div>
        </motion.div>
      )}

      {/* Invoice Table */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        {/* Filter Tabs */}
        <div className="flex gap-2 mb-4">
          {['all', 'paid', 'pending', 'failed'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-purple-500 text-white'
                  : 'bg-slate-700/50 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>

        {filteredInvoices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Invoice #</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Date</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Description</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Amount</th>
                  <th className={`text-left py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Status</th>
                  <th className={`text-right py-3 px-4 text-sm font-medium ${theme.text.secondary}`}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredInvoices.map((invoice) => (
                  <tr key={invoice.id} className="border-b border-slate-800 hover:bg-slate-700/30 transition-colors">
                    <td className={`py-3 px-4 text-sm font-mono ${theme.text.primary}`}>
                      #{invoice.number || invoice.id.slice(0, 8)}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.primary}`}>
                      {formatDate(invoice.date)}
                    </td>
                    <td className={`py-3 px-4 text-sm ${theme.text.secondary}`}>
                      {invoice.description || 'Subscription payment'}
                    </td>
                    <td className={`py-3 px-4 text-sm font-medium ${theme.text.primary}`}>
                      {formatCurrency(invoice.amount)}
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={invoice.status} />
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {invoice.status === 'paid' && (
                          <button
                            onClick={() => handleDownloadInvoice(invoice.id)}
                            className="text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors"
                          >
                            <DocumentArrowDownIcon className="w-4 h-4 inline mr-1" />
                            PDF
                          </button>
                        )}
                        {invoice.status === 'failed' && (
                          <button
                            onClick={() => handleRetryPayment(invoice.id)}
                            className="text-green-400 hover:text-green-300 text-sm font-medium transition-colors"
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState theme={theme} />
        )}
      </motion.div>
    </div>
  );
}
