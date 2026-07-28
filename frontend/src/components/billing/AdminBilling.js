import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, TextField, Button,
  Switch, FormControlLabel, Divider, Box, IconButton,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Dialog, DialogTitle, DialogContent, DialogActions, Chip,
  List, ListItem, ListItemText, ListItemSecondaryAction,
  InputAdornment, Tooltip
} from '@mui/material';
import {
  Save, Add, Delete, Edit, Visibility, VisibilityOff,
  CheckCircle, Cancel, Settings, Key, CreditCard, Layers
} from '@mui/icons-material';

export default function AdminBilling({ showSnackbar }) {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showKeys, setShowKeys] = useState({});
  const [editDialog, setEditDialog] = useState({ open: false, type: null, data: null });
  const [servicesStatus, setServicesStatus] = useState(null);

  useEffect(() => {
    fetchConfig();
    checkServicesStatus();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch('/api/v1/billing/config', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) throw new Error('Failed to fetch configuration');

      const data = await response.json();
      setConfig(data);
    } catch (err) {
      showSnackbar(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const checkServicesStatus = async () => {
    try {
      const response = await fetch('/api/v1/billing/services/status');
      if (response.ok) {
        const data = await response.json();
        setServicesStatus(data);
      }
    } catch (err) {
      console.error('Failed to check services status:', err);
    }
  };

  const saveConfig = async () => {
    try {
      const response = await fetch('/api/v1/billing/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) throw new Error('Failed to save configuration');

      showSnackbar('Configuration saved successfully');
      fetchConfig();
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const toggleKeyVisibility = (provider) => {
    setShowKeys(prev => ({
      ...prev,
      [provider]: !prev[provider]
    }));
  };

  const openEditDialog = (type, data = null) => {
    setEditDialog({ open: true, type, data: data || getDefaultData(type) });
  };

  const closeEditDialog = () => {
    setEditDialog({ open: false, type: null, data: null });
  };

  const getDefaultData = (type) => {
    switch (type) {
      case 'provider-key':
        return { provider: '', key: '', is_active: true };
      case 'subscription-tier':
        return {
          name: '',
          price: 0,
          tokens_per_month: 100000,
          features: [],
          byok_enabled: false
        };
      case 'stripe':
        return {
          publishable_key: '',
          secret_key: '',
          webhook_secret: '',
          test_mode: true
        };
      default:
        return {};
    }
  };

  const handleDialogSave = async () => {
    const { type, data } = editDialog;

    try {
      if (type === 'provider-key') {
        const response = await fetch('/api/v1/billing/config/provider-keys', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Admin-Token': localStorage.getItem('adminToken') || ''
          },
          body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to save provider key');
        showSnackbar('Provider key saved successfully');
      } else if (type === 'subscription-tier') {
        const newTiers = [...(config.subscription_tiers || [])];
        const existingIndex = newTiers.findIndex(t => t.name === data.name);

        if (existingIndex >= 0) {
          newTiers[existingIndex] = data;
        } else {
          newTiers.push(data);
        }

        const response = await fetch('/api/v1/billing/config/subscription-tiers', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Admin-Token': localStorage.getItem('adminToken') || ''
          },
          body: JSON.stringify(newTiers)
        });

        if (!response.ok) throw new Error('Failed to save subscription tiers');
        showSnackbar('Subscription tier saved successfully');
      } else if (type === 'stripe') {
        const response = await fetch('/api/v1/billing/config/stripe', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Admin-Token': localStorage.getItem('adminToken') || ''
          },
          body: JSON.stringify(data)
        });

        if (!response.ok) throw new Error('Failed to save Stripe configuration');
        showSnackbar('Stripe configuration saved successfully');
      }

      fetchConfig();
      closeEditDialog();
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const deleteProviderKey = async (provider) => {
    try {
      const response = await fetch(`/api/v1/billing/config/provider-keys/${provider}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) throw new Error('Failed to delete provider key');

      showSnackbar('Provider key deleted successfully');
      fetchConfig();
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const ServiceStatusChip = ({ service, status }) => {
    const getColor = () => {
      if (status === 'healthy' || status === 'configured' || status === true) return 'success';
      if (status === 'unhealthy') return 'warning';
      return 'error';
    };

    return (
      <Chip
        label={`${service}: ${status === true ? 'configured' : status || 'offline'}`}
        color={getColor()}
        size="small"
        sx={{ mr: 1, mb: 1 }}
      />
    );
  };

  if (loading || !config) {
    return <Typography>Loading configuration...</Typography>;
  }

  return (
    <Grid container spacing={3}>
      {/* Service Status */}
      {servicesStatus && (
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🔌 Service Status
              </Typography>
              <Box sx={{ mt: 2 }}>
                <ServiceStatusChip service="Lago" status={servicesStatus.lago?.status} />
                <ServiceStatusChip service="LiteLLM" status={servicesStatus.litellm?.status} />
                <ServiceStatusChip service="Stripe" status={servicesStatus.stripe?.configured} />
                <ServiceStatusChip service="Authentik" status={servicesStatus.authentik?.integrated} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      )}

      {/* Billing Configuration */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">⚙️ Billing Configuration</Typography>
              <Switch
                checked={config.billing_enabled || false}
                onChange={(e) => setConfig({ ...config, billing_enabled: e.target.checked })}
                color="primary"
              />
            </Box>

            <FormControlLabel
              control={
                <Switch
                  checked={config.billing_enabled || false}
                  onChange={(e) => setConfig({ ...config, billing_enabled: e.target.checked })}
                />
              }
              label="Enable Billing System"
              sx={{ mb: 2 }}
            />

            <TextField
              fullWidth
              label="Lago API Key"
              value={config.lago_api_key || ''}
              onChange={(e) => setConfig({ ...config, lago_api_key: e.target.value })}
              margin="normal"
              type={showKeys.lago ? 'text' : 'password'}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => toggleKeyVisibility('lago')}>
                      {showKeys.lago ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />

            <TextField
              fullWidth
              label="LiteLLM Master Key"
              value={config.litellm_master_key || ''}
              onChange={(e) => setConfig({ ...config, litellm_master_key: e.target.value })}
              margin="normal"
              type={showKeys.litellm ? 'text' : 'password'}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={() => toggleKeyVisibility('litellm')}>
                      {showKeys.litellm ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />

            <Box mt={2}>
              <Button
                variant="contained"
                color="primary"
                onClick={saveConfig}
                startIcon={<Save />}
                fullWidth
              >
                Save Configuration
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Stripe Configuration */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">💳 Stripe Configuration</Typography>
              <IconButton
                color="primary"
                onClick={() => openEditDialog('stripe', config.stripe)}
              >
                <Settings />
              </IconButton>
            </Box>

            {config.stripe ? (
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Publishable Key"
                    secondary={config.stripe.publishable_key ? '••••••' + config.stripe.publishable_key.slice(-4) : 'Not configured'}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Mode"
                    secondary={config.stripe.test_mode ? 'Test Mode' : 'Live Mode'}
                  />
                  <Chip
                    label={config.stripe.test_mode ? 'TEST' : 'LIVE'}
                    color={config.stripe.test_mode ? 'warning' : 'success'}
                    size="small"
                  />
                </ListItem>
              </List>
            ) : (
              <Box textAlign="center" py={2}>
                <Typography color="textSecondary">
                  Stripe not configured
                </Typography>
                <Button
                  variant="outlined"
                  onClick={() => openEditDialog('stripe')}
                  sx={{ mt: 1 }}
                >
                  Configure Stripe
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* Provider API Keys */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">🔑 Provider API Keys</Typography>
              <Button
                variant="outlined"
                startIcon={<Add />}
                onClick={() => openEditDialog('provider-key')}
              >
                Add Key
              </Button>
            </Box>

            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Provider</TableCell>
                    <TableCell>Key</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Added</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(config.provider_keys || []).map((key) => (
                    <TableRow key={key.provider}>
                      <TableCell>
                        <Chip label={key.provider} size="small" />
                      </TableCell>
                      <TableCell>
                        {showKeys[key.provider] ? key.key : '••••••' + key.key.slice(-4)}
                        <IconButton
                          size="small"
                          onClick={() => toggleKeyVisibility(key.provider)}
                        >
                          {showKeys[key.provider] ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </TableCell>
                      <TableCell>
                        {key.is_active ? (
                          <Chip label="Active" color="success" size="small" />
                        ) : (
                          <Chip label="Inactive" color="default" size="small" />
                        )}
                      </TableCell>
                      <TableCell>
                        {key.added_date ? new Date(key.added_date).toLocaleDateString() : 'Unknown'}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => openEditDialog('provider-key', key)}
                        >
                          <Edit />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => deleteProviderKey(key.provider)}
                        >
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(!config.provider_keys || config.provider_keys.length === 0) && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography color="textSecondary">
                          No provider keys configured
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>

      {/* Subscription Tiers */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">📦 Subscription Tiers</Typography>
              <Button
                variant="outlined"
                startIcon={<Add />}
                onClick={() => openEditDialog('subscription-tier')}
              >
                Add Tier
              </Button>
            </Box>

            <Grid container spacing={2}>
              {(config.subscription_tiers || []).map((tier) => (
                <Grid item xs={12} sm={6} md={3} key={tier.name}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" color="primary" gutterBottom>
                        {tier.name.toUpperCase()}
                      </Typography>
                      <Typography variant="h4" gutterBottom>
                        ${tier.price}
                        <Typography variant="body2" component="span" color="textSecondary">
                          /month
                        </Typography>
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="body2" color="textSecondary" gutterBottom>
                        {tier.tokens_per_month === -1
                          ? 'Unlimited tokens'
                          : `${tier.tokens_per_month.toLocaleString()} tokens/month`}
                      </Typography>
                      {tier.byok_enabled && (
                        <Chip label="BYOK" color="primary" size="small" sx={{ mb: 1 }} />
                      )}
                      <List dense>
                        {tier.features.map((feature, idx) => (
                          <ListItem key={idx} sx={{ py: 0 }}>
                            <ListItemText
                              primary={`• ${feature}`}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                      </List>
                      <Button
                        size="small"
                        onClick={() => openEditDialog('subscription-tier', tier)}
                        fullWidth
                      >
                        Edit
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Edit Dialog */}
      <Dialog open={editDialog.open} onClose={closeEditDialog} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editDialog.type === 'provider-key' && '🔑 Provider API Key'}
          {editDialog.type === 'subscription-tier' && '📦 Subscription Tier'}
          {editDialog.type === 'stripe' && '💳 Stripe Configuration'}
        </DialogTitle>
        <DialogContent>
          {editDialog.type === 'provider-key' && (
            <>
              <TextField
                fullWidth
                label="Provider"
                value={editDialog.data?.provider || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, provider: e.target.value }
                })}
                margin="normal"
                placeholder="e.g., openai, anthropic"
              />
              <TextField
                fullWidth
                label="API Key"
                value={editDialog.data?.key || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, key: e.target.value }
                })}
                margin="normal"
                type="password"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={editDialog.data?.is_active || false}
                    onChange={(e) => setEditDialog({
                      ...editDialog,
                      data: { ...editDialog.data, is_active: e.target.checked }
                    })}
                  />
                }
                label="Active"
                sx={{ mt: 2 }}
              />
            </>
          )}

          {editDialog.type === 'subscription-tier' && (
            <>
              <TextField
                fullWidth
                label="Tier Name"
                value={editDialog.data?.name || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, name: e.target.value }
                })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Price ($/month)"
                type="number"
                value={editDialog.data?.price || 0}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, price: parseFloat(e.target.value) }
                })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Tokens per Month (-1 for unlimited)"
                type="number"
                value={editDialog.data?.tokens_per_month || 0}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, tokens_per_month: parseInt(e.target.value) }
                })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Features (comma-separated)"
                value={editDialog.data?.features?.join(', ') || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: {
                    ...editDialog.data,
                    features: e.target.value.split(',').map(f => f.trim()).filter(f => f)
                  }
                })}
                margin="normal"
                multiline
                rows={3}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={editDialog.data?.byok_enabled || false}
                    onChange={(e) => setEditDialog({
                      ...editDialog,
                      data: { ...editDialog.data, byok_enabled: e.target.checked }
                    })}
                  />
                }
                label="Enable BYOK (Bring Your Own Key)"
                sx={{ mt: 2 }}
              />
            </>
          )}

          {editDialog.type === 'stripe' && (
            <>
              <TextField
                fullWidth
                label="Publishable Key"
                value={editDialog.data?.publishable_key || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, publishable_key: e.target.value }
                })}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Secret Key"
                value={editDialog.data?.secret_key || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, secret_key: e.target.value }
                })}
                margin="normal"
                type="password"
              />
              <TextField
                fullWidth
                label="Webhook Secret"
                value={editDialog.data?.webhook_secret || ''}
                onChange={(e) => setEditDialog({
                  ...editDialog,
                  data: { ...editDialog.data, webhook_secret: e.target.value }
                })}
                margin="normal"
                type="password"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={editDialog.data?.test_mode !== false}
                    onChange={(e) => setEditDialog({
                      ...editDialog,
                      data: { ...editDialog.data, test_mode: e.target.checked }
                    })}
                  />
                }
                label="Test Mode"
                sx={{ mt: 2 }}
              />
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeEditDialog}>Cancel</Button>
          <Button onClick={handleDialogSave} variant="contained" color="primary">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
}