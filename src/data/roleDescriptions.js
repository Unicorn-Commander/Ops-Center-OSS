/**
 * Role Descriptions for UC-Cloud RBAC (Role-Based Access Control)
 *
 * Defines all user roles, their permissions, and hierarchy.
 * Used by: UserManagement, RoleManagement, PermissionMatrix
 *
 * @module roleDescriptions
 */

/**
 * Role definitions with permissions and metadata
 */
export const roleDescriptions = {
  admin: {
    name: 'Administrator',
    description: 'Full system access with all administrative privileges',
    category: 'System',
    color: 'error', // red
    icon: 'admin_panel_settings',
    hierarchy: 1,
    permissions: [
      // Global permissions
      'system.*',

      // User management
      'users.read',
      'users.create',
      'users.update',
      'users.delete',
      'users.impersonate',
      'users.assign_roles',
      'users.manage_api_keys',

      // Organization management
      'organizations.read',
      'organizations.create',
      'organizations.update',
      'organizations.delete',
      'organizations.manage_members',

      // Service management
      'services.read',
      'services.start',
      'services.stop',
      'services.restart',
      'services.configure',
      'services.delete',

      // LLM management
      'llm.read',
      'llm.configure',
      'llm.execute',
      'llm.manage_providers',
      'llm.manage_models',

      // Billing & subscriptions
      'billing.read',
      'billing.write',
      'billing.configure',
      'billing.manage_plans',

      // System settings
      'settings.read',
      'settings.write',
      'settings.configure',

      // Monitoring & logs
      'logs.read',
      'logs.export',
      'audit.read',
      'audit.export',
      'metrics.read',

      // Security
      'security.read',
      'security.configure',
      'rbac.manage',
      'api_keys.manage'
    ],
    canManageRoles: ['admin', 'moderator', 'developer', 'analyst', 'viewer'],
    limits: {
      maxApiKeys: 50,
      maxOrganizations: -1, // unlimited
      maxTeamMembers: -1
    }
  },

  moderator: {
    name: 'Moderator',
    description: 'User and content management with limited system access',
    category: 'System',
    color: 'warning', // orange
    icon: 'verified_user',
    hierarchy: 2,
    permissions: [
      // User management (limited)
      'users.read',
      'users.create',
      'users.update',
      'users.assign_roles', // limited to roles below moderator

      // Organization management (limited)
      'organizations.read',
      'organizations.update',
      'organizations.manage_members',

      // Content moderation
      'content.read',
      'content.moderate',
      'content.delete',

      // Service viewing
      'services.read',

      // LLM usage
      'llm.read',
      'llm.execute',

      // Billing viewing
      'billing.read',

      // Logs and monitoring
      'logs.read',
      'audit.read',
      'metrics.read'
    ],
    canManageRoles: ['developer', 'analyst', 'viewer'],
    limits: {
      maxApiKeys: 20,
      maxOrganizations: 5,
      maxTeamMembers: 50
    }
  },

  developer: {
    name: 'Developer',
    description: 'Service access, API usage, and development tools',
    category: 'Technical',
    color: 'primary', // blue
    icon: 'code',
    hierarchy: 3,
    permissions: [
      // Service access
      'services.read',
      'services.execute',

      // LLM usage
      'llm.read',
      'llm.execute',
      'llm.manage_models', // personal models only

      // API access
      'api.read',
      'api.execute',
      'api_keys.manage', // own keys only

      // Development tools
      'dev_tools.access',
      'brigade.access',
      'brigade.create_agents',

      // Personal organization
      'organizations.read',
      'organizations.update', // own org only

      // Usage metrics
      'metrics.read', // own usage only
      'billing.read', // own billing only

      // Documentation
      'docs.read',
      'docs.write'
    ],
    canManageRoles: [],
    limits: {
      maxApiKeys: 10,
      maxOrganizations: 1,
      maxTeamMembers: 10
    }
  },

  analyst: {
    name: 'Analyst',
    description: 'Read-only access to analytics, billing, and reporting',
    category: 'Business',
    color: 'success', // green
    icon: 'analytics',
    hierarchy: 4,
    permissions: [
      // Analytics access
      'analytics.read',
      'metrics.read',
      'reports.read',
      'reports.export',

      // Billing viewing
      'billing.read',
      'billing.export',

      // User viewing
      'users.read',

      // Organization viewing
      'organizations.read',

      // Service viewing
      'services.read',

      // LLM viewing
      'llm.read',

      // Logs viewing
      'logs.read',
      'audit.read'
    ],
    canManageRoles: [],
    limits: {
      maxApiKeys: 5,
      maxOrganizations: 0,
      maxTeamMembers: 0
    }
  },

  viewer: {
    name: 'Viewer',
    description: 'Basic read-only access to dashboard and services',
    category: 'General',
    color: 'default', // gray
    icon: 'visibility',
    hierarchy: 5,
    permissions: [
      // Dashboard access
      'dashboard.read',

      // Service viewing
      'services.read',

      // Personal profile
      'profile.read',
      'profile.update',

      // Personal settings
      'settings.read', // own settings only

      // Documentation
      'docs.read'
    ],
    canManageRoles: [],
    limits: {
      maxApiKeys: 2,
      maxOrganizations: 0,
      maxTeamMembers: 0
    }
  },

  // ============================================================
  // Organization-specific roles
  // ============================================================
  org_owner: {
    name: 'Organization Owner',
    description: 'Full control over organization settings, members, and billing',
    category: 'Organization',
    color: 'secondary', // purple
    icon: 'business',
    hierarchy: 1,
    scope: 'organization',
    permissions: [
      'org.read',
      'org.update',
      'org.delete',
      'org.manage_members',
      'org.manage_roles',
      'org.manage_billing',
      'org.manage_settings',
      'org.view_audit'
    ],
    canManageRoles: ['org_admin', 'org_member'],
    limits: {
      maxApiKeys: 20,
      maxTeamMembers: -1
    }
  },

  org_admin: {
    name: 'Organization Admin',
    description: 'Manage organization members and settings',
    category: 'Organization',
    color: 'info', // light blue
    icon: 'manage_accounts',
    hierarchy: 2,
    scope: 'organization',
    permissions: [
      'org.read',
      'org.update',
      'org.manage_members',
      'org.view_billing',
      'org.manage_settings'
    ],
    canManageRoles: ['org_member'],
    limits: {
      maxApiKeys: 10,
      maxTeamMembers: 50
    }
  },

  org_member: {
    name: 'Organization Member',
    description: 'Standard organization member with service access',
    category: 'Organization',
    color: 'default',
    icon: 'person',
    hierarchy: 3,
    scope: 'organization',
    permissions: [
      'org.read',
      'services.read',
      'services.execute',
      'llm.execute'
    ],
    canManageRoles: [],
    limits: {
      maxApiKeys: 5,
      maxTeamMembers: 0
    }
  }
};

