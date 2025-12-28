import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Alert,
  CircularProgress,
  IconButton,
  InputAdornment,
  Typography,
  Chip,
  Stack,
  Paper,
  Divider,
  Grid
} from '@mui/material';
import {
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  TrashIcon,
  ArrowPathIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import { credentialService } from '../../services/credentialService';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * NameCheap Settings Component
 *
 * Manages NameCheap API credentials with:
 * - API Key (password field)
 * - Username (text field)
 * - Client IP (text field with auto-detect)
 * - Masked display of existing credentials
 * - Test connection with all three fields
 */
export default function NameCheapSettings() {
  const { theme } = useTheme();
  const isDark = theme === 'magic-unicorn' || theme === 'dark';

  // State management
  const [credential, setCredential] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  // Form state (NameCheap requires all three fields)
  const [apiKey, setApiKey] = useState('');
  const [username, setUsername] = useState('');
  const [clientIp, setClientIp] = useState('');
  const [description, setDescription] = useState('');
  const [showApiKey, setShowApiKey] = useState(false);

  // Operation states
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [detectingIp, setDetectingIp] = useState(false);
  const [error, setError] = useState(null);

  // Auto-hide timer
  const [hideTimer, setHideTimer] = useState(null);

  // Load credential on mount
  useEffect(() => {
    loadCredential();
  }, []);

  // Auto-hide API key after 30 seconds
  useEffect(() => {
    if (showApiKey) {
      const timer = setTimeout(() => {
        setShowApiKey(false);
      }, 30000);
      setHideTimer(timer);

      return () => {
        if (timer) clearTimeout(timer);
      };
    }
  }, [showApiKey]);

  /**
   * Load credential from backend
   */
  const loadCredential = async () => {
    setLoading(true);
    setError(null);

    try {
      const credentials = await credentialService.list();
      const ncCred = credentials.find(c => c.service === 'namecheap' && c.credential_type === 'api_key');

      if (ncCred) {
        setCredential(ncCred);
        // Parse composite credential from metadata
        const meta = ncCred.metadata || {};
        setUsername(meta.username || '');
        setClientIp(meta.client_ip || '');
        setDescription(meta.description || '');
      } else {
        setEditing(true); // No credential exists, show form
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  /**
   * Detect client IP address
   */
  const detectClientIP = async () => {
    setDetectingIp(true);
    setError(null);

    try {
      const response = await fetch('https://api.ipify.org?format=json');
      if (!response.ok) throw new Error('Failed to detect IP');

      const data = await response.json();
      setClientIp(data.ip);
    } catch (err) {
      setError('Failed to detect IP address. Please enter manually.');
    } finally {
      setDetectingIp(false);
    }
  };

  /**
   * Save credential (create or update)
   */
  const handleSave = async () => {
    // Validate all required fields
    if (!apiKey.trim()) {
      setError('API key is required');
      return;
    }
    if (!username.trim()) {
      setError('Username is required');
      return;
    }
    if (!clientIp.trim()) {
      setError('Client IP is required');
      return;
    }

    setError(null);
    setSaving(true);

    try {
      // Store username and client_ip in metadata
      const metadata = {
        username: username.trim(),
        client_ip: clientIp.trim(),
        description: description.trim()
      };

      if (credential) {
        await credentialService.update('namecheap', 'api_key', apiKey, metadata);
      } else {
        await credentialService.create('namecheap', 'api_key', apiKey, metadata);
      }

      await loadCredential();
      setEditing(false);
      setApiKey('');
      setShowApiKey(false);
      setTestResult({ success: true, message: 'Credentials saved successfully' });

      // Auto-clear success message after 5 seconds
      setTimeout(() => setTestResult(null), 5000);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  /**
   * Test credential connection
   */
  const handleTest = async () => {
    // Validate fields before testing
    const valueToTest = apiKey.trim() || (credential ? null : '');

    if (!valueToTest && !credential) {
      setError('No credential to test');
      return;
    }

    // If editing, need all three fields
    if (apiKey && (!username.trim() || !clientIp.trim())) {
      setError('Username and Client IP are required for testing');
      return;
    }

    setTesting(true);
    setTestResult(null);
    setError(null);

    try {
      // If testing new credentials, pass composite value
      let testValue = valueToTest;
      if (apiKey) {
        testValue = JSON.stringify({
          api_key: apiKey,
          username: username.trim(),
          client_ip: clientIp.trim()
        });
      }

      const result = await credentialService.test('namecheap', testValue);
      setTestResult(result);

      // Auto-clear test result after 10 seconds
      setTimeout(() => setTestResult(null), 10000);
    } catch (err) {
      setTestResult({ success: false, error: err.message });
    } finally {
      setTesting(false);
    }
  };

  /**
   * Delete credential
   */
  const handleDelete = async () => {
    if (!window.confirm('Delete NameCheap credentials? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    setError(null);

    try {
      await credentialService.delete('namecheap', 'api_key');
      setCredential(null);
      setEditing(true);
      setTestResult(null);
      setApiKey('');
      setUsername('');
      setClientIp('');
      setDescription('');
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  /**
   * Toggle API key visibility
   */
  const handleToggleVisibility = () => {
    setShowApiKey(!showApiKey);
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        NameCheap API Credentials
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Used for domain management, DNS configuration, and SSL certificate provisioning.
        NameCheap requires an API key, username, and whitelisted IP address.
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {!editing && credential ? (
        // ===== DISPLAY MODE =====
        <Paper
          sx={{
            p: 3,
            backgroundColor: isDark ? 'rgba(30, 41, 59, 0.5)' : 'rgba(248, 250, 252, 1)',
            border: isDark ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid rgba(0, 0, 0, 0.12)'
          }}
        >
          <Grid container spacing={3}>
            {/* Masked API Key */}
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                API Key
              </Typography>
              <Stack direction="row" spacing={2} alignItems="center">
                <Typography
                  variant="body1"
                  sx={{
                    fontFamily: 'monospace',
                    flexGrow: 1,
                    fontSize: '0.95rem',
                    color: isDark ? 'rgba(255, 255, 255, 0.9)' : 'rgba(0, 0, 0, 0.87)'
                  }}
                >
                  {credential.masked_value}
                </Typography>
                <Chip
                  label="Encrypted"
                  size="small"
                  color="success"
                  icon={<CheckCircleIcon className="h-4 w-4" />}
                />
              </Stack>
            </Grid>

            {/* Username */}
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Username
              </Typography>
              <Typography variant="body1">
                {credential.metadata?.username || 'Not set'}
              </Typography>
            </Grid>

            {/* Client IP */}
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Client IP
              </Typography>
              <Typography variant="body1" sx={{ fontFamily: 'monospace' }}>
                {credential.metadata?.client_ip || 'Not set'}
              </Typography>
            </Grid>

            {/* Description */}
            {credential.metadata?.description && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body2">
                  {credential.metadata.description}
                </Typography>
              </Grid>
            )}
          </Grid>

          <Divider sx={{ my: 2 }} />

          {/* Last Tested Status */}
          {credential.last_tested && (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 3 }}>
              {credential.test_status === 'success' ? (
                <CheckCircleIcon className="h-5 w-5 text-green-500" />
              ) : (
                <ExclamationCircleIcon className="h-5 w-5 text-red-500" />
              )}
              <Typography variant="body2" color="text.secondary">
                Last tested: {new Date(credential.last_tested).toLocaleString()}
              </Typography>
            </Stack>
          )}

          {/* Action Buttons */}
          <Stack direction="row" spacing={2}>
            <Button
              variant="outlined"
              onClick={handleTest}
              disabled={testing}
              startIcon={testing ? <CircularProgress size={16} /> : <ArrowPathIcon className="h-5 w-5" />}
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </Button>
            <Button
              variant="contained"
              onClick={() => setEditing(true)}
            >
              Update
            </Button>
            <Button
              variant="outlined"
              color="error"
              onClick={handleDelete}
              disabled={deleting}
              startIcon={deleting ? <CircularProgress size={16} /> : <TrashIcon className="h-5 w-5" />}
            >
              {deleting ? 'Deleting...' : 'Delete'}
            </Button>
          </Stack>
        </Paper>
      ) : (
        // ===== EDIT MODE =====
        <Box>
          <Grid container spacing={2}>
            {/* API Key Input */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="API Key"
                type={showApiKey ? 'text' : 'password'}
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                placeholder="Enter your NameCheap API key"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={handleToggleVisibility} edge="end">
                        {showApiKey ? (
                          <EyeSlashIcon className="h-5 w-5" />
                        ) : (
                          <EyeIcon className="h-5 w-5" />
                        )}
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                helperText="Enable API access in NameCheap Account → Profile → Tools → API Access"
              />
            </Grid>

            {/* Username Input */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Your NameCheap username"
                helperText="Your NameCheap account username"
              />
            </Grid>

            {/* Client IP Input with Auto-Detect */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Client IP"
                value={clientIp}
                onChange={(e) => setClientIp(e.target.value)}
                placeholder="123.45.67.89"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <Button
                        size="small"
                        onClick={detectClientIP}
                        disabled={detectingIp}
                        startIcon={detectingIp ? <CircularProgress size={14} /> : <GlobeAltIcon className="h-4 w-4" />}
                      >
                        {detectingIp ? 'Detecting...' : 'Detect'}
                      </Button>
                    </InputAdornment>
                  )
                }}
                helperText="Whitelist this IP in NameCheap API settings"
              />
            </Grid>

            {/* Description Input */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description (optional)"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="e.g., Production account"
                helperText="Add a note to help identify this credential"
              />
            </Grid>
          </Grid>

          {/* Action Buttons */}
          <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={!apiKey.trim() || !username.trim() || !clientIp.trim() || saving}
              startIcon={saving ? <CircularProgress size={16} /> : null}
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>

            <Button
              variant="outlined"
              onClick={handleTest}
              disabled={!apiKey.trim() || !username.trim() || !clientIp.trim() || testing}
              startIcon={testing ? <CircularProgress size={16} /> : <ArrowPathIcon className="h-5 w-5" />}
            >
              {testing ? 'Testing...' : 'Test Before Saving'}
            </Button>

            {credential && (
              <Button
                variant="outlined"
                onClick={() => {
                  setEditing(false);
                  setApiKey('');
                  setShowApiKey(false);
                }}
              >
                Cancel
              </Button>
            )}
          </Stack>

          {/* Help Text */}
          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="body2" gutterBottom>
              <strong>Setup Steps:</strong>
            </Typography>
            <Typography variant="body2" component="div">
              1. Login to NameCheap → Account → Profile → Tools<br />
              2. Enable API Access and generate API key<br />
              3. Whitelist your server IP address<br />
              4. Enter credentials above and test connection
            </Typography>
          </Alert>
        </Box>
      )}

      {/* Test Result Alert */}
      {testResult && (
        <Alert
          severity={testResult.success ? 'success' : 'error'}
          sx={{ mt: 3 }}
          onClose={() => setTestResult(null)}
          icon={
            testResult.success ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <ExclamationCircleIcon className="h-5 w-5" />
            )
          }
        >
          {testResult.success
            ? (testResult.message || 'Connection successful')
            : (testResult.error || 'Connection failed')
          }
        </Alert>
      )}
    </Box>
  );
}
