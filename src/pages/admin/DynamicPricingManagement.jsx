/**
 * Dynamic Pricing Management Page
 * Admin interface for managing BYOK pricing, platform pricing, credit packages, and analytics
 * Epic: Dynamic Pricing System GUI
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Alert,
  Tooltip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Divider,
  Slider,
  Stack,
  Drawer,
  List,
  ListItem,
  ListItemText,
  InputAdornment
} from '@mui/material';
import {
  Edit as EditIcon,
  Delete as DeleteIcon,
  Add as AddIcon,
  Calculate as CalculateIcon,
  TrendingUp as TrendingUpIcon,
  AttachMoney as MoneyIcon,
  LocalOffer as PromoIcon,
  Refresh as RefreshIcon,
  Close as CloseIcon,
  Check as CheckIcon,
  Info as InfoIcon,
  Warning as WarningIcon
} from '@mui/icons-material';
import PageHeader from '../../components/admin/PageHeader';

const DynamicPricingManagement = () => {
  // ============================================
  // State Management
  // ============================================
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // BYOK Rules State
  const [byokRules, setByokRules] = useState([]);
  const [selectedByokRule, setSelectedByokRule] = useState(null);
  const [byokDialogOpen, setByokDialogOpen] = useState(false);
  const [byokFormData, setByokFormData] = useState({
    markup_value: 0.05,
    free_credits_monthly: 0,
    is_active: true,
    description: ''
  });

  // Platform Rules State
  const [platformRules, setPlatformRules] = useState([]);
  const [selectedPlatformRule, setSelectedPlatformRule] = useState(null);
  const [platformDialogOpen, setPlatformDialogOpen] = useState(false);
  const [platformFormData, setPlatformFormData] = useState({
    markup_value: 0.40,
    is_active: true,
    description: ''
  });

  // Credit Packages State
  const [creditPackages, setCreditPackages] = useState([]);
  const [selectedPackage, setSelectedPackage] = useState(null);
  const [packageDialogOpen, setPackageDialogOpen] = useState(false);
  const [promoDialogOpen, setPromoDialogOpen] = useState(false);
  const [packageFormData, setPackageFormData] = useState({
    package_code: '',
    package_name: '',
    description: '',
    credits: 1000,
    price_usd: 10,
    discount_percentage: 0,
    is_featured: false,
    badge_text: ''
  });
  const [promoFormData, setPromoFormData] = useState({
    promo_price: 0,
    promo_code: '',
    promo_start_date: '',
    promo_end_date: ''
  });

  // Analytics State
  const [analyticsData, setAnalyticsData] = useState(null);

  // Cost Calculator State (Drawer)
  const [calculatorOpen, setCalculatorOpen] = useState(false);
  const [calculatorData, setCalculatorData] = useState({
    provider: 'openai',
    model: 'gpt-4',
    tokens: 1000,
    tier: 'professional',
    use_byok: false
  });
  const [calculatorResult, setCalculatorResult] = useState(null);

  // ============================================
  // API Functions
  // ============================================

  const fetchByokRules = async () => {
    try {
      const response = await fetch('/api/v1/pricing/rules/byok?include_inactive=true', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch BYOK rules');
      const data = await response.json();
      setByokRules(data.rules || []);
    } catch (err) {
      setError(`BYOK Rules: ${err.message}`);
      console.error('Error fetching BYOK rules:', err);
    }
  };

  const fetchPlatformRules = async () => {
    try {
      const response = await fetch('/api/v1/pricing/rules/platform?include_inactive=true', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch Platform rules');
      const data = await response.json();
      setPlatformRules(data.rules || []);
    } catch (err) {
      setError(`Platform Rules: ${err.message}`);
      console.error('Error fetching Platform rules:', err);
    }
  };

  const fetchCreditPackages = async () => {
    try {
      const response = await fetch('/api/v1/pricing/packages?include_inactive=true', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch credit packages');
      const data = await response.json();
      setCreditPackages(data.packages || []);
    } catch (err) {
      setError(`Credit Packages: ${err.message}`);
      console.error('Error fetching credit packages:', err);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('/api/v1/pricing/dashboard/overview', {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalyticsData(data);
    } catch (err) {
      setError(`Analytics: ${err.message}`);
      console.error('Error fetching analytics:', err);
    }
  };

  const updateByokRule = async (ruleId, updates) => {
    try {
      const response = await fetch(`/api/v1/pricing/rules/byok/${ruleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates)
      });
      if (!response.ok) throw new Error('Failed to update BYOK rule');
      setSuccess('BYOK rule updated successfully');
      await fetchByokRules();
      setByokDialogOpen(false);
    } catch (err) {
      setError(`Update Failed: ${err.message}`);
      console.error('Error updating BYOK rule:', err);
    }
  };

  const updatePlatformRule = async (tierCode, updates) => {
    try {
      const response = await fetch(`/api/v1/pricing/rules/platform/${tierCode}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates)
      });
      if (!response.ok) throw new Error('Failed to update Platform rule');
      setSuccess('Platform pricing updated successfully');
      await fetchPlatformRules();
      setPlatformDialogOpen(false);
    } catch (err) {
      setError(`Update Failed: ${err.message}`);
      console.error('Error updating Platform rule:', err);
    }
  };

  const createCreditPackage = async (packageData) => {
    try {
      const response = await fetch('/api/v1/pricing/packages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(packageData)
      });
      if (!response.ok) throw new Error('Failed to create credit package');
      setSuccess('Credit package created successfully');
      await fetchCreditPackages();
      setPackageDialogOpen(false);
    } catch (err) {
      setError(`Creation Failed: ${err.message}`);
      console.error('Error creating credit package:', err);
    }
  };

  const updateCreditPackage = async (packageId, updates) => {
    try {
      const response = await fetch(`/api/v1/pricing/packages/${packageId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(updates)
      });
      if (!response.ok) throw new Error('Failed to update credit package');
      setSuccess('Credit package updated successfully');
      await fetchCreditPackages();
      setPackageDialogOpen(false);
    } catch (err) {
      setError(`Update Failed: ${err.message}`);
      console.error('Error updating credit package:', err);
    }
  };

  const addPromotion = async (packageId, promoData) => {
    try {
      const response = await fetch(`/api/v1/pricing/packages/${packageId}/promo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(promoData)
      });
      if (!response.ok) throw new Error('Failed to add promotion');
      setSuccess('Promotion added successfully');
      await fetchCreditPackages();
      setPromoDialogOpen(false);
    } catch (err) {
      setError(`Promotion Failed: ${err.message}`);
      console.error('Error adding promotion:', err);
    }
  };

  const calculateCost = async () => {
    try {
      const response = await fetch('/api/v1/pricing/calculate/comparison', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          provider: calculatorData.provider,
          model: calculatorData.model,
          tokens_used: calculatorData.tokens,
          user_tier: calculatorData.tier
        })
      });
      if (!response.ok) throw new Error('Failed to calculate cost');
      const data = await response.json();
      setCalculatorResult(data);
    } catch (err) {
      setError(`Calculation Failed: ${err.message}`);
      console.error('Error calculating cost:', err);
    }
  };

  // ============================================
  // Effects
  // ============================================

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        await Promise.all([
          fetchByokRules(),
          fetchPlatformRules(),
          fetchCreditPackages(),
          fetchAnalytics()
        ]);
      } catch (err) {
        setError('Failed to load pricing data');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  // Auto-dismiss alerts
  useEffect(() => {
    if (success) {
      const timer = setTimeout(() => setSuccess(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [success]);

  useEffect(() => {
    if (error) {
      const timer = setTimeout(() => setError(null), 8000);
      return () => clearTimeout(timer);
    }
  }, [error]);

  // ============================================
  // Helper Functions
  // ============================================

  const formatMarkup = (value, type = 'percentage') => {
    if (type === 'percentage') {
      return `${(parseFloat(value) * 100).toFixed(0)}%`;
    }
    return `$${parseFloat(value).toFixed(2)}`;
  };

  const formatCredits = (value) => {
    return `$${parseFloat(value).toFixed(2)}`;
  };

  const getStatusChip = (isActive) => {
    return (
      <Chip
        label={isActive ? 'Active' : 'Inactive'}
        color={isActive ? 'success' : 'default'}
        size="small"
      />
    );
  };

  const getTierColor = (tierCode) => {
    const colors = {
      trial: 'info',
      starter: 'primary',
      professional: 'secondary',
      enterprise: 'error'
    };
    return colors[tierCode] || 'default';
  };

  const calculateExampleCost = (basePrice, markupValue, markupType = 'percentage') => {
    if (markupType === 'percentage') {
      return basePrice * (1 + parseFloat(markupValue));
    }
    return basePrice + parseFloat(markupValue);
  };

  // ============================================
  // Event Handlers
  // ============================================

  const handleEditByokRule = (rule) => {
    setSelectedByokRule(rule);
    setByokFormData({
      markup_value: parseFloat(rule.markup_value),
      free_credits_monthly: parseFloat(rule.free_credits_monthly || 0),
      is_active: rule.is_active,
      description: rule.description || ''
    });
    setByokDialogOpen(true);
  };

  const handleEditPlatformRule = (rule) => {
    setSelectedPlatformRule(rule);
    setPlatformFormData({
      markup_value: parseFloat(rule.markup_value),
      is_active: rule.is_active,
      description: rule.description || ''
    });
    setPlatformDialogOpen(true);
  };

  const handleEditPackage = (pkg) => {
    setSelectedPackage(pkg);
    setPackageFormData({
      package_name: pkg.package_name,
      description: pkg.description || '',
      price_usd: parseFloat(pkg.price_usd),
      discount_percentage: pkg.discount_percentage || 0,
      is_featured: pkg.is_featured || false,
      badge_text: pkg.badge_text || ''
    });
    setPackageDialogOpen(true);
  };

  const handleAddPromotion = (pkg) => {
    setSelectedPackage(pkg);
    setPromoFormData({
      promo_price: parseFloat(pkg.price_usd) * 0.8, // 20% off default
      promo_code: '',
      promo_start_date: new Date().toISOString().split('T')[0],
      promo_end_date: ''
    });
    setPromoDialogOpen(true);
  };

  const handleSaveByokRule = () => {
    if (!selectedByokRule) return;
    updateByokRule(selectedByokRule.id, byokFormData);
  };

  const handleSavePlatformRule = () => {
    if (!selectedPlatformRule) return;
    updatePlatformRule(selectedPlatformRule.tier_code, platformFormData);
  };

  const handleSavePackage = () => {
    if (selectedPackage) {
      updateCreditPackage(selectedPackage.id, packageFormData);
    } else {
      createCreditPackage(packageFormData);
    }
  };

  const handleSavePromotion = () => {
    if (!selectedPackage) return;
    addPromotion(selectedPackage.id, promoFormData);
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      switch (tabValue) {
        case 0:
          await fetchByokRules();
          break;
        case 1:
          await fetchPlatformRules();
          break;
        case 2:
          await fetchCreditPackages();
          break;
        case 3:
          await fetchAnalytics();
          break;
        default:
          break;
      }
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // Render Functions
  // ============================================

  const renderByokTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">BYOK Pricing Rules</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>BYOK (Bring Your Own Key)</strong> pricing allows users to use their own API keys
          with a small markup for platform services. Configure provider-specific markups and free monthly credits.
        </Typography>
      </Alert>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><strong>Provider</strong></TableCell>
              <TableCell><strong>Markup</strong></TableCell>
              <TableCell><strong>Free Credits/Month</strong></TableCell>
              <TableCell><strong>Applies To Tiers</strong></TableCell>
              <TableCell><strong>Status</strong></TableCell>
              <TableCell align="right"><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {byokRules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="textSecondary">No BYOK rules found</Typography>
                </TableCell>
              </TableRow>
            ) : (
              byokRules.map((rule) => (
                <TableRow key={rule.id}>
                  <TableCell>
                    <Chip
                      label={rule.provider === '*' ? 'Global Default' : rule.provider}
                      color={rule.provider === '*' ? 'default' : 'primary'}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatMarkup(rule.markup_value, rule.markup_type)}</TableCell>
                  <TableCell>{formatCredits(rule.free_credits_monthly || 0)}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={0.5} flexWrap="wrap">
                      {(rule.applies_to_tiers || []).map((tier) => (
                        <Chip
                          key={tier}
                          label={tier}
                          color={getTierColor(tier)}
                          size="small"
                          sx={{ mb: 0.5 }}
                        />
                      ))}
                    </Stack>
                  </TableCell>
                  <TableCell>{getStatusChip(rule.is_active)}</TableCell>
                  <TableCell align="right">
                    <Tooltip title="Edit">
                      <IconButton
                        size="small"
                        onClick={() => handleEditByokRule(rule)}
                        color="primary"
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );

  const renderPlatformTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Platform Pricing Tiers</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Refresh
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="body2">
          <strong>Platform Pricing</strong> applies to users who don't provide their own API keys.
          Higher tiers get better pricing. Markups are applied to base model costs.
        </Typography>
      </Alert>

      <Grid container spacing={3} mb={3}>
        {platformRules.map((rule) => (
          <Grid item xs={12} sm={6} md={3} key={rule.id}>
            <Card>
              <CardContent>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Chip label={rule.tier_code} color={getTierColor(rule.tier_code)} />
                  {getStatusChip(rule.is_active)}
                </Box>
                <Typography variant="h4" color="primary" gutterBottom>
                  {formatMarkup(rule.markup_value)}
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Markup on base costs
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Typography variant="caption" color="textSecondary">
                  Example: $0.01 base → ${calculateExampleCost(0.01, rule.markup_value).toFixed(4)}
                </Typography>
                <Box mt={2}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<EditIcon />}
                    onClick={() => handleEditPlatformRule(rule)}
                    fullWidth
                  >
                    Edit
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          BYOK vs Platform Cost Comparison
        </Typography>
        <Typography variant="body2" color="textSecondary" mb={2}>
          Example costs for popular models (per 1K tokens)
        </Typography>
        <TableContainer>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell><strong>Model</strong></TableCell>
                <TableCell><strong>Base Cost</strong></TableCell>
                <TableCell><strong>BYOK (5%)</strong></TableCell>
                <TableCell><strong>Starter (40%)</strong></TableCell>
                <TableCell><strong>Pro (60%)</strong></TableCell>
                <TableCell><strong>Enterprise (80%)</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              <TableRow>
                <TableCell>GPT-4</TableCell>
                <TableCell>$0.03</TableCell>
                <TableCell>$0.0315</TableCell>
                <TableCell>$0.042</TableCell>
                <TableCell>$0.048</TableCell>
                <TableCell>$0.054</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>Claude 3.5 Sonnet</TableCell>
                <TableCell>$0.015</TableCell>
                <TableCell>$0.01575</TableCell>
                <TableCell>$0.021</TableCell>
                <TableCell>$0.024</TableCell>
                <TableCell>$0.027</TableCell>
              </TableRow>
              <TableRow>
                <TableCell>GPT-3.5 Turbo</TableCell>
                <TableCell>$0.002</TableCell>
                <TableCell>$0.0021</TableCell>
                <TableCell>$0.0028</TableCell>
                <TableCell>$0.0032</TableCell>
                <TableCell>$0.0036</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );

  const renderCreditPackagesTab = () => (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Credit Packages</Typography>
        <Stack direction="row" spacing={2}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setSelectedPackage(null);
              setPackageFormData({
                package_code: '',
                package_name: '',
                description: '',
                credits: 1000,
                price_usd: 10,
                discount_percentage: 0,
                is_featured: false,
                badge_text: ''
              });
              setPackageDialogOpen(true);
            }}
          >
            New Package
          </Button>
        </Stack>
      </Box>

      <Grid container spacing={3}>
        {creditPackages.map((pkg) => (
          <Grid item xs={12} sm={6} md={3} key={pkg.id}>
            <Card sx={{ height: '100%', position: 'relative' }}>
              {pkg.is_featured && (
                <Chip
                  label="Featured"
                  color="secondary"
                  size="small"
                  sx={{ position: 'absolute', top: 8, right: 8 }}
                />
              )}
              {pkg.badge_text && (
                <Chip
                  label={pkg.badge_text}
                  color="warning"
                  size="small"
                  sx={{ position: 'absolute', top: 8, left: 8 }}
                />
              )}
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {pkg.package_name}
                </Typography>
                <Typography variant="h3" color="primary" gutterBottom>
                  {pkg.credits.toLocaleString()}
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  credits
                </Typography>
                <Divider sx={{ my: 2 }} />
                <Box display="flex" alignItems="baseline" mb={1}>
                  <Typography variant="h5" color="primary">
                    ${parseFloat(pkg.price_usd).toFixed(2)}
                  </Typography>
                  {pkg.discount_percentage > 0 && (
                    <Chip
                      label={`-${pkg.discount_percentage}%`}
                      color="success"
                      size="small"
                      sx={{ ml: 1 }}
                    />
                  )}
                </Box>
                {pkg.promo_active && (
                  <Alert severity="success" sx={{ mb: 2 }}>
                    <Typography variant="caption">
                      Promo: ${parseFloat(pkg.promo_price).toFixed(2)}
                      <br />
                      Code: {pkg.promo_code}
                    </Typography>
                  </Alert>
                )}
                <Typography variant="caption" color="textSecondary" paragraph>
                  ${(parseFloat(pkg.price_usd) / pkg.credits * 1000).toFixed(2)} per 1000 credits
                </Typography>
                {pkg.description && (
                  <Typography variant="body2" color="textSecondary" paragraph>
                    {pkg.description}
                  </Typography>
                )}
                <Stack spacing={1}>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<EditIcon />}
                    onClick={() => handleEditPackage(pkg)}
                    fullWidth
                  >
                    Edit
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="secondary"
                    startIcon={<PromoIcon />}
                    onClick={() => handleAddPromotion(pkg)}
                    fullWidth
                  >
                    Add Promo
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );

  const renderAnalyticsTab = () => {
    if (!analyticsData) {
      return (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
          <CircularProgress />
        </Box>
      );
    }

    return (
      <Box>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
          <Typography variant="h6">Pricing Analytics</Typography>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            Refresh
          </Button>
        </Box>

        <Grid container spacing={3}>
          {/* Revenue Metrics */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <MoneyIcon color="primary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Total Revenue</Typography>
                </Box>
                <Typography variant="h3" color="primary">
                  ${parseFloat(analyticsData.revenue?.total || 0).toFixed(2)}
                </Typography>
                <Typography variant="body2" color="textSecondary" mt={1}>
                  BYOK: ${parseFloat(analyticsData.revenue?.byok || 0).toFixed(2)}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Platform: ${parseFloat(analyticsData.revenue?.platform || 0).toFixed(2)}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Active Users */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <TrendingUpIcon color="secondary" sx={{ mr: 1 }} />
                  <Typography variant="h6">Active Users</Typography>
                </Box>
                <Typography variant="h3" color="secondary">
                  {analyticsData.users?.total || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary" mt={1}>
                  BYOK: {analyticsData.users?.byok || 0}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Platform: {analyticsData.users?.platform || 0}
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Average Savings */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <InfoIcon color="success" sx={{ mr: 1 }} />
                  <Typography variant="h6">BYOK Savings</Typography>
                </Box>
                <Typography variant="h3" color="success.main">
                  {analyticsData.savings?.average_percentage || 0}%
                </Typography>
                <Typography variant="body2" color="textSecondary" mt={1}>
                  Average cost reduction with BYOK
                </Typography>
              </CardContent>
            </Card>
          </Grid>

          {/* Most Popular Models */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Most Popular Models
              </Typography>
              <List>
                {(analyticsData.popular_models || []).slice(0, 5).map((model, index) => (
                  <ListItem key={index} divider={index < 4}>
                    <ListItemText
                      primary={model.model_name}
                      secondary={`${model.usage_count} requests`}
                    />
                    <Chip
                      label={`$${parseFloat(model.total_cost || 0).toFixed(2)}`}
                      color="primary"
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>

          {/* Cost Savings by Tier */}
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                Cost Savings by Tier
              </Typography>
              <List>
                {Object.entries(analyticsData.savings_by_tier || {}).map(([tier, savings], index) => (
                  <ListItem key={tier} divider={index < Object.keys(analyticsData.savings_by_tier || {}).length - 1}>
                    <ListItemText
                      primary={tier.charAt(0).toUpperCase() + tier.slice(1)}
                      secondary={`${savings.user_count} users`}
                    />
                    <Stack direction="row" spacing={1} alignItems="center">
                      <Chip
                        label={`${savings.percentage}%`}
                        color="success"
                        size="small"
                      />
                      <Typography variant="body2" color="textSecondary">
                        ${parseFloat(savings.total_saved || 0).toFixed(2)}
                      </Typography>
                    </Stack>
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Grid>
        </Grid>
      </Box>
    );
  };

  const renderCostCalculator = () => (
    <Drawer
      anchor="right"
      open={calculatorOpen}
      onClose={() => setCalculatorOpen(false)}
      PaperProps={{ sx: { width: 400, p: 3 } }}
    >
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">Cost Calculator</Typography>
        <IconButton onClick={() => setCalculatorOpen(false)} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      <Stack spacing={3}>
        <FormControl fullWidth>
          <InputLabel>Provider</InputLabel>
          <Select
            value={calculatorData.provider}
            label="Provider"
            onChange={(e) => setCalculatorData({ ...calculatorData, provider: e.target.value })}
          >
            <MenuItem value="openai">OpenAI</MenuItem>
            <MenuItem value="anthropic">Anthropic</MenuItem>
            <MenuItem value="google">Google</MenuItem>
            <MenuItem value="openrouter">OpenRouter</MenuItem>
          </Select>
        </FormControl>

        <TextField
          fullWidth
          label="Model"
          value={calculatorData.model}
          onChange={(e) => setCalculatorData({ ...calculatorData, model: e.target.value })}
          helperText="e.g., gpt-4, claude-3-sonnet"
        />

        <TextField
          fullWidth
          type="number"
          label="Token Count"
          value={calculatorData.tokens}
          onChange={(e) => setCalculatorData({ ...calculatorData, tokens: parseInt(e.target.value) || 0 })}
          InputProps={{
            endAdornment: <InputAdornment position="end">tokens</InputAdornment>
          }}
        />

        <FormControl fullWidth>
          <InputLabel>User Tier</InputLabel>
          <Select
            value={calculatorData.tier}
            label="User Tier"
            onChange={(e) => setCalculatorData({ ...calculatorData, tier: e.target.value })}
          >
            <MenuItem value="trial">Trial</MenuItem>
            <MenuItem value="starter">Starter</MenuItem>
            <MenuItem value="professional">Professional</MenuItem>
            <MenuItem value="enterprise">Enterprise</MenuItem>
          </Select>
        </FormControl>

        <FormControlLabel
          control={
            <Switch
              checked={calculatorData.use_byok}
              onChange={(e) => setCalculatorData({ ...calculatorData, use_byok: e.target.checked })}
            />
          }
          label="User has BYOK"
        />

        <Button
          variant="contained"
          startIcon={<CalculateIcon />}
          onClick={calculateCost}
          fullWidth
        >
          Calculate
        </Button>

        {calculatorResult && (
          <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
            <Typography variant="subtitle2" gutterBottom>
              Cost Comparison
            </Typography>
            <Divider sx={{ my: 2 }} />

            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">
                BYOK Cost
              </Typography>
              <Typography variant="h5" color="primary">
                ${parseFloat(calculatorResult.byok_cost?.final_cost || 0).toFixed(4)}
              </Typography>
              {calculatorResult.byok_cost?.free_credits_used > 0 && (
                <Typography variant="caption" color="success.main">
                  (${parseFloat(calculatorResult.byok_cost.free_credits_used).toFixed(4)} from free credits)
                </Typography>
              )}
            </Box>

            <Box mb={2}>
              <Typography variant="body2" color="textSecondary">
                Platform Cost
              </Typography>
              <Typography variant="h5" color="secondary">
                ${parseFloat(calculatorResult.platform_cost?.final_cost || 0).toFixed(4)}
              </Typography>
            </Box>

            <Divider sx={{ my: 2 }} />

            <Alert severity={calculatorResult.savings > 0 ? 'success' : 'info'}>
              <Typography variant="body2">
                {calculatorResult.savings > 0 ? (
                  <>
                    <strong>Save ${parseFloat(calculatorResult.savings).toFixed(4)}</strong>
                    <br />
                    ({calculatorResult.savings_percentage}% cheaper with BYOK)
                  </>
                ) : (
                  'Platform pricing is competitive for this model'
                )}
              </Typography>
            </Alert>
          </Paper>
        )}
      </Stack>
    </Drawer>
  );

  // ============================================
  // BYOK Edit Dialog
  // ============================================

  const renderByokDialog = () => (
    <Dialog open={byokDialogOpen} onClose={() => setByokDialogOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        Edit BYOK Pricing Rule
        {selectedByokRule && (
          <Typography variant="subtitle2" color="textSecondary">
            {selectedByokRule.provider === '*' ? 'Global Default' : selectedByokRule.provider}
          </Typography>
        )}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          <Box>
            <Typography gutterBottom>
              Markup Percentage: {(byokFormData.markup_value * 100).toFixed(0)}%
            </Typography>
            <Slider
              value={byokFormData.markup_value * 100}
              onChange={(e, val) => setByokFormData({ ...byokFormData, markup_value: val / 100 })}
              min={0}
              max={20}
              step={0.5}
              marks={[
                { value: 0, label: '0%' },
                { value: 5, label: '5%' },
                { value: 10, label: '10%' },
                { value: 15, label: '15%' },
                { value: 20, label: '20%' }
              ]}
              valueLabelDisplay="auto"
            />
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                Example: $0.01 base cost → ${calculateExampleCost(0.01, byokFormData.markup_value).toFixed(4)}
              </Typography>
            </Alert>
          </Box>

          <TextField
            fullWidth
            type="number"
            label="Free Monthly Credits"
            value={byokFormData.free_credits_monthly}
            onChange={(e) => setByokFormData({ ...byokFormData, free_credits_monthly: parseFloat(e.target.value) || 0 })}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>
            }}
            helperText="Free credits given to users each month for this provider"
          />

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Description"
            value={byokFormData.description}
            onChange={(e) => setByokFormData({ ...byokFormData, description: e.target.value })}
          />

          <FormControlLabel
            control={
              <Switch
                checked={byokFormData.is_active}
                onChange={(e) => setByokFormData({ ...byokFormData, is_active: e.target.checked })}
              />
            }
            label="Active"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setByokDialogOpen(false)}>Cancel</Button>
        <Button onClick={handleSaveByokRule} variant="contained">
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );

  // ============================================
  // Platform Edit Dialog
  // ============================================

  const renderPlatformDialog = () => (
    <Dialog open={platformDialogOpen} onClose={() => setPlatformDialogOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        Edit Platform Pricing
        {selectedPlatformRule && (
          <Typography variant="subtitle2" color="textSecondary">
            {selectedPlatformRule.tier_code.charAt(0).toUpperCase() + selectedPlatformRule.tier_code.slice(1)} Tier
          </Typography>
        )}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          <Box>
            <Typography gutterBottom>
              Markup Percentage: {(platformFormData.markup_value * 100).toFixed(0)}%
            </Typography>
            <Slider
              value={platformFormData.markup_value * 100}
              onChange={(e, val) => setPlatformFormData({ ...platformFormData, markup_value: val / 100 })}
              min={0}
              max={100}
              step={5}
              marks={[
                { value: 0, label: '0%' },
                { value: 25, label: '25%' },
                { value: 50, label: '50%' },
                { value: 75, label: '75%' },
                { value: 100, label: '100%' }
              ]}
              valueLabelDisplay="auto"
            />
            <Alert severity="info" sx={{ mt: 2 }}>
              <Typography variant="caption">
                Example: $0.01 base cost → ${calculateExampleCost(0.01, platformFormData.markup_value).toFixed(4)}
              </Typography>
            </Alert>
          </Box>

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Description"
            value={platformFormData.description}
            onChange={(e) => setPlatformFormData({ ...platformFormData, description: e.target.value })}
          />

          <FormControlLabel
            control={
              <Switch
                checked={platformFormData.is_active}
                onChange={(e) => setPlatformFormData({ ...platformFormData, is_active: e.target.checked })}
              />
            }
            label="Active"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPlatformDialogOpen(false)}>Cancel</Button>
        <Button onClick={handleSavePlatformRule} variant="contained">
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );

  // ============================================
  // Credit Package Dialog
  // ============================================

  const renderPackageDialog = () => (
    <Dialog open={packageDialogOpen} onClose={() => setPackageDialogOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>
        {selectedPackage ? 'Edit Credit Package' : 'Create Credit Package'}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          {!selectedPackage && (
            <TextField
              fullWidth
              required
              label="Package Code"
              value={packageFormData.package_code}
              onChange={(e) => setPackageFormData({ ...packageFormData, package_code: e.target.value })}
              helperText="Unique identifier (lowercase, underscores allowed)"
            />
          )}

          <TextField
            fullWidth
            required
            label="Package Name"
            value={packageFormData.package_name}
            onChange={(e) => setPackageFormData({ ...packageFormData, package_name: e.target.value })}
          />

          <TextField
            fullWidth
            multiline
            rows={2}
            label="Description"
            value={packageFormData.description}
            onChange={(e) => setPackageFormData({ ...packageFormData, description: e.target.value })}
          />

          {!selectedPackage && (
            <TextField
              fullWidth
              required
              type="number"
              label="Credits"
              value={packageFormData.credits}
              onChange={(e) => setPackageFormData({ ...packageFormData, credits: parseInt(e.target.value) || 0 })}
            />
          )}

          <TextField
            fullWidth
            required
            type="number"
            label="Price (USD)"
            value={packageFormData.price_usd}
            onChange={(e) => setPackageFormData({ ...packageFormData, price_usd: parseFloat(e.target.value) || 0 })}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>
            }}
          />

          <TextField
            fullWidth
            type="number"
            label="Discount Percentage"
            value={packageFormData.discount_percentage}
            onChange={(e) => setPackageFormData({ ...packageFormData, discount_percentage: parseInt(e.target.value) || 0 })}
            InputProps={{
              endAdornment: <InputAdornment position="end">%</InputAdornment>
            }}
            helperText="Visual indicator only, actual discount applied in price"
          />

          <TextField
            fullWidth
            label="Badge Text"
            value={packageFormData.badge_text}
            onChange={(e) => setPackageFormData({ ...packageFormData, badge_text: e.target.value })}
            helperText="e.g., 'BEST VALUE', 'LIMITED TIME'"
          />

          <FormControlLabel
            control={
              <Switch
                checked={packageFormData.is_featured}
                onChange={(e) => setPackageFormData({ ...packageFormData, is_featured: e.target.checked })}
              />
            }
            label="Featured Package"
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPackageDialogOpen(false)}>Cancel</Button>
        <Button onClick={handleSavePackage} variant="contained">
          {selectedPackage ? 'Save Changes' : 'Create Package'}
        </Button>
      </DialogActions>
    </Dialog>
  );

  // ============================================
  // Promotion Dialog
  // ============================================

  const renderPromoDialog = () => (
    <Dialog open={promoDialogOpen} onClose={() => setPromoDialogOpen(false)} maxWidth="sm" fullWidth>
      <DialogTitle>Add Promotional Pricing</DialogTitle>
      <DialogContent>
        <Stack spacing={3} sx={{ mt: 2 }}>
          <TextField
            fullWidth
            required
            type="number"
            label="Promotional Price"
            value={promoFormData.promo_price}
            onChange={(e) => setPromoFormData({ ...promoFormData, promo_price: parseFloat(e.target.value) || 0 })}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>
            }}
          />

          <TextField
            fullWidth
            required
            label="Promo Code"
            value={promoFormData.promo_code}
            onChange={(e) => setPromoFormData({ ...promoFormData, promo_code: e.target.value })}
            helperText="Unique code for this promotion"
          />

          <TextField
            fullWidth
            required
            type="date"
            label="Start Date"
            value={promoFormData.promo_start_date}
            onChange={(e) => setPromoFormData({ ...promoFormData, promo_start_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />

          <TextField
            fullWidth
            required
            type="date"
            label="End Date"
            value={promoFormData.promo_end_date}
            onChange={(e) => setPromoFormData({ ...promoFormData, promo_end_date: e.target.value })}
            InputLabelProps={{ shrink: true }}
          />
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPromoDialogOpen(false)}>Cancel</Button>
        <Button onClick={handleSavePromotion} variant="contained">
          Add Promotion
        </Button>
      </DialogActions>
    </Dialog>
  );

  // ============================================
  // Main Render
  // ============================================

  if (loading && !byokRules.length && !platformRules.length) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={600}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <PageHeader
        title="Dynamic Pricing Management"
        subtitle="Configure BYOK markups, platform pricing tiers, and credit packages"
        actions={(
          <Button
            variant="contained"
            startIcon={<CalculateIcon />}
            onClick={() => setCalculatorOpen(true)}
          >
            Cost Calculator
          </Button>
        )}
      />

      {/* Alerts */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 3 }}>
          {success}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={tabValue}
          onChange={(e, newValue) => setTabValue(newValue)}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label="BYOK Pricing" />
          <Tab label="Platform Pricing" />
          <Tab label="Credit Packages" />
          <Tab label="Analytics" />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {tabValue === 0 && renderByokTab()}
        {tabValue === 1 && renderPlatformTab()}
        {tabValue === 2 && renderCreditPackagesTab()}
        {tabValue === 3 && renderAnalyticsTab()}
      </Box>

      {/* Dialogs and Drawers */}
      {renderByokDialog()}
      {renderPlatformDialog()}
      {renderPackageDialog()}
      {renderPromoDialog()}
      {renderCostCalculator()}
    </Box>
  );
};

export default DynamicPricingManagement;
