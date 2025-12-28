import React from 'react';
import {
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Typography,
  CircularProgress,
  Box,
} from '@mui/material';
import DNSRecordRow from './DNSRecordRow';

/**
 * DNSRecordsTable - Table display for DNS records with pagination
 *
 * Props:
 * - records: Array - filtered & paginated DNS records
 * - loading: Boolean - loading state
 * - page: Number - current page
 * - rowsPerPage: Number - rows per page
 * - totalCount: Number - total filtered records
 * - onPageChange: Function - page change handler
 * - onRowsPerPageChange: Function - rows per page change handler
 * - onEditRecord: Function - edit record handler
 * - onDeleteRecord: Function - delete record handler
 * - onToggleProxy: Function - toggle proxy handler
 * - searchQuery: String - current search query (for empty state)
 * - typeFilter: String - current type filter (for empty state)
 */
const DNSRecordsTable = ({
  records,
  loading,
  page,
  rowsPerPage,
  totalCount,
  onPageChange,
  onRowsPerPageChange,
  onEditRecord,
  onDeleteRecord,
  onToggleProxy,
  searchQuery,
  typeFilter
}) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Card>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Type</TableCell>
              <TableCell>Name</TableCell>
              <TableCell>Content</TableCell>
              <TableCell>TTL</TableCell>
              <TableCell>Proxy</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {records.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center" sx={{ py: 8 }}>
                  <Typography color="text.secondary">
                    {searchQuery || typeFilter !== 'all'
                      ? 'No records match your filters'
                      : 'No DNS records configured'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              records.map((record) => (
                <DNSRecordRow
                  key={record.id}
                  record={record}
                  onEdit={onEditRecord}
                  onDelete={onDeleteRecord}
                  onToggleProxy={onToggleProxy}
                />
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <TablePagination
        component="div"
        count={totalCount}
        page={page}
        onPageChange={onPageChange}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={onRowsPerPageChange}
        rowsPerPageOptions={[10, 25, 50, 100]}
      />
    </Card>
  );
};

export default DNSRecordsTable;
