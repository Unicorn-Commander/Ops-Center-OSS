/**
 * Federation Settings Page
 * Admin interface for configuring federation between UC-Cloud nodes.
 *
 * Features:
 * - Node identity configuration (ID, display name, public URL, roles)
 * - Branding & theme configuration with live preview
 * - Security settings (federation key, heartbeat)
 * - Peer node management (add, remove, test connections)
 * - Advertised services discovery and toggling
 * - Detected hardware display (GPUs, CPU, RAM)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  TextField,
  Switch,
  FormControlLabel,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Stack,
  Alert,
  CircularProgress,
  Tooltip,
  Divider,
  Radio,
  RadioGroup,
  FormControl,
  FormLabel,
  Checkbox,
  FormGroup,
  Select,
  MenuItem,
  InputLabel,
  InputAdornment,
  Snackbar,
  Paper,
  LinearProgress
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Hub as HubIcon,
  Security as SecurityIcon,
  Palette as PaletteIcon,
  Dns as DnsIcon,
  DeviceHub as DeviceHubIcon,
  Memory as MemoryIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  ContentCopy as CopyIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  NetworkCheck as NetworkCheckIcon,
  Save as SaveIcon,
  Undo as UndoIcon,
  Link as LinkIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Computer as ComputerIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

// API base URL
const API_BASE = '/api/v1/admin/federation';

// Theme options matching ThemeContext
const THEME_OPTIONS = [
  { id: 'dark', name: 'Professional Dark' },
  { id: 'light', name: 'Professional Light' },
  { id: 'unicorn', name: 'Magic Unicorn' },
  { id: 'galaxy', name: 'Unicorn Galaxy' },
  { id: 'underground', name: 'Special Projects' }
];

// Helper: format date
const formatDate = (dateStr) => {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Helper: time ago
const timeAgo = (dateStr) => {
  if (!dateStr) return 'Never';
  const date = new Date(dateStr);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 60) return 'Just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return formatDate(dateStr);
};

/**
 * Node Preview Card - Shows how this node appears to federation peers
 */
const NodePreviewCard = ({ settings }) => {
  const { node_id, display_name, public_url, region, roles, branding } = settings;
  const accentColor = branding?.accent_color || '#7c3aed';
  const logoUrl = branding?.logo_url;
  const companyName = branding?.company_name;

  return (
    <Card
      sx={{
        border: `2px solid ${accentColor}`,
        maxWidth: 300,
        background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(124, 58, 237, 0.1) 100%)'
      }}
    >
      <CardContent>
        <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
          Peer Preview
        </Typography>
        {logoUrl && (
          <Box sx={{ mb: 1 }}>
            <img
              src={logoUrl}
              alt="logo"
              style={{ height: 32, maxWidth: '100%', objectFit: 'contain' }}
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          </Box>
        )}
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          {companyName || display_name || 'Unnamed Node'}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {node_id || 'no-id'} {region ? `\u2022 ${region}` : ''}
        </Typography>
        {public_url && (
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
            {public_url}
          </Typography>
        )}
        <Stack direction="row" spacing={0.5} sx={{ mt: 1, flexWrap: 'wrap', gap: 0.5 }}>
          {(roles || []).map((r) => (
            <Chip key={r} label={r} size="small" color="primary" variant="outlined" />
          ))}
        </Stack>
      </CardContent>
    </Card>
  );
};

/**
 * Add Peer Dialog
 */
