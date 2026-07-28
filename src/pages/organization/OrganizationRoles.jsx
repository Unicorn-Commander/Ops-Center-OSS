import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  ShieldCheckIcon,
  PlusIcon,
  CheckCircleIcon,
  XMarkIcon,
  LockClosedIcon,
  KeyIcon,
  UserGroupIcon
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

// Default role permissions
const defaultPermissions = {
  owner: {
    name: 'Owner',
    description: 'Full access to all organization features and settings',
    permissions: [
      'Manage billing and subscriptions',
      'Invite and remove team members',
      'Assign and modify roles',
      'Delete organization',
      'Manage organization settings',
      'Access all services',
      'View usage analytics'
    ],
    color: 'purple',
    editable: false
  },
  admin: {
    name: 'Administrator',
    description: 'Manage team members and organization settings',
    permissions: [
      'Invite and remove team members',
      'Assign member roles',
      'Manage organization settings',
      'Access all services',
      'View usage analytics'
    ],
    color: 'blue',
    editable: false
  },
  member: {
    name: 'Member',
    description: 'Standard access to organization services',
    permissions: [
      'Access assigned services',
      'View own usage data',
      'Update profile settings'
    ],
    color: 'gray',
    editable: false
  }
};

export default function OrganizationRoles() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg, loading: orgLoading } = useOrganization();
  const [roles] = useState(defaultPermissions);
  const [loading, setLoading] = useState(true);
  const [selectedRole, setSelectedRole] = useState(null);
  // Real per-role member counts derived from the org members API
  // (null = counts unavailable, rendered as "—")
  const [roleCounts, setRoleCounts] = useState(null);

  // Toast notification
  const [toast, setToast] = useState({
    show: false,
    message: '',
    type: 'success'
  });

  useEffect(() => {
    if (orgLoading) return;
    if (currentOrg) {
      fetchRoleCounts();
    } else {
      setLoading(false);
    }
  }, [currentOrg, orgLoading]);

  const fetchRoleCounts = async () => {
    setLoading(true);
    try {
      // Same data access pattern as OrganizationTeam: count members by org_role
      const response = await fetch(`/api/v1/org/${currentOrg.id}/members?limit=1000`, {
        credentials: 'include'
      });
      if (!response.ok) throw new Error('Failed to fetch members');

      const data = await response.json();
      const counts = { owner: 0, admin: 0, member: 0 };
      (data.members || []).forEach((m) => {
        const role = (m.org_role || m.role || 'member').toLowerCase();
        if (counts[role] !== undefined) {
          counts[role] += 1;
        } else {
          counts.member += 1;
        }
      });
      setRoleCounts(counts);
    } catch (error) {
      console.error('Failed to fetch member counts:', error);
      setRoleCounts(null);
      showToast('Could not load member counts', 'error');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message, type = 'success') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type }), 5000);
  };

  const getRoleColorClasses = (color) => {
    const colors = {
      purple: 'from-purple-500 to-indigo-600 border-purple-500/30',
      blue: 'from-blue-500 to-cyan-600 border-blue-500/30',
      gray: 'from-gray-500 to-gray-600 border-gray-500/30',
      green: 'from-green-500 to-emerald-600 border-green-500/30',
      orange: 'from-orange-500 to-red-600 border-orange-500/30'
    };
    return colors[color] || colors.gray;
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
                <ShieldCheckIcon className="h-6 w-6 text-white" />
              </div>
              Organization Roles
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>Define roles and permissions for your organization</p>
          </div>
          <button
            disabled={true}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-gray-400 rounded-lg cursor-not-allowed"
            title="Custom roles are not available yet"
          >
            <PlusIcon className="h-4 w-4" />
            Create Custom Role (not available yet)
          </button>
        </div>
      </motion.div>

      {/* Info Banner */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-4 border border-blue-500/20`}>
        <div className="flex items-start gap-3">
          <KeyIcon className="h-5 w-5 text-blue-500 mt-0.5" />
          <div>
            <h3 className={`font-semibold ${theme.text.primary}`}>Role-Based Access Control</h3>
            <p className={`text-sm ${theme.text.secondary} mt-1`}>
              Roles determine what actions members can perform within your organization. Default roles cannot be modified, but you can create custom roles for specific needs.
            </p>
          </div>
        </div>
      </motion.div>

      {/* Roles Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      ) : (
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {Object.entries(roles).map(([roleKey, role]) => (
            <motion.div
              key={roleKey}
              whileHover={{ scale: 1.02 }}
              className={`${theme.card} rounded-xl p-6 border transition-all cursor-pointer ${
                selectedRole === roleKey ? 'border-blue-500 shadow-lg shadow-blue-500/20' : 'border-gray-700/50'
              }`}
              onClick={() => setSelectedRole(roleKey)}
            >
              {/* Role Header */}
              <div className="flex items-start justify-between mb-4">
                <div className={`w-12 h-12 bg-gradient-to-br ${getRoleColorClasses(role.color)} rounded-lg flex items-center justify-center shadow-lg border`}>
                  {roleKey === 'owner' ? (
                    <LockClosedIcon className="h-6 w-6 text-white" />
                  ) : roleKey === 'admin' ? (
                    <ShieldCheckIcon className="h-6 w-6 text-white" />
                  ) : (
                    <UserGroupIcon className="h-6 w-6 text-white" />
                  )}
                </div>
                {!role.editable && (
                  <span className="px-2 py-1 text-xs bg-gray-500/20 text-gray-400 rounded-full border border-gray-500/30">
                    System Role
                  </span>
                )}
              </div>

              {/* Role Title */}
              <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>{role.name}</h3>
              <p className={`text-sm ${theme.text.secondary} mb-4`}>{role.description}</p>

              {/* Member Count - real count from the org members API, "—" if unavailable */}
              <div className="flex items-center gap-2 mb-4 pb-4 border-b border-gray-700/50">
                <UserGroupIcon className="h-4 w-4 text-gray-400" />
                <span className={`text-sm ${theme.text.secondary}`}>
                  {roleCounts
                    ? `${roleCounts[roleKey] ?? 0} ${(roleCounts[roleKey] ?? 0) === 1 ? 'member' : 'members'}`
                    : '— members'}
                </span>
              </div>

              {/* Permissions */}
              <div>
                <h4 className={`text-sm font-semibold ${theme.text.secondary} mb-3`}>Permissions</h4>
                <ul className="space-y-2">
                  {role.permissions.map((permission, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 flex-shrink-0" />
                      <span className={`text-sm ${theme.text.primary}`}>{permission}</span>
                    </li>
                  ))}
                </ul>
              </div>

            </motion.div>
          ))}
        </motion.div>
      )}

      {/* Role Comparison Table */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>Permission Comparison</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className={`border-b ${currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'}`}>
                <th className={`text-left py-3 px-4 ${theme.text.secondary} font-semibold`}>Permission</th>
                <th className={`text-center py-3 px-4 ${theme.text.secondary} font-semibold`}>Owner</th>
                <th className={`text-center py-3 px-4 ${theme.text.secondary} font-semibold`}>Admin</th>
                <th className={`text-center py-3 px-4 ${theme.text.secondary} font-semibold`}>Member</th>
              </tr>
            </thead>
            <tbody>
              {[
                'Manage billing',
                'Delete organization',
                'Invite members',
                'Remove members',
                'Assign roles',
                'Manage settings',
                'Access services',
                'View analytics'
              ].map((permission, index) => (
                <tr
                  key={index}
                  className={`border-b ${currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'}`}
                >
                  <td className={`py-3 px-4 ${theme.text.primary}`}>{permission}</td>
                  <td className="py-3 px-4 text-center">
                    <CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" />
                  </td>
                  <td className="py-3 px-4 text-center">
                    {['Manage billing', 'Delete organization'].includes(permission) ? (
                      <XMarkIcon className="h-5 w-5 text-red-500 mx-auto" />
                    ) : (
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" />
                    )}
                  </td>
                  <td className="py-3 px-4 text-center">
                    {['Access services', 'View analytics'].includes(permission) ? (
                      <CheckCircleIcon className="h-5 w-5 text-green-500 mx-auto" />
                    ) : (
                      <XMarkIcon className="h-5 w-5 text-red-500 mx-auto" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Custom roles notice */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-yellow-500/20`}>
        <div className="flex items-start gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-lg flex items-center justify-center shadow-lg">
            <PlusIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className={`text-lg font-semibold ${theme.text.primary}`}>Custom Roles (not available yet)</h3>
            <p className={`text-sm ${theme.text.secondary} mt-2`}>
              Organizations currently use the three built-in roles above. Custom roles with granular permissions are not available yet.
            </p>
          </div>
        </div>
      </motion.div>

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
