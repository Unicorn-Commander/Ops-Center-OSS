/**
 * Integrations Settings Component
 * External API keys and service integrations
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Typography,
  Paper,
  Grid,
  InputAdornment,
  IconButton,
  Button
} from '@mui/material';
import { Visibility, VisibilityOff, CheckCircle, Cancel } from '@mui/icons-material';

const APIKeyField = ({ label, value, onChange, helperText }) => {
  const [showKey, setShowKey] = useState(false);

  return (
    <TextField
      fullWidth
      label={label}
      type={showKey ? 'text' : 'password'}
      value={value || ''}
      onChange={(e) => onChange(e.target.value)}
      helperText={helperText}
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            <IconButton
              onClick={() => setShowKey(!showKey)}
              edge="end"
            >
              {showKey ? <VisibilityOff /> : <Visibility />}
            </IconButton>
          </InputAdornment>
        )
      }}
    />
  );
};

const IntegrationsSettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange(key, value);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        External Integrations
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure API keys for external services
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Grid container spacing={3}>
          {/* Stripe */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Stripe Payment Processing
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <APIKeyField
              label="Stripe Publishable Key"
              value={settings.stripe_publishable_key}
              onChange={(value) => handleChange('stripe_publishable_key', value)}
              helperText="Public key for client-side Stripe.js (pk_test_... or pk_live_...)"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <APIKeyField
              label="Stripe Secret Key"
              value={settings.stripe_secret_key}
              onChange={(value) => handleChange('stripe_secret_key', value)}
              helperText="Secret key for server-side API calls (sk_test_... or sk_live_...)"
            />
          </Grid>

          {/* Email Provider */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Email Service
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="SMTP Host"
              value={settings.smtp_host || ''}
              onChange={(e) => handleChange('smtp_host', e.target.value)}
              helperText="SMTP server hostname"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="SMTP Port"
              type="number"
              value={settings.smtp_port || ''}
              onChange={(e) => handleChange('smtp_port', e.target.value)}
              helperText="SMTP server port (usually 587 or 465)"
            />
          </Grid>

          {/* Analytics */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Analytics & Monitoring
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <APIKeyField
              label="Google Analytics ID"
              value={settings.google_analytics_id}
              onChange={(value) => handleChange('google_analytics_id', value)}
              helperText="Google Analytics Measurement ID (G-XXXXXXXXXX)"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Sentry DSN"
              value={settings.sentry_dsn || ''}
              onChange={(e) => handleChange('sentry_dsn', e.target.value)}
              helperText="Sentry error tracking DSN (optional)"
            />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default IntegrationsSettings;
