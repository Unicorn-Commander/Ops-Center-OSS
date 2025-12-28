import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  CreditCardIcon,
  PlusCircleIcon,
  TrashIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';
import { useToast } from '../../components/Toast';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';

// Animation variants
const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

// Initialize Stripe (replace with your publishable key)
const stripePromise = loadStripe(window.STRIPE_PUBLISHABLE_KEY || 'pk_test_YOUR_KEY');

// Card element options
const cardElementOptions = {
  style: {
    base: {
      fontSize: '16px',
      color: '#fff',
      '::placeholder': {
        color: '#94a3b8'
      },
      backgroundColor: 'transparent'
    },
    invalid: {
      color: '#ef4444'
    }
  },
  hidePostalCode: false
};

// Add Payment Method Form Component
function AddPaymentMethodForm({ onSuccess, onCancel, theme }) {
  const stripe = useStripe();
  const elements = useElements();
  const toast = useToast();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cardholderName, setCardholderName] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create payment method
      const { error: stripeError, paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: elements.getElement(CardElement),
        billing_details: {
          name: cardholderName
        }
      });

      // Handle Stripe-specific errors - don't retry failed payments
      if (stripeError) {
        if (stripeError.decline_code) {
          // Card declined - specific error for user
          const errorMsg = `Card declined: ${stripeError.decline_code}`;
          setError(errorMsg);
          toast.error(errorMsg);
        } else if (stripeError.type === 'validation_error') {
          // Validation error - show specific message
          const errorMsg = `Validation error: ${stripeError.message}`;
          setError(errorMsg);
          toast.error(errorMsg);
        } else if (stripeError.type === 'card_error') {
          // Card error - show specific message
          const errorMsg = `Card error: ${stripeError.message}`;
          setError(errorMsg);
          toast.error(errorMsg);
        } else {
          // Generic Stripe error
          setError(stripeError.message);
          toast.error(stripeError.message);
        }
        setLoading(false);
        return;
      }

      // Attach payment method to customer
      const res = await fetch('/api/v1/billing/payment-methods', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_method_id: paymentMethod.id,
          set_default: true
        })
      });

      if (!res.ok) {
        const data = await res.json();
        const errorMsg = data.error || 'Failed to add payment method';
        setError(errorMsg);
        toast.error(errorMsg);
        return;
      }

      // Success - call onSuccess callback
      toast.success('Payment method added successfully');
      onSuccess();
    } catch (error) {
      console.error('Error adding payment method:', error);
      const errorMsg = `Network error: ${error.message || 'Unable to connect to payment server'}`;
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
          Cardholder Name
        </label>
        <input
          type="text"
          value={cardholderName}
          onChange={(e) => setCardholderName(e.target.value)}
          placeholder="John Doe"
          required
          className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:border-purple-500"
        />
      </div>

      <div>
        <label className={`block text-sm font-medium ${theme.text.primary} mb-2`}>
          Card Details
        </label>
        <div className="p-4 bg-slate-700/50 border border-slate-600 rounded-lg">
          <CardElement options={cardElementOptions} />
        </div>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 flex items-start gap-2">
          <ExclamationTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      <div className="flex gap-3">
        <button
          type="submit"
          disabled={!stripe || loading}
          className={`flex-1 ${theme.button} rounded-lg py-2 px-4 text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? 'Adding...' : 'Add Payment Method'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={loading}
          className="flex-1 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg py-2 px-4 text-sm font-medium transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}

// Empty state component
const EmptyState = ({ onAddClick, theme }) => (
  <div className="text-center py-12">
    <CreditCardIcon className="w-16 h-16 mx-auto mb-4 text-slate-500" />
    <h3 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>No Payment Methods</h3>
    <p className={`${theme.text.secondary} mb-6`}>Add a payment method to manage your subscription</p>
    <button
      onClick={onAddClick}
      className={`${theme.button} rounded-lg py-2 px-6 text-sm font-medium`}
    >
      <PlusCircleIcon className="w-4 h-4 inline mr-2" />
      Add Card
    </button>
  </div>
);

// Main Component
function SubscriptionPaymentContent() {
  const { theme } = useTheme();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;

  useEffect(() => {
    loadPaymentMethods();
  }, []);

  const loadPaymentMethods = async (isRetry = false) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch('/api/v1/billing/payment-methods');
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      const data = await res.json();
      setPaymentMethods(data);
      setRetryCount(0); // Reset retry count on success

      // Only show success toast if it's a retry
      if (isRetry) {
        toast.success('Payment methods loaded successfully');
      }
    } catch (error) {
      console.error('Error loading payment methods:', error);
      const errorMsg = `Failed to load payment methods: ${error.message}`;
      setError(errorMsg);

      // Retry logic with exponential backoff
      if (retryCount < maxRetries) {
        const backoffDelay = 2000 * (retryCount + 1);
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          loadPaymentMethods(true);
        }, backoffDelay);
        toast.warning(`Loading payment methods... Retry ${retryCount + 1}/${maxRetries}`);
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setRetryCount(0); // Reset retry count for manual refresh
    await loadPaymentMethods(true); // Show success toast on manual refresh
    setRefreshing(false);
  };

  const handleSetDefault = async (paymentMethodId) => {
    try {
      const res = await fetch(`/api/v1/billing/payment-methods/${paymentMethodId}/default`, {
        method: 'POST'
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      await loadPaymentMethods();
      toast.success('Default payment method updated');
    } catch (error) {
      console.error('Error setting default payment method:', error);
      toast.error(`Failed to set default payment method: ${error.message}`);
    }
  };

  const handleRemove = async (paymentMethodId) => {
    if (!confirm('Are you sure you want to remove this payment method?')) {
      return;
    }

    try {
      const res = await fetch(`/api/v1/billing/payment-methods/${paymentMethodId}`, {
        method: 'DELETE'
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      await loadPaymentMethods();
      toast.success('Payment method removed successfully');
    } catch (error) {
      console.error('Error removing payment method:', error);
      toast.error(`Failed to remove payment method: ${error.message}`);
    }
  };

  const handleAddSuccess = async () => {
    setShowAddForm(false);
    await loadPaymentMethods();
    // Toast already shown in AddPaymentMethodForm
  };

  if (loading) {
    return (
      <div className={`${theme.card} rounded-xl p-6 animate-pulse`}>
        <div className="h-6 bg-slate-700 rounded w-1/3 mb-4"></div>
        <div className="h-32 bg-slate-700 rounded"></div>
      </div>
    );
  }

  if (error && retryCount >= maxRetries) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-red-900/20 border border-red-500/50 rounded-xl p-6"
      >
        <div className="flex items-start gap-3">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-red-200 text-sm font-medium mb-2">{error}</p>
            <p className="text-red-300 text-xs mb-3">
              Failed to load payment methods after {maxRetries} attempts. This may be due to network issues or server problems.
            </p>
          </div>
          <button
            onClick={() => {
              setRetryCount(0);
              setError(null);
              loadPaymentMethods(true);
            }}
            className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-500 transition-colors"
          >
            Retry Now
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Controls */}
      <div className="flex items-center justify-between">
        <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
          <CreditCardIcon className="w-5 h-5 text-green-400" />
          Payment Methods
        </h3>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={`flex items-center gap-2 px-3 py-2 border border-slate-600 text-slate-300 hover:bg-slate-700 rounded-lg text-sm transition-colors disabled:opacity-50`}
          >
            <ArrowPathIcon className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          {!showAddForm && paymentMethods.length > 0 && (
            <button
              onClick={() => setShowAddForm(true)}
              className="flex items-center gap-2 text-sm font-medium text-purple-400 hover:text-purple-300 transition-colors"
            >
              <PlusCircleIcon className="w-5 h-5" />
              Add Payment Method
            </button>
          )}
        </div>
      </div>

      {/* Add Payment Method Form */}
      {showAddForm && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className={`${theme.card} rounded-xl p-6`}
        >
          <h4 className={`text-md font-semibold ${theme.text.primary} mb-4`}>Add New Payment Method</h4>
          <AddPaymentMethodForm
            onSuccess={handleAddSuccess}
            onCancel={() => setShowAddForm(false)}
            theme={theme}
          />
        </motion.div>
      )}

      {/* Payment Methods List */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        {paymentMethods.length > 0 ? (
          <div className="space-y-3">
            {paymentMethods.map((method) => (
              <div
                key={method.id}
                className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-8 bg-slate-600 rounded flex items-center justify-center">
                    <CreditCardIcon className="w-6 h-6 text-slate-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className={`font-medium ${theme.text.primary}`}>
                        {method.brand?.toUpperCase() || 'CARD'} •••• {method.last4}
                      </p>
                      {method.is_default && (
                        <span className="px-2 py-1 bg-purple-500/20 text-purple-400 text-xs font-medium rounded border border-purple-500/30">
                          Default
                        </span>
                      )}
                    </div>
                    <p className={`text-sm ${theme.text.secondary}`}>
                      Expires {String(method.exp_month).padStart(2, '0')}/{method.exp_year}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {!method.is_default && (
                    <button
                      onClick={() => handleSetDefault(method.id)}
                      className="text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors"
                    >
                      Set Default
                    </button>
                  )}
                  <button
                    onClick={() => handleRemove(method.id)}
                    className="text-red-400 hover:text-red-300 transition-colors p-2"
                    disabled={method.is_default && paymentMethods.length === 1}
                    title={method.is_default && paymentMethods.length === 1 ? 'Cannot remove the only payment method' : 'Remove payment method'}
                  >
                    <TrashIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState onAddClick={() => setShowAddForm(true)} theme={theme} />
        )}
      </motion.div>

      {/* Security Notice */}
      <motion.div
        variants={itemVariants}
        className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 flex items-start gap-3"
      >
        <CheckCircleIcon className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className={`font-medium ${theme.text.primary} mb-1`}>Secure Payment Processing</p>
          <p className={theme.text.secondary}>
            All payment information is encrypted and processed securely through Stripe.
            We never store your complete card details on our servers.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

// Wrapper component with Stripe Elements
export default function SubscriptionPayment() {
  return (
    <Elements stripe={stripePromise}>
      <SubscriptionPaymentContent />
    </Elements>
  );
}
