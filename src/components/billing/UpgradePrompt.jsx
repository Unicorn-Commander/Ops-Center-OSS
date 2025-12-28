import React, { useState, useEffect } from 'react';
import {
  Dialog, DialogTitle, DialogContent, DialogActions,
  Button, Typography, Box, Card, CardContent, Chip,
  IconButton, Alert, List, ListItem, ListItemText, Divider
} from '@mui/material';
import {
  Close, Lock, TrendingUp, Star, Rocket, Warning
} from '@mui/icons-material';

/**
 * UpgradePrompt Component
 *
 * Displays when user tries to access locked features based on their tier.
 * Can be shown as modal, banner, or inline notification.
 *
 * Props:
 * - open: Boolean to control dialog visibility
 * - onClose: Callback when dialog is closed
 * - feature: String describing the locked feature
 * - requiredTier: Minimum tier required
 * - currentTier: User's current tier
 * - variant: 'modal' | 'banner' | 'inline' (default: 'modal')
 * - autoHide: Auto-dismiss after X seconds (banner only)
 */
export default function UpgradePrompt({
  open = false,
  onClose,
  feature = 'this feature',
  requiredTier = 'Starter',
  currentTier = 'Free',
  variant = 'modal',
  autoHide = null
}) {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (variant === 'banner' && autoHide && open) {
      const timer = setTimeout(() => {
        handleClose();
      }, autoHide * 1000);
      return () => clearTimeout(timer);
    }
  }, [open, autoHide, variant]);

  const handleClose = () => {
    setDismissed(true);
    if (onClose) onClose();
  };

  const handleUpgrade = () => {
    // Redirect to subscription page
    window.location.href = '/billing#plans';
  };

  const getTierIcon = (tier) => {
    switch (tier.toLowerCase()) {
      case 'free': return '🆓';
      case 'starter': return '⚡';
      case 'professional': return '💼';
      case 'enterprise': return '🏢';
      default: return '✨';
    }
  };

  const getTierColor = (tier) => {
    switch (tier.toLowerCase()) {
      case 'free': return '#6c757d';
      case 'starter': return '#0d6efd';
      case 'professional': return '#6f42c1';
      case 'enterprise': return '#d4af37';
      default: return '#6c757d';
    }
  };

  const getUpgradeReasons = () => {
    const reasons = {
      starter: [
        'Access to basic search features',
        '1,000 API calls per month',
        'BYOK (Bring Your Own Key)',
        'Priority support'
      ],
      professional: [
        'All Starter features',
        'Advanced search with reranking',
        '10,000 API calls per month',
        'Access to Lago billing dashboard',
        'TTS & STT services',
        'LiteLLM gateway with 50+ models'
      ],
      enterprise: [
        'All Professional features',
        'Unlimited API calls',
        'Team management',
        'SSO integration',
        'Audit logs',
        'Dedicated support'
      ]
    };
    return reasons[requiredTier.toLowerCase()] || reasons.starter;
  };

  // Banner variant
  if (variant === 'banner' && !dismissed) {
    return (
      <Alert
        severity="warning"
        icon={<Lock />}
        action={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button size="small" variant="contained" color="primary" onClick={handleUpgrade}>
              Upgrade Now
            </Button>
            <IconButton size="small" color="inherit" onClick={handleClose}>
              <Close />
            </IconButton>
          </Box>
        }
        sx={{
          mb: 2,
          borderLeft: `4px solid ${getTierColor(requiredTier)}`
        }}
      >
        <Typography variant="body2" fontWeight="medium">
          <strong>{feature}</strong> requires {getTierIcon(requiredTier)} {requiredTier} tier or higher
        </Typography>
      </Alert>
    );
  }

  // Inline variant
  if (variant === 'inline' && !dismissed) {
    return (
      <Card
        sx={{
          border: '2px solid',
          borderColor: getTierColor(requiredTier),
          background: `linear-gradient(135deg, rgba(0,0,0,0.7), ${getTierColor(requiredTier)}22)`,
          backdropFilter: 'blur(10px)'
        }}
      >
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <Lock sx={{ color: getTierColor(requiredTier) }} />
              <Typography variant="h6">
                {getTierIcon(requiredTier)} Upgrade Required
              </Typography>
            </Box>
            <IconButton size="small" onClick={handleClose}>
              <Close />
            </IconButton>
          </Box>

          <Typography variant="body2" color="textSecondary" mb={2}>
            <strong>{feature}</strong> is available on the <strong>{requiredTier}</strong> tier
          </Typography>

          <Box display="flex" gap={2}>
            <Button variant="contained" color="primary" onClick={handleUpgrade} startIcon={<Rocket />}>
              View Plans
            </Button>
            <Button variant="outlined" onClick={handleClose}>
              Maybe Later
            </Button>
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Modal variant (default)
  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          background: 'linear-gradient(135deg, #1a0033 0%, #3a0e5a 100%)',
          border: '2px solid',
          borderColor: getTierColor(requiredTier),
          borderRadius: 2
        }
      }}
    >
      <DialogTitle>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box display="flex" alignItems="center" gap={1}>
            <Lock sx={{ color: getTierColor(requiredTier), fontSize: 32 }} />
            <Typography variant="h5" fontWeight="bold">
              {getTierIcon(requiredTier)} Upgrade to {requiredTier}
            </Typography>
          </Box>
          <IconButton onClick={handleClose} size="small">
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent>
        {/* Current Status */}
        <Alert severity="info" icon={<Warning />} sx={{ mb: 3 }}>
          <Typography variant="body2">
            You're currently on the <Chip label={currentTier} size="small" sx={{ mx: 0.5 }} /> tier.
            To access <strong>{feature}</strong>, upgrade to <strong>{requiredTier}</strong> or higher.
          </Typography>
        </Alert>

        {/* Tier Comparison */}
        <Box mb={3}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TrendingUp /> What You'll Get with {requiredTier}
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <List dense>
            {getUpgradeReasons().map((reason, idx) => (
              <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                <ListItemText
                  primary={`✓ ${reason}`}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Box>

        {/* Pricing Preview */}
        <Card variant="outlined" sx={{ bgcolor: 'rgba(255,255,255,0.05)', mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h4" color="primary" fontWeight="bold">
                  {requiredTier === 'Starter' && '$19'}
                  {requiredTier === 'Professional' && '$49'}
                  {requiredTier === 'Enterprise' && '$99'}
                  <Typography variant="body2" component="span" color="textSecondary">
                    /month
                  </Typography>
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  Cancel anytime • No hidden fees
                </Typography>
              </Box>
              <Star sx={{ fontSize: 48, color: getTierColor(requiredTier), opacity: 0.3 }} />
            </Box>
          </CardContent>
        </Card>

        <Typography variant="caption" color="textSecondary" display="block" textAlign="center">
          🎉 Join thousands of developers building amazing AI applications
        </Typography>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose} variant="outlined">
          Maybe Later
        </Button>
        <Button
          onClick={handleUpgrade}
          variant="contained"
          color="primary"
          size="large"
          startIcon={<Rocket />}
          sx={{
            background: `linear-gradient(135deg, ${getTierColor(requiredTier)}, #d4af37)`,
            fontWeight: 'bold'
          }}
        >
          View Plans & Upgrade
        </Button>
      </DialogActions>
    </Dialog>
  );
}
