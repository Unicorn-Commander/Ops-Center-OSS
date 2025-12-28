/**
 * useResponsive Hook
 *
 * Custom hook for responsive design using Material-UI breakpoints
 * Provides convenient boolean flags for different screen sizes
 *
 * @returns {Object} Responsive flags and utility functions
 */

import { useTheme, useMediaQuery } from '@mui/material';

export const useResponsive = () => {
  const theme = useTheme();

  // Material-UI breakpoints
  // xs: 0-599px    (Mobile portrait)
  // sm: 600-959px  (Mobile landscape / Small tablet)
  // md: 960-1279px (Tablet)
  // lg: 1280-1919px (Desktop)
  // xl: 1920px+    (Large desktop)

  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const isTablet = useMediaQuery(theme.breakpoints.between('sm', 'md'));
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const isLargeDesktop = useMediaQuery(theme.breakpoints.up('xl'));

  // Specific breakpoint checks
  const isXs = useMediaQuery(theme.breakpoints.only('xs'));
  const isSm = useMediaQuery(theme.breakpoints.only('sm'));
  const isMd = useMediaQuery(theme.breakpoints.only('md'));
  const isLg = useMediaQuery(theme.breakpoints.only('lg'));
  const isXl = useMediaQuery(theme.breakpoints.only('xl'));

  // Utility functions
  const getGridColumns = () => {
    if (isMobile) return 1;
    if (isTablet) return 2;
    if (isDesktop) return 3;
    if (isLargeDesktop) return 4;
    return 3; // default
  };

  const getChartHeight = () => {
    if (isMobile) return 200;
    if (isTablet) return 250;
    return 300;
  };

  const getCircularProgressSize = () => {
    if (isMobile) return 100;
    return 150;
  };

  const getTouchTargetSize = () => {
    return isMobile ? 44 : 40; // Minimum 44px for mobile touch
  };

  const getFontScale = () => {
    if (isMobile) return 0.875; // 87.5% of base
    if (isTablet) return 0.9375; // 93.75% of base
    return 1; // 100% of base
  };

  return {
    // Boolean flags
    isMobile,
    isTablet,
    isDesktop,
    isLargeDesktop,

    // Specific breakpoint checks
    isXs,
    isSm,
    isMd,
    isLg,
    isXl,

    // Utility functions
    getGridColumns,
    getChartHeight,
    getCircularProgressSize,
    getTouchTargetSize,
    getFontScale,

    // Theme for additional queries
    theme,
  };
};

export default useResponsive;
