import React from 'react';
import { Card, CardContent, TextField, InputAdornment } from '@mui/material';
import { Search } from 'lucide-react';

const SearchBar = ({ searchTerm, setSearchTerm }) => {
  return (
    <Card sx={{ mb: 3, backdropFilter: 'blur(10px)' }}>
      <CardContent>
        <TextField
          fullWidth
          placeholder="Search by username or group..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <Search size={20} />
              </InputAdornment>
            ),
          }}
        />
      </CardContent>
    </Card>
  );
};

export default SearchBar;
