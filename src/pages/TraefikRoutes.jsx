import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  Menu,
  MenuItem,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  Alert,
  Skeleton,
  Tooltip
} from '@mui/material';
import {
  PlusIcon,
  MagnifyingGlassIcon,
  EllipsisVerticalIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  LockClosedIcon,
  BeakerIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useNavigate, useSearchParams } from 'react-router-dom';
import TraefikRouteEditor from '../components/TraefikRouteEditor';
import { useToast } from '../components/Toast';

const TraefikRoutes = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const toast = useToast();
  const [routes, setRoutes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [retryCount, setRetryCount] = useState({
    loadRoutes: 0,
    deleteRoute: 0,
    testRoute: 0,
    saveRoute: 0
  });

  // Table state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sslFilter, setSSLFilter] = useState('all');

  // Menu state
  const [menuAnchor, setMenuAnchor] = useState(null);
  const [selectedRoute, setSelectedRoute] = useState(null);

  // Editor modal state
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingRoute, setEditingRoute] = useState(null);

  const maxRetries = 3;

  useEffect(() => {
    loadRoutes();

    // Check if we should open the editor
    if (searchParams.get('action') === 'new') {
      setEditorOpen(true);
      setEditingRoute(null);
    }
  }, [searchParams]);

  const loadRoutes = async () => {
    try {
      // NEW: Fetch REAL live routes from Docker labels
      const response = await fetch('/api/v1/traefik/live/routes', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      // Live API returns array directly, not wrapped in object
      setRoutes(Array.isArray(data) ? data : []);
      setError(null);
      setRetryCount(prev => ({ ...prev, loadRoutes: 0 }));
    } catch (err) {
      console.error('Failed to load routes:', err);
      const errorMsg = `Failed to load Traefik routes: ${err.message}`;
      setError(errorMsg);

      // Retry logic with exponential backoff
      if (retryCount.loadRoutes < maxRetries) {
        const backoffDelay = 2000 * (retryCount.loadRoutes + 1);
        toast.warning(`Retrying... (Attempt ${retryCount.loadRoutes + 1}/${maxRetries})`);
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, loadRoutes: prev.loadRoutes + 1 }));
          loadRoutes();
        }, backoffDelay);
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (routeId) => {
    if (!confirm('Are you sure you want to delete this route?')) return;

    try {
      const response = await fetch(`/api/v1/traefik/routes/${routeId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const successMsg = 'Route deleted successfully';
      setSuccess(successMsg);
      toast.success(successMsg);
      setRetryCount(prev => ({ ...prev, deleteRoute: 0 }));
      loadRoutes();
    } catch (err) {
      console.error('Failed to delete route:', err);
      const errorMsg = `Failed to delete route: ${err.message}`;
      setError(errorMsg);

      // Retry logic with exponential backoff
      if (retryCount.deleteRoute < maxRetries) {
        const backoffDelay = 2000 * (retryCount.deleteRoute + 1);
        toast.warning(`Retrying delete... (Attempt ${retryCount.deleteRoute + 1}/${maxRetries})`);
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, deleteRoute: prev.deleteRoute + 1 }));
          handleDelete(routeId);
        }, backoffDelay);
      } else {
        toast.error(errorMsg);
      }
    }
  };

  const handleTest = async (routeId) => {
    try {
      const response = await fetch(`/api/v1/traefik/routes/${routeId}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      const msg = `Route test ${result.success ? 'passed' : 'failed'}: ${result.message}`;

      if (result.success) {
        setSuccess(msg);
        toast.success(msg);
      } else {
        setError(msg);
        toast.warning(msg);
      }

      setRetryCount(prev => ({ ...prev, testRoute: 0 }));
    } catch (err) {
      console.error('Failed to test route:', err);
      const errorMsg = `Failed to test route: ${err.message}`;
      setError(errorMsg);

      // Retry logic with exponential backoff
      if (retryCount.testRoute < maxRetries) {
        const backoffDelay = 2000 * (retryCount.testRoute + 1);
        toast.warning(`Retrying test... (Attempt ${retryCount.testRoute + 1}/${maxRetries})`);
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, testRoute: prev.testRoute + 1 }));
          handleTest(routeId);
        }, backoffDelay);
      } else {
        toast.error(errorMsg);
      }
    }
  };

  const handleMenuOpen = (event, route) => {
    setMenuAnchor(event.currentTarget);
    setSelectedRoute(route);
  };

  const handleMenuClose = () => {
    setMenuAnchor(null);
    setSelectedRoute(null);
  };

  const handleEdit = (route) => {
    setEditingRoute(route);
    setEditorOpen(true);
    handleMenuClose();
  };

  const handleSaveRoute = async (routeData) => {
    try {
      const url = routeData.id
        ? `/api/v1/traefik/routes/${routeData.id}`
        : '/api/v1/traefik/routes';

      const method = routeData.id ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(routeData)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const successMsg = `Route ${routeData.id ? 'updated' : 'created'} successfully`;
      setSuccess(successMsg);
      toast.success(successMsg);
      setRetryCount(prev => ({ ...prev, saveRoute: 0 }));
      setEditorOpen(false);
      setEditingRoute(null);
      loadRoutes();
    } catch (err) {
      console.error('Failed to save route:', err);
      const errorMsg = `Failed to save route: ${err.message}`;
      setError(errorMsg);

      // Retry logic with exponential backoff
      if (retryCount.saveRoute < maxRetries) {
        const backoffDelay = 2000 * (retryCount.saveRoute + 1);
        toast.warning(`Retrying save... (Attempt ${retryCount.saveRoute + 1}/${maxRetries})`);
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, saveRoute: prev.saveRoute + 1 }));
          handleSaveRoute(routeData);
        }, backoffDelay);
      } else {
        toast.error(errorMsg);
      }
    }
  };

  // Filter routes
  const filteredRoutes = routes.filter((route) => {
    const matchesSearch =
      route.domain?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      route.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      route.name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus =
      statusFilter === 'all' ||
      route.status === statusFilter;

    const matchesSSL =
      sslFilter === 'all' ||
      (sslFilter === 'enabled' && route.ssl) ||
      (sslFilter === 'disabled' && !route.ssl);

    return matchesSearch && matchesStatus && matchesSSL;
  });

  // Paginated routes
  const paginatedRoutes = filteredRoutes.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Routes
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage Traefik routing rules
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<PlusIcon style={{ width: 20, height: 20 }} />}
          onClick={() => {
            setEditingRoute(null);
            setEditorOpen(true);
          }}
        >
          Add Route
        </Button>
      </Box>

      {error && (
        <Alert
          severity="error"
          sx={{ mb: 3 }}
          onClose={() => setError(null)}
          action={
            <Button
              color="inherit"
              size="small"
              startIcon={<ArrowPathIcon style={{ width: 16, height: 16 }} />}
              onClick={() => {
                setError(null);
                setRetryCount({ loadRoutes: 0, deleteRoute: 0, testRoute: 0, saveRoute: 0 });
                loadRoutes();
              }}
            >
              Retry Now
            </Button>
          }
        >
          <Box display="flex" alignItems="center" gap={1}>
            <ExclamationTriangleIcon style={{ width: 20, height: 20 }} />
            <span>{error}</span>
          </Box>
          {(retryCount.loadRoutes > 0 || retryCount.deleteRoute > 0 ||
            retryCount.testRoute > 0 || retryCount.saveRoute > 0) &&
            Object.values(retryCount).some(count => count > 0 && count < maxRetries) && (
            <Box mt={1} fontSize="0.875rem">
              Retrying... (Attempt {Math.max(...Object.values(retryCount))}/{maxRetries})
            </Box>
          )}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      )}

      {/* Filters */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search by domain, service, or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <MagnifyingGlassIcon style={{ width: 20, height: 20 }} />
                  </InputAdornment>
                )
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="inactive">Inactive</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>SSL</InputLabel>
              <Select
                value={sslFilter}
                onChange={(e) => setSSLFilter(e.target.value)}
                label="SSL"
              >
                <MenuItem value="all">All Routes</MenuItem>
                <MenuItem value="enabled">SSL Enabled</MenuItem>
                <MenuItem value="disabled">No SSL</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>

      {/* Routes Table */}
      <Paper>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Domain</TableCell>
                <TableCell>Path/Rule</TableCell>
                <TableCell>Service</TableCell>
                <TableCell>Middleware</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {loading ? (
                [...Array(5)].map((_, i) => (
                  <TableRow key={i}>
                    {[...Array(6)].map((_, j) => (
                      <TableCell key={j}>
                        <Skeleton />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              ) : paginatedRoutes.length > 0 ? (
                paginatedRoutes.map((route) => (
                  <TableRow key={route.id} hover>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {route.ssl && (
                          <LockClosedIcon
                            style={{ width: 16, height: 16, color: 'green' }}
                          />
                        )}
                        <Typography variant="body2">
                          {route.domain}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                        {route.rule || route.path || '/'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {route.service}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {route.middleware && route.middleware.length > 0 ? (
                        <Box display="flex" gap={0.5} flexWrap="wrap">
                          {route.middleware.slice(0, 2).map((m) => (
                            <Chip key={m} label={m} size="small" />
                          ))}
                          {route.middleware.length > 2 && (
                            <Chip label={`+${route.middleware.length - 2}`} size="small" />
                          )}
                        </Box>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          None
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={route.status}
                        size="small"
                        color={route.status === 'active' ? 'success' : 'default'}
                        icon={
                          route.status === 'active' ? (
                            <CheckCircleIcon style={{ width: 16, height: 16 }} />
                          ) : (
                            <XCircleIcon style={{ width: 16, height: 16 }} />
                          )
                        }
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Test Route">
                        <IconButton
                          size="small"
                          onClick={() => handleTest(route.id)}
                        >
                          <BeakerIcon style={{ width: 20, height: 20 }} />
                        </IconButton>
                      </Tooltip>
                      <IconButton
                        size="small"
                        onClick={(e) => handleMenuOpen(e, route)}
                      >
                        <EllipsisVerticalIcon style={{ width: 20, height: 20 }} />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              ) : error && !loading ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                    <Box display="flex" flexDirection="column" alignItems="center" gap={2}>
                      <ExclamationTriangleIcon style={{ width: 48, height: 48, color: '#f87171' }} />
                      <Typography variant="body1" color="error">
                        Failed to load Traefik routes
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {error}
                      </Typography>
                      <Button
                        variant="contained"
                        startIcon={<ArrowPathIcon style={{ width: 20, height: 20 }} />}
                        onClick={() => {
                          setError(null);
                          setLoading(true);
                          setRetryCount({ loadRoutes: 0, deleteRoute: 0, testRoute: 0, saveRoute: 0 });
                          loadRoutes();
                        }}
                      >
                        Retry Now
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
              ) : (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                    <Typography variant="body2" color="text.secondary">
                      No routes found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          component="div"
          count={filteredRoutes.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>

      {/* Action Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => handleEdit(selectedRoute)}>
          <PencilIcon style={{ width: 16, height: 16, marginRight: 8 }} />
          Edit
        </MenuItem>
        <MenuItem onClick={() => handleTest(selectedRoute?.id)}>
          <BeakerIcon style={{ width: 16, height: 16, marginRight: 8 }} />
          Test
        </MenuItem>
        <MenuItem
          onClick={() => {
            handleDelete(selectedRoute?.id);
            handleMenuClose();
          }}
          sx={{ color: 'error.main' }}
        >
          <TrashIcon style={{ width: 16, height: 16, marginRight: 8 }} />
          Delete
        </MenuItem>
      </Menu>

      {/* Route Editor Modal */}
      <TraefikRouteEditor
        open={editorOpen}
        onClose={() => {
          setEditorOpen(false);
          setEditingRoute(null);
        }}
        route={editingRoute}
        onSave={handleSaveRoute}
      />
    </Container>
  );
};

export default TraefikRoutes;
