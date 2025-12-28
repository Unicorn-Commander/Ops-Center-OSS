import React, { useState, useEffect } from 'react';
// Safe utilities for defensive rendering (Phase 3 refactoring)
import { safeMap, safeFilter } from '../utils/safeArrayUtils';
import { safeToFixed } from '../utils/safeNumberUtils';
import {
  Box,
  Container,
  Typography,
  Tabs,
  Tab,
  Paper,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  Button
} from '@mui/material';
import {
  Memory,
  CloudQueue,
  Route,
  Analytics,
  Settings,
  Refresh
} from '@mui/icons-material';
import ModelRegistry from '../components/llm/ModelRegistry';
import ProviderCard from '../components/llm/ProviderCard';
import UsageChart from '../components/llm/UsageChart';
import CostChart from '../components/llm/CostChart';
import CacheStatsCard from '../components/llm/CacheStatsCard';

/**
 * LLMManagement Component
 *
 * Comprehensive LiteLLM management dashboard with:
 * - Tab 1: Models - Model registry with CRUD operations
 * - Tab 2: Providers - Provider configuration and testing
 * - Tab 3: Routing - Routing rules and load balancing
 * - Tab 4: Analytics - Usage and cost analytics
 * - Tab 5: Settings - Rate limits and cache configuration
 */
