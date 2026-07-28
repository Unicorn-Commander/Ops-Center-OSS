/**
 * App-Model Pricing Policy Page
 * Admin interface for the per-(app, model) included-vs-metered inference policy.
 *
 * Default behavior is "metered" (drawn from the org credit wallet). Adding an
 * "included" row bundles a model into an app's subscription (cost absorbed).
 * Deleting the row reverts that (app, model) back to metered.
 *
 * Backed by /api/v1/admin/inference-policy (admin-gated, audited).
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  DialogContentText,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Stack,
  Alert,
  AlertTitle,
  CircularProgress,
  LinearProgress,
  Tooltip,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  AttachMoney as MoneyIcon,
  LocalOffer as IncludedIcon,
  Bolt as MeteredIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

const API_BASE = '/api/v1/admin/inference-policy';

// model selector is exact, a 'prefix*', or the bare '*' (mirrors the backend validator)
const isValidModel = (model) => {
  const m = (model || '').trim();
  if (!m) return false;
  if (m === '*') return true;
  const stars = (m.match(/\*/g) || []).length;
  if (stars === 0) return true;
  return stars === 1 && m.endsWith('*');
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return '-';
  return d.toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  });
};

const PolicyChip = ({ policy }) =>
  policy === 'included' ? (
    <Chip icon={<IncludedIcon />} label="Included" color="success" size="small" variant="filled" sx={{ fontWeight: 600 }} />
  ) : (
    <Chip icon={<MeteredIcon />} label="Metered" color="default" size="small" variant="outlined" sx={{ fontWeight: 600 }} />
  );

/**
 * Add / Edit dialog. In edit mode, app + model are locked (they form the key);
 * only policy and note are editable.
 */
