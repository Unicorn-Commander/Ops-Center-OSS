import React, { useState } from 'react';
import {
  Box, Chip, Tooltip, Typography, Popover, List, ListItem,
  ListItemText, LinearProgress, Divider, Button
} from '@mui/material';
import {
  Star, TrendingUp, CheckCircle, Lock
} from '@mui/icons-material';

/**
 * TierBadge Component
 *
 * Displays user's subscription tier with optional usage stats.
 * Can be shown as simple badge or with detailed popover.
 *
 * Props:
 * - tier: User's current tier (free, starter, professional, enterprise)
 * - usage: Optional usage stats object { used, limit, percentage }
 * - compact: Boolean for smaller display
 * - showUsage: Show usage stats in badge
 * - onClick: Optional click handler for navigation
 */
export default function TierBadge({
  tier = 'free',
  usage = null,
  compact = false,
  showUsage = false,
  onClick = null
}) {
  const [anchorEl, setAnchorEl] = useState(null);

  const handleClick = (event) => {
    if (!compact) {
      setAnchorEl(event.currentTarget);
    }
    if (onClick) onClick();
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  const getTierConfig = (tierName) => {
    const configs = {
      free: {
        label: 'Free',
        icon: '🆓',
        color: '#6c757d',
        bgGradient: 'linear-gradient(135deg, #6c757d, #495057)',
        features: [
          'Basic access to Ops Center',
          'Limited API calls',
          'Community support'
        ],
        limits: {
          apiCalls: 100,
          models: 'Basic models only'
        }
      },
      starter: {
        label: 'Starter',
        icon: '⚡',
        color: '#0d6efd',
        bgGradient: 'linear-gradient(135deg, #0d6efd, #0a58ca)',
        features: [
          'Access to Chat & Search',
          '1,000 API calls/month',
          'BYOK support',
          'Email support'
        ],
        limits: {
          apiCalls: 1000,
          models: 'All basic models'
        }
      },
      professional: {
        label: 'Professional',
        icon: '💼',
        color: '#6f42c1',
        bgGradient: 'linear-gradient(135deg, #6f42c1, #4e2a84)',
        features: [
          'All Starter features',
          '10,000 API calls/month',
          'Advanced search + reranking',
          'Lago billing dashboard',
          'TTS & STT services',
          '50+ AI models via LiteLLM',
          'Priority support'
        ],
        limits: {
          apiCalls: 10000,
          models: 'All premium models'
        }
      },
      enterprise: {
        label: 'Enterprise',
        icon: '🏢',
        color: '#d4af37',
        bgGradient: 'linear-gradient(135deg, #d4af37, #f4d03f)',
        features: [
          'All Professional features',
          'Unlimited API calls',
          'Team management',
          'SSO integration',
          'Audit logs',
          'White-label options',
          'Dedicated support'
        ],
        limits: {
          apiCalls: 'Unlimited',
          models: 'All models + custom'
        }
      }
    };
    return configs[tierName.toLowerCase()] || configs.free;
  };

  const config = getTierConfig(tier);

  // Compact badge (no popover)
  if (compact) {
    return (
      <Chip
        icon={<span style={{ fontSize: '16px' }}>{config.icon}</span>}
        label={config.label}
        size="small"
        sx={{
          background: config.bgGradient,
          color: 'white',
          fontWeight: 'bold',
          cursor: onClick ? 'pointer' : 'default',
          '&:hover': onClick ? {
            opacity: 0.9,
            transform: 'scale(1.05)',
            transition: 'all 0.2s'
          } : {}
        }}
        onClick={handleClick}
      />
    );
  }

  // Full badge with popover
  return (
    <>
      <Tooltip title="View subscription details">
        <Box
          onClick={handleClick}
          sx={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 1,
            padding: '6px 12px',
            borderRadius: 2,
            background: config.bgGradient,
            color: 'white',
            cursor: 'pointer',
            transition: 'all 0.3s',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
            }
          }}
        >
          {/* Tier Icon & Name */}
          <Box display="flex" alignItems="center" gap={0.5}>
            <span style={{ fontSize: '20px' }}>{config.icon}</span>
            <Typography variant="body2" fontWeight="bold">
              {config.label}
            </Typography>
          </Box>

          {/* Usage indicator */}
          {showUsage && usage && (
            <>
              <Divider orientation="vertical" flexItem sx={{ bgcolor: 'rgba(255,255,255,0.3)' }} />
              <Box minWidth={80}>
                <Typography variant="caption" display="block">
                  {usage.used?.toLocaleString() || 0} / {usage.limit === -1 ? '∞' : usage.limit?.toLocaleString()}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={usage.percentage || 0}
                  sx={{
                    height: 4,
                    borderRadius: 2,
                    bgcolor: 'rgba(255,255,255,0.2)',
                    '& .MuiLinearProgress-bar': {
                      bgcolor: usage.percentage > 80 ? '#f44336' : '#4caf50'
                    }
                  }}
                />
              </Box>
            </>
          )}

          {/* Tier indicator */}
          <Star sx={{ fontSize: 18, opacity: 0.7 }} />
        </Box>
      </Tooltip>

      {/* Popover with tier details */}
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'left',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'left',
        }}
        PaperProps={{
          sx: {
            width: 320,
            background: 'linear-gradient(135deg, #1a0033 0%, #3a0e5a 100%)',
            border: '2px solid',
            borderColor: config.color,
            borderRadius: 2,
            p: 2
          }
        }}
      >
        {/* Header */}
        <Box display="flex" alignItems="center" gap={1} mb={2}>
          <span style={{ fontSize: '32px' }}>{config.icon}</span>
          <Box>
            <Typography variant="h6" fontWeight="bold">
              {config.label} Tier
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Your current subscription
            </Typography>
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {/* Usage Stats */}
        {usage && (
          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" mb={1}>
              <Typography variant="body2" color="textSecondary">
                API Usage This Month
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {usage.percentage?.toFixed(0)}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={usage.percentage || 0}
              sx={{
                height: 8,
                borderRadius: 4,
                bgcolor: 'rgba(255,255,255,0.1)',
                '& .MuiLinearProgress-bar': {
                  bgcolor: usage.percentage > 80 ? '#f44336' : config.color
                }
              }}
            />
            <Typography variant="caption" color="textSecondary" display="block" mt={0.5}>
              {usage.used?.toLocaleString() || 0} of {usage.limit === -1 ? 'unlimited' : usage.limit?.toLocaleString()} calls used
            </Typography>
          </Box>
        )}

        {/* Features */}
        <Box mb={2}>
          <Typography variant="body2" fontWeight="bold" mb={1} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
            <TrendingUp fontSize="small" /> Included Features
          </Typography>
          <List dense>
            {config.features.map((feature, idx) => (
              <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                <CheckCircle sx={{ fontSize: 16, color: config.color, mr: 1 }} />
                <ListItemText
                  primary={feature}
                  primaryTypographyProps={{ variant: 'body2' }}
                />
              </ListItem>
            ))}
          </List>
        </Box>

        {/* Limits */}
        <Box mb={2} p={1.5} bgcolor="rgba(0,0,0,0.3)" borderRadius={1}>
          <Typography variant="caption" fontWeight="bold" display="block" mb={0.5}>
            Your Limits
          </Typography>
          <Typography variant="body2" color="textSecondary">
            • API Calls: <strong>{config.limits.apiCalls}</strong>
          </Typography>
          <Typography variant="body2" color="textSecondary">
            • Models: <strong>{config.limits.models}</strong>
          </Typography>
        </Box>

        {/* Upgrade CTA (if not enterprise) */}
        {tier.toLowerCase() !== 'enterprise' && (
          <Button
            fullWidth
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #d4af37, #f4d03f)',
              color: '#000',
              fontWeight: 'bold',
              '&:hover': {
                background: 'linear-gradient(135deg, #f4d03f, #d4af37)'
              }
            }}
            onClick={() => {
              window.location.href = '/billing#plans';
              handleClose();
            }}
          >
            🚀 Upgrade Now
          </Button>
        )}

        {/* Manage Subscription */}
        <Button
          fullWidth
          variant="text"
          size="small"
          sx={{ mt: 1 }}
          onClick={() => {
            window.location.href = '/billing';
            handleClose();
          }}
        >
          Manage Subscription
        </Button>
      </Popover>
    </>
  );
}
