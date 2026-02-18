/**
 * BottomNavBar Component - Fixed Bottom Navigation for Mobile
 *
 * Features:
 * - Fixed to bottom of screen (mobile only)
 * - 5 primary actions: Dashboard, Users, Billing, Analytics, Account
 * - Active state highlighting
 * - Icon + label (label hidden on very small screens < 375px)
 * - Safe area padding for iPhone notch
 * - Theme-aware styling
 * - Role-based visibility
 *
 * Props:
 * - currentPath: Current route path for active state
 * - userRole: User role for conditional rendering
 *
 * Usage:
 * <BottomNavBar currentPath={location.pathname} userRole={userInfo.role} />
 */

import React, { useMemo } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  BottomNavigation,
  BottomNavigationAction,
  Paper,
  useMediaQuery,
  useTheme,
  Badge
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  Payment as PaymentIcon,
  Analytics as AnalyticsIcon,
  AccountCircle as AccountCircleIcon,
  Settings as SettingsIcon,
  CreditCard as CreditCardIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { useTheme as useAppTheme } from '../contexts/ThemeContext';

export default function BottomNavBar({ currentPath, userRole }) {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const { currentTheme } = useAppTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const isVerySmallScreen = useMediaQuery('(max-width:375px)');

  // Get user info for role determination
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  const role = userRole || userInfo.role || 'viewer';
  const currentRoute = currentPath || location.pathname;

  // Get theme colors
  const getThemeColors = () => {
    if (currentTheme === 'unicorn') {
      return {
        navBg: 'linear-gradient(180deg, rgba(26, 0, 51, 0.98) 0%, rgba(45, 0, 82, 0.98) 100%)',
        borderColor: 'rgba(155, 81, 224, 0.3)',
        activeColor: '#c084fc',
        inactiveColor: 'rgba(255, 255, 255, 0.6)',
        activeBg: 'rgba(192, 132, 252, 0.15)',
        shadowColor: 'rgba(107, 31, 177, 0.3)'
      };
    } else if (currentTheme === 'light') {
      return {
        navBg: '#ffffff',
        borderColor: '#e0e0e0',
        activeColor: '#6b1fb1',
        inactiveColor: '#757575',
        activeBg: '#f3e5f5',
        shadowColor: 'rgba(0, 0, 0, 0.1)'
      };
    } else {
      return {
        navBg: '#1e293b',
        borderColor: '#334155',
        activeColor: '#818cf8',
        inactiveColor: '#94a3b8',
        activeBg: '#334155',
        shadowColor: 'rgba(0, 0, 0, 0.3)'
      };
    }
  };

  const colors = getThemeColors();

  // Navigation items configuration based on user role
  const navigationItems = useMemo(() => {
    const baseItems = [
      {
        label: 'Dashboard',
        value: '/admin/',
        icon: <DashboardIcon />,
        visible: true
      }
    ];

    // Admin-specific items
    if (role === 'admin') {
      return [
        ...baseItems,
        {
          label: 'Users',
          value: '/admin/people/users',
          icon: <PeopleIcon />,
          visible: true
        },
        {
          label: 'Billing',
          value: '/admin/billing/system',
          icon: <PaymentIcon />,
          visible: true
        },
        {
          label: 'Analytics',
          value: '/admin/monitoring/analytics',
          icon: <AnalyticsIcon />,
          visible: true
        },
        {
          label: 'Settings',
          value: '/admin/integrations/credentials',
          icon: <SettingsIcon />,
          visible: true
        }
      ];
    }

    // Regular user items
    return [
      ...baseItems,
      {
        label: 'Account',
        value: '/admin/account/profile',
        icon: <AccountCircleIcon />,
        visible: true
      },
      {
        label: 'Subscription',
        value: '/admin/subscription/plan',
        icon: <CreditCardIcon />,
        visible: true
      },
      {
        label: 'Org',
        value: '/admin/org/settings',
        icon: <BusinessIcon />,
        visible: true
      },
      {
        label: 'Settings',
        value: '/admin/account/security',
        icon: <SettingsIcon />,
        visible: true
      }
    ];
  }, [role]);

  // Filter visible items
  const visibleItems = navigationItems.filter(item => item.visible);

  // Determine active value
  const activeValue = useMemo(() => {
    // Find exact match first
    const exactMatch = visibleItems.find(item => currentRoute === item.value);
    if (exactMatch) return exactMatch.value;

    // Find partial match (current route starts with item value)
    const partialMatch = visibleItems.find(item =>
      currentRoute.startsWith(item.value) && item.value !== '/admin/'
    );
    if (partialMatch) return partialMatch.value;

    // Default to first item (Dashboard)
    return visibleItems[0]?.value || '/admin/';
  }, [currentRoute, visibleItems]);

  // Handle navigation change
  const handleChange = (event, newValue) => {
    navigate(newValue);
  };

  // Don't render on desktop
  if (!isMobile) {
    return null;
  }

  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1200,
        display: { xs: 'block', md: 'none' },
        background: colors.navBg,
        backgroundImage: currentTheme === 'unicorn' ? colors.navBg : 'none',
        borderTop: `1px solid ${colors.borderColor}`,
        boxShadow: `0 -2px 10px ${colors.shadowColor}`,
        pb: 'env(safe-area-inset-bottom, 0px)', // iPhone notch safe area
        // Ensure it stays above other content
        backdropFilter: currentTheme === 'unicorn' ? 'blur(10px)' : 'none'
      }}
      elevation={8}
    >
      <BottomNavigation
        value={activeValue}
        onChange={handleChange}
        showLabels={!isVerySmallScreen}
        sx={{
          background: 'transparent',
          height: isVerySmallScreen ? 56 : 64,
          '& .MuiBottomNavigationAction-root': {
            minWidth: isVerySmallScreen ? 60 : 80,
            maxWidth: 168,
            color: colors.inactiveColor,
            transition: 'all 0.3s ease',
            '&.Mui-selected': {
              color: colors.activeColor,
              backgroundColor: colors.activeBg,
              '& .MuiBottomNavigationAction-label': {
                fontSize: isVerySmallScreen ? '0.7rem' : '0.75rem',
                fontWeight: 600,
                opacity: 1
              }
            },
            '&:active': {
              transform: 'scale(0.95)'
            },
            '& .MuiBottomNavigationAction-label': {
              fontSize: isVerySmallScreen ? '0.65rem' : '0.75rem',
              opacity: isVerySmallScreen ? 0 : 0.8,
              transition: 'opacity 0.3s ease, font-size 0.3s ease',
              mt: 0.5
            },
            '& .MuiSvgIcon-root': {
              fontSize: isVerySmallScreen ? '1.5rem' : '1.75rem'
            }
          }
        }}
      >
        {visibleItems.map((item) => (
          <BottomNavigationAction
            key={item.value}
            label={item.label}
            value={item.value}
            icon={item.icon}
            sx={{
              // Add ripple effect
              '&::after': {
                content: '""',
                position: 'absolute',
                top: '50%',
                left: '50%',
                width: 0,
                height: 0,
                borderRadius: '50%',
                backgroundColor: colors.activeColor,
                opacity: 0,
                transform: 'translate(-50%, -50%)',
                transition: 'width 0.3s ease, height 0.3s ease, opacity 0.3s ease'
              },
              '&:active::after': {
                width: '100%',
                height: '100%',
                opacity: 0.2
              }
            }}
          />
        ))}
      </BottomNavigation>
    </Paper>
  );
}
