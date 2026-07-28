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
  FormHelperText,
  IconButton,
} from '@mui/material';
import { Close as CloseIcon } from '@mui/icons-material';
import { RECORD_TYPES, TTL_OPTIONS } from '../Shared/constants';

/**
 * AddEditRecordModal - Dialog for adding/editing DNS records
 *
 * Props:
 * - open: Boolean - modal visibility
 * - onClose: Function - close handler
 * - dnsRecord: Object - form state { type, name, content, ttl, proxied, priority }
 * - setDnsRecord: Function - form state setter
 * - formErrors: Object - validation errors
 * - selectedRecord: Object | null - record being edited (null for add)
 * - selectedZone: Object - current zone
 * - onSubmit: Function - add/update handler
 */
const AddEditRecordModal = ({
  open,
  onClose,
  dnsRecord,
  setDnsRecord,
  formErrors,
  selectedRecord,
  selectedZone,
  onSubmit
}) => {
  const getPlaceholder = (type) => {
    switch (type) {
      case 'A':
        return '192.168.1.1';
      case 'AAAA':
        return '2001:db8::1';
      case 'CNAME':
        return 'target.example.com';
      case 'MX':
        return 'mail.example.com';
      default:
        return 'Record content';
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6">{selectedRecord ? 'Edit' : 'Add'} DNS Record</Typography>
          <IconButton onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, mt: 1 }}>
          <FormControl fullWidth required>
            <InputLabel>Type</InputLabel>
            <Select
              value={dnsRecord.type}
              onChange={(e) => setDnsRecord({ ...dnsRecord, type: e.target.value })}
              label="Type"
              disabled={!!selectedRecord}
            >
              {RECORD_TYPES.map(type => (
                <MenuItem key={type} value={type}>{type}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            label="Name"
            value={dnsRecord.name}
            onChange={(e) => setDnsRecord({ ...dnsRecord, name: e.target.value })}
            placeholder="@ or subdomain"
            helperText={`Full domain: ${dnsRecord.name || '@'}.${selectedZone?.domain || 'domain.com'}`}
            error={!!formErrors.name}
            fullWidth
            required
          />

          <TextField
            label="Content"
            value={dnsRecord.content}
            onChange={(e) => setDnsRecord({ ...dnsRecord, content: e.target.value })}
            placeholder={getPlaceholder(dnsRecord.type)}
            error={!!formErrors.content}
            helperText={formErrors.content}
            fullWidth
            required
          />

          <FormControl fullWidth>
            <InputLabel>TTL</InputLabel>
            <Select
              value={dnsRecord.ttl}
              onChange={(e) => setDnsRecord({ ...dnsRecord, ttl: e.target.value })}
              label="TTL"
            >
              {TTL_OPTIONS.map(option => (
                <MenuItem key={option.value} value={option.value}>{option.label}</MenuItem>
              ))}
            </Select>
            <FormHelperText>Time To Live - How long DNS resolvers cache this record</FormHelperText>
          </FormControl>

          {(dnsRecord.type === 'MX' || dnsRecord.type === 'SRV') && (
            <TextField
              label="Priority"
              type="number"
              value={dnsRecord.priority}
              onChange={(e) => setDnsRecord({ ...dnsRecord, priority: e.target.value })}
              inputProps={{ min: 0, max: 65535 }}
              error={!!formErrors.priority}
              helperText={formErrors.priority || 'Lower values have higher priority (0-65535)'}
              fullWidth
              required
            />
          )}

          {['A', 'AAAA', 'CNAME'].includes(dnsRecord.type) && (
            <FormControlLabel
              control={
                <Switch
                  checked={dnsRecord.proxied}
                  onChange={(e) => setDnsRecord({ ...dnsRecord, proxied: e.target.checked })}
                />
              }
              label={
                <Box>
                  <Typography variant="body2">Proxied (Orange Cloud)</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Enable Cloudflare proxy for DDoS protection and caching
                  </Typography>
                </Box>
              }
            />
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>
          Cancel
        </Button>
        <Button
          onClick={onSubmit}
          variant="contained"
          disabled={!dnsRecord.name || !dnsRecord.content}
        >
          {selectedRecord ? 'Update' : 'Add'} Record
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AddEditRecordModal;
