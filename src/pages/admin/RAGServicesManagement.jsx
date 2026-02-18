/**
 * RAG Services Management Page
 * Admin interface for managing Infinity embedding/reranker services
 * Part of the Ops-Center admin dashboard.
 *
 * Features:
 * - Infinity Proxy health status
 * - Embeddings service status and controls
 * - Reranker service status and controls
 * - GPU memory usage display
 * - Idle timeout configuration
 * - Manual start/stop controls
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Chip,
  Tooltip,
  IconButton,
  TextField,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Memory as GpuIcon,
  Settings as SettingsIcon,
  CheckCircle as HealthyIcon,
  Cancel as UnhealthyIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Storage as ModelIcon,
  Timer as TimerIcon,
  Cloud as CloudIcon,
  CloudOff as CloudOffIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

// API base URL
const API_BASE = '/api/v1/rag-services';

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

/**
 * Service Card Component
 * Displays status and controls for a single service (embeddings or reranker)
 */
const ServiceCard = ({
  name,
  displayName,
  status,
  model,
  onStart,
  onStop,
  loading,
  disabled
}) => {
  const isRunning = status?.running || false;
  const serviceStatus = status?.service_status || 'unknown';
  const lastActivity = status?.last_activity_seconds_ago;

  const getStatusColor = () => {
    if (serviceStatus === 'healthy') return 'success';
    if (serviceStatus === 'starting') return 'warning';
    if (isRunning) return 'info';
    return 'default';
  };

  const getStatusLabel = () => {
    if (serviceStatus === 'healthy') return 'Running';
    if (serviceStatus === 'starting') return 'Starting...';
    if (isRunning) return 'Container Running';
    return 'Stopped';
  };

  const formatLastActivity = () => {
    if (!lastActivity) return 'Never';
    if (lastActivity < 60) return `${lastActivity}s ago`;
    if (lastActivity < 3600) return `${Math.floor(lastActivity / 60)}m ago`;
    return `${Math.floor(lastActivity / 3600)}h ago`;
  };

  return (
    <Card
      sx={{
        height: '100%',
        background: isRunning
          ? 'linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(76, 175, 80, 0.1) 100%)'
          : 'linear-gradient(135deg, rgba(158, 158, 158, 0.05) 0%, rgba(158, 158, 158, 0.1) 100%)',
        border: `1px solid ${isRunning ? 'rgba(76, 175, 80, 0.3)' : 'rgba(158, 158, 158, 0.3)'}`,
        borderRadius: 2
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
              {isRunning ? (
                <CloudIcon sx={{ color: 'success.main' }} />
              ) : (
                <CloudOffIcon sx={{ color: 'text.disabled' }} />
              )}
              {displayName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {name}
            </Typography>
          </Box>
          <Chip
            label={getStatusLabel()}
            size="small"
            color={getStatusColor()}
            sx={{ fontWeight: 600 }}
          />
        </Box>

        {/* Model Info */}
        <Box sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <ModelIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
            <Typography variant="body2" color="text.secondary">
              Model
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ fontFamily: 'monospace', pl: 3 }}>
            {model || 'Not configured'}
          </Typography>
        </Box>

        {/* Container Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            Container: <code style={{ color: '#1976d2' }}>{status?.container || 'N/A'}</code>
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upstream: <code style={{ color: '#1976d2' }}>{status?.upstream || 'N/A'}</code>
          </Typography>
        </Box>

        {/* Last Activity */}
        {isRunning && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimerIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Last Activity: {formatLastActivity()}
              </Typography>
            </Box>
          </Box>
        )}

        <Divider sx={{ my: 2 }} />

        {/* Controls */}
        <Box sx={{ display: 'flex', gap: 1 }}>
          {isRunning ? (
            <Button
              variant="outlined"
              color="error"
              startIcon={loading ? <CircularProgress size={16} /> : <StopIcon />}
              onClick={onStop}
              disabled={loading || disabled}
              fullWidth
              sx={{ textTransform: 'none' }}
            >
              Stop Service
            </Button>
          ) : (
            <Button
              variant="contained"
              color="success"
              startIcon={loading ? <CircularProgress size={16} /> : <StartIcon />}
              onClick={onStart}
              disabled={loading || disabled}
              fullWidth
              sx={{ textTransform: 'none' }}
            >
              Start Service
            </Button>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

/**
 * GPU Memory Card Component
 */
const GPUMemoryCard = ({ gpuInfo }) => {
  if (!gpuInfo || !gpuInfo.gpus || gpuInfo.gpus.length === 0) {
    return (
      <Card sx={{ height: '100%', borderRadius: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <GpuIcon sx={{ color: 'text.secondary' }} />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              GPU Memory
            </Typography>
          </Box>
          <Alert severity="info">
            GPU information not available. nvidia-smi may not be accessible.
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%', borderRadius: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <GpuIcon sx={{ color: 'primary.main' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            GPU Memory
          </Typography>
          <Chip
            label={`${gpuInfo.gpus.length} GPU${gpuInfo.gpus.length > 1 ? 's' : ''}`}
            size="small"
            variant="outlined"
          />
        </Box>

        {gpuInfo.gpus.map((gpu, index) => {
          const usagePercent = (gpu.memory_used_mb / gpu.memory_total_mb) * 100;
          return (
            <Box key={index} sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  GPU {gpu.index}: {gpu.name}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {gpu.memory_used_mb} / {gpu.memory_total_mb} MB
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={usagePercent}
                sx={{
                  height: 8,
                  borderRadius: 4,
                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                    backgroundColor: usagePercent > 90 ? '#f44336' : usagePercent > 70 ? '#ff9800' : '#4caf50'
                  }
                }}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 0.5 }}>
                <Typography variant="caption" color="text.secondary">
                  {usagePercent.toFixed(1)}% used
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {gpu.memory_free_mb} MB free
                </Typography>
              </Box>
            </Box>
          );
        })}

        {/* Total Summary */}
        <Divider sx={{ my: 2 }} />
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Typography variant="body2" color="text.secondary">
            Total Memory:
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {gpuInfo.used_memory_mb.toLocaleString()} / {gpuInfo.total_memory_mb.toLocaleString()} MB
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

/**
 * Main RAG Services Management Page
 */
const RAGServicesManagement = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Service status
  const [status, setStatus] = useState(null);

  // Operation loading states
  const [embeddingsLoading, setEmbeddingsLoading] = useState(false);
  const [rerankerLoading, setRerankerLoading] = useState(false);

  // Idle timeout state
  const [idleTimeout, setIdleTimeout] = useState(1800);
  const [idleTimeoutInput, setIdleTimeoutInput] = useState('1800');
  const [savingTimeout, setSavingTimeout] = useState(false);

  const { apiCall } = useApi();

  // Fetch status
  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiCall('/status');
      setStatus(data);
      setIdleTimeout(data.idle_timeout_seconds);
      setIdleTimeoutInput(String(data.idle_timeout_seconds));
      setError(null);
    } catch (err) {
      console.error('Failed to fetch RAG services status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  // Service control handlers
  const handleStartEmbeddings = async () => {
    setEmbeddingsLoading(true);
    try {
      await apiCall('/embeddings/start', { method: 'POST' });
      setSuccess('Embeddings service starting...');
      setTimeout(() => setSuccess(null), 3000);
      // Refresh status after a delay
      setTimeout(fetchStatus, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setEmbeddingsLoading(false);
    }
  };

  const handleStopEmbeddings = async () => {
    setEmbeddingsLoading(true);
    try {
      await apiCall('/embeddings/stop', { method: 'POST' });
      setSuccess('Embeddings service stopped');
      setTimeout(() => setSuccess(null), 3000);
      setTimeout(fetchStatus, 1000);
    } catch (err) {
      setError(err.message);
    } finally {
      setEmbeddingsLoading(false);
    }
  };

  const handleStartReranker = async () => {
    setRerankerLoading(true);
    try {
      await apiCall('/reranker/start', { method: 'POST' });
      setSuccess('Reranker service starting...');
      setTimeout(() => setSuccess(null), 3000);
      setTimeout(fetchStatus, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setRerankerLoading(false);
    }
  };

  const handleStopReranker = async () => {
    setRerankerLoading(true);
    try {
      await apiCall('/reranker/stop', { method: 'POST' });
      setSuccess('Reranker service stopped');
      setTimeout(() => setSuccess(null), 3000);
      setTimeout(fetchStatus, 1000);
    } catch (err) {
      setError(err.message);
    } finally {
      setRerankerLoading(false);
    }
  };

  const handleSaveIdleTimeout = async () => {
    const timeoutValue = parseInt(idleTimeoutInput, 10);
    if (isNaN(timeoutValue) || timeoutValue < 60 || timeoutValue > 86400) {
      setError('Idle timeout must be between 60 and 86400 seconds');
      return;
    }

    setSavingTimeout(true);
    try {
      await apiCall('/config/idle-timeout', {
        method: 'PUT',
        body: JSON.stringify({ idle_timeout_seconds: timeoutValue })
      });
      setIdleTimeout(timeoutValue);
      setSuccess('Idle timeout updated. Proxy restart may be required.');
      setTimeout(() => setSuccess(null), 5000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSavingTimeout(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await fetchStatus();
    setSuccess('Status refreshed');
    setTimeout(() => setSuccess(null), 2000);
  };

  // Loading state
  if (loading && !status) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="RAG Services"
        subtitle="Manage Infinity embedding and reranker services for RAG applications"
        actions={(
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              icon={status?.proxy_healthy ? <HealthyIcon /> : <UnhealthyIcon />}
              label={`Proxy: ${status?.proxy_healthy ? 'Healthy' : 'Unhealthy'}`}
              color={status?.proxy_healthy ? 'success' : 'error'}
              variant="outlined"
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

      {/* Service Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <ServiceCard
            name="embeddings"
            displayName="Embeddings Service"
            status={status?.embeddings}
            model={status?.embeddings?.model}
            onStart={handleStartEmbeddings}
            onStop={handleStopEmbeddings}
            loading={embeddingsLoading}
            disabled={rerankerLoading}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <ServiceCard
            name="reranker"
            displayName="Reranker Service"
            status={status?.reranker}
            model={status?.reranker?.model}
            onStart={handleStartReranker}
            onStop={handleStopReranker}
            loading={rerankerLoading}
            disabled={embeddingsLoading}
          />
        </Grid>
      </Grid>

      {/* GPU Memory */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12}>
          <GPUMemoryCard gpuInfo={status?.gpu_info} />
        </Grid>
      </Grid>

      {/* Configuration */}
      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
          <SettingsIcon sx={{ color: 'text.secondary' }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Configuration
          </Typography>
        </Box>

        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={4}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <TimerIcon sx={{ color: 'text.secondary' }} />
              <Typography variant="body2" color="text.secondary">
                Idle Timeout (seconds)
              </Typography>
            </Box>
          </Grid>
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              size="small"
              type="number"
              value={idleTimeoutInput}
              onChange={(e) => setIdleTimeoutInput(e.target.value)}
              inputProps={{ min: 60, max: 86400 }}
              helperText="Services auto-stop after this idle period (60-86400)"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              onClick={handleSaveIdleTimeout}
              disabled={savingTimeout || idleTimeoutInput === String(idleTimeout)}
              startIcon={savingTimeout ? <CircularProgress size={16} /> : null}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: 2,
                textTransform: 'none',
                fontWeight: 600,
                '&:hover': {
                  background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)',
                }
              }}
            >
              Save Timeout
            </Button>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Proxy Info */}
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <strong>Proxy URL:</strong> {status?.proxy_url || 'http://localhost:8086'}
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <strong>Current Idle Timeout:</strong> {idleTimeout} seconds ({Math.floor(idleTimeout / 60)} minutes)
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Last Updated:</strong> {status?.last_updated ? new Date(status.last_updated).toLocaleString() : 'N/A'}
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default RAGServicesManagement;
