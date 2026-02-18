/**
 * Granite API Keys Management Page
 * Admin interface for managing API keys for the Granite Extraction service.
 *
 * Features:
 * - View all API keys with status, creation date, last used
 * - Create new API keys (shown once on creation)
 * - Revoke existing keys
 * - Sync keys to extraction service
 * - View proxy status
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  CircularProgress,
  Card,
  CardContent,
  Grid,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as HealthyIcon,
  Cancel as UnhealthyIcon,
  Sync as SyncIcon,
  Key as KeyIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
const API_BASE = '/api/v1/granite-keys';

/**
 * Format date to readable string
 */
const formatDate = (dateStr) => {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Time ago helper
 */
const timeAgo = (dateStr) => {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);

  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return formatDate(dateStr);
};

/**
 * Create API Key Dialog
 */
const CreateKeyDialog = ({ open, onClose, onCreated }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [expiresDays, setExpiresDays] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Name is required');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(API_BASE + '/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name: name.trim(),
          description: description.trim() || null,
          expires_days: expiresDays ? parseInt(expiresDays) : null
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create API key');
      }

      const data = await response.json();
      onCreated(data);
      handleClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setExpiresDays('');
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New API Key</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

        <TextField
          autoFocus
          label="Key Name"
          placeholder="e.g., multistate-retirement-leads"
          fullWidth
          value={name}
          onChange={(e) => setName(e.target.value)}
          margin="normal"
          required
          helperText="A descriptive name to identify this key"
        />

        <TextField
          label="Description"
          placeholder="What this key is used for..."
          fullWidth
          multiline
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          margin="normal"
        />

        <FormControl fullWidth margin="normal">
          <InputLabel>Expiration</InputLabel>
          <Select
            value={expiresDays}
            onChange={(e) => setExpiresDays(e.target.value)}
            label="Expiration"
          >
            <MenuItem value="">Never expires</MenuItem>
            <MenuItem value="30">30 days</MenuItem>
            <MenuItem value="90">90 days</MenuItem>
            <MenuItem value="180">180 days</MenuItem>
            <MenuItem value="365">1 year</MenuItem>
          </Select>
        </FormControl>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>Cancel</Button>
        <Button
          onClick={handleCreate}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <AddIcon />}
        >
          Create Key
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Display New Key Dialog - Shows the key ONCE after creation
 */
const DisplayKeyDialog = ({ open, onClose, keyData }) => {
  const [copied, setCopied] = useState(false);
  const [showKey, setShowKey] = useState(true);

  const handleCopy = () => {
    navigator.clipboard.writeText(keyData?.api_key || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <KeyIcon color="primary" />
        API Key Created
      </DialogTitle>
      <DialogContent>
        <Alert severity="warning" sx={{ mb: 2 }}>
          <strong>Important:</strong> This is the only time you will see this API key.
          Copy it now and store it securely.
        </Alert>

        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          Key Name
        </Typography>
        <Typography variant="body1" sx={{ mb: 2 }}>
          {keyData?.name}
        </Typography>

        <Typography variant="subtitle2" color="text.secondary" gutterBottom>
          API Key
        </Typography>
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            fontFamily: 'monospace',
            fontSize: '0.9rem',
            wordBreak: 'break-all',
            backgroundColor: 'grey.100',
            display: 'flex',
            alignItems: 'center',
            gap: 1
          }}
        >
          <Box sx={{ flexGrow: 1 }}>
            {showKey ? keyData?.api_key : '•'.repeat(40)}
          </Box>
          <IconButton size="small" onClick={() => setShowKey(!showKey)}>
            {showKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
          </IconButton>
          <IconButton size="small" onClick={handleCopy} color={copied ? 'success' : 'default'}>
            <CopyIcon />
          </IconButton>
        </Paper>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Use this key in the <code>Authorization</code> header:
        </Typography>
        <Paper variant="outlined" sx={{ p: 1, mt: 1, fontFamily: 'monospace', fontSize: '0.8rem' }}>
          Authorization: Bearer {keyData?.api_key_prefix}...
        </Paper>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCopy} startIcon={<CopyIcon />}>
          {copied ? 'Copied!' : 'Copy Key'}
        </Button>
        <Button onClick={onClose} variant="contained">
          Done
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Confirm Revoke Dialog
 */
const RevokeDialog = ({ open, onClose, onConfirm, keyData, loading }) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <WarningIcon color="warning" />
        Revoke API Key?
      </DialogTitle>
      <DialogContent>
        <Typography>
          Are you sure you want to revoke the API key <strong>{keyData?.name}</strong>?
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          This action cannot be undone. Any applications using this key will stop working.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>Cancel</Button>
        <Button
          onClick={onConfirm}
          color="error"
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={16} /> : <DeleteIcon />}
        >
          Revoke Key
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Main Component
 */
