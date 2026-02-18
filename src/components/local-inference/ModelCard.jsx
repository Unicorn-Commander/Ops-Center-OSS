/**
 * Model Card Component
 * Displays local model information with status, size, and actions.
 * Part of the Local Inference Module for Ops-Center.
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Chip,
  Button,
  IconButton,
  Checkbox,
  FormControlLabel,
  Tooltip,
  CircularProgress,
  Collapse
} from '@mui/material';
import {
  PlayArrow as LoadIcon,
  Stop as UnloadIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Memory as MemoryIcon,
  Settings as SettingsIcon,
  Info as InfoIcon
} from '@mui/icons-material';

/**
 * Format file size to human-readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} - Formatted string
 */
const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '-';
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
};

/**
 * Get status chip props based on model status
 * @param {string} status - Model status
 * @returns {object} - Chip props
 */
const getStatusProps = (status) => {
  switch (status?.toLowerCase()) {
    case 'loaded':
    case 'running':
      return {
        label: 'Loaded',
        color: 'success',
        sx: { backgroundColor: 'rgba(76, 175, 80, 0.15)', color: '#4caf50', fontWeight: 600 }
      };
    case 'loading':
      return {
        label: 'Loading...',
        color: 'warning',
        sx: { backgroundColor: 'rgba(255, 152, 0, 0.15)', color: '#ff9800', fontWeight: 600 }
      };
    case 'unloading':
      return {
        label: 'Unloading...',
        color: 'warning',
        sx: { backgroundColor: 'rgba(255, 152, 0, 0.15)', color: '#ff9800', fontWeight: 600 }
      };
    case 'error':
      return {
        label: 'Error',
        color: 'error',
        sx: { backgroundColor: 'rgba(244, 67, 54, 0.15)', color: '#f44336', fontWeight: 600 }
      };
    case 'unloaded':
    default:
      return {
        label: 'Unloaded',
        color: 'default',
        sx: { backgroundColor: 'rgba(158, 158, 158, 0.15)', color: '#9e9e9e', fontWeight: 600 }
      };
  }
};

/**
 * Get quantization badge color
 * @param {string} quant - Quantization type
 * @returns {string} - Color code
 */
const getQuantColor = (quant) => {
  if (!quant) return '#9e9e9e';
  const q = quant.toLowerCase();
  if (q.includes('q4') || q.includes('4bit')) return '#4caf50';
  if (q.includes('q5')) return '#8bc34a';
  if (q.includes('q6')) return '#cddc39';
  if (q.includes('q8') || q.includes('8bit')) return '#ff9800';
  if (q.includes('fp16') || q.includes('f16')) return '#2196f3';
  if (q.includes('fp32') || q.includes('f32')) return '#9c27b0';
  return '#9e9e9e';
};

