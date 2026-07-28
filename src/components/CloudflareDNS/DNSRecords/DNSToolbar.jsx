import React from 'react';
import { Box, TextField, FormControl, InputLabel, Select, MenuItem, Button } from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';
import { RECORD_TYPES } from '../Shared/constants';

/**
 * DNSToolbar - Search, filter, and add controls for DNS records
 *
 * Props:
 * - searchQuery: String - current search query
 * - setSearchQuery: Function - update search
 * - typeFilter: String - current type filter
 * - setTypeFilter: Function - update filter
 * - onAddRecord: Function - add record handler
 * - currentTheme: String - theme for gradient button
 */
const DNSToolbar = ({
  searchQuery,
  setSearchQuery,
  typeFilter,
  setTypeFilter,
  onAddRecord,
  currentTheme
}) => {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
        <TextField
          size="small"
          placeholder="Search records..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{ minWidth: 250 }}
        />
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Type</InputLabel>
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            label="Type"
          >
            <MenuItem value="all">All Types</MenuItem>
            {RECORD_TYPES.map(type => (
              <MenuItem key={type} value={type.toLowerCase()}>{type}</MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <Button
        variant="contained"
        startIcon={<AddIcon />}
        onClick={onAddRecord}
        sx={{
          background: currentTheme === 'unicorn'
            ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
            : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)'
        }}
      >
        Add Record
      </Button>
    </Box>
  );
};

export default DNSToolbar;
