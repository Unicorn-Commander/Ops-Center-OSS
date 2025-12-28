import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  IconButton,
  InputAdornment,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Tooltip,
  Grid
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Save,
  Refresh,
  CheckCircle,
  Warning,
  Error as ErrorIcon,
  ExpandMore,
  Security,
  Public,
  Payment,
  Key,
  Cloud,
  Domain,
  Code
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

const PlatformSettings = () => {
  const { theme } = useTheme();
  const [settings, setSettings] = useState([]);
  const [grouped, setGrouped] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editedSettings, setEditedSettings] = useState({});
  const [showSecrets, setShowSecrets] = useState({});
  const [testDialog, setTestDialog] = useState({ open: false, category: null, testing: false });
  const [restartDialog, setRestartDialog] = useState(false);

  // Category icons and colors
  const categoryConfig = {
    stripe: { icon: <Payment />, color: '#635BFF', label: 'Stripe Payment' },
    lago: { icon: <Payment />, color: '#00D4AA', label: 'Lago Billing' },
    keycloak: { icon: <Security />, color: '#00B8E3', label: 'Keycloak SSO' },
    cloudflare: { icon: <Cloud />, color: '#F38020', label: 'Cloudflare DNS' },
    namecheap: { icon: <Domain />, color: '#FF6C02', label: 'NameCheap Domains' },
    forgejo: { icon: <Code />, color: '#609926', label: 'Forgejo Git' },
    other: { icon: <Key />, color: '#9CA3AF', label: 'Other' }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/platform/settings', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load settings');
      }

      const data = await response.json();
      setSettings(data.settings);
      setGrouped(data.grouped);
    } catch (err) {
      console.error('Error loading settings:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (key, value) => {
    setEditedSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleToggleSecret = (key) => {
    setShowSecrets(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const handleSave = async (restartRequired = false) => {
    if (Object.keys(editedSettings).length === 0) {
      setError('No changes to save');
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/v1/platform/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          settings: editedSettings,
          restart_required: restartRequired
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save settings');
      }

      const data = await response.json();
      setSuccess(`Updated ${data.updated} settings successfully` +
        (restartRequired ? '. Container is restarting...' : ''));
      setEditedSettings({});

      // Refresh settings after save
      if (!restartRequired) {
        setTimeout(fetchSettings, 1000);
      } else {
        // Wait longer for container restart
        setTimeout(fetchSettings, 5000);
      }
    } catch (err) {
      console.error('Error saving settings:', err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (category) => {
    setTestDialog({ open: true, category, testing: true, result: null });

    // Get credentials for this category
    const categorySettings = grouped[category] || [];
    const credentials = {};

    categorySettings.forEach(setting => {
      const value = editedSettings[setting.key] ||
                   (showSecrets[setting.key] ? setting.value : '');
      if (value && !value.includes('...')) {
        credentials[setting.key] = value;
      }
    });

    try {
      const response = await fetch('/api/v1/platform/settings/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          category,
          credentials
        })
      });

      const data = await response.json();
      setTestDialog(prev => ({
        ...prev,
        testing: false,
        result: data
      }));
    } catch (err) {
      console.error('Test connection error:', err);
      setTestDialog(prev => ({
        ...prev,
        testing: false,
        result: {
          success: false,
          message: err.message,
          details: {}
        }
      }));
    }
  };

  const handleRestart = async () => {
    setRestartDialog(false);
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch('/api/v1/platform/settings/restart', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to restart container');
      }

      setSuccess('Container restarted successfully. Settings will be applied in 5-10 seconds.');

      // Refresh settings after restart
      setTimeout(fetchSettings, 7000);
    } catch (err) {
      console.error('Restart error:', err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  const hasChanges = Object.keys(editedSettings).length > 0;

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" className={theme.text.primary} sx={{ mb: 1 }}>
          Platform Settings
        </Typography>
        <Typography variant="body2" className={theme.text.secondary}>
          Manage API keys, secrets, and integration credentials
        </Typography>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Action Buttons */}
      {hasChanges && (
        <Card className={theme.card} sx={{ mb: 3, borderColor: 'warning.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Warning color="warning" />
                <Box>
                  <Typography variant="h6" className={theme.text.primary}>
                    Unsaved Changes
                  </Typography>
                  <Typography variant="body2" className={theme.text.secondary}>
                    You have {Object.keys(editedSettings).length} unsaved change(s)
                  </Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="outlined"
                  onClick={() => setEditedSettings({})}
                  disabled={saving}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Save />}
                  onClick={() => handleSave(false)}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save (No Restart)'}
                </Button>
                <Button
                  variant="contained"
                  color="warning"
                  startIcon={<Refresh />}
                  onClick={() => handleSave(true)}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save & Restart'}
                </Button>
              </Box>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Settings by Category */}
      {Object.entries(grouped).map(([category, categorySettings]) => {
        const config = categoryConfig[category] || categoryConfig.other;
        const allConfigured = categorySettings.every(s => s.is_configured);

        return (
          <Accordion
            key={category}
            defaultExpanded={category === 'stripe'}
            className={theme.card}
            sx={{ mb: 2 }}
          >
            <AccordionSummary expandIcon={<ExpandMore />}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                <Box sx={{ color: config.color }}>
                  {config.icon}
                </Box>
                <Typography variant="h6" className={theme.text.primary}>
                  {config.label}
                </Typography>
                <Chip
                  label={`${categorySettings.filter(s => s.is_configured).length}/${categorySettings.length} configured`}
                  size="small"
                  color={allConfigured ? 'success' : 'warning'}
                  sx={{ ml: 'auto' }}
                />
                {categorySettings.some(s => s.test_connection) && (
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleTestConnection(category);
                    }}
                    sx={{ ml: 1 }}
                  >
                    Test Connection
                  </Button>
                )}
              </Box>
            </AccordionSummary>
            <AccordionDetails>
              <Grid container spacing={3}>
                {categorySettings.map(setting => {
                  const currentValue = editedSettings[setting.key] ?? setting.value ?? '';
                  const isSecret = setting.is_secret;
                  const showValue = showSecrets[setting.key] || !isSecret;

                  return (
                    <Grid item xs={12} key={setting.key}>
                      <TextField
                        fullWidth
                        label={setting.key}
                        value={currentValue}
                        onChange={(e) => handleEdit(setting.key, e.target.value)}
                        type={showValue ? 'text' : 'password'}
                        helperText={setting.description}
                        required={setting.required}
                        InputProps={{
                          endAdornment: isSecret && (
                            <InputAdornment position="end">
                              <IconButton
                                onClick={() => handleToggleSecret(setting.key)}
                                edge="end"
                              >
                                {showValue ? <VisibilityOff /> : <Visibility />}
                              </IconButton>
                            </InputAdornment>
                          ),
                          startAdornment: setting.is_configured && !editedSettings[setting.key] && (
                            <InputAdornment position="start">
                              <Tooltip title="Currently configured">
                                <CheckCircle color="success" fontSize="small" />
                              </Tooltip>
                            </InputAdornment>
                          )
                        }}
                      />
                    </Grid>
                  );
                })}
              </Grid>
            </AccordionDetails>
          </Accordion>
        );
      })}

      {/* Manual Restart Button */}
      <Card className={theme.card} sx={{ mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box>
              <Typography variant="h6" className={theme.text.primary}>
                Container Restart
              </Typography>
              <Typography variant="body2" className={theme.text.secondary}>
                Restart the ops-center container to apply settings changes
              </Typography>
            </Box>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => setRestartDialog(true)}
              disabled={saving}
            >
              Restart Container
            </Button>
          </Box>
        </CardContent>
      </Card>

      {/* Test Connection Dialog */}
      <Dialog
        open={testDialog.open}
        onClose={() => !testDialog.testing && setTestDialog({ open: false, category: null, testing: false })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Test {categoryConfig[testDialog.category]?.label || 'Connection'}
        </DialogTitle>
        <DialogContent>
          {testDialog.testing ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
              <CircularProgress sx={{ mb: 2 }} />
              <Typography>Testing connection...</Typography>
            </Box>
          ) : testDialog.result ? (
            <Box>
              <Alert severity={testDialog.result.success ? 'success' : 'error'} sx={{ mb: 2 }}>
                {testDialog.result.message}
              </Alert>
              {testDialog.result.details && Object.keys(testDialog.result.details).length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Details:
                  </Typography>
                  <pre style={{
                    background: '#1e1e1e',
                    padding: '12px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    overflow: 'auto'
                  }}>
                    {JSON.stringify(testDialog.result.details, null, 2)}
                  </pre>
                </Box>
              )}
            </Box>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialog({ open: false, category: null, testing: false })}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Restart Confirmation Dialog */}
      <Dialog
        open={restartDialog}
        onClose={() => setRestartDialog(false)}
      >
        <DialogTitle>Restart Container?</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This will cause 5-10 seconds of downtime
          </Alert>
          <Typography>
            The ops-center container will restart to apply any settings changes.
            All active sessions will be interrupted briefly.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestartDialog(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleRestart}
            variant="contained"
            color="warning"
            startIcon={<Refresh />}
          >
            Restart Now
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PlatformSettings;
