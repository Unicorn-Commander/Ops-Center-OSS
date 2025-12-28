import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Alert,
  AlertTitle,
  IconButton,
  Skeleton,
  Chip,
  Tooltip,
  Switch,
  FormControlLabel,
  Divider,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Download,
  Refresh,
  Close,
  Cloud,
  Search,
  Psychology,
  RecordVoiceOver,
  Hearing,
  Storage,
  TrendingFlat,
  Lightbulb,
  Warning,
  CheckCircle,
  Info,
  AttachMoney,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Service configuration with icons and colors
const SERVICE_CONFIG = {
  llm_inference: {
    name: 'LLM Inference',
    icon: Psychology,
    unit: 'tokens',
    color: '#9333ea',
  },
  search_queries: {
    name: 'Search Queries',
    icon: Search,
    unit: 'searches',
    color: '#3b82f6',
  },
  agent_invocations: {
    name: 'Agent Invocations',
    icon: Cloud,
    unit: 'calls',
    color: '#10b981',
  },
  tts: {
    name: 'Text-to-Speech',
    icon: RecordVoiceOver,
    unit: 'minutes',
    color: '#f59e0b',
  },
  stt: {
    name: 'Speech-to-Text',
    icon: Hearing,
    unit: 'minutes',
    color: '#ef4444',
  },
  storage: {
    name: 'Storage',
    icon: Storage,
    unit: 'GB',
    color: '#8b5cf6',
  },
};

// Mock data generator (use if API not ready)
const generateMockData = () => {
  const services = Object.keys(SERVICE_CONFIG);
  const mockSummary = {
    period: '2025-10',
    total_cost: 42.50,
    tier_limit: 10000,
    usage_percentage: 65,
    services: {},
  };

  services.forEach((serviceKey) => {
    const baseUsage = Math.floor(Math.random() * 1000) + 100;
    mockSummary.services[serviceKey] = {
      count: baseUsage,
      unit: SERVICE_CONFIG[serviceKey].unit,
      cost: (baseUsage * 0.002).toFixed(2),
      limit: 1000,
      usage_percentage: (baseUsage / 1000) * 100,
      change_percentage: Math.floor(Math.random() * 40) - 10,
      last_period_count: baseUsage - Math.floor(Math.random() * 200),
    };
  });

  return mockSummary;
};

// Calculate linear regression trend from data points
const calculateTrend = (dataPoints) => {
  if (!dataPoints || dataPoints.length < 2) {
    return { slope: 0, intercept: 0, trend: 'stable', confidence: 'low' };
  }

  // Simple linear regression
  const n = dataPoints.length;
  const sumX = dataPoints.reduce((sum, _, i) => sum + i, 0);
  const sumY = dataPoints.reduce((sum, d) => sum + (d.usage || d.value || 0), 0);
  const sumXY = dataPoints.reduce((sum, d, i) => sum + i * (d.usage || d.value || 0), 0);
  const sumX2 = dataPoints.reduce((sum, _, i) => sum + i * i, 0);

  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  const intercept = (sumY - slope * sumX) / n;

  // Calculate R-squared for confidence
  const yMean = sumY / n;
  const ssTotal = dataPoints.reduce((sum, d) => {
    const y = d.usage || d.value || 0;
    return sum + Math.pow(y - yMean, 2);
  }, 0);
  const ssRes = dataPoints.reduce((sum, d, i) => {
    const y = d.usage || d.value || 0;
    const predicted = slope * i + intercept;
    return sum + Math.pow(y - predicted, 2);
  }, 0);
  const rSquared = 1 - (ssRes / ssTotal);

  // Determine trend direction
  const avgValue = sumY / n;
  const slopePercent = (slope / avgValue) * 100;
  let trend = 'stable';
  if (slopePercent > 5) trend = 'up';
  else if (slopePercent < -5) trend = 'down';

  // Determine confidence based on R-squared
  let confidence = 'low';
  if (rSquared > 0.7) confidence = 'high';
  else if (rSquared > 0.4) confidence = 'medium';

  return { slope, intercept, trend, slopePercent, confidence, rSquared };
};

