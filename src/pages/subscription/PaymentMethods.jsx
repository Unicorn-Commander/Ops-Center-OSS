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
import { toast } from 'react-hot-toast';
import axios from 'axios';

import { StripeProvider } from '../../components/StripeProvider';
import { PaymentMethodCard } from '../../components/PaymentMethodCard';
import { AddPaymentMethodDialog } from '../../components/AddPaymentMethodDialog';
import { UpcomingInvoiceCard } from '../../components/UpcomingInvoiceCard';

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

  // Fetch on mount
  useEffect(() => {
    fetchPaymentMethods();
  }, []);

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
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          <CreditCardIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: '2rem' }} />
          Payment Methods
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage your saved payment methods and billing information
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Payment Methods List */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Saved Payment Methods
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddPaymentMethod}
                disabled={actionLoading}
              >
                Add Payment Method
              </Button>
            </Box>

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

      {/* Add Payment Method Dialog (wrapped in Stripe provider) */}
      <StripeProvider>
        <AddPaymentMethodDialog
          open={addDialogOpen}
          onClose={() => setAddDialogOpen(false)}
          onSuccess={handleAddSuccess}
        />
      </StripeProvider>
    </Container>
  );
};

export default PaymentMethods;
