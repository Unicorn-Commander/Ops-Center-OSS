import React from 'react';
import { Grid, Typography } from '@mui/material';

const UserOverviewTab = ({ user }) => {
  return (
    <Grid container spacing={2}>
      <Grid item xs={6}>
        <Typography variant="body2" color="text.secondary">Username</Typography>
        <Typography variant="body1">{user.username}</Typography>
      </Grid>
      <Grid item xs={6}>
        <Typography variant="body2" color="text.secondary">UID</Typography>
        <Typography variant="body1">{user.uid}</Typography>
      </Grid>
      <Grid item xs={6}>
        <Typography variant="body2" color="text.secondary">GID</Typography>
        <Typography variant="body1">{user.gid}</Typography>
      </Grid>
      <Grid item xs={6}>
        <Typography variant="body2" color="text.secondary">Shell</Typography>
        <Typography variant="body1">
          <code>{user.shell}</code>
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Typography variant="body2" color="text.secondary">Home Directory</Typography>
        <Typography variant="body1">
          <code>{user.home}</code>
        </Typography>
      </Grid>
      <Grid item xs={12}>
        <Typography variant="body2" color="text.secondary">Last Login</Typography>
        <Typography variant="body1">
          {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}
        </Typography>
      </Grid>
    </Grid>
  );
};

export default UserOverviewTab;
