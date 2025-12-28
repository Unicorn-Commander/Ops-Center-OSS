/**
 * Tooltip Content for UC-Cloud Ops-Center
 *
 * Provides comprehensive help tooltips across the application.
 * Used by: HelpTooltip component throughout the application
 *
 * @module tooltipContent
 */

const tooltips = {
  // ============================================================
  // User Management
  // ============================================================
  users: {
    subscriptionTier: {
      title: 'Subscription Tier',
      content: 'The user\'s current subscription plan: Trial (7 days), Starter ($19/mo), Professional ($49/mo), or Enterprise ($99/mo). Each tier has different API call limits and feature access.'
    },
    roleHierarchy: {
      title: 'Role Hierarchy',
      content: 'Roles follow a strict hierarchy: Admin > Moderator > Developer > Analyst > Viewer. Higher roles can manage lower roles but not vice versa.'
    },
    impersonation: {
      title: 'User Impersonation',
      content: 'Admins can "login as" a user to troubleshoot issues or test permissions. Session expires after 24 hours. All actions are logged in the audit trail.'
    },
    apiKeys: {
      title: 'API Keys',
      content: 'Unique authentication tokens for programmatic API access. Keys are hashed with bcrypt and cannot be recovered - only regenerated.'
    },
    bulkOperations: {
      title: 'Bulk Operations',
      content: 'Select multiple users to perform batch actions: assign roles, change tiers, suspend, or delete. CSV import/export supports up to 1,000 users at once.'
    }
  },

  // ============================================================
  // Billing & Subscriptions
  // ============================================================
  billing: {
    lagoIntegration: {
      title: 'Lago Billing',
      content: 'UC-Cloud uses Lago for subscription management and Stripe for payment processing. All billing is usage-based with monthly limits.'
    },
    apiCallMetering: {
      title: 'API Call Metering',
      content: 'API calls are tracked in real-time and reset monthly. Overage fees apply for Professional/Enterprise tiers. Trial and Starter plans have hard limits.'
    },
    stripeCheckout: {
      title: 'Stripe Checkout',
      content: 'Secure payment processing through Stripe. Supports credit cards, Apple Pay, Google Pay. All payment data is PCI-compliant and never stored on our servers.'
    },
    invoiceHistory: {
      title: 'Invoice History',
      content: 'View all past invoices, payment receipts, and upcoming charges. Download PDFs for accounting purposes.'
    }
  },

  // ============================================================
  // Organizations
  // ============================================================
  organizations: {
    teamManagement: {
      title: 'Team Management',
      content: 'Invite team members, assign roles, and manage access. Professional tier supports 3 members, Enterprise tier supports 5+ (additional seats $15/mo each).'
    },
    roleAssignment: {
      title: 'Role Assignment',
      content: 'Organization roles: Owner (full control), Admin (manage members), Member (service access). System roles are separate from organization roles.'
    },
    organizationBilling: {
      title: 'Organization Billing',
      content: 'Enterprise tier includes organization-level billing. All team member usage is aggregated and billed to the organization owner.'
    }
  },

  // ============================================================
  // Services
  // ============================================================
  services: {
    serviceStatus: {
      title: 'Service Status',
      content: 'Real-time status of Docker containers: Operational (green), Degraded (yellow), Down (red), Optional (blue). Click for detailed logs.'
    },
    dependencies: {
      title: 'Service Dependencies',
      content: 'Some services depend on others to function. For example, Open-WebUI requires vLLM, PostgreSQL, Redis, and Qdrant to be operational.'
    },
    portMapping: {
      title: 'Port Mapping',
      content: 'Services expose ports for API access. External URLs use Traefik reverse proxy with SSL/TLS. Local URLs are for development/debugging.'
    },
    healthChecks: {
      title: 'Health Checks',
      content: 'Automated health checks run every 30 seconds. Failed checks trigger alerts and automatic restart attempts.'
    }
  },

  // ============================================================
  // LLM Management
  // ============================================================
  llm: {
    modelProviders: {
      title: 'Model Providers',
      content: 'UC-Cloud supports multiple LLM providers: OpenAI, Anthropic, Google, Cohere, OpenRouter, and local models via vLLM. Configure API keys and fallback routing.'
    },
    byokSupport: {
      title: 'BYOK (Bring Your Own Key)',
      content: 'Starter tier and above can use their own API keys for LLM providers. This bypasses usage limits and billing, but you pay the provider directly.'
    },
    modelSwitching: {
      title: 'Model Switching',
      content: 'Switch between models without restarting services. vLLM supports hot-swapping with PagedAttention for minimal downtime.'
    },
    executionServers: {
      title: 'Execution Servers',
      content: 'LiteLLM proxy can route requests to multiple backend servers for load balancing and redundancy. Supports local vLLM and remote API endpoints.'
    }
  },

  // ============================================================
  // Hardware & Resources
  // ============================================================
  hardware: {
    gpuMonitoring: {
      title: 'GPU Monitoring',
      content: 'Real-time NVIDIA GPU utilization via nvidia-smi. Track VRAM usage, temperature, and power draw. RTX 5090 optimized for LLM inference.'
    },
    memoryManagement: {
      title: 'Memory Management',
      content: 'vLLM uses PagedAttention for efficient GPU memory allocation. Configure GPU_MEMORY_UTIL (default 95%) to balance performance and stability.'
    },
    cpuAllocation: {
      title: 'CPU Allocation',
      content: 'Embeddings, reranker, and support services run on CPU. Monitor CPU usage to prevent bottlenecks. Docker containers have configurable CPU limits.'
    }
  },

  // ============================================================
  // Security & Authentication
  // ============================================================
  security: {
    keycloakSSO: {
      title: 'Keycloak SSO',
      content: 'Centralized authentication via Keycloak uchub realm. Supports social login (Google, GitHub, Microsoft), MFA, and OAuth2/OIDC protocols.'
    },
    rbacPermissions: {
      title: 'RBAC Permissions',
      content: 'Role-Based Access Control with granular permissions. Each role has specific allowed actions (read, write, execute, admin) per resource category.'
    },
    apiKeyRotation: {
      title: 'API Key Rotation',
      content: 'Best practice: rotate API keys every 90 days. Ops-Center tracks key age and sends expiration warnings. Old keys are automatically revoked after 120 days.'
    },
    auditLogging: {
      title: 'Audit Logging',
      content: 'All sensitive actions are logged: user changes, role assignments, service restarts, billing updates. Logs are immutable and retained for 90 days.'
    }
  },

  // ============================================================
  // Extensions
  // ============================================================
  extensions: {
    dockerContainer: {
      title: 'Docker Container',
      content: 'Extensions run in isolated Docker containers for security and resource management. Each container has CPU/memory limits and network isolation.'
    },
    extensionStatus: {
      title: 'Extension Status',
      content: 'Shows the current status of the extension: running (green), stopped (gray), error (red). Click to view logs or restart.'
    },
    brigadePlatform: {
      title: 'Unicorn Brigade',
      content: 'Agent factory platform with 47+ pre-built domain specialists. Create custom agents via Gunny conversational builder or use The General orchestrator.'
    },
    centerDeepSearch: {
      title: 'Center-Deep Pro',
      content: 'Enterprise metasearch engine querying 70+ search engines simultaneously. Includes 4 AI tool servers for specialized search tasks.'
    }
  },

  // ============================================================
  // UI Components
  // ============================================================
  ui: {
    refreshButton: {
      title: 'Refresh',
      content: 'Click to refresh the current data from the server. Uses cached data if available (60-second TTL).'
    },
    filterPanel: {
      title: 'Advanced Filters',
      content: 'Combine multiple filters for precise data queries. Filters persist in URL params for bookmarking. Use "Clear All" to reset.'
    },
    pagination: {
      title: 'Pagination',
      content: 'Navigate large datasets with pagination. Adjust rows per page (10, 25, 50, 100) or use keyboard shortcuts (← →) for navigation.'
    },
    exportData: {
      title: 'Export Data',
      content: 'Export visible data to CSV format. Respects current filters and sorting. Max 10,000 rows per export to prevent browser crashes.'
    },
    chartInteraction: {
      title: 'Interactive Charts',
      content: 'Click chart legends to toggle data series. Hover for tooltips. Use mouse wheel to zoom on time-series charts.'
    }
  },

  // ============================================================
  // Analytics & Monitoring
  // ============================================================
  analytics: {
    usageMetrics: {
      title: 'Usage Metrics',
      content: 'Track API calls, token consumption, and service usage over time. Metrics update hourly. Real-time data available for Enterprise tier.'
    },
    costTracking: {
      title: 'Cost Tracking',
      content: 'Monitor LLM API costs by provider, model, and user. Professional/Enterprise tiers include cost optimization recommendations.'
    },
    performanceMonitoring: {
      title: 'Performance Monitoring',
      content: 'Track request latency, error rates, and throughput. Integrates with Prometheus/Grafana for advanced monitoring (Enterprise tier).'
    }
  },

  // ============================================================
  // System Settings
  // ============================================================
  settings: {
    emailProvider: {
      title: 'Email Provider',
      content: 'Configure SMTP or Microsoft 365 OAuth2 for transactional emails. Test email functionality before enabling production notifications.'
    },
    notificationSettings: {
      title: 'Notification Settings',
      content: 'Control which events trigger email notifications: billing updates, service alerts, security events, usage warnings. Customize per-user.'
    },
    systemBackups: {
      title: 'System Backups',
      content: 'Automated daily backups to local storage. Includes databases, configurations, and user data. Retention: 7 days (configurable).'
    }
  }
};

