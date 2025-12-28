import React, { useEffect, useState, lazy, Suspense } from 'react';
import { Box, Alert, CircularProgress, Skeleton } from '@mui/material';

// Lazy load ReDoc - Only loaded when ApiDocumentation tab 1 is active
const RedocStandalone = lazy(() =>
  import('redoc').then(module => ({ default: module.RedocStandalone }))
);

/**
 * ReDocWrapper
 *
 * Wrapper component for ReDoc API documentation
 * Provides a clean, read-only view of the API documentation
 */
const ReDocWrapper = () => {
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchOpenAPISpec();
  }, []);

  const fetchOpenAPISpec = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/docs/openapi.json');

      if (!response.ok) {
        throw new Error(`Failed to load API spec: ${response.statusText}`);
      }

      const data = await response.json();
      setSpec(data);
    } catch (err) {
      console.error('Error loading OpenAPI spec:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '400px'
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          <strong>Error loading API documentation:</strong> {error}
        </Alert>
      </Box>
    );
  }

  // Loading skeleton for ReDoc
  const ReDocLoadingSkeleton = () => (
    <Box sx={{ p: 3 }}>
      <Skeleton variant="rectangular" height={80} sx={{ mb: 2 }} />
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Skeleton variant="rectangular" width="30%" height={600} />
        <Skeleton variant="rectangular" width="70%" height={600} />
      </Box>
    </Box>
  );

  // ReDoc options for customization
  const redocOptions = {
    theme: {
      colors: {
        primary: {
          main: '#7c3aed',
        },
        success: {
          main: '#10b981',
        },
        warning: {
          main: '#f59e0b',
        },
        error: {
          main: '#ef4444',
        },
        text: {
          primary: '#111827',
          secondary: '#6b7280',
        },
        border: {
          dark: '#e5e7eb',
          light: '#f3f4f6',
        },
      },
      typography: {
        fontSize: '14px',
        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        lineHeight: '1.6',
        code: {
          fontSize: '13px',
          fontFamily: '"Fira Code", "Courier New", monospace',
          backgroundColor: '#f3f4f6',
          color: '#111827',
        },
        headings: {
          fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
          fontWeight: '600',
        },
      },
      sidebar: {
        backgroundColor: '#f9fafb',
        textColor: '#374151',
        activeTextColor: '#7c3aed',
        groupItems: {
          textTransform: 'uppercase',
          fontSize: '12px',
          fontWeight: '600',
          letterSpacing: '0.5px',
        },
      },
      rightPanel: {
        backgroundColor: '#1f2937',
        textColor: '#f9fafb',
      },
    },
    scrollYOffset: 0,
    hideDownloadButton: false,
    disableSearch: false,
    expandResponses: '200,201',
    expandSingleSchemaField: true,
    hideLoading: false,
    nativeScrollbars: false,
    pathInMiddlePanel: false,
    requiredPropsFirst: true,
    sortPropsAlphabetically: false,
    showExtensions: true,
    hideSingleRequestSampleTab: true,
    menuToggle: true,
    jsonSampleExpandLevel: 2,
  };

  return (
    <Box
      sx={{
        // Custom ReDoc styling
        '& .redoc-wrap': {
          fontFamily: 'inherit',
        },

        // Menu styling
        '& .menu-content': {
          backgroundColor: '#f9fafb',

          '& label': {
            color: '#374151',

            '&.active': {
              color: '#7c3aed',
              fontWeight: 600,
            },
          },
        },

        // Search box
        '& .search-box': {
          '& input': {
            borderColor: '#e5e7eb',

            '&:focus': {
              borderColor: '#7c3aed',
              outline: 'none',
            },
          },
        },

        // HTTP method badges
        '& .http-verb': {
          fontSize: '12px',
          fontWeight: 600,
          borderRadius: '4px',
          padding: '2px 8px',

          '&.get': {
            backgroundColor: '#10b981',
            color: 'white',
          },

          '&.post': {
            backgroundColor: '#3b82f6',
            color: 'white',
          },

          '&.put': {
            backgroundColor: '#f59e0b',
            color: 'white',
          },

          '&.delete': {
            backgroundColor: '#ef4444',
            color: 'white',
          },

          '&.patch': {
            backgroundColor: '#8b5cf6',
            color: 'white',
          },
        },

        // Code blocks
        '& pre': {
          backgroundColor: '#1f2937',
          color: '#f9fafb',
          padding: '16px',
          borderRadius: '6px',
          overflow: 'auto',
          fontSize: '13px',
          lineHeight: 1.6,
        },

        // Tables
        '& table': {
          '& th': {
            backgroundColor: '#f3f4f6',
            color: '#111827',
            fontWeight: 600,
            fontSize: '13px',
            padding: '12px',
            borderBottom: '2px solid #e5e7eb',
          },

          '& td': {
            padding: '12px',
            borderBottom: '1px solid #f3f4f6',
            fontSize: '14px',
          },
        },

        // Mobile responsive styles
        '@media (max-width: 768px)': {
          '& .redoc-wrap': {
            '& .menu-content': {
              position: 'fixed',
              top: 0,
              left: 0,
              width: '80%',
              maxWidth: '300px',
              height: '100%',
              zIndex: 100,
              boxShadow: '2px 0 8px rgba(0, 0, 0, 0.1)',
            },

            '& .api-content': {
              padding: '20px 16px',
            },

            '& pre': {
              fontSize: '12px',
              padding: '12px',
            },

            '& table': {
              fontSize: '13px',

              '& th, & td': {
                padding: '8px',
              },
            },
          },
        },
      }}
    >
      <Suspense fallback={<ReDocLoadingSkeleton />}>
        <RedocStandalone
          spec={spec}
          options={redocOptions}
        />
      </Suspense>
    </Box>
  );
};

export default ReDocWrapper;
