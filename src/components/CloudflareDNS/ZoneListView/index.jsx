import React from 'react';
import { Box } from '@mui/material';
import ZoneListHeader from './ZoneListHeader';
import ZoneMetricsCards from './ZoneMetricsCards';
import WarningsBanner from './WarningsBanner';
import ZoneListToolbar from './ZoneListToolbar';
import ZonesTable from './ZonesTable';

const ZoneListView = ({
  accountInfo,
  searchQuery,
  setSearchQuery,
  statusFilter,
  setStatusFilter,
  page,
  setPage,
  rowsPerPage,
  setRowsPerPage,
  paginatedZones,
  filteredZones,
  onCreateZone,
  onRefresh,
  onSelectZone,
  onCheckStatus,
  onDeleteZone,
  onCopyNameservers,
  currentTheme
}) => {
  return (
    <Box sx={{ p: 3 }}>
      <ZoneListHeader currentTheme={currentTheme} />

      <ZoneMetricsCards accountInfo={accountInfo} />

      <WarningsBanner accountInfo={accountInfo} />

      <ZoneListToolbar
        onCreateZone={onCreateZone}
        onRefresh={onRefresh}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        currentTheme={currentTheme}
      />

      <ZonesTable
        zones={paginatedZones}
        page={page}
        rowsPerPage={rowsPerPage}
        totalCount={filteredZones.length}
        onPageChange={setPage}
        onRowsPerPageChange={(newRowsPerPage) => {
          setRowsPerPage(newRowsPerPage);
          setPage(0);
        }}
        onSelectZone={onSelectZone}
        onCheckStatus={onCheckStatus}
        onDeleteZone={onDeleteZone}
        onCopyNameservers={onCopyNameservers}
        searchQuery={searchQuery}
        statusFilter={statusFilter}
      />
    </Box>
  );
};

export default ZoneListView;
