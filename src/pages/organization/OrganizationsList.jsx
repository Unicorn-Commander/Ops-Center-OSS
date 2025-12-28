import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
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
  Grid,
  Card,
  CardContent,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Alert,
  Snackbar,
  CircularProgress,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Add as AddIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  Star as StarIcon,
  Block as BlockIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Delete as DeleteIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
} from '@mui/icons-material';
import CreateOrganizationModal from '../../components/CreateOrganizationModal';
import { useOrganization } from '../../contexts/OrganizationContext';

const OrganizationsList = () => {
  const navigate = useNavigate();
  const { setCurrentOrg } = useOrganization();

  // State for organization list
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalOrgs, setTotalOrgs] = useState(0);

  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // all, active, suspended, deleted
  const [tierFilter, setTierFilter] = useState('all');

  // Modal states
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);

  // Statistics
  const [stats, setStats] = useState({
    total_orgs: 0,
    active_orgs: 0,
    suspended_orgs: 0,
    professional_tier_count: 0,
  });

  // Toast notification
  const [toast, setToast] = useState({
    open: false,
    message: '',
    severity: 'success',
  });

  // Fetch organizations with filters
  const fetchOrganizations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: rowsPerPage.toString(),
        offset: (page * rowsPerPage).toString(),
      });

      if (searchQuery) {
        params.append('search', searchQuery);
      }

      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }

      if (tierFilter !== 'all') {
        params.append('tier', tierFilter);
      }

      const response = await fetch(`/api/v1/org/organizations?${params}`, {
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to fetch organizations');

      const data = await response.json();
      setOrganizations(data.organizations || []);
      setTotalOrgs(data.total || 0);

      // Calculate stats
      calculateStats(data.organizations || []);
    } catch (err) {
      setError(err.message);
      showToast('Failed to load organizations', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Calculate statistics from organization data
  const calculateStats = (orgs) => {
    const activeOrgs = orgs.filter(org => org.status === 'active').length;
    const suspendedOrgs = orgs.filter(org => org.status === 'suspended').length;
    const professionalTier = orgs.filter(org => org.subscription_tier === 'professional').length;

    setStats({
      total_orgs: orgs.length,
      active_orgs: activeOrgs,
      suspended_orgs: suspendedOrgs,
      professional_tier_count: professionalTier,
    });
  };

  useEffect(() => {
    fetchOrganizations();
  }, [page, rowsPerPage, searchQuery, statusFilter, tierFilter]);

  // Show toast notification
  const showToast = (message, severity = 'success') => {
    setToast({ open: true, message, severity });
  };

  // Handle search
  const handleSearch = (event) => {
    setSearchQuery(event.target.value);
    setPage(0); // Reset to first page
  };

  // Handle pagination
  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  // View organization details
  const handleViewOrganization = (org) => {
    // Set current organization in context (without reloading)
    if (setCurrentOrg) {
      setCurrentOrg(org.id);
    }
    // Navigate to organization team page
    navigate(`/admin/organization/team?org=${org.id}`);
  };

  // Handle organization created
  const handleOrganizationCreated = async (newOrg) => {
    showToast('Organization created successfully');
    setCreateModalOpen(false);

    // Set current organization in context (without reloading)
    if (setCurrentOrg) {
      setCurrentOrg(newOrg.id);
    }

    // Refresh the list
    await fetchOrganizations();

    // Navigate to the new organization's team page
    navigate(`/admin/organization/team?org=${newOrg.id}`);
  };

  // Delete organization
  const handleDeleteOrganization = async () => {
    if (!selectedOrg) return;

    try {
      const response = await fetch(`/api/v1/org/${selectedOrg.id}`, {
        method: 'DELETE',
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Failed to delete organization (${response.status})`);
      }

      showToast('Organization deleted successfully', 'success');
      setDeleteConfirmOpen(false);
      setSelectedOrg(null);
      fetchOrganizations();
    } catch (err) {
      showToast(err.message || 'Failed to delete organization', 'error');
    }
  };

  // Toggle organization status (suspend/activate)
  const handleToggleStatus = async (org) => {
    try {
      const newStatus = org.status === 'active' ? 'suspended' : 'active';

      const response = await fetch(`/api/v1/org/${org.id}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Failed to update status');

      showToast(`Organization ${newStatus === 'active' ? 'activated' : 'suspended'}`, 'success');
      fetchOrganizations();
    } catch (err) {
      showToast(err.message || 'Failed to update status', 'error');
    }
  };

  // Get status chip color
  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'success';
      case 'suspended':
        return 'warning';
      case 'deleted':
        return 'error';
      default:
        return 'default';
    }
  };

  // Get tier badge color
  const getTierColor = (tier) => {
    switch (tier) {
      case 'enterprise':
        return 'error';
      case 'professional':
        return 'secondary';
      case 'starter':
        return 'primary';
      case 'trial':
        return 'warning';
      default:
        return 'default';
    }
  };

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
                    {stats.total_orgs}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Organizations
                  </Typography>
                </Box>
                <BusinessIcon sx={{ fontSize: 48, opacity: 0.8 }} />
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
                    {stats.active_orgs}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Active Organizations
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 48, opacity: 0.8 }} />
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
                    {stats.suspended_orgs}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Suspended Organizations
                  </Typography>
                </Box>
                <BlockIcon sx={{ fontSize: 48, opacity: 0.8 }} />
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
                    {stats.professional_tier_count}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Professional Tier
                  </Typography>
                </Box>
                <StarIcon sx={{ fontSize: 48, opacity: 0.8 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" fontWeight="bold">
            Organizations Management
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateModalOpen(true)}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              },
            }}
          >
            Create Organization
          </Button>
        </Box>

        {/* Search and Filter Controls */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} md={5}>
            <TextField
              fullWidth
              placeholder="Search organizations by name"
              value={searchQuery}
              onChange={handleSearch}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  setPage(0);
                }}
                label="Status"
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value="active">Active</MenuItem>
                <MenuItem value="suspended">Suspended</MenuItem>
                <MenuItem value="deleted">Deleted</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} sm={6} md={2}>
            <FormControl fullWidth>
              <InputLabel>Tier</InputLabel>
              <Select
                value={tierFilter}
                onChange={(e) => {
                  setTierFilter(e.target.value);
                  setPage(0);
                }}
                label="Tier"
              >
                <MenuItem value="all">All Tiers</MenuItem>
                <MenuItem value="trial">Trial</MenuItem>
                <MenuItem value="starter">Starter</MenuItem>
                <MenuItem value="professional">Professional</MenuItem>
                <MenuItem value="enterprise">Enterprise</MenuItem>
                <MenuItem value="founders_friend">Founders Friend</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchOrganizations}
              sx={{ height: '56px' }}
            >
              Refresh
            </Button>
          </Grid>
        </Grid>

        {/* Results Count */}
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Showing {organizations.length} organizations
          {totalOrgs > 0 && ` of ${totalOrgs} total`}
        </Typography>

        {/* Organizations Table */}
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : organizations.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <BusinessIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              No organizations found
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              {searchQuery || statusFilter !== 'all' || tierFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Create your first organization to get started'}
            </Typography>
          </Box>
        ) : (
          <>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Owner</TableCell>
                    <TableCell>Members</TableCell>
                    <TableCell>Tier</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell align="right">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {organizations.map((org) => (
                    <TableRow
                      key={org.id}
                      hover
                      onClick={() => handleViewOrganization(org)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <BusinessIcon color="primary" />
                          <Typography fontWeight="medium">{org.name}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>{org.owner}</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <PeopleIcon fontSize="small" color="action" />
                          <Typography>{org.member_count}</Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={org.subscription_tier}
                          color={getTierColor(org.subscription_tier)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={org.status}
                          color={getStatusColor(org.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {new Date(org.created_at).toLocaleDateString()}
                      </TableCell>
                      <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleViewOrganization(org);
                            }}
                            color="primary"
                          >
                            <VisibilityIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title={org.status === 'active' ? 'Suspend' : 'Activate'}>
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleToggleStatus(org);
                            }}
                            color={org.status === 'active' ? 'warning' : 'success'}
                          >
                            {org.status === 'active' ? <BlockIcon /> : <CheckCircleIcon />}
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Delete">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedOrg(org);
                              setDeleteConfirmOpen(true);
                            }}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              count={totalOrgs}
              page={page}
              onPageChange={handleChangePage}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={handleChangeRowsPerPage}
              rowsPerPageOptions={[5, 10, 25, 50]}
            />
          </>
        )}
      </Paper>

      {/* Create Organization Modal */}
      <CreateOrganizationModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={handleOrganizationCreated}
      />

      {/* Delete Confirmation Modal */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Confirm Delete</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete organization <strong>{selectedOrg?.name}</strong>?
            This action cannot be undone and will remove all members and data associated with this organization.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmOpen(false)}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleDeleteOrganization}
          >
            Delete
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

export default OrganizationsList;
