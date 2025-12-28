import React from 'react';
import {
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  CircularProgress,
} from '@mui/material';
import UserRow from './UserRow';

const UserTable = ({ users, loading, formatLastLogin, onViewDetails }) => {
  return (
    <Card sx={{ backdropFilter: 'blur(10px)' }}>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Username</TableCell>
              <TableCell>UID</TableCell>
              <TableCell>Groups</TableCell>
              <TableCell>Shell</TableCell>
              <TableCell align="center">Sudo</TableCell>
              <TableCell align="center">SSH Keys</TableCell>
              <TableCell>Last Login</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No users found
                </TableCell>
              </TableRow>
            ) : (
              users.map((user) => (
                <UserRow
                  key={user.username}
                  user={user}
                  formatLastLogin={formatLastLogin}
                  onViewDetails={onViewDetails}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Card>
  );
};

export default UserTable;
