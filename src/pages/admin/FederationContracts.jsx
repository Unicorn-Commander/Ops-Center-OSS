/**
 * Federation Contracts Page
 * Admin interface for enforced federation_peers trust_mode/publish/consume/is_active.
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Card,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  Grid,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Snackbar,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import {
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Save as SaveIcon,
  Security as SecurityIcon,
  ShieldOutlined as ShieldIcon,
  WarningAmber as WarningIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

const API_BASE = '/api/v1/admin/federation';

const SERVICE_TYPES = ['llm', 'embeddings', 'reranker', 'agents', 'image_gen', 'tts', 'stt', 'music_gen'];

const TRUST_MODES = [
  { value: 'full', label: 'Full', description: 'Bidirectional unrestricted federation traffic.' },
  { value: 'scoped', label: 'Scoped', description: 'Only publish[] and consume[] grants are allowed.' },
  { value: 'consumer', label: 'Consumer', description: 'Outbound-only: this node calls the peer.' },
  { value: 'publisher', label: 'Publisher', description: 'Inbound-only: this node serves the peer.' },
  { value: 'isolated', label: 'Isolated', description: 'No live federation traffic.' }
];

const MODE_COLORS = {
  full: 'success',
  scoped: 'primary',
  consumer: 'info',
  publisher: 'warning',
  isolated: 'default'
};

const formatDate = (value) => {
  if (!value) return 'Never';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const errorMessage = (error) => {
  if (!error) return 'Unknown error';
  if (typeof error === 'string') return error;
  if (Array.isArray(error)) {
    return error.map((item) => item.msg || JSON.stringify(item)).join(', ');
  }
  return error.detail || error.message || JSON.stringify(error);
};

const unique = (items) => Array.from(new Set(items.filter(Boolean)));

async function apiFetch(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    throw new Error(errorMessage(body.detail || body));
  }
  return response.json();
}

function ModeSelect({ value, onChange, label = 'Trust Mode', disabled = false }) {
  return (
    <FormControl fullWidth size="small" disabled={disabled}>
      <InputLabel>{label}</InputLabel>
      <Select value={value || 'full'} label={label} onChange={(event) => onChange(event.target.value)}>
        {TRUST_MODES.map((mode) => (
          <MenuItem key={mode.value} value={mode.value}>
            <Box>
              <Typography variant="body2">{mode.label}</Typography>
              <Typography variant="caption" color="text.secondary">
                {mode.description}
              </Typography>
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

function ChipList({ values, empty = 'None' }) {
  const items = values || [];
  if (items.length === 0) {
    return <Typography variant="caption" color="text.secondary">{empty}</Typography>;
  }
  return (
    <Stack direction="row" spacing={0.5} sx={{ flexWrap: 'wrap', gap: 0.5 }}>
      {items.map((value) => (
        <Chip key={value} label={value} size="small" variant="outlined" />
      ))}
    </Stack>
  );
}

function AclEditor({ title, values, onChange, agentChoices, disabled }) {
  const current = values || [];
  const serviceValues = current.filter((value) => !value.includes('/'));
  const resourceValues = current.filter((value) => value.includes('/'));
  const resourceOptions = unique([
    ...agentChoices.map((item) => item.grant || `agents/${item.agent_id}`),
    ...resourceValues
  ]);

  const setService = (serviceType, checked) => {
    const nextServices = checked
      ? unique([...serviceValues, serviceType])
      : serviceValues.filter((value) => value !== serviceType);
    onChange(unique([...nextServices, ...resourceValues]));
  };

  const setResources = (nextResources) => {
    onChange(unique([...serviceValues, ...nextResources.map((value) => value.trim()).filter(Boolean)]));
  };

  return (
    <Box sx={{ opacity: disabled ? 0.6 : 1 }}>
      <Typography variant="subtitle2" sx={{ mb: 1 }}>
        {title}
      </Typography>
      <FormGroup row sx={{ mb: 1 }}>
        {SERVICE_TYPES.map((serviceType) => (
          <FormControlLabel
            key={serviceType}
            control={
              <Checkbox
                size="small"
                checked={serviceValues.includes(serviceType)}
                onChange={(event) => setService(serviceType, event.target.checked)}
                disabled={disabled}
              />
            }
            label={<Typography variant="caption">{serviceType}</Typography>}
          />
        ))}
      </FormGroup>
      <Autocomplete
        multiple
        freeSolo
        size="small"
        disabled={disabled}
        options={resourceOptions}
        value={resourceValues}
        onChange={(_, nextValue) => setResources(nextValue)}
        renderTags={(tagValue, getTagProps) =>
          tagValue.map((option, index) => {
            const { key, ...tagProps } = getTagProps({ index });
            return (
              <Chip
                key={key}
                label={option}
                size="small"
                {...tagProps}
              />
            );
          })
        }
        renderInput={(params) => (
          <TextField
            {...params}
            label="Resource grants"
            placeholder="agents/sql-analyst"
            helperText="Use type/resource for resource-scoped grants."
          />
        )}
      />
    </Box>
  );
}

function ContractDialog({ open, contract, agentChoices, onClose, onSave }) {
  const [draft, setDraft] = useState(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setDraft(contract ? JSON.parse(JSON.stringify(contract)) : null);
  }, [contract]);

  if (!draft) return null;

  const scoped = draft.trust_mode === 'scoped';

  const handleSave = async () => {
    setSaving(true);
    try {
      await onSave(draft);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Edit Federation Contract
        <Typography variant="body2" color="text.secondary">
          {draft.display_name || draft.remote_node_id} ({draft.remote_node_id})
        </Typography>
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <ModeSelect
                value={draft.trust_mode}
                onChange={(trustMode) => setDraft((prev) => ({ ...prev, trust_mode: trustMode }))}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControlLabel
                control={
                  <Switch
                    checked={draft.is_active}
                    onChange={(event) => setDraft((prev) => ({ ...prev, is_active: event.target.checked }))}
                  />
                }
                label="Active"
              />
            </Grid>
          </Grid>

          {!scoped && (
            <Alert severity="info" icon={<ShieldIcon />}>
              publish[] and consume[] are only enforced in scoped mode. Saved values are retained for later.
            </Alert>
          )}

          <AclEditor
            title="publish[] - peer may see"
            values={draft.publish}
            onChange={(publish) => setDraft((prev) => ({ ...prev, publish }))}
            agentChoices={agentChoices}
            disabled={!scoped}
          />
          <Divider />
          <AclEditor
            title="consume[] - peer may call / this node may call"
            values={draft.consume}
            onChange={(consume) => setDraft((prev) => ({ ...prev, consume }))}
            agentChoices={agentChoices}
            disabled={!scoped}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={saving}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving}
          startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function FederationContracts() {
  const [loading, setLoading] = useState(true);
  const [savingDefault, setSavingDefault] = useState(false);
  const [error, setError] = useState('');
  const [localNodeId, setLocalNodeId] = useState('');
  const [contracts, setContracts] = useState([]);
  const [defaultMode, setDefaultMode] = useState('full');
  const [draftDefaultMode, setDraftDefaultMode] = useState('full');
  const [agentChoices, setAgentChoices] = useState([]);
  const [editing, setEditing] = useState(null);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const fetchContracts = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch('/contracts');
      setLocalNodeId(data.local_node_id || '');
      setContracts(data.contracts || []);
      setDefaultMode(data.default_trust_mode || 'full');
      setDraftDefaultMode(data.default_trust_mode || 'full');
      setError(data.warning || '');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAgentChoices = useCallback(async () => {
    try {
      const data = await apiFetch('/contracts/agent-choices');
      setAgentChoices(data.agents || []);
    } catch (err) {
      setAgentChoices([]);
    }
  }, []);

  useEffect(() => {
    fetchContracts();
    fetchAgentChoices();
  }, [fetchContracts, fetchAgentChoices]);

  const selectedMode = useMemo(
    () => TRUST_MODES.find((mode) => mode.value === draftDefaultMode) || TRUST_MODES[0],
    [draftDefaultMode]
  );

  const handleDefaultSave = async () => {
    setSavingDefault(true);
    try {
      const result = await apiFetch('/contracts/default-trust-mode', {
        method: 'PUT',
        body: JSON.stringify({ trust_mode: draftDefaultMode })
      });
      setDefaultMode(result.trust_mode);
      showToast('Default trust mode updated');
      fetchContracts();
    } catch (err) {
      showToast(`Failed to update default trust mode: ${err.message}`, 'error');
    } finally {
      setSavingDefault(false);
    }
  };

  const handleContractSave = async (draft) => {
    try {
      await apiFetch(`/contracts/${encodeURIComponent(draft.peer_row_id)}`, {
        method: 'PUT',
        body: JSON.stringify({
          trust_mode: draft.trust_mode,
          publish: draft.publish || [],
          consume: draft.consume || [],
          is_active: draft.is_active
        })
      });
      showToast(`Contract updated for ${draft.remote_node_id}`);
      await fetchContracts();
    } catch (err) {
      showToast(`Failed to save contract: ${err.message}`, 'error');
      throw err;
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <PageHeader title="Federation Contracts" subtitle="Loading enforced trust contracts..." />
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Federation Contracts"
        subtitle="Manage enforced trust_mode, publish, consume, and active state for registered peers"
        actions={
          <Button variant="outlined" startIcon={<RefreshIcon />} onClick={fetchContracts}>
            Refresh
          </Button>
        }
      />

      {error && (
        <Alert severity={localNodeId ? 'warning' : 'error'} sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stack spacing={2}>
            <Stack direction="row" spacing={1} alignItems="center">
              <SecurityIcon color="primary" />
              <Box>
                <Typography variant="h6">Global Default Trust Mode</Typography>
                <Typography variant="body2" color="text.secondary">
                  Default for unknown peers (no explicit contract). isolated = deny-by-default. Applies within ~30s.
                </Typography>
              </Box>
            </Stack>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <ModeSelect value={draftDefaultMode} onChange={setDraftDefaultMode} label="Default Trust Mode" />
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="body2" color="text.secondary">
                  Current: <strong>{defaultMode}</strong>. Selected: {selectedMode.description}
                </Typography>
              </Grid>
              <Grid item xs={12} md={2}>
                <Button
                  fullWidth
                  variant="contained"
                  onClick={handleDefaultSave}
                  disabled={savingDefault || draftDefaultMode === defaultMode}
                  startIcon={savingDefault ? <CircularProgress size={16} /> : <SaveIcon />}
                >
                  Save
                </Button>
              </Grid>
            </Grid>
          </Stack>
        </CardContent>
      </Card>

      {contracts.length === 0 ? (
        <Alert severity="info" icon={<WarningIcon />}>
          No explicit peer contracts yet. Peers appear here once they register or heartbeat; the global default governs unknown peers.
        </Alert>
      ) : (
        <Card>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Peer</TableCell>
                <TableCell>Trust Mode</TableCell>
                <TableCell>Scoped ACLs</TableCell>
                <TableCell>Active</TableCell>
                <TableCell>Token</TableCell>
                <TableCell>Authority</TableCell>
                <TableCell>Consumer Of</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {contracts.map((contract) => (
                <TableRow key={contract.peer_row_id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={600}>
                      {contract.display_name || contract.remote_node_id}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {contract.remote_node_id}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={contract.trust_mode}
                      color={MODE_COLORS[contract.trust_mode] || 'default'}
                      size="small"
                      variant={contract.is_active ? 'filled' : 'outlined'}
                    />
                  </TableCell>
                  <TableCell sx={{ minWidth: 260 }}>
                    <Stack spacing={0.75}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">publish[]</Typography>
                        <ChipList values={contract.publish} />
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">consume[]</Typography>
                        <ChipList values={contract.consume} />
                      </Box>
                    </Stack>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={contract.is_active ? 'active' : 'inactive'}
                      color={contract.is_active ? 'success' : 'default'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={contract.capability_token ? 'token present' : 'none'}
                      color={contract.capability_token ? 'info' : 'default'}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <ChipList values={contract.authority_for} />
                  </TableCell>
                  <TableCell>
                    <ChipList values={contract.consumer_of} />
                  </TableCell>
                  <TableCell>
                    <Stack spacing={0.25}>
                      <Chip label={contract.status || 'unknown'} size="small" variant="outlined" />
                      <Tooltip title={contract.last_heartbeat || 'Never'}>
                        <Typography variant="caption" color="text.secondary">
                          {formatDate(contract.last_heartbeat)}
                        </Typography>
                      </Tooltip>
                    </Stack>
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit contract">
                      <IconButton size="small" onClick={() => setEditing(contract)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}

      <ContractDialog
        open={Boolean(editing)}
        contract={editing}
        agentChoices={agentChoices}
        onClose={() => setEditing(null)}
        onSave={handleContractSave}
      />

      <Snackbar
        open={toast.open}
        autoHideDuration={5000}
        onClose={() => setToast((prev) => ({ ...prev, open: false }))}
      >
        <Alert
          severity={toast.severity}
          variant="filled"
          onClose={() => setToast((prev) => ({ ...prev, open: false }))}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
