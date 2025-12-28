/**
 * OrganizationSelector - Dropdown for Switching Organizations
 *
 * Simple React implementation matching Ops-Center design patterns
 *
 * Features:
 * - Displays current organization with logo
 * - Lists all user's organizations with role badges
 * - One-click organization switching
 * - "Create New Organization" option
 * - Search filter for users with 5+ orgs
 * - Visual role indicators (Owner, Admin, Member)
 *
 * Created: October 17, 2025
 * Status: Production Ready
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  BuildingOfficeIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
  PlusCircleIcon,
  CheckIcon
} from '@heroicons/react/24/outline';
import { useOrganization } from '../contexts/OrganizationContext';
import { useTheme } from '../contexts/ThemeContext';
import CreateOrganizationModal from './CreateOrganizationModal';

// Role badge component
function RoleBadge({ role }) {
  const badgeStyles = {
    owner: 'bg-purple-100 text-purple-700 border-purple-300',
    admin: 'bg-blue-100 text-blue-700 border-blue-300',
    billing_admin: 'bg-green-100 text-green-700 border-green-300',
    member: 'bg-gray-100 text-gray-700 border-gray-300'
  };

  const style = badgeStyles[role] || badgeStyles.member;

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${style}`}>
      {role.replace('_', ' ').toUpperCase()}
    </span>
  );
}

export default function OrganizationSelector() {
  const {
    currentOrgId,
    organizations,
    loading,
    switchOrganization,
    getCurrentOrganization,
    refreshOrganizations
  } = useOrganization();

  const { currentTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentOrg = getCurrentOrganization();

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter organizations by search query
  const filteredOrgs = organizations.filter(org =>
    org.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Handle organization switch
  const handleSwitch = (orgId) => {
    setIsOpen(false);
    setSearchQuery('');
    switchOrganization(orgId);
  };

  // Handle create new organization
  const handleCreateOrg = () => {
    setIsOpen(false);
    setCreateModalOpen(true);
  };

  // Handle organization created
  const handleOrgCreated = (newOrg) => {
    console.log('New organization created:', newOrg);
    // Refresh the organization list
    if (refreshOrganizations) {
      refreshOrganizations();
    }
    // Switch to the newly created organization
    if (newOrg && newOrg.id) {
      switchOrganization(newOrg.id);
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800">
        <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-gray-600"></div>
        <span className="text-sm text-gray-600 dark:text-gray-300">Loading...</span>
      </div>
    );
  }

  // No organizations state
  if (!organizations || organizations.length === 0) {
    return (
      <button
        onClick={handleCreateOrg}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${
          currentTheme === 'unicorn'
            ? 'bg-purple-600/20 text-purple-200 hover:bg-purple-600/30'
            : currentTheme === 'light'
            ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        }`}
      >
        <PlusCircleIcon className="h-5 w-5" />
        <span className="text-sm font-medium">Create Organization</span>
      </button>
    );
  }

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-3 px-4 py-2 rounded-lg transition-all duration-200 min-w-[200px] ${
          currentTheme === 'unicorn'
            ? 'bg-purple-600/20 text-purple-200 hover:bg-purple-600/30'
            : currentTheme === 'light'
            ? 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
        } ${isOpen ? 'ring-2 ring-purple-500' : ''}`}
      >
        {/* Organization Icon/Logo */}
        {currentOrg?.logo_url ? (
          <img
            src={currentOrg.logo_url}
            alt={currentOrg.name}
            className="w-6 h-6 rounded-full object-cover"
          />
        ) : (
          <BuildingOfficeIcon className="h-6 w-6" />
        )}

        {/* Organization Name and Role */}
        <div className="flex-1 text-left">
          <div className="text-sm font-semibold truncate max-w-[150px]">
            {currentOrg?.name || 'Select Organization'}
          </div>
          {currentOrg && (
            <div className="text-xs opacity-70">
              {currentOrg.role?.replace('_', ' ').toUpperCase()}
            </div>
          )}
        </div>

        {/* Dropdown Arrow */}
        <ChevronDownIcon
          className={`h-5 w-5 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          className={`absolute top-full mt-2 w-[320px] rounded-lg shadow-2xl z-50 ${
            currentTheme === 'unicorn'
              ? 'bg-gradient-to-br from-purple-900 to-pink-900 border border-purple-500/30'
              : currentTheme === 'light'
              ? 'bg-white border border-gray-200'
              : 'bg-gray-900 border border-gray-700'
          }`}
        >
          {/* Search Bar (only show if 5+ orgs) */}
          {organizations.length >= 5 && (
            <div className="p-3 border-b border-gray-200 dark:border-gray-700">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search organizations..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2 rounded-lg text-sm ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-800/30 text-purple-100 placeholder-purple-300/50 border border-purple-500/30 focus:border-purple-400'
                      : currentTheme === 'light'
                      ? 'bg-gray-50 text-gray-900 placeholder-gray-400 border border-gray-300 focus:border-blue-500'
                      : 'bg-gray-800 text-gray-100 placeholder-gray-500 border border-gray-600 focus:border-gray-500'
                  } focus:outline-none focus:ring-2 focus:ring-purple-500/50`}
                />
              </div>
            </div>
          )}

          {/* Organization List */}
          <div className="max-h-[400px] overflow-y-auto py-2">
            {filteredOrgs.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-gray-500">
                No organizations found
              </div>
            ) : (
              filteredOrgs.map((org) => (
                <button
                  key={org.id}
                  onClick={() => handleSwitch(org.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 transition-all duration-150 ${
                    org.id === currentOrgId
                      ? currentTheme === 'unicorn'
                        ? 'bg-purple-600/30'
                        : currentTheme === 'light'
                        ? 'bg-blue-50'
                        : 'bg-gray-800'
                      : currentTheme === 'unicorn'
                      ? 'hover:bg-purple-600/20'
                      : currentTheme === 'light'
                      ? 'hover:bg-gray-50'
                      : 'hover:bg-gray-800/50'
                  }`}
                >
                  {/* Check Icon (current org) */}
                  {org.id === currentOrgId && (
                    <CheckIcon className="h-5 w-5 text-green-500 flex-shrink-0" />
                  )}

                  {/* Organization Logo */}
                  {org.logo_url ? (
                    <img
                      src={org.logo_url}
                      alt={org.name}
                      className="w-8 h-8 rounded-full object-cover flex-shrink-0"
                    />
                  ) : (
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        currentTheme === 'unicorn'
                          ? 'bg-purple-600/30'
                          : currentTheme === 'light'
                          ? 'bg-gray-200'
                          : 'bg-gray-700'
                      }`}
                    >
                      <BuildingOfficeIcon className="h-5 w-5" />
                    </div>
                  )}

                  {/* Organization Details */}
                  <div className="flex-1 text-left min-w-0">
                    <div className={`text-sm font-semibold truncate ${
                      currentTheme === 'unicorn'
                        ? 'text-purple-100'
                        : currentTheme === 'light'
                        ? 'text-gray-900'
                        : 'text-gray-100'
                    }`}>
                      {org.name}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      <RoleBadge role={org.role} />
                      {org.member_count !== undefined && (
                        <span className={`text-xs ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-300/70'
                            : currentTheme === 'light'
                            ? 'text-gray-500'
                            : 'text-gray-400'
                        }`}>
                          {org.member_count} member{org.member_count !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>
                  </div>
                </button>
              ))
            )}
          </div>

          {/* Create New Organization Button */}
          <div className="border-t border-gray-200 dark:border-gray-700 p-2">
            <button
              onClick={handleCreateOrg}
              className={`w-full flex items-center gap-2 px-4 py-3 rounded-lg transition-all duration-150 ${
                currentTheme === 'unicorn'
                  ? 'text-purple-200 hover:bg-purple-600/20'
                  : currentTheme === 'light'
                  ? 'text-gray-700 hover:bg-gray-100'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <PlusCircleIcon className="h-5 w-5" />
              <span className="text-sm font-medium">Create New Organization</span>
            </button>
          </div>
        </div>
      )}

      {/* Create Organization Modal */}
      <CreateOrganizationModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onCreated={handleOrgCreated}
      />
    </div>
  );
}
