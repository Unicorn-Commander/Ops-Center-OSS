import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, Button, Collapse, IconButton } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  UserPlusIcon,
  ArrowUpIcon,
  ArrowPathIcon,
  Cog6ToothIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  ChevronDownIcon,
  ArrowRightIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function RecentActivityWidget({ activities, limit = 10, autoRefresh = false }) {
  const { theme, currentTheme } = useTheme();
  const navigate = useNavigate();
  const [expanded, setExpanded] = useState({});
  const [displayActivities, setDisplayActivities] = useState([]);

  // Mock activities if none provided
  const mockActivities = [
    {
      id: 1,
      type: 'user_login',
      user: 'admin@example.com',
      action: 'User logged in',
      details: 'Successful authentication via Google SSO',
      timestamp: new Date(Date.now() - 2 * 60 * 1000),
      severity: 'info'
    },
    {
      id: 2,
      type: 'tier_upgrade',
      user: 'john@example.com',
      action: 'Tier upgrade',
      details: 'Upgraded from Starter to Professional tier',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      severity: 'success'
    },
    {
      id: 3,
      type: 'service_restart',
      user: 'system',
      action: 'Service restarted',
      details: 'ops-center-direct container restarted successfully',
      timestamp: new Date(Date.now() - 35 * 60 * 1000),
      severity: 'warning'
    },
    {
      id: 4,
      type: 'config_change',
      user: 'admin',
      action: 'Configuration updated',
      details: 'Modified system settings: email provider configuration',
      timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
      severity: 'info'
    },
    {
      id: 5,
      type: 'error',
      user: 'system',
      action: 'API error detected',
      details: 'Failed to connect to external service: timeout after 30s',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      severity: 'error'
    },
    {
      id: 6,
      type: 'user_login',
      user: 'jane@example.com',
      action: 'User logged in',
      details: 'Successful authentication via GitHub SSO',
      timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
      severity: 'info'
    },
    {
      id: 7,
      type: 'service_start',
      user: 'admin',
      action: 'Service started',
      details: 'unicorn-brigade service started manually',
      timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
      severity: 'success'
    },
    {
      id: 8,
      type: 'user_created',
      user: 'admin',
      action: 'User created',
      details: 'New user account created: test@example.com',
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
      severity: 'info'
    },
    {
      id: 9,
      type: 'config_change',
      user: 'admin',
      action: 'Configuration updated',
      details: 'Updated LLM model: changed default model to gpt-4',
      timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
      severity: 'info'
    },
    {
      id: 10,
      type: 'warning',
      user: 'system',
      action: 'Resource warning',
      details: 'Disk usage exceeded 80% threshold on /data volume',
      timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000),
      severity: 'warning'
    }
  ];

  useEffect(() => {
    const data = activities && activities.length > 0 ? activities : mockActivities;
    setDisplayActivities(data.slice(0, limit));
  }, [activities, limit]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // In production, this would fetch fresh data
      console.log('Auto-refreshing activity feed...');
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const getActivityIcon = (type) => {
    const icons = {
      user_login: UserPlusIcon,
      user_created: UserPlusIcon,
      tier_upgrade: ArrowUpIcon,
      service_restart: ArrowPathIcon,
      service_start: CheckCircleIcon,
      config_change: Cog6ToothIcon,
      error: ExclamationTriangleIcon,
      warning: ExclamationTriangleIcon,
      info: InformationCircleIcon
    };
    return icons[type] || InformationCircleIcon;
  };

  const getSeverityColor = (severity) => {
    const colors = {
      success: {
        dot: 'bg-emerald-500',
        icon: 'text-emerald-400',
        bg: 'bg-emerald-500/10',
        border: 'border-emerald-500/30'
      },
      warning: {
        dot: 'bg-yellow-500',
        icon: 'text-yellow-400',
        bg: 'bg-yellow-500/10',
        border: 'border-yellow-500/30'
      },
      error: {
        dot: 'bg-red-500',
        icon: 'text-red-400',
        bg: 'bg-red-500/10',
        border: 'border-red-500/30'
      },
      info: {
        dot: 'bg-blue-500',
        icon: 'text-blue-400',
        bg: 'bg-blue-500/10',
        border: 'border-blue-500/30'
      }
    };
    return colors[severity] || colors.info;
  };

  const formatTimeAgo = (date) => {
    const seconds = Math.floor((new Date() - date) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  const toggleExpanded = (id) => {
    setExpanded(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleViewAll = () => {
    navigate('/admin/monitoring/logs');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <Card className={`${theme.card} h-full flex flex-col`}>
        <CardContent className="p-6 flex-1 flex flex-col">
          {/* Header */}
          <Box className="flex items-center justify-between mb-6">
            <Typography variant="h6" className={`font-bold ${theme.text.primary}`}>
              Recent Activity
            </Typography>
            {autoRefresh && (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <ArrowPathIcon className={`h-4 w-4 ${theme.text.accent}`} />
              </motion.div>
            )}
          </Box>

          {/* Timeline */}
          <Box className="flex-1 overflow-y-auto max-h-[500px] pr-2" sx={{ scrollbarWidth: 'thin' }}>
            <Box className="relative">
              {/* Vertical timeline line */}
              <Box
                className="absolute left-4 top-0 bottom-0 w-0.5"
                sx={{
                  background: currentTheme === 'unicorn'
                    ? 'linear-gradient(to bottom, rgba(168, 85, 247, 0.3), rgba(168, 85, 247, 0.1))'
                    : currentTheme === 'light'
                    ? 'linear-gradient(to bottom, rgba(59, 130, 246, 0.3), rgba(59, 130, 246, 0.1))'
                    : 'linear-gradient(to bottom, rgba(59, 130, 246, 0.3), rgba(59, 130, 246, 0.1))'
                }}
              />

              <AnimatePresence>
                {displayActivities.map((activity, index) => {
                  const Icon = getActivityIcon(activity.type);
                  const colors = getSeverityColor(activity.severity);

                  return (
                    <motion.div
                      key={activity.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05, duration: 0.3 }}
                      className="relative pl-12 pb-8 last:pb-0"
                    >
                      {/* Timeline dot */}
                      <Box
                        className={`absolute left-3 top-0 w-3 h-3 rounded-full ${colors.dot} ring-4 ${
                          currentTheme === 'light' ? 'ring-white' : 'ring-gray-900'
                        }`}
                      />

                      {/* Activity card */}
                      <Box
                        className={`p-4 rounded-xl ${colors.bg} border ${colors.border} cursor-pointer hover:shadow-lg transition-all duration-300`}
                        onClick={() => toggleExpanded(activity.id)}
                      >
                        <Box className="flex items-start justify-between mb-2">
                          <Box className="flex items-center gap-3">
                            <Icon className={`h-5 w-5 ${colors.icon}`} />
                            <Box>
                              <Typography
                                variant="body2"
                                className={`font-semibold ${theme.text.primary}`}
                              >
                                {activity.action}
                              </Typography>
                              <Typography
                                variant="caption"
                                className={theme.text.secondary}
                              >
                                {activity.user}
                              </Typography>
                            </Box>
                          </Box>

                          <Box className="flex items-center gap-2">
                            <Typography
                              variant="caption"
                              className={`${theme.text.secondary} whitespace-nowrap`}
                            >
                              {formatTimeAgo(activity.timestamp)}
                            </Typography>
                            <motion.div
                              animate={{ rotate: expanded[activity.id] ? 180 : 0 }}
                              transition={{ duration: 0.2 }}
                            >
                              <ChevronDownIcon className={`h-4 w-4 ${theme.text.secondary}`} />
                            </motion.div>
                          </Box>
                        </Box>

                        {/* Expandable details */}
                        <Collapse in={expanded[activity.id]}>
                          <Box className="mt-3 pt-3 border-t border-gray-700">
                            <Typography
                              variant="body2"
                              className={`${theme.text.secondary} text-sm`}
                            >
                              {activity.details}
                            </Typography>
                          </Box>
                        </Collapse>
                      </Box>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </Box>
          </Box>

          {/* View All Button */}
          <Box className="mt-6 pt-4 border-t border-gray-700">
            <Button
              fullWidth
              variant="outlined"
              onClick={handleViewAll}
              endIcon={<ArrowRightIcon className="h-4 w-4" />}
              sx={{
                color: currentTheme === 'unicorn'
                  ? 'rgba(168, 85, 247, 1)'
                  : currentTheme === 'light'
                  ? 'rgba(59, 130, 246, 1)'
                  : 'rgba(59, 130, 246, 1)',
                borderColor: currentTheme === 'unicorn'
                  ? 'rgba(168, 85, 247, 0.3)'
                  : currentTheme === 'light'
                  ? 'rgba(59, 130, 246, 0.3)'
                  : 'rgba(59, 130, 246, 0.3)',
                '&:hover': {
                  borderColor: currentTheme === 'unicorn'
                    ? 'rgba(168, 85, 247, 0.5)'
                    : 'rgba(59, 130, 246, 0.5)',
                  backgroundColor: currentTheme === 'unicorn'
                    ? 'rgba(168, 85, 247, 0.1)'
                    : 'rgba(59, 130, 246, 0.1)'
                }
              }}
            >
              View All Activity
            </Button>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
}
