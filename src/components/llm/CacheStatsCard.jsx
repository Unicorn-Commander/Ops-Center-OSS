import React from 'react';
import { Card, CardContent, Typography, Box, LinearProgress, Button } from '@mui/material';
import { Refresh } from '@mui/icons-material';

export default function CacheStatsCard({ stats, onClear }) {
  const hitRate = ((stats?.hit_rate || 0) * 100).toFixed(1);
  const usagePercent = ((stats?.size_mb || 0) / (stats?.max_size_mb || 100)) * 100;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="h6">Cache Statistics</Typography>
          <Button size="small" startIcon={<Refresh />} onClick={onClear}>Clear Cache</Button>
        </Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">Hit Rate</Typography>
          <Typography variant="h4" color="primary">{hitRate}%</Typography>
          <LinearProgress variant="determinate" value={parseFloat(hitRate)} sx={{ mt: 1 }} />
        </Box>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">Cache Size</Typography>
          <Typography variant="body1">{stats?.size_mb?.toFixed(1) || 0} MB / {stats?.max_size_mb || 100} MB</Typography>
          <LinearProgress variant="determinate" value={usagePercent} sx={{ mt: 1 }} />
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2">Hits: {stats?.cache_hits?.toLocaleString() || 0}</Typography>
          <Typography variant="body2">Misses: {stats?.cache_misses?.toLocaleString() || 0}</Typography>
        </Box>
      </CardContent>
    </Card>
  );
}
