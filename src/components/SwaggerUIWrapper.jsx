import React, { useEffect, useState, lazy, Suspense } from 'react';
import { Box, Alert, CircularProgress, Skeleton } from '@mui/material';

// Lazy load Swagger UI - Only loaded when ApiDocumentation tab 0 is active
const SwaggerUI = lazy(() => import('swagger-ui-react'));

// Lazy load CSS separately
const loadSwaggerCSS = () => {
  if (typeof window !== 'undefined' && !document.getElementById('swagger-ui-css')) {
    const link = document.createElement('link');
    link.id = 'swagger-ui-css';
    link.rel = 'stylesheet';
    link.href = 'https://cdn.jsdelivr.net/npm/swagger-ui-react@5.29.5/swagger-ui.css';
    document.head.appendChild(link);
  }
};

/**
 * SwaggerUIWrapper
 *
 * Wrapper component for Swagger UI with authentication integration
 * Automatically injects auth tokens into API requests for "Try it out" functionality
 */
const SwaggerUIWrapper = () => {
  const [spec, setSpec] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSwaggerCSS();
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

  // Request interceptor to add authentication
  const requestInterceptor = (request) => {
    // Try to get auth token from localStorage
    const token = localStorage.getItem('authToken');

    if (token) {
      // Add Bearer token to Authorization header
      request.headers['Authorization'] = `Bearer ${token}`;
    }

    // Try to get API key from localStorage
    const apiKey = localStorage.getItem('apiKey');

    if (apiKey) {
      // Add API key header
      request.headers['X-API-Key'] = apiKey;
    }

    return request;
  };

  // Response interceptor for error handling
  const responseInterceptor = (response) => {
    // Log responses for debugging
    if (response.status >= 400) {
      console.error('API Error:', response);
    }
    return response;
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

  // Loading skeleton for Swagger UI
  const SwaggerLoadingSkeleton = () => (
    <Box sx={{ p: 3 }}>
      <Skeleton variant="rectangular" height={60} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" height={400} sx={{ mb: 2 }} />
      <Skeleton variant="rectangular" height={200} />
    </Box>
  );

  return (
    <Box
      sx={{
        '& .swagger-ui': {
          // Custom Swagger UI styling
          fontFamily: 'inherit',

          // Topbar styling
          '& .topbar': {
            backgroundColor: '#7c3aed',
            padding: '10px 0',

            '& .download-url-wrapper': {
              '& input[type=text]': {
                borderColor: '#7c3aed',
              },
            },
          },

          // Models section
          '& .model-box': {
            backgroundColor: '#f9fafb',
            borderRadius: '4px',
          },

          // Try it out button
          '& .btn.try-out__btn': {
            backgroundColor: '#7c3aed',
            color: 'white',
            border: 'none',

            '&:hover': {
              backgroundColor: '#6d28d9',
            },
          },

          // Execute button
          '& .btn.execute': {
            backgroundColor: '#10b981',
            color: 'white',
            border: 'none',

            '&:hover': {
              backgroundColor: '#059669',
            },
          },

          // Response section
          '& .responses-wrapper': {
            '& .responses-inner': {
              '& .response': {
                '& .response-col_status': {
                  fontSize: '14px',
                  fontWeight: 600,
                },
              },
            },
          },

          // Parameters table
          '& .parameters': {
            '& .parameter__name': {
              fontWeight: 600,
              color: '#374151',
            },

            '& .parameter__type': {
              color: '#6b7280',
              fontSize: '12px',
            },
          },

          // Markdown content
          '& .markdown': {
            '& p, & li': {
              fontSize: '14px',
              lineHeight: 1.6,
            },

            '& code': {
              backgroundColor: '#f3f4f6',
              padding: '2px 6px',
              borderRadius: '3px',
              fontSize: '13px',
            },

            '& pre': {
              backgroundColor: '#1f2937',
              color: '#f9fafb',
              padding: '16px',
              borderRadius: '6px',
              overflow: 'auto',
            },
          },
        },

        // Mobile responsive styles
        '@media (max-width: 768px)': {
          '& .swagger-ui': {
            '& .topbar': {
              padding: '8px 0',
            },

            '& .scheme-container': {
              padding: '10px',
            },

            '& .opblock': {
              margin: '0 0 15px',
            },

            '& .opblock-summary': {
              padding: '10px',
            },

            '& .opblock-body': {
              padding: '10px',
            },
          },
        },
      }}
    >
      <Suspense fallback={<SwaggerLoadingSkeleton />}>
        <SwaggerUI
          spec={spec}
          requestInterceptor={requestInterceptor}
          responseInterceptor={responseInterceptor}
          defaultModelsExpandDepth={1}
          defaultModelExpandDepth={3}
          docExpansion="list"
          filter={true}
          showRequestHeaders={true}
          displayRequestDuration={true}
          tryItOutEnabled={true}
          persistAuthorization={true}
          supportedSubmitMethods={['get', 'post', 'put', 'delete', 'patch']}
        />
      </Suspense>
    </Box>
  );
};

export default SwaggerUIWrapper;
