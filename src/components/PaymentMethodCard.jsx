/**
 * Payment Method Card Component
 * Displays a single payment method with actions
 */

import React, { useState } from 'react';
import {
  Card,
  CardContent,
  Grid,
  Typography,
  Button,
  IconButton,
  Chip,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import CreditCardIcon from '@mui/icons-material/CreditCard';
import {
  SiVisa,
  SiMastercard,
  SiAmericanexpress,
  SiDiscover
} from 'react-icons/si';

/**
 * Get card brand icon component
 */
const CardBrandIcon = ({ brand }) => {
  const iconStyle = { fontSize: '2.5rem' };

  switch (brand.toLowerCase()) {
    case 'visa':
      return <SiVisa style={{ ...iconStyle, color: '#1A1F71' }} />;
    case 'mastercard':
      return <SiMastercard style={{ ...iconStyle, color: '#EB001B' }} />;
    case 'amex':
    case 'american express':
      return <SiAmericanexpress style={{ ...iconStyle, color: '#006FCF' }} />;
    case 'discover':
      return <SiDiscover style={{ ...iconStyle, color: '#FF6000' }} />;
    default:
      return <CreditCardIcon sx={{ fontSize: '2.5rem', color: 'text.secondary' }} />;
  }
};

/**
 * PaymentMethodCard Component
 *
 * @param {object} method - Payment method object
 * @param {boolean} isDefault - Whether this is the default payment method
 * @param {function} onSetDefault - Callback when user sets as default
 * @param {function} onRemove - Callback when user removes payment method
 * @param {boolean} loading - Whether actions are loading
 */
export const PaymentMethodCard = ({
  method,
  isDefault,
  onSetDefault,
  onRemove,
  loading = false
}) => {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);

  const handleDelete = () => {
    setDeleteDialogOpen(true);
  };

  const confirmDelete = () => {
    onRemove(method.id);
    setDeleteDialogOpen(false);
  };

  const cancelDelete = () => {
    setDeleteDialogOpen(false);
  };

  return (
    <>
      <Card
        sx={{
          mb: 2,
          border: isDefault ? '2px solid' : '1px solid',
          borderColor: isDefault ? 'primary.main' : 'divider',
          boxShadow: isDefault ? 3 : 1,
          transition: 'all 0.3s',
          '&:hover': {
            boxShadow: 4
          }
        }}
      >
        <CardContent>
          <Grid container alignItems="center" spacing={2}>
            {/* Card brand icon */}
            <Grid item xs={12} sm={2} sx={{ textAlign: 'center' }}>
              <CardBrandIcon brand={method.brand} />
            </Grid>

            {/* Card details */}
            <Grid item xs={12} sm={6}>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                •••• •••• •••• {method.last4}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {method.brand.charAt(0).toUpperCase() + method.brand.slice(1)}
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" color="text.secondary">
                  Expires {String(method.exp_month).padStart(2, '0')}/{method.exp_year}
                </Typography>
                {method.expires_soon && (
                  <Chip
                    label="Expires Soon"
                    color="warning"
                    size="small"
                    sx={{ ml: 1 }}
                  />
                )}
              </Box>
              {method.funding && (
                <Typography variant="caption" color="text.secondary" display="block">
                  {method.funding.charAt(0).toUpperCase() + method.funding.slice(1)} Card
                </Typography>
              )}
            </Grid>

            {/* Actions */}
            <Grid item xs={12} sm={4} sx={{ textAlign: 'right' }}>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, alignItems: 'flex-end' }}>
                {isDefault ? (
                  <Chip
                    label="Default"
                    color="primary"
                    icon={<CreditCardIcon />}
                    sx={{ fontWeight: 600 }}
                  />
                ) : (
                  <Button
                    size="small"
                    variant="outlined"
                    onClick={() => onSetDefault(method.id)}
                    disabled={loading}
                  >
                    Set as Default
                  </Button>
                )}

                <IconButton
                  color="error"
                  onClick={handleDelete}
                  disabled={loading}
                  size="small"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={cancelDelete}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Remove Payment Method</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Are you sure you want to remove this payment method?
          </Alert>
          <Typography variant="body1">
            <strong>{method.brand.toUpperCase()}</strong> ending in <strong>{method.last4}</strong>
          </Typography>
          {isDefault && (
            <Alert severity="info" sx={{ mt: 2 }}>
              This is your default payment method. You'll need to set another card as default
              after removing this one.
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelDelete}>Cancel</Button>
          <Button
            onClick={confirmDelete}
            variant="contained"
            color="error"
            disabled={loading}
          >
            Remove
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default PaymentMethodCard;