const ModelCard = ({
  model,
  onLoad,
  onUnload,
  onAutoLoadChange,
  onSettingsClick,
  loading = false,
  disabled = false
}) => {
  const [expanded, setExpanded] = useState(false);

  if (!model) {
    return null;
  }

  const {
    id,
    name,
    filename,
    size,
    size_bytes,
    quantization,
    status = 'unloaded',
    auto_load = false,
    context_length,
    parameters,
    family,
    provider,
    modified_at,
    details = {}
  } = model;

  const statusProps = getStatusProps(status);
  const isLoaded = status === 'loaded' || status === 'running';
  const isTransitioning = status === 'loading' || status === 'unloading';
  const quantColor = getQuantColor(quantization);

  const handleLoadToggle = () => {
    if (isLoaded) {
      onUnload?.(model);
    } else {
      onLoad?.(model);
    }
  };

  const displayName = name || filename || id || 'Unknown Model';
  const displaySize = size || formatSize(size_bytes);

  return (
    <Paper
      sx={{
        mb: 1.5,
        overflow: 'hidden',
        borderRadius: 2,
        border: '1px solid',
        borderColor: isLoaded ? 'success.main' : 'divider',
        transition: 'all 0.2s ease',
        '&:hover': {
          borderColor: isLoaded ? 'success.main' : 'primary.main',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }
      }}
    >
      {/* Main Row */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          flexWrap: 'wrap'
        }}
      >
        {/* Expand Button */}
        <IconButton
          size="small"
          onClick={() => setExpanded(!expanded)}
          sx={{ p: 0.5 }}
        >
          {expanded ? <CollapseIcon /> : <ExpandIcon />}
        </IconButton>

        {/* Model Name */}
        <Box sx={{ flex: 1, minWidth: 200 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600, fontSize: '0.95rem' }}>
            {displayName}
          </Typography>
          {filename && filename !== name && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block' }}>
              {filename}
            </Typography>
          )}
        </Box>

        {/* Size */}
        <Tooltip title="Model file size" arrow>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, minWidth: 80 }}>
            <MemoryIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
            <Typography variant="body2" sx={{ fontWeight: 500 }}>
              {displaySize}
            </Typography>
          </Box>
        </Tooltip>

        {/* Quantization */}
        {quantization && (
          <Tooltip title={`Quantization: ${quantization}`} arrow>
            <Chip
              label={quantization}
              size="small"
              sx={{
                backgroundColor: `${quantColor}20`,
                color: quantColor,
                fontWeight: 600,
                fontSize: '0.7rem',
                height: 24
              }}
            />
          </Tooltip>
        )}

        {/* Status */}
        <Chip
          {...statusProps}
          size="small"
          sx={{
            ...statusProps.sx,
            minWidth: 80,
            height: 24,
            fontSize: '0.75rem'
          }}
        />

        {/* Auto-load Checkbox */}
        <Tooltip title="Automatically load model on startup" arrow>
          <FormControlLabel
            control={
              <Checkbox
                size="small"
                checked={auto_load}
                onChange={(e) => onAutoLoadChange?.(model, e.target.checked)}
                disabled={disabled}
              />
            }
            label={<Typography variant="caption">Auto</Typography>}
            sx={{ m: 0, minWidth: 60 }}
          />
        </Tooltip>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant={isLoaded ? 'outlined' : 'contained'}
            color={isLoaded ? 'error' : 'primary'}
            size="small"
            onClick={handleLoadToggle}
            disabled={disabled || loading || isTransitioning}
            startIcon={
              loading || isTransitioning ? (
                <CircularProgress size={16} color="inherit" />
              ) : isLoaded ? (
                <UnloadIcon />
              ) : (
                <LoadIcon />
              )
            }
            sx={{
              minWidth: 100,
              borderRadius: 1.5,
              textTransform: 'none',
              fontWeight: 600,
              ...(isLoaded ? {} : {
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
                }
              })
            }}
          >
            {isTransitioning ? (status === 'loading' ? 'Loading' : 'Unloading') : isLoaded ? 'Unload' : 'Load'}
          </Button>

          {onSettingsClick && (
            <Tooltip title="Model settings" arrow>
              <IconButton
                size="small"
                onClick={() => onSettingsClick?.(model)}
                disabled={disabled}
              >
                <SettingsIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {/* Expanded Details */}
      <Collapse in={expanded}>
        <Box
          sx={{
            px: 2,
            pb: 2,
            pt: 0,
            borderTop: '1px solid',
            borderColor: 'divider',
            backgroundColor: 'rgba(0, 0, 0, 0.02)'
          }}
        >
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3, pt: 2 }}>
            {provider && (
              <Box>
                <Typography variant="caption" color="text.secondary">Provider</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{provider}</Typography>
              </Box>
            )}
            {family && (
              <Box>
                <Typography variant="caption" color="text.secondary">Family</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{family}</Typography>
              </Box>
            )}
            {parameters && (
              <Box>
                <Typography variant="caption" color="text.secondary">Parameters</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{parameters}</Typography>
              </Box>
            )}
            {context_length && (
              <Box>
                <Typography variant="caption" color="text.secondary">Context Length</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{context_length.toLocaleString()}</Typography>
              </Box>
            )}
            {modified_at && (
              <Box>
                <Typography variant="caption" color="text.secondary">Modified</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {new Date(modified_at).toLocaleDateString()}
                </Typography>
              </Box>
            )}
            {details.parameter_size && (
              <Box>
                <Typography variant="caption" color="text.secondary">Parameter Size</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{details.parameter_size}</Typography>
              </Box>
            )}
            {details.quantization_level && (
              <Box>
                <Typography variant="caption" color="text.secondary">Quantization Level</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{details.quantization_level}</Typography>
              </Box>
            )}
          </Box>

          {/* Model ID for reference */}
          <Box sx={{ mt: 2, pt: 1, borderTop: '1px dashed', borderColor: 'divider' }}>
            <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
              ID: {id}
            </Typography>
          </Box>
        </Box>
      </Collapse>
    </Paper>
  );
};

export default ModelCard;
