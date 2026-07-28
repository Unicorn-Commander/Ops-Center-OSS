import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Chip,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, Tooltip, Button, Collapse, CircularProgress, Alert
} from '@mui/material';
import {
  Check, Close, Lock, ExpandMore, ExpandLess, Rocket,
  Dashboard, Star, Mic, Assessment, Groups, Security, Apps
} from '@mui/icons-material';

/**
 * AppMatrix Component
 *
 * Dynamically displays app/feature availability across subscription tiers.
 * Fetches live data from APIs instead of using hardcoded features.
 *
 * Props:
 * - currentTier: User's current subscription tier
 * - compact: Show compact view (fewer features)
 * - onUpgradeClick: Callback when upgrade button is clicked
 */
export default function AppMatrix({
  currentTier = 'free',
  compact = false,
  onUpgradeClick = null
}) {
  const [expandedCategory, setExpandedCategory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [apps, setApps] = useState([]);
  const [tierAppData, setTierAppData] = useState([]);
  const [appsByCategory, setAppsByCategory] = useState({});

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

  // Category icons
  const categoryIcons = {
    'services': <Apps />,
    'ai_features': <Star />,
    'voice': <Mic />,
    'analytics': <Assessment />,
    'support': <Security />,
    'enterprise': <Groups />,
    'default': <Dashboard />
  };

  // Fetch apps and tier associations
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch all apps (including inactive for complete list)
        const appsResponse = await fetch('/api/v1/admin/apps/?active_only=false', {
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });

        if (!appsResponse.ok) {
          throw new Error(`Failed to fetch apps: ${appsResponse.status} ${appsResponse.statusText}`);
        }

        const appsData = await appsResponse.json();

        // Fetch tier-app associations with detailed info
        const tierAppsResponse = await fetch('/api/v1/admin/tiers/features/detailed', {
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include'
        });

        if (!tierAppsResponse.ok) {
          throw new Error(`Failed to fetch tier apps: ${tierAppsResponse.status} ${tierAppsResponse.statusText}`);
        }

        const tierAppsData = await tierAppsResponse.json();

        setApps(appsData);
        setTierAppData(tierAppsData);

        // Group apps by category
        const grouped = groupAppsByCategory(appsData);
        setAppsByCategory(grouped);

      } catch (err) {
        console.error('Error fetching app matrix data:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  /**
   * Group apps by category for organized display
   */
  const groupAppsByCategory = (appsData) => {
    const grouped = {};

    appsData.forEach(app => {
      const category = app.category || 'other';
      if (!grouped[category]) {
        grouped[category] = {
          name: formatCategoryName(category),
          icon: categoryIcons[category] || categoryIcons.default,
          apps: []
        };
      }
      grouped[category].apps.push(app);
    });

    return grouped;
  };

  /**
   * Format category names for display
   */
  const formatCategoryName = (category) => {
    const names = {
      'services': 'Core Services',
      'ai_features': 'AI Features',
      'voice': 'Voice Services',
      'analytics': 'Analytics & Reporting',
      'support': 'Support',
      'enterprise': 'Team & Enterprise',
      'other': 'Other Features'
    };
    return names[category] || category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  /**
   * Check if an app is included in a specific tier
   */
  const isAppInTier = (appCode, tierCode) => {
    return tierAppData.some(
      item => item.app_code === appCode && item.tier_code === tierCode
    );
  };

  /**
   * Render feature availability indicator
   */
  const renderFeatureValue = (isAvailable, tierName, isCurrentTier) => {
    if (isAvailable) {
      return <Check sx={{ color: '#4caf50', fontSize: 24 }} />;
    } else {
      return <Lock sx={{ color: isCurrentTier ? '#f44336' : '#6c757d', fontSize: 20 }} />;
    }
  };

  /**
   * Handle upgrade button click
   */
  const handleUpgrade = (tier) => {
    if (onUpgradeClick) {
      onUpgradeClick(tier);
    } else {
      window.location.href = `/billing#${tier}`;
    }
  };

  /**
   * Toggle category expansion
   */
  const toggleCategory = (category) => {
    setExpandedCategory(expandedCategory === category ? null : category);
  };

  // Loading state
  if (loading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
            <Typography variant="body1" ml={2}>
              Loading app matrix...
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  // Error state
  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">
            <Typography variant="h6">Error Loading App Matrix</Typography>
            <Typography variant="body2">{error}</Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={() => window.location.reload()}
              sx={{ mt: 2 }}
            >
              Retry
            </Button>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Compact view - show only tier cards
  if (compact) {
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            ✨ Quick App Comparison
          </Typography>

          <Grid container spacing={2} mt={1}>
            {tiers.map((tier) => {
              const config = tierConfig[tier];
              const isActive = tier === currentTier.toLowerCase();
              const appCount = tierAppData.filter(item => item.tier_code === tier).length;

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
                        <Chip
                          label={`${appCount} apps`}
                          size="small"
                          sx={{ mt: 1 }}
                        />
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

  // Full app matrix
  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h5" fontWeight="bold" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            ✨ Complete App Matrix
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

        {/* Summary statistics */}
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center" p={2} bgcolor="rgba(255,255,255,0.05)" borderRadius={1}>
              <Typography variant="h4" fontWeight="bold">{apps.length}</Typography>
              <Typography variant="caption" color="textSecondary">Total Apps</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center" p={2} bgcolor="rgba(255,255,255,0.05)" borderRadius={1}>
              <Typography variant="h4" fontWeight="bold">{Object.keys(appsByCategory).length}</Typography>
              <Typography variant="caption" color="textSecondary">Categories</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center" p={2} bgcolor="rgba(255,255,255,0.05)" borderRadius={1}>
              <Typography variant="h4" fontWeight="bold">
                {tierAppData.filter(item => item.tier_code === currentTier.toLowerCase()).length}
              </Typography>
              <Typography variant="caption" color="textSecondary">Your Apps</Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center" p={2} bgcolor="rgba(255,255,255,0.05)" borderRadius={1}>
              <Typography variant="h4" fontWeight="bold">
                {apps.length - tierAppData.filter(item => item.tier_code === currentTier.toLowerCase()).length}
              </Typography>
              <Typography variant="caption" color="textSecondary">Locked Apps</Typography>
            </Box>
          </Grid>
        </Grid>

        {/* Category-based app listing */}
        {Object.entries(appsByCategory).map(([categoryKey, category]) => (
          <Box key={categoryKey} mb={2}>
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
              onClick={() => toggleCategory(categoryKey)}
            >
              <Box display="flex" alignItems="center" gap={1}>
                {category.icon}
                <Typography variant="h6" fontWeight="bold">
                  {category.name}
                </Typography>
                <Chip
                  label={`${category.apps.length} apps`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              <IconButton size="small">
                {expandedCategory === categoryKey ? <ExpandLess /> : <ExpandMore />}
              </IconButton>
            </Box>

            <Collapse in={expandedCategory === categoryKey || !compact}>
              <TableContainer component={Paper} sx={{ mt: 1, bgcolor: 'transparent' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell sx={{ fontWeight: 'bold' }}>App / Feature</TableCell>
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
                    {category.apps.map((app) => (
                      <TableRow key={app.app_key} hover>
                        <TableCell>
                          <Tooltip title={app.description || 'No description available'} arrow placement="right">
                            <Box>
                              <Typography variant="body2" fontWeight="medium">
                                {app.app_name}
                              </Typography>
                              {app.description && (
                                <Typography variant="caption" color="textSecondary">
                                  {app.description.length > 60
                                    ? `${app.description.substring(0, 60)}...`
                                    : app.description}
                                </Typography>
                              )}
                              {!app.is_active && (
                                <Chip
                                  label="Inactive"
                                  size="small"
                                  color="warning"
                                  sx={{ ml: 1, height: 20 }}
                                />
                              )}
                            </Box>
                          </Tooltip>
                        </TableCell>
                        {tiers.map((tier) => {
                          const isActive = tier === currentTier.toLowerCase();
                          const isAvailable = isAppInTier(app.app_key, tier);
                          return (
                            <TableCell
                              key={tier}
                              align="center"
                              sx={{
                                bgcolor: isActive ? `${tierConfig[tier].color}11` : 'transparent',
                                borderLeft: isActive ? `2px solid ${tierConfig[tier].color}` : 'none'
                              }}
                            >
                              {renderFeatureValue(isAvailable, tier, isActive)}
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
              Unlock more apps and take your platform to the next level
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
