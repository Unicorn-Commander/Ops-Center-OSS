import React, { useState, useEffect } from 'react';
import {
  Box, Grid, Card, CardContent, Typography, Select, MenuItem,
  FormControl, InputLabel, CircularProgress, Alert, Button
} from '@mui/material';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
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
  Legend,
  Filler
} from 'chart.js';
import ModelUsageChart from './ModelUsageChart';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

export default function UsageMetrics() {
  const [timeRange, setTimeRange] = useState('7d'); // 24h, 7d, 30d, 90d
  const [usageData, setUsageData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadUsageData();
  }, [timeRange]);

  const loadUsageData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/credits/usage/metrics?range=${timeRange}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (!response.ok) throw new Error('Failed to load usage metrics');

      const data = await response.json();
      setUsageData(data);
    } catch (err) {
      console.error('Usage metrics load error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
        <Button onClick={loadUsageData} sx={{ ml: 2 }}>Retry</Button>
      </Alert>
    );
  }

  // Prepare chart data
  const dailyUsageData = {
    labels: usageData?.daily_trend?.labels || [],
    datasets: [
      {
        label: 'Daily Usage ($)',
        data: usageData?.daily_trend?.values || [],
        borderColor: 'rgb(139, 92, 246)',
        backgroundColor: 'rgba(139, 92, 246, 0.1)',
        fill: true,
        tension: 0.4
      }
    ]
  };

  const serviceBreakdownData = {
    labels: usageData?.by_service?.labels || [],
    datasets: [
      {
        data: usageData?.by_service?.values || [],
        backgroundColor: [
          'rgba(139, 92, 246, 0.8)',
          'rgba(168, 85, 247, 0.8)',
          'rgba(192, 132, 252, 0.8)',
          'rgba(216, 180, 254, 0.8)',
          'rgba(233, 213, 255, 0.8)'
        ],
        borderColor: [
          'rgb(139, 92, 246)',
          'rgb(168, 85, 247)',
          'rgb(192, 132, 252)',
          'rgb(216, 180, 254)',
          'rgb(233, 213, 255)'
        ],
        borderWidth: 2
      }
    ]
  };

  const freePaidData = {
    labels: ['Free Models', 'Paid Models'],
    datasets: [
      {
        label: 'Usage ($)',
        data: [
          usageData?.free_vs_paid?.free || 0,
          usageData?.free_vs_paid?.paid || 0
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)'
        ],
        borderColor: [
          'rgb(34, 197, 94)',
          'rgb(59, 130, 246)'
        ],
        borderWidth: 2
      }
    ]
  };

  const costBreakdownData = {
    labels: ['Provider Cost', 'Markup'],
    datasets: [
      {
        label: 'Amount ($)',
        data: [
          usageData?.cost_breakdown?.provider_cost || 0,
          usageData?.cost_breakdown?.markup || 0
        ],
        backgroundColor: [
          'rgba(249, 115, 22, 0.8)',
          'rgba(234, 179, 8, 0.8)'
        ],
        borderColor: [
          'rgb(249, 115, 22)',
          'rgb(234, 179, 8)'
        ],
        borderWidth: 2
      }
    ]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            let label = context.dataset.label || '';
            if (label) {
              label += ': ';
            }
            label += '$' + context.parsed.y.toFixed(4);
            return label;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            return '$' + value.toFixed(2);
          }
        }
      }
    }
  };

  const barOptions = {
    ...chartOptions,
    indexAxis: 'y'
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((value / total) * 100).toFixed(1);
            return `${label}: $${value.toFixed(2)} (${percentage}%)`;
          }
        }
      }
    }
  };

  return (
    <Box>
      {/* Time Range Selector */}
      <Box sx={{ mb: 3 }}>
        <FormControl size="small" sx={{ minWidth: 200 }}>
          <InputLabel>Time Range</InputLabel>
          <Select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            label="Time Range"
          >
            <MenuItem value="24h">Last 24 Hours</MenuItem>
            <MenuItem value="7d">Last 7 Days</MenuItem>
            <MenuItem value="30d">Last 30 Days</MenuItem>
            <MenuItem value="90d">Last 90 Days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Charts Grid */}
      <Grid container spacing={3}>
        {/* Daily Usage Trend */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Daily Usage Trend</Typography>
              <Box sx={{ height: 300 }}>
                <Line data={dailyUsageData} options={chartOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Service Breakdown */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>By Service</Typography>
              <Box sx={{ height: 300 }}>
                <Doughnut data={serviceBreakdownData} options={doughnutOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Model Usage */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Top Models by Usage</Typography>
              <ModelUsageChart data={usageData?.by_model} />
            </CardContent>
          </Card>
        </Grid>

        {/* Free vs Paid */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Free vs Paid Models</Typography>
              <Box sx={{ height: 300 }}>
                <Bar data={freePaidData} options={barOptions} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Cost Breakdown */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Cost Breakdown</Typography>
              <Box sx={{ height: 300 }}>
                <Bar data={costBreakdownData} options={barOptions} />
              </Box>
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="textSecondary">
                  Provider Cost: ${usageData?.cost_breakdown?.provider_cost?.toFixed(2) || '0.00'}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Markup: ${usageData?.cost_breakdown?.markup?.toFixed(2) || '0.00'}
                </Typography>
                <Typography variant="body2" fontWeight={600}>
                  Total: ${((usageData?.cost_breakdown?.provider_cost || 0) + (usageData?.cost_breakdown?.markup || 0)).toFixed(2)}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