// Generate projection data points based on trend
const projectFutureDays = (chartData, days = 7) => {
  if (!chartData || chartData.length === 0) return [];

  // Use last 14 days for trend calculation
  const recentData = chartData.slice(-14);
  const trend = calculateTrend(recentData);

  const projections = [];
  const startIndex = chartData.length;
  const today = new Date();

  for (let i = 1; i <= days; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() + i);
    const projectedValue = Math.max(0, trend.slope * (startIndex + i) + trend.intercept);

    projections.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      projected: Math.round(projectedValue),
      usage: null,
    });
  }

  return projections;
};

// Generate insights based on service data and trends
const generateInsights = (serviceData, chartData, serviceName) => {
  const insights = [];

  if (!serviceData || !chartData || chartData.length === 0) return insights;

  const usagePercent = serviceData.usage_percentage || 0;
  const recentData = chartData.slice(-7);
  const trend = calculateTrend(recentData);

  // Rule 1: High usage warning
  if (usagePercent > 80) {
    insights.push({
      type: 'warning',
      icon: Warning,
      title: 'High Usage Alert',
      message: `${serviceName} at ${usagePercent.toFixed(1)}% of limit. Consider upgrading to avoid service interruption.`,
    });
  }

  // Rule 2: Trending up alert
  if (trend.trend === 'up' && trend.slopePercent > 20) {
    const projectedMonthly = (serviceData.count || 0) * (1 + trend.slopePercent / 100);
    insights.push({
      type: 'info',
      icon: TrendingUp,
      title: 'Usage Trending Up',
      message: `${serviceName} usage trending up ${Math.abs(trend.slopePercent).toFixed(1)}% this week. Projected monthly: ${Math.round(projectedMonthly).toLocaleString()} ${serviceData.unit}.`,
    });
  }

  // Rule 3: Cost savings opportunity
  if (trend.trend === 'down' && trend.slopePercent < -20) {
    insights.push({
      type: 'success',
      icon: CheckCircle,
      title: 'Usage Decreasing',
      message: `Good news! ${serviceName} usage decreased ${Math.abs(trend.slopePercent).toFixed(1)}% this week. You may be eligible for a lower tier.`,
    });
  }

  // Rule 4: Approaching limit
  if (usagePercent > 50 && usagePercent <= 80 && trend.trend === 'up') {
    const daysToLimit = ((100 - usagePercent) / trend.slopePercent) * 7;
    if (daysToLimit < 30 && daysToLimit > 0) {
      insights.push({
        type: 'warning',
        icon: Info,
        title: 'Approaching Limit',
        message: `At current rate, ${serviceName} will reach limit in ~${Math.round(daysToLimit)} days.`,
      });
    }
  }

  // Rule 5: Stable usage (low variance)
  if (trend.trend === 'stable' && trend.confidence === 'high') {
    insights.push({
      type: 'success',
      icon: TrendingFlat,
      title: 'Stable Usage Pattern',
      message: `${serviceName} shows consistent usage. Current plan is well-suited to your needs.`,
    });
  }

  // Rule 6: Under-utilization
  if (usagePercent < 20 && trend.trend === 'stable') {
    insights.push({
      type: 'info',
      icon: Lightbulb,
      title: 'Under-Utilization Detected',
      message: `${serviceName} is only at ${usagePercent.toFixed(1)}% usage. You may save costs with a lower tier.`,
    });
  }

  return insights;
};

