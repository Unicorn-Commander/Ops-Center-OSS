import React from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Edit,
  Delete,
  PlayArrow,
  CheckCircle,
  Error,
  Warning
} from '@mui/icons-material';

/**
 * ModelCard Component
 *
 * Displays individual model information with status, usage, and actions
 */
export default function ModelCard({ model, onEdit, onDelete, onTest }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'inactive':
        return 'default';
      case 'error':
        return 'error';
      case 'testing':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active':
        return <CheckCircle fontSize="small" />;
      case 'error':
        return <Error fontSize="small" />;
      case 'testing':
        return <Warning fontSize="small" />;
      default:
        return null;
    }
  };

  return (
    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="div" gutterBottom>
              {model.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {model.provider}
            </Typography>
          </Box>
          <Chip
            label={model.status}
            color={getStatusColor(model.status)}
            size="small"
            icon={getStatusIcon(model.status)}
          />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Context Length: {model.context_length.toLocaleString()} tokens
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Input: ${model.cost_per_input_token.toFixed(6)}/token
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Output: ${model.cost_per_output_token.toFixed(6)}/token
          </Typography>
        </Box>

        {model.latency_avg_ms && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" gutterBottom>
              Avg Latency: {model.latency_avg_ms.toFixed(0)}ms
            </Typography>
          </Box>
        )}

        <Box sx={{ mb: 1 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Usage Count
          </Typography>
          <LinearProgress
            variant="determinate"
            value={Math.min((model.usage_count / 1000) * 100, 100)}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Typography variant="caption" color="text.secondary">
            {model.usage_count.toLocaleString()} requests
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mt: 2 }}>
          <Tooltip title="Test Model">
            <IconButton size="small" onClick={() => onTest(model)} color="primary">
              <PlayArrow />
            </IconButton>
          </Tooltip>
          <Tooltip title="Edit Model">
            <IconButton size="small" onClick={() => onEdit(model)} color="primary">
              <Edit />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete Model">
            <IconButton size="small" onClick={() => onDelete(model)} color="error">
              <Delete />
            </IconButton>
          </Tooltip>
        </Box>
      </CardContent>
    </Card>
  );
}
