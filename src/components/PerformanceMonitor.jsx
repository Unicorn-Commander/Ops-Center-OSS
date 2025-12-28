/**
 * Performance Monitor Component
 *
 * Real-time performance monitoring dashboard showing:
 * - Core Web Vitals (CLS, FID, LCP, FCP, TTFB, INP)
 * - Bundle size and chunk loading metrics
 * - API response times
 * - Cache hit rates
 * - Resource loading timeline
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  LinearProgress,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Timer as TimerIcon,
  Storage as StorageIcon,
  CloudDownload as CloudIcon
} from '@mui/icons-material';
import { getMetrics, getMetricsSummary, getNavigationMetrics, trackBundleMetrics, THRESHOLDS } from '../utils/webVitals';

const PerformanceMonitor = () => {
  const [metrics, setMetrics] = useState({});
  const [summary, setSummary] = useState({ overall: 'good', metrics: [], counts: {} });
  const [navigation, setNavigation] = useState(null);
  const [bundle, setBundle] = useState(null);
  const [apiMetrics, setApiMetrics] = useState([]);

  // Update metrics from web vitals
  useEffect(() => {
    const updateMetrics = () => {
      setMetrics(getMetrics());
      setSummary(getMetricsSummary());
      setNavigation(getNavigationMetrics());
      setBundle(trackBundleMetrics());
    };

    // Initial load
    updateMetrics();

    // Listen for web vitals events
    const handleWebVitals = (event) => {
      updateMetrics();
    };

    window.addEventListener('webvitals', handleWebVitals);

    // Update every 5 seconds
    const interval = setInterval(updateMetrics, 5000);

    return () => {
      window.removeEventListener('webvitals', handleWebVitals);
      clearInterval(interval);
    };
  }, []);

  // Fetch API performance metrics
  useEffect(() => {
    const fetchApiMetrics = async () => {
      try {
        const response = await fetch('/api/v1/analytics/performance', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken') || ''}`
          }
        });
        if (response.ok) {
          const data = await response.json();
          setApiMetrics(data.recent_requests || []);
        }
      } catch (error) {
        console.debug('API metrics unavailable:', error);
      }
    };

    fetchApiMetrics();
    const interval = setInterval(fetchApiMetrics, 10000); // Every 10 seconds

    return () => clearInterval(interval);
  }, []);

  // Get rating color
  const getRatingColor = (rating) => {
    switch (rating) {
      case 'good':
        return 'success';
      case 'needs-improvement':
        return 'warning';
      case 'poor':
        return 'error';
      default:
        return 'default';
    }
  };

  // Get rating icon
  const getRatingIcon = (rating) => {
    switch (rating) {
      case 'good':
        return <CheckIcon fontSize="small" />;
      case 'needs-improvement':
        return <WarningIcon fontSize="small" />;
      case 'poor':
        return <ErrorIcon fontSize="small" />;
      default:
        return <SpeedIcon fontSize="small" />;
    }
  };

  // Format metric value
  const formatValue = (name, value) => {
    if (name === 'CLS') {
      return value.toFixed(3);
    }
    return `${Math.round(value)}ms`;
  };

  // Format bytes
  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          <SpeedIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          Performance Monitor
        </Typography>
        <Chip
          icon={getRatingIcon(summary.overall)}
          label={`Overall: ${summary.overall.replace('-', ' ').toUpperCase()}`}
          color={getRatingColor(summary.overall)}
          size="medium"
        />
      </Box>

      <Grid container spacing={3}>
        {/* Core Web Vitals */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Core Web Vitals
              </Typography>
              <Grid container spacing={2}>
                {Object.entries(metrics).map(([name, metric]) => (
                  <Grid item xs={12} sm={6} md={4} lg={2} key={name}>
                    <Card variant="outlined">
                      <CardContent>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                          <Typography variant="caption" color="text.secondary">
                            {name}
                          </Typography>
                          <Chip
                            icon={getRatingIcon(metric.rating)}
                            label={metric.rating.split('-')[0].toUpperCase()}
                            color={getRatingColor(metric.rating)}
                            size="small"
                          />
                        </Box>
                        <Typography variant="h6">
                          {formatValue(name, metric.value)}
                        </Typography>
                        <Tooltip title={`Threshold: ${THRESHOLDS[name]?.good}ms (good), ${THRESHOLDS[name]?.needsImprovement}ms (needs improvement)`}>
                          <LinearProgress
                            variant="determinate"
                            value={Math.min((metric.value / THRESHOLDS[name]?.needsImprovement) * 100, 100)}
                            color={getRatingColor(metric.rating)}
                            sx={{ mt: 1 }}
                          />
                        </Tooltip>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Navigation Timing */}
        {navigation && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TimerIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Navigation Timing
                </Typography>
                <Table size="small">
                  <TableBody>
                    <TableRow>
                      <TableCell>DOM Content Loaded</TableCell>
                      <TableCell align="right">{Math.round(navigation.domContentLoaded)}ms</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>DOM Complete</TableCell>
                      <TableCell align="right">{Math.round(navigation.domComplete)}ms</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Load Complete</TableCell>
                      <TableCell align="right">{Math.round(navigation.loadComplete)}ms</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>DNS Lookup</TableCell>
                      <TableCell align="right">{Math.round(navigation.dns)}ms</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>TCP Connection</TableCell>
                      <TableCell align="right">{Math.round(navigation.tcp)}ms</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Request</TableCell>
                      <TableCell align="right">{Math.round(navigation.request)}ms</TableCell>
                    </TableRow>
                    <TableRow>
                      <TableCell>Response</TableCell>
                      <TableCell align="right">{Math.round(navigation.response)}ms</TableCell>
                    </TableRow>
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* Bundle Metrics */}
        {bundle && (
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <StorageIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Bundle Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Total Scripts
                    </Typography>
                    <Typography variant="h6">{bundle.scriptCount}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Total Size
                    </Typography>
                    <Typography variant="h6">{formatBytes(bundle.totalSize)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Avg Size
                    </Typography>
                    <Typography variant="h6">{formatBytes(bundle.avgSize)}</Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">
                      Load Time
                    </Typography>
                    <Typography variant="h6">{Math.round(bundle.totalTime)}ms</Typography>
                  </Grid>
                </Grid>
                {bundle.scripts && bundle.scripts.length > 0 && (
                  <>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2, mb: 1 }}>
                      Largest Bundles
                    </Typography>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>File</TableCell>
                          <TableCell align="right">Size</TableCell>
                          <TableCell align="right">Cache</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {bundle.scripts
                          .sort((a, b) => b.size - a.size)
                          .slice(0, 5)
                          .map((script, idx) => (
                            <TableRow key={idx}>
                              <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                                {script.name.substring(0, 30)}
                              </TableCell>
                              <TableCell align="right">{formatBytes(script.size)}</TableCell>
                              <TableCell align="right">
                                {script.cached ? (
                                  <Chip label="HIT" color="success" size="small" />
                                ) : (
                                  <Chip label="MISS" color="default" size="small" />
                                )}
                              </TableCell>
                            </TableRow>
                          ))}
                      </TableBody>
                    </Table>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        {/* API Performance */}
        {apiMetrics.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <CloudIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                  Recent API Requests
                </Typography>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Endpoint</TableCell>
                      <TableCell align="right">Duration</TableCell>
                      <TableCell align="right">Status</TableCell>
                      <TableCell align="right">Cached</TableCell>
                      <TableCell align="right">Timestamp</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {apiMetrics.slice(0, 10).map((request, idx) => (
                      <TableRow key={idx}>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                          {request.endpoint}
                        </TableCell>
                        <TableCell align="right">{Math.round(request.duration)}ms</TableCell>
                        <TableCell align="right">
                          <Chip
                            label={request.status}
                            color={request.status === 200 ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right">
                          {request.cached ? (
                            <Chip label="HIT" color="success" size="small" />
                          ) : (
                            <Chip label="MISS" color="default" size="small" />
                          )}
                        </TableCell>
                        <TableCell align="right">
                          {new Date(request.timestamp).toLocaleTimeString()}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default PerformanceMonitor;
