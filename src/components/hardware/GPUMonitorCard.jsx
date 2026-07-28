import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button
} from '@mui/material';
import {
  Speed as SpeedIcon,
  Refresh as RefreshIcon,
  Warning as WarningIcon,
  TrendingUp as TrendingUpIcon,
  PowerSettingsNew as PowerIcon,
  Memory as MemoryIcon
} from '@mui/icons-material';

const GPUMonitorCard = ({ gpuData, onRefresh, loading }) => {
  const [detailsOpen, setDetailsOpen] = useState(false);

  if (!gpuData) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="center" minHeight="300px">
            <Typography color="text.secondary">No GPU detected</Typography>
          </Box>
        </CardContent>
      </Card>
    );
  }

  const getTempColor = (temp) => {
    if (temp < 70) return 'success';
    if (temp < 80) return 'warning';
    return 'error';
  };

  const getUtilizationColor = (util) => {
    if (util < 50) return 'success';
    if (util < 80) return 'info';
    return 'warning';
  };

  const alerts = [];
  if (gpuData?.temperature != null && gpuData.temperature >= 80) {
    alerts.push({ severity: 'error', message: `High temperature: ${gpuData.temperature.toFixed(1)}°C` });
  }
  if (gpuData?.memory_percent != null && gpuData.memory_percent >= 90) {
    alerts.push({ severity: 'warning', message: `High memory usage: ${gpuData.memory_percent.toFixed(1)}%` });
  }
  if (gpuData?.utilization != null && gpuData.utilization >= 95) {
    alerts.push({ severity: 'info', message: `High utilization: ${gpuData.utilization.toFixed(1)}%` });
  }

  return (
    <>
      <Card sx={{ height: '100%' }}>
        <CardContent>
          {/* Header */}
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <SpeedIcon sx={{ color: 'primary.main', fontSize: 32 }} />
              <Typography variant="h6" fontWeight="bold">GPU Monitor</Typography>
            </Box>
            <Tooltip title="Refresh GPU data">
              <IconButton onClick={onRefresh} disabled={loading} size="small">
                <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              </IconButton>
            </Tooltip>
          </Box>

          {/* GPU Model */}
          <Typography variant="body2" color="text.secondary" mb={2} fontWeight="medium">
            {gpuData.model || 'Unknown GPU'}
          </Typography>

          {/* Alerts */}
          {alerts.length > 0 && (
            <Box mb={2}>
              {alerts.map((alert, idx) => (
                <Alert
                  key={idx}
                  severity={alert.severity}
                  icon={<WarningIcon />}
                  sx={{ mb: 1, py: 0.5 }}
                >
                  <Typography variant="caption">{alert.message}</Typography>
                </Alert>
              ))}
            </Box>
          )}

          {/* Temperature */}
          <Box mb={2.5}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
              <Typography variant="caption" fontWeight="medium">Temperature</Typography>
              <Chip
                label={`${(gpuData.temperature || 0).toFixed(1)}°C`}
                size="small"
                color={getTempColor(gpuData.temperature || 0)}
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={((gpuData.temperature || 0) / 100) * 100}
              sx={{
                height: 8,
                borderRadius: 1,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: (gpuData.temperature || 0) >= 80 ? 'error.main' :
                                  (gpuData.temperature || 0) >= 70 ? 'warning.main' : 'success.main'
                }
              }}
            />
          </Box>

          {/* Memory Usage */}
          <Box mb={2.5}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
              <Typography variant="caption" fontWeight="medium">Memory</Typography>
              <Typography variant="caption" color="text.secondary">
                {((gpuData.memory_used || 0) / 1024).toFixed(1)} GB / {((gpuData.memory_total || 0) / 1024).toFixed(1)} GB
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={gpuData.memory_percent || 0}
              color={(gpuData.memory_percent || 0) >= 90 ? 'error' : (gpuData.memory_percent || 0) >= 75 ? 'warning' : 'primary'}
              sx={{ height: 8, borderRadius: 1 }}
            />
            <Typography variant="caption" color="text.secondary">
              {(gpuData.memory_percent || 0).toFixed(1)}% used
            </Typography>
          </Box>

          {/* Utilization */}
          <Box mb={2.5}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
              <Typography variant="caption" fontWeight="medium">Utilization</Typography>
              <Chip
                label={`${(gpuData.utilization || 0).toFixed(1)}%`}
                size="small"
                color={getUtilizationColor(gpuData.utilization || 0)}
              />
            </Box>
            <LinearProgress
              variant="determinate"
              value={gpuData.utilization || 0}
              color={getUtilizationColor(gpuData.utilization || 0)}
              sx={{ height: 8, borderRadius: 1 }}
            />
          </Box>

          {/* Power Draw */}
          <Box mb={2}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box display="flex" alignItems="center" gap={0.5}>
                <PowerIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                <Typography variant="caption" fontWeight="medium">Power</Typography>
              </Box>
              <Typography variant="caption" color="text.secondary">
                {(gpuData.power_draw || 0).toFixed(1)} W / {(gpuData.power_limit || 0).toFixed(0)} W
              </Typography>
            </Box>
          </Box>

          {/* Details Button */}
          <Button
            fullWidth
            variant="outlined"
            size="small"
            onClick={() => setDetailsOpen(true)}
            startIcon={<TrendingUpIcon />}
          >
            View Details
          </Button>
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <Dialog open={detailsOpen} onClose={() => setDetailsOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>GPU Details</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'grid', gap: 2 }}>
            <Box>
              <Typography variant="caption" color="text.secondary">Model</Typography>
              <Typography variant="body2" fontWeight="medium">{gpuData.model || 'Unknown'}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Driver Version</Typography>
              <Typography variant="body2" fontWeight="medium">{gpuData.driver_version || 'N/A'}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Compute Capability</Typography>
              <Typography variant="body2" fontWeight="medium">{gpuData.compute_capability || 'N/A'}</Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Total Memory</Typography>
              <Typography variant="body2" fontWeight="medium">
                {((gpuData.memory_total || 0) / 1024).toFixed(2)} GB
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Free Memory</Typography>
              <Typography variant="body2" fontWeight="medium">
                {((gpuData.memory_free || 0) / 1024).toFixed(2)} GB
              </Typography>
            </Box>
            <Box>
              <Typography variant="caption" color="text.secondary">Power Limit</Typography>
              <Typography variant="body2" fontWeight="medium">
                {(gpuData.power_limit || 0).toFixed(0)} W
              </Typography>
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDetailsOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default GPUMonitorCard;
