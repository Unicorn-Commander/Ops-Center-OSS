import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  Button,
  Menu,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import {
  MoreVert as MoreIcon,
  Refresh as RefreshIcon,
  Computer as ComputerIcon,
  Memory as GPUIcon,
  RestartAlt as RestartIcon,
  Stop as StopIcon,
  PlayArrow as StartIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';

const ServiceResourceAllocation = ({ services, onRefresh, onServiceAction, loading }) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [actionDialogOpen, setActionDialogOpen] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);

  const handleMenuOpen = (event, service) => {
    setAnchorEl(event.currentTarget);
    setSelectedService(service);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setSelectedService(null);
  };

  const handleAction = (action) => {
    setPendingAction(action);
    setActionDialogOpen(true);
    handleMenuClose();
  };

  const confirmAction = async () => {
    if (selectedService && pendingAction && onServiceAction) {
      await onServiceAction(selectedService.service_name, pendingAction);
    }
    setActionDialogOpen(false);
    setPendingAction(null);
  };

  const getStatusColor = (status) => {
    if (status === 'running') return 'success';
    if (status === 'stopped') return 'error';
    return 'default';
  };

  const getHardwareIcon = (type) => {
    return type === 'gpu' ? <GPUIcon fontSize="small" /> : <ComputerIcon fontSize="small" />;
  };

  const getUsageColor = (usage) => {
    if (usage < 50) return 'success';
    if (usage < 80) return 'warning';
    return 'error';
  };

  if (!services || services.length === 0) {
    return (
      <Card>
        <CardContent>
          <Typography color="text.secondary">No service data available</Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card>
        <CardContent>
          {/* Header */}
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6" fontWeight="bold">Service Hardware Allocation</Typography>
            <Tooltip title="Refresh service data">
              <IconButton onClick={onRefresh} disabled={loading} size="small">
                <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              </IconButton>
            </Tooltip>
          </Box>

          {/* Table */}
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Service</TableCell>
                  <TableCell align="center">Hardware</TableCell>
                  <TableCell align="center">Status</TableCell>
                  <TableCell>Resource Usage</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {services.map((service, index) => (
                  <TableRow key={service.service_name || service.name || index} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="medium">
                        {service.service_name || service.name || service.display_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {service.usage_level || 'normal'} priority
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        icon={getHardwareIcon(service.hardware_type || 'cpu')}
                        label={(service.hardware_type || 'cpu').toUpperCase()}
                        size="small"
                        color={service.hardware_type === 'gpu' ? 'primary' : 'default'}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={service.status}
                        size="small"
                        color={getStatusColor(service.status)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <LinearProgress
                          variant="determinate"
                          value={service.resource_usage || service.cpu_percent || 0}
                          color={getUsageColor(service.resource_usage || service.cpu_percent || 0)}
                          sx={{ width: 100, height: 6, borderRadius: 1 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {(service.resource_usage || service.cpu_percent || 0).toFixed(1)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, service)}
                      >
                        <MoreIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {/* Summary */}
          <Box mt={3} p={2} sx={{ backgroundColor: 'grey.50', borderRadius: 1 }}>
            <Typography variant="caption" fontWeight="medium" gutterBottom>
              Summary
            </Typography>
            <Box display="flex" gap={3} mt={1}>
              <Box>
                <Typography variant="caption" color="text.secondary">Total Services</Typography>
                <Typography variant="h6">{services.length}</Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Running</Typography>
                <Typography variant="h6" color="success.main">
                  {services.filter(s => s.status === 'running').length}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">GPU Services</Typography>
                <Typography variant="h6" color="primary.main">
                  {services.filter(s => s.hardware_type === 'gpu' || s.gpu_enabled).length}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">Avg CPU Usage</Typography>
                <Typography variant="h6">
                  {services.length > 0 ? (services.reduce((sum, s) => sum + (s.resource_usage || s.cpu_percent || 0), 0) / services.length).toFixed(1) : 0}%
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Action Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        {selectedService?.status === 'running' ? (
          [
            <MenuItem key="restart" onClick={() => handleAction('restart')}>
              <RestartIcon fontSize="small" sx={{ mr: 1 }} />
              Restart Service
            </MenuItem>,
            <MenuItem key="stop" onClick={() => handleAction('stop')}>
              <StopIcon fontSize="small" sx={{ mr: 1 }} />
              Stop Service
            </MenuItem>
          ]
        ) : (
          <MenuItem onClick={() => handleAction('start')}>
            <StartIcon fontSize="small" sx={{ mr: 1 }} />
            Start Service
          </MenuItem>
        )}
        <MenuItem onClick={handleMenuClose}>
          <SettingsIcon fontSize="small" sx={{ mr: 1 }} />
          Configure
        </MenuItem>
      </Menu>

      {/* Action Confirmation Dialog */}
      <Dialog open={actionDialogOpen} onClose={() => setActionDialogOpen(false)}>
        <DialogTitle>Confirm Action</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            You are about to {pendingAction} the service: <strong>{selectedService?.service_name}</strong>
          </Alert>
          <Typography variant="body2">
            {pendingAction === 'restart' && 'The service will be restarted. This may cause brief downtime.'}
            {pendingAction === 'stop' && 'The service will be stopped. Dependent services may be affected.'}
            {pendingAction === 'start' && 'The service will be started. This may take a few moments.'}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setActionDialogOpen(false)}>Cancel</Button>
          <Button onClick={confirmAction} variant="contained" color="primary">
            Confirm
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default ServiceResourceAllocation;
