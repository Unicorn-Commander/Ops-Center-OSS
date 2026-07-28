import React from 'react';
import { TextField, Button, Box } from '@mui/material';
import { Plus } from 'lucide-react';

const AddSSHKeyForm = ({ newSSHKey, setNewSSHKey, onAddKey }) => {
  return (
    <Box>
      <TextField
        fullWidth
        multiline
        rows={3}
        placeholder="Paste SSH public key here..."
        value={newSSHKey}
        onChange={(e) => setNewSSHKey(e.target.value)}
        sx={{ mb: 2 }}
      />
      <Button
        variant="contained"
        startIcon={<Plus size={16} />}
        onClick={onAddKey}
        disabled={!newSSHKey.trim()}
        sx={{ mb: 3 }}
      >
        Add SSH Key
      </Button>
    </Box>
  );
};

export default AddSSHKeyForm;
