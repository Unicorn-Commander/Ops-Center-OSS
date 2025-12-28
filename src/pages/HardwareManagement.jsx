import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  LinearProgress,
  CircularProgress,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  ToggleButtonGroup,
  ToggleButton,
  Alert,
  AlertTitle,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Computer as ComputerIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  CleaningServices as CleanIcon,
  RestartAlt as RestartIcon,
  Tune as TuneIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

// Import new hardware components
import GPUMonitorCard from '../components/hardware/GPUMonitorCard';
import StorageBreakdown from '../components/hardware/StorageBreakdown';
import NetworkTrafficChart from '../components/hardware/NetworkTrafficChart';
import ServiceResourceAllocation from '../components/hardware/ServiceResourceAllocation';

// Import safe utilities
import { safeToFixed } from '../utils/safeNumberUtils';

const HardwareManagement = () => {
  const [hardwareStatus, setHardwareStatus] = useState(null);
  const [history, setHistory] = useState([]);
  const [services, setServices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [networkData, setNetworkData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState('1hour');
  const [selectedMetric, setSelectedMetric] = useState('gpu_utilization');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [optimizeDialogOpen, setOptimizeDialogOpen] = useState(false);
  const [error, setError] = useState(null);

  // Show snackbar notification
  const showNotification = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  // Fetch hardware status
  const fetchHardwareStatus = async (showLoading = true) => {
    if (showLoading) setRefreshing(true);

    try {
      const response = await fetch('/api/v1/system/hardware', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setHardwareStatus(data);
        setError(null); // Clear any previous errors
      } else {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText || response.statusText}`);
      }
    } catch (error) {
      console.error('Failed to fetch hardware status:', error);
      setError(`Failed to load hardware data: ${error.message}`);
      showNotification(`Failed to load hardware data: ${error.message}`, 'error');
    } finally {
      if (showLoading) setRefreshing(false);
    }
  };

  // Fetch historical data - DISABLED (endpoint not available)
  const fetchHistory = async () => {
    // TODO: Implement /api/v1/hardware/history endpoint
    setHistory([]);
  };

  // Fetch service allocations
  const fetchServices = async () => {
    try {
      // Use existing /api/v1/services endpoint
      const response = await fetch('/api/v1/services', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setServices(data || []);
      }
    } catch (error) {
      console.error('Failed to fetch services:', error);
      setServices([]);
    }
  };

  // Check for alerts - Generate client-side based on hardware status
  const checkAlerts = async () => {
    const alerts = [];

    if (hardwareStatus) {
      // Check GPU temperature (with null safety)
      const gpuTemp = hardwareStatus.gpu?.temperature;
      if (gpuTemp !== undefined && gpuTemp !== null) {
        if (gpuTemp > 85) {
          alerts.push({
            severity: 'critical',
            component: 'GPU',
            metric: 'temperature',
            message: `GPU temperature is ${safeToFixed(gpuTemp, 1)}°C (critical: >85°C)`
          });
        } else if (gpuTemp > 75) {
          alerts.push({
            severity: 'warning',
            component: 'GPU',
            metric: 'temperature',
            message: `GPU temperature is ${safeToFixed(gpuTemp, 1)}°C (warning: >75°C)`
          });
        }
      }

      // Check disk space (with null safety)
      const diskPct = hardwareStatus.disk?.percentage;
      if (diskPct !== undefined && diskPct !== null) {
        if (diskPct > 90) {
          alerts.push({
            severity: 'critical',
            component: 'Disk',
            metric: 'space',
            message: `Disk usage is ${safeToFixed(diskPct, 1)}% (critical: >90%)`
          });
        } else if (diskPct > 80) {
          alerts.push({
            severity: 'warning',
            component: 'Disk',
            metric: 'space',
            message: `Disk usage is ${safeToFixed(diskPct, 1)}% (warning: >80%)`
          });
        }
      }

      // Check memory usage (with null safety)
      const memPct = hardwareStatus.memory?.percentage;
      if (memPct !== undefined && memPct !== null) {
        if (memPct > 90) {
          alerts.push({
            severity: 'warning',
            component: 'Memory',
            metric: 'usage',
            message: `Memory usage is ${safeToFixed(memPct, 1)}% (warning: >90%)`
          });
        }
      }
    }

    setAlerts(alerts);
  };

  // Fetch network data - Use system network endpoint
  const fetchNetworkData = async () => {
    try {
      const response = await fetch('/api/v1/system/network', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        // Map network config to traffic data format
        setNetworkData({
          upload_rate: 0,
          download_rate: 0,
          active_connections: 0,
          tcp_connections: 0,
          udp_connections: 0,
          interface: data.interface || 'N/A'
        });
      } else {
        // Fallback to reasonable defaults if API not available
        setNetworkData({
          upload_rate: 0,
          download_rate: 0,
          active_connections: 0,
          tcp_connections: 0,
          udp_connections: 0
        });
      }
    } catch (error) {
      console.error('Failed to fetch network data:', error);
      // Fallback to reasonable defaults
      setNetworkData({
        upload_rate: 0,
        download_rate: 0,
        active_connections: 0,
        tcp_connections: 0,
        udp_connections: 0
      });
    }
  };

  // Initial load
  useEffect(() => {
    const loadAll = async () => {
      setLoading(true);
      await Promise.all([
        fetchHardwareStatus(false),
        fetchHistory(),
        fetchServices(),
        checkAlerts(),
        fetchNetworkData()
      ]);
      setLoading(false);
    };

    loadAll();
  }, [timeRange]);

  // Check alerts whenever hardware status changes
  useEffect(() => {
    if (hardwareStatus) {
      checkAlerts();
    }
  }, [hardwareStatus]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchHardwareStatus(false);
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Manual refresh
  const handleRefresh = () => {
    fetchHardwareStatus(true);
    fetchHistory();
    fetchServices();
    checkAlerts();
    fetchNetworkData();
  };

  // Handle storage cleanup
  const handleStorageCleanup = async () => {
    try {
      const response = await fetch('/api/v1/hardware/cleanup', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operations: ['logs', 'docker_cache', 'temp_files'] })
      });

      if (response.ok) {
        showNotification('Storage cleanup completed successfully', 'success');
        fetchHardwareStatus();
      } else {
        showNotification('Storage cleanup failed', 'error');
      }
    } catch (error) {
      console.error('Storage cleanup error:', error);
      showNotification('Storage cleanup error: ' + error.message, 'error');
    }
  };

  // Handle service action (restart, stop, start)
  const handleServiceAction = async (serviceName, action) => {
    try {
      const response = await fetch(`/api/v1/hardware/services/${serviceName}/${action}`, {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        showNotification(`Service ${serviceName} ${action}ed successfully`, 'success');
        fetchServices();
      } else {
        showNotification(`Failed to ${action} service ${serviceName}`, 'error');
      }
    } catch (error) {
      console.error('Service action error:', error);
      showNotification(`Service action error: ${error.message}`, 'error');
    }
  };

  // Handle GPU optimization
  const handleOptimizeGPU = async () => {
    try {
      const response = await fetch('/api/v1/hardware/gpu/optimize', {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        showNotification('GPU optimization completed', 'success');
        setOptimizeDialogOpen(false);
        fetchHardwareStatus();
      } else {
        showNotification('GPU optimization failed', 'error');
      }
    } catch (error) {
      console.error('GPU optimization error:', error);
      showNotification('GPU optimization error: ' + error.message, 'error');
    }
  };

  // Format bytes to GB
  const formatGB = (bytes) => {
    return safeToFixed(bytes / (1024 ** 3), 2);
  };

  // Format temperature color
  const getTempColor = (temp, type = 'gpu') => {
    if (type === 'gpu') {
      if (temp < 70) return 'success';
      if (temp < 80) return 'warning';
      return 'error';
    } else {
      if (temp < 70) return 'success';
      if (temp < 80) return 'warning';
      return 'error';
    }
  };

  // Get status chip color
  const getStatusColor = (status) => {
    if (status === 'running') return 'success';
    if (status === 'stopped') return 'error';
    return 'default';
  };

  // Prepare chart data
  const getChartData = () => {
    const metricHistory = history.find(h => h.metric_name === selectedMetric.split('_')[0]);
    if (!metricHistory) return [];

    return metricHistory.data_points.map(point => ({
      timestamp: new Date(point.timestamp).toLocaleTimeString(),
      value: selectedMetric === 'gpu_utilization' ? point.utilization :
             selectedMetric === 'gpu_temperature' ? point.temperature :
             selectedMetric === 'gpu_memory' ? point.memory_percent :
             selectedMetric === 'cpu_usage' ? point.usage :
             selectedMetric === 'cpu_temperature' ? point.temperature :
             selectedMetric === 'memory_usage' ? point.percentage :
             point.percentage
    }));
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" fontWeight="bold">
            Hardware Management
          </Typography>
          <Typography variant="body2" color="text.secondary" mt={0.5}>
            Monitor and manage system resources and services
          </Typography>
        </Box>
        <Box display="flex" gap={2} alignItems="center">
          <Button
            variant="outlined"
            startIcon={<TuneIcon />}
            onClick={() => setOptimizeDialogOpen(true)}
            disabled={!hardwareStatus?.gpu}
          >
            Optimize GPU
          </Button>
          <Chip
            label={autoRefresh ? 'Auto-refresh: ON' : 'Auto-refresh: OFF'}
            color={autoRefresh ? 'success' : 'default'}
            onClick={() => setAutoRefresh(!autoRefresh)}
            sx={{ cursor: 'pointer' }}
          />
          <Tooltip title="Refresh All">
            <IconButton onClick={handleRefresh} disabled={refreshing} color="primary">
              <RefreshIcon sx={{ animation: refreshing ? 'spin 1s linear infinite' : 'none' }} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          action={
            <Button color="inherit" size="small" onClick={() => fetchHardwareStatus(true)}>
              Retry
            </Button>
          }
        >
          <AlertTitle>Failed to Load Hardware Data</AlertTitle>
          {error}
        </Alert>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <Box mb={3}>
          {alerts.map((alert, index) => (
            <Alert
              key={index}
              severity={alert.severity}
              icon={alert.severity === 'critical' ? <ErrorIcon /> : <WarningIcon />}
              sx={{ mb: 1 }}
            >
              <AlertTitle>{alert.component} - {alert.metric}</AlertTitle>
              {alert.message}
            </Alert>
          ))}
        </Box>
      )}

      {/* Enhanced Hardware Management Grid */}
      <Grid container spacing={3} mb={3}>
        {/* GPU Monitor (using new component) */}
        {hardwareStatus?.gpu && (
          <Grid item xs={12} md={6} lg={4}>
            <GPUMonitorCard
              gpuData={hardwareStatus.gpu}
              onRefresh={() => fetchHardwareStatus(true)}
              loading={refreshing}
            />
          </Grid>
        )}

        {/* Storage Breakdown (using new component) */}
        <Grid item xs={12} md={6} lg={4}>
          <StorageBreakdown
            diskData={hardwareStatus?.disk}
            onRefresh={() => fetchHardwareStatus(true)}
            onCleanup={handleStorageCleanup}
            loading={refreshing}
          />
        </Grid>

        {/* Network Traffic (using new component) */}
        <Grid item xs={12} md={12} lg={4}>
          <NetworkTrafficChart
            networkData={networkData || {
              upload_rate: 0,
              download_rate: 0,
              active_connections: 0,
              tcp_connections: 0,
              udp_connections: 0
            }}
            onRefresh={fetchNetworkData}
            loading={refreshing}
          />
        </Grid>

        {/* CPU & Memory Cards (compact versions) */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <ComputerIcon sx={{ mr: 1, color: 'info.main' }} />
                <Typography variant="h6">CPU</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={1}>
                {hardwareStatus?.cpu?.model || 'Unknown CPU'}
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block" mb={2}>
                {hardwareStatus?.cpu?.cores} Cores / {hardwareStatus?.cpu?.threads} Threads
              </Typography>
              <Box mb={2}>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="caption">Usage</Typography>
                  <Typography variant="caption">
                    {safeToFixed(hardwareStatus?.cpu?.usage, 1)}%
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={hardwareStatus?.cpu?.usage || 0}
                  sx={{ height: 8, borderRadius: 1 }}
                />
              </Box>
              {hardwareStatus?.cpu?.temperature && (
                <Box>
                  <Box display="flex" justifyContent="space-between">
                    <Typography variant="caption">Temperature</Typography>
                    <Chip
                      label={`${safeToFixed(hardwareStatus.cpu.temperature, 1)}°C`}
                      size="small"
                      color={(hardwareStatus.cpu.temperature || 0) >= 80 ? 'error' : (hardwareStatus.cpu.temperature || 0) >= 70 ? 'warning' : 'success'}
                    />
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <MemoryIcon sx={{ mr: 1, color: 'warning.main' }} />
                <Typography variant="h6">Memory</Typography>
              </Box>
              <Typography variant="body2" color="text.secondary" mb={2}>
                System RAM
              </Typography>
              <Box mb={2}>
                <Box display="flex" justifyContent="space-between" mb={0.5}>
                  <Typography variant="caption">Usage</Typography>
                  <Typography variant="caption">
                    {formatGB(hardwareStatus?.memory?.used || 0)} GB / {formatGB(hardwareStatus?.memory?.total || 0)} GB
                  </Typography>
                </Box>
                <LinearProgress
                  variant="determinate"
                  value={hardwareStatus?.memory?.percentage || 0}
                  sx={{ height: 8, borderRadius: 1 }}
                />
                <Typography variant="caption" color="text.secondary">
                  {safeToFixed(hardwareStatus?.memory?.percentage, 1)}% used
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>


      {/* Historical Charts */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
              <Typography variant="h6">Historical Metrics</Typography>
              <Box display="flex" gap={2}>
                <ToggleButtonGroup
                  value={selectedMetric}
                  exclusive
                  onChange={(e, value) => value && setSelectedMetric(value)}
                  size="small"
                >
                  {hardwareStatus?.gpu && (
                    <>
                      <ToggleButton value="gpu_utilization">GPU Utilization</ToggleButton>
                      <ToggleButton value="gpu_temperature">GPU Temp</ToggleButton>
                      <ToggleButton value="gpu_memory">GPU Memory</ToggleButton>
                    </>
                  )}
                  <ToggleButton value="cpu_usage">CPU Usage</ToggleButton>
                  <ToggleButton value="memory_usage">Memory</ToggleButton>
                </ToggleButtonGroup>

                <ToggleButtonGroup
                  value={timeRange}
                  exclusive
                  onChange={(e, value) => value && setTimeRange(value)}
                  size="small"
                >
                  <ToggleButton value="1hour">1H</ToggleButton>
                  <ToggleButton value="6hours">6H</ToggleButton>
                  <ToggleButton value="12hours">12H</ToggleButton>
                  <ToggleButton value="24hours">24H</ToggleButton>
                </ToggleButtonGroup>
              </Box>
            </Box>

            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={getChartData()}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8884d8" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="timestamp" />
                <YAxis />
                <RechartsTooltip />
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#8884d8"
                  fillOpacity={1}
                  fill="url(#colorValue)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* Service Allocation Table (using new component) */}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <ServiceResourceAllocation
            services={services}
            onRefresh={fetchServices}
            onServiceAction={handleServiceAction}
            loading={refreshing}
          />
        </Grid>
      </Grid>

      {/* GPU Optimization Dialog */}
      <Dialog open={optimizeDialogOpen} onClose={() => setOptimizeDialogOpen(false)}>
        <DialogTitle>GPU Optimization</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            This will optimize GPU memory allocation and clear GPU cache.
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            Services using the GPU may experience brief interruptions during this operation.
          </Alert>
          {hardwareStatus?.gpu && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary">Current GPU Status:</Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="body2">
                  Memory: {safeToFixed((hardwareStatus.gpu.memory_used || 0) / 1024, 1)} GB / {safeToFixed((hardwareStatus.gpu.memory_total || 0) / 1024, 1)} GB
                </Typography>
                <Typography variant="body2">
                  Utilization: {safeToFixed(hardwareStatus.gpu.utilization, 1)}%
                </Typography>
                <Typography variant="body2">
                  Temperature: {safeToFixed(hardwareStatus.gpu.temperature, 1)}°C
                </Typography>
              </Box>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOptimizeDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleOptimizeGPU} variant="contained" color="primary">
            Optimize Now
          </Button>
        </DialogActions>
      </Dialog>

      {/* Notification Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false})}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default HardwareManagement;
