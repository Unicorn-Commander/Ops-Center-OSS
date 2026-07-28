import React from 'react';
import { Box, FormControlLabel, Checkbox, Alert } from '@mui/material';
import { Shield, AlertTriangle } from 'lucide-react';

const UserSudoTab = ({ user, onSudoToggle }) => {
  const hasSudo = user.groups?.includes('sudo');

  return (
    <Box>
      <FormControlLabel
        control={
          <Checkbox
            checked={hasSudo}
            onChange={(e) => {
              if (e.target.checked || hasSudo) {
                onSudoToggle({
                  username: user.username,
                  currentHasSudo: hasSudo,
                });
              }
            }}
          />
        }
        label={
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Shield size={16} style={{ marginRight: 8 }} />
            Grant sudo access
          </Box>
        }
      />

      {hasSudo ? (
        <Alert severity="warning" sx={{ mt: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AlertTriangle size={16} style={{ marginRight: 8 }} />
            This user has administrative privileges via sudo
          </Box>
        </Alert>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          This user does not have sudo access
        </Alert>
      )}
    </Box>
  );
};

export default UserSudoTab;
