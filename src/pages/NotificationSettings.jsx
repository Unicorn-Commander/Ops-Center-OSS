import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Switch,
  FormControlLabel,
  Slider,
  Radio,
  RadioGroup,
  TextField,
  Button,
  Divider,
  Alert,
  Chip,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  FormGroup,
  FormControl,
  FormLabel,
  InputAdornment,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Email as EmailIcon,
  Warning as WarningIcon,
  Memory as MemoryIcon,
  CreditCard as CreditCardIcon,
  Security as SecurityIcon,
  Send as SendIcon,
  Info as InfoIcon,
  Check as CheckIcon,
  Chat as SlackIcon,
  Sms as SmsIcon,
} from '@mui/icons-material';

const NotificationSettings = () => {
  // State
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [preferences, setPreferences] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [testResult, setTestResult] = useState(null);

  // Load preferences on mount
  useEffect(() => {
    loadPreferences();
  }, []);

  const loadPreferences = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/notifications/preferences', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to load notification preferences');
      }

      const data = await response.json();
      setPreferences(data);
    } catch (err) {
      console.error('Error loading preferences:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const savePreferences = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/notifications/preferences', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(preferences),
      });

      if (!response.ok) {
        throw new Error('Failed to save preferences');
      }

      const data = await response.json();
      setPreferences(data);
      setSuccess('Notification preferences saved successfully!');

      // Clear success message after 3 seconds
      setTimeout(() => setSuccess(null), 3000);
    } catch (err) {
      console.error('Error saving preferences:', err);
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  const testNotification = async (notificationType) => {
    try {
      setTesting(true);
      setTestResult(null);
      setError(null);

      const response = await fetch('/api/v1/notifications/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ notification_type: notificationType }),
      });

      if (!response.ok) {
        throw new Error('Failed to send test notification');
      }

      const data = await response.json();
      setTestResult(data);

      // Clear test result after 5 seconds
      setTimeout(() => setTestResult(null), 5000);
    } catch (err) {
      console.error('Error testing notification:', err);
      setError(err.message);
    } finally {
      setTesting(false);
    }
  };

  const updatePreference = (field, value) => {
    setPreferences((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  // Loading state
  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  // Error state
  if (!preferences) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error">Failed to load notification preferences</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box mb={4}>
        <Box display="flex" alignItems="center" gap={2} mb={1}>
          <NotificationsIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <Typography variant="h4" component="h1">
            Notification Settings
          </Typography>
        </Box>
        <Typography variant="body1" color="text.secondary">
          Configure how and when you receive alerts and notifications
        </Typography>
      </Box>

      {/* Phase 3 Notice */}
      <Alert severity="info" sx={{ mb: 3 }} icon={<InfoIcon />}>
        <strong>Email notifications will be enabled in a future release.</strong> Your preferences are
        being saved and will automatically apply when the feature is activated.
      </Alert>

      {/* Success Message */}
      {success && (
        <Alert severity="success" sx={{ mb: 3 }} icon={<CheckIcon />}>
          {success}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Test Result */}
      {testResult && (
        <Alert
          severity={testResult.preview.enabled ? 'success' : 'warning'}
          sx={{ mb: 3 }}
        >
          <Typography variant="subtitle2" fontWeight="bold">
            {testResult.message}
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            <strong>Subject:</strong> {testResult.preview.subject}
          </Typography>
          <Typography variant="body2">
            <strong>Message:</strong> {testResult.preview.message}
          </Typography>
          <Typography variant="caption" display="block" sx={{ mt: 1, fontStyle: 'italic' }}>
            {testResult.note}
          </Typography>
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Alert Types Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
              <WarningIcon color="primary" />
              Alert Types
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Choose which types of alerts you want to receive
            </Typography>

            <Grid container spacing={2}>
              {/* Usage Alerts */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.usage_alerts_enabled}
                          onChange={(e) =>
                            updatePreference('usage_alerts_enabled', e.target.checked)
                          }
                          color="primary"
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold">
                            Usage Alerts
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Get notified when approaching tier limits
                          </Typography>
                        </Box>
                      }
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Hardware Alerts */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.hardware_alerts_enabled}
                          onChange={(e) =>
                            updatePreference('hardware_alerts_enabled', e.target.checked)
                          }
                          color="primary"
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold">
                            Hardware Alerts
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Temperature and utilization warnings
                          </Typography>
                        </Box>
                      }
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Billing Alerts */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.billing_alerts_enabled}
                          onChange={(e) =>
                            updatePreference('billing_alerts_enabled', e.target.checked)
                          }
                          color="primary"
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold">
                            Billing Alerts
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Invoices and payment notifications
                          </Typography>
                        </Box>
                      }
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Security Alerts */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined">
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.security_alerts_enabled}
                          onChange={(e) =>
                            updatePreference('security_alerts_enabled', e.target.checked)
                          }
                          color="primary"
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="subtitle1" fontWeight="bold">
                            Security Alerts
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Unauthorized access and security events
                          </Typography>
                        </Box>
                      }
                    />
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Alert Thresholds Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
              <MemoryIcon color="primary" />
              Alert Thresholds
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Set when you want to be alerted based on thresholds
            </Typography>

            <Grid container spacing={4}>
              {/* Usage Alert Threshold */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Usage Alert Threshold
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Alert when reaching {preferences.usage_alert_threshold}% of tier limit
                </Typography>
                <Slider
                  value={preferences.usage_alert_threshold}
                  onChange={(e, value) => updatePreference('usage_alert_threshold', value)}
                  min={50}
                  max={95}
                  step={5}
                  marks={[
                    { value: 50, label: '50%' },
                    { value: 75, label: '75%' },
                    { value: 90, label: '90%' },
                  ]}
                  valueLabelDisplay="on"
                  valueLabelFormat={(value) => `${value}%`}
                />
              </Grid>

              {/* Hardware Temperature Threshold */}
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Hardware Temperature Threshold
                </Typography>
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Alert when temperature reaches {preferences.hardware_temp_threshold}°C
                </Typography>
                <Slider
                  value={preferences.hardware_temp_threshold}
                  onChange={(e, value) => updatePreference('hardware_temp_threshold', value)}
                  min={70}
                  max={95}
                  step={5}
                  marks={[
                    { value: 70, label: '70°C' },
                    { value: 80, label: '80°C' },
                    { value: 90, label: '90°C' },
                  ]}
                  valueLabelDisplay="on"
                  valueLabelFormat={(value) => `${value}°C`}
                />
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Alert Frequency Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Alert Frequency
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Choose how often you want to receive notifications
            </Typography>

            <FormControl component="fieldset">
              <RadioGroup
                value={preferences.alert_frequency}
                onChange={(e) => updatePreference('alert_frequency', e.target.value)}
              >
                <FormControlLabel
                  value="immediate"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="subtitle1">Immediate</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Receive alerts as they occur
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="daily"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="subtitle1">Daily Digest</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Receive a summary once per day
                      </Typography>
                    </Box>
                  }
                />
                <FormControlLabel
                  value="weekly"
                  control={<Radio />}
                  label={
                    <Box>
                      <Typography variant="subtitle1">Weekly Summary</Typography>
                      <Typography variant="body2" color="text.secondary">
                        Receive a summary once per week
                      </Typography>
                    </Box>
                  }
                />
              </RadioGroup>
            </FormControl>
          </Paper>
        </Grid>

        {/* Notification Channels Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
              <EmailIcon color="primary" />
              Notification Channels
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Choose how you want to receive notifications
            </Typography>

            <Grid container spacing={3}>
              {/* Email Channel */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={preferences.email_enabled}
                          onChange={(e) =>
                            updatePreference('email_enabled', e.target.checked)
                          }
                          color="primary"
                        />
                      }
                      label={
                        <Box display="flex" alignItems="center" gap={1}>
                          <EmailIcon />
                          <Typography variant="subtitle1" fontWeight="bold">
                            Email Notifications
                          </Typography>
                        </Box>
                      }
                    />
                    <TextField
                      fullWidth
                      size="small"
                      label="Email Address"
                      type="email"
                      value={preferences.email}
                      onChange={(e) => updatePreference('email', e.target.value)}
                      disabled={!preferences.email_enabled}
                      sx={{ mt: 2 }}
                    />
                  </CardContent>
                </Card>
              </Grid>

              {/* Slack Channel */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <FormControlLabel
                        control={
                          <Switch
                            checked={preferences.slack_enabled}
                            onChange={(e) =>
                              updatePreference('slack_enabled', e.target.checked)
                            }
                            color="primary"
                          />
                        }
                        label={
                          <Box display="flex" alignItems="center" gap={1}>
                            <SlackIcon />
                            <Typography variant="subtitle1" fontWeight="bold">
                              Slack Notifications
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip label="Coming Soon" size="small" color="info" />
                    </Box>
                    <TextField
                      fullWidth
                      size="small"
                      label="Slack Webhook URL"
                      placeholder="https://hooks.slack.com/services/..."
                      value={preferences.slack_webhook_url || ''}
                      onChange={(e) => updatePreference('slack_webhook_url', e.target.value)}
                      disabled={!preferences.slack_enabled}
                      sx={{ mt: 2 }}
                    />
                    <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                      Slack integration will be available in a future release
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>

              {/* SMS Channel */}
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <FormControlLabel
                        control={
                          <Switch
                            checked={preferences.sms_enabled}
                            onChange={(e) =>
                              updatePreference('sms_enabled', e.target.checked)
                            }
                            color="primary"
                            disabled
                          />
                        }
                        label={
                          <Box display="flex" alignItems="center" gap={1}>
                            <SmsIcon />
                            <Typography variant="subtitle1" fontWeight="bold">
                              SMS Notifications
                            </Typography>
                          </Box>
                        }
                      />
                      <Chip label="Coming Soon" size="small" color="warning" />
                    </Box>
                    <Typography variant="caption" color="text.secondary" display="block" mt={1}>
                      SMS notifications will be available in a future release
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Paper>
        </Grid>

        {/* Test Notification Section */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom display="flex" alignItems="center" gap={1}>
              <SendIcon color="primary" />
              Test Notifications
            </Typography>
            <Typography variant="body2" color="text.secondary" mb={3}>
              Send a test notification to preview your settings
            </Typography>

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<WarningIcon />}
                  onClick={() => testNotification('usage')}
                  disabled={testing}
                >
                  Test Usage Alert
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<MemoryIcon />}
                  onClick={() => testNotification('hardware')}
                  disabled={testing}
                >
                  Test Hardware Alert
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<CreditCardIcon />}
                  onClick={() => testNotification('billing')}
                  disabled={testing}
                >
                  Test Billing Alert
                </Button>
              </Grid>
              <Grid item xs={12} sm={6} md={3}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<SecurityIcon />}
                  onClick={() => testNotification('security')}
                  disabled={testing}
                >
                  Test Security Alert
                </Button>
              </Grid>
            </Grid>
          </Paper>
        </Grid>
      </Grid>

      {/* Save Button */}
      <Box mt={4} display="flex" justifyContent="flex-end" gap={2}>
        <Button variant="outlined" onClick={loadPreferences} disabled={saving}>
          Reset Changes
        </Button>
        <Button
          variant="contained"
          size="large"
          onClick={savePreferences}
          disabled={saving}
          startIcon={saving ? <CircularProgress size={20} /> : <CheckIcon />}
        >
          {saving ? 'Saving...' : 'Save Preferences'}
        </Button>
      </Box>
    </Container>
  );
};

export default NotificationSettings;
