/**
 * GPU Services Management Page
 * Admin interface for managing GPU-based services (Infinity RAG + Granite Extraction LLMs)
 * Part of the Ops-Center admin dashboard.
 *
 * Features:
 * - RAG Services (Infinity): embeddings and reranker for RAG applications
 * - Extraction Services (Granite): granite1 and granite2 for document extraction LLMs
 * - GPU memory usage display for both GPUs
 * - Idle timeout configuration for each service category
 * - Manual start/stop controls
 * - Auto-refresh every 30 seconds
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
  LinearProgress,
  Tabs,
  Tab
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
  CloudOff as CloudOffIcon,
  Hub as HubIcon,
  TextFields as TextFieldsIcon,
  Description as DocumentIcon,
  Key as KeyIcon,
  Dns as ServicesIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

// Lazy load the API Keys component
const GraniteApiKeysPanel = React.lazy(() => import('./GraniteApiKeysManagement'));

// API base URL
const API_BASE = '/api/v1/gpu-services';

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
 * Displays status and controls for a single GPU service
 */
const ServiceCard = ({
  name,
  displayName,
  description,
  status,
  model,
  containerName,
  onStart,
  onStop,
  loading,
  disabled,
  icon: IconComponent
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
    if (!lastActivity && lastActivity !== 0) return 'Never';
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
                <IconComponent sx={{ color: 'success.main' }} />
              ) : (
                <IconComponent sx={{ color: 'text.disabled' }} />
              )}
              {displayName}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {description}
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
          <Typography variant="body2" sx={{ fontFamily: 'monospace', pl: 3, fontSize: '0.8rem' }}>
            {model || 'Not configured'}
          </Typography>
        </Box>

        {/* Container Info */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
            Container: <code style={{ color: '#1976d2' }}>{containerName || status?.container || 'N/A'}</code>
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
 * Displays memory usage for both GPUs with progress bars
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
            {gpuInfo.used_memory_mb?.toLocaleString() || 0} / {gpuInfo.total_memory_mb?.toLocaleString() || 0} MB
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );
};

/**
 * Section Header Component
 */
const SectionHeader = ({ title, subtitle, icon: IconComponent, statusCount }) => {
  return (
    <Box sx={{ mb: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconComponent sx={{ fontSize: 24, color: 'primary.main' }} />
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
        {statusCount !== undefined && (
          <Chip
            label={`${statusCount.running}/${statusCount.total} Running`}
            size="small"
            color={statusCount.running === statusCount.total ? 'success' : statusCount.running > 0 ? 'warning' : 'default'}
            sx={{ ml: 1 }}
          />
        )}
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ pl: 4 }}>
        {subtitle}
      </Typography>
    </Box>
  );
};

/**
 * Main GPU Services Management Page
 */
