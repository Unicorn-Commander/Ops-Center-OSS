/**
 * White Label Builder
 * Visual white-label customization interface for Ops-Center
 * Allows admins to customize branding (logo, colors, company name) with live preview
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Grid,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Divider,
  IconButton,
  Snackbar,
  Stack,
  Tooltip,
  InputAdornment
} from '@mui/material';
import {
  Upload as UploadIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Visibility as PreviewIcon,
  RestoreOutlined as ResetIcon,
  Palette as PaletteIcon,
  Business as BusinessIcon,
  Settings as SettingsIcon,
  Image as ImageIcon,
  Code as CodeIcon
} from '@mui/icons-material';

const WhiteLabelBuilder = () => {
  // Tab state
  const [currentTab, setCurrentTab] = useState(0);

  // Loading and error states
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');

  // Configuration state
  const [config, setConfig] = useState({
    companyName: '',
    companySubtitle: '',
    logoUrl: '',
    templateBase: 'default',
    primaryColor: '#6366f1',
    secondaryColor: '#8b5cf6',
    accentColor: '#ec4899',
    customDomain: '',
    hideAttribution: false,
    customCSS: ''
  });

  // Template options
  const [templates, setTemplates] = useState([]);

  // Color presets
  const [colorPresets, setColorPresets] = useState([]);

  // Logo upload state
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [uploadingLogo, setUploadingLogo] = useState(false);

  // ============================================
  // API Functions
  // ============================================

  const fetchConfig = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/white-label/config', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch white-label configuration');
      const data = await response.json();
      setConfig(data);
      setLogoPreview(data.logoUrl);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching config:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/admin/white-label/templates', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      console.error('Error fetching templates:', err);
    }
  };

  const fetchColorPresets = async () => {
    try {
      const response = await fetch('/api/v1/admin/white-label/colors/presets', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch color presets');
      const data = await response.json();
      setColorPresets(data);
    } catch (err) {
      console.error('Error fetching color presets:', err);
    }
  };

  const saveConfig = async () => {
    setSaving(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/white-label/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(config)
      });

      if (!response.ok) throw new Error('Failed to save configuration');

      setSuccessMessage('Configuration saved successfully!');
      await fetchConfig(); // Refresh config
    } catch (err) {
      setError(err.message);
      console.error('Error saving config:', err);
    } finally {
      setSaving(false);
    }
  };

  const uploadLogo = async () => {
    if (!logoFile) return;

    setUploadingLogo(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('logo', logoFile);

      const response = await fetch('/api/v1/admin/white-label/logo', {
        method: 'POST',
        credentials: 'include',
        body: formData
      });

      if (!response.ok) throw new Error('Failed to upload logo');

      const data = await response.json();
      setConfig(prev => ({ ...prev, logoUrl: data.logoUrl }));
      setLogoPreview(data.logoUrl);
      setSuccessMessage('Logo uploaded successfully!');
    } catch (err) {
      setError(err.message);
      console.error('Error uploading logo:', err);
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to reset to default configuration?')) return;

    setLoading(true);
    try {
      // Reset to defaults (you can implement a reset endpoint or use default values)
      const defaultConfig = {
        companyName: '',
        companySubtitle: '',
        logoUrl: '',
        templateBase: 'default',
        primaryColor: '#6366f1',
        secondaryColor: '#8b5cf6',
        accentColor: '#ec4899',
        customDomain: '',
        hideAttribution: false,
        customCSS: ''
      };
      setConfig(defaultConfig);
      setLogoPreview(null);
      setLogoFile(null);
      setSuccessMessage('Reset to default configuration');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // Event Handlers
  // ============================================

  const handleConfigChange = (field, value) => {
    setConfig(prev => ({ ...prev, [field]: value }));
  };

  const handleLogoFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setLogoFile(file);

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setLogoPreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const applyColorPreset = (preset) => {
    setConfig(prev => ({
      ...prev,
      primaryColor: preset.primary,
      secondaryColor: preset.secondary,
      accentColor: preset.accent
    }));
    setSuccessMessage(`Applied "${preset.name}" color preset`);
  };

  // ============================================
  // Lifecycle
  // ============================================

  useEffect(() => {
    fetchConfig();
    fetchTemplates();
    fetchColorPresets();
  }, []);

  // ============================================
  // Render Functions
  // ============================================

  const renderBrandingTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <BusinessIcon /> Company Information
      </Typography>

      <Stack spacing={3} sx={{ mt: 2 }}>
        <TextField
          fullWidth
          label="Company Name"
          value={config.companyName}
          onChange={(e) => handleConfigChange('companyName', e.target.value)}
          placeholder="Your Company Name"
          helperText="This will appear in the header and title"
        />

        <TextField
          fullWidth
          label="Company Subtitle / Tagline"
          value={config.companySubtitle}
          onChange={(e) => handleConfigChange('companySubtitle', e.target.value)}
          placeholder="Your tagline or subtitle"
          helperText="Optional subtitle that appears below the company name"
        />

        <Divider />

        <Box>
          <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <ImageIcon /> Company Logo
          </Typography>

          <Card variant="outlined" sx={{ mt: 2, p: 2 }}>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <input
                  accept="image/*"
                  style={{ display: 'none' }}
                  id="logo-upload"
                  type="file"
                  onChange={handleLogoFileChange}
                />
                <label htmlFor="logo-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<UploadIcon />}
                    fullWidth
                  >
                    Choose Logo File
                  </Button>
                </label>

                {logoFile && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Selected: {logoFile.name}
                    </Typography>
                    <Button
                      variant="contained"
                      onClick={uploadLogo}
                      disabled={uploadingLogo}
                      startIcon={uploadingLogo ? <CircularProgress size={20} /> : <SaveIcon />}
                      sx={{ mt: 1 }}
                    >
                      {uploadingLogo ? 'Uploading...' : 'Upload Logo'}
                    </Button>
                  </Box>
                )}
              </Grid>

              <Grid item xs={12} md={6}>
                {logoPreview ? (
                  <Box sx={{ textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Preview:
                    </Typography>
                    <Box
                      component="img"
                      src={logoPreview}
                      alt="Logo preview"
                      sx={{
                        maxWidth: '200px',
                        maxHeight: '100px',
                        objectFit: 'contain',
                        border: '1px solid',
                        borderColor: 'divider',
                        borderRadius: 1,
                        p: 1,
                        bgcolor: 'background.paper'
                      }}
                    />
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
                    <ImageIcon sx={{ fontSize: 48, opacity: 0.3 }} />
                    <Typography variant="body2">No logo uploaded</Typography>
                  </Box>
                )}
              </Grid>
            </Grid>
          </Card>
        </Box>

        <Divider />

        <FormControl fullWidth>
          <InputLabel>Template Base</InputLabel>
          <Select
            value={config.templateBase}
            onChange={(e) => handleConfigChange('templateBase', e.target.value)}
            label="Template Base"
          >
            <MenuItem value="default">Default</MenuItem>
            {templates.map((template) => (
              <MenuItem key={template.id} value={template.id}>
                {template.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>
    </Box>
  );

  const renderThemeTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <PaletteIcon /> Color Customization
      </Typography>

      {colorPresets.length > 0 && (
        <Box sx={{ mt: 2, mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Quick Presets
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {colorPresets.map((preset) => (
              <Chip
                key={preset.id}
                label={preset.name}
                onClick={() => applyColorPreset(preset)}
                sx={{
                  background: `linear-gradient(135deg, ${preset.primary} 0%, ${preset.secondary} 50%, ${preset.accent} 100%)`,
                  color: 'white',
                  fontWeight: 'bold',
                  '&:hover': {
                    opacity: 0.8
                  }
                }}
              />
            ))}
          </Stack>
        </Box>
      )}

      <Divider sx={{ my: 3 }} />

      <Stack spacing={3}>
        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Primary Color
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                type="color"
                value={config.primaryColor}
                onChange={(e) => handleConfigChange('primaryColor', e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Box
                        sx={{
                          width: 24,
                          height: 24,
                          bgcolor: config.primaryColor,
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1
                        }}
                      />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                value={config.primaryColor}
                onChange={(e) => handleConfigChange('primaryColor', e.target.value)}
                placeholder="#6366f1"
                InputProps={{
                  startAdornment: <InputAdornment position="start">#</InputAdornment>
                }}
              />
            </Grid>
          </Grid>
        </Box>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Secondary Color
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                type="color"
                value={config.secondaryColor}
                onChange={(e) => handleConfigChange('secondaryColor', e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Box
                        sx={{
                          width: 24,
                          height: 24,
                          bgcolor: config.secondaryColor,
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1
                        }}
                      />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                value={config.secondaryColor}
                onChange={(e) => handleConfigChange('secondaryColor', e.target.value)}
                placeholder="#8b5cf6"
                InputProps={{
                  startAdornment: <InputAdornment position="start">#</InputAdornment>
                }}
              />
            </Grid>
          </Grid>
        </Box>

        <Box>
          <Typography variant="subtitle2" gutterBottom>
            Accent Color
          </Typography>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                type="color"
                value={config.accentColor}
                onChange={(e) => handleConfigChange('accentColor', e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Box
                        sx={{
                          width: 24,
                          height: 24,
                          bgcolor: config.accentColor,
                          border: '1px solid',
                          borderColor: 'divider',
                          borderRadius: 1
                        }}
                      />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                value={config.accentColor}
                onChange={(e) => handleConfigChange('accentColor', e.target.value)}
                placeholder="#ec4899"
                InputProps={{
                  startAdornment: <InputAdornment position="start">#</InputAdornment>
                }}
              />
            </Grid>
          </Grid>
        </Box>
      </Stack>
    </Box>
  );

  const renderServicesTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom>
        Service Visibility
      </Typography>

      <Alert severity="info" sx={{ mt: 2 }}>
        Configure which services are visible to end users (coming soon in v2)
      </Alert>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
        This feature will allow you to:
      </Typography>
      <Box component="ul" sx={{ mt: 1, color: 'text.secondary' }}>
        <li>Show/hide specific services from the dashboard</li>
        <li>Reorder services in the navigation</li>
        <li>Create custom service groups</li>
        <li>Set default landing pages</li>
      </Box>
    </Box>
  );

  const renderAdvancedTab = () => (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SettingsIcon /> Advanced Settings
      </Typography>

      <Stack spacing={3} sx={{ mt: 2 }}>
        <TextField
          fullWidth
          label="Custom Domain"
          value={config.customDomain}
          onChange={(e) => handleConfigChange('customDomain', e.target.value)}
          placeholder="app.yourdomain.com"
          helperText="Configure your custom domain for white-label hosting"
        />

        <FormControlLabel
          control={
            <Switch
              checked={config.hideAttribution}
              onChange={(e) => handleConfigChange('hideAttribution', e.target.checked)}
            />
          }
          label="Hide 'Powered by' Attribution"
        />

        <Divider />

        <Box>
          <Typography variant="subtitle1" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CodeIcon /> Custom CSS
          </Typography>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Add custom CSS to further customize the appearance (optional)
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={8}
            value={config.customCSS}
            onChange={(e) => handleConfigChange('customCSS', e.target.value)}
            placeholder="/* Enter custom CSS here */
