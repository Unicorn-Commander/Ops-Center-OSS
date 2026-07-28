import React from 'react';
import { Box } from '@mui/material';
import ZoneDetailHeader from './ZoneDetailHeader';
import ZoneDetailTabs from './ZoneDetailTabs';
import OverviewTab from './tabs/OverviewTab';
import DNSRecordsTab from './tabs/DNSRecordsTab';
import NameserversTab from './tabs/NameserversTab';
import SettingsTab from './tabs/SettingsTab';

const ZoneDetailView = ({
  zone,
  onBack,
  activeTab,
  setActiveTab,
  dnsRecords,
  loadingRecords,
  onAddRecord,
  onEditRecord,
  onDeleteRecord,
  onToggleProxy,
  recordSearchQuery,
  setRecordSearchQuery,
  recordTypeFilter,
  setRecordTypeFilter,
  recordPage,
  setRecordPage,
  recordRowsPerPage,
  setRecordRowsPerPage,
  filteredRecords,
  paginatedRecords,
  onCheckStatus,
  onDeleteZone,
  onCopyNameservers,
  currentTheme
}) => {
  return (
    <Box sx={{ p: 3 }}>
      <ZoneDetailHeader
        zone={zone}
        onBack={onBack}
        onCheckStatus={onCheckStatus}
        onDeleteZone={onDeleteZone}
      />

      <ZoneDetailTabs
        activeTab={activeTab}
        onChange={setActiveTab}
      />

      {/* Tab Content */}
      {activeTab === 0 && (
        <OverviewTab
          zone={zone}
          dnsRecords={dnsRecords}
        />
      )}

      {activeTab === 1 && (
        <DNSRecordsTab
          recordSearchQuery={recordSearchQuery}
          setRecordSearchQuery={setRecordSearchQuery}
          recordTypeFilter={recordTypeFilter}
          setRecordTypeFilter={setRecordTypeFilter}
          onAddRecord={onAddRecord}
          currentTheme={currentTheme}
          paginatedRecords={paginatedRecords}
          filteredRecords={filteredRecords}
          loadingRecords={loadingRecords}
          recordPage={recordPage}
          setRecordPage={setRecordPage}
          recordRowsPerPage={recordRowsPerPage}
          setRecordRowsPerPage={setRecordRowsPerPage}
          onEditRecord={onEditRecord}
          onDeleteRecord={onDeleteRecord}
          onToggleProxy={onToggleProxy}
        />
      )}

      {activeTab === 2 && (
        <NameserversTab
          zone={zone}
          onCopyNameservers={onCopyNameservers}
        />
      )}

      {activeTab === 3 && (
        <SettingsTab
          zone={zone}
          onDeleteZone={onDeleteZone}
        />
      )}
    </Box>
  );
};

export default ZoneDetailView;
