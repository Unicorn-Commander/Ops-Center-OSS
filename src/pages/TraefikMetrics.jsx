import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Box,
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  Skeleton
} from '@mui/material';
import {
  ChartBarIcon,
  ArrowDownTrayIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Line, Bar, Pie } from 'react-chartjs-2';
import { useToast } from '../components/Toast';
import { useTheme } from '../contexts/ThemeContext';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

const TraefikMetrics = () => {
  const toast = useToast();
  const { theme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('day');
  const [retryCount, setRetryCount] = useState(0);
  const [metricsData, setMetricsData] = useState({
    requestsByRoute: [],
    responseTimes: [],
    errorRates: [],
    statusCodes: {}
  });

  const maxRetries = 3;

  useEffect(() => {
    loadMetrics();
  }, [timeRange]);

  const loadMetrics = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/traefik/metrics?range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setMetricsData(data);
      setError(null);
      setRetryCount(0);
    } catch (err) {
      console.error('Failed to load Traefik metrics:', err);
      const errorMsg = `Failed to load traffic metrics: ${err.message}`;
      setError(errorMsg);

      // Retry logic for transient failures
      if (retryCount < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => prev + 1);
          loadMetrics();
        }, 2000 * (retryCount + 1)); // Exponential backoff
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const response = await fetch(`/api/v1/traefik/metrics/export?range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: Export failed`);
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `traefik-metrics-${timeRange}-${Date.now()}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('Metrics exported successfully');
    } catch (err) {
      console.error('Export failed:', err);
      const errorMsg = `Failed to export metrics: ${err.message}`;
      setError(errorMsg);
      toast.error(errorMsg);
    }
  };

  // Chart configurations
  const requestsByRouteData = {
    labels: metricsData.requestsByRoute?.map((r) => r.route) || [],
    datasets: [
      {
        label: 'Requests',
        data: metricsData.requestsByRoute?.map((r) => r.count) || [],
        backgroundColor: 'rgba(99, 102, 241, 0.5)',
        borderColor: 'rgba(99, 102, 241, 1)',
        borderWidth: 1
      }
    ]
  };

  const responseTimesData = {
    labels: metricsData.responseTimes?.map((r) => r.timestamp) || [],
    datasets: [
      {
        label: 'Response Time (ms)',
        data: metricsData.responseTimes?.map((r) => r.avgTime) || [],
        borderColor: 'rgba(34, 197, 94, 1)',
        backgroundColor: 'rgba(34, 197, 94, 0.2)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  const errorRatesData = {
    labels: metricsData.errorRates?.map((r) => r.timestamp) || [],
    datasets: [
      {
        label: 'Error Rate (%)',
        data: metricsData.errorRates?.map((r) => r.rate) || [],
        borderColor: 'rgba(239, 68, 68, 1)',
        backgroundColor: 'rgba(239, 68, 68, 0.2)',
        tension: 0.4,
        fill: true
      }
    ]
  };

  const statusCodesData = {
    labels: Object.keys(metricsData.statusCodes || {}),
    datasets: [
      {
        data: Object.values(metricsData.statusCodes || {}),
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',   // 2xx - Green
          'rgba(251, 191, 36, 0.8)',  // 3xx - Yellow
          'rgba(59, 130, 246, 0.8)',  // 4xx - Blue
          'rgba(239, 68, 68, 0.8)'    // 5xx - Red
        ],
        borderWidth: 0
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top'
      }
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Traffic Metrics
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Monitor traffic and performance
          </Typography>
        </Box>
        <Box display="flex" gap={2}>
          <FormControl sx={{ minWidth: 150 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="hour">Last Hour</MenuItem>
              <MenuItem value="day">Last 24 Hours</MenuItem>
              <MenuItem value="week">Last Week</MenuItem>
              <MenuItem value="month">Last Month</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<ArrowPathIcon style={{ width: 20, height: 20 }} />}
            onClick={loadMetrics}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<ArrowDownTrayIcon style={{ width: 20, height: 20 }} />}
            onClick={handleExport}
          >
            Export CSV
          </Button>
        </Box>
      </Box>

      {/* Error Alert with Retry */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Alert
            severity="error"
            sx={{ mb: 3 }}
            onClose={() => setError(null)}
            action={
              <Box display="flex" alignItems="center" gap={1}>
                {retryCount > 0 && retryCount < maxRetries && (
                  <Typography variant="caption" sx={{ mr: 1 }}>
                    Retrying... (Attempt {retryCount}/{maxRetries})
                  </Typography>
                )}
                <Button
                  color="inherit"
                  size="small"
                  onClick={loadMetrics}
                  startIcon={<ArrowPathIcon style={{ width: 16, height: 16 }} />}
                >
                  Retry Now
                </Button>
              </Box>
            }
            icon={<ExclamationTriangleIcon style={{ width: 20, height: 20 }} />}
          >
            {error}
          </Alert>
        </motion.div>
      )}

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Requests by Route */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Requests by Route
              </Typography>
              <Box sx={{ height: 300 }}>
                {loading ? (
                  <Skeleton variant="rectangular" height="100%" />
                ) : (
                  <Bar data={requestsByRouteData} options={chartOptions} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Response Times */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Average Response Time
              </Typography>
              <Box sx={{ height: 300 }}>
                {loading ? (
                  <Skeleton variant="rectangular" height="100%" />
                ) : (
                  <Line data={responseTimesData} options={chartOptions} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Error Rates */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Error Rate Over Time
              </Typography>
              <Box sx={{ height: 300 }}>
                {loading ? (
                  <Skeleton variant="rectangular" height="100%" />
                ) : (
                  <Line data={errorRatesData} options={chartOptions} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Status Codes Distribution */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                HTTP Status Codes
              </Typography>
              <Box sx={{ height: 300 }}>
                {loading ? (
                  <Skeleton variant="rectangular" height="100%" />
                ) : (
                  <Pie data={statusCodesData} options={chartOptions} />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Summary Statistics */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Summary Statistics
        </Typography>
        <Grid container spacing={3} mt={1}>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="primary.main">
                {loading ? <Skeleton width={80} /> : metricsData.totalRequests?.toLocaleString() || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Requests
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="success.main">
                {loading ? <Skeleton width={80} /> : `${metricsData.avgResponseTime || 0}ms`}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Response Time
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="warning.main">
                {loading ? <Skeleton width={80} /> : `${metricsData.errorRate || 0}%`}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Error Rate
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box textAlign="center">
              <Typography variant="h4" color="info.main">
                {loading ? <Skeleton width={80} /> : metricsData.activeRoutes || 0}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Active Routes
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default TraefikMetrics;
