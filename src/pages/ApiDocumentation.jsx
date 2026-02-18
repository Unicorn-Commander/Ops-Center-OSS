import React, { useState } from 'react';
import {
  Box,
  Container,
  Paper,
  Tabs,
  Tab,
  Typography,
  Button,
  Chip,
  Divider,
  Alert,
  Link,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  Code as CodeIcon,
  Description as DescriptionIcon,
  Download as DownloadIcon,
  OpenInNew as OpenInNewIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import SwaggerUIWrapper from '../components/SwaggerUIWrapper';
import ReDocWrapper from '../components/ReDocWrapper';
import ApiEndpointList from '../components/ApiEndpointList';
import CodeExampleTabs from '../components/CodeExampleTabs';

/**
 * ApiDocumentation
 *
 * Main API documentation page with tabbed interface
 * Provides Swagger UI, ReDoc, and code examples for the Ops-Center API
 */
const ApiDocumentation = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const [activeTab, setActiveTab] = useState(0);
  const [selectedEndpoint, setSelectedEndpoint] = useState(null);

  const handleDownloadSpec = async () => {
    try {
      const response = await fetch('/api/v1/docs/openapi.json');
      const spec = await response.json();

      const blob = new Blob([JSON.stringify(spec, null, 2)], {
        type: 'application/json',
      });

      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'ops-center-openapi.json';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download OpenAPI spec:', error);
    }
  };

  const tabs = [
    {
      label: 'Swagger UI',
      icon: <CodeIcon />,
      description: 'Interactive API explorer - try endpoints directly',
    },
    {
      label: 'ReDoc',
      icon: <DescriptionIcon />,
      description: 'Clean, read-only documentation',
    },
    {
      label: 'Code Examples',
      icon: <CodeIcon />,
      description: 'Multi-language code snippets',
    },
  ];

  return (
    <Box
      sx={{
        minHeight: '100vh',
        backgroundColor: 'background.default',
        pt: isMobile ? 2 : 3,
        pb: 4,
      }}
    >
      <Container maxWidth="xl">
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" fontWeight={600} gutterBottom>
            API Documentation
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Complete reference for the UC-Cloud Ops-Center REST API
          </Typography>

          {/* Quick Info Alert */}
          <Alert severity="info" icon={<InfoIcon />} sx={{ mb: 2 }}>
            <Typography variant="body2">
              <strong>Authentication Required:</strong> All API endpoints require authentication
              via OAuth 2.0 Bearer token or API key. The "Try it out" feature automatically uses
              your current session token.
            </Typography>
          </Alert>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadSpec}
              sx={{
                backgroundColor: theme.palette.primary.main,
                '&:hover': {
                  backgroundColor: theme.palette.primary.dark,
                },
              }}
            >
              Download OpenAPI Spec
            </Button>

            <Button
              variant="outlined"
              startIcon={<OpenInNewIcon />}
              href="/api/v1/docs/swagger"
              target="_blank"
            >
              Open Swagger UI (Full Screen)
            </Button>

            <Button
              variant="outlined"
              startIcon={<OpenInNewIcon />}
              href="/api/v1/docs/redoc"
              target="_blank"
            >
              Open ReDoc (Full Screen)
            </Button>
          </Box>
        </Box>

        {/* API Info Cards */}
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: isMobile ? '1fr' : 'repeat(auto-fit, minmax(250px, 1fr))',
            gap: 2,
            mb: 3,
          }}
        >
          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Base URL
            </Typography>
            <Typography
              variant="body2"
              fontWeight={500}
              sx={{ fontFamily: 'monospace', fontSize: '13px' }}
            >
              https://unicorncommander.ai
            </Typography>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Authentication
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip label="OAuth 2.0" size="small" color="primary" />
              <Chip label="API Key" size="small" color="primary" />
            </Box>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Version
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              v1.0.0
            </Typography>
          </Paper>

          <Paper sx={{ p: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Format
            </Typography>
            <Typography variant="body2" fontWeight={500}>
              OpenAPI 3.0
            </Typography>
          </Paper>
        </Box>

        {/* Main Content */}
        <Paper sx={{ overflow: 'hidden' }}>
          {/* Tabs */}
          <Box
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              backgroundColor: 'rgba(0, 0, 0, 0.02)',
            }}
          >
            <Tabs
              value={activeTab}
              onChange={(e, newValue) => setActiveTab(newValue)}
              variant={isMobile ? 'scrollable' : 'standard'}
              scrollButtons="auto"
              sx={{
                '& .MuiTab-root': {
                  minHeight: 64,
                  textTransform: 'none',
                  fontWeight: 500,
                },
              }}
            >
              {tabs.map((tab, index) => (
                <Tab
                  key={index}
                  icon={tab.icon}
                  iconPosition="start"
                  label={
                    <Box sx={{ textAlign: 'left' }}>
                      <Typography variant="body2" fontWeight={600}>
                        {tab.label}
                      </Typography>
                      {!isMobile && (
                        <Typography variant="caption" color="text.secondary">
                          {tab.description}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              ))}
            </Tabs>
          </Box>

          {/* Tab Panels */}
          <Box sx={{ minHeight: '600px' }}>
            {/* Swagger UI Tab - Lazy loaded only when active */}
            {activeTab === 0 && (
              <Box>
                <SwaggerUIWrapper />
              </Box>
            )}

            {/* ReDoc Tab - Lazy loaded only when active */}
            {activeTab === 1 && (
              <Box>
                <ReDocWrapper />
              </Box>
            )}

            {/* Code Examples Tab */}
            {activeTab === 2 && (
              <Box sx={{ display: 'flex', height: '600px' }}>
                {/* Endpoint List Sidebar */}
                <ApiEndpointList
                  onEndpointSelect={setSelectedEndpoint}
                  selectedEndpoint={selectedEndpoint}
                />

                {/* Code Examples Content */}
                <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
                  {selectedEndpoint ? (
                    <>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Code Examples
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                        Copy and paste these examples to get started quickly
                      </Typography>
                      <CodeExampleTabs endpoint={selectedEndpoint} />
                    </>
                  ) : (
                    <Box
                      sx={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        height: '100%',
                        textAlign: 'center',
                        p: 3,
                      }}
                    >
                      <CodeIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        Select an Endpoint
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Choose an endpoint from the sidebar to view code examples in cURL,
                        JavaScript, and Python
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Box>
            )}
          </Box>
        </Paper>

        {/* Footer Links */}
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Need help?{' '}
            <Link href="https://unicorncommander.com/docs" target="_blank" underline="hover">
              View Documentation
            </Link>
            {' | '}
            <Link href="mailto:support@magicunicorn.tech" underline="hover">
              Contact Support
            </Link>
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default ApiDocumentation;
