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
  Stack
} from '@mui/material';
import { Launch as LaunchIcon, Public as PublicIcon, Business as BusinessIcon } from '@mui/icons-material';

/**
 * AppsLauncher - Tier-Filtered Apps Dashboard
 *
 * Shows ONLY apps the user's subscription tier includes.
 * Fetches from /api/v1/my-apps/authorized (tier-filtered backend endpoint)
 *
 * Apps can be hosted ANYWHERE:
 * - Same domain (your-domain.com/admin)
 * - Different subdomain (chat.your-domain.com)
 * - Completely different domain (search.centerdeep.online)
 *
 * launch_url is the source of truth for where the app lives.
 */
const AppsLauncher = () => {
  const [apps, setApps] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchApps();
  }, []);

  const fetchApps = async () => {
    try {
      // NEW API: tier-filtered apps the user has access to
      const response = await fetch('/api/v1/my-apps/authorized');
      if (!response.ok) throw new Error('Failed to fetch apps');

      const data = await response.json();
      setApps(data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching apps:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleLaunch = (app) => {
    // Open app in new tab - launch_url can be ANYWHERE
    window.open(app.launch_url, '_blank', 'noopener,noreferrer');
  };

  const getHostBadge = (launch_url) => {
    try {
      const url = new URL(launch_url);
      const host = url.hostname;

      // Determine if hosted by UC or federated
      if (host.includes('your-domain.com')) {
        return { label: 'UC Hosted', icon: <BusinessIcon />, color: 'primary' };
      } else {
        return { label: 'Federated', icon: <PublicIcon />, color: 'secondary' };
      }
    } catch (e) {
      return { label: 'External', icon: <PublicIcon />, color: 'default' };
    }
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
        <Alert severity="error">Error loading apps: {error}</Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box mb={4}>
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600 }}>
          My Apps
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Apps included in your subscription tier
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {apps.map((app) => {
          const hostBadge = getHostBadge(app.launch_url);

          return (
            <Grid item xs={12} sm={6} md={4} lg={3} key={app.id}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  position: 'relative',
                  '&:hover': {
                    transform: 'translateY(-8px)',
                    boxShadow: 6,
                    borderColor: 'primary.main',
                    borderWidth: 2,
                    borderStyle: 'solid'
                  }
                }}
                onClick={() => handleLaunch(app)}
              >
                {/* Host Badge */}
                <Box sx={{ position: 'absolute', top: 12, right: 12, zIndex: 1 }}>
                  <Chip
                    icon={hostBadge.icon}
                    label={hostBadge.label}
                    size="small"
                    color={hostBadge.color}
                    sx={{ fontSize: '0.7rem' }}
                  />
                </Box>

                {/* App Icon */}
                <Box
                  sx={{
                    p: 3,
                    pt: 5,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    bgcolor: 'background.default',
                    minHeight: 140
                  }}
                >
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
                    <LaunchIcon sx={{ fontSize: 80, color: 'text.secondary' }} />
                  )}
                </Box>

                {/* App Info */}
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="h6" gutterBottom textAlign="center">
                    {app.name}
                  </Typography>

                  {app.description && (
                    <Typography
                      variant="body2"
                      color="text.secondary"
                      sx={{ mb: 2, flexGrow: 1, textAlign: 'center' }}
                    >
                      {app.description.length > 80
                        ? app.description.substring(0, 80) + '...'
                        : app.description
                      }
                    </Typography>
                  )}

                  <Button
                    variant="contained"
                    startIcon={<LaunchIcon />}
                    fullWidth
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLaunch(app);
                    }}
                    sx={{ mt: 'auto' }}
                  >
                    Launch App
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {apps.length === 0 && (
        <Box textAlign="center" py={8}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No apps in your tier
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upgrade your subscription to access more apps
          </Typography>
          <Button
            variant="contained"
            color="primary"
            sx={{ mt: 3 }}
            onClick={() => window.location.href = '/admin/apps/marketplace'}
          >
            Browse Marketplace
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default AppsLauncher;