const GPUServicesManagement = () => {
  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Service status
  const [status, setStatus] = useState(null);

  // Operation loading states
  const [embeddingsLoading, setEmbeddingsLoading] = useState(false);
  const [rerankerLoading, setRerankerLoading] = useState(false);
  const [granite1Loading, setGranite1Loading] = useState(false);
  const [granite2Loading, setGranite2Loading] = useState(false);

  // Idle timeout states
  const [infinityIdleTimeout, setInfinityIdleTimeout] = useState(1800);
  const [infinityIdleTimeoutInput, setInfinityIdleTimeoutInput] = useState('1800');
  const [graniteIdleTimeout, setGraniteIdleTimeout] = useState(300);
  const [graniteIdleTimeoutInput, setGraniteIdleTimeoutInput] = useState('300');
  const [savingInfinityTimeout, setSavingInfinityTimeout] = useState(false);
  const [savingGraniteTimeout, setSavingGraniteTimeout] = useState(false);

  const { apiCall } = useApi();

  // Fetch status
  const fetchStatus = useCallback(async () => {
    try {
      const data = await apiCall('/status');
      setStatus(data);

      // Update idle timeout states from response
      if (data.infinity_idle_timeout_seconds !== undefined) {
        setInfinityIdleTimeout(data.infinity_idle_timeout_seconds);
        setInfinityIdleTimeoutInput(String(data.infinity_idle_timeout_seconds));
      }
      if (data.granite_idle_timeout_seconds !== undefined) {
        setGraniteIdleTimeout(data.granite_idle_timeout_seconds);
        setGraniteIdleTimeoutInput(String(data.granite_idle_timeout_seconds));
      }

      setError(null);
    } catch (err) {
      console.error('Failed to fetch GPU services status:', err);
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
  const handleStartService = async (service, setLoadingFn) => {
    setLoadingFn(true);
    try {
      await apiCall(`/${service}/start`, { method: 'POST' });
      setSuccess(`${service} service starting...`);
      setTimeout(() => setSuccess(null), 3000);
      setTimeout(fetchStatus, 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingFn(false);
    }
  };

  const handleStopService = async (service, setLoadingFn) => {
    setLoadingFn(true);
    try {
      await apiCall(`/${service}/stop`, { method: 'POST' });
      setSuccess(`${service} service stopped`);
      setTimeout(() => setSuccess(null), 3000);
      setTimeout(fetchStatus, 1000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingFn(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await fetchStatus();
    setSuccess('Status refreshed');
    setTimeout(() => setSuccess(null), 2000);
  };

  // Count running services for each category
  const getRAGServiceCount = () => {
    const running = (status?.embeddings?.running ? 1 : 0) + (status?.reranker?.running ? 1 : 0);
    return { running, total: 2 };
  };

  const getGraniteServiceCount = () => {
    const running = (status?.granite1?.running ? 1 : 0) + (status?.granite2?.running ? 1 : 0);
    return { running, total: 2 };
  };

  // Overall status
  const getOverallStatus = () => {
    const rag = getRAGServiceCount();
    const granite = getGraniteServiceCount();
    const totalRunning = rag.running + granite.running;
    const total = rag.total + granite.total;
    return { running: totalRunning, total };
  };

  // Loading state
  if (loading && !status) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const overallStatus = getOverallStatus();

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="GPU Services"
        subtitle="Manage GPU-based services for RAG and document extraction"
        actions={(
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Chip
              icon={overallStatus.running > 0 ? <HealthyIcon /> : <UnhealthyIcon />}
              label={`${overallStatus.running}/${overallStatus.total} Running`}
              color={overallStatus.running === overallStatus.total ? 'success' : overallStatus.running > 0 ? 'warning' : 'default'}
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

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab icon={<ServicesIcon />} iconPosition="start" label="Services" />
          <Tab icon={<KeyIcon />} iconPosition="start" label="API Keys" />
        </Tabs>
      </Paper>

      {/* Tab Panel: Services */}
      {activeTab === 0 && (
        <>
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

          {/* RAG Services Section */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <SectionHeader
          title="RAG Services (Infinity)"
          subtitle="Embedding and reranking services for Retrieval-Augmented Generation"
          icon={HubIcon}
          statusCount={getRAGServiceCount()}
        />
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <ServiceCard
              name="embeddings"
              displayName="Embeddings"
              description="Text embedding generation"
              status={status?.embeddings}
              model={status?.embeddings?.model || "BAAI/bge-base-en-v1.5"}
              containerName="infinity-embeddings"
              onStart={() => handleStartService('embeddings', setEmbeddingsLoading)}
              onStop={() => handleStopService('embeddings', setEmbeddingsLoading)}
              loading={embeddingsLoading}
              disabled={rerankerLoading || granite1Loading || granite2Loading}
              icon={TextFieldsIcon}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <ServiceCard
              name="reranker"
              displayName="Reranker"
              description="Document reranking for improved search"
              status={status?.reranker}
              model={status?.reranker?.model || "BAAI/bge-reranker-v2-m3"}
              containerName="infinity-reranker"
              onStart={() => handleStartService('reranker', setRerankerLoading)}
              onStop={() => handleStopService('reranker', setRerankerLoading)}
              loading={rerankerLoading}
              disabled={embeddingsLoading || granite1Loading || granite2Loading}
              icon={HubIcon}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Extraction Services Section */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <SectionHeader
          title="Extraction Services (Granite)"
          subtitle="Language model services for document extraction and processing"
          icon={DocumentIcon}
          statusCount={getGraniteServiceCount()}
        />
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <ServiceCard
              name="granite1"
              displayName="Granite 1"
              description="Primary extraction LLM instance"
              status={status?.granite1}
              model={status?.granite1?.model || "ibm-granite/granite-3.1-8b-instruct"}
              containerName="granite1"
              onStart={() => handleStartService('granite1', setGranite1Loading)}
              onStop={() => handleStopService('granite1', setGranite1Loading)}
              loading={granite1Loading}
              disabled={embeddingsLoading || rerankerLoading || granite2Loading}
              icon={DocumentIcon}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <ServiceCard
              name="granite2"
              displayName="Granite 2"
              description="Secondary extraction LLM instance"
              status={status?.granite2}
              model={status?.granite2?.model || "ibm-granite/granite-3.1-8b-instruct"}
              containerName="granite2"
              onStart={() => handleStartService('granite2', setGranite2Loading)}
              onStop={() => handleStopService('granite2', setGranite2Loading)}
              loading={granite2Loading}
              disabled={embeddingsLoading || rerankerLoading || granite1Loading}
              icon={DocumentIcon}
            />
          </Grid>
        </Grid>
      </Paper>

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

        {/* Infinity Idle Timeout */}
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2, fontWeight: 600 }}>
          Infinity Services (RAG)
        </Typography>
        <Grid container spacing={3} alignItems="center" sx={{ mb: 3 }}>
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
              value={infinityIdleTimeoutInput}
              onChange={(e) => setInfinityIdleTimeoutInput(e.target.value)}
              inputProps={{ min: 60, max: 86400 }}
              helperText="Default: 1800 (30 minutes)"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              disabled={savingInfinityTimeout || infinityIdleTimeoutInput === String(infinityIdleTimeout)}
              startIcon={savingInfinityTimeout ? <CircularProgress size={16} /> : null}
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
              Save
            </Button>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Granite Idle Timeout */}
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 2, fontWeight: 600 }}>
          Granite Services (Extraction)
        </Typography>
        <Grid container spacing={3} alignItems="center" sx={{ mb: 3 }}>
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
              value={graniteIdleTimeoutInput}
              onChange={(e) => setGraniteIdleTimeoutInput(e.target.value)}
              inputProps={{ min: 60, max: 86400 }}
              helperText="Default: 300 (5 minutes)"
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <Button
              variant="contained"
              disabled={savingGraniteTimeout || graniteIdleTimeoutInput === String(graniteIdleTimeout)}
              startIcon={savingGraniteTimeout ? <CircularProgress size={16} /> : null}
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
              Save
            </Button>
          </Grid>
        </Grid>

        <Divider sx={{ my: 3 }} />

        {/* Summary Info */}
        <Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <strong>Infinity Idle Timeout:</strong> {infinityIdleTimeout} seconds ({Math.floor(infinityIdleTimeout / 60)} minutes)
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            <strong>Granite Idle Timeout:</strong> {graniteIdleTimeout} seconds ({Math.floor(graniteIdleTimeout / 60)} minutes)
          </Typography>
          <Typography variant="body2" color="text.secondary">
            <strong>Last Updated:</strong> {status?.last_updated ? new Date(status.last_updated).toLocaleString() : 'N/A'}
          </Typography>
        </Box>
      </Paper>
        </>
      )}

      {/* Tab Panel: API Keys */}
      {activeTab === 1 && (
        <React.Suspense fallback={
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        }>
          <GraniteApiKeysPanel />
        </React.Suspense>
      )}
    </Box>
  );
};

export default GPUServicesManagement;
