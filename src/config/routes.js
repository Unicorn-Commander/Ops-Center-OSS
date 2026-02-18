/**
 * Centralized Route Configuration for Ops-Center
 *
 * Route Structure:
 * - Personal: Always visible to authenticated users
 * - Organization: Visible to org_role: admin, owner
 * - System/Admin: Visible to role: admin (platform administrators)
 *
 * Each route includes:
 * - path: URL path
 * - component: Component name (imported in App.jsx)
 * - roles: Required user roles ['admin', 'power_user', 'user', 'viewer']
 * - orgRoles: Required organization roles ['owner', 'admin', 'member']
 * - name: Display name for navigation/page title
 * - icon: Icon identifier (optional)
 * - section: Section grouping (optional)
 * - nav: Set to false to hide from navigation
 *
 * Phase 1 Consolidation (February 2026):
 * - AI & Models: 12 items → 7 nav items (5 demoted to nav:false)
 * - Monitoring: 12 items → 6 nav items (Grafana/Prometheus/Umami → External Tools tab page)
 * - Billing: 8 items → 5 nav items (3 billing dashboards → Revenue Dashboard)
 * - User sections: Credits & Usage merged into Subscription & Credits
 * - Infrastructure: Traefik → Reverse Proxy, Security promoted to visible
 */