/**
 * Get tooltip by category and key
 * @param {string} category - Tooltip category
 * @param {string} key - Tooltip key within category
 * @returns {Object} Tooltip object with title and content
 */
export function getTooltip(category, key) {
  return tooltips[category]?.[key] || { title: 'Help', content: 'No description available' };
}

/**
 * Get all tooltips for a category
 * @param {string} category - Tooltip category
 * @returns {Object} All tooltips in the category
 */
export function getCategoryTooltips(category) {
  return tooltips[category] || {};
}

/**
 * Get all available categories
 * @returns {Array} Array of category names
 */
export function getCategories() {
  return Object.keys(tooltips);
}

/**
 * Search tooltips by text
 * @param {string} searchText - Text to search for
 * @returns {Array} Array of matching tooltips with category and key
 */
export function searchTooltips(searchText) {
  const results = [];
  const search = searchText.toLowerCase();

  Object.entries(tooltips).forEach(([category, items]) => {
    Object.entries(items).forEach(([key, tooltip]) => {
      if (
        tooltip.title.toLowerCase().includes(search) ||
        tooltip.content.toLowerCase().includes(search)
      ) {
        results.push({ category, key, ...tooltip });
      }
    });
  });

  return results;
}

/**
 * Tooltip presets for common UI patterns
 */
export const tooltipPresets = {
  save: { title: 'Save Changes', content: 'Click to save your changes. Unsaved changes will be lost.' },
  cancel: { title: 'Cancel', content: 'Discard changes and return to the previous view.' },
  delete: { title: 'Delete', content: 'Permanently delete this item. This action cannot be undone.' },
  edit: { title: 'Edit', content: 'Modify this item\'s settings and properties.' },
  refresh: { title: 'Refresh', content: 'Reload data from the server. Cached data: 60s TTL.' },
  filter: { title: 'Filter', content: 'Apply filters to narrow down the results.' },
  export: { title: 'Export', content: 'Export data to CSV format (max 10,000 rows).' },
  import: { title: 'Import', content: 'Import data from CSV file (max 1,000 rows).' },
  help: { title: 'Help', content: 'View documentation and help resources.' },
  settings: { title: 'Settings', content: 'Configure application preferences and options.' }
};

export default tooltips;
