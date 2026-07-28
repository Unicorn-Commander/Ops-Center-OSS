import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Alert,
  CircularProgress,
  Box,
  InputAdornment,
  IconButton,
  Chip,
  Typography,
} from '@mui/material';
import {
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';

const EditSettingModal = ({ open, onClose, setting, onSave }) => {
  const isEdit = setting !== null;

  // Form state
  const [formData, setFormData] = useState({
    key: '',
    value: '',
    description: '',
    category: 'security',
    sensitive: false,
  });

  // UI state
  const [showValue, setShowValue] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [validation, setValidation] = useState({ key: true, value: true });

  // Reset form when modal opens/closes or setting changes
  useEffect(() => {
    if (open) {
      if (setting) {
        setFormData({
          key: setting.key || '',
          value: setting.value || '',
          description: setting.description || '',
          category: setting.category || 'security',
          sensitive: setting.sensitive || setting.is_sensitive || false,
        });
      } else {
        setFormData({
          key: '',
          value: '',
          description: '',
          category: 'security',
          sensitive: false,
        });
      }
      setShowValue(false);
      setError(null);
      setValidation({ key: true, value: true });
    }
  }, [open, setting]);

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));

    // Real-time validation
    if (field === 'key') {
      // Key must be UPPERCASE_WITH_UNDERSCORES
      const isValid = /^[A-Z][A-Z0-9_]*$/.test(value);
      setValidation((prev) => ({ ...prev, key: isValid || value === '' }));
    }
    if (field === 'value') {
      setValidation((prev) => ({ ...prev, value: value.trim() !== '' }));
    }
  };

  const handleSubmit = async () => {
    // Validate
    if (!formData.key.trim() || !formData.value.trim()) {
      setError('Key and value are required');
      return;
    }

    if (!validation.key) {
      setError('Key must be uppercase with underscores (e.g., MY_API_KEY)');
      return;
    }

    setSaving(true);
    setError(null);

    try {
      await onSave(formData);
      // Don't close here - let parent handle it after successful save
    } catch (err) {
      setError(err.message || 'Failed to save setting');
      setSaving(false);
    }
  };

  const handleClose = () => {
    if (!saving) {
      onClose();
    }
  };

  // Pre-defined common settings
  const commonSettings = {
    security: [
      { key: 'BYOK_ENCRYPTION_KEY', description: 'Encryption key for BYOK (Bring Your Own Key)' },
      { key: 'JWT_SECRET_KEY', description: 'Secret key for JWT token signing' },
      { key: 'SESSION_SECRET', description: 'Session encryption secret' },
    ],
    billing: [
      { key: 'STRIPE_SECRET_KEY', description: 'Stripe API secret key' },
      { key: 'STRIPE_PUBLISHABLE_KEY', description: 'Stripe publishable key' },
      { key: 'LAGO_API_KEY', description: 'Lago billing API key' },
      { key: 'LAGO_API_URL', description: 'Lago API endpoint URL' },
    ],
    llm: [
      { key: 'OPENROUTER_API_KEY', description: 'OpenRouter API key for LLM access' },
      { key: 'OPENAI_API_KEY', description: 'OpenAI API key' },
      { key: 'ANTHROPIC_API_KEY', description: 'Anthropic Claude API key' },
      { key: 'LITELLM_MASTER_KEY', description: 'LiteLLM proxy master key' },
    ],
    email: [
      { key: 'SMTP_USERNAME', description: 'SMTP server username' },
      { key: 'SMTP_PASSWORD', description: 'SMTP server password' },
      { key: 'SMTP_HOST', description: 'SMTP server hostname' },
      { key: 'SMTP_PORT', description: 'SMTP server port' },
    ],
    storage: [
      { key: 'AWS_ACCESS_KEY_ID', description: 'AWS access key for S3 storage' },
      { key: 'AWS_SECRET_ACCESS_KEY', description: 'AWS secret access key' },
      { key: 'S3_BUCKET_NAME', description: 'S3 bucket name for file storage' },
    ],
  };

  const handleQuickFill = (template) => {
    setFormData((prev) => ({
      ...prev,
      key: template.key,
      description: template.description,
      sensitive: template.key.includes('KEY') || template.key.includes('SECRET') || template.key.includes('PASSWORD'),
    }));
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {isEdit ? 'Edit System Setting' : 'Add New System Setting'}
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Quick Templates (only for new settings) */}
        {!isEdit && formData.category && commonSettings[formData.category] && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              Quick Fill:
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              {commonSettings[formData.category].map((template) => (
                <Chip
                  key={template.key}
                  label={template.key}
                  size="small"
                  onClick={() => handleQuickFill(template)}
                  clickable
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Category */}
        <FormControl fullWidth sx={{ mb: 2 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={formData.category}
            onChange={(e) => handleChange('category', e.target.value)}
            label="Category"
          >
            <MenuItem value="security">Security</MenuItem>
            <MenuItem value="billing">Billing</MenuItem>
            <MenuItem value="llm">LLM</MenuItem>
            <MenuItem value="email">Email</MenuItem>
            <MenuItem value="storage">Storage</MenuItem>
          </Select>
        </FormControl>

        {/* Key */}
        <TextField
          fullWidth
          label="Key"
          value={formData.key}
          onChange={(e) => handleChange('key', e.target.value.toUpperCase())}
          placeholder="MY_API_KEY"
          disabled={isEdit} // Can't change key on edit
          error={!validation.key}
          helperText={!validation.key ? 'Use UPPERCASE_WITH_UNDERSCORES format' : 'Environment variable name'}
          sx={{ mb: 2 }}
          InputProps={{
            endAdornment: validation.key && formData.key ? (
              <InputAdornment position="end">
                <CheckCircleIcon color="success" fontSize="small" />
              </InputAdornment>
            ) : null,
          }}
        />

        {/* Value */}
        <TextField
          fullWidth
          label="Value"
          value={formData.value}
          onChange={(e) => handleChange('value', e.target.value)}
          type={showValue ? 'text' : 'password'}
          placeholder="Enter value..."
          error={!validation.value}
          helperText={!validation.value ? 'Value is required' : ''}
          sx={{ mb: 2 }}
          InputProps={{
            endAdornment: (
              <InputAdornment position="end">
                <IconButton onClick={() => setShowValue(!showValue)} edge="end">
                  {showValue ? <VisibilityOffIcon /> : <VisibilityIcon />}
                </IconButton>
              </InputAdornment>
            ),
          }}
        />

        {/* Description */}
        <TextField
          fullWidth
          label="Description"
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          placeholder="Brief description of this setting..."
          multiline
          rows={2}
          sx={{ mb: 2 }}
        />

        {/* Sensitive toggle */}
        <FormControlLabel
          control={
            <Switch
              checked={formData.sensitive}
              onChange={(e) => handleChange('sensitive', e.target.checked)}
              color="warning"
            />
          }
          label="Sensitive value (mask in UI)"
        />

        {formData.sensitive && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Sensitive values will be masked in the UI and only show the last 8 characters
          </Alert>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={saving}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={saving || !validation.key || !validation.value}
          startIcon={saving && <CircularProgress size={16} />}
        >
          {saving ? 'Saving...' : isEdit ? 'Update' : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default EditSettingModal;
