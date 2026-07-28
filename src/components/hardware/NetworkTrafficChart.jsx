import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  IconButton,
  Tooltip,
  ToggleButtonGroup,
  ToggleButton,
  Chip
} from '@mui/material';
import {
  NetworkCheck as NetworkIcon,
  Refresh as RefreshIcon,
  TrendingUp as UploadIcon,
  TrendingDown as DownloadIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';

const NetworkTrafficChart = ({ networkData, onRefresh, loading }) => {
  const [timeRange, setTimeRange] = useState('1hour');
  const [chartData, setChartData] = useState([]);

  // Generate mock historical data (would come from backend in real implementation)
  useEffect(() => {
    const generateData = () => {
      const points = timeRange === '1hour' ? 60 : timeRange === '6hours' ? 72 : 144;
      const data = [];
      const now = Date.now();

      for (let i = points - 1; i >= 0; i--) {
        const timestamp = new Date(now - i * 60000); // 1 minute intervals
        data.push({
          time: timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          upload: Math.random() * 100 + 20, // MB/s
          download: Math.random() * 150 + 30 // MB/s
        });
      }

      return data;
    };

    setChartData(generateData());
  }, [timeRange]);

  // Calculate current rates from networkData
  const currentUpload = networkData?.upload_rate || 0;
  const currentDownload = networkData?.download_rate || 0;

  const formatBandwidth = (mbps) => {
    if (mbps >= 1000) {
      return `${(mbps / 1000).toFixed(2)} GB/s`;
    }
    return `${mbps.toFixed(2)} MB/s`;
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        {/* Header */}
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <NetworkIcon sx={{ color: 'info.main', fontSize: 32 }} />
            <Typography variant="h6" fontWeight="bold">Network Traffic</Typography>
          </Box>
          <Box display="flex" alignItems="center" gap={1}>
            <ToggleButtonGroup
              value={timeRange}
              exclusive
              onChange={(e, value) => value && setTimeRange(value)}
              size="small"
            >
              <ToggleButton value="1hour">1H</ToggleButton>
              <ToggleButton value="6hours">6H</ToggleButton>
              <ToggleButton value="24hours">24H</ToggleButton>
            </ToggleButtonGroup>
            <Tooltip title="Refresh network data">
              <IconButton onClick={onRefresh} disabled={loading} size="small">
                <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Current Stats */}
        <Box display="flex" gap={2} mb={3}>
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
              <UploadIcon fontSize="small" sx={{ color: 'primary.main' }} />
              <Typography variant="caption" color="text.secondary">Upload</Typography>
            </Box>
            <Typography variant="h6" color="primary.main">
              {formatBandwidth(currentUpload)}
            </Typography>
          </Box>
          <Box flex={1}>
            <Box display="flex" alignItems="center" gap={0.5} mb={0.5}>
              <DownloadIcon fontSize="small" sx={{ color: 'success.main' }} />
              <Typography variant="caption" color="text.secondary">Download</Typography>
            </Box>
            <Typography variant="h6" color="success.main">
              {formatBandwidth(currentDownload)}
            </Typography>
          </Box>
        </Box>

        {/* Active Connections */}
        <Box display="flex" gap={1} mb={3}>
          <Chip
            label={`${networkData?.active_connections || 0} Active Connections`}
            size="small"
            color="default"
          />
          <Chip
            label={`${networkData?.tcp_connections || 0} TCP`}
            size="small"
            variant="outlined"
          />
          <Chip
            label={`${networkData?.udp_connections || 0} UDP`}
            size="small"
            variant="outlined"
          />
        </Box>

        {/* Chart */}
        <Box sx={{ height: 250 }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis
                tick={{ fontSize: 12 }}
                label={{ value: 'MB/s', angle: -90, position: 'insideLeft' }}
              />
              <RechartsTooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="upload"
                stroke="#1976d2"
                strokeWidth={2}
                dot={false}
                name="Upload"
              />
              <Line
                type="monotone"
                dataKey="download"
                stroke="#2e7d32"
                strokeWidth={2}
                dot={false}
                name="Download"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>

        {/* Service Endpoints Status */}
        <Box mt={3}>
          <Typography variant="caption" fontWeight="medium" gutterBottom>
            Service Endpoints
          </Typography>
          <Box display="flex" flexWrap="wrap" gap={1} mt={1}>
            {[
              { name: 'Open-WebUI', port: 8080, status: 'healthy' },
              { name: 'Brigade API', port: 8101, status: 'healthy' },
              { name: 'Ops-Center', port: 8084, status: 'healthy' },
              { name: 'PostgreSQL', port: 5432, status: 'healthy' },
              { name: 'Redis', port: 6379, status: 'healthy' }
            ].map((service) => (
              <Tooltip key={service.name} title={`Port ${service.port}`}>
                <Chip
                  label={service.name}
                  size="small"
                  color={service.status === 'healthy' ? 'success' : 'error'}
                  variant="outlined"
                />
              </Tooltip>
            ))}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default NetworkTrafficChart;
