import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import {
  Storage as StorageIcon,
  Refresh as RefreshIcon,
  DeleteOutline as DeleteIcon,
  FolderOpen as FolderIcon,
  CleaningServices as CleanIcon
} from '@mui/icons-material';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip as RechartsTooltip } from 'recharts';

const StorageBreakdown = ({ diskData, onRefresh, onCleanup, loading }) => {
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);
  const [breakdown, setBreakdown] = useState([]);

  // Calculate storage breakdown
  useEffect(() => {
    if (diskData) {
      const used_gb = diskData.used / (1024 ** 3);
      const free_gb = diskData.free / (1024 ** 3);

      // Estimate breakdown (would be fetched from backend in real implementation)
      const docker_volumes = used_gb * 0.4;
      const databases = used_gb * 0.25;
      const logs = used_gb * 0.15;
      const system = used_gb * 0.15;
      const other = used_gb * 0.05;

      setBreakdown([
        { name: 'Docker Volumes', value: docker_volumes, color: '#8884d8' },
        { name: 'Databases', value: databases, color: '#82ca9d' },
        { name: 'Log Files', value: logs, color: '#ffc658' },
        { name: 'System Files', value: system, color: '#ff8042' },
        { name: 'Other', value: other, color: '#a4de6c' },
        { name: 'Free Space', value: free_gb, color: '#e0e0e0' }
      ]);
    }
  }, [diskData]);

  if (!diskData) {
    return (
      <Card>
        <CardContent>
          <Typography color="text.secondary">Loading storage data...</Typography>
        </CardContent>
      </Card>
    );
  }

  const used_gb = diskData.used / (1024 ** 3);
  const total_gb = diskData.total / (1024 ** 3);
  const free_gb = diskData.free / (1024 ** 3);
  const usage_percent = diskData.percentage;

  const formatBytes = (bytes) => {
    return (bytes / (1024 ** 3)).toFixed(2) + ' GB';
  };

  const handleCleanup = async () => {
    setCleanupDialogOpen(false);
    if (onCleanup) {
      await onCleanup();
    }
  };

  return (
    <>
      <Card sx={{ height: '100%' }}>
        <CardContent>
          {/* Header */}
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Box display="flex" alignItems="center" gap={1}>
              <StorageIcon sx={{ color: 'success.main', fontSize: 32 }} />
              <Typography variant="h6" fontWeight="bold">Storage Breakdown</Typography>
            </Box>
            <Tooltip title="Refresh storage data">
              <IconButton onClick={onRefresh} disabled={loading} size="small">
                <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Alert */}
          {usage_percent >= 85 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Disk usage is high ({usage_percent.toFixed(1)}%). Consider cleanup.
            </Alert>
          )}

          {/* Overall Usage */}
          <Box mb={3}>
            <Box display="flex" justifyContent="space-between" mb={0.5}>
              <Typography variant="caption" fontWeight="medium">Total Usage</Typography>
              <Typography variant="caption" color="text.secondary">
                {used_gb.toFixed(1)} GB / {total_gb.toFixed(1)} GB
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={usage_percent}
              color={usage_percent >= 90 ? 'error' : usage_percent >= 75 ? 'warning' : 'success'}
              sx={{ height: 8, borderRadius: 1 }}
            />
            <Box display="flex" justifyContent="space-between" mt={0.5}>
              <Typography variant="caption" color="text.secondary">
                {usage_percent.toFixed(1)}% used
              </Typography>
              <Typography variant="caption" color="success.main">
                {free_gb.toFixed(1)} GB free
              </Typography>
            </Box>
          </Box>

          {/* Pie Chart */}
          <Box sx={{ height: 200, mb: 2 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={breakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip formatter={(value) => `${value.toFixed(2)} GB`} />
              </PieChart>
            </ResponsiveContainer>
          </Box>

          {/* Breakdown List */}
          <List dense>
            {breakdown.slice(0, -1).map((item, idx) => (
              <ListItem key={idx} sx={{ px: 0 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: item.color,
                    mr: 1.5
                  }}
                />
                <ListItemText
                  primary={item.name}
                  secondary={`${item.value.toFixed(2)} GB`}
                  primaryTypographyProps={{ variant: 'caption' }}
                  secondaryTypographyProps={{ variant: 'caption' }}
                />
              </ListItem>
            ))}
          </List>

          {/* Cleanup Button */}
          <Button
            fullWidth
            variant="outlined"
            size="small"
            color="warning"
            startIcon={<CleanIcon />}
            onClick={() => setCleanupDialogOpen(true)}
            sx={{ mt: 2 }}
          >
            Clean Up Storage
          </Button>
        </CardContent>
      </Card>

      {/* Cleanup Dialog */}
      <Dialog open={cleanupDialogOpen} onClose={() => setCleanupDialogOpen(false)}>
        <DialogTitle>Storage Cleanup</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            This will perform the following cleanup operations:
          </Typography>
          <List dense>
            <ListItem>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              <ListItemText primary="Remove old Docker logs (>7 days)" />
            </ListItem>
            <ListItem>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              <ListItemText primary="Clean Docker build cache" />
            </ListItem>
            <ListItem>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              <ListItemText primary="Remove unused Docker images" />
            </ListItem>
            <ListItem>
              <DeleteIcon fontSize="small" sx={{ mr: 1 }} />
              <ListItemText primary="Clear temporary files" />
            </ListItem>
          </List>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This operation may take several minutes. Services will not be interrupted.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCleanupDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleCleanup} variant="contained" color="warning">
            Start Cleanup
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default StorageBreakdown;
