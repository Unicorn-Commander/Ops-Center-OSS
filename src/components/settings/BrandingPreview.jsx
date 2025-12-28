/**
 * Branding Preview Component
 * Live preview of branding changes before saving
 */

import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Button
} from '@mui/material';

const BrandingPreview = ({ settings }) => {
  const {
    company_name = 'Your Company',
    company_tagline = 'Your tagline here',
    primary_color = '#6B46C1',
    secondary_color = '#9333EA',
    accent_color = '#F59E0B',
    logo_url
  } = settings || {};

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Live Preview
      </Typography>
      <Typography variant="body2" color="text.secondary" paragraph>
        See how your branding changes will look
      </Typography>

      <Paper
        sx={{
          p: 4,
          mt: 2,
          background: `linear-gradient(135deg, ${primary_color}20 0%, ${secondary_color}20 100%)`,
          border: '2px dashed',
          borderColor: 'divider'
        }}
      >
        {/* Mock Header */}
        <Box sx={{ mb: 4, textAlign: 'center' }}>
          {logo_url && (
            <Box
              component="img"
              src={logo_url}
              alt={company_name}
              sx={{
                maxWidth: 200,
                maxHeight: 60,
                mb: 2,
                objectFit: 'contain'
              }}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
          )}
          <Typography
            variant="h4"
            fontWeight="bold"
            sx={{ color: primary_color }}
            gutterBottom
          >
            {company_name}
          </Typography>
          <Typography
            variant="subtitle1"
            sx={{ color: secondary_color }}
          >
            {company_tagline}
          </Typography>
        </Box>

        {/* Mock UI Elements */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Sample UI Elements
          </Typography>

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mt: 2 }}>
            <Button
              variant="contained"
              sx={{
                backgroundColor: primary_color,
                '&:hover': {
                  backgroundColor: primary_color,
                  opacity: 0.9
                }
              }}
            >
              Primary Button
            </Button>

            <Button
              variant="contained"
              sx={{
                backgroundColor: secondary_color,
                '&:hover': {
                  backgroundColor: secondary_color,
                  opacity: 0.9
                }
              }}
            >
              Secondary Button
            </Button>

            <Button
              variant="contained"
              sx={{
                backgroundColor: accent_color,
                '&:hover': {
                  backgroundColor: accent_color,
                  opacity: 0.9
                }
              }}
            >
              Accent Button
            </Button>
          </Box>
        </Box>

        {/* Color Swatches */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Color Palette
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <Box sx={{ flex: 1, textAlign: 'center' }}>
              <Box
                sx={{
                  height: 80,
                  backgroundColor: primary_color,
                  borderRadius: 1,
                  mb: 1
                }}
              />
              <Typography variant="caption" display="block">
                Primary
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                {primary_color}
              </Typography>
            </Box>

            <Box sx={{ flex: 1, textAlign: 'center' }}>
              <Box
                sx={{
                  height: 80,
                  backgroundColor: secondary_color,
                  borderRadius: 1,
                  mb: 1
                }}
              />
              <Typography variant="caption" display="block">
                Secondary
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                {secondary_color}
              </Typography>
            </Box>

            <Box sx={{ flex: 1, textAlign: 'center' }}>
              <Box
                sx={{
                  height: 80,
                  backgroundColor: accent_color,
                  borderRadius: 1,
                  mb: 1
                }}
              />
              <Typography variant="caption" display="block">
                Accent
              </Typography>
              <Typography variant="caption" color="text.secondary" display="block">
                {accent_color}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default BrandingPreview;
