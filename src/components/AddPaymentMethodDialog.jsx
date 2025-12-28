/**
 * Add Payment Method Dialog Component
 * Dialog with Stripe Elements for adding a new payment method
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { toast } from 'react-hot-toast';
import axios from 'axios';

/**
 * Stripe CardElement custom styling
 */
const CARD_ELEMENT_OPTIONS = {
  style: {
    base: {
      fontSize: '16px',
      color: '#424770',
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      '::placeholder': {
        color: '#aab7c4'
      },
      iconColor: '#666EE8'
    },
    invalid: {
      color: '#fa755a',
      iconColor: '#fa755a'
    }
  },
  hidePostalCode: false
};

/**
 * AddPaymentMethodDialog Component
 *
 * @param {boolean} open - Whether dialog is open
 * @param {function} onClose - Callback when dialog closes
 * @param {function} onSuccess - Callback when payment method is added successfully
 */
export const AddPaymentMethodDialog = ({ open, onClose, onSuccess }) => {
  const stripe = useStripe();
  const elements = useElements();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cardComplete, setCardComplete] = useState(false);

  // Billing details state
  const [billingName, setBillingName] = useState('');
  const [addressLine1, setAddressLine1] = useState('');
  const [addressLine2, setAddressLine2] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('US');

  // Reset form when dialog opens
  useEffect(() => {
    if (open) {
      setBillingName('');
      setAddressLine1('');
      setAddressLine2('');
      setCity('');
      setState('');
      setPostalCode('');
      setCountry('US');
      setError(null);
      setCardComplete(false);
    }
  }, [open]);

  /**
   * Handle card element changes
   */
  const handleCardChange = (event) => {
    setCardComplete(event.complete);
    if (event.error) {
      setError(event.error.message);
    } else {
      setError(null);
    }
  };

  /**
   * Validate form
   */
  const validateForm = () => {
    if (!billingName.trim()) {
      setError('Please enter the name on the card');
      return false;
    }

    if (!addressLine1.trim()) {
      setError('Please enter your billing address');
      return false;
    }

    if (!city.trim()) {
      setError('Please enter your city');
      return false;
    }

    if (!postalCode.trim()) {
      setError('Please enter your postal code');
      return false;
    }

    if (!cardComplete) {
      setError('Please complete the card information');
      return false;
    }

    if (!stripe || !elements) {
      setError('Stripe is not loaded. Please refresh the page.');
      return false;
    }

    return true;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Step 1: Get SetupIntent client_secret from backend
      const setupResponse = await axios.post(
        '/api/v1/payment-methods/setup-intent',
        {},
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      const { client_secret } = setupResponse.data;

      if (!client_secret) {
        throw new Error('Failed to create payment setup');
      }

      // Step 2: Confirm card setup with Stripe
      const cardElement = elements.getElement(CardElement);

      const { error: stripeError, setupIntent } = await stripe.confirmCardSetup(
        client_secret,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: billingName,
              address: {
                line1: addressLine1,
                line2: addressLine2 || undefined,
                city: city,
                state: state || undefined,
                postal_code: postalCode,
                country: country
              }
            }
          }
        }
      );

      if (stripeError) {
        throw new Error(stripeError.message);
      }

      if (setupIntent.status !== 'succeeded') {
        throw new Error('Payment method setup failed');
      }

      // Success!
      toast.success('Payment method added successfully');
      onSuccess && onSuccess();
      onClose();

    } catch (err) {
      console.error('Error adding payment method:', err);

      // User-friendly error messages
      let errorMessage = 'Failed to add payment method. Please try again.';

      if (err.response) {
        errorMessage = err.response.data?.detail || errorMessage;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Handle dialog close
   */
  const handleClose = () => {
    if (!loading) {
      onClose();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      disableEscapeKeyDown={loading}
    >
      <form onSubmit={handleSubmit}>
        <DialogTitle>Add Payment Method</DialogTitle>

        <DialogContent>
          <Box sx={{ pt: 1 }}>
            {/* Name on card */}
            <TextField
              label="Name on Card"
              fullWidth
              margin="normal"
              value={billingName}
              onChange={(e) => setBillingName(e.target.value)}
              required
              disabled={loading}
              autoComplete="cc-name"
            />

            {/* Stripe CardElement */}
            <Box sx={{ mt: 3, mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Card Information
              </Typography>
              <Box
                sx={{
                  p: 2,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  bgcolor: loading ? 'action.disabledBackground' : 'background.paper',
                  '&:hover': {
                    borderColor: loading ? 'divider' : 'primary.main'
                  },
                  '&:focus-within': {
                    borderColor: 'primary.main',
                    borderWidth: '2px'
                  }
                }}
              >
                <CardElement
                  options={CARD_ELEMENT_OPTIONS}
                  onChange={handleCardChange}
                />
              </Box>
            </Box>

            {/* Billing address */}
            <Typography variant="h6" sx={{ mt: 3, mb: 1 }}>
              Billing Address
            </Typography>

            <TextField
              label="Address Line 1"
              fullWidth
              margin="normal"
              value={addressLine1}
              onChange={(e) => setAddressLine1(e.target.value)}
              required
              disabled={loading}
              autoComplete="address-line1"
            />

            <TextField
              label="Address Line 2 (Optional)"
              fullWidth
              margin="normal"
              value={addressLine2}
              onChange={(e) => setAddressLine2(e.target.value)}
              disabled={loading}
              autoComplete="address-line2"
            />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="City"
                  fullWidth
                  margin="normal"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  required
                  disabled={loading}
                  autoComplete="address-level2"
                />
              </Grid>

              <Grid item xs={12} sm={3}>
                <TextField
                  label="State"
                  fullWidth
                  margin="normal"
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  disabled={loading}
                  autoComplete="address-level1"
                />
              </Grid>

              <Grid item xs={12} sm={3}>
                <TextField
                  label="ZIP"
                  fullWidth
                  margin="normal"
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                  required
                  disabled={loading}
                  autoComplete="postal-code"
                />
              </Grid>
            </Grid>

            <TextField
              label="Country"
              fullWidth
              margin="normal"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              required
              disabled={loading}
              autoComplete="country"
              helperText="Two-letter country code (e.g., US, CA, GB)"
            />

            {/* Error display */}
            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            {/* Test card info */}
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Test Card:</strong> 4242 4242 4242 4242
              </Typography>
              <Typography variant="caption">
                Use any future expiration date and any 3-digit CVC
              </Typography>
            </Alert>
          </Box>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Button
            type="submit"
            variant="contained"
            disabled={!stripe || loading || !cardComplete}
            startIcon={loading && <CircularProgress size={20} />}
          >
            {loading ? 'Adding...' : 'Add Card'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default AddPaymentMethodDialog;
