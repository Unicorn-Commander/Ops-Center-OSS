import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  Chip,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Stack
} from '@mui/material';
import {
  ShoppingCart as ShoppingCartIcon,
  LocalOffer as OfferIcon,
  CheckCircle as CheckIcon,
  Star as StarIcon,
  History as HistoryIcon
} from '@mui/icons-material';

const CreditPurchase = () => {
  const [packages, setPackages] = useState([]);
  const [balance, setBalance] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [purchasing, setPurchasing] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Load packages and balance on mount
  useEffect(() => {
    loadData();
    checkPurchaseStatus();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load credit packages
      const packagesRes = await fetch('/api/v1/billing/credits/packages', {
        credentials: 'include'
      });

      if (!packagesRes.ok) {
        throw new Error('Failed to load credit packages');
      }

      const packagesData = await packagesRes.json();
      setPackages(packagesData);

      // Load current balance
      const balanceRes = await fetch('/api/v1/credits/balance', {
        credentials: 'include'
      });

      if (balanceRes.ok) {
        const balanceData = await balanceRes.json();
        setBalance(balanceData);
      }

      // Load purchase history
      const historyRes = await fetch('/api/v1/billing/credits/history?limit=10', {
        credentials: 'include'
      });

      if (historyRes.ok) {
        const historyData = await historyRes.json();
        setHistory(historyData);
      }

    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const checkPurchaseStatus = () => {
    // Check URL params for purchase status
    const params = new URLSearchParams(window.location.search);
    const purchaseStatus = params.get('purchase');

    if (purchaseStatus === 'success') {
      setSuccess('Purchase successful! Your credits have been added to your account.');
      // Clear URL params
      window.history.replaceState({}, '', window.location.pathname);
      // Reload data to show updated balance
      setTimeout(loadData, 2000);
    } else if (purchaseStatus === 'cancelled') {
      setError('Purchase was cancelled. No charges were made.');
      window.history.replaceState({}, '', window.location.pathname);
    }
  };

  const handlePurchase = async (packageCode) => {
    try {
      setPurchasing(packageCode);
      setError(null);

      const response = await fetch('/api/v1/billing/credits/purchase', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          package_code: packageCode
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create checkout session');
      }

      const data = await response.json();

      // Redirect to Stripe Checkout
      window.location.href = data.checkout_url;

    } catch (err) {
      console.error('Purchase failed:', err);
      setError(err.message);
      setPurchasing(null);
    }
  };

  const formatCredits = (amount) => {
    if (!amount) return '0';
    return Math.floor(parseFloat(amount)).toLocaleString();
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'pending':
        return 'warning';
      case 'failed':
        return 'error';
      case 'refunded':
        return 'info';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>Loading credit packages...</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Buy Credits
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Purchase credits to use AI models, tools, and services
        </Typography>
      </Box>

      {/* Alerts */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Current Balance */}
      {balance && (
        <Paper sx={{ p: 3, mb: 4, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Current Balance
              </Typography>
              <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
                {formatCredits(balance.balance)} credits
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Monthly Allocation: {formatCredits(balance.allocated_monthly)} credits
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9 }}>
                Tier: {balance.tier}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Credit Packages */}
      <Typography variant="h5" gutterBottom sx={{ mb: 3 }}>
        Available Packages
      </Typography>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        {packages.map((pkg) => {
          const isPurchasing = purchasing === pkg.package_code;
          const discount = pkg.discount_percentage;

          return (
            <Grid item xs={12} sm={6} md={3} key={pkg.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  '&:hover': {
                    boxShadow: 6,
                    transform: 'translateY(-4px)',
                    transition: 'all 0.3s'
                  }
                }}
              >
                {/* Discount Badge */}
                {discount > 0 && (
                  <Chip
                    icon={<OfferIcon />}
                    label={`${discount}% OFF`}
                    color="secondary"
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 16,
                      right: 16,
                      fontWeight: 'bold'
                    }}
                  />
                )}

                {/* Popular Badge */}
                {pkg.package_code === 'pro' && (
                  <Chip
                    icon={<StarIcon />}
                    label="POPULAR"
                    color="primary"
                    size="small"
                    sx={{
                      position: 'absolute',
                      top: 16,
                      left: 16,
                      fontWeight: 'bold'
                    }}
                  />
                )}

                <CardContent sx={{ flexGrow: 1, pt: 5 }}>
                  <Typography variant="h6" component="div" gutterBottom>
                    {pkg.package_name}
                  </Typography>

                  <Typography variant="h4" component="div" sx={{ my: 2, fontWeight: 'bold' }}>
                    {formatCurrency(pkg.price_usd)}
                  </Typography>

                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    {pkg.credits.toLocaleString()} credits
                  </Typography>

                  {pkg.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      {pkg.description}
                    </Typography>
                  )}

                  {/* Value calculation */}
                  <Box sx={{ mt: 2, p: 1, bgcolor: 'action.hover', borderRadius: 1 }}>
                    <Typography variant="caption" display="block">
                      ${(pkg.price_usd / pkg.credits * 1000).toFixed(2)} per 1,000 credits
                    </Typography>
                  </Box>
                </CardContent>

                <CardActions sx={{ p: 2, pt: 0 }}>
                  <Button
                    fullWidth
                    variant="contained"
                    size="large"
                    startIcon={isPurchasing ? <CircularProgress size={20} /> : <ShoppingCartIcon />}
                    disabled={isPurchasing}
                    onClick={() => handlePurchase(pkg.package_code)}
                  >
                    {isPurchasing ? 'Processing...' : 'Buy Now'}
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Purchase History */}
      {history && history.length > 0 && (
        <>
          <Divider sx={{ my: 4 }} />

          <Box sx={{ mb: 3 }}>
            <Stack direction="row" spacing={1} alignItems="center">
              <HistoryIcon />
              <Typography variant="h5">Purchase History</Typography>
            </Stack>
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>Package</TableCell>
                  <TableCell align="right">Credits</TableCell>
                  <TableCell align="right">Amount</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {history.map((purchase) => (
                  <TableRow key={purchase.id} hover>
                    <TableCell>{formatDate(purchase.created_at)}</TableCell>
                    <TableCell>{purchase.package_name}</TableCell>
                    <TableCell align="right">
                      {formatCredits(purchase.amount_credits)}
                    </TableCell>
                    <TableCell align="right">
                      {formatCurrency(purchase.amount_paid)}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={purchase.status}
                        color={getStatusColor(purchase.status)}
                        size="small"
                        icon={purchase.status === 'completed' ? <CheckIcon /> : undefined}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </>
      )}

      {/* Info Box */}
      <Paper sx={{ p: 3, mt: 4, bgcolor: 'action.hover' }}>
        <Typography variant="h6" gutterBottom>
          How Credits Work
        </Typography>
        <Stack spacing={1}>
          <Typography variant="body2">
            • Credits are used for AI model inference, embeddings, and other services
          </Typography>
          <Typography variant="body2">
            • Credits never expire and roll over month-to-month
          </Typography>
          <Typography variant="body2">
            • Larger packages include discounts for better value
          </Typography>
          <Typography variant="body2">
            • All payments are processed securely through Stripe
          </Typography>
          <Typography variant="body2">
            • Credits are added instantly after successful payment
          </Typography>
        </Stack>
      </Paper>
    </Container>
  );
};

export default CreditPurchase;
