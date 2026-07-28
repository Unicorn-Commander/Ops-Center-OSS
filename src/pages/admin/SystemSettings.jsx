/**
 * System Settings Page
 * Main admin page for managing all system settings across categories
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Button,
  Alert,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  Save as SaveIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import toast from 'react-hot-toast';

import useSystemSettings from '../../hooks/useSystemSettings';
import AuthenticationSettings from '../../components/settings/AuthenticationSettings';
import BrandingSettings from '../../components/settings/BrandingSettings';
import FeaturesSettings from '../../components/settings/FeaturesSettings';
import IntegrationsSettings from '../../components/settings/IntegrationsSettings';
import NotificationsSettings from '../../components/settings/NotificationsSettings';
import SecuritySettings from '../../components/settings/SecuritySettings';
import BrandingPreview from '../../components/settings/BrandingPreview';

// Tab panel component
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`settings-tabpanel-${index}`}
      aria-labelledby={`settings-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const SystemSettings = () => {
  const {
    settings,
    metadata,
    categories,
    loading,
    saving,
    error,
    fetchSettings,
    bulkUpdateSettings,
    getCategorySettings
  } = useSystemSettings();

  const [currentTab, setCurrentTab] = useState(0);
  const [localSettings, setLocalSettings] = useState({});
  const [hasChanges, setHasChanges] = useState(false);

  // Category definitions
  const categoryTabs = [
    { label: 'Authentication', key: 'authentication', icon: '🔐' },
    { label: 'Branding', key: 'branding', icon: '🎨' },
    { label: 'Features', key: 'features', icon: '✨' },
    { label: 'Integrations', key: 'integrations', icon: '🔌' },
    { label: 'Notifications', key: 'notifications', icon: '🔔' },
    { label: 'Security', key: 'security', icon: '🛡️' }
  ];

  // Initialize local settings when settings load
  useEffect(() => {
    if (settings && Object.keys(settings).length > 0) {
      setLocalSettings(settings);
    }
  }, [settings]);

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    if (hasChanges) {
      const confirmChange = window.confirm(
        'You have unsaved changes. Are you sure you want to switch tabs?'
      );
      if (!confirmChange) return;
    }
    setCurrentTab(newValue);
  };

  // Handle setting change
  const handleSettingChange = (category, key, value) => {
    setLocalSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setHasChanges(true);
  };

  // Save all changes
  const handleSave = async () => {
    try {
      // Prepare bulk update payload
      const updates = {};

      // Compare local settings with original settings and collect changes
      Object.keys(localSettings).forEach(category => {
        Object.keys(localSettings[category] || {}).forEach(key => {
          const newValue = localSettings[category][key];
          const oldValue = settings[category]?.[key];

          // Only include changed values
          if (newValue !== oldValue) {
            updates[key] = newValue;
          }
        });
      });

      if (Object.keys(updates).length === 0) {
        toast.info('No changes to save');
        return;
      }

      await bulkUpdateSettings(updates);
      setHasChanges(false);
      toast.success(`Successfully updated ${Object.keys(updates).length} setting(s)`);
    } catch (err) {
      toast.error(`Failed to save settings: ${err.message}`);
    }
  };

  // Refresh settings
  const handleRefresh = async () => {
    if (hasChanges) {
      const confirmRefresh = window.confirm(
        'You have unsaved changes. Are you sure you want to refresh?'
      );
      if (!confirmRefresh) return;
    }

    await fetchSettings();
    setHasChanges(false);
    toast.success('Settings refreshed');
  };

  // Warn before leaving page with unsaved changes
  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (hasChanges) {
        e.preventDefault();
        e.returnValue = '';
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasChanges]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, textAlign: 'center' }}>
        <CircularProgress />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          Loading settings...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Page Header */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            System Settings
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Configure platform-wide settings and preferences
          </Typography>
        </div>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={saving}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<SaveIcon />}
            onClick={handleSave}
            disabled={!hasChanges || saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </Button>
        </Box>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => {}}>
          {error}
        </Alert>
      )}

      {/* Unsaved Changes Warning */}
      {hasChanges && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          You have unsaved changes. Click "Save Changes" to apply them.
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={currentTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider'
          }}
        >
          {categoryTabs.map((tab, index) => (
            <Tab
              key={tab.key}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </Box>
              }
              id={`settings-tab-${index}`}
              aria-controls={`settings-tabpanel-${index}`}
            />
          ))}
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <TabPanel value={currentTab} index={0}>
        <AuthenticationSettings
          settings={localSettings.authentication || {}}
          onChange={(key, value) => handleSettingChange('authentication', key, value)}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={1}>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, gap: 3 }}>
          <Box>
            <BrandingSettings
              settings={localSettings.branding || {}}
              onChange={(key, value) => handleSettingChange('branding', key, value)}
            />
          </Box>
          <Box>
            <BrandingPreview settings={localSettings.branding || {}} />
          </Box>
        </Box>
      </TabPanel>

      <TabPanel value={currentTab} index={2}>
        <FeaturesSettings
          settings={localSettings.features || {}}
          onChange={(key, value) => handleSettingChange('features', key, value)}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={3}>
        <IntegrationsSettings
          settings={localSettings.integrations || {}}
          onChange={(key, value) => handleSettingChange('integrations', key, value)}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={4}>
        <NotificationsSettings
          settings={localSettings.notifications || {}}
          onChange={(key, value) => handleSettingChange('notifications', key, value)}
        />
      </TabPanel>

      <TabPanel value={currentTab} index={5}>
        <SecuritySettings
          settings={localSettings.security || {}}
          onChange={(key, value) => handleSettingChange('security', key, value)}
        />
      </TabPanel>

      {/* Bottom Action Bar */}
      <Box sx={{ mt: 4, display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={handleRefresh}
          disabled={saving}
        >
          Cancel
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          disabled={!hasChanges || saving}
          size="large"
        >
          {saving ? 'Saving...' : 'Save All Changes'}
        </Button>
      </Box>
    </Container>
  );
};

export default SystemSettings;
