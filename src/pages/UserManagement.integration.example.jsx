/**
 * UserManagement.jsx Integration Example
 *
 * This file shows the exact changes needed to add bulk operations
 * to the existing UserManagement component.
 *
 * DO NOT use this file directly - copy the code snippets into UserManagement.jsx
 */

import React, { useState, useEffect } from 'react';
// ... existing imports
import BulkActionsToolbar from '../components/BulkActionsToolbar';
import ImportCSVModal from '../components/ImportCSVModal';
import {
  Upload as UploadIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';

// ===== ADD THESE STATE VARIABLES =====
const UserManagement = () => {
  // ... existing state variables

  // ADD: Multi-select state
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [importModalOpen, setImportModalOpen] = useState(false);

  // ===== ADD THESE HANDLERS =====

  // Handle individual user selection
  const handleSelectUser = (userId, checked) => {
    if (checked) {
      setSelectedUsers([...selectedUsers, userId]);
    } else {
      setSelectedUsers(selectedUsers.filter(id => id !== userId));
    }
  };

  // Handle select all
  const handleSelectAll = () => {
    if (selectAll) {
      setSelectedUsers([]);
      setSelectAll(false);
    } else {
      setSelectedUsers(users.map(u => u.user_id || u.id));
      setSelectAll(true);
    }
  };

  // Clear selection
  const handleClearSelection = () => {
    setSelectedUsers([]);
    setSelectAll(false);
  };

  // Bulk delete handler
  const handleBulkDelete = async (userIds, reason) => {
    try {
      const response = await fetch('/api/v1/admin/users/bulk/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_ids: userIds, reason }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Bulk delete failed');

      const results = await response.json();
      showToast(`Deleted ${results.deleted} users successfully`, 'success');
      fetchUsers();
      fetchStats();
      handleClearSelection();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  // Bulk suspend handler
  const handleBulkSuspend = async (userIds, reason) => {
    try {
      const response = await fetch('/api/v1/admin/users/bulk/suspend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_ids: userIds, reason }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Bulk suspend failed');

      const results = await response.json();
      showToast(`Suspended ${results.suspended} users successfully`, 'success');
      fetchUsers();
      fetchStats();
      handleClearSelection();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  // Bulk assign roles handler
  const handleBulkAssignRoles = async (userIds, roles) => {
    try {
      const response = await fetch('/api/v1/admin/users/bulk/assign-roles', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_ids: userIds, roles }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Bulk role assignment failed');

      const results = await response.json();
      showToast(`Assigned roles to ${results.updated} users successfully`, 'success');
      fetchUsers();
      handleClearSelection();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  // Bulk change tier handler
  const handleBulkChangeTier = async (userIds, tier, reason) => {
    try {
      const response = await fetch('/api/v1/admin/users/bulk/set-tier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_ids: userIds, tier, reason }),
        credentials: 'include',
      });

      if (!response.ok) throw new Error('Bulk tier change failed');

      const results = await response.json();
      showToast(`Changed tier for ${results.updated} users successfully`, 'success');
      fetchUsers();
      fetchStats();
      handleClearSelection();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  // Export CSV handler
  const handleExportCSV = () => {
    // Build query params from current filters
    const params = new URLSearchParams();
    if (searchQuery) params.append('search', searchQuery);
    if (filters.tiers.length > 0) params.append('tier', filters.tiers.join(','));
    if (filters.statuses.length > 0) params.append('status', filters.statuses.join(','));

    // Trigger download
    window.location.href = `/api/v1/admin/users/export?${params}`;
    showToast('CSV export started', 'success');
  };

  // ===== ADD TO JSX (AFTER STATISTICS CARDS, BEFORE USER TABLE) =====
  return (
    <Box sx={{ p: 3 }}>
      {/* ... existing Statistics Cards ... */}

      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h5" fontWeight="bold">
            User Management
          </Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            {/* ADD: Import/Export Buttons */}
            <Button
              variant="outlined"
              startIcon={<UploadIcon />}
              onClick={() => setImportModalOpen(true)}
            >
              Import CSV
            </Button>
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleExportCSV}
            >
              Export CSV
            </Button>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={handleCreateUser}
              sx={{
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
                },
              }}
            >
              Create User
            </Button>
          </Box>
        </Box>

        {/* ... existing Filters ... */}

        {/* ADD: Bulk Actions Toolbar (shows when users are selected) */}
        {selectedUsers.length > 0 && (
          <BulkActionsToolbar
            selectedCount={selectedUsers.length}
            selectedUsers={selectedUsers}
            onClearSelection={handleClearSelection}
            onBulkDelete={handleBulkDelete}
            onBulkSuspend={handleBulkSuspend}
            onBulkAssignRoles={handleBulkAssignRoles}
            onBulkChangeTier={handleBulkChangeTier}
            availableRoles={availableRoles}
          />
        )}

        {/* User Table */}
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                {/* ADD: Checkbox column header */}
                <TableCell padding="checkbox">
                  <Checkbox
                    checked={selectAll}
                    indeterminate={selectedUsers.length > 0 && selectedUsers.length < users.length}
                    onChange={handleSelectAll}
                  />
                </TableCell>
                <TableCell>Avatar</TableCell>
                <TableCell>Name</TableCell>
                {/* ... existing columns ... */}
              </TableRow>
            </TableHead>
            <TableBody>
              {users.map((user) => (
                <TableRow key={user.id} hover>
                  {/* ADD: Checkbox column */}
                  <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                    <Checkbox
                      checked={selectedUsers.includes(user.user_id || user.id)}
                      onChange={(e) => handleSelectUser(user.user_id || user.id, e.target.checked)}
                    />
                  </TableCell>
                  {/* ... existing columns ... */}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
        {/* ... existing pagination ... */}
      </Paper>

      {/* ADD: Import CSV Modal */}
      <ImportCSVModal
        open={importModalOpen}
        onClose={() => setImportModalOpen(false)}
        onImportComplete={(results) => {
          showToast(`Imported ${results.created} users successfully`, 'success');
          fetchUsers();
          fetchStats();
        }}
      />

      {/* ... existing modals ... */}
    </Box>
  );
};

export default UserManagement;
