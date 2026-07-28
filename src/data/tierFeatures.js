/**
 * Subscription Tier Features for UC-Cloud
 *
 * Defines all subscription plans, their features, limits, and pricing.
 * Used by: SubscriptionPlan, BillingDashboard, UserManagement
 *
 * Synced with Lago billing system plan codes.
 *
 * @module tierFeatures
 */

/**
 * Subscription tier feature definitions
 */
export const tierFeatures = {
  trial: {
    // Basic information
    name: 'Trial',
    code: 'trial',
    tagline: 'Try before you buy',
    description: 'Explore UC-Cloud with limited features for 7 days',

    // Pricing
    price: '$1.00',
    period: 'week',
    billingPeriod: 'Weekly',
    currency: 'USD',
    trialDays: 7,

    // Visual styling
    color: 'info',
    icon: 'science',
    badge: null,
    popular: false,

    // Features list (shown in UI)
    features: [
      '100 API calls per day (700 total)',
      'Open-WebUI chat access',
      'Basic AI models (GPT-3.5 equivalent)',
      'Community support',
      'Email notifications',
      'Basic documentation access'
    ],

    // Limitations
    limitations: [
      'No BYOK (Bring Your Own Key)',
      'No API access',
      'No organization features',
      'No priority support',
      'Limited model selection'
    ],

    // Quota limits
    limits: {
      api_calls_daily: 100,
      api_calls_total: 700,
      models: ['gpt-3.5-turbo', 'qwen-2.5-7b'],
      organizations: 0,
      team_members: 1,
      api_keys: 0,
      storage_gb: 1,
      concurrent_requests: 2,
      max_context_tokens: 4096,
      support: 'community'
    },

    // Service access
    services: {
      'open-webui': true,
      'vllm': true,
      'center-deep': false,
      'brigade': false,
      'unicorn-orator': false,
      'unicorn-amanuensis': false,
      'litellm': false
    },

    // Lago plan details
    lago: {
      planId: 'bbbba413-45de-468d-b03e-f23713684354',
      planCode: 'trial',
      meteringEnabled: true,
      autoRenew: false
    }
  },

  starter: {
    // Basic information
    name: 'Starter',
    code: 'starter',
    tagline: 'Perfect for individuals',
    description: 'Essential AI tools for personal projects and learning',

    // Pricing
    price: '$19.00',
    period: 'month',
    billingPeriod: 'Monthly',
    currency: 'USD',
    trialDays: 0,

    // Visual styling
    color: 'success',
    icon: 'rocket_launch',
    badge: null,
    popular: false,

    // Features list
    features: [
      '1,000 API calls per month',
      'Open-WebUI + Center-Deep access',
      'All AI models (GPT-4, Claude, Qwen)',
      'BYOK support (Bring Your Own API Keys)',
      'Email support (24hr response)',
      'Full documentation access',
      'API access with rate limiting',
      'Basic analytics dashboard'
    ],

    // Limitations
    limitations: [
      'No organization features',
      'No priority support',
      'No custom integrations',
      'Limited concurrent requests'
    ],

    // Quota limits
    limits: {
      api_calls_monthly: 1000,
      api_calls_daily: 100,
      models: 'all',
      organizations: 0,
      team_members: 1,
      api_keys: 5,
      storage_gb: 5,
      concurrent_requests: 5,
      max_context_tokens: 16384,
      support: 'email',
      byok: true
    },

    // Service access
    services: {
      'open-webui': true,
      'vllm': true,
      'center-deep': true,
      'brigade': false,
      'unicorn-orator': true,
      'unicorn-amanuensis': true,
      'litellm': true
    },

    // Lago plan details
    lago: {
      planId: '02a9058d-e0f6-4e09-9c39-a775d57676d1',
      planCode: 'starter',
      meteringEnabled: true,
      autoRenew: true
    }
  },

  professional: {
    // Basic information
    name: 'Professional',
    code: 'professional',
    tagline: 'For serious developers',
    description: 'Advanced features for professional development and production use',

    // Pricing
    price: '$49.00',
    period: 'month',
    billingPeriod: 'Monthly',
    currency: 'USD',
    trialDays: 0,

    // Visual styling
    color: 'primary',
    icon: 'workspace_premium',
    badge: 'Most Popular',
    popular: true,

    // Features list
    features: [
      '10,000 API calls per month',
      'All services access (Chat, Search, Voice, Agents)',
      'Unlimited AI models',
      'BYOK support with usage optimization',
      'Billing dashboard with cost analytics',
      'Priority email support (4hr response)',
      'Advanced API features',
      'Real-time usage monitoring',
      'Unicorn Brigade agent platform',
      'Custom agent creation',
      'Webhook integrations'
    ],

    // Limitations
    limitations: [
      'No team management',
      'No white-label options',
      'No dedicated support'
    ],

    // Quota limits
    limits: {
      api_calls_monthly: 10000,
      api_calls_daily: 500,
      models: 'all',
      organizations: 1,
      team_members: 3,
      api_keys: 10,
      storage_gb: 25,
      concurrent_requests: 20,
      max_context_tokens: 32768,
      support: 'priority',
      byok: true,
      webhooks: 5,
      custom_agents: 10
    },

    // Service access
    services: {
      'open-webui': true,
      'vllm': true,
      'center-deep': true,
      'brigade': true,
      'unicorn-orator': true,
      'unicorn-amanuensis': true,
      'litellm': true,
      'magicdeck': true
    },

    // Lago plan details
    lago: {
      planId: '0eefed2d-cdf8-4d0a-b5d0-852dacf9909d',
      planCode: 'professional',
      meteringEnabled: true,
      autoRenew: true
    }
  },

  enterprise: {
    // Basic information
    name: 'Enterprise',
    code: 'enterprise',
    tagline: 'For teams and businesses',
    description: 'Unlimited access with team management and dedicated support',

    // Pricing
    price: '$99.00',
    period: 'month',
    billingPeriod: 'Monthly',
    currency: 'USD',
    trialDays: 0,

    // Visual styling
    color: 'secondary',
    icon: 'domain',
    badge: 'Best Value',
    popular: false,

    // Features list
    features: [
      'Unlimited API calls',
      'All services with unlimited usage',
      'Team management (5 seats included)',
      'Organization-level billing',
      'Custom integrations and workflows',
      '24/7 dedicated support (1hr response)',
      'Priority queue for all services',
      'White-label options available',
      'Custom domain support',
      'Advanced security features',
      'SSO/SAML integration',
      'Unlimited webhooks',
      'Unlimited custom agents',
      'Data residency options',
      'SLA guarantee (99.9% uptime)'
    ],

    // Limitations
    limitations: [
      // No limitations - enterprise tier
    ],

    // Quota limits
    limits: {
      api_calls_monthly: -1, // unlimited
      api_calls_daily: -1,
      models: 'all',
      organizations: 1,
      team_members: 5, // included, can purchase more
      additional_seats_price: 15, // per seat/month
      api_keys: 50,
      storage_gb: 100,
      concurrent_requests: 100,
      max_context_tokens: 128000,
      support: 'dedicated',
      byok: true,
      webhooks: -1, // unlimited
      custom_agents: -1,
      white_label: true,
      custom_domain: true,
      sso: true,
      sla: '99.9%'
    },

    // Service access
    services: {
      'open-webui': true,
      'vllm': true,
      'center-deep': true,
      'brigade': true,
      'unicorn-orator': true,
      'unicorn-amanuensis': true,
      'litellm': true,
      'magicdeck': true,
      'grafana': true,
      'prometheus': true
    },

    // Lago plan details
    lago: {
      planId: 'ee2d9d3d-e985-4166-97ba-2fd6e8cd5b0b',
      planCode: 'enterprise',
      meteringEnabled: true,
      autoRenew: true
    }
  }
};