/**
 * Role hierarchy (top to bottom = highest to lowest privilege)
 */
export const roleHierarchy = [
  'admin',
  'moderator',
  'developer',
  'analyst',
  'viewer'
];

/**
 * Organization role hierarchy
 */
export const orgRoleHierarchy = [
  'org_owner',
  'org_admin',
  'org_member'
];

/**
 * Permission categories for grouping in UI
 */
export const permissionCategories = {
  users: {
    name: 'User Management',
    description: 'Manage user accounts and permissions',
    icon: 'people'
  },
  organizations: {
    name: 'Organizations',
    description: 'Manage organizations and teams',
    icon: 'business'
  },
  services: {
    name: 'Services',
    description: 'Access and manage platform services',
    icon: 'apps'
  },
  llm: {
    name: 'LLM & AI',
    description: 'Manage AI models and inference',
    icon: 'psychology'
  },
  billing: {
    name: 'Billing',
    description: 'View and manage billing information',
    icon: 'payments'
  },
  settings: {
    name: 'Settings',
    description: 'Configure system and user settings',
    icon: 'settings'
  },
  security: {
    name: 'Security',
    description: 'Security and access control',
    icon: 'security'
  },
  logs: {
    name: 'Logs & Monitoring',
    description: 'Access system logs and metrics',
    icon: 'description'
  }
};

/**
 * Get role by key
 * @param {string} roleKey - Role identifier
 * @returns {Object|null} Role description or null if not found
 */
export function getRole(roleKey) {
  return roleDescriptions[roleKey] || null;
}

/**
 * Get all roles in a category
 * @param {string} category - Category name
 * @returns {Array} Array of role objects with keys
 */
export function getRolesByCategory(category) {
  return Object.entries(roleDescriptions)
    .filter(([_, role]) => role.category === category)
    .map(([key, role]) => ({ key, ...role }));
}

/**
 * Check if role has permission
 * @param {string} roleKey - Role identifier
 * @param {string} permission - Permission to check
 * @returns {boolean} True if role has permission
 */
export function hasPermission(roleKey, permission) {
  const role = getRole(roleKey);
  if (!role) return false;

  // Check for wildcard permissions
  if (role.permissions.includes('system.*')) return true;

  // Check exact match
  if (role.permissions.includes(permission)) return true;

  // Check for category wildcard (e.g., "users.*")
  const category = permission.split('.')[0];
  return role.permissions.includes(`${category}.*`);
}

/**
 * Check if role A can manage role B
 * @param {string} roleA - Managing role
 * @param {string} roleB - Role to be managed
 * @returns {boolean} True if roleA can manage roleB
 */
export function canManageRole(roleA, roleB) {
  const role = getRole(roleA);
  if (!role) return false;

  return role.canManageRoles.includes(roleB);
}

/**
 * Get effective permissions for a role
 * @param {string} roleKey - Role identifier
 * @returns {Array} Array of expanded permissions
 */
export function getEffectivePermissions(roleKey) {
  const role = getRole(roleKey);
  if (!role) return [];

  // If role has system.*, return all possible permissions
  if (role.permissions.includes('system.*')) {
    return ['ALL_PERMISSIONS'];
  }

  return role.permissions;
}

/**
 * Compare role hierarchy
 * @param {string} roleA - First role
 * @param {string} roleB - Second role
 * @returns {number} -1 if roleA > roleB, 0 if equal, 1 if roleA < roleB
 */
export function compareRoles(roleA, roleB) {
  const a = getRole(roleA);
  const b = getRole(roleB);

  if (!a || !b) return 0;

  if (a.hierarchy < b.hierarchy) return -1;
  if (a.hierarchy > b.hierarchy) return 1;
  return 0;
}

export default roleDescriptions;
