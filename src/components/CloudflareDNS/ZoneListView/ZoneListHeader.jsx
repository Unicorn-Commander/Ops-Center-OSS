import React from 'react';
import { Box, Card, CardContent, Typography } from '@mui/material';
import { Cloud as CloudIcon } from '@mui/icons-material';

const ZoneListHeader = ({ currentTheme }) => {
  return (
    <Card
      sx={{
        mb: 3,
        background: currentTheme === 'unicorn'
          ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
          : 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)',
        color: 'white'
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <CloudIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                Cloudflare DNS Management
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
                Manage domains and DNS records
              </Typography>
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ZoneListHeader;
