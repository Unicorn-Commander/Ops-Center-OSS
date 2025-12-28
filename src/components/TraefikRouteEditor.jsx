import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  Box,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Typography,
  Alert,
  Chip,
  IconButton,
  Paper,
  Divider
} from '@mui/material';
import {
  PlusIcon,
  TrashIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import TraefikMiddlewareBuilder from './TraefikMiddlewareBuilder';

const steps = ['Basic Info', 'Backend Service', 'SSL Configuration', 'Middleware', 'Review'];

const TraefikRouteEditor = ({ open, onClose, route, onSave }) => {
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [services, setServices] = useState([]);

  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    path: '/',
    ruleType: 'prefix',
    service: '',
    customServiceUrl: '',
    loadBalancing: 'round-robin',
    ssl: true,
    certificateResolver: 'letsencrypt',
    forceHttps: true,
    middleware: [],
    status: 'active'
  });

  useEffect(() => {
    if (route) {
      setFormData({
        ...route
      });
    } else {
      // Reset form for new route
      setFormData({
        name: '',
        domain: '',
        path: '/',
        ruleType: 'prefix',
        service: '',
        customServiceUrl: '',
        loadBalancing: 'round-robin',
        ssl: true,
        certificateResolver: 'letsencrypt',
        forceHttps: true,
        middleware: [],
        status: 'active'
      });
    }
    setActiveStep(0);
    setError(null);

    if (open) {
      loadServices();
    }
  }, [route, open]);

  const loadServices = async () => {
    try {
      const response = await fetch('/api/v1/traefik/services', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setServices(data.services || []);
      }
    } catch (err) {
      console.error('Failed to load services:', err);
    }
  };

  const handleNext = () => {
    // Validation
    if (activeStep === 0) {
      if (!formData.name || !formData.domain) {
        setError('Name and domain are required');
        return;
      }
      // Validate domain format
      const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-_.]*[a-zA-Z0-9]$/;
      if (!domainRegex.test(formData.domain)) {
        setError('Invalid domain format');
        return;
      }
    } else if (activeStep === 1) {
      if (!formData.service && !formData.customServiceUrl) {
        setError('Please select a service or enter a custom URL');
        return;
      }
    }

    setError(null);
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
    setError(null);
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      await onSave(formData);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value
    }));
  };

  const renderStepContent = (step) => {
    switch (step) {
      case 0: // Basic Info
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <TextField
              label="Route Name"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              fullWidth
              required
              helperText="A descriptive name for this route"
            />

            <TextField
              label="Domain"
              value={formData.domain}
              onChange={(e) => handleChange('domain', e.target.value)}
              fullWidth
              required
              placeholder="example.com"
              helperText="The domain this route will respond to"
            />

            <Box display="flex" gap={2}>
              <FormControl sx={{ flex: 1 }}>
                <InputLabel>Rule Type</InputLabel>
                <Select
                  value={formData.ruleType}
                  onChange={(e) => handleChange('ruleType', e.target.value)}
                  label="Rule Type"
                >
                  <MenuItem value="exact">Exact Match</MenuItem>
                  <MenuItem value="prefix">Path Prefix</MenuItem>
                  <MenuItem value="regex">Regular Expression</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="Path"
                value={formData.path}
                onChange={(e) => handleChange('path', e.target.value)}
                sx={{ flex: 1 }}
                placeholder="/"
                helperText={
                  formData.ruleType === 'exact'
                    ? 'Exact path to match'
                    : formData.ruleType === 'prefix'
                    ? 'Path prefix (e.g., /api)'
                    : 'Regular expression pattern'
                }
              />
            </Box>

            <Alert severity="info">
              This route will match requests to:{' '}
              <strong>
                {formData.domain}
                {formData.path}
              </strong>
            </Alert>
          </Box>
        );

      case 1: // Backend Service
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <FormControl fullWidth>
              <InputLabel>Select Service</InputLabel>
              <Select
                value={formData.service}
                onChange={(e) => handleChange('service', e.target.value)}
                label="Select Service"
              >
                <MenuItem value="">Custom URL</MenuItem>
                {services.map((service) => (
                  <MenuItem key={service.id} value={service.id}>
                    {service.name} ({service.url})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {!formData.service && (
              <TextField
                label="Custom Service URL"
                value={formData.customServiceUrl}
                onChange={(e) => handleChange('customServiceUrl', e.target.value)}
                fullWidth
                placeholder="http://service:8080"
                helperText="Enter the backend service URL (e.g., http://container-name:port)"
              />
            )}

            <FormControl fullWidth>
              <InputLabel>Load Balancing</InputLabel>
              <Select
                value={formData.loadBalancing}
                onChange={(e) => handleChange('loadBalancing', e.target.value)}
                label="Load Balancing"
              >
                <MenuItem value="round-robin">Round Robin</MenuItem>
                <MenuItem value="weighted">Weighted</MenuItem>
                <MenuItem value="least-connections">Least Connections</MenuItem>
              </Select>
            </FormControl>

            <Alert severity="info">
              Requests will be forwarded to:{' '}
              <strong>
                {formData.service
                  ? services.find((s) => s.id === formData.service)?.url || 'service'
                  : formData.customServiceUrl || 'backend service'}
              </strong>
            </Alert>
          </Box>
        );

      case 2: // SSL Configuration
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <FormControlLabel
              control={
                <Switch
                  checked={formData.ssl}
                  onChange={(e) => handleChange('ssl', e.target.checked)}
                />
              }
              label="Enable HTTPS"
            />

            {formData.ssl && (
              <>
                <FormControl fullWidth>
                  <InputLabel>Certificate Resolver</InputLabel>
                  <Select
                    value={formData.certificateResolver}
                    onChange={(e) => handleChange('certificateResolver', e.target.value)}
                    label="Certificate Resolver"
                  >
                    <MenuItem value="letsencrypt">Let's Encrypt (Automatic)</MenuItem>
                    <MenuItem value="custom">Custom Certificate</MenuItem>
                  </Select>
                </FormControl>

                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.forceHttps}
                      onChange={(e) => handleChange('forceHttps', e.target.checked)}
                    />
                  }
                  label="Force HTTPS Redirect"
                />

                <Alert severity="success">
                  SSL certificate will be automatically obtained from Let's Encrypt and renewed
                  before expiry.
                </Alert>
              </>
            )}

            {!formData.ssl && (
              <Alert severity="warning">
                HTTP-only routes are not recommended for production use. Enable HTTPS for secure
                communication.
              </Alert>
            )}
          </Box>
        );

      case 3: // Middleware
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <Typography variant="body2" color="text.secondary">
              Add middleware to process requests before they reach your backend service.
            </Typography>

            <TraefikMiddlewareBuilder
              middleware={formData.middleware}
              onChange={(middleware) => handleChange('middleware', middleware)}
            />

            {formData.middleware.length === 0 && (
              <Alert severity="info">
                No middleware configured. Requests will be forwarded directly to the backend
                service.
              </Alert>
            )}
          </Box>
        );

      case 4: // Review
        return (
          <Box display="flex" flexDirection="column" gap={3}>
            <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
              <Typography variant="subtitle2" gutterBottom>
                Route Configuration
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Name:
                  </Typography>
                  <Typography variant="body2">{formData.name}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Domain:
                  </Typography>
                  <Typography variant="body2">{formData.domain}</Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Rule:
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {formData.ruleType} {formData.path}
                  </Typography>
                </Box>
              </Box>
            </Paper>

            <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
              <Typography variant="subtitle2" gutterBottom>
                Backend Service
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Service:
                  </Typography>
                  <Typography variant="body2">
                    {formData.service
                      ? services.find((s) => s.id === formData.service)?.name || 'Unknown'
                      : 'Custom'}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    URL:
                  </Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {formData.service
                      ? services.find((s) => s.id === formData.service)?.url
                      : formData.customServiceUrl}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    Load Balancing:
                  </Typography>
                  <Typography variant="body2">{formData.loadBalancing}</Typography>
                </Box>
              </Box>
            </Paper>

            <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
              <Typography variant="subtitle2" gutterBottom>
                SSL Configuration
              </Typography>
              <Divider sx={{ my: 1 }} />
              <Box display="flex" flexDirection="column" gap={1}>
                <Box display="flex" justifyContent="space-between">
                  <Typography variant="body2" color="text.secondary">
                    HTTPS:
                  </Typography>
                  <Chip
                    label={formData.ssl ? 'Enabled' : 'Disabled'}
                    size="small"
                    color={formData.ssl ? 'success' : 'default'}
                  />
                </Box>
                {formData.ssl && (
                  <>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">
                        Certificate:
                      </Typography>
                      <Typography variant="body2">{formData.certificateResolver}</Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2" color="text.secondary">
                        Force HTTPS:
                      </Typography>
                      <Chip
                        label={formData.forceHttps ? 'Yes' : 'No'}
                        size="small"
                        color={formData.forceHttps ? 'success' : 'default'}
                      />
                    </Box>
                  </>
                )}
              </Box>
            </Paper>

            {formData.middleware.length > 0 && (
              <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                <Typography variant="subtitle2" gutterBottom>
                  Middleware ({formData.middleware.length})
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Box display="flex" flexWrap="wrap" gap={1}>
                  {formData.middleware.map((m, i) => (
                    <Chip key={i} label={m.type} size="small" />
                  ))}
                </Box>
              </Paper>
            )}

            <Alert severity="info" icon={<CheckCircleIcon style={{ width: 20, height: 20 }} />}>
              Review your configuration above. Click "Save Route" to apply these settings.
            </Alert>
          </Box>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {route ? 'Edit Route' : 'Create New Route'}
      </DialogTitle>

      <DialogContent>
        <Box sx={{ mt: 2 }}>
          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          {renderStepContent(activeStep)}
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        {activeStep > 0 && (
          <Button onClick={handleBack} disabled={loading}>
            Back
          </Button>
        )}
        {activeStep < steps.length - 1 ? (
          <Button variant="contained" onClick={handleNext} disabled={loading}>
            Next
          </Button>
        ) : (
          <Button variant="contained" onClick={handleSave} disabled={loading}>
            Save Route
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default TraefikRouteEditor;
