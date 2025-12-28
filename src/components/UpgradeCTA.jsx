/**
 * UpgradeCTA Component
 *
 * Reusable upgrade call-to-action banner component.
 * Shows when users hit tier limits or try to access locked features.
 *
 * Usage:
 * <UpgradeCTA
 *   feature="API calls"
 *   requiredTier="professional"
 *   variant="banner"
 * />
 *
 * Epic 2.4: Self-Service Upgrades
 */

import React, { useState } from 'react';
import {
  Alert, AlertTitle, Button, Box, Collapse, IconButton, Chip
} from '@mui/material';
import {
  Close, TrendingUp, Lock, Star, Rocket
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { tierFeatures } from '../data/tierFeatures';

/**
 * Tier icon mapping
 */
const tierIcons = {
  trial: '🔬',
  starter: '🚀',
  professional: '💼',
  enterprise: '🏢'
};

/**
 * Severity mapping for tier requirements
 */
const tierSeverity = {
  trial: 'info',
  starter: 'info',
  professional: 'warning',
  enterprise: 'error'
};

export default function UpgradeCTA({
  feature = 'this feature',
  requiredTier = 'starter',
  variant = 'banner',
  currentTier = null,
  autoHide = false,
  autoHideDuration = 10000,
  onClose = null,
  customMessage = null,
  customButtonText = null
}) {
  const navigate = useNavigate();
  const [visible, setVisible] = useState(true);

  // Auto-hide functionality
  React.useEffect(() => {
    if (autoHide && autoHideDuration) {
      const timer = setTimeout(() => {
        handleClose();
      }, autoHideDuration);

      return () => clearTimeout(timer);
    }
  }, [autoHide, autoHideDuration]);

  const handleClose = () => {
    setVisible(false);
    if (onClose) {
      onClose();
    }
  };

  const handleUpgrade = () => {
    navigate(`/admin/upgrade?tier=${requiredTier}`);
  };

  const requiredPlan = tierFeatures[requiredTier];

  if (!visible || !requiredPlan) {
    return null;
  }

  const severity = tierSeverity[requiredTier] || 'warning';
  const title = customMessage || `${tierIcons[requiredTier]} Upgrade to ${requiredPlan.name} Required`;
  const message = `Access to ${feature} requires the ${requiredPlan.name} plan or higher.`;
  const buttonText = customButtonText || `Upgrade to ${requiredPlan.name}`;

  // Banner Variant
  if (variant === 'banner') {
    return (
      <Collapse in={visible}>
        <Alert
          severity={severity}
          action={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                color="inherit"
                size="small"
                onClick={handleUpgrade}
                startIcon={<TrendingUp />}
                variant="outlined"
              >
                {buttonText}
              </Button>
              <IconButton
                size="small"
                color="inherit"
                onClick={handleClose}
              >
                <Close fontSize="small" />
              </IconButton>
            </Box>
          }
          sx={{
            mb: 3,
            '& .MuiAlert-action': {
              alignItems: 'center'
            }
          }}
        >
          <AlertTitle>{title}</AlertTitle>
          {message}
          {requiredPlan && (
            <Box sx={{ mt: 1 }}>
              <Chip
                label={`${requiredPlan.price}/${requiredPlan.period}`}
                size="small"
                color="primary"
                variant="outlined"
              />
            </Box>
          )}
        </Alert>
      </Collapse>
    );
  }

  // Inline Variant
  if (variant === 'inline') {
    return (
      <Collapse in={visible}>
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            p: 2,
            border: '1px solid',
            borderColor: 'warning.main',
            borderRadius: 1,
            bgcolor: 'warning.light',
            color: 'warning.contrastText',
            mb: 2
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Lock sx={{ color: 'warning.dark' }} />
            <Box>
              <Box sx={{ fontWeight: 600, mb: 0.5 }}>{title}</Box>
              <Box sx={{ fontSize: '0.875rem', opacity: 0.9 }}>{message}</Box>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="contained"
              size="small"
              onClick={handleUpgrade}
              startIcon={<TrendingUp />}
            >
              {buttonText}
            </Button>
            <IconButton size="small" onClick={handleClose}>
              <Close fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      </Collapse>
    );
  }

  // Card Variant (default)
  return (
    <Collapse in={visible}>
      <Box
        sx={{
          position: 'relative',
          p: 3,
          border: '2px solid',
          borderColor: 'primary.main',
          borderRadius: 2,
          bgcolor: 'background.paper',
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(168, 85, 247, 0.05) 100%)',
          boxShadow: 2,
          mb: 3
        }}
      >
        <IconButton
          size="small"
          onClick={handleClose}
          sx={{ position: 'absolute', top: 8, right: 8 }}
        >
          <Close fontSize="small" />
        </IconButton>

        <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '50%',
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            <Star sx={{ color: 'white' }} />
          </Box>

          <Box sx={{ flex: 1 }}>
            <Box sx={{ fontSize: '1.25rem', fontWeight: 600, mb: 1 }}>
              {title}
            </Box>
            <Box sx={{ color: 'text.secondary', mb: 2 }}>
              {message}
            </Box>

            {requiredPlan && (
              <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                <Chip
                  label={`${requiredPlan.price}/${requiredPlan.period}`}
                  color="primary"
                  size="small"
                />
                {requiredPlan.popular && (
                  <Chip
                    label="Most Popular"
                    icon={<Star />}
                    color="primary"
                    variant="outlined"
                    size="small"
                  />
                )}
              </Box>
            )}

            <Button
              variant="contained"
              onClick={handleUpgrade}
              startIcon={<TrendingUp />}
              size="large"
            >
              {buttonText}
            </Button>
          </Box>
        </Box>
      </Box>
    </Collapse>
  );
}
