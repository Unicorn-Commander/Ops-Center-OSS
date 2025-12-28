/**
 * CreateUserModal Component - Enhanced Multi-Tab User Creation
 *
 * CREATED: October 15, 2025
 * PURPOSE: Comprehensive user creation with tabs for basic info, org/roles,
 *          subscription/billing, access/permissions, and metadata
 *
 * FEATURES:
 * - Tab 1: Basic Information (email, username, password with strength indicator)
 * - Tab 2: Organization & Roles (org selection, Brigade roles, Keycloak roles)
 * - Tab 3: Subscription & Billing (tier selection, payment, limits)
 * - Tab 4: Access & Permissions (service access, feature flags, rate limits)
 * - Tab 5: Metadata (tags, notes, account source)
 *
 * VALIDATION:
 * - Required field validation
 * - Email format validation
 * - Password strength validation (using zxcvbn)
 * - Password confirmation matching
 * - Tab-level validation before allowing navigation
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  FormControlLabel,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  Checkbox,
  FormGroup,
  Chip,
  Box,
  Grid,
  Tabs,
  Tab,
  Typography,
  Alert,
  LinearProgress,
  InputAdornment,
  IconButton,
  RadioGroup,
  Radio,
  FormLabel,
  CircularProgress,
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  CheckCircle,
  Cancel,
  Warning,
  Add as AddIcon,
} from '@mui/icons-material';
import zxcvbn from 'zxcvbn';

// Tab Panel Component
function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

// Password Strength Indicator Component
function PasswordStrengthIndicator({ password }) {
  if (!password) return null;

  const result = zxcvbn(password);
  const score = result.score; // 0-4
  const colors = ['error', 'error', 'warning', 'info', 'success'];
  const labels = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong'];

  return (
    <Box sx={{ mt: 1 }}>
      <LinearProgress
        variant="determinate"
        value={(score / 4) * 100}
        color={colors[score]}
        sx={{ mb: 0.5 }}
      />
      <Typography variant="caption" color={`${colors[score]}.main`}>
        Password Strength: {labels[score]}
      </Typography>
      {result.feedback.warning && (
        <Typography variant="caption" display="block" color="warning.main">
          {result.feedback.warning}
        </Typography>
      )}
    </Box>
  );
}

// Create Organization Sub-Modal Component
function CreateOrganizationModal({ open, onClose, onCreated }) {
  const [orgData, setOrgData] = useState({
    name: '',
    description: '',
    domain: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleCreate = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/org', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(orgData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create organization');
      }

      const newOrg = await response.json();
      onCreated(newOrg);
      setOrgData({ name: '', description: '', domain: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Create New Organization</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Box sx={{ pt: 2 }}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Organization Name"
                required
                value={orgData.name}
                onChange={(e) => setOrgData({ ...orgData, name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={orgData.description}
                onChange={(e) => setOrgData({ ...orgData, description: e.target.value })}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Domain (optional)"
                placeholder="example.com"
                value={orgData.domain}
                onChange={(e) => setOrgData({ ...orgData, domain: e.target.value })}
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          variant="contained"
          onClick={handleCreate}
          disabled={!orgData.name || loading}
        >
          {loading ? <CircularProgress size={24} /> : 'Create'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function CreateUserModal({ open, onClose, onUserCreated }) {
  const [currentTab, setCurrentTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [createOrgModalOpen, setCreateOrgModalOpen] = useState(false);

  // Data fetched from API
  const [organizations, setOrganizations] = useState([]);
  const [availableRoles, setAvailableRoles] = useState([]);

  // Form data state
  const [formData, setFormData] = useState({
    // Tab 1: Basic Information
    email: '',
    username: '',
    firstName: '',
    lastName: '',
    password: '',
    confirmPassword: '',
    enabled: true,
    emailVerified: false,
    sendWelcomeEmail: true,

    // Tab 2: Organization & Roles
    organizationId: '',
    brigadeRoles: [],
    keycloakRoles: [],

    // Tab 3: Subscription & Billing
    subscriptionTier: 'free',
    billingStartDate: new Date().toISOString().split('T')[0],
    paymentMethod: 'skip',
    apiCallLimitOverride: null,
    initialCredits: 0,

    // Tab 4: Access & Permissions
    serviceAccess: {
      openWebUI: true,
      centerDeep: false,
      unicornBrigade: false,
      unicornOrator: false,
      unicornAmanuensis: false,
    },
    featureFlags: {
      byokEnabled: false,
      apiAccessEnabled: false,
      webhookAccess: false,
    },
    rateLimits: {
      callsPerMinute: 60,
      callsPerDay: 1000,
    },

    // Tab 5: Metadata
    tags: [],
    internalNotes: '',
    accountSource: 'admin-created',
  });

  // Tag input state
  const [tagInput, setTagInput] = useState('');

  // Validation state
  const [validationErrors, setValidationErrors] = useState({});

  // Subscription tier configs
  const subscriptionTiers = [
    { value: 'free', label: 'Free', price: '$0/month', callsPerDay: 100 },
    { value: 'trial', label: 'Trial', price: '$1/week', callsPerDay: 700 },
    { value: 'starter', label: 'Starter', price: '$19/month', callsPerDay: 1000 },
    { value: 'professional', label: 'Professional', price: '$49/month', callsPerDay: 10000 },
    { value: 'enterprise', label: 'Enterprise', price: '$99/month', callsPerDay: -1 },
  ];

  // Brigade roles
  const brigadeRolesList = [
    'brigade-platform-admin',
    'brigade-developer',
    'brigade-agent-creator',
    'brigade-agent-user',
    'brigade-viewer',
  ];

  // Fetch organizations on mount
  useEffect(() => {
    if (open) {
      fetchOrganizations();
      fetchAvailableRoles();
    }
  }, [open]);

  // Update rate limits based on selected tier
  useEffect(() => {
    const tier = subscriptionTiers.find((t) => t.value === formData.subscriptionTier);
    if (tier && !formData.apiCallLimitOverride) {
      setFormData((prev) => ({
        ...prev,
        rateLimits: {
          ...prev.rateLimits,
          callsPerDay: tier.callsPerDay === -1 ? 999999 : tier.callsPerDay,
        },
      }));
    }
  }, [formData.subscriptionTier]);

  const fetchOrganizations = async () => {
    try {
      const response = await fetch('/api/v1/organizations', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch organizations');
      const data = await response.json();
      setOrganizations(data.organizations || []);
    } catch (err) {
      console.error('Failed to fetch organizations:', err);
    }
  };

  const fetchAvailableRoles = async () => {
    try {
      const response = await fetch('/api/v1/admin/users/roles/available', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch roles');
      const data = await response.json();
      setAvailableRoles(data.roles || []);
    } catch (err) {
      console.error('Failed to fetch roles:', err);
    }
  };

  const handleOrgCreated = (newOrg) => {
    setOrganizations([...organizations, newOrg]);
    setFormData({ ...formData, organizationId: newOrg.id });
    setCreateOrgModalOpen(false);
  };

  // Validation functions
  const validateEmail = (email) => {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  };

  const validateTab = (tabIndex) => {
    const errors = {};

    switch (tabIndex) {
      case 0: // Basic Information
        if (!formData.email) errors.email = 'Email is required';
        else if (!validateEmail(formData.email)) errors.email = 'Invalid email format';

        if (!formData.username) errors.username = 'Username is required';
        else if (formData.username.length < 3)
          errors.username = 'Username must be at least 3 characters';

        if (!formData.password) errors.password = 'Password is required';
        else if (formData.password.length < 8)
          errors.password = 'Password must be at least 8 characters';

        if (!formData.confirmPassword)
          errors.confirmPassword = 'Please confirm password';
        else if (formData.password !== formData.confirmPassword)
          errors.confirmPassword = 'Passwords do not match';

        // Check password strength
        if (formData.password && zxcvbn(formData.password).score < 2) {
          errors.password = 'Password is too weak';
        }
        break;

      case 1: // Organization & Roles
        // Optional validation - no required fields
        break;

      case 2: // Subscription & Billing
        if (formData.paymentMethod === 'stripe' && !formData.stripeCardToken) {
          errors.paymentMethod = 'Please provide payment information';
        }
        break;

      case 3: // Access & Permissions
        // Optional validation
        break;

      case 4: // Metadata
        // Optional validation
        break;

      default:
        break;
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleTabChange = (event, newValue) => {
    // Validate current tab before allowing navigation
    if (validateTab(currentTab)) {
      setCurrentTab(newValue);
    }
  };

  const handleSubmit = async () => {
    // Validate all tabs
    let allValid = true;
    for (let i = 0; i <= 4; i++) {
      if (!validateTab(i)) {
        allValid = false;
        setCurrentTab(i); // Jump to first invalid tab
        break;
      }
    }

    if (!allValid) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/admin/users/comprehensive', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create user');
      }

      const newUser = await response.json();
      onUserCreated(newUser);
      handleClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    // Reset form
    setFormData({
      email: '',
      username: '',
      firstName: '',
      lastName: '',
      password: '',
      confirmPassword: '',
      enabled: true,
      emailVerified: false,
      sendWelcomeEmail: true,
      organizationId: '',
      brigadeRoles: [],
      keycloakRoles: [],
      subscriptionTier: 'free',
      billingStartDate: new Date().toISOString().split('T')[0],
      paymentMethod: 'skip',
      apiCallLimitOverride: null,
      initialCredits: 0,
      serviceAccess: {
        openWebUI: true,
        centerDeep: false,
        unicornBrigade: false,
        unicornOrator: false,
        unicornAmanuensis: false,
      },
      featureFlags: {
        byokEnabled: false,
        apiAccessEnabled: false,
        webhookAccess: false,
      },
      rateLimits: {
        callsPerMinute: 60,
        callsPerDay: 1000,
      },
      tags: [],
      internalNotes: '',
      accountSource: 'admin-created',
    });
    setCurrentTab(0);
    setValidationErrors({});
    setError(null);
    onClose();
  };

  const handleAddTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({
        ...formData,
        tags: [...formData.tags, tagInput.trim()],
      });
      setTagInput('');
    }
  };

  const handleDeleteTag = (tagToDelete) => {
    setFormData({
      ...formData,
      tags: formData.tags.filter((tag) => tag !== tagToDelete),
    });
  };

  const isFormValid = () => {
    return (
      formData.email &&
      validateEmail(formData.email) &&
      formData.username &&
      formData.password &&
      formData.password === formData.confirmPassword &&
      zxcvbn(formData.password).score >= 2
    );
  };

  return (
    <>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle>Create New User</DialogTitle>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
              {error}
            </Alert>
          )}

          <Box sx={{ borderBottom: 1, borderColor: 'divider', mt: 2 }}>
            <Tabs value={currentTab} onChange={handleTabChange}>
              <Tab
                label="Basic Info"
                icon={
                  Object.keys(validationErrors).some((k) =>
                    ['email', 'username', 'password', 'confirmPassword'].includes(k)
                  ) ? (
                    <Cancel color="error" fontSize="small" />
                  ) : null
                }
                iconPosition="end"
              />
              <Tab label="Org & Roles" />
              <Tab label="Subscription" />
              <Tab label="Access" />
              <Tab label="Metadata" />
            </Tabs>
          </Box>

          {/* Tab 1: Basic Information */}
          <TabPanel value={currentTab} index={0}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={formData.firstName}
                  onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={formData.lastName}
                  onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="Email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  error={!!validationErrors.email}
                  helperText={validationErrors.email}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="Username"
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  error={!!validationErrors.username}
                  helperText={validationErrors.username}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="Password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  error={!!validationErrors.password}
                  helperText={validationErrors.password}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton onClick={() => setShowPassword(!showPassword)} edge="end">
                          {showPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
                <PasswordStrengthIndicator password={formData.password} />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="Confirm Password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={formData.confirmPassword}
                  onChange={(e) =>
                    setFormData({ ...formData, confirmPassword: e.target.value })
                  }
                  error={!!validationErrors.confirmPassword}
                  helperText={validationErrors.confirmPassword}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                          edge="end"
                        >
                          {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
                        </IconButton>
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.enabled}
                      onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                    />
                  }
                  label="Enabled"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.emailVerified}
                      onChange={(e) =>
                        setFormData({ ...formData, emailVerified: e.target.checked })
                      }
                    />
                  }
                  label="Email Verified"
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.sendWelcomeEmail}
                      onChange={(e) =>
                        setFormData({ ...formData, sendWelcomeEmail: e.target.checked })
                      }
                    />
                  }
                  label="Send Welcome Email"
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 2: Organization & Roles */}
          <TabPanel value={currentTab} index={1}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <FormControl fullWidth>
                    <InputLabel>Organization</InputLabel>
                    <Select
                      value={formData.organizationId}
                      label="Organization"
                      onChange={(e) =>
                        setFormData({ ...formData, organizationId: e.target.value })
                      }
                    >
                      <MenuItem value="">None</MenuItem>
                      {organizations.map((org) => (
                        <MenuItem key={org.id} value={org.id}>
                          {org.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <Button
                    variant="outlined"
                    startIcon={<AddIcon />}
                    onClick={() => setCreateOrgModalOpen(true)}
                    sx={{ minWidth: 160 }}
                  >
                    New Org
                  </Button>
                </Box>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Brigade Roles
                </Typography>
                <FormGroup>
                  {brigadeRolesList.map((role) => (
                    <FormControlLabel
                      key={role}
                      control={
                        <Checkbox
                          checked={formData.brigadeRoles.includes(role)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                brigadeRoles: [...formData.brigadeRoles, role],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                brigadeRoles: formData.brigadeRoles.filter((r) => r !== role),
                              });
                            }
                          }}
                        />
                      }
                      label={role}
                    />
                  ))}
                </FormGroup>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Keycloak Roles
                </Typography>
                <FormGroup>
                  {availableRoles.map((role) => (
                    <FormControlLabel
                      key={role}
                      control={
                        <Checkbox
                          checked={formData.keycloakRoles.includes(role)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({
                                ...formData,
                                keycloakRoles: [...formData.keycloakRoles, role],
                              });
                            } else {
                              setFormData({
                                ...formData,
                                keycloakRoles: formData.keycloakRoles.filter((r) => r !== role),
                              });
                            }
                          }}
                        />
                      }
                      label={role}
                    />
                  ))}
                </FormGroup>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 3: Subscription & Billing */}
          <TabPanel value={currentTab} index={2}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Subscription Tier</InputLabel>
                  <Select
                    value={formData.subscriptionTier}
                    label="Subscription Tier"
                    onChange={(e) =>
                      setFormData({ ...formData, subscriptionTier: e.target.value })
                    }
                  >
                    {subscriptionTiers.map((tier) => (
                      <MenuItem key={tier.value} value={tier.value}>
                        {tier.label} - {tier.price}
                        {tier.callsPerDay !== -1 && ` (${tier.callsPerDay} calls/day)`}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Billing Start Date"
                  type="date"
                  value={formData.billingStartDate}
                  onChange={(e) =>
                    setFormData({ ...formData, billingStartDate: e.target.value })
                  }
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl>
                  <FormLabel>Payment Method</FormLabel>
                  <RadioGroup
                    value={formData.paymentMethod}
                    onChange={(e) => setFormData({ ...formData, paymentMethod: e.target.value })}
                  >
                    <FormControlLabel value="skip" control={<Radio />} label="Skip for now" />
                    <FormControlLabel
                      value="stripe"
                      control={<Radio />}
                      label="Stripe card entry"
                    />
                    <FormControlLabel
                      value="invoice"
                      control={<Radio />}
                      label="Invoice billing"
                    />
                  </RadioGroup>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="API Call Limit Override"
                  type="number"
                  value={formData.apiCallLimitOverride || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      apiCallLimitOverride: e.target.value ? parseInt(e.target.value) : null,
                    })
                  }
                  helperText="Leave empty for tier default"
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Initial Credits"
                  type="number"
                  value={formData.initialCredits}
                  onChange={(e) =>
                    setFormData({ ...formData, initialCredits: parseInt(e.target.value) || 0 })
                  }
                />
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 4: Access & Permissions */}
          <TabPanel value={currentTab} index={3}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Service Access
                </Typography>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.serviceAccess.openWebUI}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            serviceAccess: {
                              ...formData.serviceAccess,
                              openWebUI: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Open-WebUI"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.serviceAccess.centerDeep}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            serviceAccess: {
                              ...formData.serviceAccess,
                              centerDeep: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Center-Deep"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.serviceAccess.unicornBrigade}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            serviceAccess: {
                              ...formData.serviceAccess,
                              unicornBrigade: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Unicorn Brigade"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.serviceAccess.unicornOrator}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            serviceAccess: {
                              ...formData.serviceAccess,
                              unicornOrator: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Unicorn Orator (TTS)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.serviceAccess.unicornAmanuensis}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            serviceAccess: {
                              ...formData.serviceAccess,
                              unicornAmanuensis: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Unicorn Amanuensis (STT)"
                  />
                </FormGroup>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Feature Flags
                </Typography>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.featureFlags.byokEnabled}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            featureFlags: {
                              ...formData.featureFlags,
                              byokEnabled: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="BYOK Enabled (Bring Your Own Key)"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.featureFlags.apiAccessEnabled}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            featureFlags: {
                              ...formData.featureFlags,
                              apiAccessEnabled: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="API Access Enabled"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={formData.featureFlags.webhookAccess}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            featureFlags: {
                              ...formData.featureFlags,
                              webhookAccess: e.target.checked,
                            },
                          })
                        }
                      />
                    }
                    label="Webhook Access"
                  />
                </FormGroup>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Rate Limits
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Calls per Minute"
                      type="number"
                      value={formData.rateLimits.callsPerMinute}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rateLimits: {
                            ...formData.rateLimits,
                            callsPerMinute: parseInt(e.target.value) || 60,
                          },
                        })
                      }
                    />
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Calls per Day"
                      type="number"
                      value={formData.rateLimits.callsPerDay}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          rateLimits: {
                            ...formData.rateLimits,
                            callsPerDay: parseInt(e.target.value) || 1000,
                          },
                        })
                      }
                    />
                  </Grid>
                </Grid>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Tab 5: Metadata */}
          <TabPanel value={currentTab} index={4}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>
                  Tags
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                  <TextField
                    fullWidth
                    placeholder="Add tag (e.g., VIP, Beta, Partner)"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        handleAddTag();
                      }
                    }}
                  />
                  <Button variant="outlined" onClick={handleAddTag}>
                    Add
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {formData.tags.map((tag) => (
                    <Chip key={tag} label={tag} onDelete={() => handleDeleteTag(tag)} />
                  ))}
                </Box>
              </Grid>

              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Internal Notes"
                  multiline
                  rows={4}
                  value={formData.internalNotes}
                  onChange={(e) => setFormData({ ...formData, internalNotes: e.target.value })}
                  placeholder="Internal notes about this user account..."
                />
              </Grid>

              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Account Source</InputLabel>
                  <Select
                    value={formData.accountSource}
                    label="Account Source"
                    onChange={(e) => setFormData({ ...formData, accountSource: e.target.value })}
                  >
                    <MenuItem value="self-signup">Self-signup</MenuItem>
                    <MenuItem value="admin-created">Admin created</MenuItem>
                    <MenuItem value="api">API</MenuItem>
                    <MenuItem value="migration">Migration</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </TabPanel>
        </DialogContent>

        <DialogActions sx={{ px: 3, py: 2 }}>
          <Button onClick={handleClose} disabled={loading}>
            Cancel
          </Button>
          <Box sx={{ flex: 1 }} />
          {currentTab > 0 && (
            <Button onClick={() => setCurrentTab(currentTab - 1)} disabled={loading}>
              Previous
            </Button>
          )}
          {currentTab < 4 ? (
            <Button
              variant="outlined"
              onClick={() => {
                if (validateTab(currentTab)) {
                  setCurrentTab(currentTab + 1);
                }
              }}
              disabled={loading}
            >
              Next
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleSubmit}
              disabled={!isFormValid() || loading}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                },
              }}
            >
              {loading ? <CircularProgress size={24} /> : 'Create User'}
            </Button>
          )}
        </DialogActions>
      </Dialog>

      {/* Create Organization Sub-Modal */}
      <CreateOrganizationModal
        open={createOrgModalOpen}
        onClose={() => setCreateOrgModalOpen(false)}
        onCreated={handleOrgCreated}
      />
    </>
  );
}
