import React from 'react';
import { Chip, Tooltip } from '@mui/material';
import CloudOutlinedIcon from '@mui/icons-material/CloudOutlined';
import StorageOutlinedIcon from '@mui/icons-material/StorageOutlined';

/**
 * ProvenanceBadge — a small "served by X" chip for billing / metering / analytics
 * surfaces. Makes it transparent WHICH pluggable service backs the data on this
 * deployment: local (this server) vs. a federated central hub.
 */
export default function ProvenanceBadge({ config, prefix = 'Billing', sx }) {
  if (!config) return null;
  const remote = config?.source?.kind === 'remote';
  const label = config?.source?.label || config?.display_name || 'this server';
  const tip = remote
    ? `${prefix} is provided by ${label} (federated). This console shows a live view; purchases & cards live at the hub.`
    : `${prefix} runs on this server (${label}).`;

  return (
    <Tooltip title={tip} arrow placement="bottom-start">
      <Chip
        size="small"
        variant="outlined"
        icon={remote ? <CloudOutlinedIcon sx={{ fontSize: 15 }} /> : <StorageOutlinedIcon sx={{ fontSize: 15 }} />}
        label={`${prefix} · ${label}`}
        sx={{
          height: 24,
          fontSize: 11.5,
          fontWeight: 500,
          letterSpacing: 0.2,
          color: 'text.secondary',
          borderColor: 'rgba(160,170,210,0.22)',
          background: 'rgba(160,170,210,0.05)',
          '& .MuiChip-icon': { color: remote ? '#67e8f9' : '#a78bfa', ml: 0.75 },
          ...sx,
        }}
      />
    </Tooltip>
  );
}
