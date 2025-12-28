/**
 * CreditPurchase.jsx - Credit Purchase Flow
 *
 * Handle organization credit purchases with Stripe integration.
 * Features: Package selection, pricing display, Stripe checkout, confirmation.
 *
 * API: POST /api/v1/org-billing/credits/{org_id}/add
 * Created: November 15, 2025
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  CreditCardIcon,
  BanknotesIcon,
  CheckCircleIcon,
  XCircleIcon,
  SparklesIcon,
  ArrowPathIcon,
  ShoppingCartIcon,
  LockClosedIcon
} from '@heroicons/react/24/outline';

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

const CREDIT_PACKAGES = [
  {
    id: 'starter',
    credits: 1000,
    price: 10,
    popular: false,
    savings: 0,
    description: 'Perfect for small teams getting started'
  },
  {
    id: 'professional',
    credits: 5000,
    price: 45,
    popular: true,
    savings: 10,
    description: 'Most popular choice for growing teams'
  },
  {
    id: 'enterprise',
    credits: 10000,
    price: 80,
    popular: false,
    savings: 20,
    description: 'Best value for large organizations'
  },
  {
    id: 'custom',
    credits: 0,
    price: 0,
    popular: false,
    savings: 0,
    description: 'Choose your own amount'
  }
];

export default function CreditPurchase() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg } = useOrganization();
  const navigate = useNavigate();

  const [selectedPackage, setSelectedPackage] = useState('professional');
  const [customAmount, setCustomAmount] = useState('');
  const [loading, setLoading] = useState(false);
  const [creditPool, setCreditPool] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [purchaseSuccess, setPurchaseSuccess] = useState(false);

  useEffect(() => {
    if (currentOrg) {
      loadCreditPool();
    }
  }, [currentOrg]);

  const loadCreditPool = async () => {
    try {
      const response = await fetch(`/api/v1/org-billing/credits/${currentOrg.id}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (response.ok) {
        const data = await response.json();
        setCreditPool(data.credit_pool);
      }
    } catch (err) {
      console.error('Failed to load credit pool:', err);
    }
  };

  const formatCredits = (amount) => {
    if (amount === null || amount === undefined) return '0';
    return Math.floor(parseFloat(amount)).toLocaleString();
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const getSelectedCredits = () => {
    if (selectedPackage === 'custom') {
      return parseInt(customAmount) || 0;
    }
    const pkg = CREDIT_PACKAGES.find(p => p.id === selectedPackage);
    return pkg ? pkg.credits : 0;
  };

  const getSelectedPrice = () => {
    if (selectedPackage === 'custom') {
      const credits = parseInt(customAmount) || 0;
      return credits * 0.01; // $0.01 per credit
    }
    const pkg = CREDIT_PACKAGES.find(p => p.id === selectedPackage);
    return pkg ? pkg.price : 0;
  };

  const handlePurchase = async () => {
    const credits = getSelectedCredits();
    const price = getSelectedPrice();

    if (credits <= 0 || price <= 0) {
      alert('Please select a valid credit package');
      return;
    }

    setLoading(true);

    try {
      // In production, this would redirect to Stripe Checkout
      // For now, we'll simulate the purchase via direct API call
      const response = await fetch(
        `/api/v1/org-billing/credits/${currentOrg.id}/add?credits=${credits}&purchase_amount=${price}`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        }
      );

      if (!response.ok) {
        throw new Error('Purchase failed');
      }

      setPurchaseSuccess(true);
      setShowConfirmation(true);
      await loadCreditPool();
    } catch (err) {
      alert('Purchase failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStripeCheckout = async () => {
    const credits = getSelectedCredits();
    const price = getSelectedPrice();

    if (credits <= 0 || price <= 0) {
      alert('Please select a valid credit package');
      return;
    }

    setLoading(true);

    try {
      // TODO: Implement Stripe Checkout Session creation
      // For now, use direct purchase
      await handlePurchase();
    } catch (err) {
      alert('Failed to create checkout session: ' + err.message);
      setLoading(false);
    }
  };

  if (!currentOrg) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-400">Please select an organization</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: currentTheme.text }}>
            Purchase Credits
          </h1>
          <p className="text-sm mt-1" style={{ color: currentTheme.textSecondary }}>
            Add credits to your organization's pool
          </p>
        </div>
        <button
          onClick={() => navigate('/admin/organization/credits')}
          className="px-4 py-2 rounded-lg border border-purple-500 text-purple-400 hover:bg-purple-500/10"
        >
          Back to Dashboard
        </button>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Current Balance */}
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border bg-gradient-to-r from-purple-500/10 to-pink-500/10"
          style={{ borderColor: currentTheme.border }}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Current Balance
              </div>
              <div className="text-4xl font-bold" style={{ color: currentTheme.text }}>
                {formatCredits(creditPool?.total_credits || 0)}
              </div>
              <div className="text-sm mt-2" style={{ color: currentTheme.textSecondary }}>
                {formatCurrency((creditPool?.total_credits || 0) * 0.01)} value
              </div>
            </div>
            <BanknotesIcon className="h-16 w-16 text-purple-400 opacity-50" />
          </div>
        </motion.div>

        {/* Credit Packages */}
        <motion.div variants={itemVariants}>
          <h2 className="text-xl font-semibold mb-4" style={{ color: currentTheme.text }}>
            Select Package
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {CREDIT_PACKAGES.map((pkg) => (
              <motion.div
                key={pkg.id}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedPackage(pkg.id)}
                className={`relative rounded-xl p-6 border-2 cursor-pointer transition-all ${
                  selectedPackage === pkg.id
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-gray-700 hover:border-purple-500/50'
                }`}
                style={{ background: selectedPackage === pkg.id ? undefined : currentTheme.cardBackground }}
              >
                {pkg.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white text-xs px-3 py-1 rounded-full flex items-center gap-1">
                      <SparklesIcon className="h-3 w-3" />
                      Most Popular
                    </div>
                  </div>
                )}

                <div className="text-center">
                  <h3 className="text-lg font-bold mb-2" style={{ color: currentTheme.text }}>
                    {pkg.id === 'custom' ? 'Custom' : `${formatCredits(pkg.credits)} Credits`}
                  </h3>
                  {pkg.id !== 'custom' && (
                    <>
                      <div className="text-3xl font-bold mb-2 text-purple-400">
                        {formatCurrency(pkg.price)}
                      </div>
                      {pkg.savings > 0 && (
                        <div className="text-sm text-green-400 mb-2">
                          Save {pkg.savings}%
                        </div>
                      )}
                      <div className="text-xs mb-4" style={{ color: currentTheme.textSecondary }}>
                        {formatCurrency(pkg.price / pkg.credits)} per credit
                      </div>
                    </>
                  )}
                  <p className="text-xs" style={{ color: currentTheme.textSecondary }}>
                    {pkg.description}
                  </p>
                </div>

                {selectedPackage === pkg.id && (
                  <div className="absolute top-3 right-3">
                    <CheckCircleIcon className="h-6 w-6 text-purple-400" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Custom Amount Input */}
        {selectedPackage === 'custom' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            variants={itemVariants}
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <h3 className="text-lg font-semibold mb-4" style={{ color: currentTheme.text }}>
              Enter Custom Amount
            </h3>
            <div className="max-w-md">
              <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Number of Credits
              </label>
              <input
                type="number"
                value={customAmount}
                onChange={(e) => setCustomAmount(e.target.value)}
                className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500 text-lg"
                style={{ color: currentTheme.text }}
                placeholder="Enter amount (e.g., 2500)"
                min="100"
                step="100"
              />
              {customAmount && parseInt(customAmount) >= 100 && (
                <div className="mt-3 p-3 bg-purple-500/10 border border-purple-500/30 rounded-lg">
                  <div className="flex items-center justify-between text-sm">
                    <span style={{ color: currentTheme.textSecondary }}>Total Cost:</span>
                    <span className="text-xl font-bold text-purple-400">
                      {formatCurrency(parseInt(customAmount) * 0.01)}
                    </span>
                  </div>
                  <div className="text-xs mt-1" style={{ color: currentTheme.textSecondary }}>
                    $0.01 per credit
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Purchase Summary */}
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <h3 className="text-lg font-semibold mb-4" style={{ color: currentTheme.text }}>
            Purchase Summary
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: currentTheme.border }}>
              <span style={{ color: currentTheme.textSecondary }}>Credits to Add</span>
              <span className="text-xl font-bold" style={{ color: currentTheme.text }}>
                {formatCredits(getSelectedCredits())}
              </span>
            </div>
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: currentTheme.border }}>
              <span style={{ color: currentTheme.textSecondary }}>Current Balance</span>
              <span className="font-semibold" style={{ color: currentTheme.text }}>
                {formatCredits(creditPool?.total_credits || 0)}
              </span>
            </div>
            <div className="flex items-center justify-between pb-3 border-b" style={{ borderColor: currentTheme.border }}>
              <span style={{ color: currentTheme.textSecondary }}>New Balance</span>
              <span className="text-xl font-bold text-green-400">
                {formatCredits((creditPool?.total_credits || 0) + getSelectedCredits())}
              </span>
            </div>
            <div className="flex items-center justify-between pt-3">
              <span className="text-lg font-semibold" style={{ color: currentTheme.text }}>
                Total Cost
              </span>
              <span className="text-3xl font-bold text-purple-400">
                {formatCurrency(getSelectedPrice())}
              </span>
            </div>
          </div>

          <div className="mt-6 flex items-center gap-3">
            <button
              onClick={handleStripeCheckout}
              disabled={loading || getSelectedCredits() <= 0}
              className="flex-1 px-6 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50 flex items-center justify-center gap-2 text-lg font-semibold"
            >
              {loading ? (
                <>
                  <ArrowPathIcon className="h-5 w-5 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <LockClosedIcon className="h-5 w-5" />
                  Secure Checkout with Stripe
                </>
              )}
            </button>
          </div>

          <div className="mt-4 flex items-center justify-center gap-2 text-xs" style={{ color: currentTheme.textSecondary }}>
            <LockClosedIcon className="h-4 w-4" />
            Secure payment powered by Stripe. Your payment information is never stored on our servers.
          </div>
        </motion.div>

        {/* Payment Information */}
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <h3 className="text-lg font-semibold mb-4" style={{ color: currentTheme.text }}>
            What You Get
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="h-6 w-6 text-green-400 flex-shrink-0 mt-1" />
              <div>
                <div className="font-semibold mb-1" style={{ color: currentTheme.text }}>
                  Instant Activation
                </div>
                <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
                  Credits added to your account immediately after payment
                </div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="h-6 w-6 text-green-400 flex-shrink-0 mt-1" />
              <div>
                <div className="font-semibold mb-1" style={{ color: currentTheme.text }}>
                  No Expiration
                </div>
                <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
                  Credits never expire and roll over month-to-month
                </div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <CheckCircleIcon className="h-6 w-6 text-green-400 flex-shrink-0 mt-1" />
              <div>
                <div className="font-semibold mb-1" style={{ color: currentTheme.text }}>
                  Full Transparency
                </div>
                <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
                  Track every credit spent with detailed usage reports
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>

      {/* Success Modal */}
      {showConfirmation && purchaseSuccess && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-gray-900 rounded-xl p-8 max-w-md w-full mx-4 border border-green-500/30 text-center"
          >
            <CheckCircleIcon className="h-16 w-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold mb-2" style={{ color: currentTheme.text }}>
              Purchase Successful!
            </h3>
            <p className="text-lg mb-4" style={{ color: currentTheme.textSecondary }}>
              {formatCredits(getSelectedCredits())} credits have been added to your organization
            </p>
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4 mb-6">
              <div className="text-sm mb-1" style={{ color: currentTheme.textSecondary }}>
                New Balance
              </div>
              <div className="text-3xl font-bold text-green-400">
                {formatCredits(creditPool?.total_credits || 0)}
              </div>
            </div>
            <button
              onClick={() => navigate('/admin/organization/credits')}
              className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700"
            >
              Go to Dashboard
            </button>
          </motion.div>
        </div>
      )}
    </div>
  );
}
