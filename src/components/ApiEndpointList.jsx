import React, { useState, useEffect } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Typography,
  Chip,
  TextField,
  InputAdornment,
  Collapse,
  CircularProgress,
  Alert,
  IconButton,
  Drawer,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Search as SearchIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
} from '@mui/icons-material';

/**
 * ApiEndpointList
 *
 * Sidebar component displaying grouped API endpoints with search functionality
 * Mobile-responsive with collapsible drawer on small screens
 */
const ApiEndpointList = ({ onEndpointSelect, selectedEndpoint }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [endpoints, setEndpoints] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedGroups, setExpandedGroups] = useState({});
  const [drawerOpen, setDrawerOpen] = useState(!isMobile);

  useEffect(() => {
    fetchEndpoints();
  }, []);

  useEffect(() => {
    // Auto-close drawer on mobile when endpoint selected
    if (isMobile && selectedEndpoint) {
      setDrawerOpen(false);
    }
  }, [selectedEndpoint, isMobile]);

  const fetchEndpoints = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/docs/endpoints');

      if (!response.ok) {
        throw new Error('Failed to load endpoints');
      }

      const data = await response.json();
      setEndpoints(data);

      // Auto-expand all groups initially
      const expanded = {};
      Object.keys(data).forEach((tag) => {
        expanded[tag] = true;
      });
      setExpandedGroups(expanded);
    } catch (err) {
      console.error('Error loading endpoints:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleGroup = (tag) => {
    setExpandedGroups((prev) => ({
      ...prev,
      [tag]: !prev[tag],
    }));
  };

  const handleSearchChange = (event) => {
    setSearchQuery(event.target.value);
  };

  const getMethodColor = (method) => {
    const colors = {
      GET: 'success',
      POST: 'primary',
      PUT: 'warning',
      DELETE: 'error',
      PATCH: 'secondary',
    };
    return colors[method] || 'default';
  };

  const formatTagName = (tag) => {
    return tag
      .split(/[-_]/)
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  // Filter endpoints based on search query
  const filterEndpoints = (endpointsList) => {
    if (!searchQuery.trim()) return endpointsList;

    return endpointsList.filter((endpoint) => {
      const searchText = `${endpoint.method} ${endpoint.path} ${endpoint.summary}`.toLowerCase();
      return searchText.includes(searchQuery.toLowerCase());
    });
  };

  const EndpointListContent = () => {
    if (loading) {
      return (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
          <CircularProgress size={24} />
        </Box>
      );
    }

    if (error) {
      return (
        <Box sx={{ p: 2 }}>
          <Alert severity="error" variant="outlined">
            {error}
          </Alert>
        </Box>
      );
    }

    return (
      <List sx={{ py: 0 }}>
        {Object.entries(endpoints).map(([tag, endpointsList]) => {
          const filtered = filterEndpoints(endpointsList);

          // Hide groups with no matching endpoints
          if (filtered.length === 0) return null;

          return (
            <Box key={tag}>
              {/* Group Header */}
              <ListItemButton
                onClick={() => handleToggleGroup(tag)}
                sx={{
                  backgroundColor: 'rgba(0, 0, 0, 0.02)',
                  borderBottom: '1px solid rgba(0, 0, 0, 0.08)',
                  py: 1.5,
                  '&:hover': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  },
                }}
              >
                <ListItemText
                  primary={
                    <Typography variant="subtitle2" fontWeight={600}>
                      {formatTagName(tag)}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {filtered.length} endpoint{filtered.length !== 1 ? 's' : ''}
                    </Typography>
                  }
                />
                {expandedGroups[tag] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </ListItemButton>

              {/* Endpoints List */}
              <Collapse in={expandedGroups[tag]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {filtered.map((endpoint, index) => (
                    <ListItemButton
                      key={`${endpoint.method}-${endpoint.path}-${index}`}
                      selected={
                        selectedEndpoint?.method === endpoint.method &&
                        selectedEndpoint?.path === endpoint.path
                      }
                      onClick={() => onEndpointSelect?.(endpoint)}
                      sx={{
                        pl: 3,
                        pr: 2,
                        py: 1,
                        borderLeft: '3px solid transparent',
                        '&.Mui-selected': {
                          borderLeftColor: theme.palette.primary.main,
                          backgroundColor: 'rgba(124, 58, 237, 0.08)',
                          '&:hover': {
                            backgroundColor: 'rgba(124, 58, 237, 0.12)',
                          },
                        },
                      }}
                    >
                      <Box sx={{ width: '100%' }}>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 1,
                            mb: 0.5,
                          }}
                        >
                          <Chip
                            label={endpoint.method}
                            size="small"
                            color={getMethodColor(endpoint.method)}
                            sx={{
                              height: 20,
                              fontSize: '10px',
                              fontWeight: 600,
                              minWidth: 50,
                            }}
                          />
                          {endpoint.deprecated && (
                            <Chip
                              label="DEPRECATED"
                              size="small"
                              color="error"
                              variant="outlined"
                              sx={{
                                height: 20,
                                fontSize: '9px',
                                fontWeight: 600,
                              }}
                            />
                          )}
                        </Box>
                        <Typography
                          variant="body2"
                          sx={{
                            fontFamily: 'monospace',
                            fontSize: '12px',
                            wordBreak: 'break-all',
                            color: 'text.primary',
                          }}
                        >
                          {endpoint.path}
                        </Typography>
                        {endpoint.summary && (
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{
                              display: 'block',
                              mt: 0.5,
                              lineHeight: 1.4,
                            }}
                          >
                            {endpoint.summary}
                          </Typography>
                        )}
                      </Box>
                    </ListItemButton>
                  ))}
                </List>
              </Collapse>
            </Box>
          );
        })}
      </List>
    );
  };

  const drawer = (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'background.paper',
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: '1px solid',
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Typography variant="h6" fontWeight={600}>
          API Endpoints
        </Typography>
        {isMobile && (
          <IconButton onClick={() => setDrawerOpen(false)} size="small">
            <CloseIcon />
          </IconButton>
        )}
      </Box>

      {/* Search Box */}
      <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Search endpoints..."
          value={searchQuery}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
      </Box>

      {/* Endpoints List */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        <EndpointListContent />
      </Box>
    </Box>
  );

  if (isMobile) {
    return (
      <>
        {/* Mobile Menu Button */}
        <IconButton
          onClick={() => setDrawerOpen(true)}
          sx={{
            position: 'fixed',
            left: 16,
            bottom: 16,
            zIndex: 1000,
            backgroundColor: 'primary.main',
            color: 'white',
            '&:hover': {
              backgroundColor: 'primary.dark',
            },
            boxShadow: 3,
          }}
        >
          <MenuIcon />
        </IconButton>

        {/* Mobile Drawer */}
        <Drawer
          anchor="left"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          sx={{
            '& .MuiDrawer-paper': {
              width: '85%',
              maxWidth: 360,
            },
          }}
        >
          {drawer}
        </Drawer>
      </>
    );
  }

  // Desktop - always visible sidebar
  return (
    <Box
      sx={{
        width: 320,
        height: '100%',
        borderRight: '1px solid',
        borderColor: 'divider',
        overflow: 'hidden',
      }}
    >
      {drawer}
    </Box>
  );
};

export default ApiEndpointList;
