import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowDownIcon,
  InformationCircleIcon,
  GiftIcon,
  HeartIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import { useNavigate } from 'react-router-dom';

const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export default function SubscriptionDowngrade() {
  const { theme } = useTheme();
  const toast = useToast();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [effectiveDate, setEffectiveDate] = useState('next_cycle'); // 'immediate' or 'next_cycle'
  const [showRetentionOffer, setShowRetentionOffer] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [downgrading, setDowngrading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
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

      const plansRes = await fetch('/api/v1/billing/plans', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (plansRes.ok) {
        const plansData = await plansRes.json();
        // Only show plans cheaper than current
        if (subData) {
          const lowerPlans = plansData.filter(p => p.price_monthly < subData.price);
          setPlans(lowerPlans);
        }
      }

    } catch (error) {
      console.error('Error loading data:', error);
      toast.error('Failed to load downgrade options');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectPlan = async (plan) => {
    setSelectedPlan(plan);

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
        setShowRetentionOffer(true);
      }
    } catch (error) {
      console.error('Error previewing downgrade:', error);
      toast.error('Failed to preview downgrade');
    }
  };

  const handleStayOnPlan = () => {
    toast.success('Great! We\'re glad you\'re staying with us. 🎉');
    setTimeout(() => {
      navigate('/admin/subscription/plan');
    }, 1500);
  };

  const handleProceedToConfirmation = () => {
    setShowRetentionOffer(false);
    setShowConfirmation(true);
  };

  const handleConfirmDowngrade = async () => {
    if (!selectedPlan) return;

    setDowngrading(true);

    try {
      const res = await fetch('/api/v1/subscriptions/downgrade', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        credentials: 'include',
        body: JSON.stringify({
          plan_code: selectedPlan.id,
          effective_date: effectiveDate
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to downgrade');
      }

      const data = await res.json();

      toast.success(data.message || 'Downgrade scheduled successfully');

      setTimeout(() => {
        navigate('/admin/subscription/plan');
      }, 2000);

    } catch (error) {
      console.error('Error downgrading:', error);
      toast.error(error.message || 'Failed to downgrade subscription');
      setDowngrading(false);
    }
  };

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-12 text-center animate-pulse`}>
        <div className="inline-block h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className={`text-lg ${theme.text.secondary}`}>Loading options...</p>
      </div>
    );
  }

  if (!currentSubscription) {
    return (
      <div className={`${theme.card} rounded-xl p-8 text-center`}>
        <ExclamationTriangleIcon className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
        <h3 className={`text-xl font-semibold ${theme.text.primary} mb-2`}>No Active Subscription</h3>
        <p className={theme.text.secondary}>You don't have an active subscription to downgrade.</p>
        <button
          onClick={() => navigate('/admin/subscription/plan')}
          className={`mt-4 ${theme.button} rounded-lg px-6 py-2 text-sm font-medium`}
        >
          View Plans
        </button>
      </div>
    );
  }

  if (plans.length === 0) {
    return (
      <div className={`${theme.card} rounded-xl p-8 text-center`}>
        <InformationCircleIcon className="w-16 h-16 mx-auto mb-4 text-blue-400" />
        <h3 className={`text-xl font-semibold ${theme.text.primary} mb-2`}>No Lower Plans Available</h3>
        <p className={theme.text.secondary}>You're on the lowest tier. Consider canceling if you no longer need the service.</p>
        <div className="flex gap-4 justify-center mt-6">
          <button
            onClick={() => navigate('/admin/subscription/plan')}
            className="border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg px-6 py-2 text-sm font-medium"
          >
            Back
          </button>
          <button
            onClick={() => navigate('/admin/subscription/cancel')}
            className="border border-red-600 text-red-400 hover:bg-red-500/10 rounded-lg px-6 py-2 text-sm font-medium"
          >
            Cancel Subscription
          </button>
        </div>
      </div>
    );
  }

  // Retention Offer Modal
  if (showRetentionOffer && previewData && selectedPlan) {
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`${theme.card} rounded-xl p-8 border-2 border-purple-500`}
        >
          <div className="text-center mb-8">
            <HeartIcon className="w-16 h-16 mx-auto mb-4 text-purple-400" />
            <h2 className={`text-3xl font-bold ${theme.text.primary} mb-2`}>
              Before You Downgrade...
            </h2>
            <p className={`text-lg ${theme.text.secondary}`}>
              We'd love to keep you on your current plan!
            </p>
          </div>

          {/* Retention Offers */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            <div className={`${theme.card} border border-green-500/30 rounded-lg p-6 text-center`}>
              <GiftIcon className="w-12 h-12 mx-auto mb-3 text-green-400" />
              <h4 className={`font-semibold ${theme.text.primary} mb-2`}>20% Off</h4>
              <p className={`text-sm ${theme.text.secondary}`}>
                Stay on {currentSubscription.tier} and get 20% off for the next 3 months
              </p>
            </div>

            <div className={`${theme.card} border border-blue-500/30 rounded-lg p-6 text-center`}>
              <GiftIcon className="w-12 h-12 mx-auto mb-3 text-blue-400" />
              <h4 className={`font-semibold ${theme.text.primary} mb-2`}>Pause Subscription</h4>
              <p className={`text-sm ${theme.text.secondary}`}>
                Need a break? Pause your subscription for up to 3 months
              </p>
            </div>

            <div className={`${theme.card} border border-amber-500/30 rounded-lg p-6 text-center`}>
              <GiftIcon className="w-12 h-12 mx-auto mb-3 text-amber-400" />
              <h4 className={`font-semibold ${theme.text.primary} mb-2`}>Feature Request</h4>
              <p className={`text-sm ${theme.text.secondary}`}>
                Tell us what's missing and we'll prioritize it
              </p>
            </div>
          </div>

          {/* What You'll Lose */}
          {previewData.features_removed.length > 0 && (
            <div className="border border-red-500/30 rounded-lg p-6 mb-6 bg-red-500/5">
              <h4 className={`font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
                <ExclamationTriangleIcon className="w-5 h-5 text-red-400" />
                You'll Lose Access To:
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {previewData.features_removed.map((feature, index) => (
                  <div key={index} className="flex items-start gap-2">
                    <XCircleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <span className={`text-sm ${theme.text.primary}`}>{feature}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={handleStayOnPlan}
              className={`flex-1 ${theme.button} rounded-lg py-3 font-medium`}
            >
              Stay on {currentSubscription.tier} Plan
            </button>
            <button
              onClick={handleProceedToConfirmation}
              className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-3 font-medium"
            >
              Continue Downgrade
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Confirmation Modal
  if (showConfirmation && previewData && selectedPlan) {
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`${theme.card} rounded-xl p-8`}
        >
          <div className="text-center mb-8">
            <ExclamationTriangleIcon className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
            <h2 className={`text-2xl font-bold ${theme.text.primary} mb-2`}>
              Confirm Downgrade
            </h2>
            <p className={theme.text.secondary}>
              Are you sure you want to downgrade your subscription?
            </p>
          </div>

          {/* Summary */}
          <div className="space-y-6 mb-8">
            <div className="flex items-center justify-between p-4 bg-slate-800/50 rounded-lg">
              <div>
                <p className={`text-sm ${theme.text.secondary}`}>From</p>
                <p className={`text-xl font-bold ${theme.text.primary}`}>{previewData.current_plan}</p>
                <p className={theme.text.secondary}>{formatCurrency(previewData.current_price)}/month</p>
              </div>
              <ArrowDownIcon className="w-8 h-8 text-yellow-400" />
              <div className="text-right">
                <p className={`text-sm ${theme.text.secondary}`}>To</p>
                <p className={`text-xl font-bold ${theme.text.primary}`}>{previewData.target_plan}</p>
                <p className={theme.text.secondary}>{formatCurrency(previewData.target_price)}/month</p>
              </div>
            </div>

            <div className="border border-slate-700 rounded-lg p-6 space-y-4">
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Monthly Savings</span>
                <span className="text-green-400 font-semibold">
                  {formatCurrency(Math.abs(previewData.price_difference))}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>New Monthly Bill</span>
                <span className={`text-2xl font-bold ${theme.text.primary}`}>
                  {formatCurrency(previewData.target_price)}
                </span>
              </div>
            </div>

            {/* Effective Date Selection */}
            <div className="border border-slate-700 rounded-lg p-6">
              <h4 className={`font-semibold ${theme.text.primary} mb-4`}>When should this take effect?</h4>
              <div className="space-y-3">
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="radio"
                    value="next_cycle"
                    checked={effectiveDate === 'next_cycle'}
                    onChange={(e) => setEffectiveDate(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <p className={`font-medium ${theme.text.primary}`}>
                      At next billing date <span className="text-green-400">(Recommended)</span>
                    </p>
                    <p className={`text-sm ${theme.text.secondary}`}>
                      Change takes effect on {formatDate(currentSubscription.next_billing_date)}
                    </p>
                  </div>
                </label>
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="radio"
                    value="immediate"
                    checked={effectiveDate === 'immediate'}
                    onChange={(e) => setEffectiveDate(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <p className={`font-medium ${theme.text.primary}`}>Immediately</p>
                    <p className={`text-sm ${theme.text.secondary}`}>
                      Lose access to premium features right away
                    </p>
                  </div>
                </label>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => setShowConfirmation(false)}
              disabled={downgrading}
              className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-3 font-medium transition-colors"
            >
              Go Back
            </button>
            <button
              onClick={handleConfirmDowngrade}
              disabled={downgrading}
              className={`flex-1 bg-yellow-600 hover:bg-yellow-500 text-white rounded-lg py-3 font-medium transition-colors ${
                downgrading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {downgrading ? 'Processing...' : 'Confirm Downgrade'}
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Plan Selection
  return (
    <div className="space-y-6">
      <div className="text-center py-8">
        <h1 className={`text-4xl font-bold ${theme.text.primary} mb-4`}>
          Downgrade Your Plan
        </h1>
        <p className={`text-lg ${theme.text.secondary} max-w-2xl mx-auto`}>
          Choose a lower-cost plan that better fits your needs
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`${theme.card} rounded-xl p-6 border-2 border-slate-700 hover:border-purple-500 transition-all cursor-pointer`}
            onClick={() => handleSelectPlan(plan)}
          >
            <h3 className={`text-2xl font-bold ${theme.text.primary} mb-4`}>
              {plan.display_name}
            </h3>
            <div className="mb-6">
              <span className={`text-4xl font-bold ${theme.text.primary}`}>
                {formatCurrency(plan.price_monthly)}
              </span>
              <span className={`text-sm ${theme.text.secondary}`}>/month</span>
            </div>
            <button
              className={`w-full ${theme.button} rounded-lg py-3 text-sm font-medium`}
            >
              Select This Plan
            </button>
          </div>
        ))}
      </div>

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
