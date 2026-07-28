import React from 'react';
import { Grid, Card, CardContent, Typography } from '@mui/material';

const ZoneMetricsCards = ({ accountInfo }) => {
  if (!accountInfo.zones) return null;

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      <Grid item xs={12} sm={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" variant="body2">Total Zones</Typography>
            <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
              {accountInfo.zones.total || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" variant="body2">Active Zones</Typography>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
              {accountInfo.zones.active || 0}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" variant="body2">Pending Zones</Typography>
            <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
              {accountInfo.zones.pending || 0} / {accountInfo.zones.limit || 3}
            </Typography>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} sm={3}>
        <Card>
          <CardContent>
            <Typography color="text.secondary" variant="body2">Plan</Typography>
            <Typography variant="h5" sx={{ fontWeight: 'bold', textTransform: 'uppercase' }}>
              {accountInfo.plan || 'FREE'}
            </Typography>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default ZoneMetricsCards;
