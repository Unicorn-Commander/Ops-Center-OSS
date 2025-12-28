import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, Box, Button,
  Divider, Chip, Alert, LinearProgress, List, ListItem,
  ListItemText, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, TextField, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Paper
} from '@mui/material';
import {
  CreditCard, CalendarToday, TrendingUp, Receipt, Edit,
  Cancel, CheckCircle, Warning, Info, Download, Refresh
} from '@mui/icons-material';
import TierBadge from './TierBadge';
import FeatureMatrix from './FeatureMatrix';
import UpgradePrompt from './UpgradePrompt';

/**
 * SubscriptionManagement Component
 *
 * Complete subscription management page with:
 * - Current plan details
 * - Billing cycle information
 * - Usage statistics
 * - Payment method management
 * - Invoice history
 * - Upgrade/downgrade options
 *
 * Props:
 * - userInfo: User account information
 * - refreshUserInfo: Callback to refresh user data
 * - showSnackbar: Snackbar notification function
 */
export default function SubscriptionManagement({
  userInfo,
  refreshUserInfo,
  showSnackbar
}) {
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [paymentMethod, setPaymentMethod] = useState(null);
  const [cancelDialog, setCancelDialog] = useState(false);
  const [updatePaymentDialog, setUpdatePaymentDialog] = useState(false);
  const [upgradeDialog, setUpgradeDialog] = useState({ open: false, tier: null });

  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    setLoading(true);
    try {
      // Fetch subscription details
      const subResponse = await fetch('/api/v1/billing/subscription', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });
      if (subResponse.ok) {
        const subData = await subResponse.json();
        setSubscription(subData);
      }

      // Fetch usage stats
      const usageResponse = await fetch('/api/v1/billing/account/usage', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });
      if (usageResponse.ok) {
        const usageData = await usageResponse.json();
        setUsage(usageData);
      }

      // Fetch invoices
      const invoiceResponse = await fetch('/api/v1/billing/invoices', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });
      if (invoiceResponse.ok) {
        const invoiceData = await invoiceResponse.json();
        setInvoices(invoiceData.invoices || []);
      }

      // Fetch payment method
      const paymentResponse = await fetch('/api/v1/billing/payment-method', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });
      if (paymentResponse.ok) {
        const paymentData = await paymentResponse.json();
        setPaymentMethod(paymentData);
      }
    } catch (err) {
      console.error('Failed to fetch subscription data:', err);
      showSnackbar('Failed to load subscription data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleCancelSubscription = async () => {
    try {
      const response = await fetch('/api/v1/billing/subscription/cancel', {
        method: 'POST',
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) throw new Error('Failed to cancel subscription');

      showSnackbar('Subscription cancelled successfully');
      setCancelDialog(false);
      fetchSubscriptionData();
      refreshUserInfo();
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const handleUpdatePaymentMethod = async () => {
    try {
      const response = await fetch('/api/v1/billing/payment-method/update', {
        method: 'POST',
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) throw new Error('Failed to update payment method');

      const data = await response.json();
      // Redirect to Stripe payment update page
      window.open(data.update_url, '_blank');
      setUpdatePaymentDialog(false);
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const handleUpgrade = (tier) => {
    setUpgradeDialog({ open: true, tier });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusColor = (status) => {
    const colors = {
      active: 'success',
      trialing: 'info',
      past_due: 'warning',
      canceled: 'error',
      incomplete: 'warning'
    };
    return colors[status] || 'default';
  };

  if (loading) {
    return (
      <Box p={3}>
        <LinearProgress />
        <Typography variant="body2" color="textSecondary" textAlign="center" mt={2}>
          Loading subscription details...
        </Typography>
      </Box>
    );
  }

  return (
    <Box>
      <Grid container spacing={3}>
        {/* Page Header */}
        <Grid item xs={12}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h4" fontWeight="bold">
              💳 Subscription Management
            </Typography>
            <TierBadge
              tier={userInfo?.subscription_tier || 'free'}
              usage={usage?.current_month ? {
                used: usage.current_month.tokens_used,
                limit: usage.current_month.tokens_limit,
                percentage: (usage.current_month.tokens_used / usage.current_month.tokens_limit) * 100
              } : null}
              showUsage={true}
            />
          </Box>
        </Grid>

        {/* Current Plan Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <CheckCircle sx={{ mr: 1, color: 'success.main' }} />
                <Typography variant="h6">Current Plan</Typography>
              </Box>

              <Box mb={2}>
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {userInfo?.subscription_tier?.toUpperCase() || 'FREE'}
                </Typography>
                {subscription?.price && (
                  <Typography variant="h5" color="textSecondary">
                    ${subscription.price}
                    <Typography variant="body2" component="span"> /month</Typography>
                  </Typography>
                )}
              </Box>

              <List dense>
                <ListItem>
                  <CalendarToday sx={{ mr: 2, color: 'primary.main' }} />
                  <ListItemText
                    primary="Billing Cycle"
                    secondary={subscription?.billing_cycle || 'Monthly'}
                  />
                </ListItem>
                {subscription?.next_billing_date && (
                  <ListItem>
                    <TrendingUp sx={{ mr: 2, color: 'primary.main' }} />
                    <ListItemText
                      primary="Next Payment"
                      secondary={formatDate(subscription.next_billing_date)}
                    />
                  </ListItem>
                )}
                <ListItem>
                  <Info sx={{ mr: 2, color: 'primary.main' }} />
                  <ListItemText
                    primary="Status"
                    secondary={
                      <Chip
                        label={subscription?.status?.toUpperCase() || 'ACTIVE'}
                        color={getStatusColor(subscription?.status)}
                        size="small"
                      />
                    }
                  />
                </ListItem>
              </List>

              <Divider sx={{ my: 2 }} />

              {userInfo?.subscription_tier !== 'enterprise' && (
                <Button
                  variant="contained"
                  fullWidth
                  onClick={() => handleUpgrade('professional')}
                  sx={{
                    background: 'linear-gradient(135deg, #6f42c1, #d4af37)',
                    mb: 1
                  }}
                >
                  🚀 Upgrade Plan
                </Button>
              )}

              {subscription?.status === 'active' && userInfo?.subscription_tier !== 'free' && (
                <Button
                  variant="outlined"
                  fullWidth
                  color="error"
                  onClick={() => setCancelDialog(true)}
                >
                  Cancel Subscription
                </Button>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Usage Statistics Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Usage This Month</Typography>
                <IconButton size="small" sx={{ ml: 'auto' }} onClick={fetchSubscriptionData}>
                  <Refresh />
                </IconButton>
              </Box>

              {usage?.current_month ? (
                <>
                  <Box mb={3}>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">API Calls</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {usage.current_month.tokens_used?.toLocaleString() || 0} / {
                          usage.current_month.tokens_limit === -1
                            ? '∞'
                            : usage.current_month.tokens_limit?.toLocaleString()
                        }
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min(100, (usage.current_month.tokens_used / usage.current_month.tokens_limit) * 100)}
                      sx={{ height: 8, borderRadius: 1 }}
                      color={(usage.current_month.tokens_used / usage.current_month.tokens_limit) > 0.8 ? 'warning' : 'primary'}
                    />
                  </Box>

                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Requests
                      </Typography>
                      <Typography variant="h5">
                        {usage.current_month.requests?.toLocaleString() || 0}
                      </Typography>
                    </Grid>
                    <Grid item xs={6}>
                      <Typography variant="body2" color="textSecondary">
                        Estimated Cost
                      </Typography>
                      <Typography variant="h5" color="primary">
                        ${usage.current_month.cost?.toFixed(2) || '0.00'}
                      </Typography>
                    </Grid>
                  </Grid>

                  {(usage.current_month.tokens_used / usage.current_month.tokens_limit) > 0.8 && (
                    <Alert severity="warning" sx={{ mt: 2 }} icon={<Warning />}>
                      You've used {((usage.current_month.tokens_used / usage.current_month.tokens_limit) * 100).toFixed(0)}% of your monthly limit.
                      Consider upgrading to avoid service interruption.
                    </Alert>
                  )}
                </>
              ) : (
                <Typography color="textSecondary">No usage data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Payment Method Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Box display="flex" alignItems="center">
                  <CreditCard sx={{ mr: 1, color: 'primary.main' }} />
                  <Typography variant="h6">Payment Method</Typography>
                </Box>
                {paymentMethod && (
                  <IconButton size="small" onClick={() => setUpdatePaymentDialog(true)}>
                    <Edit />
                  </IconButton>
                )}
              </Box>

              {paymentMethod ? (
                <Box>
                  <Typography variant="body1" mb={1}>
                    {paymentMethod.brand?.toUpperCase()} •••• {paymentMethod.last4}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Expires {paymentMethod.exp_month}/{paymentMethod.exp_year}
                  </Typography>
                </Box>
              ) : (
                <Box>
                  <Typography variant="body2" color="textSecondary" mb={2}>
                    No payment method on file
                  </Typography>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => setUpdatePaymentDialog(true)}
                  >
                    Add Payment Method
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Invoice History Card */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Receipt sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Invoice History</Typography>
              </Box>

              {invoices.length > 0 ? (
                <TableContainer component={Paper} sx={{ maxHeight: 300, bgcolor: 'transparent' }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell>Amount</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Action</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {invoices.map((invoice) => (
                        <TableRow key={invoice.id} hover>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDate(invoice.date)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2" fontWeight="medium">
                              ${invoice.amount?.toFixed(2)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={invoice.status}
                              size="small"
                              color={invoice.status === 'paid' ? 'success' : 'warning'}
                            />
                          </TableCell>
                          <TableCell>
                            <IconButton
                              size="small"
                              onClick={() => window.open(invoice.pdf_url, '_blank')}
                            >
                              <Download />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  No invoices available
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Feature Matrix */}
        <Grid item xs={12}>
          <FeatureMatrix
            currentTier={userInfo?.subscription_tier || 'free'}
            onUpgradeClick={handleUpgrade}
          />
        </Grid>
      </Grid>

      {/* Cancel Subscription Dialog */}
      <Dialog open={cancelDialog} onClose={() => setCancelDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Cancel Subscription?</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Are you sure you want to cancel your subscription? You'll lose access to premium features at the end of your billing cycle.
          </Alert>
          <Typography variant="body2" color="textSecondary">
            Your subscription will remain active until {formatDate(subscription?.next_billing_date)}.
            After that, your account will be downgraded to the Free tier.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialog(false)}>Keep Subscription</Button>
          <Button onClick={handleCancelSubscription} color="error" variant="contained">
            Confirm Cancellation
          </Button>
        </DialogActions>
      </Dialog>

      {/* Update Payment Method Dialog */}
      <Dialog open={updatePaymentDialog} onClose={() => setUpdatePaymentDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Update Payment Method</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" mb={2}>
            You'll be redirected to Stripe to securely update your payment method.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpdatePaymentDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdatePaymentMethod} variant="contained" color="primary">
            Continue to Stripe
          </Button>
        </DialogActions>
      </Dialog>

      {/* Upgrade Dialog */}
      <UpgradePrompt
        open={upgradeDialog.open}
        onClose={() => setUpgradeDialog({ open: false, tier: null })}
        feature="advanced features"
        requiredTier={upgradeDialog.tier || 'Professional'}
        currentTier={userInfo?.subscription_tier || 'free'}
        variant="modal"
      />
    </Box>
  );
}
