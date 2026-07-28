import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Alert,
  Typography,
  Box,
} from '@mui/material';
import { AlertTriangle } from 'lucide-react';

const SudoToggleDialog = ({ open, sudoConfirm, onClose, onConfirm }) => {
  if (!sudoConfirm) return null;

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>
        {sudoConfirm.currentHasSudo ? 'Remove Sudo Access' : 'Grant Sudo Access'}
      </DialogTitle>
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AlertTriangle size={16} style={{ marginRight: 8 }} />
            {sudoConfirm.currentHasSudo
              ? 'Removing sudo access will revoke administrative privileges'
              : 'Granting sudo access gives administrative privileges'}
          </Box>
        </Alert>
        <Typography>
          Are you sure you want to {sudoConfirm.currentHasSudo ? 'remove' : 'grant'} sudo access for{' '}
          <strong>{sudoConfirm.username}</strong>?
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          color={sudoConfirm.currentHasSudo ? 'error' : 'primary'}
          onClick={() => onConfirm(sudoConfirm.username, sudoConfirm.currentHasSudo)}
        >
          {sudoConfirm.currentHasSudo ? 'Remove Access' : 'Grant Access'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default SudoToggleDialog;
