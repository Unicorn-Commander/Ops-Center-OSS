/**
 * Webhooks Management Page
 * Admin interface for managing webhooks with delivery history and testing
 *
 * Features:
 * - Webhook CRUD operations
 * - Event subscription management
 * - Delivery history with status codes
 * - Webhook testing
 * - Secret key management
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
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControlLabel,
  Switch,
  Alert,
  Snackbar,
  Tooltip,
  Grid,
  Card,
  CardContent,
  Collapse,
  CircularProgress,
  FormGroup,
  Checkbox,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandIcon,
  ChevronRight as CollapseIcon,
  ContentCopy as CopyIcon,
  Refresh as RefreshIcon,
  PlayArrow as TestIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Link as LinkIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

// Available webhook events
const WEBHOOK_EVENTS = [
  { key: 'user.created', label: 'User Created', category: 'Users' },
  { key: 'user.deleted', label: 'User Deleted', category: 'Users' },
  { key: 'subscription.created', label: 'Subscription Created', category: 'Billing' },
  { key: 'subscription.cancelled', label: 'Subscription Cancelled', category: 'Billing' },
  { key: 'payment.received', label: 'Payment Received', category: 'Billing' },
  { key: 'payment.failed', label: 'Payment Failed', category: 'Billing' },
  { key: 'service.started', label: 'Service Started', category: 'Services' },
  { key: 'service.stopped', label: 'Service Stopped', category: 'Services' }
];

// Group events by category
const groupedEvents = WEBHOOK_EVENTS.reduce((acc, event) => {
  if (!acc[event.category]) {
    acc[event.category] = [];
  }
  acc[event.category].push(event);
  return acc;
}, {});

const WebhooksManagement = () => {
  // State management
  const [webhooks, setWebhooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState(null);
  const [expandedWebhook, setExpandedWebhook] = useState(null);
  const [deliveries, setDeliveries] = useState({});
  const [loadingDeliveries, setLoadingDeliveries] = useState({});
  const [testingWebhook, setTestingWebhook] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    events: [],
    secret: '',
    is_active: true
  });
  const [formErrors, setFormErrors] = useState({});

  // Load webhooks on mount
  useEffect(() => {
    loadWebhooks();
  }, []);

  // ============================================
  // API Functions
  // ============================================

  const loadWebhooks = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/admin/webhooks', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load webhooks');
      }

      const data = await response.json();
      setWebhooks(data.webhooks || data || []);
    } catch (error) {
      console.error('Error loading webhooks:', error);
      showSnackbar('Failed to load webhooks', 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadDeliveries = async (webhookId) => {
    if (deliveries[webhookId]) {
      return; // Already loaded
    }

    try {
      setLoadingDeliveries(prev => ({ ...prev, [webhookId]: true }));
      const response = await fetch(`/api/v1/admin/webhooks/${webhookId}/deliveries`, {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load deliveries');
      }

      const data = await response.json();
      setDeliveries(prev => ({
        ...prev,
        [webhookId]: data.deliveries || data || []
      }));
    } catch (error) {
      console.error('Error loading deliveries:', error);
      showSnackbar('Failed to load delivery history', 'error');
    } finally {
      setLoadingDeliveries(prev => ({ ...prev, [webhookId]: false }));
    }
  };

  const handleCreateOrUpdate = async () => {
    // Validate form
    const errors = {};
    if (!formData.name.trim()) {
      errors.name = 'Name is required';
    }
    if (!formData.url.trim()) {
      errors.url = 'URL is required';
    } else if (!formData.url.startsWith('https://')) {
      errors.url = 'URL must start with https://';
    }
    if (formData.events.length === 0) {
      errors.events = 'Select at least one event';
    }

    if (Object.keys(errors).length > 0) {
      setFormErrors(errors);
      return;
    }

    try {
      const isEditing = !!editingWebhook;
      const url = isEditing
        ? `/api/v1/admin/webhooks/${editingWebhook.id}`
        : '/api/v1/admin/webhooks';
      const method = isEditing ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Failed to ${isEditing ? 'update' : 'create'} webhook`);
      }

      showSnackbar(`Webhook ${isEditing ? 'updated' : 'created'} successfully`, 'success');
      handleCloseDialog();
      loadWebhooks();
    } catch (error) {
      console.error('Error saving webhook:', error);
      showSnackbar(`Failed to ${editingWebhook ? 'update' : 'create'} webhook`, 'error');
    }
  };

  const handleDelete = async (webhook) => {
    if (!window.confirm(`Are you sure you want to delete webhook "${webhook.name}"?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/admin/webhooks/${webhook.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete webhook');
      }

      showSnackbar('Webhook deleted successfully', 'success');
      loadWebhooks();
    } catch (error) {
      console.error('Error deleting webhook:', error);
      showSnackbar('Failed to delete webhook', 'error');
    }
  };

  const handleTestWebhook = async (webhook) => {
    try {
      setTestingWebhook(webhook.id);
      const response = await fetch(`/api/v1/admin/webhooks/${webhook.id}/test`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to send test webhook');
      }

      const result = await response.json();
      if (result.success) {
        showSnackbar(`Test webhook sent successfully (Status: ${result.status_code})`, 'success');
      } else {
        showSnackbar(`Test webhook failed: ${result.error || 'Unknown error'}`, 'warning');
      }

      // Refresh deliveries if expanded
      if (expandedWebhook === webhook.id) {
        setDeliveries(prev => ({ ...prev, [webhook.id]: null }));
        loadDeliveries(webhook.id);
      }
    } catch (error) {
      console.error('Error testing webhook:', error);
      showSnackbar('Failed to send test webhook', 'error');
    } finally {
      setTestingWebhook(null);
    }
  };

  // ============================================
  // Event Handlers
  // ============================================

  const handleOpenDialog = (webhook = null) => {
    if (webhook) {
      setEditingWebhook(webhook);
      setFormData({
        name: webhook.name,
        url: webhook.url,
        events: webhook.events || [],
        secret: '', // Don't pre-fill secret for security
        is_active: webhook.is_active
      });
    } else {
      setEditingWebhook(null);
      setFormData({
        name: '',
        url: '',
        events: [],
        secret: generateSecret(),
        is_active: true
      });
    }
    setFormErrors({});
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingWebhook(null);
    setFormData({
      name: '',
      url: '',
      events: [],
      secret: '',
      is_active: true
    });
    setFormErrors({});
  };

  const handleExpandWebhook = async (webhookId) => {
    if (expandedWebhook === webhookId) {
      setExpandedWebhook(null);
    } else {
      setExpandedWebhook(webhookId);
      await loadDeliveries(webhookId);
    }
  };

  const handleEventToggle = (eventKey) => {
    setFormData(prev => ({
      ...prev,
      events: prev.events.includes(eventKey)
        ? prev.events.filter(e => e !== eventKey)
        : [...prev.events, eventKey]
    }));
    if (formErrors.events) {
      setFormErrors(prev => ({ ...prev, events: null }));
    }
  };

  const handleCopySecret = (secret) => {
    navigator.clipboard.writeText(secret);
    showSnackbar('Secret copied to clipboard', 'success');
  };

  const handleGenerateNewSecret = () => {
    setFormData(prev => ({ ...prev, secret: generateSecret() }));
  };

  // ============================================
  // Helper Functions
  // ============================================

  const generateSecret = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let secret = 'whsec_';
    for (let i = 0; i < 32; i++) {
      secret += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return secret;
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  const getStatusIcon = (statusCode) => {
    if (!statusCode) return <WarningIcon color="warning" fontSize="small" />;
    if (statusCode >= 200 && statusCode < 300) {
      return <SuccessIcon color="success" fontSize="small" />;
    }
    return <ErrorIcon color="error" fontSize="small" />;
  };

  const getStatusChip = (webhook) => {
    if (!webhook.is_active) {
      return <Chip label="Disabled" color="default" size="small" />;
    }
    return <Chip label="Active" color="success" size="small" />;
  };

  // Calculate summary statistics
  const stats = {
    total: webhooks.length,
    active: webhooks.filter(w => w.is_active).length,
    disabled: webhooks.filter(w => !w.is_active).length
  };

  // ============================================
  // Render
  // ============================================

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Webhook Management"
        subtitle="Configure webhooks for real-time event notifications"
        actions={(
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={loadWebhooks}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => handleOpenDialog()}
            >
              Add Webhook
            </Button>
          </Box>
        )}
      />

      {/* Summary Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(102, 126, 234, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Total Webhooks
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {stats.total}
                  </Typography>
                </Box>
                <LinkIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(17, 153, 142, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Active
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {stats.active}
                  </Typography>
                </Box>
                <SuccessIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #636363 0%, #a2ab58 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(99, 99, 99, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Disabled
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {stats.disabled}
                  </Typography>
                </Box>
                <WarningIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Webhooks Table */}
      <Paper sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: 2 }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                <TableCell sx={{ width: 50 }}></TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>URL</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Events</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Last Triggered</TableCell>
                <TableCell align="right" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <CircularProgress size={32} />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                      Loading webhooks...
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : webhooks.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No webhooks configured
                    </Typography>
                    <Button
                      variant="text"
                      startIcon={<AddIcon />}
                      onClick={() => handleOpenDialog()}
                      sx={{ mt: 1 }}
                    >
                      Add your first webhook
                    </Button>
                  </TableCell>
                </TableRow>
              ) : (
                webhooks.map((webhook) => (
                  <React.Fragment key={webhook.id}>
                    <TableRow
                      hover
                      sx={{
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        '&:hover': {
                          backgroundColor: 'rgba(102, 126, 234, 0.04)'
                        }
                      }}
                    >
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleExpandWebhook(webhook.id)}
                        >
                          {expandedWebhook === webhook.id ? <ExpandIcon /> : <CollapseIcon />}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body1" fontWeight="bold">
                          {webhook.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            maxWidth: 250,
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {webhook.url}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {(webhook.events || []).slice(0, 3).map((event) => (
                            <Chip
                              key={event}
                              label={event}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: '0.7rem' }}
                            />
                          ))}
                          {(webhook.events || []).length > 3 && (
                            <Chip
                              label={`+${webhook.events.length - 3}`}
                              size="small"
                              color="primary"
                              sx={{ fontSize: '0.7rem' }}
                            />
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>{getStatusChip(webhook)}</TableCell>
                      <TableCell>
                        <Typography variant="body2" color="text.secondary">
                          {formatDate(webhook.last_triggered_at)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Test webhook">
                          <IconButton
                            size="small"
                            onClick={() => handleTestWebhook(webhook)}
                            disabled={testingWebhook === webhook.id || !webhook.is_active}
                          >
                            {testingWebhook === webhook.id ? (
                              <CircularProgress size={18} />
                            ) : (
                              <TestIcon fontSize="small" />
                            )}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton size="small" onClick={() => handleOpenDialog(webhook)}>
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton size="small" onClick={() => handleDelete(webhook)}>
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>

                    {/* Expandable Delivery History */}
                    <TableRow>
                      <TableCell colSpan={7} sx={{ py: 0, borderBottom: expandedWebhook === webhook.id ? 1 : 0 }}>
                        <Collapse in={expandedWebhook === webhook.id} timeout="auto" unmountOnExit>
                          <Box sx={{ p: 2, backgroundColor: 'rgba(102, 126, 234, 0.02)' }}>
                            <Typography variant="subtitle2" sx={{ mb: 2, fontWeight: 600 }}>
                              Recent Deliveries
                            </Typography>
                            {loadingDeliveries[webhook.id] ? (
                              <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                                <CircularProgress size={24} />
                              </Box>
                            ) : (deliveries[webhook.id] || []).length === 0 ? (
                              <Typography variant="body2" color="text.secondary">
                                No delivery history yet
                              </Typography>
                            ) : (
                              <Table size="small">
                                <TableHead>
                                  <TableRow>
                                    <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Status</TableCell>
                                    <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Event</TableCell>
                                    <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Response</TableCell>
                                    <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Duration</TableCell>
                                    <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Timestamp</TableCell>
                                  </TableRow>
                                </TableHead>
                                <TableBody>
                                  {(deliveries[webhook.id] || []).map((delivery, idx) => (
                                    <TableRow key={delivery.id || idx}>
                                      <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                          {getStatusIcon(delivery.status_code)}
                                          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                            {delivery.status_code || 'N/A'}
                                          </Typography>
                                        </Box>
                                      </TableCell>
                                      <TableCell>
                                        <Chip
                                          label={delivery.event}
                                          size="small"
                                          sx={{ fontSize: '0.7rem' }}
                                        />
                                      </TableCell>
                                      <TableCell>
                                        <Typography
                                          variant="body2"
                                          sx={{
                                            fontSize: '0.75rem',
                                            maxWidth: 200,
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                          }}
                                        >
                                          {delivery.response_body || '-'}
                                        </Typography>
                                      </TableCell>
                                      <TableCell>
                                        <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                          {delivery.duration_ms ? `${delivery.duration_ms}ms` : '-'}
                                        </Typography>
                                      </TableCell>
                                      <TableCell>
                                        <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                          {formatDate(delivery.created_at)}
                                        </Typography>
                                      </TableCell>
                                    </TableRow>
                                  ))}
                                </TableBody>
                              </Table>
                            )}
                          </Box>
                        </Collapse>
                      </TableCell>
                    </TableRow>
                  </React.Fragment>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Add/Edit Webhook Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingWebhook ? 'Edit Webhook' : 'Add Webhook'}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Name"
              value={formData.name}
              onChange={(e) => {
                setFormData({ ...formData, name: e.target.value });
                if (formErrors.name) setFormErrors({ ...formErrors, name: null });
              }}
              error={!!formErrors.name}
              helperText={formErrors.name || 'A friendly name for this webhook'}
              fullWidth
              required
            />

            <TextField
              label="URL"
              value={formData.url}
              onChange={(e) => {
                setFormData({ ...formData, url: e.target.value });
                if (formErrors.url) setFormErrors({ ...formErrors, url: null });
              }}
              error={!!formErrors.url}
              helperText={formErrors.url || 'Must be a secure HTTPS endpoint'}
              fullWidth
              required
              placeholder="https://example.com/webhook"
            />

            <Box>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                Events *
              </Typography>
              {formErrors.events && (
                <Alert severity="error" sx={{ mb: 1 }}>
                  {formErrors.events}
                </Alert>
              )}
              {Object.entries(groupedEvents).map(([category, events]) => (
                <Box key={category} sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>
                    {category}
                  </Typography>
                  <FormGroup row>
                    {events.map((event) => (
                      <FormControlLabel
                        key={event.key}
                        control={
                          <Checkbox
                            checked={formData.events.includes(event.key)}
                            onChange={() => handleEventToggle(event.key)}
                            size="small"
                          />
                        }
                        label={event.label}
                        sx={{ minWidth: '45%' }}
                      />
                    ))}
                  </FormGroup>
                </Box>
              ))}
            </Box>

            <TextField
              label="Secret Key"
              value={formData.secret}
              onChange={(e) => setFormData({ ...formData, secret: e.target.value })}
              helperText={editingWebhook
                ? 'Leave blank to keep existing secret, or enter a new one'
                : 'Used to verify webhook signatures'
              }
              fullWidth
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <Tooltip title="Copy secret">
                      <IconButton
                        size="small"
                        onClick={() => handleCopySecret(formData.secret)}
                        disabled={!formData.secret}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Generate new secret">
                      <IconButton
                        size="small"
                        onClick={handleGenerateNewSecret}
                      >
                        <RefreshIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </InputAdornment>
                ),
                sx: { fontFamily: 'monospace', fontSize: '0.875rem' }
              }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleCreateOrUpdate} variant="contained">
            {editingWebhook ? 'Save Changes' : 'Create Webhook'}
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

export default WebhooksManagement;
