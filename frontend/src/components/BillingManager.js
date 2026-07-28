import React, { useState, useEffect } from 'react';
import {
  Container, Paper, Tabs, Tab, Box, Typography, CircularProgress,
  Alert, Snackbar
} from '@mui/material';
import AdminBilling from './billing/AdminBilling';
import UserAccount from './billing/UserAccount';
import { useAuth } from '../contexts/AuthContext';

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function BillingManager() {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const { user } = useAuth();

  useEffect(() => {
    fetchUserInfo();
  }, []);

  const fetchUserInfo = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/billing/account', {
        headers: {
          'X-Admin-Token': localStorage.getItem('adminToken') || ''
        }
      });

      if (!response.ok) throw new Error('Failed to fetch user info');

      const data = await response.json();
      setUserInfo(data);

      // If user is not admin, show only account tab
      if (!data.is_admin) {
        setTabValue(1);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    // Only allow admin to switch tabs
    if (userInfo?.is_admin || newValue === 1) {
      setTabValue(newValue);
    }
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error">Error loading billing information: {error}</Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Paper sx={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white',
        p: 3,
        mb: 3,
        borderRadius: 2
      }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          💳 Billing & Account Management
        </Typography>
        <Typography variant="body1">
          {userInfo?.is_admin
            ? 'Configure billing settings, manage API keys, and set subscription tiers'
            : 'Manage your account, subscription, and API keys'}
        </Typography>
      </Paper>

      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          {userInfo?.is_admin && (
            <Tab label="⚙️ Admin Configuration" />
          )}
          <Tab label="👤 My Account" />
        </Tabs>

        {userInfo?.is_admin && (
          <TabPanel value={tabValue} index={0}>
            <AdminBilling
              showSnackbar={showSnackbar}
              userInfo={userInfo}
            />
          </TabPanel>
        )}

        <TabPanel value={tabValue} index={userInfo?.is_admin ? 1 : 0}>
          <UserAccount
            showSnackbar={showSnackbar}
            userInfo={userInfo}
            refreshUserInfo={fetchUserInfo}
          />
        </TabPanel>
      </Paper>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}