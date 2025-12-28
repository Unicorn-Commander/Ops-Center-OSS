/**
 * Forgejo Management Page
 * Admin interface for managing Forgejo Git service (organizations and repositories)
 *
 * Features:
 * - Instance overview with statistics
 * - Organization list with repository counts
 * - Repository browser by organization
 * - Quick access links to Forgejo
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
  CircularProgress,
  Collapse,
  Link as MuiLink,
  TableSortLabel,
  Tabs,
  Tab,
  TextField,
  InputAdornment
} from '@mui/material';
import {
  Business as OrgIcon,
  Folder as RepoIcon,
  CheckCircle as CheckIcon,
  OpenInNew as ExternalIcon,
  ExpandMore as ExpandIcon,
  ChevronRight as CollapseIcon,
  ContentCopy as CopyIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { useTheme } from '../../contexts/ThemeContext';

const ForgejoManagement = () => {
  // State management
  const [stats, setStats] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [repositories, setRepositories] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // UI state
  const [expandedOrg, setExpandedOrg] = useState(null);
  const [selectedOrg, setSelectedOrg] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [sortOrder, setSortOrder] = useState('asc');
  const [searchQuery, setSearchQuery] = useState('');

  const { currentTheme } = useTheme();

  // ============================================
  // API Functions
  // ============================================

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/forgejo/stats', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch Forgejo stats');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching Forgejo stats:', err);
      setError(err.message);
    }
  };

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('/api/v1/forgejo/orgs', {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch organizations');
      }

      const data = await response.json();
      // API returns {organizations: [...], count: N}
      setOrganizations(data.organizations || data || []);
    } catch (err) {
      console.error('Error fetching organizations:', err);
      setError(err.message);
    }
  };

  const fetchOrgRepos = async (orgName) => {
    if (repositories[orgName]) {
      // Already fetched
      return;
    }

    try {
      const response = await fetch(`/api/v1/forgejo/orgs/${orgName}/repos`, {
        credentials: 'include',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch repositories for ${orgName}`);
      }

      const data = await response.json();
      setRepositories(prev => ({
        ...prev,
        [orgName]: data.repositories || data || []
      }));
    } catch (err) {
      console.error(`Error fetching repos for ${orgName}:`, err);
      setError(err.message);
    }
  };

  const refreshAll = async () => {
    setLoading(true);
    setError(null);
    await Promise.all([
      fetchStats(),
      fetchOrganizations()
    ]);
    setLoading(false);
    setSuccess('Data refreshed successfully');
    setTimeout(() => setSuccess(null), 3000);
  };

  // ============================================
  // Event Handlers
  // ============================================

  const handleExpandOrg = async (orgName) => {
    if (expandedOrg === orgName) {
      setExpandedOrg(null);
    } else {
      setExpandedOrg(orgName);
      await fetchOrgRepos(orgName);
    }
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
    setTimeout(() => setSuccess(null), 2000);
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([
        fetchStats(),
        fetchOrganizations()
      ]);
      setLoading(false);
    };

    loadData();
  }, []);

  // ============================================
  // Render Helpers
  // ============================================

  const sortedOrgs = [...organizations].sort((a, b) => {
    let aVal, bVal;
    if (sortBy === 'name') {
      aVal = a.name || a.username;
      bVal = b.name || b.username;
    } else if (sortBy === 'repos') {
      aVal = a.repo_count || 0;
      bVal = b.repo_count || 0;
    }

    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : -1;
    } else {
      return aVal < bVal ? 1 : -1;
    }
  });

  const filteredOrgs = sortedOrgs.filter(org => {
    if (!searchQuery) return true;
    const name = org.name || org.username || '';
    const desc = org.description || '';
    return name.toLowerCase().includes(searchQuery.toLowerCase()) ||
           desc.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const allRepos = Object.values(repositories).flat();
  const filteredRepos = selectedOrg === 'all'
    ? allRepos
    : repositories[selectedOrg] || [];

  // ============================================
  // Main Render
  // ============================================

  if (loading && !stats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box
        sx={{
          background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)',
          borderRadius: 2,
          p: 3,
          mb: 3,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Box>
          <Typography variant="h4" component="h1" sx={{ fontWeight: 700, mb: 0.5 }}>
            Forgejo Git Service
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Manage organizations and repositories
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={refreshAll}
            disabled={loading}
            sx={{
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: 2
              }
            }}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<ExternalIcon />}
            onClick={() => window.open(stats?.instance_url || 'https://git.your-domain.com', '_blank')}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: 2,
              transition: 'all 0.2s',
              '&:hover': {
                transform: 'translateY(-2px)',
                boxShadow: 4,
                background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
              }
            }}
          >
            Open Forgejo
          </Button>
        </Box>
      </Box>

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* Instance Overview Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(102, 126, 234, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Organizations
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {stats?.total_organizations || 0}
                  </Typography>
                </Box>
                <OrgIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(240, 147, 251, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Repositories
                  </Typography>
                  <Typography variant="h3" sx={{ fontWeight: 700 }}>
                    {stats?.total_repositories || 0}
                  </Typography>
                </Box>
                <RepoIcon sx={{ fontSize: 48, opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white',
              transition: 'transform 0.2s, box-shadow 0.2s',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: '0 12px 24px rgba(79, 172, 254, 0.3)'
              }
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography sx={{ opacity: 0.9, fontSize: '0.875rem', mb: 1 }}>
                    Instance Status
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 2 }}>
                    <CheckIcon sx={{ fontSize: 32 }} />
                    <Typography variant="h5" sx={{ fontWeight: 600 }}>
                      Online
                    </Typography>
                  </Box>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Organizations Table */}
      <Paper sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: 2, mb: 3 }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Organizations
            </Typography>
            <TextField
              size="small"
              placeholder="Search organizations..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon fontSize="small" />
                  </InputAdornment>
                )
              }}
              sx={{ width: 300 }}
            />
          </Box>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)' }}>
                <TableCell sx={{ width: 50 }}></TableCell>
                <TableCell sx={{ fontWeight: 700 }}>
                  <TableSortLabel
                    active={sortBy === 'name'}
                    direction={sortBy === 'name' ? sortOrder : 'asc'}
                    onClick={() => handleSort('name')}
                  >
                    Name
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Description</TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Visibility</TableCell>
                <TableCell sx={{ fontWeight: 700, textAlign: 'center' }}>
                  <TableSortLabel
                    active={sortBy === 'repos'}
                    direction={sortBy === 'repos' ? sortOrder : 'asc'}
                    onClick={() => handleSort('repos')}
                  >
                    Repositories
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ fontWeight: 700 }}>Link</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredOrgs.map((org) => (
                <React.Fragment key={org.id}>
                  <TableRow
                    hover
                    sx={{
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      '&:hover': {
                        backgroundColor: 'rgba(102, 126, 234, 0.04)',
                        transform: 'scale(1.001)'
                      }
                    }}
                  >
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => handleExpandOrg(org.username || org.name)}
                      >
                        {expandedOrg === (org.username || org.name) ? <ExpandIcon /> : <CollapseIcon />}
                      </IconButton>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <OrgIcon color="primary" />
                        <Typography variant="body1" fontWeight="bold">
                          {org.name || org.username}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" color="text.secondary">
                        {org.description || 'No description'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={org.visibility || 'public'}
                        size="small"
                        color={org.visibility === 'private' ? 'error' : 'success'}
                        sx={{ textTransform: 'capitalize' }}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={org.repo_count || 0}
                        size="small"
                        color="primary"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell>
                      <Tooltip title="Open in Forgejo">
                        <IconButton
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(org.html_url || `${stats?.instance_url}/${org.username}`, '_blank');
                          }}
                        >
                          <ExternalIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                  {/* Expandable Repository List */}
                  <TableRow>
                    <TableCell colSpan={6} sx={{ py: 0, borderBottom: 0 }}>
                      <Collapse in={expandedOrg === (org.username || org.name)} timeout="auto" unmountOnExit>
                        <Box sx={{ p: 2, backgroundColor: 'rgba(102, 126, 234, 0.02)' }}>
                          {repositories[org.username || org.name] ? (
                            <Table size="small">
                              <TableHead>
                                <TableRow>
                                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Repository</TableCell>
                                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Description</TableCell>
                                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Size</TableCell>
                                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Updated</TableCell>
                                  <TableCell sx={{ fontWeight: 600, fontSize: '0.75rem' }}>Clone URL</TableCell>
                                </TableRow>
                              </TableHead>
                              <TableBody>
                                {repositories[org.username || org.name].map((repo) => (
                                  <TableRow key={repo.id}>
                                    <TableCell>
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                        <RepoIcon fontSize="small" color="action" />
                                        <MuiLink
                                          href={repo.html_url}
                                          target="_blank"
                                          sx={{ fontWeight: 500, fontSize: '0.875rem' }}
                                        >
                                          {repo.name}
                                        </MuiLink>
                                        {repo.private && (
                                          <Chip label="private" size="small" color="error" sx={{ height: 16, fontSize: '0.6rem' }} />
                                        )}
                                      </Box>
                                    </TableCell>
                                    <TableCell>
                                      <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.75rem' }}>
                                        {repo.description || 'No description'}
                                      </Typography>
                                    </TableCell>
                                    <TableCell>
                                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                        {repo.size ? `${(repo.size / 1024).toFixed(1)} MB` : '-'}
                                      </Typography>
                                    </TableCell>
                                    <TableCell>
                                      <Typography variant="body2" sx={{ fontSize: '0.75rem' }}>
                                        {repo.updated_at ? new Date(repo.updated_at).toLocaleDateString() : '-'}
                                      </Typography>
                                    </TableCell>
                                    <TableCell>
                                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                                        <Typography
                                          variant="body2"
                                          sx={{
                                            fontFamily: 'monospace',
                                            fontSize: '0.7rem',
                                            maxWidth: 200,
                                            overflow: 'hidden',
                                            textOverflow: 'ellipsis',
                                            whiteSpace: 'nowrap'
                                          }}
                                        >
                                          {repo.clone_url}
                                        </Typography>
                                        <Tooltip title="Copy clone URL">
                                          <IconButton
                                            size="small"
                                            onClick={() => copyToClipboard(repo.clone_url)}
                                            sx={{ p: 0.5 }}
                                          >
                                            <CopyIcon sx={{ fontSize: 14 }} />
                                          </IconButton>
                                        </Tooltip>
                                      </Box>
                                    </TableCell>
                                  </TableRow>
                                ))}
                              </TableBody>
                            </Table>
                          ) : (
                            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                              <CircularProgress size={24} />
                            </Box>
                          )}
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Repository Browser (Tabbed View) */}
      <Paper sx={{ borderRadius: 2, overflow: 'hidden', boxShadow: 2 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider', p: 2 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Repository Browser
          </Typography>
        </Box>
        <Tabs
          value={selectedOrg}
          onChange={(e, newValue) => {
            setSelectedOrg(newValue);
            if (newValue !== 'all') {
              fetchOrgRepos(newValue);
            }
          }}
          variant="scrollable"
          scrollButtons="auto"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab label="All Repositories" value="all" />
          {organizations.map((org) => (
            <Tab
              key={org.id}
              label={`${org.name || org.username} (${org.repo_count || 0})`}
              value={org.username || org.name}
            />
          ))}
        </Tabs>
        <Box sx={{ p: 2 }}>
          {filteredRepos.length > 0 ? (
            <Grid container spacing={2}>
              {filteredRepos.map((repo) => (
                <Grid item xs={12} md={6} key={repo.id}>
                  <Paper
                    variant="outlined"
                    sx={{
                      p: 2,
                      transition: 'all 0.2s',
                      '&:hover': {
                        boxShadow: 2,
                        transform: 'translateY(-2px)'
                      }
                    }}
                  >
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <RepoIcon color="primary" />
                        <MuiLink
                          href={repo.html_url}
                          target="_blank"
                          sx={{ fontWeight: 600, fontSize: '1rem' }}
                        >
                          {repo.name}
                        </MuiLink>
                      </Box>
                      {repo.private && (
                        <Chip label="Private" size="small" color="error" />
                      )}
                    </Box>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1, minHeight: 40 }}>
                      {repo.description || 'No description'}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 2, fontSize: '0.75rem', color: 'text.secondary', mb: 1 }}>
                      <span>Size: {repo.size ? `${(repo.size / 1024).toFixed(1)} MB` : '-'}</span>
                      <span>Updated: {repo.updated_at ? new Date(repo.updated_at).toLocaleDateString() : '-'}</span>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <TextField
                        size="small"
                        fullWidth
                        value={repo.clone_url}
                        InputProps={{
                          readOnly: true,
                          endAdornment: (
                            <InputAdornment position="end">
                              <Tooltip title="Copy clone URL">
                                <IconButton
                                  size="small"
                                  onClick={() => copyToClipboard(repo.clone_url)}
                                >
                                  <CopyIcon fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </InputAdornment>
                          ),
                          sx: { fontFamily: 'monospace', fontSize: '0.75rem' }
                        }}
                      />
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Typography variant="body1" color="text.secondary">
                {selectedOrg === 'all' ? 'No repositories found' : 'No repositories in this organization'}
              </Typography>
            </Box>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default ForgejoManagement;
