import React, { useState } from 'react';
import {
  Box, Card, CardContent, Typography, TextField, Button, Alert,
  Autocomplete, Grid, Chip, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, IconButton, Dialog, DialogTitle, DialogContent,
  DialogActions, FormControl, InputLabel, Select, MenuItem, CircularProgress
} from '@mui/material';
import {
  Add, History, Undo, Search, Download
} from '@mui/icons-material';

export default function CreditAllocation() {
  const [selectedUser, setSelectedUser] = useState(null);
  const [amount, setAmount] = useState('');
  const [reason, setReason] = useState('');
  const [allocating, setAllocating] = useState(false);
  const [refunding, setRefunding] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [allocationHistory, setAllocationHistory] = useState([]);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [bulkMode, setBulkMode] = useState(false);
  const [bulkAmount, setBulkAmount] = useState('');
  const [bulkFilter, setBulkFilter] = useState('all'); // all, tier, role

  // Search for users
  const searchUsers = async (query) => {
    if (!query || query.length < 2) {
      setSearchResults([]);
      return;
    }

    try {
      setLoading(true);
      const response = await fetch(`/api/v1/admin/users?search=${encodeURIComponent(query)}&limit=10`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (!response.ok) throw new Error('Search failed');

      const data = await response.json();
      setSearchResults(data.users || []);
    } catch (err) {
      console.error('User search error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Allocate credits to a specific user
  const allocateCredits = async () => {
    if (!selectedUser || !amount || parseFloat(amount) <= 0) {
      setError('Please select a user and enter a valid amount');
      return;
    }

    try {
      setAllocating(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/admin/credits/allocate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          user_id: selectedUser.id,
          amount: parseFloat(amount),
          reason: reason || 'Manual allocation by admin'
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Allocation failed');
      }

      const data = await response.json();
      setSuccess(`Successfully allocated $${amount} to ${selectedUser.email}`);

      // Reset form
      setSelectedUser(null);
      setAmount('');
      setReason('');
      setSearchResults([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setAllocating(false);
    }
  };

  // Bulk allocate credits
  const bulkAllocateCredits = async () => {
    if (!bulkAmount || parseFloat(bulkAmount) <= 0) {
      setError('Please enter a valid amount');
      return;
    }

    try {
      setAllocating(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/admin/credits/bulk-allocate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          amount: parseFloat(bulkAmount),
          filter: bulkFilter,
          reason: reason || 'Bulk allocation by admin'
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Bulk allocation failed');
      }

      const data = await response.json();
      setSuccess(`Successfully allocated $${bulkAmount} to ${data.users_affected} users`);

      // Reset form
      setBulkAmount('');
      setReason('');
    } catch (err) {
      setError(err.message);
    } finally {
      setAllocating(false);
    }
  };

  // Refund credits (create negative transaction)
  const refundCredits = async () => {
    if (!selectedUser || !amount || parseFloat(amount) <= 0) {
      setError('Please select a user and enter a valid amount');
      return;
    }

    try {
      setRefunding(true);
      setError(null);
      setSuccess(null);

      const response = await fetch('/api/v1/admin/credits/refund', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          user_id: selectedUser.id,
          amount: parseFloat(amount),
          reason: reason || 'Manual refund by admin'
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Refund failed');
      }

      const data = await response.json();
      setSuccess(`Successfully refunded $${amount} from ${selectedUser.email}`);

      // Reset form
      setSelectedUser(null);
      setAmount('');
      setReason('');
      setSearchResults([]);
    } catch (err) {
      setError(err.message);
    } finally {
      setRefunding(false);
    }
  };

  // Load allocation history
  const loadHistory = async () => {
    try {
      const response = await fetch('/api/v1/admin/credits/history?limit=50', {
        headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (!response.ok) throw new Error('Failed to load history');

      const data = await response.json();
      setAllocationHistory(data.allocations || []);
      setHistoryDialogOpen(true);
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Credit Allocation Management
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

      <Grid container spacing={3}>
        {/* Single User Allocation */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
                <Typography variant="h6">Allocate to Single User</Typography>
                <Chip
                  label={bulkMode ? 'Bulk Mode' : 'Single Mode'}
                  color={bulkMode ? 'secondary' : 'primary'}
                  onClick={() => setBulkMode(!bulkMode)}
                  clickable
                />
              </Box>

              {!bulkMode ? (
                <>
                  {/* User Search */}
                  <Autocomplete
                    options={searchResults}
                    getOptionLabel={(option) => `${option.email} (${option.username})`}
                    value={selectedUser}
                    onChange={(e, newValue) => setSelectedUser(newValue)}
                    onInputChange={(e, value) => searchUsers(value)}
                    loading={loading}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Search User"
                        placeholder="Type email or username..."
                        InputProps={{
                          ...params.InputProps,
                          startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />,
                          endAdornment: (
                            <>
                              {loading ? <CircularProgress size={20} /> : null}
                              {params.InputProps.endAdornment}
                            </>
                          )
                        }}
                      />
                    )}
                    sx={{ mb: 2 }}
                  />

                  {/* Amount Input */}
                  <TextField
                    label="Amount ($)"
                    type="number"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    fullWidth
                    inputProps={{ min: 0, step: 0.01 }}
                    sx={{ mb: 2 }}
                  />

                  {/* Reason Input */}
                  <TextField
                    label="Reason (Optional)"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    fullWidth
                    multiline
                    rows={2}
                    sx={{ mb: 2 }}
                  />

                  {/* Action Buttons */}
                  <Box sx={{ display: 'flex', gap: 2 }}>
                    <Button
                      variant="contained"
                      startIcon={allocating ? <CircularProgress size={16} /> : <Add />}
                      onClick={allocateCredits}
                      disabled={!selectedUser || !amount || allocating}
                      fullWidth
                    >
                      Allocate Credits
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={refunding ? <CircularProgress size={16} /> : <Undo />}
                      onClick={refundCredits}
                      disabled={!selectedUser || !amount || refunding}
                      fullWidth
                    >
                      Refund
                    </Button>
                  </Box>
                </>
              ) : (
                <>
                  {/* Bulk Allocation */}
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>User Filter</InputLabel>
                    <Select
                      value={bulkFilter}
                      onChange={(e) => setBulkFilter(e.target.value)}
                      label="User Filter"
                    >
                      <MenuItem value="all">All Users</MenuItem>
                      <MenuItem value="free">Free Tier Users</MenuItem>
                      <MenuItem value="starter">Starter Tier Users</MenuItem>
                      <MenuItem value="professional">Professional Tier Users</MenuItem>
                      <MenuItem value="enterprise">Enterprise Tier Users</MenuItem>
                    </Select>
                  </FormControl>

                  <TextField
                    label="Amount per User ($)"
                    type="number"
                    value={bulkAmount}
                    onChange={(e) => setBulkAmount(e.target.value)}
                    fullWidth
                    inputProps={{ min: 0, step: 0.01 }}
                    sx={{ mb: 2 }}
                  />

                  <TextField
                    label="Reason (Optional)"
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    fullWidth
                    multiline
                    rows={2}
                    sx={{ mb: 2 }}
                  />

                  <Button
                    variant="contained"
                    startIcon={allocating ? <CircularProgress size={16} /> : <Add />}
                    onClick={bulkAllocateCredits}
                    disabled={!bulkAmount || allocating}
                    fullWidth
                  >
                    Bulk Allocate
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Quick Stats & Actions */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Quick Actions</Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<History />}
                  onClick={loadHistory}
                  fullWidth
                >
                  View Allocation History
                </Button>

                <Button
                  variant="outlined"
                  startIcon={<Download />}
                  href="/api/v1/admin/credits/export"
                  fullWidth
                >
                  Export All Transactions
                </Button>
              </Box>

              {/* Info Box */}
              <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                <Typography variant="body2" fontWeight={600} gutterBottom>
                  Important Notes:
                </Typography>
                <Typography variant="caption" display="block">
                  • Allocations are immediate and create allocation transactions
                </Typography>
                <Typography variant="caption" display="block">
                  • Refunds create negative adjustment transactions
                </Typography>
                <Typography variant="caption" display="block">
                  • Bulk allocations apply to all users matching the filter
                </Typography>
                <Typography variant="caption" display="block">
                  • All operations are logged in the audit trail
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Allocation History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Allocation History</DialogTitle>
        <DialogContent>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Date</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Amount</TableCell>
                  <TableCell>Reason</TableCell>
                  <TableCell>Admin</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {allocationHistory.map((allocation) => (
                  <TableRow key={allocation.id}>
                    <TableCell>{new Date(allocation.created_at).toLocaleString()}</TableCell>
                    <TableCell>{allocation.user_email}</TableCell>
                    <TableCell>
                      <Typography
                        variant="body2"
                        color={allocation.amount > 0 ? 'success.main' : 'error.main'}
                        fontWeight={600}
                      >
                        {allocation.amount > 0 ? '+' : ''}${allocation.amount}
                      </Typography>
                    </TableCell>
                    <TableCell>{allocation.reason}</TableCell>
                    <TableCell>{allocation.admin_email}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
