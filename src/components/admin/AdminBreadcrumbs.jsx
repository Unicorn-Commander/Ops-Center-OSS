import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Box, Breadcrumbs, Typography, Chip } from '@mui/material';
import { HomeIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { getRouteByPath } from '../../config/routes';

/**
 * AdminBreadcrumbs - Shows current navigation path
 *
 * Automatically generates breadcrumbs from current route path.
 * Uses routes.js for page names.
 *
 * Usage:
 *   <AdminBreadcrumbs />
 */
export default function AdminBreadcrumbs() {
  const location = useLocation();
  const pathSegments = location.pathname.split('/').filter(Boolean);

  // Build breadcrumb items
  const breadcrumbs = [];
  let currentPath = '';

  // Add home
  breadcrumbs.push({
    label: 'Dashboard',
    path: '/admin',
    icon: HomeIcon,
  });

  // Build path segments
  for (let i = 0; i < pathSegments.length; i++) {
    const segment = pathSegments[i];
    currentPath += '/' + segment;

    // Skip 'admin' segment
    if (segment === 'admin') continue;

    // Look up route name
    const route = getRouteByPath(currentPath);
    const label = route?.name || formatSegment(segment);

    // Skip if same as previous
    if (breadcrumbs.length > 0 && breadcrumbs[breadcrumbs.length - 1].label === label) {
      continue;
    }

    breadcrumbs.push({
      label,
      path: currentPath,
    });
  }

  // Don't show if only home
  if (breadcrumbs.length <= 1) return null;

  return (
    <Box sx={{ mb: 2 }}>
      <Breadcrumbs
        separator={
          <ChevronRightIcon
            style={{ width: 16, height: 16, color: 'var(--mui-palette-text-disabled, #999)' }}
          />
        }
        aria-label="breadcrumb"
        sx={{
          '& .MuiBreadcrumbs-ol': {
            flexWrap: 'nowrap',
          },
        }}
      >
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          const Icon = crumb.icon;

          if (isLast) {
            return (
              <Chip
                key={crumb.path}
                label={crumb.label}
                size="small"
                sx={{
                  backgroundColor: 'primary.main',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '0.75rem',
                  height: 24,
                  '& .MuiChip-label': {
                    px: 1.5,
                  },
                }}
              />
            );
          }

          return (
            <Link
              key={crumb.path}
              to={crumb.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 4,
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              {Icon && <Icon style={{ width: 16, height: 16 }} />}
              <Typography
                variant="body2"
                sx={{
                  color: 'text.secondary',
                  '&:hover': {
                    color: 'primary.main',
                    textDecoration: 'underline',
                  },
                }}
              >
                {crumb.label}
              </Typography>
            </Link>
          );
        })}
      </Breadcrumbs>
    </Box>
  );
}

// Format URL segment to readable label
function formatSegment(segment) {
  return segment
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}
