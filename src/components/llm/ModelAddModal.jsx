import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  MenuItem,
  Box,
  Alert
} from '@mui/material';

/**
 * ModelAddModal Component
 *
 * Modal for adding a new model to the registry
 */
export default function ModelAddModal({ open, onClose, onAdd }) {
  const [formData, setFormData] = useState({
    name: '',
    provider: 'vllm',
    endpoint: '',
    api_key: '',
    context_length: 4096,
    cost_per_input_token: 0.0,
    cost_per_output_token: 0.0,
    config: {}
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const providers = [
    { value: 'vllm', label: 'vLLM' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'cohere', label: 'Cohere' },
    { value: 'openrouter', label: 'OpenRouter' },
    { value: 'byok', label: 'BYOK' },
    { value: 'custom', label: 'Custom' }
  ];

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    });
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      // Validate required fields
      if (!formData.name) {
        throw new Error('Model name is required');
      }

      await onAdd(formData);
      handleClose();
    } catch (err) {
      setError(err.message || 'Failed to add model');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      name: '',
      provider: 'vllm',
      endpoint: '',
      api_key: '',
      context_length: 4096,
      cost_per_input_token: 0.0,
      cost_per_output_token: 0.0,
      config: {}
    });
    setError('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add New Model</DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}

          <TextField
            label="Model Name"
            value={formData.name}
            onChange={handleChange('name')}
            required
            fullWidth
            placeholder="e.g., gpt-4o-mini, qwen2.5-32b"
          />

          <TextField
            select
            label="Provider"
            value={formData.provider}
            onChange={handleChange('provider')}
            required
            fullWidth
          >
            {providers.map((option) => (
              <MenuItem key={option.value} value={option.value}>
                {option.label}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="Endpoint URL (optional)"
            value={formData.endpoint}
            onChange={handleChange('endpoint')}
            fullWidth
            placeholder="http://unicorn-vllm:8000"
            helperText="Leave empty to use default provider endpoint"
          />

          <TextField
            label="API Key (optional)"
            value={formData.api_key}
            onChange={handleChange('api_key')}
            fullWidth
            type="password"
            placeholder="sk-..."
          />

          <TextField
            label="Context Length"
            value={formData.context_length}
            onChange={handleChange('context_length')}
            type="number"
            fullWidth
            helperText="Maximum context window in tokens"
          />

          <TextField
            label="Cost per Input Token ($)"
            value={formData.cost_per_input_token}
            onChange={handleChange('cost_per_input_token')}
            type="number"
            inputProps={{ step: '0.000001' }}
            fullWidth
            helperText="e.g., 0.00001 for $0.01/1K tokens"
          />

          <TextField
            label="Cost per Output Token ($)"
            value={formData.cost_per_output_token}
            onChange={handleChange('cost_per_output_token')}
            type="number"
            inputProps={{ step: '0.000001' }}
            fullWidth
            helperText="e.g., 0.00003 for $0.03/1K tokens"
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {loading ? 'Adding...' : 'Add Model'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
