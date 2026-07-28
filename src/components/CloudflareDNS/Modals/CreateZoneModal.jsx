import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Alert,
  FormHelperText,
  IconButton,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { ZONE_PRIORITIES } from '../Shared/constants';

/**
 * CreateZoneModal - Dialog for creating new Cloudflare zone
 *
 * Props:
 * - open: Boolean - modal visibility
 * - onClose: Function - close handler
 * - newZone: Object - form state { domain, jump_start, priority }
 * - setNewZone: Function - form state setter
 * - accountInfo: Object - account limits and status
 * - onCreate: Function - create zone handler
 */
const CreateZoneModal = ({ open, onClose, newZone, setNewZone, accountInfo, onCreate }) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">Create Zone</Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          <TextField
            label="Domain Name"
            value={newZone.domain}
            onChange={(e) => setNewZone({ ...newZone, domain: e.target.value })}
            placeholder="example.com"
            helperText="Enter your domain without www"
            fullWidth
            required
            autoFocus
          />

          <FormControl fullWidth>
            <InputLabel>Priority</InputLabel>
            <Select
              value={newZone.priority}
              onChange={(e) => setNewZone({ ...newZone, priority: e.target.value })}
              label="Priority"
            >
              {ZONE_PRIORITIES.map(priority => (
                <MenuItem key={priority.value} value={priority.value}>
                  {priority.label}
                </MenuItem>
              ))}
            </Select>
            <FormHelperText>
              Higher priority zones are processed first when queue is full
            </FormHelperText>
          </FormControl>

          <FormControlLabel
            control={
              <Switch
                checked={newZone.jump_start}
                onChange={(e) => setNewZone({ ...newZone, jump_start: e.target.checked })}
              />
            }
            label="Jump Start (Auto-import DNS records)"
          />

          <Alert severity="info">
            After creating the zone, you'll receive Cloudflare nameservers. Update these at your domain registrar to activate the zone.
          </Alert>

          {accountInfo.zones?.at_limit && (
            <Alert severity="warning">
              You have reached the pending zone limit ({accountInfo.zones.pending}/{accountInfo.zones.limit}).
              This domain will be added to the queue and created automatically when a slot becomes available.
            </Alert>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button
          onClick={onCreate}
          variant="contained"
          disabled={!newZone.domain}
        >
          Create Zone
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default CreateZoneModal;
