/**
 * Organization Card Component
 * Displays organization summary information in a card format
 */

import React from 'react';
import { BuildingOfficeIcon, UsersIcon, ChartBarIcon } from '@heroicons/react/24/outline';

export default function OrganizationCard({ organization, onSelect, isSelected }) {
  const {
    id,
    name,
    display_name,
    logo_url,
    plan_tier,
    max_seats,
    status,
    created_at
  } = organization;

  const statusColors = {
    active: 'bg-green-100 text-green-800',
    suspended: 'bg-yellow-100 text-yellow-800',
    deleted: 'bg-red-100 text-red-800'
  };

  const tierColors = {
    founders_friend: 'bg-purple-100 text-purple-800',
    starter: 'bg-blue-100 text-blue-800',
    professional: 'bg-indigo-100 text-indigo-800',
    enterprise: 'bg-pink-100 text-pink-800'
  };

  return (
    <div
      onClick={() => onSelect(organization)}
      className={`
        bg-white rounded-lg shadow p-6 cursor-pointer transition-all
        hover:shadow-lg hover:scale-105
        ${isSelected ? 'ring-2 ring-purple-500' : ''}
      `}
    >
      {/* Header with Logo */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          {logo_url ? (
            <img
              src={logo_url}
              alt={name}
              className="w-12 h-12 rounded-lg object-cover"
            />
          ) : (
            <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
              <BuildingOfficeIcon className="w-6 h-6 text-purple-600" />
            </div>
          )}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              {display_name || name}
            </h3>
            {display_name && (
              <p className="text-sm text-gray-500">{name}</p>
            )}
          </div>
        </div>

        {/* Status Badge */}
        <span className={`
          px-3 py-1 rounded-full text-xs font-medium
          ${statusColors[status] || 'bg-gray-100 text-gray-800'}
        `}>
          {status}
        </span>
      </div>

      {/* Plan Tier Badge */}
      <div className="mb-4">
        <span className={`
          inline-flex items-center px-3 py-1 rounded-full text-xs font-medium
          ${tierColors[plan_tier] || 'bg-gray-100 text-gray-800'}
        `}>
          {plan_tier.replace('_', ' ').toUpperCase()}
        </span>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center space-x-2">
          <UsersIcon className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm text-gray-500">Seats</p>
            <p className="text-lg font-semibold text-gray-900">
              {max_seats}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <ChartBarIcon className="w-5 h-5 text-gray-400" />
          <div>
            <p className="text-sm text-gray-500">Created</p>
            <p className="text-sm font-medium text-gray-900">
              {new Date(created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
