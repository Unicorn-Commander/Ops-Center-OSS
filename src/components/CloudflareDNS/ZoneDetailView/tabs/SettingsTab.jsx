import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Divider, Alert, Button, FormControlLabel, Switch } from '@mui/material';
import { Delete as DeleteIcon } from '@mui/icons-material';

const SettingsTab = ({ zone, onDeleteZone }) => {
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Zone Settings</Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Development Mode</Typography>
                  <FormControlLabel
                    control={<Switch disabled />}
                    label="Temporarily bypass cache (3 hours)"
                  />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Auto HTTPS Rewrites</Typography>
                  <FormControlLabel
                    control={<Switch disabled defaultChecked />}
                    label="Automatically rewrite HTTP to HTTPS"
                  />
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>Always Use HTTPS</Typography>
                  <FormControlLabel
                    control={<Switch disabled defaultChecked />}
                    label="Redirect all HTTP requests to HTTPS"
                  />
                </Box>
              </Box>
              <Alert severity="info" sx={{ mt: 2 }}>
                Advanced settings coming soon. Visit Cloudflare dashboard for full configuration.
              </Alert>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Danger Zone</Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Delete this zone and all its DNS records
                  </Typography>
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={onDeleteZone}
                    fullWidth
                  >
                    Delete Zone
                  </Button>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default SettingsTab;
