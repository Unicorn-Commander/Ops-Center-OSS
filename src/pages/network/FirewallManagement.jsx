import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
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
  Divider,
  FormHelperText,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Security as SecurityIcon,
  CheckCircle as EnabledIcon,
  Cancel as DisabledIcon,
  Refresh as RefreshIcon,
  RestartAlt as ResetIcon,
  FilterList as FilterListIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';

const FirewallManagement = () => {
  const { currentTheme } = useTheme();

  // State management
  const [status, setStatus] = useState({ enabled: false, rules: [], default_incoming: 'deny', default_outgoing: 'allow' });
  const [loading, setLoading] = useState(true);
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openTemplateDialog, setOpenTemplateDialog] = useState(false);
  const [openResetDialog, setOpenResetDialog] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [ruleToDelete, setRuleToDelete] = useState(null);

  // Form state
  const [newRule, setNewRule] = useState({
    port: '',
    protocol: 'tcp',
    action: 'allow',
    from_ip: '',
    description: ''
  });
  const [formErrors, setFormErrors] = useState({});

  // Pagination and filtering
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(50);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterProtocol, setFilterProtocol] = useState('all');

  // Notification state
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });

  // Template selection
  const [selectedTemplate, setSelectedTemplate] = useState('');

  const templates = [
    { value: 'web_server', label: 'Web Server (HTTP/HTTPS)', ports: '80, 443' },
    { value: 'ssh_secure', label: 'SSH Secure', ports: '22' },
    { value: 'database', label: 'Database (PostgreSQL/Redis)', ports: '5432, 6379' },
    { value: 'docker', label: 'Docker', ports: '2375, 2376' }
  ];

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/network/firewall/status', {
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to fetch firewall status');

      const data = await response.json();
      setStatus(data);
    } catch (err) {
      showToast('Failed to load firewall status: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFirewall = async (enabled) => {
    try {
      const endpoint = enabled
        ? '/api/v1/network/firewall/enable'
        : '/api/v1/network/firewall/disable';

      const response = await fetch(endpoint, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to toggle firewall');
      }

      showToast(`Firewall ${enabled ? 'enabled' : 'disabled'} successfully`, 'success');
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const validateRule = () => {
    const errors = {};

    // Validate port
    const port = parseInt(newRule.port);
    if (isNaN(port) || port < 1 || port > 65535) {
      errors.port = 'Port must be between 1 and 65535';
    }

    // Validate IP/CIDR if provided
    if (newRule.from_ip) {
      const ipRegex = /^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$/;
      if (!ipRegex.test(newRule.from_ip)) {
        errors.from_ip = 'Invalid IP address or CIDR notation';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAddRule = async () => {
    if (!validateRule()) {
      showToast('Please fix validation errors', 'error');
      return;
    }

    try {
      const response = await fetch('/api/v1/network/firewall/rules', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          port: parseInt(newRule.port),
          protocol: newRule.protocol,
          action: newRule.action,
          from_ip: newRule.from_ip || null,
          description: newRule.description
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add rule');
      }

      showToast('Firewall rule added successfully', 'success');
      setOpenAddDialog(false);
      setNewRule({ port: '', protocol: 'tcp', action: 'allow', from_ip: '', description: '' });
      setFormErrors({});
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleDeleteRule = async () => {
    if (!ruleToDelete) return;

    const { num, port } = ruleToDelete;

    try {
      const response = await fetch(`/api/v1/network/firewall/rules/${num}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          override_ssh: port === '22' || port === 22
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to delete rule');
      }

      showToast('Rule deleted successfully', 'success');
      setDeleteDialogOpen(false);
      setRuleToDelete(null);
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleApplyTemplate = async () => {
    if (!selectedTemplate) {
      showToast('Please select a template', 'error');
      return;
    }

    try {
      const response = await fetch(`/api/v1/network/firewall/templates/${selectedTemplate}`, {
        method: 'POST',
        credentials: 'include'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to apply template');
      }

      const data = await response.json();
      showToast(`Template applied: ${data.rules_added} rules added`, 'success');
      setOpenTemplateDialog(false);
      setSelectedTemplate('');
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleResetFirewall = async () => {
    try {
      const response = await fetch('/api/v1/network/firewall/reset', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          confirm: true,
          keep_ssh: true
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to reset firewall');
      }

      showToast('Firewall reset successfully', 'success');
      setOpenResetDialog(false);
      fetchStatus();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const showToast = (message, severity = 'info') => {
    setToast({ open: true, message, severity });
  };

  const openDeleteDialog = (rule) => {
    setRuleToDelete(rule);
    setDeleteDialogOpen(true);
  };

  // Filter and paginate rules
  const filteredRules = status.rules.filter(rule => {
    const matchesSearch = !searchQuery ||
      rule.port?.toString().includes(searchQuery) ||
      rule.description?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProtocol = filterProtocol === 'all' ||
      rule.protocol?.toLowerCase() === filterProtocol.toLowerCase();

    return matchesSearch && matchesProtocol;
  });

  const paginatedRules = filteredRules.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
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
                  Firewall Status
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                  {status.enabled ? (
                    <>
                      <EnabledIcon sx={{ color: '#4ade80' }} />
                      <Typography>Enabled & Protected</Typography>
                    </>
                  ) : (
                    <>
                      <DisabledIcon sx={{ color: '#f87171' }} />
                      <Typography>Disabled - Unprotected</Typography>
                    </>
                  )}
                </Box>
              </Box>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box sx={{ textAlign: 'right', mr: 2 }}>
                <Typography variant="body2" sx={{ opacity: 0.9 }}>
                  Default Policy
                </Typography>
                <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                  Incoming: {status.default_incoming?.toUpperCase()} | Outgoing: {status.default_outgoing?.toUpperCase()}
                </Typography>
              </Box>

              <Switch
                checked={status.enabled}
                onChange={(e) => handleToggleFirewall(e.target.checked)}
                sx={{
                  '& .MuiSwitch-thumb': {
                    backgroundColor: status.enabled ? '#4ade80' : '#f87171'
                  },
                  '& .MuiSwitch-track': {
                    backgroundColor: status.enabled ? '#166534' : '#7f1d1d'
                  }
                }}
              />
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Actions Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpenAddDialog(true)}
            sx={{
              background: currentTheme === 'unicorn'
                ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
                : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
              '&:hover': {
                background: currentTheme === 'unicorn'
                  ? 'linear-gradient(135deg, #5568d3 0%, #653a8b 100%)'
                  : 'linear-gradient(135deg, #2563eb 0%, #1e3a8a 100%)'
              }
            }}
          >
            Add Rule
          </Button>

          <Button
            variant="outlined"
            startIcon={<FilterListIcon />}
            onClick={() => setOpenTemplateDialog(true)}
          >
            Apply Template
          </Button>

          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={fetchStatus}
          >
            Refresh
          </Button>

          <Button
            variant="outlined"
            color="warning"
            startIcon={<ResetIcon />}
            onClick={() => setOpenResetDialog(true)}
          >
            Reset All
          </Button>
        </Box>

        {/* Filter Controls */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            size="small"
            placeholder="Search by port or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ minWidth: 250 }}
          />

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Protocol</InputLabel>
            <Select
              value={filterProtocol}
              onChange={(e) => setFilterProtocol(e.target.value)}
              label="Protocol"
            >
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="tcp">TCP</MenuItem>
              <MenuItem value="udp">UDP</MenuItem>
              <MenuItem value="both">Both</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>

      {/* Stats Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2">
                Total Rules
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold' }}>
                {status.rules.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2">
                Allow Rules
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                {status.rules.filter(r => r.action === 'ALLOW').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={4}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" variant="body2">
                Deny Rules
              </Typography>
              <Typography variant="h4" sx={{ fontWeight: 'bold', color: 'error.main' }}>
                {status.rules.filter(r => r.action === 'DENY' || r.action === 'REJECT').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Rules Table */}
      <Card>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Port</TableCell>
                <TableCell>Protocol</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>From</TableCell>
                <TableCell>Description</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {paginatedRules.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} align="center" sx={{ py: 8 }}>
                    <Typography color="text.secondary">
                      {searchQuery || filterProtocol !== 'all'
                        ? 'No rules match your filters'
                        : 'No firewall rules configured'}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                paginatedRules.map((rule) => (
                  <TableRow key={rule.num} hover>
                    <TableCell>{rule.num}</TableCell>
                    <TableCell>
                      <Chip label={rule.port || 'Any'} color="primary" size="small" />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ textTransform: 'uppercase' }}>
                        {rule.protocol}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={rule.action}
                        color={rule.action === 'ALLOW' ? 'success' : 'error'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                        {rule.from || 'Anywhere'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {rule.description || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Tooltip title="Delete Rule">
                        <IconButton
                          color="error"
                          size="small"
                          onClick={() => openDeleteDialog(rule)}
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
          count={filteredRules.length}
          page={page}
          onPageChange={(e, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Card>

      {/* Add Rule Dialog */}
      <Dialog
        open={openAddDialog}
        onClose={() => setOpenAddDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <Typography variant="h6">Add Firewall Rule</Typography>
            <IconButton onClick={() => setOpenAddDialog(false)}>
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
            <TextField
              label="Port"
              type="number"
              value={newRule.port}
              onChange={(e) => setNewRule({ ...newRule, port: e.target.value })}
              inputProps={{ min: 1, max: 65535 }}
              error={!!formErrors.port}
              helperText={formErrors.port || '1-65535'}
              fullWidth
              required
            />

            <FormControl fullWidth>
              <InputLabel>Protocol</InputLabel>
              <Select
                value={newRule.protocol}
                onChange={(e) => setNewRule({ ...newRule, protocol: e.target.value })}
                label="Protocol"
              >
                <MenuItem value="tcp">TCP</MenuItem>
                <MenuItem value="udp">UDP</MenuItem>
                <MenuItem value="both">Both (TCP & UDP)</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>Action</InputLabel>
              <Select
                value={newRule.action}
                onChange={(e) => setNewRule({ ...newRule, action: e.target.value })}
                label="Action"
              >
                <MenuItem value="allow">Allow</MenuItem>
                <MenuItem value="deny">Deny</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="From IP/CIDR (optional)"
              value={newRule.from_ip}
              onChange={(e) => setNewRule({ ...newRule, from_ip: e.target.value })}
              placeholder="e.g., 192.168.1.0/24"
              error={!!formErrors.from_ip}
              helperText={formErrors.from_ip || 'Leave empty for any IP'}
              fullWidth
            />

            <TextField
              label="Description"
              value={newRule.description}
              onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
              placeholder="e.g., Allow HTTP traffic"
              multiline
              rows={2}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Cancel</Button>
          <Button
            onClick={handleAddRule}
            variant="contained"
            disabled={!newRule.port}
          >
            Add Rule
          </Button>
        </DialogActions>
      </Dialog>

      {/* Apply Template Dialog */}
      <Dialog
        open={openTemplateDialog}
        onClose={() => setOpenTemplateDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Apply Firewall Template</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Select a pre-configured template to quickly add common firewall rules.
          </Typography>

          <FormControl fullWidth>
            <InputLabel>Template</InputLabel>
            <Select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              label="Template"
            >
              {templates.map(template => (
                <MenuItem key={template.value} value={template.value}>
                  <Box>
                    <Typography variant="body1">{template.label}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      Ports: {template.ports}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTemplateDialog(false)}>Cancel</Button>
          <Button
            onClick={handleApplyTemplate}
            variant="contained"
            disabled={!selectedTemplate}
          >
            Apply Template
          </Button>
        </DialogActions>
      </Dialog>

      {/* Reset Firewall Dialog */}
      <Dialog
        open={openResetDialog}
        onClose={() => setOpenResetDialog(false)}
        maxWidth="sm"
      >
        <DialogTitle>Reset Firewall</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              This action will delete all firewall rules!
            </Typography>
          </Alert>
          <Typography variant="body1">
            Are you sure you want to reset the firewall? This will remove all custom rules.
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            SSH access (port 22) will be preserved to prevent lockout.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenResetDialog(false)}>Cancel</Button>
          <Button
            onClick={handleResetFirewall}
            variant="contained"
            color="warning"
          >
            Reset Firewall
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        maxWidth="sm"
      >
        <DialogTitle>Delete Firewall Rule</DialogTitle>
        <DialogContent>
          {ruleToDelete && (ruleToDelete.port === '22' || ruleToDelete.port === 22) && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <Typography variant="body2" sx={{ fontWeight: 600 }}>
                ⚠️ WARNING: This is the SSH rule!
              </Typography>
              <Typography variant="body2">
                Deleting this rule may lock you out of the system. Make sure you have alternative access before proceeding.
              </Typography>
            </Alert>
          )}

          <Typography variant="body1">
            Are you sure you want to delete this firewall rule?
          </Typography>

          {ruleToDelete && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
              <Typography variant="body2">
                <strong>Rule #{ruleToDelete.num}</strong>
              </Typography>
              <Typography variant="body2">
                Port: {ruleToDelete.port} | Protocol: {ruleToDelete.protocol} | Action: {ruleToDelete.action}
              </Typography>
              {ruleToDelete.description && (
                <Typography variant="body2">
                  Description: {ruleToDelete.description}
                </Typography>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleDeleteRule}
            variant="contained"
            color="error"
          >
            Delete Rule
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

export default FirewallManagement;
