import React from 'react';
import { Box, Chip, Typography } from '@mui/material';

const UserGroupsTab = ({ user }) => {
  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Member of {user.groups?.length || 0} groups
      </Typography>
      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {user.groups?.map(group => (
          <Chip
            key={group}
            label={group}
            onDelete={group !== 'sudo' ? () => {} : undefined}
            color={group === 'sudo' ? 'secondary' : 'default'}
          />
        ))}
      </Box>
    </Box>
  );
};

export default UserGroupsTab;
