/**
 * LLM Provider Management Interface
 *
 * Comprehensive UI for managing multi-provider LLM routing with:
 * - Provider configuration (OpenRouter, OpenAI, Anthropic, Together AI, etc.)
 * - Model management and pricing
 * - WilmerAI-style routing (Eco/Balanced/Precision power levels)
 * - BYOK (Bring Your Own Key) support
 * - Usage analytics and cost tracking
 * - Provider health monitoring
 *
 * Author: Frontend Developer
 * Date: October 23, 2025
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Alert,
  CircularProgress,
  Tooltip,
  Grid,
  LinearProgress,
  Divider
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  Settings as SettingsIcon,
  TrendingUp as TrendingUpIcon,
  Speed as SpeedIcon,
  AttachMoney as MoneyIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  VpnKey as KeyIcon,
  CloudQueue as CloudIcon
} from '@mui/icons-material';

const API_BASE = '';

/**
 * Provider Types
 */
const PROVIDER_TYPES = [
  { value: 'openrouter', label: 'OpenRouter' },
  { value: 'openai', label: 'OpenAI' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'together', label: 'Together AI' },
  { value: 'huggingface', label: 'HuggingFace' },
  { value: 'google', label: 'Google' },
  { value: 'cohere', label: 'Cohere' },
  { value: 'custom', label: 'Custom' }
];

/**
 * Routing Strategies
 */
const ROUTING_STRATEGIES = [
  { value: 'cost', label: 'Cost Optimized', description: 'Always use cheapest model' },
  { value: 'latency', label: 'Latency Optimized', description: 'Always use fastest model' },
  { value: 'balanced', label: 'Balanced', description: 'Balance cost, latency, and quality' },
  { value: 'custom', label: 'Custom', description: 'Custom weighted scoring' }
];

/**
 * Power Levels (WilmerAI-style)
 */
const POWER_LEVELS = [
  { value: 'eco', label: 'Eco Mode', description: 'Cost optimized - use cheapest models', color: 'success' },
  { value: 'balanced', label: 'Balanced Mode', description: 'Balance cost and quality', color: 'primary' },
  { value: 'precision', label: 'Precision Mode', description: 'Quality optimized - use best models', color: 'warning' }
];

/**
 * Main Component
 */
