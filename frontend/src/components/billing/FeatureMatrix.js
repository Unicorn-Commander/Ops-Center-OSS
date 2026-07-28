import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, Tooltip, Button, Collapse
} from '@mui/material';
import {
  Check, Close, Lock, ExpandMore, ExpandLess, Rocket,
  Chat, Search, Mic, RecordVoiceOver, Dashboard, Groups,
  Security, Assessment, Star
} from '@mui/icons-material';

/**
 * FeatureMatrix Component
 *
 * Displays comprehensive feature comparison across all subscription tiers.
 * Shows available vs locked features with visual indicators.
 *
 * Props:
 * - currentTier: User's current subscription tier
 * - compact: Show compact view (fewer features)
 * - onUpgradeClick: Callback when upgrade button is clicked
 */
export default function FeatureMatrix({
  currentTier = 'free',
  compact = false,
  onUpgradeClick = null
}) {
  const [expandedCategory, setExpandedCategory] = useState(null);

  const tiers = ['free', 'starter', 'professional', 'enterprise'];

  const tierConfig = {
    free: {
      name: 'Free',
      icon: '🆓',
      price: 0,
      color: '#6c757d'
    },
    starter: {
      name: 'Starter',
      icon: '⚡',
      price: 19,
      color: '#0d6efd'
    },
    professional: {
      name: 'Professional',
      icon: '💼',
      price: 49,
      color: '#6f42c1'
    },
    enterprise: {
      name: 'Enterprise',
      icon: '🏢',
      price: 99,
      color: '#d4af37'
    }
  };

  const featureCategories = {
    'Core Services': {
      icon: <Dashboard />,
      features: [
        {
          name: 'Ops Center Dashboard',
          description: 'Central management hub',
          free: true,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Open-WebUI Chat',
          description: 'AI chat interface',
          free: true,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Center-Deep Search',
          description: 'AI-powered metasearch',
          free: false,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Lago Billing Dashboard',
          description: 'Usage & billing analytics',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        },
        {
          name: 'LiteLLM Gateway',
          description: '50+ AI models',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        }
      ]
    },
    'AI Features': {
      icon: <Star />,
      features: [
        {
          name: 'Basic AI Models',
          description: 'GPT-3.5, Claude Instant',
          free: true,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Premium AI Models',
          description: 'GPT-4, Claude 3.5 Sonnet',
          free: false,
          starter: 'Limited',
          professional: true,
          enterprise: true
        },
        {
          name: 'BYOK Support',
          description: 'Use your own API keys',
          free: false,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Advanced Search Reranking',
          description: 'Improved search accuracy',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        },
        {
          name: 'Custom Model Deployment',
          description: 'Deploy your own models',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        }
      ]
    },
    'Voice Services': {
      icon: <Mic />,
      features: [
        {
          name: 'Text-to-Speech (TTS)',
          description: 'Unicorn Orator service',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        },
        {
          name: 'Speech-to-Text (STT)',
          description: 'Unicorn Amanuensis',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        },
        {
          name: 'Voice Customization',
          description: '20+ premium voices',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        },
        {
          name: 'Speaker Diarization',
          description: 'Multi-speaker detection',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        }
      ]
    },
    'Usage & Limits': {
      icon: <Assessment />,
      features: [
        {
          name: 'API Calls per Month',
          description: '',
          free: '100',
          starter: '1,000',
          professional: '10,000',
          enterprise: 'Unlimited'
        },
        {
          name: 'Concurrent Searches',
          description: '',
          free: '1',
          starter: '3',
          professional: '10',
          enterprise: 'Unlimited'
        },
        {
          name: 'Storage Quota',
          description: '',
          free: '1 GB',
          starter: '10 GB',
          professional: '100 GB',
          enterprise: 'Custom'
        },
        {
          name: 'Rate Limiting',
          description: '',
          free: '10/min',
          starter: '100/min',
          professional: '1000/min',
          enterprise: 'Custom'
        }
      ]
    },
    'Team & Enterprise': {
      icon: <Groups />,
      features: [
        {
          name: 'Team Management',
          description: 'Multi-user accounts',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        },
        {
          name: 'SSO Integration',
          description: 'SAML, OAuth, LDAP',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        },
        {
          name: 'Audit Logs',
          description: 'Compliance & tracking',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        },
        {
          name: 'White-label Options',
          description: 'Custom branding',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        },
        {
          name: 'Dedicated Support',
          description: '24/7 priority support',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        }
      ]
    },
    'Support': {
      icon: <Security />,
      features: [
        {
          name: 'Community Support',
          description: 'Forums & documentation',
          free: true,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Email Support',
          description: 'Response within 48h',
          free: false,
          starter: true,
          professional: true,
          enterprise: true
        },
        {
          name: 'Priority Support',
          description: 'Response within 24h',
          free: false,
          starter: false,
          professional: true,
          enterprise: true
        },
        {
          name: 'Dedicated Support',
          description: 'Direct line to engineering',
          free: false,
          starter: false,
          professional: false,
          enterprise: true
        }
      ]
    }
  };

  const renderFeatureValue = (value, tierName, isCurrentTier) => {
    if (typeof value === 'boolean') {
      return value ? (
        <Check sx={{ color: '#4caf50', fontSize: 24 }} />
      ) : (
        <Lock sx={{ color: isCurrentTier ? '#f44336' : '#6c757d', fontSize: 20 }} />
      );
    }

    if (typeof value === 'string') {
      if (value === 'Limited') {
        return (
          <Chip
            label="Limited"
            size="small"
            sx={{ bgcolor: 'rgba(255,193,7,0.2)', color: '#ffc107' }}
          />
        );
      }
      return (
        <Typography variant="body2" fontWeight="medium">
          {value}
        </Typography>
      );
    }

    return <Close sx={{ color: '#6c757d' }} />;
  };

  const handleUpgrade = (tier) => {
    if (onUpgradeClick) {
      onUpgradeClick(tier);
    } else {
      window.location.href = `/billing#${tier}`;
    }
  };

  const toggleCategory = (category) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  // Compact view - show only key features
  if (compact) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            ✨ Quick Feature Comparison
          </Typography>

          <Grid container spacing={2} mt={1}>
            {tiers.map((tier) => {
              const config = tierConfig[tier];
              const isActive = tier === currentTier.toLowerCase();

              return (
                <Grid item xs={12} sm={6} md={3} key={tier}>
                  <Card
                    variant="outlined"
                    sx={{
                      border: isActive ? '2px solid' : '1px solid',
                      borderColor: isActive ? config.color : 'divider',
                      bgcolor: isActive ? `${config.color}11` : 'transparent'
                    }}
                  >
                    <CardContent>
                      <Box textAlign="center" mb={2}>
                        <Typography variant="h4" mb={0.5}>{config.icon}</Typography>
                        <Typography variant="h6" fontWeight="bold">
                          {config.name}
                        </Typography>
                        <Typography variant="h5" color="primary" mt={1}>
                          ${config.price}
                          <Typography variant="caption" color="textSecondary">/mo</Typography>
                        </Typography>
                      </Box>

                      {!isActive && (
                        <Button
                          fullWidth
                          variant="contained"
                          size="small"
                          onClick={() => handleUpgrade(tier)}
                          sx={{ background: config.color }}
                        >
                          Upgrade
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </CardContent>
      </Card>
    );
  }

  // Full feature matrix
  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            ✨ Complete Feature Matrix
          </Typography>
          <Chip
            label={`Current: ${tierConfig[currentTier.toLowerCase()].icon} ${tierConfig[currentTier.toLowerCase()].name}`}
            sx={{
              background: tierConfig[currentTier.toLowerCase()].color,
              color: 'white',
              fontWeight: 'bold'
            }}
          />
        </Box>

        {/* Category-based feature listing */}
        {Object.entries(featureCategories).map(([categoryName, category]) => (
          <Box key={categoryName} mb={2}>
            <Box
              display="flex"
              alignItems="center"
              justifyContent="space-between"
              sx={{
                cursor: 'pointer',
                p: 1.5,
                bgcolor: 'rgba(255,255,255,0.05)',
                borderRadius: 1,
                '&:hover': { bgcolor: 'rgba(255,255,255,0.08)' }
              }}
              onClick={() => toggleCategory(categoryName)}
            >
              <Box display="flex" alignItems="center" gap={1}>
                {category.icon}
                <Typography variant="h6" fontWeight="bold">
                  {categoryName}
                </Typography>
                <Chip
                  label={`${category.features.length} features`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <IconButton size="small">
                {expandedCategory === categoryName ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>

            <Collapse in={expandedCategory === categoryName || !compact}>
              <TableContainer component={Paper} sx={{ mt: 1, bgcolor: 'transparent' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>Feature</TableCell>
                      {tiers.map((tier) => {
                        const config = tierConfig[tier];
                        const isActive = tier === currentTier.toLowerCase();
                        return (
                          <TableCell
                            key={tier}
                            align="center"
                            sx={{
                              fontWeight: 'bold',
                              bgcolor: isActive ? `${config.color}22` : 'transparent',
                              borderLeft: isActive ? `2px solid ${config.color}` : 'none'
                            }}
                          >
                            <Box>
                              <span style={{ fontSize: '20px' }}>{config.icon}</span>
                              <Typography variant="body2" fontWeight="bold">
                                {config.name}
                              </Typography>
                              <Typography variant="caption" color="textSecondary">
                                ${config.price}/mo
                              </Typography>
                            </Box>
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {category.features.map((feature, idx) => (
                      <TableRow key={idx} hover>
                        <TableCell>
                          <Tooltip title={feature.description} arrow placement="right">
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {feature.name}
                              </Typography>
                              {feature.description && (
                                <Typography variant="caption" color="textSecondary">
                                  {feature.description}
                                </Typography>
                              )}
                            </Box>
                          </Tooltip>
                        </TableCell>
                        {tiers.map((tier) => {
                          const isActive = tier === currentTier.toLowerCase();
                          return (
                            <TableCell
                              key={tier}
                              align="center"
                              sx={{
                                bgcolor: isActive ? `${tierConfig[tier].color}11` : 'transparent',
                                borderLeft: isActive ? `2px solid ${tierConfig[tier].color}` : 'none'
                              }}
                            >
                              {renderFeatureValue(feature[tier], tier, isActive)}
                            </TableCell>
                          );
                        })}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Collapse>
          </Box>
        ))}

        {/* Upgrade CTA */}
        {currentTier.toLowerCase() !== 'enterprise' && (
          <Box mt={4} p={3} bgcolor="rgba(212,175,55,0.1)" borderRadius={2} textAlign="center">
            <Typography variant="h6" gutterBottom>
              🚀 Ready to Upgrade?
            </Typography>
            <Typography variant="body2" color="textSecondary" mb={2}>
              Unlock more features and take your AI platform to the next level
            </Typography>
            <Button
              variant="contained"
              size="large"
              startIcon={<Rocket />}
              onClick={() => handleUpgrade('professional')}
              sx={{
                background: 'linear-gradient(135deg, #6f42c1, #d4af37)',
                fontWeight: 'bold'
              }}
            >
              View All Plans
            </Button>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
