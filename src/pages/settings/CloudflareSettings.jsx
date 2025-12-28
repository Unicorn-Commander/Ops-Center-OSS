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
  Divider
} from '@mui/material';
import {
  EyeIcon,
  EyeSlashIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  TrashIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { credentialService } from '../../services/credentialService';
import { useTheme } from '../../contexts/ThemeContext';

/**
 * Cloudflare Settings Component
 *
 * Manages Cloudflare API Token credential with:
 * - Masked display of existing credentials
 * - Show/hide password toggle with auto-hide after 30s
 * - Test connection before saving
 * - Edit and delete operations
 */
export default function CloudflareSettings() {
  const { theme } = useTheme();
  const isDark = theme === 'magic-unicorn' || theme === 'dark';

  // State management
  const [credential, setCredential] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);

  // Form state
  const [apiToken, setApiToken] = useState('');
  const [description, setDescription] = useState('');
  const [showToken, setShowToken] = useState(false);

  // Operation states
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState(null);

  // Auto-hide timer
  const [hideTimer, setHideTimer] = useState(null);

  // Load credential on mount
  useEffect(() => {
    loadCredential();
  }, []);

  // Auto-hide password after 30 seconds
  useEffect(() => {
    if (showToken) {
      const timer = setTimeout(() => {
        setShowToken(false);
      }, 30000); // 30 seconds
      setHideTimer(timer);

      return () => {
        if (timer) clearTimeout(timer);
      };
    }
  }, [showToken]);

  /**
   * Load credential from backend
   */
  const loadCredential = async () => {
    setLoading(true);
    setError(null);

    try {
      const credentials = await credentialService.list();
      const cfCred = credentials.find(c => c.service === 'cloudflare' && c.credential_type === 'api_token');

      if (cfCred) {
        setCredential(cfCred);
        setDescription(cfCred.metadata?.description || '');
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
   * Save credential (create or update)
   */
  const handleSave = async () => {
    if (!apiToken.trim()) {
      setError('API token is required');
      return;
    }

    setError(null);
    setSaving(true);

    try {
      const metadata = { description: description.trim() };

      if (credential) {
        await credentialService.update('cloudflare', 'api_token', apiToken, metadata);
      } else {
        await credentialService.create('cloudflare', 'api_token', apiToken, metadata);
      }

      await loadCredential();
      setEditing(false);
      setApiToken('');
      setShowToken(false);
      setTestResult({ success: true, message: 'Credential saved successfully' });

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
    const valueToTest = apiToken.trim() || null;

    if (!valueToTest && !credential) {
      setError('No credential to test');
      return;
    }

    setTesting(true);
    setTestResult(null);
    setError(null);

    try {
      const result = await credentialService.test('cloudflare', valueToTest);
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
    if (!window.confirm('Delete Cloudflare credentials? This action cannot be undone.')) {
      return;
    }

    setDeleting(true);
    setError(null);

    try {
      await credentialService.delete('cloudflare', 'api_token');
      setCredential(null);
      setEditing(true);
      setTestResult(null);
      setApiToken('');
      setDescription('');
    } catch (err) {
      setError(err.message);
    } finally {
      setDeleting(false);
    }
  };

  /**
   * Toggle password visibility
   */
  const handleToggleVisibility = () => {
    setShowToken(!showToken);
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
        Cloudflare API Token
      </Typography>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Used for DNS management, SSL certificate provisioning, and WAF configuration.
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
          {/* Masked Token Display */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              API Token
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
          </Box>

          {/* Description */}
          {credential.metadata?.description && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Description
              </Typography>
              <Typography variant="body2">
                {credential.metadata.description}
              </Typography>
            </Box>
          )}

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
          {/* API Token Input */}
          <TextField
            fullWidth
            label="API Token"
            type={showToken ? 'text' : 'password'}
            value={apiToken}
            onChange={(e) => setApiToken(e.target.value)}
            placeholder="cf_..."
            sx={{ mb: 2 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={handleToggleVisibility} edge="end">
                    {showToken ? (
                      <EyeSlashIcon className="h-5 w-5" />
                    ) : (
                      <EyeIcon className="h-5 w-5" />
                    )}
                  </IconButton>
                </InputAdornment>
              )
            }}
            helperText="Create at: Cloudflare Dashboard → My Profile → API Tokens → Create Token"
          />

          {/* Description Input */}
          <TextField
            fullWidth
            label="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g., Production account"
            sx={{ mb: 3 }}
            helperText="Add a note to help identify this credential"
          />

          {/* Action Buttons */}
          <Stack direction="row" spacing={2}>
            <Button
              variant="contained"
              onClick={handleSave}
              disabled={!apiToken.trim() || saving}
              startIcon={saving ? <CircularProgress size={16} /> : null}
            >
              {saving ? 'Saving...' : 'Save'}
            </Button>

            <Button
              variant="outlined"
              onClick={handleTest}
              disabled={!apiToken.trim() || testing}
              startIcon={testing ? <CircularProgress size={16} /> : <ArrowPathIcon className="h-5 w-5" />}
            >
              {testing ? 'Testing...' : 'Test Before Saving'}
            </Button>

            {credential && (
              <Button
                variant="outlined"
                onClick={() => {
                  setEditing(false);
                  setApiToken('');
                  setShowToken(false);
                }}
              >
                Cancel
              </Button>
            )}
          </Stack>

          {/* Help Text */}
          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="body2">
              <strong>Required Permissions:</strong> Zone:Read, DNS:Edit, SSL:Edit
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