export default function LLMProviderManagement() {
  const [currentTab, setCurrentTab] = useState(0);
  const [providers, setProviders] = useState([]);
  const [models, setModels] = useState([]);
  const [routingRules, setRoutingRules] = useState(null);
  const [usageStats, setUsageStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Dialogs
  const [providerDialogOpen, setProviderDialogOpen] = useState(false);
  const [modelDialogOpen, setModelDialogOpen] = useState(false);
  const [routingDialogOpen, setRoutingDialogOpen] = useState(false);
  const [byokDialogOpen, setBYOKDialogOpen] = useState(false);

  // Forms
  const [providerForm, setProviderForm] = useState({
    name: '',
    type: 'openrouter',
    api_key: '',
    api_base_url: '',
    enabled: true,
    priority: 0,
    config: {}
  });
  const [editingProvider, setEditingProvider] = useState(null);

  const [modelForm, setModelForm] = useState({
    provider_id: '',
    name: '',
    display_name: '',
    cost_per_1m_input_tokens: 0,
    cost_per_1m_output_tokens: 0,
    context_length: 4096,
    enabled: true,
    metadata: {}
  });

  const [routingForm, setRoutingForm] = useState({
    strategy: 'balanced',
    fallback_providers: [],
    model_aliases: {},
    config: {}
  });

  const [byokForm, setBYOKForm] = useState({
    provider_type: 'openai',
    api_key: '',
    enabled: true,
    preferences: {}
  });

  /**
   * Load Data
   */
  useEffect(() => {
    loadAllData();
  }, [currentTab]);

  const loadAllData = async () => {
    setLoading(true);
    setError(null);

    try {
      await Promise.all([
        loadProviders(),
        loadModels(),
        loadRoutingRules(),
        loadUsageStats()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadProviders = async () => {
    const response = await fetch(`${API_BASE}/api/v1/llm/providers`);
    if (!response.ok) throw new Error('Failed to load providers');
    const data = await response.json();
    setProviders(data);
  };

  const loadModels = async () => {
    const response = await fetch(`${API_BASE}/api/v1/llm/models?enabled_only=false`);
    if (!response.ok) throw new Error('Failed to load models');
    const data = await response.json();
    setModels(data);
  };

  const loadRoutingRules = async () => {
    const response = await fetch(`${API_BASE}/api/v1/llm/routing/rules`);
    if (!response.ok) throw new Error('Failed to load routing rules');
    const data = await response.json();
    setRoutingRules(data);
    setRoutingForm({
      strategy: data.strategy,
      fallback_providers: data.fallback_providers || [],
      model_aliases: data.model_aliases || {},
      config: data.config || {}
    });
  };

  const loadUsageStats = async () => {
    const response = await fetch(`${API_BASE}/api/v1/llm/usage?days=7`);
    if (!response.ok) throw new Error('Failed to load usage stats');
    const data = await response.json();
    setUsageStats(data);
  };

  /**
   * Provider Actions
   */
  const handleCreateProvider = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/llm/providers`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(providerForm)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create provider');
      }

      setSuccess('Provider created successfully');
      setProviderDialogOpen(false);
      resetProviderForm();
      loadProviders();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleUpdateProvider = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/llm/providers/${editingProvider.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_key: providerForm.api_key || undefined,
          enabled: providerForm.enabled,
          priority: providerForm.priority,
          config: providerForm.config
        })
      });

      if (!response.ok) throw new Error('Failed to update provider');

      setSuccess('Provider updated successfully');
      setProviderDialogOpen(false);
      setEditingProvider(null);
      resetProviderForm();
      loadProviders();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteProvider = async (providerId) => {
    if (!confirm('Are you sure? This will delete all associated models.')) return;

    try {
      const response = await fetch(`${API_BASE}/api/v1/llm/providers/${providerId}`, {
        method: 'DELETE'
      });

      if (!response.ok) throw new Error('Failed to delete provider');

      setSuccess('Provider deleted successfully');
      loadProviders();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleTestProvider = async (providerId) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/llm/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider_id: providerId })
      });

      const result = await response.json();

      if (result.status === 'success') {
        setSuccess(`Provider test successful! Latency: ${result.latency_ms}ms`);
      } else {
        setError(`Provider test failed: ${result.error}`);
      }

      loadProviders();
    } catch (err) {
      setError(err.message);
    }
  };

  const resetProviderForm = () => {
    setProviderForm({
      name: '',
      type: 'openrouter',
      api_key: '',
      api_base_url: '',
      enabled: true,
      priority: 0,
      config: {}
    });
  };

  const openEditProvider = (provider) => {
    setEditingProvider(provider);
    setProviderForm({
      name: provider.name,
      type: provider.type,
      api_key: '', // Don't show actual key
      api_base_url: '',
      enabled: provider.status === 'active',
      priority: provider.priority,
      config: {}
    });
    setProviderDialogOpen(true);
  };

  /**
   * Model Actions
   */
  const handleCreateModel = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/llm/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(modelForm)
      });

      if (!response.ok) throw new Error('Failed to create model');

      setSuccess('Model created successfully');
      setModelDialogOpen(false);
      loadModels();
    } catch (err) {
      setError(err.message);
    }
  };

  /**
   * Routing Rules Actions
   */
  const handleUpdateRoutingRules = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/llm/routing/rules`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(routingForm)
      });

      if (!response.ok) throw new Error('Failed to update routing rules');

      setSuccess('Routing rules updated successfully');
      setRoutingDialogOpen(false);
      loadRoutingRules();
    } catch (err) {
      setError(err.message);
    }
  };

  /**
   * Health Status Badge
   */
  const getHealthBadge = (status) => {
    const config = {
      healthy: { icon: <CheckCircleIcon />, color: 'success', label: 'Healthy' },
      unhealthy: { icon: <ErrorIcon />, color: 'error', label: 'Unhealthy' },
      unknown: { icon: <WarningIcon />, color: 'warning', label: 'Unknown' }
    };

    const { icon, color, label } = config[status] || config.unknown;

    return (
      <Chip
        icon={icon}
        label={label}
        color={color}
        size="small"
      />
    );
  };

  /**
   * Render Tabs
   */
  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">LLM Provider Management</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            resetProviderForm();
            setEditingProvider(null);
            setProviderDialogOpen(true);
          }}
        >
          Add Provider
        </Button>
      </Box>

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

      <Tabs value={currentTab} onChange={(e, v) => setCurrentTab(v)} sx={{ mb: 3 }}>
        <Tab label="Providers" icon={<CloudIcon />} />
        <Tab label="Models" icon={<SettingsIcon />} />
        <Tab label="Routing Rules" icon={<SpeedIcon />} />
        <Tab label="Usage Analytics" icon={<TrendingUpIcon />} />
        <Tab label="BYOK Settings" icon={<KeyIcon />} />
      </Tabs>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          {/* Tab 0: Providers */}
          {currentTab === 0 && (
            <ProvidersTab
              providers={providers}
              onEdit={openEditProvider}
              onDelete={handleDeleteProvider}
              onTest={handleTestProvider}
              getHealthBadge={getHealthBadge}
            />
          )}

          {/* Tab 1: Models */}
          {currentTab === 1 && (
            <ModelsTab
              models={models}
              providers={providers}
              onAddModel={() => setModelDialogOpen(true)}
            />
          )}

          {/* Tab 2: Routing Rules */}
          {currentTab === 2 && (
            <RoutingTab
              routingRules={routingRules}
              providers={providers}
              onEdit={() => setRoutingDialogOpen(true)}
            />
          )}

          {/* Tab 3: Usage Analytics */}
          {currentTab === 3 && (
            <UsageTab usageStats={usageStats} />
          )}

          {/* Tab 4: BYOK Settings */}
          {currentTab === 4 && (
            <BYOKTab onAddBYOK={() => setBYOKDialogOpen(true)} />
          )}
        </>
      )}

      {/* Provider Dialog */}
      <Dialog
        open={providerDialogOpen}
        onClose={() => {
          setProviderDialogOpen(false);
          setEditingProvider(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {editingProvider ? 'Edit Provider' : 'Add New Provider'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Provider Name"
                value={providerForm.name}
                onChange={(e) => setProviderForm({ ...providerForm, name: e.target.value })}
                disabled={!!editingProvider}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Provider Type</InputLabel>
                <Select
                  value={providerForm.type}
                  label="Provider Type"
                  onChange={(e) => setProviderForm({ ...providerForm, type: e.target.value })}
                  disabled={!!editingProvider}
                >
                  {PROVIDER_TYPES.map(pt => (
                    <MenuItem key={pt.value} value={pt.value}>{pt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="API Key"
                type="password"
                value={providerForm.api_key}
                onChange={(e) => setProviderForm({ ...providerForm, api_key: e.target.value })}
                placeholder={editingProvider ? "Leave blank to keep current key" : "sk-..."}
                helperText="OpenAI: platform.openai.com/api-keys | Anthropic: console.anthropic.com | Google: ai.google.dev"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="API Base URL (Optional)"
                value={providerForm.api_base_url}
                onChange={(e) => setProviderForm({ ...providerForm, api_base_url: e.target.value })}
                placeholder="https://api.example.com"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Priority"
                value={providerForm.priority}
                onChange={(e) => setProviderForm({ ...providerForm, priority: parseInt(e.target.value) })}
                helperText="Higher priority = more preferred"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={providerForm.enabled}
                    onChange={(e) => setProviderForm({ ...providerForm, enabled: e.target.checked })}
                  />
                }
                label="Enabled"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setProviderDialogOpen(false);
            setEditingProvider(null);
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={editingProvider ? handleUpdateProvider : handleCreateProvider}
          >
            {editingProvider ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Model Dialog */}
      <Dialog open={modelDialogOpen} onClose={() => setModelDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Model</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Provider</InputLabel>
                <Select
                  value={modelForm.provider_id}
                  label="Provider"
                  onChange={(e) => setModelForm({ ...modelForm, provider_id: e.target.value })}
                >
                  {providers.map(p => (
                    <MenuItem key={p.id} value={p.id}>{p.name}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Model Name"
                value={modelForm.name}
                onChange={(e) => setModelForm({ ...modelForm, name: e.target.value })}
                placeholder="gpt-4-turbo"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Display Name"
                value={modelForm.display_name}
                onChange={(e) => setModelForm({ ...modelForm, display_name: e.target.value })}
                placeholder="GPT-4 Turbo"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Cost per 1M Input Tokens ($)"
                value={modelForm.cost_per_1m_input_tokens}
                onChange={(e) => setModelForm({ ...modelForm, cost_per_1m_input_tokens: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type="number"
                label="Cost per 1M Output Tokens ($)"
                value={modelForm.cost_per_1m_output_tokens}
                onChange={(e) => setModelForm({ ...modelForm, cost_per_1m_output_tokens: parseFloat(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                type="number"
                label="Context Length"
                value={modelForm.context_length}
                onChange={(e) => setModelForm({ ...modelForm, context_length: parseInt(e.target.value) })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModelDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreateModel}>Create</Button>
        </DialogActions>
      </Dialog>

      {/* Routing Rules Dialog */}
      <Dialog open={routingDialogOpen} onClose={() => setRoutingDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Update Routing Rules</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Routing Strategy</InputLabel>
                <Select
                  value={routingForm.strategy}
                  label="Routing Strategy"
                  onChange={(e) => setRoutingForm({ ...routingForm, strategy: e.target.value })}
                >
                  {ROUTING_STRATEGIES.map(rs => (
                    <MenuItem key={rs.value} value={rs.value}>
                      {rs.label} - {rs.description}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                User Power Levels
              </Typography>
              {POWER_LEVELS.map(pl => (
                <Chip
                  key={pl.value}
                  label={pl.label}
                  color={pl.color}
                  sx={{ mr: 1, mb: 1 }}
                  icon={pl.value === 'eco' ? <MoneyIcon /> : pl.value === 'precision' ? <TrendingUpIcon /> : <SpeedIcon />}
                />
              ))}
              <Typography variant="caption" display="block" sx={{ mt: 1 }}>
                Users can select their preferred power level to balance cost, speed, and quality.
              </Typography>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRoutingDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleUpdateRoutingRules}>Update</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

/**
 * Providers Tab
 */
function ProvidersTab({ providers, onEdit, onDelete, onTest, getHealthBadge }) {
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Provider</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Health</TableCell>
            <TableCell>Models</TableCell>
            <TableCell>Avg Cost/1M</TableCell>
            <TableCell>Priority</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {providers.map((provider) => (
            <TableRow key={provider.id}>
              <TableCell>{provider.name}</TableCell>
              <TableCell>{provider.type}</TableCell>
              <TableCell>
                <Chip
                  label={provider.status}
                  color={provider.status === 'active' ? 'success' : 'default'}
                  size="small"
                />
              </TableCell>
              <TableCell>{getHealthBadge(provider.health_status)}</TableCell>
              <TableCell>{provider.models}</TableCell>
              <TableCell>
                {provider.avg_cost_per_1m !== null
                  ? `$${provider.avg_cost_per_1m.toFixed(2)}`
                  : 'N/A'}
              </TableCell>
              <TableCell>{provider.priority}</TableCell>
              <TableCell>
                <Tooltip title="Test Connection">
                  <IconButton onClick={() => onTest(provider.id)} size="small">
                    <TestIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Edit">
                  <IconButton onClick={() => onEdit(provider)} size="small">
                    <EditIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton onClick={() => onDelete(provider.id)} size="small" color="error">
                    <DeleteIcon />
                  </IconButton>
                </Tooltip>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

/**
 * Models Tab
 */
function ModelsTab({ models, providers, onAddModel }) {
  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
        <Button variant="contained" startIcon={<AddIcon />} onClick={onAddModel}>
          Add Model
        </Button>
      </Box>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Model</TableCell>
              <TableCell>Provider</TableCell>
              <TableCell>Input Cost/1M</TableCell>
              <TableCell>Output Cost/1M</TableCell>
              <TableCell>Context</TableCell>
              <TableCell>Latency</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {models.map((model) => (
              <TableRow key={model.id}>
                <TableCell>{model.display_name}</TableCell>
                <TableCell>{model.provider_name}</TableCell>
                <TableCell>${model.cost_per_1m_input.toFixed(2)}</TableCell>
                <TableCell>${model.cost_per_1m_output.toFixed(2)}</TableCell>
                <TableCell>{model.context_length.toLocaleString()}</TableCell>
                <TableCell>
                  {model.avg_latency_ms ? `${model.avg_latency_ms}ms` : 'Unknown'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={model.enabled ? 'Enabled' : 'Disabled'}
                    color={model.enabled ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}

/**
 * Routing Tab
 */
function RoutingTab({ routingRules, providers, onEdit }) {
  if (!routingRules) return null;

  return (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Current Routing Strategy</Typography>
            <Button variant="contained" startIcon={<SettingsIcon />} onClick={onEdit}>
              Configure
            </Button>
          </Box>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="body1" gutterBottom>
            <strong>Strategy:</strong> {routingRules.strategy}
          </Typography>
          <Typography variant="h6" sx={{ mt: 3, mb: 2 }}>
            User Power Levels
          </Typography>
          <Grid container spacing={2}>
            {POWER_LEVELS.map((pl) => (
              <Grid item xs={12} md={4} key={pl.value}>
                <Card variant="outlined">
                  <CardContent>
                    <Chip label={pl.label} color={pl.color} sx={{ mb: 1 }} />
                    <Typography variant="body2" color="textSecondary">
                      {pl.description}
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>
    </Box>
  );
}

/**
 * Usage Tab
 */
function UsageTab({ usageStats }) {
  if (!usageStats) return null;

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Requests
              </Typography>
              <Typography variant="h4">{usageStats.total_requests.toLocaleString()}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Tokens
              </Typography>
              <Typography variant="h4">{usageStats.total_tokens.toLocaleString()}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Cost
              </Typography>
              <Typography variant="h4">${usageStats.total_cost.toFixed(2)}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Cost/Request
              </Typography>
              <Typography variant="h4">${usageStats.avg_cost_per_request.toFixed(4)}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Provider Usage (Last 7 Days)
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Provider</TableCell>
                  <TableCell>Requests</TableCell>
                  <TableCell>Tokens</TableCell>
                  <TableCell>Cost</TableCell>
                  <TableCell>Avg Latency</TableCell>
                  <TableCell>Unique Users</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {usageStats.providers.map((provider, index) => (
                  <TableRow key={index}>
                    <TableCell>{provider.provider_name}</TableCell>
                    <TableCell>{provider.requests.toLocaleString()}</TableCell>
                    <TableCell>{provider.tokens.toLocaleString()}</TableCell>
                    <TableCell>${provider.cost.toFixed(2)}</TableCell>
                    <TableCell>{provider.avg_latency_ms}ms</TableCell>
                    <TableCell>{provider.unique_users}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
}

/**
 * BYOK Tab
 */
function BYOKTab({ onAddBYOK }) {
  return (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Bring Your Own Key (BYOK)
          </Typography>
          <Typography variant="body2" color="textSecondary" paragraph>
            Configure your own API keys to use your provider accounts directly. Benefits:
          </Typography>
          <ul>
            <li><strong>Use your own API credits</strong> - Pay providers directly</li>
            <li><strong>Access exclusive models</strong> - Use models from your subscriptions</li>
            <li><strong>Custom rate limits</strong> - Based on your provider tier</li>
            <li><strong>Direct billing</strong> - Transparent costs from providers</li>
          </ul>
          <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
            <Typography variant="body2">
              <strong>How to get API keys:</strong><br/>
              • OpenAI: <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener">platform.openai.com/api-keys</a><br/>
              • Anthropic: <a href="https://console.anthropic.com" target="_blank" rel="noopener">console.anthropic.com</a><br/>
              • Google AI: <a href="https://ai.google.dev" target="_blank" rel="noopener">ai.google.dev</a>
            </Typography>
          </Alert>
          <Button variant="contained" startIcon={<KeyIcon />} onClick={onAddBYOK}>
            Configure BYOK
          </Button>
        </CardContent>
      </Card>
    </Box>
  );
}
