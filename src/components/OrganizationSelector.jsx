import React, { useState, useEffect } from 'react';
import {
  Box,
  Autocomplete,
  TextField,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Add as AddIcon,
  Business as BusinessIcon,
  People as PeopleIcon,
  CalendarToday as CalendarIcon,
  Star as StarIcon,
} from '@mui/icons-material';

/**
 * OrganizationSelector Component
 *
 * Allows users to select from existing organizations or create new ones.
 * Used in the Create User modal (Tab 2).
 *
 * Features:
 * - Dropdown to select from existing organizations
 * - Search/filter functionality
 * - "None (personal account)" option
 * - Create new organization modal
 * - Organization details preview
 *
 * @param {Object} props
 * @param {string|null} props.value - Selected organization ID
 * @param {Function} props.onChange - Callback when selection changes
 * @param {string} props.error - Error message
 * @param {string} props.helperText - Helper text
 * @param {boolean} props.required - Whether selection is required
 */
const OrganizationSelector = ({
  value,
  onChange,
  error,
  helperText,
  required = false,
}) => {
  // State for organizations list
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState(null);

  // State for selected organization details
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [orgDetails, setOrgDetails] = useState(null);
  const [detailsLoading, setDetailsLoading] = useState(false);

  // State for create modal
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState(null);

  // State for parent organizations (for hierarchies)
  const [parentOrgs, setParentOrgs] = useState([]);

  // Form data for new organization
  const [formData, setFormData] = useState({
    name: '',
    domain: '',
    description: '',
    logo_url: '',
    billing_email: '',
    max_members: 5,
    parent_org_id: '',
  });

  // Fetch organizations on mount
  useEffect(() => {
    fetchOrganizations();
  }, []);

  // Fetch organization details when selection changes
  useEffect(() => {
    if (value && value !== 'none') {
      fetchOrgDetails(value);
    } else {
      setOrgDetails(null);
    }
  }, [value]);

  // Fetch all organizations
  const fetchOrganizations = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const response = await fetch('/api/v1/organizations', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch organizations');
      }

      const data = await response.json();
      setOrganizations(data.organizations || []);
      setParentOrgs(data.organizations || []); // For hierarchy selector
    } catch (err) {
      console.error('Failed to fetch organizations:', err);
      setLoadError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Fetch organization details
  const fetchOrgDetails = async (orgId) => {
    setDetailsLoading(true);
    try {
      const response = await fetch(`/api/v1/organizations/${orgId}`, {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to fetch organization details');
      }

      const data = await response.json();
      setOrgDetails(data.organization || data);
    } catch (err) {
      console.error('Failed to fetch organization details:', err);
      setOrgDetails(null);
    } finally {
      setDetailsLoading(false);
    }
  };

  // Handle organization selection
  const handleOrgSelect = (event, newValue) => {
    if (newValue === null || newValue.id === 'none') {
      setSelectedOrg(null);
      onChange(null);
    } else {
      setSelectedOrg(newValue);
      onChange(newValue.id);
    }
  };

  // Open create modal
  const handleOpenCreate = () => {
    setFormData({
      name: '',
      domain: '',
      description: '',
      logo_url: '',
      billing_email: '',
      max_members: 5,
      parent_org_id: '',
    });
    setCreateError(null);
    setCreateModalOpen(true);
  };

  // Close create modal
  const handleCloseCreate = () => {
    setCreateModalOpen(false);
    setCreateError(null);
  };

  // Create new organization
  const handleCreateOrg = async () => {
    setCreating(true);
    setCreateError(null);

    try {
      // Validate required fields
      if (!formData.name.trim()) {
        throw new Error('Organization name is required');
      }

      const response = await fetch('/api/v1/organizations', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
        credentials: 'include',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create organization');
      }

      const data = await response.json();
      const newOrg = data.organization || data;

      // Refresh organizations list
      await fetchOrganizations();

      // Auto-select the new organization
      setSelectedOrg(newOrg);
      onChange(newOrg.id);

      // Close modal
      handleCloseCreate();
    } catch (err) {
      console.error('Failed to create organization:', err);
      setCreateError(err.message);
    } finally {
      setCreating(false);
    }
  };

  // Format organizations for Autocomplete
  const orgOptions = [
    { id: 'none', name: 'None (personal account)', member_count: 0, tier: 'personal' },
    ...organizations,
  ];

  // Get currently selected option
  const currentOption = orgOptions.find((org) =>
    value === null ? org.id === 'none' : org.id === value
  ) || orgOptions[0];

  return (
    <Box>
      {/* Organization Selector */}
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-start' }}>
        <Autocomplete
          fullWidth
          options={orgOptions}
          value={currentOption}
          onChange={handleOrgSelect}
          loading={loading}
          getOptionLabel={(option) => option.name || ''}
          isOptionEqualToValue={(option, value) => option.id === value.id}
          renderOption={(props, option) => (
            <Box component="li" {...props} key={option.id}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%' }}>
                <BusinessIcon sx={{ color: option.id === 'none' ? 'text.secondary' : 'primary.main' }} />
                <Box sx={{ flexGrow: 1 }}>
                  <Typography variant="body2" fontWeight="medium">
                    {option.name}
                  </Typography>
                  {option.id !== 'none' && (
                    <Typography variant="caption" color="text.secondary">
                      {option.member_count || 0} members · {option.tier || 'free'} tier
                    </Typography>
                  )}
                </Box>
              </Box>
            </Box>
          )}
          renderInput={(params) => (
            <TextField
              {...params}
              label="Organization"
              required={required}
              error={!!error}
              helperText={error || helperText}
              InputProps={{
                ...params.InputProps,
                endAdornment: (
                  <>
                    {loading ? <CircularProgress color="inherit" size={20} /> : null}
                    {params.InputProps.endAdornment}
                  </>
                ),
              }}
            />
          )}
        />

        <Button
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={handleOpenCreate}
          sx={{
            mt: 0.5,
            minWidth: '140px',
            height: '56px',
            borderColor: 'primary.main',
            color: 'primary.main',
            '&:hover': {
              borderColor: 'primary.dark',
              background: 'rgba(102, 126, 234, 0.04)',
            },
          }}
        >
          New Org
        </Button>
      </Box>

      {/* Loading Error */}
      {loadError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {loadError}
        </Alert>
      )}

      {/* Organization Details Preview */}
      {value && value !== 'none' && orgDetails && (
        <Paper
          elevation={0}
          sx={{
            mt: 2,
            p: 2,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 1,
            background: 'linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%)',
          }}
        >
          <Typography variant="subtitle2" fontWeight="bold" sx={{ mb: 1.5, color: 'primary.main' }}>
            Organization Details
          </Typography>

          {detailsLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
              <CircularProgress size={24} />
            </Box>
          ) : (
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PeopleIcon fontSize="small" color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Members
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {orgDetails.member_count || 0} / {orgDetails.max_members || '∞'}
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <StarIcon fontSize="small" color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Subscription Tier
                    </Typography>
                    <Chip
                      label={orgDetails.tier || 'free'}
                      size="small"
                      color={orgDetails.tier === 'enterprise' ? 'secondary' : 'default'}
                      sx={{ mt: 0.5 }}
                    />
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BusinessIcon fontSize="small" color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Owner
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {orgDetails.owner_name || orgDetails.owner_email || 'N/A'}
                    </Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CalendarIcon fontSize="small" color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary" display="block">
                      Created
                    </Typography>
                    <Typography variant="body2" fontWeight="medium">
                      {orgDetails.created_at
                        ? new Date(orgDetails.created_at).toLocaleDateString()
                        : 'N/A'
                      }
                    </Typography>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          )}
        </Paper>
      )}

      {/* Create Organization Modal */}
      <Dialog
        open={createModalOpen}
        onClose={handleCloseCreate}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <BusinessIcon color="primary" />
            <Typography variant="h6" component="span">
              Create New Organization
            </Typography>
          </Box>
        </DialogTitle>

        <DialogContent>
          {createError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {createError}
            </Alert>
          )}

          <Box sx={{ pt: 2 }}>
            <Grid container spacing={2}>
              {/* Organization Name */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  required
                  label="Organization Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Acme Corporation"
                  helperText="The official name of your organization"
                />
              </Grid>

              {/* Domain */}
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Domain"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                  placeholder="e.g., acme.com"
                  helperText="For email validation (optional)"
                />
              </Grid>

              {/* Billing Email */}
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Billing Email"
                  type="email"
                  value={formData.billing_email}
                  onChange={(e) => setFormData({ ...formData, billing_email: e.target.value })}
                  placeholder="billing@acme.com"
                  helperText="Defaults to user email"
                />
              </Grid>

              {/* Description */}
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Brief description of your organization..."
                  helperText="Optional description"
                />
              </Grid>

              {/* Logo URL */}
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Logo URL"
                  value={formData.logo_url}
                  onChange={(e) => setFormData({ ...formData, logo_url: e.target.value })}
                  placeholder="https://..."
                  helperText="URL to organization logo"
                />
              </Grid>

              {/* Max Members */}
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Max Members"
                  value={formData.max_members}
                  onChange={(e) => setFormData({ ...formData, max_members: parseInt(e.target.value) || 5 })}
                  inputProps={{ min: 1, max: 1000 }}
                  helperText="Maximum team size"
                />
              </Grid>

              {/* Parent Organization */}
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Parent Organization (Optional)</InputLabel>
                  <Select
                    value={formData.parent_org_id}
                    label="Parent Organization (Optional)"
                    onChange={(e) => setFormData({ ...formData, parent_org_id: e.target.value })}
                  >
                    <MenuItem value="">
                      <em>None - Top-level organization</em>
                    </MenuItem>
                    {parentOrgs.map((org) => (
                      <MenuItem key={org.id} value={org.id}>
                        {org.name}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>

        <DialogActions sx={{ px: 3, pb: 2 }}>
          <Button onClick={handleCloseCreate} disabled={creating}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleCreateOrg}
            disabled={creating || !formData.name.trim()}
            startIcon={creating ? <CircularProgress size={20} /> : <AddIcon />}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              },
            }}
          >
            {creating ? 'Creating...' : 'Create Organization'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default OrganizationSelector;
