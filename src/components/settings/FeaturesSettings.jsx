/**
 * Features Settings Component
 * Feature flags and experimental features
 */

import React from 'react';
import {
  Box,
  FormControl,
  Switch,
  Typography,
  Paper,
  Chip
} from '@mui/material';

const FeatureToggle = ({ label, description, value, onChange, beta = false }) => (
  <FormControl fullWidth sx={{ mb: 3 }}>
    <Box display="flex" alignItems="center" justifyContent="space-between">
      <Box>
        <Box display="flex" alignItems="center" gap={1}>
          <Typography variant="body2" fontWeight="medium">
            {label}
          </Typography>
          {beta && <Chip label="Beta" size="small" color="warning" />}
        </Box>
        <Typography variant="caption" color="text.secondary">
          {description}
        </Typography>
      </Box>
      <Switch checked={value || false} onChange={(e) => onChange(e.target.checked)} />
    </Box>
  </FormControl>
);

const FeaturesSettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange(key, value);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Feature Flags
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Enable or disable platform features and experimental functionality
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <FeatureToggle
          label="API Access"
          description="Enable REST API access for developers"
          value={settings.enable_api_access}
          onChange={(value) => handleChange('enable_api_access', value)}
        />

        <FeatureToggle
          label="Marketplace"
          description="Enable the app marketplace for users to browse and purchase apps"
          value={settings.enable_marketplace}
          onChange={(value) => handleChange('enable_marketplace', value)}
        />

        <FeatureToggle
          label="Organizations"
          description="Enable multi-user organizations with team management"
          value={settings.enable_organizations}
          onChange={(value) => handleChange('enable_organizations', value)}
        />

        <FeatureToggle
          label="Credit System"
          description="Enable credit-based billing and usage tracking"
          value={settings.enable_credit_system}
          onChange={(value) => handleChange('enable_credit_system', value)}
        />

        <FeatureToggle
          label="Analytics Dashboard"
          description="Enable advanced analytics and reporting features"
          value={settings.enable_analytics}
          onChange={(value) => handleChange('enable_analytics', value)}
          beta={true}
        />
      </Paper>
    </Box>
  );
};

export default FeaturesSettings;