export const routes = {
  // ==========================================================================
  // PERSONAL SECTION - Always visible to authenticated users
  // ==========================================================================
  personal: {
    dashboard: {
      path: '/admin/',
      component: 'AppsLauncher',
      roles: ['admin', 'power_user', 'user', 'viewer'],
      name: 'Dashboard',
      icon: 'HomeIcon',
      description: 'Main dashboard with quick stats and service status'
    },
    myDashboard: {
      path: '/admin/my-dashboard',
      component: 'UserDashboard',
      roles: ['admin', 'power_user', 'user', 'viewer'],
      name: 'My Dashboard',
      icon: 'ChartBarSquareIcon',
      description: 'Personal credits, usage, and subscription overview'
    },
    login: {
      path: '/admin/login',
      component: 'Login',
      roles: ['admin', 'power_user', 'user', 'viewer'],
      name: 'Login',
      nav: false
    },
    marketplace: {
      path: '/admin/apps/marketplace',
      component: 'AppMarketplace',
      roles: ['admin', 'power_user', 'user', 'viewer'],
      name: 'Marketplace',
      icon: 'ShoppingBagIcon',
      description: 'Browse and install apps and extensions'
    },

    // Account (unchanged)
    account: {
      section: 'Account',
      icon: 'UserCircleIcon',
      children: {
        profile: {
          path: '/admin/account/profile',
          component: 'AccountProfile',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Profile & Preferences'
        },
        security: {
          path: '/admin/account/security',
          component: 'AccountSecurity',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Security & Sessions'
        },
        apiKeys: {
          path: '/admin/account/api-keys',
          component: 'AccountAPIKeys',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'API Keys (BYOK)'
        },
        notificationSettings: {
          path: '/admin/account/notification-settings',
          component: 'NotificationSettings',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Notification Preferences'
        }
      }
    },

    // Subscription & Credits (merged from "My Subscription" + "Credits & Usage")
    subscription: {
      section: 'Subscription & Credits',
      icon: 'CreditCardIcon',
      roles: ['admin', 'power_user', 'user', 'viewer'],
      children: {
        plan: {
          path: '/admin/subscription/plan',
          component: 'SubscriptionPlan',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Current Plan'
        },
        usage: {
          path: '/admin/subscription/usage',
          component: 'SubscriptionUsage',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Usage & Limits'
        },
        billing: {
          path: '/admin/subscription/billing',
          component: 'SubscriptionBilling',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Billing History'
        },
        payment: {
          path: '/admin/subscription/payment',
          component: 'PaymentMethods',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Payment Methods'
        },
        creditsAndTiers: {
          path: '/admin/billing/tiers/compare',
          component: 'TierComparison',
          roles: ['admin', 'power_user', 'user', 'viewer'],
          name: 'Credits & Tiers'
        }
      }
    }
  },

  // ==========================================================================
  // ORGANIZATION SECTION - Visible to org_role: admin, owner
  // ==========================================================================
  organization: {
    section: 'My Organization',
    icon: 'BuildingOfficeIcon',
    orgRoles: ['admin', 'owner'],
    children: {
      team: {
        path: '/admin/org/team',
        component: 'OrganizationTeam',
        orgRoles: ['admin', 'owner'],
        name: 'Team Members'
      },
      roles: {
        path: '/admin/org/roles',
        component: 'OrganizationRoles',
        orgRoles: ['admin', 'owner'],
        name: 'Roles & Permissions'
      },
      settings: {
        path: '/admin/org/settings',
        component: 'OrganizationSettings',
        orgRoles: ['admin', 'owner'],
        name: 'Organization Settings'
      },
      billing: {
        path: '/admin/org/billing',
        component: 'OrganizationBilling',
        orgRoles: ['owner'],
        name: 'Organization Billing'
      }
    }
  },

  // ==========================================================================
  // SYSTEM/ADMIN SECTION - Visible to role: admin (platform administrators only)
  // ==========================================================================
  system: {
    section: 'Admin',
    icon: 'CogIcon',
    roles: ['admin'],
    children: {
      peopleAccess: {
        section: 'People & Access',
        icon: 'UsersIcon',
        roles: ['admin'],
        children: {
          users: {
            path: '/admin/people/users',
            component: 'UserManagement',
            roles: ['admin'],
            name: 'Users'
          },
          userDetail: {
            path: '/admin/people/users/:userId',
            component: 'UserDetail',
            roles: ['admin'],
            name: 'User Detail',
            nav: false
          },
          organizations: {
            path: '/admin/people/organizations',
            component: 'OrganizationsList',
            roles: ['admin'],
            name: 'Organizations'
          },
          orgBilling: {
            path: '/admin/people/organizations/:orgId/billing',
            component: 'OrganizationBillingPro',
            roles: ['admin'],
            name: 'Organization Billing',
            nav: false
          },
          inviteCodes: {
            path: '/admin/people/invite-codes',
            component: 'InviteCodesManagement',
            roles: ['admin'],
            name: 'Invite Codes'
          },
          authentication: {
            path: '/admin/people/authentication',
            component: 'Authentication',
            roles: ['admin'],
            name: 'Authentication'
          }
        }
      },

      // Billing & Plans — consolidated from 8 nav items to 5
      billingPlans: {
        section: 'Billing & Plans',
        icon: 'CreditCardIcon',
        roles: ['admin'],
        children: {
          tiers: {
            path: '/admin/billing/tiers',
            component: 'SubscriptionManagement',
            roles: ['admin'],
            name: 'Subscription Tiers'
          },
          apps: {
            path: '/admin/billing/apps',
            component: 'AppManagement',
            roles: ['admin'],
            name: 'App Entitlements'
          },
          pricing: {
            path: '/admin/billing/pricing',
            component: 'DynamicPricingManagement',
            roles: ['admin'],
            name: 'Pricing Rules'
          },
          revenue: {
            path: '/admin/billing/revenue',
            component: 'RevenueDashboard',
            roles: ['admin'],
            name: 'Revenue Dashboard'
          },
          creditManagement: {
            path: '/admin/billing/credits',
            component: 'CreditPurchase',
            roles: ['admin'],
            name: 'Credit Management'
          },
          // Keep old paths routable but hidden from nav
          systemBilling: {
            path: '/admin/billing/system',
            component: 'BillingDashboard',
            roles: ['admin'],
            name: 'Billing Analytics',
            nav: false
          },
          userBilling: {
            path: '/admin/billing/user',
            component: 'UserBillingDashboard',
            roles: ['admin'],
            name: 'User Billing',
            nav: false
          },
          overview: {
            path: '/admin/billing/overview',
            component: 'SystemBillingOverview',
            roles: ['admin'],
            name: 'System Billing Overview',
            nav: false
          },
          creditPurchase: {
            path: '/admin/billing/credits/purchase',
            component: 'CreditPurchase',
            roles: ['admin'],
            name: 'Buy Credits',
            nav: false
          },
          tierComparison: {
            path: '/admin/billing/tiers/compare',
            component: 'TierComparison',
            roles: ['admin'],
            name: 'Tier Comparison',
            nav: false
          }
        }
      },

      // AI & Models — consolidated from 12 nav items to 7
      aiModels: {
        section: 'AI & Models',
        icon: 'CpuChipIcon',
        roles: ['admin'],
        children: {
          overview: {
            path: '/admin/ai',
            component: 'LLMHub',
            roles: ['admin'],
            name: 'AI Hub'
          },
          unifiedModels: {
            path: '/admin/ai/models',
            component: 'LLMManagementUnified',
            roles: ['admin'],
            name: 'Model Catalog'
          },
          modelLists: {
            path: '/admin/ai/model-lists',
            component: 'ModelListManagement',
            roles: ['admin'],
            name: 'Model Lists'
          },
          colonel: {
            path: '/admin/ai/colonel',
            component: 'ColonelChat',
            roles: ['admin'],
            name: 'The Colonel',
            icon: 'SparklesIcon'
          },
          localModels: {
            path: '/admin/ai/local-models',
            component: 'LocalModelsManagement',
            roles: ['admin'],
            name: 'Local Models'
          },
          gpuServices: {
            path: '/admin/ai/gpu-services',
            component: 'GPUServicesManagement',
            roles: ['admin'],
            name: 'GPU Services'
          },
          ragServices: {
            path: '/admin/ai/rag-services',
            component: 'RAGServicesManagement',
            roles: ['admin'],
            name: 'RAG Services'
          },
          // Demoted from nav — accessible via AI Hub tabs or direct URL
          management: {
            path: '/admin/ai/management',
            component: 'LLMManagement',
            roles: ['admin'],
            name: 'LLM Management',
            nav: false
          },
          providers: {
            path: '/admin/ai/providers',
            component: 'LiteLLMManagement',
            roles: ['admin'],
            name: 'Providers',
            nav: false
          },
          modelRegistry: {
            path: '/admin/ai/registry',
            component: 'AIModelManagement',
            roles: ['admin'],
            name: 'Model Registry',
            nav: false
          },
          openrouter: {
            path: '/admin/ai/openrouter',
            component: 'OpenRouterSettings',
            roles: ['admin'],
            name: 'OpenRouter',
            nav: false
          },
          usage: {
            path: '/admin/ai/usage',
            component: 'LLMUsage',
            roles: ['admin'],
            name: 'Usage Analytics',
            nav: false
          },
          graniteKeys: {
            path: '/admin/ai/granite-keys',
            component: 'GraniteApiKeysManagement',
            roles: ['admin'],
            name: 'Granite API Keys',
            nav: false
          },
          colonelSetup: {
            path: '/admin/ai/colonel/setup',
            component: 'ColonelOnboarding',
            roles: ['admin'],
            name: 'Colonel Setup',
            nav: false
          },
          colonelStatus: {
            path: '/admin/ai/colonel/status',
            component: 'ColonelStatus',
            roles: ['admin'],
            name: 'Colonel Status',
            nav: false
          }
        }
      },

      // Infrastructure — minor cleanup
      infrastructure: {
        section: 'Infrastructure',
        icon: 'ServerIcon',
        roles: ['admin'],
        children: {
          services: {
            path: '/admin/infra/services',
            component: 'Services',
            roles: ['admin'],
            name: 'Services'
          },
          resources: {
            path: '/admin/infra/resources',
            component: 'System',
            roles: ['admin'],
            name: 'Resources'
          },
          hardware: {
            path: '/admin/infra/hardware',
            component: 'HardwareManagement',
            roles: ['admin'],
            name: 'Hardware'
          },
          network: {
            path: '/admin/infra/network',
            component: 'Network',
            roles: ['admin'],
            name: 'Network'
          },
          storage: {
            path: '/admin/infra/storage',
            component: 'StorageBackup',
            roles: ['admin'],
            name: 'Storage & Backup'
          },
          traefik: {
            path: '/admin/infra/traefik',
            component: 'TraefikConfig',
            roles: ['admin'],
            name: 'Reverse Proxy'
          },
          security: {
            path: '/admin/system/security',
            component: 'Security',
            roles: ['admin'],
            name: 'Security'
          },
          // Keep routable but hidden from nav
          localUsers: {
            path: '/admin/infra/local-users',
            component: 'LocalUserManagement',
            roles: ['admin'],
            name: 'Local Users',
            nav: false
          },
          traefikDashboard: {
            path: '/admin/infra/traefik/dashboard',
            component: 'TraefikDashboard',
            roles: ['admin'],
            name: 'Traefik Dashboard',
            nav: false
          },
          traefikRoutes: {
            path: '/admin/infra/traefik/routes',
            component: 'TraefikRoutes',
            roles: ['admin'],
            name: 'Traefik Routes',
            nav: false
          },
          traefikServices: {
            path: '/admin/infra/traefik/services',
            component: 'TraefikServices',
            roles: ['admin'],
            name: 'Traefik Services',
            nav: false
          },
          traefikSSL: {
            path: '/admin/infra/traefik/ssl',
            component: 'TraefikSSL',
            roles: ['admin'],
            name: 'Traefik SSL',
            nav: false
          },
          traefikMetrics: {
            path: '/admin/infra/traefik/metrics',
            component: 'TraefikMetrics',
            roles: ['admin'],
            name: 'Traefik Metrics',
            nav: false
          },
          migration: {
            path: '/admin/infra/migration',
            component: 'MigrationWizard',
            roles: ['admin'],
            name: 'Migration',
            nav: false
          },
          forgejo: {
            path: '/admin/system/forgejo',
            component: 'ForgejoManagement',
            roles: ['admin'],
            name: 'Forgejo Git Server',
            nav: false
          }
        }
      },

      // Monitoring — consolidated from 12 nav items to 6
      monitoring: {
        section: 'Monitoring',
        icon: 'ChartBarIcon',
        roles: ['admin'],
        children: {
          analytics: {
            path: '/admin/monitoring/analytics',
            component: 'AnalyticsDashboard',
            roles: ['admin'],
            name: 'Analytics'
          },
          logs: {
            path: '/admin/monitoring/logs',
            component: 'Logs',
            roles: ['admin'],
            name: 'System Logs'
          },
          alerts: {
            path: '/admin/monitoring/alerts',
            component: 'AlertsManagement',
            roles: ['admin'],
            name: 'Alerts'
          },
          audit: {
            path: '/admin/monitoring/audit',
            component: 'SystemAuditLog',
            roles: ['admin'],
            name: 'Audit Log'
          },
          websiteMonitor: {
            path: '/admin/monitoring/website-monitor',
            component: 'WebsiteMonitor',
            roles: ['admin'],
            name: 'Uptime Monitor'
          },
          externalTools: {
            path: '/admin/monitoring/tools',
            component: 'ExternalMonitoringTools',
            roles: ['admin'],
            name: 'External Tools'
          },
          // Demoted from nav — accessible via External Tools or direct URL
          grafana: {
            path: '/admin/monitoring/grafana',
            component: 'GrafanaConfig',
            roles: ['admin'],
            name: 'Grafana',
            nav: false
          },
          grafanaDashboards: {
            path: '/admin/monitoring/grafana/dashboards',
            component: 'GrafanaViewer',
            roles: ['admin'],
            name: 'Grafana Dashboards',
            nav: false
          },
          prometheus: {
            path: '/admin/monitoring/prometheus',
            component: 'PrometheusConfig',
            roles: ['admin'],
            name: 'Prometheus',
            nav: false
          },
          umami: {
            path: '/admin/monitoring/umami',
            component: 'UmamiConfig',
            roles: ['admin'],
            name: 'Umami',
            nav: false
          },
          umamiDashboard: {
            path: '/admin/monitoring/umami-dashboard',
            component: 'UmamiConfig',
            roles: ['admin'],
            name: 'Umami Dashboard',
            nav: false
          },
          overview: {
            path: '/admin/monitoring/overview',
            component: 'MonitoringOverview',
            roles: ['admin'],
            name: 'Monitoring Overview',
            nav: false
          },
          analyticsAdvanced: {
            path: '/admin/monitoring/analytics/advanced',
            component: 'AdvancedAnalytics',
            roles: ['admin'],
            name: 'Advanced Analytics',
            nav: false
          },
          usageAnalytics: {
            path: '/admin/monitoring/usage-analytics',
            component: 'UsageAnalytics',
            roles: ['admin'],
            name: 'Usage Analytics',
            nav: false
          },
          usageMetrics: {
            path: '/admin/monitoring/usage-metrics',
            component: 'UsageMetrics',
            roles: ['admin'],
            name: 'Usage Metrics',
            nav: false
          }
        }
      },

      integrations: {
        section: 'Integrations',
        icon: 'LinkIcon',
        roles: ['admin'],
        children: {
          credentials: {
            path: '/admin/integrations/credentials',
            component: 'PlatformSettings',
            roles: ['admin'],
            name: 'API Credentials'
          },
          email: {
            path: '/admin/integrations/email',
            component: 'EmailSettings',
            roles: ['admin'],
            name: 'Email Providers'
          },
          dns: {
            path: '/admin/integrations/cloudflare',
            component: 'CloudflareDNS',
            roles: ['admin'],
            name: 'Cloudflare DNS'
          },
          webhooks: {
            path: '/admin/integrations/webhooks',
            component: 'WebhooksManagement',
            roles: ['admin'],
            name: 'Webhooks'
          }
        }
      },

      platform: {
        section: 'Platform',
        icon: 'SparklesIcon',
        roles: ['admin'],
        children: {
          centerDeep: {
            path: 'https://search.unicorncommander.ai',
            component: 'External',
            roles: ['admin'],
            name: 'Center-Deep Search',
            icon: 'MagnifyingGlassIcon',
            external: true
          },
          landing: {
            path: '/admin/platform/landing',
            component: 'LandingCustomization',
            roles: ['admin'],
            name: 'Landing Page'
          },
          whiteLabel: {
            path: '/admin/platform/white-label',
            component: 'WhiteLabelBuilder',
            roles: ['admin'],
            name: 'White Label'
          },
          systemSettings: {
            path: '/admin/system/settings',
            component: 'SystemSettings',
            roles: ['admin'],
            name: 'System Settings',
            icon: 'CogIcon'
          },
          extensions: {
            path: '/admin/platform/extensions',
            component: 'ExtensionsMarketplace',
            roles: ['admin'],
            name: 'Extensions Marketplace'
          },
          purchases: {
            path: '/admin/platform/purchases',
            component: 'PurchaseHistory',
            roles: ['admin'],
            name: 'Purchase History',
            nav: false
          }
        }
      }
    }
  },

  // ==========================================================================
  // REDIRECTS - Backwards compatibility for old routes
  // ==========================================================================
  redirects: [
    // Top-level legacy paths (commonly linked from external sources)
    { from: '/admin/models', to: '/admin/ai/registry', type: 'permanent' },
    { from: '/admin/system', to: '/admin/infra/resources', type: 'permanent' },
    { from: '/admin/network', to: '/admin/infra/network', type: 'permanent' },

    // People & Access
    { from: '/admin/system/users', to: '/admin/people/users', type: 'permanent' },
    { from: '/admin/system/users/:userId', to: '/admin/people/users/:userId', type: 'permanent' },
    { from: '/admin/organization/list', to: '/admin/people/organizations', type: 'permanent' },
    { from: '/admin/system/invite-codes', to: '/admin/people/invite-codes', type: 'permanent' },
    { from: '/admin/system/authentication', to: '/admin/people/authentication', type: 'permanent' },

    // Billing & Plans — old paths redirect to consolidated destinations
    { from: '/admin/system/subscription-management', to: '/admin/billing/tiers', type: 'permanent' },
    { from: '/admin/system/app-management', to: '/admin/billing/apps', type: 'permanent' },
    { from: '/admin/system/pricing-management', to: '/admin/billing/pricing', type: 'permanent' },
    { from: '/admin/system/billing', to: '/admin/billing/revenue', type: 'permanent' },
    { from: '/admin/billing/dashboard', to: '/admin/billing/revenue', type: 'permanent' },
    { from: '/admin/credits', to: '/admin/billing/credits', type: 'permanent' },
    { from: '/admin/credits/purchase', to: '/admin/billing/credits', type: 'permanent' },
    { from: '/admin/credits/tiers', to: '/admin/billing/tiers/compare', type: 'permanent' },

    // AI & Models
    { from: '/admin/llm-hub', to: '/admin/ai', type: 'permanent' },
    { from: '/admin/llm-management', to: '/admin/ai/management', type: 'permanent' },
    { from: '/admin/litellm-providers', to: '/admin/ai/providers', type: 'permanent' },
    { from: '/admin/llm-models', to: '/admin/ai/models', type: 'permanent' },
    { from: '/admin/system/models', to: '/admin/ai/registry', type: 'permanent' },
    { from: '/admin/openrouter-settings', to: '/admin/ai/openrouter', type: 'permanent' },
    { from: '/admin/llm/usage', to: '/admin/ai/usage', type: 'permanent' },
    { from: '/admin/system/model-lists', to: '/admin/ai/model-lists', type: 'permanent' },
    { from: '/admin/system/local-models', to: '/admin/ai/local-models', type: 'permanent' },
    { from: '/admin/system/rag-services', to: '/admin/ai/rag-services', type: 'permanent' },
    { from: '/admin/system/gpu-services', to: '/admin/ai/gpu-services', type: 'permanent' },

    // Infrastructure
    { from: '/admin/system/services', to: '/admin/infra/services', type: 'permanent' },
    { from: '/admin/system/resources', to: '/admin/infra/resources', type: 'permanent' },
    { from: '/admin/system/hardware', to: '/admin/infra/hardware', type: 'permanent' },
    { from: '/admin/infrastructure/hardware', to: '/admin/infra/hardware', type: 'permanent' },
    { from: '/admin/system/local-users', to: '/admin/infra/local-users', type: 'permanent' },
    { from: '/admin/system/network', to: '/admin/infra/network', type: 'permanent' },
    { from: '/admin/system/storage', to: '/admin/infra/storage', type: 'permanent' },
    { from: '/admin/system/traefik', to: '/admin/infra/traefik', type: 'permanent' },
    { from: '/admin/traefik/dashboard', to: '/admin/infra/traefik/dashboard', type: 'permanent' },
    { from: '/admin/traefik/routes', to: '/admin/infra/traefik/routes', type: 'permanent' },
    { from: '/admin/traefik/services', to: '/admin/infra/traefik/services', type: 'permanent' },
    { from: '/admin/traefik/ssl', to: '/admin/infra/traefik/ssl', type: 'permanent' },
    { from: '/admin/traefik/metrics', to: '/admin/infra/traefik/metrics', type: 'permanent' },
    { from: '/admin/infrastructure/migration', to: '/admin/infra/migration', type: 'permanent' },

    // Monitoring — old paths redirect to consolidated destinations
    { from: '/admin/analytics', to: '/admin/monitoring/analytics', type: 'permanent' },
    { from: '/admin/system/analytics', to: '/admin/monitoring/analytics', type: 'permanent' },
    { from: '/admin/system/usage-analytics', to: '/admin/monitoring/analytics', type: 'permanent' },
    { from: '/admin/system/usage-metrics', to: '/admin/monitoring/analytics', type: 'permanent' },

    // Integrations
    { from: '/admin/platform/settings', to: '/admin/integrations/credentials', type: 'permanent' },
    { from: '/admin/platform/email-settings', to: '/admin/integrations/email', type: 'permanent' },
    { from: '/admin/infrastructure/cloudflare', to: '/admin/integrations/cloudflare', type: 'permanent' },

    // Platform
    { from: '/admin/system/landing', to: '/admin/platform/landing', type: 'permanent' },
    { from: '/admin/system/extensions', to: '/admin/platform/extensions', type: 'permanent' },
    { from: '/admin/extensions', to: '/admin/platform/extensions', type: 'permanent' },
    { from: '/admin/purchases', to: '/admin/platform/purchases', type: 'permanent' },

    // Legacy personal routes
    { from: '/admin/user-settings', to: '/admin/account/profile', type: 'permanent' },
    { from: '/admin/billing', to: '/admin/subscription/plan', type: 'permanent' }
  ]
};

