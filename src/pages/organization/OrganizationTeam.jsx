import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  UsersIcon,
  UserPlusIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  TrashIcon,
  ShieldCheckIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon,
  EnvelopeIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

export default function OrganizationTeam() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg, loading: orgLoading } = useOrganization();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalMembers, setTotalMembers] = useState(0);

  // Modals
  const [inviteModalOpen, setInviteModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);

  // Form data
  const [inviteData, setInviteData] = useState({
    email: '',
    role: 'member',
    firstName: '',
    lastName: ''
  });

  // Toast notification
  const [toast, setToast] = useState({
    show: false,
    message: '',
    type: 'success'
  });

  // Stats
  const [stats, setStats] = useState({
    totalMembers: 0,
    activeMembers: 0,
    admins: 0,
    pendingInvites: 0
  });

  useEffect(() => {
    // Wait for OrganizationContext to finish loading
    if (orgLoading) {
      console.log('[OrganizationTeam] Waiting for organizations to load...');
      return;
    }

    if (currentOrg) {
      console.log('[OrganizationTeam] Loading members for org:', currentOrg.id);
      fetchMembers();
      fetchStats();
    } else {
      console.log('[OrganizationTeam] No current organization set');
      setLoading(false);
    }
  }, [currentOrg, orgLoading, page, rowsPerPage, searchQuery]);

  const fetchMembers = async () => {
    if (!currentOrg) return;

    setLoading(true);
    try {
      const offset = page * rowsPerPage;
      const params = new URLSearchParams({
        offset: offset.toString(),
        limit: rowsPerPage.toString(),
        search: searchQuery
      });

      const response = await fetch(`/api/v1/org/${currentOrg.id}/members?${params}`, {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch team members');

      const data = await response.json();
      setMembers(data.members || []);
      setTotalMembers(data.total || 0);
    } catch (error) {
      showToast('Failed to load team members', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    if (!currentOrg) return;

    try {
      const response = await fetch(`/api/v1/org/${currentOrg.id}/stats`, {
        credentials: 'include'
      });
      if (!response.ok) {
        // If stats endpoint doesn't exist, derive from members
        console.warn('Stats endpoint not available, deriving from members');
        return;
      }

      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
      // Derive basic stats from members if API fails
      if (members.length > 0) {
        setStats({
          totalMembers: members.length,
          activeMembers: members.filter(m => m.enabled).length,
          admins: members.filter(m => ['admin', 'owner'].includes(m.org_role)).length,
          pendingInvites: 0
        });
      }
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type }), 5000);
  };

  const handleInviteMember = async () => {
    if (!currentOrg) return;

    try {
      const response = await fetch(`/api/v1/org/${currentOrg.id}/members`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(inviteData)
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Failed to invite member');
      }

      showToast('Invitation sent successfully');
      setInviteModalOpen(false);
      setInviteData({ email: '', role: 'member', firstName: '', lastName: '' });
      fetchMembers();
      fetchStats();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  const handleUpdateRole = async (memberId, newRole) => {
    if (!currentOrg) return;

    try {
      const response = await fetch(`/api/v1/org/${currentOrg.id}/members/${memberId}/role`, {
        method: 'PUT',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ org_role: newRole })
      });

      if (!response.ok) throw new Error('Failed to update role');

      showToast('Member role updated successfully');
      fetchMembers();
      fetchStats();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  const handleRemoveMember = async () => {
    if (!currentOrg || !selectedMember) return;

    try {
      const response = await fetch(`/api/v1/org/${currentOrg.id}/members/${selectedMember.id}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (!response.ok) throw new Error('Failed to remove member');

      showToast('Member removed successfully');
      setDeleteModalOpen(false);
      setSelectedMember(null);
      fetchMembers();
      fetchStats();
    } catch (error) {
      showToast(error.message, 'error');
    }
  };

  const getRoleBadgeColor = (role) => {
    switch (role) {
      case 'owner':
        return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'admin':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'member':
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
      default:
        return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const getInitials = (member) => {
    const first = member.firstName?.[0] || '';
    const last = member.lastName?.[0] || '';
    return (first + last).toUpperCase() || member.email?.[0]?.toUpperCase() || '?';
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                <UsersIcon className="h-6 w-6 text-white" />
              </div>
              Team Members
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>Manage your organization's team members and roles</p>
          </div>
        </div>
      </motion.div>

      {/* Statistics Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-3xl font-bold ${theme.text.primary}`}>{stats.totalMembers}</div>
              <div className={`text-sm ${theme.text.secondary} mt-1`}>Total Members</div>
            </div>
            <UsersIcon className="h-10 w-10 text-blue-500 opacity-50" />
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-green-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-3xl font-bold ${theme.text.primary}`}>{stats.activeMembers}</div>
              <div className={`text-sm ${theme.text.secondary} mt-1`}>Active Members</div>
            </div>
            <CheckCircleIcon className="h-10 w-10 text-green-500 opacity-50" />
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-3xl font-bold ${theme.text.primary}`}>{stats.admins}</div>
              <div className={`text-sm ${theme.text.secondary} mt-1`}>Administrators</div>
            </div>
            <ShieldCheckIcon className="h-10 w-10 text-purple-500 opacity-50" />
          </div>
        </div>

        <div className={`${theme.card} rounded-xl p-6 border border-yellow-500/20`}>
          <div className="flex items-center justify-between">
            <div>
              <div className={`text-3xl font-bold ${theme.text.primary}`}>{stats.pendingInvites}</div>
              <div className={`text-sm ${theme.text.secondary} mt-1`}>Pending Invites</div>
            </div>
            <ClockIcon className="h-10 w-10 text-yellow-500 opacity-50" />
          </div>
        </div>
      </motion.div>

      {/* Main Content */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        {/* Toolbar */}
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or email..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                fetchMembers();
                fetchStats();
              }}
              className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
            >
              <ArrowPathIcon className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={() => setInviteModalOpen(true)}
              className={`flex items-center gap-2 px-4 py-2 ${theme.button} rounded-lg transition-colors`}
            >
              <UserPlusIcon className="h-4 w-4" />
              Invite Member
            </button>
          </div>
        </div>

        {/* Members Table */}
        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          </div>
        ) : members.length === 0 ? (
          <div className="text-center py-12">
            <UsersIcon className="h-16 w-16 mx-auto text-gray-500 mb-4" />
            <p className={`${theme.text.secondary}`}>No team members found</p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className={`border-b ${currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'}`}>
                    <th className={`text-left py-3 px-4 ${theme.text.secondary} font-semibold`}>Member</th>
                    <th className={`text-left py-3 px-4 ${theme.text.secondary} font-semibold`}>Email</th>
                    <th className={`text-left py-3 px-4 ${theme.text.secondary} font-semibold`}>Role</th>
                    <th className={`text-left py-3 px-4 ${theme.text.secondary} font-semibold`}>Status</th>
                    <th className={`text-left py-3 px-4 ${theme.text.secondary} font-semibold`}>Joined</th>
                    <th className={`text-right py-3 px-4 ${theme.text.secondary} font-semibold`}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {members.map((member) => (
                    <tr
                      key={member.id}
                      className={`border-b ${currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'} hover:bg-gray-700/20 transition-colors`}
                    >
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold">
                            {getInitials(member)}
                          </div>
                          <div>
                            <div className={`font-medium ${theme.text.primary}`}>
                              {member.firstName} {member.lastName}
                            </div>
                            <div className={`text-xs ${theme.text.secondary}`}>
                              {member.username}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className={`py-4 px-4 ${theme.text.primary}`}>
                        <div className="flex items-center gap-2">
                          <EnvelopeIcon className="h-4 w-4 text-gray-400" />
                          {member.email}
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <select
                          value={member.org_role}
                          onChange={(e) => handleUpdateRole(member.id, e.target.value)}
                          disabled={member.org_role === 'owner'}
                          className={`px-3 py-1 rounded-lg border text-sm font-medium ${getRoleBadgeColor(member.org_role)} ${member.org_role === 'owner' ? 'cursor-not-allowed' : 'cursor-pointer'}`}
                        >
                          <option value="member">Member</option>
                          <option value="admin">Admin</option>
                          <option value="owner">Owner</option>
                        </select>
                      </td>
                      <td className="py-4 px-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          member.enabled
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                            : 'bg-red-500/20 text-red-400 border border-red-500/30'
                        }`}>
                          {member.enabled ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className={`py-4 px-4 ${theme.text.secondary} text-sm`}>
                        {member.createdAt ? new Date(member.createdAt).toLocaleDateString() : 'N/A'}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setSelectedMember(member);
                              setDeleteModalOpen(true);
                            }}
                            disabled={member.org_role === 'owner'}
                            className={`p-2 rounded-lg transition-colors ${
                              member.org_role === 'owner'
                                ? 'text-gray-500 cursor-not-allowed'
                                : 'text-red-400 hover:bg-red-500/20'
                            }`}
                            title={member.org_role === 'owner' ? 'Cannot remove owner' : 'Remove member'}
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between mt-6">
              <div className={`text-sm ${theme.text.secondary}`}>
                Showing {page * rowsPerPage + 1} to {Math.min((page + 1) * rowsPerPage, totalMembers)} of {totalMembers} members
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    page === 0
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-700 hover:bg-gray-600 text-white'
                  }`}
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={(page + 1) * rowsPerPage >= totalMembers}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    (page + 1) * rowsPerPage >= totalMembers
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-gray-700 hover:bg-gray-600 text-white'
                  }`}
                >
                  Next
                </button>
              </div>
            </div>
          </>
        )}
      </motion.div>

      {/* Invite Member Modal */}
      {inviteModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setInviteModalOpen(false)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`${theme.card} rounded-xl p-6 max-w-md w-full m-4`}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className={`text-xl font-semibold ${theme.text.primary} mb-4`}>Invite Team Member</h3>
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Email *</label>
                <input
                  type="email"
                  value={inviteData.email}
                  onChange={(e) => setInviteData({ ...inviteData, email: e.target.value })}
                  className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  placeholder="member@example.com"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>First Name</label>
                  <input
                    type="text"
                    value={inviteData.firstName}
                    onChange={(e) => setInviteData({ ...inviteData, firstName: e.target.value })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Last Name</label>
                  <input
                    type="text"
                    value={inviteData.lastName}
                    onChange={(e) => setInviteData({ ...inviteData, lastName: e.target.value })}
                    className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                  />
                </div>
              </div>
              <div>
                <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>Role *</label>
                <select
                  value={inviteData.role}
                  onChange={(e) => setInviteData({ ...inviteData, role: e.target.value })}
                  className={`w-full px-4 py-2 ${theme.card} border ${currentTheme === 'light' ? 'border-gray-300' : 'border-gray-600'} rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500`}
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setInviteModalOpen(false)}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleInviteMember}
                disabled={!inviteData.email}
                className={`flex-1 px-4 py-2 ${theme.button} rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                Send Invitation
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalOpen && selectedMember && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={() => setDeleteModalOpen(false)}>
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className={`${theme.card} rounded-xl p-6 max-w-md w-full m-4`}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />
              </div>
              <h3 className={`text-xl font-semibold ${theme.text.primary}`}>Remove Member</h3>
            </div>
            <p className={`${theme.text.secondary} mb-6`}>
              Are you sure you want to remove <strong className={theme.text.primary}>{selectedMember.firstName} {selectedMember.lastName}</strong> from your organization? This action cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setDeleteModalOpen(false)}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleRemoveMember}
                className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Remove
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Toast Notification */}
      {toast.show && (
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 50 }}
          className="fixed bottom-4 right-4 z-50"
        >
          <div className={`flex items-center gap-3 px-6 py-4 rounded-lg shadow-lg ${
            toast.type === 'success'
              ? 'bg-green-500/20 border border-green-500/30 text-green-400'
              : 'bg-red-500/20 border border-red-500/30 text-red-400'
          }`}>
            {toast.type === 'success' ? (
              <CheckCircleIcon className="h-5 w-5" />
            ) : (
              <XMarkIcon className="h-5 w-5" />
            )}
            <span>{toast.message}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