/**
 * Tier comparison matrix (what each tier includes)
 */
export const tierComparison = {
  features: [
    {
      category: 'API Access',
      items: [
        { name: 'API Calls per Month', trial: '700 total', starter: '1,000', professional: '10,000', enterprise: 'Unlimited' },
        { name: 'API Keys', trial: '0', starter: '5', professional: '10', enterprise: '50' },
        { name: 'Concurrent Requests', trial: '2', starter: '5', professional: '20', enterprise: '100' }
      ]
    },
    {
      category: 'Services',
      items: [
        { name: 'Open-WebUI Chat', trial: true, starter: true, professional: true, enterprise: true },
        { name: 'Center-Deep Search', trial: false, starter: true, professional: true, enterprise: true },
        { name: 'Unicorn Brigade Agents', trial: false, starter: false, professional: true, enterprise: true },
        { name: 'Voice Services (TTS/STT)', trial: false, starter: true, professional: true, enterprise: true }
      ]
    },
    {
      category: 'AI Models',
      items: [
        { name: 'Basic Models', trial: true, starter: true, professional: true, enterprise: true },
        { name: 'Advanced Models (GPT-4, Claude)', trial: false, starter: true, professional: true, enterprise: true },
        { name: 'BYOK (Bring Your Own Keys)', trial: false, starter: true, professional: true, enterprise: true },
        { name: 'Model Priority Queue', trial: false, starter: false, professional: false, enterprise: true }
      ]
    },
    {
      category: 'Team & Organization',
      items: [
        { name: 'Organizations', trial: '0', starter: '0', professional: '1', enterprise: '1' },
        { name: 'Team Members', trial: '1', starter: '1', professional: '3', enterprise: '5+' },
        { name: 'Role-Based Access', trial: false, starter: false, professional: true, enterprise: true },
        { name: 'SSO/SAML', trial: false, starter: false, professional: false, enterprise: true }
      ]
    },
    {
      category: 'Support',
      items: [
        { name: 'Community Support', trial: true, starter: false, professional: false, enterprise: false },
        { name: 'Email Support', trial: false, starter: '24hr', professional: '4hr', enterprise: '1hr' },
        { name: 'Priority Support', trial: false, starter: false, professional: true, enterprise: true },
        { name: 'Dedicated Support', trial: false, starter: false, professional: false, enterprise: true }
      ]
    },
    {
      category: 'Advanced Features',
      items: [
        { name: 'Billing Dashboard', trial: false, starter: false, professional: true, enterprise: true },
        { name: 'Usage Analytics', trial: false, starter: 'Basic', professional: 'Advanced', enterprise: 'Real-time' },
        { name: 'Webhooks', trial: '0', starter: '0', professional: '5', enterprise: 'Unlimited' },
        { name: 'Custom Agents', trial: '0', starter: '0', professional: '10', enterprise: 'Unlimited' },
        { name: 'White-Label Options', trial: false, starter: false, professional: false, enterprise: true },
        { name: 'SLA Guarantee', trial: false, starter: false, professional: false, enterprise: '99.9%' }
      ]
    }
  ]
};