const AddPeerDialog = ({ open, onClose, onAdd }) => {
  const [url, setUrl] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [trustLevel, setTrustLevel] = useState('standard');
  const [autoConnect, setAutoConnect] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async () => {
    if (!url.trim()) {
      setError('Peer URL is required');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await onAdd({ url: url.trim(), display_name: displayName.trim(), trust_level: trustLevel, auto_connect: autoConnect });
      setUrl('');
      setDisplayName('');
      setTrustLevel('standard');
      setAutoConnect(true);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Add Peer Node</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="Peer URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            fullWidth
            placeholder="https://peer-node.example.com"
            helperText="The public federation endpoint URL of the peer"
          />
          <TextField
            label="Display Name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            fullWidth
            placeholder="Production Node 2"
            helperText="Optional friendly name for this peer"
          />
          <FormControl fullWidth>
            <InputLabel>Bootstrap Trust Level</InputLabel>
            <Select
              value={trustLevel}
              label="Bootstrap Trust Level"
              onChange={(e) => setTrustLevel(e.target.value)}
            >
              <MenuItem value="full">Full - bootstrap metadata only</MenuItem>
              <MenuItem value="standard">Standard - bootstrap metadata only</MenuItem>
              <MenuItem value="limited">Limited - bootstrap metadata only</MenuItem>
            </Select>
          </FormControl>
          <Alert
            severity="warning"
            action={
              <Button color="inherit" size="small" href="/admin/infra/federation/contracts">
                Contracts
              </Button>
            }
          >
            This field does not govern live federation enforcement. Use Federation Contracts for trust_mode, publish, and consume.
          </Alert>
          <FormControlLabel
            control={
              <Switch
                checked={autoConnect}
                onChange={(e) => setAutoConnect(e.target.checked)}
              />
            }
            label="Auto-connect on startup"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={loading || !url.trim()}
          startIcon={loading ? <CircularProgress size={16} /> : <AddIcon />}
        >
          Add Peer
        </Button>
      </DialogActions>
    </Dialog>
  );
};

/**
 * Rotate Key Confirmation Dialog
 */
const RotateKeyDialog = ({ open, onClose, onConfirm, loading }) => (
  <Dialog open={open} onClose={onClose} maxWidth="sm">
    <DialogTitle>Rotate Federation Key</DialogTitle>
    <DialogContent>
      <Alert severity="warning" sx={{ mt: 1 }}>
        Rotating the federation key will invalidate the current key. All peers will need to
        re-authenticate. This action cannot be undone.
      </Alert>
    </DialogContent>
    <DialogActions>
      <Button onClick={onClose}>Cancel</Button>
      <Button
        variant="contained"
        color="warning"
        onClick={onConfirm}
        disabled={loading}
        startIcon={loading ? <CircularProgress size={16} /> : <SecurityIcon />}
      >
        Rotate Key
      </Button>
    </DialogActions>
  </Dialog>
);

/**
 * Main Federation Settings Component
 */
const FederationSettings = () => {
  // Settings state
  const [settings, setSettings] = useState({
    federation_enabled: false,
    node_id: '',
    display_name: '',
    public_url: '',
    region: '',
    roles: [],
    routing_priority: 'latency',
    is_billing_node: false,
    branding: {
      theme: 'underground',
      logo_url: '',
      company_name: '',
      company_subtitle: '',
      accent_color: '#7c3aed'
    },
    security: {
      federation_key: '',
      heartbeat_interval: 30
    }
  });
  const [originalSettings, setOriginalSettings] = useState(null);

  // Peers state
  const [peers, setPeers] = useState([]);
  const [peersLoading, setPeersLoading] = useState(false);

  // Services state
  const [services, setServices] = useState([]);
  const [servicesLoading, setServicesLoading] = useState(false);

  // Hardware state
  const [hardware, setHardware] = useState(null);
  const [hardwareLoading, setHardwareLoading] = useState(false);

  // UI state
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSection, setExpandedSection] = useState('identity');
  const [showKey, setShowKey] = useState(false);
  const [addPeerOpen, setAddPeerOpen] = useState(false);
  const [rotateKeyOpen, setRotateKeyOpen] = useState(false);
  const [rotatingKey, setRotatingKey] = useState(false);
  const [testingPeer, setTestingPeer] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);

  // Toast
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  // Track changes
  useEffect(() => {
    if (originalSettings) {
      setHasChanges(JSON.stringify(settings) !== JSON.stringify(originalSettings));
    }
  }, [settings, originalSettings]);

  // API helper
  const apiFetch = useCallback(async (endpoint, options = {}) => {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      },
      credentials: 'include'
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(err.detail || `API error: ${response.status}`);
    }
    return response.json();
  }, []);

  // Fetch settings
  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiFetch('/settings');
      setSettings(data);
      setOriginalSettings(JSON.parse(JSON.stringify(data)));
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [apiFetch]);

  // Fetch peers
  const fetchPeers = useCallback(async () => {
    try {
      setPeersLoading(true);
      const data = await apiFetch('/peers');
      setPeers(Array.isArray(data) ? data : data.peers || []);
    } catch (err) {
      console.error('Failed to fetch peers:', err);
    } finally {
      setPeersLoading(false);
    }
  }, [apiFetch]);

  // Fetch services
  const fetchServices = useCallback(async () => {
    try {
      setServicesLoading(true);
      const data = await apiFetch('/services');
      setServices(Array.isArray(data) ? data : data.services || []);
    } catch (err) {
      console.error('Failed to fetch services:', err);
    } finally {
      setServicesLoading(false);
    }
  }, [apiFetch]);

  // Fetch hardware
  const fetchHardware = useCallback(async () => {
    try {
      setHardwareLoading(true);
      const data = await apiFetch('/hardware');
      setHardware(data);
    } catch (err) {
      console.error('Failed to fetch hardware:', err);
    } finally {
      setHardwareLoading(false);
    }
  }, [apiFetch]);

  // Initial load
  useEffect(() => {
    fetchSettings();
    fetchPeers();
    fetchServices();
    fetchHardware();
  }, [fetchSettings, fetchPeers, fetchServices, fetchHardware]);

  // Save settings
  const handleSave = async () => {
    try {
      setSaving(true);
      await apiFetch('/settings', {
        method: 'PUT',
        body: JSON.stringify(settings)
      });
      setOriginalSettings(JSON.parse(JSON.stringify(settings)));
      setHasChanges(false);
      showToast('Federation settings saved successfully');
    } catch (err) {
      showToast(`Failed to save settings: ${err.message}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  // Discard changes
  const handleDiscard = () => {
    if (originalSettings) {
      setSettings(JSON.parse(JSON.stringify(originalSettings)));
      setHasChanges(false);
      showToast('Changes discarded', 'info');
    }
  };

  // Full connectivity test
  const handleTestFederation = async () => {
    try {
      setTesting(true);
      const result = await apiFetch('/test', { method: 'POST' });
      const passed = result.success || result.status === 'ok';
      showToast(
        passed ? 'Federation test passed - all systems operational' : `Federation test: ${result.message || 'Issues detected'}`,
        passed ? 'success' : 'warning'
      );
    } catch (err) {
      showToast(`Federation test failed: ${err.message}`, 'error');
    } finally {
      setTesting(false);
    }
  };

  // Add peer
  const handleAddPeer = async (peerData) => {
    await apiFetch('/peers', {
      method: 'POST',
      body: JSON.stringify(peerData)
    });
    showToast(`Peer ${peerData.display_name || peerData.url} added`);
    fetchPeers();
  };

  // Remove peer
  const handleRemovePeer = async (peerUrl) => {
    try {
      await apiFetch(`/peers/${encodeURIComponent(peerUrl)}`, { method: 'DELETE' });
      showToast('Peer removed');
      fetchPeers();
    } catch (err) {
      showToast(`Failed to remove peer: ${err.message}`, 'error');
    }
  };

  // Test peer
  const handleTestPeer = async (peerUrl) => {
    try {
      setTestingPeer(peerUrl);
      const result = await apiFetch(`/peers/${encodeURIComponent(peerUrl)}/test`, { method: 'POST' });
      const latency = result.latency_ms ? ` (${result.latency_ms}ms)` : '';
      showToast(`Peer connection test ${result.success ? 'passed' : 'failed'}${latency}`, result.success ? 'success' : 'error');
      fetchPeers();
    } catch (err) {
      showToast(`Peer test failed: ${err.message}`, 'error');
    } finally {
      setTestingPeer(null);
    }
  };

  // Rotate key
  const handleRotateKey = async () => {
    try {
      setRotatingKey(true);
      const result = await apiFetch('/key/rotate', { method: 'POST' });
      if (result.key) {
        setSettings((prev) => ({
          ...prev,
          security: { ...prev.security, federation_key: result.key }
        }));
      }
      showToast('Federation key rotated. Update all peers with the new key.');
      setRotateKeyOpen(false);
      fetchSettings();
    } catch (err) {
      showToast(`Failed to rotate key: ${err.message}`, 'error');
    } finally {
      setRotatingKey(false);
    }
  };

  // Toggle service advertisement
  const handleToggleService = async (serviceId, advertised) => {
    try {
      const updated = services.map((s) =>
        s.id === serviceId ? { ...s, advertised } : s
      );
      setServices(updated);
      await apiFetch('/services', {
        method: 'PUT',
        body: JSON.stringify({ services: updated })
      });
      showToast(`Service ${advertised ? 'advertised' : 'hidden'} from federation`);
    } catch (err) {
      showToast(`Failed to update service: ${err.message}`, 'error');
      fetchServices();
    }
  };

  // Re-discover services
  const handleDiscoverServices = async () => {
    try {
      setServicesLoading(true);
      await apiFetch('/discover', { method: 'POST' });
      showToast('Service discovery completed');
      fetchServices();
    } catch (err) {
      showToast(`Service discovery failed: ${err.message}`, 'error');
      setServicesLoading(false);
    }
  };

  // Copy to clipboard
  const handleCopyKey = () => {
    navigator.clipboard.writeText(settings.security?.federation_key || '');
    showToast('Federation key copied to clipboard', 'info');
  };

  // Update settings helper
  const updateSettings = (path, value) => {
    setSettings((prev) => {
      const updated = { ...prev };
      const parts = path.split('.');
      let obj = updated;
      for (let i = 0; i < parts.length - 1; i++) {
        obj[parts[i]] = { ...obj[parts[i]] };
        obj = obj[parts[i]];
      }
      obj[parts[parts.length - 1]] = value;
      return updated;
    });
  };

  // Toggle role
  const toggleRole = (role) => {
    const current = settings.roles || [];
    if (current.includes(role)) {
      updateSettings('roles', current.filter((r) => r !== role));
    } else {
      updateSettings('roles', [...current, role]);
    }
  };

  // Peer status helpers
  const getStatusChip = (status) => {
    const statusMap = {
      online: { color: 'success', label: 'Online' },
      degraded: { color: 'warning', label: 'Degraded' },
      offline: { color: 'error', label: 'Offline' },
      unknown: { color: 'default', label: 'Unknown' }
    };
    const config = statusMap[status] || statusMap.unknown;
    return <Chip label={config.label} color={config.color} size="small" sx={{ fontWeight: 600 }} />;
  };

  // URL validation
  const isValidUrl = (str) => {
    if (!str) return true;
    try {
      new URL(str);
      return true;
    } catch {
      return false;
    }
  };

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <PageHeader title="Federation Settings" subtitle="Loading configuration..." />
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Federation Settings"
        subtitle="Configure node identity, peers, and service sharing across your UC-Cloud federation"
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={testing ? <CircularProgress size={16} /> : <NetworkCheckIcon />}
              onClick={handleTestFederation}
              disabled={testing || !settings.federation_enabled}
            >
              Test Federation
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              startIcon={<UndoIcon />}
              onClick={handleDiscard}
              disabled={!hasChanges}
            >
              Discard
            </Button>
            <Button
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} /> : <SaveIcon />}
              onClick={handleSave}
              disabled={saving || !hasChanges}
            >
              Save Settings
            </Button>
          </Stack>
        }
      />

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {hasChanges && (
        <Alert severity="info" sx={{ mb: 2 }}>
          You have unsaved changes. Click "Save Settings" to apply them.
        </Alert>
      )}

      {/* Federation Enabled Toggle */}
      <Card
        sx={{
          mb: 3,
          background: settings.federation_enabled
            ? 'linear-gradient(135deg, rgba(76, 175, 80, 0.05) 0%, rgba(76, 175, 80, 0.1) 100%)'
            : 'linear-gradient(135deg, rgba(158, 158, 158, 0.05) 0%, rgba(158, 158, 158, 0.1) 100%)',
          border: `1px solid ${settings.federation_enabled ? 'rgba(76, 175, 80, 0.3)' : 'rgba(158, 158, 158, 0.3)'}`,
          borderRadius: 2
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <HubIcon sx={{ fontSize: 32, color: settings.federation_enabled ? 'success.main' : 'text.disabled' }} />
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600 }}>
                  Federation {settings.federation_enabled ? 'Enabled' : 'Disabled'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {settings.federation_enabled
                    ? 'This node is participating in the federation network'
                    : 'Enable to share services and connect with peer nodes'}
                </Typography>
              </Box>
            </Box>
            <Switch
              checked={settings.federation_enabled}
              onChange={(e) => updateSettings('federation_enabled', e.target.checked)}
              color="success"
              size="medium"
            />
          </Box>
        </CardContent>
      </Card>

      {/* Section 1: Node Identity */}
      <Accordion
        expanded={expandedSection === 'identity'}
        onChange={() => setExpandedSection(expandedSection === 'identity' ? false : 'identity')}
        sx={{ mb: 1, borderRadius: 2, '&:before': { display: 'none' } }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <DnsIcon color="primary" />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Node Identity</Typography>
              <Typography variant="caption" color="text.secondary">
                Configure how this node identifies itself in the federation
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <TextField
                label="Node ID"
                value={settings.node_id || ''}
                onChange={(e) => updateSettings('node_id', e.target.value)}
                fullWidth
                helperText="Unique identifier. Auto-generated from hostname if empty."
                placeholder="magicunicorn-yoda"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Display Name"
                value={settings.display_name || ''}
                onChange={(e) => updateSettings('display_name', e.target.value)}
                fullWidth
                helperText="Human-readable name shown to peers"
                placeholder="Magic Unicorn HQ"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Public URL"
                value={settings.public_url || ''}
                onChange={(e) => updateSettings('public_url', e.target.value)}
                fullWidth
                error={!isValidUrl(settings.public_url)}
                helperText={
                  !isValidUrl(settings.public_url)
                    ? 'Please enter a valid URL'
                    : 'Publicly accessible URL for this node'
                }
                placeholder="https://magicunicorn.dev"
                InputProps={{
                  startAdornment: <InputAdornment position="start"><LinkIcon /></InputAdornment>
                }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Region"
                value={settings.region || ''}
                onChange={(e) => updateSettings('region', e.target.value)}
                fullWidth
                helperText="Optional geographic region identifier"
                placeholder="us-west-2"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <FormLabel component="legend">Roles</FormLabel>
                <FormGroup row>
                  {['Inference', 'Gateway', 'Billing'].map((role) => (
                    <FormControlLabel
                      key={role}
                      control={
                        <Checkbox
                          checked={(settings.roles || []).includes(role)}
                          onChange={() => toggleRole(role)}
                        />
                      }
                      label={role}
                    />
                  ))}
                </FormGroup>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl component="fieldset">
                <FormLabel component="legend">Routing Priority</FormLabel>
                <RadioGroup
                  row
                  value={settings.routing_priority || 'latency'}
                  onChange={(e) => updateSettings('routing_priority', e.target.value)}
                >
                  <FormControlLabel value="cost" control={<Radio />} label="Cost" />
                  <FormControlLabel value="latency" control={<Radio />} label="Latency" />
                  <FormControlLabel value="quality" control={<Radio />} label="Quality" />
                </RadioGroup>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.is_billing_node || false}
                    onChange={(e) => updateSettings('is_billing_node', e.target.checked)}
                  />
                }
                label="This node is a billing node (handles credit deduction and metering)"
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Section 2: Branding & Theme */}
      <Accordion
        expanded={expandedSection === 'branding'}
        onChange={() => setExpandedSection(expandedSection === 'branding' ? false : 'branding')}
        sx={{ mb: 1, borderRadius: 2, '&:before': { display: 'none' } }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <PaletteIcon color="secondary" />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Branding & Theme</Typography>
              <Typography variant="caption" color="text.secondary">
                Configure how this node appears to federation peers
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Theme</InputLabel>
                    <Select
                      value={settings.branding?.theme || 'underground'}
                      label="Theme"
                      onChange={(e) => updateSettings('branding.theme', e.target.value)}
                    >
                      {THEME_OPTIONS.map((t) => (
                        <MenuItem key={t.id} value={t.id}>{t.name}</MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Accent Color"
                    value={settings.branding?.accent_color || '#7c3aed'}
                    onChange={(e) => updateSettings('branding.accent_color', e.target.value)}
                    fullWidth
                    placeholder="#7c3aed"
                    InputProps={{
                      startAdornment: (
                        <InputAdornment position="start">
                          <Box
                            sx={{
                              width: 20,
                              height: 20,
                              borderRadius: '50%',
                              backgroundColor: settings.branding?.accent_color || '#7c3aed',
                              border: '1px solid rgba(0,0,0,0.2)'
                            }}
                          />
                        </InputAdornment>
                      ),
                      endAdornment: (
                        <InputAdornment position="end">
                          <input
                            type="color"
                            value={settings.branding?.accent_color || '#7c3aed'}
                            onChange={(e) => updateSettings('branding.accent_color', e.target.value)}
                            style={{ width: 28, height: 28, border: 'none', cursor: 'pointer', background: 'transparent' }}
                          />
                        </InputAdornment>
                      )
                    }}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Logo URL"
                    value={settings.branding?.logo_url || ''}
                    onChange={(e) => updateSettings('branding.logo_url', e.target.value)}
                    fullWidth
                    placeholder="https://example.com/logo.png"
                    helperText="URL to your organization logo (displayed to peers)"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Company Name"
                    value={settings.branding?.company_name || ''}
                    onChange={(e) => updateSettings('branding.company_name', e.target.value)}
                    fullWidth
                    placeholder="Magic Unicorn Inc"
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Company Subtitle"
                    value={settings.branding?.company_subtitle || ''}
                    onChange={(e) => updateSettings('branding.company_subtitle', e.target.value)}
                    fullWidth
                    placeholder="AI Infrastructure"
                  />
                </Grid>
              </Grid>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Node Preview</Typography>
              <NodePreviewCard settings={settings} />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Section 3: Security */}
      <Accordion
        expanded={expandedSection === 'security'}
        onChange={() => setExpandedSection(expandedSection === 'security' ? false : 'security')}
        sx={{ mb: 1, borderRadius: 2, '&:before': { display: 'none' } }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <SecurityIcon color="warning" />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Security</Typography>
              <Typography variant="caption" color="text.secondary">
                Federation key, heartbeat, and authentication settings
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="subtitle2" sx={{ mb: 1 }}>Federation Key</Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <TextField
                  value={showKey ? (settings.security?.federation_key || '') : '\u2022'.repeat(40)}
                  fullWidth
                  InputProps={{
                    readOnly: true,
                    sx: { fontFamily: 'monospace', fontSize: '0.85rem' },
                    endAdornment: (
                      <InputAdornment position="end">
                        <Tooltip title={showKey ? 'Hide key' : 'Show key'}>
                          <IconButton onClick={() => setShowKey(!showKey)} size="small">
                            {showKey ? <VisibilityOffIcon /> : <VisibilityIcon />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Copy key">
                          <IconButton onClick={handleCopyKey} size="small">
                            <CopyIcon />
                          </IconButton>
                        </Tooltip>
                      </InputAdornment>
                    )
                  }}
                />
                <Button
                  variant="outlined"
                  color="warning"
                  onClick={() => setRotateKeyOpen(true)}
                  sx={{ whiteSpace: 'nowrap', minWidth: 120 }}
                >
                  Rotate Key
                </Button>
              </Box>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                This key authenticates peer-to-peer communication. Keep it secret.
              </Typography>
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                label="Heartbeat Interval (seconds)"
                type="number"
                value={settings.security?.heartbeat_interval || 30}
                onChange={(e) => updateSettings('security.heartbeat_interval', parseInt(e.target.value, 10) || 30)}
                fullWidth
                inputProps={{ min: 5, max: 300 }}
                helperText="How often to send heartbeat to peers (5-300 seconds)"
              />
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Section 4: Peer Nodes */}
      <Accordion
        expanded={expandedSection === 'peers'}
        onChange={() => setExpandedSection(expandedSection === 'peers' ? false : 'peers')}
        sx={{ mb: 1, borderRadius: 2, '&:before': { display: 'none' } }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <DeviceHubIcon color="info" />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Peer Nodes
                {peers.length > 0 && (
                  <Chip label={peers.length} size="small" sx={{ ml: 1 }} />
                )}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Manage connections to other federation nodes
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Alert
            severity="warning"
            sx={{ mb: 2 }}
            action={
              <Button color="inherit" size="small" href="/admin/infra/federation/contracts">
                Federation Contracts
              </Button>
            }
          >
            Peer trust levels here are connection bootstrap metadata only and do not affect live enforcement.
          </Alert>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              {peers.length === 0 ? 'No peers configured yet' : `${peers.length} peer(s) configured`}
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<RefreshIcon />}
                onClick={fetchPeers}
                disabled={peersLoading}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setAddPeerOpen(true)}
              >
                Add Peer
              </Button>
            </Stack>
          </Box>

          {peersLoading && <LinearProgress sx={{ mb: 2 }} />}

          {peers.length > 0 && (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Status</TableCell>
                    <TableCell>Name / URL</TableCell>
                    <TableCell>Bootstrap Trust</TableCell>
                    <TableCell>Last Seen</TableCell>
                    <TableCell>Latency</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {peers.map((peer) => (
                    <TableRow key={peer.url} hover>
                      <TableCell>{getStatusChip(peer.status || 'unknown')}</TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {peer.display_name || 'Unnamed'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
                          {peer.url}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Tooltip title="Bootstrap metadata only. Enforcement is managed in Federation Contracts.">
                          <Chip
                            label={peer.trust_level || 'standard'}
                            size="small"
                            variant="outlined"
                            color={peer.trust_level === 'full' ? 'success' : peer.trust_level === 'limited' ? 'warning' : 'default'}
                          />
                        </Tooltip>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">{timeAgo(peer.last_seen)}</Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption">
                          {peer.latency_ms != null ? `${peer.latency_ms}ms` : '--'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={0.5} justifyContent="flex-end">
                          <Tooltip title="Test connection">
                            <IconButton
                              size="small"
                              onClick={() => handleTestPeer(peer.url)}
                              disabled={testingPeer === peer.url}
                            >
                              {testingPeer === peer.url ? <CircularProgress size={16} /> : <NetworkCheckIcon />}
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Remove peer">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleRemovePeer(peer.url)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          {peers.length === 0 && !peersLoading && (
            <Paper
              variant="outlined"
              sx={{ p: 4, textAlign: 'center', borderStyle: 'dashed' }}
            >
              <DeviceHubIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No peer nodes configured. Add a peer to start federating.
              </Typography>
            </Paper>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Section 5: Advertised Services */}
      <Accordion
        expanded={expandedSection === 'services'}
        onChange={() => setExpandedSection(expandedSection === 'services' ? false : 'services')}
        sx={{ mb: 1, borderRadius: 2, '&:before': { display: 'none' } }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <SettingsIcon color="action" />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                Advertised Services
                {services.length > 0 && (
                  <Chip label={services.filter((s) => s.advertised).length + '/' + services.length} size="small" sx={{ ml: 1 }} />
                )}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Control which local services are shared with federation peers
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={servicesLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={handleDiscoverServices}
              disabled={servicesLoading}
            >
              Re-discover Services
            </Button>
          </Box>

          {servicesLoading && <LinearProgress sx={{ mb: 2 }} />}

          {services.length > 0 ? (
            <Grid container spacing={2}>
              {services.map((svc) => (
                <Grid item xs={12} md={6} key={svc.id || svc.type}>
                  <Card
                    variant="outlined"
                    sx={{
                      opacity: svc.advertised ? 1 : 0.6,
                      borderColor: svc.advertised ? 'primary.main' : 'divider'
                    }}
                  >
                    <CardContent sx={{ pb: '12px !important' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {svc.display_name || svc.type}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {svc.endpoint || svc.type}
                          </Typography>
                          {svc.models && svc.models.length > 0 && (
                            <Box sx={{ mt: 0.5 }}>
                              {svc.models.slice(0, 3).map((m) => (
                                <Chip key={m} label={m} size="small" sx={{ mr: 0.5, mb: 0.5 }} variant="outlined" />
                              ))}
                              {svc.models.length > 3 && (
                                <Chip label={`+${svc.models.length - 3}`} size="small" variant="outlined" />
                              )}
                            </Box>
                          )}
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Chip
                            label={svc.status || 'unknown'}
                            size="small"
                            color={svc.status === 'running' || svc.status === 'healthy' ? 'success' : svc.status === 'stopped' ? 'error' : 'default'}
                          />
                          <Switch
                            checked={svc.advertised || false}
                            onChange={(e) => handleToggleService(svc.id || svc.type, e.target.checked)}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            !servicesLoading && (
              <Paper
                variant="outlined"
                sx={{ p: 4, textAlign: 'center', borderStyle: 'dashed' }}
              >
                <SettingsIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  No services detected. Click "Re-discover Services" to scan for local services.
                </Typography>
              </Paper>
            )
          )}
        </AccordionDetails>
      </Accordion>

      {/* Section 6: Detected Hardware */}
      <Accordion
        expanded={expandedSection === 'hardware'}
        onChange={() => setExpandedSection(expandedSection === 'hardware' ? false : 'hardware')}
        sx={{ mb: 1, borderRadius: 2, '&:before': { display: 'none' } }}
      >
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <ComputerIcon sx={{ color: 'text.secondary' }} />
            <Box>
              <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>Detected Hardware</Typography>
              <Typography variant="caption" color="text.secondary">
                Hardware inventory advertised to federation peers (read-only)
              </Typography>
            </Box>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ mb: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              size="small"
              startIcon={hardwareLoading ? <CircularProgress size={16} /> : <RefreshIcon />}
              onClick={fetchHardware}
              disabled={hardwareLoading}
            >
              Refresh
            </Button>
          </Box>

          {hardwareLoading && <LinearProgress sx={{ mb: 2 }} />}

          {hardware ? (
            <Grid container spacing={2}>
              {/* GPUs */}
              {hardware.gpus && hardware.gpus.length > 0 && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 1 }}>
                    <MemoryIcon fontSize="small" /> GPUs ({hardware.gpus.length})
                  </Typography>
                  <Grid container spacing={2}>
                    {hardware.gpus.map((gpu, idx) => (
                      <Grid item xs={12} md={6} key={idx}>
                        <Card variant="outlined">
                          <CardContent sx={{ pb: '12px !important' }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                              {gpu.name || `GPU ${idx}`}
                            </Typography>
                            <Stack spacing={0.5} sx={{ mt: 1 }}>
                              {gpu.vram && (
                                <Typography variant="caption" color="text.secondary">
                                  VRAM: {gpu.vram}
                                </Typography>
                              )}
                              {gpu.compute_capability && (
                                <Typography variant="caption" color="text.secondary">
                                  Compute: {gpu.compute_capability}
                                </Typography>
                              )}
                              {gpu.architecture && (
                                <Typography variant="caption" color="text.secondary">
                                  Architecture: {gpu.architecture}
                                </Typography>
                              )}
                              {gpu.memory_used && gpu.memory_total && (
                                <Box>
                                  <LinearProgress
                                    variant="determinate"
                                    value={(parseFloat(gpu.memory_used) / parseFloat(gpu.memory_total)) * 100}
                                    sx={{ height: 6, borderRadius: 3 }}
                                  />
                                  <Typography variant="caption" color="text.secondary">
                                    {gpu.memory_used} / {gpu.memory_total}
                                  </Typography>
                                </Box>
                              )}
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Grid>
              )}

              {/* CPU */}
              {hardware.cpu && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>CPU</Typography>
                  <Card variant="outlined">
                    <CardContent sx={{ pb: '12px !important' }}>
                      <Typography variant="body2">{hardware.cpu.name || 'Unknown CPU'}</Typography>
                      {hardware.cpu.cores && (
                        <Typography variant="caption" color="text.secondary">
                          Cores: {hardware.cpu.cores} {hardware.cpu.threads ? `/ Threads: ${hardware.cpu.threads}` : ''}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* RAM */}
              {hardware.ram && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>Memory</Typography>
                  <Card variant="outlined">
                    <CardContent sx={{ pb: '12px !important' }}>
                      <Typography variant="body2">{hardware.ram.total || 'Unknown'}</Typography>
                      {hardware.ram.speed && (
                        <Typography variant="caption" color="text.secondary">
                          Speed: {hardware.ram.speed}
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              )}

              {/* NPU */}
              {hardware.npu && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>NPU</Typography>
                  <Card variant="outlined">
                    <CardContent sx={{ pb: '12px !important' }}>
                      <Typography variant="body2">{hardware.npu.name || 'Detected'}</Typography>
                      {hardware.npu.tops && (
                        <Typography variant="caption" color="text.secondary">
                          Performance: {hardware.npu.tops} TOPS
                        </Typography>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          ) : (
            !hardwareLoading && (
              <Paper
                variant="outlined"
                sx={{ p: 4, textAlign: 'center', borderStyle: 'dashed' }}
              >
                <ComputerIcon sx={{ fontSize: 48, color: 'text.disabled', mb: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  No hardware information available. Click Refresh to detect hardware.
                </Typography>
              </Paper>
            )
          )}
        </AccordionDetails>
      </Accordion>

      {/* Dialogs */}
      <AddPeerDialog
        open={addPeerOpen}
        onClose={() => setAddPeerOpen(false)}
        onAdd={handleAddPeer}
      />

      <RotateKeyDialog
        open={rotateKeyOpen}
        onClose={() => setRotateKeyOpen(false)}
        onConfirm={handleRotateKey}
        loading={rotatingKey}
      />

      {/* Toast */}
      <Snackbar
        open={toast.open}
        autoHideDuration={4000}
        onClose={() => setToast({ ...toast, open: false })}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          severity={toast.severity}
          onClose={() => setToast({ ...toast, open: false })}
        >
          {toast.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default FederationSettings;
