import React from 'react';
import { Tooltip, IconButton, Typography } from '@mui/material';
import { CloudQueue as ProxiedIcon, CloudOff as DNSOnlyIcon } from '@mui/icons-material';

/**
 * ProxyToggle - Display and toggle proxy status (Orange/Grey cloud)
 *
 * Props:
 * - record: DNS record object
 * - onToggle: Function to toggle proxy
 */
const ProxyToggle = ({ record, onToggle }) => {
  // Only A, AAAA, CNAME can be proxied
  const canProxy = ['A', 'AAAA', 'CNAME'].includes(record.type);

  if (!canProxy) {
    return <Typography variant="caption" color="text.secondary">-</Typography>;
  }

  return (
    <Tooltip title={record.proxied ? 'Proxied (Orange Cloud)' : 'DNS Only (Grey Cloud)'}>
      <IconButton
        size="small"
        onClick={() => onToggle(record)}
        sx={{ color: record.proxied ? 'warning.main' : 'action.disabled' }}
      >
        {record.proxied ? <ProxiedIcon /> : <DNSOnlyIcon />}
      </IconButton>
    </Tooltip>
  );
};

export default ProxyToggle;
