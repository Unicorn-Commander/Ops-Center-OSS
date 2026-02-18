/**
 * Model List Management Page
 * Admin interface for managing app-specific curated model lists
 * Allows admins to create and manage model lists for Bolt.diy, Presenton, Open-WebUI, etc.
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Autocomplete,
  FormGroup,
  FormControlLabel,
  Snackbar,
  Menu,
  ListItemIcon,
  ListItemText,
  Divider,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  DragIndicator as DragIcon,
  Refresh as RefreshIcon,
  Upload as ImportIcon,
  Download as ExportIcon,
  Search as SearchIcon,
  Psychology as ModelIcon,
  Speed as SpeedIcon,
  Code as CodeIcon,
  Lightbulb as CreativeIcon,
  QuestionAnswer as ReasoningIcon,
  MoreVert as MoreIcon,
  ContentCopy as CloneIcon,
  Visibility as PreviewIcon,
  Close as CloseIcon,
  CheckCircle as FreeIcon,
  Image as ImageIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

// Category color definitions
const categoryColors = {
  coding: { bg: 'rgba(33, 150, 243, 0.15)', color: '#2196f3', border: '#2196f3', icon: <CodeIcon fontSize="small" /> },
  reasoning: { bg: 'rgba(156, 39, 176, 0.15)', color: '#9c27b0', border: '#9c27b0', icon: <ReasoningIcon fontSize="small" /> },
  general: { bg: 'rgba(117, 117, 117, 0.15)', color: '#757575', border: '#757575', icon: <ModelIcon fontSize="small" /> },
  fast: { bg: 'rgba(255, 193, 7, 0.15)', color: '#ffc107', border: '#ffc107', icon: <SpeedIcon fontSize="small" /> },
  creative: { bg: 'rgba(76, 175, 80, 0.15)', color: '#4caf50', border: '#4caf50', icon: <CreativeIcon fontSize="small" /> },
  image: { bg: 'rgba(233, 30, 99, 0.15)', color: '#e91e63', border: '#e91e63', icon: <ImageIcon fontSize="small" /> }
};

// Tier definitions
const tierOptions = [
  { id: 'trial', name: 'Trial', color: '#9e9e9e' },
  { id: 'starter', name: 'Starter', color: '#2196f3' },
  { id: 'professional', name: 'Professional', color: '#9c27b0' },
  { id: 'enterprise', name: 'Enterprise', color: '#f44336' },
  { id: 'vip_founder', name: 'VIP Founder', color: '#FFD700' },
  { id: 'byok', name: 'BYOK', color: '#4caf50' }
];

// Default app tabs
const defaultApps = [
  { id: 'global', name: 'Global', description: 'Default models for all apps' },
  { id: 'bolt', name: 'Bolt.diy', description: 'AI development environment' },
  { id: 'presenton', name: 'Presenton', description: 'AI presentations' },
  { id: 'openwebui', name: 'Open-WebUI', description: 'Chat interface' }
];

const ModelListManagement = () => {
  // State management
  const [lists, setLists] = useState([]);
  const [selectedList, setSelectedList] = useState(null);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Tab state
  const [tabValue, setTabValue] = useState(0);

  // Dialog states
  const [createListDialogOpen, setCreateListDialogOpen] = useState(false);
  const [addModelDialogOpen, setAddModelDialogOpen] = useState(false);
  const [editModelDialogOpen, setEditModelDialogOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [bulkDeleteConfirmOpen, setBulkDeleteConfirmOpen] = useState(false);

  // Search and catalog state
  const [catalogModels, setCatalogModels] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Selected items for bulk operations
  const [selectedModels, setSelectedModels] = useState([]);
  const [selectedModelForEdit, setSelectedModelForEdit] = useState(null);
  const [modelToDelete, setModelToDelete] = useState(null);

  // Preview tier filter
  const [previewTier, setPreviewTier] = useState('all');

  // Drag and drop state
  const [draggedItem, setDraggedItem] = useState(null);

  // Menu anchor for context menus
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [menuModel, setMenuModel] = useState(null);

  // Form data
  const [listFormData, setListFormData] = useState({
    name: '',
    app_id: '',
    description: ''
  });

  const [modelFormData, setModelFormData] = useState({
    model_id: '',
    display_name: '',
    category: 'general',
    description: '',
    tiers: ['starter', 'professional', 'enterprise', 'vip_founder', 'byok']
  });

  // Toast notification
  const [toast, setToast] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  // ============================================
  // API Functions
  // ============================================

  const fetchLists = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/admin/model-lists', { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch model lists');
      const data = await response.json();
      setLists(data);

      // Auto-select first list if available
      if (data.length > 0 && !selectedList) {
        setSelectedList(data[0]);
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching lists:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedList]);

  const fetchModels = useCallback(async (listId) => {
    if (!listId) return;
    setModelsLoading(true);
    try {
      const response = await fetch(`/api/v1/admin/model-lists/${listId}/models`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      setModels(data);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching models:', err);
    } finally {
      setModelsLoading(false);
    }
  }, []);

  const fetchCatalog = async (query) => {
    if (!query || query.length < 2) return;
    setCatalogLoading(true);
    try {
      // Fetch from OpenRouter catalog
      const response = await fetch(`/api/v1/llm/models?search=${encodeURIComponent(query)}`, { credentials: 'include' });
      if (!response.ok) throw new Error('Failed to fetch catalog');
      const data = await response.json();
      setCatalogModels(data.models || data || []);
    } catch (err) {
      console.error('Error fetching catalog:', err);
      setCatalogModels([]);
    } finally {
      setCatalogLoading(false);
    }
  };

  const createList = async () => {
    try {
      const response = await fetch('/api/v1/admin/model-lists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(listFormData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create list');
      }

      const newList = await response.json();
      showToast('Model list created successfully');
      setCreateListDialogOpen(false);
      resetListForm();
      await fetchLists();
      setSelectedList(newList);
    } catch (err) {
      showToast(err.message, 'error');
      console.error('Error creating list:', err);
    }
  };

  const deleteList = async (listId) => {
    try {
      const response = await fetch(`/api/v1/admin/model-lists/${listId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to delete list');

      showToast('Model list deleted successfully');
      await fetchLists();
      setSelectedList(null);
    } catch (err) {
      showToast(err.message, 'error');
      console.error('Error deleting list:', err);
    }
  };

  const addModel = async () => {
    if (!selectedList) return;
    try {
      const response = await fetch(`/api/v1/admin/model-lists/${selectedList.id}/models`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(modelFormData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to add model');
      }

      showToast('Model added successfully');
      setAddModelDialogOpen(false);
      resetModelForm();
      await fetchModels(selectedList.id);
    } catch (err) {
      showToast(err.message, 'error');
      console.error('Error adding model:', err);
    }
  };

  const updateModel = async () => {
    if (!selectedList || !selectedModelForEdit) return;
    try {
      const response = await fetch(`/api/v1/admin/model-lists/${selectedList.id}/models/${selectedModelForEdit.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(modelFormData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to update model');
      }

      showToast('Model updated successfully');
      setEditModelDialogOpen(false);
      resetModelForm();
      await fetchModels(selectedList.id);
    } catch (err) {
      showToast(err.message, 'error');
      console.error('Error updating model:', err);
    }
  };

  const deleteModel = async () => {
    if (!selectedList || !modelToDelete) return;
    try {
      const response = await fetch(`/api/v1/admin/model-lists/${selectedList.id}/models/${modelToDelete.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to delete model');

      showToast('Model removed successfully');
      setDeleteConfirmOpen(false);
      setModelToDelete(null);
      await fetchModels(selectedList.id);
    } catch (err) {
      showToast(err.message, 'error');
      console.error('Error deleting model:', err);
    }
  };

  const bulkDeleteModels = async () => {
    if (!selectedList || selectedModels.length === 0) return;
    try {
      // Delete each selected model
      await Promise.all(
        selectedModels.map(modelId =>
          fetch(`/api/v1/admin/model-lists/${selectedList.id}/models/${modelId}`, {
            method: 'DELETE',
            credentials: 'include'
          })
        )
      );

      showToast(`${selectedModels.length} models removed successfully`);
      setBulkDeleteConfirmOpen(false);
      setSelectedModels([]);
      await fetchModels(selectedList.id);
    } catch (err) {
      showToast(err.message, 'error');
      console.error('Error bulk deleting models:', err);
    }
  };

  const reorderModels = async (newOrder) => {
    if (!selectedList) return;
    try {
      const response = await fetch(`/api/v1/admin/model-lists/${selectedList.id}/reorder`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ model_ids: newOrder })
      });

      if (!response.ok) throw new Error('Failed to reorder models');

      showToast('Models reordered successfully');
    } catch (err) {
      showToast(err.message, 'error');
      // Revert optimistic update
      await fetchModels(selectedList.id);
    }
  };

  const exportList = () => {
    if (!selectedList || models.length === 0) return;

    const exportData = {
      list: {
        name: selectedList.name,
        app_id: selectedList.app_id,
        description: selectedList.description
      },
      models: models.map(m => ({
        model_id: m.model_id,
        display_name: m.display_name,
        category: m.category,
        description: m.description,
        tiers: m.tiers
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `model-list-${selectedList.app_id || 'custom'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    showToast('Model list exported');
  };

  const importList = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const data = JSON.parse(text);

      // Validate structure
      if (!data.models || !Array.isArray(data.models)) {
        throw new Error('Invalid file format');
      }

      // Add each model to current list
      for (const model of data.models) {
        await fetch(`/api/v1/admin/model-lists/${selectedList.id}/models`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify(model)
        });
      }

      showToast(`Imported ${data.models.length} models`);
      await fetchModels(selectedList.id);
    } catch (err) {
      showToast(`Import failed: ${err.message}`, 'error');
    }

    // Reset file input
    event.target.value = '';
  };

  // ============================================
  // Form Handlers
  // ============================================

  const resetListForm = () => {
    setListFormData({
      name: '',
      app_id: '',
      description: ''
    });
  };

  const resetModelForm = () => {
    setModelFormData({
      model_id: '',
      display_name: '',
      category: 'general',
      description: '',
      tiers: ['starter', 'professional', 'enterprise', 'vip_founder', 'byok']
    });
    setSelectedModelForEdit(null);
  };

  const handleEditModel = (model) => {
    setSelectedModelForEdit(model);
    setModelFormData({
      model_id: model.model_id,
      display_name: model.display_name || '',
      category: model.category || 'general',
      description: model.description || '',
      tiers: model.tiers || ['starter', 'professional', 'enterprise', 'vip_founder', 'byok']
    });
    setEditModelDialogOpen(true);
  };

  const handleTierToggle = (tierId) => {
    setModelFormData(prev => ({
      ...prev,
      tiers: prev.tiers.includes(tierId)
        ? prev.tiers.filter(t => t !== tierId)
        : [...prev.tiers, tierId]
    }));
  };

  const handleSelectAllModels = () => {
    if (selectedModels.length === filteredModels.length) {
      setSelectedModels([]);
    } else {
      setSelectedModels(filteredModels.map(m => m.id));
    }
  };

  const handleSelectModel = (modelId) => {
    setSelectedModels(prev =>
      prev.includes(modelId)
        ? prev.filter(id => id !== modelId)
        : [...prev, modelId]
    );
  };

  // ============================================
  // Drag and Drop Handlers
  // ============================================

  const handleDragStart = (e, index) => {
    setDraggedItem(index);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
    if (draggedItem === null || draggedItem === index) return;

    // Optimistic reorder
    const newModels = [...models];
    const draggedModel = newModels[draggedItem];
    newModels.splice(draggedItem, 1);
    newModels.splice(index, 0, draggedModel);
    setModels(newModels);
    setDraggedItem(index);
  };

  const handleDragEnd = () => {
    if (draggedItem !== null) {
      const newOrder = models.map(m => m.id);
      reorderModels(newOrder);
    }
    setDraggedItem(null);
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    fetchLists();
  }, []);

  useEffect(() => {
    if (selectedList) {
      fetchModels(selectedList.id);
      setSelectedModels([]);
    }
  }, [selectedList, fetchModels]);

  // Handle tab changes
  useEffect(() => {
    if (lists.length > 0) {
      const appId = defaultApps[tabValue]?.id;
      const list = lists.find(l => l.app_id === appId);
      if (list) {
        setSelectedList(list);
      } else {
        setSelectedList(null);
        setModels([]);
      }
    }
  }, [tabValue, lists]);

  // ============================================
  // Helper Functions
  // ============================================

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  const getCategoryStyle = (category) => {
    return categoryColors[category] || categoryColors.general;
  };

  const formatContextLength = (context) => {
    if (!context) return '-';
    if (context >= 1000000) return `${(context / 1000000).toFixed(1)}M`;
    if (context >= 1000) return `${(context / 1000).toFixed(0)}K`;
    return context.toString();
  };

  // Filter models based on preview tier
  const filteredModels = models.filter(model => {
    if (previewTier === 'all') return true;
    return model.tiers?.includes(previewTier);
  });

  // ============================================
  // Main Render
  // ============================================

  if (loading && lists.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Model List Management"
        subtitle="Create and manage app-specific curated model lists"
        actions={(
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => {
                fetchLists();
                if (selectedList) fetchModels(selectedList.id);
              }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                resetListForm();
                setCreateListDialogOpen(true);
              }}
            >
              Create New List
            </Button>
          </Box>
        )}
      />

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
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
                    Total Lists
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {lists.length}
                  </Typography>
                </Box>
                <ModelIcon sx={{ fontSize: 48, opacity: 0.3 }} />
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
                    Current List Models
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {models.length}
                  </Typography>
                </Box>
                <SpeedIcon sx={{ fontSize: 48, opacity: 0.3 }} />
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
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Filtered Models
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {filteredModels.length}
                  </Typography>
                </Box>
                <PreviewIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(250, 112, 154, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Categories
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {Object.keys(categoryColors).length}
                  </Typography>
                </Box>
                <CreativeIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* App Tabs */}
      <Paper sx={{ mb: 3, borderRadius: 2 }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              fontWeight: 600,
              textTransform: 'none'
            }
          }}
        >
          {defaultApps.map((app, index) => (
            <Tab key={app.id} label={app.name} />
          ))}
        </Tabs>

        {/* Toolbar */}
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            {selectedList && (
              <>
                <Button
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    resetModelForm();
                    setAddModelDialogOpen(true);
                  }}
                  variant="contained"
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    borderRadius: 2,
                    '&:hover': {
                      background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
                    }
                  }}
                >
                  Add Model
                </Button>
                <input
                  type="file"
                  accept=".json"
                  id="import-input"
                  style={{ display: 'none' }}
                  onChange={importList}
                />
                <label htmlFor="import-input">
                  <Button
                    size="small"
                    startIcon={<ImportIcon />}
                    component="span"
                    variant="outlined"
                    sx={{ borderRadius: 2 }}
                  >
                    Import
                  </Button>
                </label>
                <Button
                  size="small"
                  startIcon={<ExportIcon />}
                  onClick={exportList}
                  variant="outlined"
                  disabled={models.length === 0}
                  sx={{ borderRadius: 2 }}
                >
                  Export
                </Button>
                {selectedModels.length > 0 && (
                  <Button
                    size="small"
                    startIcon={<DeleteIcon />}
                    onClick={() => setBulkDeleteConfirmOpen(true)}
                    color="error"
                    variant="outlined"
                    sx={{ borderRadius: 2 }}
                  >
                    Delete ({selectedModels.length})
                  </Button>
                )}
              </>
            )}
          </Box>

          {/* Preview as Tier */}
          <FormControl size="small" sx={{ minWidth: 160 }}>
            <InputLabel>Preview as Tier</InputLabel>
            <Select
              value={previewTier}
              onChange={(e) => setPreviewTier(e.target.value)}
              label="Preview as Tier"
            >
              <MenuItem value="all">All Tiers</MenuItem>
              <Divider />
              {tierOptions.map(tier => (
                <MenuItem key={tier.id} value={tier.id}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Box
                      sx={{
                        width: 8,
                        height: 8,
                        borderRadius: '50%',
                        bgcolor: tier.color
                      }}
                    />
                    {tier.name}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* Model Table */}
      <Paper sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: 2 }}>
        {!selectedList ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              No model list exists for {defaultApps[tabValue]?.name}
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setListFormData({
                  name: `${defaultApps[tabValue]?.name} Models`,
                  app_id: defaultApps[tabValue]?.id,
                  description: `Curated models for ${defaultApps[tabValue]?.name}`
                });
                setCreateListDialogOpen(true);
              }}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                borderRadius: 2
              }}
            >
              Create List for {defaultApps[tabValue]?.name}
            </Button>
          </Box>
        ) : modelsLoading ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <CircularProgress />
          </Box>
        ) : filteredModels.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography color="text.secondary" sx={{ mb: 2 }}>
              {previewTier !== 'all'
                ? `No models available for ${tierOptions.find(t => t.id === previewTier)?.name} tier`
                : 'No models in this list yet'}
            </Typography>
            {previewTier === 'all' && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  resetModelForm();
                  setAddModelDialogOpen(true);
                }}
                sx={{
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  borderRadius: 2
                }}
              >
                Add First Model
              </Button>
            )}
          </Box>
        ) : (
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedModels.length === filteredModels.length && filteredModels.length > 0}
                      indeterminate={selectedModels.length > 0 && selectedModels.length < filteredModels.length}
                      onChange={handleSelectAllModels}
                    />
                  </TableCell>
                  <TableCell sx={{ fontWeight: 700, width: 40 }}>Order</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Model ID</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Display Name</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Category</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Context</TableCell>
                  <TableCell sx={{ fontWeight: 700 }}>Tiers</TableCell>
                  <TableCell align="center" sx={{ fontWeight: 700 }}>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredModels.map((model, index) => (
                  <TableRow
                    key={model.id}
                    hover
                    draggable
                    onDragStart={(e) => handleDragStart(e, index)}
                    onDragOver={(e) => handleDragOver(e, index)}
                    onDragEnd={handleDragEnd}
                    sx={{
                      cursor: 'grab',
                      transition: 'all 0.2s',
                      '&:hover': {
                        backgroundColor: 'rgba(102, 126, 234, 0.04)'
                      },
                      opacity: draggedItem === index ? 0.5 : 1
                    }}
                  >
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedModels.includes(model.id)}
                        onChange={() => handleSelectModel(model.id)}
                      />
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <DragIcon sx={{ color: 'text.secondary', mr: 1 }} />
                        <Typography variant="body2">{index + 1}</Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {model.model_id}
                        </Typography>
                        {model.is_free && (
                          <Chip
                            label="FREE"
                            size="small"
                            icon={<FreeIcon sx={{ fontSize: 14 }} />}
                            sx={{
                              bgcolor: 'rgba(76, 175, 80, 0.15)',
                              color: '#4caf50',
                              fontWeight: 600,
                              fontSize: '0.65rem',
                              height: 20
                            }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body1" fontWeight="bold">
                        {model.display_name || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getCategoryStyle(model.category).icon}
                        label={model.category}
                        size="small"
                        sx={{
                          bgcolor: getCategoryStyle(model.category).bg,
                          color: getCategoryStyle(model.category).color,
                          fontWeight: 600,
                          border: `1px solid ${getCategoryStyle(model.category).border}`
                        }}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatContextLength(model.context_length)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                        {model.tiers?.slice(0, 3).map(tierId => {
                          const tier = tierOptions.find(t => t.id === tierId);
                          return tier ? (
                            <Chip
                              key={tierId}
                              label={tier.name}
                              size="small"
                              sx={{
                                bgcolor: `${tier.color}20`,
                                color: tier.color,
                                fontWeight: 600,
                                fontSize: '0.65rem',
                                height: 20
                              }}
                            />
                          ) : null;
                        })}
                        {model.tiers?.length > 3 && (
                          <Chip
                            label={`+${model.tiers.length - 3}`}
                            size="small"
                            sx={{ height: 20, fontSize: '0.65rem' }}
                          />
                        )}
                      </Box>
                    </TableCell>
                    <TableCell align="center">
                      <Tooltip title="Edit">
                        <IconButton
                          size="small"
                          onClick={() => handleEditModel(model)}
                        >
                          <EditIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton
                          size="small"
                          onClick={() => {
                            setModelToDelete(model);
                            setDeleteConfirmOpen(true);
                          }}
                        >
                          <DeleteIcon fontSize="small" />
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

      {/* Create List Dialog */}
      <Dialog
        open={createListDialogOpen}
        onClose={() => setCreateListDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create Model List</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="List Name"
                value={listFormData.name}
                onChange={(e) => setListFormData({ ...listFormData, name: e.target.value })}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>App</InputLabel>
                <Select
                  value={listFormData.app_id}
                  onChange={(e) => setListFormData({ ...listFormData, app_id: e.target.value })}
                  label="App"
                >
                  {defaultApps.map(app => (
                    <MenuItem key={app.id} value={app.id}>
                      {app.name}
                    </MenuItem>
                  ))}
                  <MenuItem value="custom">Custom</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={listFormData.description}
                onChange={(e) => setListFormData({ ...listFormData, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setCreateListDialogOpen(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={createList}
            variant="contained"
            disabled={!listFormData.name}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              '&:hover': {
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              }
            }}
          >
            Create List
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add Model Dialog */}
      <Dialog
        open={addModelDialogOpen}
        onClose={() => setAddModelDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Add Model to List</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Autocomplete
                freeSolo
                options={catalogModels}
                getOptionLabel={(option) => typeof option === 'string' ? option : option.id || ''}
                inputValue={searchQuery}
                onInputChange={(e, value) => {
                  setSearchQuery(value);
                  if (value.length >= 2) {
                    fetchCatalog(value);
                  }
                }}
                onChange={(e, value) => {
                  if (value && typeof value === 'object') {
                    setModelFormData(prev => ({
                      ...prev,
                      model_id: value.id,
                      display_name: value.name || value.id.split('/').pop(),
                      context_length: value.context_length
                    }));
                  } else if (typeof value === 'string') {
                    setModelFormData(prev => ({
                      ...prev,
                      model_id: value
                    }));
                  }
                }}
                loading={catalogLoading}
                renderInput={(params) => (
                  <TextField
                    {...params}
                    label="Search Model"
                    placeholder="Type to search OpenRouter catalog..."
                    InputProps={{
                      ...params.InputProps,
                      startAdornment: (
                        <InputAdornment position="start">
                          <SearchIcon />
                        </InputAdornment>
                      )
                    }}
                  />
                )}
                renderOption={(props, option) => (
                  <Box component="li" {...props}>
                    <Box sx={{ width: '100%' }}>
                      <Typography variant="body2" fontWeight="bold">
                        {option.name || option.id}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {option.id} | Context: {formatContextLength(option.context_length)}
                        {option.pricing && ` | $${(option.pricing.prompt * 1000).toFixed(4)}/1K`}
                      </Typography>
                    </Box>
                  </Box>
                )}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Model ID"
                value={modelFormData.model_id}
                onChange={(e) => setModelFormData({ ...modelFormData, model_id: e.target.value })}
                required
                helperText="e.g., openai/gpt-4-turbo"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Display Name"
                value={modelFormData.display_name}
                onChange={(e) => setModelFormData({ ...modelFormData, display_name: e.target.value })}
                helperText="Optional custom display name"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={modelFormData.category}
                  onChange={(e) => setModelFormData({ ...modelFormData, category: e.target.value })}
                  label="Category"
                >
                  {Object.keys(categoryColors).map(cat => (
                    <MenuItem key={cat} value={cat}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {categoryColors[cat].icon}
                        <span style={{ textTransform: 'capitalize' }}>{cat}</span>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Description"
                value={modelFormData.description}
                onChange={(e) => setModelFormData({ ...modelFormData, description: e.target.value })}
                helperText="Optional description"
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Available for Tiers
              </Typography>
              <FormGroup row>
                {tierOptions.map(tier => (
                  <FormControlLabel
                    key={tier.id}
                    control={
                      <Checkbox
                        checked={modelFormData.tiers.includes(tier.id)}
                        onChange={() => handleTierToggle(tier.id)}
                        sx={{
                          color: tier.color,
                          '&.Mui-checked': { color: tier.color }
                        }}
                      />
                    }
                    label={tier.name}
                  />
                ))}
              </FormGroup>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setAddModelDialogOpen(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={addModel}
            variant="contained"
            disabled={!modelFormData.model_id}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              '&:hover': {
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              }
            }}
          >
            Add Model
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Model Dialog */}
      <Dialog
        open={editModelDialogOpen}
        onClose={() => setEditModelDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Edit Model</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Model ID"
                value={modelFormData.model_id}
                disabled
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Display Name"
                value={modelFormData.display_name}
                onChange={(e) => setModelFormData({ ...modelFormData, display_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={modelFormData.category}
                  onChange={(e) => setModelFormData({ ...modelFormData, category: e.target.value })}
                  label="Category"
                >
                  {Object.keys(categoryColors).map(cat => (
                    <MenuItem key={cat} value={cat}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {categoryColors[cat].icon}
                        <span style={{ textTransform: 'capitalize' }}>{cat}</span>
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                value={modelFormData.description}
                onChange={(e) => setModelFormData({ ...modelFormData, description: e.target.value })}
                multiline
                rows={2}
              />
            </Grid>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>
                Available for Tiers
              </Typography>
              <FormGroup row>
                {tierOptions.map(tier => (
                  <FormControlLabel
                    key={tier.id}
                    control={
                      <Checkbox
                        checked={modelFormData.tiers.includes(tier.id)}
                        onChange={() => handleTierToggle(tier.id)}
                        sx={{
                          color: tier.color,
                          '&.Mui-checked': { color: tier.color }
                        }}
                      />
                    }
                    label={tier.name}
                  />
                ))}
              </FormGroup>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setEditModelDialogOpen(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={updateModel}
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              borderRadius: 2,
              '&:hover': {
                background: 'linear-gradient(135deg, #5fbcff 0%, #10ffff 100%)'
              }
            }}
          >
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove <strong>{modelToDelete?.model_id}</strong> from this list?
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setDeleteConfirmOpen(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={deleteModel}
            variant="contained"
            color="error"
            sx={{ borderRadius: 2 }}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog
        open={bulkDeleteConfirmOpen}
        onClose={() => setBulkDeleteConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Confirm Bulk Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to remove <strong>{selectedModels.length} models</strong> from this list?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button onClick={() => setBulkDeleteConfirmOpen(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={bulkDeleteModels}
            variant="contained"
            color="error"
            sx={{ borderRadius: 2 }}
          >
            Delete {selectedModels.length} Models
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notification */}
      <Snackbar
        open={toast.open}
        autoHideDuration={6000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={() => setToast({ ...toast, open: false })}
          severity={toast.severity}
          sx={{ width: '100%' }}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ModelListManagement;
