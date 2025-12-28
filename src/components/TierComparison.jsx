/**
 * TierComparison Component
 *
 * Beautiful, animated tier comparison cards for subscription plans.
 * Displays 4 tiers (Trial, Starter, Professional, Enterprise) with:
 * - Feature breakdown
 * - Visual design with hover animations
 * - Current plan highlighting
 * - Upgrade/Downgrade buttons
 *
 * Epic 2.4: Self-Service Upgrades
 */

import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Button,
  Chip, List, ListItem, ListItemIcon, ListItemText,
  CircularProgress, Alert
} from '@mui/material';
import {
  Check, Star, TrendingUp, TrendingDown, WorkspacePremium,
  Science, RocketLaunch, Domain
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';
import { tierFeatures } from '../data/tierFeatures';

/**
 * Icon mapping for tier badges
 */
const tierIcons = {
  trial: Science,
  starter: RocketLaunch,
  professional: WorkspacePremium,
  enterprise: Domain
};

/**
 * Tier color mapping for purple/gold theme
 */
const tierColors = {
  trial: {
    light: '#60A5FA',
    main: '#3B82F6',
    dark: '#2563EB',
    bg: 'rgba(59, 130, 246, 0.05)'
  },
  starter: {
    light: '#34D399',
    main: '#10B981',
    dark: '#059669',
    bg: 'rgba(16, 185, 129, 0.05)'
  },
  professional: {
    light: '#A78BFA',
    main: '#7C3AED',
    dark: '#6D28D9',
    bg: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)'
  },
  enterprise: {
    light: '#FCD34D',
    main: '#F59E0B',
    dark: '#D97706',
    bg: 'rgba(245, 158, 11, 0.05)'
  }
};

