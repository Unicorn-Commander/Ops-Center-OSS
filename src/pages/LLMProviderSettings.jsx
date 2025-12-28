import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Paper,
  Snackbar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Chip,
  Card,
  CardContent
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  CloudUpload as CloudIcon,
  Key as KeyIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import AIServerCard from '../components/llm/AIServerCard';
import AddAIServerModal from '../components/llm/AddAIServerModal';
import APIKeyCard from '../components/llm/APIKeyCard';
import AddAPIKeyModal from '../components/llm/AddAPIKeyModal';

const LLMProviderSettings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // AI Servers State
  const [aiServers, setAiServers] = useState([]);
  const [serverModalOpen, setServerModalOpen] = useState(false);
  const [editingServer, setEditingServer] = useState(null);
  const [deleteServerDialog, setDeleteServerDialog] = useState(null);

  // API Keys State
  const [apiKeys, setApiKeys] = useState([]);
  const [keyModalOpen, setKeyModalOpen] = useState(false);
  const [editingKey, setEditingKey] = useState(null);
  const [deleteKeyDialog, setDeleteKeyDialog] = useState(null);

  // UI State
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [error, setError] = useState(null);

  // Load data on mount
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      await Promise.all([loadAIServers(), loadAPIKeys()]);
    } catch (err) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadAIServers = async () => {
    try {
      const response = await fetch('/api/v1/llm-config/servers', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load AI servers');
      }

      const data = await response.json();
      setAiServers(data.servers || []);
    } catch (err) {
      console.error('Error loading AI servers:', err);
      // Set empty array on error
      setAiServers([]);
    }
  };

  const loadAPIKeys = async () => {
    try {
      const response = await fetch('/api/v1/llm-config/api-keys', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to load API keys');
      }

      const data = await response.json();
      setApiKeys(data.api_keys || []);

      // Pre-populate OpenRouter key if no keys exist
      if (!data.api_keys || data.api_keys.length === 0) {
        setTimeout(() => {
          setKeyModalOpen(true);
        }, 1000);
      }
    } catch (err) {
      console.error('Error loading API keys:', err);
      // Set empty array on error
      setApiKeys([]);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
    showSnackbar('Data refreshed successfully', 'success');
  };

  // AI Server Handlers
  const handleAddServer = () => {
    setEditingServer(null);
    setServerModalOpen(true);
  };

  const handleEditServer = (server) => {
    setEditingServer(server);
    setServerModalOpen(true);
  };

  const handleSaveServer = async (serverData) => {
    try {
      const url = serverData.id
        ? `/api/v1/llm-config/servers/${serverData.id}`
        : '/api/v1/llm-config/servers';

      const method = serverData.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(serverData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save server');
      }

      const result = await response.json();

      setServerModalOpen(false);
      setEditingServer(null);
      await loadAIServers();
      showSnackbar(
        serverData.id ? 'Server updated successfully' : 'Server added successfully',
        'success'
      );
    } catch (err) {
      showSnackbar(err.message || 'Failed to save server', 'error');
    }
  };

  const handleDeleteServer = async (serverId) => {
    try {
      const response = await fetch(`/api/v1/llm-config/servers/${serverId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete server');
      }

      setDeleteServerDialog(null);
      await loadAIServers();
      showSnackbar('Server deleted successfully', 'success');
    } catch (err) {
      showSnackbar(err.message || 'Failed to delete server', 'error');
    }
  };

  const handleToggleServer = async (serverId, enabled) => {
    try {
      const server = aiServers.find((s) => s.id === serverId);
      if (!server) return;

      const response = await fetch(`/api/v1/llm-config/servers/${serverId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          ...server,
          enabled
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update server');
      }

      await loadAIServers();
      showSnackbar(`Server ${enabled ? 'enabled' : 'disabled'} successfully`, 'success');
    } catch (err) {
      showSnackbar(err.message || 'Failed to update server', 'error');
    }
  };

  const handleTestServer = async (serverId) => {
    try {
      const response = await fetch(`/api/v1/llm-config/servers/${serverId}/test`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || 'Connection test failed'
        };
      }

      const result = await response.json();
      return result;
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Failed to test connection'
      };
    }
  };

  // API Key Handlers
  const handleAddKey = () => {
    setEditingKey(null);
    setKeyModalOpen(true);
  };

  const handleEditKey = (key) => {
    setEditingKey(key);
    setKeyModalOpen(true);
  };

  const handleSaveKey = async (keyData) => {
    try {
      const url = keyData.id
        ? `/api/v1/llm-config/api-keys/${keyData.id}`
        : '/api/v1/llm-config/api-keys';

      const method = keyData.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(keyData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save API key');
      }

      const result = await response.json();

      setKeyModalOpen(false);
      setEditingKey(null);
      await loadAPIKeys();
      showSnackbar(
        keyData.id ? 'API key updated successfully' : 'API key added successfully',
        'success'
      );
    } catch (err) {
      showSnackbar(err.message || 'Failed to save API key', 'error');
    }
  };

  const handleDeleteKey = async (keyId) => {
    try {
      const response = await fetch(`/api/v1/llm-config/api-keys/${keyId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error('Failed to delete API key');
      }

      setDeleteKeyDialog(null);
      await loadAPIKeys();
      showSnackbar('API key deleted successfully', 'success');
    } catch (err) {
      showSnackbar(err.message || 'Failed to delete API key', 'error');
    }
  };

  const handleToggleKey = async (keyId, enabled) => {
    try {
      const key = apiKeys.find((k) => k.id === keyId);
      if (!key) return;

      const response = await fetch(`/api/v1/llm-config/api-keys/${keyId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({
          ...key,
          enabled
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update API key');
      }

      await loadAPIKeys();
      showSnackbar(`API key ${enabled ? 'enabled' : 'disabled'} successfully`, 'success');
    } catch (err) {
      showSnackbar(err.message || 'Failed to update API key', 'error');
    }
  };

  const handleTestKey = async (keyId) => {
    try {
      const response = await fetch(`/api/v1/llm-config/api-keys/${keyId}/test`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || 'API key validation failed'
        };
      }

      const result = await response.json();
      return result;
    } catch (err) {
      return {
        success: false,
        error: err.message || 'Failed to validate API key'
      };
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '60vh'
        }}
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ padding: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            mb: 1
          }}
        >
          LLM Provider Settings
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Manage AI servers and API keys for LLM inference
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Get Started Banner (show if no servers and no keys) */}
      {aiServers.length === 0 && apiKeys.length === 0 && (
        <Card
          sx={{
            mb: 3,
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
            border: '1px solid rgba(139, 92, 246, 0.2)'
          }}
        >
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <InfoIcon sx={{ fontSize: 40, color: 'primary.main' }} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Get Started with LLM Providers
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Add AI servers or API keys to enable LLM inference in Ops-Center
                </Typography>
              </Box>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                startIcon={<CloudIcon />}
                onClick={handleAddServer}
                sx={{
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c3aed 0%, #db2777 100%)'
                  }
                }}
              >
                Add AI Server
              </Button>
              <Button
                variant="outlined"
                startIcon={<KeyIcon />}
                onClick={handleAddKey}
                sx={{
                  borderColor: 'primary.main',
                  color: 'primary.main'
                }}
              >
                Add API Key
              </Button>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Paper
        sx={{
          mb: 3,
          background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(139, 92, 246, 0.2)'
        }}
      >
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={activeTab}
            onChange={(e, newValue) => setActiveTab(newValue)}
            sx={{
              '& .MuiTab-root': {
                fontWeight: 600,
                fontSize: '1rem'
              }
            }}
          >
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CloudIcon />
                  <span>AI Servers ({aiServers.length})</span>
                </Box>
              }
            />
            <Tab
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <KeyIcon />
                  <span>API Keys ({apiKeys.length})</span>
                </Box>
              }
            />
          </Tabs>
        </Box>

        {/* Tab Actions */}
        <Box
          sx={{
            padding: 2,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            borderBottom: '1px solid rgba(139, 92, 246, 0.1)'
          }}
        >
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            {activeTab === 0 && (
              <>
                <Chip
                  label={`${aiServers.filter((s) => s.enabled).length} Active`}
                  color="success"
                  size="small"
                />
                <Chip
                  label={`${aiServers.filter((s) => s.status === 'healthy').length} Healthy`}
                  color="primary"
                  size="small"
                />
              </>
            )}
            {activeTab === 1 && (
              <>
                <Chip
                  label={`${apiKeys.filter((k) => k.enabled).length} Active`}
                  color="success"
                  size="small"
                />
                <Chip
                  label={`${apiKeys.filter((k) => k.status === 'active').length} Valid`}
                  color="primary"
                  size="small"
                />
              </>
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              startIcon={refreshing ? <CircularProgress size={20} /> : <RefreshIcon />}
              onClick={handleRefresh}
              disabled={refreshing}
              sx={{ color: 'text.secondary' }}
            >
              Refresh
            </Button>
            {activeTab === 0 && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddServer}
                sx={{
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c3aed 0%, #db2777 100%)'
                  }
                }}
              >
                Add Server
              </Button>
            )}
            {activeTab === 1 && (
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddKey}
                sx={{
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c3aed 0%, #db2777 100%)'
                  }
                }}
              >
                Add API Key
              </Button>
            )}
          </Box>
        </Box>
      </Paper>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Box>
          {aiServers.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                padding: 6,
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
                borderRadius: 2,
                border: '1px dashed rgba(139, 92, 246, 0.3)'
              }}
            >
              <CloudIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" sx={{ mb: 1 }}>
                No AI Servers Configured
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Add your first AI server to enable self-hosted LLM inference
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddServer}
                sx={{
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c3aed 0%, #db2777 100%)'
                  }
                }}
              >
                Add AI Server
              </Button>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {aiServers.map((server) => (
                <Grid item xs={12} md={6} lg={4} key={server.id}>
                  <AIServerCard
                    server={server}
                    onEdit={handleEditServer}
                    onDelete={(id) => setDeleteServerDialog(id)}
                    onToggle={handleToggleServer}
                    onTest={handleTestServer}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {activeTab === 1 && (
        <Box>
          {apiKeys.length === 0 ? (
            <Box
              sx={{
                textAlign: 'center',
                padding: 6,
                background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.05) 0%, rgba(236, 72, 153, 0.05) 100%)',
                borderRadius: 2,
                border: '1px dashed rgba(139, 92, 246, 0.3)'
              }}
            >
              <KeyIcon sx={{ fontSize: 80, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" sx={{ mb: 1 }}>
                No API Keys Configured
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Add your first API key to access third-party LLM providers
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={handleAddKey}
                sx={{
                  background: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
                  '&:hover': {
                    background: 'linear-gradient(135deg, #7c3aed 0%, #db2777 100%)'
                  }
                }}
              >
                Add API Key
              </Button>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {apiKeys.map((key) => (
                <Grid item xs={12} md={6} lg={4} key={key.id}>
                  <APIKeyCard
                    apiKey={key}
                    onEdit={handleEditKey}
                    onDelete={(id) => setDeleteKeyDialog(id)}
                    onToggle={handleToggleKey}
                    onTest={handleTestKey}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Box>
      )}

      {/* Add/Edit Server Modal */}
      <AddAIServerModal
        open={serverModalOpen}
        onClose={() => {
          setServerModalOpen(false);
          setEditingServer(null);
        }}
        onSave={handleSaveServer}
        editServer={editingServer}
      />

      {/* Add/Edit API Key Modal */}
      <AddAPIKeyModal
        open={keyModalOpen}
        onClose={() => {
          setKeyModalOpen(false);
          setEditingKey(null);
        }}
        onSave={handleSaveKey}
        editApiKey={editingKey}
      />

      {/* Delete Server Confirmation */}
      <Dialog
        open={deleteServerDialog !== null}
        onClose={() => setDeleteServerDialog(null)}
        PaperProps={{
          sx: {
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(139, 92, 246, 0.2)'
          }
        }}
      >
        <DialogTitle>Delete AI Server</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this AI server? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteServerDialog(null)} sx={{ color: 'text.secondary' }}>
            Cancel
          </Button>
          <Button
            onClick={() => handleDeleteServer(deleteServerDialog)}
            variant="contained"
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete API Key Confirmation */}
      <Dialog
        open={deleteKeyDialog !== null}
        onClose={() => setDeleteKeyDialog(null)}
        PaperProps={{
          sx: {
            background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)',
            backdropFilter: 'blur(10px)',
            border: '1px solid rgba(139, 92, 246, 0.2)'
          }
        }}
      >
        <DialogTitle>Delete API Key</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete this API key? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteKeyDialog(null)} sx={{ color: 'text.secondary' }}>
            Cancel
          </Button>
          <Button
            onClick={() => handleDeleteKey(deleteKeyDialog)}
            variant="contained"
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default LLMProviderSettings;
