/**
 * CreateOrganizationModal - Modal for creating new organizations
 *
 * Reusable modal component for organization creation
 * Extracted from CreateUserModal for standalone use
 *
 * Created: October 19, 2025
 * Status: Production Ready
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';

export default function CreateOrganizationModal({ open, onClose, onCreated }) {
  const [orgData, setOrgData] = useState({
    name: '',
    description: '',
    domain: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log('Creating organization with data:', orgData);

      const response = await fetch('/api/v1/org', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(orgData),
      });

      console.log('Response status:', response.status);

      if (!response.ok) {
        let errorMessage = 'Failed to create organization';
        try {
          const errorData = await response.json();
          console.error('Backend error response:', errorData);
          errorMessage = errorData.detail || errorData.message || JSON.stringify(errorData);
        } catch (e) {
          const text = await response.text();
          console.error('Backend error text:', text);
          errorMessage = text || `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const newOrg = await response.json();
      console.log('Organization created successfully:', newOrg);

      // Call onCreated callback with new organization
      if (onCreated) {
        onCreated(newOrg);
      }

      // Reset form and close modal
      setOrgData({ name: '', description: '', domain: '' });
      onClose();
    } catch (err) {
      console.error('Error creating organization:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setOrgData({ name: '', description: '', domain: '' });
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Organization</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Box sx={{ pt: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Organization Name"
                required
                value={orgData.name}
                onChange={(e) => setOrgData({ ...orgData, name: e.target.value })}
                helperText="Enter a unique name for your organization"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={orgData.description}
                onChange={(e) => setOrgData({ ...orgData, description: e.target.value })}
                helperText="Describe what this organization is for"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Domain (optional)"
                placeholder="example.com"
                value={orgData.domain}
                onChange={(e) => setOrgData({ ...orgData, domain: e.target.value })}
                helperText="Your organization's domain name"
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleCreate}
          disabled={!orgData.name || loading}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            '&:hover': {
              background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
            },
          }}
        >
          {loading ? <CircularProgress size={24} /> : 'Create Organization'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
