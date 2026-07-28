import React from 'react';
import { Box, Tabs, Tab } from '@mui/material';
import { Info as InfoIcon, Dns as DnsIcon, Storage as StorageIcon, Settings as SettingsIcon } from '@mui/icons-material';

const ZoneDetailTabs = ({ activeTab, onChange }) => {
  return (
    <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
      <Tabs value={activeTab} onChange={(e, newValue) => onChange(newValue)}>
        <Tab label="Overview" icon={<InfoIcon />} iconPosition="start" />
        <Tab label="DNS Records" icon={<DnsIcon />} iconPosition="start" />
        <Tab label="Nameservers" icon={<StorageIcon />} iconPosition="start" />
        <Tab label="Settings" icon={<SettingsIcon />} iconPosition="start" />
      </Tabs>
    </Box>
  );
};

export default ZoneDetailTabs;
