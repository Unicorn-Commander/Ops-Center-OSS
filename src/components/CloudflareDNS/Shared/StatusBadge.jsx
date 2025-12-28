import React from 'react';
import { Chip } from '@mui/material';
import {
  CheckCircle as ActiveIcon,
  Pending as PendingIcon,
  Cancel as InactiveIcon,
} from '@mui/icons-material';

/**
 * StatusBadge - Display zone status with icon and color
 *
 * Props:
 * - status: Zone status string (active, pending, deactivated, deleted)
 */
const StatusBadge = ({ status }) => {
  const statusConfig = {
    active: { color: 'success', icon: <ActiveIcon fontSize="small" />, label: 'Active' },
    pending: { color: 'warning', icon: <PendingIcon fontSize="small" />, label: 'Pending' },
    deactivated: { color: 'error', icon: <InactiveIcon fontSize="small" />, label: 'Deactivated' },
    deleted: { color: 'default', icon: <InactiveIcon fontSize="small" />, label: 'Deleted' }
  };

  const config = statusConfig[status.toLowerCase()] || statusConfig.pending;

  return (
    <Chip
      icon={config.icon}
      label={config.label}
      color={config.color}
      size="small"
      sx={{ fontWeight: 600 }}
    />
  );
};

export default StatusBadge;
