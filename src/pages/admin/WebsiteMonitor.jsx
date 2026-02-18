import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Tooltip,
  Switch,
  FormControlLabel,
  LinearProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip as ChartTooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(LineElement, PointElement, LinearScale, CategoryScale, ChartTooltip, Legend, Filler);
import {
  Language as WebsiteIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Timer as TimerIcon,
  Security as SecurityIcon,
  History as HistoryIcon,
  PlayArrow as CheckNowIcon,
  Search as DiscoverIcon,
  Storage as ServerIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

const WebsiteMonitor = () => {
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState(null);
  const [websites, setWebsites] = useState([]);
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [discoverDialogOpen, setDiscoverDialogOpen] = useState(false);
  const [selectedWebsite, setSelectedWebsite] = useState(null);
  const [websiteHistory, setWebsiteHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [discoveredSites, setDiscoveredSites] = useState([]);
  const [discovering, setDiscovering] = useState(false);
  const [selectedForImport, setSelectedForImport] = useState([]);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    server: 'primary',
    check_interval: 300,
    timeout: 30,
    is_active: true
  });

  const fetchWebsites = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/website-monitor/websites');
      if (!response.ok) throw new Error('Failed to fetch websites');
      const data = await response.json();
      setWebsites(data.websites || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const checkAllWebsites = async () => {
    setChecking(true);
    try {
      const response = await fetch('/api/v1/website-monitor/check-all', {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to check websites');
      await fetchWebsites();
    } catch (err) {
      setError(err.message);
    } finally {
      setChecking(false);
    }
  };

  const checkSingleWebsite = async (websiteId) => {
    try {
      const response = await fetch(`/api/v1/website-monitor/websites/${websiteId}/check`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to check website');
      await fetchWebsites();
    } catch (err) {
      setError(err.message);
    }
  };

  const addWebsite = async () => {
    try {
      const response = await fetch('/api/v1/website-monitor/websites', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!response.ok) throw new Error('Failed to add website');
      setAddDialogOpen(false);
      resetForm();
      await fetchWebsites();
    } catch (err) {
      setError(err.message);
    }
  };

  const updateWebsite = async () => {
    try {
      const response = await fetch(`/api/v1/website-monitor/websites/${selectedWebsite.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!response.ok) throw new Error('Failed to update website');
      setEditDialogOpen(false);
      resetForm();
      await fetchWebsites();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteWebsite = async (websiteId) => {
    if (!window.confirm('Are you sure you want to delete this website?')) return;
    try {
      const response = await fetch(`/api/v1/website-monitor/websites/${websiteId}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete website');
      await fetchWebsites();
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchHistory = async (websiteId) => {
    setHistoryLoading(true);
    try {
      const response = await fetch(`/api/v1/website-monitor/websites/${websiteId}/history?limit=50`);
      if (!response.ok) throw new Error('Failed to fetch history');
      const data = await response.json();
      setWebsiteHistory(data.checks || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setHistoryLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      url: '',
      server: 'primary',
      check_interval: 300,
      timeout: 30,
      is_active: true
    });
    setSelectedWebsite(null);
  };

  const discoverWebsites = async () => {
    setDiscovering(true);
    try {
      const response = await fetch('/api/v1/website-monitor/discover');
      if (!response.ok) throw new Error('Failed to discover websites');
      const data = await response.json();
      setDiscoveredSites(data.discovered || []);
      setSelectedForImport([]);
      setDiscoverDialogOpen(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setDiscovering(false);
    }
  };

  const importSelectedWebsites = async () => {
    if (selectedForImport.length === 0) return;

    try {
      const websitesToAdd = discoveredSites
        .filter((_, idx) => selectedForImport.includes(idx))
        .map(site => ({
          name: site.name,
          url: site.url,
          server: site.server,
          check_interval: 300,
          timeout: 30,
          expected_status: 200,
          notify_on_down: true
        }));

      const response = await fetch('/api/v1/website-monitor/bulk-add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(websitesToAdd)
      });

      if (!response.ok) throw new Error('Failed to import websites');

      const result = await response.json();
      setDiscoverDialogOpen(false);
      setSelectedForImport([]);
      await fetchWebsites();

      // Show success message
      alert(`Added ${result.added} websites. ${result.skipped} skipped (already exist).`);
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleSiteSelection = (idx) => {
    setSelectedForImport(prev =>
      prev.includes(idx)
        ? prev.filter(i => i !== idx)
        : [...prev, idx]
    );
  };

  const selectAllSites = () => {
    if (selectedForImport.length === discoveredSites.length) {
      setSelectedForImport([]);
    } else {
      setSelectedForImport(discoveredSites.map((_, idx) => idx));
    }
  };

  const openEditDialog = (website) => {
    setSelectedWebsite(website);
    setFormData({
      name: website.name,
      url: website.url,
      server: website.server || 'primary',
      check_interval: website.check_interval,
      timeout: website.timeout,
      is_active: website.is_active
    });
    setEditDialogOpen(true);
  };

  const openHistoryDialog = (website) => {
    setSelectedWebsite(website);
    setHistoryDialogOpen(true);
    fetchHistory(website.id);
  };

  useEffect(() => {
    fetchWebsites();
  }, [fetchWebsites]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'up':
        return <CheckCircleIcon sx={{ color: 'success.main' }} />;
      case 'down':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      case 'degraded':
        return <WarningIcon sx={{ color: 'warning.main' }} />;
      default:
        return <WarningIcon sx={{ color: 'text.secondary' }} />;
    }
  };

  const getStatusChip = (status) => {
    const config = {
      up: { color: 'success', label: 'Up' },
      down: { color: 'error', label: 'Down' },
      degraded: { color: 'warning', label: 'Degraded' },
      unknown: { color: 'default', label: 'Unknown' }
    };
    const { color, label } = config[status] || config.unknown;
    return <Chip size="small" color={color} label={label} />;
  };

  const formatResponseTime = (ms) => {
    if (ms === null || ms === undefined) return '-';
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  };

  const formatLastCheck = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const getUptimeColor = (uptime) => {
    if (uptime >= 99) return 'success.main';
    if (uptime >= 95) return 'warning.main';
    return 'error.main';
  };

  // Stats calculation
  const stats = {
    total: websites.length,
    up: websites.filter(w => w.status === 'up').length,
    down: websites.filter(w => w.status === 'down').length,
    avgResponseTime: websites.length > 0
      ? Math.round(websites.reduce((sum, w) => sum + (w.response_time || 0), 0) / websites.length)
      : 0
  };

  const StatCard = ({ title, value, icon: Icon, color = 'primary' }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography color="textSecondary" variant="body2" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
              {value}
            </Typography>
          </Box>
          <Box
            sx={{
              bgcolor: `${color}.lighter`,
              borderRadius: 2,
              p: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <Icon sx={{ color: `${color}.main`, fontSize: 28 }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  if (loading && websites.length === 0) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="Website Monitor"
        subtitle="Monitor website uptime and response times"
        actions={(
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<DiscoverIcon />}
              onClick={discoverWebsites}
              disabled={discovering}
              color="secondary"
            >
              {discovering ? 'Discovering...' : 'Discover Sites'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={checkAllWebsites}
              disabled={checking}
            >
              {checking ? 'Checking...' : 'Check All'}
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setAddDialogOpen(true)}
            >
              Add Website
            </Button>
          </Box>
        )}
      />

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {checking && <LinearProgress sx={{ mb: 2 }} />}

      {/* Stats */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Total Websites" value={stats.total} icon={WebsiteIcon} color="primary" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Websites Up" value={stats.up} icon={CheckCircleIcon} color="success" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard title="Websites Down" value={stats.down} icon={ErrorIcon} color="error" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Avg Response Time"
            value={formatResponseTime(stats.avgResponseTime)}
            icon={TimerIcon}
            color="info"
          />
        </Grid>
      </Grid>

      {/* Websites Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <WebsiteIcon />
            Monitored Websites
          </Typography>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Status</TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>Server</TableCell>
                  <TableCell>URL</TableCell>
                  <TableCell align="right">Response Time</TableCell>
                  <TableCell align="right">Uptime</TableCell>
                  <TableCell>SSL</TableCell>
                  <TableCell>Last Check</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {websites.map((website) => (
                  <TableRow key={website.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {getStatusIcon(website.status)}
                        {getStatusChip(website.status)}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {website.name}
                      </Typography>
                      {!website.is_active && (
                        <Chip label="Paused" size="small" sx={{ ml: 1 }} />
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={<ServerIcon sx={{ fontSize: 14 }} />}
                        label={website.server || 'primary'}
                        size="small"
                        variant="outlined"
                        color="info"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={website.url}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace', maxWidth: 250 }}
                        component="a"
                        href={website.url}
                        target="_blank"
                        clickable
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 'bold',
                          color: website.response_time > 2000 ? 'warning.main' : 'text.primary'
                        }}
                      >
                        {formatResponseTime(website.response_time)}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography
                        variant="body2"
                        sx={{
                          fontWeight: 'bold',
                          color: getUptimeColor(website.uptime_percentage || 100)
                        }}
                      >
                        {website.uptime_percentage?.toFixed(2) || '100.00'}%
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {website.ssl_valid !== null && (
                        <Tooltip title={website.ssl_expiry ? `Expires: ${website.ssl_expiry}` : ''}>
                          <SecurityIcon
                            sx={{
                              color: website.ssl_valid ? 'success.main' : 'error.main',
                              fontSize: 20
                            }}
                          />
                        </Tooltip>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption" color="textSecondary">
                        {formatLastCheck(website.last_check)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Box sx={{ display: 'flex', gap: 0.5, justifyContent: 'center' }}>
                        <Tooltip title="Check Now">
                          <IconButton
                            size="small"
                            onClick={() => checkSingleWebsite(website.id)}
                          >
                            <CheckNowIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="History">
                          <IconButton
                            size="small"
                            onClick={() => openHistoryDialog(website)}
                          >
                            <HistoryIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Edit">
                          <IconButton
                            size="small"
                            onClick={() => openEditDialog(website)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => deleteWebsite(website.id)}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
                {websites.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                      <Typography color="textSecondary" gutterBottom>
                        No websites configured. Add a website to start monitoring.
                      </Typography>
                      <Button
                        variant="outlined"
                        startIcon={<DiscoverIcon />}
                        onClick={discoverWebsites}
                        sx={{ mt: 1 }}
                      >
                        Discover Local Sites
                      </Button>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Add Website Dialog */}
      <Dialog open={addDialogOpen} onClose={() => { setAddDialogOpen(false); resetForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Add Website</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
              placeholder="My Website"
            />
            <TextField
              label="URL"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              fullWidth
              placeholder="https://example.com"
            />
            <TextField
              label="Server"
              value={formData.server}
              onChange={(e) => setFormData({ ...formData, server: e.target.value })}
              fullWidth
              placeholder="primary"
              helperText="Identifier for the server hosting this website"
            />
            <FormControl fullWidth>
              <InputLabel>Check Interval</InputLabel>
              <Select
                value={formData.check_interval}
                onChange={(e) => setFormData({ ...formData, check_interval: e.target.value })}
                label="Check Interval"
              >
                <MenuItem value={60}>1 minute</MenuItem>
                <MenuItem value={300}>5 minutes</MenuItem>
                <MenuItem value={600}>10 minutes</MenuItem>
                <MenuItem value={1800}>30 minutes</MenuItem>
                <MenuItem value={3600}>1 hour</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Timeout (seconds)"
              type="number"
              value={formData.timeout}
              onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
              fullWidth
              inputProps={{ min: 5, max: 120 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setAddDialogOpen(false); resetForm(); }}>Cancel</Button>
          <Button onClick={addWebsite} variant="contained" disabled={!formData.name || !formData.url}>
            Add Website
          </Button>
        </DialogActions>
      </Dialog>

      {/* Edit Website Dialog */}
      <Dialog open={editDialogOpen} onClose={() => { setEditDialogOpen(false); resetForm(); }} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Website</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              label="Name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              fullWidth
            />
            <TextField
              label="URL"
              value={formData.url}
              onChange={(e) => setFormData({ ...formData, url: e.target.value })}
              fullWidth
            />
            <TextField
              label="Server"
              value={formData.server}
              onChange={(e) => setFormData({ ...formData, server: e.target.value })}
              fullWidth
              placeholder="primary"
              helperText="Identifier for the server hosting this website"
            />
            <FormControl fullWidth>
              <InputLabel>Check Interval</InputLabel>
              <Select
                value={formData.check_interval}
                onChange={(e) => setFormData({ ...formData, check_interval: e.target.value })}
                label="Check Interval"
              >
                <MenuItem value={60}>1 minute</MenuItem>
                <MenuItem value={300}>5 minutes</MenuItem>
                <MenuItem value={600}>10 minutes</MenuItem>
                <MenuItem value={1800}>30 minutes</MenuItem>
                <MenuItem value={3600}>1 hour</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Timeout (seconds)"
              type="number"
              value={formData.timeout}
              onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) })}
              fullWidth
              inputProps={{ min: 5, max: 120 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={formData.is_active}
                  onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                />
              }
              label="Active"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setEditDialogOpen(false); resetForm(); }}>Cancel</Button>
          <Button onClick={updateWebsite} variant="contained" disabled={!formData.name || !formData.url}>
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Discover Dialog */}
      <Dialog open={discoverDialogOpen} onClose={() => setDiscoverDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DiscoverIcon />
            Discovered Websites ({discoveredSites.length})
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            Select the websites you want to add to monitoring. These were discovered from your local server configuration.
          </Typography>
          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={selectedForImport.length === discoveredSites.length && discoveredSites.length > 0}
                  onChange={selectAllSites}
                />
              }
              label={`Select All (${selectedForImport.length}/${discoveredSites.length})`}
            />
          </Box>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell padding="checkbox"></TableCell>
                  <TableCell>Name</TableCell>
                  <TableCell>URL</TableCell>
                  <TableCell>Server</TableCell>
                  <TableCell>Source</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {discoveredSites.map((site, idx) => (
                  <TableRow
                    key={idx}
                    hover
                    onClick={() => toggleSiteSelection(idx)}
                    sx={{ cursor: 'pointer' }}
                    selected={selectedForImport.includes(idx)}
                  >
                    <TableCell padding="checkbox">
                      <Switch
                        checked={selectedForImport.includes(idx)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                        {site.name}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={site.url}
                        size="small"
                        variant="outlined"
                        sx={{ fontFamily: 'monospace', maxWidth: 300 }}
                        component="a"
                        href={site.url}
                        target="_blank"
                        clickable
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={<ServerIcon sx={{ fontSize: 14 }} />}
                        label={site.server}
                        size="small"
                        variant="outlined"
                        color="info"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={site.source}
                        size="small"
                        color={site.source === 'traefik-labels' ? 'primary' : 'default'}
                      />
                    </TableCell>
                  </TableRow>
                ))}
                {discoveredSites.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                      <Typography color="textSecondary">
                        No websites discovered
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDiscoverDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={importSelectedWebsites}
            variant="contained"
            disabled={selectedForImport.length === 0}
            startIcon={<AddIcon />}
          >
            Add {selectedForImport.length} Website{selectedForImport.length !== 1 ? 's' : ''}
          </Button>
        </DialogActions>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={historyDialogOpen} onClose={() => setHistoryDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Check History - {selectedWebsite?.name}
        </DialogTitle>
        <DialogContent>
          {historyLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              {/* Response Time Chart */}
              {websiteHistory.length > 0 && (
                <Box sx={{ mb: 3, mt: 1 }}>
                  <Typography variant="subtitle2" color="textSecondary" gutterBottom>
                    Response Time History
                  </Typography>
                  <Paper variant="outlined" sx={{ p: 2 }}>
                    <Line
                      data={{
                        labels: websiteHistory
                          .slice()
                          .reverse()
                          .map(h => new Date(h.checked_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })),
                        datasets: [{
                          label: 'Response Time (ms)',
                          data: websiteHistory
                            .slice()
                            .reverse()
                            .map(h => h.response_time || 0),
                          borderColor: 'rgb(75, 192, 192)',
                          backgroundColor: 'rgba(75, 192, 192, 0.1)',
                          tension: 0.3,
                          fill: true,
                          pointBackgroundColor: websiteHistory
                            .slice()
                            .reverse()
                            .map(h => h.is_up ? 'rgb(76, 175, 80)' : 'rgb(244, 67, 54)'),
                          pointBorderColor: websiteHistory
                            .slice()
                            .reverse()
                            .map(h => h.is_up ? 'rgb(76, 175, 80)' : 'rgb(244, 67, 54)'),
                          pointRadius: 4,
                          pointHoverRadius: 6
                        }]
                      }}
                      options={{
                        responsive: true,
                        maintainAspectRatio: true,
                        aspectRatio: 2.5,
                        plugins: {
                          legend: {
                            display: false
                          },
                          tooltip: {
                            callbacks: {
                              label: (context) => {
                                const idx = context.dataIndex;
                                const historyItem = websiteHistory.slice().reverse()[idx];
                                const status = historyItem?.is_up ? 'Up' : 'Down';
                                return `${context.parsed.y}ms (${status})`;
                              }
                            }
                          }
                        },
                        scales: {
                          y: {
                            beginAtZero: true,
                            title: {
                              display: true,
                              text: 'Response Time (ms)'
                            }
                          },
                          x: {
                            title: {
                              display: true,
                              text: 'Time'
                            }
                          }
                        }
                      }}
                    />
                  </Paper>
                  <Box sx={{ display: 'flex', gap: 2, mt: 1, justifyContent: 'center' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'rgb(76, 175, 80)' }} />
                      <Typography variant="caption" color="textSecondary">Up</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: 'rgb(244, 67, 54)' }} />
                      <Typography variant="caption" color="textSecondary">Down</Typography>
                    </Box>
                  </Box>
                </Box>
              )}

              {/* History Table */}
              <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Timestamp</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell align="right">Response Time</TableCell>
                    <TableCell align="right">Status Code</TableCell>
                    <TableCell>Error</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {websiteHistory.map((check, idx) => (
                    <TableRow key={idx}>
                      <TableCell>
                        <Typography variant="caption">
                          {new Date(check.checked_at).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {check.is_up ? (
                          <Chip size="small" color="success" label="Up" />
                        ) : (
                          <Chip size="small" color="error" label="Down" />
                        )}
                      </TableCell>
                      <TableCell align="right">
                        {formatResponseTime(check.response_time)}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          size="small"
                          label={check.status_code || '-'}
                          color={check.status_code >= 200 && check.status_code < 400 ? 'success' : 'error'}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        {check.error_message && (
                          <Typography variant="caption" color="error">
                            {check.error_message}
                          </Typography>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                  {websiteHistory.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={5} align="center" sx={{ py: 3 }}>
                        <Typography color="textSecondary">
                          No check history available
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default WebsiteMonitor;
