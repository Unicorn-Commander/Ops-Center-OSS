/**
 * Credit Packages Management Page
 * Admin interface for managing buyable credit packs (credit_packages table).
 *
 * These are the one-time credit packs surfaced to buyers on the "Buy Credits"
 * page. This page lets admins create/edit/deactivate them instead of hand-
 * writing SQL. Backed by /api/v1/admin/credit-packages.
 */

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
  TablePagination,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Grid,
  Alert,
  Tooltip,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  CreditCard as CreditCardIcon,
  InfoOutlined as InfoOutlinedIcon
} from '@mui/icons-material';

const API_BASE = '/api/v1/admin/credit-packages';

const emptyForm = {
  package_code: '',
  package_name: '',
  description: '',
  credits: 1000,
  price_usd: 10,
  discount_percentage: 0,
  stripe_price_id: '',
  stripe_product_id: '',
  is_active: true,
  display_order: 0
};

const CreditPackages = () => {
  const [packages, setPackages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [saving, setSaving] = useState(false);

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [selectedId, setSelectedId] = useState(null);
  const [formData, setFormData] = useState(emptyForm);

  // ============================================
  // API
  // ============================================

  const fetchPackages = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/`, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load credit packages');
      const data = await res.json();
      setPackages(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching credit packages:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPackages();
  }, []);

  const savePackage = async () => {
    setSaving(true);
    setError(null);
    try {
      // Build payload. For create we send everything; for edit we omit the
      // immutable package_code (backend ignores it on PUT anyway).
      const payload = {
        package_name: formData.package_name,
        description: formData.description || null,
        credits: parseInt(formData.credits, 10),
        price_usd: parseFloat(formData.price_usd),
        discount_percentage: parseInt(formData.discount_percentage, 10) || 0,
        stripe_price_id: formData.stripe_price_id || null,
        stripe_product_id: formData.stripe_product_id || null,
        is_active: formData.is_active,
        display_order: parseInt(formData.display_order, 10) || 0
      };
      if (!isEditing) {
        payload.package_code = formData.package_code;
      }

      const url = isEditing ? `${API_BASE}/${selectedId}` : `${API_BASE}/`;
      const method = isEditing ? 'PUT' : 'POST';

      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const detail = errData.detail;
        const msg = Array.isArray(detail)
          ? detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
          : (detail || 'Failed to save credit package');
        throw new Error(msg);
      }

      setSuccess(isEditing ? 'Credit package updated' : 'Credit package created');
      setDialogOpen(false);
      fetchPackages();
    } catch (err) {
      setError(err.message);
      console.error('Error saving credit package:', err);
    } finally {
      setSaving(false);
    }
  };

  const toggleActive = async (pkg) => {
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/${pkg.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ is_active: !pkg.is_active })
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to update package');
      }
      setSuccess(`Package '${pkg.package_code}' ${pkg.is_active ? 'deactivated' : 'activated'}`);
      fetchPackages();
    } catch (err) {
      setError(err.message);
      console.error('Error toggling package:', err);
    }
  };

  const softDelete = async (pkg) => {
    if (!window.confirm(
      `Deactivate credit package "${pkg.package_name}" (${pkg.package_code})?\n\n` +
      'This is a soft delete: the pack is hidden from buyers but purchase history is preserved. ' +
      'You can re-activate it later.'
    )) {
      return;
    }
    setError(null);
    try {
      const res = await fetch(`${API_BASE}/${pkg.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || 'Failed to delete package');
      }
      setSuccess(`Package '${pkg.package_code}' deactivated`);
      fetchPackages();
    } catch (err) {
      setError(err.message);
      console.error('Error deleting package:', err);
    }
  };

  // ============================================
  // Form handlers
  // ============================================

  const openCreate = () => {
    setIsEditing(false);
    setSelectedId(null);
    setFormData(emptyForm);
    setDialogOpen(true);
  };

  const openEdit = (pkg) => {
    setIsEditing(true);
    setSelectedId(pkg.id);
    setFormData({
      package_code: pkg.package_code,
      package_name: pkg.package_name,
      description: pkg.description || '',
      credits: pkg.credits,
      price_usd: pkg.price_usd,
      discount_percentage: pkg.discount_percentage || 0,
      stripe_price_id: pkg.stripe_price_id || '',
      stripe_product_id: pkg.stripe_product_id || '',
      is_active: pkg.is_active,
      display_order: pkg.display_order || 0
    });
    setDialogOpen(true);
  };

  // ============================================
  // Render helpers
  // ============================================

  const formatPrice = (price) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(price || 0);

  const pricePer1k = (pkg) => {
    if (!pkg.credits) return '-';
    return `${formatPrice((pkg.price_usd / pkg.credits) * 1000)} / 1k`;
  };

  // Basic client-side validity mirror of the backend constraints.
  const formValid =
    (isEditing || formData.package_code.trim().length > 0) &&
    formData.package_name.trim().length > 0 &&
    parseInt(formData.credits, 10) > 0 &&
    parseFloat(formData.price_usd) > 0 &&
    parseInt(formData.discount_percentage, 10) >= 0 &&
    parseInt(formData.discount_percentage, 10) <= 100;

  // ============================================
  // Main render
  // ============================================

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <CreditCardIcon color="primary" />
          <Box>
            <Typography variant="h4" component="h1">Credit Packages</Typography>
            <Typography variant="body2" color="text.secondary">
              Manage the buyable credit packs shown on the "Buy Credits" page
            </Typography>
          </Box>
        </Box>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          Add Package
        </Button>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Alert severity="info" sx={{ mb: 3 }}>
        Stripe Price/Product IDs are optional. When set, they tie this pack to the live Stripe
        checkout for accurate reporting. Editing them here only affects new purchases going forward;
        in-flight checkouts and existing purchase history are unaffected.
      </Alert>

      {/* Table */}
      <Paper sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: 2 }}>
        {loading && packages.length === 0 ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <CircularProgress />
            <Typography sx={{ mt: 2 }} color="text.secondary">Loading credit packages...</Typography>
          </Box>
        ) : packages.length === 0 ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>No credit packages yet</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Create your first buyable credit pack to make it available to customers.
            </Typography>
            <Button variant="outlined" startIcon={<AddIcon />} onClick={openCreate}>
              Add Package
            </Button>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                    <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
                    <TableCell sx={{ fontWeight: 700 }}>
                      Code
                      <Tooltip title="Stable machine-readable id the buyer flow uses to look up this pack. It cannot be changed after creation." arrow>
                        <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                      </Tooltip>
                    </TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>Credits</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>Price</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 700 }}>
                      Value
                      <Tooltip title="Effective price per 1,000 credits — handy for comparing packs." arrow>
                        <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                      </Tooltip>
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>Discount</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>
                      Stripe
                      <Tooltip title="Whether this pack is linked to a Stripe price id." arrow>
                        <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                      </Tooltip>
                    </TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>Active</TableCell>
                    <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {packages
                    .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                    .map((pkg) => (
                      <TableRow key={pkg.id} hover sx={{ opacity: pkg.is_active ? 1 : 0.55 }}>
                        <TableCell>
                          <Typography variant="body1" fontWeight="bold">{pkg.package_name}</Typography>
                          {pkg.description && (
                            <Typography variant="caption" color="text.secondary" noWrap sx={{ display: 'block', maxWidth: 260 }}>
                              {pkg.description}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Chip label={pkg.package_code} size="small" variant="outlined" />
                        </TableCell>
                        <TableCell align="right">{pkg.credits.toLocaleString()}</TableCell>
                        <TableCell align="right">
                          <Typography variant="body2" fontWeight="bold">{formatPrice(pkg.price_usd)}</Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography variant="caption" color="text.secondary">{pricePer1k(pkg)}</Typography>
                        </TableCell>
                        <TableCell align="center">
                          {pkg.discount_percentage > 0
                            ? <Chip label={`${pkg.discount_percentage}% off`} size="small" color="secondary" />
                            : <Typography variant="caption" color="text.secondary">—</Typography>}
                        </TableCell>
                        <TableCell align="center">
                          {pkg.stripe_price_id
                            ? <Tooltip title={pkg.stripe_price_id}><Chip label="Linked" size="small" color="success" variant="outlined" /></Tooltip>
                            : <Chip label="None" size="small" variant="outlined" />}
                        </TableCell>
                        <TableCell align="center">
                          <Switch
                            checked={pkg.is_active}
                            onChange={() => toggleActive(pkg)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="center">
                          <Tooltip title="Edit">
                            <IconButton size="small" onClick={() => openEdit(pkg)}>
                              <EditIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Deactivate (soft delete)">
                            <span>
                              <IconButton size="small" onClick={() => softDelete(pkg)} disabled={!pkg.is_active}>
                                <DeleteIcon />
                              </IconButton>
                            </span>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            </TableContainer>
            <TablePagination
              rowsPerPageOptions={[5, 10, 25]}
              component="div"
              count={packages.length}
              rowsPerPage={rowsPerPage}
              page={page}
              onPageChange={(e, newPage) => setPage(newPage)}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
            />
          </>
        )}
      </Paper>

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>{isEditing ? 'Edit Credit Package' : 'Create Credit Package'}</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Package Code"
                value={formData.package_code}
                onChange={(e) => setFormData({ ...formData, package_code: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
                helperText={isEditing ? 'Code cannot be changed' : "Lowercase, no spaces (e.g. 'starter')"}
                disabled={isEditing}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Package Name"
                value={formData.package_name}
                onChange={(e) => setFormData({ ...formData, package_name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={2}
                helperText="Shown on the package card to buyers"
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Credits"
                type="number"
                value={formData.credits}
                onChange={(e) => setFormData({ ...formData, credits: e.target.value })}
                helperText="Must be greater than 0"
                inputProps={{ min: 1, step: 1 }}
                error={parseInt(formData.credits, 10) <= 0 || Number.isNaN(parseInt(formData.credits, 10))}
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Price (USD)"
                type="number"
                value={formData.price_usd}
                onChange={(e) => setFormData({ ...formData, price_usd: e.target.value })}
                helperText="Must be greater than 0"
                inputProps={{ min: 0.01, step: 0.01 }}
                error={parseFloat(formData.price_usd) <= 0 || Number.isNaN(parseFloat(formData.price_usd))}
                required
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Discount %"
                type="number"
                value={formData.discount_percentage}
                onChange={(e) => setFormData({ ...formData, discount_percentage: e.target.value })}
                helperText="0–100 (badge only)"
                inputProps={{ min: 0, max: 100, step: 1 }}
                error={parseInt(formData.discount_percentage, 10) < 0 || parseInt(formData.discount_percentage, 10) > 100}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }}>
                <Typography variant="subtitle2" color="text.secondary">
                  Stripe (optional — ties to live checkout)
                </Typography>
              </Divider>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Stripe Price ID"
                value={formData.stripe_price_id}
                onChange={(e) => setFormData({ ...formData, stripe_price_id: e.target.value })}
                helperText="e.g. price_1A2b3C... (leave blank to use dynamic pricing)"
                InputProps={{
                  endAdornment: (
                    <Tooltip title="The Stripe price object this pack maps to. Optional; the buyer flow can also build a price dynamically from the credits/price above." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 16, opacity: 0.6, cursor: 'help' }} />
                    </Tooltip>
                  )
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Stripe Product ID"
                value={formData.stripe_product_id}
                onChange={(e) => setFormData({ ...formData, stripe_product_id: e.target.value })}
                helperText="e.g. prod_ABC123 (optional)"
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 1 }} />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Display Order"
                type="number"
                value={formData.display_order}
                onChange={(e) => setFormData({ ...formData, display_order: e.target.value })}
                helperText="Lower numbers show first"
                inputProps={{ step: 1 }}
              />
            </Grid>
            <Grid item xs={12} md={6} sx={{ display: 'flex', alignItems: 'center' }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_active}
                    onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                  />
                }
                label="Active (visible to buyers)"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={savePackage}
            variant="contained"
            disabled={!formValid || saving}
            startIcon={saving ? <CircularProgress size={18} /> : undefined}
          >
            {isEditing ? 'Save Changes' : 'Create Package'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CreditPackages;
