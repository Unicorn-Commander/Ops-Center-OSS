import React from 'react';
import { Box } from '@mui/material';
import DNSToolbar from '../../DNSRecords/DNSToolbar';
import DNSRecordsTable from '../../DNSRecords/DNSRecordsTable';

const DNSRecordsTab = ({
  recordSearchQuery,
  setRecordSearchQuery,
  recordTypeFilter,
  setRecordTypeFilter,
  onAddRecord,
  currentTheme,
  paginatedRecords,
  filteredRecords,
  loadingRecords,
  recordPage,
  setRecordPage,
  recordRowsPerPage,
  setRecordRowsPerPage,
  onEditRecord,
  onDeleteRecord,
  onToggleProxy
}) => {
  return (
    <Box>
      <DNSToolbar
        searchQuery={recordSearchQuery}
        setSearchQuery={setRecordSearchQuery}
        typeFilter={recordTypeFilter}
        setTypeFilter={setRecordTypeFilter}
        onAddRecord={onAddRecord}
        currentTheme={currentTheme}
      />

      <DNSRecordsTable
        records={paginatedRecords}
        loading={loadingRecords}
        page={recordPage}
        rowsPerPage={recordRowsPerPage}
        totalCount={filteredRecords.length}
        onPageChange={setRecordPage}
        onRowsPerPageChange={(newRowsPerPage) => {
          setRecordRowsPerPage(newRowsPerPage);
          setRecordPage(0);
        }}
        onEditRecord={onEditRecord}
        onDeleteRecord={onDeleteRecord}
        onToggleProxy={onToggleProxy}
        searchQuery={recordSearchQuery}
        typeFilter={recordTypeFilter}
      />
    </Box>
  );
};

export default DNSRecordsTab;
