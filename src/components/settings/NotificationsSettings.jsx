/**
 * Notifications Settings Component
 * Email notifications and webhook configurations
 */

import React from 'react';
import {
  Box,
  TextField,
  Typography,
  Paper,
  FormControl,
  Switch,
  Grid
} from '@mui/material';

const NotificationsSettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange(key, value);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Notifications & Alerts
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure system notifications and webhook integrations
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Grid container spacing={3}>
          {/* Email Notifications */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Email Notifications
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Send Welcome Emails
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Send welcome email to new users upon registration
                  </Typography>
                </Box>
                <Switch
                  checked={settings.send_welcome_emails || false}
                  onChange={(e) => handleChange('send_welcome_emails', e.target.checked)}
                />
              </Box>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Send Invoice Emails
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Email invoices to customers after payment
                  </Typography>
                </Box>
                <Switch
                  checked={settings.send_invoice_emails || false}
                  onChange={(e) => handleChange('send_invoice_emails', e.target.checked)}
                />
              </Box>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Send Usage Alerts
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Notify users when approaching usage limits
                  </Typography>
                </Box>
                <Switch
                  checked={settings.send_usage_alerts || false}
                  onChange={(e) => handleChange('send_usage_alerts', e.target.checked)}
                />
              </Box>
            </FormControl>
          </Grid>

          {/* Webhooks */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Webhooks
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Webhook URL"
              value={settings.webhook_url || ''}
              onChange={(e) => handleChange('webhook_url', e.target.value)}
              helperText="URL to receive webhook events (subscription changes, payments, etc.)"
              placeholder="https://your-domain.com/webhooks/ops-center"
            />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default NotificationsSettings;
