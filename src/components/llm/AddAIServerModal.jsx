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
  FormGroup,
  IconButton
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';

const serverTypes = [
  { value: 'vllm', label: 'vLLM', description: 'Fast inference for large language models' },
  { value: 'ollama', label: 'Ollama', description: 'Run Llama 2, Code Llama, and other models' },
  { value: 'llama.cpp', label: 'llama.cpp', description: 'CPU-optimized inference engine' },
  { value: 'openai-compatible', label: 'OpenAI-compatible', description: 'Any OpenAI-compatible API' }
];

const AddAIServerModal = ({ open, onClose, onSave, editServer = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    type: 'vllm',
    base_url: '',
    api_key: '',
    model_path: '',
    enabled: true,
    use_for_chat: true,
    use_for_embeddings: false,
    use_for_reranking: false
  });

  const [errors, setErrors] = useState({});
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    if (editServer) {
      setFormData({
        name: editServer.name || '',
        type: editServer.type || 'vllm',
        base_url: editServer.base_url || '',
        api_key: editServer.api_key || '',
        model_path: editServer.model_path || '',
        enabled: editServer.enabled !== false,
        use_for_chat: editServer.use_for_chat !== false,
        use_for_embeddings: editServer.use_for_embeddings || false,
        use_for_reranking: editServer.use_for_reranking || false
      });
    } else {
      // Reset form for new server
      setFormData({
        name: '',
        type: 'vllm',
        base_url: '',
        api_key: '',
        model_path: '',
        enabled: true,
        use_for_chat: true,
        use_for_embeddings: false,
        use_for_reranking: false
      });
    }
    setErrors({});
    setTestResult(null);
  }, [editServer, open]);

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

    if (!formData.name.trim()) {
      newErrors.name = 'Server name is required';
    }

    if (!formData.base_url.trim()) {
      newErrors.base_url = 'Base URL is required';
    } else {
      try {
        new URL(formData.base_url);
      } catch (e) {
        newErrors.base_url = 'Invalid URL format';
      }
    }

    if (formData.type === 'vllm' && !formData.model_path.trim()) {
      newErrors.model_path = 'Model path is required for vLLM servers';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleTestConnection = async () => {
    if (!validateForm()) {
      return;
    }

    setIsTesting(true);
    setTestResult(null);

    try {
      // Simulate API call to test connection
      const response = await fetch('/api/v1/llm-config/servers/test-connection', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          base_url: formData.base_url,
          api_key: formData.api_key,
          type: formData.type
        })
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setTestResult({
          success: true,
          message: result.message || 'Connection successful!',
          models: result.models || []
        });
      } else {
        setTestResult({
          success: false,
          error: result.error || 'Connection test failed'
        });
      }
    } catch (error) {
      setTestResult({
        success: false,
        error: error.message || 'Failed to test connection'
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
      id: editServer?.id
    });
  };

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
          {editServer ? 'Edit AI Server' : 'Add AI Server'}
        </Typography>
        <IconButton onClick={onClose} size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent sx={{ mt: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
          {/* Server Name */}
          <TextField
            label="Server Name"
            value={formData.name}
            onChange={handleChange('name')}
            error={!!errors.name}
            helperText={errors.name || 'e.g., "Production vLLM" or "Local Ollama"'}
            fullWidth
            required
          />

          {/* Server Type */}
          <FormControl fullWidth required>
            <InputLabel>Server Type</InputLabel>
            <Select
              value={formData.type}
              onChange={handleChange('type')}
              label="Server Type"
            >
              {serverTypes.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box>
                    <Typography variant="body1">{type.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {type.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {/* Base URL */}
          <TextField
            label="Base URL"
            value={formData.base_url}
            onChange={handleChange('base_url')}
            error={!!errors.base_url}
            helperText={errors.base_url || 'e.g., http://localhost:8000 or http://unicorn-vllm:8000'}
            fullWidth
            required
            placeholder="http://localhost:8000"
          />

          {/* API Key (optional) */}
          <TextField
            label="API Key (Optional)"
            value={formData.api_key}
            onChange={handleChange('api_key')}
            type="password"
            helperText="Only required if the server endpoint is protected"
            fullWidth
          />

          {/* Model Path (conditional) */}
          {(formData.type === 'vllm' || formData.type === 'llama.cpp') && (
            <TextField
              label="Model Path"
              value={formData.model_path}
              onChange={handleChange('model_path')}
              error={!!errors.model_path}
              helperText={errors.model_path || 'e.g., Qwen/Qwen2.5-32B-Instruct-AWQ'}
              fullWidth
              required={formData.type === 'vllm'}
              placeholder="HuggingFace model path or local path"
            />
          )}

          {/* Usage Options */}
          <Box
            sx={{
              padding: 2,
              borderRadius: 1,
              background: 'rgba(139, 92, 246, 0.05)',
              border: '1px solid rgba(139, 92, 246, 0.1)'
            }}
          >
            <Typography variant="subtitle2" sx={{ mb: 1.5, fontWeight: 600 }}>
              Use this server for:
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.use_for_chat}
                    onChange={handleChange('use_for_chat')}
                    color="primary"
                  />
                }
                label="Chat Inference"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.use_for_embeddings}
                    onChange={handleChange('use_for_embeddings')}
                    color="secondary"
                  />
                }
                label="Embeddings Generation"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.use_for_reranking}
                    onChange={handleChange('use_for_reranking')}
                    color="info"
                  />
                }
                label="Reranking"
              />
            </FormGroup>
          </Box>

          {/* Enable Server */}
          <FormControlLabel
            control={
              <Checkbox
                checked={formData.enabled}
                onChange={handleChange('enabled')}
                color="primary"
              />
            }
            label="Enable this server for use in Ops-Center"
          />

          {/* Test Connection Button */}
          <Button
            variant="outlined"
            onClick={handleTestConnection}
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
            {isTesting ? 'Testing Connection...' : 'Test Connection'}
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
              {testResult.models && testResult.models.length > 0 && (
                <Box sx={{ mt: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    Found {testResult.models.length} model(s): {testResult.models.slice(0, 3).join(', ')}
                    {testResult.models.length > 3 && ` and ${testResult.models.length - 3} more`}
                  </Typography>
                </Box>
              )}
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
          {editServer ? 'Update Server' : 'Add Server'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddAIServerModal;
