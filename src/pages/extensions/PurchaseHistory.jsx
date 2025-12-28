import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  DocumentTextIcon,
  FunnelIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useExtensions } from '../../contexts/ExtensionsContext';
import { getGlassmorphismStyles } from '../../styles/glassmorphism';
import { useToast } from '../../components/Toast';

// Status badge colors
const STATUS_COLORS = {
  completed: {
    bg: 'bg-green-500/20',
    text: 'text-green-400',
    icon: CheckCircleIcon
  },
  pending: {
    bg: 'bg-amber-500/20',
    text: 'text-amber-400',
    icon: ClockIcon
  },
  failed: {
    bg: 'bg-red-500/20',
    text: 'text-red-400',
    icon: XCircleIcon
  },
  refunded: {
    bg: 'bg-purple-500/20',
    text: 'text-purple-400',
    icon: ArrowPathIcon
  }
};

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

/**
 * Purchase History Component
 * Shows user's purchase history with filtering, search, and invoice download
 */
export default function PurchaseHistory() {
  const { theme, currentTheme } = useTheme();
  const { purchases, activeAddons, loadPurchases, loadActiveAddons, downloadInvoice, loading } = useExtensions();
  const toast = useToast();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  // Filter state
  const [filters, setFilters] = useState({
    status: 'all',
    search: '',
    from_date: '',
    to_date: ''
  });

  // Active tab: purchases vs active add-ons
  const [activeTab, setActiveTab] = useState('purchases'); // 'purchases' | 'active'

  // Load data on mount
  useEffect(() => {
    loadPurchases();
    loadActiveAddons();
  }, [loadPurchases, loadActiveAddons]);

  // Apply filters
  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    loadPurchases(newFilters);
  };

  const handleInvoiceDownload = async (purchase_id) => {
    await downloadInvoice(purchase_id);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Filter purchases by search
  const filteredPurchases = purchases.filter(purchase => {
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      return purchase.items?.some(item =>
        item.name.toLowerCase().includes(searchLower)
      );
    }
    return true;
  });

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-7xl mx-auto px-4 py-8 space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center gap-3 mb-2">
          <DocumentTextIcon className={`h-8 w-8 ${theme.text.accent}`} />
          <h1 className={`text-3xl font-bold ${theme.text.primary}`}>
            Purchase History
          </h1>
        </div>
        <p className={`${theme.text.secondary}`}>
          View your purchase history, active add-ons, and download invoices
        </p>
      </motion.div>

      {/* Tabs */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-xl p-2 flex gap-2`}>
        <button
          onClick={() => setActiveTab('purchases')}
          className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all ${
            activeTab === 'purchases'
              ? 'bg-gradient-to-r from-blue-500 to-cyan-500 text-white shadow-lg'
              : `${theme.text.secondary} hover:bg-white/10`
          }`}
        >
          Purchase History
        </button>
        <button
          onClick={() => setActiveTab('active')}
          className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-all ${
            activeTab === 'active'
              ? 'bg-gradient-to-r from-green-500 to-emerald-500 text-white shadow-lg'
              : `${theme.text.secondary} hover:bg-white/10`
          }`}
        >
          Active Add-ons ({activeAddons.length})
        </button>
      </motion.div>

      {/* Purchases Tab */}
      {activeTab === 'purchases' && (
        <>
          {/* Filters */}
          <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-xl p-6`}>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {/* Search */}
              <div className="md:col-span-2 relative">
                <MagnifyingGlassIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
                <input
                  type="text"
                  placeholder="Search add-ons..."
                  value={filters.search}
                  onChange={(e) => handleFilterChange('search', e.target.value)}
                  className={`w-full pl-10 pr-4 py-2 rounded-lg ${glassStyles.card} ${theme.text.primary} placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:outline-none`}
                />
              </div>

              {/* Status Filter */}
              <div className="relative">
                <FunnelIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
                <select
                  value={filters.status}
                  onChange={(e) => handleFilterChange('status', e.target.value)}
                  className={`w-full pl-10 pr-4 py-2 rounded-lg ${glassStyles.card} ${theme.text.primary} focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer`}
                >
                  <option value="all">All Status</option>
                  <option value="completed">Completed</option>
                  <option value="pending">Pending</option>
                  <option value="failed">Failed</option>
                  <option value="refunded">Refunded</option>
                </select>
              </div>

              {/* Export Button */}
              <button
                className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg ${glassStyles.card} hover:bg-white/10 ${theme.text.primary} font-semibold transition-all`}
              >
                <ArrowDownTrayIcon className="h-5 w-5" />
                <span>Export CSV</span>
              </button>
            </div>

            {/* Date Range */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <label className={`text-xs ${theme.text.secondary} mb-1 block`}>From Date</label>
                <input
                  type="date"
                  value={filters.from_date}
                  onChange={(e) => handleFilterChange('from_date', e.target.value)}
                  className={`w-full px-4 py-2 rounded-lg ${glassStyles.card} ${theme.text.primary} focus:ring-2 focus:ring-blue-500 focus:outline-none`}
                />
              </div>
              <div>
                <label className={`text-xs ${theme.text.secondary} mb-1 block`}>To Date</label>
                <input
                  type="date"
                  value={filters.to_date}
                  onChange={(e) => handleFilterChange('to_date', e.target.value)}
                  className={`w-full px-4 py-2 rounded-lg ${glassStyles.card} ${theme.text.primary} focus:ring-2 focus:ring-blue-500 focus:outline-none`}
                />
              </div>
            </div>
          </motion.div>

          {/* Purchase List */}
          <motion.div variants={itemVariants} className="space-y-4">
            {loading.purchases ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className={theme.text.secondary}>Loading purchases...</p>
              </div>
            ) : filteredPurchases.length === 0 ? (
              <div className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
                <DocumentTextIcon className={`h-16 w-16 ${theme.text.secondary} mx-auto mb-4 opacity-50`} />
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
                  No purchases found
                </h3>
                <p className={theme.text.secondary}>
                  You haven't made any purchases yet
                </p>
              </div>
            ) : (
              filteredPurchases.map((purchase, index) => {
                const statusConfig = STATUS_COLORS[purchase.status] || STATUS_COLORS.completed;
                const StatusIcon = statusConfig.icon;

                return (
                  <motion.div
                    key={purchase.id || index}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    className={`${glassStyles.card} rounded-xl p-6`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      {/* Purchase Info */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <span className={`px-3 py-1 rounded-lg ${statusConfig.bg} ${statusConfig.text} text-xs font-semibold uppercase flex items-center gap-1`}>
                            <StatusIcon className="h-4 w-4" />
                            {purchase.status}
                          </span>
                          <span className={`text-sm ${theme.text.secondary}`}>
                            {formatDate(purchase.created_at)}
                          </span>
                        </div>

                        {/* Items */}
                        <div className="space-y-2">
                          {purchase.items?.map((item, i) => (
                            <div key={i} className="flex items-center justify-between">
                              <span className={theme.text.primary}>{item.name}</span>
                              <span className={`font-semibold ${theme.text.primary}`}>
                                {formatCurrency(item.price)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Total & Actions */}
                      <div className="text-right space-y-3">
                        <div>
                          <p className={`text-sm ${theme.text.secondary}`}>Total</p>
                          <p className={`text-2xl font-bold ${theme.text.primary}`}>
                            {formatCurrency(purchase.total)}
                          </p>
                        </div>

                        <button
                          onClick={() => handleInvoiceDownload(purchase.id)}
                          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 text-white rounded-lg font-semibold transition-all shadow-lg text-sm"
                        >
                          <ArrowDownTrayIcon className="h-4 w-4" />
                          <span>Invoice</span>
                        </button>
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </motion.div>
        </>
      )}

      {/* Active Add-ons Tab */}
      {activeTab === 'active' && (
        <motion.div variants={itemVariants} className="space-y-4">
          {loading.activeAddons ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500 mx-auto mb-4"></div>
              <p className={theme.text.secondary}>Loading active add-ons...</p>
            </div>
          ) : activeAddons.length === 0 ? (
            <div className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
              <CheckCircleIcon className={`h-16 w-16 ${theme.text.secondary} mx-auto mb-4 opacity-50`} />
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
                No active add-ons
              </h3>
              <p className={theme.text.secondary}>
                You don't have any active add-ons yet
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {activeAddons.map((addon, index) => (
                <motion.div
                  key={addon.id || index}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className={`${glassStyles.card} rounded-xl p-6`}
                >
                  {/* Icon */}
                  <div className={`w-16 h-16 bg-gradient-to-br ${addon.iconColor || 'from-blue-500 to-cyan-500'} rounded-2xl flex items-center justify-center shadow-2xl mb-4`}>
                    {addon.icon && <addon.icon className="h-8 w-8 text-white" />}
                  </div>

                  {/* Name & Status */}
                  <h3 className={`text-lg font-bold ${theme.text.primary} mb-2`}>
                    {addon.name}
                  </h3>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className={theme.text.secondary}>Status</span>
                      <span className="px-2 py-1 rounded bg-green-500/20 text-green-400 text-xs font-semibold">
                        Active
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className={theme.text.secondary}>Billing</span>
                      <span className={theme.text.primary}>
                        {formatCurrency(addon.price)}/{addon.period}
                      </span>
                    </div>

                    {addon.expiration_date && (
                      <div className="flex items-center justify-between">
                        <span className={theme.text.secondary}>Renews</span>
                        <span className={theme.text.primary}>
                          {formatDate(addon.expiration_date)}
                        </span>
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </motion.div>
      )}
    </motion.div>
  );
}
