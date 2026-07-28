/**
 * SubscriptionTierSelector Component
 *
 * A comprehensive subscription tier selector with pricing display
 * Used in Create User modal (Tab 3: Subscription & Billing)
 *
 * Features:
 * - Visual tier cards with pricing and features
 * - Monthly/Annual billing toggle with savings display
 * - API call limit override capability
 * - Dynamic feature loading from backend
 * - Responsive grid layout
 * - Purple gradient styling for selected tier
 *
 * Created: October 15, 2025
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Star as StarIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Group as GroupIcon,
  Bolt as BoltIcon,
} from '@mui/icons-material';

// Tier icons mapping
const tierIcons = {
  free: '🆓',
  trial: '🎯',
  starter: '🚀',
  professional: '⭐',
  enterprise: '👑',
};

// Default tier configurations (fallback if API fails)
const defaultTiers = [
  {
    code: 'free',
    name: 'Free',
    amountCents: 0,
    features: [
      '100 API calls/day',
      'Basic features',
      'Community support',
      'Open-WebUI access',
    ],
    limits: { api_calls: 100, period: 'day' },
  },
  {
    code: 'trial',
    name: 'Trial',
    amountCents: 100,
    interval: 'weekly',
    features: [
      '100 API calls/day (700 total)',
      'All features',
      '7-day trial period',
      'Email support',
    ],
    limits: { api_calls: 700, period: 'week' },
    badge: 'Limited Time',
  },
  {
    code: 'starter',
    name: 'Starter',
    amountCents: 1900,
    features: [
      '1,000 API calls/month',
      'All AI models',
      'BYOK support',
      'Email support',
      'Open-WebUI + Center-Deep',
    ],
    limits: { api_calls: 1000, period: 'month' },
  },
  {
    code: 'professional',
    name: 'Professional',
    amountCents: 4900,
    features: [
      '10,000 API calls/month',
      'All services access',
      'Priority support',
      'Billing dashboard',
      'BYOK support',
      'Advanced analytics',
    ],
    limits: { api_calls: 10000, period: 'month' },
    popular: true,
    badge: 'Most Popular',
  },
  {
    code: 'enterprise',
    name: 'Enterprise',
    amountCents: 9900,
    features: [
      'Unlimited API calls',
      'Team management (5 seats)',
      'Custom integrations',
      '24/7 dedicated support',
      'White-label options',
      'SLA guarantees',
    ],
    limits: { api_calls: -1, period: 'month' }, // -1 = unlimited
    badge: 'Best Value',
  },
];

const SubscriptionTierSelector = ({
  value,
  onChange,
  billingPeriod = 'monthly',
  onBillingPeriodChange,
  apiLimitOverride,
  onApiLimitChange,
}) => {
  const [tiers, setTiers] = useState(defaultTiers);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedTier, setExpandedTier] = useState(null);
  const [customLimit, setCustomLimit] = useState(apiLimitOverride || '');

  // Fetch subscription plans from backend
  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const response = await fetch('/api/v1/billing/plans', {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch subscription plans');
        }

        const data = await response.json();

        // Transform API response to tier format
        if (data.plans && Array.isArray(data.plans)) {
          const transformedTiers = data.plans.map(plan => ({
            code: plan.code,
            name: plan.name,
            amountCents: plan.amountCents || plan.amount_cents || 0,
            interval: plan.interval,
            features: plan.charges?.map(c => c.billable_metric?.name) || [],
            limits: {
              api_calls: plan.charges?.[0]?.properties?.amount || 100,
              period: plan.interval === 'weekly' ? 'week' : 'month',
            },
            popular: plan.code === 'professional',
            badge: plan.code === 'professional' ? 'Most Popular' :
                   plan.code === 'trial' ? 'Limited Time' :
                   plan.code === 'enterprise' ? 'Best Value' : null,
          }));

          setTiers(transformedTiers.length > 0 ? transformedTiers : defaultTiers);
        }

        setLoading(false);
      } catch (err) {
        console.error('Error fetching plans:', err);
        setError(err.message);
        setTiers(defaultTiers); // Use defaults on error
        setLoading(false);
      }
    };

    fetchPlans();
  }, []);

  // Format price based on billing period
  const formatPrice = (tier) => {
    let price = tier.amountCents / 100;

    if (billingPeriod === 'annual' && tier.interval !== 'weekly') {
      // Annual billing gets 20% discount
      price = price * 12 * 0.8;
      return { amount: price.toFixed(2), period: '/year', savings: '20%' };
    }

    const period = tier.interval === 'weekly' ? '/week' : '/month';
    return { amount: price.toFixed(2), period, savings: null };
  };

  // Get tier default API limit
  const getTierLimit = (tierCode) => {
    const tier = tiers.find(t => t.code === tierCode);
    return tier?.limits?.api_calls || 100;
  };

  // Handle tier selection
  const handleSelectTier = (tierCode) => {
    const tierLimit = getTierLimit(tierCode);
    const limits = {
      api_calls: customLimit || tierLimit,
      api_calls_default: tierLimit,
    };

    onChange(tierCode, limits);
  };

  // Handle custom limit change
  const handleLimitChange = (e) => {
    const newLimit = parseInt(e.target.value, 10);
    setCustomLimit(newLimit);

    if (onApiLimitChange) {
      onApiLimitChange(newLimit);
    }
  };

  // Validate custom limit
  const isLimitValid = (limit) => {
    const tierLimit = getTierLimit(value);
    return !limit || limit >= tierLimit;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error && tiers.length === 0) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load subscription plans: {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Billing Period Toggle */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mb: 3 }}>
        <ToggleButtonGroup
          value={billingPeriod}
          exclusive
          onChange={(e, newPeriod) => {
            if (newPeriod && onBillingPeriodChange) {
              onBillingPeriodChange(newPeriod);
            }
          }}
          sx={{
            '& .MuiToggleButton-root': {
              px: 3,
              py: 1,
              '&.Mui-selected': {
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                color: 'white',
                '&:hover': {
                  background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                },
              },
            },
          }}
        >
          <ToggleButton value="monthly">
            Monthly
          </ToggleButton>
          <ToggleButton value="annual">
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              Annual
              <Chip
                label="Save 20%"
                size="small"
                color="success"
                sx={{ height: 20, fontSize: '0.7rem' }}
              />
            </Box>
          </ToggleButton>
        </ToggleButtonGroup>
      </Box>

      {/* Tier Cards Grid */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {tiers.map((tier) => {
          const isSelected = value === tier.code;
          const pricing = formatPrice(tier);
          const isExpanded = expandedTier === tier.code;

          return (
            <Grid item xs={12} sm={6} md={4} key={tier.code}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  position: 'relative',
                  border: isSelected ? '2px solid' : '1px solid',
                  borderColor: isSelected ? 'primary.main' : 'divider',
                  background: isSelected
                    ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
                    : 'background.paper',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 6,
                  },
                }}
              >
                {/* Popular Badge */}
                {tier.badge && (
                  <Box
                    sx={{
                      position: 'absolute',
                      top: -12,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      zIndex: 1,
                    }}
                  >
                    <Chip
                      label={tier.badge}
                      color={tier.popular ? 'secondary' : 'primary'}
                      size="small"
                      icon={tier.popular ? <StarIcon /> : <BoltIcon />}
                      sx={{
                        fontWeight: 'bold',
                        px: 1,
                      }}
                    />
                  </Box>
                )}

                <CardContent sx={{ flexGrow: 1, pt: tier.badge ? 3 : 2 }}>
                  {/* Tier Icon and Name */}
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h2" sx={{ fontSize: '3rem', mb: 1 }}>
                      {tierIcons[tier.code]}
                    </Typography>
                    <Typography variant="h5" fontWeight="bold" gutterBottom>
                      {tier.name}
                    </Typography>
                  </Box>

                  {/* Pricing */}
                  <Box sx={{ textAlign: 'center', mb: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'baseline', justifyContent: 'center', gap: 0.5 }}>
                      <Typography variant="h3" fontWeight="bold" color="primary">
                        ${pricing.amount}
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        {pricing.period}
                      </Typography>
                    </Box>
                    {pricing.savings && (
                      <Chip
                        label={`Save ${pricing.savings}`}
                        size="small"
                        color="success"
                        sx={{ mt: 1 }}
                      />
                    )}
                  </Box>

                  {/* Features List (collapsed/expanded) */}
                  <List dense sx={{ mb: 2 }}>
                    {tier.features.slice(0, isExpanded ? undefined : 3).map((feature, idx) => (
                      <ListItem key={idx} sx={{ px: 0, py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <CheckIcon color="success" fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={feature}
                          primaryTypographyProps={{
                            variant: 'body2',
                            fontSize: '0.875rem',
                          }}
                        />
                      </ListItem>
                    ))}
                  </List>

                  {/* Expand/Collapse Button */}
                  {tier.features.length > 3 && (
                    <Box sx={{ textAlign: 'center', mb: 2 }}>
                      <Button
                        size="small"
                        onClick={() => setExpandedTier(isExpanded ? null : tier.code)}
                        endIcon={isExpanded ? <CollapseIcon /> : <ExpandIcon />}
                      >
                        {isExpanded ? 'Show Less' : `+${tier.features.length - 3} More`}
                      </Button>
                    </Box>
                  )}

                  {/* Select Button */}
                  <Button
                    fullWidth
                    variant={isSelected ? 'contained' : 'outlined'}
                    onClick={() => handleSelectTier(tier.code)}
                    sx={{
                      background: isSelected
                        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                        : undefined,
                      '&:hover': {
                        background: isSelected
                          ? 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)'
                          : undefined,
                      },
                    }}
                  >
                    {isSelected ? 'Selected' : 'Select Plan'}
                  </Button>

                  {/* API Limit Info */}
                  {isSelected && (
                    <Box sx={{ mt: 2, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                      <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                        API Call Limit
                      </Typography>
                      <Typography variant="body2" fontWeight="medium">
                        {tier.limits.api_calls === -1
                          ? 'Unlimited'
                          : `${tier.limits.api_calls.toLocaleString()} calls/${tier.limits.period}`
                        }
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* API Limit Override */}
      {value && (
        <Collapse in={!!value}>
          <Card sx={{ p: 2, bgcolor: 'background.default' }}>
            <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
              Custom API Limit (Optional)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Override the default API call limit for this user. Must be greater than or equal to the tier's default limit.
            </Typography>

            <Grid container spacing={2} alignItems="flex-start">
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Custom API Limit"
                  placeholder={`Default: ${getTierLimit(value)}`}
                  value={customLimit}
                  onChange={handleLimitChange}
                  error={customLimit && !isLimitValid(customLimit)}
                  helperText={
                    customLimit && !isLimitValid(customLimit)
                      ? `Must be at least ${getTierLimit(value)}`
                      : `Tier default: ${getTierLimit(value)} calls`
                  }
                  InputProps={{
                    endAdornment: customLimit && (
                      <IconButton
                        size="small"
                        onClick={() => {
                          setCustomLimit('');
                          if (onApiLimitChange) onApiLimitChange(null);
                        }}
                      >
                        <CancelIcon fontSize="small" />
                      </IconButton>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <Alert severity="info" sx={{ height: '100%', display: 'flex', alignItems: 'center' }}>
                  <Typography variant="caption">
                    Leave empty to use tier default. Unlimited tiers cannot be overridden.
                  </Typography>
                </Alert>
              </Grid>
            </Grid>
          </Card>
        </Collapse>
      )}

      {/* Tier Comparison Help */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'info.lighter', borderRadius: 1, border: '1px solid', borderColor: 'info.light' }}>
        <Typography variant="body2" color="text.secondary">
          <strong>Need help choosing?</strong> Start with the Free tier to explore, or try our Trial for a week.
          Most users find Professional offers the best balance of features and value.
        </Typography>
      </Box>
    </Box>
  );
};

export default SubscriptionTierSelector;