const GraniteApiKeysManagement = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [proxyStatus, setProxyStatus] = useState(null);

  // Dialog states
  const [createOpen, setCreateOpen] = useState(false);
  const [displayKeyData, setDisplayKeyData] = useState(null);
  const [revokeKey, setRevokeKey] = useState(null);
  const [revoking, setRevoking] = useState(false);
  const [syncing, setSyncing] = useState(false);

  // Toast
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const fetchKeys = useCallback(async () => {
    try {
      const response = await fetch(API_BASE + '/', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch API keys');
      const data = await response.json();
      setKeys(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchProxyStatus = useCallback(async () => {
    try {
      const response = await fetch(API_BASE + '/status/proxy', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setProxyStatus(data);
      }
    } catch (err) {
      console.error('Failed to fetch proxy status:', err);
    }
  }, []);

  useEffect(() => {
    fetchKeys();
    fetchProxyStatus();

    // Auto-refresh every 30 seconds
    const interval = setInterval(() => {
      fetchKeys();
      fetchProxyStatus();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchKeys, fetchProxyStatus]);

  const handleKeyCreated = (newKey) => {
    setDisplayKeyData(newKey);
    fetchKeys(); // Refresh list
    setToast({ open: true, message: 'API key created successfully', severity: 'success' });
  };

  const handleRevoke = async () => {
    if (!revokeKey) return;

    setRevoking(true);
    try {
      const response = await fetch(`${API_BASE}/${revokeKey.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to revoke key');
      }

      fetchKeys();
      setRevokeKey(null);
      setToast({ open: true, message: 'API key revoked', severity: 'success' });
    } catch (err) {
      setToast({ open: true, message: err.message, severity: 'error' });
    } finally {
      setRevoking(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await fetch(`${API_BASE}/sync`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Sync failed');
      }

      const data = await response.json();
      setToast({
        open: true,
        message: data.success ? 'Proxy restarted successfully' : data.message,
        severity: data.success ? 'success' : 'warning'
      });
      fetchProxyStatus();
    } catch (err) {
      setToast({ open: true, message: err.message, severity: 'error' });
    } finally {
      setSyncing(false);
    }
  };

  const activeKeys = keys.filter(k => k.is_active);
  const revokedKeys = keys.filter(k => !k.is_active);

  return (
    <Box>
      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1, mb: 2 }}>
        <Button
          variant="outlined"
          startIcon={syncing ? <CircularProgress size={16} /> : <SyncIcon />}
          onClick={handleSync}
          disabled={syncing}
        >
          Sync & Restart Proxy
        </Button>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateOpen(true)}
        >
          Create Key
        </Button>
      </Box>

      {/* Status Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Active Keys
              </Typography>
              <Typography variant="h4">
                {activeKeys.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Revoked Keys
              </Typography>
              <Typography variant="h4" color="text.secondary">
                {revokedKeys.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary">
                Proxy Status
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {proxyStatus?.proxy_status === 'running' ? (
                  <>
                    <HealthyIcon color="success" />
                    <Typography variant="h6" color="success.main">Running</Typography>
                  </>
                ) : (
                  <>
                    <UnhealthyIcon color="error" />
                    <Typography variant="h6" color="error.main">
                      {proxyStatus?.proxy_status || 'Unknown'}
                    </Typography>
                  </>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} action={
          <Button color="inherit" size="small" onClick={fetchKeys}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      )}

      {/* API Keys Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Key Prefix</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Last Used</TableCell>
                <TableCell>Expires</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <CircularProgress size={24} />
                  </TableCell>
                </TableRow>
              ) : keys.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography color="text.secondary">
                      No API keys yet. Create one to get started.
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                keys.map((key) => (
                  <TableRow
                    key={key.id}
                    sx={{
                      opacity: key.is_active ? 1 : 0.6,
                      '&:hover': { backgroundColor: 'action.hover' }
                    }}
                  >
                    <TableCell>
                      <Typography variant="body2" fontWeight={500}>
                        {key.name}
                      </Typography>
                      {key.description && (
                        <Typography variant="caption" color="text.secondary">
                          {key.description}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" fontFamily="monospace">
                        {key.api_key_prefix}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={key.is_active ? 'Active' : 'Revoked'}
                        color={key.is_active ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title={formatDate(key.created_at)}>
                        <Typography variant="body2">
                          {timeAgo(key.created_at)}
                        </Typography>
                      </Tooltip>
                      {key.created_by && (
                        <Typography variant="caption" color="text.secondary">
                          by {key.created_by}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {timeAgo(key.last_used_at)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {key.expires_at ? (
                        <Tooltip title={formatDate(key.expires_at)}>
                          <Typography variant="body2">
                            {new Date(key.expires_at) < new Date() ? (
                              <Chip size="small" label="Expired" color="error" />
                            ) : (
                              timeAgo(key.expires_at)
                            )}
                          </Typography>
                        </Tooltip>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          Never
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell align="right">
                      {key.is_active && (
                        <Tooltip title="Revoke Key">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setRevokeKey(key)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Usage Example */}
      <Paper sx={{ p: 2, mt: 3 }}>
        <Typography variant="subtitle1" gutterBottom>
          Usage Example
        </Typography>
        <Box
          component="pre"
          sx={{
            p: 2,
            backgroundColor: 'grey.900',
            color: 'grey.100',
            borderRadius: 1,
            overflow: 'auto',
            fontSize: '0.85rem'
          }}
        >
{`# Make a request to the Granite extraction service
curl -X POST https://extraction.your-domain.com/v1/chat/completions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "model": "granite",
    "messages": [{"role": "user", "content": "Extract entities from: ..."}]
  }'`}
        </Box>
      </Paper>

      {/* Dialogs */}
      <CreateKeyDialog
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={handleKeyCreated}
      />

      <DisplayKeyDialog
        open={!!displayKeyData}
        onClose={() => setDisplayKeyData(null)}
        keyData={displayKeyData}
      />

      <RevokeDialog
        open={!!revokeKey}
        onClose={() => setRevokeKey(null)}
        onConfirm={handleRevoke}
        keyData={revokeKey}
        loading={revoking}
      />

      {/* Toast */}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={toast.severity}
          onClose={() => setToast({ ...toast, open: false })}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default GraniteApiKeysManagement;
