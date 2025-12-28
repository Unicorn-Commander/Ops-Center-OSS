import React, { useState } from 'react';
import {
  Box, TextField, Button, Alert, Typography, Card, CardContent,
  CircularProgress, Chip
} from '@mui/material';
import { Redeem, CheckCircle, Error } from '@mui/icons-material';

export default function CouponRedemption({ onSuccess }) {
  const [code, setCode] = useState('');
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState(null);

  const handleRedeem = async () => {
    if (!code.trim()) {
      setResult({ success: false, message: 'Please enter a coupon code' });
      return;
    }

    try {
      setValidating(true);
      setResult(null);

      const response = await fetch('/api/v1/credits/coupons/redeem', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({ code: code.toUpperCase() })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to redeem coupon');
      }

      setResult({
        success: true,
        message: data.message || 'Coupon redeemed successfully!',
        credits_added: data.credits_added,
        new_balance: data.new_balance
      });

      setCode('');

      // Call onSuccess callback if provided
      if (onSuccess) {
        setTimeout(() => onSuccess(), 1500);
      }
    } catch (err) {
      setResult({
        success: false,
        message: err.message || 'Failed to redeem coupon'
      });
    } finally {
      setValidating(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleRedeem();
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Redeem sx={{ mr: 1, color: 'primary.main', fontSize: 28 }} />
          <Typography variant="h6">
            Redeem Coupon Code
          </Typography>
        </Box>

        <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
          Enter a promotional code to add credits to your account
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            label="Coupon Code"
            value={code}
            onChange={(e) => {
              setCode(e.target.value.toUpperCase());
              setResult(null);
            }}
            onKeyPress={handleKeyPress}
            placeholder="FREEMONTH"
            fullWidth
            disabled={validating}
            inputProps={{
              style: { textTransform: 'uppercase', fontFamily: 'monospace' }
            }}
          />
          <Button
            variant="contained"
            onClick={handleRedeem}
            disabled={!code.trim() || validating}
            sx={{ minWidth: 120 }}
          >
            {validating ? <CircularProgress size={24} /> : 'Redeem'}
          </Button>
        </Box>

        {result && (
          <Alert
            severity={result.success ? 'success' : 'error'}
            icon={result.success ? <CheckCircle /> : <Error />}
            sx={{ mt: 2 }}
          >
            <Typography variant="body2" sx={{ mb: result.credits_added ? 1 : 0 }}>
              {result.message}
            </Typography>
            {result.credits_added && (
              <Box sx={{ mt: 1 }}>
                <Chip
                  label={`+$${result.credits_added.toFixed(2)} Credits`}
                  color="success"
                  size="small"
                  sx={{ mr: 1 }}
                />
                <Chip
                  label={`New Balance: $${result.new_balance.toFixed(2)}`}
                  color="info"
                  size="small"
                />
              </Box>
            )}
          </Alert>
        )}

        {/* Example Codes (for demo/testing) */}
        <Box sx={{ mt: 3, p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
          <Typography variant="caption" color="textSecondary" display="block" gutterBottom>
            Example coupon codes:
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1 }}>
            <Chip
              label="WELCOME10"
              size="small"
              variant="outlined"
              onClick={() => setCode('WELCOME10')}
              clickable
            />
            <Chip
              label="FREEMONTH"
              size="small"
              variant="outlined"
              onClick={() => setCode('FREEMONTH')}
              clickable
            />
            <Chip
              label="EARLYBIRD"
              size="small"
              variant="outlined"
              onClick={() => setCode('EARLYBIRD')}
              clickable
            />
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
}
