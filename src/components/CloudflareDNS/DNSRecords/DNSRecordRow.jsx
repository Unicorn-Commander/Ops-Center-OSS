import React from 'react';
import { TableRow, TableCell, Chip, Typography, Tooltip, IconButton } from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import ProxyToggle from './ProxyToggle';

/**
 * DNSRecordRow - Individual DNS record row in table
 *
 * Props:
 * - record: DNS record object
 * - onEdit: Function - edit record handler
 * - onDelete: Function - delete record handler
 * - onToggleProxy: Function - toggle proxy handler
 */
const DNSRecordRow = ({ record, onEdit, onDelete, onToggleProxy }) => {
  return (
    <TableRow hover>
      <TableCell>
        <Chip
          label={record.type}
          color="primary"
          size="small"
          sx={{ fontWeight: 600 }}
        />
      </TableCell>
      <TableCell>
        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
          {record.name}
        </Typography>
      </TableCell>
      <TableCell>
        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
          {record.content}
        </Typography>
        {record.priority !== undefined && (
          <Typography variant="caption" color="text.secondary">
            Priority: {record.priority}
          </Typography>
        )}
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {record.ttl === 1 ? 'Auto' : `${record.ttl}s`}
        </Typography>
      </TableCell>
      <TableCell>
        <ProxyToggle record={record} onToggle={onToggleProxy} />
      </TableCell>
      <TableCell align="right">
        <Tooltip title="Edit Record">
          <IconButton
            size="small"
            onClick={() => onEdit(record)}
          >
            <EditIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Delete Record">
          <IconButton
            size="small"
            color="error"
            onClick={() => onDelete(record)}
          >
            <DeleteIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </TableCell>
    </TableRow>
  );
};

export default DNSRecordRow;
