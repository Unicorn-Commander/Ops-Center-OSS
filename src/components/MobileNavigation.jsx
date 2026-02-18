/**
 * MobileNavigation Component - Mobile-Friendly Navigation Drawer
 *
 * Features:
 * - Hamburger menu with animated icon (☰ → ✕)
 * - Slide-out drawer (80% screen width, max 320px)
 * - Smooth 300ms animations
 * - Swipe gestures (swipe right to open, left to close)
 * - Backdrop overlay with touch-to-close
 * - User profile section at top
 * - Expandable navigation sections (accordion)
 * - Active state highlighting
 * - Touch-optimized targets (56px height)
 *
 * Props:
 * - user: Current user object { name, username, avatar, subscription_tier, role }
 * - currentPath: Current route path for active state
 *
 * Usage:
 * <MobileNavigation user={userInfo} currentPath={location.pathname} />
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer,
  Box,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Avatar,
  Divider,
  Typography,
  Chip,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Payment as PaymentIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  Computer as ComputerIcon,
  AccountCircle as AccountCircleIcon,
  ExpandLess,
  ExpandMore,
  ExitToApp as ExitToAppIcon,
  Help as HelpIcon,
  Palette as PaletteIcon,
  Business as BusinessIcon,
  Security as SecurityIcon,
  Key as KeyIcon,
  Description as DescriptionIcon,
  CreditCard as CreditCardIcon,
  BarChart as BarChartIcon,
  Dns as ServerIcon,
  Build as BuildIcon,
  Cloud as CloudIcon,
  AttachMoney as AttachMoneyIcon,
  PieChart as PieChartIcon,
  Receipt as ReceiptIcon,
  Search as SearchIcon,
  AutoAwesome as AutoAwesomeIcon,
  Email as EmailIcon,
  Language as LanguageIcon,
  ViewList as ViewListIcon
} from '@mui/icons-material';
import { useTheme as useAppTheme } from '../contexts/ThemeContext';
import { useSwipeDrawer } from '../hooks/useSwipeGestures';

export default function MobileNavigation({ user, currentPath }) {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { currentTheme } = useAppTheme();
  const navigate = useNavigate();
  const location = useLocation();

  // Drawer state with swipe gestures
  const {
    isOpen,
    setIsOpen,
    swipeHandlers,
    toggleDrawer,
    closeDrawer
  } = useSwipeDrawer(false);

  // Expandable sections state
  const [expandedSections, setExpandedSections] = useState({
    infrastructure: false,
    usersOrgs: false,
    billingUsage: false,
    platform: false,
    account: false,
    subscription: false
  });

  // Get user info from props or localStorage
  const userInfo = user || JSON.parse(localStorage.getItem('userInfo') || '{}');
  const userRole = userInfo.role || 'viewer';
  const currentRoute = currentPath || location.pathname;

  // Close drawer when route changes (mobile navigation completed)
  useEffect(() => {
    if (isOpen) {
      closeDrawer();
    }
  }, [currentRoute]);

  // Toggle section expansion
  const toggleSection = useCallback((section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  }, []);

  // Handle logout
  const handleLogout = async () => {
    try {
      await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout failed:', error);
    }

    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('user');
    localStorage.removeItem('token');

    window.location.href = '/';
  };

  // Navigation click handler
  const handleNavigate = useCallback((path, external = false) => {
    if (external) {
      window.open(path, '_blank');
    } else {
      navigate(path);
    }
    closeDrawer();
  }, [navigate, closeDrawer]);

  // Check if path is active
  const isActive = useCallback((path, exact = false) => {
    if (exact) {
      return currentRoute === path;
    }
    return currentRoute.startsWith(path);
  }, [currentRoute]);

  // Theme colors
  const getThemeColors = () => {
    if (currentTheme === 'unicorn') {
      return {
        drawerBg: 'linear-gradient(180deg, #1a0033 0%, #2d0052 100%)',
        headerBg: 'linear-gradient(135deg, #6b1fb1 0%, #c2185b 100%)',
        activeBg: 'rgba(255, 255, 255, 0.1)',
        hoverBg: 'rgba(255, 255, 255, 0.05)',
        textPrimary: '#ffffff',
        textSecondary: 'rgba(255, 255, 255, 0.7)',
        divider: 'rgba(255, 255, 255, 0.12)',
        chipBg: 'rgba(255, 255, 255, 0.2)'
      };
    } else if (currentTheme === 'light') {
      return {
        drawerBg: '#ffffff',
        headerBg: 'linear-gradient(135deg, #6b1fb1 0%, #c2185b 100%)',
        activeBg: '#f3e5f5',
        hoverBg: '#fafafa',
        textPrimary: '#212121',
        textSecondary: '#757575',
        divider: '#e0e0e0',
        chipBg: 'rgba(107, 31, 177, 0.1)'
      };
    } else {
      return {
        drawerBg: '#1e293b',
        headerBg: '#334155',
        activeBg: '#334155',
        hoverBg: '#293548',
        textPrimary: '#f1f5f9',
        textSecondary: '#94a3b8',
        divider: '#334155',
        chipBg: 'rgba(100, 116, 139, 0.3)'
      };
    }
  };

  const colors = getThemeColors();

  // Navigation items configuration
  const navigationConfig = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <DashboardIcon />,
      path: '/admin/',
      exact: true,
      visible: true
    },
    {
      id: 'infrastructure',
      label: 'Infrastructure',
      icon: <ComputerIcon />,
      visible: userRole === 'admin',
      children: [
        { label: 'Services', path: '/admin/infra/services', icon: <ServerIcon /> },
        { label: 'Hardware', path: '/admin/infra/hardware', icon: <BuildIcon /> },
        { label: 'Monitoring', path: '/admin/monitoring/overview', icon: <BarChartIcon /> },
        { label: 'LLM Management', path: '/admin/ai/management', icon: <CloudIcon /> },
        { label: 'LLM Providers', path: '/admin/ai/providers', icon: <AutoAwesomeIcon /> },
        { label: 'Model Catalog', path: '/admin/ai/models', icon: <ViewListIcon /> },
        { label: 'Cloudflare DNS', path: '/admin/integrations/cloudflare', icon: <LanguageIcon /> }
      ]
    },
    {
      id: 'usersOrgs',
      label: 'Users & Orgs',
      icon: <PeopleIcon />,
      visible: userRole === 'admin',
      children: [
        { label: 'User Management', path: '/admin/people/users', icon: <PeopleIcon /> },
        { label: 'Organizations', path: '/admin/org/settings', icon: <BusinessIcon /> },
        { label: 'Permissions', path: '/admin/org/roles', icon: <SecurityIcon /> },
        { label: 'Authentication', path: '/admin/people/authentication', icon: <KeyIcon /> }
      ]
    },
    {
      id: 'billingUsage',
      label: 'Billing & Usage',
      icon: <PaymentIcon />,
      visible: userRole === 'admin',
      children: [
        { label: 'Subscription Management', path: '/admin/billing/tiers', icon: <CreditCardIcon /> },
        { label: 'App Management', path: '/admin/billing/apps', icon: <SettingsIcon /> },
        { label: 'Billing Dashboard', path: '/admin/billing/system', icon: <AttachMoneyIcon /> },
        { label: 'Analytics', path: '/admin/monitoring/analytics', icon: <AnalyticsIcon /> },
        { label: 'Usage Metrics', path: '/admin/monitoring/usage-metrics', icon: <PieChartIcon /> },
        { label: 'Subscriptions', path: '/admin/subscription/plan', icon: <DescriptionIcon /> },
        { label: 'Invoices', path: '/admin/billing/overview', icon: <ReceiptIcon /> }
      ]
    },
    {
      id: 'platform',
      label: 'Platform',
      icon: <AutoAwesomeIcon />,
      visible: userRole === 'admin',
      children: [
        { label: 'Unicorn Brigade', path: '/admin/brigade', icon: <AutoAwesomeIcon /> },
        { label: 'Center-Deep Search', path: 'https://search.unicorncommander.ai', icon: <SearchIcon />, external: true },
        { label: 'Email Settings', path: '/admin/integrations/email', icon: <EmailIcon /> },
        { label: 'Platform Settings', path: '/admin/integrations/credentials', icon: <SettingsIcon /> }
      ]
    },
    {
      id: 'account',
      label: 'My Account',
      icon: <AccountCircleIcon />,
      visible: true,
      children: [
        { label: 'Profile', path: '/admin/account/profile', icon: <AccountCircleIcon /> },
        { label: 'Security', path: '/admin/account/security', icon: <SecurityIcon /> },
        { label: 'API Keys', path: '/admin/account/api-keys', icon: <KeyIcon /> }
      ]
    },
    {
      id: 'subscription',
      label: 'My Subscription',
      icon: <CreditCardIcon />,
      visible: true,
      children: [
        { label: 'Plan', path: '/admin/subscription/plan', icon: <DescriptionIcon /> },
        { label: 'Usage', path: '/admin/subscription/usage', icon: <BarChartIcon /> },
        { label: 'Billing', path: '/admin/subscription/billing', icon: <ReceiptIcon /> },
        { label: 'Payment', path: '/admin/subscription/payment', icon: <CreditCardIcon /> }
      ]
    }
  ];

  // Filter visible items
  const visibleItems = navigationConfig.filter(item => item.visible !== false);

  // Get tier badge display
  const getTierDisplay = (tier) => {
    const tierMap = {
      trial: { label: 'Trial', emoji: '🔬', color: 'info' },
      starter: { label: 'Starter', emoji: '🚀', color: 'success' },
      professional: { label: 'Pro', emoji: '💼', color: 'primary' },
      enterprise: { label: 'Enterprise', emoji: '🏢', color: 'secondary' }
    };
    return tierMap[tier] || { label: tier, emoji: '', color: 'default' };
  };

  const tierInfo = getTierDisplay(userInfo.subscription_tier);

  // Don't render on desktop
  if (!isMobile) {
    return null;
  }

  return (
    <>
      {/* Hamburger Menu Button */}
      <IconButton
        onClick={toggleDrawer}
        sx={{
          display: { xs: 'flex', md: 'none' },
          position: 'fixed',
          top: 16,
          left: 16,
          zIndex: 1300,
          width: 48,
          height: 48,
          backgroundColor: currentTheme === 'unicorn' ? '#6b1fb1' : currentTheme === 'light' ? '#6b1fb1' : '#334155',
          color: 'white',
          boxShadow: 3,
          transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          '&:hover': {
            backgroundColor: currentTheme === 'unicorn' ? '#8e24aa' : currentTheme === 'light' ? '#8e24aa' : '#475569',
            transform: 'scale(1.05)'
          },
          '&:active': {
            transform: 'scale(0.95)'
          }
        }}
        aria-label="Open navigation menu"
      >
        {isOpen ? <CloseIcon /> : <MenuIcon />}
      </IconButton>

      {/* Slide-Out Drawer */}
      <Drawer
        anchor="left"
        open={isOpen}
        onClose={closeDrawer}
        {...swipeHandlers}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: '80%',
            maxWidth: 320,
            background: colors.drawerBg,
            backgroundImage: currentTheme === 'unicorn' ? colors.drawerBg : 'none',
            overflowY: 'auto'
          }
        }}
        ModalProps={{
          keepMounted: true // Better mobile performance
        }}
      >
        {/* User Profile Header */}
        <Box
          sx={{
            p: 3,
            textAlign: 'center',
            background: colors.headerBg,
            color: 'white',
            boxShadow: 1
          }}
        >
          <Avatar
            src={userInfo.avatar}
            sx={{
              width: 72,
              height: 72,
              margin: '0 auto 12px',
              border: '3px solid rgba(255, 255, 255, 0.3)',
              boxShadow: 2
            }}
          >
            {userInfo.username?.charAt(0).toUpperCase() || userInfo.name?.charAt(0).toUpperCase() || 'U'}
          </Avatar>
          <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
            {userInfo.username || userInfo.name || 'User'}
          </Typography>
          {userInfo.subscription_tier && (
            <Chip
              label={`${tierInfo.emoji} ${tierInfo.label}`}
              size="small"
              sx={{
                backgroundColor: colors.chipBg,
                color: 'white',
                fontWeight: 500,
                fontSize: '0.75rem'
              }}
            />
          )}
          {userRole === 'admin' && (
            <Chip
              label="Administrator"
              size="small"
              sx={{
                mt: 1,
                backgroundColor: 'rgba(255, 193, 7, 0.3)',
                color: 'white',
                fontWeight: 500,
                fontSize: '0.7rem'
              }}
            />
          )}
        </Box>

        <Divider sx={{ borderColor: colors.divider }} />

        {/* Navigation Items */}
        <List sx={{ pt: 1, pb: 1 }}>
          {visibleItems.map((item) => (
            <React.Fragment key={item.id}>
              {item.children ? (
                // Expandable Section
                <>
                  <ListItemButton
                    onClick={() => toggleSection(item.id)}
                    sx={{
                      minHeight: 56,
                      px: 2,
                      color: colors.textPrimary,
                      '&:hover': {
                        backgroundColor: colors.hoverBg
                      }
                    }}
                  >
                    <ListItemIcon sx={{ color: colors.textPrimary, minWidth: 40 }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{ fontWeight: 500 }}
                    />
                    {expandedSections[item.id] ? <ExpandLess /> : <ExpandMore />}
                  </ListItemButton>
                  <Collapse in={expandedSections[item.id]} timeout="auto" unmountOnExit>
                    <List component="div" disablePadding>
                      {item.children.map((child) => (
                        <ListItemButton
                          key={child.path}
                          component={child.external ? 'a' : Link}
                          to={!child.external ? child.path : undefined}
                          href={child.external ? child.path : undefined}
                          target={child.external ? '_blank' : undefined}
                          selected={!child.external && isActive(child.path)}
                          sx={{
                            minHeight: 48,
                            pl: 6,
                            pr: 2,
                            color: colors.textSecondary,
                            backgroundColor: !child.external && isActive(child.path) ? colors.activeBg : 'transparent',
                            '&:hover': {
                              backgroundColor: colors.hoverBg,
                              color: colors.textPrimary
                            },
                            '&.Mui-selected': {
                              backgroundColor: colors.activeBg,
                              color: colors.textPrimary,
                              fontWeight: 600,
                              '&:hover': {
                                backgroundColor: colors.activeBg
                              }
                            }
                          }}
                        >
                          <ListItemIcon sx={{ color: 'inherit', minWidth: 36, fontSize: '1.2rem' }}>
                            {child.icon}
                          </ListItemIcon>
                          <ListItemText
                            primary={child.label}
                            primaryTypographyProps={{ fontSize: '0.9rem' }}
                          />
                        </ListItemButton>
                      ))}
                    </List>
                  </Collapse>
                </>
              ) : (
                // Single Item
                <ListItemButton
                  component={Link}
                  to={item.path}
                  selected={isActive(item.path, item.exact)}
                  sx={{
                    minHeight: 56,
                    px: 2,
                    color: colors.textPrimary,
                    backgroundColor: isActive(item.path, item.exact) ? colors.activeBg : 'transparent',
                    '&:hover': {
                      backgroundColor: colors.hoverBg
                    },
                    '&.Mui-selected': {
                      backgroundColor: colors.activeBg,
                      fontWeight: 600,
                      '&:hover': {
                        backgroundColor: colors.activeBg
                      }
                    }
                  }}
                >
                  <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.label}
                    primaryTypographyProps={{ fontWeight: isActive(item.path, item.exact) ? 600 : 500 }}
                  />
                </ListItemButton>
              )}
            </React.Fragment>
          ))}
        </List>

        <Divider sx={{ borderColor: colors.divider, mt: 'auto' }} />

        {/* Help Button */}
        <List sx={{ pt: 1 }}>
          <ListItemButton
            onClick={() => {
              const currentHost = window.location.hostname;
              window.open(`http://${currentHost}:8086`, '_blank');
              closeDrawer();
            }}
            sx={{
              minHeight: 56,
              px: 2,
              color: colors.textSecondary,
              '&:hover': {
                backgroundColor: colors.hoverBg,
                color: colors.textPrimary
              }
            }}
          >
            <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
              <HelpIcon />
            </ListItemIcon>
            <ListItemText primary="Help & Docs" />
          </ListItemButton>

          {/* Logout Button */}
          <ListItemButton
            onClick={handleLogout}
            sx={{
              minHeight: 56,
              px: 2,
              color: '#ef4444',
              '&:hover': {
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                color: '#dc2626'
              }
            }}
          >
            <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
              <ExitToAppIcon />
            </ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItemButton>
        </List>

        {/* Version Footer */}
        <Box
          sx={{
            p: 2,
            textAlign: 'center',
            borderTop: `1px solid ${colors.divider}`
          }}
        >
          <Typography variant="caption" sx={{ color: colors.textSecondary, display: 'block', mb: 0.5 }}>
            Ops Center
          </Typography>
          <Typography variant="caption" sx={{ color: colors.textSecondary, fontFamily: 'monospace' }}>
            v2.1.0
          </Typography>
        </Box>
      </Drawer>
    </>
  );
}
