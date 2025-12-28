import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  TablePagination,
  CircularProgress,
  Snackbar,
  Grid,
  Tabs,
  Tab,
  Switch,
  FormControlLabel,
  Divider,
  LinearProgress,
  FormHelperText,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Cloud as CloudIcon,
  CheckCircle as ActiveIcon,
  Pending as PendingIcon,
  Cancel as InactiveIcon,
  Refresh as RefreshIcon,
  ContentCopy as CopyIcon,
  FilterList as FilterIcon,
  Close as CloseIcon,
  Warning as WarningIcon,
  CloudQueue as ProxiedIcon,
  CloudOff as DNSOnlyIcon,
  Settings as SettingsIcon,
  Storage as StorageIcon,
  Dns as DnsIcon,
  Info as InfoIcon,
  TrendingUp as AnalyticsIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';
import axios from 'axios';

// Configure axios to send credentials
axios.defaults.withCredentials = true;

const CloudflareDNS = () => {
  const { currentTheme } = useTheme();

  // State management - Zones
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [loading, setLoading] = useState(true);
  const [zoneDetailView, setZoneDetailView] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  // State management - DNS Records
  const [dnsRecords, setDnsRecords] = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // State management - Account info
  const [accountInfo, setAccountInfo] = useState({ zones: {}, rate_limit: {}, features: {} });

  // Dialogs
  const [openCreateZone, setOpenCreateZone] = useState(false);
  const [openAddRecord, setOpenAddRecord] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Pagination and filtering - Zones
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Pagination and filtering - DNS Records
  const [recordPage, setRecordPage] = useState(0);
  const [recordRowsPerPage, setRecordRowsPerPage] = useState(10);
  const [recordSearchQuery, setRecordSearchQuery] = useState('');
  const [recordTypeFilter, setRecordTypeFilter] = useState('all');

  // Form state - Create Zone
  const [newZone, setNewZone] = useState({
    domain: '',
    jump_start: true,
    priority: 'normal'
  });

  // Form state - Add/Edit DNS Record
  const [dnsRecord, setDnsRecord] = useState({
    type: 'A',
    name: '',
    content: '',
    ttl: 1,
    proxied: false,
    priority: 10
  });
  const [formErrors, setFormErrors] = useState({});

  // Notification state
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });

  // Record types
  const recordTypes = ['A', 'AAAA', 'CNAME', 'MX', 'TXT', 'NS', 'SRV', 'CAA'];
  const ttlOptions = [
    { value: 1, label: 'Auto' },
    { value: 60, label: '1 minute' },
    { value: 300, label: '5 minutes' },
    { value: 600, label: '10 minutes' },
    { value: 3600, label: '1 hour' },
    { value: 86400, label: '1 day' }
  ];

  useEffect(() => {
    fetchZones();
    fetchAccountInfo();
  }, []);

  useEffect(() => {
    if (selectedZone && zoneDetailView) {
      fetchDnsRecords(selectedZone.zone_id);
    }
  }, [selectedZone, zoneDetailView]);

  // API calls
  const fetchZones = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/cloudflare/zones', {
        params: { limit: 100 }
      });
      setZones(response.data.zones || []);
    } catch (err) {
      showToast('Failed to load zones: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAccountInfo = async () => {
    try {
      const response = await axios.get('/api/v1/cloudflare/account/limits');
      setAccountInfo(response.data);
    } catch (err) {
      console.error('Failed to load account info:', err);
    }
  };

  const fetchDnsRecords = async (zoneId) => {
    try {
      setLoadingRecords(true);
      const response = await axios.get(`/api/v1/cloudflare/zones/${zoneId}/dns`, {
        params: { limit: 1000 }
      });
      setDnsRecords(response.data.records || []);
    } catch (err) {
      showToast('Failed to load DNS records: ' + err.message, 'error');
    } finally {
      setLoadingRecords(false);
    }
  };

  const handleCreateZone = async () => {
    if (!newZone.domain) {
      showToast('Please enter a domain name', 'error');
      return;
    }

    try {
      const response = await axios.post('/api/v1/cloudflare/zones', newZone);
      showToast(`Zone created: ${response.data.domain}`, 'success');
      setOpenCreateZone(false);
      setNewZone({ domain: '', jump_start: true, priority: 'normal' });
      fetchZones();
      fetchAccountInfo();
    } catch (err) {
      if (err.response?.status === 429) {
        showToast(`Zone queued: ${err.response.data.message}`, 'warning');
      } else {
        showToast(err.response?.data?.detail || 'Failed to create zone', 'error');
      }
    }
  };

  const handleDeleteZone = async () => {
    if (!deleteTarget) return;

    try {
      await axios.delete(`/api/v1/cloudflare/zones/${deleteTarget.zone_id}`);
      showToast(`Zone ${deleteTarget.domain} deleted`, 'success');
      setDeleteTarget(null);
      setOpenDeleteDialog(false);
      fetchZones();
      fetchAccountInfo();
      if (selectedZone?.zone_id === deleteTarget.zone_id) {
        setZoneDetailView(false);
        setSelectedZone(null);
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete zone', 'error');
    }
  };

  const handleCheckStatus = async (zoneId) => {
    try {
      await axios.post(`/api/v1/cloudflare/zones/${zoneId}/check-status`);
      showToast('Status updated', 'success');
      fetchZones();
    } catch (err) {
      showToast('Failed to check status', 'error');
    }
  };

  const validateDnsRecord = () => {
    const errors = {};

    if (!dnsRecord.name) {
      errors.name = 'Name is required';
    }

    if (!dnsRecord.content) {
      errors.content = 'Content is required';
    }

    // Type-specific validation
    if (dnsRecord.type === 'A') {
      const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipv4Regex.test(dnsRecord.content)) {
        errors.content = 'Invalid IPv4 address';
      }
    } else if (dnsRecord.type === 'AAAA') {
      // Simple IPv6 check
      if (!dnsRecord.content.includes(':')) {
        errors.content = 'Invalid IPv6 address';
      }
    } else if (dnsRecord.type === 'MX' && (dnsRecord.priority < 0 || dnsRecord.priority > 65535)) {
      errors.priority = 'Priority must be between 0 and 65535';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAddDnsRecord = async () => {
    if (!validateDnsRecord()) {
      showToast('Please fix validation errors', 'error');
      return;
    }

    try {
      const payload = {
        type: dnsRecord.type,
        name: dnsRecord.name,
        content: dnsRecord.content,
        ttl: parseInt(dnsRecord.ttl),
        proxied: dnsRecord.proxied
      };

      if (dnsRecord.type === 'MX' || dnsRecord.type === 'SRV') {
        payload.priority = parseInt(dnsRecord.priority);
      }

      if (selectedRecord) {
        // Update existing record
        await axios.put(
          `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns/${selectedRecord.id}`,
          payload
        );
        showToast('DNS record updated', 'success');
      } else {
        // Create new record
        await axios.post(
          `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns`,
          payload
        );
        showToast('DNS record added', 'success');
      }

      setOpenAddRecord(false);
      resetDnsRecordForm();
      fetchDnsRecords(selectedZone.zone_id);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to save DNS record', 'error');
    }
  };

  const handleDeleteDnsRecord = async () => {
    if (!deleteTarget) return;

    // Check if email-related record
    const isEmailRecord = deleteTarget.type === 'MX' ||
      (deleteTarget.type === 'TXT' && (
        deleteTarget.content.includes('v=spf1') ||
        deleteTarget.content.includes('v=DMARC1') ||
        deleteTarget.name.includes('dkim')
      ));

    if (isEmailRecord) {
      showToast('Warning: This appears to be an email-related record', 'warning');
    }

    try {
      await axios.delete(
        `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns/${deleteTarget.id}`
      );
      showToast('DNS record deleted', 'success');
      setDeleteTarget(null);
      setOpenDeleteDialog(false);
      fetchDnsRecords(selectedZone.zone_id);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete DNS record', 'error');
    }
  };

  const handleToggleProxy = async (record) => {
    try {
      await axios.post(
        `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns/${record.id}/toggle-proxy`
      );
      showToast(`Proxy ${record.proxied ? 'disabled' : 'enabled'}`, 'success');
      fetchDnsRecords(selectedZone.zone_id);
    } catch (err) {
      showToast('Failed to toggle proxy', 'error');
    }
  };

  const handleCopyNameservers = (nameservers) => {
    if (!nameservers || nameservers.length === 0) return;
    const text = nameservers.join('\n');
    navigator.clipboard.writeText(text);
    showToast('Nameservers copied to clipboard', 'success');
  };

  const handleEditRecord = (record) => {
    setSelectedRecord(record);
    setDnsRecord({
      type: record.type,
      name: record.name.replace(`.${selectedZone.domain}`, '').replace(selectedZone.domain, '@'),
      content: record.content,
      ttl: record.ttl || 1,
      proxied: record.proxied || false,
      priority: record.priority || 10
    });
    setOpenAddRecord(true);
  };

  const resetDnsRecordForm = () => {
    setDnsRecord({
      type: 'A',
      name: '',
      content: '',
      ttl: 1,
      proxied: false,
      priority: 10
    });
    setSelectedRecord(null);
    setFormErrors({});
  };

  const openDeleteConfirmation = (target, isZone = false) => {
    setDeleteTarget({ ...target, isZone });
    setOpenDeleteDialog(true);
  };

  const showToast = (message, severity = 'info') => {
    setToast({ open: true, message, severity });
  };

  // Filter and paginate zones
  const filteredZones = zones.filter(zone => {
    const matchesSearch = !searchQuery ||
      zone.domain.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' ||
      zone.status.toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesStatus;
  });

  const paginatedZones = filteredZones.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Filter and paginate DNS records
  const filteredRecords = dnsRecords.filter(record => {
    const matchesSearch = !recordSearchQuery ||
      record.name.toLowerCase().includes(recordSearchQuery.toLowerCase()) ||
      record.content.toLowerCase().includes(recordSearchQuery.toLowerCase());

    const matchesType = recordTypeFilter === 'all' ||
      record.type.toLowerCase() === recordTypeFilter.toLowerCase();

    return matchesSearch && matchesType;
  });

  const paginatedRecords = filteredRecords.slice(
    recordPage * recordRowsPerPage,
    recordPage * recordRowsPerPage + recordRowsPerPage
  );

  // Status badge component
  const StatusBadge = ({ status }) => {
    const statusConfig = {
      active: { color: 'success', icon: <ActiveIcon fontSize="small" />, label: 'Active' },
      pending: { color: 'warning', icon: <PendingIcon fontSize="small" />, label: 'Pending' },
      deactivated: { color: 'error', icon: <InactiveIcon fontSize="small" />, label: 'Deactivated' },
      deleted: { color: 'default', icon: <InactiveIcon fontSize="small" />, label: 'Deleted' }
    };

    const config = statusConfig[status.toLowerCase()] || statusConfig.pending;

    return (
      <Chip
        icon={config.icon}
        label={config.label}
        color={config.color}
        size="small"
        sx={{ fontWeight: 600 }}
      />
    );
  };

  // Nameservers display component
  const NameserversDisplay = ({ nameservers, zone }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Box>
        {nameservers && nameservers.length > 0 ? (
          nameservers.map((ns, idx) => (
            <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
              {ns}
            </Typography>
          ))
        ) : (
          <Typography variant="body2" color="text.secondary">-</Typography>
        )}
      </Box>
      {nameservers && nameservers.length > 0 && (
        <Tooltip title="Copy nameservers">
          <IconButton size="small" onClick={() => handleCopyNameservers(nameservers)}>
            <CopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Zone Detail View
  if (zoneDetailView && selectedZone) {
    return (
      <Box sx={{ p: 3 }}>
        {/* Header */}
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
          <Box>
            <Button
              variant="text"
              onClick={() => {
                setZoneDetailView(false);
                setSelectedZone(null);
                setActiveTab(0);
              }}
              sx={{ mb: 1 }}
            >
              ← Back to Zones
            </Button>
            <Typography variant="h4" sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
              <CloudIcon />
              {selectedZone.domain}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
              <StatusBadge status={selectedZone.status} />
              <Chip label={selectedZone.plan?.toUpperCase() || 'FREE'} size="small" />
            </Box>
          </Box>

          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => handleCheckStatus(selectedZone.zone_id)}
            >
              Check Status
            </Button>
            <Button
              variant="outlined"
              color="error"
              startIcon={<DeleteIcon />}
              onClick={() => openDeleteConfirmation(selectedZone, true)}
            >
              Delete Zone
            </Button>
          </Box>
        </Box>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="Overview" icon={<InfoIcon />} iconPosition="start" />
            <Tab label="DNS Records" icon={<DnsIcon />} iconPosition="start" />
            <Tab label="Nameservers" icon={<StorageIcon />} iconPosition="start" />
            <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        {/* Tab Content */}
        {activeTab === 0 && (
          <Box>
            {/* Overview Tab */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Zone Information</Typography>
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Zone ID</Typography>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>{selectedZone.zone_id}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Status</Typography>
                        <Box sx={{ mt: 0.5 }}>
                          <StatusBadge status={selectedZone.status} />
                        </Box>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Plan</Typography>
                        <Typography variant="body2">{selectedZone.plan?.toUpperCase() || 'FREE'}</Typography>
                      </Box>
                      <Box>
                        <Typography variant="caption" color="text.secondary">Created</Typography>
                        <Typography variant="body2">{new Date(selectedZone.created_at).toLocaleString()}</Typography>
                      </Box>
                      {selectedZone.activated_at && (
                        <Box>
                          <Typography variant="caption" color="text.secondary">Activated</Typography>
                          <Typography variant="body2">{new Date(selectedZone.activated_at).toLocaleString()}</Typography>
                        </Box>
                      )}
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>DNS Records Summary</Typography>
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">Total Records</Typography>
                        <Typography variant="h5" sx={{ fontWeight: 'bold' }}>{dnsRecords.length}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">Proxied Records</Typography>
                        <Typography variant="h6" sx={{ color: 'warning.main' }}>
                          {dnsRecords.filter(r => r.proxied).length}
                        </Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2">DNS-Only Records</Typography>
                        <Typography variant="h6" sx={{ color: 'info.main' }}>
                          {dnsRecords.filter(r => !r.proxied).length}
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Alert severity="info" icon={<InfoIcon />}>
                  {selectedZone.status === 'pending' ? (
                    <>
                      <strong>Action Required:</strong> Update your nameservers at your domain registrar to activate this zone.
                      Copy the nameservers from the "Nameservers" tab.
                    </>
                  ) : (
                    <>
                      <strong>Zone Active:</strong> Your domain is now using Cloudflare nameservers. Changes to DNS records will propagate automatically.
                    </>
                  )}
                </Alert>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 1 && (
          <Box>
            {/* DNS Records Tab */}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <TextField
                  size="small"
                  placeholder="Search records..."
                  value={recordSearchQuery}
                  onChange={(e) => setRecordSearchQuery(e.target.value)}
                  sx={{ minWidth: 250 }}
                />
                <FormControl size="small" sx={{ minWidth: 120 }}>
                  <InputLabel>Type</InputLabel>
                  <Select
                    value={recordTypeFilter}
                    onChange={(e) => setRecordTypeFilter(e.target.value)}
                    label="Type"
                  >
                    <MenuItem value="all">All Types</MenuItem>
                    {recordTypes.map(type => (
                      <MenuItem key={type} value={type.toLowerCase()}>{type}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>

              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  resetDnsRecordForm();
                  setOpenAddRecord(true);
                }}
                sx={{
                  background: currentTheme === 'unicorn'
                    ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                    : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
                }}
              >
                Add Record
              </Button>
            </Box>

            {loadingRecords ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Card>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Type</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Content</TableCell>
                        <TableCell>TTL</TableCell>
                        <TableCell>Proxy</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {paginatedRecords.length === 0 ? (
                        <TableRow>
                          <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                            <Typography color="text.secondary">
                              {recordSearchQuery || recordTypeFilter !== 'all'
                                ? 'No records match your filters'
                                : 'No DNS records configured'}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ) : (
                        paginatedRecords.map((record) => (
                          <TableRow key={record.id} hover>
                            <TableCell>
                              <Chip
                                label={record.type}
                                color="primary"
                                size="small"
                                sx={{ fontWeight: 600 }}
                              />
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                {record.name}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                {record.content}
                              </Typography>
                              {record.priority !== undefined && (
                                <Typography variant="caption" color="text.secondary">
                                  Priority: {record.priority}
                                </Typography>
                              )}
                            </TableCell>
                            <TableCell>
                              <Typography variant="body2">
                                {record.ttl === 1 ? 'Auto' : `${record.ttl}s`}
                              </Typography>
                            </TableCell>
                            <TableCell>
                              {['A', 'AAAA', 'CNAME'].includes(record.type) ? (
                                <Tooltip title={record.proxied ? 'Proxied (Orange Cloud)' : 'DNS Only (Grey Cloud)'}>
                                  <IconButton
                                    size="small"
                                    onClick={() => handleToggleProxy(record)}
                                    sx={{ color: record.proxied ? 'warning.main' : 'action.disabled' }}
                                  >
                                    {record.proxied ? <ProxiedIcon /> : <DNSOnlyIcon />}
                                  </IconButton>
                                </Tooltip>
                              ) : (
                                <Typography variant="caption" color="text.secondary">-</Typography>
                              )}
                            </TableCell>
                            <TableCell align="right">
                              <Tooltip title="Edit Record">
                                <IconButton
                                  size="small"
                                  onClick={() => handleEditRecord(record)}
                                >
                                  <EditIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete Record">
                                <IconButton
                                  size="small"
                                  color="error"
                                  onClick={() => openDeleteConfirmation(record, false)}
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
                  count={filteredRecords.length}
                  page={recordPage}
                  onPageChange={(e, newPage) => setRecordPage(newPage)}
                  rowsPerPage={recordRowsPerPage}
                  onRowsPerPageChange={(e) => {
                    setRecordRowsPerPage(parseInt(e.target.value, 10));
                    setRecordPage(0);
                  }}
                  rowsPerPageOptions={[10, 25, 50, 100]}
                />
              </Card>
            )}
          </Box>
        )}

        {activeTab === 2 && (
          <Box>
            {/* Nameservers Tab */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Assigned Nameservers</Typography>
                    <Divider sx={{ my: 2 }} />
                    {selectedZone.nameservers && selectedZone.nameservers.length > 0 ? (
                      <Box>
                        {selectedZone.nameservers.map((ns, idx) => (
                          <Box key={idx} sx={{ mb: 1, p: 1.5, bgcolor: 'action.hover', borderRadius: 1 }}>
                            <Typography variant="body1" sx={{ fontFamily: 'monospace', fontWeight: 600 }}>
                              {ns}
                            </Typography>
                          </Box>
                        ))}
                        <Button
                          fullWidth
                          variant="outlined"
                          startIcon={<CopyIcon />}
                          onClick={() => handleCopyNameservers(selectedZone.nameservers)}
                          sx={{ mt: 2 }}
                        >
                          Copy Nameservers
                        </Button>
                      </Box>
                    ) : (
                      <Alert severity="info">Nameservers not yet assigned</Alert>
                    )}
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Update Instructions</Typography>
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>1. Log in to your domain registrar</Typography>
                        <Typography variant="body2" color="text.secondary">
                          (e.g., NameCheap, GoDaddy, Google Domains)
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>2. Find the DNS or Nameserver settings</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Usually under "Domain Management" or "DNS Settings"
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>3. Replace existing nameservers</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Remove old nameservers and add the Cloudflare nameservers above
                        </Typography>
                      </Box>
                      <Box>
                        <Typography variant="body2" sx={{ fontWeight: 600, mb: 0.5 }}>4. Wait for propagation</Typography>
                        <Typography variant="body2" color="text.secondary">
                          DNS propagation can take 1-24 hours. Check status periodically.
                        </Typography>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Alert severity={selectedZone.status === 'active' ? 'success' : 'warning'}>
                  {selectedZone.status === 'active' ? (
                    <>
                      <strong>Propagation Complete:</strong> Your domain is now using Cloudflare nameservers globally.
                    </>
                  ) : (
                    <>
                      <strong>Propagation Pending:</strong> Nameservers have not been updated yet. Follow the instructions above.
                    </>
                  )}
                </Alert>
              </Grid>
            </Grid>
          </Box>
        )}

        {activeTab === 3 && (
          <Box>
            {/* Settings Tab */}
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Zone Settings</Typography>
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>Development Mode</Typography>
                        <FormControlLabel
                          control={<Switch disabled />}
                          label="Temporarily bypass cache (3 hours)"
                        />
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>Auto HTTPS Rewrites</Typography>
                        <FormControlLabel
                          control={<Switch disabled defaultChecked />}
                          label="Automatically rewrite HTTP to HTTPS"
                        />
                      </Box>
                      <Box>
                        <Typography variant="body2" color="text.secondary" gutterBottom>Always Use HTTPS</Typography>
                        <FormControlLabel
                          control={<Switch disabled defaultChecked />}
                          label="Redirect all HTTP requests to HTTPS"
                        />
                      </Box>
                    </Box>
                    <Alert severity="info" sx={{ mt: 2 }}>
                      Advanced settings coming soon. Visit Cloudflare dashboard for full configuration.
                    </Alert>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>Danger Zone</Typography>
                    <Divider sx={{ my: 2 }} />
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      <Box>
                        <Typography variant="body2" gutterBottom>
                          Delete this zone and all its DNS records
                        </Typography>
                        <Button
                          variant="contained"
                          color="error"
                          startIcon={<DeleteIcon />}
                          onClick={() => openDeleteConfirmation(selectedZone, true)}
                          fullWidth
                        >
                          Delete Zone
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Box>
    );
  }

  // Zone List View (Main Page)
  return (
    <Box sx={{ p: 3 }}>
      {/* Header Card */}
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
              <CloudIcon sx={{ fontSize: 40 }} />
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                  Cloudflare DNS Management
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
                  Manage domains and DNS records
                </Typography>
              </Box>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Account Info */}
      {accountInfo.zones && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2">Total Zones</Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  {accountInfo.zones.total || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2">Active Zones</Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                  {accountInfo.zones.active || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2">Pending Zones</Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'warning.main' }}>
                  {accountInfo.zones.pending || 0} / {accountInfo.zones.limit || 3}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={3}>
            <Card>
              <CardContent>
                <Typography color="text.secondary" variant="body2">Plan</Typography>
                <Typography variant="h5" sx={{ fontWeight: 'bold', textTransform: 'uppercase' }}>
                  {accountInfo.plan || 'FREE'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Rate Limit Warning */}
      {accountInfo.rate_limit && accountInfo.rate_limit.percent_used > 80 && (
        <Alert severity="warning" sx={{ mb: 3 }} icon={<WarningIcon />}>
          <strong>Rate Limit Warning:</strong> You've used {accountInfo.rate_limit.percent_used.toFixed(1)}% of your API rate limit.
          Requests may be throttled. Resets at {new Date(accountInfo.rate_limit.reset_at).toLocaleTimeString()}.
        </Alert>
      )}

      {/* Pending Limit Warning */}
      {accountInfo.zones?.at_limit && (
        <Alert severity="warning" sx={{ mb: 3 }} icon={<WarningIcon />}>
          <strong>Pending Zone Limit Reached:</strong> You have {accountInfo.zones.pending} pending zones (max {accountInfo.zones.limit}).
          New zones will be queued until existing zones become active.
        </Alert>
      )}

      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenCreateZone(true)}
            sx={{
              background: currentTheme === 'unicorn'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
            }}
          >
            Create Zone
          </Button>

          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => {
              fetchZones();
              fetchAccountInfo();
            }}
          >
            Refresh
          </Button>
        </Box>

        {/* Filter Controls */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search domains..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ minWidth: 250 }}
          />

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Status</InputLabel>
            <Select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              label="Status"
            >
              <MenuItem value="all">All Status</MenuItem>
              <MenuItem value="active">Active</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="deactivated">Deactivated</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Zones Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Domain</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Nameservers</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedZones.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      {searchQuery || statusFilter !== 'all'
                        ? 'No zones match your filters'
                        : 'No zones configured. Create your first zone to get started.'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedZones.map((zone) => (
                  <TableRow
                    key={zone.zone_id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => {
                      setSelectedZone(zone);
                      setZoneDetailView(true);
                    }}
                  >
                    <TableCell>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        {zone.domain}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {zone.zone_id}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={zone.status} />
                    </TableCell>
                    <TableCell>
                      <NameserversDisplay nameservers={zone.nameservers} zone={zone} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {new Date(zone.created_at).toLocaleDateString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                      <Tooltip title="Check Status">
                        <IconButton
                          size="small"
                          onClick={() => handleCheckStatus(zone.zone_id)}
                        >
                          <RefreshIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Zone">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => openDeleteConfirmation(zone, true)}
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
          count={filteredZones.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[5, 10, 25, 50]}
        />
      </Card>

      {/* Create Zone Dialog */}
      <Dialog
        open={openCreateZone}
        onClose={() => setOpenCreateZone(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Create Zone</Typography>
            <IconButton onClick={() => setOpenCreateZone(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            <TextField
              label="Domain Name"
              value={newZone.domain}
              onChange={(e) => setNewZone({ ...newZone, domain: e.target.value })}
              placeholder="example.com"
              helperText="Enter your domain without www"
              fullWidth
              required
              autoFocus
            />

            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={newZone.priority}
                onChange={(e) => setNewZone({ ...newZone, priority: e.target.value })}
                label="Priority"
              >
                <MenuItem value="critical">Critical - Add First</MenuItem>
                <MenuItem value="high">High Priority</MenuItem>
                <MenuItem value="normal">Normal Priority</MenuItem>
                <MenuItem value="low">Low Priority</MenuItem>
              </Select>
              <FormHelperText>
                Higher priority zones are processed first when queue is full
              </FormHelperText>
            </FormControl>

            <FormControlLabel
              control={
                <Switch
                  checked={newZone.jump_start}
                  onChange={(e) => setNewZone({ ...newZone, jump_start: e.target.checked })}
                />
              }
              label="Jump Start (Auto-import DNS records)"
            />

            <Alert severity="info">
              After creating the zone, you'll receive Cloudflare nameservers. Update these at your domain registrar to activate the zone.
            </Alert>

            {accountInfo.zones?.at_limit && (
              <Alert severity="warning">
                You have reached the pending zone limit ({accountInfo.zones.pending}/{accountInfo.zones.limit}).
                This domain will be added to the queue and created automatically when a slot becomes available.
              </Alert>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCreateZone(false)}>Cancel</Button>
          <Button
            onClick={handleCreateZone}
            variant="contained"
            disabled={!newZone.domain}
          >
            Create Zone
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add/Edit DNS Record Dialog */}
      <Dialog
        open={openAddRecord}
        onClose={() => {
          setOpenAddRecord(false);
          resetDnsRecordForm();
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">{selectedRecord ? 'Edit' : 'Add'} DNS Record</Typography>
            <IconButton onClick={() => {
              setOpenAddRecord(false);
              resetDnsRecordForm();
            }}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            <FormControl fullWidth required>
              <InputLabel>Type</InputLabel>
              <Select
                value={dnsRecord.type}
                onChange={(e) => setDnsRecord({ ...dnsRecord, type: e.target.value })}
                label="Type"
                disabled={!!selectedRecord}
              >
                {recordTypes.map(type => (
                  <MenuItem key={type} value={type}>{type}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <TextField
              label="Name"
              value={dnsRecord.name}
              onChange={(e) => setDnsRecord({ ...dnsRecord, name: e.target.value })}
              placeholder="@ or subdomain"
              helperText={`Full domain: ${dnsRecord.name || '@'}.${selectedZone?.domain || 'domain.com'}`}
              error={!!formErrors.name}
              fullWidth
              required
            />

            <TextField
              label="Content"
              value={dnsRecord.content}
              onChange={(e) => setDnsRecord({ ...dnsRecord, content: e.target.value })}
              placeholder={
                dnsRecord.type === 'A' ? '192.168.1.1' :
                dnsRecord.type === 'AAAA' ? '2001:db8::1' :
                dnsRecord.type === 'CNAME' ? 'target.example.com' :
                dnsRecord.type === 'MX' ? 'mail.example.com' :
                'Record content'
              }
              error={!!formErrors.content}
              helperText={formErrors.content}
              fullWidth
              required
            />

            <FormControl fullWidth>
              <InputLabel>TTL</InputLabel>
              <Select
                value={dnsRecord.ttl}
                onChange={(e) => setDnsRecord({ ...dnsRecord, ttl: e.target.value })}
                label="TTL"
              >
                {ttlOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
                ))}
              </Select>
              <FormHelperText>Time To Live - How long DNS resolvers cache this record</FormHelperText>
            </FormControl>

            {(dnsRecord.type === 'MX' || dnsRecord.type === 'SRV') && (
              <TextField
                label="Priority"
                type="number"
                value={dnsRecord.priority}
                onChange={(e) => setDnsRecord({ ...dnsRecord, priority: e.target.value })}
                inputProps={{ min: 0, max: 65535 }}
                error={!!formErrors.priority}
                helperText={formErrors.priority || 'Lower values have higher priority (0-65535)'}
                fullWidth
                required
              />
            )}

            {['A', 'AAAA', 'CNAME'].includes(dnsRecord.type) && (
              <FormControlLabel
                control={
                  <Switch
                    checked={dnsRecord.proxied}
                    onChange={(e) => setDnsRecord({ ...dnsRecord, proxied: e.target.checked })}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">Proxied (Orange Cloud)</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Enable Cloudflare proxy for DDoS protection and caching
                    </Typography>
                  </Box>
                }
              />
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setOpenAddRecord(false);
            resetDnsRecordForm();
          }}>
            Cancel
          </Button>
          <Button
            onClick={handleAddDnsRecord}
            variant="contained"
            disabled={!dnsRecord.name || !dnsRecord.content}
          >
            {selectedRecord ? 'Update' : 'Add'} Record
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={openDeleteDialog}
        onClose={() => {
          setOpenDeleteDialog(false);
          setDeleteTarget(null);
        }}
        maxWidth="sm"
      >
        <DialogTitle>Delete {deleteTarget?.isZone ? 'Zone' : 'DNS Record'}</DialogTitle>
        <DialogContent>
          {deleteTarget?.isZone ? (
            <>
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 600 }}>
                  ⚠️ WARNING: This will delete the entire zone!
                </Typography>
                <Typography variant="body2">
                  All DNS records and settings will be permanently deleted.
                </Typography>
              </Alert>
              <Typography variant="body1">
                Are you sure you want to delete the zone <strong>{deleteTarget?.domain}</strong>?
              </Typography>
            </>
          ) : (
            <>
              {deleteTarget && (deleteTarget.type === 'MX' ||
                (deleteTarget.type === 'TXT' && (
                  deleteTarget.content.includes('v=spf1') ||
                  deleteTarget.content.includes('v=DMARC1') ||
                  deleteTarget.name.includes('dkim')
                ))) && (
                <Alert severity="warning" sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    ⚠️ Email-Related Record
                  </Typography>
                  <Typography variant="body2">
                    This appears to be an email configuration record. Deleting it may affect email delivery.
                  </Typography>
                </Alert>
              )}
              <Typography variant="body1" gutterBottom>
                Are you sure you want to delete this DNS record?
              </Typography>
              {deleteTarget && (
                <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
                  <Typography variant="body2">
                    <strong>Type:</strong> {deleteTarget.type}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Name:</strong> {deleteTarget.name}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Content:</strong> {deleteTarget.content}
                  </Typography>
                </Box>
              )}
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setOpenDeleteDialog(false);
            setDeleteTarget(null);
          }}>
            Cancel
          </Button>
          <Button
            onClick={deleteTarget?.isZone ? handleDeleteZone : handleDeleteDnsRecord}
            variant="contained"
            color="error"
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Toast Notifications */}
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

export default CloudflareDNS;
