import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Grid, Typography, LinearProgress,
  Chip, Button, Alert, Tabs, Tab, Paper, CircularProgress,
  IconButton, Tooltip
} from '@mui/material';
import {
  AccountBalanceWallet, TrendingUp, Schedule, Redeem,
  Refresh, Download, Info
} from '@mui/icons-material';
import { useTheme } from '../contexts/ThemeContext';
import CreditTransactions from '../components/CreditTransactions';
import UsageMetrics from '../components/UsageMetrics';
import CouponRedemption from '../components/CouponRedemption';
import OpenRouterAccountStatus from '../components/OpenRouterAccountStatus';

export default function CreditDashboard() {
  const { currentTheme } = useTheme();
  const [balance, setBalance] = useState(null);
  const [usage, setUsage] = useState(null);
  const [openRouterAccount, setOpenRouterAccount] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [balanceRes, usageRes, accountRes] = await Promise.all([
        fetch('/api/v1/credits/balance', {
          headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch('/api/v1/credits/usage/summary', {
          headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch('/api/v1/credits/openrouter/account', {
          headers: { Authorization: `Bearer ${localStorage.getItem('authToken')}` }
        })
      ]);

      if (!balanceRes.ok) throw new Error('Failed to load balance');

      const balanceData = await balanceRes.json();
      const usageData = usageRes.ok ? await usageRes.json() : null;
      const accountData = accountRes.ok ? await accountRes.json() : null;

      setBalance(balanceData);
      setUsage(usageData);
      setOpenRouterAccount(accountData);
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  const formatCredits = (amount) => {
    if (amount === null || amount === undefined) return '0 credits';
    // Format as whole number with commas, add "credits" label
    return `${Math.floor(parseFloat(amount)).toLocaleString()} credits`;
  };

  const formatCurrency = (amount) => {
    // Keep this for any actual money amounts (like transactions)
    if (amount === null || amount === undefined) return '$0.00';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const calculateUsagePercent = () => {
    if (!balance?.allocated_monthly || !usage?.this_month) return 0;
    return Math.min((usage.this_month / balance.allocated_monthly) * 100, 100);
  };

  const getStatusColor = (percent) => {
    if (percent >= 90) return 'error';
    if (percent >= 75) return 'warning';
    return 'success';
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          {error}
          <Button onClick={loadDashboardData} sx={{ ml: 2 }}>Retry</Button>
        </Alert>
      </Box>
    );
  }

  const usagePercent = calculateUsagePercent();

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Credits & Usage
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <Refresh className={refreshing ? 'animate-spin' : ''} />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Balance Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {/* Current Balance */}
        <Grid item xs={12} md={3}>
          <Card sx={{
            background: currentTheme === 'magic-unicorn'
              ? 'linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%)'
              : undefined,
            border: currentTheme === 'magic-unicorn' ? '1px solid rgba(168, 85, 247, 0.3)' : undefined
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <AccountBalanceWallet sx={{ mr: 1, color: 'primary.main' }} />
                <Typography color="textSecondary" variant="body2">
                  Current Balance
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ mb: 2, fontWeight: 700 }}>
                {formatCredits(balance?.balance)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={(balance?.balance / balance?.allocated_monthly) * 100 || 0}
                color={getStatusColor((balance?.balance / balance?.allocated_monthly) * 100 || 0)}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {((balance?.balance / balance?.allocated_monthly) * 100 || 0).toFixed(1)}% remaining
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Monthly Allocation */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Schedule sx={{ mr: 1, color: 'info.main' }} />
                <Typography color="textSecondary" variant="body2">
                  Monthly Allocation
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ mb: 1, fontWeight: 700 }}>
                {formatCredits(balance?.allocated_monthly)}
              </Typography>
              <Chip
                label={`Resets on ${balance?.next_reset_date || 'N/A'}`}
                size="small"
                color="info"
                variant="outlined"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Used This Month */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <TrendingUp sx={{ mr: 1, color: usagePercent >= 75 ? 'warning.main' : 'success.main' }} />
                <Typography color="textSecondary" variant="body2">
                  Used This Month
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ mb: 2, fontWeight: 700 }}>
                {formatCredits(usage?.this_month)}
              </Typography>
              <LinearProgress
                variant="determinate"
                value={usagePercent}
                color={getStatusColor(usagePercent)}
                sx={{ height: 8, borderRadius: 4 }}
              />
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                {usagePercent.toFixed(1)}% of allocation
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Free Tier Credits */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Redeem sx={{ mr: 1, color: 'success.main' }} />
                <Typography color="textSecondary" variant="body2">
                  Free Tier Credits
                </Typography>
              </Box>
              <Typography variant="h3" sx={{ mb: 1, fontWeight: 700 }}>
                {formatCredits(openRouterAccount?.free_credits_remaining || 0)}
              </Typography>
              <Chip
                label={openRouterAccount?.openrouter_email ? 'Active' : 'Not Configured'}
                size="small"
                color={openRouterAccount?.openrouter_email ? 'success' : 'default'}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Quick Stats Alert */}
      {usagePercent >= 90 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2">
            You've used {usagePercent.toFixed(1)}% of your monthly allocation.
            Consider upgrading your plan or adding credits to avoid interruptions.
          </Typography>
          <Button
            variant="outlined"
            size="small"
            sx={{ mt: 1 }}
            href="/admin/subscription/plan"
          >
            View Plans
          </Button>
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, v) => setActiveTab(v)}
          variant="fullWidth"
          sx={{ borderBottom: 1, borderColor: 'divider' }}
        >
          <Tab
            label="Overview"
            icon={<Info />}
            iconPosition="start"
          />
          <Tab
            label="Usage Metrics"
            icon={<TrendingUp />}
            iconPosition="start"
          />
          <Tab
            label="Transactions"
            icon={<Download />}
            iconPosition="start"
          />
          <Tab
            label="Account"
            icon={<AccountBalanceWallet />}
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      {activeTab === 0 && <OverviewTab balance={balance} usage={usage} />}
      {activeTab === 1 && <UsageMetrics />}
      {activeTab === 2 && <CreditTransactions />}
      {activeTab === 3 && <AccountTab openRouterAccount={openRouterAccount} onRefresh={loadDashboardData} />}
    </Box>
  );
}

