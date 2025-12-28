/**
 * Centralized Route Configuration for Ops-Center
 *
 * This file defines all routes for the Ops-Center application in a hierarchical
 * structure that aligns with the multi-tenant SaaS architecture.
 *
 * Route Structure:
 * - Personal: Always visible to authenticated users
 * - Organization: Visible to org_role: admin, owner
 * - System: Visible to role: admin (platform administrators)
 *
 * Each route includes:
 * - path: URL path
 * - component: Component name (imported in App.jsx)
 * - roles: Required user roles ['admin', 'power_user', 'user', 'viewer']
 * - orgRoles: Required organization roles ['owner', 'admin', 'member']
 * - name: Display name for navigation
 * - icon: Icon identifier (optional)
 * - section: Section grouping (optional)
 */

export const routes = {
  // ============================================================================
  // PERSONAL SECTION - Always visible to authenticated users
  // ============================================================================
  personal: {
    dashboard: {
      path: '/admin/',
      component: 'DashboardPro',
      roles: ['admin', 'power_user', 'user', 'viewer'],
      name: 'Dashboard',
      icon: 'HomeIcon',
      description: 'Main dashboard with quick stats and service status'
    },

    // My Account submenu
    account: {
      section: 'My Account',
      icon: 'UserCircleIcon',
      children: {
        profile: {
          path: '/admin/account/profile',
          component: 'UserSettings', // Will be refactored to AccountProfile
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Profile & Preferences',
          description: 'Personal information and preferences'
        },
        notifications: {
          path: '/admin/account/notifications',
          component: 'AccountNotifications', // TO BE CREATED
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Notifications',
          description: 'Email and push notification preferences',
          status: 'planned'
        },
        notificationSettings: {
          path: '/admin/account/notification-settings',
          component: 'NotificationSettings',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Notification Preferences',
          description: 'Configure alert types, thresholds, and channels',
          status: 'active'
        },
        security: {
          path: '/admin/account/security',
          component: 'AccountSecurity', // TO BE CREATED
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Security & Sessions',
          description: 'Password, 2FA, active sessions',
          status: 'planned'
        },
        apiKeys: {
          path: '/admin/account/api-keys',
          component: 'AccountAPIKeys', // TO BE CREATED
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'API Keys (BYOK)',
          description: 'Bring Your Own Key - Personal API keys',
          status: 'planned'
        }
      }
    },

    // My Subscription submenu
    subscription: {
      section: 'My Subscription',
      icon: 'CreditCardIcon',
      roles: ['admin', 'power_user', 'user', 'viewer'], // All can view their subscription
      children: {
        plan: {
          path: '/admin/subscription/plan',
          component: 'BillingDashboard', // Will be refactored to SubscriptionPlan
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Current Plan',
          description: 'Current subscription plan and features'
        },
        usage: {
          path: '/admin/subscription/usage',
          component: 'SubscriptionUsage', // TO BE CREATED
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Usage & Limits',
          description: 'API usage tracking and limits',
          status: 'planned'
        },
        billing: {
          path: '/admin/subscription/billing',
          component: 'SubscriptionBilling', // TO BE CREATED
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Billing History',
          description: 'Invoices and billing history',
          status: 'planned'
        },
        payment: {
          path: '/admin/subscription/payment',
          component: 'SubscriptionPayment', // TO BE CREATED
          roles: ['admin', 'power_user', 'user', 'viewer'],
          orgRoles: ['owner'], // Only org owner can manage payment methods
          name: 'Payment Methods',
          description: 'Credit cards and payment methods',
          status: 'planned'
        }
      }
    },

    // Credits & Usage submenu
    credits: {
      section: 'Credits & Usage',
      icon: 'CurrencyDollarIcon',
      roles: ['admin', 'power_user', 'user', 'viewer'], // All can view their credits
      children: {
        dashboard: {
          path: '/admin/credits',
          component: 'CreditDashboard',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Credit Dashboard',
          description: 'View credit balance, usage metrics, and transaction history',
          status: 'active'
        },
        tiers: {
          path: '/admin/credits/tiers',
          component: 'TierComparison',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Pricing Tiers',
          description: 'Compare subscription tiers and pricing',
          status: 'active'
        }
      }
    }
  },

  // ============================================================================
  // ORGANIZATION SECTION - Visible to org_role: admin, owner
  // ============================================================================
  organization: {
    section: 'Organization',
    icon: 'BuildingOfficeIcon',
    orgRoles: ['admin', 'owner'],
    children: {
      team: {
        path: '/admin/org/team',
        component: 'OrganizationTeam', // Organization team management
        orgRoles: ['admin', 'owner'],
        name: 'Team Members',
        description: 'Add/remove team members, manage roles',
        icon: 'UsersIcon'
      },
      roles: {
        path: '/admin/org/roles',
        component: 'OrganizationRoles', // TO BE CREATED
        orgRoles: ['admin', 'owner'],
        name: 'Roles & Permissions',
        description: 'Define custom roles and permission levels',
        status: 'planned'
      },
      settings: {
        path: '/admin/org/settings',
        component: 'OrganizationSettings', // TO BE CREATED
        orgRoles: ['admin', 'owner'],
        name: 'Organization Settings',
        description: 'Org name, logo, branding, shared preferences',
        status: 'planned'
      },
      billing: {
        path: '/admin/org/billing',
        component: 'OrganizationBilling', // TO BE CREATED
        orgRoles: ['owner'], // Only org owner
        name: 'Organization Billing',
        description: 'Org-wide usage, team seat management',
        status: 'planned'
      }
    }
  },

  // ============================================================================
  // SYSTEM SECTION - Visible to role: admin (platform administrators only)
  // ============================================================================
  system: {
    section: 'System',
    icon: 'CogIcon',
    roles: ['admin'],
    children: {
      // ========================================================================
      // USERS & ORGANIZATIONS
      // ========================================================================
      usersOrgs: {
        section: 'Users & Organizations',
        icon: 'UsersIcon',
        roles: ['admin'],
        children: {
          users: {
            path: '/admin/system/users',
            component: 'UserManagement',
            roles: ['admin'],
            name: 'User Management',
            description: 'Platform user administration, roles, permissions',
            icon: 'UsersIcon'
          },
          organizations: {
            path: '/admin/organization/list',
            component: 'OrganizationsList',
            roles: ['admin'],
            name: 'Organizations',
            description: 'Platform organization administration, team management',
            icon: 'BuildingOfficeIcon'
          },
          billing: {
            path: '/admin/system/billing',
            component: 'BillingDashboard',
            roles: ['admin'],
            name: 'Billing Analytics',
            description: 'Platform-wide billing analytics, revenue metrics, payment tracking',
            icon: 'CreditCardIcon'
          },
          localUsers: {
            path: '/admin/system/local-users',
            component: 'LocalUserManagement',
            roles: ['admin'],
            name: 'Local Users',
            description: 'Linux system user management, SSH keys, sudo permissions',
            icon: 'UserCircleIcon'
          }
        }
      },

      // ========================================================================
      // LLM & AI
      // ========================================================================
      llmAI: {
        section: 'LLM & AI',
        icon: 'SparklesIcon',
        roles: ['admin'],
        children: {
          models: {
            path: '/admin/system/models',
            component: 'AIModelManagement',
            roles: ['admin'],
            name: 'AI Models',
            description: 'Model registry, downloads, GPU allocation',
            icon: 'CubeIcon'
          },
          litellm: {
            path: '/admin/litellm-providers',
            component: 'LiteLLMManagement',
            roles: ['admin'],
            name: 'LLM Providers',
            description: 'Multi-provider LLM routing, cost optimization, BYOK',
            icon: 'ServerIcon'
          },
          openrouter: {
            path: '/admin/openrouter-settings',
            component: 'OpenRouterSettings',
            roles: ['admin'],
            name: 'OpenRouter',
            description: 'OpenRouter API configuration and 348 model browser',
            icon: 'GlobeAltIcon'
          },
          llmUsage: {
            path: '/admin/llm/usage',
            component: 'LLMUsage',
            roles: ['admin', 'power_user', 'user', 'viewer'],
            name: 'Usage Analytics',
            description: 'LLM API usage analytics and cost tracking',
            icon: 'ChartBarIcon'
          }
        }
      },

      // ========================================================================
      // INFRASTRUCTURE
      // ========================================================================
      infrastructure: {
        section: 'Infrastructure',
        icon: 'ServerIcon',
        roles: ['admin'],
        children: {
          services: {
            path: '/admin/system/services',
            component: 'Services',
            roles: ['admin'],
            name: 'Services',
            description: 'Docker service management, health monitoring',
            icon: 'ServerIcon'
          },
          resources: {
            path: '/admin/system/resources',
            component: 'System',
            roles: ['admin'],
            name: 'Resources',
            description: 'CPU, Memory, GPU, Disk, performance graphs',
            icon: 'ChartBarIcon'
          },
          hardware: {
            path: '/admin/system/hardware',
            component: 'HardwareManagement',
            roles: ['admin'],
            name: 'Hardware Monitoring',
            description: 'Real-time GPU, CPU, memory monitoring with historical charts',
            icon: 'CpuChipIcon'
          },
          network: {
            path: '/admin/system/network',
            component: 'Network',
            roles: ['admin'],
            name: 'Network',
            description: 'Network configuration, firewall rules',
            icon: 'WifiIcon'
          },
          storage: {
            path: '/admin/system/storage',
            component: 'StorageBackup',
            roles: ['admin'],
            name: 'Storage & Backup',
            description: 'Volume management, backup schedules',
            icon: 'ArchiveBoxIcon'
          },
          traefik: {
            path: '/admin/system/traefik',
            component: 'TraefikConfig',
            roles: ['admin'],
            name: 'Traefik',
            description: 'Reverse proxy, SSL/TLS, routing configuration',
            icon: 'ArrowsRightLeftIcon'
          }
        }
      },
      // ========================================================================
      // INTEGRATIONS
      // ========================================================================
      integrations: {
        section: 'Integrations',
        icon: 'LinkIcon',
        roles: ['admin'],
        children: {
          credentials: {
            path: '/admin/integrations/credentials',
            component: 'PlatformSettings',
            roles: ['admin'],
            name: 'API Credentials',
            description: 'Manage API keys for Stripe, Lago, Cloudflare, NameCheap, Forgejo',
            icon: 'KeyIcon'
          },
          email: {
            path: '/admin/integrations/email',
            component: 'EmailSettings',
            roles: ['admin'],
            name: 'Email Providers',
            description: 'Configure email providers for notifications',
            icon: 'EnvelopeIcon'
          },
          dns: {
            path: '/admin/integrations/cloudflare',
            component: 'CloudflareDNS',
            roles: ['admin'],
            name: 'DNS Management',
            description: 'Cloudflare DNS zones and record management',
            icon: 'GlobeAltIcon'
          }
        }
      },

      // ========================================================================
      // MONITORING & ANALYTICS
      // ========================================================================
      monitoring: {
        section: 'Monitoring & Analytics',
        icon: 'ChartBarIcon',
        roles: ['admin'],
        children: {
          overview: {
            path: '/admin/monitoring/overview',
            component: 'MonitoringOverview',
            roles: ['admin'],
            name: 'Overview',
            description: 'System health, metrics, and alerts dashboard',
            icon: 'PresentationChartBarIcon',
            status: 'planned'
          },
          grafana: {
            path: '/admin/monitoring/grafana',
            component: 'GrafanaConfig',
            roles: ['admin'],
            name: 'Grafana',
            description: 'Grafana dashboard configuration and data sources',
            icon: 'ChartBarIcon',
            status: 'planned'
          },
          prometheus: {
            path: '/admin/monitoring/prometheus',
            component: 'PrometheusConfig',
            roles: ['admin'],
            name: 'Prometheus',
            description: 'Metrics collection and scrape configuration',
            icon: 'CircleStackIcon',
            status: 'planned'
          },
          umami: {
            path: '/admin/monitoring/umami',
            component: 'UmamiConfig',
            roles: ['admin'],
            name: 'Umami Analytics',
            description: 'Web analytics tracking and configuration',
            icon: 'ChartPieIcon',
            status: 'planned'
          },
          logs: {
            path: '/admin/monitoring/logs',
            component: 'Logs',
            roles: ['admin'],
            name: 'System Logs',
            description: 'Service logs and error tracking',
            icon: 'DocumentTextIcon'
          }
        }
      },

      // ========================================================================
      // SECURITY & COMPLIANCE
      // ========================================================================
      security: {
        section: 'Security & Compliance',
        icon: 'ShieldCheckIcon',
        roles: ['admin'],
        children: {
          authentication: {
            path: '/admin/system/authentication',
            component: 'Authentication',
            roles: ['admin'],
            name: 'Authentication',
            description: 'Keycloak/SSO configuration, identity providers',
            icon: 'KeyIcon'
          },
          securityPolicies: {
            path: '/admin/system/security',
            component: 'Security',
            roles: ['admin'],
            name: 'Security Policies',
            description: 'Security policies, audit logs, compliance',
            icon: 'ShieldCheckIcon'
          }
        }
      },

      // ========================================================================
      // CONFIGURATION
      // ========================================================================
      configuration: {
        section: 'Configuration',
        icon: 'CogIcon',
        roles: ['admin'],
        children: {
          landing: {
            path: '/admin/system/landing',
            component: 'LandingCustomization',
            roles: ['admin'],
            name: 'Landing Page',
            description: 'Customize public landing page',
            icon: 'PaintBrushIcon'
          },
          extensions: {
            path: '/admin/system/extensions',
            component: 'Extensions',
            roles: ['admin'],
            name: 'Extensions',
            description: 'Plugin management',
            icon: 'PuzzlePieceIcon'
          }
        }
      }
    }
  },

  // ============================================================================
  // REDIRECTS - Backwards compatibility for old routes
  // ============================================================================
  redirects: [
    // System admin routes moved to /admin/system/* namespace
    { from: '/admin/models', to: '/admin/system/models', type: 'permanent' },
    { from: '/admin/services', to: '/admin/system/services', type: 'permanent' },
    { from: '/admin/system', to: '/admin/system/resources', type: 'permanent' },
    { from: '/admin/network', to: '/admin/system/network', type: 'permanent' },
    { from: '/admin/storage', to: '/admin/system/storage', type: 'permanent' },
    { from: '/admin/logs', to: '/admin/system/logs', type: 'permanent' },
    { from: '/admin/security', to: '/admin/system/security', type: 'permanent' },
    { from: '/admin/authentication', to: '/admin/system/authentication', type: 'permanent' },
    { from: '/admin/extensions', to: '/admin/system/extensions', type: 'permanent' },
    { from: '/admin/landing', to: '/admin/system/landing', type: 'permanent' },
    { from: '/admin/settings', to: '/admin/system/settings', type: 'permanent' },

    // Personal routes moved to /admin/account/* namespace
    { from: '/admin/user-settings', to: '/admin/account/profile', type: 'permanent' },

    // Billing routes moved to /admin/subscription/* namespace
    { from: '/admin/billing', to: '/admin/subscription/plan', type: 'permanent' },

    // Platform Settings renamed to Integrations
    { from: '/admin/platform/settings', to: '/admin/integrations/credentials', type: 'permanent' },
    { from: '/admin/platform/email-settings', to: '/admin/integrations/email', type: 'permanent' },

    // Logs moved to Monitoring section
    { from: '/admin/system/logs', to: '/admin/monitoring/logs', type: 'permanent' },

    // Cloudflare DNS moved to Integrations
    { from: '/admin/infrastructure/cloudflare', to: '/admin/integrations/cloudflare', type: 'permanent' },
  ],

  // ============================================================================
  // LEGACY ROUTES - Currently in App.jsx, to be migrated
  // ============================================================================
  legacy: {
    // These are still using old paths and will be migrated
    dashboard: { path: '/admin/', component: 'DashboardPro' },
    models: { path: '/admin/models', component: 'AIModelManagement' },
    services: { path: '/admin/services', component: 'Services' },
    system: { path: '/admin/system', component: 'System' },
    network: { path: '/admin/network', component: 'Network' },
    storage: { path: '/admin/storage', component: 'StorageBackup' },
    extensions: { path: '/admin/extensions', component: 'Extensions' },
    logs: { path: '/admin/logs', component: 'Logs' },
    security: { path: '/admin/security', component: 'Security' },
    authentication: { path: '/admin/authentication', component: 'Authentication' },
    settings: { path: '/admin/settings', component: 'Settings' },
    userSettings: { path: '/admin/user-settings', component: 'UserSettings' },
    billing: { path: '/admin/billing', component: 'BillingDashboard' },
    landing: { path: '/admin/landing', component: 'LandingCustomization' }
  }
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get all routes as a flat array (useful for React Router)
 */
export function getAllRoutes() {
  const allRoutes = [];

  // Extract personal routes
  Object.entries(routes.personal).forEach(([key, value]) => {
    if (value.path) {
      allRoutes.push(value);
    } else if (value.children) {
      Object.values(value.children).forEach(child => allRoutes.push(child));
    }
  });

  // Extract organization routes
  if (routes.organization.children) {
    Object.values(routes.organization.children).forEach(route => allRoutes.push(route));
  }

  // Extract system routes
  if (routes.system.children) {
    Object.values(routes.system.children).forEach(route => allRoutes.push(route));
  }

  return allRoutes;
}

/**
 * Get routes for navigation menu (hierarchical structure)
 */
export function getNavigationStructure() {
  return {
    personal: routes.personal,
    organization: routes.organization,
    system: routes.system
  };
}

/**
 * Get redirect mappings
 */
export function getRedirects() {
  return routes.redirects;
}

/**
 * Find new route for a legacy path
 */
export function findRedirect(oldPath) {
  const redirect = routes.redirects.find(r => r.from === oldPath);
  return redirect ? redirect.to : null;
}

/**
 * Check if user has access to a route based on role
 */
export function hasRouteAccess(route, userRole, userOrgRole = null) {
  // Check platform role
  if (route.roles && !route.roles.includes(userRole)) {
    return false;
  }

  // Check org role if specified
  if (route.orgRoles && (!userOrgRole || !route.orgRoles.includes(userOrgRole))) {
    return false;
  }

  return true;
}

/**
 * Filter routes by user permissions
 */
export function getAccessibleRoutes(userRole, userOrgRole = null) {
  const accessible = [];

  getAllRoutes().forEach(route => {
    if (hasRouteAccess(route, userRole, userOrgRole)) {
      accessible.push(route);
    }
  });

  return accessible;
}

/**
 * Get routes for a specific section
 */
export function getRoutesBySection(section) {
  switch (section) {
    case 'personal':
      return routes.personal;
    case 'organization':
      return routes.organization;
    case 'system':
      return routes.system;
    default:
      return {};
  }
}

export default routes;
