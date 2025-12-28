import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  IconButton,
  Alert,
  Skeleton,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider
} from '@mui/material';
import {
  ServerIcon,
  GlobeAltIcon,
  LockClosedIcon,
  ChartBarIcon,
  PlusIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../components/Toast';

const TraefikDashboard = () => {
  const navigate = useNavigate();
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const maxRetries = 3;
  const [dashboardData, setDashboardData] = useState({
    summary: {
      totalRoutes: 0,
      activeServices: 0,
      sslCertificates: 0,
      requestRate: 0
    },
    health: {
      status: 'unknown',
      lastCheck: null
    },
    recentActivity: [],
    certificates: {
      valid: 0,
      expiringSoon: 0,
      expired: 0
    }
  });

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      // NEW: Fetch REAL live data from Docker labels
      const [overviewResponse, routesResponse, servicesResponse] = await Promise.all([
        fetch('/api/v1/traefik/live/overview', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch('/api/v1/traefik/live/routes', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch('/api/v1/traefik/live/services', {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        })
      ]);

      if (!overviewResponse.ok || !routesResponse.ok || !servicesResponse.ok) {
        throw new Error(`HTTP error: ${overviewResponse.status}`);
      }

      const overview = await overviewResponse.json();
      const routes = await routesResponse.json();
      const services = await servicesResponse.json();

      // Count TLS certificates from routes
      const tlsRoutes = routes.filter(r => r.tls);
      const expiringSoonThreshold = new Date();
      expiringSoonThreshold.setDate(expiringSoonThreshold.getDate() + 30);

      // Transform live data to dashboard format
      const transformedData = {
        summary: {
          totalRoutes: overview.routes_count || 0,
          activeServices: overview.services_count || 0,
          sslCertificates: overview.tls_routes_count || 0,
          requestRate: 0 // Not available from Docker labels
        },
        health: {
          status: 'healthy',
          lastCheck: overview.timestamp || new Date().toISOString()
        },
        recentActivity: routes.slice(0, 5).map(route => ({
          type: 'route',
          action: 'active',
          resource: route.name,
          timestamp: overview.timestamp,
          details: `${route.rule} → ${route.service}`
        })),
        certificates: {
          valid: tlsRoutes.length,
          expiringSoon: 0, // Cannot determine without cert expiry dates
          expired: 0
        },
        // NEW: Include raw live data for detailed views
        liveRoutes: routes,
        liveServices: services
      };

      setDashboardData(transformedData);
      setError(null);
      setRetryCount(0);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      const errorMsg = `Failed to load Traefik dashboard: ${err.message}`;
      setError(errorMsg);

      // Retry logic for transient failures
      if (retryCount < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          loadDashboardData();
        }, 2000 * (retryCount + 1)); // Exponential backoff
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const getHealthColor = (status) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const SummaryCard = ({ title, value, icon: Icon, color, onClick }) => (
    <Card
      sx={{
        cursor: onClick ? 'pointer' : 'default',
        transition: 'all 0.2s',
        '&:hover': onClick ? { transform: 'translateY(-4px)', boxShadow: 6 } : {}
      }}
      onClick={onClick}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between">
          <Box>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" component="div">
              {loading ? <Skeleton width={80} /> : value}
            </Typography>
          </Box>
          <Box
            sx={{
              bgcolor: `${color}.lighter`,
              borderRadius: '50%',
              p: 2,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Icon style={{ width: 32, height: 32, color: `var(--${color}-main)` }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const ActivityItem = ({ activity }) => (
    <ListItem>
      <ListItemIcon>
        {activity.type === 'create' && <PlusIcon style={{ width: 20, height: 20, color: 'green' }} />}
        {activity.type === 'update' && <ArrowPathIcon style={{ width: 20, height: 20, color: 'blue' }} />}
        {activity.type === 'delete' && <ExclamationTriangleIcon style={{ width: 20, height: 20, color: 'red' }} />}
      </ListItemIcon>
      <ListItemText
        primary={activity.description}
        secondary={new Date(activity.timestamp).toLocaleString()}
      />
    </ListItem>
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Traefik Dashboard
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Reverse proxy configuration and monitoring
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <Button
            variant="outlined"
            startIcon={<ArrowPathIcon style={{ width: 20, height: 20 }} />}
            onClick={loadDashboardData}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<PlusIcon style={{ width: 20, height: 20 }} />}
            onClick={() => navigate('/admin/traefik/routes?action=new')}
          >
            Add Route
          </Button>
        </Box>
      </Box>

      {/* Error Alert with Retry */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => {
                setError(null);
                setRetryCount(0);
                loadDashboardData();
              }}
              disabled={retryCount >= maxRetries && retryCount > 0}
            >
              Retry Now
            </Button>
          }
        >
          <Box>
            <Typography variant="body2" fontWeight="medium">
              {error}
            </Typography>
            {retryCount > 0 && retryCount < maxRetries && (
              <Typography variant="caption" display="block" mt={0.5}>
                Retrying... (Attempt {retryCount}/{maxRetries})
              </Typography>
            )}
            {retryCount >= maxRetries && (
              <Typography variant="caption" display="block" mt={0.5}>
                Maximum retry attempts reached. Please check your network connection or try again later.
              </Typography>
            )}
          </Box>
        </Alert>
      )}

      {/* Summary Cards */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="Total Routes"
            value={dashboardData?.summary?.totalRoutes || 0}
            icon={GlobeAltIcon}
            color="primary"
            onClick={() => navigate('/admin/traefik/routes')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="Active Services"
            value={dashboardData?.summary?.activeServices || 0}
            icon={ServerIcon}
            color="info"
            onClick={() => navigate('/admin/traefik/services')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="SSL Certificates"
            value={dashboardData?.summary?.sslCertificates || 0}
            icon={LockClosedIcon}
            color="success"
            onClick={() => navigate('/admin/traefik/ssl')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <SummaryCard
            title="Requests/sec"
            value={dashboardData?.summary?.requestRate?.toFixed(1) ?? '0.0'}
            icon={ChartBarIcon}
            color="warning"
            onClick={() => navigate('/admin/traefik/metrics')}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Health Status */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box display="flex" alignItems="center" gap={2} mt={2}>
                <Chip
                  label={(dashboardData?.health?.status || 'unknown').toUpperCase()}
                  color={getHealthColor(dashboardData?.health?.status)}
                  icon={<CheckCircleIcon style={{ width: 16, height: 16 }} />}
                />
                {dashboardData?.health?.lastCheck && (
                  <Typography variant="body2" color="text.secondary">
                    Last checked: {new Date(dashboardData.health.lastCheck).toLocaleString()}
                  </Typography>
                )}
              </Box>

              <Box mt={3}>
                <Typography variant="subtitle2" gutterBottom>
                  SSL Certificates
                </Typography>
                <Grid container spacing={2} mt={1}>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="success.main">
                        {dashboardData?.certificates?.valid || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Valid
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="warning.main">
                        {dashboardData?.certificates?.expiringSoon || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Expiring Soon
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={4}>
                    <Box textAlign="center">
                      <Typography variant="h4" color="error.main">
                        {dashboardData?.certificates?.expired || 0}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Expired
                      </Typography>
                    </Box>
                  </Grid>
                </Grid>
              </Box>

              <Box mt={3} display="flex" gap={2}>
                <Button
                  variant="outlined"
                  size="small"
                  fullWidth
                  onClick={() => navigate('/admin/traefik/ssl')}
                >
                  View Certificates
                </Button>
                <Button
                  variant="outlined"
                  size="small"
                  fullWidth
                  startIcon={<DocumentTextIcon style={{ width: 16, height: 16 }} />}
                  onClick={() => navigate('/admin/logs')}
                >
                  View Logs
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recent Activity
              </Typography>

              {loading ? (
                <Box>
                  {[1, 2, 3, 4].map((i) => (
                    <Box key={i} mb={2}>
                      <Skeleton variant="text" width="80%" />
                      <Skeleton variant="text" width="40%" />
                    </Box>
                  ))}
                </Box>
              ) : (dashboardData?.recentActivity?.length || 0) > 0 ? (
                <List>
                  {(dashboardData?.recentActivity || []).slice(0, 5).map((activity, index) => (
                    <React.Fragment key={activity.id}>
                      <ActivityItem activity={activity} />
                      {index < (dashboardData?.recentActivity?.length || 0) - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box textAlign="center" py={4}>
                  <ClockIcon style={{ width: 48, height: 48, color: '#ccc', margin: '0 auto' }} />
                  <Typography variant="body2" color="text.secondary" mt={2}>
                    No recent activity
                  </Typography>
                </Box>
              )}

              {(dashboardData?.recentActivity?.length || 0) > 5 && (
                <Box mt={2} textAlign="center">
                  <Button size="small" onClick={() => navigate('/admin/logs')}>
                    View All Activity
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Grid container spacing={2} mt={1}>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<PlusIcon style={{ width: 20, height: 20 }} />}
                    onClick={() => navigate('/admin/traefik/routes?action=new')}
                  >
                    Add Route
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<ServerIcon style={{ width: 20, height: 20 }} />}
                    onClick={() => navigate('/admin/traefik/services?action=discover')}
                  >
                    Discover Services
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<LockClosedIcon style={{ width: 20, height: 20 }} />}
                    onClick={() => navigate('/admin/traefik/ssl?action=renew')}
                  >
                    Renew Certificates
                  </Button>
                </Grid>
                <Grid item xs={12} sm={6} md={3}>
                  <Button
                    variant="outlined"
                    fullWidth
                    startIcon={<ChartBarIcon style={{ width: 20, height: 20 }} />}
                    onClick={() => navigate('/admin/traefik/metrics')}
                  >
                    View Metrics
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default TraefikDashboard;
