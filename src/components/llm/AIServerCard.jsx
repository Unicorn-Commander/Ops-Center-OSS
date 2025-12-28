import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Switch,
  Button,
  CircularProgress,
  Tooltip,
  Divider,
  Stack
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Storage as ServerIcon
} from '@mui/icons-material';

const AIServerCard = ({ server, onEdit, onDelete, onToggle, onTest }) => {
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await onTest(server.id);
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setIsTesting(false);
    }
  };

  const getStatusColor = () => {
    if (server.status === 'healthy') return 'success';
    if (server.status === 'degraded') return 'warning';
    return 'error';
  };

  const getStatusIcon = () => {
    if (server.status === 'healthy') return <CheckCircleIcon fontSize="small" />;
    if (server.status === 'degraded') return <WarningIcon fontSize="small" />;
    return <ErrorIcon fontSize="small" />;
  };

  const getTypeColor = (type) => {
    const colors = {
      vllm: 'primary',
      ollama: 'secondary',
      'llama.cpp': 'info',
      'openai-compatible': 'success'
    };
    return colors[type] || 'default';
  };

  return (
    <Card
      sx={{
        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(139, 92, 246, 0.2)',
        transition: 'all 0.3s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 8px 24px rgba(139, 92, 246, 0.3)'
        }
      }}
    >
      <CardContent>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flex: 1 }}>
            <Box
              sx={{
                width: 48,
                height: 48,
                borderRadius: 2,
                background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            >
              <ServerIcon sx={{ color: 'white', fontSize: 28 }} />
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                {server.name}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  label={server.type}
                  color={getTypeColor(server.type)}
                  size="small"
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
                <Chip
                  icon={getStatusIcon()}
                  label={server.status}
                  color={getStatusColor()}
                  size="small"
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              </Box>
            </Box>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title={server.enabled ? 'Disable' : 'Enable'}>
              <Switch
                checked={server.enabled}
                onChange={() => onToggle(server.id, !server.enabled)}
                color="primary"
              />
            </Tooltip>
            <Tooltip title="Test Connection">
              <IconButton
                onClick={handleTest}
                disabled={isTesting}
                sx={{
                  color: 'primary.main',
                  '&:hover': { background: 'rgba(139, 92, 246, 0.1)' }
                }}
              >
                {isTesting ? <CircularProgress size={20} /> : <TestIcon />}
              </IconButton>
            </Tooltip>
            <Tooltip title="Edit">
              <IconButton
                onClick={() => onEdit(server)}
                sx={{
                  color: 'primary.main',
                  '&:hover': { background: 'rgba(139, 92, 246, 0.1)' }
                }}
              >
                <EditIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Delete">
              <IconButton
                onClick={() => onDelete(server.id)}
                sx={{
                  color: 'error.main',
                  '&:hover': { background: 'rgba(239, 68, 68, 0.1)' }
                }}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        {/* Server URL */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            Base URL
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              background: 'rgba(0, 0, 0, 0.2)',
              padding: '4px 8px',
              borderRadius: 1
            }}
          >
            {server.base_url}
          </Typography>
        </Box>

        {/* Model Path (if applicable) */}
        {server.model_path && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
              Model Path
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontFamily: 'monospace',
                background: 'rgba(0, 0, 0, 0.2)',
                padding: '4px 8px',
                borderRadius: 1
              }}
            >
              {server.model_path}
            </Typography>
          </Box>
        )}

        {/* Usage Options */}
        {server.enabled && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Enabled For
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {server.use_for_chat && (
                <Chip label="Chat Inference" size="small" color="primary" variant="outlined" />
              )}
              {server.use_for_embeddings && (
                <Chip label="Embeddings" size="small" color="secondary" variant="outlined" />
              )}
              {server.use_for_reranking && (
                <Chip label="Reranking" size="small" color="info" variant="outlined" />
              )}
            </Stack>
          </Box>
        )}

        {/* Available Models */}
        {server.available_models && server.available_models.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Available Models ({server.available_models.length})
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
              {server.available_models.slice(0, 3).map((model, idx) => (
                <Chip
                  key={idx}
                  label={model}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.65rem',
                    background: 'rgba(139, 92, 246, 0.1)'
                  }}
                />
              ))}
              {server.available_models.length > 3 && (
                <Chip
                  label={`+${server.available_models.length - 3} more`}
                  size="small"
                  sx={{
                    height: 20,
                    fontSize: '0.65rem',
                    background: 'rgba(236, 72, 153, 0.1)'
                  }}
                />
              )}
            </Box>
          </Box>
        )}

        {/* Test Result */}
        {testResult && (
          <Box
            sx={{
              mt: 2,
              pt: 2,
              borderTop: '1px solid rgba(139, 92, 246, 0.2)'
            }}
          >
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                padding: 1.5,
                borderRadius: 1,
                background: testResult.success
                  ? 'rgba(34, 197, 94, 0.1)'
                  : 'rgba(239, 68, 68, 0.1)'
              }}
            >
              {testResult.success ? (
                <CheckCircleIcon sx={{ color: 'success.main' }} />
              ) : (
                <ErrorIcon sx={{ color: 'error.main' }} />
              )}
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {testResult.success ? 'Connection successful!' : 'Connection failed'}
                </Typography>
                {testResult.message && (
                  <Typography variant="caption" color="text.secondary">
                    {testResult.message}
                  </Typography>
                )}
                {testResult.error && (
                  <Typography variant="caption" color="error.main">
                    {testResult.error}
                  </Typography>
                )}
              </Box>
            </Box>
          </Box>
        )}

        {/* Last Health Check */}
        {server.last_health_check && (
          <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid rgba(139, 92, 246, 0.2)' }}>
            <Typography variant="caption" color="text.secondary">
              Last health check: {new Date(server.last_health_check).toLocaleString()}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default AIServerCard;
