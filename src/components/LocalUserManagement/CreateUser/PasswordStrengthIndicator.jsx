import React from 'react';
import { Box, LinearProgress, Typography } from '@mui/material';

const PasswordStrengthIndicator = ({ strength }) => {
  const getPasswordStrengthLabel = (strength) => {
    if (strength < 40) return { label: 'Weak', color: 'error' };
    if (strength < 70) return { label: 'Medium', color: 'warning' };
    return { label: 'Strong', color: 'success' };
  };

  const strengthInfo = getPasswordStrengthLabel(strength);

  return (
    <Box sx={{ mb: 2 }}>
      <LinearProgress
        variant="determinate"
        value={strength}
        color={strengthInfo.color}
        sx={{ mb: 0.5 }}
      />
      <Typography variant="caption" color="text.secondary">
        Password Strength: {strengthInfo.label}
      </Typography>
    </Box>
  );
};

export default PasswordStrengthIndicator;
