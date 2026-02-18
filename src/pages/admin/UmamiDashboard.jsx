import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Analytics as AnalyticsIcon,
  Refresh as RefreshIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  People as PeopleIcon,
  Visibility as VisibilityIcon,
  OpenInNew as OpenInNewIcon,
  Language as LanguageIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

const UmamiDashboard = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [period, setPeriod] = useState('24h');
  const [selectedWebsite, setSelectedWebsite] = useState(null);
  const [websiteDetails, setWebsiteDetails] = useState(null);

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/umami/dashboard?period=${period}`);
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setDashboardData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchWebsiteDetails = async (websiteId) => {
    try {
      const [statsRes, pageviewsRes, metricsRes] = await Promise.all([
        fetch(`/api/v1/umami/websites/${websiteId}/stats?period=${period}`),
        fetch(`/api/v1/umami/websites/${websiteId}/pageviews?period=${period}`),
        fetch(`/api/v1/umami/websites/${websiteId}/metrics?metric_type=url&period=${period}`)
      ]);

      const stats = await statsRes.json();
      const pageviews = await pageviewsRes.json();
      const metrics = await metricsRes.json();

      setWebsiteDetails({ stats, pageviews, metrics });
    } catch (err) {
      console.error('Failed to fetch website details:', err);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [period]);

  useEffect(() => {
    if (selectedWebsite) {
      fetchWebsiteDetails(selectedWebsite);
    }
  }, [selectedWebsite, period]);

  const formatNumber = (num) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num?.toString() || '0';
  };

  const StatCard = ({ title, value, icon: Icon, change, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="textSecondary" variant="body2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {formatNumber(value)}
            </Typography>
            {change !== undefined && (
              <Box sx={{ display: 'flex', alignItems: 'center', mt: 1 }}>
                {change >= 0 ? (
                  <TrendingUpIcon sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                ) : (
                  <TrendingDownIcon sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
                )}
                <Typography
                  variant="body2"
                  sx={{ color: change >= 0 ? 'success.main' : 'error.main' }}
                >
                  {Math.abs(change)}%
                </Typography>
              </Box>
            )}
          </Box>
          <Box
            sx={{
              bgcolor: `${color}.lighter`,
              borderRadius: 2,
              p: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Icon sx={{ color: `${color}.main`, fontSize: 28 }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading && !dashboardData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Umami Analytics"
        subtitle="Website analytics and visitor insights"
        actions={(
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select value={period} onChange={(e) => setPeriod(e.target.value)} label="Period">
                <MenuItem value="24h">Last 24 Hours</MenuItem>
                <MenuItem value="7d">Last 7 Days</MenuItem>
                <MenuItem value="30d">Last 30 Days</MenuItem>
                <MenuItem value="90d">Last 90 Days</MenuItem>
              </Select>
            </FormControl>
            <Tooltip title="Refresh">
              <IconButton onClick={fetchDashboard} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Open Umami Dashboard">
              <IconButton
                component="a"
                href="http://localhost:3002"
                target="_blank"
                rel="noopener"
              >
                <OpenInNewIcon />
              </IconButton>
            </Tooltip>
          </Box>
        )}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      {dashboardData && (
        <>
          {/* Summary Stats */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Pageviews"
                value={dashboardData.totals?.pageviews || 0}
                icon={VisibilityIcon}
                color="primary"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Unique Visitors"
                value={dashboardData.totals?.visitors || 0}
                icon={PeopleIcon}
                color="success"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Total Visits"
                value={dashboardData.totals?.visits || 0}
                icon={TrendingUpIcon}
                color="info"
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <StatCard
                title="Websites Tracked"
                value={dashboardData.totals?.websites_count || 0}
                icon={LanguageIcon}
                color="warning"
              />
            </Grid>
          </Grid>

          {/* Websites Table */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <LanguageIcon />
                Tracked Websites
              </Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Website</TableCell>
                      <TableCell>Domain</TableCell>
                      <TableCell align="right">Pageviews</TableCell>
                      <TableCell align="right">Visitors</TableCell>
                      <TableCell align="right">Visits</TableCell>
                      <TableCell align="right">Bounce Rate</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {dashboardData.websites?.map((website) => {
                      const stats = website.stats || {};
                      const pageviews = stats.pageviews?.value || 0;
                      const visitors = stats.visitors?.value || 0;
                      const visits = stats.visits?.value || 0;
                      const bounces = stats.bounces?.value || 0;
                      const bounceRate = visits > 0 ? ((bounces / visits) * 100).toFixed(1) : 0;

                      return (
                        <TableRow
                          key={website.id}
                          hover
                          sx={{
                            cursor: 'pointer',
                            bgcolor: selectedWebsite === website.id ? 'action.selected' : 'inherit'
                          }}
                          onClick={() => setSelectedWebsite(website.id)}
                        >
                          <TableCell>
                            <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                              {website.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={website.domain}
                              size="small"
                              variant="outlined"
                              sx={{ fontFamily: 'monospace' }}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                              {formatNumber(pageviews)}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">{formatNumber(visitors)}</TableCell>
                          <TableCell align="right">{formatNumber(visits)}</TableCell>
                          <TableCell align="right">
                            <Chip
                              label={`${bounceRate}%`}
                              size="small"
                              color={bounceRate > 70 ? 'warning' : bounceRate > 50 ? 'default' : 'success'}
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Tooltip title="View Details">
                              <IconButton
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setSelectedWebsite(website.id);
                                }}
                              >
                                <VisibilityIcon fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                    {(!dashboardData.websites || dashboardData.websites.length === 0) && (
                      <TableRow>
                        <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                          <Typography color="textSecondary">
                            No websites tracked yet. Add websites in Umami dashboard.
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>

          {/* Website Details */}
          {selectedWebsite && websiteDetails && (
            <Card sx={{ mt: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Website Details
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      Top Pages
                    </Typography>
                    <TableContainer component={Paper} variant="outlined">
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>URL</TableCell>
                            <TableCell align="right">Views</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {websiteDetails.metrics?.slice(0, 10).map((metric, idx) => (
                            <TableRow key={idx}>
                              <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                                {metric.x || metric.url || '-'}
                              </TableCell>
                              <TableCell align="right">{metric.y || metric.count || 0}</TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                      Stats Summary
                    </Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      {websiteDetails.stats && Object.entries(websiteDetails.stats).map(([key, val]) => (
                        <Box key={key} sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <Typography variant="body2" color="textSecondary" sx={{ textTransform: 'capitalize' }}>
                            {key}
                          </Typography>
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {typeof val === 'object' ? val.value : val}
                          </Typography>
                        </Box>
                      ))}
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </Box>
  );
};

export default UmamiDashboard;
