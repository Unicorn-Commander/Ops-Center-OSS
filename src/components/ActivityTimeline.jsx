import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Paper,
  Chip,
  IconButton,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Login as LoginIcon,
  Logout as LogoutIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Security as SecurityIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';

const ActivityTimeline = ({ userId }) => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionFilter, setActionFilter] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [pagination, setPagination] = useState({
    total: 0,
    offset: 0,
    limit: 50,
    hasMore: false,
  });

  useEffect(() => {
    if (userId) {
      fetchActivities();
    }
  }, [userId, actionFilter]);

  const fetchActivities = async (offset = 0) => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: pagination.limit.toString(),
        offset: offset.toString(),
      });

      if (actionFilter) {
        params.append('action_filter', actionFilter);
      }

      const response = await fetch(
        `/api/v1/admin/users/${userId}/activity?${params}`,
        {
          credentials: 'include',
        }
      );

      if (!response.ok) throw new Error('Failed to fetch activity');

      const data = await response.json();
      if (offset === 0) {
        setActivities(data.activities || []);
      } else {
        setActivities((prev) => [...prev, ...(data.activities || [])]);
      }
      setPagination(data.pagination);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    fetchActivities(pagination.offset + pagination.limit);
  };

  const getActionIcon = (action, result) => {
    if (result === 'failure' || result === 'error') {
      return <ErrorIcon />;
    }

    if (action.includes('login')) return <LoginIcon />;
    if (action.includes('logout')) return <LogoutIcon />;
    if (action.includes('created') || action.includes('add')) return <AddIcon />;
    if (action.includes('updated') || action.includes('edit')) return <EditIcon />;
    if (action.includes('deleted') || action.includes('remove')) return <DeleteIcon />;
    if (action.includes('role') || action.includes('security')) return <SecurityIcon />;

    return <InfoIcon />;
  };

  const getActionColor = (result) => {
    switch (result) {
      case 'success':
        return 'success';
      case 'failure':
      case 'error':
        return 'error';
      case 'denied':
        return 'warning';
      default:
        return 'info';
    }
  };

  const getActionLabel = (action) => {
    // Convert action to readable format
    return action
      .replace(/_/g, ' ')
      .split(' ')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const groupByDate = (activities) => {
    const groups = {};
    activities.forEach((activity) => {
      const date = new Date(activity.timestamp).toLocaleDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(activity);
    });
    return groups;
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  const groupedActivities = groupByDate(activities);

  return (
    <Box>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          mb: 2,
        }}
      >
        <Typography variant="h6">Activity Timeline</Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Filter by Action</InputLabel>
            <Select
              value={actionFilter}
              label="Filter by Action"
              onChange={(e) => setActionFilter(e.target.value)}
            >
              <MenuItem value="">All Actions</MenuItem>
              <MenuItem value="auth.login">Login</MenuItem>
              <MenuItem value="auth.logout">Logout</MenuItem>
              <MenuItem value="user_created">User Created</MenuItem>
              <MenuItem value="user_updated">User Updated</MenuItem>
              <MenuItem value="role_assigned">Role Assigned</MenuItem>
              <MenuItem value="role_removed">Role Removed</MenuItem>
              <MenuItem value="api_key_created">API Key Created</MenuItem>
              <MenuItem value="api_key_revoked">API Key Revoked</MenuItem>
              <MenuItem value="permission_denied">Permission Denied</MenuItem>
            </Select>
          </FormControl>
          <IconButton onClick={() => fetchActivities(0)} size="small">
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {loading && activities.length === 0 ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : activities.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            No activity found
          </Typography>
        </Paper>
      ) : (
        <>
          {Object.entries(groupedActivities).map(([date, dateActivities]) => (
            <Box key={date} sx={{ mb: 3 }}>
              <Typography
                variant="subtitle1"
                fontWeight="bold"
                sx={{ mb: 1, color: 'primary.main' }}
              >
                {date}
              </Typography>

              <Timeline position="right">
                {dateActivities.map((activity, index) => (
                  <TimelineItem key={activity.id}>
                    <TimelineOppositeContent
                      sx={{ m: 'auto 0', minWidth: '80px' }}
                      align="right"
                      variant="body2"
                      color="text.secondary"
                    >
                      {formatTime(activity.timestamp)}
                    </TimelineOppositeContent>
                    <TimelineSeparator>
                      <TimelineConnector
                        sx={{
                          bgcolor:
                            index === 0 ? 'transparent' : 'grey.400',
                        }}
                      />
                      <TimelineDot color={getActionColor(activity.result)}>
                        {getActionIcon(activity.action, activity.result)}
                      </TimelineDot>
                      <TimelineConnector
                        sx={{
                          bgcolor:
                            index === dateActivities.length - 1
                              ? 'transparent'
                              : 'grey.400',
                        }}
                      />
                    </TimelineSeparator>
                    <TimelineContent sx={{ py: '12px', px: 2 }}>
                      <Paper
                        elevation={1}
                        sx={{
                          p: 2,
                          bgcolor:
                            activity.result === 'failure' ||
                            activity.result === 'error'
                              ? 'error.50'
                              : 'background.paper',
                        }}
                      >
                        <Box
                          sx={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            mb: 1,
                          }}
                        >
                          <Typography variant="subtitle2" fontWeight="bold">
                            {getActionLabel(activity.action)}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 0.5 }}>
                            <Chip
                              label={activity.result}
                              size="small"
                              color={getActionColor(activity.result)}
                            />
                            {expandedId === activity.id ? (
                              <IconButton
                                size="small"
                                onClick={() => setExpandedId(null)}
                              >
                                <ExpandLessIcon />
                              </IconButton>
                            ) : (
                              <IconButton
                                size="small"
                                onClick={() => setExpandedId(activity.id)}
                              >
                                <ExpandMoreIcon />
                              </IconButton>
                            )}
                          </Box>
                        </Box>

                        {activity.resource_type && (
                          <Typography variant="body2" color="text.secondary">
                            Resource: {activity.resource_type}
                            {activity.resource_id && ` (${activity.resource_id})`}
                          </Typography>
                        )}

                        {activity.ip_address && (
                          <Typography variant="body2" color="text.secondary">
                            IP: {activity.ip_address}
                          </Typography>
                        )}

                        {activity.error_message && (
                          <Typography
                            variant="body2"
                            color="error"
                            sx={{ mt: 1 }}
                          >
                            Error: {activity.error_message}
                          </Typography>
                        )}

                        <Collapse in={expandedId === activity.id}>
                          <Box
                            sx={{
                              mt: 2,
                              p: 1,
                              bgcolor: 'background.default',
                              borderRadius: 1,
                            }}
                          >
                            {activity.user_agent && (
                              <Typography
                                variant="caption"
                                display="block"
                                color="text.secondary"
                              >
                                User Agent: {activity.user_agent}
                              </Typography>
                            )}
                            {activity.session_id && (
                              <Typography
                                variant="caption"
                                display="block"
                                color="text.secondary"
                              >
                                Session: {activity.session_id}
                              </Typography>
                            )}
                            {activity.metadata &&
                              Object.keys(activity.metadata).length > 0 && (
                                <>
                                  <Typography
                                    variant="caption"
                                    display="block"
                                    fontWeight="bold"
                                    sx={{ mt: 1 }}
                                  >
                                    Metadata:
                                  </Typography>
                                  <Box
                                    component="pre"
                                    sx={{
                                      fontSize: '11px',
                                      overflow: 'auto',
                                      maxHeight: '200px',
                                      p: 1,
                                      bgcolor: 'grey.100',
                                      borderRadius: 1,
                                    }}
                                  >
                                    {JSON.stringify(activity.metadata, null, 2)}
                                  </Box>
                                </>
                              )}
                          </Box>
                        </Collapse>
                      </Paper>
                    </TimelineContent>
                  </TimelineItem>
                ))}
              </Timeline>
            </Box>
          ))}

          {pagination.hasMore && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
              <Button
                variant="outlined"
                onClick={loadMore}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={16} /> : undefined}
              >
                {loading ? 'Loading...' : 'Load More'}
              </Button>
            </Box>
          )}

          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ display: 'block', textAlign: 'center', mt: 2 }}
          >
            Showing {activities.length} of {pagination.total} activities
          </Typography>
        </>
      )}
    </Box>
  );
};

export default ActivityTimeline;
