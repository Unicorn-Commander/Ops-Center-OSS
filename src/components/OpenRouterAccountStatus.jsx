import React, { useState } from 'react';
import {
  Card, CardContent, Typography, Button, Chip, Alert, Box, LinearProgress,
  Dialog, DialogTitle, DialogContent, DialogContentText, DialogActions,
  CircularProgress
} from '@mui/material';
import { Sync, Delete, Add, CheckCircle, Warning } from '@mui/icons-material';

export default function OpenRouterAccountStatus({ account, onRefresh }) {
  const [syncing, setSyncing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const syncBalance = async () => {
    try {
      setSyncing(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/credits/openrouter/sync', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to sync balance');
      }

      const data = await response.json();
      setSuccess(`Balance synced: $${data.free_credits_remaining?.toFixed(2) || '0.00'} remaining`);

      if (onRefresh) {
        setTimeout(() => onRefresh(), 1000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setSyncing(false);
    }
  };

  const createAccount = async () => {
    try {
      setCreating(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/credits/openrouter/create', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create account');
      }

      const data = await response.json();
      setSuccess(`Account created with ${data.email}`);

      if (onRefresh) {
        setTimeout(() => onRefresh(), 1000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setCreating(false);
    }
  };

  const confirmDelete = () => {
    setDeleteDialogOpen(true);
  };

  const deleteAccount = async () => {
    try {
      setDeleting(true);
      setError(null);
      setSuccess(null);
      setDeleteDialogOpen(false);

      const response = await fetch('/api/v1/credits/openrouter/delete', {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to delete account');
      }

      setSuccess('Account deleted successfully');

      if (onRefresh) {
        setTimeout(() => onRefresh(), 1000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  const getFreeCreditsPercent = () => {
    if (!account?.free_credits_remaining) return 0;
    return (account.free_credits_remaining / 10) * 100;
  };

  const getLastSyncedText = () => {
    if (!account?.last_synced) return 'Never';
    const date = new Date(account.last_synced);
    const now = new Date();
    const diffMinutes = Math.floor((now - date) / 60000);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;
    if (diffMinutes < 1440) return `${Math.floor(diffMinutes / 60)}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          OpenRouter Account
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {account ? (
          <>
            {/* Account Email */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Account Email
              </Typography>
              <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                {account.openrouter_email}
              </Typography>
              <Chip
                label="Active"
                color="success"
                size="small"
                icon={<CheckCircle />}
                sx={{ mt: 1 }}
              />
            </Box>

            {/* Free Credits Remaining */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Free Credits Remaining
              </Typography>
              <Typography variant="h4" color="success.main" sx={{ mb: 1 }}>
                ${account.free_credits_remaining?.toFixed(2) || '0.00'}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={getFreeCreditsPercent()}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {getFreeCreditsPercent().toFixed(0)}% of $10.00 free tier
              </Typography>
            </Box>

            {/* Last Synced */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" color="textSecondary">
                Last synced: {getLastSyncedText()}
              </Typography>
            </Box>

            {/* Low Balance Warning */}
            {account.free_credits_remaining < 2 && (
              <Alert severity="warning" sx={{ mb: 2 }} icon={<Warning />}>
                <Typography variant="body2">
                  Free credits running low! Consider upgrading to a paid plan.
                </Typography>
              </Alert>
            )}

            {/* Actions */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="outlined"
                startIcon={syncing ? <CircularProgress size={16} /> : <Sync />}
                onClick={syncBalance}
                disabled={syncing}
              >
                Sync Balance
              </Button>
              <Button
                variant="outlined"
                color="error"
                startIcon={<Delete />}
                onClick={confirmDelete}
                disabled={deleting}
              >
                Delete Account
              </Button>
            </Box>
          </>
        ) : (
          <Box sx={{ textAlign: 'center', py: 3 }}>
            <Typography variant="body1" color="textSecondary" sx={{ mb: 2 }}>
              No OpenRouter account created yet
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
              Create a free OpenRouter account to get $10 in free credits for testing AI models
            </Typography>
            <Button
              variant="contained"
              startIcon={creating ? <CircularProgress size={16} /> : <Add />}
              onClick={createAccount}
              disabled={creating}
            >
              Create Account
            </Button>
          </Box>
        )}
      </CardContent>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
      >
        <DialogTitle>Delete OpenRouter Account?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete your OpenRouter account? This will remove:
          </DialogContentText>
          <Box component="ul" sx={{ mt: 2 }}>
            <li>Account email: {account?.openrouter_email}</li>
            <li>Remaining free credits: ${account?.free_credits_remaining?.toFixed(2) || '0.00'}</li>
            <li>All associated usage history</li>
          </Box>
          <DialogContentText sx={{ mt: 2, color: 'error.main' }}>
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button onClick={deleteAccount} color="error" variant="contained">
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </Card>
  );
}
