/**
 * Provider Panel Component
 * Reusable panel for managing local inference providers (llama.cpp, Ollama, vLLM).
 * Includes settings form, health status, and models list.
 * Part of the Local Inference Module for Ops-Center.
 */

import React, { useState, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Grid,
  Chip,
  Divider,
  Alert,
  CircularProgress,
  Tooltip,
  IconButton,
  Collapse,
  InputAdornment
} from '@mui/material';
import {
  CheckCircle as HealthyIcon,
  Error as UnhealthyIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandIcon,
  ExpandLess as CollapseIcon,
  Save as SaveIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import ModelCard from './ModelCard';

/**
 * Health status indicator component
 */
const HealthIndicator = ({ health, lastCheck, onRefresh, loading }) => {
  const isHealthy = health?.healthy || health?.status === 'ok' || health?.status === 'healthy';
  const statusText = health?.message || (isHealthy ? 'Connected' : 'Disconnected');

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
      <Tooltip title={statusText} arrow>
        <Chip
          icon={isHealthy ? <HealthyIcon /> : <UnhealthyIcon />}
          label={isHealthy ? 'Healthy' : 'Unhealthy'}
          size="small"
          color={isHealthy ? 'success' : 'error'}
          sx={{
            fontWeight: 600,
            '& .MuiChip-icon': {
              fontSize: 16
            }
          }}
        />
      </Tooltip>
      {lastCheck && (
        <Typography variant="caption" color="text.secondary">
          Last check: {new Date(lastCheck).toLocaleTimeString()}
        </Typography>
      )}
      <Tooltip title="Refresh health status" arrow>
        <IconButton
          size="small"
          onClick={onRefresh}
          disabled={loading}
          sx={{ p: 0.5 }}
        >
          {loading ? <CircularProgress size={16} /> : <RefreshIcon fontSize="small" />}
        </IconButton>
      </Tooltip>
    </Box>
  );
};

