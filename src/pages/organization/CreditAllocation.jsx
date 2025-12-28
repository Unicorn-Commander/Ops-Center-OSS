/**
 * CreditAllocation.jsx - Credit Allocation Manager
 *
 * Manage credit allocations to organization members.
 * Features: List members, allocate credits, revoke, adjust, bulk actions.
 *
 * API: POST /api/v1/org-billing/credits/{org_id}/allocate
 * Created: November 15, 2025
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  UserGroupIcon,
  ArrowPathIcon,
  PlusIcon,
  PencilIcon,
  TrashIcon,
  CheckCircleIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  ArrowsUpDownIcon
} from '@heroicons/react/24/outline';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.03 }
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

export default function CreditAllocation() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg } = useOrganization();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [members, setMembers] = useState([]);
  const [allocations, setAllocations] = useState([]);
  const [creditPool, setCreditPool] = useState(null);
  const [error, setError] = useState(null);

  // UI state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all'); // all, allocated, not-allocated, low
  const [sortBy, setSortBy] = useState('name'); // name, allocated, used, remaining
  const [sortOrder, setSortOrder] = useState('asc');
  const [selectedMembers, setSelectedMembers] = useState([]);

  // Modals
  const [showAllocateModal, setShowAllocateModal] = useState(false);
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [currentMember, setCurrentMember] = useState(null);
  const [allocationAmount, setAllocationAmount] = useState('');
  const [bulkAmount, setBulkAmount] = useState('');

  // Toast
  const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

  useEffect(() => {
    if (currentOrg) {
      loadData();
    }
  }, [currentOrg]);

  const loadData = async () => {
    if (!currentOrg) return;

    try {
      setLoading(true);
      setError(null);

      const [membersRes, allocationsRes, poolRes] = await Promise.all([
        fetch(`/api/v1/org/org/${currentOrg.id}/members`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch(`/api/v1/org-billing/credits/${currentOrg.id}/allocations`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        }),
        fetch(`/api/v1/org-billing/credits/${currentOrg.id}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
        })
      ]);

      if (!membersRes.ok) throw new Error('Failed to load members');

      const membersData = await membersRes.json();
      const allocationsData = allocationsRes.ok ? await allocationsRes.json() : [];
      const poolData = poolRes.ok ? await poolRes.json() : null;

      setMembers(membersData);
      setAllocations(allocationsData);
      setCreditPool(poolData?.credit_pool);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type }), 5000);
  };

  const formatCredits = (amount) => {
    if (amount === null || amount === undefined) return '0';
    return Math.floor(parseFloat(amount)).toLocaleString();
  };

  const getAllocation = (userId) => {
    return allocations.find(a => a.user_id === userId);
  };

  const handleAllocate = async () => {
    if (!currentMember || !allocationAmount) return;

    try {
      const response = await fetch(
        `/api/v1/org-billing/credits/${currentOrg.id}/allocate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({
            user_id: currentMember.user_id,
            credits: parseInt(allocationAmount)
          })
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to allocate credits');
      }

      showToast(`Successfully allocated ${formatCredits(allocationAmount)} credits to ${currentMember.user_email}`, 'success');
      setShowAllocateModal(false);
      setCurrentMember(null);
      setAllocationAmount('');
      await loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleRevoke = async (userId, userEmail) => {
    if (!confirm(`Revoke all credit allocations from ${userEmail}?`)) return;

    try {
      const response = await fetch(
        `/api/v1/org-billing/credits/${currentOrg.id}/allocate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({
            user_id: userId,
            credits: 0
          })
        }
      );

      if (!response.ok) throw new Error('Failed to revoke credits');

      showToast(`Successfully revoked credits from ${userEmail}`, 'success');
      await loadData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  const handleBulkAllocate = async () => {
    if (selectedMembers.length === 0 || !bulkAmount) return;

    try {
      const promises = selectedMembers.map(memberId => {
        const member = members.find(m => m.user_id === memberId);
        return fetch(
          `/api/v1/org-billing/credits/${currentOrg.id}/allocate`,
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: JSON.stringify({
              user_id: memberId,
              credits: parseInt(bulkAmount)
            })
          }
        );
      });

      await Promise.all(promises);

      showToast(`Successfully allocated ${formatCredits(bulkAmount)} credits to ${selectedMembers.length} members`, 'success');
      setShowBulkModal(false);
      setSelectedMembers([]);
      setBulkAmount('');
      await loadData();
    } catch (err) {
      showToast('Failed to allocate credits to some members', 'error');
    }
  };

  const toggleMemberSelection = (userId) => {
    setSelectedMembers(prev =>
      prev.includes(userId)
        ? prev.filter(id => id !== userId)
        : [...prev, userId]
    );
  };

  const toggleAllMembers = () => {
    if (selectedMembers.length === filteredMembers.length) {
      setSelectedMembers([]);
    } else {
      setSelectedMembers(filteredMembers.map(m => m.user_id));
    }
  };

  // Filter and sort members
  const filteredMembers = members
    .filter(member => {
      const allocation = getAllocation(member.user_id);
      const matchesSearch = member.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                           member.user_name?.toLowerCase().includes(searchQuery.toLowerCase());

      if (!matchesSearch) return false;

      switch (filterStatus) {
        case 'allocated':
          return allocation && allocation.credits_allocated > 0;
        case 'not-allocated':
          return !allocation || allocation.credits_allocated === 0;
        case 'low':
          return allocation && (allocation.credits_allocated - allocation.credits_used) < 1000;
        default:
          return true;
      }
    })
    .sort((a, b) => {
      const allocA = getAllocation(a.user_id);
      const allocB = getAllocation(b.user_id);

      let compareValue = 0;
      switch (sortBy) {
        case 'name':
          compareValue = (a.user_email || '').localeCompare(b.user_email || '');
          break;
        case 'allocated':
          compareValue = (allocA?.credits_allocated || 0) - (allocB?.credits_allocated || 0);
          break;
        case 'used':
          compareValue = (allocA?.credits_used || 0) - (allocB?.credits_used || 0);
          break;
        case 'remaining':
          const remainingA = (allocA?.credits_allocated || 0) - (allocA?.credits_used || 0);
          const remainingB = (allocB?.credits_allocated || 0) - (allocB?.credits_used || 0);
          compareValue = remainingA - remainingB;
          break;
      }

      return sortOrder === 'asc' ? compareValue : -compareValue;
    });

  const availableCredits = creditPool ? (creditPool.total_credits - creditPool.credits_allocated) : 0;

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <ArrowPathIcon className="h-12 w-12 animate-spin mx-auto mb-4 text-purple-500" />
          <p className="text-gray-400">Loading allocations...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: currentTheme.text }}>
            Credit Allocation
          </h1>
          <p className="text-sm mt-1" style={{ color: currentTheme.textSecondary }}>
            Manage credit allocations for {members.length} organization members
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 rounded-lg border border-purple-500 text-purple-400 hover:bg-purple-500/10 disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={() => navigate('/admin/organization/credits')}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {/* Credit Pool Status */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="mb-6 grid grid-cols-1 md:grid-cols-3 gap-4"
      >
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <div className="text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
            Available to Allocate
          </div>
          <div className="text-3xl font-bold text-green-400">
            {formatCredits(availableCredits)}
          </div>
        </motion.div>

        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <div className="text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
            Total Allocated
          </div>
          <div className="text-3xl font-bold text-yellow-400">
            {formatCredits(creditPool?.credits_allocated || 0)}
          </div>
        </motion.div>

        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <div className="text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
            Members with Allocations
          </div>
          <div className="text-3xl font-bold text-purple-400">
            {allocations.filter(a => a.credits_allocated > 0).length}
          </div>
        </motion.div>
      </motion.div>

      {/* Filters and Actions */}
      <motion.div
        variants={itemVariants}
        className="mb-6 rounded-xl p-4 border"
        style={{
          background: currentTheme.cardBackground,
          borderColor: currentTheme.border
        }}
      >
        <div className="flex flex-col md:flex-row items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search members..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
              style={{ color: currentTheme.text }}
            />
          </div>

          {/* Filter */}
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
            style={{ color: currentTheme.text }}
          >
            <option value="all">All Members</option>
            <option value="allocated">With Allocations</option>
            <option value="not-allocated">No Allocations</option>
            <option value="low">Low Balance (&lt; 1000)</option>
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
            style={{ color: currentTheme.text }}
          >
            <option value="name">Sort by Name</option>
            <option value="allocated">Sort by Allocated</option>
            <option value="used">Sort by Used</option>
            <option value="remaining">Sort by Remaining</option>
          </select>

          <button
            onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
            className="p-2 rounded-lg border border-purple-500 text-purple-400 hover:bg-purple-500/10"
          >
            <ArrowsUpDownIcon className="h-5 w-5" />
          </button>

          {/* Bulk Actions */}
          {selectedMembers.length > 0 && (
            <button
              onClick={() => setShowBulkModal(true)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2"
            >
              <PlusIcon className="h-5 w-5" />
              Bulk Allocate ({selectedMembers.length})
            </button>
          )}
        </div>
      </motion.div>

      {/* Members Table */}
      <motion.div
        variants={itemVariants}
        className="rounded-xl border overflow-hidden"
        style={{
          background: currentTheme.cardBackground,
          borderColor: currentTheme.border
        }}
      >
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead style={{ background: 'rgba(168, 85, 247, 0.1)' }}>
              <tr>
                <th className="text-left py-3 px-4">
                  <input
                    type="checkbox"
                    checked={selectedMembers.length === filteredMembers.length && filteredMembers.length > 0}
                    onChange={toggleAllMembers}
                    className="rounded"
                  />
                </th>
                <th className="text-left py-3 px-4" style={{ color: currentTheme.text }}>
                  Member
                </th>
                <th className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                  Allocated
                </th>
                <th className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                  Used
                </th>
                <th className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                  Remaining
                </th>
                <th className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                  Usage %
                </th>
                <th className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredMembers.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center py-8" style={{ color: currentTheme.textSecondary }}>
                    No members found
                  </td>
                </tr>
              ) : (
                filteredMembers.map((member) => {
                  const allocation = getAllocation(member.user_id);
                  const allocated = allocation?.credits_allocated || 0;
                  const used = allocation?.credits_used || 0;
                  const remaining = allocated - used;
                  const usagePercent = allocated > 0 ? (used / allocated) * 100 : 0;
                  const isSelected = selectedMembers.includes(member.user_id);

                  return (
                    <tr
                      key={member.user_id}
                      className="border-b hover:bg-white/5 transition-colors"
                      style={{ borderColor: currentTheme.border }}
                    >
                      <td className="py-3 px-4">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleMemberSelection(member.user_id)}
                          className="rounded"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                            {member.user_email?.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="font-medium" style={{ color: currentTheme.text }}>
                              {member.user_email}
                            </div>
                            <div className="text-xs" style={{ color: currentTheme.textSecondary }}>
                              {member.user_name || 'No name'}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                        {formatCredits(allocated)}
                      </td>
                      <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                        {formatCredits(used)}
                      </td>
                      <td className="text-right py-3 px-4">
                        <span className={remaining < 1000 ? 'text-red-400' : ''} style={{ color: remaining >= 1000 ? currentTheme.text : undefined }}>
                          {formatCredits(remaining)}
                        </span>
                      </td>
                      <td className="text-right py-3 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <span className={`text-sm font-semibold ${usagePercent >= 90 ? 'text-red-400' : usagePercent >= 75 ? 'text-yellow-400' : 'text-green-400'}`}>
                            {usagePercent.toFixed(0)}%
                          </span>
                          <div className="w-20 bg-gray-700 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${usagePercent >= 90 ? 'bg-red-500' : usagePercent >= 75 ? 'bg-yellow-500' : 'bg-green-500'}`}
                              style={{ width: `${Math.min(usagePercent, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="text-right py-3 px-4">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => {
                              setCurrentMember(member);
                              setAllocationAmount(allocated.toString());
                              setShowAllocateModal(true);
                            }}
                            className="p-2 rounded-lg text-purple-400 hover:bg-purple-500/10"
                            title="Allocate/Adjust"
                          >
                            <PencilIcon className="h-4 w-4" />
                          </button>
                          {allocated > 0 && (
                            <button
                              onClick={() => handleRevoke(member.user_id, member.user_email)}
                              className="p-2 rounded-lg text-red-400 hover:bg-red-500/10"
                              title="Revoke All"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Allocate Modal */}
      {showAllocateModal && currentMember && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-gray-900 rounded-xl p-6 max-w-md w-full mx-4 border border-purple-500/30"
          >
            <h3 className="text-xl font-bold mb-4" style={{ color: currentTheme.text }}>
              Allocate Credits
            </h3>
            <p className="text-sm mb-4" style={{ color: currentTheme.textSecondary }}>
              Allocating to: <span className="font-semibold">{currentMember.user_email}</span>
            </p>
            <div className="mb-4">
              <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Credit Amount
              </label>
              <input
                type="number"
                value={allocationAmount}
                onChange={(e) => setAllocationAmount(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                style={{ color: currentTheme.text }}
                placeholder="Enter amount"
                min="0"
              />
              <p className="text-xs mt-2" style={{ color: currentTheme.textSecondary }}>
                Available: {formatCredits(availableCredits)} credits
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  setShowAllocateModal(false);
                  setCurrentMember(null);
                  setAllocationAmount('');
                }}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={handleAllocate}
                disabled={!allocationAmount || parseInt(allocationAmount) < 0}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
              >
                Allocate
              </button>
            </div>
          </motion.div>
        </div>
      )}

      {/* Bulk Allocate Modal */}
      {showBulkModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="bg-gray-900 rounded-xl p-6 max-w-md w-full mx-4 border border-purple-500/30"
          >
            <h3 className="text-xl font-bold mb-4" style={{ color: currentTheme.text }}>
              Bulk Allocate Credits
            </h3>
            <p className="text-sm mb-4" style={{ color: currentTheme.textSecondary }}>
              Allocating to {selectedMembers.length} selected members
            </p>
            <div className="mb-4">
              <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Credit Amount (per member)
              </label>
              <input
                type="number"
                value={bulkAmount}
                onChange={(e) => setBulkAmount(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                style={{ color: currentTheme.text }}
                placeholder="Enter amount"
                min="0"
              />
              <p className="text-xs mt-2" style={{ color: currentTheme.textSecondary }}>
                Total needed: {formatCredits(parseInt(bulkAmount || 0) * selectedMembers.length)} credits
              </p>
              <p className="text-xs" style={{ color: currentTheme.textSecondary }}>
                Available: {formatCredits(availableCredits)} credits
              </p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => {
                  setShowBulkModal(false);
                  setBulkAmount('');
                }}
                className="flex-1 px-4 py-2 bg-gray-700 text-white rounded-lg hover:bg-gray-600"
              >
                Cancel
              </button>
              <button
                onClick={handleBulkAllocate}
                disabled={!bulkAmount || parseInt(bulkAmount) < 0}
                className="flex-1 px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:opacity-50"
              >
                Allocate All
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
          className={`fixed bottom-6 right-6 px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 ${
            toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'
          } text-white z-50`}
        >
          {toast.type === 'success' ? (
            <CheckCircleIcon className="h-6 w-6" />
          ) : (
            <ExclamationTriangleIcon className="h-6 w-6" />
          )}
          <span>{toast.message}</span>
        </motion.div>
      )}
    </div>
  );
}
