import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  FormControlLabel,
  Switch,
  Alert,
  Snackbar,
  Tooltip,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  HourglassEmpty as ExpiringIcon,
  Group as GroupIcon
} from '@mui/icons-material';

const InviteCodesManagement = () => {
  const [codes, setCodes] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openEditDialog, setOpenEditDialog] = useState(false);
  const [selectedCode, setSelectedCode] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Form state for creating new code
  const [newCode, setNewCode] = useState({
    tier_code: 'vip_founder',
    max_uses: null,
    expires_in_days: null,
    notes: ''
  });

  // Form state for editing code
  const [editData, setEditData] = useState({
    is_active: true,
    max_uses: null,
    expires_at: null,
    notes: ''
  });

  useEffect(() => {
    loadCodes();
    loadTiers();
  }, []);

  const loadCodes = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/admin/invite-codes/', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load invite codes');
      }

      const data = await response.json();
      setCodes(data);
    } catch (error) {
      console.error('Error loading invite codes:', error);
      showSnackbar('Failed to load invite codes', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadTiers = async () => {
    try {
      const response = await fetch('/api/v1/admin/tiers/', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load tiers');
      }

      const data = await response.json();
      setTiers(data);
    } catch (error) {
      console.error('Error loading tiers:', error);
    }
  };

  const handleGenerateCode = async () => {
    try {
      const response = await fetch('/api/v1/admin/invite-codes/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(newCode)
      });

      if (!response.ok) {
        throw new Error('Failed to generate invite code');
      }

      const data = await response.json();
      showSnackbar(`Invite code generated: ${data.code}`, 'success');
      setOpenDialog(false);
      setNewCode({
        tier_code: 'vip_founder',
        max_uses: null,
        expires_in_days: null,
        notes: ''
      });
      loadCodes();
    } catch (error) {
      console.error('Error generating code:', error);
      showSnackbar('Failed to generate invite code', 'error');
    }
  };

  const handleUpdateCode = async () => {
    try {
      const response = await fetch(`/api/v1/admin/invite-codes/${selectedCode.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(editData)
      });

      if (!response.ok) {
        throw new Error('Failed to update invite code');
      }

      showSnackbar('Invite code updated successfully', 'success');
      setOpenEditDialog(false);
      setSelectedCode(null);
      loadCodes();
    } catch (error) {
      console.error('Error updating code:', error);
      showSnackbar('Failed to update invite code', 'error');
    }
  };

  const handleDeleteCode = async (codeId, codeName) => {
    if (!window.confirm(`Are you sure you want to delete invite code ${codeName}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/invite-codes/${codeId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete invite code');
      }

      showSnackbar('Invite code deleted successfully', 'success');
      loadCodes();
    } catch (error) {
      console.error('Error deleting code:', error);
      showSnackbar('Failed to delete invite code', 'error');
    }
  };

  const handleCopyCode = (code) => {
    navigator.clipboard.writeText(code);
    showSnackbar('Code copied to clipboard', 'success');
  };

  const handleEditClick = (code) => {
    setSelectedCode(code);
    setEditData({
      is_active: code.is_active,
      max_uses: code.max_uses,
      expires_at: code.expires_at ? new Date(code.expires_at).toISOString().split('T')[0] : null,
      notes: code.notes || ''
    });
    setOpenEditDialog(true);
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const getStatusChip = (code) => {
    if (!code.is_active) {
      return <Chip label="Inactive" color="default" size="small" icon={<CancelIcon />} />;
    }
    if (code.is_expired) {
      return <Chip label="Expired" color="error" size="small" icon={<CancelIcon />} />;
    }
    if (code.is_exhausted) {
      return <Chip label="Exhausted" color="warning" size="small" icon={<CancelIcon />} />;
    }
    if (code.expires_at && new Date(code.expires_at) < new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)) {
      return <Chip label="Active (Expiring Soon)" color="warning" size="small" icon={<ExpiringIcon />} />;
    }
    return <Chip label="Active" color="success" size="small" icon={<CheckCircleIcon />} />;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  const formatRemaining = (code) => {
    if (code.max_uses === null) {
      return '∞ (Unlimited)';
    }
    return `${code.remaining_uses} / ${code.max_uses}`;
  };

  // Calculate summary statistics
  const stats = {
    total: codes.length,
    active: codes.filter(c => c.is_active && !c.is_expired && !c.is_exhausted).length,
    expired: codes.filter(c => c.is_expired).length,
    exhausted: codes.filter(c => c.is_exhausted).length,
    totalRedemptions: codes.reduce((sum, c) => sum + c.redemption_count, 0)
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Invite Code Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setOpenDialog(true)}
        >
          Generate New Code
        </Button>
      </Box>

      {/* Summary Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Codes</Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Active</Typography>
              <Typography variant="h4" color="success.main">{stats.active}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Expired</Typography>
              <Typography variant="h4" color="error.main">{stats.expired}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Exhausted</Typography>
              <Typography variant="h4" color="warning.main">{stats.exhausted}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={2.4}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Redemptions</Typography>
              <Typography variant="h4">{stats.totalRedemptions}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Codes Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Code</TableCell>
              <TableCell>Tier</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Remaining Uses</TableCell>
              <TableCell>Redemptions</TableCell>
              <TableCell>Expires</TableCell>
              <TableCell>Created By</TableCell>
              <TableCell>Notes</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : codes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  No invite codes found
                </TableCell>
              </TableRow>
            ) : (
              codes.map((code) => (
                <TableRow key={code.id}>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2" fontFamily="monospace">
                        {code.code}
                      </Typography>
                      <Tooltip title="Copy code">
                        <IconButton size="small" onClick={() => handleCopyCode(code.code)}>
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip label={code.tier_name || code.tier_code} size="small" />
                  </TableCell>
                  <TableCell>{getStatusChip(code)}</TableCell>
                  <TableCell>{formatRemaining(code)}</TableCell>
                  <TableCell>
                    <Chip
                      label={code.redemption_count}
                      size="small"
                      icon={<GroupIcon />}
                      color={code.redemption_count > 0 ? 'primary' : 'default'}
                    />
                  </TableCell>
                  <TableCell>{formatDate(code.expires_at)}</TableCell>
                  <TableCell>{code.created_by || 'System'}</TableCell>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                      {code.notes || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton size="small" onClick={() => handleEditClick(code)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Delete">
                      <IconButton
                        size="small"
                        onClick={() => handleDeleteCode(code.id, code.code)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Generate Code Dialog */}
      <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Generate New Invite Code</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Subscription Tier</InputLabel>
              <Select
                value={newCode.tier_code}
                onChange={(e) => setNewCode({ ...newCode, tier_code: e.target.value })}
                label="Subscription Tier"
              >
                {tiers.map((tier) => (
                  <MenuItem key={tier.tier_code} value={tier.tier_code}>
                    {tier.tier_name} ({tier.tier_code})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Max Uses (leave blank for unlimited)"
              type="number"
              value={newCode.max_uses || ''}
              onChange={(e) => setNewCode({ ...newCode, max_uses: e.target.value ? parseInt(e.target.value) : null })}
              helperText="Number of times this code can be redeemed"
              fullWidth
            />

            <TextField
              label="Expires in Days (leave blank for no expiration)"
              type="number"
              value={newCode.expires_in_days || ''}
              onChange={(e) => setNewCode({ ...newCode, expires_in_days: e.target.value ? parseInt(e.target.value) : null })}
              helperText="Days until this code expires"
              fullWidth
            />

            <TextField
              label="Notes"
              multiline
              rows={3}
              value={newCode.notes}
              onChange={(e) => setNewCode({ ...newCode, notes: e.target.value })}
              helperText="Admin notes (not visible to users)"
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDialog(false)}>Cancel</Button>
          <Button onClick={handleGenerateCode} variant="contained">
            Generate Code
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Code Dialog */}
      <Dialog open={openEditDialog} onClose={() => setOpenEditDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Invite Code</DialogTitle>
        <DialogContent>
          {selectedCode && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
              <Alert severity="info">
                Code: <strong>{selectedCode.code}</strong>
              </Alert>

              <FormControlLabel
                control={
                  <Switch
                    checked={editData.is_active}
                    onChange={(e) => setEditData({ ...editData, is_active: e.target.checked })}
                  />
                }
                label="Active"
              />

              <TextField
                label="Max Uses"
                type="number"
                value={editData.max_uses || ''}
                onChange={(e) => setEditData({ ...editData, max_uses: e.target.value ? parseInt(e.target.value) : null })}
                helperText="Leave blank for unlimited"
                fullWidth
              />

              <TextField
                label="Expiration Date"
                type="date"
                value={editData.expires_at || ''}
                onChange={(e) => setEditData({ ...editData, expires_at: e.target.value || null })}
                InputLabelProps={{ shrink: true }}
                helperText="Leave blank for no expiration"
                fullWidth
              />

              <TextField
                label="Notes"
                multiline
                rows={3}
                value={editData.notes}
                onChange={(e) => setEditData({ ...editData, notes: e.target.value })}
                fullWidth
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEditDialog(false)}>Cancel</Button>
          <Button onClick={handleUpdateCode} variant="contained">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          variant="filled"
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default InviteCodesManagement;