.custom-class {
  /* Your styles */
}"
            sx={{
              mt: 1,
              fontFamily: 'monospace',
              '& textarea': {
                fontFamily: 'monospace'
              }
            }}
          />
        </Box>
      </Stack>
    </Box>
  );

  const renderLivePreview = () => (
    <Paper
      elevation={3}
      sx={{
        position: 'sticky',
        top: 20,
        p: 3,
        background: `linear-gradient(135deg, ${config.primaryColor} 0%, ${config.secondaryColor} 100%)`,
        color: 'white',
        minHeight: '400px'
      }}
    >
      <Typography variant="overline" sx={{ opacity: 0.8 }}>
        Live Preview
      </Typography>

      <Box sx={{ mt: 3, textAlign: 'center' }}>
        {logoPreview ? (
          <Box
            component="img"
            src={logoPreview}
            alt="Logo preview"
            sx={{
              maxWidth: '200px',
              maxHeight: '80px',
              objectFit: 'contain',
              mb: 2,
              filter: 'drop-shadow(0 4px 6px rgba(0,0,0,0.3))'
            }}
          />
        ) : (
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              bgcolor: 'rgba(255,255,255,0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              mx: 'auto',
              mb: 2
            }}
          >
            <BusinessIcon sx={{ fontSize: 40 }} />
          </Box>
        )}

        <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold' }}>
          {config.companyName || 'Your Company Name'}
        </Typography>

        <Typography variant="subtitle1" sx={{ opacity: 0.9, mb: 4 }}>
          {config.companySubtitle || 'Your tagline here'}
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Box
            sx={{
              px: 3,
              py: 1.5,
              borderRadius: 2,
              bgcolor: config.accentColor,
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'scale(1.05)'
              }
            }}
          >
            Get Started
          </Box>

          <Box
            sx={{
              px: 3,
              py: 1.5,
              borderRadius: 2,
              border: '2px solid white',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              '&:hover': {
                transform: 'scale(1.05)',
                bgcolor: 'rgba(255,255,255,0.1)'
              }
            }}
          >
            Learn More
          </Box>
        </Box>

        <Box sx={{ mt: 4, pt: 3, borderTop: '1px solid rgba(255,255,255,0.2)' }}>
          <Typography variant="caption" sx={{ opacity: 0.7 }}>
            Color Palette Preview
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1, justifyContent: 'center' }}>
            <Tooltip title="Primary Color">
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 1,
                  bgcolor: config.primaryColor,
                  border: '2px solid white',
                  boxShadow: 2
                }}
              />
            </Tooltip>
            <Tooltip title="Secondary Color">
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 1,
                  bgcolor: config.secondaryColor,
                  border: '2px solid white',
                  boxShadow: 2
                }}
              />
            </Tooltip>
            <Tooltip title="Accent Color">
              <Box
                sx={{
                  width: 40,
                  height: 40,
                  borderRadius: 1,
                  bgcolor: config.accentColor,
                  border: '2px solid white',
                  boxShadow: 2
                }}
              />
            </Tooltip>
          </Stack>
        </Box>
      </Box>

      {!config.hideAttribution && (
        <Typography
          variant="caption"
          sx={{
            display: 'block',
            textAlign: 'center',
            mt: 3,
            opacity: 0.6
          }}
        >
          Powered by UC-Cloud Ops-Center
        </Typography>
      )}
    </Paper>
  );

  // ============================================
  // Main Render
  // ============================================

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PaletteIcon fontSize="large" />
          White Label Builder
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Customize the branding and appearance of your Ops-Center instance
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Action Buttons */}
      <Stack direction="row" spacing={2} sx={{ mb: 3 }}>
        <Button
          variant="contained"
          startIcon={saving ? <CircularProgress size={20} /> : <SaveIcon />}
          onClick={saveConfig}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Configuration'}
        </Button>

        <Button
          variant="outlined"
          startIcon={<PreviewIcon />}
          onClick={() => window.open('/', '_blank')}
        >
          Preview
        </Button>

        <Button
          variant="outlined"
          color="warning"
          startIcon={<ResetIcon />}
          onClick={handleReset}
        >
          Reset to Defaults
        </Button>
      </Stack>

      {/* Main Content - Two Column Layout */}
      <Grid container spacing={3}>
        {/* Left Column - Configuration Tabs */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3 }}>
            <Tabs
              value={currentTab}
              onChange={(e, newValue) => setCurrentTab(newValue)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}
            >
              <Tab label="Branding" icon={<BusinessIcon />} iconPosition="start" />
              <Tab label="Theme" icon={<PaletteIcon />} iconPosition="start" />
              <Tab label="Services" icon={<SettingsIcon />} iconPosition="start" />
              <Tab label="Advanced" icon={<CodeIcon />} iconPosition="start" />
            </Tabs>

            <Box sx={{ mt: 2 }}>
              {currentTab === 0 && renderBrandingTab()}
              {currentTab === 1 && renderThemeTab()}
              {currentTab === 2 && renderServicesTab()}
              {currentTab === 3 && renderAdvancedTab()}
            </Box>
          </Paper>
        </Grid>

        {/* Right Column - Live Preview */}
        <Grid item xs={12} md={5}>
          {renderLivePreview()}
        </Grid>
      </Grid>

      {/* Success Snackbar */}
      <Snackbar
        open={!!successMessage}
        autoHideDuration={4000}
        onClose={() => setSuccessMessage('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity="success" onClose={() => setSuccessMessage('')}>
          {successMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WhiteLabelBuilder;
