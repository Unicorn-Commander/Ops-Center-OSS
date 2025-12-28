/**
 * Tier Access Dialog Component
 * Allows admins to manage which subscription tiers can access a specific model
 * Epic 3.3: Model Access Control System
 */

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormGroup,
  FormControlLabel,
  Checkbox,
  TextField,
  Typography,
  Box,
  Chip,
  Divider,
  Alert,
  CircularProgress,
  Skeleton
} from '@mui/material';

const TierAccessDialog = ({ model, open, onClose, onSave }) => {
  const [tiers, setTiers] = useState([]);
  const [selectedTiers, setSelectedTiers] = useState({});
  const [markups, setMarkups] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!open) return;

    const fetchTiers = async () => {
      setLoading(true);
      setError(null);
      try {
        // Fetch all available tiers
        const response = await fetch('/api/v1/admin/tiers/', {
          credentials: 'include'
        });

        if (!response.ok) {
          throw new Error('Failed to fetch tiers');
        }

        const data = await response.json();
        setTiers(data);

        // Initialize selected tiers from model
        const selected = {};
        const markupValues = {};
        (model.tiers || []).forEach(t => {
          selected[t.tier_code] = true;
          markupValues[t.tier_code] = t.markup_multiplier || 1.0;
        });
        setSelectedTiers(selected);
        setMarkups(markupValues);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching tiers:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTiers();
  }, [model, open]);

  const handleToggleTier = (tierCode) => {
    setSelectedTiers(prev => ({
      ...prev,
      [tierCode]: !prev[tierCode]
    }));

    // Set default markup if enabling for first time
    if (!selectedTiers[tierCode] && !markups[tierCode]) {
      setMarkups(prev => ({
        ...prev,
        [tierCode]: 1.0
      }));
    }
  };

  const handleMarkupChange = (tierCode, value) => {
    setMarkups(prev => ({
      ...prev,
      [tierCode]: parseFloat(value) || 1.0
    }));
  };

  const handleSave = async () => {
    try {
      // Build tier assignments
      const assignments = {};
      tiers.forEach(tier => {
        if (selectedTiers[tier.tier_code]) {
          assignments[tier.tier_code] = {
            enabled: true,
            markup_multiplier: markups[tier.tier_code] || 1.0
          };
        } else {
          assignments[tier.tier_code] = { enabled: false };
        }
      });

      // Save via API
      const response = await fetch(`/api/v1/admin/models/${model.model_id}/tiers`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ tier_assignments: assignments })
      });

      if (!response.ok) {
        throw new Error('Failed to update tier access');
      }

      onSave();
      onClose();
    } catch (err) {
      setError(err.message);
      console.error('Error saving tier access:', err);
    }
  };

  const getTierBadgeColor = (tierCode) => {
    switch (tierCode) {
      case 'trial':
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' };
      case 'starter':
        return { bg: 'rgba(59, 130, 246, 0.15)', color: '#3b82f6' };
      case 'professional':
        return { bg: 'rgba(124, 58, 237, 0.15)', color: '#7c3aed' };
      case 'enterprise':
        return { bg: 'rgba(255, 215, 0, 0.15)', color: '#FFD700' };
      default:
        return { bg: 'rgba(148, 163, 184, 0.15)', color: '#94a3b8' };
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        Tier Access: {model?.display_name || model?.model_id}
      </DialogTitle>
      <DialogContent>
        {loading ? (
          <Box sx={{ p: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Loading tier information...
            </Typography>
            <Skeleton variant="rectangular" height={80} sx={{ mb: 2, borderRadius: 1 }} />
            <Skeleton variant="rectangular" height={80} sx={{ mb: 2, borderRadius: 1 }} />
            <Skeleton variant="rectangular" height={80} sx={{ mb: 2, borderRadius: 1 }} />
            <Skeleton variant="rectangular" height={80} sx={{ borderRadius: 1 }} />
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        ) : (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Select which subscription tiers can access this model and configure pricing markup.
            </Typography>

            <FormGroup>
              {tiers.map(tier => {
                const tierColors = getTierBadgeColor(tier.tier_code);
                const isSelected = selectedTiers[tier.tier_code] || false;
                const currentMarkup = markups[tier.tier_code] || 1.0;

                return (
                  <Box key={tier.tier_code} sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isSelected}
                            onChange={() => handleToggleTier(tier.tier_code)}
                          />
                        }
                        label={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body1" fontWeight={600}>
                              {tier.tier_name}
                            </Typography>
                            <Chip
                              label={tier.tier_code}
                              size="small"
                              sx={{
                                backgroundColor: tierColors.bg,
                                color: tierColors.color,
                                fontWeight: 600
                              }}
                            />
                          </Box>
                        }
                        sx={{ flex: 1 }}
                      />
                      {isSelected && (
                        <TextField
                          type="number"
                          label="Markup Multiplier"
                          value={currentMarkup}
                          onChange={(e) => handleMarkupChange(tier.tier_code, e.target.value)}
                          size="small"
                          sx={{ width: '150px' }}
                          inputProps={{
                            min: 0.1,
                            max: 10,
                            step: 0.1
                          }}
                          helperText={currentMarkup !== 1.0 ? `${((currentMarkup - 1) * 100).toFixed(0)}% ${currentMarkup > 1 ? 'markup' : 'discount'}` : ''}
                        />
                      )}
                    </Box>
                    <Typography variant="caption" color="text.secondary" sx={{ ml: 4 }}>
                      {tier.description || `${tier.active_user_count} active users, $${tier.price_monthly}/mo`}
                    </Typography>
                    {tier.tier_code !== tiers[tiers.length - 1].tier_code && (
                      <Divider sx={{ mt: 1 }} />
                    )}
                  </Box>
                );
              })}
            </FormGroup>

            <Box sx={{ mt: 3, p: 2, bgcolor: 'rgba(102, 126, 234, 0.08)', borderRadius: 1 }}>
              <Typography variant="subtitle2" fontWeight={600} gutterBottom>
                Pricing Example:
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Base price: <strong>${model?.pricing_output?.toFixed(4) || '0.0000'}/1K tokens</strong>
                <br />
                With 1.5x markup: <strong>${((model?.pricing_output || 0) * 1.5).toFixed(4)}/1K tokens</strong>
                <br />
                With 0.8x discount: <strong>${((model?.pricing_output || 0) * 0.8).toFixed(4)}/1K tokens</strong>
              </Typography>
            </Box>
          </>
        )}
      </DialogContent>
      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button
          onClick={onClose}
          sx={{
            borderRadius: 2,
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-1px)'
            }
          }}
        >
          Cancel
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={loading}
          sx={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            borderRadius: 2,
            transition: 'all 0.2s',
            '&:hover': {
              transform: 'translateY(-1px)',
              boxShadow: 4,
              background: 'linear-gradient(135deg, #7e8fef 0%, #8a5bb2 100%)'
            }
          }}
        >
          Save Changes
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TierAccessDialog;
