import React, { useState } from 'react';
import { Box, Typography, FormControl, Select, MenuItem, InputLabel, Tooltip, Grid } from '@mui/material';
import { Bar } from 'react-chartjs-2';

export default function ModelUsageChart({ data }) {
  const [sortBy, setSortBy] = useState('cost'); // cost, tokens, requests

  if (!data || data.length === 0) {
    return (
      <Box sx={{ p: 4, textAlign: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          No model usage data available
        </Typography>
      </Box>
    );
  }

  // Sort data based on selected metric
  const sortedData = [...data].sort((a, b) => {
    switch (sortBy) {
      case 'cost':
        return b.cost - a.cost;
      case 'tokens':
        return b.total_tokens - a.total_tokens;
      case 'requests':
        return b.request_count - a.request_count;
      default:
        return 0;
    }
  }).slice(0, 10); // Top 10 models

  // Prepare chart data
  const chartData = {
    labels: sortedData.map(item => item.model_name),
    datasets: [
      {
        label: sortBy === 'cost' ? 'Cost ($)' : sortBy === 'tokens' ? 'Tokens' : 'Requests',
        data: sortedData.map(item => {
          switch (sortBy) {
            case 'cost':
              return item.cost;
            case 'tokens':
              return item.total_tokens;
            case 'requests':
              return item.request_count;
            default:
              return 0;
          }
        }),
        backgroundColor: sortedData.map(item =>
          item.is_free ? 'rgba(34, 197, 94, 0.8)' : 'rgba(59, 130, 246, 0.8)'
        ),
        borderColor: sortedData.map(item =>
          item.is_free ? 'rgb(34, 197, 94)' : 'rgb(59, 130, 246)'
        ),
        borderWidth: 2
      }
    ]
  };

  const chartOptions = {
    indexAxis: 'y',
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          title: function(context) {
            return context[0].label;
          },
          label: function(context) {
            const index = context.dataIndex;
            const item = sortedData[index];
            return [
              `Cost: $${item.cost.toFixed(4)}`,
              `Tokens: ${item.total_tokens.toLocaleString()}`,
              `Requests: ${item.request_count.toLocaleString()}`,
              `Type: ${item.is_free ? 'Free' : 'Paid'}`
            ];
          }
        }
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: {
          callback: function(value) {
            if (sortBy === 'cost') {
              return '$' + value.toFixed(2);
            } else if (sortBy === 'tokens') {
              return (value / 1000).toFixed(0) + 'K';
            } else {
              return value;
            }
          }
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const index = elements[0].index;
        const modelName = sortedData[index].model_name;
        // Filter transactions by this model
        window.location.href = `/admin/billing/credits?model=${encodeURIComponent(modelName)}`;
      }
    }
  };

  return (
    <Box>
      {/* Sort Controls */}
      <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="textSecondary">
          Click on a bar to view transactions for that model
        </Typography>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Sort By</InputLabel>
          <Select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            label="Sort By"
          >
            <MenuItem value="cost">Cost</MenuItem>
            <MenuItem value="tokens">Tokens</MenuItem>
            <MenuItem value="requests">Requests</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Chart */}
      <Box sx={{ height: 400 }}>
        <Bar data={chartData} options={chartOptions} />
      </Box>

      {/* Legend */}
      <Box sx={{ mt: 2, display: 'flex', gap: 3, justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 16, height: 16, bgcolor: 'rgba(34, 197, 94, 0.8)', borderRadius: 1 }} />
          <Typography variant="body2">Free Models</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Box sx={{ width: 16, height: 16, bgcolor: 'rgba(59, 130, 246, 0.8)', borderRadius: 1 }} />
          <Typography variant="body2">Paid Models</Typography>
        </Box>
      </Box>

      {/* Summary Stats */}
      <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
        <Grid container spacing={2}>
          <Grid item xs={4}>
            <Typography variant="body2" color="textSecondary">Total Cost</Typography>
            <Typography variant="h6">
              ${sortedData.reduce((sum, item) => sum + item.cost, 0).toFixed(2)}
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2" color="textSecondary">Total Tokens</Typography>
            <Typography variant="h6">
              {(sortedData.reduce((sum, item) => sum + item.total_tokens, 0) / 1000000).toFixed(2)}M
            </Typography>
          </Grid>
          <Grid item xs={4}>
            <Typography variant="body2" color="textSecondary">Total Requests</Typography>
            <Typography variant="h6">
              {sortedData.reduce((sum, item) => sum + item.request_count, 0).toLocaleString()}
            </Typography>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}
