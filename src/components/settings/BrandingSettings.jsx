/**
 * Branding Settings Component
 * Customizable branding elements (colors, logos, company info)
 */

import React, { useState } from 'react';
import {
  Box,
  TextField,
  Typography,
  Paper,
  Grid,
  Button
} from '@mui/material';
import { SketchPicker } from 'react-color';

const ColorPickerField = ({ label, value, onChange, helperText }) => {
  const [showPicker, setShowPicker] = useState(false);

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="body2" fontWeight="medium" gutterBottom>
        {label}
      </Typography>
      <Box display="flex" alignItems="center" gap={2}>
        <Box
          sx={{
            width: 60,
            height: 40,
            backgroundColor: value || '#000000',
            border: '2px solid',
            borderColor: 'divider',
            borderRadius: 1,
            cursor: 'pointer'
          }}
          onClick={() => setShowPicker(!showPicker)}
        />
        <TextField
          value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          placeholder="#000000"
          size="small"
          sx={{ flex: 1 }}
          helperText={helperText}
        />
        <Button
          variant="outlined"
          size="small"
          onClick={() => setShowPicker(!showPicker)}
        >
          {showPicker ? 'Close' : 'Pick'}
        </Button>
      </Box>
      {showPicker && (
        <Box sx={{ mt: 2, position: 'relative', zIndex: 2 }}>
          <SketchPicker
            color={value || '#000000'}
            onChangeComplete={(color) => onChange(color.hex)}
          />
        </Box>
      )}
    </Box>
  );
};

const BrandingSettings = ({ settings, onChange }) => {
  const handleChange = (key, value) => {
    onChange(key, value);
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Brand Identity & Appearance
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        Customize your platform's visual identity and branding elements
      </Typography>

      <Paper sx={{ p: 3, mt: 2 }}>
        <Grid container spacing={3}>
          {/* Company Information */}
          <Grid item xs={12}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Company Information
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Company Name"
              value={settings.company_name || ''}
              onChange={(e) => handleChange('company_name', e.target.value)}
              helperText="Displayed in page titles and headers"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Company Tagline"
              value={settings.company_tagline || ''}
              onChange={(e) => handleChange('company_tagline', e.target.value)}
              helperText="Short description or slogan"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Support Email"
              type="email"
              value={settings.support_email || ''}
              onChange={(e) => handleChange('support_email', e.target.value)}
              helperText="Customer support email address"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Support Phone"
              value={settings.support_phone || ''}
              onChange={(e) => handleChange('support_phone', e.target.value)}
              helperText="Customer support phone number"
            />
          </Grid>

          {/* Logos */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Logos & Icons
            </Typography>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Logo URL"
              value={settings.logo_url || ''}
              onChange={(e) => handleChange('logo_url', e.target.value)}
              helperText="URL to your company logo (recommended: 200x60px)"
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Favicon URL"
              value={settings.favicon_url || ''}
              onChange={(e) => handleChange('favicon_url', e.target.value)}
              helperText="URL to your favicon (recommended: 32x32px)"
            />
          </Grid>

          {/* Color Palette */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Color Palette
            </Typography>
          </Grid>

          <Grid item xs={12} md={4}>
            <ColorPickerField
              label="Primary Color"
              value={settings.primary_color}
              onChange={(color) => handleChange('primary_color', color)}
              helperText="Main brand color (buttons, links, accents)"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <ColorPickerField
              label="Secondary Color"
              value={settings.secondary_color}
              onChange={(color) => handleChange('secondary_color', color)}
              helperText="Secondary brand color (headers, highlights)"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <ColorPickerField
              label="Accent Color"
              value={settings.accent_color}
              onChange={(color) => handleChange('accent_color', color)}
              helperText="Accent color (badges, notifications)"
            />
          </Grid>

          {/* Footer Text */}
          <Grid item xs={12} sx={{ mt: 2 }}>
            <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
              Footer Information
            </Typography>
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              multiline
              rows={2}
              label="Footer Text"
              value={settings.footer_text || ''}
              onChange={(e) => handleChange('footer_text', e.target.value)}
              helperText="Text displayed in the page footer"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Privacy Policy URL"
              value={settings.privacy_policy_url || ''}
              onChange={(e) => handleChange('privacy_policy_url', e.target.value)}
              helperText="Link to your privacy policy"
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Terms of Service URL"
              value={settings.terms_of_service_url || ''}
              onChange={(e) => handleChange('terms_of_service_url', e.target.value)}
              helperText="Link to your terms of service"
            />
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default BrandingSettings;
