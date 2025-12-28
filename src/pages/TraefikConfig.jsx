import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  IconButton,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Paper,
  Grid,
  Divider,
  Switch,
  FormControlLabel,
  Checkbox,
  ListItemText,
  OutlinedInput,
  Box as MuiBox,
} from '@mui/material';
import {
  Security as SecurityIcon,
  Route as RouteIcon,
  Settings as SettingsIcon,
  Backup as BackupIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  FilterList as FilterListIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Code as CodeIcon,
  Close as CloseIcon,
  SaveAlt as SaveAltIcon,
  Restore as RestoreIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

const TraefikConfig = () => {
  const { currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState(0);

  // Global state
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

  // Auto-refresh every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (activeTab === 0) {
        fetchCertificates();
        fetchAcmeStatus();
      }
      if (activeTab === 1) fetchRoutes();
      if (activeTab === 2) fetchServicesTab();
      if (activeTab === 3) fetchMiddleware();
      if (activeTab === 4) fetchConfig();
    }, 60000);

    return () => clearInterval(interval);
  }, [activeTab]);

  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  // ============================================================
  // CERTIFICATES TAB STATE & HANDLERS
  // ============================================================

  const [certificates, setCertificates] = useState([]);
  const [certPage, setCertPage] = useState(0);
  const [certRowsPerPage, setCertRowsPerPage] = useState(10);
  const [certDialogOpen, setCertDialogOpen] = useState(false);
  const [revokeDialogOpen, setRevokeDialogOpen] = useState(false);
  const [selectedCert, setSelectedCert] = useState(null);
  const [newCert, setNewCert] = useState({ domain: '', email: '' });
  const [acmeStatus, setAcmeStatus] = useState(null);

  useEffect(() => {
    if (activeTab === 0) {
      fetchCertificates();
      fetchAcmeStatus();
    }
  }, [activeTab]);

  const fetchCertificates = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/traefik/certificates', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch certificates');

      const data = await response.json();
      setCertificates(data.certificates || []);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAcmeStatus = async () => {
    try {
      const response = await fetch('/api/v1/traefik/acme/status', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch ACME status');

      const data = await response.json();
      setAcmeStatus(data);
    } catch (err) {
      console.error('Failed to fetch ACME status:', err);
      setAcmeStatus(null);
    }
  };

  const handleRequestCertificate = async () => {
    try {
      const response = await fetch('/api/v1/traefik/certificates', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify(newCert),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to request certificate');
      }

      showToast('Certificate requested successfully');
      setCertDialogOpen(false);
      setNewCert({ domain: '', email: '' });
      fetchCertificates();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleRevokeCertificate = async () => {
    if (!selectedCert) return;

    try {
      const response = await fetch(`/api/v1/traefik/certificates/${selectedCert.domain}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to revoke certificate');

      showToast('Certificate revoked successfully');
      setRevokeDialogOpen(false);
      setSelectedCert(null);
      fetchCertificates();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const getCertStatus = (cert) => {
    const expiryDate = new Date(cert.expiry);
    const now = new Date();
    const daysUntilExpiry = Math.floor((expiryDate - now) / (1000 * 60 * 60 * 24));

    if (daysUntilExpiry < 0) return { label: 'Expired', color: 'error', icon: <ErrorIcon /> };
    if (daysUntilExpiry < 30) return { label: 'Expiring Soon', color: 'warning', icon: <WarningIcon /> };
    return { label: 'Valid', color: 'success', icon: <CheckCircleIcon /> };
  };

  // ============================================================
  // ROUTES TAB STATE & HANDLERS
  // ============================================================

  const [routes, setRoutes] = useState([]);
  const [routePage, setRoutePage] = useState(0);
  const [routeRowsPerPage, setRouteRowsPerPage] = useState(10);
  const [routeDialogOpen, setRouteDialogOpen] = useState(false);
  const [routeEditMode, setRouteEditMode] = useState(false);
  const [routeDeleteDialogOpen, setRouteDeleteDialogOpen] = useState(false);
  const [selectedRoute, setSelectedRoute] = useState(null);
  const [newRoute, setNewRoute] = useState({
    name: '',
    rule: '',
    service: '',
    middleware: []
  });
  const [routeSearchQuery, setRouteSearchQuery] = useState('');
  const [availableServices, setAvailableServices] = useState([]);
  const [availableMiddleware, setAvailableMiddleware] = useState([]);

  useEffect(() => {
    if (activeTab === 1) {
      fetchRoutes();
      fetchServices();
      fetchMiddleware();
    }
  }, [activeTab]);

  const fetchRoutes = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/traefik/routes', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch routes');

      const data = await response.json();
      setRoutes(data.routes || []);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchServices = async () => {
    try {
      const response = await fetch('/api/v1/traefik/services', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch services');

      const data = await response.json();
      setAvailableServices(data.services || []);
    } catch (err) {
      console.error('Failed to fetch services:', err);
    }
  };

  const handleSaveRoute = async () => {
    try {
      const url = routeEditMode
        ? `/api/v1/traefik/routes/${selectedRoute.name}`
        : '/api/v1/traefik/routes';

      const method = routeEditMode ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify(newRoute),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save route');
      }

      showToast(`Route ${routeEditMode ? 'updated' : 'created'} successfully`);
      setRouteDialogOpen(false);
      setRouteEditMode(false);
      setNewRoute({ name: '', rule: '', service: '', middleware: [] });
      fetchRoutes();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleEditRoute = (route) => {
    setSelectedRoute(route);
    setNewRoute({
      name: route.name,
      rule: route.rule,
      service: route.service,
      middleware: route.middleware || []
    });
    setRouteEditMode(true);
    setRouteDialogOpen(true);
  };

  const handleDeleteRoute = async () => {
    if (!selectedRoute) return;

    try {
      const response = await fetch(`/api/v1/traefik/routes/${selectedRoute.name}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to delete route');

      showToast('Route deleted successfully');
      setRouteDeleteDialogOpen(false);
      setSelectedRoute(null);
      fetchRoutes();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const filteredRoutes = routes.filter(route =>
    !routeSearchQuery ||
    route.name?.toLowerCase().includes(routeSearchQuery.toLowerCase()) ||
    route.rule?.toLowerCase().includes(routeSearchQuery.toLowerCase())
  );

  // ============================================================
  // SERVICES TAB STATE & HANDLERS
  // ============================================================

  const [services, setServices] = useState([]);
  const [servicePage, setServicePage] = useState(0);
  const [serviceRowsPerPage, setServiceRowsPerPage] = useState(10);
  const [serviceDialogOpen, setServiceDialogOpen] = useState(false);
  const [serviceEditMode, setServiceEditMode] = useState(false);
  const [serviceDeleteDialogOpen, setServiceDeleteDialogOpen] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [newService, setNewService] = useState({
    name: '',
    url: '',
    healthcheck: false
  });

  // We already have fetchServices() above for populating dropdown
  // But we need a separate one for the services tab to set the main services state

  const fetchServicesTab = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/traefik/services', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch services');

      const data = await response.json();
      setServices(data.services || []);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveService = async () => {
    try {
      const url = serviceEditMode
        ? `/api/v1/traefik/services/${selectedService.name}`
        : '/api/v1/traefik/services';

      const method = serviceEditMode ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify(newService),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save service');
      }

      showToast(`Service ${serviceEditMode ? 'updated' : 'created'} successfully`);
      setServiceDialogOpen(false);
      setServiceEditMode(false);
      setNewService({ name: '', url: '', healthcheck: false });
      fetchServicesTab();
      fetchServices(); // Also refresh the dropdown list
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleEditService = (service) => {
    setSelectedService(service);
    setNewService({
      name: service.name,
      url: service.url,
      healthcheck: service.healthcheck || false
    });
    setServiceEditMode(true);
    setServiceDialogOpen(true);
  };

  const handleDeleteService = async () => {
    if (!selectedService) return;

    try {
      const response = await fetch(`/api/v1/traefik/services/${selectedService.name}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to delete service');

      showToast('Service deleted successfully');
      setServiceDeleteDialogOpen(false);
      setSelectedService(null);
      fetchServicesTab();
      fetchServices(); // Also refresh the dropdown list
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // ============================================================
  // MIDDLEWARE TAB STATE & HANDLERS
  // ============================================================

  const [middleware, setMiddleware] = useState([]);
  const [middlewarePage, setMiddlewarePage] = useState(0);
  const [middlewareRowsPerPage, setMiddlewareRowsPerPage] = useState(10);
  const [middlewareDialogOpen, setMiddlewareDialogOpen] = useState(false);
  const [middlewareEditMode, setMiddlewareEditMode] = useState(false);
  const [middlewareDeleteDialogOpen, setMiddlewareDeleteDialogOpen] = useState(false);
  const [selectedMiddleware, setSelectedMiddleware] = useState(null);
  const [newMiddleware, setNewMiddleware] = useState({
    name: '',
    type: 'basicAuth',
    config: {}
  });

  const middlewareTypes = [
    { value: 'basicAuth', label: 'Basic Auth' },
    { value: 'rateLimit', label: 'Rate Limit' },
    { value: 'redirect', label: 'Redirect' },
    { value: 'compress', label: 'Compress' },
    { value: 'headers', label: 'Headers' },
  ];

  useEffect(() => {
    if (activeTab === 2) fetchServicesTab();
  }, [activeTab]);

  useEffect(() => {
    if (activeTab === 3) fetchMiddleware();
  }, [activeTab]);

  const fetchMiddleware = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/traefik/middlewares', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch middleware');

      const data = await response.json();
      setMiddleware(data.middlewares || []);
      setAvailableMiddleware(data.middlewares || []);
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveMiddleware = async () => {
    try {
      const url = middlewareEditMode
        ? `/api/v1/traefik/middlewares/${selectedMiddleware.name}`
        : '/api/v1/traefik/middlewares';

      const method = middlewareEditMode ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify(newMiddleware),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save middleware');
      }

      showToast(`Middleware ${middlewareEditMode ? 'updated' : 'created'} successfully`);
      setMiddlewareDialogOpen(false);
      setMiddlewareEditMode(false);
      setNewMiddleware({ name: '', type: 'basicAuth', config: {} });
      fetchMiddleware();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleEditMiddleware = (m) => {
    setSelectedMiddleware(m);
    setNewMiddleware({
      name: m.name,
      type: m.type,
      config: m.config || {}
    });
    setMiddlewareEditMode(true);
    setMiddlewareDialogOpen(true);
  };

  const handleDeleteMiddleware = async () => {
    if (!selectedMiddleware) return;

    try {
      const response = await fetch(`/api/v1/traefik/middlewares/${selectedMiddleware.name}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to delete middleware');

      showToast('Middleware deleted successfully');
      setMiddlewareDeleteDialogOpen(false);
      setSelectedMiddleware(null);
      fetchMiddleware();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // ============================================================
  // CONFIGURATION TAB STATE & HANDLERS
  // ============================================================

  const [config, setConfig] = useState('');
  const [configEditing, setConfigEditing] = useState(false);
  const [editedConfig, setEditedConfig] = useState('');
  const [backups, setBackups] = useState([]);
  const [restoreDialogOpen, setRestoreDialogOpen] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState('');

  useEffect(() => {
    if (activeTab === 4) {
      fetchConfig();
      fetchBackups();
    }
  }, [activeTab]);

  const fetchConfig = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/traefik/config', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch config');

      const data = await response.json();
      setConfig(data.config || '');
      setEditedConfig(data.config || '');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchBackups = async () => {
    try {
      const response = await fetch('/api/v1/traefik/backups', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch backups');

      const data = await response.json();
      setBackups(data.backups || []);
    } catch (err) {
      console.error('Failed to fetch backups:', err);
    }
  };

  const handleValidateConfig = async () => {
    try {
      const response = await fetch('/api/v1/traefik/config/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify({ config: editedConfig }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Configuration validation failed');
      }

      showToast('Configuration is valid');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleSaveConfig = async () => {
    try {
      const response = await fetch('/api/v1/traefik/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        credentials: 'include',
        body: JSON.stringify({ config: editedConfig }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save config');
      }

      showToast('Configuration saved successfully');
      setConfig(editedConfig);
      setConfigEditing(false);
      fetchConfig();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleBackupConfig = async () => {
    try {
      const response = await fetch('/api/v1/traefik/config/backup', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to create backup');

      showToast('Backup created successfully');
      fetchBackups();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleRestoreBackup = async () => {
    if (!selectedBackup) return;

    try {
      const response = await fetch(`/api/v1/traefik/config/restore/${selectedBackup}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to restore backup');

      showToast('Configuration restored successfully');
      setRestoreDialogOpen(false);
      setSelectedBackup('');
      fetchConfig();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleReloadTraefik = async () => {
    try {
      const response = await fetch('/api/v1/traefik/config/reload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` },
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to reload Traefik');

      showToast('Traefik reloaded successfully');
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // ============================================================
  // RENDER FUNCTIONS
  // ============================================================

  const renderCertificatesTab = () => (
    <Box>
      {/* Status Card */}
      <Card
        sx={{
          mb: 3,
          background: currentTheme === 'unicorn'
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : 'linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%)',
          color: 'white'
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <SecurityIcon sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  SSL Certificates
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9, mt: 1 }}>
                  {certificates.length} certificates managed
                </Typography>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => setCertDialogOpen(true)}
                sx={{
                  bgcolor: 'rgba(255,255,255,0.2)',
                  '&:hover': { bgcolor: 'rgba(255,255,255,0.3)' }
                }}
              >
                Request Certificate
              </Button>
              <IconButton
                onClick={fetchCertificates}
                sx={{ color: 'white' }}
              >
                <RefreshIcon />
              </IconButton>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Certificates Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Domain</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Expiry Date</TableCell>
                <TableCell>Issuer</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : certificates.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      No certificates found
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                certificates
                  .slice(certPage * certRowsPerPage, certPage * certRowsPerPage + certRowsPerPage)
                  .map((cert, index) => {
                    const status = getCertStatus(cert);
                    return (
                      <TableRow key={index} hover>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 500 }}>
                            {cert.domain}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={status.label}
                            color={status.color}
                            size="small"
                            icon={status.icon}
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(cert.expiry).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {cert.issuer || 'Let\'s Encrypt'}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Tooltip title="Revoke Certificate">
                            <IconButton
                              color="error"
                              size="small"
                              onClick={() => {
                                setSelectedCert(cert);
                                setRevokeDialogOpen(true);
                              }}
                            >
                              <DeleteIcon fontSize="small" />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    );
                  })
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={certificates.length}
          page={certPage}
          onPageChange={(e, newPage) => setCertPage(newPage)}
          rowsPerPage={certRowsPerPage}
          onRowsPerPageChange={(e) => {
            setCertRowsPerPage(parseInt(e.target.value, 10));
            setCertPage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>

      {/* ACME Status Card */}
      {acmeStatus && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
              <Typography variant="h6">
                ACME Status
              </Typography>
              <IconButton onClick={fetchAcmeStatus} size="small">
                <RefreshIcon />
              </IconButton>
            </Box>

            <Grid container spacing={2}>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Provider
                  </Typography>
                  <Typography variant="h6">
                    {acmeStatus.provider || 'Let\'s Encrypt'}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Email
                  </Typography>
                  <Typography variant="h6" sx={{ fontSize: '0.95rem' }}>
                    {acmeStatus.email || 'Not configured'}
                  </Typography>
                </Paper>
              </Grid>
              <Grid item xs={12} md={4}>
                <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Status
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip
                      label={acmeStatus.enabled ? 'Enabled' : 'Disabled'}
                      color={acmeStatus.enabled ? 'success' : 'default'}
                      size="small"
                    />
                  </Box>
                </Paper>
              </Grid>
            </Grid>

            {acmeStatus.last_renewal && (
              <Alert severity="info" sx={{ mt: 2 }}>
                Last renewal: {new Date(acmeStatus.last_renewal).toLocaleString()}
              </Alert>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );

  const renderRoutesTab = () => (
    <Box>
      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setRouteEditMode(false);
              setNewRoute({ name: '', rule: '', service: '', middleware: [] });
              setRouteDialogOpen(true);
            }}
            sx={{
              background: currentTheme === 'unicorn'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
            }}
          >
            Add Route
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchRoutes}
          >
            Refresh
          </Button>
        </Box>

        <TextField
          size="small"
          placeholder="Search routes..."
          value={routeSearchQuery}
          onChange={(e) => setRouteSearchQuery(e.target.value)}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
          }}
          sx={{ minWidth: 300 }}
        />
      </Box>

      {/* Routes Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Rule</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Middleware</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : filteredRoutes.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      {routeSearchQuery ? 'No routes match your search' : 'No routes configured'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredRoutes
                  .slice(routePage * routeRowsPerPage, routePage * routeRowsPerPage + routeRowsPerPage)
                  .map((route, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {route.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'text.secondary' }}
                        >
                          {route.rule}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={route.service} color="primary" size="small" />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {route.middleware?.map((m, i) => (
                            <Chip key={i} label={m} size="small" variant="outlined" />
                          ))}
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit">
                          <IconButton
                            color="primary"
                            size="small"
                            onClick={() => handleEditRoute(route)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            color="error"
                            size="small"
                            onClick={() => {
                              setSelectedRoute(route);
                              setRouteDeleteDialogOpen(true);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={filteredRoutes.length}
          page={routePage}
          onPageChange={(e, newPage) => setRoutePage(newPage)}
          rowsPerPage={routeRowsPerPage}
          onRowsPerPageChange={(e) => {
            setRouteRowsPerPage(parseInt(e.target.value, 10));
            setRoutePage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>
    </Box>
  );

  const renderServicesTab = () => (
    <Box>
      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setServiceEditMode(false);
              setNewService({ name: '', url: '', healthcheck: false });
              setServiceDialogOpen(true);
            }}
            sx={{
              background: currentTheme === 'unicorn'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
            }}
          >
            Add Service
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchServicesTab}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Services Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>URL</TableCell>
                <TableCell>Health Check</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : services.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      No services configured
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                services
                  .slice(servicePage * serviceRowsPerPage, servicePage * serviceRowsPerPage + serviceRowsPerPage)
                  .map((service, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {service.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography
                          variant="body2"
                          sx={{ fontFamily: 'monospace', fontSize: '0.85rem', color: 'text.secondary' }}
                        >
                          {service.url}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={service.healthcheck ? 'Enabled' : 'Disabled'}
                          color={service.healthcheck ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={service.status || 'Unknown'}
                          color={service.status === 'healthy' ? 'success' : service.status === 'unhealthy' ? 'error' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit">
                          <IconButton
                            color="primary"
                            size="small"
                            onClick={() => handleEditService(service)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            color="error"
                            size="small"
                            onClick={() => {
                              setSelectedService(service);
                              setServiceDeleteDialogOpen(true);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={services.length}
          page={servicePage}
          onPageChange={(e, newPage) => setServicePage(newPage)}
          rowsPerPage={serviceRowsPerPage}
          onRowsPerPageChange={(e) => {
            setServiceRowsPerPage(parseInt(e.target.value, 10));
            setServicePage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>
    </Box>
  );

  const renderMiddlewareTab = () => (
    <Box>
      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setMiddlewareEditMode(false);
              setNewMiddleware({ name: '', type: 'basicAuth', config: {} });
              setMiddlewareDialogOpen(true);
            }}
            sx={{
              background: currentTheme === 'unicorn'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
            }}
          >
            Add Middleware
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchMiddleware}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Middleware Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 8 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              ) : middleware.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      No middleware configured
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                middleware
                  .slice(middlewarePage * middlewareRowsPerPage, middlewarePage * middlewareRowsPerPage + middlewareRowsPerPage)
                  .map((m, index) => (
                    <TableRow key={index} hover>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>
                          {m.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={middlewareTypes.find(t => t.value === m.type)?.label || m.type}
                          color="primary"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={m.enabled !== false ? 'Active' : 'Disabled'}
                          color={m.enabled !== false ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell align="right">
                        <Tooltip title="Edit">
                          <IconButton
                            color="primary"
                            size="small"
                            onClick={() => handleEditMiddleware(m)}
                          >
                            <EditIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            color="error"
                            size="small"
                            onClick={() => {
                              setSelectedMiddleware(m);
                              setMiddlewareDeleteDialogOpen(true);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={middleware.length}
          page={middlewarePage}
          onPageChange={(e, newPage) => setMiddlewarePage(newPage)}
          rowsPerPage={middlewareRowsPerPage}
          onRowsPerPageChange={(e) => {
            setMiddlewareRowsPerPage(parseInt(e.target.value, 10));
            setMiddlewarePage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>
    </Box>
  );

  const renderConfigTab = () => (
    <Box>
      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {configEditing ? (
            <>
              <Button
                variant="contained"
                color="primary"
                startIcon={<SaveAltIcon />}
                onClick={handleSaveConfig}
              >
                Save
              </Button>
              <Button
                variant="outlined"
                onClick={handleValidateConfig}
              >
                Validate
              </Button>
              <Button
                variant="outlined"
                onClick={() => {
                  setEditedConfig(config);
                  setConfigEditing(false);
                }}
              >
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button
                variant="contained"
                startIcon={<EditIcon />}
                onClick={() => setConfigEditing(true)}
                sx={{
                  background: currentTheme === 'unicorn'
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
                }}
              >
                Edit Config
              </Button>
              <Button
                variant="outlined"
                startIcon={<BackupIcon />}
                onClick={handleBackupConfig}
              >
                Backup
              </Button>
              <Button
                variant="outlined"
                startIcon={<RestoreIcon />}
                onClick={() => setRestoreDialogOpen(true)}
                disabled={backups.length === 0}
              >
                Restore
              </Button>
              <Button
                variant="outlined"
                color="warning"
                startIcon={<RefreshIcon />}
                onClick={handleReloadTraefik}
              >
                Reload Traefik
              </Button>
            </>
          )}
        </Box>
      </Box>

      {/* Config Display */}
      <Card>
        <CardContent>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
              <CircularProgress />
            </Box>
          ) : configEditing ? (
            <TextField
              fullWidth
              multiline
              rows={20}
              value={editedConfig}
              onChange={(e) => setEditedConfig(e.target.value)}
              variant="outlined"
              sx={{
                '& .MuiInputBase-input': {
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                }
              }}
            />
          ) : (
            <Paper
              sx={{
                p: 2,
                bgcolor: 'grey.900',
                color: 'grey.100',
                fontFamily: 'monospace',
                fontSize: '0.9rem',
                whiteSpace: 'pre-wrap',
                overflowX: 'auto',
                maxHeight: '600px',
                overflowY: 'auto'
              }}
            >
              {config || 'No configuration available'}
            </Paper>
          )}
        </CardContent>
      </Card>

      {/* Recent Backups */}
      {!configEditing && backups.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Recent Backups
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {backups.slice(0, 5).map((backup, index) => (
                <Box
                  key={index}
                  sx={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    p: 1,
                    bgcolor: 'action.hover',
                    borderRadius: 1
                  }}
                >
                  <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                    {backup}
                  </Typography>
                  <Button
                    size="small"
                    startIcon={<RestoreIcon />}
                    onClick={() => {
                      setSelectedBackup(backup);
                      setRestoreDialogOpen(true);
                    }}
                  >
                    Restore
                  </Button>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );

  // ============================================================
  // MAIN RENDER
  // ============================================================

  return (
    <Box sx={{ p: 3 }}>
      {/* Page Header */}
      <Typography variant="h4" sx={{ mb: 1, fontWeight: 'bold' }}>
        Traefik Configuration
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage SSL certificates, routes, middleware, and configuration
      </Typography>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, val) => setActiveTab(val)}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              minHeight: 64,
              textTransform: 'none',
            }
          }}
        >
          <Tab
            icon={<SecurityIcon />}
            label="SSL Certificates"
            iconPosition="start"
          />
          <Tab
            icon={<RouteIcon />}
            label="Routes"
            iconPosition="start"
          />
          <Tab
            icon={<CodeIcon />}
            label="Services"
            iconPosition="start"
          />
          <Tab
            icon={<SettingsIcon />}
            label="Middleware"
            iconPosition="start"
          />
          <Tab
            icon={<BackupIcon />}
            label="Configuration"
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box sx={{ mt: 3 }}>
        {activeTab === 0 && renderCertificatesTab()}
        {activeTab === 1 && renderRoutesTab()}
        {activeTab === 2 && renderServicesTab()}
        {activeTab === 3 && renderMiddlewareTab()}
        {activeTab === 4 && renderConfigTab()}
      </Box>

      {/* ============================================================ */}
      {/* DIALOGS */}
      {/* ============================================================ */}

      {/* Request Certificate Dialog */}
      <Dialog
        open={certDialogOpen}
        onClose={() => setCertDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Request SSL Certificate</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
            <TextField
              label="Domain"
              value={newCert.domain}
              onChange={(e) => setNewCert({ ...newCert, domain: e.target.value })}
              placeholder="example.com"
              fullWidth
              required
              helperText="Domain name for the certificate"
            />
            <TextField
              label="Email"
              type="email"
              value={newCert.email}
              onChange={(e) => setNewCert({ ...newCert, email: e.target.value })}
              placeholder="admin@example.com"
              fullWidth
              required
              helperText="Contact email for certificate renewal notifications"
            />
            <Alert severity="info">
              Certificate will be requested from Let's Encrypt. Make sure the domain DNS is properly configured.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCertDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleRequestCertificate}
            variant="contained"
            disabled={!newCert.domain || !newCert.email}
          >
            Request Certificate
          </Button>
        </DialogActions>
      </Dialog>

      {/* Revoke Certificate Dialog */}
      <Dialog
        open={revokeDialogOpen}
        onClose={() => setRevokeDialogOpen(false)}
        maxWidth="xs"
      >
        <DialogTitle>Revoke Certificate</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action cannot be undone!
          </Alert>
          <Typography>
            Are you sure you want to revoke the certificate for <strong>{selectedCert?.domain}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRevokeDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleRevokeCertificate}
            variant="contained"
            color="error"
          >
            Revoke
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add/Edit Route Dialog */}
      <Dialog
        open={routeDialogOpen}
        onClose={() => setRouteDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{routeEditMode ? 'Edit Route' : 'Add Route'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <TextField
              label="Name"
              value={newRoute.name}
              onChange={(e) => setNewRoute({ ...newRoute, name: e.target.value })}
              placeholder="my-route"
              fullWidth
              required
              disabled={routeEditMode}
              helperText="Unique identifier for this route"
            />

            <TextField
              label="Rule"
              value={newRoute.rule}
              onChange={(e) => setNewRoute({ ...newRoute, rule: e.target.value })}
              placeholder="Host(`example.com`)"
              fullWidth
              required
              helperText='Examples: Host(`example.com`), PathPrefix(`/api`), Host(`example.com`) && PathPrefix(`/api`)'
              multiline
              rows={2}
            />

            <FormControl fullWidth>
              <InputLabel>Service</InputLabel>
              <Select
                value={newRoute.service}
                onChange={(e) => setNewRoute({ ...newRoute, service: e.target.value })}
                label="Service"
              >
                {availableServices.map(service => (
                  <MenuItem key={service} value={service}>
                    {service}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Middleware (optional)</InputLabel>
              <Select
                multiple
                value={newRoute.middleware}
                onChange={(e) => setNewRoute({ ...newRoute, middleware: e.target.value })}
                input={<OutlinedInput label="Middleware (optional)" />}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} size="small" />
                    ))}
                  </Box>
                )}
              >
                {availableMiddleware.map((m) => (
                  <MenuItem key={m.name} value={m.name}>
                    <Checkbox checked={newRoute.middleware.indexOf(m.name) > -1} />
                    <ListItemText primary={m.name} />
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRouteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveRoute}
            variant="contained"
            disabled={!newRoute.name || !newRoute.rule || !newRoute.service}
          >
            {routeEditMode ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Route Dialog */}
      <Dialog
        open={routeDeleteDialogOpen}
        onClose={() => setRouteDeleteDialogOpen(false)}
        maxWidth="xs"
      >
        <DialogTitle>Delete Route</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the route <strong>{selectedRoute?.name}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRouteDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteRoute}
            variant="contained"
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add/Edit Service Dialog */}
      <Dialog
        open={serviceDialogOpen}
        onClose={() => setServiceDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{serviceEditMode ? 'Edit Service' : 'Add Service'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <TextField
              label="Name"
              value={newService.name}
              onChange={(e) => setNewService({ ...newService, name: e.target.value })}
              placeholder="my-service"
              fullWidth
              required
              disabled={serviceEditMode}
              helperText="Unique identifier for this service"
            />

            <TextField
              label="URL"
              value={newService.url}
              onChange={(e) => setNewService({ ...newService, url: e.target.value })}
              placeholder="http://backend:8080"
              fullWidth
              required
              helperText="Backend service URL (e.g., http://container:port)"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={newService.healthcheck}
                  onChange={(e) => setNewService({ ...newService, healthcheck: e.target.checked })}
                />
              }
              label="Enable Health Check"
            />

            <Alert severity="info">
              Services define backend targets that routes can forward traffic to.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setServiceDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveService}
            variant="contained"
            disabled={!newService.name || !newService.url}
          >
            {serviceEditMode ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Service Dialog */}
      <Dialog
        open={serviceDeleteDialogOpen}
        onClose={() => setServiceDeleteDialogOpen(false)}
        maxWidth="xs"
      >
        <DialogTitle>Delete Service</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the service <strong>{selectedService?.name}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setServiceDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteService}
            variant="contained"
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add/Edit Middleware Dialog */}
      <Dialog
        open={middlewareDialogOpen}
        onClose={() => setMiddlewareDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>{middlewareEditMode ? 'Edit Middleware' : 'Add Middleware'}</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 2 }}>
            <TextField
              label="Name"
              value={newMiddleware.name}
              onChange={(e) => setNewMiddleware({ ...newMiddleware, name: e.target.value })}
              placeholder="my-middleware"
              fullWidth
              required
              disabled={middlewareEditMode}
            />

            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={newMiddleware.type}
                onChange={(e) => setNewMiddleware({ ...newMiddleware, type: e.target.value })}
                label="Type"
              >
                {middlewareTypes.map(type => (
                  <MenuItem key={type.value} value={type.value}>
                    {type.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Alert severity="info">
              Configuration for middleware will be managed through the advanced configuration editor.
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMiddlewareDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleSaveMiddleware}
            variant="contained"
            disabled={!newMiddleware.name || !newMiddleware.type}
          >
            {middlewareEditMode ? 'Update' : 'Create'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Middleware Dialog */}
      <Dialog
        open={middlewareDeleteDialogOpen}
        onClose={() => setMiddlewareDeleteDialogOpen(false)}
        maxWidth="xs"
      >
        <DialogTitle>Delete Middleware</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete the middleware <strong>{selectedMiddleware?.name}</strong>?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMiddlewareDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteMiddleware}
            variant="contained"
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Restore Backup Dialog */}
      <Dialog
        open={restoreDialogOpen}
        onClose={() => setRestoreDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Restore Configuration Backup</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 3 }}>
            This will replace the current configuration!
          </Alert>

          <FormControl fullWidth>
            <InputLabel>Select Backup</InputLabel>
            <Select
              value={selectedBackup}
              onChange={(e) => setSelectedBackup(e.target.value)}
              label="Select Backup"
            >
              {backups.map(backup => (
                <MenuItem key={backup} value={backup}>
                  {backup}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRestoreDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleRestoreBackup}
            variant="contained"
            color="warning"
            disabled={!selectedBackup}
          >
            Restore
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

export default TraefikConfig;
