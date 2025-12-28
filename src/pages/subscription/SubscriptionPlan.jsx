import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  SparklesIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import { safeFind } from '../../utils/safeArrayUtils';

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
    past_due: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium border ${colors[status] || colors.trialing}`}>
      {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
    </span>
  );
};

// Plan features will be loaded from API dynamically
// No hardcoded features - fetched from /api/v1/tiers/features

export default function SubscriptionPlan() {
  const { theme } = useTheme();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [subscription, setSubscription] = useState(null);
  const [showComparison, setShowComparison] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [tierFeatures, setTierFeatures] = useState([]); // Real features from API
  const maxRetries = 3;

  // Dynamic plan loading from backend
  const [availablePlans, setAvailablePlans] = useState([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [plansError, setPlansError] = useState(null);

  useEffect(() => {
    loadSubscription();
    loadTierFeatures();
    loadAvailablePlans();  // Load plans from API

    // Check for canceled checkout
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('canceled') === 'true') {
      setError('Checkout was canceled. Please try again when you\'re ready.');
      // Clean up URL
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  const loadSubscription = async (attempt = 1) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/subscriptions/current', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        } else if (res.status === 403) {
          throw new Error('You do not have permission to view subscription information.');
        } else if (res.status === 404) {
          // No subscription found is OK - user may not have subscribed yet
          setSubscription(null);
          return;
        } else {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to load subscription (${res.status})`);
        }
      }

      const data = await res.json();
      setSubscription(data);
      setRetryCount(0); // Reset retry count on success
      toast.success('Subscription loaded successfully');
    } catch (error) {
      console.error('Error loading subscription:', error);
      const errorMsg = error.message || 'Failed to load subscription';
      setError(errorMsg);

      // Retry logic for transient failures
      if (attempt < maxRetries && !error.message.includes('Authentication') && !error.message.includes('permission')) {
        setTimeout(() => {
          setRetryCount(attempt);
          loadSubscription(attempt + 1);
        }, 2000 * attempt); // Exponential backoff
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadTierFeatures = async () => {
    try {
      const res = await fetch('/api/v1/tiers/features', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (!res.ok) {
        console.error('Failed to load tier features:', res.status);
        return;
      }

      const data = await res.json();
      setTierFeatures(data);
      console.log('Loaded tier features:', data);
    } catch (error) {
      console.error('Error loading tier features:', error);
    }
  };

  const loadAvailablePlans = async () => {
    setLoadingPlans(true);
    setPlansError(null);
    try {
      const res = await fetch('/api/v1/subscriptions/plans', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (!res.ok) {
        throw new Error(`Failed to load plans (${res.status})`);
      }

      const data = await res.json();
      const plans = data.plans || [];

      // Transform backend plans to frontend format
      const transformedPlans = plans.map(plan => ({
        tier: plan.id,
        tier_code: plan.id,
        name: plan.display_name,
        price: plan.price_monthly,
        period: plan.price_monthly === 1.0 ? 'week' : 'month',
        description: plan.features[0] || '',  // Use first feature as description
        popular: plan.id === 'professional'  // Mark Professional as popular
      }));

      setAvailablePlans(transformedPlans);
      console.log('Loaded subscription plans:', transformedPlans);
    } catch (error) {
      console.error('Error loading plans:', error);
      setPlansError(error.message || 'Failed to load subscription plans');
      toast.error('Failed to load subscription plans');

      // Fallback to minimal plan list if API fails
      setAvailablePlans([
        { tier: 'trial', tier_code: 'trial', name: 'Trial', price: 1.0, period: 'week', description: '7-day trial' },
        { tier: 'starter', tier_code: 'starter', name: 'Starter', price: 19.0, period: 'month', description: 'For individuals' },
        { tier: 'professional', tier_code: 'professional', name: 'Professional', price: 49.0, period: 'month', description: 'For teams', popular: true },
        { tier: 'enterprise', tier_code: 'enterprise', name: 'Enterprise', price: 99.0, period: 'month', description: 'For organizations' }
      ]);
    } finally {
      setLoadingPlans(false);
    }
  };

  // Helper function to get features for a tier
  const getFeaturesForTier = (tierCode) => {
    // Use safeFind to handle potentially undefined tierFeatures
    const tierData = safeFind(tierFeatures, t => t.tier_code === tierCode);
    if (!tierData || !tierData.features) return [];

    // Return features in display format with included: true
    return tierData.features.map(f => ({
      name: f.feature_name,
      included: true,
      category: f.category,
      description: f.description
    }));
  };

  const handleUpgrade = async (targetTier, attempt = 1) => {
    setCheckoutLoading(true);
    setError(null);

    try {
      // Find the plan object for the target tier (using safeFind to handle undefined availablePlans)
      const plan = safeFind(availablePlans, p => p.tier === targetTier);
      if (!plan) {
        throw new Error('Invalid plan selected. Please refresh the page and try again.');
      }

      // Call the correct billing checkout endpoint
      const res = await fetch('/api/v1/billing/subscriptions/checkout', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        credentials: 'include',
        body: JSON.stringify({
          tier_id: plan.tier,
          billing_cycle: 'monthly',
          success_url: window.location.origin + '/admin/subscription/success?session_id={CHECKOUT_SESSION_ID}',
          cancel_url: window.location.origin + '/admin/subscription/plan?canceled=true'
        })
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        } else if (res.status === 403) {
          throw new Error('You do not have permission to modify subscriptions.');
        } else if (res.status === 400) {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || 'Invalid subscription request');
        } else {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to create checkout session (${res.status})`);
        }
      }

      const data = await res.json();

      // Redirect to Stripe Checkout
      if (data.checkout_url) {
        toast.info('Redirecting to secure payment page...');
        setTimeout(() => {
          window.location.href = data.checkout_url;
        }, 500);
      } else {
        throw new Error('No checkout URL returned from server. Please contact support.');
      }
    } catch (error) {
      console.error('Checkout error:', error);

      // Stripe-specific error handling
      let errorMsg = error.message || 'Failed to initiate checkout';

      if (error.type === 'StripeCardError') {
        errorMsg = `Payment failed: ${error.message}`;
        toast.error(errorMsg);
      } else if (error.type === 'StripeInvalidRequestError') {
        errorMsg = 'Invalid payment request. Please try again or contact support.';
        toast.error(errorMsg);
      } else if (error.type === 'StripeAPIError') {
        errorMsg = 'Payment service unavailable. Please try again later.';
        toast.error(errorMsg);
      } else if (error.type === 'StripeAuthenticationError') {
        errorMsg = 'Payment authentication failed. Please contact support.';
        toast.error(errorMsg);
      } else if (error.type === 'StripeRateLimitError') {
        errorMsg = 'Too many requests. Please wait a moment and try again.';
        toast.warning(errorMsg);
      } else if (error.message.includes('Authentication')) {
        errorMsg = error.message;
        toast.error(errorMsg);
        // Redirect to login after 2 seconds
        setTimeout(() => {
          window.location.href = '/auth/login';
        }, 2000);
      } else {
        // Retry logic for transient failures
        if (attempt < maxRetries && !error.message.includes('Invalid') && !error.message.includes('permission')) {
          toast.warning(`Retrying checkout... (Attempt ${attempt}/${maxRetries})`);
          setTimeout(() => {
            handleUpgrade(targetTier, attempt + 1);
          }, 2000 * attempt); // Exponential backoff
          return;
        } else {
          toast.error(errorMsg);
        }
      }

      setError(errorMsg);
      setCheckoutLoading(false);
    }
  };

  const handleDowngrade = async (targetTier, attempt = 1) => {
    if (!confirm(`Are you sure you want to downgrade to ${targetTier}? This change will take effect at the end of your current billing period.`)) {
      return;
    }

    try {
      const res = await fetch('/api/v1/subscriptions/change', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        credentials: 'include',
        body: JSON.stringify({ target_tier: targetTier })
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        } else if (res.status === 403) {
          throw new Error('You do not have permission to modify subscriptions.');
        } else {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to downgrade subscription (${res.status})`);
        }
      }

      toast.success(`Successfully scheduled downgrade to ${targetTier}. Change will take effect at the end of your billing period.`);
      await loadSubscription();
    } catch (error) {
      console.error('Error downgrading:', error);
      const errorMsg = error.message || 'Failed to downgrade subscription';

      // Retry logic for transient failures
      if (attempt < maxRetries && !error.message.includes('Authentication') && !error.message.includes('permission')) {
        toast.warning(`Retrying downgrade... (Attempt ${attempt}/${maxRetries})`);
        setTimeout(() => {
          handleDowngrade(targetTier, attempt + 1);
        }, 2000 * attempt);
      } else {
        toast.error(errorMsg);
        setError(errorMsg);
      }
    }
  };

  const handleCancelSubscription = async (attempt = 1) => {
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access at the end of your billing period.')) {
      return;
    }

    try {
      const res = await fetch('/api/v1/subscriptions/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        credentials: 'include'
      });

      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Authentication required. Please log in again.');
        } else if (res.status === 403) {
          throw new Error('You do not have permission to cancel subscriptions.');
        } else {
          const errorData = await res.json().catch(() => ({}));
          throw new Error(errorData.detail || `Failed to cancel subscription (${res.status})`);
        }
      }

      toast.success('Subscription canceled successfully. You will retain access until the end of your billing period.');
      await loadSubscription();
    } catch (error) {
      console.error('Error canceling subscription:', error);
      const errorMsg = error.message || 'Failed to cancel subscription';

      // Retry logic for transient failures
      if (attempt < maxRetries && !error.message.includes('Authentication') && !error.message.includes('permission')) {
        toast.warning(`Retrying cancellation... (Attempt ${attempt}/${maxRetries})`);
        setTimeout(() => {
          handleCancelSubscription(attempt + 1);
        }, 2000 * attempt);
      } else {
        toast.error(errorMsg);
        setError(errorMsg);
      }
    }
  };

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-6 animate-pulse`}>
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
        <div className="h-24 bg-slate-700 rounded"></div>
      </div>
    );
  }

  if (error && !loading && retryCount >= maxRetries) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${theme.card} rounded-xl p-6 border border-red-500/50`}
      >
        <div className="flex items-start gap-3">
          <ExclamationTriangleIcon className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-red-400 mb-2">Failed to Load Subscription</h3>
            <p className="text-red-300 text-sm mb-4">{error}</p>
            {retryCount > 0 && retryCount < maxRetries && (
              <p className="text-red-400 text-xs mb-4">
                Retrying... (Attempt {retryCount}/{maxRetries})
              </p>
            )}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  setError(null);
                  setRetryCount(0);
                  loadSubscription();
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-500 transition-colors text-sm font-medium"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/admin/dashboard'}
                className="px-4 py-2 border border-gray-600 text-gray-300 hover:bg-gray-700 rounded-lg transition-colors text-sm font-medium"
              >
                Go to Dashboard
              </button>
            </div>
          </div>
        </div>
      </motion.div>
    );
  }

  const currentFeatures = subscription ? getFeaturesForTier(subscription.tier_code || subscription.tier) : [];

  return (
    <div className="space-y-6">
      {/* Error Banner (non-critical errors during operation) */}
      {error && !checkoutLoading && retryCount < maxRetries && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-yellow-900/20 border border-yellow-500/50 rounded-xl p-4 flex items-start gap-3"
        >
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-yellow-200 text-sm font-medium">{error}</p>
            {retryCount > 0 && (
              <p className="text-yellow-300 text-xs mt-1">
                Retrying... (Attempt {retryCount}/{maxRetries})
              </p>
            )}
          </div>
          <button
            onClick={() => setError(null)}
            className="text-yellow-400 hover:text-yellow-300 transition-colors"
          >
            <XCircleIcon className="h-5 w-5" />
          </button>
        </motion.div>
      )}

      {/* Checkout Loading Overlay */}
      {checkoutLoading && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className={`${theme.card} p-8 rounded-xl text-center`}>
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500 mx-auto mb-4"></div>
            <p className={`text-lg font-semibold ${theme.text.primary}`}>Redirecting to Stripe Checkout...</p>
            <p className={`text-sm ${theme.text.secondary} mt-2`}>Please wait while we prepare your payment</p>
          </div>
        </div>
      )}

      {/* Current Subscription Card */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <div className="flex items-center justify-between mb-6">
          <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
            <SparklesIcon className="w-5 h-5 text-purple-400" />
            Current Subscription
          </h3>
          {subscription && <TierBadge tier={subscription.tier} />}
        </div>

        {subscription ? (
          <div className="space-y-6">
            {/* Plan Details Grid */}
            <div className="grid grid-cols-2 gap-6">
              <div>
                <p className={`text-sm ${theme.text.secondary} mb-1`}>Plan</p>
                <p className={`text-2xl font-bold ${theme.text.primary}`}>
                  {subscription.tier ? subscription.tier.charAt(0).toUpperCase() + subscription.tier.slice(1) : 'Unknown'}
                </p>
              </div>
              <div>
                <p className={`text-sm ${theme.text.secondary} mb-1`}>Price</p>
                <p className={`text-2xl font-bold ${theme.text.primary}`}>
                  {formatCurrency(subscription.price)}
                  <span className="text-sm font-normal text-slate-400">
                    /{subscription.tier === 'trial' ? 'week' : 'month'}
                  </span>
                </p>
              </div>
              <div>
                <p className={`text-sm ${theme.text.secondary} mb-1`}>Status</p>
                <div className="mt-1">
                  <StatusBadge status={subscription.status} />
                </div>
              </div>
              <div>
                <p className={`text-sm ${theme.text.secondary} mb-1`}>Next Billing Date</p>
                <p className={`text-sm font-medium ${theme.text.primary} mt-1`}>
                  {formatDate(subscription.next_billing_date)}
                </p>
              </div>
            </div>

            {/* Features List */}
            <div className="border-t border-slate-700 pt-6">
              <h4 className={`text-sm font-semibold ${theme.text.primary} mb-4`}>Plan Features</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {currentFeatures.map((feature, index) => (
                  <div key={index} className="flex items-start gap-2">
                    {feature.included ? (
                      <CheckCircleIcon className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircleIcon className="w-5 h-5 text-slate-600 flex-shrink-0 mt-0.5" />
                    )}
                    <span className={`text-sm ${feature.included ? theme.text.primary : theme.text.secondary}`}>
                      {feature.name}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4 border-t border-slate-700">
              {subscription.tier !== 'enterprise' && subscription.tier !== 'founders-friend' && (
                <button
                  onClick={() => window.location.href = '/admin/subscription/upgrade'}
                  className={`flex-1 ${theme.button} rounded-lg py-2 px-4 text-sm font-medium transition-all`}
                >
                  <ArrowUpIcon className="w-4 h-4 inline mr-2" />
                  Upgrade Plan
                </button>
              )}
              {subscription.tier !== 'trial' && subscription.tier !== 'starter' && (
                <button
                  onClick={() => window.location.href = '/admin/subscription/downgrade'}
                  className="flex-1 border border-amber-600 text-amber-400 hover:bg-amber-500/10 rounded-lg py-2 px-4 text-sm font-medium transition-colors"
                >
                  <ArrowDownIcon className="w-4 h-4 inline mr-2" />
                  Downgrade Plan
                </button>
              )}
              <button
                onClick={() => setShowComparison(!showComparison)}
                className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-2 px-4 text-sm font-medium transition-colors"
              >
                Compare Plans
              </button>
              {subscription.status === 'active' && (
                <button
                  onClick={() => window.location.href = '/admin/subscription/cancel'}
                  className="border border-red-600 text-red-400 hover:bg-red-500/10 rounded-lg py-2 px-4 text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center py-8">
            <SparklesIcon className="w-16 h-16 mx-auto mb-4 text-slate-500" />
            <h3 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>No Active Subscription</h3>
            <p className={`${theme.text.secondary} mb-6`}>Start your subscription to access premium features</p>
            <button
              onClick={() => setShowComparison(true)}
              className={`${theme.button} rounded-lg py-2 px-6 text-sm font-medium`}
            >
              View Plans
            </button>
          </div>
        )}
      </motion.div>

      {/* Plan Comparison Table */}
      {showComparison && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`${theme.card} rounded-xl p-6`}
        >
          <div className="flex items-center justify-between mb-6">
            <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Compare Plans</h3>
            <button
              onClick={() => setShowComparison(false)}
              className="text-slate-400 hover:text-slate-300 text-sm"
            >
              Hide
            </button>
          </div>

          {/* Plan loading indicator */}
          {loadingPlans && (
            <div className={`${theme.card} rounded-xl p-6 text-center`}>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500 mx-auto mb-4"></div>
              <p className={theme.text.secondary}>Loading subscription plans...</p>
            </div>
          )}

          {/* Plan loading error */}
          {plansError && !loadingPlans && (
            <div className="bg-red-900/20 border border-red-500/50 rounded-xl p-4 flex items-start gap-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-200 text-sm font-medium">{plansError}</p>
                <button
                  onClick={loadAvailablePlans}
                  className="mt-2 text-red-400 hover:text-red-300 text-sm underline"
                >
                  Retry
                </button>
              </div>
            </div>
          )}

          {/* Plan comparison grid */}
          {!loadingPlans && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {availablePlans.map((plan) => (
              <div
                key={plan.tier}
                className={`relative border rounded-xl p-6 transition-all ${
                  subscription?.tier === plan.tier
                    ? 'border-purple-500 bg-purple-500/5'
                    : 'border-slate-700 hover:border-slate-600'
                } ${plan.popular ? 'ring-2 ring-purple-500/50' : ''}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <span className="bg-purple-500 text-white text-xs font-semibold px-3 py-1 rounded-full">
                      Popular
                    </span>
                  </div>
                )}

                <div className="text-center mb-4">
                  <TierBadge tier={plan.tier} />
                  <h4 className={`text-xl font-bold ${theme.text.primary} mt-3 mb-1`}>{plan.name}</h4>
                  <p className={`text-xs ${theme.text.secondary}`}>{plan.description}</p>
                </div>

                <div className="text-center mb-6">
                  <p className={`text-3xl font-bold ${theme.text.primary}`}>
                    {formatCurrency(plan.price)}
                  </p>
                  <p className={`text-sm ${theme.text.secondary}`}>per {plan.period}</p>
                </div>

                <div className="space-y-2 mb-6">
                  {(getFeaturesForTier(plan.tier_code || plan.tier) || []).slice(0, 4).map((feature, index) => (
                    <div key={index} className="flex items-start gap-2">
                      {feature.included ? (
                        <CheckCircleIcon className="w-4 h-4 text-green-400 flex-shrink-0 mt-0.5" />
                      ) : (
                        <XCircleIcon className="w-4 h-4 text-slate-600 flex-shrink-0 mt-0.5" />
                      )}
                      <span className={`text-xs ${feature.included ? theme.text.primary : theme.text.secondary}`}>
                        {feature.name}
                      </span>
                    </div>
                  ))}
                </div>

                {subscription?.tier === plan.tier ? (
                  <button
                    disabled
                    className="w-full bg-slate-700 text-slate-500 rounded-lg py-2 text-sm font-medium cursor-not-allowed"
                  >
                    Current Plan
                  </button>
                ) : subscription && getTierLevel(plan.tier) > getTierLevel(subscription.tier) ? (
                  <button
                    onClick={() => handleUpgrade(plan.tier)}
                    disabled={checkoutLoading}
                    className={`w-full ${theme.button} rounded-lg py-2 text-sm font-medium ${checkoutLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {checkoutLoading ? 'Processing...' : 'Upgrade'}
                  </button>
                ) : subscription ? (
                  <button
                    onClick={() => handleDowngrade(plan.tier)}
                    disabled={checkoutLoading}
                    className={`w-full border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-2 text-sm font-medium transition-colors ${checkoutLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    Downgrade
                  </button>
                ) : (
                  <button
                    onClick={() => handleUpgrade(plan.tier)}
                    disabled={checkoutLoading}
                    className={`w-full ${theme.button} rounded-lg py-2 text-sm font-medium ${checkoutLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {checkoutLoading ? 'Processing...' : 'Select Plan'}
                  </button>
                )}
              </div>
            ))}
            </div>
          )}

          {!loadingPlans && (
            <div className={`mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg flex gap-3`}>
              <InformationCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0" />
              <div className="text-sm">
                <p className={`font-medium ${theme.text.primary} mb-1`}>Plan Changes</p>
                <p className={theme.text.secondary}>
                  Upgrades take effect immediately. Downgrades take effect at the end of your current billing period.
              </p>
            </div>
          </div>
          )}
        </motion.div>
      )}
    </div>
  );
}

// Helper function to determine tier level for comparison
function getTierLevel(tier) {
  const levels = { trial: 1, starter: 2, professional: 3, enterprise: 4 };
  return levels[tier] || 0;
}
