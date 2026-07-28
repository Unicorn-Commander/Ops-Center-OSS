import React from 'react';
import { Card, CardContent, Typography, Box, Chip, IconButton, Tooltip } from '@mui/material';
import { Edit, Delete, PlayArrow, CheckCircle, Error } from '@mui/icons-material';

export default function ProviderCard({ provider, onEdit, onDelete, onTest }) {
  const getStatusColor = (status) => status === 'active' ? 'success' : 'error';

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
          <Box>
            <Typography variant="h6">{provider.name}</Typography>
            <Typography variant="body2" color="text.secondary">{provider.type}</Typography>
          </Box>
          <Chip label={provider.status} color={getStatusColor(provider.status)} size="small" />
        </Box>
        <Typography variant="body2" color="text.secondary">
          Models: {provider.models?.length || 0}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Usage: {provider.usage_count.toLocaleString()} requests
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 2 }}>
          <Tooltip title="Test Connection"><IconButton size="small" onClick={() => onTest(provider)}><PlayArrow /></IconButton></Tooltip>
          <Tooltip title="Edit"><IconButton size="small" onClick={() => onEdit(provider)}><Edit /></IconButton></Tooltip>
          <Tooltip title="Delete"><IconButton size="small" onClick={() => onDelete(provider)} color="error"><Delete /></IconButton></Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
}
