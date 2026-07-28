import React, { useState } from 'react';
import { Box, Tabs, Tab, Paper } from '@mui/material';
import {
  SettingsEthernet as NetworkIcon,
  Security as SecurityIcon,
  Dns as DnsIcon,
  VpnKey as VpnIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';

// Import network components
import NetworkConfig from './NetworkConfig'; // The original Network.jsx content
import FirewallManagement from './network/FirewallManagement';
import CloudflareDNS from './network/CloudflareDNS';

// Tab Panel Component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`network-tabpanel-${index}`}
      aria-labelledby={`network-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function NetworkTabbed() {
  const { currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          mb: 2,
          background: currentTheme === 'unicorn'
            ? 'linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%)'
            : 'transparent'
        }}
      >
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="network configuration tabs"
          sx={{
            '& .MuiTab-root': {
              minHeight: 64,
              fontSize: '0.95rem',
              fontWeight: 500,
            },
            '& .Mui-selected': {
              color: currentTheme === 'unicorn' ? '#a78bfa' : '#3b82f6',
            },
            '& .MuiTabs-indicator': {
              backgroundColor: currentTheme === 'unicorn' ? '#a78bfa' : '#3b82f6',
              height: 3,
            },
          }}
        >
          <Tab
            icon={<NetworkIcon />}
            label="Network Settings"
            iconPosition="start"
          />
          <Tab
            icon={<SecurityIcon />}
            label="Firewall"
            iconPosition="start"
          />
          <Tab
            icon={<DnsIcon />}
            label="DNS"
            iconPosition="start"
          />
          <Tab
            icon={<VpnIcon />}
            label="VPN"
            iconPosition="start"
            disabled
          />
          <Tab
            icon={<SpeedIcon />}
            label="Diagnostics"
            iconPosition="start"
            disabled
          />
        </Tabs>
      </Paper>

      <TabPanel value={activeTab} index={0}>
        <NetworkConfig />
      </TabPanel>

      <TabPanel value={activeTab} index={1}>
        <FirewallManagement />
      </TabPanel>

      <TabPanel value={activeTab} index={2}>
        <CloudflareDNS />
      </TabPanel>

      <TabPanel value={activeTab} index={3}>
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <VpnIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <h3>VPN Management</h3>
          <p style={{ color: 'gray' }}>Coming Soon - Phase 3</p>
        </Box>
      </TabPanel>

      <TabPanel value={activeTab} index={4}>
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <SpeedIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <h3>Network Diagnostics</h3>
          <p style={{ color: 'gray' }}>Coming Soon - Phase 4</p>
        </Box>
      </TabPanel>
    </Box>
  );
}
