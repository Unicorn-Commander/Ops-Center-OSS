import React from 'react';
import { Alert } from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';

const WarningsBanner = ({ accountInfo }) => {
  return (
    <>
      {/* Rate Limit Warning */}
      {accountInfo.rate_limit && accountInfo.rate_limit.percent_used > 80 && (
        <Alert severity="warning" sx={{ mb: 3 }} icon={<WarningIcon />}>
          <strong>Rate Limit Warning:</strong> You've used {accountInfo.rate_limit.percent_used.toFixed(1)}% of your API rate limit.
          Requests may be throttled. Resets at {new Date(accountInfo.rate_limit.reset_at).toLocaleTimeString()}.
        </Alert>
      )}

      {/* Pending Limit Warning */}
      {accountInfo.zones?.at_limit && (
        <Alert severity="warning" sx={{ mb: 3 }} icon={<WarningIcon />}>
          <strong>Pending Zone Limit Reached:</strong> You have {accountInfo.zones.pending} pending zones (max {accountInfo.zones.limit}).
          New zones will be queued until existing zones become active.
        </Alert>
      )}
    </>
  );
};

export default WarningsBanner;