/**
 * Tier hierarchy (lowest to highest)
 */
export const tierHierarchy = ['trial', 'starter', 'professional', 'enterprise'];

/**
 * Get tier by code
 * @param {string} tierCode - Tier code (trial, starter, professional, enterprise)
 * @returns {Object|null} Tier details or null if not found
 */
export function getTier(tierCode) {
  return tierFeatures[tierCode] || null;
}

/**
 * Get all available tiers
 * @returns {Array} Array of tier objects with codes
 */
export function getAllTiers() {
  return Object.entries(tierFeatures).map(([code, tier]) => ({ code, ...tier }));
}

/**
 * Compare tier levels
 * @param {string} tierA - First tier code
 * @param {string} tierB - Second tier code
 * @returns {number} -1 if tierA < tierB, 0 if equal, 1 if tierA > tierB
 */
export function compareTiers(tierA, tierB) {
  const indexA = tierHierarchy.indexOf(tierA);
  const indexB = tierHierarchy.indexOf(tierB);

  if (indexA === -1 || indexB === -1) return 0;

  if (indexA < indexB) return -1;
  if (indexA > indexB) return 1;
  return 0;
}

/**
 * Check if upgrade is available
 * @param {string} currentTier - Current tier code
 * @param {string} targetTier - Target tier code
 * @returns {boolean} True if upgrade is possible
 */
export function canUpgrade(currentTier, targetTier) {
  return compareTiers(currentTier, targetTier) === -1;
}

/**
 * Get next tier in hierarchy
 * @param {string} currentTier - Current tier code
 * @returns {string|null} Next tier code or null if at max
 */
export function getNextTier(currentTier) {
  const index = tierHierarchy.indexOf(currentTier);
  if (index === -1 || index === tierHierarchy.length - 1) return null;
  return tierHierarchy[index + 1];
}

/**
 * Calculate price difference between tiers
 * @param {string} fromTier - Starting tier code
 * @param {string} toTier - Target tier code
 * @returns {number} Price difference in USD
 */
export function getPriceDifference(fromTier, toTier) {
  const from = getTier(fromTier);
  const to = getTier(toTier);

  if (!from || !to) return 0;

  const fromPrice = parseFloat(from.price.replace('$', ''));
  const toPrice = parseFloat(to.price.replace('$', ''));

  return toPrice - fromPrice;
}

/**
 * Check if feature is available in tier
 * @param {string} tierCode - Tier code
 * @param {string} feature - Feature name
 * @returns {boolean} True if feature is available
 */
export function hasFeature(tierCode, feature) {
  const tier = getTier(tierCode);
  if (!tier) return false;

  return tier.features.some(f =>
    f.toLowerCase().includes(feature.toLowerCase())
  );
}

/**
 * Get service access for tier
 * @param {string} tierCode - Tier code
 * @param {string} serviceKey - Service identifier
 * @returns {boolean} True if service is accessible
 */
export function hasServiceAccess(tierCode, serviceKey) {
  const tier = getTier(tierCode);
  if (!tier) return false;

  return tier.services[serviceKey] === true;
}

export default tierFeatures;
