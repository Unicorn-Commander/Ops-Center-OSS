/**
 * Upcoming Invoice Card Component
 * Displays preview of the next billing cycle
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Divider,
  Button,
  CircularProgress,
  Alert,
  Chip
} from '@mui/material';
import { toast } from 'react-hot-toast';
import axios from 'axios';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';

/**
 * Format currency
 */
const formatCurrency = (amountInCents, currency = 'usd') => {
  const amount = amountInCents / 100;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency.toUpperCase()
  }).format(amount);
};

/**
 * Format date
 */
const formatDate = (timestamp) => {
  if (!timestamp) return 'N/A';
  return new Date(timestamp * 1000).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
};

/**
 * UpcomingInvoiceCard Component
 *
 * Displays the upcoming invoice preview with payment method information
 */
export const UpcomingInvoiceCard = ({ refreshTrigger = 0 }) => {
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  /**
   * Fetch upcoming invoice
   */
  const fetchUpcomingInvoice = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(
        '/api/v1/payment-methods/upcoming-invoice',
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`
          }
        }
      );

      setInvoice(response.data);
    } catch (err) {
      console.error('Error fetching upcoming invoice:', err);

      // Handle specific error: no active subscription
      if (err.response?.status === 404) {
        setError('No upcoming invoice found. You may not have an active subscription.');
      } else {
        setError('Failed to load upcoming invoice');
      }
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount and when refresh triggered
  useEffect(() => {
    fetchUpcomingInvoice();
  }, [refreshTrigger]);

  /**
   * Render loading state
   */
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render error state
   */
  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  /**
   * Render no invoice state
   */
  if (!invoice) {
    return (
      <Card>
        <CardContent>
          <Alert severity="info">
            No upcoming invoice. Subscribe to a plan to see your next billing cycle.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card
      sx={{
        boxShadow: 3,
        border: '1px solid',
        borderColor: 'primary.main',
        position: 'sticky',
        top: 20
      }}
    >
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
          <CalendarTodayIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Next Billing Cycle
        </Typography>

        <Divider sx={{ my: 2 }} />

        {/* Amount due */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Amount Due
          </Typography>
          <Typography variant="h3" color="primary.main" sx={{ fontWeight: 700 }}>
            {formatCurrency(invoice.amount_due, invoice.currency)}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            Due on {formatDate(invoice.next_payment_attempt)}
          </Typography>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Billing period */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Billing Period
          </Typography>
          <Typography variant="body1">
            {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
          </Typography>
        </Box>

        {/* Invoice lines */}
        {invoice.lines && invoice.lines.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Items
            </Typography>
            {invoice.lines.map((line, index) => (
              <Box key={index} sx={{ mb: 1 }}>
                <Typography variant="body2">
                  {line.description}
                </Typography>
                {line.quantity > 1 && (
                  <Typography variant="caption" color="text.secondary">
                    Quantity: {line.quantity}
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Payment method */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            <CreditCardIcon sx={{ mr: 0.5, fontSize: '1rem', verticalAlign: 'middle' }} />
            Payment Method
          </Typography>
          {invoice.default_payment_method ? (
            <Box>
              <Typography variant="body1" sx={{ fontWeight: 500 }}>
                {invoice.default_payment_method.brand.toUpperCase()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                •••• •••• •••• {invoice.default_payment_method.last4}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Expires {String(invoice.default_payment_method.exp_month).padStart(2, '0')}/
                {invoice.default_payment_method.exp_year}
              </Typography>
            </Box>
          ) : (
            <Alert severity="warning" sx={{ mt: 1 }}>
              No payment method set. Please add a payment method to avoid billing issues.
            </Alert>
          )}
        </Box>

        {/* Subtotal, tax, total */}
        <Divider sx={{ my: 2 }} />

        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
            <Typography variant="body2" color="text.secondary">
              Subtotal
            </Typography>
            <Typography variant="body2">
              {formatCurrency(invoice.subtotal, invoice.currency)}
            </Typography>
          </Box>

          {invoice.tax > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
              <Typography variant="body2" color="text.secondary">
                Tax
              </Typography>
              <Typography variant="body2">
                {formatCurrency(invoice.tax, invoice.currency)}
              </Typography>
            </Box>
          )}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              Total
            </Typography>
            <Typography variant="body1" sx={{ fontWeight: 600 }}>
              {formatCurrency(invoice.total, invoice.currency)}
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Action button */}
        <Button
          variant="outlined"
          fullWidth
          startIcon={<AttachMoneyIcon />}
          href="/admin/subscription/billing"
        >
          View Billing History
        </Button>
      </CardContent>
    </Card>
  );
};

export default UpcomingInvoiceCard;