export default function LLMManagement({ showSnackbar }) {
  const [tabValue, setTabValue] = useState(0);
  const [providers, setProviders] = useState([]);
  const [usage, setUsage] = useState({});
  const [costs, setCosts] = useState({});
  const [cacheStats, setCacheStats] = useState({});
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (tabValue === 1) fetchProviders();
    if (tabValue === 3) fetchAnalytics();
    if (tabValue === 4) fetchCacheStats();
  }, [tabValue]);

  const fetchProviders = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/llm/providers', {
        headers: { 'X-Admin-Token': localStorage.getItem('adminToken') || '' }
      });
      if (!response.ok) throw new Error('Failed to fetch providers');
      const data = await response.json();
      setProviders(data.providers || []);
    } catch (err) {
      showSnackbar(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const [usageRes, costsRes] = await Promise.all([
        fetch('/api/v1/llm/usage?period=7d', {
          headers: { 'X-Admin-Token': localStorage.getItem('adminToken') || '' }
        }),
        fetch('/api/v1/llm/costs?period=30d', {
          headers: { 'X-Admin-Token': localStorage.getItem('adminToken') || '' }
        })
      ]);

      if (usageRes.ok) {
        const usageData = await usageRes.json();
        setUsage(usageData.by_model || {});
      }

      if (costsRes.ok) {
        const costsData = await costsRes.json();
        setCosts(costsData.by_model || {});
      }
    } catch (err) {
      showSnackbar(err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchCacheStats = async () => {
    try {
      const response = await fetch('/api/v1/llm/cache-stats', {
        headers: { 'X-Admin-Token': localStorage.getItem('adminToken') || '' }
      });
      if (response.ok) {
        const data = await response.json();
        setCacheStats(data);
      }
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const handleClearCache = async () => {
    try {
      const response = await fetch('/api/v1/llm/cache/clear', {
        method: 'POST',
        headers: { 'X-Admin-Token': localStorage.getItem('adminToken') || '' }
      });
      if (response.ok) {
        showSnackbar('Cache cleared successfully', 'success');
        fetchCacheStats();
      }
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  const handleTestProvider = async (provider) => {
    try {
      showSnackbar('Testing provider...', 'info');
      const response = await fetch(`/api/v1/llm/providers/${provider.provider_id}/test`, {
        method: 'POST',
        headers: { 'X-Admin-Token': localStorage.getItem('adminToken') || '' }
      });
      const result = await response.json();
      if (result.success) {
        // REFACTORED: Using safeToFixed for latency formatting
        showSnackbar(`Provider is online (${safeToFixed(result.latency_ms, 0)}ms)`, 'success');
      } else {
        showSnackbar(`Provider test failed: ${result.error}`, 'error');
      }
    } catch (err) {
      showSnackbar(err.message, 'error');
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          LiteLLM Management
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Manage models, providers, routing, and analytics for your LLM infrastructure
        </Typography>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<Memory />} label="Models" iconPosition="start" />
          <Tab icon={<CloudQueue />} label="Providers" iconPosition="start" />
          <Tab icon={<Route />} label="Routing & Load Balancing" iconPosition="start" />
          <Tab icon={<Analytics />} label="Analytics" iconPosition="start" />
          <Tab icon={<Settings />} label="Settings" iconPosition="start" />
        </Tabs>
      </Paper>

      <Box sx={{ py: 3 }}>
        {/* Tab 1: Models */}
        {tabValue === 0 && (
          <ModelRegistry showSnackbar={showSnackbar} />
        )}

        {/* Tab 2: Providers */}
        {tabValue === 1 && (
          <Box>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="h5">Provider Management</Typography>
              <Button startIcon={<Refresh />} onClick={fetchProviders} variant="outlined">
                Refresh
              </Button>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : providers.length === 0 ? (
              <Alert severity="info">No providers configured yet.</Alert>
            ) : (
              <Grid container spacing={3}>
                {/* REFACTORED: Using safeMap for provider list */}
                {safeMap(providers, (provider) => (
                  <Grid item xs={12} sm={6} md={4} key={provider.provider_id}>
                    <ProviderCard
                      provider={provider}
                      onEdit={() => {}}
                      onDelete={() => {}}
                      onTest={handleTestProvider}
                    />
                  </Grid>
                ))}
              </Grid>
            )}
          </Box>
        )}

        {/* Tab 3: Routing & Load Balancing */}
        {tabValue === 2 && (
          <Box>
            <Typography variant="h5" gutterBottom>
              Routing Rules & Load Balancing
            </Typography>
            <Alert severity="info" sx={{ mb: 3 }}>
              Routing rules allow you to direct requests to specific providers based on model patterns,
              user tiers, or other conditions.
            </Alert>

            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Load Balancing Strategy
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Current strategy: Round Robin
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                  Configure routing rules to optimize cost, latency, or reliability.
                </Typography>
              </CardContent>
            </Card>
          </Box>
        )}

        {/* Tab 4: Analytics */}
        {tabValue === 3 && (
          <Box>
            <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="h5">Usage & Cost Analytics</Typography>
              <Button startIcon={<Refresh />} onClick={fetchAnalytics} variant="outlined">
                Refresh
              </Button>
            </Box>

            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : (
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <UsageChart data={usage} title="Usage by Model (Last 7 Days)" />
                </Grid>
                <Grid item xs={12} md={6}>
                  <CostChart data={costs} title="Cost Breakdown (Last 30 Days)" />
                </Grid>
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        Summary Statistics
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">
                            Total Requests
                          </Typography>
                          <Typography variant="h4">
                            {Object.values(usage).reduce(
                              (sum, u) => sum + (u.request_count || 0),
                              0
                            ).toLocaleString()}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">
                            Total Tokens
                          </Typography>
                          <Typography variant="h4">
                            {Object.values(usage).reduce(
                              (sum, u) =>
                                sum +
                                (u.total_input_tokens || 0) +
                                (u.total_output_tokens || 0),
                              0
                            ).toLocaleString()}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">
                            Total Cost
                          </Typography>
                          <Typography variant="h4" color="primary">
                            ${Object.values(costs).reduce(
                              (sum, c) => sum + (c.total_cost || 0),
                              0
                            ).toFixed(2)}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                          <Typography variant="body2" color="text.secondary">
                            Avg Latency
                          </Typography>
                          <Typography variant="h4">
                            {(
                              Object.values(usage).reduce(
                                (sum, u) => sum + (u.avg_latency_ms || 0),
                                0
                              ) / Object.keys(usage).length || 0
                            ).toFixed(0)}
                            ms
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            )}
          </Box>
        )}

        {/* Tab 5: Settings */}
        {tabValue === 4 && (
          <Box>
            <Typography variant="h5" gutterBottom>
              Settings
            </Typography>

            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <CacheStatsCard stats={cacheStats} onClear={handleClearCache} />
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Rate Limiting
                    </Typography>
                    <Alert severity="info">
                      Configure rate limits per model, provider, or user to prevent abuse and
                      manage costs.
                    </Alert>
                  </CardContent>
                </Card>
              </Grid>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Fallback Configuration
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Configure automatic fallback to secondary providers when the primary provider
                      fails or is unavailable.
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        )}
      </Box>
    </Container>
  );
}
