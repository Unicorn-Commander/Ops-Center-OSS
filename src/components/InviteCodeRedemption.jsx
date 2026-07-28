import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Chip
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Redeem as RedeemIcon
} from '@mui/icons-material';

/**
 * Invite Code Redemption Component
 *
 * Can be embedded in signup flow or user settings
 * Shows validation status and handles redemption
 */
const InviteCodeRedemption = ({ onSuccess, standalone = false }) => {
  const [code, setCode] = useState('');
  const [validating, setValidating] = useState(false);
  const [redeeming, setRedeeming] = useState(false);
  const [validation, setValidation] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Validate code in real-time
  const handleValidate = async () => {
    if (!code.trim()) {
      setValidation(null);
      return;
    }

    try {
      setValidating(true);
      setError(null);

      const response = await fetch(`/api/v1/invite-codes/validate/${encodeURIComponent(code.trim())}`, {
        credentials: 'include'
      });

      const data = await response.json();
      setValidation(data);

      if (!data.valid) {
        setError(data.message);
      }
    } catch (err) {
      console.error('Error validating code:', err);
      setError('Failed to validate invite code');
      setValidation(null);
    } finally {
      setValidating(false);
    }
  };

  // Redeem the code
  const handleRedeem = async () => {
    if (!validation || !validation.valid) {
      return;
    }

    try {
      setRedeeming(true);
      setError(null);

      const response = await fetch('/api/v1/invite-codes/redeem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ code: code.trim() })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to redeem invite code');
      }

      const data = await response.json();
      setSuccess(data);
      setCode('');
      setValidation(null);

      // Notify parent component
      if (onSuccess) {
        onSuccess(data);
      }
    } catch (err) {
      console.error('Error redeeming code:', err);
      setError(err.message || 'Failed to redeem invite code');
    } finally {
      setRedeeming(false);
    }
  };

  // Trigger validation when user stops typing
  React.useEffect(() => {
    const timer = setTimeout(() => {
      if (code.trim()) {
        handleValidate();
      }
    }, 500);

    return () => clearTimeout(timer);
  }, [code]);

  return (
    <Paper sx={{ p: 3, maxWidth: standalone ? 500 : '100%', mx: standalone ? 'auto' : 0 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
        <RedeemIcon color="primary" />
        <Typography variant="h6">Have an Invite Code?</Typography>
      </Box>

      <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
        Enter your invite code below to unlock special access and benefits.
      </Typography>

      {/* Input Field */}
      <TextField
        fullWidth
        label="Invite Code"
        placeholder="VIP-FOUNDER-XXXXX"
        value={code}
        onChange={(e) => setCode(e.target.value.toUpperCase())}
        disabled={redeeming || !!success}
        sx={{ mb: 2 }}
        InputProps={{
          endAdornment: validating && <CircularProgress size={20} />
        }}
      />

      {/* Validation Status */}
      {validation && validation.valid && !success && (
        <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold">
            Valid invite code for: {validation.tier_name || validation.tier_code}
          </Typography>
          {validation.expires_at && (
            <Typography variant="caption" display="block">
              Expires: {new Date(validation.expires_at).toLocaleDateString()}
            </Typography>
          )}
          {validation.remaining_uses !== null && (
            <Typography variant="caption" display="block">
              Remaining uses: {validation.remaining_uses}
            </Typography>
          )}
        </Alert>
      )}

      {/* Error Message */}
      {error && (
        <Alert severity="error" icon={<ErrorIcon />} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Success Message */}
      {success && (
        <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 2 }}>
          <Typography variant="body2" fontWeight="bold">
            Invite code redeemed successfully!
          </Typography>
          <Typography variant="caption" display="block">
            You've been assigned to: {success.tier_name || success.tier_code}
          </Typography>
        </Alert>
      )}

      {/* Redeem Button */}
      {!success && (
        <Button
          fullWidth
          variant="contained"
          size="large"
          disabled={!validation || !validation.valid || redeeming}
          onClick={handleRedeem}
          startIcon={redeeming ? <CircularProgress size={20} /> : <RedeemIcon />}
        >
          {redeeming ? 'Redeeming...' : 'Redeem Invite Code'}
        </Button>
      )}

      {/* Help Text */}
      {!success && (
        <Typography variant="caption" color="textSecondary" sx={{ mt: 2, display: 'block' }}>
          Invite codes are provided by administrators for special access. Contact support if you
          need assistance.
        </Typography>
      )}
    </Paper>
  );
};

export default InviteCodeRedemption;
