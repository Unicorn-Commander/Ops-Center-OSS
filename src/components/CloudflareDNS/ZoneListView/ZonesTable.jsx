import React from 'react';
import { Card, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, TablePagination, Typography } from '@mui/material';
import ZoneRow from './ZoneRow';

const ZonesTable = ({
  zones,
  page,
  rowsPerPage,
  totalCount,
  onPageChange,
  onRowsPerPageChange,
  onSelectZone,
  onCheckStatus,
  onDeleteZone,
  onCopyNameservers,
  searchQuery,
  statusFilter
}) => {
  return (
    <Card>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Domain</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Nameservers</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {zones.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
                  <Typography color="text.secondary">
                    {searchQuery || statusFilter !== 'all'
                      ? 'No zones match your filters'
                      : 'No zones configured. Create your first zone to get started.'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              zones.map((zone) => (
                <ZoneRow
                  key={zone.zone_id}
                  zone={zone}
                  onSelectZone={onSelectZone}
                  onCheckStatus={onCheckStatus}
                  onDeleteZone={onDeleteZone}
                  onCopyNameservers={onCopyNameservers}
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
        onPageChange={(e, newPage) => onPageChange(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(e) => {
          onRowsPerPageChange(parseInt(e.target.value, 10));
        }}
        rowsPerPageOptions={[5, 10, 25, 50]}
      />
    </Card>
  );
};

export default ZonesTable;
