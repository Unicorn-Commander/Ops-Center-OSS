import React from 'react';
import { Snackbar, Alert } from '@mui/material';

/**
 * Toast - Toast notification wrapper
 *
 * Props:
 * - toast: Object { open, message, severity }
 * - onClose: Function to handle close
 */
const Toast = ({ toast, onClose }) => (
  <Snackbar
    open={toast.open}
    autoHideDuration={6000}
    onClose={onClose}
    anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
  >
    <Alert
      onClose={onClose}
      severity={toast.severity}
      sx={{ width: '100%' }}
    >
      {toast.message}
    </Alert>
  </Snackbar>
);

export default Toast;
