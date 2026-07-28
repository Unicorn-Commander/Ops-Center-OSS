/**
 * GPU Status Card Component
 * Displays GPU information including memory usage, utilization, temperature, and power draw.
 * Part of the Local Inference Module for Ops-Center.
 */

import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Tooltip,
  Grid
} from '@mui/material';
import {
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Thermostat as ThermostatIcon,
  BoltOutlined as PowerIcon
} from '@mui/icons-material';

/**
 * Get temperature color based on value
 * @param {number} temp - Temperature in Celsius
 * @returns {string} - Color code
 */
const getTemperatureColor = (temp) => {
  if (temp < 60) return '#4caf50'; // Green
  if (temp < 80) return '#ff9800'; // Yellow/Orange
  return '#f44336'; // Red
};

/**
 * Get utilization color based on percentage
 * @param {number} util - Utilization percentage
 * @returns {string} - Color code
 */
const getUtilizationColor = (util) => {
  if (util < 50) return '#4caf50'; // Green
  if (util < 80) return '#2196f3'; // Blue
  if (util < 95) return '#ff9800'; // Orange
  return '#f44336'; // Red
};

/**
 * Format bytes to human-readable format
 * @param {number} bytes - Bytes value
 * @returns {string} - Formatted string
 */
const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * Format memory in MiB to GB
 * @param {number} mib - Memory in MiB
 * @returns {string} - Formatted string in GB
 */
const formatMemoryGB = (mib) => {
  if (!mib) return '0 GB';
  const gb = mib / 1024;
  return `${gb.toFixed(1)} GB`;
};

const GPUStatusCard = ({ gpu, index }) => {
  if (!gpu) {
    return (
      <Card sx={{
        height: '100%',
        background: 'linear-gradient(135deg, rgba(100, 100, 100, 0.1) 0%, rgba(50, 50, 50, 0.1) 100%)',
        borderRadius: 2
      }}>
        <CardContent>
          <Typography color="text.secondary">No GPU data available</Typography>
        </CardContent>
      </Card>
    );
  }

  const {
    name = 'Unknown GPU',
    memory_used = 0,
    memory_total = 0,
    utilization = 0,
    temperature = 0,
    power_draw = 0,
    power_limit = 0,
    fan_speed,
    driver_version,
    cuda_version
  } = gpu;

  const memoryPercentage = memory_total > 0 ? (memory_used / memory_total) * 100 : 0;
  const powerPercentage = power_limit > 0 ? (power_draw / power_limit) * 100 : 0;
  const tempColor = getTemperatureColor(temperature);
  const utilColor = getUtilizationColor(utilization);

  return (
    <Card
      sx={{
        height: '100%',
        background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)',
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: '0 8px 24px rgba(102, 126, 234, 0.15)'
        }
      }}
    >
      <CardContent>
        {/* GPU Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
              GPU {index !== undefined ? index : ''}
            </Typography>
            <Typography variant="h6" sx={{ fontWeight: 600, fontSize: '1rem' }}>
              {name}
            </Typography>
          </Box>
          <Chip
            label={`${temperature}°C`}
            size="small"
            icon={<ThermostatIcon sx={{ fontSize: 14 }} />}
            sx={{
              backgroundColor: `${tempColor}20`,
              color: tempColor,
              fontWeight: 600,
              fontSize: '0.75rem',
              '& .MuiChip-icon': { color: tempColor }
            }}
          />
        </Box>

        {/* Memory Usage */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <MemoryIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Memory
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {formatMemoryGB(memory_used)} / {formatMemoryGB(memory_total)}
            </Typography>
          </Box>
          <Tooltip title={`${memoryPercentage.toFixed(1)}% used`} arrow>
            <LinearProgress
              variant="determinate"
              value={memoryPercentage}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  background: memoryPercentage > 90
                    ? 'linear-gradient(90deg, #f44336, #ff5722)'
                    : memoryPercentage > 70
                      ? 'linear-gradient(90deg, #ff9800, #ffc107)'
                      : 'linear-gradient(90deg, #667eea, #764ba2)'
                }
              }}
            />
          </Tooltip>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
            {memoryPercentage.toFixed(1)}% used
          </Typography>
        </Box>

        {/* Utilization */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <SpeedIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Utilization
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 600, color: utilColor }}>
              {utilization}%
            </Typography>
          </Box>
          <Tooltip title={`GPU Core utilization: ${utilization}%`} arrow>
            <LinearProgress
              variant="determinate"
              value={utilization}
              sx={{
                height: 8,
                borderRadius: 4,
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 4,
                  backgroundColor: utilColor
                }
              }}
            />
          </Tooltip>
        </Box>

        {/* Power Draw */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 0.5 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <PowerIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Power
              </Typography>
            </Box>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {power_draw?.toFixed(0) || 0}W / {power_limit?.toFixed(0) || 0}W
            </Typography>
          </Box>
          <Tooltip title={`Power draw: ${powerPercentage.toFixed(1)}% of limit`} arrow>
            <LinearProgress
              variant="determinate"
              value={Math.min(powerPercentage, 100)}
              sx={{
                height: 6,
                borderRadius: 3,
                backgroundColor: 'rgba(0, 0, 0, 0.1)',
                '& .MuiLinearProgress-bar': {
                  borderRadius: 3,
                  background: powerPercentage > 90
                    ? '#f44336'
                    : 'linear-gradient(90deg, #43e97b, #38f9d7)'
                }
              }}
            />
          </Tooltip>
        </Box>

        {/* Additional Info */}
        <Grid container spacing={1}>
          {fan_speed !== undefined && (
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Fan Speed
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {fan_speed}%
              </Typography>
            </Grid>
          )}
          {driver_version && (
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                Driver
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500, fontSize: '0.75rem' }}>
                {driver_version}
              </Typography>
            </Grid>
          )}
          {cuda_version && (
            <Grid item xs={6}>
              <Typography variant="caption" color="text.secondary">
                CUDA
              </Typography>
              <Typography variant="body2" sx={{ fontWeight: 500 }}>
                {cuda_version}
              </Typography>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
};

export default GPUStatusCard;
