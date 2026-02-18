import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Checkbox,
  Box,
  Typography,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  Avatar
} from '@mui/material';
import {
  Close as CloseIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';

const providers = [
  {
    value: 'openrouter',
    label: 'OpenRouter',
    icon: '🔀',
    color: '#6366f1',
    description: 'Access 200+ models with one API',
    keyPrefix: 'sk-or-v1-'
  },
  {
    value: 'openai',
    label: 'OpenAI',
    icon: '🤖',
    color: '#10a37f',
    description: 'GPT-4, GPT-3.5, and more',
    keyPrefix: 'sk-'
  },
  {
    value: 'anthropic',
    label: 'Anthropic',
    icon: '🟣',
    color: '#8b5cf6',
    description: 'Claude 3 family',
    keyPrefix: 'sk-ant-'
  },
  {
    value: 'google',
    label: 'Google AI',
    icon: '🔵',
    color: '#4285f4',
    description: 'Gemini models',
    keyPrefix: ''
  },
  {
    value: 'cohere',
    label: 'Cohere',
    icon: '🟢',
    color: '#22c55e',
    description: 'Command and Embed models',
    keyPrefix: ''
  },
  {
    value: 'huggingface',
    label: 'HuggingFace',
    icon: '🤗',
    color: '#fbbf24',
    description: 'Inference API access',
    keyPrefix: 'hf_'
  },
  {
    value: 'together',
    label: 'Together AI',
    icon: '🤝',
    color: '#ec4899',
    description: 'Open-source models at scale',
    keyPrefix: ''
  },
  {
    value: 'groq',
    label: 'Groq',
    icon: '⚡',
    color: '#f59e0b',
    description: 'Ultra-fast LLM inference',
    keyPrefix: 'gsk_'
  }
];

const AddAPIKeyModal = ({ open, onClose, onSave, editApiKey = null }) => {
  const [formData, setFormData] = useState({
    provider: 'openrouter',
    api_key: '',
    key_name: '',
    enabled: true
  });

  const [errors, setErrors] = useState({});
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [showKey, setShowKey] = useState(false);

  useEffect(() => {
    if (editApiKey) {
      setFormData({
        provider: editApiKey.provider || 'openrouter',
        api_key: editApiKey.api_key || '',
        key_name: editApiKey.key_name || '',
        enabled: editApiKey.enabled !== false
      });
    } else {
      // Reset form for new API key
      setFormData({
        provider: 'openrouter',
        api_key: '',
        key_name: '',
        enabled: true
      });
    }
    setErrors({});
    setTestResult(null);
    setShowKey(false);
  }, [editApiKey, open]);

  const handleChange = (field) => (event) => {
    const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
    setFormData((prev) => ({
      ...prev,
      [field]: value
    }));
    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.api_key.trim()) {
      newErrors.api_key = 'API key is required';
    } else {
      const provider = providers.find((p) => p.value === formData.provider);
      if (provider?.keyPrefix && !formData.api_key.startsWith(provider.keyPrefix)) {
        newErrors.api_key = `${provider.label} keys typically start with "${provider.keyPrefix}"`;
      }
    }

    if (!formData.key_name.trim()) {
      newErrors.key_name = 'Please provide a name for this key';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleTestKey = async () => {
    if (!validateForm()) {
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      // Simulate API call to test key
      const response = await fetch('/api/v1/llm-config/api-keys/test-key', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          provider: formData.provider,
          api_key: formData.api_key
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setTestResult({
          success: true,
          message: result.message || 'API key is valid!',
          details: result.details
        });
      } else {
        setTestResult({
          success: false,
          error: result.error || 'API key validation failed'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        error: error.message || 'Failed to validate API key'
      });
    } finally {
      setIsTesting(false);
    }
  };

  const handleSave = () => {
    if (!validateForm()) {
      return;
    }

    onSave({
      ...formData,
      id: editApiKey?.id
    });
  };

  const selectedProvider = providers.find((p) => p.value === formData.provider);

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }
      }}
    >
      <DialogTitle
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          borderBottom: '1px solid rgba(139, 92, 246, 0.2)'
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          {editApiKey ? 'Edit API Key' : 'Add API Key'}
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {/* Provider Selection */}
          <FormControl fullWidth required>
            <InputLabel>Provider</InputLabel>
            <Select
              value={formData.provider}
              onChange={handleChange('provider')}
              label="Provider"
              renderValue={(value) => {
                const provider = providers.find((p) => p.value === value);
                return (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <span style={{ fontSize: '20px' }}>{provider?.icon}</span>
                    <span>{provider?.label}</span>
                  </Box>
                );
              }}
            >
              {providers.map((provider) => (
                <MenuItem key={provider.value} value={provider.value}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    <Avatar
                      sx={{
                        width: 40,
                        height: 40,
                        background: `linear-gradient(135deg, ${provider.color} 0%, ${provider.color}cc 100%)`,
                        fontSize: '20px'
                      }}
                    >
                      {provider.icon}
                    </Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography variant="body1" sx={{ fontWeight: 500 }}>
                        {provider.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {provider.description}
                      </Typography>
                    </Box>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Provider Info Banner */}
          {selectedProvider && (
            <Alert
              severity="info"
              icon={<span style={{ fontSize: '24px' }}>{selectedProvider.icon}</span>}
              sx={{
                background: `linear-gradient(135deg, ${selectedProvider.color}15 0%, ${selectedProvider.color}05 100%)`,
                border: `1px solid ${selectedProvider.color}30`
              }}
            >
              <Typography variant="body2">
                {selectedProvider.description}
              </Typography>
              {selectedProvider.keyPrefix && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                  API keys start with: <code>{selectedProvider.keyPrefix}</code>
                </Typography>
              )}
            </Alert>
          )}

          {/* Key Name */}
          <TextField
            label="Key Name"
            value={formData.key_name}
            onChange={handleChange('key_name')}
            error={!!errors.key_name}
            helperText={errors.key_name || 'A friendly name to identify this key (e.g., "Production Key" or "Aaron\'s Key")'}
            fullWidth
            required
            placeholder="e.g., Production API Key"
          />

          {/* API Key */}
          <TextField
            label="API Key"
            value={formData.api_key}
            onChange={handleChange('api_key')}
            error={!!errors.api_key}
            helperText={errors.api_key || `Enter your ${selectedProvider?.label} API key`}
            fullWidth
            required
            type={showKey ? 'text' : 'password'}
            placeholder={selectedProvider?.keyPrefix ? `${selectedProvider.keyPrefix}...` : 'Enter API key'}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowKey(!showKey)}
                    edge="end"
                    size="small"
                  >
                    {showKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                </InputAdornment>
              )
            }}
          />

          {/* Enable Key */}
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.enabled}
                onChange={handleChange('enabled')}
                color="primary"
              />
            }
            label="Enable this API key for use in Ops-Center"
          />

          {/* Test Key Button */}
          <Button
            variant="outlined"
            onClick={handleTestKey}
            disabled={isTesting}
            startIcon={isTesting ? <CircularProgress size={20} /> : null}
            sx={{
              borderColor: 'primary.main',
              color: 'primary.main',
              '&:hover': {
                borderColor: 'primary.light',
                background: 'rgba(139, 92, 246, 0.1)'
              }
            }}
          >
            {isTesting ? 'Testing API Key...' : 'Test API Key'}
          </Button>

          {/* Test Result */}
          {testResult && (
            <Alert
              severity={testResult.success ? 'success' : 'error'}
              onClose={() => setTestResult(null)}
            >
              <Typography variant="body2">
                {testResult.success ? testResult.message : testResult.error}
              </Typography>
              {testResult.details && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {JSON.stringify(testResult.details)}
                  </Typography>
                </Box>
              )}
            </Alert>
          )}

          {/* OpenRouter Pre-populate Notice */}
          {!editApiKey && formData.provider === 'openrouter' && !formData.api_key && (
            <Alert severity="success">
              <Typography variant="body2">
                <strong>Quick Start:</strong> We can pre-populate an OpenRouter key for testing.
              </Typography>
              <Button
                size="small"
                onClick={() => {
                  setFormData((prev) => ({
                    ...prev,
                    api_key: 'sk-or-v1-your-openrouter-key',
                    key_name: 'Default OpenRouter Key'
                  }));
                }}
                sx={{ mt: 1 }}
              >
                Use Default OpenRouter Key
              </Button>
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ padding: 2, borderTop: '1px solid rgba(139, 92, 246, 0.2)' }}>
        <Button onClick={onClose} sx={{ color: 'text.secondary' }}>
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          sx={{
            background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #7c3aed 0%, #db2777 100%)'
            }
          }}
        >
          {editApiKey ? 'Update Key' : 'Add Key'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddAPIKeyModal;
