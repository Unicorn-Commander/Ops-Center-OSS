import React from 'react';
import { Box, Typography } from '@mui/material';
import AddSSHKeyForm from './AddSSHKeyForm';
import SSHKeyList from './SSHKeyList';

const UserSSHKeysTab = ({
  sshKeys,
  newSSHKey,
  setNewSSHKey,
  copiedKey,
  onAddKey,
  onCopyKey,
  onDeleteKey,
}) => {
  return (
    <Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {sshKeys.length} SSH key(s) configured
      </Typography>

      <AddSSHKeyForm
        newSSHKey={newSSHKey}
        setNewSSHKey={setNewSSHKey}
        onAddKey={onAddKey}
      />

      <SSHKeyList
        sshKeys={sshKeys}
        copiedKey={copiedKey}
        onCopyKey={onCopyKey}
        onDeleteKey={onDeleteKey}
      />
    </Box>
  );
};

export default UserSSHKeysTab;
