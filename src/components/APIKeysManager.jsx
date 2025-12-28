import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Alert,
  Paper,
  Tooltip,
  InputAdornment,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

const APIKeysManager = ({ userId, userEmail }) => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [selectedKey, setSelectedKey] = useState(null);
  const [newKeyData, setNewKeyData] = useState(null);
  const [showFullKey, setShowFullKey] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    expires_in_days: 90,
    scopes: {
      read: true,
      write: false,
      admin: false,
    },
  });

  useEffect(() => {
    if (userId) {
      fetchKeys();
    }
  }, [userId]);

  const fetchKeys = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/api-keys`, {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch API keys');

      const data = await response.json();
      setKeys(data.keys || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async () => {
    try {
      const response = await fetch(`/api/v1/admin/users/${userId}/api-keys`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to create API key');

      const data = await response.json();
      setNewKeyData(data);
      setCreateModalOpen(false);
      fetchKeys();

      // Reset form
      setFormData({
        name: '',
        expires_in_days: 90,
        scopes: {
          read: true,
          write: false,
          admin: false,
        },
      });
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRevokeKey = async () => {
    try {
      const response = await fetch(
        `/api/v1/admin/users/${userId}/api-keys/${selectedKey.id}`,
        {
          method: 'DELETE',
          credentials: 'include',
        }
      );

      if (!response.ok) throw new Error('Failed to revoke API key');

      setDeleteConfirmOpen(false);
      setSelectedKey(null);
      fetchKeys();
    } catch (err) {
      setError(err.message);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const getScopeChips = (scopes) => {
    return Object.entries(scopes)
      .filter(([, enabled]) => enabled)
      .map(([scope]) => (
        <Chip
          key={scope}
          label={scope}
          size="small"
          color={scope === 'admin' ? 'error' : 'default'}
          sx={{ mr: 0.5 }}
        />
      ));
  };

  const isExpired = (expiresAt) => {
    if (!expiresAt) return false;
    return new Date(expiresAt) < new Date();
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'Never';
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">API Keys</Typography>
        <Box>
          <IconButton onClick={fetchKeys} size="small" sx={{ mr: 1 }}>
            <RefreshIcon />
          </IconButton>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateModalOpen(true)}
            size="small"
          >
            Generate Key
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Key Prefix</TableCell>
              <TableCell>Scopes</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Last Used</TableCell>
              <TableCell>Expires</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {keys.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography variant="body2" color="text.secondary">
                    No API keys found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              keys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell>{key.name}</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <code style={{ fontSize: '12px' }}>{key.key_prefix}...</code>
                      <Tooltip title="Copy prefix">
                        <IconButton
                          size="small"
                          onClick={() => copyToClipboard(key.key_prefix)}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {getScopeChips(key.scopes)}
                    </Box>
                  </TableCell>
                  <TableCell>{formatDate(key.created_at)}</TableCell>
                  <TableCell>
                    {key.last_used_at ? formatDate(key.last_used_at) : 'Never'}
                  </TableCell>
                  <TableCell>{formatDate(key.expires_at)}</TableCell>
                  <TableCell>
                    <Chip
                      label={
                        !key.is_active
                          ? 'Revoked'
                          : isExpired(key.expires_at)
                          ? 'Expired'
                          : 'Active'
                      }
                      color={
                        !key.is_active
                          ? 'error'
                          : isExpired(key.expires_at)
                          ? 'warning'
                          : 'success'
                      }
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Revoke Key">
                      <IconButton
                        size="small"
                        onClick={() => {
                          setSelectedKey(key);
                          setDeleteConfirmOpen(true);
                        }}
                        color="error"
                        disabled={!key.is_active}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create API Key Modal */}
      <Dialog
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Generate New API Key</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Key Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Production API Key"
              sx={{ mb: 2 }}
              required
            />

            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Expiration</InputLabel>
              <Select
                value={formData.expires_in_days}
                label="Expiration"
                onChange={(e) =>
                  setFormData({ ...formData, expires_in_days: e.target.value })
                }
              >
                <MenuItem value={30}>30 days</MenuItem>
                <MenuItem value={60}>60 days</MenuItem>
                <MenuItem value={90}>90 days</MenuItem>
                <MenuItem value={180}>180 days</MenuItem>
                <MenuItem value={365}>1 year</MenuItem>
                <MenuItem value={null}>Never expires</MenuItem>
              </Select>
            </FormControl>

            <Typography variant="subtitle2" gutterBottom>
              Scopes
            </Typography>
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.scopes.read}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scopes: { ...formData.scopes, read: e.target.checked },
                    })
                  }
                />
              }
              label="Read"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.scopes.write}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scopes: { ...formData.scopes, write: e.target.checked },
                    })
                  }
                />
              }
              label="Write"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={formData.scopes.admin}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      scopes: { ...formData.scopes, admin: e.target.checked },
                    })
                  }
                />
              }
              label="Admin"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateModalOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateKey}
            disabled={!formData.name}
          >
            Generate
          </Button>
        </DialogActions>
      </Dialog>

      {/* New Key Display Modal */}
      <Dialog
        open={Boolean(newKeyData)}
        onClose={() => setNewKeyData(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>API Key Generated</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This key will only be shown once. Store it securely!
          </Alert>

          <TextField
            fullWidth
            label="API Key"
            value={newKeyData?.key || ''}
            InputProps={{
              readOnly: true,
              type: showFullKey ? 'text' : 'password',
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    onClick={() => setShowFullKey(!showFullKey)}
                    edge="end"
                  >
                    {showFullKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                  </IconButton>
                  <IconButton
                    onClick={() => copyToClipboard(newKeyData?.key || '')}
                    edge="end"
                  >
                    <CopyIcon />
                  </IconButton>
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2, fontFamily: 'monospace' }}
          />

          <Typography variant="body2" color="text.secondary">
            Name: {newKeyData?.name}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Expires: {formatDate(newKeyData?.expires_at)}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Scopes: {Object.entries(newKeyData?.scopes || {}).filter(([, v]) => v).map(([k]) => k).join(', ')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button variant="contained" onClick={() => setNewKeyData(null)}>
            I've Saved It
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Modal */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Revoke API Key?</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to revoke the API key "{selectedKey?.name}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>Cancel</Button>
          <Button variant="contained" color="error" onClick={handleRevokeKey}>
            Revoke Key
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default APIKeysManager;
