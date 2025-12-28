import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Button,
  TextField,
  MenuItem,
  Typography,
  Alert,
  CircularProgress
} from '@mui/material';
import { Add, Refresh } from '@mui/icons-material';
import ModelCard from './ModelCard';
import ModelAddModal from './ModelAddModal';
import ModelTestModal from './ModelTestModal';

/**
 * ModelRegistry Component
 *
 * Main component for managing LLM models
 */
export default function ModelRegistry({ showSnackbar }) {
  const [models, setModels] = useState([]);
  const [filteredModels, setFilteredModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [filterProvider, setFilterProvider] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const [addModalOpen, setAddModalOpen] = useState(false);
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState(null);

  useEffect(() => {
    fetchModels();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [models, filterProvider, filterStatus, searchQuery]);

  const fetchModels = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/v1/llm/models', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }

      const data = await response.json();
      setModels(data.models || []);
    } catch (err) {
      setError(err.message);
      showSnackbar(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...models];

    if (filterProvider !== 'all') {
      filtered = filtered.filter((m) => m.provider === filterProvider);
    }

    if (filterStatus !== 'all') {
      filtered = filtered.filter((m) => m.status === filterStatus);
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (m) =>
          m.name.toLowerCase().includes(query) ||
          m.model_id.toLowerCase().includes(query)
      );
    }

    setFilteredModels(filtered);
  };

  const handleAddModel = async (modelData) => {
    try {
      const response = await fetch('/api/v1/llm/models', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        },
        body: JSON.stringify(modelData)
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to add model');
      }

      showSnackbar('Model added successfully', 'success');
      fetchModels();
    } catch (err) {
      showSnackbar(err.message, 'error');
      throw err;
    }
  };

  const handleDeleteModel = async (model) => {
    if (!confirm(`Are you sure you want to delete ${model.name}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/llm/models/${model.model_id}`, {
        method: 'DELETE',
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete model');
      }

      showSnackbar('Model deleted successfully', 'success');
      fetchModels();
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const handleTestModel = async (modelId, prompt) => {
    const response = await fetch(`/api/v1/llm/models/${modelId}/test`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Admin-Token': localStorage.getItem('adminToken') || ''
      },
      body: JSON.stringify({ test_prompt: prompt })
    });

    if (!response.ok) {
      const data = await response.json();
      throw new Error(data.detail || 'Test failed');
    }

    return await response.json();
  };

  const handleOpenTest = (model) => {
    setSelectedModel(model);
    setTestModalOpen(true);
  };

  const providers = ['all', 'vllm', 'openai', 'anthropic', 'cohere', 'openrouter', 'byok'];
  const statuses = ['all', 'active', 'inactive', 'error', 'testing'];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          label="Search Models"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          size="small"
          sx={{ minWidth: 250 }}
        />

        <TextField
          select
          label="Provider"
          value={filterProvider}
          onChange={(e) => setFilterProvider(e.target.value)}
          size="small"
          sx={{ minWidth: 150 }}
        >
          {providers.map((p) => (
            <MenuItem key={p} value={p}>
              {p.charAt(0).toUpperCase() + p.slice(1)}
            </MenuItem>
          ))}
        </TextField>

        <TextField
          select
          label="Status"
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          size="small"
          sx={{ minWidth: 150 }}
        >
          {statuses.map((s) => (
            <MenuItem key={s} value={s}>
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </MenuItem>
          ))}
        </TextField>

        <Box sx={{ flexGrow: 1 }} />

        <Button
          startIcon={<Refresh />}
          onClick={fetchModels}
          variant="outlined"
          size="small"
        >
          Refresh
        </Button>

        <Button
          startIcon={<Add />}
          onClick={() => setAddModalOpen(true)}
          variant="contained"
          size="small"
        >
          Add Model
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {filteredModels.length === 0 ? (
        <Alert severity="info">
          No models found. Click "Add Model" to get started.
        </Alert>
      ) : (
        <>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Showing {filteredModels.length} of {models.length} models
          </Typography>

          <Grid container spacing={2}>
            {filteredModels.map((model) => (
              <Grid item xs={12} sm={6} md={4} key={model.model_id}>
                <ModelCard
                  model={model}
                  onEdit={() => {}}
                  onDelete={handleDeleteModel}
                  onTest={handleOpenTest}
                />
              </Grid>
            ))}
          </Grid>
        </>
      )}

      <ModelAddModal
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onAdd={handleAddModel}
      />

      {selectedModel && (
        <ModelTestModal
          open={testModalOpen}
          model={selectedModel}
          onClose={() => {
            setTestModalOpen(false);
            setSelectedModel(null);
          }}
          onTest={handleTestModel}
        />
      )}
    </Box>
  );
}
