/**
 * Payment Methods Page
 * User interface for managing payment methods
 */

import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Button,
  Box,
  Alert,
  CircularProgress,
  Paper,
  Breadcrumbs,
  Link as MuiLink
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import CloudDoneIcon from '@mui/icons-material/CloudDone';
import { toast } from 'react-hot-toast';
import axios from 'axios';

import { StripeProvider } from '../../components/StripeProvider';
import { PaymentMethodCard } from '../../components/PaymentMethodCard';
import { AddPaymentMethodDialog } from '../../components/AddPaymentMethodDialog';
import { UpcomingInvoiceCard } from '../../components/UpcomingInvoiceCard';
import { useBillingConfig } from '../../hooks/useBillingConfig';
import ProvenanceBadge from '../../components/ProvenanceBadge';

/**
 * Shown when this deployment FEDERATES billing to a central hub (provider=federated).
 * Cards/invoices/credits live at the hub; the console just deep-links out.
 */
const CentralBillingPanel = ({ config }) => {
  const name = config.display_name || 'the billing hub';
  const url = config.manage_url || config.buy_credits_url || '';
  return (
    <Paper sx={{ p: { xs: 3, sm: 5 }, textAlign: 'center', borderRadius: '16px' }}>
      <Box
        sx={{
          width: 64, height: 64, borderRadius: '50%', mx: 'auto', mb: 2.5,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          background: 'rgba(103,232,249,0.10)', border: '1px solid rgba(103,232,249,0.28)',
        }}
      >
        <CloudDoneIcon sx={{ fontSize: 32, color: '#67e8f9' }} />
      </Box>
      <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
        Billing is managed centrally
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 520, mx: 'auto', mb: 1 }}>
        Your payment methods, invoices, and credits live in <strong>{name}</strong>. Manage them once
        there — your balance works across every app in the suite.
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 3 }}>
        No card details are ever stored on this server.
      </Typography>
      {url ? (
        <Button
          variant="contained"
          size="large"
          endIcon={<OpenInNewIcon />}
          onClick={() => window.open(url, '_blank', 'noopener')}
        >
          Manage billing at {name}
        </Button>
      ) : (
        <Alert severity="info" sx={{ maxWidth: 480, mx: 'auto', textAlign: 'left' }}>
          Central billing isn’t linked yet. Ask your administrator to set the billing hub URL
          (<code>BILLING_MANAGE_URL</code>).
        </Alert>
      )}
    </Paper>
  );
};

/**
 * PaymentMethods Component
 *
 * Main page for managing payment methods
 */
