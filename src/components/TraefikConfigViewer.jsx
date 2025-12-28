import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  IconButton,
  Alert,
  Skeleton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip
} from '@mui/material';
import {
  ArrowDownTrayIcon,
  ArrowPathIcon,
  DocumentTextIcon,
  ClockIcon
} from '@heroicons/react/24/outline';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml';
import { atomOneDark } from 'react-syntax-highlighter/dist/esm/styles/hljs';

// Register YAML language
SyntaxHighlighter.registerLanguage('yaml', yaml);

const TraefikConfigViewer = ({ open, onClose }) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [currentConfig, setCurrentConfig] = useState('');
  const [backups, setBackups] = useState([]);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [backupDialogOpen, setBackupDialogOpen] = useState(false);

  useEffect(() => {
    if (open) {
      loadConfig();
      loadBackups();
    }
  }, [open]);

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/traefik/config', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) throw new Error('Failed to load configuration');

      const data = await response.json();
      setCurrentConfig(data.config || '');
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadBackups = async () => {
    try {
      const response = await fetch('/api/v1/traefik/config/backups', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setBackups(data.backups || []);
      }
    } catch (err) {
      console.error('Failed to load backups:', err);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([currentConfig], { type: 'text/yaml' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `traefik-config-${Date.now()}.yml`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleRestore = async () => {
    if (!selectedBackup) return;

    if (!confirm('Are you sure you want to restore this configuration? This will restart Traefik.')) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/traefik/config/restore/${selectedBackup.id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) throw new Error('Failed to restore configuration');

      setSuccess('Configuration restored successfully. Traefik is restarting...');
      setBackupDialogOpen(false);
      setSelectedBackup(null);
      loadConfig();
    } catch (err) {
      setError(err.message);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">Traefik Configuration</Typography>
          <Box display="flex" gap={1}>
            <IconButton onClick={loadConfig} disabled={loading}>
              <ArrowPathIcon style={{ width: 20, height: 20 }} />
            </IconButton>
            <IconButton onClick={handleDownload} disabled={loading}>
              <ArrowDownTrayIcon style={{ width: 20, height: 20 }} />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>

      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        <Tabs value={activeTab} onChange={(e, v) => setActiveTab(v)} sx={{ mb: 2 }}>
          <Tab label="Current Configuration" />
          <Tab label={`Backups (${backups.length})`} />
        </Tabs>

        {/* Current Config Tab */}
        {activeTab === 0 && (
          <Box>
            {loading ? (
              <Skeleton variant="rectangular" height={400} />
            ) : (
              <Paper variant="outlined" sx={{ maxHeight: 500, overflow: 'auto' }}>
                <SyntaxHighlighter
                  language="yaml"
                  style={atomOneDark}
                  customStyle={{
                    margin: 0,
                    borderRadius: 4,
                    fontSize: '0.85rem'
                  }}
                >
                  {currentConfig}
                </SyntaxHighlighter>
              </Paper>
            )}

            <Alert severity="info" sx={{ mt: 2 }}>
              This is a read-only view of the current Traefik configuration. Use the Routes,
              Services, and Middleware pages to make changes.
            </Alert>
          </Box>
        )}

        {/* Backups Tab */}
        {activeTab === 1 && (
          <Box>
            {backups.length > 0 ? (
              <List>
                {backups.map((backup) => (
                  <ListItem
                    key={backup.id}
                    button
                    onClick={() => {
                      setSelectedBackup(backup);
                      setBackupDialogOpen(true);
                    }}
                    sx={{
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1,
                      mb: 1
                    }}
                  >
                    <ListItemIcon>
                      <DocumentTextIcon style={{ width: 24, height: 24 }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body2">
                            {new Date(backup.createdAt).toLocaleString()}
                          </Typography>
                          {backup.auto && <Chip label="Auto" size="small" />}
                        </Box>
                      }
                      secondary={`${formatFileSize(backup.size)} • ${backup.routes || 0} routes`}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Box textAlign="center" py={8}>
                <ClockIcon style={{ width: 48, height: 48, color: '#ccc', margin: '0 auto' }} />
                <Typography variant="body2" color="text.secondary" mt={2}>
                  No configuration backups available
                </Typography>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>

      {/* Backup Preview/Restore Dialog */}
      <Dialog
        open={backupDialogOpen}
        onClose={() => {
          setBackupDialogOpen(false);
          setSelectedBackup(null);
        }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Restore Configuration Backup
        </DialogTitle>
        <DialogContent>
          {selectedBackup && (
            <Box>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Created At
                </Typography>
                <Typography variant="body1">
                  {new Date(selectedBackup.createdAt).toLocaleString()}
                </Typography>
              </Box>

              <Box mb={2}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Details
                </Typography>
                <Typography variant="body1">
                  {selectedBackup.routes || 0} routes • {formatFileSize(selectedBackup.size)}
                </Typography>
              </Box>

              <Alert severity="warning">
                Restoring this backup will replace the current configuration and restart Traefik.
                This may cause a brief interruption in service.
              </Alert>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setBackupDialogOpen(false);
              setSelectedBackup(null);
            }}
          >
            Cancel
          </Button>
          <Button variant="contained" color="warning" onClick={handleRestore}>
            Restore Backup
          </Button>
        </DialogActions>
      </Dialog>
    </Dialog>
  );
};

export default TraefikConfigViewer;
