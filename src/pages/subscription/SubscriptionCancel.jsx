import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowLeftIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import { useNavigate } from 'react-router-dom';

const CANCELLATION_REASONS = [
  { value: 'too_expensive', label: 'Too expensive', description: 'The subscription cost is too high for my budget' },
  { value: 'not_using', label: 'Not using the service', description: "I'm not using the features enough to justify the cost" },
  { value: 'missing_features', label: 'Missing features', description: "The service doesn't have the features I need" },
  { value: 'found_alternative', label: 'Found an alternative', description: "I found another service that better meets my needs" },
  { value: 'technical_issues', label: 'Technical issues', description: "I'm experiencing bugs or performance problems" },
  { value: 'other', label: 'Other', description: 'My reason is not listed here' }
];

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

export default function SubscriptionCancel() {
  const { theme } = useTheme();
  const toast = useToast();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [selectedReason, setSelectedReason] = useState('');
  const [feedback, setFeedback] = useState('');
  const [immediate, setImmediate] = useState(false);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [canceling, setCanceling] = useState(false);

  useEffect(() => {
    loadSubscription();
  }, []);

  const loadSubscription = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/subscriptions/current', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        }
      });

      if (res.ok) {
        const data = await res.json();
        setCurrentSubscription(data);
      }
    } catch (error) {
      console.error('Error loading subscription:', error);
      toast.error('Failed to load subscription information');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    if (!selectedReason) {
      toast.warning('Please select a reason for cancellation');
      return;
    }

    setShowConfirmation(true);
  };

  const handleConfirmCancellation = async () => {
    if (!selectedReason) return;

    setCanceling(true);

    try {
      const res = await fetch('/api/v1/subscriptions/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
        },
        credentials: 'include',
        body: JSON.stringify({
          reason: selectedReason,
          feedback: feedback || null,
          immediate
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to cancel subscription');
      }

      const data = await res.json();

      toast.success(data.message || 'Subscription canceled successfully');

      setTimeout(() => {
        navigate('/admin/subscription/plan');
      }, 2000);

    } catch (error) {
      console.error('Error canceling:', error);
      toast.error(error.message || 'Failed to cancel subscription');
      setCanceling(false);
    }
  };

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-12 text-center animate-pulse`}>
        <div className="inline-block h-12 w-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mb-4"></div>
        <p className={`text-lg ${theme.text.secondary}`}>Loading...</p>
      </div>
    );
  }

  if (!currentSubscription) {
    return (
      <div className={`${theme.card} rounded-xl p-8 text-center`}>
        <ExclamationTriangleIcon className="w-16 h-16 mx-auto mb-4 text-yellow-400" />
        <h3 className={`text-xl font-semibold ${theme.text.primary} mb-2`}>No Active Subscription</h3>
        <p className={theme.text.secondary}>You don't have an active subscription to cancel.</p>
        <button
          onClick={() => navigate('/admin/subscription/plan')}
          className={`mt-4 ${theme.button} rounded-lg px-6 py-2 text-sm font-medium`}
        >
          View Plans
        </button>
      </div>
    );
  }

  // Confirmation Modal
  if (showConfirmation) {
    return (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className={`${theme.card} rounded-xl p-8 border-2 border-red-500`}
        >
          <div className="text-center mb-8">
            <ExclamationTriangleIcon className="w-20 h-20 mx-auto mb-4 text-red-400" />
            <h2 className={`text-3xl font-bold ${theme.text.primary} mb-4`}>
              Are you absolutely sure?
            </h2>
            <p className={`text-lg ${theme.text.secondary} mb-6`}>
              This action will cancel your subscription
            </p>
          </div>

          {/* Cancellation Summary */}
          <div className="border border-red-500/30 rounded-lg p-6 mb-8 bg-red-500/5 space-y-4">
            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Current Plan</p>
              <p className={`text-xl font-bold ${theme.text.primary}`}>
                {currentSubscription.tier ? currentSubscription.tier.charAt(0).toUpperCase() + currentSubscription.tier.slice(1) : 'Unknown'}
              </p>
            </div>

            <div>
              <p className={`text-sm ${theme.text.secondary}`}>Cancellation Reason</p>
              <p className={`font-medium ${theme.text.primary}`}>
                {CANCELLATION_REASONS.find(r => r.value === selectedReason)?.label || selectedReason}
              </p>
            </div>

            {feedback && (
              <div>
                <p className={`text-sm ${theme.text.secondary} mb-1`}>Your Feedback</p>
                <p className={`text-sm ${theme.text.primary} italic`}>"{feedback}"</p>
              </div>
            )}

            <div className="pt-4 border-t border-red-500/30">
              <p className={`text-sm ${theme.text.secondary}`}>Access Until</p>
              <p className={`text-lg font-bold ${immediate ? 'text-red-400' : 'text-green-400'}`}>
                {immediate ? 'Immediately' : formatDate(currentSubscription.next_billing_date)}
              </p>
            </div>
          </div>

          {/* Final Warning */}
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4 mb-6">
            <div className="flex gap-3">
              <ExclamationTriangleIcon className="w-6 h-6 text-yellow-400 flex-shrink-0" />
              <div>
                <p className={`font-semibold ${theme.text.primary} mb-1`}>Important Notice</p>
                <p className={`text-sm ${theme.text.secondary}`}>
                  {immediate
                    ? 'Your subscription will be canceled immediately and you will lose access to all premium features right now.'
                    : `You will retain access to all premium features until ${formatDate(currentSubscription.next_billing_date)}. After that, your account will be downgraded to the free tier.`
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => setShowConfirmation(false)}
              disabled={canceling}
              className={`flex-1 ${theme.button} rounded-lg py-3 font-medium`}
            >
              Go Back
            </button>
            <button
              onClick={handleConfirmCancellation}
              disabled={canceling}
              className={`flex-1 bg-red-600 hover:bg-red-500 text-white rounded-lg py-3 font-medium transition-colors ${
                canceling ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {canceling ? 'Canceling...' : 'Yes, Cancel Subscription'}
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Cancellation Form
  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="text-center py-8">
        <ExclamationTriangleIcon className="w-20 h-20 mx-auto mb-4 text-red-400" />
        <h1 className={`text-4xl font-bold ${theme.text.primary} mb-4`}>
          We're Sorry to See You Go
        </h1>
        <p className={`text-lg ${theme.text.secondary}`}>
          Before you cancel, please let us know why you're leaving
        </p>
      </div>

      {/* Main Form */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${theme.card} rounded-xl p-8`}
      >
        {/* Cancellation Reasons */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
            Why are you canceling?
          </h3>
          <div className="space-y-3">
            {CANCELLATION_REASONS.map((reason) => (
              <label
                key={reason.value}
                className={`flex items-start gap-4 p-4 rounded-lg border-2 cursor-pointer transition-all ${
                  selectedReason === reason.value
                    ? 'border-purple-500 bg-purple-500/10'
                    : 'border-slate-700 hover:border-slate-600'
                }`}
              >
                <input
                  type="radio"
                  name="cancellation_reason"
                  value={reason.value}
                  checked={selectedReason === reason.value}
                  onChange={(e) => setSelectedReason(e.target.value)}
                  className="mt-1"
                />
                <div className="flex-1">
                  <p className={`font-medium ${theme.text.primary} mb-1`}>
                    {reason.label}
                  </p>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    {reason.description}
                  </p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Feedback Textarea */}
        <div className="mb-8">
          <label className={`block text-sm font-semibold ${theme.text.primary} mb-2`}>
            What could we do better? (Optional)
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Your feedback helps us improve our service for everyone..."
            rows={4}
            className={`w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-3 ${theme.text.primary} placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
          />
          <p className={`text-xs ${theme.text.secondary} mt-2`}>
            Your feedback is valuable and will be reviewed by our team
          </p>
        </div>

        {/* Immediate Cancellation Option */}
        <div className="mb-8 border border-slate-700 rounded-lg p-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={immediate}
              onChange={(e) => setImmediate(e.target.checked)}
              className="mt-1"
            />
            <div>
              <p className={`font-medium ${theme.text.primary} mb-1`}>
                Cancel immediately
              </p>
              <p className={`text-sm ${theme.text.secondary}`}>
                By default, you'll retain access until{' '}
                <span className="font-semibold text-green-400">
                  {formatDate(currentSubscription.next_billing_date)}
                </span>
                . Check this box to cancel immediately and lose access now.
              </p>
            </div>
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          <button
            onClick={() => navigate('/admin/subscription/plan')}
            className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-3 font-medium transition-colors"
          >
            <ArrowLeftIcon className="w-4 h-4 inline mr-2" />
            Keep My Subscription
          </button>
          <button
            onClick={handleCancel}
            disabled={!selectedReason}
            className={`flex-1 bg-red-600 hover:bg-red-500 text-white rounded-lg py-3 font-medium transition-colors ${
              !selectedReason ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            Continue Cancellation
          </button>
        </div>
      </motion.div>

      {/* Alternatives Section */}
      <div className={`${theme.card} rounded-xl p-6 border border-blue-500/30 bg-blue-500/5`}>
        <h3 className={`font-semibold ${theme.text.primary} mb-4`}>
          Before you go, have you considered?
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4">
            <CheckCircleIcon className="w-10 h-10 mx-auto mb-2 text-blue-400" />
            <p className={`font-medium ${theme.text.primary} mb-1`}>Downgrade Plan</p>
            <p className={`text-xs ${theme.text.secondary}`}>
              Lower your cost while keeping essential features
            </p>
            <button
              onClick={() => navigate('/admin/subscription/downgrade')}
              className="mt-2 text-blue-400 hover:text-blue-300 text-sm font-medium"
            >
              View Lower Plans →
            </button>
          </div>

          <div className="text-center p-4">
            <CheckCircleIcon className="w-10 h-10 mx-auto mb-2 text-green-400" />
            <p className={`font-medium ${theme.text.primary} mb-1`}>Pause Subscription</p>
            <p className={`text-xs ${theme.text.secondary}`}>
              Take a break for up to 3 months
            </p>
            <button
              className="mt-2 text-green-400 hover:text-green-300 text-sm font-medium"
            >
              Pause Instead →
            </button>
          </div>

          <div className="text-center p-4">
            <CheckCircleIcon className="w-10 h-10 mx-auto mb-2 text-purple-400" />
            <p className={`font-medium ${theme.text.primary} mb-1`}>Contact Support</p>
            <p className={`text-xs ${theme.text.secondary}`}>
              Let us help solve any issues you're facing
            </p>
            <button
              className="mt-2 text-purple-400 hover:text-purple-300 text-sm font-medium"
            >
              Get Help →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
