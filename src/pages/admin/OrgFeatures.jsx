/**
 * Org Feature Grants Page
 * Admin interface for granting / revoking per-organization app & feature access,
 * independent of the org's subscription tier.
 *
 * Flow:
 *  1. Pick an organization (searchable list from /api/v1/org/organizations,
 *     with a free-text org-id fallback if the list can't be loaded).
 *  2. View that org's current feature grants (GET /api/v1/admin/orgs/{id}/features)
 *     in a table, each with a Revoke action (DELETE).
 *  3. Grant a new feature: pick from /api/v1/admin/features/available
 *     (already-granted features excluded), optionally add a note, submit (POST).
 *
 * Backend: backend/org_features_api.py (all endpoints admin-gated).
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
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
  DialogContentText,
  DialogActions,
  TextField,
  Autocomplete,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Snackbar,
  CircularProgress,
  LinearProgress,
  Tooltip,
  Stack
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';
import AdminBreadcrumbs from '../../components/admin/AdminBreadcrumbs';
import EmptyState from '../../components/admin/EmptyState';

const ADMIN_BASE = '/api/v1/admin';

// Format an ISO timestamp for display
const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const OrgFeatures = () => {
  // Organization list (for the picker)
  const [orgs, setOrgs] = useState([]);
  const [orgsLoading, setOrgsLoading] = useState(true);
  const [orgsLoadFailed, setOrgsLoadFailed] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null); // { id, name } from list
  const [manualOrgId, setManualOrgId] = useState(''); // free-text fallback

  // The org id we are currently operating on (resolved from picker or manual entry)
  const [activeOrgId, setActiveOrgId] = useState('');
  const [activeOrgLabel, setActiveOrgLabel] = useState('');

  // Current grants for the active org
  const [grants, setGrants] = useState([]);
  const [grantsLoading, setGrantsLoading] = useState(false);

  // Available (grantable) features
  const [availableFeatures, setAvailableFeatures] = useState([]);
  const [availableLoading, setAvailableLoading] = useState(false);

  // Grant dialog
  const [grantDialogOpen, setGrantDialogOpen] = useState(false);
  const [grantFeatureKey, setGrantFeatureKey] = useState('');
  const [grantNotes, setGrantNotes] = useState('');
  const [granting, setGranting] = useState(false);

  // Revoke confirm dialog
  const [revokeTarget, setRevokeTarget] = useState(null); // grant row to revoke
  const [revoking, setRevoking] = useState(false);

  // Toast
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });
  const showToast = (message, severity = 'success') => setToast({ open: true, message, severity });

  // --- API helper ---------------------------------------------------------
  const apiFetch = useCallback(async (url, options = {}) => {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include'
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: `Request failed (${response.status})` }));
      throw new Error(err.detail || `Request failed (${response.status})`);
    }
    // DELETE / some endpoints may return empty body
    const text = await response.text();
    return text ? JSON.parse(text) : null;
  }, []);

  // --- Load organizations for the picker ----------------------------------
  const fetchOrgs = useCallback(async () => {
    setOrgsLoading(true);
    try {
      const data = await apiFetch('/api/v1/org/organizations?limit=200');
      setOrgs(Array.isArray(data?.organizations) ? data.organizations : []);
      setOrgsLoadFailed(false);
    } catch (err) {
      console.error('Failed to load organizations:', err);
      setOrgsLoadFailed(true);
      showToast('Could not load the organization list — enter an org ID manually below.', 'warning');
    } finally {
      setOrgsLoading(false);
    }
  }, [apiFetch]);

  // --- Load available features (for the grant dropdown) -------------------
  const fetchAvailableFeatures = useCallback(async () => {
    setAvailableLoading(true);
    try {
      const data = await apiFetch(`${ADMIN_BASE}/features/available`);
      setAvailableFeatures(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load available features:', err);
      showToast(`Failed to load available features: ${err.message}`, 'error');
    } finally {
      setAvailableLoading(false);
    }
  }, [apiFetch]);

  // --- Load grants for a specific org ------------------------------------
  const fetchGrants = useCallback(async (orgId) => {
    if (!orgId) return;
    setGrantsLoading(true);
    try {
      const data = await apiFetch(`${ADMIN_BASE}/orgs/${encodeURIComponent(orgId)}/features`);
      setGrants(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Failed to load org features:', err);
      setGrants([]);
      showToast(`Failed to load grants: ${err.message}`, 'error');
    } finally {
      setGrantsLoading(false);
    }
  }, [apiFetch]);

  // Initial load
  useEffect(() => {
    fetchOrgs();
    fetchAvailableFeatures();
  }, [fetchOrgs, fetchAvailableFeatures]);

  // --- Org selection handlers --------------------------------------------
  const handleSelectOrg = (org) => {
    setSelectedOrg(org);
    if (org?.id) {
      setActiveOrgId(org.id);
      setActiveOrgLabel(org.name || org.id);
      fetchGrants(org.id);
    } else {
      setActiveOrgId('');
      setActiveOrgLabel('');
      setGrants([]);
    }
  };

  const handleManualLoad = () => {
    const id = manualOrgId.trim();
    if (!id) return;
    setSelectedOrg(null);
    setActiveOrgId(id);
    setActiveOrgLabel(id);
    fetchGrants(id);
  };

  // --- Grant a feature ----------------------------------------------------
  // Exclude already-granted (enabled) features from the dropdown.
  const grantedKeys = new Set(grants.filter((g) => g.enabled !== false).map((g) => g.feature_key));
  const grantableFeatures = availableFeatures.filter((f) => !grantedKeys.has(f.feature_key));

  const openGrantDialog = () => {
    setGrantFeatureKey('');
    setGrantNotes('');
    setGrantDialogOpen(true);
  };

  const handleGrant = async () => {
    if (!activeOrgId || !grantFeatureKey) return;
    setGranting(true);
    try {
      // POST body matches backend OrgFeatureGrant model: { feature_key, notes }
      await apiFetch(`${ADMIN_BASE}/orgs/${encodeURIComponent(activeOrgId)}/features`, {
        method: 'POST',
        body: JSON.stringify({
          feature_key: grantFeatureKey,
          notes: grantNotes.trim() || null
        })
      });
      showToast(`Feature "${grantFeatureKey}" granted to ${activeOrgLabel}`);
      setGrantDialogOpen(false);
      fetchGrants(activeOrgId);
    } catch (err) {
      showToast(`Failed to grant feature: ${err.message}`, 'error');
    } finally {
      setGranting(false);
    }
  };

  // --- Revoke a feature ---------------------------------------------------
  const handleRevoke = async () => {
    if (!revokeTarget || !activeOrgId) return;
    setRevoking(true);
    try {
      await apiFetch(
        `${ADMIN_BASE}/orgs/${encodeURIComponent(activeOrgId)}/features/${encodeURIComponent(revokeTarget.feature_key)}`,
        { method: 'DELETE' }
      );
      showToast(`Feature "${revokeTarget.feature_key}" revoked from ${activeOrgLabel}`);
      setRevokeTarget(null);
      fetchGrants(activeOrgId);
    } catch (err) {
      showToast(`Failed to revoke feature: ${err.message}`, 'error');
    } finally {
      setRevoking(false);
    }
  };

  // Lookup an app name for a feature_key (fallback when grant row has no app_name)
  const appNameFor = (featureKey) => {
    const f = availableFeatures.find((x) => x.feature_key === featureKey);
    return f?.app_name || null;
  };

  return (
    <Box sx={{ p: 3 }}>
      <AdminBreadcrumbs />

      <PageHeader
        title="Org Feature Grants"
        subtitle="Grant or revoke specific app & feature access for an organization, independent of its subscription tier"
        actions={
          <Button
            variant="outlined"
            startIcon={grantsLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
            onClick={() => activeOrgId && fetchGrants(activeOrgId)}
            disabled={!activeOrgId || grantsLoading}
          >
            Refresh
          </Button>
        }
      />

      {/* Organization picker */}
      <Card sx={{ mb: 3, borderRadius: 2 }}>
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
            <BusinessIcon color="primary" />
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Select Organization
            </Typography>
          </Box>

          {!orgsLoadFailed ? (
            <Autocomplete
              options={orgs}
              loading={orgsLoading}
              value={selectedOrg}
              onChange={(e, val) => handleSelectOrg(val)}
              getOptionLabel={(opt) => (opt?.name ? `${opt.name}` : opt?.id || '')}
              isOptionEqualToValue={(opt, val) => opt?.id === val?.id}
              renderOption={(props, opt) => (
                <li {...props} key={opt.id}>
                  <Box>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {opt.name || '(unnamed)'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                      {opt.id}
                      {opt.subscription_tier ? ` • ${opt.subscription_tier}` : ''}
                    </Typography>
                  </Box>
                </li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Organization"
                  placeholder="Search by name..."
                  helperText="Pick an org to view and manage its feature grants"
                  InputProps={{
                    ...params.InputProps,
                    endAdornment: (
                      <>
                        {orgsLoading ? <CircularProgress color="inherit" size={18} /> : null}
                        {params.InputProps.endAdornment}
                      </>
                    )
                  }}
                />
              )}
            />
          ) : (
            // Fallback: free-text org id input
            <Stack direction="row" spacing={1} alignItems="flex-start">
              <TextField
                label="Organization ID"
                value={manualOrgId}
                onChange={(e) => setManualOrgId(e.target.value)}
                placeholder="org UUID, e.g. 052a068c-e1ad-484c-a791-12249e0d5d5b"
                helperText="Org list unavailable — paste the organization UUID"
                fullWidth
                onKeyDown={(e) => { if (e.key === 'Enter') handleManualLoad(); }}
              />
              <Button
                variant="contained"
                onClick={handleManualLoad}
                disabled={!manualOrgId.trim()}
                sx={{ mt: 1, whiteSpace: 'nowrap' }}
              >
                Load
              </Button>
              <Button
                variant="text"
                onClick={fetchOrgs}
                startIcon={<RefreshIcon />}
                sx={{ mt: 1, whiteSpace: 'nowrap' }}
              >
                Retry list
              </Button>
            </Stack>
          )}
        </CardContent>
      </Card>

      {/* Grants table (only once an org is active) */}
      {activeOrgId && (
        <Paper sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: 2 }}>
          <Box
            sx={{
              p: 2,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              borderBottom: '1px solid',
              borderColor: 'divider'
            }}
          >
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Feature Grants
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {activeOrgLabel}
                <Box component="span" sx={{ fontFamily: 'monospace', ml: 1, opacity: 0.7 }}>
                  {activeOrgId}
                </Box>
              </Typography>
            </Box>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={openGrantDialog}
              disabled={availableLoading}
            >
              Grant Feature
            </Button>
          </Box>

          {grantsLoading && <LinearProgress />}

          {!grantsLoading && grants.length === 0 ? (
            <Box sx={{ p: 2 }}>
              <EmptyState
                icon="inbox"
                title="No feature grants"
                description="This organization has no per-org feature grants yet. It still has whatever its subscription tier includes."
                actionLabel="Grant Feature"
                onAction={openGrantDialog}
              />
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                    <TableCell sx={{ fontWeight: 700 }}>App</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Feature Key</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>Status</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Granted By</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Granted At</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>Notes</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {grants.map((g) => (
                    <TableRow key={g.id || g.feature_key} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {g.app_name || appNameFor(g.feature_key) || '—'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={g.feature_key}
                          size="small"
                          variant="outlined"
                          sx={{ fontFamily: 'monospace' }}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={g.enabled === false ? 'Disabled' : 'Enabled'}
                          size="small"
                          color={g.enabled === false ? 'default' : 'success'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{g.granted_by || '—'}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">{formatDate(g.granted_at)}</Typography>
                      </TableCell>
                      <TableCell>
                        {g.notes ? (
                          <Tooltip title={g.notes}>
                            <Typography variant="body2" noWrap sx={{ maxWidth: 220 }}>
                              {g.notes}
                            </Typography>
                          </Tooltip>
                        ) : (
                          <Typography variant="body2" color="text.secondary">—</Typography>
                        )}
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Revoke feature">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => setRevokeTarget(g)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {/* Grant Feature Dialog */}
      <Dialog open={grantDialogOpen} onClose={() => setGrantDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Grant Feature to {activeOrgLabel}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            {grantableFeatures.length === 0 ? (
              <Alert severity="info">
                {availableFeatures.length === 0
                  ? 'No grantable features are available. Add apps with a feature_key in the App Entitlements admin first.'
                  : 'All available features are already granted to this organization.'}
              </Alert>
            ) : (
              <FormControl fullWidth required>
                <InputLabel>Feature</InputLabel>
                <Select
                  value={grantFeatureKey}
                  label="Feature"
                  onChange={(e) => setGrantFeatureKey(e.target.value)}
                >
                  {grantableFeatures.map((f) => (
                    <MenuItem key={f.feature_key} value={f.feature_key}>
                      <Box>
                        <Typography variant="body2">{f.app_name}</Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                          {f.feature_key}
                        </Typography>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            <TextField
              label="Notes (optional)"
              value={grantNotes}
              onChange={(e) => setGrantNotes(e.target.value)}
              fullWidth
              multiline
              rows={2}
              placeholder="Reason for this grant, e.g. 'Partner deal Q1 2026'"
              helperText="Recorded for audit purposes"
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setGrantDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleGrant}
            disabled={granting || !grantFeatureKey || grantableFeatures.length === 0}
            startIcon={granting ? <CircularProgress size={16} /> : <AddIcon />}
          >
            Grant Feature
          </Button>
        </DialogActions>
      </Dialog>

      {/* Revoke Confirm Dialog */}
      <Dialog open={Boolean(revokeTarget)} onClose={() => setRevokeTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Revoke Feature</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Revoke{' '}
            <strong>{revokeTarget?.app_name || appNameFor(revokeTarget?.feature_key) || revokeTarget?.feature_key}</strong>
            {' '}(<Box component="span" sx={{ fontFamily: 'monospace' }}>{revokeTarget?.feature_key}</Box>){' '}
            from <strong>{activeOrgLabel}</strong>?
          </DialogContentText>
          <Alert severity="warning" sx={{ mt: 2 }}>
            The organization will lose access to this app unless its subscription tier also includes it.
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setRevokeTarget(null)}>Cancel</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleRevoke}
            disabled={revoking}
            startIcon={revoking ? <CircularProgress size={16} /> : <DeleteIcon />}
          >
            Revoke
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

export default OrgFeatures;