const PaymentMethods = () => {
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [defaultPaymentMethodId, setDefaultPaymentMethodId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Pluggable billing provider for THIS deployment (local vs. federated hub).
  const { config, loading: cfgLoading } = useBillingConfig();
  const federated = config.provider === 'federated';
  const savedCardsEnabled = config.capabilities?.saved_cards !== false;

  /**
   * Fetch payment methods
   */
  const fetchPaymentMethods = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        '/api/v1/payment-methods',
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      setPaymentMethods(response.data.payment_methods || []);
      setDefaultPaymentMethodId(response.data.default_payment_method_id);
    } catch (err) {
      console.error('Error fetching payment methods:', err);

      let errorMessage = 'Failed to load payment methods';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }

      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Only fetch local payment methods when this deployment bills locally;
  // when federated, cards live at the hub and we render the deep-link panel.
  useEffect(() => {
    if (cfgLoading) return;
    if (federated) {
      setLoading(false);
      return;
    }
    fetchPaymentMethods();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cfgLoading, federated]);

  /**
   * Handle add payment method
   */
  const handleAddPaymentMethod = () => {
    setAddDialogOpen(true);
  };

  /**
   * Handle add payment method success
   */
  const handleAddSuccess = () => {
    fetchPaymentMethods();
    setRefreshTrigger(prev => prev + 1);
  };

  /**
   * Handle set default payment method
   */
  const handleSetDefault = async (paymentMethodId) => {
    setActionLoading(true);

    try {
      await axios.post(
        `/api/v1/payment-methods/${paymentMethodId}/set-default`,
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      toast.success('Default payment method updated');
      fetchPaymentMethods();
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error('Error setting default payment method:', err);

      let errorMessage = 'Failed to set default payment method';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }

      toast.error(errorMessage);
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Handle remove payment method
   */
  const handleRemove = async (paymentMethodId) => {
    setActionLoading(true);

    try {
      await axios.delete(
        `/api/v1/payment-methods/${paymentMethodId}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      toast.success('Payment method removed');
      fetchPaymentMethods();
      setRefreshTrigger(prev => prev + 1);
    } catch (err) {
      console.error('Error removing payment method:', err);

      let errorMessage = 'Failed to remove payment method';
      if (err.response?.data?.detail) {
        errorMessage = err.response.data.detail;
      }

      // Show user-friendly error for last payment method with active subscription
      if (errorMessage.includes('last payment method')) {
        toast.error(
          'Cannot remove the last payment method while subscription is active. ' +
          'Please add another payment method first.',
          { duration: 5000 }
        );
      } else {
        toast.error(errorMessage);
      }
    } finally {
      setActionLoading(false);
    }
  };

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress size={60} />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Breadcrumbs */}
      <Breadcrumbs
        separator={<NavigateNextIcon fontSize="small" />}
        sx={{ mb: 2 }}
      >
        <MuiLink
          component={RouterLink}
          to="/admin"
          underline="hover"
          color="inherit"
        >
          Dashboard
        </MuiLink>
        <MuiLink
          component={RouterLink}
          to="/admin/subscription"
          underline="hover"
          color="inherit"
        >
          Subscription
        </MuiLink>
        <Typography color="text.primary">Payment Methods</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 0.5 }}>
          <Typography variant="h4" sx={{ fontWeight: 600 }}>
            <CreditCardIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: '2rem' }} />
            Payment Methods
          </Typography>
          <ProvenanceBadge config={config} prefix="Billing" />
        </Box>
        <Typography variant="body1" color="text.secondary">
          {federated
            ? `Billing is handled by ${config.display_name}. Manage your cards and invoices there.`
            : 'Manage your saved payment methods and billing information'}
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {federated ? (
        <CentralBillingPanel config={config} />
      ) : (
        <>
          <Grid container spacing={3}>
            {/* Payment Methods List */}
            <Grid item xs={12} md={8}>
              <Paper sx={{ p: 3 }}>
                <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Saved Payment Methods
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<AddIcon />}
                    onClick={handleAddPaymentMethod}
                    disabled={actionLoading || !savedCardsEnabled}
                  >
                    Add Payment Method
                  </Button>
                </Box>

                {!savedCardsEnabled && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    Card entry isn’t configured on this server yet — set a Stripe publishable key to enable it.
                  </Alert>
                )}

                {/* Payment methods list */}
                {paymentMethods.length === 0 ? (
                  <Alert severity="info">
                    No payment methods found. Add a payment method to enable automatic billing.
                  </Alert>
                ) : (
                  <Box>
                    {paymentMethods.map((method) => (
                      <PaymentMethodCard
                        key={method.id}
                        method={method}
                        isDefault={method.id === defaultPaymentMethodId}
                        onSetDefault={handleSetDefault}
                        onRemove={handleRemove}
                        loading={actionLoading}
                      />
                    ))}
                  </Box>
                )}

                {/* Informational alerts */}
                <Box sx={{ mt: 3 }}>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      <strong>Default Payment Method:</strong> This card will be charged automatically
                      for your subscription renewals.
                    </Typography>
                  </Alert>

                  <Alert severity="warning">
                    <Typography variant="body2">
                      <strong>Security Notice:</strong> All payment information is securely processed
                      by Stripe. We never store your full card details on our servers.
                    </Typography>
                  </Alert>
                </Box>
              </Paper>
            </Grid>

            {/* Upcoming Invoice */}
            <Grid item xs={12} md={4}>
              <UpcomingInvoiceCard refreshTrigger={refreshTrigger} />
            </Grid>
          </Grid>

          {/* Add Payment Method Dialog (wrapped in Stripe provider; runtime key) */}
          <StripeProvider publishableKey={config.stripe_publishable_key}>
            <AddPaymentMethodDialog
              open={addDialogOpen}
              onClose={() => setAddDialogOpen(false)}
              onSuccess={handleAddSuccess}
            />
          </StripeProvider>
        </>
      )}
    </Container>
  );
};

export default PaymentMethods;
