import React, { useState, useEffect, useCallback } from 'react';
import {
  Box, Paper, Typography, Button, Grid, TextField, IconButton,
  Alert, CircularProgress, Divider, Tooltip, Autocomplete, InputAdornment,
} from '@mui/material';
import {
  Save as SaveIcon, Add as AddIcon, Delete as DeleteIcon,
  Refresh as RefreshIcon, SmartToy as AgentIcon,
  InfoOutlined as InfoIcon,
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';
import { useToast } from '../../components/Toast';

const API_BASE = '/api/v1/admin/agent-pricing';

// The pricing map is {"default": n, "<agent-id>": n, ...}. The editor keeps
// `default` separate (always present) and the remaining agents as editable
// rows so an admin can add/remove explicit per-agent prices.
const AgentPricing = () => {
  const toast = useToast();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const [defaultUnits, setDefaultUnits] = useState('1');
  // rows: [{ agentId: string, units: string }]
  const [rows, setRows] = useState([]);
  const [choices, setChoices] = useState([]);

  const loadPricing = useCallback(async () => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/`, { credentials: 'include' });
      if (!res.ok) throw new Error(`Failed to load agent pricing (HTTP ${res.status})`);
      const data = await res.json();
      const pricing = (data && data.pricing) || { default: 1 };
      setDefaultUnits(String(pricing.default ?? 1));
      const nextRows = Object.entries(pricing)
        .filter(([key]) => key !== 'default')
        .map(([agentId, units]) => ({ agentId, units: String(units) }));
      setRows(nextRows);
    } catch (err) {
      console.error('Error loading agent pricing:', err);
      setError(err.message);
    }
  }, []);

  const loadChoices = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/agent-choices`, { credentials: 'include' });
      if (!res.ok) return; // suggestions are best-effort; UI accepts free-form ids
      const data = await res.json();
      if (Array.isArray(data)) {
        setChoices([...new Set(data.map((c) => c.agent_id).filter(Boolean))]);
      }
    } catch (err) {
      // Non-fatal: free-form entry still works.
      console.debug('Agent-id suggestions unavailable:', err);
    }
  }, []);

  useEffect(() => {
    Promise.all([loadPricing(), loadChoices()]).finally(() => setLoading(false));
  }, [loadPricing, loadChoices]);

  const addRow = () => setRows((prev) => [...prev, { agentId: '', units: '1' }]);

  const removeRow = (idx) =>
    setRows((prev) => prev.filter((_, i) => i !== idx));

  const updateRow = (idx, field, value) =>
    setRows((prev) => prev.map((r, i) => (i === idx ? { ...r, [field]: value } : r)));

  const buildPayload = () => {
    const pricing = {};

    const def = parseFloat(defaultUnits);
    if (!Number.isFinite(def) || def < 0) {
      throw new Error('Default units must be a number >= 0');
    }
    pricing.default = def;

    const seen = new Set(['default']);
    for (const { agentId, units } of rows) {
      const id = (agentId || '').trim();
      if (!id) {
        throw new Error('Every agent row needs an agent id (or remove the row)');
      }
      if (seen.has(id)) {
        throw new Error(`Duplicate agent id: "${id}"`);
      }
      seen.add(id);
      const n = parseFloat(units);
      if (!Number.isFinite(n) || n < 0) {
        throw new Error(`Units for "${id}" must be a number >= 0`);
      }
      pricing[id] = n;
    }
    return pricing;
  };

  const handleSave = async () => {
    let pricing;
    try {
      pricing = buildPayload();
    } catch (validationErr) {
      toast.error(validationErr.message);
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ pricing }),
      });
      if (!res.ok) {
        let detail = `Failed to save (HTTP ${res.status})`;
        try {
          const errData = await res.json();
          if (errData && errData.detail) detail = errData.detail;
        } catch (_) { /* keep default */ }
        throw new Error(detail);
      }
      const data = await res.json();
      const saved = (data && data.pricing) || pricing;
      // Reflect normalized server state (e.g. default filled in).
      setDefaultUnits(String(saved.default ?? 1));
      setRows(
        Object.entries(saved)
          .filter(([key]) => key !== 'default')
          .map(([agentId, units]) => ({ agentId, units: String(units) }))
      );
      toast.success('Agent pricing saved');
    } catch (err) {
      console.error('Error saving agent pricing:', err);
      setError(err.message);
      toast.error(err.message);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Federation Agent Pricing"
        subtitle="Units charged per federated agent invocation, priced at the Lago plan"
        actions={
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => { setLoading(true); Promise.all([loadPricing(), loadChoices()]).finally(() => setLoading(false)); }}
              disabled={saving}
            >
              Reload
            </Button>
            <Button
              variant="contained"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={saving}
            >
              {saving ? 'Saving…' : 'Save'}
            </Button>
          </Box>
        }
      />

      <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 3 }}>
        Each federated <strong>agent invocation</strong> is metered as a number of
        units; what a unit costs is decided by the Lago plan charge on the
        <code> agent_invocation </code> metric. The <strong>default</strong>{' '}
        applies to any agent without an explicit price below.
      </Alert>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>
          Default
        </Typography>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={4}>
            <TextField
              fullWidth
              label="Default units / invocation"
              type="number"
              value={defaultUnits}
              onChange={(e) => setDefaultUnits(e.target.value)}
              inputProps={{ min: 0, step: 0.5 }}
              helperText="Applied to agents without an explicit price"
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper sx={{ p: 3, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Per-agent overrides
            </Typography>
            <Tooltip
              title="Set a specific unit price for an individual agent id. Agents not listed here use the default above."
              arrow
            >
              <InfoIcon sx={{ fontSize: 16, opacity: 0.6 }} />
            </Tooltip>
          </Box>
          <Button startIcon={<AddIcon />} onClick={addRow} size="small">
            Add agent
          </Button>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {rows.length === 0 ? (
          <Alert severity="info" variant="outlined">
            No per-agent prices. Every agent is charged the default
            ({defaultUnits || '1'} unit{Number(defaultUnits) === 1 ? '' : 's'}) per invocation.
            Click “Add agent” to set a specific price.
          </Alert>
        ) : (
          rows.map((row, idx) => (
            <Grid container spacing={2} alignItems="center" key={idx} sx={{ mb: 1.5 }}>
              <Grid item xs={12} sm={7} md={8}>
                <Autocomplete
                  freeSolo
                  options={choices}
                  value={row.agentId}
                  onChange={(_, newVal) => updateRow(idx, 'agentId', newVal || '')}
                  onInputChange={(_, newVal) => updateRow(idx, 'agentId', newVal)}
                  renderInput={(params) => (
                    <TextField
                      {...params}
                      label="Agent id"
                      placeholder="e.g. deep-research"
                      InputProps={{
                        ...params.InputProps,
                        startAdornment: (
                          <InputAdornment position="start">
                            <AgentIcon fontSize="small" sx={{ opacity: 0.6 }} />
                          </InputAdornment>
                        ),
                      }}
                    />
                  )}
                />
              </Grid>
              <Grid item xs={9} sm={4} md={3}>
                <TextField
                  fullWidth
                  label="Units"
                  type="number"
                  value={row.units}
                  onChange={(e) => updateRow(idx, 'units', e.target.value)}
                  inputProps={{ min: 0, step: 0.5 }}
                />
              </Grid>
              <Grid item xs={3} sm={1} md={1}>
                <Tooltip title="Remove" arrow>
                  <IconButton color="error" onClick={() => removeRow(idx)} aria-label="remove agent price">
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </Grid>
            </Grid>
          ))
        )}
      </Paper>
    </Box>
  );
};

export default AgentPricing;
