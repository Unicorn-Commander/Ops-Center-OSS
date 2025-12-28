/**
 * Model Management Page
 * Admin interface for managing LLM model access control per subscription tier
 * Epic 3.3: Model Access Control System
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
  Card,
  CardContent,
  Alert,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  ToggleButtonGroup,
  ToggleButton,
  Checkbox,
  FormGroup,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayArrowIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
  Category as CategoryIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as MoneyIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import TierAccessDialog from '../../components/admin/TierAccessDialog';

const ModelManagement = () => {
  // State management
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);

  // Dialog states
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [tierAccessDialogOpen, setTierAccessDialogOpen] = useState(false);

  // Selected model for editing/deleting
  const [selectedModel, setSelectedModel] = useState(null);

  // Filter states
  const [providerFilter, setProviderFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Available tiers (will be fetched from API)
  const [availableTiers] = useState([
    { code: 'trial', name: 'Trial' },
    { code: 'starter', name: 'Starter' },
    { code: 'professional', name: 'Professional' },
    { code: 'enterprise', name: 'Enterprise' }
  ]);

  // Form data
  const [formData, setFormData] = useState({
    model_id: '',
    display_name: '',
    provider: 'openrouter',
    description: '',
    tier_access: [],
    pricing_input: 0,
    pricing_output: 0,
    context_length: 4096,
    enabled: true
  });

  // ============================================
  // API Functions
  // ============================================

  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/models/admin/models', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }

      const data = await response.json();
      setModels(data.models || []);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching models:', err);

      // Mock data for development
      setModels([
        {
          id: 1,
          model_id: 'openai/gpt-4-turbo',
          display_name: 'GPT-4 Turbo',
          provider: 'openai',
          tier_access: ['professional', 'enterprise'],
          pricing_input: 0.01,
          pricing_output: 0.03,
          context_length: 128000,
          enabled: true,
          description: 'Most capable OpenAI model'
        },
        {
          id: 2,
          model_id: 'anthropic/claude-3-opus',
          display_name: 'Claude 3 Opus',
          provider: 'anthropic',
          tier_access: ['enterprise'],
          pricing_input: 0.015,
          pricing_output: 0.075,
          context_length: 200000,
          enabled: true,
          description: 'Most powerful Claude model'
        },
        {
          id: 3,
          model_id: 'openrouter/meta-llama/llama-3.1-8b',
          display_name: 'Llama 3.1 8B',
          provider: 'openrouter',
          tier_access: ['trial', 'starter', 'professional', 'enterprise'],
          pricing_input: 0.0001,
          pricing_output: 0.0002,
          context_length: 8192,
          enabled: true,
          description: 'Open source model via OpenRouter'
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const createModel = async () => {
    try {
      const response = await fetch('/api/v1/models/admin/models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create model');
      }

      setSuccess('Model created successfully');
      setCreateDialogOpen(false);
      fetchModels();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error creating model:', err);
    }
  };

  const updateModel = async () => {
    if (!selectedModel) return;

    try {
      const response = await fetch(`/api/v1/models/admin/models/${selectedModel.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update model');
      }

      setSuccess('Model updated successfully');
      setEditDialogOpen(false);
      fetchModels();
      resetForm();
    } catch (err) {
      setError(err.message);
      console.error('Error updating model:', err);
    }
  };

  const deleteModel = async () => {
    if (!selectedModel) return;

    try {
      const response = await fetch(`/api/v1/models/admin/models/${selectedModel.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete model');
      }

      setSuccess('Model deleted successfully');
      setDeleteDialogOpen(false);
      fetchModels();
      setSelectedModel(null);
    } catch (err) {
      setError(err.message);
      console.error('Error deleting model:', err);
    }
  };

  const toggleModelStatus = async (model) => {
    try {
      const response = await fetch(`/api/v1/models/admin/models/${model.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify({ ...model, enabled: !model.enabled })
      });

      if (!response.ok) {
        throw new Error('Failed to update model status');
      }

      setSuccess(`Model ${model.enabled ? 'disabled' : 'enabled'} successfully`);
      fetchModels();
    } catch (err) {
      setError(err.message);
      console.error('Error toggling model status:', err);
    }
  };

  const testModel = (model) => {
    setSelectedModel(model);
    setTestDialogOpen(true);
  };

  // ============================================
  // Form Handlers
  // ============================================

  const resetForm = () => {
    setFormData({
      model_id: '',
      display_name: '',
      provider: 'openrouter',
      description: '',
      tier_access: [],
      pricing_input: 0,
      pricing_output: 0,
      context_length: 4096,
      enabled: true
    });
  };

  const handleEditModel = (model) => {
    setSelectedModel(model);
    setFormData({
      model_id: model.model_id,
      display_name: model.display_name,
      provider: model.provider,
      description: model.description || '',
      tier_access: model.tier_access || [],
      pricing_input: model.pricing_input || 0,
      pricing_output: model.pricing_output || 0,
      context_length: model.context_length || 4096,
      enabled: model.enabled
    });
    setEditDialogOpen(true);
  };

  const handleDeleteModel = (model) => {
    setSelectedModel(model);
    setDeleteDialogOpen(true);
  };

  const handleEditTierAccess = (model) => {
    setSelectedModel(model);
    setTierAccessDialogOpen(true);
  };

  const handleTierAccessSave = async () => {
    // Close dialog first for better UX
    setTierAccessDialogOpen(false);

    // Show success message
    setSuccess('Tier access updated successfully');

    // Refresh model list to show updated tier badges
    await fetchModels();
  };

  const handleTierToggle = (tierCode) => {
    setFormData(prev => ({
      ...prev,
      tier_access: prev.tier_access.includes(tierCode)
        ? prev.tier_access.filter(t => t !== tierCode)
        : [...prev.tier_access, tierCode]
    }));
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    fetchModels();
  }, []);

  // ============================================
  // Render Helpers
  // ============================================

  const getProviderColor = (provider) => {
    switch (provider.toLowerCase()) {
      case 'openai':
        return { bg: 'rgba(16, 163, 127, 0.1)', color: '#10a37f', border: '#10a37f' };
      case 'anthropic':
        return { bg: 'rgba(219, 144, 71, 0.1)', color: '#db9047', border: '#db9047' };
      case 'openrouter':
        return { bg: 'rgba(124, 58, 237, 0.1)', color: '#7c3aed', border: '#7c3aed' };
      default:
        return { bg: 'rgba(100, 116, 139, 0.1)', color: '#64748b', border: '#64748b' };
    }
  };

  const getTierBadgeColor = (tierCode) => {
    switch (tierCode) {
      case 'trial':
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: '#94a3b8' };
      case 'starter':
        return { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6', border: '#3b82f6' };
      case 'professional':
        return { bg: 'rgba(124, 58, 237, 0.15)', color: '#7c3aed', border: '#7c3aed' };
      case 'enterprise':
        return { bg: 'rgba(255, 215, 0, 0.15)', color: '#FFD700', border: '#FFD700' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8', border: '#94a3b8' };
    }
  };

  const getStatsData = () => {
    const enabledModels = models.filter(m => m.enabled).length;
    const providers = [...new Set(models.map(m => m.provider))].length;
    const avgCost = models.length > 0
      ? (models.reduce((sum, m) => sum + (m.pricing_output || 0), 0) / models.length).toFixed(4)
      : '0.0000';

    return { enabledModels, providers, avgCost };
  };

  const filteredModels = models
    .filter(m => providerFilter === 'all' || m.provider === providerFilter)
    .filter(m => statusFilter === 'all' || (statusFilter === 'enabled' ? m.enabled : !m.enabled))
    .filter(m =>
      searchQuery === '' ||
      m.model_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.display_name.toLowerCase().includes(searchQuery.toLowerCase())
    );

  // ============================================
  // Main Render
  // ============================================

  if (loading && models.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const { enabledModels, providers, avgCost } = getStatsData();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          borderRadius: 2,
          p: 3,
          mb: 3,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 0.5 }}>
            Model Access Control
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage which models are available to each subscription tier
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {
            resetForm();
            setCreateDialogOpen(true);
          }}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: 2,
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-2px)',
              boxShadow: 4,
              background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
            }
          }}
        >
          Add Model
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

      {/* Analytics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
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
                    Total Models
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {models.length}
                  </Typography>
                </Box>
                <CategoryIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(240, 147, 251, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Enabled Models
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {enabledModels}
                  </Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(79, 172, 254, 0.3)'
              }
            }}
          >
            <CardContent>
              <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                Providers
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                {providers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(67, 233, 123, 0.3)'
              }
            }}
          >
            <CardContent>
              <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                Avg Output Cost
              </Typography>
              <Typography variant="h3" sx={{ fontWeight: 700 }}>
                ${avgCost}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2, borderRadius: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search models..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Provider</InputLabel>
              <Select
                value={providerFilter}
                onChange={(e) => setProviderFilter(e.target.value)}
                label="Provider"
              >
                <MenuItem value="all">All Providers</MenuItem>
                <MenuItem value="openai">OpenAI</MenuItem>
                <MenuItem value="anthropic">Anthropic</MenuItem>
                <MenuItem value="openrouter">OpenRouter</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <ToggleButtonGroup
              value={statusFilter}
              exclusive
              onChange={(e, newValue) => {
                if (newValue !== null) setStatusFilter(newValue);
              }}
              size="small"
              fullWidth
            >
              <ToggleButton value="all">All</ToggleButton>
              <ToggleButton value="enabled">Enabled</ToggleButton>
              <ToggleButton value="disabled">Disabled</ToggleButton>
            </ToggleButtonGroup>
          </Grid>
          <Grid item xs={12} md={2}>
            <Typography variant="body2" color="text.secondary" textAlign="right">
              {filteredModels.length} of {models.length} models
            </Typography>
          </Grid>
        </Grid>
      </Paper>

      {/* Models Table */}
      <Paper
        sx={{
          borderRadius: 2,
          overflow: 'hidden',
          boxShadow: 2
        }}
      >
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                <TableCell sx={{ fontWeight: 700 }}>Model ID</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Display Name</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Provider</TableCell>
                <TableCell sx={{ fontWeight: 700, minWidth: 280 }}>Available To (Tiers)</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Pricing (per 1K)</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Status</TableCell>
                <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredModels
                .slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
                .map((model) => {
                  const providerStyle = getProviderColor(model.provider);
                  return (
                    <TableRow
                      key={model.id}
                      hover
                      sx={{
                        transition: 'all 0.2s',
                        '&:hover': {
                          backgroundColor: 'rgba(102, 126, 234, 0.04)',
                          transform: 'scale(1.001)'
                        }
                      }}
                    >
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {model.model_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body1" fontWeight="bold">
                          {model.display_name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={model.provider}
                          size="small"
                          sx={{
                            backgroundColor: providerStyle.bg,
                            color: providerStyle.color,
                            border: `1px solid ${providerStyle.border}`,
                            textTransform: 'capitalize',
                            fontWeight: 600
                          }}
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {(model.tiers || model.tier_access || []).slice(0, 3).map((tier) => {
                            const tierCode = typeof tier === 'string' ? tier : (tier?.tier_code || 'unknown');
                            const tierStyle = getTierBadgeColor(tierCode);
                            const tierName = availableTiers.find(t => t.code === tierCode)?.name || tierCode;
                            return (
                              <Chip
                                key={tierCode}
                                label={tierName}
                                size="small"
                                sx={{
                                  backgroundColor: tierStyle.bg,
                                  color: tierStyle.color,
                                  border: `1px solid ${tierStyle.border}`,
                                  fontWeight: 600,
                                  fontSize: '0.7rem'
                                }}
                              />
                            );
                          })}
                        {(model.tiers || model.tier_access || []).length > 3 && (
                          <Chip
                            label={`+${(model.tiers || model.tier_access || []).length - 3}`}
                            size="small"
                            sx={{ fontSize: '0.7rem' }}
                          />
                        )}
                        <IconButton
                          size="small"
                          onClick={() => handleEditTierAccess(model)}
                          sx={{ ml: 0.5 }}
                          title="Manage Tier Access"
                        >
                          <SecurityIcon fontSize="small" />
                        </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                            In: ${model.pricing_input?.toFixed(4) || '0.0000'}
                          </Typography>
                          <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                            Out: ${model.pricing_output?.toFixed(4) || '0.0000'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Switch
                          checked={model.enabled}
                          onChange={() => toggleModelStatus(model)}
                          color="primary"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => handleEditModel(model)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Test Model">
                          <IconButton
                            size="small"
                            onClick={() => testModel(model)}
                            color="primary"
                          >
                            <PlayArrowIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={() => handleDeleteModel(model)}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  );
                })}
            </TableBody>
          </Table>
        </TableContainer>
        <TablePagination
          rowsPerPageOptions={[25, 50, 100]}
          component="div"
          count={filteredModels.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
        />
      </Paper>

      {/* Create/Edit Model Dialog */}
      <Dialog
        open={createDialogOpen || editDialogOpen}
        onClose={() => {
          setCreateDialogOpen(false);
          setEditDialogOpen(false);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {createDialogOpen ? 'Add New Model' : 'Edit Model'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Model ID"
                value={formData.model_id}
                onChange={(e) => setFormData({ ...formData, model_id: e.target.value })}
                placeholder="e.g., openai/gpt-4-turbo"
                required
                disabled={editDialogOpen}
                helperText={editDialogOpen ? "Cannot change model ID" : "Unique identifier for the model"}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Display Name"
                value={formData.display_name}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                placeholder="e.g., GPT-4 Turbo"
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth required>
                <InputLabel>Provider</InputLabel>
                <Select
                  value={formData.provider}
                  onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                  label="Provider"
                >
                  <MenuItem value="openai">OpenAI</MenuItem>
                  <MenuItem value="anthropic">Anthropic</MenuItem>
                  <MenuItem value="openrouter">OpenRouter</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Context Length"
                type="number"
                value={formData.context_length}
                onChange={(e) => setFormData({ ...formData, context_length: parseInt(e.target.value) || 4096 })}
                helperText="Maximum tokens in context"
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
                placeholder="Brief description of the model's capabilities"
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                Tier Access
              </Typography>
              <FormGroup>
                {availableTiers.map((tier) => (
                  <FormControlLabel
                    key={tier.code}
                    control={
                      <Checkbox
                        checked={formData.tier_access.includes(tier.code)}
                        onChange={() => handleTierToggle(tier.code)}
                      />
                    }
                    label={tier.name}
                  />
                ))}
              </FormGroup>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1, mt: 2, fontWeight: 600 }}>
                Pricing (per 1K tokens)
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Input Price"
                type="number"
                value={formData.pricing_input}
                onChange={(e) => setFormData({ ...formData, pricing_input: parseFloat(e.target.value) || 0 })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>
                }}
                inputProps={{ step: '0.0001', min: '0' }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Output Price"
                type="number"
                value={formData.pricing_output}
                onChange={(e) => setFormData({ ...formData, pricing_output: parseFloat(e.target.value) || 0 })}
                InputProps={{
                  startAdornment: <InputAdornment position="start">$</InputAdornment>
                }}
                inputProps={{ step: '0.0001', min: '0' }}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={formData.enabled}
                    onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                  />
                }
                label="Enabled"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => {
              setCreateDialogOpen(false);
              setEditDialogOpen(false);
            }}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={createDialogOpen ? createModel : updateModel}
            variant="contained"
            disabled={!formData.model_id || !formData.display_name}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              },
              '&:disabled': {
                background: '#ccc'
              }
            }}
          >
            {createDialogOpen ? 'Add Model' : 'Save Changes'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Delete Model</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete <strong>{selectedModel?.display_name}</strong>?
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This will remove access for all subscription tiers. This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button
            onClick={() => setDeleteDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Cancel
          </Button>
          <Button
            onClick={deleteModel}
            variant="contained"
            color="error"
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow: 4
              }
            }}
          >
            Delete Model
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Model Dialog */}
      <Dialog
        open={testDialogOpen}
        onClose={() => setTestDialogOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Test Model: {selectedModel?.display_name}</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Model testing interface coming soon. This will allow you to send test prompts to verify model functionality.
          </Typography>
          <Alert severity="info">
            Model ID: {selectedModel?.model_id}
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button
            onClick={() => setTestDialogOpen(false)}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-1px)'
              }
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Tier Access Dialog */}
      {selectedModel && (
        <TierAccessDialog
          model={selectedModel}
          open={tierAccessDialogOpen}
          onClose={() => setTierAccessDialogOpen(false)}
          onSave={handleTierAccessSave}
        />
      )}
    </Box>
  );
};

export default ModelManagement;
