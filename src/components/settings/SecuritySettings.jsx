/**
 * Security Settings Component
 * Security policies and access control
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

const SecuritySettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange(key, value);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Security & Access Policies
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Configure security settings and password policies
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Grid container spacing={3}>
          {/* Session Management */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Session Management
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Session Timeout (minutes)"
              value={settings.session_timeout_minutes || ''}
              onChange={(e) => handleChange('session_timeout_minutes', parseInt(e.target.value))}
              helperText="Automatically log out inactive users after this duration"
              inputProps={{ min: 5, max: 1440 }}
            />
          </Grid>

          {/* Password Policy */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Password Policy
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Minimum Password Length"
              value={settings.min_password_length || ''}
              onChange={(e) => handleChange('min_password_length', parseInt(e.target.value))}
              helperText="Minimum number of characters required"
              inputProps={{ min: 8, max: 32 }}
            />
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Require Special Characters
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Passwords must contain at least one special character (!@#$%^&*)
                  </Typography>
                </Box>
                <Switch
                  checked={settings.require_special_chars || false}
                  onChange={(e) => handleChange('require_special_chars', e.target.checked)}
                />
              </Box>
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <FormControl fullWidth>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography variant="body2" fontWeight="medium">
                    Require Numbers
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Passwords must contain at least one number (0-9)
                  </Typography>
                </Box>
                <Switch
                  checked={settings.require_numbers || false}
                  onChange={(e) => handleChange('require_numbers', e.target.checked)}
                />
              </Box>
            </FormControl>
          </Grid>

          {/* Rate Limiting */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Rate Limiting
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type="number"
              label="Max Login Attempts"
              value={settings.max_login_attempts || ''}
              onChange={(e) => handleChange('max_login_attempts', parseInt(e.target.value))}
              helperText="Lock account after this many failed login attempts"
              inputProps={{ min: 3, max: 10 }}
            />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default SecuritySettings;
