/**
 * Authentication Settings Component
 * Settings for SSO, login behavior, and user registration
 */

import React from 'react';
import {
  Box,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  Switch,
  Typography,
  Paper,
  Divider
} from '@mui/material';

const AuthenticationSettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange(key, value);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Authentication & Access Control
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure how users authenticate and access the system
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        {/* Landing Page Mode */}
        <FormControl component="fieldset" fullWidth sx={{ mb: 3 }}>
          <FormLabel component="legend">Landing Page Mode</FormLabel>
          <RadioGroup
            value={settings.landing_page_mode || 'public_marketplace'}
            onChange={(e) => handleChange('landing_page_mode', e.target.value)}
          >
            <FormControlLabel
              value="direct_sso_login"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Direct SSO Login
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Immediately redirect to Keycloak SSO login page (best for private/enterprise deployments)
                  </Typography>
                </Box>
              }
            />
            <FormControlLabel
              value="public_marketplace"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Public Marketplace
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Show public app marketplace with "Login" button (best for SaaS/public instances)
                  </Typography>
                </Box>
              }
            />
            <FormControlLabel
              value="custom_landing_page"
              control={<Radio />}
              label={
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Custom Landing Page
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Display custom branded landing page with manual login
                  </Typography>
                </Box>
              }
            />
          </RadioGroup>
        </FormControl>

        <Divider sx={{ my: 3 }} />

        {/* SSO Auto Redirect */}
        <FormControl fullWidth sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="body2" fontWeight="medium">
                SSO Auto Redirect
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Automatically redirect unauthenticated users to SSO login
              </Typography>
            </Box>
            <Switch
              checked={settings.sso_auto_redirect || false}
              onChange={(e) => handleChange('sso_auto_redirect', e.target.checked)}
            />
          </Box>
        </FormControl>

        {/* Allow Registration */}
        <FormControl fullWidth sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="body2" fontWeight="medium">
                Allow New User Registration
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Enable self-service registration for new users
              </Typography>
            </Box>
            <Switch
              checked={settings.allow_registration || true}
              onChange={(e) => handleChange('allow_registration', e.target.checked)}
            />
          </Box>
        </FormControl>

        {/* Require Email Verification */}
        <FormControl fullWidth sx={{ mb: 3 }}>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="body2" fontWeight="medium">
                Require Email Verification
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Require users to verify their email address before accessing the system
              </Typography>
            </Box>
            <Switch
              checked={settings.require_email_verification || false}
              onChange={(e) => handleChange('require_email_verification', e.target.checked)}
            />
          </Box>
        </FormControl>

        {/* Enable Social Logins */}
        <FormControl fullWidth>
          <Box display="flex" alignItems="center" justifyContent="space-between">
            <Box>
              <Typography variant="body2" fontWeight="medium">
                Enable Social Logins
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Allow login via Google, GitHub, Microsoft (configured in Keycloak)
              </Typography>
            </Box>
            <Switch
              checked={settings.enable_social_logins || true}
              onChange={(e) => handleChange('enable_social_logins', e.target.checked)}
            />
          </Box>
        </FormControl>
      </Paper>
    </Box>
  );
};

export default AuthenticationSettings;
