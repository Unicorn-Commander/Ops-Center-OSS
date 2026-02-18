/**
 * System Audit Log Page
 * Comprehensive audit logging for all system, user, and admin actions
 *
 * Features:
 * - Timeline view of all system events
 * - Advanced filtering (date, type, user, severity)
 * - CSV export capability
 * - Real-time auto-refresh toggle
 * - Expandable event details (user agent, metadata)
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Grid,
  Card,
  CardContent,
  Alert,
  Chip,
  CircularProgress,
  IconButton,
  Tooltip,
  Collapse,
  InputAdornment,
  Switch,
  FormControlLabel,
  Pagination,
  Divider
} from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentArrowDownIcon,
  MagnifyingGlassIcon,
  ArrowPathIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  UserIcon,
  CogIcon,
  CreditCardIcon,
  ServerIcon,
  ShieldCheckIcon,
  CommandLineIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  ExclamationCircleIcon,
  InformationCircleIcon,
  XCircleIcon,
  GlobeAltIcon,
  ComputerDesktopIcon,
  FunnelIcon
} from '@heroicons/react/24/outline';
import PageHeader from '../../components/admin/PageHeader';

// Event type configuration with colors and icons
const EVENT_TYPES = {
  auth: { label: 'Authentication', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)', icon: ShieldCheckIcon },
  billing: { label: 'Billing', color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.1)', icon: CreditCardIcon },
  service: { label: 'Service', color: '#8b5cf6', bgColor: 'rgba(139, 92, 246, 0.1)', icon: ServerIcon },
  admin: { label: 'Admin', color: '#f97316', bgColor: 'rgba(249, 115, 22, 0.1)', icon: CogIcon },
  api: { label: 'API', color: '#6b7280', bgColor: 'rgba(107, 114, 128, 0.1)', icon: CommandLineIcon },
  user: { label: 'User', color: '#14b8a6', bgColor: 'rgba(20, 184, 166, 0.1)', icon: UserIcon }
};

// Severity configuration
const SEVERITIES = {
  info: { label: 'Info', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.1)', icon: InformationCircleIcon },
  warning: { label: 'Warning', color: '#f59e0b', bgColor: 'rgba(245, 158, 11, 0.1)', icon: ExclamationTriangleIcon },
  error: { label: 'Error', color: '#ef4444', bgColor: 'rgba(239, 68, 68, 0.1)', icon: ExclamationCircleIcon },
  critical: { label: 'Critical', color: '#dc2626', bgColor: 'rgba(220, 38, 38, 0.15)', icon: XCircleIcon }
};

// Date range presets
const DATE_RANGES = [
  { value: '24h', label: 'Last 24 hours' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
  { value: 'custom', label: 'Custom range' }
];

const SystemAuditLog = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [entries, setEntries] = useState([]);
  const [stats, setStats] = useState({ total: 0, byType: {}, bySeverity: {} });

  // Filter state
  const [dateRange, setDateRange] = useState('24h');
  const [customDateFrom, setCustomDateFrom] = useState('');
  const [customDateTo, setCustomDateTo] = useState('');
  const [eventType, setEventType] = useState('all');
  const [severity, setSeverity] = useState('all');
  const [userSearch, setUserSearch] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Pagination state
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalEntries, setTotalEntries] = useState(0);
  const entriesPerPage = 50;

  // UI state
  const [expandedEntries, setExpandedEntries] = useState(new Set());
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [showFilters, setShowFilters] = useState(true);

  // Fetch audit log entries
  const fetchAuditLog = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      params.append('page', page);
      params.append('limit', entriesPerPage);

      // Date range
      if (dateRange === 'custom' && customDateFrom) {
        params.append('from_date', customDateFrom);
        if (customDateTo) params.append('to_date', customDateTo);
      } else if (dateRange !== 'custom') {
        params.append('date_range', dateRange);
      }

      // Filters
      if (eventType !== 'all') params.append('event_type', eventType);
      if (severity !== 'all') params.append('severity', severity);
      if (userSearch.trim()) params.append('user', userSearch.trim());
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const response = await fetch(`/api/v1/admin/audit-log?${params.toString()}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch audit log');
      }

      const data = await response.json();
      setEntries(data.entries || []);
      setTotalEntries(data.total || 0);
      setTotalPages(Math.ceil((data.total || 0) / entriesPerPage));
      setStats(data.stats || { total: 0, byType: {}, bySeverity: {} });
    } catch (err) {
      console.error('Error fetching audit log:', err);
      setError(err.message);
      // Generate mock data for development
      generateMockData();
    } finally {
      setLoading(false);
    }
  }, [page, dateRange, customDateFrom, customDateTo, eventType, severity, userSearch, searchQuery]);

  // Generate mock data for development/demo
  const generateMockData = () => {
    const mockEntries = [];
    const actions = {
      auth: ['User logged in', 'User logged out', 'Password changed', 'MFA enabled', 'Session expired', 'Failed login attempt'],
      billing: ['Payment processed', 'Subscription upgraded', 'Invoice generated', 'Payment method added', 'Subscription cancelled'],
      service: ['Service started', 'Service stopped', 'Service restarted', 'Health check failed', 'Configuration updated'],
      admin: ['User role changed', 'Settings updated', 'User suspended', 'API key generated', 'Feature flag toggled'],
      api: ['API key used', 'Rate limit reached', 'Endpoint accessed', 'Webhook triggered', 'Token refreshed'],
      user: ['Profile updated', 'Preferences changed', 'Avatar uploaded', 'Notification settings updated', 'Account linked']
    };

    const severities = ['info', 'warning', 'error', 'critical'];
    const users = ['admin@example.com', 'connect@shafenkhan.com', 'System', 'API Service', 'admin@unicorn.io'];
    const ips = ['192.168.1.100', '10.0.0.45', '172.16.0.22', '::1', '8.8.8.8'];
    const userAgents = [
      'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0',
      'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1.15',
      'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Firefox/121.0',
      'Ops-Center API Client/2.4.0',
      'curl/8.0.1'
    ];

    const types = Object.keys(actions);
    const now = Date.now();

    for (let i = 0; i < 150; i++) {
      const type = types[Math.floor(Math.random() * types.length)];
      const typeActions = actions[type];
      const action = typeActions[Math.floor(Math.random() * typeActions.length)];
      const sev = severities[Math.floor(Math.random() * (i < 10 ? 2 : 4))]; // More info/warning than error/critical

      mockEntries.push({
        id: `audit-${i}`,
        timestamp: new Date(now - i * 300000 - Math.random() * 300000).toISOString(),
        event_type: type,
        severity: sev,
        action: action,
        user: users[Math.floor(Math.random() * users.length)],
        ip_address: ips[Math.floor(Math.random() * ips.length)],
        user_agent: userAgents[Math.floor(Math.random() * userAgents.length)],
        resource: type === 'service' ? `unicorn-${['api', 'web', 'worker', 'cache'][Math.floor(Math.random() * 4)]}` : null,
        metadata: {
          request_id: `req-${Math.random().toString(36).substr(2, 9)}`,
          duration_ms: Math.floor(Math.random() * 500) + 10
        }
      });
    }

    // Apply filters to mock data
    let filtered = mockEntries;
    if (eventType !== 'all') filtered = filtered.filter(e => e.event_type === eventType);
    if (severity !== 'all') filtered = filtered.filter(e => e.severity === severity);
    if (userSearch.trim()) filtered = filtered.filter(e => e.user.toLowerCase().includes(userSearch.toLowerCase()));
    if (searchQuery.trim()) filtered = filtered.filter(e => e.action.toLowerCase().includes(searchQuery.toLowerCase()));

    const start = (page - 1) * entriesPerPage;
    const end = start + entriesPerPage;

    setEntries(filtered.slice(start, end));
    setTotalEntries(filtered.length);
    setTotalPages(Math.ceil(filtered.length / entriesPerPage));
    setStats({
      total: filtered.length,
      byType: types.reduce((acc, t) => ({ ...acc, [t]: filtered.filter(e => e.event_type === t).length }), {}),
      bySeverity: severities.reduce((acc, s) => ({ ...acc, [s]: filtered.filter(e => e.severity === s).length }), {})
    });
  };

  // Export to CSV
  const handleExport = async () => {
    setExporting(true);
    try {
      const params = new URLSearchParams();
      if (dateRange === 'custom' && customDateFrom) {
        params.append('from_date', customDateFrom);
        if (customDateTo) params.append('to_date', customDateTo);
      } else if (dateRange !== 'custom') {
        params.append('date_range', dateRange);
      }
      if (eventType !== 'all') params.append('event_type', eventType);
      if (severity !== 'all') params.append('severity', severity);
      if (userSearch.trim()) params.append('user', userSearch.trim());
      if (searchQuery.trim()) params.append('search', searchQuery.trim());

      const response = await fetch(`/api/v1/admin/audit-log/export?${params.toString()}`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
      // Fallback: export current entries as CSV
      const headers = ['Timestamp', 'Type', 'Severity', 'Action', 'User', 'IP Address', 'User Agent'];
      const rows = entries.map(e => [
        e.timestamp,
        e.event_type,
        e.severity,
        e.action,
        e.user,
        e.ip_address,
        e.user_agent
      ].map(v => `"${(v || '').toString().replace(/"/g, '""')}"`).join(','));

      const csv = [headers.join(','), ...rows].join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `audit-log-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  };

  // Toggle entry expansion
  const toggleExpanded = (id) => {
    setExpandedEntries(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  // Reset filters
  const handleResetFilters = () => {
    setDateRange('24h');
    setCustomDateFrom('');
    setCustomDateTo('');
    setEventType('all');
    setSeverity('all');
    setUserSearch('');
    setSearchQuery('');
    setPage(1);
  };

  // Effects
  useEffect(() => {
    fetchAuditLog();
  }, [fetchAuditLog]);

  useEffect(() => {
    let interval;
    if (autoRefresh) {
      interval = setInterval(fetchAuditLog, 30000);
    }
    return () => clearInterval(interval);
  }, [autoRefresh, fetchAuditLog]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [dateRange, customDateFrom, customDateTo, eventType, severity, userSearch, searchQuery]);

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Get event type config
  const getEventTypeConfig = (type) => EVENT_TYPES[type] || EVENT_TYPES.user;

  // Get severity config
  const getSeverityConfig = (sev) => SEVERITIES[sev] || SEVERITIES.info;

  // Stat Card component
  const StatCard = ({ title, value, icon: Icon, color }) => (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${color}15 0%, ${color}08 100%)`,
        border: `1px solid ${color}20`,
        backdropFilter: 'blur(10px)',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: `0 8px 24px ${color}15`
        }
      }}
    >
      <CardContent sx={{ py: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box>
            <Typography variant="body2" sx={{ color: 'text.secondary', mb: 0.5 }}>
              {title}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, color }}>
              {value.toLocaleString()}
            </Typography>
          </Box>
          <Box sx={{
            p: 1.5,
            borderRadius: 2,
            bgcolor: `${color}15`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Icon style={{ width: 28, height: 28, color }} />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  // Timeline Entry component
  const TimelineEntry = ({ entry, isExpanded, onToggle }) => {
    const typeConfig = getEventTypeConfig(entry.event_type);
    const sevConfig = getSeverityConfig(entry.severity);
    const TypeIcon = typeConfig.icon;
    const SevIcon = sevConfig.icon;

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.2 }}
      >
        <Paper
          sx={{
            p: 2,
            mb: 1.5,
            background: 'rgba(255, 255, 255, 0.02)',
            backdropFilter: 'blur(10px)',
            border: '1px solid',
            borderColor: 'divider',
            borderLeft: `4px solid ${typeConfig.color}`,
            transition: 'all 0.2s',
            cursor: 'pointer',
            '&:hover': {
              background: 'rgba(255, 255, 255, 0.04)',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
            }
          }}
          onClick={() => onToggle(entry.id)}
        >
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
            {/* Timeline dot */}
            <Box sx={{
              p: 1,
              borderRadius: 1.5,
              bgcolor: typeConfig.bgColor,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}>
              <TypeIcon style={{ width: 20, height: 20, color: typeConfig.color }} />
            </Box>

            {/* Main content */}
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5, flexWrap: 'wrap' }}>
                {/* Event type badge */}
                <Chip
                  size="small"
                  label={typeConfig.label}
                  sx={{
                    bgcolor: typeConfig.bgColor,
                    color: typeConfig.color,
                    fontWeight: 600,
                    fontSize: '0.7rem',
                    height: 22
                  }}
                />

                {/* Severity badge */}
                <Chip
                  size="small"
                  icon={<SevIcon style={{ width: 14, height: 14, color: sevConfig.color }} />}
                  label={sevConfig.label}
                  sx={{
                    bgcolor: sevConfig.bgColor,
                    color: sevConfig.color,
                    fontWeight: 500,
                    fontSize: '0.7rem',
                    height: 22,
                    '& .MuiChip-icon': { ml: 0.5 }
                  }}
                />

                {/* Timestamp */}
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, ml: 'auto' }}>
                  <ClockIcon style={{ width: 14, height: 14, color: '#6b7280' }} />
                  <Typography variant="caption" color="text.secondary">
                    {formatTimestamp(entry.timestamp)}
                  </Typography>
                </Box>
              </Box>

              {/* Action description */}
              <Typography variant="body1" sx={{ fontWeight: 500, mb: 0.5 }}>
                {entry.action}
              </Typography>

              {/* User and IP */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexWrap: 'wrap' }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <UserIcon style={{ width: 14, height: 14, color: '#6b7280' }} />
                  <Typography variant="body2" color="text.secondary">
                    {entry.user || 'System'}
                  </Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <GlobeAltIcon style={{ width: 14, height: 14, color: '#6b7280' }} />
                  <Typography variant="body2" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.8rem' }}>
                    {entry.ip_address || 'N/A'}
                  </Typography>
                </Box>
                {entry.resource && (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                    <ServerIcon style={{ width: 14, height: 14, color: '#6b7280' }} />
                    <Typography variant="body2" color="text.secondary">
                      {entry.resource}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>

            {/* Expand toggle */}
            <IconButton size="small" sx={{ ml: 1 }}>
              {isExpanded ? (
                <ChevronUpIcon style={{ width: 20, height: 20 }} />
              ) : (
                <ChevronDownIcon style={{ width: 20, height: 20 }} />
              )}
            </IconButton>
          </Box>

          {/* Expanded details */}
          <Collapse in={isExpanded}>
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                    User Agent
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ComputerDesktopIcon style={{ width: 16, height: 16, color: '#6b7280' }} />
                    <Typography
                      variant="body2"
                      sx={{
                        fontFamily: 'monospace',
                        fontSize: '0.75rem',
                        wordBreak: 'break-all',
                        color: 'text.secondary'
                      }}
                    >
                      {entry.user_agent || 'Unknown'}
                    </Typography>
                  </Box>
                </Grid>
                {entry.metadata && (
                  <Grid item xs={12}>
                    <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 0.5 }}>
                      Metadata
                    </Typography>
                    <Paper
                      variant="outlined"
                      sx={{
                        p: 1.5,
                        bgcolor: 'rgba(0,0,0,0.02)',
                        borderRadius: 1
                      }}
                    >
                      <Typography
                        variant="body2"
                        component="pre"
                        sx={{
                          fontFamily: 'monospace',
                          fontSize: '0.75rem',
                          margin: 0,
                          whiteSpace: 'pre-wrap',
                          wordBreak: 'break-all'
                        }}
                      >
                        {JSON.stringify(entry.metadata, null, 2)}
                      </Typography>
                    </Paper>
                  </Grid>
                )}
              </Grid>
            </Box>
          </Collapse>
        </Paper>
      </motion.div>
    );
  };

  return (
    <Box sx={{ p: 3 }}>
      <PageHeader
        title="System Audit Log"
        subtitle="Monitor all system, user, and administrative actions"
        actions={(
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <ArrowPathIcon style={{ width: 16, height: 16 }} />
                  Auto-refresh
                </Typography>
              }
              sx={{ mr: 1 }}
            />
            <Button
              variant="outlined"
              startIcon={<ArrowPathIcon style={{ width: 18, height: 18 }} />}
              onClick={fetchAuditLog}
              disabled={loading}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<DocumentArrowDownIcon style={{ width: 18, height: 18 }} />}
              onClick={handleExport}
              disabled={exporting || loading}
            >
              {exporting ? 'Exporting...' : 'Export CSV'}
            </Button>
          </Box>
        )}
      />

      {error && (
        <Alert severity="warning" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error} - Showing demo data
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Total Events"
            value={totalEntries}
            icon={ClockIcon}
            color="#3b82f6"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Info"
            value={stats.bySeverity?.info || 0}
            icon={InformationCircleIcon}
            color="#3b82f6"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Warnings"
            value={stats.bySeverity?.warning || 0}
            icon={ExclamationTriangleIcon}
            color="#f59e0b"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Errors"
            value={(stats.bySeverity?.error || 0) + (stats.bySeverity?.critical || 0)}
            icon={ExclamationCircleIcon}
            color="#ef4444"
          />
        </Grid>
      </Grid>

      {/* Filter Bar */}
      <Paper
        sx={{
          p: 2,
          mb: 3,
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(10px)',
          border: '1px solid',
          borderColor: 'divider'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: showFilters ? 2 : 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FunnelIcon style={{ width: 20, height: 20 }} />
            <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
              Filters
            </Typography>
            {(eventType !== 'all' || severity !== 'all' || userSearch || searchQuery || dateRange !== '24h') && (
              <Chip
                size="small"
                label="Active"
                color="primary"
                sx={{ ml: 1 }}
              />
            )}
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button size="small" onClick={handleResetFilters}>
              Reset
            </Button>
            <IconButton size="small" onClick={() => setShowFilters(!showFilters)}>
              {showFilters ? (
                <ChevronUpIcon style={{ width: 20, height: 20 }} />
              ) : (
                <ChevronDownIcon style={{ width: 20, height: 20 }} />
              )}
            </IconButton>
          </Box>
        </Box>

        <Collapse in={showFilters}>
          <Grid container spacing={2}>
            {/* Date Range */}
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Date Range</InputLabel>
                <Select
                  value={dateRange}
                  onChange={(e) => setDateRange(e.target.value)}
                  label="Date Range"
                >
                  {DATE_RANGES.map(range => (
                    <MenuItem key={range.value} value={range.value}>
                      {range.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Custom Date Range */}
            {dateRange === 'custom' && (
              <>
                <Grid item xs={12} sm={6} md={2}>
                  <TextField
                    type="date"
                    size="small"
                    fullWidth
                    label="From"
                    value={customDateFrom}
                    onChange={(e) => setCustomDateFrom(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6} md={2}>
                  <TextField
                    type="date"
                    size="small"
                    fullWidth
                    label="To"
                    value={customDateTo}
                    onChange={(e) => setCustomDateTo(e.target.value)}
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
              </>
            )}

            {/* Event Type */}
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Event Type</InputLabel>
                <Select
                  value={eventType}
                  onChange={(e) => setEventType(e.target.value)}
                  label="Event Type"
                >
                  <MenuItem value="all">All Types</MenuItem>
                  {Object.entries(EVENT_TYPES).map(([key, config]) => (
                    <MenuItem key={key} value={key}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: config.color }} />
                        {config.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* Severity */}
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Severity</InputLabel>
                <Select
                  value={severity}
                  onChange={(e) => setSeverity(e.target.value)}
                  label="Severity"
                >
                  <MenuItem value="all">All Severities</MenuItem>
                  {Object.entries(SEVERITIES).map(([key, config]) => (
                    <MenuItem key={key} value={key}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: config.color }} />
                        {config.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {/* User Search */}
            <Grid item xs={12} sm={6} md={dateRange === 'custom' ? 2 : 3}>
              <TextField
                size="small"
                fullWidth
                label="User"
                placeholder="Search by user..."
                value={userSearch}
                onChange={(e) => setUserSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <UserIcon style={{ width: 18, height: 18, color: '#6b7280' }} />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>

            {/* Search Query */}
            <Grid item xs={12} sm={6} md={dateRange === 'custom' ? 2 : 3}>
              <TextField
                size="small"
                fullWidth
                label="Search"
                placeholder="Search actions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <MagnifyingGlassIcon style={{ width: 18, height: 18, color: '#6b7280' }} />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>
          </Grid>
        </Collapse>
      </Paper>

      {/* Timeline */}
      <Paper
        sx={{
          p: 2,
          background: 'rgba(255, 255, 255, 0.02)',
          backdropFilter: 'blur(10px)',
          border: '1px solid',
          borderColor: 'divider',
          minHeight: 400
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
            Audit Timeline
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Showing {entries.length} of {totalEntries.toLocaleString()} events
          </Typography>
        </Box>

        <Divider sx={{ mb: 2 }} />

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : entries.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <ClockIcon style={{ width: 48, height: 48, color: '#6b7280', marginBottom: 16 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No audit entries found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Try adjusting your filters or date range
            </Typography>
          </Box>
        ) : (
          <AnimatePresence mode="popLayout">
            {entries.map(entry => (
              <TimelineEntry
                key={entry.id}
                entry={entry}
                isExpanded={expandedEntries.has(entry.id)}
                onToggle={toggleExpanded}
              />
            ))}
          </AnimatePresence>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(e, newPage) => setPage(newPage)}
              color="primary"
              showFirstButton
              showLastButton
            />
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default SystemAuditLog;
