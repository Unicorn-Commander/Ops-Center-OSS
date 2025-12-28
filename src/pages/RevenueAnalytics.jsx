/**
 * Revenue Analytics Dashboard
 * Epic 2.6: Advanced Analytics - Revenue Analytics Component
 *
 * Comprehensive revenue analytics dashboard with MRR/ARR tracking,
 * forecasting, and interactive visualizations.
 *
 * Author: Revenue Analytics Lead
 * Created: October 24, 2025
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Button,
  ButtonGroup,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Divider,
  Chip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  AttachMoney as MoneyIcon,
  People as PeopleIcon,
  AccountBalance as AccountBalanceIcon,
  ShowChart as ShowChartIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  CalendarToday as CalendarIcon,
} from '@mui/icons-material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip as ChartTooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Pie, Bar } from 'react-chartjs-2';
import axios from 'axios';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  ChartTooltip,
  Legend,
  Filler
);

// API base URL
const API_BASE_URL = '/api/v1/analytics/revenue';

// Glassmorphism card style
const glassCardStyle = {
  background: 'rgba(255, 255, 255, 0.1)',
  backdropFilter: 'blur(10px)',
  borderRadius: '16px',
  border: '1px solid rgba(255, 255, 255, 0.2)',
  boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
};

const RevenueAnalytics = () => {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState(365); // days
  const [trendPeriod, setTrendPeriod] = useState('monthly');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Data state
  const [overview, setOverview] = useState(null);
  const [trends, setTrends] = useState(null);
  const [planBreakdown, setPlanBreakdown] = useState(null);
  const [forecasts, setForecasts] = useState(null);
  const [churnImpact, setChurnImpact] = useState(null);
  const [ltv, setLtv] = useState(null);
  const [cohorts, setCohorts] = useState(null);

  // Fetch all revenue data
  const fetchRevenueData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        overviewRes,
        trendsRes,
        planRes,
        forecastsRes,
        churnRes,
        ltvRes,
        cohortsRes,
      ] = await Promise.all([
        axios.get(`${API_BASE_URL}/overview`),
        axios.get(`${API_BASE_URL}/trends`, {
          params: { period: trendPeriod, days: timeRange },
        }),
        axios.get(`${API_BASE_URL}/by-plan`),
        axios.get(`${API_BASE_URL}/forecasts`),
        axios.get(`${API_BASE_URL}/churn-impact`),
        axios.get(`${API_BASE_URL}/ltv`),
        axios.get(`${API_BASE_URL}/cohorts/revenue`),
      ]);

      setOverview(overviewRes.data);
      setTrends(trendsRes.data);
      setPlanBreakdown(planRes.data);
      setForecasts(forecastsRes.data);
      setChurnImpact(churnRes.data);
      setLtv(ltvRes.data);
      setCohorts(cohortsRes.data);
    } catch (err) {
      console.error('Error fetching revenue data:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load revenue data');
    } finally {
      setLoading(false);
    }
  }, [timeRange, trendPeriod]);

  // Initial load
  useEffect(() => {
    fetchRevenueData();
  }, [fetchRevenueData]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchRevenueData();
    }, 60000);

    return () => clearInterval(interval);
  }, [autoRefresh, fetchRevenueData]);

  // Export to CSV
  const exportToCSV = () => {
    if (!trends || !trends.data) return;

    const csvContent = [
      ['Date', 'Revenue', 'Customers'].join(','),
      ...trends.data.map((row) =>
        [row.date, row.revenue, row.customers].join(',')
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `revenue-analytics-${new Date().toISOString()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  // Chart colors
  const chartColors = {
    primary: 'rgba(99, 102, 241, 1)',
    primaryTransparent: 'rgba(99, 102, 241, 0.2)',
    success: 'rgba(34, 197, 94, 1)',
    warning: 'rgba(251, 191, 36, 1)',
    danger: 'rgba(239, 68, 68, 1)',
    info: 'rgba(59, 130, 246, 1)',
    purple: 'rgba(168, 85, 247, 1)',
    pink: 'rgba(236, 72, 153, 1)',
  };

  // MRR/ARR Trend Chart Data
  const trendChartData = useMemo(() => {
    if (!trends || !trends.data) return null;

    return {
      labels: trends.data.map((item) => {
        const date = new Date(item.date);
        return trendPeriod === 'monthly'
          ? date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
          : date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }),
      datasets: [
        {
          label: 'Revenue',
          data: trends.data.map((item) => item.revenue),
          borderColor: chartColors.primary,
          backgroundColor: chartColors.primaryTransparent,
          fill: true,
          tension: 0.4,
        },
      ],
    };
  }, [trends, trendPeriod]);

  // Revenue by Plan Pie Chart Data
  const planChartData = useMemo(() => {
    if (!planBreakdown) return null;

    return {
      labels: planBreakdown.map((plan) => plan.plan_name),
      datasets: [
        {
          label: 'MRR',
          data: planBreakdown.map((plan) => plan.mrr),
          backgroundColor: [
            chartColors.primary,
            chartColors.success,
            chartColors.warning,
            chartColors.purple,
            chartColors.pink,
          ],
          borderWidth: 2,
          borderColor: '#fff',
        },
      ],
    };
  }, [planBreakdown]);

  // Revenue Forecast Chart Data
  const forecastChartData = useMemo(() => {
    if (!forecasts || !trends || !trends.data) return null;

    const historicalData = trends.data.slice(-6);
    const lastDate = new Date(historicalData[historicalData.length - 1].date);

    // Generate future months
    const futureLabels = [3, 6, 12].map((months) => {
      const date = new Date(lastDate);
      date.setMonth(date.getMonth() + months);
      return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
    });

    return {
      labels: [
        ...historicalData.map((item) => {
          const date = new Date(item.date);
          return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
        }),
        ...futureLabels,
      ],
      datasets: [
        {
          label: 'Historical Revenue',
          data: [
            ...historicalData.map((item) => item.revenue),
            null,
            null,
            null,
          ],
          borderColor: chartColors.primary,
          backgroundColor: chartColors.primaryTransparent,
          fill: true,
        },
        {
          label: 'Forecast',
          data: [
            ...historicalData.map(() => null),
            forecasts.forecast_3_months,
            forecasts.forecast_6_months,
            forecasts.forecast_12_months,
          ],
          borderColor: chartColors.success,
          backgroundColor: 'rgba(34, 197, 94, 0.1)',
          borderDash: [5, 5],
          fill: true,
        },
        {
          label: 'Confidence Range',
          data: [
            ...historicalData.map(() => null),
            forecasts.confidence_interval_low,
            null,
            forecasts.confidence_interval_high,
          ],
          borderColor: chartColors.warning,
          backgroundColor: 'rgba(251, 191, 36, 0.1)',
          borderDash: [2, 2],
          fill: false,
        },
      ],
    };
  }, [forecasts, trends]);

  // Cohort Revenue Bar Chart Data
  const cohortChartData = useMemo(() => {
    if (!cohorts) return null;

    return {
      labels: cohorts.map((cohort) => {
        const date = new Date(cohort.cohort);
        return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' });
      }),
      datasets: [
        {
          label: 'Total Revenue',
          data: cohorts.map((cohort) => cohort.total_revenue),
          backgroundColor: chartColors.primary,
        },
        {
          label: 'Avg Revenue per Customer',
          data: cohorts.map((cohort) => cohort.average_revenue_per_customer),
          backgroundColor: chartColors.success,
        },
      ],
    };
  }, [cohorts]);

  // Chart options
  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => formatCurrency(value),
        },
      },
    },
  };

  const pieChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed || 0;
            return `${label}: ${formatCurrency(value)}`;
          },
        },
      },
    },
  };

  const barChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top',
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `${context.dataset.label}: ${formatCurrency(context.parsed.y)}`;
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: (value) => formatCurrency(value),
        },
      },
    },
  };

  // Loading state
  if (loading && !overview) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="80vh"
      >
        <CircularProgress size={60} />
      </Box>
    );
  }

  // Error state
  if (error && !overview) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4" fontWeight="bold">
          Revenue Analytics
        </Typography>
        <Box display="flex" gap={2} alignItems="center">
          <ButtonGroup variant="outlined">
            <Button
              onClick={() => setTimeRange(30)}
              variant={timeRange === 30 ? 'contained' : 'outlined'}
            >
              30D
            </Button>
            <Button
              onClick={() => setTimeRange(90)}
              variant={timeRange === 90 ? 'contained' : 'outlined'}
            >
              90D
            </Button>
            <Button
              onClick={() => setTimeRange(365)}
              variant={timeRange === 365 ? 'contained' : 'outlined'}
            >
              1Y
            </Button>
          </ButtonGroup>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={trendPeriod}
              onChange={(e) => setTrendPeriod(e.target.value)}
              label="Period"
            >
              <MenuItem value="daily">Daily</MenuItem>
              <MenuItem value="weekly">Weekly</MenuItem>
              <MenuItem value="monthly">Monthly</MenuItem>
            </Select>
          </FormControl>
          <Tooltip title="Export to CSV">
            <IconButton onClick={exportToCSV} color="primary">
              <DownloadIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={autoRefresh ? 'Auto-refresh enabled' : 'Auto-refresh disabled'}>
            <IconButton
              onClick={() => setAutoRefresh(!autoRefresh)}
              color={autoRefresh ? 'primary' : 'default'}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Key Metrics Cards */}
      {overview && (
        <Grid container spacing={3} mb={4}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={glassCardStyle}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <MoneyIcon sx={{ mr: 1, color: chartColors.primary }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    MRR
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {formatCurrency(overview.mrr)}
                </Typography>
                <Box display="flex" alignItems="center" mt={1}>
                  {overview.growth_rate >= 0 ? (
                    <TrendingUpIcon sx={{ color: chartColors.success, mr: 0.5 }} />
                  ) : (
                    <TrendingDownIcon sx={{ color: chartColors.danger, mr: 0.5 }} />
                  )}
                  <Typography
                    variant="body2"
                    color={overview.growth_rate >= 0 ? 'success.main' : 'error.main'}
                  >
                    {formatPercentage(Math.abs(overview.growth_rate))} MoM
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={glassCardStyle}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <AccountBalanceIcon sx={{ mr: 1, color: chartColors.success }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    ARR
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {formatCurrency(overview.arr)}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  Annual Run Rate
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={glassCardStyle}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <PeopleIcon sx={{ mr: 1, color: chartColors.info }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    Active Customers
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {overview.total_customers.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  ARPU: {formatCurrency(overview.average_revenue_per_user)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card sx={glassCardStyle}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={1}>
                  <ShowChartIcon sx={{ mr: 1, color: chartColors.warning }} />
                  <Typography variant="subtitle2" color="text.secondary">
                    Churn Rate
                  </Typography>
                </Box>
                <Typography variant="h4" fontWeight="bold">
                  {formatPercentage(overview.churn_rate)}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={1}>
                  {overview.active_subscriptions} subscriptions
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Revenue Trend Chart */}
      {trendChartData && (
        <Card sx={{ ...glassCardStyle, mb: 4 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Revenue Trends
            </Typography>
            <Box height={400}>
              <Line data={trendChartData} options={lineChartOptions} />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Revenue by Plan and Forecast */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          {planChartData && (
            <Card sx={{ ...glassCardStyle, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={2}>
                  Revenue by Plan
                </Typography>
                <Box height={350}>
                  <Pie data={planChartData} options={pieChartOptions} />
                </Box>
                <Divider sx={{ my: 2 }} />
                {planBreakdown && (
                  <Box>
                    {planBreakdown.map((plan) => (
                      <Box
                        key={plan.plan_code}
                        display="flex"
                        justifyContent="space-between"
                        alignItems="center"
                        mb={1}
                      >
                        <Typography variant="body2">{plan.plan_name}</Typography>
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip
                            label={`${plan.subscriber_count} subs`}
                            size="small"
                            variant="outlined"
                          />
                          <Typography variant="body2" fontWeight="bold">
                            {formatCurrency(plan.mrr)}
                          </Typography>
                        </Box>
                      </Box>
                    ))}
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          {forecastChartData && (
            <Card sx={{ ...glassCardStyle, height: '100%' }}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={2}>
                  Revenue Forecast
                </Typography>
                <Box height={350}>
                  <Line data={forecastChartData} options={lineChartOptions} />
                </Box>
                <Divider sx={{ my: 2 }} />
                {forecasts && (
                  <Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">3 Months</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {formatCurrency(forecasts.forecast_3_months)}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">6 Months</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {formatCurrency(forecasts.forecast_6_months)}
                      </Typography>
                    </Box>
                    <Box display="flex" justifyContent="space-between" mb={1}>
                      <Typography variant="body2">12 Months</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {formatCurrency(forecasts.forecast_12_months)}
                      </Typography>
                    </Box>
                    <Typography variant="caption" color="text.secondary" mt={1}>
                      Accuracy Score: {formatPercentage(forecasts.accuracy_score * 100)}
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* LTV and Churn Impact */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={6}>
          {ltv && (
            <Card sx={glassCardStyle}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={2}>
                  Customer Lifetime Value
                </Typography>
                <Box mb={3}>
                  <Typography variant="body2" color="text.secondary">
                    Average LTV
                  </Typography>
                  <Typography variant="h4" fontWeight="bold">
                    {formatCurrency(ltv.average_ltv)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" mt={1}>
                    Avg Lifetime: {ltv.average_customer_lifetime_months.toFixed(1)} months
                  </Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <Typography variant="subtitle2" mb={1}>
                  LTV by Plan
                </Typography>
                {Object.entries(ltv.ltv_by_plan).map(([plan, value]) => (
                  <Box
                    key={plan}
                    display="flex"
                    justifyContent="space-between"
                    mb={1}
                  >
                    <Typography variant="body2">{plan}</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {formatCurrency(value)}
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid item xs={12} md={6}>
          {churnImpact && (
            <Card sx={glassCardStyle}>
              <CardContent>
                <Typography variant="h6" fontWeight="bold" mb={2}>
                  Churn Impact
                </Typography>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Churned MRR
                  </Typography>
                  <Typography variant="h4" fontWeight="bold" color="error.main">
                    {formatCurrency(churnImpact.churned_mrr)}
                  </Typography>
                </Box>
                <Divider sx={{ mb: 2 }} />
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Churned Subscribers</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {churnImpact.churned_subscribers}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Churn Rate</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {formatPercentage(churnImpact.churn_rate)}
                  </Typography>
                </Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2">Annual Revenue Impact</Typography>
                  <Typography variant="body2" fontWeight="bold" color="error.main">
                    {formatCurrency(churnImpact.revenue_impact)}
                  </Typography>
                </Box>
                <Typography variant="caption" color="text.secondary" mt={1}>
                  Period: {churnImpact.period.replace('_', ' ')}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>

      {/* Cohort Revenue Chart */}
      {cohortChartData && (
        <Card sx={glassCardStyle}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Cohort Revenue Analysis
            </Typography>
            <Box height={400}>
              <Bar data={cohortChartData} options={barChartOptions} />
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Cohort Revenue Table */}
      {cohorts && cohorts.length > 0 && (
        <Card sx={{ ...glassCardStyle, mt: 4 }}>
          <CardContent>
            <Typography variant="h6" fontWeight="bold" mb={2}>
              Cohort Details
            </Typography>
            <TableContainer component={Paper} sx={{ bgcolor: 'transparent' }}>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Cohort</TableCell>
                    <TableCell align="right">Customers</TableCell>
                    <TableCell align="right">Total Revenue</TableCell>
                    <TableCell align="right">Avg Revenue/Customer</TableCell>
                    <TableCell align="right">Retention Rate</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {cohorts.map((cohort) => (
                    <TableRow key={cohort.cohort}>
                      <TableCell>
                        {new Date(cohort.cohort).toLocaleDateString('en-US', {
                          month: 'short',
                          year: 'numeric',
                        })}
                      </TableCell>
                      <TableCell align="right">
                        {cohort.customer_count.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        {formatCurrency(cohort.total_revenue)}
                      </TableCell>
                      <TableCell align="right">
                        {formatCurrency(cohort.average_revenue_per_customer)}
                      </TableCell>
                      <TableCell align="right">
                        <Chip
                          label={formatPercentage(cohort.retention_rate)}
                          color={cohort.retention_rate >= 80 ? 'success' : 'warning'}
                          size="small"
                        />
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      )}
    </Container>
  );
};

export default RevenueAnalytics;