// Calculate projected monthly cost
const calculateProjectedCost = (summary, tableData, chartData) => {
  if (!summary || !tableData || tableData.length === 0) {
    return { total: 0, breakdown: {}, confidence: 'low', comparison: 0 };
  }

  const currentDay = new Date().getDate();
  const daysInMonth = new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).getDate();
  const daysRemaining = daysInMonth - currentDay;

  let projectedTotal = 0;
  const breakdown = {};
  let confidenceScore = 0;

  Object.keys(SERVICE_CONFIG).forEach((serviceKey) => {
    const service = summary.services?.[serviceKey];
    if (!service) return;

    // Get trend from recent data
    const serviceChartData = chartData[serviceKey] || [];
    const trend = calculateTrend(serviceChartData.slice(-7));

    // Calculate daily average
    const dailyAverage = (service.count || 0) / currentDay;

    // Project to end of month
    const projectedCount = service.count + (dailyAverage * daysRemaining * (1 + trend.slopePercent / 100));
    const projectedCost = (projectedCount * 0.002); // Mock pricing

    projectedTotal += projectedCost;
    breakdown[serviceKey] = {
      name: SERVICE_CONFIG[serviceKey].name,
      current: service.cost,
      projected: projectedCost.toFixed(2),
      count: Math.round(projectedCount),
    };

    confidenceScore += trend.rSquared || 0;
  });

  const avgConfidence = confidenceScore / Object.keys(SERVICE_CONFIG).length;
  let confidence = 'low';
  if (avgConfidence > 0.7) confidence = 'high';
  else if (avgConfidence > 0.4) confidence = 'medium';

  const comparison = summary.total_cost ? ((projectedTotal - summary.total_cost) / summary.total_cost) * 100 : 0;

  return { total: projectedTotal, breakdown, confidence, comparison };
};

// Generate 30 days of mock chart data
const generateMockChartData = (serviceKey) => {
  const data = [];
  const today = new Date();

  // Generate realistic trend
  const trendFactor = Math.random() > 0.5 ? 1 : -1;
  const baseValue = Math.floor(Math.random() * 50) + 50;

  for (let i = 29; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);

    // Add trend and noise
    const trendValue = baseValue + (trendFactor * (29 - i) * 0.5);
    const noise = (Math.random() - 0.5) * 20;
    const value = Math.max(10, Math.round(trendValue + noise));

    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      usage: value,
    });
  }

  return data;
};

// Generate mock table data
const generateMockTableData = () => {
  return Object.keys(SERVICE_CONFIG).map((serviceKey) => {
    const currentPeriod = Math.floor(Math.random() * 1000) + 100;
    const lastPeriod = Math.floor(Math.random() * 1000) + 100;
    const change = ((currentPeriod - lastPeriod) / lastPeriod * 100).toFixed(1);
    const cost = (currentPeriod * 0.002).toFixed(2);
    const usagePercent = (currentPeriod / 1000) * 100;

    let status = 'normal';
    if (usagePercent > 80) status = 'critical';
    else if (usagePercent > 50) status = 'warning';

    return {
      service: serviceKey,
      currentPeriod,
      lastPeriod,
      change: parseFloat(change),
      cost: parseFloat(cost),
      status,
    };
  });
};

// Generate mock alerts
const generateMockAlerts = () => {
  return [
    {
      id: 1,
      service: 'llm_inference',
      severity: 'warning',
      message: 'LLM Inference usage at 85% of monthly limit',
      action: 'Consider upgrading to Professional tier',
    },
    {
      id: 2,
      service: 'search_queries',
      severity: 'info',
      message: 'Search usage trending up 25% this week',
      action: 'Monitor for potential overage',
    },
  ];
};

