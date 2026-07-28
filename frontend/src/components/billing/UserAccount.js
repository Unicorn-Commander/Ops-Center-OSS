import React, { useState, useEffect } from 'react';
import {
  Grid, Card, CardContent, Typography, TextField, Button,
  Box, IconButton, List, ListItem, ListItemText, ListItemSecondaryAction,
  Dialog, DialogTitle, DialogContent, DialogActions, Chip,
  LinearProgress, InputAdornment, Alert, Divider,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow
} from '@mui/material';
import {
  Key, Add, Delete, Visibility, VisibilityOff, CreditCard,
  TrendingUp, AccessTime, CheckCircle, Warning, Person
} from '@mui/icons-material';

export default function UserAccount({ showSnackbar, userInfo, refreshUserInfo }) {
  const [usage, setUsage] = useState(null);
  const [byokKeys, setByokKeys] = useState([]);
  const [subscriptionTiers, setSubscriptionTiers] = useState([]);
  const [showKeys, setShowKeys] = useState({});
  const [keyDialog, setKeyDialog] = useState({ open: false, data: null });
  const [upgradeDialog, setUpgradeDialog] = useState({ open: false, tier: null });
  const [loadingUsage, setLoadingUsage] = useState(true);

  useEffect(() => {
    fetchUsage();
    fetchSubscriptionTiers();
  }, []);

  const fetchUsage = async () => {
    try {
      setLoadingUsage(true);
      const response = await fetch('/api/v1/billing/account/usage', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsage(data);
      }
    } catch (err) {
      console.error('Failed to fetch usage:', err);
    } finally {
      setLoadingUsage(false);
    }
  };

  const fetchSubscriptionTiers = async () => {
    try {
      const response = await fetch('/api/v1/billing/config/subscription-tiers');
      if (response.ok) {
        const data = await response.json();
        setSubscriptionTiers(data);
      }
    } catch (err) {
      console.error('Failed to fetch subscription tiers:', err);
    }
  };

  const handleAddKey = () => {
    setKeyDialog({
      open: true,
      data: { provider: '', key: '', is_active: true }
    });
  };

  const handleSaveKey = async () => {
    try {
      const response = await fetch('/api/v1/billing/account/byok-keys', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        },
        body: JSON.stringify(keyDialog.data)
      });

      if (!response.ok) throw new Error('Failed to save API key');

      showSnackbar('API key saved successfully');
      refreshUserInfo();
      setKeyDialog({ open: false, data: null });
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const handleDeleteKey = async (provider) => {
    try {
      const response = await fetch(`/api/v1/billing/account/byok-keys/${provider}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) throw new Error('Failed to delete API key');

      showSnackbar('API key deleted successfully');
      refreshUserInfo();
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

  const handleUpgrade = async (tier) => {
    try {
      const response = await fetch('/api/v1/billing/account/subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        },
        body: JSON.stringify({ tier: tier.name })
      });

      if (!response.ok) throw new Error('Failed to update subscription');

      const data = await response.json();

      if (data.payment_required) {
        // Redirect to payment page
        window.open(data.checkout_url, '_blank');
        showSnackbar('Redirecting to payment page...');
      } else {
        showSnackbar('Subscription updated successfully');
        refreshUserInfo();
      }

      setUpgradeDialog({ open: false, tier: null });
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const getUsagePercentage = () => {
    if (!usage?.current_month || usage.current_month.tokens_limit <= 0) return 0;
    return Math.min(100, (usage.current_month.tokens_used / usage.current_month.tokens_limit) * 100);
  };

  const formatNumber = (num) => {
    if (num === -1) return 'Unlimited';
    return num.toLocaleString();
  };

  const getCurrentTier = () => {
    return subscriptionTiers.find(t => t.name === userInfo?.subscription_tier) || null;
  };

  return (
    <Grid container spacing={3}>
      {/* Account Overview */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <Person sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Account Information</Typography>
            </Box>

            <List>
              <ListItem>
                <ListItemText
                  primary="Email"
                  secondary={userInfo?.email || 'N/A'}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="User ID"
                  secondary={userInfo?.user_id || 'N/A'}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Subscription Tier"
                  secondary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Chip
                        label={userInfo?.subscription_tier?.toUpperCase() || 'FREE'}
                        color={userInfo?.subscription_tier === 'enterprise' ? 'primary' : 'default'}
                        size="small"
                      />
                      {getCurrentTier()?.byok_enabled && (
                        <Chip label="BYOK Enabled" color="success" size="small" />
                      )}
                    </Box>
                  }
                />
              </ListItem>
            </List>
          </CardContent>
        </Card>
      </Grid>

      {/* Usage Statistics */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <TrendingUp sx={{ mr: 1, color: 'primary.main' }} />
              <Typography variant="h6">Usage This Month</Typography>
            </Box>

            {loadingUsage ? (
              <LinearProgress />
            ) : usage?.current_month ? (
              <>
                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">Tokens Used</Typography>
                    <Typography variant="body2">
                      {formatNumber(usage.current_month.tokens_used)} / {formatNumber(usage.current_month.tokens_limit)}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={getUsagePercentage()}
                    color={getUsagePercentage() > 80 ? 'warning' : 'primary'}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                  {getUsagePercentage() > 80 && (
                    <Alert severity="warning" sx={{ mt: 1 }}>
                      You've used {getUsagePercentage().toFixed(0)}% of your monthly tokens
                    </Alert>
                  )}
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Requests
                    </Typography>
                    <Typography variant="h6">
                      {usage.current_month.requests?.toLocaleString() || 0}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="textSecondary">
                      Estimated Cost
                    </Typography>
                    <Typography variant="h6">
                      ${usage.current_month.cost?.toFixed(2) || '0.00'}
                    </Typography>
                  </Grid>
                </Grid>

                {usage.current_month.models_used && (
                  <Box mt={2}>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      Models Used
                    </Typography>
                    {Object.entries(usage.current_month.models_used).map(([model, tokens]) => (
                      <Box key={model} display="flex" justifyContent="space-between" mb={0.5}>
                        <Typography variant="body2">{model}</Typography>
                        <Typography variant="body2">{tokens.toLocaleString()} tokens</Typography>
                      </Box>
                    ))}
                  </Box>
                )}
              </>
            ) : (
              <Typography color="textSecondary">No usage data available</Typography>
            )}
          </CardContent>
        </Card>
      </Grid>

      {/* BYOK API Keys */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Box display="flex" alignItems="center">
                <Key sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">Your API Keys (BYOK)</Typography>
              </Box>
              <Button
                variant="outlined"
                startIcon={<Add />}
                onClick={handleAddKey}
                disabled={!getCurrentTier()?.byok_enabled && userInfo?.subscription_tier !== 'enterprise'}
              >
                Add Key
              </Button>
            </Box>

            {!getCurrentTier()?.byok_enabled && userInfo?.subscription_tier !== 'enterprise' && (
              <Alert severity="info" sx={{ mb: 2 }}>
                Upgrade to a paid plan to use your own API keys (BYOK)
              </Alert>
            )}

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
                  {(userInfo?.byok_keys || []).map((key) => (
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
                        <Chip
                          label={key.is_active ? 'Active' : 'Inactive'}
                          color={key.is_active ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {key.added_date ? new Date(key.added_date).toLocaleDateString() : 'Unknown'}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => handleDeleteKey(key.provider)}
                        >
                          <Delete />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                  {(!userInfo?.byok_keys || userInfo.byok_keys.length === 0) && (
                    <TableRow>
                      <TableCell colSpan={5} align="center">
                        <Typography color="textSecondary">
                          No API keys configured
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

      {/* Subscription Plans */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              💎 Subscription Plans
            </Typography>

            <Grid container spacing={2}>
              {subscriptionTiers.map((tier) => (
                <Grid item xs={12} sm={6} md={3} key={tier.name}>
                  <Card
                    variant="outlined"
                    sx={{
                      border: tier.name === userInfo?.subscription_tier ? '2px solid' : '1px solid',
                      borderColor: tier.name === userInfo?.subscription_tier ? 'primary.main' : 'divider'
                    }}
                  >
                    <CardContent>
                      {tier.name === userInfo?.subscription_tier && (
                        <Chip label="Current Plan" color="primary" size="small" sx={{ mb: 1 }} />
                      )}
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
                        <Chip label="BYOK Support" color="success" size="small" sx={{ mb: 1 }} />
                      )}
                      <List dense sx={{ mb: 2 }}>
                        {tier.features.slice(0, 3).map((feature, idx) => (
                          <ListItem key={idx} sx={{ py: 0, px: 0 }}>
                            <ListItemText
                              primary={`✓ ${feature}`}
                              primaryTypographyProps={{ variant: 'body2' }}
                            />
                          </ListItem>
                        ))}
                      </List>
                      {tier.name !== userInfo?.subscription_tier && (
                        <Button
                          variant={tier.price > 0 ? 'contained' : 'outlined'}
                          color="primary"
                          size="small"
                          fullWidth
                          onClick={() => setUpgradeDialog({ open: true, tier })}
                        >
                          {tier.price === 0 ? 'Downgrade' : 'Upgrade'}
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      {/* Add API Key Dialog */}
      <Dialog open={keyDialog.open} onClose={() => setKeyDialog({ open: false, data: null })} maxWidth="sm" fullWidth>
        <DialogTitle>Add API Key</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Provider"
            value={keyDialog.data?.provider || ''}
            onChange={(e) => setKeyDialog({
              ...keyDialog,
              data: { ...keyDialog.data, provider: e.target.value }
            })}
            margin="normal"
            placeholder="e.g., openai, anthropic, openrouter"
            helperText="Enter the provider name (openai, anthropic, cohere, openrouter, etc.)"
          />
          <TextField
            fullWidth
            label="API Key"
            value={keyDialog.data?.key || ''}
            onChange={(e) => setKeyDialog({
              ...keyDialog,
              data: { ...keyDialog.data, key: e.target.value }
            })}
            margin="normal"
            type="password"
            helperText="Your API key will be encrypted and stored securely"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setKeyDialog({ open: false, data: null })}>
            Cancel
          </Button>
          <Button
            onClick={handleSaveKey}
            variant="contained"
            color="primary"
            disabled={!keyDialog.data?.provider || !keyDialog.data?.key}
          >
            Save Key
          </Button>
        </DialogActions>
      </Dialog>

      {/* Upgrade Dialog */}
      <Dialog open={upgradeDialog.open} onClose={() => setUpgradeDialog({ open: false, tier: null })} maxWidth="sm" fullWidth>
        <DialogTitle>
          {upgradeDialog.tier?.price > 0 ? 'Upgrade' : 'Change'} to {upgradeDialog.tier?.name.toUpperCase()}
        </DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            You are about to {upgradeDialog.tier?.price > 0 ? 'upgrade' : 'change'} to the {upgradeDialog.tier?.name.toUpperCase()} plan.
          </Typography>

          <Box mt={2}>
            <Typography variant="h5">
              ${upgradeDialog.tier?.price}/month
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              {upgradeDialog.tier?.tokens_per_month === -1
                ? 'Unlimited tokens'
                : `${upgradeDialog.tier?.tokens_per_month?.toLocaleString()} tokens per month`}
            </Typography>
          </Box>

          <Box mt={2}>
            <Typography variant="body2" fontWeight="bold">Features:</Typography>
            <List dense>
              {upgradeDialog.tier?.features.map((feature, idx) => (
                <ListItem key={idx} sx={{ py: 0, px: 0 }}>
                  <ListItemText
                    primary={`✓ ${feature}`}
                    primaryTypographyProps={{ variant: 'body2' }}
                  />
                </ListItem>
              ))}
            </List>
          </Box>

          {upgradeDialog.tier?.price > 0 && (
            <Alert severity="info" sx={{ mt: 2 }}>
              You will be redirected to the payment page to complete your subscription.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUpgradeDialog({ open: false, tier: null })}>
            Cancel
          </Button>
          <Button
            onClick={() => handleUpgrade(upgradeDialog.tier)}
            variant="contained"
            color="primary"
          >
            {upgradeDialog.tier?.price > 0 ? 'Continue to Payment' : 'Confirm Change'}
          </Button>
        </DialogActions>
      </Dialog>
    </Grid>
  );
}