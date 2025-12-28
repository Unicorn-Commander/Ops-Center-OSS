/**
 * NotificationBell Component
 *
 * Real-time notification bell with dropdown showing recent admin notifications.
 * Uses WebSocket to receive notifications in real-time.
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  IconButton,
  Badge,
  Menu,
  MenuItem,
  Typography,
  Box,
  Divider,
  ListItemText,
  ListItemIcon,
  Switch,
  FormControlLabel,
  Chip
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Circle as CircleIcon,
  PersonAdd as PersonAddIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  Error as ErrorIcon,
  CheckCircle as CheckCircleIcon,
  Settings as SettingsIcon,
  VolumeUp as VolumeUpIcon,
  VolumeOff as VolumeOffIcon
} from '@mui/icons-material';
import { useWebSocketChannel } from '../hooks/useWebSocket';

const MAX_NOTIFICATIONS = 50;
const NOTIFICATION_EXPIRY = 24 * 60 * 60 * 1000; // 24 hours

// Notification sound
const notificationSound = new Audio('/notification.mp3'); // Add notification.mp3 to public folder

const getCategoryIcon = (category) => {
  switch (category) {
    case 'user_signup':
    case 'user_created':
      return <PersonAddIcon fontSize="small" />;
    case 'security_alert':
    case 'permission_change':
      return <SecurityIcon fontSize="small" />;
    case 'system_alert':
    case 'service_down':
      return <WarningIcon fontSize="small" />;
    case 'error':
      return <ErrorIcon fontSize="small" />;
    case 'success':
      return <CheckCircleIcon fontSize="small" />;
    default:
      return <InfoIcon fontSize="small" />;
  }
};

const getCategoryColor = (category) => {
  switch (category) {
    case 'user_signup':
    case 'user_created':
      return 'primary';
    case 'security_alert':
    case 'permission_change':
      return 'warning';
    case 'system_alert':
    case 'service_down':
      return 'error';
    case 'success':
      return 'success';
    default:
      return 'info';
  }
};

const formatTimestamp = (timestamp) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return date.toLocaleDateString();
};

export default function NotificationBell() {
  const [anchorEl, setAnchorEl] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [desktopEnabled, setDesktopEnabled] = useState(false);

  const notificationPermissionRef = useRef(false);

  // Subscribe to notifications channel
  const { messages: notificationMessages } = useWebSocketChannel('notifications');

  // Request desktop notification permission
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        notificationPermissionRef.current = permission === 'granted';
        setDesktopEnabled(permission === 'granted');
      });
    } else if ('Notification' in window && Notification.permission === 'granted') {
      notificationPermissionRef.current = true;
      setDesktopEnabled(true);
    }
  }, []);

  // Load notifications from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('adminNotifications');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Filter out expired notifications
        const valid = parsed.filter(n => {
          const age = Date.now() - new Date(n.timestamp).getTime();
          return age < NOTIFICATION_EXPIRY;
        });
        setNotifications(valid);

        // Count unread
        const unread = valid.filter(n => !n.read).length;
        setUnreadCount(unread);
      } catch (err) {
        console.error('Failed to parse stored notifications:', err);
      }
    }

    // Load sound preference
    const soundPref = localStorage.getItem('notificationSound');
    if (soundPref !== null) {
      setSoundEnabled(soundPref === 'true');
    }
  }, []);

  // Handle new notifications from WebSocket
  useEffect(() => {
    if (notificationMessages.length > 0) {
      const latestMessage = notificationMessages[notificationMessages.length - 1];

      // Create notification object
      const notification = {
        id: Date.now().toString(),
        category: latestMessage.category || 'info',
        message: latestMessage.message || 'New notification',
        data: latestMessage.data || {},
        timestamp: latestMessage.timestamp || new Date().toISOString(),
        read: false
      };

      // Add to notifications
      setNotifications(prev => {
        const updated = [notification, ...prev];
        // Keep only last MAX_NOTIFICATIONS
        if (updated.length > MAX_NOTIFICATIONS) {
          updated.pop();
        }

        // Save to localStorage
        localStorage.setItem('adminNotifications', JSON.stringify(updated));

        return updated;
      });

      // Increment unread count
      setUnreadCount(prev => prev + 1);

      // Play sound if enabled
      if (soundEnabled) {
        notificationSound.play().catch(err => {
          console.warn('Failed to play notification sound:', err);
        });
      }

      // Show desktop notification if enabled
      if (desktopEnabled && notificationPermissionRef.current) {
        new Notification('Ops-Center Admin', {
          body: notification.message,
          icon: '/favicon.png',
          tag: notification.id
        });
      }
    }
  }, [notificationMessages, soundEnabled, desktopEnabled]);

  const handleClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleMarkAllRead = () => {
    const updated = notifications.map(n => ({ ...n, read: true }));
    setNotifications(updated);
    setUnreadCount(0);
    localStorage.setItem('adminNotifications', JSON.stringify(updated));
  };

  const handleMarkRead = (id) => {
    const updated = notifications.map(n =>
      n.id === id ? { ...n, read: true } : n
    );
    setNotifications(updated);
    setUnreadCount(prev => Math.max(0, prev - 1));
    localStorage.setItem('adminNotifications', JSON.stringify(updated));
  };

  const handleClearAll = () => {
    setNotifications([]);
    setUnreadCount(0);
    localStorage.removeItem('adminNotifications');
    handleClose();
  };

  const handleToggleSound = () => {
    const newValue = !soundEnabled;
    setSoundEnabled(newValue);
    localStorage.setItem('notificationSound', newValue.toString());
  };

  const handleToggleDesktop = () => {
    if (!desktopEnabled && 'Notification' in window) {
      Notification.requestPermission().then(permission => {
        const granted = permission === 'granted';
        notificationPermissionRef.current = granted;
        setDesktopEnabled(granted);
      });
    } else {
      setDesktopEnabled(false);
    }
  };

  const open = Boolean(anchorEl);

  return (
    <>
      <IconButton color="inherit" onClick={handleClick}>
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        PaperProps={{
          sx: {
            width: 400,
            maxHeight: 600,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column'
          }
        }}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
      >
        {/* Header */}
        <Box sx={{ p: 2, pb: 1 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h6">Notifications</Typography>
            {notifications.length > 0 && (
              <Box>
                {unreadCount > 0 && (
                  <IconButton size="small" onClick={handleMarkAllRead} title="Mark all as read">
                    <CheckCircleIcon fontSize="small" />
                  </IconButton>
                )}
                <IconButton size="small" onClick={handleClearAll} title="Clear all">
                  <SettingsIcon fontSize="small" />
                </IconButton>
              </Box>
            )}
          </Box>

          {/* Settings */}
          <Box sx={{ mt: 1, display: 'flex', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  size="small"
                  checked={soundEnabled}
                  onChange={handleToggleSound}
                  icon={<VolumeOffIcon fontSize="small" />}
                  checkedIcon={<VolumeUpIcon fontSize="small" />}
                />
              }
              label={<Typography variant="caption">Sound</Typography>}
            />
            {'Notification' in window && (
              <FormControlLabel
                control={
                  <Switch
                    size="small"
                    checked={desktopEnabled}
                    onChange={handleToggleDesktop}
                  />
                }
                label={<Typography variant="caption">Desktop</Typography>}
              />
            )}
          </Box>
        </Box>

        <Divider />

        {/* Notifications List */}
        <Box sx={{ flexGrow: 1, overflow: 'auto' }}>
          {notifications.length === 0 ? (
            <Box sx={{ p: 4, textAlign: 'center' }}>
              <NotificationsIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body2" color="text.secondary">
                No notifications yet
              </Typography>
            </Box>
          ) : (
            notifications.map((notification) => (
              <MenuItem
                key={notification.id}
                onClick={() => handleMarkRead(notification.id)}
                sx={{
                  borderLeft: 3,
                  borderColor: notification.read ? 'transparent' : getCategoryColor(notification.category) + '.main',
                  bgcolor: notification.read ? 'transparent' : 'action.hover',
                  '&:hover': {
                    bgcolor: 'action.selected'
                  }
                }}
              >
                <ListItemIcon>
                  {getCategoryIcon(notification.category)}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2" fontWeight={notification.read ? 400 : 600}>
                        {notification.message}
                      </Typography>
                      {!notification.read && (
                        <CircleIcon sx={{ fontSize: 8, color: 'primary.main', ml: 1 }} />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 0.5 }}>
                      <Box display="flex" gap={1} alignItems="center">
                        <Chip
                          label={notification.category.replace('_', ' ')}
                          size="small"
                          color={getCategoryColor(notification.category)}
                          sx={{ height: 18, fontSize: '0.65rem' }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {formatTimestamp(notification.timestamp)}
                        </Typography>
                      </Box>
                      {notification.data && Object.keys(notification.data).length > 0 && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          {Object.entries(notification.data).slice(0, 2).map(([key, value]) => (
                            <span key={key}>{key}: {String(value).substring(0, 30)} </span>
                          ))}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </MenuItem>
            ))
          )}
        </Box>
      </Menu>
    </>
  );
}