const PolicyDialog = ({ open, mode, initial, onClose, onSubmit }) => {
  const [app, setApp] = useState('');
  const [model, setModel] = useState('');
  const [policy, setPolicy] = useState('metered');
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (open) {
      setApp(initial?.app || '');
      setModel(initial?.model || '');
      setPolicy(initial?.policy || 'metered');
      setNote(initial?.note || '');
      setError(null);
    }
  }, [open, initial]);

  const isEdit = mode === 'edit';
  const appValid = app.trim().length > 0;
  const modelValid = isValidModel(model);

  const handleSubmit = async () => {
    if (!isEdit && (!appValid || !modelValid)) {
      setError('Provide a service name and a valid model selector.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit({ app: app.trim(), model: model.trim(), policy, note: note.trim() || null });
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{isEdit ? 'Edit Pricing Policy' : 'Add Pricing Policy'}</DialogTitle>
      <DialogContent>
        <Stack spacing={2.5} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="App (service name)"
            value={app}
            onChange={(e) => setApp(e.target.value)}
            fullWidth
            disabled={isEdit}
            placeholder="meeting-ops-service"
            error={!isEdit && app.length > 0 && !appValid}
            helperText={
              isEdit
                ? 'The calling service this policy applies to (locked)'
                : 'The calling UC app / service_name or feature_key, e.g. meeting-ops-service'
            }
          />
          <TextField
            label="Model"
            value={model}
            onChange={(e) => setModel(e.target.value)}
            fullWidth
            disabled={isEdit}
            placeholder="Qwen3.6-*"
            error={!isEdit && model.length > 0 && !modelValid}
            helperText={
              isEdit
                ? 'The model selector (locked)'
                : "Exact (gpt-4o), a prefix (Qwen3.6-*), or '*' for all models"
            }
          />
          <FormControl fullWidth>
            <InputLabel>Policy</InputLabel>
            <Select value={policy} label="Policy" onChange={(e) => setPolicy(e.target.value)}>
              <MenuItem value="metered">Metered — drawn from the credit wallet (default)</MenuItem>
              <MenuItem value="included">Included — bundled into the app subscription (cost absorbed)</MenuItem>
            </Select>
          </FormControl>
          <TextField
            label="Note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            fullWidth
            multiline
            rows={2}
            placeholder="Why this model is bundled for this app"
          />
        </Stack>
      </DialogContent>
      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={submitting || (!isEdit && (!appValid || !modelValid))}
          startIcon={submitting ? <CircularProgress size={16} /> : isEdit ? <EditIcon /> : <AddIcon />}
        >
          {isEdit ? 'Save Changes' : 'Add Policy'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

const AppModelPolicy = () => {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogMode, setDialogMode] = useState('add'); // 'add' | 'edit'
  const [dialogInitial, setDialogInitial] = useState(null);

  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });
  const showToast = (message, severity = 'success') => setToast({ open: true, message, severity });

  const apiFetch = useCallback(async (endpoint, options = {}) => {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
      credentials: 'include'
    });
    if (response.status === 204) return null;
    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.detail ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail)) : `Request failed (${response.status})`);
    }
    return data;
  }, []);

  const fetchRows = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch('/');
      setRows(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);

  useEffect(() => { fetchRows(); }, [fetchRows]);

  const openAdd = () => {
    setDialogMode('add');
    setDialogInitial(null);
    setDialogOpen(true);
  };

  const openEdit = (row) => {
    setDialogMode('edit');
    setDialogInitial(row);
    setDialogOpen(true);
  };

  const handleSubmit = async (payload) => {
    if (dialogMode === 'add') {
      await apiFetch('/', { method: 'POST', body: JSON.stringify(payload) });
      showToast(`Policy added for ${payload.app} / ${payload.model}`);
    } else {
      await apiFetch(`/${dialogInitial.id}`, {
        method: 'PUT',
        body: JSON.stringify({ policy: payload.policy, note: payload.note })
      });
      showToast('Policy updated');
    }
    fetchRows();
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    try {
      setDeleting(true);
      await apiFetch(`/${deleteTarget.id}`, { method: 'DELETE' });
      showToast(`Policy removed — ${deleteTarget.app} / ${deleteTarget.model} reverts to metered`, 'info');
      setDeleteTarget(null);
      fetchRows();
    } catch (err) {
      showToast(`Failed to delete: ${err.message}`, 'error');
    } finally {
      setDeleting(false);
    }
  };

  const includedCount = rows.filter((r) => r.policy === 'included').length;

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Inference Pricing Policy"
        subtitle="Bundle a model into an app subscription (included) or bill it from the credit wallet (metered)"
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchRows} disabled={loading}>
              Refresh
            </Button>
            <Button variant="contained" startIcon={<AddIcon />} onClick={openAdd}>
              Add Policy
            </Button>
          </Stack>
        }
      />

      {/* Explainer */}
      <Alert severity="info" icon={<MoneyIcon />} sx={{ mb: 3 }}>
        <AlertTitle>How this works</AlertTitle>
        <Typography variant="body2" sx={{ mb: 1 }}>
          The default for every (app, model) is <strong>metered</strong> — usage is drawn from the
          organization's credit wallet. Add an <strong>included</strong> row to bundle a specific
          model into an app's subscription, absorbing the cost. Deleting a row reverts that pair to
          metered. An empty table means everything is metered (no behavior change).
        </Typography>
        <Typography variant="body2" component="div">
          <strong>model</strong> may be exact (<code>gpt-4o</code>), a prefix (<code>Qwen3.6-*</code>),
          or <code>*</code> for all models. <strong>app</strong> is the calling service name, e.g.{' '}
          <code>meeting-ops-service</code>. Most-specific match wins (exact &gt; longest prefix &gt; <code>*</code>).
        </Typography>
        <Box sx={{ mt: 1.5, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          <Chip size="small" variant="outlined" label="meeting-ops-service · Qwen3.6-* · included" />
          <Chip size="small" variant="outlined" label="meeting-ops-service · Parakeet-STT · included" />
          <Chip size="small" variant="outlined" label="brand-ops-service · * · metered" />
        </Box>
      </Alert>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card sx={{ borderRadius: 2 }}>
        <CardContent sx={{ pb: '8px !important' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Policy Rows
              {rows.length > 0 && (
                <Chip
                  label={`${includedCount} included / ${rows.length} total`}
                  size="small"
                  sx={{ ml: 1 }}
                />
              )}
            </Typography>
          </Box>

          {loading && <LinearProgress sx={{ mb: 2 }} />}

          {rows.length > 0 ? (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ fontWeight: 700 }}>App</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Model</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>Policy</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Note</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Created</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map((row) => (
                    <TableRow key={row.id} hover>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{row.app}</TableCell>
                      <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{row.model}</TableCell>
                      <TableCell align="center"><PolicyChip policy={row.policy} /></TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 280 }} noWrap title={row.note || ''}>
                          {row.note || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="text.secondary">{formatDate(row.created_at)}</Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="Edit policy / note">
                            <IconButton size="small" onClick={() => openEdit(row)}>
                              <EditIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete (reverts to metered)">
                            <IconButton size="small" color="error" onClick={() => setDeleteTarget(row)}>
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          ) : (
            !loading && (
              <Paper variant="outlined" sx={{ p: 4, textAlign: 'center', borderStyle: 'dashed' }}>
                <MoneyIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  No policy rows yet — every (app, model) resolves to <strong>metered</strong>.
                  Add an <strong>included</strong> row to bundle a model into an app subscription.
                </Typography>
                <Button variant="contained" startIcon={<AddIcon />} onClick={openAdd}>
                  Add Policy
                </Button>
              </Paper>
            )
          )}
        </CardContent>
      </Card>

      {/* Add / Edit dialog */}
      <PolicyDialog
        open={dialogOpen}
        mode={dialogMode}
        initial={dialogInitial}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleSubmit}
      />

      {/* Delete confirm */}
      <Dialog open={Boolean(deleteTarget)} onClose={() => !deleting && setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Delete Pricing Policy?</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Remove the policy for{' '}
            <code>{deleteTarget?.app}</code> / <code>{deleteTarget?.model}</code>? This pair will
            revert to <strong>metered</strong> (billed from the credit wallet).
          </DialogContentText>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setDeleteTarget(null)} disabled={deleting}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDelete}
            disabled={deleting}
            startIcon={deleting ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast */}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert severity={toast.severity} onClose={() => setToast({ ...toast, open: false })}>
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AppModelPolicy;
