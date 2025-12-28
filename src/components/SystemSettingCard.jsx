import React, { useState } from 'react';
import {
  TableCell,
  TableRow,
  IconButton,
  Tooltip,
  Chip,
  Typography,
  Box,
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Cable as CableIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';

const SystemSettingCard = ({ setting, onEdit, onDelete, onTest }) => {
  const [showValue, setShowValue] = useState(false);

  const isSensitive = setting.sensitive || setting.is_sensitive;
  const categoryColors = {
    security: 'error',
    billing: 'success',
    llm: 'primary',
    email: 'info',
    storage: 'warning',
  };

  // Mask sensitive values (show last 8 characters)
  const getMaskedValue = (value) => {
    if (!isSensitive) return value;
    if (!showValue) {
      if (value.length <= 8) {
        return '••••••••';
      }
      return '••••••••' + value.slice(-8);
    }
    return value;
  };

  const handleCopyToClipboard = () => {
    navigator.clipboard.writeText(setting.value);
    // Could show a toast notification here
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Determine if this setting can be tested (API keys, URLs, etc.)
  const canTest = ['llm', 'email', 'billing'].includes(setting.category) &&
    (setting.key.includes('KEY') || setting.key.includes('URL') || setting.key.includes('SECRET'));

  return (
    <TableRow hover>
      {/* Key */}
      <TableCell>
        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontWeight: 'bold' }}>
          {setting.key}
        </Typography>
      </TableCell>

      {/* Value */}
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              maxWidth: 300,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {getMaskedValue(setting.value)}
          </Typography>
          {isSensitive && (
            <Tooltip title={showValue ? 'Hide value' : 'Show value'}>
              <IconButton size="small" onClick={() => setShowValue(!showValue)}>
                {showValue ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Copy to clipboard">
            <IconButton size="small" onClick={handleCopyToClipboard}>
              <CopyIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </TableCell>

      {/* Description */}
      <TableCell>
        <Typography variant="body2" color="text.secondary">
          {setting.description || 'No description'}
        </Typography>
      </TableCell>

      {/* Category */}
      <TableCell>
        <Chip
          label={setting.category.toUpperCase()}
          color={categoryColors[setting.category] || 'default'}
          size="small"
        />
      </TableCell>

      {/* Last Updated */}
      <TableCell>
        <Typography variant="caption" color="text.secondary">
          {formatDate(setting.updated_at)}
        </Typography>
      </TableCell>

      {/* Actions */}
      <TableCell>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {canTest && (
            <Tooltip title="Test connection">
              <IconButton
                size="small"
                onClick={() => onTest(setting.key, setting.category)}
                color="primary"
              >
                <CableIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
          <Tooltip title="Edit">
            <IconButton size="small" onClick={() => onEdit(setting)} color="primary">
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Delete">
            <IconButton size="small" onClick={() => onDelete(setting.key)} color="error">
              <DeleteIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </TableCell>
    </TableRow>
  );
};

export default SystemSettingCard;
