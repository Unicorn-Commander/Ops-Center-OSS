import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  useTheme,
  alpha,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  People,
  PersonAdd,
  PersonOff,
  Refresh,
  Download,
  Warning,
  CheckCircle,
  Info,
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
import { Line, Bar, Pie } from 'react-chartjs-2';

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

const UserAnalytics = () => {
  const theme = useTheme();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  // Analytics data state
  const [overview, setOverview] = useState(null);
  const [cohorts, setCohorts] = useState([]);
  const [engagement, setEngagement] = useState(null);
  const [churnPredictions, setChurnPredictions] = useState([]);
  const [segments, setSegments] = useState(null);
  const [growthData, setGrowthData] = useState([]);
  const [behaviorPatterns, setBehaviorPatterns] = useState(null);

  // UI state
  const [selectedCohort, setSelectedCohort] = useState('all');
  const [riskFilter, setRiskFilter] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Fetch all analytics data
  const fetchAnalytics = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      // Fetch all endpoints in parallel
      const [
        overviewRes,
        cohortsRes,
        engagementRes,
        churnRes,
        segmentsRes,
        growthRes,
        behaviorRes,
      ] = await Promise.all([
        fetch('/api/v1/analytics/users/overview'),
        fetch('/api/v1/analytics/users/cohorts?months=6'),
        fetch('/api/v1/analytics/users/engagement'),
        fetch('/api/v1/analytics/users/churn/prediction?limit=50'),
        fetch('/api/v1/analytics/users/segments'),
        fetch('/api/v1/analytics/users/growth?months=6'),
        fetch('/api/v1/analytics/users/behavior/patterns'),
      ]);

      // Check for errors
      if (!overviewRes.ok) throw new Error('Failed to fetch overview');
      if (!cohortsRes.ok) throw new Error('Failed to fetch cohorts');
      if (!engagementRes.ok) throw new Error('Failed to fetch engagement');
      if (!churnRes.ok) throw new Error('Failed to fetch churn predictions');
      if (!segmentsRes.ok) throw new Error('Failed to fetch segments');
      if (!growthRes.ok) throw new Error('Failed to fetch growth data');
      if (!behaviorRes.ok) throw new Error('Failed to fetch behavior patterns');

      // Parse responses
      const overviewData = await overviewRes.json();
      const cohortsData = await cohortsRes.json();
      const engagementData = await engagementRes.json();
      const churnData = await churnRes.json();
      const segmentsData = await segmentsRes.json();
      const growthDataRes = await growthRes.json();
      const behaviorData = await behaviorRes.json();

      // Update state
      setOverview(overviewData);
      setCohorts(cohortsData);
      setEngagement(engagementData);
      setChurnPredictions(churnData);
      setSegments(segmentsData);
      setGrowthData(growthDataRes);
      setBehaviorPatterns(behaviorData);
    } catch (err) {
      console.error('Analytics fetch error:', err);
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Initial load
  useEffect(() => {
    fetchAnalytics();
  }, []);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAnalytics(true);
    }, 60000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  // Export churn predictions to CSV
  const exportChurnPredictions = () => {
    const csv = [
      ['User ID', 'Username', 'Churn Probability (%)', 'Risk Level', 'Days Since Signup', 'Last Login Days Ago'],
      ...churnPredictions.map(p => [
        p.user_id,
        p.username,
        p.churn_probability,
        p.risk_level,
        p.days_since_signup,
        p.last_login_days_ago,
      ]),
    ]
      .map(row => row.join(','))
      .join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `churn_predictions_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  // Filter churn predictions by risk level
  const filteredPredictions = riskFilter === 'all'
    ? churnPredictions
    : churnPredictions.filter(p => p.risk_level === riskFilter);

  // Render metric card
  const MetricCard = ({ title, value, subtitle, icon: Icon, color, trend }) => (
    <Card
      sx={{
        background: `linear-gradient(135deg, ${alpha(color, 0.1)} 0%, ${alpha(color, 0.05)} 100%)`,
        backdropFilter: 'blur(10px)',
        border: `1px solid ${alpha(color, 0.2)}`,
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
          <Icon sx={{ color, fontSize: 40 }} />
          {trend !== undefined && (
            <Box display="flex" alignItems="center">
              {trend >= 0 ? (
                <TrendingUp sx={{ color: theme.palette.success.main, mr: 0.5 }} />
              ) : (
                <TrendingDown sx={{ color: theme.palette.error.main, mr: 0.5 }} />
              )}
              <Typography variant="body2" color={trend >= 0 ? 'success.main' : 'error.main'}>
                {Math.abs(trend).toFixed(1)}%
              </Typography>
            </Box>
          )}
        </Box>
        <Typography variant="h3" fontWeight="bold" color={color}>
          {value.toLocaleString()}
        </Typography>
        <Typography variant="body2" color="text.secondary" mt={1}>
          {title}
        </Typography>
        {subtitle && (
          <Typography variant="caption" color="text.secondary">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  );

  // Cohort retention heatmap
  const CohortHeatmap = () => {
    if (!cohorts.length) return null;

    // Get max months
    const maxMonths = Math.max(...cohorts.map(c => Object.keys(c.retention).length));

    // Generate color based on retention rate
    const getColor = (rate) => {
      if (rate >= 80) return theme.palette.success.main;
      if (rate >= 60) return theme.palette.warning.main;
      if (rate >= 40) return theme.palette.warning.light;
      if (rate >= 20) return theme.palette.error.light;
      return theme.palette.error.main;
    };

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Cohort Retention Matrix
          </Typography>
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Cohort</TableCell>
                  <TableCell align="right">Signups</TableCell>
                  {[...Array(maxMonths)].map((_, i) => (
                    <TableCell key={i} align="center">
                      M{i}
                    </TableCell>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {cohorts.map((cohort) => (
                  <TableRow key={cohort.month}>
                    <TableCell>{cohort.month}</TableCell>
                    <TableCell align="right">{cohort.signup_count}</TableCell>
                    {Object.entries(cohort.retention).map(([month, rate]) => (
                      <TableCell
                        key={month}
                        align="center"
                        sx={{
                          bgcolor: alpha(getColor(rate), 0.3),
                          fontWeight: 'bold',
                        }}
                      >
                        {rate.toFixed(0)}%
                      </TableCell>
                    ))}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Box>
        </CardContent>
      </Card>
    );
  };

  // Engagement trend chart
  const EngagementChart = () => {
    if (!engagement) return null;

    const data = {
      labels: ['DAU', 'WAU', 'MAU'],
      datasets: [
        {
          label: 'Active Users',
          data: [engagement.dau, engagement.wau, engagement.mau],
          backgroundColor: [
            alpha(theme.palette.primary.main, 0.6),
            alpha(theme.palette.secondary.main, 0.6),
            alpha(theme.palette.info.main, 0.6),
          ],
          borderColor: [
            theme.palette.primary.main,
            theme.palette.secondary.main,
            theme.palette.info.main,
          ],
          borderWidth: 2,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,
        },
        title: {
          display: true,
          text: 'Engagement Metrics',
        },
      },
    };

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            User Engagement (DAU/WAU/MAU)
          </Typography>
          <Box sx={{ height: 300 }}>
            <Bar data={data} options={options} />
          </Box>
          <Box mt={2}>
            <Typography variant="body2" color="text.secondary">
              DAU/MAU Ratio (Stickiness): <strong>{(engagement.dau_mau_ratio * 100).toFixed(1)}%</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Avg Session Duration: <strong>{engagement.avg_session_duration.toFixed(1)} min</strong>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  // User segments pie chart
  const SegmentsChart = () => {
    if (!segments) return null;

    const data = {
      labels: ['Power Users', 'Active Users', 'At Risk', 'Inactive'],
      datasets: [
        {
          data: [
            segments.power_users,
            segments.active_users,
            segments.at_risk,
            segments.inactive,
          ],
          backgroundColor: [
            alpha(theme.palette.success.main, 0.7),
            alpha(theme.palette.primary.main, 0.7),
            alpha(theme.palette.warning.main, 0.7),
            alpha(theme.palette.error.main, 0.7),
          ],
          borderColor: [
            theme.palette.success.main,
            theme.palette.primary.main,
            theme.palette.warning.main,
            theme.palette.error.main,
          ],
          borderWidth: 2,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
        },
        title: {
          display: true,
          text: 'User Segmentation',
        },
      },
    };

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            User Segments Distribution
          </Typography>
          <Box sx={{ height: 300 }}>
            <Pie data={data} options={options} />
          </Box>
        </CardContent>
      </Card>
    );
  };

  // Growth metrics chart
  const GrowthChart = () => {
    if (!growthData.length) return null;

    const data = {
      labels: growthData.map(d => d.month).reverse(),
      datasets: [
        {
          label: 'Signups',
          data: growthData.map(d => d.signups).reverse(),
          borderColor: theme.palette.success.main,
          backgroundColor: alpha(theme.palette.success.main, 0.1),
          fill: true,
        },
        {
          label: 'Churned',
          data: growthData.map(d => d.churned).reverse(),
          borderColor: theme.palette.error.main,
          backgroundColor: alpha(theme.palette.error.main, 0.1),
          fill: true,
        },
      ],
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
        },
        title: {
          display: true,
          text: 'User Growth Trends',
        },
      },
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    };

    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Signups vs Churn
          </Typography>
          <Box sx={{ height: 300 }}>
            <Line data={data} options={options} />
          </Box>
        </CardContent>
      </Card>
    );
  };

  // Churn predictions table
  const ChurnPredictionsTable = () => {
    const getRiskChip = (level) => {
      const colors = {
        high: 'error',
        medium: 'warning',
        low: 'success',
      };

      const icons = {
        high: <Warning />,
        medium: <Info />,
        low: <CheckCircle />,
      };

      return (
        <Chip
          label={level.toUpperCase()}
          color={colors[level]}
          size="small"
          icon={icons[level]}
        />
      );
    };

    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
            <Typography variant="h6">
              Churn Predictions
            </Typography>
            <Box display="flex" gap={1}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Risk Level</InputLabel>
                <Select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  label="Risk Level"
                >
                  <MenuItem value="all">All</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
              <Button
                startIcon={<Download />}
                onClick={exportChurnPredictions}
                variant="outlined"
                size="small"
              >
                Export CSV
              </Button>
            </Box>
          </Box>

          <TableContainer sx={{ maxHeight: 400 }}>
            <Table stickyHeader size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Username</TableCell>
                  <TableCell align="right">Churn Probability</TableCell>
                  <TableCell align="center">Risk Level</TableCell>
                  <TableCell align="right">Days Since Signup</TableCell>
                  <TableCell align="right">Last Login</TableCell>
                  <TableCell align="right">Login Count</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredPredictions.map((prediction) => (
                  <TableRow key={prediction.user_id} hover>
                    <TableCell>{prediction.username}</TableCell>
                    <TableCell align="right">
                      <Typography
                        fontWeight="bold"
                        color={
                          prediction.churn_probability >= 70
                            ? 'error.main'
                            : prediction.churn_probability >= 40
                            ? 'warning.main'
                            : 'success.main'
                        }
                      >
                        {prediction.churn_probability.toFixed(1)}%
                      </Typography>
                    </TableCell>
                    <TableCell align="center">
                      {getRiskChip(prediction.risk_level)}
                    </TableCell>
                    <TableCell align="right">{prediction.days_since_signup}</TableCell>
                    <TableCell align="right">{prediction.last_login_days_ago} days ago</TableCell>
                    <TableCell align="right">{prediction.login_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error" action={
          <Button color="inherit" size="small" onClick={() => fetchAnalytics()}>
            Retry
          </Button>
        }>
          {error}
        </Alert>
      </Box>
    );
  }

  return (
    <Box p={3}>
      {/* Header */}
      <Box display="flex" alignItems="center" justifyContent="space-between" mb={3}>
        <Typography variant="h4" fontWeight="bold">
          User Analytics
        </Typography>
        <Box display="flex" gap={1}>
          <Button
            startIcon={refreshing ? <CircularProgress size={16} /> : <Refresh />}
            onClick={() => fetchAnalytics(true)}
            disabled={refreshing}
            variant="outlined"
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Overview Cards */}
      {overview && (
        <Grid container spacing={2} mb={3}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Users"
              value={overview.total_users}
              icon={People}
              color={theme.palette.primary.main}
              trend={overview.growth_rate}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Active Users (30d)"
              value={overview.active_users}
              subtitle={`${((overview.active_users / overview.total_users) * 100).toFixed(1)}% of total`}
              icon={People}
              color={theme.palette.success.main}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="New Users (30d)"
              value={overview.new_users_30d}
              icon={PersonAdd}
              color={theme.palette.info.main}
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Churned Users (30d)"
              value={overview.churned_users_30d}
              icon={PersonOff}
              color={theme.palette.error.main}
            />
          </Grid>
        </Grid>
      )}

      {/* Charts Row 1 */}
      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={6}>
          <EngagementChart />
        </Grid>
        <Grid item xs={12} md={6}>
          <SegmentsChart />
        </Grid>
      </Grid>

      {/* Growth Chart */}
      <Box mb={3}>
        <GrowthChart />
      </Box>

      {/* Cohort Heatmap */}
      <Box mb={3}>
        <CohortHeatmap />
      </Box>

      {/* Churn Predictions Table */}
      <ChurnPredictionsTable />
    </Box>
  );
};

export default UserAnalytics;