function UsageMetrics() {
  // State management
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [selectedPeriod, setSelectedPeriod] = useState('this_month');
  const [selectedService, setSelectedService] = useState('llm_inference');
  const [chartData, setChartData] = useState([]);
  const [tableData, setTableData] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [sortBy, setSortBy] = useState('service');
  const [sortOrder, setSortOrder] = useState('asc');
  const [dismissedAlerts, setDismissedAlerts] = useState([]);

  // New state for enhancements
  const [comparisonMode, setComparisonMode] = useState(false);
  const [lastPeriodChartData, setLastPeriodChartData] = useState([]);
  const [allServiceChartData, setAllServiceChartData] = useState({});
  const [insights, setInsights] = useState([]);
  const [projectedCost, setProjectedCost] = useState(null);

  // Fetch data
  useEffect(() => {
    fetchData();
  }, [selectedPeriod]);

  // Fetch chart data when service changes
  useEffect(() => {
    if (selectedService) {
      fetchChartData(selectedService);
    }
  }, [selectedService, selectedPeriod, comparisonMode]);

  // Calculate projected cost whenever data changes
  useEffect(() => {
    if (summary && Object.keys(allServiceChartData).length > 0) {
      const projection = calculateProjectedCost(summary, tableData, allServiceChartData);
      setProjectedCost(projection);
    }
  }, [summary, tableData, allServiceChartData]);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Try to fetch from API
      const response = await fetch(`/api/v1/metering/summary?period=${selectedPeriod}`, {
        credentials: 'include',
      });

      if (response.ok) {
        const data = await response.json();
        setSummary(data);
        setTableData(generateTableDataFromSummary(data));

        // Fetch alerts
        const alertsResponse = await fetch('/api/v1/metering/alerts', {
          credentials: 'include',
        });
        if (alertsResponse.ok) {
          const alertsData = await alertsResponse.json();
          setAlerts(alertsData.alerts || []);
        }

        // Fetch all service chart data for insights and cost projection
        const allChartData = {};
        for (const serviceKey of Object.keys(SERVICE_CONFIG)) {
          const chartResponse = await fetch(
            `/api/v1/metering/service/${serviceKey}?period=${selectedPeriod}`,
            { credentials: 'include' }
          );
          if (chartResponse.ok) {
            const chartDataResult = await chartResponse.json();
            allChartData[serviceKey] = chartDataResult.daily_usage || [];
          }
        }
        setAllServiceChartData(allChartData);
      } else {
        throw new Error('API not available, using mock data');
      }
    } catch (err) {
      console.warn('Using mock data:', err.message);
      // Use mock data
      const mockData = generateMockData();
      setSummary(mockData);
      setTableData(generateMockTableData());
      setAlerts(generateMockAlerts());

      // Generate mock chart data for all services
      const allChartData = {};
      Object.keys(SERVICE_CONFIG).forEach((serviceKey) => {
        allChartData[serviceKey] = generateMockChartData(serviceKey);
      });
      setAllServiceChartData(allChartData);
    } finally {
      setLoading(false);
    }
  };

  const fetchChartData = async (serviceKey) => {
    try {
      const response = await fetch(
        `/api/v1/metering/service/${serviceKey}?period=${selectedPeriod}`,
        { credentials: 'include' }
      );

      if (response.ok) {
        const data = await response.json();
        const currentData = data.daily_usage || [];
        setChartData(currentData);

        // Fetch last period data for comparison
        if (comparisonMode) {
          const lastPeriodMap = {
            'this_month': 'last_month',
            'last_month': 'last_3_months',
            'last_3_months': 'last_6_months',
          };
          const lastPeriod = lastPeriodMap[selectedPeriod] || 'last_month';

          const lastResponse = await fetch(
            `/api/v1/metering/service/${serviceKey}?period=${lastPeriod}`,
            { credentials: 'include' }
          );
          if (lastResponse.ok) {
            const lastData = await lastResponse.json();
            setLastPeriodChartData(lastData.daily_usage || []);
          }
        }

        // Generate insights for selected service
        if (summary && summary.services?.[serviceKey]) {
          const serviceInsights = generateInsights(
            summary.services[serviceKey],
            currentData,
            SERVICE_CONFIG[serviceKey].name
          );
          setInsights(serviceInsights);
        }
      } else {
        throw new Error('API not available');
      }
    } catch (err) {
      // Use mock chart data
      const currentData = generateMockChartData(serviceKey);
      setChartData(currentData);

      if (comparisonMode) {
        setLastPeriodChartData(generateMockChartData(serviceKey));
      }

      // Generate insights from mock data
      if (summary && summary.services?.[serviceKey]) {
        const serviceInsights = generateInsights(
          summary.services[serviceKey],
          currentData,
          SERVICE_CONFIG[serviceKey].name
        );
        setInsights(serviceInsights);
      }
    }
  };

  const generateTableDataFromSummary = (summaryData) => {
    return Object.keys(summaryData.services).map((serviceKey) => {
      const service = summaryData.services[serviceKey];
      return {
        service: serviceKey,
        currentPeriod: service.count,
        lastPeriod: service.last_period_count,
        change: service.change_percentage,
        cost: service.cost,
        status: service.usage_percentage > 80 ? 'critical' :
                service.usage_percentage > 50 ? 'warning' : 'normal',
      };
    });
  };

  const handleSort = (column) => {
    const isAsc = sortBy === column && sortOrder === 'asc';
    setSortOrder(isAsc ? 'desc' : 'asc');
    setSortBy(column);
  };

  const sortedTableData = [...tableData].sort((a, b) => {
    const multiplier = sortOrder === 'asc' ? 1 : -1;
    if (sortBy === 'service') {
      return multiplier * a.service.localeCompare(b.service);
    }
    return multiplier * (a[sortBy] - b[sortBy]);
  });

  const exportToCSV = () => {
    const headers = ['Service', 'Current Period', 'Last Period', 'Change %', 'Cost', 'Status'];
    const rows = tableData.map((row) => [
      SERVICE_CONFIG[row.service].name,
      row.currentPeriod,
      row.lastPeriod,
      `${row.change}%`,
      `$${row.cost}`,
      row.status,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map((row) => row.join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `usage-metrics-${selectedPeriod}.csv`;
    a.click();
  };

  const dismissAlert = (alertId) => {
    setDismissedAlerts([...dismissedAlerts, alertId]);
  };

  const getUsageColor = (percentage) => {
    if (percentage > 80) return '#ef4444';
    if (percentage > 50) return '#f59e0b';
    return '#10b981';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'critical':
        return '#ef4444';
      case 'warning':
        return '#f59e0b';
      default:
        return '#10b981';
    }
  };

  const visibleAlerts = alerts.filter((alert) => !dismissedAlerts.includes(alert.id));

  if (loading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          Usage Metrics
        </Typography>
        <Grid container spacing={3}>
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Skeleton variant="rectangular" height={200} />
            </Grid>
          ))}
        </Grid>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header Section */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Usage Metrics
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Period</InputLabel>
            <Select
              value={selectedPeriod}
              label="Period"
              onChange={(e) => setSelectedPeriod(e.target.value)}
            >
              <MenuItem value="this_month">This Month</MenuItem>
              <MenuItem value="last_month">Last Month</MenuItem>
              <MenuItem value="last_3_months">Last 3 Months</MenuItem>
              <MenuItem value="last_6_months">Last 6 Months</MenuItem>
            </Select>
          </FormControl>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={fetchData}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Total Cost Display */}
      <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}>
        <Typography variant="h6" sx={{ color: 'white', mb: 1 }}>
          Total Cost This Period
        </Typography>
        <Typography variant="h2" sx={{ color: 'white', fontWeight: 700, mb: 2 }}>
          ${summary?.total_cost?.toFixed(2) || '0.00'}
        </Typography>
        <Box sx={{ mb: 1 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="body2" sx={{ color: 'white' }}>
              Usage: {summary?.usage_percentage || 0}% of tier limit
            </Typography>
            <Typography variant="body2" sx={{ color: 'white' }}>
              {summary?.tier_limit?.toLocaleString() || '0'} limit
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={summary?.usage_percentage || 0}
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(255,255,255,0.3)',
              '& .MuiLinearProgress-bar': {
                backgroundColor: getUsageColor(summary?.usage_percentage || 0),
                borderRadius: 4,
              },
            }}
          />
        </Box>
      </Paper>

      {/* Alerts Section */}
      {visibleAlerts.length > 0 && (
        <Box sx={{ mb: 3 }}>
          {visibleAlerts.map((alert) => (
            <Alert
              key={alert.id}
              severity={alert.severity}
              action={
                <IconButton
                  aria-label="close"
                  color="inherit"
                  size="small"
                  onClick={() => dismissAlert(alert.id)}
                >
                  <Close fontSize="inherit" />
                </IconButton>
              }
              sx={{ mb: 1 }}
            >
              <AlertTitle>{SERVICE_CONFIG[alert.service]?.name || alert.service}</AlertTitle>
              {alert.message} — <strong>{alert.action}</strong>
            </Alert>
          ))}
        </Box>
      )}

      {/* Service Cards Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {Object.keys(SERVICE_CONFIG).map((serviceKey) => {
          const service = summary?.services?.[serviceKey];
          if (!service) return null;

          const Icon = SERVICE_CONFIG[serviceKey].icon;
          const usagePercent = service.usage_percentage || 0;

          // Calculate trend from recent chart data
          const serviceChartData = allServiceChartData[serviceKey] || [];
          const recentData = serviceChartData.slice(-7);
          const trendAnalysis = calculateTrend(recentData);

          // Determine trend icon and color
          let TrendIcon = TrendingFlat;
          let trendColor = '#6b7280';
          let trendLabel = 'Stable';

          if (trendAnalysis.trend === 'up') {
            TrendIcon = TrendingUp;
            trendColor = Math.abs(trendAnalysis.slopePercent) > 20 ? '#ef4444' : '#f59e0b';
            trendLabel = `↑ ${Math.abs(trendAnalysis.slopePercent).toFixed(1)}%`;
          } else if (trendAnalysis.trend === 'down') {
            TrendIcon = TrendingDown;
            trendColor = '#10b981';
            trendLabel = `↓ ${Math.abs(trendAnalysis.slopePercent).toFixed(1)}%`;
          }

          return (
            <Grid item xs={12} sm={6} md={4} key={serviceKey}>
              <Card
                sx={{
                  cursor: 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                  border: selectedService === serviceKey ? `2px solid ${SERVICE_CONFIG[serviceKey].color}` : '1px solid #e5e7eb',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    boxShadow: 3,
                  },
                }}
                onClick={() => setSelectedService(serviceKey)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Icon sx={{ fontSize: 40, color: SERVICE_CONFIG[serviceKey].color }} />
                    <Tooltip title={`Trend: ${trendAnalysis.trend} (${trendAnalysis.confidence} confidence)`}>
                      <Chip
                        icon={<TrendIcon />}
                        label={trendLabel}
                        size="small"
                        sx={{
                          backgroundColor: `${trendColor}20`,
                          color: trendColor,
                          fontWeight: 600,
                        }}
                      />
                    </Tooltip>
                  </Box>
                  <Typography variant="h6" sx={{ mb: 1, color: '#374151' }}>
                    {SERVICE_CONFIG[serviceKey].name}
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: SERVICE_CONFIG[serviceKey].color, mb: 1 }}>
                    {service.count?.toLocaleString() || 0}
                  </Typography>
                  <Typography variant="body2" sx={{ color: '#6b7280', mb: 2 }}>
                    {service.unit} • ${service.cost}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min(usagePercent, 100)}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      backgroundColor: '#e5e7eb',
                      '& .MuiLinearProgress-bar': {
                        backgroundColor: getUsageColor(usagePercent),
                        borderRadius: 3,
                      },
                    }}
                  />
                  <Typography variant="caption" sx={{ color: '#6b7280', mt: 0.5, display: 'block' }}>
                    {usagePercent.toFixed(1)}% of limit
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Cost Forecast Card - NEW */}
      {projectedCost && (
        <Paper sx={{ p: 3, mb: 4, background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <Box>
              <Typography variant="h6" sx={{ color: 'white', mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                <AttachMoney /> Projected Monthly Cost
              </Typography>
              <Typography variant="h2" sx={{ color: 'white', fontWeight: 700, mb: 2 }}>
                ${projectedCost.total.toFixed(2)}
              </Typography>
              <Box sx={{ display: 'flex', gap: 3, alignItems: 'center' }}>
                <Chip
                  label={`${projectedCost.confidence.toUpperCase()} Confidence`}
                  size="small"
                  sx={{
                    backgroundColor: 'rgba(255,255,255,0.3)',
                    color: 'white',
                    fontWeight: 600,
                  }}
                />
                <Typography variant="body2" sx={{ color: 'white' }}>
                  {projectedCost.comparison > 0 ? '+' : ''}{projectedCost.comparison.toFixed(1)}% vs current
                </Typography>
              </Box>
            </Box>
            <Box sx={{ textAlign: 'right' }}>
              <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.9)' }}>
                Based on last 14 days
              </Typography>
            </Box>
          </Box>
        </Paper>
      )}

      {/* Insights Panel - NEW */}
      {insights.length > 0 && (
        <Box sx={{ mb: 4 }}>
          <Typography variant="h6" sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <Lightbulb sx={{ color: '#f59e0b' }} /> Smart Insights
          </Typography>
          <Grid container spacing={2}>
            {insights.map((insight, index) => {
              const InsightIcon = insight.icon;
              const colorMap = {
                warning: '#f59e0b',
                info: '#3b82f6',
                success: '#10b981',
              };
              const bgColorMap = {
                warning: '#fef3c7',
                info: '#dbeafe',
                success: '#d1fae5',
              };

              return (
                <Grid item xs={12} md={6} key={index}>
                  <Paper
                    sx={{
                      p: 2,
                      backgroundColor: bgColorMap[insight.type],
                      border: `1px solid ${colorMap[insight.type]}40`,
                    }}
                  >
                    <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-start' }}>
                      <InsightIcon sx={{ color: colorMap[insight.type], fontSize: 32, mt: 0.5 }} />
                      <Box sx={{ flex: 1 }}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#374151', mb: 0.5 }}>
                          {insight.title}
                        </Typography>
                        <Typography variant="body2" sx={{ color: '#6b7280' }}>
                          {insight.message}
                        </Typography>
                      </Box>
                    </Box>
                  </Paper>
                </Grid>
              );
            })}
          </Grid>
        </Box>
      )}

      {/* Usage Chart */}
      <Paper sx={{ p: 3, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">
            {SERVICE_CONFIG[selectedService]?.name || 'Service'} - Daily Usage
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
            <FormControlLabel
              control={
                <Switch
                  checked={comparisonMode}
                  onChange={(e) => setComparisonMode(e.target.checked)}
                  size="small"
                />
              }
              label="Compare to Last Period"
            />
            <FormControl size="small" sx={{ minWidth: 200 }}>
              <InputLabel>Service</InputLabel>
              <Select
                value={selectedService}
                label="Service"
                onChange={(e) => setSelectedService(e.target.value)}
              >
                {Object.keys(SERVICE_CONFIG).map((key) => (
                  <MenuItem key={key} value={key}>
                    {SERVICE_CONFIG[key].name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </Box>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={[...chartData, ...projectFutureDays(chartData)]}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis
              dataKey="date"
              stroke="#6b7280"
              style={{ fontSize: 12 }}
            />
            <YAxis
              stroke="#6b7280"
              style={{ fontSize: 12 }}
            />
            <RechartsTooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e5e7eb',
                borderRadius: 8,
              }}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="usage"
              stroke={SERVICE_CONFIG[selectedService]?.color || '#3b82f6'}
              strokeWidth={3}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
              name="Actual Usage"
            />
            {comparisonMode && lastPeriodChartData.length > 0 && (
              <Line
                type="monotone"
                dataKey="usage"
                data={lastPeriodChartData}
                stroke="#9ca3af"
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={{ r: 3 }}
                name="Last Period"
              />
            )}
            <Line
              type="monotone"
              dataKey="projected"
              stroke="#f59e0b"
              strokeWidth={2}
              strokeDasharray="8 4"
              dot={false}
              name="Projected (7 days)"
            />
          </LineChart>
        </ResponsiveContainer>
        <Box sx={{ mt: 2, display: 'flex', gap: 2, justifyContent: 'center', flexWrap: 'wrap' }}>
          <Chip
            size="small"
            label="Actual: Solid line (current period)"
            sx={{ backgroundColor: SERVICE_CONFIG[selectedService]?.color, color: 'white' }}
          />
          {comparisonMode && (
            <Chip
              size="small"
              label="Last Period: Dashed gray"
              sx={{ backgroundColor: '#9ca3af', color: 'white' }}
            />
          )}
          <Chip
            size="small"
            label="Projected: Dashed orange (next 7 days)"
            sx={{ backgroundColor: '#f59e0b', color: 'white' }}
          />
        </Box>
      </Paper>

      {/* Service Breakdown Table */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h6">Service Breakdown</Typography>
          <Button
            variant="outlined"
            startIcon={<Download />}
            onClick={exportToCSV}
          >
            Export CSV
          </Button>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>
                  <TableSortLabel
                    active={sortBy === 'service'}
                    direction={sortBy === 'service' ? sortOrder : 'asc'}
                    onClick={() => handleSort('service')}
                  >
                    Service
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={sortBy === 'currentPeriod'}
                    direction={sortBy === 'currentPeriod' ? sortOrder : 'asc'}
                    onClick={() => handleSort('currentPeriod')}
                  >
                    Current Period
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={sortBy === 'lastPeriod'}
                    direction={sortBy === 'lastPeriod' ? sortOrder : 'asc'}
                    onClick={() => handleSort('lastPeriod')}
                  >
                    Last Period
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={sortBy === 'change'}
                    direction={sortBy === 'change' ? sortOrder : 'asc'}
                    onClick={() => handleSort('change')}
                  >
                    Change %
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={sortBy === 'cost'}
                    direction={sortBy === 'cost' ? sortOrder : 'asc'}
                    onClick={() => handleSort('cost')}
                  >
                    Cost
                  </TableSortLabel>
                </TableCell>
                <TableCell align="center">Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {sortedTableData.map((row) => {
                const Icon = SERVICE_CONFIG[row.service]?.icon;
                return (
                  <TableRow
                    key={row.service}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => setSelectedService(row.service)}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        {Icon && <Icon sx={{ color: SERVICE_CONFIG[row.service].color }} />}
                        <Typography variant="body2">
                          {SERVICE_CONFIG[row.service]?.name || row.service}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2">
                        {row.currentPeriod?.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ color: '#6b7280' }}>
                        {row.lastPeriod?.toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                        {row.change > 0 ? (
                          <TrendingUp sx={{ fontSize: 16, color: '#10b981' }} />
                        ) : row.change < 0 ? (
                          <TrendingDown sx={{ fontSize: 16, color: '#ef4444' }} />
                        ) : null}
                        <Typography
                          variant="body2"
                          sx={{
                            color: row.change > 0 ? '#10b981' : row.change < 0 ? '#ef4444' : '#6b7280',
                            fontWeight: 600,
                          }}
                        >
                          {row.change > 0 ? '+' : ''}{row.change}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        ${row.cost?.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      <Chip
                        label={row.status}
                        size="small"
                        sx={{
                          backgroundColor: getStatusColor(row.status),
                          color: 'white',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                        }}
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}

export default UsageMetrics;
