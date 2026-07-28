import React from 'react';
import { Box, Grid, Card, CardContent, Typography, Divider, Alert } from '@mui/material';
import { Info as InfoIcon } from '@mui/icons-material';
import StatusBadge from '../../Shared/StatusBadge';

const OverviewTab = ({ zone, dnsRecords }) => {
  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Zone Information</Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                <Box>
                  <Typography variant="caption" color="text.secondary">Zone ID</Typography>
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{zone.zone_id}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Status</Typography>
                  <Box sx={{ mt: 0.5 }}>
                    <StatusBadge status={zone.status} />
                  </Box>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Plan</Typography>
                  <Typography variant="body2">{zone.plan?.toUpperCase() || 'FREE'}</Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">Created</Typography>
                  <Typography variant="body2">{new Date(zone.created_at).toLocaleString()}</Typography>
                </Box>
                {zone.activated_at && (
                  <Box>
                    <Typography variant="caption" color="text.secondary">Activated</Typography>
                    <Typography variant="body2">{new Date(zone.activated_at).toLocaleString()}</Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>DNS Records Summary</Typography>
              <Divider sx={{ my: 2 }} />
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Total Records</Typography>
                  <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{dnsRecords.length}</Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">Proxied Records</Typography>
                  <Typography variant="h6" sx={{ color: 'warning.main' }}>
                    {dnsRecords.filter(r => r.proxied).length}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2">DNS-Only Records</Typography>
                  <Typography variant="h6" sx={{ color: 'info.main' }}>
                    {dnsRecords.filter(r => !r.proxied).length}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Alert severity="info" icon={<InfoIcon />}>
            {zone.status === 'pending' ? (
              <>
                <strong>Action Required:</strong> Update your nameservers at your domain registrar to activate this zone.
                Copy the nameservers from the "Nameservers" tab.
              </>
            ) : (
              <>
                <strong>Zone Active:</strong> Your domain is now using Cloudflare nameservers. Changes to DNS records will propagate automatically.
              </>
            )}
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
};

export default OverviewTab;
