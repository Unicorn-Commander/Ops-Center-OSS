/**
 * MobileBreadcrumbs Component - Mobile-Friendly Breadcrumb Navigation
 *
 * Features:
 * - Horizontal scroll on overflow
 * - Truncated long labels (max 20 chars)
 * - Back button on first crumb
 * - Touch-friendly tap targets (44px height)
 * - Auto-hide on very small screens (< 375px)
 * - Theme-aware styling
 *
 * Props:
 * - path: Current route path (e.g., "/admin/system/users")
 * - maxLength: Maximum label length before truncation (default: 20)
 *
 * Usage:
 * <MobileBreadcrumbs path={location.pathname} />
 */

import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Chip,
  IconButton,
  useMediaQuery,
  useTheme
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  NavigateNext as NavigateNextIcon
} from '@mui/icons-material';
import { useTheme as useAppTheme } from '../contexts/ThemeContext';

export default function MobileBreadcrumbs({ path, maxLength = 20 }) {
  const theme = useTheme();
  const navigate = useNavigate();
  const { currentTheme } = useAppTheme();
  const isVerySmallScreen = useMediaQuery('(max-width:375px)');
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Parse path into breadcrumb segments
  const breadcrumbs = useMemo(() => {
    if (!path) return [];

    const segments = path.split('/').filter(Boolean);
    return segments.map((segment, index) => {
      // Build the full path up to this segment
      const fullPath = '/' + segments.slice(0, index + 1).join('/');

      // Convert segment to readable label
      const label = segment
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');

      return {
        segment,
        label,
        path: fullPath,
        isLast: index === segments.length - 1
      };
    });
  }, [path]);

  // Truncate label if too long
  const truncateLabel = (label, maxLen) => {
    if (label.length <= maxLen) return label;
    return label.substring(0, maxLen - 3) + '...';
  };

  // Handle navigation
  const handleNavigate = (targetPath) => {
    navigate(targetPath);
  };

  const handleBack = () => {
    navigate(-1);
  };

  // Get theme colors
  const getThemeColors = () => {
    if (currentTheme === 'unicorn') {
      return {
        containerBg: 'rgba(107, 31, 177, 0.1)',
        chipBg: 'rgba(255, 255, 255, 0.15)',
        chipActiveBg: 'rgba(255, 255, 255, 0.3)',
        chipText: '#ffffff',
        chipActiveText: '#ffffff',
        iconColor: 'rgba(255, 255, 255, 0.8)',
        separatorColor: 'rgba(255, 255, 255, 0.5)'
      };
    } else if (currentTheme === 'light') {
      return {
        containerBg: '#f5f5f5',
        chipBg: '#e0e0e0',
        chipActiveBg: '#6b1fb1',
        chipText: '#424242',
        chipActiveText: '#ffffff',
        iconColor: '#616161',
        separatorColor: '#9e9e9e'
      };
    } else {
      return {
        containerBg: '#1e293b',
        chipBg: '#334155',
        chipActiveBg: '#475569',
        chipText: '#cbd5e1',
        chipActiveText: '#f1f5f9',
        iconColor: '#94a3b8',
        separatorColor: '#64748b'
      };
    }
  };

  const colors = getThemeColors();

  // Don't render on desktop or very small screens
  if (!isMobile || isVerySmallScreen) {
    return null;
  }

  // Don't render if no breadcrumbs
  if (breadcrumbs.length === 0) {
    return null;
  }

  return (
    <Box
      sx={{
        display: { xs: 'flex', md: 'none' },
        alignItems: 'center',
        gap: 0.5,
        px: 2,
        py: 1.5,
        backgroundColor: colors.containerBg,
        borderBottom: `1px solid ${colors.separatorColor}20`,
        overflowX: 'auto',
        overflowY: 'hidden',
        whiteSpace: 'nowrap',
        WebkitOverflowScrolling: 'touch',
        '&::-webkit-scrollbar': {
          display: 'none'
        },
        scrollbarWidth: 'none',
        msOverflowStyle: 'none'
      }}
    >
      {/* Back Button */}
      <IconButton
        onClick={handleBack}
        size="small"
        sx={{
          minWidth: 44,
          minHeight: 44,
          color: colors.iconColor,
          flexShrink: 0,
          '&:active': {
            backgroundColor: colors.chipBg
          }
        }}
        aria-label="Go back"
      >
        <ArrowBackIcon fontSize="small" />
      </IconButton>

      {/* Breadcrumb Items */}
      {breadcrumbs.map((crumb, index) => (
        <React.Fragment key={crumb.path}>
          {index > 0 && (
            <NavigateNextIcon
              fontSize="small"
              sx={{
                color: colors.separatorColor,
                flexShrink: 0
              }}
            />
          )}
          <Chip
            label={truncateLabel(crumb.label, maxLength)}
            clickable={!crumb.isLast}
            onClick={() => !crumb.isLast && handleNavigate(crumb.path)}
            size="small"
            sx={{
              minHeight: 44,
              height: 'auto',
              py: 1,
              px: 1.5,
              fontSize: '0.875rem',
              fontWeight: crumb.isLast ? 600 : 500,
              backgroundColor: crumb.isLast ? colors.chipActiveBg : colors.chipBg,
              color: crumb.isLast ? colors.chipActiveText : colors.chipText,
              flexShrink: 0,
              cursor: crumb.isLast ? 'default' : 'pointer',
              '&:hover': !crumb.isLast ? {
                backgroundColor: colors.chipActiveBg,
                color: colors.chipActiveText
              } : {},
              '&:active': !crumb.isLast ? {
                transform: 'scale(0.95)'
              } : {},
              transition: 'all 0.2s ease'
            }}
            aria-current={crumb.isLast ? 'page' : undefined}
          />
        </React.Fragment>
      ))}
    </Box>
  );
}
