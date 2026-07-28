import React, { useState } from 'react';
import {
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Box,
  Alert,
  Chip
} from '@mui/material';
import {
  ShieldCheckIcon,
  CloudIcon,
  GlobeAltIcon,
  CodeBracketIcon,
  CreditCardIcon
} from '@heroicons/react/24/outline';
import CloudflareSettings from './CloudflareSettings';
import NameCheapSettings from './NameCheapSettings';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * Credentials Management - Main Settings Page
 *
 * Provides tabbed interface for managing API credentials across multiple services.
 * All credentials are encrypted at rest on the backend.
 */
export default function CredentialsManagement() {
  const [activeTab, setActiveTab] = useState(0);
  const { theme } = useTheme();

  const isDark = theme === 'magic-unicorn' || theme === 'dark';

  const tabs = [
    { label: 'Cloudflare', icon: CloudIcon, status: 'active' },
    { label: 'NameCheap', icon: GlobeAltIcon, status: 'active' },
    { label: 'GitHub', icon: CodeBracketIcon, status: 'coming-soon' },
    { label: 'Stripe', icon: CreditCardIcon, status: 'coming-soon' }
  ];

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <ShieldCheckIcon className="h-8 w-8 text-purple-500" />
        <Box>
          <Typography variant="h4" gutterBottom sx={{ mb: 0.5 }}>
            Credentials Management
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage API credentials for integrated services. All credentials are encrypted at rest.
          </Typography>
        </Box>
      </Box>

      {/* Security Notice */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Security:</strong> Credentials are encrypted using AES-256-GCM before storage.
          Never share or expose these values in logs or public repositories.
        </Typography>
      </Alert>

      {/* Service Tabs */}
      <Paper
        sx={{
          width: '100%',
          mt: 3,
          backgroundColor: isDark ? 'rgba(17, 24, 39, 0.8)' : 'white',
          backdropFilter: 'blur(10px)',
          border: isDark ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid rgba(0, 0, 0, 0.12)'
        }}
      >
        <Tabs
          value={activeTab}
          onChange={(e, v) => setActiveTab(v)}
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              minHeight: 64,
              textTransform: 'none',
              fontSize: '1rem'
            }
          }}
        >
          {tabs.map((tab, index) => (
            <Tab
              key={tab.label}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <tab.icon className="h-5 w-5" />
                  <span>{tab.label}</span>
                  {tab.status === 'coming-soon' && (
                    <Chip label="Soon" size="small" color="default" sx={{ ml: 0.5 }} />
                  )}
                </Box>
              }
              disabled={tab.status === 'coming-soon'}
            />
          ))}
        </Tabs>

        <Box sx={{ p: 3 }}>
          {activeTab === 0 && <CloudflareSettings />}
          {activeTab === 1 && <NameCheapSettings />}
          {activeTab === 2 && <ComingSoon service="GitHub" />}
          {activeTab === 3 && <ComingSoon service="Stripe" />}
        </Box>
      </Paper>
    </Container>
  );
}

/**
 * Placeholder component for upcoming integrations
 */
function ComingSoon({ service }) {
  return (
    <Box sx={{ textAlign: 'center', py: 6 }}>
      <Typography variant="h6" color="text.secondary" gutterBottom>
        {service} Integration
      </Typography>
      <Typography variant="body1" color="text.secondary">
        Coming soon. We're working on integrating {service} credentials management.
      </Typography>
    </Box>
  );
}
