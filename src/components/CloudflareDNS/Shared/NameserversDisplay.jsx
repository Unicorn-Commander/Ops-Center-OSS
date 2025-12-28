import React from 'react';
import { Box, Typography, Tooltip, IconButton } from '@mui/material';
import { ContentCopy as CopyIcon } from '@mui/icons-material';

/**
 * NameserversDisplay - Display nameservers with copy button
 *
 * Props:
 * - nameservers: Array of nameserver strings
 * - onCopy: Function to handle copy action
 */
const NameserversDisplay = ({ nameservers, onCopy }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
    <Box>
      {nameservers && nameservers.length > 0 ? (
        nameservers.map((ns, idx) => (
          <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
            {ns}
          </Typography>
        ))
      ) : (
        <Typography variant="body2" color="text.secondary">-</Typography>
      )}
    </Box>
    {nameservers && nameservers.length > 0 && (
      <Tooltip title="Copy nameservers">
        <IconButton size="small" onClick={() => onCopy(nameservers)}>
          <CopyIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    )}
  </Box>
);

export default NameserversDisplay;
