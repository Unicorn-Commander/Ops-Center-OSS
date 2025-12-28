import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  ButtonGroup,
  Chip,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  Alert,
} from '@mui/material';
import {
  Close as CloseIcon,
  Delete as DeleteIcon,
  Block as BlockIcon,
  Security as SecurityIcon,
  SwapHoriz as SwapHorizIcon,
  MoreVert as MoreVertIcon,
  Group as GroupIcon,
} from '@mui/icons-material';

const BulkActionsToolbar = ({
  selectedCount,
  selectedUsers,
  onClearSelection,
  onBulkDelete,
  onBulkSuspend,
  onBulkAssignRoles,
  onBulkChangeTier,
  availableRoles,
}) => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [confirmDialog, setConfirmDialog] = useState({ open: false, action: null });
  const [roleDialog, setRoleDialog] = useState(false);
  const [tierDialog, setTierDialog] = useState(false);
  const [selectedRoles, setSelectedRoles] = useState([]);
  const [selectedTier, setSelectedTier] = useState('');
  const [reason, setReason] = useState('');

  const handleMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleConfirmAction = (action) => {
    setConfirmDialog({ open: true, action });
    handleMenuClose();
  };

  const handleExecuteAction = async () => {
    const { action } = confirmDialog;

    try {
      switch (action) {
        case 'delete':
          await onBulkDelete(selectedUsers, reason);
          break;
        case 'suspend':
          await onBulkSuspend(selectedUsers, reason);
          break;
        default:
          break;
      }
      setConfirmDialog({ open: false, action: null });
      setReason('');
    } catch (error) {
      console.error('Bulk action failed:', error);
    }
  };

  const handleRoleAssignment = async () => {
    if (selectedRoles.length === 0) return;

    try {
      await onBulkAssignRoles(selectedUsers, selectedRoles);
      setRoleDialog(false);
      setSelectedRoles([]);
    } catch (error) {
      console.error('Role assignment failed:', error);
    }
  };

  const handleTierChange = async () => {
    if (!selectedTier || !reason) return;

    try {
      await onBulkChangeTier(selectedUsers, selectedTier, reason);
      setTierDialog(false);
      setSelectedTier('');
      setReason('');
    } catch (error) {
      console.error('Tier change failed:', error);
    }
  };

  return (
    <>
      <Paper
        sx={{
          p: 2,
          mb: 2,
          bgcolor: 'primary.main',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
        elevation={3}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Chip
            icon={<GroupIcon />}
            label={`${selectedCount} selected`}
            color="secondary"
            sx={{ color: 'white', fontWeight: 'bold' }}
          />
          <Typography variant="body2">
            Bulk actions available
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <ButtonGroup variant="contained" color="secondary">
            <Tooltip title="Assign Roles">
              <Button
                startIcon={<SecurityIcon />}
                onClick={() => setRoleDialog(true)}
              >
                Roles
              </Button>
            </Tooltip>
            <Tooltip title="Change Tier">
              <Button
                startIcon={<SwapHorizIcon />}
                onClick={() => setTierDialog(true)}
              >
                Tier
              </Button>
            </Tooltip>
            <Tooltip title="Suspend Users">
              <Button
                startIcon={<BlockIcon />}
                onClick={() => handleConfirmAction('suspend')}
                color="warning"
              >
                Suspend
              </Button>
            </Tooltip>
            <Tooltip title="Delete Users">
              <Button
                startIcon={<DeleteIcon />}
                onClick={() => handleConfirmAction('delete')}
                color="error"
              >
                Delete
              </Button>
            </Tooltip>
          </ButtonGroup>

          <Tooltip title="More actions">
            <IconButton
              color="inherit"
              onClick={handleMenuClick}
            >
              <MoreVertIcon />
            </IconButton>
          </Tooltip>

          <Tooltip title="Clear selection">
            <IconButton
              color="inherit"
              onClick={onClearSelection}
            >
              <CloseIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Paper>

      {/* More Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={() => { setRoleDialog(true); handleMenuClose(); }}>
          <ListItemIcon>
            <SecurityIcon />
          </ListItemIcon>
          <ListItemText>Assign Roles</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => { setTierDialog(true); handleMenuClose(); }}>
          <ListItemIcon>
            <SwapHorizIcon />
          </ListItemIcon>
          <ListItemText>Change Subscription Tier</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleConfirmAction('suspend')}>
          <ListItemIcon>
            <BlockIcon color="warning" />
          </ListItemIcon>
          <ListItemText>Suspend Accounts</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => handleConfirmAction('delete')}>
          <ListItemIcon>
            <DeleteIcon color="error" />
          </ListItemIcon>
          <ListItemText>Delete Accounts</ListItemText>
        </MenuItem>
      </Menu>

      {/* Confirmation Dialog */}
      <Dialog
        open={confirmDialog.open}
        onClose={() => setConfirmDialog({ open: false, action: null })}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Confirm {confirmDialog.action === 'delete' ? 'Deletion' : 'Suspension'}
        </DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            You are about to {confirmDialog.action} {selectedCount} user{selectedCount !== 1 ? 's' : ''}.
            {confirmDialog.action === 'delete' && ' This action cannot be undone.'}
          </Alert>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason (required)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Provide a reason for this action..."
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setConfirmDialog({ open: false, action: null });
            setReason('');
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            color={confirmDialog.action === 'delete' ? 'error' : 'warning'}
            onClick={handleExecuteAction}
            disabled={!reason.trim()}
          >
            {confirmDialog.action === 'delete' ? 'Delete' : 'Suspend'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Role Assignment Dialog */}
      <Dialog
        open={roleDialog}
        onClose={() => setRoleDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Assign Roles to {selectedCount} User{selectedCount !== 1 ? 's' : ''}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            Selected roles will be added to all selected users. Existing roles will not be affected.
          </Alert>
          <FormControl fullWidth>
            <InputLabel>Select Roles</InputLabel>
            <Select
              multiple
              value={selectedRoles}
              onChange={(e) => setSelectedRoles(e.target.value)}
              label="Select Roles"
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((role) => (
                    <Chip
                      key={role}
                      label={typeof role === 'string' ? role.replace(/^brigade-(platform-)?/, '') : String(role || '')}
                      size="small"
                    />
                  ))}
                </Box>
              )}
            >
              {availableRoles.map((role) => (
                <MenuItem key={role} value={role}>
                  {typeof role === 'string' ? role.replace(/^brigade-(platform-)?/, '') : String(role || '')}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setRoleDialog(false);
            setSelectedRoles([]);
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleRoleAssignment}
            disabled={selectedRoles.length === 0}
          >
            Assign Roles
          </Button>
        </DialogActions>
      </Dialog>

      {/* Tier Change Dialog */}
      <Dialog
        open={tierDialog}
        onClose={() => setTierDialog(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Change Tier for {selectedCount} User{selectedCount !== 1 ? 's' : ''}
        </DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>
            This will override the subscription tier for all selected users.
          </Alert>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>New Subscription Tier</InputLabel>
            <Select
              value={selectedTier}
              onChange={(e) => setSelectedTier(e.target.value)}
              label="New Subscription Tier"
            >
              <MenuItem value="trial">Trial</MenuItem>
              <MenuItem value="starter">Starter</MenuItem>
              <MenuItem value="professional">Professional</MenuItem>
              <MenuItem value="enterprise">Enterprise</MenuItem>
              <MenuItem value="founders">Founders Friend</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Reason (required)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Provide a reason for this tier change..."
            required
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => {
            setTierDialog(false);
            setSelectedTier('');
            setReason('');
          }}>
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleTierChange}
            disabled={!selectedTier || !reason.trim()}
          >
            Change Tier
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default BulkActionsToolbar;
