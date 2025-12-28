import React, { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import { useTheme } from '../../contexts/ThemeContext';
import axios from 'axios';

// Import view components
import ZoneListView from './ZoneListView';
import ZoneDetailView from './ZoneDetailView';

// Import modals
import CreateZoneModal from './Modals/CreateZoneModal';
import AddEditRecordModal from './Modals/AddEditRecordModal';
import DeleteConfirmationModal from './Modals/DeleteConfirmationModal';

// Import shared components
import Toast from './Shared/Toast';

const CloudflareDNS = () => {
  const { currentTheme } = useTheme();

  // State management - Zones
  const [zones, setZones] = useState([]);
  const [selectedZone, setSelectedZone] = useState(null);
  const [loading, setLoading] = useState(true);
  const [zoneDetailView, setZoneDetailView] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  // State management - DNS Records
  const [dnsRecords, setDnsRecords] = useState([]);
  const [loadingRecords, setLoadingRecords] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);

  // State management - Account info
  const [accountInfo, setAccountInfo] = useState({ zones: {}, rate_limit: {}, features: {} });

  // Dialogs
  const [openCreateZone, setOpenCreateZone] = useState(false);
  const [openAddRecord, setOpenAddRecord] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Pagination and filtering - Zones
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  // Pagination and filtering - DNS Records
  const [recordPage, setRecordPage] = useState(0);
  const [recordRowsPerPage, setRecordRowsPerPage] = useState(10);
  const [recordSearchQuery, setRecordSearchQuery] = useState('');
  const [recordTypeFilter, setRecordTypeFilter] = useState('all');

  // Form state - Create Zone
  const [newZone, setNewZone] = useState({
    domain: '',
    jump_start: true,
    priority: 'normal'
  });

  // Form state - Add/Edit DNS Record
  const [dnsRecord, setDnsRecord] = useState({
    type: 'A',
    name: '',
    content: '',
    ttl: 1,
    proxied: false,
    priority: 10
  });
  const [formErrors, setFormErrors] = useState({});

  // Notification state
  const [toast, setToast] = useState({ open: false, message: '', severity: 'info' });

  // Load zones and account info on mount
  useEffect(() => {
    fetchZones();
    fetchAccountInfo();
  }, []);

  // Load DNS records when zone detail view is opened
  useEffect(() => {
    if (selectedZone && zoneDetailView) {
      fetchDnsRecords(selectedZone.zone_id);
    }
  }, [selectedZone, zoneDetailView]);

  // API calls
  const fetchZones = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/v1/cloudflare/zones', {
        params: { limit: 100 }
      });
      setZones(response.data.zones || []);
    } catch (err) {
      showToast('Failed to load zones: ' + err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAccountInfo = async () => {
    try {
      const response = await axios.get('/api/v1/cloudflare/account/limits');
      setAccountInfo(response.data);
    } catch (err) {
      console.error('Failed to load account info:', err);
    }
  };

  const fetchDnsRecords = async (zoneId) => {
    try {
      setLoadingRecords(true);
      const response = await axios.get(`/api/v1/cloudflare/zones/${zoneId}/dns`, {
        params: { limit: 1000 }
      });
      setDnsRecords(response.data.records || []);
    } catch (err) {
      showToast('Failed to load DNS records: ' + err.message, 'error');
    } finally {
      setLoadingRecords(false);
    }
  };

  const handleCreateZone = async () => {
    if (!newZone.domain) {
      showToast('Please enter a domain name', 'error');
      return;
    }

    try {
      const response = await axios.post('/api/v1/cloudflare/zones', newZone);
      showToast(`Zone created: ${response.data.domain}`, 'success');
      setOpenCreateZone(false);
      setNewZone({ domain: '', jump_start: true, priority: 'normal' });
      fetchZones();
      fetchAccountInfo();
    } catch (err) {
      if (err.response?.status === 429) {
        showToast(`Zone queued: ${err.response.data.message}`, 'warning');
      } else {
        showToast(err.response?.data?.detail || 'Failed to create zone', 'error');
      }
    }
  };

  const handleDeleteZone = async () => {
    if (!deleteTarget) return;

    try {
      await axios.delete(`/api/v1/cloudflare/zones/${deleteTarget.zone_id}`);
      showToast(`Zone ${deleteTarget.domain} deleted`, 'success');
      setDeleteTarget(null);
      setOpenDeleteDialog(false);
      fetchZones();
      fetchAccountInfo();
      if (selectedZone?.zone_id === deleteTarget.zone_id) {
        setZoneDetailView(false);
        setSelectedZone(null);
      }
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete zone', 'error');
    }
  };

  const handleCheckStatus = async (zoneId) => {
    try {
      await axios.post(`/api/v1/cloudflare/zones/${zoneId}/check-status`);
      showToast('Status updated', 'success');
      fetchZones();
    } catch (err) {
      showToast('Failed to check status', 'error');
    }
  };

  const validateDnsRecord = () => {
    const errors = {};

    if (!dnsRecord.name) {
      errors.name = 'Name is required';
    }

    if (!dnsRecord.content) {
      errors.content = 'Content is required';
    }

    // Type-specific validation
    if (dnsRecord.type === 'A') {
      const ipv4Regex = /^(\d{1,3}\.){3}\d{1,3}$/;
      if (!ipv4Regex.test(dnsRecord.content)) {
        errors.content = 'Invalid IPv4 address';
      }
    } else if (dnsRecord.type === 'AAAA') {
      // Simple IPv6 check
      if (!dnsRecord.content.includes(':')) {
        errors.content = 'Invalid IPv6 address';
      }
    } else if (dnsRecord.type === 'MX' && (dnsRecord.priority < 0 || dnsRecord.priority > 65535)) {
      errors.priority = 'Priority must be between 0 and 65535';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAddDnsRecord = async () => {
    if (!validateDnsRecord()) {
      showToast('Please fix validation errors', 'error');
      return;
    }

    try {
      const payload = {
        type: dnsRecord.type,
        name: dnsRecord.name,
        content: dnsRecord.content,
        ttl: parseInt(dnsRecord.ttl),
        proxied: dnsRecord.proxied
      };

      if (dnsRecord.type === 'MX' || dnsRecord.type === 'SRV') {
        payload.priority = parseInt(dnsRecord.priority);
      }

      if (selectedRecord) {
        // Update existing record
        await axios.put(
          `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns/${selectedRecord.id}`,
          payload
        );
        showToast('DNS record updated', 'success');
      } else {
        // Create new record
        await axios.post(
          `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns`,
          payload
        );
        showToast('DNS record added', 'success');
      }

      setOpenAddRecord(false);
      resetDnsRecordForm();
      fetchDnsRecords(selectedZone.zone_id);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to save DNS record', 'error');
    }
  };

  const handleDeleteDnsRecord = async () => {
    if (!deleteTarget) return;

    // Check if email-related record
    const isEmailRecord = deleteTarget.type === 'MX' ||
      (deleteTarget.type === 'TXT' && (
        deleteTarget.content.includes('v=spf1') ||
        deleteTarget.content.includes('v=DMARC1') ||
        deleteTarget.name.includes('dkim')
      ));

    if (isEmailRecord) {
      showToast('Warning: This appears to be an email-related record', 'warning');
    }

    try {
      await axios.delete(
        `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns/${deleteTarget.id}`
      );
      showToast('DNS record deleted', 'success');
      setDeleteTarget(null);
      setOpenDeleteDialog(false);
      fetchDnsRecords(selectedZone.zone_id);
    } catch (err) {
      showToast(err.response?.data?.detail || 'Failed to delete DNS record', 'error');
    }
  };

  const handleToggleProxy = async (record) => {
    try {
      await axios.post(
        `/api/v1/cloudflare/zones/${selectedZone.zone_id}/dns/${record.id}/toggle-proxy`
      );
      showToast(`Proxy ${record.proxied ? 'disabled' : 'enabled'}`, 'success');
      fetchDnsRecords(selectedZone.zone_id);
    } catch (err) {
      showToast('Failed to toggle proxy', 'error');
    }
  };

  const handleCopyNameservers = (nameservers) => {
    if (!nameservers || nameservers.length === 0) return;
    const text = nameservers.join('\n');
    navigator.clipboard.writeText(text);
    showToast('Nameservers copied to clipboard', 'success');
  };

  const handleEditRecord = (record) => {
    setSelectedRecord(record);
    setDnsRecord({
      type: record.type,
      name: record.name.replace(`.${selectedZone.domain}`, '').replace(selectedZone.domain, '@'),
      content: record.content,
      ttl: record.ttl || 1,
      proxied: record.proxied || false,
      priority: record.priority || 10
    });
    setOpenAddRecord(true);
  };

  const resetDnsRecordForm = () => {
    setDnsRecord({
      type: 'A',
      name: '',
      content: '',
      ttl: 1,
      proxied: false,
      priority: 10
    });
    setSelectedRecord(null);
    setFormErrors({});
  };

  const openDeleteConfirmation = (target, isZone = false) => {
    setDeleteTarget({ ...target, isZone });
    setOpenDeleteDialog(true);
  };

  const showToast = (message, severity = 'info') => {
    setToast({ open: true, message, severity });
  };

  // Filter and paginate zones
  const filteredZones = zones.filter(zone => {
    const matchesSearch = !searchQuery ||
      zone.domain.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesStatus = statusFilter === 'all' ||
      zone.status.toLowerCase() === statusFilter.toLowerCase();

    return matchesSearch && matchesStatus;
  });

  const paginatedZones = filteredZones.slice(
    page * rowsPerPage,
    page * rowsPerPage + rowsPerPage
  );

  // Filter and paginate DNS records
  const filteredRecords = dnsRecords.filter(record => {
    const matchesSearch = !recordSearchQuery ||
      record.name.toLowerCase().includes(recordSearchQuery.toLowerCase()) ||
      record.content.toLowerCase().includes(recordSearchQuery.toLowerCase());

    const matchesType = recordTypeFilter === 'all' ||
      record.type.toLowerCase() === recordTypeFilter.toLowerCase();

    return matchesSearch && matchesType;
  });

  const paginatedRecords = filteredRecords.slice(
    recordPage * recordRowsPerPage,
    recordPage * recordRowsPerPage + recordRowsPerPage
  );

  // Loading state
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Zone Detail View
  if (zoneDetailView && selectedZone) {
    return (
      <>
        <ZoneDetailView
          zone={selectedZone}
          onBack={() => {
            setZoneDetailView(false);
            setSelectedZone(null);
            setActiveTab(0);
          }}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          dnsRecords={dnsRecords}
          loadingRecords={loadingRecords}
          onAddRecord={() => {
            resetDnsRecordForm();
            setOpenAddRecord(true);
          }}
          onEditRecord={handleEditRecord}
          onDeleteRecord={(record) => openDeleteConfirmation(record, false)}
          onToggleProxy={handleToggleProxy}
          recordSearchQuery={recordSearchQuery}
          setRecordSearchQuery={setRecordSearchQuery}
          recordTypeFilter={recordTypeFilter}
          setRecordTypeFilter={setRecordTypeFilter}
          recordPage={recordPage}
          setRecordPage={setRecordPage}
          recordRowsPerPage={recordRowsPerPage}
          setRecordRowsPerPage={setRecordRowsPerPage}
          filteredRecords={filteredRecords}
          paginatedRecords={paginatedRecords}
          onCheckStatus={handleCheckStatus}
          onDeleteZone={() => openDeleteConfirmation(selectedZone, true)}
          onCopyNameservers={handleCopyNameservers}
          currentTheme={currentTheme}
        />

        {/* Modals */}
        <AddEditRecordModal
          open={openAddRecord}
          onClose={() => {
            setOpenAddRecord(false);
            resetDnsRecordForm();
          }}
          dnsRecord={dnsRecord}
          setDnsRecord={setDnsRecord}
          formErrors={formErrors}
          selectedRecord={selectedRecord}
          selectedZone={selectedZone}
          onSubmit={handleAddDnsRecord}
        />

        <DeleteConfirmationModal
          open={openDeleteDialog}
          onClose={() => {
            setOpenDeleteDialog(false);
            setDeleteTarget(null);
          }}
          onConfirm={deleteTarget?.isZone ? handleDeleteZone : handleDeleteDnsRecord}
          deleteTarget={deleteTarget}
        />

        <Toast
          toast={toast}
          onClose={() => setToast({ ...toast, open: false })}
        />
      </>
    );
  }

  // Zone List View (Main Page)
  return (
    <>
      <ZoneListView
        accountInfo={accountInfo}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        statusFilter={statusFilter}
        setStatusFilter={setStatusFilter}
        page={page}
        setPage={setPage}
        rowsPerPage={rowsPerPage}
        setRowsPerPage={setRowsPerPage}
        paginatedZones={paginatedZones}
        filteredZones={filteredZones}
        onCreateZone={() => setOpenCreateZone(true)}
        onRefresh={() => {
          fetchZones();
          fetchAccountInfo();
        }}
        onSelectZone={(zone) => {
          setSelectedZone(zone);
          setZoneDetailView(true);
        }}
        onCheckStatus={handleCheckStatus}
        onDeleteZone={(zone) => openDeleteConfirmation(zone, true)}
        onCopyNameservers={handleCopyNameservers}
        currentTheme={currentTheme}
      />

      {/* Modals */}
      <CreateZoneModal
        open={openCreateZone}
        onClose={() => setOpenCreateZone(false)}
        newZone={newZone}
        setNewZone={setNewZone}
        accountInfo={accountInfo}
        onCreate={handleCreateZone}
      />

      <DeleteConfirmationModal
        open={openDeleteDialog}
        onClose={() => {
          setOpenDeleteDialog(false);
          setDeleteTarget(null);
        }}
        onConfirm={deleteTarget?.isZone ? handleDeleteZone : handleDeleteDnsRecord}
        deleteTarget={deleteTarget}
      />

      <Toast
        toast={toast}
        onClose={() => setToast({ ...toast, open: false })}
      />
    </>
  );
};

export default CloudflareDNS;
