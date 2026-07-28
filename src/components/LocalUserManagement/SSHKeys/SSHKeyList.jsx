import React from 'react';
import {
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Box,
  Chip,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import { Copy, Check, Trash2 } from 'lucide-react';

const SSHKeyList = ({ sshKeys, copiedKey, onCopyKey, onDeleteKey }) => {
  const getSSHKeyType = (key) => {
    if (key.startsWith('ssh-rsa')) return 'RSA';
    if (key.startsWith('ssh-ed25519')) return 'Ed25519';
    if (key.startsWith('ecdsa-')) return 'ECDSA';
    return 'Unknown';
  };

  const truncateSSHKey = (key) => {
    if (key.length <= 70) return key;
    return key.substring(0, 50) + '...' + key.substring(key.length - 20);
  };

  if (sshKeys.length === 0) {
    return (
      <Alert severity="info">
        No SSH keys configured for this user
      </Alert>
    );
  }

  return (
    <List>
      {sshKeys.map((key, index) => {
        // CRITICAL SECURITY FIX: Use key.id NOT array index
        // This was fixed in Sprint 2 - DO NOT CHANGE
        const keyId = typeof key === 'object' && key.id
          ? key.id
          : typeof key === 'object' && key.fingerprint
            ? key.fingerprint
            : index;

        const keyString = typeof key === 'string' ? key : key.key || key;

        return (
          <React.Fragment key={keyId}>
            <ListItem>
              <ListItemText
                primary={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label={getSSHKeyType(keyString)} size="small" />
                    <code style={{ fontSize: '0.75rem' }}>
                      {truncateSSHKey(keyString)}
                    </code>
                  </Box>
                }
              />
              <ListItemSecondaryAction>
                <Tooltip title={copiedKey === keyString ? 'Copied!' : 'Copy'}>
                  <IconButton
                    onClick={() => onCopyKey(keyString)}
                    size="small"
                    sx={{ mr: 1 }}
                  >
                    {copiedKey === keyString ? <Check size={16} /> : <Copy size={16} />}
                  </IconButton>
                </Tooltip>
                <IconButton
                  onClick={() => onDeleteKey(keyId)}
                  size="small"
                  color="error"
                >
                  <Trash2 size={16} />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
            {index < sshKeys.length - 1 && <Divider />}
          </React.Fragment>
        );
      })}
    </List>
  );
};

export default SSHKeyList;