// ==========================================================================
// HELPER FUNCTIONS
// ==========================================================================

function flattenRoutes(node, acc) {
  if (!node) return acc;
  if (node.path) {
    acc.push(node);
  }
  if (node.children) {
    Object.values(node.children).forEach(child => flattenRoutes(child, acc));
  }
  return acc;
}

/**
 * Get all routes as a flat array (useful for React Router)
 */
export function getAllRoutes() {
  const allRoutes = [];

  flattenRoutes(routes.personal, allRoutes);
  flattenRoutes(routes.organization, allRoutes);
  flattenRoutes(routes.system, allRoutes);

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

function normalizePath(path) {
  if (!path) return path;
  if (path.length > 1 && path.endsWith('/')) {
    return path.slice(0, -1);
  }
  return path;
}

function pathToRegex(path) {
  const normalized = normalizePath(path);
  const escaped = normalized
    .replace(/\//g, '\\/')
    .replace(/:[^/]+/g, '[^/]+');
  return new RegExp(`^${escaped}\\/?$`);
}

/**
 * Find a route by pathname (supports :param matching)
 */
export function getRouteByPath(pathname) {
  const allRoutes = getAllRoutes();
  const normalized = normalizePath(pathname);
  return allRoutes.find(route => pathToRegex(route.path).test(normalized));
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
  if (route.roles && !route.roles.includes(userRole)) {
    return false;
  }

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
