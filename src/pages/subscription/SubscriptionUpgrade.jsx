import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  SparklesIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowRightIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  BoltIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import { useNavigate } from 'react-router-dom';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.4 }
  }
};

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 2
  }).format(amount);
};

// Calculate savings for annual billing
const calculateAnnualSavings = (monthly, annual) => {
  const monthlyTotal = monthly * 12;
  const savings = monthlyTotal - annual;
  const percentage = Math.round((savings / monthlyTotal) * 100);
  return { amount: savings, percentage };
};

// Tier badge component
const TierBadge = ({ tier, isCurrentPlan, isPopular }) => {
  const colors = {
    trial: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
    starter: 'bg-green-500/20 text-green-400 border-green-500/40',
    professional: 'bg-purple-500/20 text-purple-400 border-purple-500/40',
    'founders-friend': 'bg-gradient-to-r from-purple-500/20 to-amber-500/20 text-amber-400 border-amber-500/40',
    enterprise: 'bg-amber-500/20 text-amber-400 border-amber-500/40'
  };

  if (isCurrentPlan) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/20 text-blue-400 border border-blue-500/40">
        <CheckCircleIcon className="w-4 h-4" />
        Current Plan
      </div>
    );
  }

  if (isPopular) {
    return (
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r from-purple-600 to-pink-600 text-white">
        <SparklesIcon className="w-4 h-4" />
        Most Popular
      </div>
    );
  }

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${colors[tier] || colors.trial}`}>
      {tier ? tier.charAt(0).toUpperCase() + tier.slice(1).replace(/[-_]/g, ' ') : 'Plan'}
    </span>
  );
};

export default function SubscriptionUpgrade() {
  const { theme } = useTheme();
  const toast = useToast();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [tierFeatures, setTierFeatures] = useState([]);
  const [billingCycle, setBillingCycle] = useState('monthly'); // 'monthly' or 'annual'
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load current subscription
      const subRes = await fetch('/api/v1/subscriptions/current', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (subRes.ok) {
        const subData = await subRes.json();
        setCurrentSubscription(subData);
      }

      // Load all plans
      const plansRes = await fetch('/api/v1/billing/plans', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (plansRes.ok) {
        const plansData = await plansRes.json();
        // Handle both {plans: [...]} wrapper and direct array formats
        const plansArray = plansData.plans || plansData;
        if (Array.isArray(plansArray)) {
          setPlans(plansArray);
        } else {
          console.error('Unexpected plans data format:', plansData);
          toast.error('Failed to load plans: unexpected data format');
        }
      } else {
        console.error('Failed to load plans, status:', plansRes.status);
        toast.error('Failed to load subscription plans');
      }

      // Load tier features
      const featuresRes = await fetch('/api/v1/tiers/features', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (featuresRes.ok) {
        const featuresData = await featuresRes.json();
        setTierFeatures(featuresData);
      }

    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load plans. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getFeaturesForTier = (tierCode) => {
    const tierData = tierFeatures.find(t => t.tier_code === tierCode);
    if (!tierData || !tierData.features) return [];

    return tierData.features.map(f => ({
      name: f.feature_name,
      category: f.category,
      description: f.description
    }));
  };

  const handlePreviewUpgrade = async (plan) => {
    if (!plan) return;

    try {
      const res = await fetch(`/api/v1/subscriptions/preview-change?new_plan_code=${plan.id}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (res.ok) {
        const preview = await res.json();
        setPreviewData(preview);
        setSelectedPlan(plan);
        setShowPreview(true);
      } else {
        throw new Error('Failed to load preview');
      }
    } catch (error) {
      console.error('Error previewing upgrade:', error);
      toast.error('Could not preview upgrade. Please try again.');
    }
  };

  const handleUpgrade = async (plan) => {
    if (!plan) return;

    setCheckoutLoading(true);

    try {
      const res = await fetch('/api/v1/subscriptions/upgrade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        credentials: 'include',
        body: JSON.stringify({
          plan_code: plan.id,
          effective_date: 'immediate'
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to initiate upgrade');
      }

      const data = await res.json();

      // Redirect to Stripe Checkout
      if (data.checkout_url) {
        toast.info('Redirecting to secure payment page...');
        setTimeout(() => {
          window.location.href = data.checkout_url;
        }, 500);
      } else {
        throw new Error('No checkout URL returned');
      }

    } catch (error) {
      console.error('Error upgrading:', error);
      toast.error(error.message || 'Failed to start upgrade process');
      setCheckoutLoading(false);
    }
  };

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-12 text-center animate-pulse`}>
        <div className="inline-block h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className={`text-lg ${theme.text.secondary}`}>Loading plans...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Checkout Loading Overlay */}
      <AnimatePresence>
        {checkoutLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center"
          >
            <div className={`${theme.card} p-8 rounded-xl text-center max-w-md`}>
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-purple-500 mx-auto mb-6"></div>
              <h3 className={`text-2xl font-bold ${theme.text.primary} mb-2`}>
                Preparing Your Upgrade
              </h3>
              <p className={`text-lg ${theme.text.secondary}`}>
                Redirecting to secure payment page...
              </p>
              <p className={`text-sm ${theme.text.secondary} mt-4`}>
                Please don't close this window
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Preview Modal */}
      <AnimatePresence>
        {showPreview && previewData && selectedPlan && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex items-center justify-center p-4"
            onClick={() => setShowPreview(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className={`${theme.card} rounded-xl p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto`}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className={`text-2xl font-bold ${theme.text.primary}`}>
                  Preview Upgrade
                </h3>
                <button
                  onClick={() => setShowPreview(false)}
                  className="text-slate-400 hover:text-slate-300"
                >
                  <XCircleIcon className="w-6 h-6" />
                </button>
              </div>

              <div className="space-y-6">
                {/* Plan Transition */}
                <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
                  <div>
                    <p className={`text-sm ${theme.text.secondary}`}>Current Plan</p>
                    <p className={`text-xl font-bold ${theme.text.primary}`}>{previewData.current_plan}</p>
                    <p className={`text-lg ${theme.text.secondary}`}>{formatCurrency(previewData.current_price)}/month</p>
                  </div>
                  <ArrowRightIcon className="w-8 h-8 text-purple-400" />
                  <div className="text-right">
                    <p className={`text-sm ${theme.text.secondary}`}>New Plan</p>
                    <p className={`text-xl font-bold ${theme.text.primary}`}>{previewData.target_plan}</p>
                    <p className={`text-lg ${theme.text.secondary}`}>{formatCurrency(previewData.target_price)}/month</p>
                  </div>
                </div>

                {/* Cost Breakdown */}
                <div className="border border-slate-700 rounded-lg p-6 space-y-4">
                  <h4 className={`font-semibold ${theme.text.primary}`}>Cost Breakdown</h4>

                  <div className="flex justify-between">
                    <span className={theme.text.secondary}>Monthly Price Difference</span>
                    <span className={`font-semibold ${previewData.price_difference > 0 ? 'text-amber-400' : 'text-green-400'}`}>
                      {previewData.price_difference > 0 ? '+' : ''}{formatCurrency(previewData.price_difference)}
                    </span>
                  </div>

                  {previewData.proration_amount !== null && previewData.proration_amount !== 0 && (
                    <div className="flex justify-between">
                      <span className={theme.text.secondary}>Prorated Amount (Today)</span>
                      <span className={`font-semibold ${previewData.proration_amount > 0 ? 'text-amber-400' : 'text-green-400'}`}>
                        {formatCurrency(Math.abs(previewData.proration_amount))}
                      </span>
                    </div>
                  )}

                  <div className="pt-4 border-t border-slate-700">
                    <div className="flex justify-between items-center">
                      <span className={`font-semibold ${theme.text.primary}`}>New Monthly Bill</span>
                      <span className={`text-2xl font-bold ${theme.text.primary}`}>
                        {formatCurrency(previewData.target_price)}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Features */}
                <div className="space-y-4">
                  {previewData.features_added.length > 0 && (
                    <div>
                      <h4 className={`font-semibold ${theme.text.primary} mb-3`}>Features You'll Gain</h4>
                      <div className="space-y-2">
                        {previewData.features_added.map((feature, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <CheckCircleIcon className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                            <span className={theme.text.primary}>{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {previewData.features_removed.length > 0 && (
                    <div>
                      <h4 className={`font-semibold ${theme.text.primary} mb-3`}>Features You'll Lose</h4>
                      <div className="space-y-2">
                        {previewData.features_removed.map((feature, index) => (
                          <div key={index} className="flex items-start gap-2">
                            <XCircleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <span className={theme.text.primary}>{feature}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-4 pt-6 border-t border-slate-700">
                  <button
                    onClick={() => setShowPreview(false)}
                    className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-3 font-medium transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={() => {
                      setShowPreview(false);
                      handleUpgrade(selectedPlan);
                    }}
                    className={`flex-1 ${theme.button} rounded-lg py-3 font-medium`}
                  >
                    Proceed to Checkout
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header */}
      <motion.div
        variants={itemVariants}
        initial="hidden"
        animate="visible"
        className="text-center py-8"
      >
        <h1 className={`text-4xl font-bold ${theme.text.primary} mb-4`}>
          Choose Your Perfect Plan
        </h1>
        <p className={`text-lg ${theme.text.secondary} max-w-2xl mx-auto`}>
          Upgrade to unlock more features, higher limits, and premium support
        </p>
      </motion.div>

      {/* Billing Cycle Toggle */}
      <motion.div
        variants={itemVariants}
        initial="hidden"
        animate="visible"
        className="flex justify-center mb-8"
      >
        <div className={`inline-flex ${theme.card} rounded-lg p-1`}>
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              billingCycle === 'monthly'
                ? 'bg-purple-600 text-white'
                : `${theme.text.secondary} hover:text-white`
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            className={`px-6 py-2 rounded-lg font-medium transition-all ${
              billingCycle === 'annual'
                ? 'bg-purple-600 text-white'
                : `${theme.text.secondary} hover:text-white`
            }`}
          >
            Annual
            <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full">
              Save 15%
            </span>
          </button>
        </div>
      </motion.div>

      {/* Plan Comparison Table */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {plans.map((plan, index) => {
          const features = getFeaturesForTier(plan.id);
          const isCurrentPlan = currentSubscription && currentSubscription.tier === plan.id;
          const isPopular = plan.id === 'professional' || plan.id === 'founders-friend';
          const price = billingCycle === 'annual' && plan.price_yearly ? plan.price_yearly : plan.price_monthly;
          const displayPrice = billingCycle === 'annual' ? price / 12 : price;

          return (
            <motion.div
              key={plan.id}
              variants={itemVariants}
              className={`relative ${theme.card} rounded-xl p-6 border-2 transition-all ${
                isPopular
                  ? 'border-purple-500 shadow-xl shadow-purple-500/20 scale-105'
                  : isCurrentPlan
                  ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                  : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              {/* Popular Badge */}
              {isPopular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <TierBadge tier={plan.id} isPopular={true} />
                </div>
              )}

              {/* Current Plan Badge */}
              {isCurrentPlan && !isPopular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <TierBadge isCurrentPlan={true} />
                </div>
              )}

              {/* Plan Header */}
              <div className="text-center mb-6 pt-4">
                <h3 className={`text-2xl font-bold ${theme.text.primary} mb-2`}>
                  {plan.display_name}
                </h3>
                <div className="mb-4">
                  <span className={`text-4xl font-bold ${theme.text.primary}`}>
                    {formatCurrency(displayPrice)}
                  </span>
                  <span className={`text-sm ${theme.text.secondary}`}>
                    /{billingCycle === 'annual' ? 'mo' : plan.id === 'trial' ? 'week' : 'month'}
                  </span>
                </div>

                {billingCycle === 'annual' && plan.price_yearly && (
                  <p className="text-xs text-green-400">
                    {formatCurrency(plan.price_yearly)} billed annually
                  </p>
                )}
              </div>

              {/* Features List */}
              <div className="space-y-3 mb-6 min-h-[240px]">
                {features.slice(0, 6).map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <CheckCircleIcon className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    <span className={`text-sm ${theme.text.primary}`}>
                      {feature.name}
                    </span>
                  </div>
                ))}
                {features.length > 6 && (
                  <p className={`text-xs ${theme.text.secondary} italic`}>
                    +{features.length - 6} more features
                  </p>
                )}
              </div>

              {/* Action Button */}
              {isCurrentPlan ? (
                <button
                  disabled
                  className="w-full bg-slate-700 text-slate-500 rounded-lg py-3 text-sm font-medium cursor-not-allowed"
                >
                  Current Plan
                </button>
              ) : (
                <div className="space-y-2">
                  <button
                    onClick={() => handlePreviewUpgrade(plan)}
                    className="w-full border border-purple-500 text-purple-400 hover:bg-purple-500/10 rounded-lg py-3 text-sm font-medium transition-colors"
                  >
                    Preview Upgrade
                  </button>
                  <button
                    onClick={() => handleUpgrade(plan)}
                    disabled={checkoutLoading}
                    className={`w-full ${theme.button} rounded-lg py-3 text-sm font-medium ${
                      checkoutLoading ? 'opacity-50 cursor-not-allowed' : ''
                    }`}
                  >
                    {checkoutLoading ? 'Processing...' : 'Upgrade Now'}
                  </button>
                </div>
              )}
            </motion.div>
          );
        })}
      </motion.div>

      {/* Information Section */}
      <motion.div
        variants={itemVariants}
        initial="hidden"
        animate="visible"
        className={`${theme.card} rounded-xl p-6 border border-blue-500/30 bg-blue-500/5`}
      >
        <div className="flex gap-4">
          <InformationCircleIcon className="w-6 h-6 text-blue-400 flex-shrink-0" />
          <div className="space-y-2">
            <h4 className={`font-semibold ${theme.text.primary}`}>Upgrade Information</h4>
            <ul className={`text-sm ${theme.text.secondary} space-y-1`}>
              <li>• Upgrades take effect immediately after payment</li>
              <li>• You'll be charged the prorated amount for the current billing period</li>
              <li>• Your next bill will reflect the new plan price</li>
              <li>• You can downgrade anytime (takes effect next billing cycle)</li>
              <li>• All upgrades are processed securely through Stripe</li>
            </ul>
          </div>
        </div>
      </motion.div>

      {/* Back Button */}
      <div className="flex justify-center pt-6">
        <button
          onClick={() => navigate('/admin/subscription/plan')}
          className="border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg px-6 py-2 text-sm font-medium transition-colors"
        >
          ← Back to Subscription
        </button>
      </div>
    </div>
  );
}
