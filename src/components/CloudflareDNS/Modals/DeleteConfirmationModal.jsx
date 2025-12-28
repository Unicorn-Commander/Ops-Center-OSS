import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Button,
  Alert,
} from '@mui/material';

/**
 * DeleteConfirmationModal - Confirmation dialog for zone or DNS record deletion
 *
 * Props:
 * - open: Boolean - modal visibility
 * - onClose: Function - close handler
 * - onConfirm: Function - delete confirmation handler
 * - deleteTarget: Object | null - zone or DNS record to delete
 */
const DeleteConfirmationModal = ({ open, onClose, onConfirm, deleteTarget }) => {
  if (!deleteTarget) return null;

  const isZone = deleteTarget.isZone;

  // Check if email-related DNS record
  const isEmailRecord = !isZone && (
    deleteTarget.type === 'MX' ||
    (deleteTarget.type === 'TXT' && (
      deleteTarget.content?.includes('v=spf1') ||
      deleteTarget.content?.includes('v=DMARC1') ||
      deleteTarget.name?.includes('dkim')
    ))
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
    >
      <DialogTitle>Delete {isZone ? 'Zone' : 'DNS Record'}</DialogTitle>
      <DialogContent>
        {isZone ? (
          <>
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                ⚠️ WARNING: This will delete the entire zone!
              </Typography>
              <Typography variant="body2">
                All DNS records and settings will be permanently deleted.
              </Typography>
            </Alert>
            <Typography variant="body1">
              Are you sure you want to delete the zone <strong>{deleteTarget.domain}</strong>?
            </Typography>
          </>
        ) : (
          <>
            {isEmailRecord && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  ⚠️ Email-Related Record
                </Typography>
                <Typography variant="body2">
                  This appears to be an email configuration record. Deleting it may affect email delivery.
                </Typography>
              </Alert>
            )}
            <Typography variant="body1" gutterBottom>
              Are you sure you want to delete this DNS record?
            </Typography>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="body2">
                <strong>Type:</strong> {deleteTarget.type}
              </Typography>
              <Typography variant="body2">
                <strong>Name:</strong> {deleteTarget.name}
              </Typography>
              <Typography variant="body2">
                <strong>Content:</strong> {deleteTarget.content}
              </Typography>
            </Box>
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={onConfirm}
          variant="contained"
          color="error"
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default DeleteConfirmationModal;
