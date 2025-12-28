import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  IconButton,
  Switch,
  CircularProgress,
  Tooltip,
  Divider,
  LinearProgress
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';

// Provider logos/icons mapping
const providerLogos = {
  openrouter: '🔀',
  openai: '🤖',
  anthropic: '🟣',
  google: '🔵',
  cohere: '🟢',
  huggingface: '🤗',
  together: '🤝',
  groq: '⚡'
};

const providerColors = {
  openrouter: '#6366f1',
  openai: '#10a37f',
  anthropic: '#8b5cf6',
  google: '#4285f4',
  cohere: '#22c55e',
  huggingface: '#fbbf24',
  together: '#ec4899',
  groq: '#f59e0b'
};

const APIKeyCard = ({ apiKey, onEdit, onDelete, onToggle, onTest }) => {
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [showKey, setShowKey] = useState(false);

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      const result = await onTest(apiKey.id);
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, error: error.message });
    } finally {
      setIsTesting(false);
    }
  };

  const maskApiKey = (key) => {
    if (!key) return '••••••••••••••••';
    if (showKey) return key;
    const prefix = key.substring(0, 7);
    const suffix = key.substring(key.length - 4);
    return `${prefix}${'•'.repeat(Math.max(0, key.length - 11))}${suffix}`;
  };

  const getStatusColor = () => {
    if (apiKey.status === 'active') return 'success';
    if (apiKey.status === 'error') return 'error';
    return 'default';
  };

  const getStatusLabel = () => {
    if (apiKey.status === 'active') return 'Active';
    if (apiKey.status === 'error') return 'Error';
    return 'Inactive';
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  const formatCost = (cost) => {
    if (!cost) return '$0.00';
    return `$${cost.toFixed(2)}`;
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
                background: `linear-gradient(135deg, ${providerColors[apiKey.provider] || '#8b5cf6'} 0%, ${providerColors[apiKey.provider] || '#ec4899'} 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '28px'
              }}
            >
              {providerLogos[apiKey.provider] || '🔑'}
            </Box>
            <Box sx={{ flex: 1 }}>
              <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5, textTransform: 'capitalize' }}>
                {apiKey.provider}
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {apiKey.key_name && (
                  <Typography variant="caption" color="text.secondary">
                    {apiKey.key_name}
                  </Typography>
                )}
                <Chip
                  icon={apiKey.status === 'active' ? <CheckCircleIcon fontSize="small" /> : <ErrorIcon fontSize="small" />}
                  label={getStatusLabel()}
                  color={getStatusColor()}
                  size="small"
                  sx={{ height: 20, fontSize: '0.7rem' }}
                />
              </Box>
            </Box>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Tooltip title={apiKey.enabled ? 'Disable' : 'Enable'}>
              <Switch
                checked={apiKey.enabled}
                onChange={() => onToggle(apiKey.id, !apiKey.enabled)}
                color="primary"
              />
            </Tooltip>
            <Tooltip title="Test Key">
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
                onClick={() => onEdit(apiKey)}
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
                onClick={() => onDelete(apiKey.id)}
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

        {/* API Key Display */}
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
            API Key
          </Typography>
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              background: 'rgba(0, 0, 0, 0.2)',
              padding: '8px 12px',
              borderRadius: 1
            }}
          >
            <Typography
              variant="body2"
              sx={{
                fontFamily: 'monospace',
                flex: 1,
                fontSize: '0.85rem'
              }}
            >
              {maskApiKey(apiKey.api_key)}
            </Typography>
            <IconButton
              size="small"
              onClick={() => setShowKey(!showKey)}
              sx={{
                color: 'text.secondary',
                '&:hover': { color: 'primary.main' }
              }}
            >
              {showKey ? <VisibilityOffIcon fontSize="small" /> : <VisibilityIcon fontSize="small" />}
            </IconButton>
          </Box>
        </Box>

        {/* Usage Statistics */}
        {apiKey.usage && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
              Usage Statistics
            </Typography>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: 2,
                padding: 1.5,
                borderRadius: 1,
                background: 'rgba(139, 92, 246, 0.05)'
              }}
            >
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  {formatNumber(apiKey.usage.requests || 0)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Requests
                </Typography>
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'secondary.main' }}>
                  {formatNumber(apiKey.usage.tokens || 0)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Tokens
                </Typography>
              </Box>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, color: 'success.main' }}>
                  {formatCost(apiKey.usage.cost || 0)}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Cost
                </Typography>
              </Box>
            </Box>
          </Box>
        )}

        {/* Test Result */}
        {testResult && (
          <Box
            sx={{
              mb: 2,
              padding: 1.5,
              borderRadius: 1,
              background: testResult.success
                ? 'rgba(34, 197, 94, 0.1)'
                : 'rgba(239, 68, 68, 0.1)'
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              {testResult.success ? (
                <CheckCircleIcon sx={{ color: 'success.main' }} />
              ) : (
                <ErrorIcon sx={{ color: 'error.main' }} />
              )}
              <Box sx={{ flex: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {testResult.success ? 'API key is valid!' : 'API key validation failed'}
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

        {/* Last Used */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', pt: 2, borderTop: '1px solid rgba(139, 92, 246, 0.2)' }}>
          <Typography variant="caption" color="text.secondary">
            {apiKey.last_used ? `Last used: ${new Date(apiKey.last_used).toLocaleString()}` : 'Never used'}
          </Typography>
          {apiKey.created_at && (
            <Typography variant="caption" color="text.secondary">
              Added: {new Date(apiKey.created_at).toLocaleDateString()}
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );
};

export default APIKeyCard;
