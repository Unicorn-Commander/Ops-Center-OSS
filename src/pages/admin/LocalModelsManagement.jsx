/**
 * Local Models Management Page
 * Admin interface for managing local inference providers (llama.cpp, Ollama, vLLM)
 * Part of the Local Inference Module for Ops-Center.
 *
 * Features:
 * - Module enable/disable toggle
 * - GPU status monitoring with auto-refresh
 * - Provider tabs with health status
 * - Model management (load/unload)
 * - Settings configuration
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Switch,
  FormControlLabel,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
  Tooltip,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Divider,
  Chip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Memory as GpuIcon,
  Settings as SettingsIcon,
  CheckCircle as EnabledIcon,
  Cancel as DisabledIcon,
  Speed as SpeedIcon,
  Computer as LocalIcon,
  CloudQueue as CloudIcon
} from '@mui/icons-material';
import GPUStatusCard from '../../components/local-inference/GPUStatusCard';
import ProviderPanel from '../../components/local-inference/ProviderPanel';
import PageHeader from '../../components/admin/PageHeader';

// API base URL
const API_BASE = '/api/v1/local-inference';

/**
 * Custom hook for API calls with error handling
 */
const useApi = () => {
  const getAuthHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('authToken')}`
  });

  const apiCall = async (endpoint, options = {}) => {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        ...getAuthHeaders(),
        ...options.headers
      },
      credentials: 'include'
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  };

  return { apiCall };
};

const LocalModelsManagement = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Module state
  const [moduleEnabled, setModuleEnabled] = useState(false);
  const [moduleConfig, setModuleConfig] = useState({});

  // GPU state
  const [gpuInfo, setGpuInfo] = useState([]);
  const [gpuMonitoringEnabled, setGpuMonitoringEnabled] = useState(true);

  // Provider state
  const [providers, setProviders] = useState({});
  const [enabledProviders, setEnabledProviders] = useState([]);
  const [activeProvider, setActiveProvider] = useState(0);
  const [providerHealth, setProviderHealth] = useState({});
  const [providerModels, setProviderModels] = useState({});

  // Settings state
  const [settings, setSettings] = useState({
    auto_detect_on_startup: true,
    health_check_interval: 30,
    default_provider: 'llama.cpp',
    gpu_monitoring_enabled: true
  });

  const { apiCall } = useApi();

  // ============================================
  // Data Fetching Functions
  // ============================================

  const fetchModuleStatus = useCallback(async () => {
    try {
      const data = await apiCall('/status');
      setModuleEnabled(data.enabled);
      setModuleConfig(data.config || {});
      setSettings(prev => ({
        ...prev,
        ...data.settings
      }));
    } catch (err) {
      console.error('Failed to fetch module status:', err);
      // Module might not be enabled, use defaults
      setModuleEnabled(false);
    }
  }, []);

  const fetchGpuStatus = useCallback(async () => {
    if (!gpuMonitoringEnabled) return;

    try {
      const data = await apiCall('/gpu/status');
      setGpuInfo(data.gpus || []);
    } catch (err) {
      console.error('Failed to fetch GPU status:', err);
      // Fallback: try system GPU endpoint
      try {
        const systemResponse = await fetch('/api/v1/hardware/gpu', {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          credentials: 'include'
        });
        if (systemResponse.ok) {
          const systemData = await systemResponse.json();
          setGpuInfo(systemData.gpus || []);
        }
      } catch (fallbackErr) {
        console.error('Fallback GPU fetch failed:', fallbackErr);
      }
    }
  }, [gpuMonitoringEnabled]);

  const fetchProviders = useCallback(async () => {
    try {
      const data = await apiCall('/providers');
      setProviders(data.providers || {});
      setEnabledProviders(
        Object.entries(data.providers || {})
          .filter(([, config]) => config.enabled)
          .map(([name]) => name)
      );
    } catch (err) {
      console.error('Failed to fetch providers:', err);
      // Use default provider list
      setProviders({
        'llama.cpp': { enabled: true, name: 'llama.cpp', base_url: 'http://localhost:8080' },
        'ollama': { enabled: true, name: 'Ollama', base_url: 'http://localhost:11434' },
        'vllm': { enabled: false, name: 'vLLM', base_url: 'http://localhost:8000' }
      });
      setEnabledProviders(['llama.cpp', 'ollama']);
    }
  }, []);

  const fetchProviderHealth = useCallback(async (providerName) => {
    try {
      const data = await apiCall(`/providers/${providerName}/health`);
      setProviderHealth(prev => ({
        ...prev,
        [providerName]: {
          ...data,
          last_check: new Date().toISOString()
        }
      }));
    } catch (err) {
      console.error(`Failed to fetch health for ${providerName}:`, err);
      setProviderHealth(prev => ({
        ...prev,
        [providerName]: {
          healthy: false,
          message: err.message,
          last_check: new Date().toISOString()
        }
      }));
    }
  }, []);

  const fetchProviderModels = useCallback(async (providerName) => {
    try {
      const data = await apiCall(`/providers/${providerName}/models`);
      setProviderModels(prev => ({
        ...prev,
        [providerName]: data.models || []
      }));
    } catch (err) {
      console.error(`Failed to fetch models for ${providerName}:`, err);
      setProviderModels(prev => ({
        ...prev,
        [providerName]: []
      }));
    }
  }, []);

  const fetchAllData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([
        fetchModuleStatus(),
        fetchProviders(),
        fetchGpuStatus()
      ]);

      // Fetch health and models for each enabled provider
      for (const provider of enabledProviders) {
        await fetchProviderHealth(provider);
        await fetchProviderModels(provider);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [fetchModuleStatus, fetchProviders, fetchGpuStatus, enabledProviders, fetchProviderHealth, fetchProviderModels]);

  // ============================================
  // Action Handlers
  // ============================================

  const handleModuleToggle = async () => {
    try {
      await apiCall('/toggle', {
        method: 'POST',
        body: JSON.stringify({ enabled: !moduleEnabled })
      });
      setModuleEnabled(!moduleEnabled);
      setSuccess(`Local inference module ${!moduleEnabled ? 'enabled' : 'disabled'}`);
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleProviderSettingsSave = async (providerName, config) => {
    try {
      await apiCall(`/providers/${providerName}/config`, {
        method: 'PUT',
        body: JSON.stringify(config)
      });
      setSuccess(`${providerName} settings saved successfully`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchProviderHealth(providerName);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleModelLoad = async (model) => {
    const providerName = enabledProviders[activeProvider];
    try {
      await apiCall(`/providers/${providerName}/models/${encodeURIComponent(model.id || model.name)}/load`, {
        method: 'POST'
      });
      setSuccess(`Model "${model.name}" loading...`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchProviderModels(providerName);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleModelUnload = async (model) => {
    const providerName = enabledProviders[activeProvider];
    try {
      await apiCall(`/providers/${providerName}/models/${encodeURIComponent(model.id || model.name)}/unload`, {
        method: 'POST'
      });
      setSuccess(`Model "${model.name}" unloaded`);
      setTimeout(() => setSuccess(null), 3000);
      await fetchProviderModels(providerName);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAutoLoadChange = async (model, autoLoad) => {
    const providerName = enabledProviders[activeProvider];
    try {
      await apiCall(`/providers/${providerName}/models/${encodeURIComponent(model.id || model.name)}/auto-load`, {
        method: 'PUT',
        body: JSON.stringify({ auto_load: autoLoad })
      });
      await fetchProviderModels(providerName);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSettingsSave = async () => {
    try {
      await apiCall('/settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      });
      setSuccess('Settings saved successfully');
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRefresh = async () => {
    await fetchAllData();
    setSuccess('Data refreshed');
    setTimeout(() => setSuccess(null), 2000);
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    fetchAllData();
  }, []);

  // Auto-refresh GPU status
  useEffect(() => {
    if (!gpuMonitoringEnabled || !moduleEnabled) return;

    const interval = setInterval(fetchGpuStatus, 10000); // 10 seconds
    return () => clearInterval(interval);
  }, [gpuMonitoringEnabled, moduleEnabled, fetchGpuStatus]);

  // Fetch provider data when enabled providers change
  useEffect(() => {
    if (enabledProviders.length > 0) {
      enabledProviders.forEach(provider => {
        fetchProviderHealth(provider);
        fetchProviderModels(provider);
      });
    }
  }, [enabledProviders]);

  // ============================================
  // Render
  // ============================================

  if (loading && !gpuInfo.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Local Inference"
        subtitle="Manage local LLM providers and GPU resources"
        actions={(
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={moduleEnabled}
                  onChange={handleModuleToggle}
                  color="primary"
                />
              }
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  {moduleEnabled ? (
                    <EnabledIcon sx={{ fontSize: 18, color: 'success.main' }} />
                  ) : (
                    <DisabledIcon sx={{ fontSize: 18, color: 'error.main' }} />
                  )}
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {moduleEnabled ? 'Enabled' : 'Disabled'}
                  </Typography>
                </Box>
              }
            />
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>
        )}
      />

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* GPU Status Section */}
      <Paper sx={{ p: 2, mb: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <GpuIcon sx={{ color: 'primary.main' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              GPU Status
            </Typography>
            <Chip
              label={`${gpuInfo.length} GPU${gpuInfo.length !== 1 ? 's' : ''}`}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Box>
          <FormControlLabel
            control={
              <Switch
                checked={gpuMonitoringEnabled}
                onChange={(e) => setGpuMonitoringEnabled(e.target.checked)}
                size="small"
              />
            }
            label={<Typography variant="caption">Auto-refresh</Typography>}
          />
        </Box>
        <Grid container spacing={2}>
          {gpuInfo.length > 0 ? (
            gpuInfo.map((gpu, index) => (
              <Grid item xs={12} md={6} lg={4} key={gpu.id || index}>
                <GPUStatusCard gpu={gpu} index={index} />
              </Grid>
            ))
          ) : (
            <Grid item xs={12}>
              <Box
                sx={{
                  p: 4,
                  textAlign: 'center',
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  borderRadius: 2
                }}
              >
                <Typography color="text.secondary">
                  No GPUs detected. Make sure GPU monitoring is enabled and drivers are installed.
                </Typography>
              </Box>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Provider Tabs */}
      {enabledProviders.length > 0 && (
        <Paper sx={{ mb: 3, borderRadius: 2, overflow: 'hidden' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs
              value={activeProvider}
              onChange={(e, newValue) => setActiveProvider(newValue)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{
                '& .MuiTab-root': {
                  textTransform: 'none',
                  fontWeight: 600,
                  minHeight: 56
                }
              }}
            >
              {enabledProviders.map((provider, index) => (
                <Tab
                  key={provider}
                  label={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {provider}
                      {providerHealth[provider]?.healthy && (
                        <Chip
                          label="Connected"
                          size="small"
                          color="success"
                          sx={{ height: 20, fontSize: '0.65rem' }}
                        />
                      )}
                    </Box>
                  }
                />
              ))}
            </Tabs>
          </Box>
          <Box sx={{ p: 2 }}>
            {enabledProviders.map((provider, index) => (
              <Box
                key={provider}
                role="tabpanel"
                hidden={activeProvider !== index}
              >
                {activeProvider === index && (
                  <ProviderPanel
                    provider={provider}
                    providerConfig={providers[provider] || {}}
                    health={providerHealth[provider]}
                    models={providerModels[provider] || []}
                    onSettingsSave={handleProviderSettingsSave}
                    onHealthRefresh={fetchProviderHealth}
                    onModelLoad={handleModelLoad}
                    onModelUnload={handleModelUnload}
                    onAutoLoadChange={handleAutoLoadChange}
                    loading={loading}
                  />
                )}
              </Box>
            ))}
          </Box>
        </Paper>
      )}

      {/* Global Settings */}
      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
          <SettingsIcon sx={{ color: 'text.secondary' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Module Settings
          </Typography>
        </Box>

        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.auto_detect_on_startup}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    auto_detect_on_startup: e.target.checked
                  }))}
                />
              }
              label="Auto-detect providers on startup"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              size="small"
              label="Health Check Interval (seconds)"
              type="number"
              value={settings.health_check_interval}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                health_check_interval: parseInt(e.target.value) || 30
              }))}
              inputProps={{ min: 10, max: 300 }}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControl fullWidth size="small">
              <InputLabel>Default Provider</InputLabel>
              <Select
                value={settings.default_provider}
                onChange={(e) => setSettings(prev => ({
                  ...prev,
                  default_provider: e.target.value
                }))}
                label="Default Provider"
              >
                <MenuItem value="llama.cpp">llama.cpp</MenuItem>
                <MenuItem value="ollama">Ollama</MenuItem>
                <MenuItem value="vllm">vLLM</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={12} md={4}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.gpu_monitoring_enabled}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    gpu_monitoring_enabled: e.target.checked
                  }))}
                />
              }
              label="Enable GPU monitoring"
            />
          </Grid>
        </Grid>

        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleSettingsSave}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              textTransform: 'none',
              fontWeight: 600,
              px: 4,
              '&:hover': {
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)',
                transform: 'translateY(-2px)',
                boxShadow: 4
              }
            }}
          >
            Save Settings
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default LocalModelsManagement;
