import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Chip,
  IconButton,
  Tooltip,
  LinearProgress,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Grid,
  Paper,
  FormControlLabel,
  Switch,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tabs,
  Tab,
  Snackbar,
} from '@mui/material';
import {
  CloudQueue as MigrationIcon,
  Search as SearchIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  GetApp as ExportIcon,
  CloudDownload as ImportIcon,
  Dns as DnsIcon,
  Storage as NameserverIcon,
  VerifiedUser as VerifyIcon,
  Timeline as ProgressIcon,
  Email as EmailIcon,
  Language as WebIcon,
  Security as SslIcon,
  Close as CloseIcon,
  FileCopy as CopyIcon,
  Restore as RollbackIcon,
  Schedule as ScheduleIcon,
  History as HistoryIcon,
  Assignment as ReportIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';
import axios from 'axios';

const MigrationWizard = () => {
  const { currentTheme } = useTheme();

  // Wizard state
  const [activeStep, setActiveStep] = useState(0);
  const [migrationJob, setMigrationJob] = useState(null);

  // Step 1 - Discovery state
  const [namecheapAccount, setNamecheapAccount] = useState({
    username: '',
    apiKey: '',
    clientIp: '',
    sandboxMode: false
  });
  const [discoveredDomains, setDiscoveredDomains] = useState([]);
  const [selectedDomains, setSelectedDomains] = useState([]);
  const [domainFilter, setDomainFilter] = useState('all');
  const [domainSearch, setDomainSearch] = useState('');
  const [connectionStatus, setConnectionStatus] = useState(null);

  // Step 2 - Export state
  const [dnsRecords, setDnsRecords] = useState({});
  const [emailServices, setEmailServices] = useState({});
  const [exportTab, setExportTab] = useState(0);
  const [loadingDns, setLoadingDns] = useState(false);

  // Step 3 - Review state
  const [migrationPlan, setMigrationPlan] = useState(null);
  const [confirmationChecklist, setConfirmationChecklist] = useState({
    backup: false,
    emailUnderstand: false,
    planReviewed: false
  });

  // Step 4 - Execute state
  const [migrationProgress, setMigrationProgress] = useState({});
  const [overallProgress, setOverallProgress] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [estimatedTime, setEstimatedTime] = useState(null);

  // Step 5 - Verify state
  const [healthChecks, setHealthChecks] = useState({});
  const [verificationTab, setVerificationTab] = useState(0);

  // UI state
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });
  const [openRollbackDialog, setOpenRollbackDialog] = useState(false);
  const [openScheduleDialog, setOpenScheduleDialog] = useState(false);
  const [rollbackReason, setRollbackReason] = useState('');
  const [scheduledDate, setScheduledDate] = useState('');
  const [dryRunMode, setDryRunMode] = useState(false);

  // Pagination state
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const steps = [
    {
      label: 'Discovery',
      description: 'Select NameCheap domains to migrate',
      icon: <SearchIcon />
    },
    {
      label: 'Export',
      description: 'Review DNS records and email settings',
      icon: <ExportIcon />
    },
    {
      label: 'Review',
      description: 'Preview migration plan and confirm',
      icon: <InfoIcon />
    },
    {
      label: 'Execute',
      description: 'Run migration with progress tracking',
      icon: <ProgressIcon />
    },
    {
      label: 'Verify',
      description: 'Health checks and verification',
      icon: <VerifyIcon />
    }
  ];

  useEffect(() => {
    // Load saved migration draft if exists
    loadMigrationDraft();

    // Set up polling for active migration
    let interval;
    if (activeStep === 4 && migrationJob) {
      interval = setInterval(fetchMigrationProgress, 2000);
    }
    return () => clearInterval(interval);
  }, [activeStep, migrationJob]);

  // API calls
  const connectNamecheap = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/v1/namecheap/accounts', namecheapAccount);
      setConnectionStatus('connected');
      showToast('Successfully connected to NameCheap', 'success');
      return true;
    } catch (err) {
      setConnectionStatus('failed');
      showToast(err.response?.data?.detail || 'Failed to connect to NameCheap', 'error');
      return false;
    } finally {
      setLoading(false);
    }
  };

  const discoverDomains = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/namecheap/domains');
      setDiscoveredDomains(response.data.domains || []);
      showToast(`Discovered ${response.data.domains?.length || 0} domains`, 'success');
    } catch (err) {
      showToast('Failed to discover domains', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchDnsRecords = async (domain) => {
    try {
      setLoadingDns(true);
      const response = await axios.get(`/api/v1/namecheap/domains/${domain}/dns`);
      setDnsRecords(prev => ({ ...prev, [domain]: response.data.records || [] }));

      // Check for email services
      const emailService = detectEmailService(response.data.records || []);
      if (emailService) {
        setEmailServices(prev => ({ ...prev, [domain]: emailService }));
      }
    } catch (err) {
      showToast(`Failed to fetch DNS for ${domain}`, 'error');
    } finally {
      setLoadingDns(false);
    }
  };

  const exportDnsRecords = async (domain, format = 'csv') => {
    try {
      const response = await axios.get(`/api/v1/namecheap/domains/${domain}/dns/export`, {
        params: { format },
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${domain}-dns-backup.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      showToast(`DNS records exported for ${domain}`, 'success');
    } catch (err) {
      showToast('Failed to export DNS records', 'error');
    }
  };

  const generateMigrationPlan = async () => {
    try {
      setLoading(true);
      const response = await axios.post('/api/v1/migration/plan', {
        domains: selectedDomains,
        dry_run: dryRunMode
      });
      setMigrationPlan(response.data);
    } catch (err) {
      showToast('Failed to generate migration plan', 'error');
    } finally {
      setLoading(false);
    }
  };

  const startMigration = async () => {
    if (!allChecklistConfirmed()) {
      showToast('Please confirm all checklist items', 'warning');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.post('/api/v1/migration/jobs', {
        domains: selectedDomains,
        dry_run: dryRunMode,
        scheduled_at: scheduledDate || null
      });
      setMigrationJob(response.data);
      setActiveStep(4);
      showToast('Migration started', 'success');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to start migration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchMigrationProgress = async () => {
    if (!migrationJob) return;

    try {
      const response = await axios.get(`/api/v1/migration/jobs/${migrationJob.id}/progress`);
      setMigrationProgress(response.data.domains || {});
      setOverallProgress(response.data.overall_percent || 0);
      setEstimatedTime(response.data.estimated_completion);

      // Check if complete
      if (response.data.status === 'completed') {
        setActiveStep(5);
        runHealthChecks();
      }
    } catch (err) {
      console.error('Failed to fetch progress:', err);
    }
  };

  const pauseMigration = async () => {
    try {
      await axios.post(`/api/v1/migration/jobs/${migrationJob.id}/pause`);
      setIsPaused(true);
      showToast('Migration paused', 'info');
    } catch (err) {
      showToast('Failed to pause migration', 'error');
    }
  };

  const resumeMigration = async () => {
    try {
      await axios.post(`/api/v1/migration/jobs/${migrationJob.id}/resume`);
      setIsPaused(false);
      showToast('Migration resumed', 'success');
    } catch (err) {
      showToast('Failed to resume migration', 'error');
    }
  };

  const rollbackMigration = async () => {
    if (!rollbackReason.trim()) {
      showToast('Please provide a reason for rollback', 'warning');
      return;
    }

    try {
      setLoading(true);
      await axios.post(`/api/v1/migration/jobs/${migrationJob.id}/rollback`, {
        reason: rollbackReason
      });
      showToast('Migration rolled back successfully', 'success');
      setOpenRollbackDialog(false);
      resetWizard();
    } catch (err) {
      showToast('Failed to rollback migration', 'error');
    } finally {
      setLoading(false);
    }
  };

  const runHealthChecks = async () => {
    if (!migrationJob) return;

    try {
      const response = await axios.post('/api/v1/migration/health-check', {
        job_id: migrationJob.id,
        check_types: ['dns_propagation', 'ssl_certificate', 'email_functionality', 'website_accessibility']
      });
      setHealthChecks(response.data.results || {});
    } catch (err) {
      showToast('Failed to run health checks', 'error');
    }
  };

  const downloadMigrationReport = async () => {
    try {
      const response = await axios.get(`/api/v1/migration/jobs/${migrationJob.id}/report`, {
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `migration-report-${migrationJob.id}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      showToast('Migration report downloaded', 'success');
    } catch (err) {
      showToast('Failed to download report', 'error');
    }
  };

  // Helper functions
  const detectEmailService = (records) => {
    const mxRecords = records.filter(r => r.type === 'MX');
    if (mxRecords.length === 0) return null;

    const mx = mxRecords[0].content;

    if (mx.includes('mail.protection.outlook.com')) {
      return {
        service: 'Microsoft 365',
        mxRecords,
        additionalRecords: records.filter(r =>
          r.type === 'TXT' && (r.content.includes('v=spf1') || r.content.includes('v=DMARC1')) ||
          r.type === 'CNAME' && (r.name.includes('autodiscover') || r.name.includes('enterpriseregistration'))
        )
      };
    } else if (mx.includes('privateemail.com')) {
      return {
        service: 'NameCheap Private Email',
        mxRecords,
        additionalRecords: records.filter(r =>
          r.type === 'CNAME' && (r.name.includes('autoconfig') || r.name.includes('autodiscover'))
        )
      };
    } else if (mx.includes('aspmx.l.google.com')) {
      return {
        service: 'Google Workspace',
        mxRecords,
        additionalRecords: records.filter(r =>
          r.type === 'TXT' && (r.content.includes('google-site-verification') || r.content.includes('v=spf1'))
        )
      };
    }

    return { service: 'Email Forwarding', mxRecords, additionalRecords: [] };
  };

  const allChecklistConfirmed = () => {
    return Object.values(confirmationChecklist).every(v => v === true);
  };

  const loadMigrationDraft = () => {
    const draft = localStorage.getItem('migration_draft');
    if (draft) {
      try {
        const parsed = JSON.parse(draft);
        setSelectedDomains(parsed.selectedDomains || []);
        setActiveStep(parsed.step || 0);
      } catch (err) {
        console.error('Failed to load draft:', err);
      }
    }
  };

  const saveMigrationDraft = () => {
    const draft = {
      selectedDomains,
      step: activeStep,
      timestamp: new Date().toISOString()
    };
    localStorage.setItem('migration_draft', JSON.stringify(draft));
    showToast('Migration draft saved', 'success');
  };

  const resetWizard = () => {
    setActiveStep(0);
    setSelectedDomains([]);
    setMigrationJob(null);
    setMigrationProgress({});
    setHealthChecks({});
    localStorage.removeItem('migration_draft');
  };

  const showToast = (message, severity = 'info') => {
    setToast({ open: true, message, severity });
  };

  const handleNext = async () => {
    if (activeStep === 0 && selectedDomains.length === 0) {
      showToast('Please select at least one domain', 'warning');
      return;
    }

    if (activeStep === 1) {
      // Fetch DNS for all selected domains
      for (const domain of selectedDomains) {
        if (!dnsRecords[domain]) {
          await fetchDnsRecords(domain);
        }
      }
    }

    if (activeStep === 2) {
      await generateMigrationPlan();
    }

    if (activeStep === 3) {
      await startMigration();
      return; // startMigration advances to step 4
    }

    setActiveStep(prev => prev + 1);
  };

  const handleBack = () => {
    setActiveStep(prev => prev - 1);
  };

  const toggleDomainSelection = (domain) => {
    setSelectedDomains(prev => {
      if (prev.includes(domain)) {
        return prev.filter(d => d !== domain);
      } else {
        return [...prev, domain];
      }
    });
  };

  const toggleSelectAll = () => {
    if (selectedDomains.length === filteredDomains.length) {
      setSelectedDomains([]);
    } else {
      setSelectedDomains(filteredDomains);
    }
  };

  // Filter domains
  const filteredDomains = discoveredDomains.filter(domain => {
    const matchesSearch = !domainSearch ||
      domain.toLowerCase().includes(domainSearch.toLowerCase());

    const matchesFilter = domainFilter === 'all' ||
      (domainFilter === 'active' && domain.status === 'active') ||
      (domainFilter === 'expired' && domain.status === 'expired') ||
      (domainFilter === 'locked' && domain.is_locked);

    return matchesSearch && matchesFilter;
  });

  const paginatedDomains = filteredDomains.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Status badge component
  const StatusBadge = ({ status, phase }) => {
    const config = {
      queued: { color: 'default', icon: <WarningIcon fontSize="small" />, label: 'Queued' },
      adding: { color: 'info', icon: <CircularProgress size={16} />, label: 'Adding to Cloudflare' },
      updating: { color: 'info', icon: <CircularProgress size={16} />, label: 'Updating Nameservers' },
      propagating: { color: 'warning', icon: <RefreshIcon fontSize="small" />, label: 'Propagating' },
      complete: { color: 'success', icon: <CheckIcon fontSize="small" />, label: 'Complete' },
      failed: { color: 'error', icon: <CancelIcon fontSize="small" />, label: 'Failed' }
    };

    const cfg = config[status] || config.queued;

    return (
      <Chip
        icon={cfg.icon}
        label={cfg.label}
        color={cfg.color}
        size="small"
        sx={{ fontWeight: 600 }}
      />
    );
  };

  // Health status badge
  const HealthStatusBadge = ({ status }) => {
    const config = {
      passed: { color: 'success', icon: <CheckIcon fontSize="small" />, label: 'Healthy' },
      warning: { color: 'warning', icon: <WarningIcon fontSize="small" />, label: 'Warning' },
      failed: { color: 'error', icon: <CancelIcon fontSize="small" />, label: 'Failed' }
    };

    const cfg = config[status] || config.warning;

    return (
      <Chip
        icon={cfg.icon}
        label={cfg.label}
        color={cfg.color}
        size="small"
      />
    );
  };

  // Render step content
  const renderStepContent = (step) => {
    switch (step) {
      case 0:
        return renderDiscoveryStep();
      case 1:
        return renderExportStep();
      case 2:
        return renderReviewStep();
      case 3:
        return renderExecuteStep();
      case 4:
        return renderVerifyStep();
      default:
        return null;
    }
  };

  // Step 1 - Discovery
  const renderDiscoveryStep = () => (
    <Box>
      {/* NameCheap Connection */}
      {!connectionStatus && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>Connect to NameCheap</Typography>
            <Divider sx={{ my: 2 }} />
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="API Username"
                  value={namecheapAccount.username}
                  onChange={(e) => setNamecheapAccount({ ...namecheapAccount, username: e.target.value })}
                  placeholder="YourUsername"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="API Key"
                  type="password"
                  value={namecheapAccount.apiKey}
                  onChange={(e) => setNamecheapAccount({ ...namecheapAccount, apiKey: e.target.value })}
                  placeholder="Your API Key"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Client IP"
                  value={namecheapAccount.clientIp}
                  onChange={(e) => setNamecheapAccount({ ...namecheapAccount, clientIp: e.target.value })}
                  placeholder="192.168.1.100"
                  helperText="Your server's public IP address"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={namecheapAccount.sandboxMode}
                      onChange={(e) => setNamecheapAccount({ ...namecheapAccount, sandboxMode: e.target.checked })}
                    />
                  }
                  label="Sandbox Mode (Testing)"
                />
              </Grid>
              <Grid item xs={12}>
                <Button
                  variant="contained"
                  onClick={async () => {
                    const connected = await connectNamecheap();
                    if (connected) {
                      await discoverDomains();
                    }
                  }}
                  disabled={!namecheapAccount.username || !namecheapAccount.apiKey || !namecheapAccount.clientIp || loading}
                  sx={{
                    background: currentTheme === 'unicorn'
                      ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                      : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
                  }}
                >
                  {loading ? 'Connecting...' : 'Connect & Discover Domains'}
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Domain Selection Table */}
      {connectionStatus === 'connected' && (
        <Card>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Select Domains to Migrate ({selectedDomains.length} selected)
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant="outlined"
                  onClick={toggleSelectAll}
                  size="small"
                >
                  {selectedDomains.length === filteredDomains.length ? 'Deselect All' : 'Select All'}
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<RefreshIcon />}
                  onClick={discoverDomains}
                  size="small"
                >
                  Refresh
                </Button>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <TextField
                size="small"
                placeholder="Search domains..."
                value={domainSearch}
                onChange={(e) => setDomainSearch(e.target.value)}
                sx={{ minWidth: 250 }}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Status Filter</InputLabel>
                <Select
                  value={domainFilter}
                  onChange={(e) => setDomainFilter(e.target.value)}
                  label="Status Filter"
                >
                  <MenuItem value="all">All Domains</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="expired">Expired</MenuItem>
                  <MenuItem value="locked">Locked</MenuItem>
                </Select>
              </FormControl>
            </Box>

            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        checked={selectedDomains.length === filteredDomains.length && filteredDomains.length > 0}
                        indeterminate={selectedDomains.length > 0 && selectedDomains.length < filteredDomains.length}
                        onChange={toggleSelectAll}
                      />
                    </TableCell>
                    <TableCell>Domain</TableCell>
                    <TableCell>Registrar</TableCell>
                    <TableCell>Expiration</TableCell>
                    <TableCell>DNS Provider</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {paginatedDomains.map((domain) => (
                    <TableRow key={domain.domain} hover>
                      <TableCell padding="checkbox">
                        <Checkbox
                          checked={selectedDomains.includes(domain.domain)}
                          onChange={() => toggleDomainSelection(domain.domain)}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontWeight: 600 }}>
                          {domain.domain}
                        </Typography>
                      </TableCell>
                      <TableCell>NameCheap</TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {domain.expiration_date ? new Date(domain.expiration_date).toLocaleDateString() : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                          {domain.current_nameservers?.[0] || 'NameCheap NS'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {domain.is_locked && <Chip label="Locked" color="warning" size="small" sx={{ mr: 1 }} />}
                        {domain.status === 'expired' && <Chip label="Expired" color="error" size="small" sx={{ mr: 1 }} />}
                        {domain.status === 'active' && !domain.is_locked && <Chip label="Active" color="success" size="small" />}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            <TablePagination
              component="div"
              count={filteredDomains.length}
              page={page}
              onPageChange={(e, newPage) => setPage(newPage)}
              rowsPerPage={rowsPerPage}
              onRowsPerPageChange={(e) => {
                setRowsPerPage(parseInt(e.target.value, 10));
                setPage(0);
              }}
              rowsPerPageOptions={[10, 25, 50]}
            />
          </CardContent>
        </Card>
      )}
    </Box>
  );

  // Step 2 - Export DNS
  const renderExportStep = () => (
    <Box>
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>DNS Records & Email Services</Typography>
          <Divider sx={{ my: 2 }} />

          {/* Summary Card */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  {selectedDomains.length}
                </Typography>
                <Typography variant="body2">Domains Selected</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, bgcolor: 'info.main', color: 'white' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  {Object.values(dnsRecords).reduce((sum, records) => sum + records.length, 0)}
                </Typography>
                <Typography variant="body2">Total DNS Records</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={4}>
              <Paper sx={{ p: 2, bgcolor: 'warning.main', color: 'white' }}>
                <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                  {Object.keys(emailServices).length}
                </Typography>
                <Typography variant="body2">Email Services Detected</Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* Tabs for each domain */}
          <Tabs
            value={exportTab}
            onChange={(e, newValue) => setExportTab(newValue)}
            variant="scrollable"
            scrollButtons="auto"
            sx={{ mb: 2 }}
          >
            {selectedDomains.map((domain, idx) => (
              <Tab
                key={domain}
                label={domain}
                icon={emailServices[domain] ? <EmailIcon color="warning" /> : null}
                iconPosition="end"
              />
            ))}
          </Tabs>

          {/* Domain DNS Records */}
          {selectedDomains.map((domain, idx) => (
            exportTab === idx && (
              <Box key={domain}>
                {/* Email Service Warning */}
                {emailServices[domain] && (
                  <Alert severity="warning" icon={<EmailIcon />} sx={{ mb: 2 }}>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      📧 {emailServices[domain].service} Detected
                    </Typography>
                    <Typography variant="body2">
                      {emailServices[domain].mxRecords.length} MX record(s) and {emailServices[domain].additionalRecords.length} additional email record(s) will be preserved.
                    </Typography>
                  </Alert>
                )}

                {/* DNS Records Table */}
                {loadingDns ? (
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                    <CircularProgress />
                  </Box>
                ) : (
                  <>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="body1" sx={{ fontWeight: 600 }}>
                        DNS Records ({dnsRecords[domain]?.length || 0} total)
                      </Typography>
                      <Button
                        variant="outlined"
                        startIcon={<ExportIcon />}
                        onClick={() => exportDnsRecords(domain, 'csv')}
                        size="small"
                      >
                        Export to CSV
                      </Button>
                    </Box>

                    <TableContainer sx={{ maxHeight: 400 }}>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Type</TableCell>
                            <TableCell>Name</TableCell>
                            <TableCell>Content</TableCell>
                            <TableCell>TTL</TableCell>
                            <TableCell>Priority</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {(dnsRecords[domain] || []).map((record, recordIdx) => {
                            const isEmailRecord = record.type === 'MX' ||
                              (record.type === 'TXT' && (record.content.includes('v=spf1') || record.content.includes('v=DMARC1')));

                            return (
                              <TableRow
                                key={recordIdx}
                                sx={{ bgcolor: isEmailRecord ? 'warning.lighter' : 'inherit' }}
                              >
                                <TableCell>
                                  <Chip
                                    label={record.type}
                                    size="small"
                                    color={isEmailRecord ? 'warning' : 'default'}
                                    icon={isEmailRecord ? <EmailIcon fontSize="small" /> : null}
                                  />
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                    {record.name}
                                  </Typography>
                                </TableCell>
                                <TableCell>
                                  <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                                    {record.content.length > 50 ? record.content.substring(0, 50) + '...' : record.content}
                                  </Typography>
                                </TableCell>
                                <TableCell>{record.ttl}s</TableCell>
                                <TableCell>{record.priority || '-'}</TableCell>
                              </TableRow>
                            );
                          })}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  </>
                )}
              </Box>
            )
          ))}
        </CardContent>
      </Card>
    </Box>
  );

  // Step 3 - Review
  const renderReviewStep = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Migration Plan Preview</Typography>
          <Divider sx={{ my: 2 }} />

          <Grid container spacing={3}>
            {/* Migration Summary */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Domains to Migrate
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
                  {selectedDomains.length}
                </Typography>
                <List dense>
                  {selectedDomains.slice(0, 5).map(domain => (
                    <ListItem key={domain}>
                      <ListItemIcon>
                        <DnsIcon fontSize="small" />
                      </ListItemIcon>
                      <ListItemText primary={domain} />
                    </ListItem>
                  ))}
                  {selectedDomains.length > 5 && (
                    <ListItem>
                      <ListItemText primary={`... and ${selectedDomains.length - 5} more`} />
                    </ListItem>
                  )}
                </List>
              </Paper>
            </Grid>

            {/* DNS Records Summary */}
            <Grid item xs={12} md={6}>
              <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  DNS Records
                </Typography>
                <Typography variant="h4" sx={{ fontWeight: 'bold', mb: 2 }}>
                  {Object.values(dnsRecords).reduce((sum, records) => sum + records.length, 0)}
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Total Records</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {Object.values(dnsRecords).reduce((sum, records) => sum + records.length, 0)}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Email Records</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600, color: 'warning.main' }}>
                      {Object.values(dnsRecords).reduce((sum, records) =>
                        sum + records.filter(r => r.type === 'MX' || (r.type === 'TXT' && r.content.includes('v=spf1'))).length, 0
                      )}
                    </Typography>
                  </Box>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                    <Typography variant="body2">Per Domain Average</Typography>
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                      {Math.round(Object.values(dnsRecords).reduce((sum, records) => sum + records.length, 0) / selectedDomains.length)}
                    </Typography>
                  </Box>
                </Box>
              </Paper>
            </Grid>
          </Grid>

          {/* Warnings */}
          <Box sx={{ mt: 3 }}>
            <Alert severity="warning" sx={{ mb: 2 }} icon={<WarningIcon />}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                Important Migration Warnings
              </Typography>
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Email Service Interruption Risk"
                    secondary={`${Object.keys(emailServices).length} domain(s) have email services configured. Email may be temporarily affected during DNS propagation.`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Propagation Delay"
                    secondary="DNS propagation typically takes 1-24 hours, sometimes up to 48 hours globally."
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Cloudflare 3-Zone Pending Limit"
                    secondary="Maximum 3 zones can be pending at once. Additional domains will be queued automatically."
                  />
                </ListItem>
              </List>
            </Alert>
          </Box>

          {/* Confirmation Checklist */}
          <Paper sx={{ p: 2, bgcolor: 'action.hover' }}>
            <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
              Confirmation Checklist
            </Typography>
            <Divider sx={{ my: 1 }} />
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmationChecklist.backup}
                  onChange={(e) => setConfirmationChecklist({ ...confirmationChecklist, backup: e.target.checked })}
                />
              }
              label="I have backed up all DNS records and exported them to CSV"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmationChecklist.emailUnderstand}
                  onChange={(e) => setConfirmationChecklist({ ...confirmationChecklist, emailUnderstand: e.target.checked })}
                />
              }
              label="I understand that email services may be temporarily affected during migration"
            />
            <FormControlLabel
              control={
                <Checkbox
                  checked={confirmationChecklist.planReviewed}
                  onChange={(e) => setConfirmationChecklist({ ...confirmationChecklist, planReviewed: e.target.checked })}
                />
              }
              label="I have reviewed the migration plan and accept the risks"
            />
          </Paper>
        </CardContent>
      </Card>

      {/* Advanced Options */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Advanced Options</Typography>
          <Divider sx={{ my: 2 }} />

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={dryRunMode}
                  onChange={(e) => setDryRunMode(e.target.checked)}
                />
              }
              label={
                <Box>
                  <Typography variant="body2">Dry Run Mode (Preview Only)</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Simulate migration without making actual changes
                  </Typography>
                </Box>
              }
            />

            <Box>
              <Button
                variant="outlined"
                startIcon={<ScheduleIcon />}
                onClick={() => setOpenScheduleDialog(true)}
              >
                Schedule Migration
              </Button>
              {scheduledDate && (
                <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                  Scheduled for: {new Date(scheduledDate).toLocaleString()}
                </Typography>
              )}
            </Box>

            <Button
              variant="outlined"
              startIcon={<HistoryIcon />}
              onClick={() => {/* Show migration history */}}
            >
              View Migration History
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  // Step 4 - Execute
  const renderExecuteStep = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Migration Progress</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {!isPaused ? (
                <Button
                  variant="outlined"
                  startIcon={<PauseIcon />}
                  onClick={pauseMigration}
                  size="small"
                >
                  Pause
                </Button>
              ) : (
                <Button
                  variant="outlined"
                  startIcon={<StartIcon />}
                  onClick={resumeMigration}
                  size="small"
                  color="success"
                >
                  Resume
                </Button>
              )}
              <Button
                variant="outlined"
                color="error"
                startIcon={<RollbackIcon />}
                onClick={() => setOpenRollbackDialog(true)}
                size="small"
              >
                Rollback
              </Button>
            </Box>
          </Box>

          {/* Overall Progress */}
          <Box sx={{ mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Overall Progress</Typography>
              <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                {overallProgress}%
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={overallProgress}
              sx={{ height: 10, borderRadius: 1 }}
            />
            {estimatedTime && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                Estimated completion: {new Date(estimatedTime).toLocaleString()}
              </Typography>
            )}
          </Box>

          {/* Per-Domain Progress */}
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {selectedDomains.map(domain => {
              const progress = migrationProgress[domain] || {};
              return (
                <Paper key={domain} sx={{ p: 2, bgcolor: 'action.hover' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {domain}
                    </Typography>
                    <StatusBadge status={progress.status || 'queued'} phase={progress.phase} />
                  </Box>

                  <LinearProgress
                    variant="determinate"
                    value={progress.percent || 0}
                    sx={{ mb: 1, height: 6, borderRadius: 1 }}
                  />

                  <Typography variant="caption" color="text.secondary">
                    {progress.current_operation || 'Waiting in queue...'}
                  </Typography>

                  {progress.error && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      <Typography variant="caption">{progress.error}</Typography>
                    </Alert>
                  )}

                  {progress.queue_position && (
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                      Queue position: {progress.queue_position}
                    </Typography>
                  )}
                </Paper>
              );
            })}
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  // Step 5 - Verify
  const renderVerifyStep = () => (
    <Box>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Health Check Dashboard</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={runHealthChecks}
                size="small"
              >
                Re-run Checks
              </Button>
              <Button
                variant="outlined"
                startIcon={<ReportIcon />}
                onClick={downloadMigrationReport}
                size="small"
              >
                Download Report
              </Button>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Tabs for health check categories */}
          <Tabs
            value={verificationTab}
            onChange={(e, newValue) => setVerificationTab(newValue)}
            sx={{ mb: 2 }}
          >
            <Tab label="DNS Propagation" icon={<DnsIcon />} iconPosition="start" />
            <Tab label="SSL Certificates" icon={<SslIcon />} iconPosition="start" />
            <Tab label="Email Delivery" icon={<EmailIcon />} iconPosition="start" />
            <Tab label="Website Availability" icon={<WebIcon />} iconPosition="start" />
          </Tabs>

          {/* Health Check Results */}
          <Box>
            {selectedDomains.map((domain) => {
              const checks = healthChecks[domain] || {};
              const currentCheck = ['dns_propagation', 'ssl_certificate', 'email_functionality', 'website_accessibility'][verificationTab];
              const checkResult = checks[currentCheck] || {};

              return (
                <Paper key={domain} sx={{ p: 2, mb: 2, bgcolor: 'action.hover' }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {domain}
                    </Typography>
                    <HealthStatusBadge status={checkResult.status || 'warning'} />
                  </Box>

                  {verificationTab === 0 && ( // DNS Propagation
                    <Box>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        Propagation: {checkResult.propagation_percent || 0}%
                      </Typography>
                      <LinearProgress
                        variant="determinate"
                        value={checkResult.propagation_percent || 0}
                        sx={{ mb: 2, height: 6, borderRadius: 1 }}
                      />
                      <Grid container spacing={1}>
                        {Object.entries(checkResult.resolvers || {}).map(([resolver, status]) => (
                          <Grid item xs={12} sm={6} key={resolver}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                              <Typography variant="caption">{resolver}</Typography>
                              {status ? (
                                <CheckIcon fontSize="small" color="success" />
                              ) : (
                                <CancelIcon fontSize="small" color="error" />
                              )}
                            </Box>
                          </Grid>
                        ))}
                      </Grid>
                    </Box>
                  )}

                  {verificationTab === 1 && ( // SSL Certificate
                    <Box>
                      {checkResult.issued ? (
                        <Alert severity="success" icon={<SslIcon />}>
                          <Typography variant="body2">
                            SSL Certificate Issued
                          </Typography>
                          <Typography variant="caption">
                            Issuer: {checkResult.issuer || 'Cloudflare Inc ECC CA-3'}
                          </Typography>
                          <br />
                          <Typography variant="caption">
                            Valid: {checkResult.valid_from} - {checkResult.valid_to}
                          </Typography>
                        </Alert>
                      ) : (
                        <Alert severity="warning">
                          <Typography variant="body2">
                            SSL Certificate Pending
                          </Typography>
                          <Typography variant="caption">
                            Certificate issuance typically takes 15-30 minutes.
                          </Typography>
                        </Alert>
                      )}
                    </Box>
                  )}

                  {verificationTab === 2 && ( // Email Functionality
                    <Box>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            {checkResult.mx_resolved ? <CheckIcon color="success" /> : <CancelIcon color="error" />}
                          </ListItemIcon>
                          <ListItemText
                            primary="MX Records"
                            secondary={checkResult.mx_records?.join(', ') || 'Not configured'}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            {checkResult.spf_configured ? <CheckIcon color="success" /> : <CancelIcon color="error" />}
                          </ListItemIcon>
                          <ListItemText primary="SPF Record" secondary={checkResult.spf_configured ? 'Configured' : 'Not configured'} />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            {checkResult.dmarc_configured ? <CheckIcon color="success" /> : <CancelIcon color="error" />}
                          </ListItemIcon>
                          <ListItemText primary="DMARC Record" secondary={checkResult.dmarc_configured ? 'Configured' : 'Not configured'} />
                        </ListItem>
                      </List>
                    </Box>
                  )}

                  {verificationTab === 3 && ( // Website Accessibility
                    <Box>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>
                            {checkResult.http_accessible ? <CheckIcon color="success" /> : <CancelIcon color="error" />}
                          </ListItemIcon>
                          <ListItemText
                            primary="HTTP"
                            secondary={checkResult.http_status ? `Status: ${checkResult.http_status}` : 'Not accessible'}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            {checkResult.https_accessible ? <CheckIcon color="success" /> : <CancelIcon color="error" />}
                          </ListItemIcon>
                          <ListItemText
                            primary="HTTPS"
                            secondary={checkResult.https_status ? `Status: ${checkResult.https_status}` : 'Not accessible'}
                          />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>
                            {checkResult.cloudflare_proxy ? <CheckIcon color="success" /> : <InfoIcon color="info" />}
                          </ListItemIcon>
                          <ListItemText
                            primary="Cloudflare Proxy"
                            secondary={checkResult.cloudflare_proxy ? 'Active (Orange Cloud)' : 'DNS Only (Grey Cloud)'}
                          />
                        </ListItem>
                      </List>
                    </Box>
                  )}
                </Paper>
              );
            })}
          </Box>
        </CardContent>
      </Card>

      {/* Migration Complete Actions */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>Migration Complete</Typography>
          <Divider sx={{ my: 2 }} />
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={() => {
                resetWizard();
                showToast('Ready to start new migration', 'success');
              }}
              sx={{
                background: currentTheme === 'unicorn'
                  ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                  : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
              }}
            >
              Start New Migration
            </Button>
            <Button
              variant="outlined"
              onClick={() => setActiveStep(0)}
            >
              View Migration Summary
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
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
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <MigrationIcon sx={{ fontSize: 40 }} />
            <Box>
              <Typography variant="h5" sx={{ fontWeight: 'bold' }}>
                NameCheap to Cloudflare Migration Wizard
              </Typography>
              <Typography variant="body2" sx={{ opacity: 0.9, mt: 0.5 }}>
                Automated domain migration with DNS preservation
              </Typography>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Stepper */}
      <Card>
        <CardContent>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel
                  icon={step.icon}
                  optional={
                    <Typography variant="caption">{step.description}</Typography>
                  }
                >
                  {step.label}
                </StepLabel>
                <StepContent>
                  {renderStepContent(index)}

                  {/* Navigation Buttons */}
                  <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
                    {index > 0 && index < 4 && (
                      <Button onClick={handleBack} disabled={loading}>
                        Back
                      </Button>
                    )}
                    {index < 3 && (
                      <Button
                        variant="contained"
                        onClick={handleNext}
                        disabled={loading || (index === 0 && selectedDomains.length === 0)}
                        sx={{
                          background: currentTheme === 'unicorn'
                            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                            : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
                        }}
                      >
                        {loading ? <CircularProgress size={24} /> : index === 3 ? 'Start Migration' : 'Next'}
                      </Button>
                    )}
                    {index > 0 && index < 4 && (
                      <Button
                        variant="outlined"
                        onClick={saveMigrationDraft}
                      >
                        Save Draft
                      </Button>
                    )}
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Rollback Dialog */}
      <Dialog
        open={openRollbackDialog}
        onClose={() => setOpenRollbackDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Rollback Migration</Typography>
            <IconButton onClick={() => setOpenRollbackDialog(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Alert severity="error" sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              ⚠️ WARNING: This will revert nameservers to original values
            </Typography>
            <Typography variant="body2">
              This action will:
              • Revert nameservers at NameCheap
              • Keep domain in Cloudflare (paused)
              • Preserve DNS records for future retry
            </Typography>
          </Alert>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason for rollback"
            value={rollbackReason}
            onChange={(e) => setRollbackReason(e.target.value)}
            placeholder="Enter the reason for rolling back this migration..."
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenRollbackDialog(false)}>Cancel</Button>
          <Button
            onClick={rollbackMigration}
            variant="contained"
            color="error"
            disabled={!rollbackReason.trim() || loading}
          >
            {loading ? <CircularProgress size={24} /> : 'Confirm Rollback'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Schedule Dialog */}
      <Dialog
        open={openScheduleDialog}
        onClose={() => setOpenScheduleDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Schedule Migration</Typography>
            <IconButton onClick={() => setOpenScheduleDialog(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <TextField
            fullWidth
            type="datetime-local"
            label="Scheduled Date & Time"
            value={scheduledDate}
            onChange={(e) => setScheduledDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
          />
          <Alert severity="info" sx={{ mt: 2 }}>
            Migration will start automatically at the scheduled time.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenScheduleDialog(false)}>Cancel</Button>
          <Button
            onClick={() => {
              setOpenScheduleDialog(false);
              showToast('Migration scheduled successfully', 'success');
            }}
            variant="contained"
            disabled={!scheduledDate}
          >
            Schedule
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

export default MigrationWizard;
