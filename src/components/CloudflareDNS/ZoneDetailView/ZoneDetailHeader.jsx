import React from 'react';
import { Box, Typography, Button, Chip } from '@mui/material';
import { Cloud as CloudIcon, Refresh as RefreshIcon, Delete as DeleteIcon } from '@mui/icons-material';
import StatusBadge from '../Shared/StatusBadge';

const ZoneDetailHeader = ({ zone, onBack, onCheckStatus, onDeleteZone }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
      <Box>
        <Button
          variant="text"
          onClick={onBack}
          sx={{ mb: 1 }}
        >
          ← Back to Zones
        </Button>
        <Typography variant="h4" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
          <CloudIcon />
          {zone.domain}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
          <StatusBadge status={zone.status} />
          <Chip label={zone.plan?.toUpperCase() || 'FREE'} size="small" />
        </Box>
      </Box>

      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => onCheckStatus(zone.zone_id)}
        >
          Check Status
        </Button>
        <Button
          variant="outlined"
          color="error"
          startIcon={<DeleteIcon />}
          onClick={onDeleteZone}
        >
          Delete Zone
        </Button>
      </Box>
    </Box>
  );
};

export default ZoneDetailHeader;