const ProviderPanel = ({
  provider,
  providerConfig,
  health,
  models = [],
  onSettingsSave,
  onHealthRefresh,
  onModelLoad,
  onModelUnload,
  onAutoLoadChange,
  loading = false,
  error = null,
  success = null
}) => {
  const [settingsExpanded, setSettingsExpanded] = useState(false);
  const [localConfig, setLocalConfig] = useState(providerConfig || {});
  const [saving, setSaving] = useState(false);
  const [healthLoading, setHealthLoading] = useState(false);

  // Provider-specific labels
  const providerLabels = {
    'llama.cpp': {
      name: 'llama.cpp Server',
      description: 'High-performance C++ inference server for GGUF models',
      urlLabel: 'Server URL',
      urlPlaceholder: 'http://localhost:8080'
    },
    'ollama': {
      name: 'Ollama',
      description: 'Local AI model runner with easy model management',
      urlLabel: 'Ollama API URL',
      urlPlaceholder: 'http://localhost:11434'
    },
    'vllm': {
      name: 'vLLM',
      description: 'High-throughput and memory-efficient inference engine',
      urlLabel: 'vLLM API URL',
      urlPlaceholder: 'http://localhost:8000'
    }
  };

  const labels = providerLabels[provider] || {
    name: provider,
    description: 'Local inference provider',
    urlLabel: 'API URL',
    urlPlaceholder: 'http://localhost:8000'
  };

  const handleConfigChange = useCallback((field, value) => {
    setLocalConfig(prev => ({
      ...prev,
      [field]: value
    }));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSettingsSave?.(provider, localConfig);
    } finally {
      setSaving(false);
    }
  };

  const handleHealthRefresh = async () => {
    setHealthLoading(true);
    try {
      await onHealthRefresh?.(provider);
    } finally {
      setHealthLoading(false);
    }
  };

  const isHealthy = health?.healthy || health?.status === 'ok' || health?.status === 'healthy';

  return (
    <Box sx={{ mb: 3 }}>
      {/* Provider Header */}
      <Paper
        sx={{
          p: 2,
          borderRadius: 2,
          border: '1px solid',
          borderColor: isHealthy ? 'success.main' : 'divider',
          background: isHealthy
            ? 'linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(56, 142, 60, 0.05) 100%)'
            : 'linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%)'
        }}
      >
        {/* Header Row */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              {labels.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {labels.description}
            </Typography>
          </Box>
          <HealthIndicator
            health={health}
            lastCheck={health?.last_check}
            onRefresh={handleHealthRefresh}
            loading={healthLoading || loading}
          />
        </Box>

        {/* Alerts */}
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => {}}>
            {error}
          </Alert>
        )}
        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => {}}>
            {success}
          </Alert>
        )}

        {/* Settings Section */}
        <Box>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              cursor: 'pointer',
              mb: 1
            }}
            onClick={() => setSettingsExpanded(!settingsExpanded)}
          >
            <SettingsIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="subtitle2" color="text.secondary">
              Settings
            </Typography>
            {settingsExpanded ? (
              <CollapseIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            ) : (
              <ExpandIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            )}
          </Box>

          <Collapse in={settingsExpanded}>
            <Box sx={{ pt: 2, pb: 1 }}>
              <Grid container spacing={2}>
                {/* API URL */}
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    size="small"
                    label={labels.urlLabel}
                    placeholder={labels.urlPlaceholder}
                    value={localConfig.base_url || localConfig.url || ''}
                    onChange={(e) => handleConfigChange('base_url', e.target.value)}
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <LinkIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>

                {/* Idle Timeout */}
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Idle Timeout (seconds)"
                    type="number"
                    value={localConfig.idle_timeout || 300}
                    onChange={(e) => handleConfigChange('idle_timeout', parseInt(e.target.value) || 300)}
                    inputProps={{ min: 0, max: 86400 }}
                    helperText="0 = never unload"
                  />
                </Grid>

                {/* Max Models */}
                <Grid item xs={12} md={3}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Max Loaded Models"
                    type="number"
                    value={localConfig.max_models || 1}
                    onChange={(e) => handleConfigChange('max_models', parseInt(e.target.value) || 1)}
                    inputProps={{ min: 1, max: 10 }}
                    helperText="Simultaneous models"
                  />
                </Grid>

                {/* Provider-specific settings */}
                {provider === 'llama.cpp' && (
                  <>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Context Size"
                        type="number"
                        value={localConfig.context_size || 4096}
                        onChange={(e) => handleConfigChange('context_size', parseInt(e.target.value) || 4096)}
                        inputProps={{ min: 512, max: 131072, step: 512 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="GPU Layers"
                        type="number"
                        value={localConfig.n_gpu_layers || -1}
                        onChange={(e) => handleConfigChange('n_gpu_layers', parseInt(e.target.value))}
                        helperText="-1 = all layers"
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Threads"
                        type="number"
                        value={localConfig.threads || 0}
                        onChange={(e) => handleConfigChange('threads', parseInt(e.target.value) || 0)}
                        helperText="0 = auto"
                      />
                    </Grid>
                  </>
                )}

                {provider === 'ollama' && (
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={localConfig.keep_alive || false}
                          onChange={(e) => handleConfigChange('keep_alive', e.target.checked)}
                        />
                      }
                      label="Keep Models Alive"
                    />
                  </Grid>
                )}

                {provider === 'vllm' && (
                  <>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="Tensor Parallel Size"
                        type="number"
                        value={localConfig.tensor_parallel_size || 1}
                        onChange={(e) => handleConfigChange('tensor_parallel_size', parseInt(e.target.value) || 1)}
                        inputProps={{ min: 1, max: 8 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={4}>
                      <TextField
                        fullWidth
                        size="small"
                        label="GPU Memory Utilization"
                        type="number"
                        value={localConfig.gpu_memory_utilization || 0.9}
                        onChange={(e) => handleConfigChange('gpu_memory_utilization', parseFloat(e.target.value) || 0.9)}
                        inputProps={{ min: 0.1, max: 1.0, step: 0.05 }}
                      />
                    </Grid>
                  </>
                )}
              </Grid>

              {/* Save Button */}
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="contained"
                  size="small"
                  onClick={handleSave}
                  disabled={saving}
                  startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    textTransform: 'none',
                    fontWeight: 600,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
                    }
                  }}
                >
                  {saving ? 'Saving...' : 'Save Settings'}
                </Button>
              </Box>
            </Box>
          </Collapse>
        </Box>

        <Divider sx={{ my: 2 }} />

        {/* Models Section */}
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Models ({models.length})
            </Typography>
            <Chip
              label={`${models.filter(m => m.status === 'loaded' || m.status === 'running').length} loaded`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>

          {models.length === 0 ? (
            <Box
              sx={{
                p: 3,
                textAlign: 'center',
                backgroundColor: 'rgba(0, 0, 0, 0.02)',
                borderRadius: 2
              }}
            >
              <Typography color="text.secondary">
                {isHealthy
                  ? 'No models found. Pull or download models to get started.'
                  : 'Connect to the provider to see available models.'}
              </Typography>
            </Box>
          ) : (
            <Box>
              {models.map((model) => (
                <ModelCard
                  key={model.id || model.name}
                  model={model}
                  onLoad={onModelLoad}
                  onUnload={onModelUnload}
                  onAutoLoadChange={onAutoLoadChange}
                  loading={loading}
                  disabled={!isHealthy}
                />
              ))}
            </Box>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default ProviderPanel;
