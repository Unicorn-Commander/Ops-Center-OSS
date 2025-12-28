import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Chip,
  IconButton,
  Tabs,
  Tab,
} from '@mui/material';
import { User, Shield, Trash2 } from 'lucide-react';
import UserOverviewTab from './UserOverviewTab';
import UserGroupsTab from './UserGroupsTab';
import UserSSHKeysTab from '../SSHKeys/UserSSHKeysTab';
import UserSudoTab from './UserSudoTab';

const UserDetailModal = ({
  open,
  onClose,
  user,
  activeTab,
  setActiveTab,
  sshKeys,
  newSSHKey,
  setNewSSHKey,
  copiedKey,
  onAddSSHKey,
  onCopyKey,
  onDeleteSSHKey,
  onSudoToggle,
  onDeleteUser,
}) => {
  if (!user) return null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <User size={24} style={{ marginRight: 12 }} />
            {user.username}
            {user.groups?.includes('sudo') && (
              <Chip
                icon={<Shield size={14} />}
                label="Sudo"
                size="small"
                color="secondary"
                sx={{ ml: 2 }}
              />
            )}
          </Box>
          <IconButton
            onClick={() => onDeleteUser(user.username)}
            color="error"
            disabled={user.username === 'muut'} // Protect current user
          >
            <Trash2 size={20} />
          </IconButton>
        </Box>
      </DialogTitle>
      <DialogContent>
        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
          <Tab label="Overview" />
          <Tab label="Groups" />
          <Tab label="SSH Keys" />
          <Tab label="Sudo" />
        </Tabs>

        <Box sx={{ mt: 3 }}>
          {activeTab === 0 && <UserOverviewTab user={user} />}
          {activeTab === 1 && <UserGroupsTab user={user} />}
          {activeTab === 2 && (
            <UserSSHKeysTab
              sshKeys={sshKeys}
              newSSHKey={newSSHKey}
              setNewSSHKey={setNewSSHKey}
              copiedKey={copiedKey}
              onAddKey={onAddSSHKey}
              onCopyKey={onCopyKey}
              onDeleteKey={onDeleteSSHKey}
            />
          )}
          {activeTab === 3 && (
            <UserSudoTab
              user={user}
              onSudoToggle={onSudoToggle}
            />
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
};

export default UserDetailModal;
