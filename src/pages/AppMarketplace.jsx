import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  CardMedia,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Chip,
  Stack,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  ShoppingCart as ShoppingCartIcon,
  CheckCircle as CheckIcon,
  TrendingUp as UpgradeIcon,
  Public as PublicIcon,
  Business as BusinessIcon,
  AttachMoney as MoneyIcon
} from '@mui/icons-material';

/**
 * AppMarketplace - Browse & Purchase Apps
 *
 * Shows apps NOT in user's current tier:
 * - Premium apps (can be purchased individually)
 * - Higher-tier apps (requires tier upgrade)
 *
 * Fetches from /api/v1/my-apps/marketplace
 * Shows pricing, tier requirements, and where apps are hosted.
 */
const AppMarketplace = () => {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchMarketplaceApps();
  }, []);

  const fetchMarketplaceApps = async () => {
    try {
      const response = await fetch('/api/v1/my-apps/marketplace');
      if (!response.ok) throw new Error('Failed to fetch marketplace apps');

      const data = await response.json();
      setApps(data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching marketplace apps:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const getHostBadge = (launch_url) => {
    try {
      const url = new URL(launch_url);
      const host = url.hostname;

      if (host.includes('your-domain.com')) {
        return { label: 'UC Hosted', icon: <BusinessIcon />, color: 'primary' };
      } else {
        return { label: 'Federated Service', icon: <PublicIcon />, color: 'secondary' };
      }
    } catch (e) {
      return { label: 'External', icon: <PublicIcon />, color: 'default' };
    }
  };

  const handlePurchase = (app) => {
    // TODO: Implement purchase flow
    console.log('Purchase app:', app);
    alert(`Purchase flow for ${app.name} - Coming soon!`);
  };

  const handleUpgrade = (app) => {
    // Redirect to upgrade page
    window.location.href = '/admin/upgrade';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">Error loading marketplace: {error}</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          App Marketplace
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Discover premium apps and upgrade your subscription for more features
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {apps.map((app) => {
          const hostBadge = getHostBadge(app.launch_url);
          const isPurchasable = app.access_type === 'premium_purchase';
          const requiresUpgrade = app.access_type === 'upgrade_required';

          return (
            <Grid item xs={12} sm={6} md={4} key={app.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 4
                  }
                }}
              >
                {/* App Icon */}
                <Box
                  sx={{
                    p: 3,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    bgcolor: 'background.default',
                    minHeight: 140,
                    position: 'relative'
                  }}
                >
                  {/* Host Badge */}
                  <Box sx={{ position: 'absolute', top: 12, right: 12 }}>
                    <Chip
                      icon={hostBadge.icon}
                      label={hostBadge.label}
                      size="small"
                      color={hostBadge.color}
                      sx={{ fontSize: '0.7rem' }}
                    />
                  </Box>

                  {app.icon_url ? (
                    <CardMedia
                      component="img"
                      image={app.icon_url}
                      alt={app.name}
                      sx={{
                        width: 80,
                        height: 80,
                        objectFit: 'contain'
                      }}
                    />
                  ) : (
                    <ShoppingCartIcon sx={{ fontSize: 80, color: 'text.secondary' }} />
                  )}
                </Box>

                {/* App Details */}
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="h6" gutterBottom>
                    {app.name}
                  </Typography>

                  {app.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2, flexGrow: 1 }}
                    >
                      {app.description}
                    </Typography>
                  )}

                  <Divider sx={{ my: 2 }} />

                  {/* Pricing Info */}
                  <Box sx={{ mb: 2 }}>
                    {isPurchasable && (
                      <Stack direction="row" alignItems="center" spacing={1}>
                        <MoneyIcon color="primary" />
                        <Typography variant="h6" color="primary">
                          ${app.price || 0}/{app.billing_type || 'month'}
                        </Typography>
                      </Stack>
                    )}
                    {requiresUpgrade && (
                      <Chip
                        icon={<UpgradeIcon />}
                        label="Upgrade Required"
                        color="warning"
                        size="small"
                      />
                    )}
                  </Box>

                  {/* Features (if available) */}
                  {app.features && app.features.length > 0 && (
                    <List dense sx={{ mb: 2 }}>
                      {app.features.slice(0, 3).map((feature, idx) => (
                        <ListItem key={idx} disableGutters>
                          <ListItemIcon sx={{ minWidth: 32 }}>
                            <CheckIcon color="success" fontSize="small" />
                          </ListItemIcon>
                          <ListItemText
                            primary={feature}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  )}

                  {/* Action Button */}
                  {isPurchasable && (
                    <Button
                      variant="contained"
                      color="primary"
                      fullWidth
                      startIcon={<ShoppingCartIcon />}
                      onClick={() => handlePurchase(app)}
                    >
                      Purchase
                    </Button>
                  )}
                  {requiresUpgrade && (
                    <Button
                      variant="outlined"
                      color="warning"
                      fullWidth
                      startIcon={<UpgradeIcon />}
                      onClick={() => handleUpgrade(app)}
                    >
                      Upgrade Tier
                    </Button>
                  )}
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {apps.length === 0 && (
        <Box textAlign="center" py={8}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No additional apps available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            You have access to all apps in your subscription tier!
          </Typography>
          <Button
            variant="contained"
            color="primary"
            sx={{ mt: 3 }}
            onClick={() => window.location.href = '/admin/apps'}
          >
            View My Apps
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default AppMarketplace;
