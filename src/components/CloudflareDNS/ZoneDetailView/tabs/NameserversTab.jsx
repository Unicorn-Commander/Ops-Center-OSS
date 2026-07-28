import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Divider, Alert, Button } from '@mui/material';
import { ContentCopy as CopyIcon } from '@mui/icons-material';

const NameserversTab = ({ zone, onCopyNameservers }) => {
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Assigned Nameservers</Typography>
              <Divider sx={{ my: 2 }} />
              {zone.nameservers && zone.nameservers.length > 0 ? (
                <Box>
                  {zone.nameservers.map((ns, idx) => (
                    <Box key={idx} sx={{ mb: 1, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                      <Typography variant="body1" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                        {ns}
                      </Typography>
                    </Box>
                  ))}
                  <Button
                    fullWidth
                    variant="outlined"
                    startIcon={<CopyIcon />}
                    onClick={() => onCopyNameservers(zone.nameservers)}
                    sx={{ mt: 2 }}
                  >
                    Copy Nameservers
                  </Button>
                </Box>
              ) : (
                <Alert severity="info">Nameservers not yet assigned</Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Update Instructions</Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>1. Log in to your domain registrar</Typography>
                  <Typography variant="body2" color="text.secondary">
                    (e.g., NameCheap, GoDaddy, Google Domains)
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>2. Find the DNS or Nameserver settings</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Usually under "Domain Management" or "DNS Settings"
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>3. Replace existing nameservers</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Remove old nameservers and add the Cloudflare nameservers above
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>4. Wait for propagation</Typography>
                  <Typography variant="body2" color="text.secondary">
                    DNS propagation can take 1-24 hours. Check status periodically.
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Alert severity={zone.status === 'active' ? 'success' : 'warning'}>
            {zone.status === 'active' ? (
              <>
                <strong>Propagation Complete:</strong> Your domain is now using Cloudflare nameservers globally.
              </>
            ) : (
              <>
                <strong>Propagation Pending:</strong> Nameservers have not been updated yet. Follow the instructions above.
              </>
            )}
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default NameserversTab;
