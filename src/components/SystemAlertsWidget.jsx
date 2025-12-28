import React, { useState, useEffect } from 'react';
import { Box, Card, CardContent, Typography, IconButton, Alert, AlertTitle, Collapse } from '@mui/material';
import { motion, AnimatePresence } from 'framer-motion';
import {
  XMarkIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ExclamationCircleIcon,
  CheckCircleIcon,
  ChevronDownIcon,
  CircleStackIcon,
  CpuChipIcon,
  ServerIcon,
  ShieldExclamationIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function SystemAlertsWidget({ alerts, onDismiss }) {
  const { theme, currentTheme } = useTheme();
  const [displayAlerts, setDisplayAlerts] = useState([]);
  const [expandedAlerts, setExpandedAlerts] = useState({});

  // Mock alerts if none provided
  const mockAlerts = [
    {
      id: 1,
      type: 'error',
      title: 'Service Down',
      message: 'unicorn-brigade service is not responding',
      details: 'The service stopped unexpectedly at 10:45 AM. Auto-restart failed after 3 attempts. Manual intervention required.',
      timestamp: new Date(Date.now() - 5 * 60 * 1000),
      icon: ServerIcon,
      dismissible: true,
      pulsing: true
    },
    {
      id: 2,
      type: 'warning',
      title: 'Low Disk Space',
      message: 'Disk usage exceeded 85% on /data volume',
      details: 'Current usage: 425GB / 500GB. Consider cleaning up old backups or expanding storage.',
      timestamp: new Date(Date.now() - 15 * 60 * 1000),
      icon: CircleStackIcon,
      dismissible: true,
      pulsing: false
    },
    {
      id: 3,
      type: 'warning',
      title: 'High CPU Usage',
      message: 'CPU usage above 90% for 10 minutes',
      details: 'vLLM service consuming 87% CPU. Consider scaling or optimizing model inference.',
      timestamp: new Date(Date.now() - 25 * 60 * 1000),
      icon: CpuChipIcon,
      dismissible: true,
      pulsing: false
    },
    {
      id: 4,
      type: 'info',
      title: 'Pending Updates',
      message: '3 system updates available',
      details: 'Security patches and feature updates ready to install. Schedule downtime for updates.',
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000),
      icon: ArrowPathIcon,
      dismissible: true,
      pulsing: false
    },
    {
      id: 5,
      type: 'error',
      title: 'Security Warning',
      message: 'Failed login attempts detected',
      details: '15 failed login attempts from IP 192.168.1.100 in the last hour. IP has been temporarily blocked.',
      timestamp: new Date(Date.now() - 45 * 60 * 1000),
      icon: ShieldExclamationIcon,
      dismissible: false,
      pulsing: true
    }
  ];

  useEffect(() => {
    const data = alerts && alerts.length > 0 ? alerts : mockAlerts;
    setDisplayAlerts(data);
  }, [alerts]);

  const getAlertConfig = (type) => {
    const configs = {
      error: {
        severity: 'error',
        color: 'red',
        bgColor: 'bg-red-500/10',
        borderColor: 'border-red-500/30',
        textColor: 'text-red-400',
        icon: ExclamationCircleIcon
      },
      warning: {
        severity: 'warning',
        color: 'yellow',
        bgColor: 'bg-yellow-500/10',
        borderColor: 'border-yellow-500/30',
        textColor: 'text-yellow-400',
        icon: ExclamationTriangleIcon
      },
      info: {
        severity: 'info',
        color: 'blue',
        bgColor: 'bg-blue-500/10',
        borderColor: 'border-blue-500/30',
        textColor: 'text-blue-400',
        icon: InformationCircleIcon
      },
      success: {
        severity: 'success',
        color: 'green',
        bgColor: 'bg-emerald-500/10',
        borderColor: 'border-emerald-500/30',
        textColor: 'text-emerald-400',
        icon: CheckCircleIcon
      }
    };
    return configs[type] || configs.info;
  };

  const handleDismiss = (alertId) => {
    setDisplayAlerts(prev => prev.filter(a => a.id !== alertId));
    if (onDismiss) {
      onDismiss(alertId);
    }
  };

  const toggleExpanded = (alertId) => {
    setExpandedAlerts(prev => ({
      ...prev,
      [alertId]: !prev[alertId]
    }));
  };

  const formatTimestamp = (date) => {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return date.toLocaleDateString();
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
            <Box className="flex items-center gap-2">
              <Typography variant="h6" className={`font-bold ${theme.text.primary}`}>
                System Alerts
              </Typography>
              {displayAlerts.length > 0 && (
                <Box
                  className={`px-2 py-0.5 rounded-full ${
                    displayAlerts.some(a => a.type === 'error')
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-yellow-500/20 text-yellow-400'
                  } text-xs font-semibold`}
                >
                  {displayAlerts.length}
                </Box>
              )}
            </Box>
          </Box>

          {/* Alerts List */}
          <Box className="flex-1 overflow-y-auto max-h-[500px] space-y-3 pr-2" sx={{ scrollbarWidth: 'thin' }}>
            <AnimatePresence mode="popLayout">
              {displayAlerts.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="flex flex-col items-center justify-center h-48"
                >
                  <CheckCircleIcon className="h-16 w-16 text-emerald-400 mb-4" />
                  <Typography variant="body1" className={`${theme.text.primary} font-semibold mb-2`}>
                    All Clear!
                  </Typography>
                  <Typography variant="body2" className={theme.text.secondary}>
                    No system alerts at this time
                  </Typography>
                </motion.div>
              ) : (
                displayAlerts.map((alert, index) => {
                  const config = getAlertConfig(alert.type);
                  const AlertIcon = alert.icon || config.icon;

                  return (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      transition={{ delay: index * 0.05, duration: 0.3 }}
                      layout
                    >
                      <Box
                        className={`relative p-4 rounded-xl ${config.bgColor} border ${config.borderColor} overflow-hidden`}
                      >
                        {/* Pulsing animation for critical alerts */}
                        {alert.pulsing && (
                          <motion.div
                            className={`absolute inset-0 ${config.bgColor}`}
                            animate={{
                              opacity: [0.3, 0.6, 0.3]
                            }}
                            transition={{
                              duration: 2,
                              repeat: Infinity,
                              ease: "easeInOut"
                            }}
                          />
                        )}

                        <Box className="relative z-10">
                          {/* Alert Header */}
                          <Box className="flex items-start justify-between mb-2">
                            <Box className="flex items-start gap-3 flex-1">
                              <AlertIcon className={`h-6 w-6 ${config.textColor} flex-shrink-0 mt-0.5`} />
                              <Box className="flex-1">
                                <Box className="flex items-center gap-2 mb-1">
                                  <Typography
                                    variant="body1"
                                    className={`font-semibold ${theme.text.primary}`}
                                  >
                                    {alert.title}
                                  </Typography>
                                  {alert.pulsing && (
                                    <motion.div
                                      className={`w-2 h-2 rounded-full ${
                                        alert.type === 'error' ? 'bg-red-500' : 'bg-yellow-500'
                                      }`}
                                      animate={{
                                        scale: [1, 1.5, 1],
                                        opacity: [1, 0.5, 1]
                                      }}
                                      transition={{
                                        duration: 1.5,
                                        repeat: Infinity
                                      }}
                                    />
                                  )}
                                </Box>
                                <Typography
                                  variant="body2"
                                  className={theme.text.secondary}
                                >
                                  {alert.message}
                                </Typography>
                                <Typography
                                  variant="caption"
                                  className={`${theme.text.secondary} text-xs mt-1 block`}
                                >
                                  {formatTimestamp(alert.timestamp)}
                                </Typography>
                              </Box>
                            </Box>

                            <Box className="flex items-center gap-1 ml-2">
                              {alert.details && (
                                <IconButton
                                  size="small"
                                  onClick={() => toggleExpanded(alert.id)}
                                >
                                  <motion.div
                                    animate={{ rotate: expandedAlerts[alert.id] ? 180 : 0 }}
                                    transition={{ duration: 0.2 }}
                                  >
                                    <ChevronDownIcon className={`h-4 w-4 ${theme.text.secondary}`} />
                                  </motion.div>
                                </IconButton>
                              )}
                              {alert.dismissible && (
                                <IconButton
                                  size="small"
                                  onClick={() => handleDismiss(alert.id)}
                                >
                                  <XMarkIcon className={`h-4 w-4 ${theme.text.secondary} hover:${config.textColor}`} />
                                </IconButton>
                              )}
                            </Box>
                          </Box>

                          {/* Expandable Details */}
                          {alert.details && (
                            <Collapse in={expandedAlerts[alert.id]}>
                              <Box className="mt-3 pt-3 border-t border-gray-700">
                                <Typography
                                  variant="body2"
                                  className={`${theme.text.secondary} text-sm`}
                                >
                                  {alert.details}
                                </Typography>
                              </Box>
                            </Collapse>
                          )}
                        </Box>
                      </Box>
                    </motion.div>
                  );
                })
              )}
            </AnimatePresence>
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
}
