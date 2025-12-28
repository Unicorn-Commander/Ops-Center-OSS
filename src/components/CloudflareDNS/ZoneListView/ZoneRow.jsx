import React from 'react';
import { TableRow, TableCell, Typography, IconButton, Tooltip } from '@mui/material';
import { Refresh as RefreshIcon, Delete as DeleteIcon } from '@mui/icons-material';
import StatusBadge from '../Shared/StatusBadge';
import NameserversDisplay from '../Shared/NameserversDisplay';

const ZoneRow = ({ zone, onSelectZone, onCheckStatus, onDeleteZone, onCopyNameservers }) => {
  return (
    <TableRow
      hover
      sx={{ cursor: 'pointer' }}
      onClick={() => onSelectZone(zone)}
    >
      <TableCell>
        <Typography variant="body1" sx={{ fontWeight: 600 }}>
          {zone.domain}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {zone.zone_id}
        </Typography>
      </TableCell>

      <TableCell>
        <StatusBadge status={zone.status} />
      </TableCell>

      <TableCell>
        <NameserversDisplay
          nameservers={zone.nameservers}
          zone={zone}
          onCopy={onCopyNameservers}
        />
      </TableCell>

      <TableCell>
        <Typography variant="body2">
          {new Date(zone.created_at).toLocaleDateString()}
        </Typography>
      </TableCell>

      <TableCell align="right" onClick={(e) => e.stopPropagation()}>
        <Tooltip title="Check Status">
          <IconButton
            size="small"
            onClick={() => onCheckStatus(zone.zone_id)}
          >
            <RefreshIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete Zone">
          <IconButton
            size="small"
            color="error"
            onClick={() => onDeleteZone(zone)}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </TableCell>
    </TableRow>
  );
};

export default ZoneRow;
