import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tooltip,
  Checkbox,
  FormControlLabel,
  Badge,
  Collapse,
  InputAdornment,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  Refresh as RefreshIcon,
  FilterList as FilterListIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Info as InfoIcon,
  Edit as EditIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Star as StarIcon,
} from '@mui/icons-material';

/**
 * Model Catalog Tab
 *
 * Displays comprehensive model catalog with filtering, search, sorting, and bulk operations.
 * Shows all models from LLM providers (OpenRouter, OpenAI, Anthropic, etc.)
 */
export default function ModelCatalog() {
  // State for models data
  const [models, setModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Selection state
  const [selectedModels, setSelectedModels] = useState([]);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedProviders, setSelectedProviders] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all'); // all, enabled, disabled
  const [sortBy, setSortBy] = useState('name'); // name, provider, price, context_length, rating
  const [sortDirection, setSortDirection] = useState('asc'); // 'asc' or 'desc'
  const [showFilters, setShowFilters] = useState(false);

  // Advanced filter state
  const [capabilityFilters, setCapabilityFilters] = useState({
    streaming: false,
    vision: false,
    function_calling: false
  });
  const [priceRangeFilters, setPriceRangeFilters] = useState({
    free: false,      // < $0.01 per 1M tokens
    budget: false,    // $0.01 - $1 per 1M tokens
    premium: false,   // $1 - $10 per 1M tokens
    ultra: false      // > $10 per 1M tokens
  });
  const [contextLengthFilters, setContextLengthFilters] = useState({
    short: false,      // < 8K tokens
    medium: false,     // 8K - 32K tokens
    long: false,       // 32K - 128K tokens
    ultraLong: false   // > 128K tokens
  });
  const [ratingFilters, setRatingFilters] = useState({
    fiveStar: false,   // rating >= 4.5
    fourPlus: false,   // rating >= 4.0
    threePlus: false,  // rating >= 3.0
    twoPlus: false,    // rating >= 2.0
    onePlus: false,    // rating >= 1.0
    unrated: false     // rating === null/undefined
  });

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Modal state
  const [selectedModel, setSelectedModel] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [copiedText, setCopiedText] = useState('');

  // Bulk actions state
  const [bulkActionLoading, setBulkActionLoading] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({ enabled: true });

  // Fetch models from API
  const fetchModels = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch categorized model list (BYOK vs Platform)
      const response = await fetch('/api/v1/llm/models/categorized', {
        credentials: 'include'
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to fetch models: ${response.statusText}`);
      }

      const data = await response.json();

      // Extract all models from categorized response
      let modelsArray = [];
      if (data && data.byok_models) {
        // Flatten BYOK models from all providers
        data.byok_models.forEach(provider => {
          if (Array.isArray(provider.models)) {
            modelsArray = modelsArray.concat(provider.models.map(m => ({
              ...m,
              source: 'byok',
              provider_name: provider.provider,
              cost_note: 'Free (using your API key)'
            })));
          }
        });
      }
      if (data && data.platform_models) {
        // Flatten Platform models from all providers
        data.platform_models.forEach(provider => {
          if (Array.isArray(provider.models)) {
            modelsArray = modelsArray.concat(provider.models.map(m => ({
              ...m,
              source: 'platform',
              provider_name: provider.provider,
              cost_note: 'Charged with credits'
            })));
          }
        });
      }

      setModels(modelsArray);
      applyClientFilters(modelsArray);
    } catch (err) {
      console.error('Failed to load models:', err);
      setError(err.message);
      setModels([]); // Ensure models is always an array even on error
    } finally {
      setLoading(false);
    }
  };

  // Apply client-side filters (search, provider, status)
  const applyClientFilters = (allModels) => {
    // Ensure allModels is always an array
    if (!Array.isArray(allModels)) {
      console.warn('applyClientFilters received non-array:', allModels);
      setFilteredModels([]);
      return;
    }

    let filtered = allModels;

    // Search filter (model name or ID)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m =>
        (m.name && m.name.toLowerCase().includes(query)) ||
        (m.id && m.id.toLowerCase().includes(query)) ||
        (m.model_id && m.model_id.toLowerCase().includes(query))
      );
    }

    // Provider filter
    if (selectedProviders.length > 0) {
      filtered = filtered.filter(m => selectedProviders.includes(m.provider_name));
    }

    // Status filter
    if (statusFilter === 'enabled') {
      filtered = filtered.filter(m => m.enabled === true);
    } else if (statusFilter === 'disabled') {
      filtered = filtered.filter(m => m.enabled === false);
    }

    // Capability filters
    const activeCapabilities = Object.keys(capabilityFilters).filter(key => capabilityFilters[key]);
    if (activeCapabilities.length > 0) {
      filtered = filtered.filter(m => {
        return activeCapabilities.every(cap => {
          if (cap === 'streaming') return m.supports_streaming === true;
          if (cap === 'vision') return m.supports_vision === true;
          if (cap === 'function_calling') return m.supports_function_calling === true;
          return true;
        });
      });
    }

    // Price range filters
    const activePriceRanges = Object.keys(priceRangeFilters).filter(key => priceRangeFilters[key]);
    if (activePriceRanges.length > 0) {
      filtered = filtered.filter(m => {
        const price = m.cost_per_1m_input ?? 0;
        return activePriceRanges.some(range => {
          if (range === 'free') return price < 0.01;
          if (range === 'budget') return price >= 0.01 && price < 1;
          if (range === 'premium') return price >= 1 && price < 10;
          if (range === 'ultra') return price >= 10;
          return false;
        });
      });
    }

    // Context length filters
    const activeContextLengths = Object.keys(contextLengthFilters).filter(key => contextLengthFilters[key]);
    if (activeContextLengths.length > 0) {
      filtered = filtered.filter(m => {
        const contextLen = m.context_length ?? 0;
        return activeContextLengths.some(range => {
          if (range === 'short') return contextLen < 8000;
          if (range === 'medium') return contextLen >= 8000 && contextLen < 32000;
          if (range === 'long') return contextLen >= 32000 && contextLen < 128000;
          if (range === 'ultraLong') return contextLen >= 128000;
          return false;
        });
      });
    }

    // Rating filters
    const activeRatings = Object.keys(ratingFilters).filter(key => ratingFilters[key]);
    if (activeRatings.length > 0) {
      filtered = filtered.filter(m => {
        const rating = m.rating;
        return activeRatings.some(filter => {
          if (filter === 'unrated') return rating === null || rating === undefined;
          if (filter === 'fiveStar') return rating >= 4.5;
          if (filter === 'fourPlus') return rating >= 4.0;
          if (filter === 'threePlus') return rating >= 3.0;
          if (filter === 'twoPlus') return rating >= 2.0;
          if (filter === 'onePlus') return rating >= 1.0;
          return false;
        });
      });
    }

    // Sorting (with null-safe comparisons and direction)
    const sortMultiplier = sortDirection === 'asc' ? 1 : -1;

    if (sortBy === 'name') {
      filtered.sort((a, b) =>
        (a.display_name || a.name || a.id || '').localeCompare(b.display_name || b.name || b.id || '') * sortMultiplier
      );
    } else if (sortBy === 'provider') {
      filtered.sort((a, b) =>
        (a.provider_name || '').localeCompare(b.provider_name || '') * sortMultiplier
      );
    } else if (sortBy === 'price') {
      filtered.sort((a, b) => {
        const priceA = a.cost_per_1m_input ?? 0;
        const priceB = b.cost_per_1m_input ?? 0;
        return (priceA - priceB) * sortMultiplier;
      });
    } else if (sortBy === 'context_length') {
      filtered.sort((a, b) => {
        const lenA = a.context_length ?? 0;
        const lenB = b.context_length ?? 0;
        return (lenB - lenA) * sortMultiplier; // Default desc for context
      });
    } else if (sortBy === 'rating') {
      filtered.sort((a, b) => {
        const ratingA = a.rating ?? 0;
        const ratingB = b.rating ?? 0;
        return (ratingB - ratingA) * sortMultiplier; // Default desc for ratings
      });
    }

    setFilteredModels(filtered);
  };

  // Selection helper functions
  const handleSelectAll = (event) => {
    if (event.target.checked) {
      const allIds = filteredModels?.map(m => m?.id).filter(Boolean) ?? [];
      setSelectedModels(allIds);
    } else {
      setSelectedModels([]);
    }
  };

  const handleSelectModel = (modelId) => {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  const isAllSelected = filteredModels && Array.isArray(filteredModels) && filteredModels.length > 0 &&
    filteredModels.every(m => m?.id && selectedModels.includes(m.id));

  const isSomeSelected = selectedModels.length > 0 && !isAllSelected;

  // Bulk action handler
  const handleBulkAction = async (action) => {
    // Null-safety check
    if (!Array.isArray(selectedModels) || selectedModels.length === 0) {
      console.warn('No models selected for bulk action');
      return;
    }

    setBulkActionLoading(true);
    try {
      const response = await fetch('/api/v1/llm/admin/models/bulk-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model_ids: selectedModels,
          action: action
        })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.detail || 'Bulk action failed');
      }

      // Refresh models after successful update
      await fetchModels();
      setSelectedModels([]);

      // Show success message
      alert(`Successfully ${action}d ${selectedModels.length} models`);
    } catch (err) {
      console.error('Bulk action failed:', err);
      alert(`Failed to ${action} models: ${err.message}`);
    } finally {
      setBulkActionLoading(false);
    }
  };

  // Edit modal handler
  const handleSaveEdit = async () => {
    setBulkActionLoading(true);
    try {
      const response = await fetch('/api/v1/llm/admin/models/bulk-update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          model_ids: selectedModels,
          action: 'update',
          updates: editFormData
        })
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error?.detail || 'Update failed');
      }

      await fetchModels();
      setSelectedModels([]);
      setEditModalOpen(false);
      setEditFormData({ enabled: true });

      alert('Models updated successfully');
    } catch (err) {
      console.error('Edit failed:', err);
      alert(`Failed to update models: ${err?.message || 'Unknown error'}`);
    } finally {
      setBulkActionLoading(false);
    }
  };

  // Initial load (fetch once, filter client-side)
  useEffect(() => {
    fetchModels();
  }, []); // Only fetch on mount, not on filter changes

  // Apply client filters when any filter changes
  useEffect(() => {
    applyClientFilters(models);
  }, [selectedProviders, models, searchQuery, statusFilter, sortBy, sortDirection]);

  // Get unique providers (with defensive check)
  const uniqueProviders = Array.isArray(models) && models.length > 0
    ? [...new Set(models.map(m => m.provider_name))].sort()
    : [];

  // Calculate statistics
  const stats = {
    total: filteredModels?.length ?? 0,
    enabled: filteredModels?.filter(m => m?.enabled).length ?? 0,
    providers: uniqueProviders.length,
    free: filteredModels?.filter(m => (m?.cost_per_1m_input ?? 0) === 0 && (m?.cost_per_1m_output ?? 0) === 0).length ?? 0,
  };

  // Handle search with debouncing
  const handleSearchChange = (event) => {
    const value = event.target.value;
    setSearchQuery(value);
    setPage(0);
  };

  // Handle provider toggle
  const handleProviderToggle = (provider) => {
    setSelectedProviders(prev => {
      if (prev.includes(provider)) {
        return prev.filter(p => p !== provider);
      } else {
        return [...prev, provider];
      }
    });
    setPage(0);
  };

  // Handle capability filter toggle
  const handleCapabilityToggle = (capability) => {
    setCapabilityFilters(prev => ({
      ...prev,
      [capability]: !prev[capability]
    }));
    setPage(0);
  };

  // Handle price range filter toggle
  const handlePriceRangeToggle = (range) => {
    setPriceRangeFilters(prev => ({
      ...prev,
      [range]: !prev[range]
    }));
    setPage(0);
  };

  // Handle context length filter toggle
  const handleContextLengthToggle = (length) => {
    setContextLengthFilters(prev => ({
      ...prev,
      [length]: !prev[length]
    }));
    setPage(0);
  };

  // Handle rating filter toggle
  const handleRatingToggle = (rating) => {
    setRatingFilters(prev => ({
      ...prev,
      [rating]: !prev[rating]
    }));
    setPage(0);
  };

  // Handle column header click for sorting
  const handleSort = (column) => {
    if (sortBy === column) {
      // Toggle direction if same column
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      // New column, default to ascending
      setSortBy(column);
      setSortDirection('asc');
    }
    setPage(0);
  };

  // Get sort icon for column header
  const getSortIcon = (column) => {
    if (sortBy !== column) return null;
    return sortDirection === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />;
  };

  // Clear all filters
  const handleClearFilters = () => {
    setSearchQuery('');
    setSelectedProviders([]);
    setStatusFilter('all');
    setCapabilityFilters({ streaming: false, vision: false, function_calling: false });
    setPriceRangeFilters({ free: false, budget: false, premium: false, ultra: false });
    setContextLengthFilters({ short: false, medium: false, long: false, ultraLong: false });
    setRatingFilters({ fiveStar: false, fourPlus: false, threePlus: false, twoPlus: false, onePlus: false, unrated: false });
    setSortBy('name');
    setSortDirection('asc');
    setPage(0);
  };

  // Format cost
  const formatCost = (inputCost, outputCost) => {
    // Handle null/undefined values
    const input = inputCost ?? 0;
    const output = outputCost ?? 0;

    if (input === 0 && output === 0) {
      return 'Free';
    }

    if (input === null || output === null || input === undefined || output === undefined) {
      return 'Pricing not available';
    }

    return `$${input.toFixed(2)} / $${output.toFixed(2)} per 1M`;
  };

  // Format context length
  const formatContextLength = (length) => {
    // Handle null/undefined values
    if (!length || length === null || length === undefined) {
      return 'Unknown';
    }

    if (length >= 1000000) {
      return `${(length / 1000000).toFixed(1)}M tokens`;
    }
    if (length >= 1000) {
      return `${(length / 1000).toFixed(0)}K tokens`;
    }
    return `${length} tokens`;
  };

  // Get provider badge color
  const getProviderColor = (provider) => {
    const colors = {
      'OpenRouter': 'primary',
      'OpenAI': 'success',
      'Anthropic': 'warning',
      'Google': 'error',
      'Cohere': 'info',
      'Meta': 'secondary',
    };
    return colors[provider] || 'default';
  };

  // Handle row click
  const handleRowClick = (model) => {
    setSelectedModel(model);
    setModalOpen(true);
  };

  // Copy to clipboard
  const handleCopy = (text, label) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(''), 2000);
  };

  // Pagination handlers
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // Get paginated models
  const paginatedModels = filteredModels?.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  ) ?? [];

  // Count active filters
  const activeFilterCount = [
    searchQuery !== '',
    selectedProviders.length > 0,
    statusFilter !== 'all',
    Object.values(capabilityFilters).some(v => v),
    Object.values(priceRangeFilters).some(v => v),
    Object.values(contextLengthFilters).some(v => v),
    Object.values(ratingFilters).some(v => v),
  ].filter(Boolean).length;

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load models: {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'primary.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.total}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Models
                  </Typography>
                </Box>
                <InfoIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'success.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.enabled}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Enabled Models
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'info.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.providers}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Providers
                  </Typography>
                </Box>
                <FilterListIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ bgcolor: 'warning.main', color: 'white' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {stats.free}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Free Models
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" fontWeight="bold">
            Model Catalog
          </Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchModels}
          >
            Refresh
          </Button>
        </Box>

        {/* Search and Filter Controls */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search by model name..."
              value={searchQuery}
              onChange={handleSearchChange}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: 'text.secondary' }} />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>

          <Grid item xs={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="enabled">Enabled</MenuItem>
                <MenuItem value="disabled">Disabled</MenuItem>
              </Select>
            </FormControl>
          </Grid>

          <Grid item xs={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={
                <Badge badgeContent={activeFilterCount} color="error">
                  <FilterListIcon />
                </Badge>
              }
              endIcon={showFilters ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              onClick={() => setShowFilters(!showFilters)}
              sx={{ height: '56px' }}
            >
              Filters
            </Button>
          </Grid>
        </Grid>

        {/* Advanced Filters Panel */}
        <Collapse in={showFilters}>
          <Paper sx={{ p: 3, mb: 3, bgcolor: 'background.default' }}>
            <Typography variant="h6" gutterBottom>
              Filter by Provider
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              {uniqueProviders.map((provider) => (
                <FormControlLabel
                  key={provider}
                  control={
                    <Checkbox
                      checked={selectedProviders.includes(provider)}
                      onChange={() => handleProviderToggle(provider)}
                    />
                  }
                  label={provider}
                />
              ))}
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Capability Filters */}
            <Typography variant="h6" gutterBottom>
              Filter by Capabilities
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={capabilityFilters.streaming}
                    onChange={() => handleCapabilityToggle('streaming')}
                  />
                }
                label="Streaming"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={capabilityFilters.vision}
                    onChange={() => handleCapabilityToggle('vision')}
                  />
                }
                label="Vision"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={capabilityFilters.function_calling}
                    onChange={() => handleCapabilityToggle('function_calling')}
                  />
                }
                label="Function Calling"
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Price Range Filters */}
            <Typography variant="h6" gutterBottom>
              Filter by Price Range (per 1M tokens)
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={priceRangeFilters.free}
                    onChange={() => handlePriceRangeToggle('free')}
                  />
                }
                label="Free (< $0.01)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={priceRangeFilters.budget}
                    onChange={() => handlePriceRangeToggle('budget')}
                  />
                }
                label="Budget ($0.01 - $1)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={priceRangeFilters.premium}
                    onChange={() => handlePriceRangeToggle('premium')}
                  />
                }
                label="Premium ($1 - $10)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={priceRangeFilters.ultra}
                    onChange={() => handlePriceRangeToggle('ultra')}
                  />
                }
                label="Ultra (> $10)"
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Context Length Filters */}
            <Typography variant="h6" gutterBottom>
              Filter by Context Length
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={contextLengthFilters.short}
                    onChange={() => handleContextLengthToggle('short')}
                  />
                }
                label="Short (< 8K)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={contextLengthFilters.medium}
                    onChange={() => handleContextLengthToggle('medium')}
                  />
                }
                label="Medium (8K - 32K)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={contextLengthFilters.long}
                    onChange={() => handleContextLengthToggle('long')}
                  />
                }
                label="Long (32K - 128K)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={contextLengthFilters.ultraLong}
                    onChange={() => handleContextLengthToggle('ultraLong')}
                  />
                }
                label="Ultra-Long (> 128K)"
              />
            </Box>

            <Divider sx={{ my: 3 }} />

            {/* Rating Filters */}
            <Typography variant="h6" gutterBottom>
              Filter by Rating
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={ratingFilters.fiveStar}
                    onChange={() => handleRatingToggle('fiveStar')}
                  />
                }
                label="5-Star (4.5+)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={ratingFilters.fourPlus}
                    onChange={() => handleRatingToggle('fourPlus')}
                  />
                }
                label="4+ Stars"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={ratingFilters.threePlus}
                    onChange={() => handleRatingToggle('threePlus')}
                  />
                }
                label="3+ Stars"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={ratingFilters.twoPlus}
                    onChange={() => handleRatingToggle('twoPlus')}
                  />
                }
                label="2+ Stars"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={ratingFilters.onePlus}
                    onChange={() => handleRatingToggle('onePlus')}
                  />
                }
                label="1+ Stars"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={ratingFilters.unrated}
                    onChange={() => handleRatingToggle('unrated')}
                  />
                }
                label="Unrated"
              />
            </Box>

            {activeFilterCount > 0 && (
              <>
                <Divider sx={{ my: 2 }} />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    {activeFilterCount} filter{activeFilterCount !== 1 ? 's' : ''} active
                  </Typography>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<CloseIcon />}
                    onClick={handleClearFilters}
                    size="small"
                  >
                    Clear All Filters
                  </Button>
                </Box>
              </>
            )}
          </Paper>
        </Collapse>

        {/* Active Filters Display */}
        {activeFilterCount > 0 && (
          <Box sx={{ mb: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {searchQuery && (
              <Chip
                label={`Search: "${searchQuery}"`}
                onDelete={() => setSearchQuery('')}
                color="primary"
                size="small"
              />
            )}
            {statusFilter !== 'all' && (
              <Chip
                label={`Status: ${statusFilter}`}
                onDelete={() => setStatusFilter('all')}
                color="secondary"
                size="small"
              />
            )}
            {selectedProviders.map((provider) => (
              <Chip
                key={provider}
                label={`Provider: ${provider}`}
                onDelete={() => handleProviderToggle(provider)}
                color="default"
                size="small"
              />
            ))}
            {capabilityFilters.streaming && (
              <Chip
                label="Capability: Streaming"
                onDelete={() => handleCapabilityToggle('streaming')}
                color="info"
                size="small"
              />
            )}
            {capabilityFilters.vision && (
              <Chip
                label="Capability: Vision"
                onDelete={() => handleCapabilityToggle('vision')}
                color="info"
                size="small"
              />
            )}
            {capabilityFilters.function_calling && (
              <Chip
                label="Capability: Function Calling"
                onDelete={() => handleCapabilityToggle('function_calling')}
                color="info"
                size="small"
              />
            )}
            {priceRangeFilters.free && (
              <Chip
                label="Price: Free"
                onDelete={() => handlePriceRangeToggle('free')}
                color="success"
                size="small"
              />
            )}
            {priceRangeFilters.budget && (
              <Chip
                label="Price: Budget"
                onDelete={() => handlePriceRangeToggle('budget')}
                color="success"
                size="small"
              />
            )}
            {priceRangeFilters.premium && (
              <Chip
                label="Price: Premium"
                onDelete={() => handlePriceRangeToggle('premium')}
                color="success"
                size="small"
              />
            )}
            {priceRangeFilters.ultra && (
              <Chip
                label="Price: Ultra"
                onDelete={() => handlePriceRangeToggle('ultra')}
                color="success"
                size="small"
              />
            )}
            {contextLengthFilters.short && (
              <Chip
                label="Context: Short"
                onDelete={() => handleContextLengthToggle('short')}
                color="warning"
                size="small"
              />
            )}
            {contextLengthFilters.medium && (
              <Chip
                label="Context: Medium"
                onDelete={() => handleContextLengthToggle('medium')}
                color="warning"
                size="small"
              />
            )}
            {contextLengthFilters.long && (
              <Chip
                label="Context: Long"
                onDelete={() => handleContextLengthToggle('long')}
                color="warning"
                size="small"
              />
            )}
            {contextLengthFilters.ultraLong && (
              <Chip
                label="Context: Ultra-Long"
                onDelete={() => handleContextLengthToggle('ultraLong')}
                color="warning"
                size="small"
              />
            )}
            {ratingFilters.fiveStar && (
              <Chip
                label="Rating: 5-Star"
                onDelete={() => handleRatingToggle('fiveStar')}
                color="error"
                size="small"
              />
            )}
            {ratingFilters.fourPlus && (
              <Chip
                label="Rating: 4+"
                onDelete={() => handleRatingToggle('fourPlus')}
                color="error"
                size="small"
              />
            )}
            {ratingFilters.threePlus && (
              <Chip
                label="Rating: 3+"
                onDelete={() => handleRatingToggle('threePlus')}
                color="error"
                size="small"
              />
            )}
            {ratingFilters.twoPlus && (
              <Chip
                label="Rating: 2+"
                onDelete={() => handleRatingToggle('twoPlus')}
                color="error"
                size="small"
              />
            )}
            {ratingFilters.onePlus && (
              <Chip
                label="Rating: 1+"
                onDelete={() => handleRatingToggle('onePlus')}
                color="error"
                size="small"
              />
            )}
            {ratingFilters.unrated && (
              <Chip
                label="Rating: Unrated"
                onDelete={() => handleRatingToggle('unrated')}
                color="error"
                size="small"
              />
            )}
          </Box>
        )}

        {/* Bulk Actions Toolbar - Show when models are selected */}
        {Array.isArray(selectedModels) && selectedModels.length > 0 && (
          <Paper
            sx={{
              p: 2,
              mb: 2,
              bgcolor: 'primary.50',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 2
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="body1" fontWeight="medium">
                {selectedModels.length} model{selectedModels.length !== 1 ? 's' : ''} selected
              </Typography>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setSelectedModels([])}
                disabled={bulkActionLoading}
              >
                Clear Selection
              </Button>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                color="success"
                size="small"
                startIcon={<CheckCircleIcon />}
                onClick={() => handleBulkAction('enable')}
                disabled={bulkActionLoading}
              >
                Enable Selected
              </Button>
              <Button
                variant="contained"
                color="warning"
                size="small"
                startIcon={<CancelIcon />}
                onClick={() => handleBulkAction('disable')}
                disabled={bulkActionLoading}
              >
                Disable Selected
              </Button>
              <Button
                variant="outlined"
                size="small"
                startIcon={<EditIcon />}
                onClick={() => setEditModalOpen(true)}
                disabled={bulkActionLoading}
              >
                Edit Selected
              </Button>
            </Box>
          </Paper>
        )}

        {/* Results Count */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Showing {paginatedModels.length} of {filteredModels?.length ?? 0} models
          {activeFilterCount > 0 && ` (${activeFilterCount} filter${activeFilterCount !== 1 ? 's' : ''} applied)`}
          {selectedModels.length > 0 && ` - ${selectedModels.length} selected`}
        </Typography>

        {/* Model Table */}
        {filteredModels?.length === 0 ? (
          <Box sx={{ py: 8, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No models found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Try adjusting your filters or search query
            </Typography>
            <Button
              variant="outlined"
              startIcon={<CloseIcon />}
              onClick={handleClearFilters}
            >
              Clear All Filters
            </Button>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={isSomeSelected}
                        checked={isAllSelected}
                        onChange={handleSelectAll}
                      />
                    </TableCell>
                    <TableCell
                      onClick={() => handleSort('name')}
                      sx={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Model Name
                        {getSortIcon('name')}
                      </Box>
                    </TableCell>
                    <TableCell
                      onClick={() => handleSort('provider')}
                      sx={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Provider
                        {getSortIcon('provider')}
                      </Box>
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('price')}
                      sx={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
                        Cost (per 1M)
                        {getSortIcon('price')}
                      </Box>
                    </TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('context_length')}
                      sx={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
                        Context Length
                        {getSortIcon('context_length')}
                      </Box>
                    </TableCell>
                    <TableCell align="center">Status</TableCell>
                    <TableCell
                      align="right"
                      onClick={() => handleSort('rating')}
                      sx={{ cursor: 'pointer', userSelect: 'none' }}
                    >
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
                        Rating
                        {getSortIcon('rating')}
                      </Box>
                    </TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedModels.map((model) => {
                    const modelId = model?.id;
                    const isSelected = modelId && selectedModels.includes(modelId);

                    return (
                      <TableRow
                        key={modelId}
                        hover
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                          <Checkbox
                            checked={isSelected}
                            onChange={() => modelId && handleSelectModel(modelId)}
                          />
                        </TableCell>
                        <TableCell onClick={() => handleRowClick(model)}>
                          <Typography variant="body2" fontWeight="medium">
                            {model?.display_name ?? 'Unknown'}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {model?.name ?? ''}
                          </Typography>
                        </TableCell>
                        <TableCell onClick={() => handleRowClick(model)}>
                          <Chip
                            label={model?.provider_name ?? 'Unknown'}
                            color={getProviderColor(model?.provider_name)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell align="right" onClick={() => handleRowClick(model)}>
                          <Typography variant="body2">
                            {formatCost(model?.cost_per_1m_input, model?.cost_per_1m_output)}
                          </Typography>
                        </TableCell>
                        <TableCell align="right" onClick={() => handleRowClick(model)}>
                          <Typography variant="body2">
                            {formatContextLength(model?.context_length)}
                          </Typography>
                        </TableCell>
                        <TableCell align="center" onClick={() => handleRowClick(model)}>
                          {model?.enabled ? (
                            <Chip
                              icon={<CheckCircleIcon />}
                              label="Enabled"
                              color="success"
                              size="small"
                            />
                          ) : (
                            <Chip
                              icon={<CancelIcon />}
                              label="Disabled"
                              color="error"
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell align="right" onClick={() => handleRowClick(model)}>
                          {model?.rating ? (
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, justifyContent: 'flex-end' }}>
                              <StarIcon sx={{ fontSize: 16, color: 'warning.main' }} />
                              <Typography variant="body2">
                                {model.rating.toFixed(1)}
                              </Typography>
                            </Box>
                          ) : (
                            <Typography variant="body2" color="text.secondary">
                              -
                            </Typography>
                          )}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              count={filteredModels?.length ?? 0}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[10, 25, 50, 100]}
            />
          </>
        )}
      </Paper>

      {/* Model Details Modal */}
      <Dialog
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Model Details
          {selectedModel && (
            <Typography variant="body2" color="text.secondary">
              {selectedModel?.display_name ?? 'Unknown'}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {selectedModel && (
            <Box sx={{ pt: 2 }}>
              <Grid container spacing={3}>
                {/* Provider */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Provider
                  </Typography>
                  <Chip
                    label={selectedModel?.provider_name ?? 'Unknown'}
                    color={getProviderColor(selectedModel?.provider_name)}
                  />
                </Grid>

                {/* Status */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Status
                  </Typography>
                  {selectedModel?.enabled ? (
                    <Chip icon={<CheckCircleIcon />} label="Enabled" color="success" />
                  ) : (
                    <Chip icon={<CancelIcon />} label="Disabled" color="error" />
                  )}
                </Grid>

                {/* Model ID */}
                <Grid item xs={12}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Model ID
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                      {selectedModel?.name ?? 'Unknown'}
                    </Typography>
                    <Tooltip title={copiedText === 'id' ? 'Copied!' : 'Copy to clipboard'}>
                      <IconButton
                        size="small"
                        onClick={() => handleCopy(selectedModel?.name ?? '', 'id')}
                      >
                        <CopyIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Grid>

                {/* Cost */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Input Cost (per 1M tokens)
                  </Typography>
                  <Typography variant="body1">
                    {selectedModel?.cost_per_1m_input !== null && selectedModel?.cost_per_1m_input !== undefined
                      ? `$${selectedModel.cost_per_1m_input.toFixed(4)}`
                      : 'Not available'}
                  </Typography>
                </Grid>

                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Output Cost (per 1M tokens)
                  </Typography>
                  <Typography variant="body1">
                    {selectedModel?.cost_per_1m_output !== null && selectedModel?.cost_per_1m_output !== undefined
                      ? `$${selectedModel.cost_per_1m_output.toFixed(4)}`
                      : 'Not available'}
                  </Typography>
                </Grid>

                {/* Context Length */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Context Length
                  </Typography>
                  <Typography variant="body1">
                    {formatContextLength(selectedModel?.context_length)}
                  </Typography>
                </Grid>

                {/* Rating */}
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Rating
                  </Typography>
                  {selectedModel?.rating ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <StarIcon sx={{ fontSize: 20, color: 'warning.main' }} />
                      <Typography variant="body1">
                        {selectedModel.rating.toFixed(1)} / 5.0
                      </Typography>
                    </Box>
                  ) : (
                    <Typography variant="body1" color="text.secondary">
                      Not rated
                    </Typography>
                  )}
                </Grid>

                {/* Internal IDs */}
                <Grid item xs={12}>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    Internal IDs (for reference)
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ minWidth: 80 }}>
                        Model ID:
                      </Typography>
                      <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                        {selectedModel?.id ?? 'Unknown'}
                      </Typography>
                      <Tooltip title={copiedText === 'model_id' ? 'Copied!' : 'Copy'}>
                        <IconButton
                          size="small"
                          onClick={() => handleCopy(selectedModel?.id ?? '', 'model_id')}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ minWidth: 80 }}>
                        Provider ID:
                      </Typography>
                      <Typography variant="caption" sx={{ fontFamily: 'monospace' }}>
                        {selectedModel?.provider_id ?? 'Unknown'}
                      </Typography>
                      <Tooltip title={copiedText === 'provider_id' ? 'Copied!' : 'Copy'}>
                        <IconButton
                          size="small"
                          onClick={() => handleCopy(selectedModel?.provider_id ?? '', 'provider_id')}
                        >
                          <CopyIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setModalOpen(false)}>
            Close
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Modal */}
      <Dialog
        open={editModalOpen}
        onClose={() => setEditModalOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Edit {selectedModels.length === 1 ? 'Model' : `${selectedModels.length} Models`}
        </DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            {selectedModels.length === 1 && (
              <>
                <Typography variant="body2" color="text.secondary">
                  Model: {models?.find(m => m?.id === selectedModels[0])?.display_name || selectedModels[0] || 'Unknown'}
                </Typography>
              </>
            )}

            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={editFormData.enabled ?? ''}
                label="Status"
                onChange={(e) => setEditFormData(prev => ({ ...prev, enabled: e.target.value }))}
              >
                <MenuItem value={true}>Enabled</MenuItem>
                <MenuItem value={false}>Disabled</MenuItem>
              </Select>
            </FormControl>

            {selectedModels.length > 1 && (
              <Typography variant="caption" color="text.secondary">
                This will update all {selectedModels.length} selected models
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditModalOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveEdit}
            variant="contained"
            disabled={bulkActionLoading}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