// Overview Tab Component
function OverviewTab({ balance, usage }) {
  return (
    <Grid container spacing={3}>
      {/* Summary Stats */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Credit Summary</Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Total Allocated</Typography>
                <Typography variant="body1" fontWeight={600}>
                  ${balance?.allocated_monthly || 0}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Current Balance</Typography>
                <Typography variant="body1" fontWeight={600} color="success.main">
                  ${balance?.balance || 0}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Used This Month</Typography>
                <Typography variant="body1" fontWeight={600} color="error.main">
                  ${usage?.this_month || 0}
                </Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="body2" color="textSecondary">Pending Charges</Typography>
                <Typography variant="body1" fontWeight={600}>
                  ${balance?.pending || 0}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Recent Activity */}
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Usage Trends</Typography>
            <Box sx={{ mt: 2 }}>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Average Daily Usage
                </Typography>
                <Typography variant="h5" fontWeight={600}>
                  ${(usage?.this_month / 30 || 0).toFixed(2)}/day
                </Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Projected Month-End
                </Typography>
                <Typography variant="h5" fontWeight={600}>
                  ${((usage?.this_month / new Date().getDate()) * 30 || 0).toFixed(2)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Top Service
                </Typography>
                <Typography variant="h6" fontWeight={600}>
                  {usage?.top_service || 'N/A'}
                </Typography>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Quick Actions */}
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Quick Actions</Typography>
            <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
              <Button variant="outlined" href="/admin/subscription/plan">
                View Plans
              </Button>
              <Button variant="outlined" href="/admin/credits/tiers">
                Compare Tiers
              </Button>
              <Button variant="outlined" href="/admin/subscription/billing">
                View Invoices
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
}

// Account Tab Component
function AccountTab({ openRouterAccount, onRefresh }) {
  return (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <OpenRouterAccountStatus account={openRouterAccount} onRefresh={onRefresh} />
      </Grid>
      <Grid item xs={12} md={6}>
        <CouponRedemption onSuccess={onRefresh} />
      </Grid>
    </Grid>
  );
}
