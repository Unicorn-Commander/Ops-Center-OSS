/**
 * UpgradeFlow Component
 *
 * Step-by-step upgrade/downgrade flow with:
 * - Step 1: Tier selection
 * - Step 2: Review changes & proration preview
 * - Step 3: Confirm & redirect to Stripe Checkout
 *
 * Epic 2.4: Self-Service Upgrades
 */

import React, { useState, useEffect } from 'react';
import {
  Box, Container, Stepper, Step, StepLabel, Card, CardContent,
  Typography, Button, Alert, CircularProgress, Divider,
  Table, TableBody, TableRow, TableCell, Chip, Paper
} from '@mui/material';
import {
  ArrowBack, ArrowForward, Check, Warning, TrendingUp, TrendingDown
} from '@mui/icons-material';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import TierComparison from '../components/TierComparison';
import { tierFeatures, compareTiers, getPriceDifference } from '../data/tierFeatures';

const steps = ['Select Plan', 'Review Changes', 'Confirm'];

export default function UpgradeFlow() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { currentTheme } = useTheme();

  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // State
  const [currentTier, setCurrentTier] = useState(null);
  const [selectedTier, setSelectedTier] = useState(searchParams.get('tier') || null);
  const [subscription, setSubscription] = useState(null);
  const [prorationPreview, setProrationPreview] = useState(null);

  // Fetch current subscription on mount
  useEffect(() => {
    fetchCurrentSubscription();
  }, []);

  // Fetch proration when tier selected
  useEffect(() => {
    if (selectedTier && currentTier && selectedTier !== currentTier) {
      fetchProrationPreview();
    }
  }, [selectedTier, currentTier]);

  const fetchCurrentSubscription = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/subscriptions/current', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to fetch current subscription');
      }

      const data = await response.json();
      setCurrentTier(data.tier || 'trial');
      setSubscription(data);
    } catch (err) {
      console.error('Error fetching subscription:', err);
      setError('Unable to load your current subscription. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchProrationPreview = async () => {
    if (!selectedTier || !currentTier) return;

    try {
      const response = await fetch('/api/v1/subscriptions/proration-preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          currentTier,
          targetTier: selectedTier
        })
      });

      if (response.ok) {
        const data = await response.json();
        setProrationPreview(data);
      }
    } catch (err) {
      console.error('Error fetching proration:', err);
      // Non-critical, can proceed without proration preview
    }
  };

  const handleSelectTier = (tierCode) => {
    if (tierCode === currentTier) {
      setError('This is already your current plan.');
      return;
    }

    setSelectedTier(tierCode);
    setError(null);
    setActiveStep(1); // Move to review step
  };

  const handleNext = () => {
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
    setError(null);
  };

  const handleConfirm = async () => {
    if (!selectedTier) {
      setError('Please select a plan to continue.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const isUpgrade = compareTiers(currentTier, selectedTier) === -1;
      const endpoint = isUpgrade
        ? '/api/v1/subscriptions/upgrade'
        : '/api/v1/subscriptions/downgrade';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          targetTier: selectedTier
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to process subscription change');
      }

      const data = await response.json();

      // If Stripe Checkout URL provided, redirect
      if (data.checkoutUrl) {
        window.location.href = data.checkoutUrl;
      } else {
        // Immediate change (e.g., downgrade scheduled for next billing cycle)
        alert('Subscription change scheduled successfully!');
        navigate('/admin/subscription/plan');
      }
    } catch (err) {
      console.error('Error changing subscription:', err);
      setError(err.message || 'An error occurred. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <TierComparison
            currentTier={currentTier}
            onSelectTier={handleSelectTier}
          />
        );

      case 1:
        return renderReviewStep();

      case 2:
        return renderConfirmStep();

      default:
        return null;
    }
  };

  const renderReviewStep = () => {
    if (!selectedTier || !currentTier) {
      return <CircularProgress />;
    }

    const currentPlan = tierFeatures[currentTier];
    const selectedPlan = tierFeatures[selectedTier];
    const isUpgrade = compareTiers(currentTier, selectedTier) === -1;
    const priceDiff = getPriceDifference(currentTier, selectedTier);

    return (
      <Box sx={{ maxWidth: 800, mx: 'auto' }}>
        <Card>
          <CardContent>
            <Typography variant="h5" fontWeight={600} gutterBottom>
              Review Your Changes
            </Typography>

            <Alert severity={isUpgrade ? 'info' : 'warning'} sx={{ mb: 3 }}>
              {isUpgrade ? (
                <>
                  <TrendingUp sx={{ mr: 1 }} />
                  You're upgrading to {selectedPlan.name}. Your new features will be available immediately.
                </>
              ) : (
                <>
                  <TrendingDown sx={{ mr: 1 }} />
                  You're downgrading to {selectedPlan.name}. Changes take effect at the end of your billing cycle.
                </>
              )}
            </Alert>

            <Divider sx={{ my: 3 }} />

            {/* Current vs New Plan */}
            <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
              <Box sx={{ flex: 1 }}>
                <Typography variant="overline" color="textSecondary">
                  Current Plan
                </Typography>
                <Typography variant="h6">{currentPlan.name}</Typography>
                <Typography variant="body2" color="textSecondary">
                  {currentPlan.price}/{currentPlan.period}
                </Typography>
              </Box>
              <ArrowForward sx={{ alignSelf: 'center', color: 'text.secondary' }} />
              <Box sx={{ flex: 1 }}>
                <Typography variant="overline" color="textSecondary">
                  New Plan
                </Typography>
                <Typography variant="h6" color="primary.main">
                  {selectedPlan.name}
                </Typography>
                <Typography variant="body2" color="primary.main">
                  {selectedPlan.price}/{selectedPlan.period}
                </Typography>
              </Box>
            </Box>

            {/* Price Difference */}
            <Paper variant="outlined" sx={{ p: 2, mb: 3 }}>
              <Table size="small">
                <TableBody>
                  <TableRow>
                    <TableCell>Price Difference</TableCell>
                    <TableCell align="right">
                      <Chip
                        label={`${priceDiff > 0 ? '+' : ''}${priceDiff.toFixed(2)} USD/month`}
                        color={priceDiff > 0 ? 'primary' : 'success'}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                  {prorationPreview && (
                    <>
                      <TableRow>
                        <TableCell>Prorated Amount Due Today</TableCell>
                        <TableCell align="right">
                          ${prorationPreview.amountDue?.toFixed(2) || '0.00'}
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Next Billing Date</TableCell>
                        <TableCell align="right">
                          {prorationPreview.nextBillingDate || 'N/A'}
                        </TableCell>
                      </TableRow>
                    </>
                  )}
                </TableBody>
              </Table>
            </Paper>

            {/* Action Buttons */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={handleBack}
                startIcon={<ArrowBack />}
                fullWidth
              >
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<ArrowForward />}
                fullWidth
              >
                Continue
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  };

  const renderConfirmStep = () => {
    if (!selectedTier || !currentTier) {
      return <CircularProgress />;
    }

    const selectedPlan = tierFeatures[selectedTier];
    const isUpgrade = compareTiers(currentTier, selectedTier) === -1;

    return (
      <Box sx={{ maxWidth: 600, mx: 'auto' }}>
        <Card>
          <CardContent sx={{ textAlign: 'center' }}>
            <Box sx={{ mb: 3 }}>
              {isUpgrade ? (
                <TrendingUp sx={{ fontSize: 80, color: 'primary.main' }} />
              ) : (
                <TrendingDown sx={{ fontSize: 80, color: 'warning.main' }} />
              )}
            </Box>

            <Typography variant="h4" fontWeight={600} gutterBottom>
              {isUpgrade ? 'Confirm Upgrade' : 'Confirm Downgrade'}
            </Typography>

            <Typography variant="body1" color="textSecondary" sx={{ mb: 4 }}>
              You're about to {isUpgrade ? 'upgrade' : 'downgrade'} to the {selectedPlan.name} plan.
            </Typography>

            <Alert severity="info" sx={{ mb: 4, textAlign: 'left' }}>
              {isUpgrade ? (
                <>
                  <strong>What happens next:</strong>
                  <ul>
                    <li>You'll be redirected to Stripe Checkout to complete payment</li>
                    <li>Your new features will be available immediately after payment</li>
                    <li>You'll receive a confirmation email with invoice details</li>
                  </ul>
                </>
              ) : (
                <>
                  <strong>What happens next:</strong>
                  <ul>
                    <li>Your downgrade will be scheduled for the end of your billing cycle</li>
                    <li>You'll retain all current features until then</li>
                    <li>You'll receive a confirmation email</li>
                  </ul>
                </>
              )}
            </Alert>

            {error && (
              <Alert severity="error" sx={{ mb: 3 }}>
                {error}
              </Alert>
            )}

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="outlined"
                onClick={handleBack}
                startIcon={<ArrowBack />}
                fullWidth
                disabled={loading}
              >
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleConfirm}
                endIcon={loading ? <CircularProgress size={20} /> : <Check />}
                fullWidth
                disabled={loading}
              >
                {loading ? 'Processing...' : isUpgrade ? 'Proceed to Payment' : 'Confirm Downgrade'}
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    );
  };

  if (!currentTier) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Stepper */}
      <Stepper activeStep={activeStep} sx={{ mb: 6 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      {/* Error Alert */}
      {error && activeStep !== 2 && (
        <Alert severity="error" sx={{ mb: 4 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Step Content */}
      {renderStepContent()}
    </Container>
  );
}
