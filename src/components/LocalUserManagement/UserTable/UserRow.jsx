import React from 'react';
import { TableRow, TableCell, Box, Chip, Typography, IconButton, Tooltip } from '@mui/material';
import { User, Shield, Key, Eye } from 'lucide-react';

const UserRow = ({ user, formatLastLogin, onViewDetails }) => {
  return (
    <TableRow
      hover
      onClick={() => onViewDetails(user)}
      sx={{ cursor: 'pointer' }}
    >
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <User size={16} style={{ marginRight: 8 }} />
          {user.username}
        </Box>
      </TableCell>
      <TableCell>{user.uid}</TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
          {user.groups?.slice(0, 3).map(group => (
            <Chip key={group} label={group} size="small" />
          ))}
          {user.groups?.length > 3 && (
            <Chip label={`+${user.groups.length - 3}`} size="small" />
          )}
        </Box>
      </TableCell>
      <TableCell>
        <code style={{ fontSize: '0.875rem' }}>{user.shell}</code>
      </TableCell>
      <TableCell align="center">
        {user.groups?.includes('sudo') ? (
          <Shield size={16} color="#f093fb" />
        ) : (
          '-'
        )}
      </TableCell>
      <TableCell align="center">
        {user.ssh_keys_count > 0 ? (
          <Chip
            label={user.ssh_keys_count}
            size="small"
            color="primary"
            icon={<Key size={14} />}
          />
        ) : (
          '-'
        )}
      </TableCell>
      <TableCell>
        <Typography variant="body2">
          {formatLastLogin(user.last_login)}
        </Typography>
      </TableCell>
      <TableCell align="center">
        <Tooltip title="View Details">
          <IconButton size="small" onClick={(e) => {
            e.stopPropagation();
            onViewDetails(user);
          }}>
            <Eye size={16} />
          </IconButton>
        </Tooltip>
      </TableCell>
    </TableRow>
  );
};

export default UserRow;