export default function TierComparison({ currentTier = null, onSelectTier }) {
  const { currentTheme } = useTheme();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userTier, setUserTier] = useState(currentTier);

  // Fetch current user tier if not provided
  useEffect(() => {
    if (!currentTier) {
      fetchCurrentTier();
    }
  }, [currentTier]);

  const fetchCurrentTier = async () => {
    try {
      const response = await fetch('/api/v1/subscriptions/current', {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        setUserTier(data.tier || 'trial');
      }
    } catch (err) {
      console.error('Error fetching current tier:', err);
      setUserTier('trial'); // Default fallback
    }
  };

  const handleSelectTier = (tierCode) => {
    if (onSelectTier) {
      onSelectTier(tierCode);
    } else {
      // Default: navigate to upgrade flow
      window.location.href = `/admin/upgrade?tier=${tierCode}`;
    }
  };

  const getButtonLabel = (tierCode) => {
    if (tierCode === userTier) {
      return 'Current Plan';
    }

    const tierHierarchy = ['trial', 'starter', 'professional', 'enterprise'];
    const currentIndex = tierHierarchy.indexOf(userTier);
    const targetIndex = tierHierarchy.indexOf(tierCode);

    if (targetIndex > currentIndex) {
      return 'Upgrade';
    } else if (targetIndex < currentIndex) {
      return 'Downgrade';
    }

    return 'Select Plan';
  };

  const getButtonVariant = (tierCode) => {
    if (tierCode === userTier) {
      return 'outlined';
    }

    return tierCode === 'professional' ? 'contained' : 'outlined';
  };

  const getButtonColor = (tierCode) => {
    if (tierCode === userTier) {
      return 'success';
    }

    const tierHierarchy = ['trial', 'starter', 'professional', 'enterprise'];
    const currentIndex = tierHierarchy.indexOf(userTier);
    const targetIndex = tierHierarchy.indexOf(tierCode);

    if (targetIndex > currentIndex) {
      return 'primary';
    } else {
      return 'warning';
    }
  };

  const getButtonIcon = (tierCode) => {
    if (tierCode === userTier) {
      return <Check />;
    }

    const tierHierarchy = ['trial', 'starter', 'professional', 'enterprise'];
    const currentIndex = tierHierarchy.indexOf(userTier);
    const targetIndex = tierHierarchy.indexOf(tierCode);

    if (targetIndex > currentIndex) {
      return <TrendingUp />;
    } else {
      return <TrendingDown />;
    }
  };

  return (
    <Box sx={{ py: 4 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 6 }}>
        <Typography variant="h3" fontWeight={700} gutterBottom>
          Choose Your Plan
        </Typography>
        <Typography variant="h6" color="textSecondary" sx={{ maxWidth: 600, mx: 'auto' }}>
          Simple, transparent pricing for every stage of your journey. Upgrade or downgrade anytime.
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 4 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Tier Cards */}
      <Grid container spacing={3} sx={{ mb: 6 }}>
        {Object.entries(tierFeatures).map(([tierCode, tier]) => {
          const TierIcon = tierIcons[tierCode];
          const isCurrentTier = tierCode === userTier;
          const isPopular = tier.popular;
          const colors = tierColors[tierCode];

          return (
            <Grid item xs={12} sm={6} md={3} key={tierCode}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  border: isCurrentTier ? '2px solid' : '1px solid',
                  borderColor: isCurrentTier ? 'success.main' : isPopular ? 'primary.main' : 'divider',
                  background: isPopular ? colors.bg : undefined,
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 8
                  }
                }}
              >
                {/* Popular Badge */}
                {isPopular && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      zIndex: 1
                    }}
                  >
                    <Chip
                      label={tier.badge || 'Most Popular'}
                      color="primary"
                      icon={<Star />}
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                )}

                {/* Current Plan Badge */}
                {isCurrentTier && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -12,
                      right: 16,
                      zIndex: 1
                    }}
                  >
                    <Chip
                      label="Current Plan"
                      color="success"
                      icon={<Check />}
                      size="small"
                      sx={{ fontWeight: 600 }}
                    />
                  </Box>
                )}

                <CardContent sx={{ flexGrow: 1, pt: isPopular || isCurrentTier ? 4 : 3 }}>
                  {/* Tier Icon & Name */}
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                    <TierIcon sx={{ fontSize: 40, color: colors.main }} />
                    <Box>
                      <Typography variant="h5" fontWeight={600}>
                        {tier.name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {tier.tagline}
                      </Typography>
                    </Box>
                  </Box>

                  {/* Price */}
                  <Box sx={{ mb: 3 }}>
                    <Typography variant="h3" fontWeight={700} component="span" sx={{ color: colors.main }}>
                      {tier.price}
                    </Typography>
                    <Typography variant="body1" color="textSecondary" component="span">
                      /{tier.period}
                    </Typography>
                    {tierCode === 'trial' && (
                      <Typography variant="caption" display="block" color="textSecondary">
                        7-day trial period
                      </Typography>
                    )}
                  </Box>

                  {/* Description */}
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 3, minHeight: 40 }}>
                    {tier.description}
                  </Typography>

                  {/* Features */}
                  <List dense>
                    {tier.features.slice(0, 6).map((feature, idx) => (
                      <ListItem key={idx} disableGutters>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <Check color="success" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={feature}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                    {tier.features.length > 6 && (
                      <ListItem disableGutters>
                        <ListItemText
                          primary={`+${tier.features.length - 6} more features`}
                          primaryTypographyProps={{ variant: 'caption', color: 'textSecondary' }}
                        />
                      </ListItem>
                    )}
                  </List>

                  {/* Action Button */}
                  <Button
                    variant={getButtonVariant(tierCode)}
                    color={getButtonColor(tierCode)}
                    fullWidth
                    size="large"
                    startIcon={getButtonIcon(tierCode)}
                    onClick={() => handleSelectTier(tierCode)}
                    disabled={isCurrentTier || loading}
                    sx={{ mt: 3 }}
                  >
                    {loading ? <CircularProgress size={24} /> : getButtonLabel(tierCode)}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Feature Comparison Note */}
      <Box sx={{ textAlign: 'center', mt: 4 }}>
        <Typography variant="body2" color="textSecondary">
          All plans include access to UC-Cloud infrastructure, OpenAI-compatible APIs, and community support.
        </Typography>
        <Button
          variant="text"
          href="/admin/credits/tiers"
          sx={{ mt: 1 }}
        >
          View Detailed Feature Comparison →
        </Button>
      </Box>
    </Box>
  );
}
