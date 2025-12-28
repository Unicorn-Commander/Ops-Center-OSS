/**
 * Service Descriptions for UC-Cloud Ecosystem
 *
 * Provides comprehensive metadata for all services managed by Ops-Center.
 * Used by: ServiceCard, Dashboard, Service Management pages
 *
 * @module serviceDescriptions
 */

export const serviceDescriptions = {
  // ============================================================
  // AI Services - LLM, Chat, and AI Infrastructure
  // ============================================================
  'open-webui': {
    name: 'Open-WebUI',
    description: 'AI chat interface with multi-model support and conversation management',
    category: 'AI Services',
    url: 'https://chat.your-domain.com',
    localUrl: 'http://localhost:8080',
    port: 8080,
    icon: 'chat',
    status: 'operational',
    features: [
      'Multi-model LLM support',
      'Conversation history',
      'File uploads',
      'Code execution',
      'Document Q&A'
    ],
    dependencies: ['vllm', 'postgres', 'redis', 'qdrant']
  },

  'vllm': {
    name: 'vLLM',
    description: 'High-performance LLM inference engine optimized for NVIDIA RTX GPUs',
    category: 'AI Services',
    url: 'http://localhost:8000',
    port: 8000,
    icon: 'memory',
    status: 'operational',
    features: [
      'GPU-accelerated inference',
      'Continuous batching',
      'PagedAttention memory optimization',
      'OpenAI-compatible API',
      'Multi-model support'
    ],
    hardware: ['NVIDIA RTX 5090 (32GB VRAM)'],
    dependencies: []
  },

  'litellm': {
    name: 'LiteLLM Proxy',
    description: 'Unified LLM API proxy supporting 100+ providers with load balancing',
    category: 'AI Services',
    url: 'http://localhost:4000',
    port: 4000,
    icon: 'hub',
    status: 'operational',
    features: [
      '100+ LLM providers',
      'OpenAI-compatible API',
      'Load balancing',
      'Fallback routing',
      'Cost tracking',
      'Rate limiting'
    ],
    dependencies: ['redis']
  },

  'embeddings': {
    name: 'Text Embeddings',
    description: 'Vector embedding service for semantic search and RAG applications',
    category: 'AI Services',
    url: 'http://localhost:8082',
    port: 8082,
    icon: 'share',
    status: 'operational',
    features: [
      'BAAI/bge-base-en-v1.5 model',
      'Batch processing',
      'Cosine similarity search',
      'Document chunking'
    ],
    dependencies: ['qdrant']
  },

  'reranker': {
    name: 'Document Reranker',
    description: 'Semantic reranking service for improved search relevance',
    category: 'AI Services',
    url: 'http://localhost:8083',
    port: 8083,
    icon: 'sort',
    status: 'operational',
    features: [
      'BAAI/bge-reranker-v2-m3 model',
      'Cross-encoder architecture',
      'Multilingual support',
      'High precision ranking'
    ],
    dependencies: []
  },

  // ============================================================
  // Voice Services - TTS and STT
  // ============================================================
  'unicorn-orator': {
    name: 'Unicorn Orator',
    description: 'Professional TTS service with 20+ voices and emotion control',
    category: 'Voice Services',
    url: 'https://tts.your-domain.com',
    localUrl: 'http://localhost:8885',
    port: 8885,
    icon: 'record_voice_over',
    status: 'operational',
    features: [
      'OpenAI-compatible API',
      '20+ voice profiles',
      'SSML support',
      'Emotion control',
      'Multi-language support',
      'GPU/CPU/NPU hardware detection'
    ],
    dependencies: []
  },

  'unicorn-amanuensis': {
    name: 'Unicorn Amanuensis',
    description: 'Professional STT service with speaker diarization and 100+ languages',
    category: 'Voice Services',
    url: 'https://stt.your-domain.com',
    localUrl: 'http://localhost:9003',
    port: 9003,
    icon: 'hearing',
    status: 'operational',
    features: [
      'OpenAI-compatible API',
      'WhisperX-based transcription',
      'Speaker diarization',
      '100+ language support',
      'Word-level timestamps',
      'Web interface at /web'
    ],
    dependencies: []
  },

  // ============================================================
  // Agent Platform - Unicorn Brigade
  // ============================================================
  'brigade': {
    name: 'Unicorn Brigade',
    description: 'Multi-agent AI platform with 47+ pre-built domain specialists',
    category: 'Agent Platform',
    url: 'https://brigade.your-domain.com',
    localUrl: 'http://localhost:8102',
    port: 8102,
    apiPort: 8101,
    icon: 'groups',
    status: 'operational',
    features: [
      'The General orchestrator',
      '47+ pre-built agents',
      'Conversational agent builder (Gunny)',
      'A2A protocol support',
      'Multi-provider LLM',
      '12+ built-in tools'
    ],
    dependencies: ['postgres', 'redis', 'keycloak']
  },

  // ============================================================
  // Search Services - Center-Deep Pro
  // ============================================================
  'center-deep': {
    name: 'Center-Deep Pro',
    description: 'Enterprise AI-powered metasearch engine with 70+ search engines',
    category: 'Search',
    url: 'https://search.your-domain.com',
    localUrl: 'http://localhost:8888',
    port: 8888,
    icon: 'search',
    status: 'operational',
    features: [
      '70+ search engines',
      'AI tool servers (4 specialized)',
      'Admin dashboard',
      'BrightData proxy integration',
      'Privacy-focused metasearch',
      'SSO authentication'
    ],
    dependencies: ['redis', 'vllm']
  },

  // ============================================================
  // Infrastructure Services
  // ============================================================
  'postgres': {
    name: 'PostgreSQL',
    description: 'Relational database for user data, organizations, and application state',
    category: 'Infrastructure',
    port: 5432,
    icon: 'storage',
    status: 'operational',
    features: [
      'PostgreSQL 16',
      'Multiple databases (unicorn_db, brigade_db)',
      'ACID compliance',
      'Full-text search',
      'JSON/JSONB support'
    ],
    databases: ['unicorn_db', 'brigade_db', 'lago'],
    dependencies: []
  },

  'redis': {
    name: 'Redis',
    description: 'In-memory cache and message broker for session management and caching',
    category: 'Infrastructure',
    port: 6379,
    icon: 'speed',
    status: 'operational',
    features: [
      'Redis 7.4',
      'Session storage',
      'Cache management',
      'Message queues',
      'Pub/sub messaging'
    ],
    dependencies: []
  },

  'qdrant': {
    name: 'Qdrant Vector Database',
    description: 'High-performance vector database for semantic search and RAG',
    category: 'Infrastructure',
    port: 6333,
    httpPort: 6334,
    icon: 'dataset',
    status: 'operational',
    features: [
      'Vector similarity search',
      'Metadata filtering',
      'Real-time indexing',
      'Distributed architecture',
      'REST and gRPC APIs'
    ],
    dependencies: []
  },

  // ============================================================
  // Security & Authentication
  // ============================================================
  'keycloak': {
    name: 'Keycloak SSO',
    description: 'Identity and access management with multi-provider authentication',
    category: 'Security',
    url: 'https://auth.your-domain.com',
    localUrl: 'http://localhost:8080',
    port: 8080,
    icon: 'vpn_key',
    status: 'operational',
    realm: 'uchub',
    features: [
      'Single Sign-On (SSO)',
      'Social login (Google, GitHub, Microsoft)',
      'RBAC (Role-Based Access Control)',
      'Multi-factor authentication',
      'User federation',
      'OAuth2/OIDC protocols'
    ],
    dependencies: ['postgres']
  },

  'traefik': {
    name: 'Traefik Reverse Proxy',
    description: 'Cloud-native reverse proxy with automatic SSL/TLS certificate management',
    category: 'Infrastructure',
    port: 80,
    httpsPort: 443,
    icon: 'router',
    status: 'operational',
    features: [
      "Let's Encrypt integration",
      'Automatic SSL/TLS',
      'Load balancing',
      'Health checks',
      'Docker integration',
      'Dynamic configuration'
    ],
    dependencies: []
  },

  // ============================================================
  // Billing & Analytics
  // ============================================================
  'lago': {
    name: 'Lago Billing',
    description: 'Open-source subscription billing and metering platform',
    category: 'Billing',
    url: 'https://billing.your-domain.com',
    localUrl: 'http://localhost:3000',
    port: 3000,
    icon: 'payments',
    status: 'operational',
    features: [
      'Subscription management',
      'Usage-based billing',
      'Stripe integration',
      'Invoice generation',
      'Webhook events',
      'Analytics dashboard'
    ],
    plans: ['trial', 'starter', 'professional', 'enterprise'],
    dependencies: ['postgres', 'redis']
  },

  // ============================================================
  // Development & Extensions
  // ============================================================
  'bolt-diy': {
    name: 'Bolt.DIY',
    description: 'AI-powered web development environment for rapid prototyping',
    category: 'Development',
    url: 'http://localhost:5173',
    port: 5173,
    icon: 'code',
    status: 'optional',
    features: [
      'AI-assisted coding',
      'Live preview',
      'Component library',
      'Deployment tools'
    ],
    dependencies: []
  },

  'magicdeck': {
    name: 'MagicDeck',
    description: 'AI-powered presentation creation tool with SSO and multi-tenancy',
    category: 'Productivity',
    port: 3000,
    icon: 'slideshow',
    status: 'optional',
    features: [
      'AI presentation generation',
      'Template library',
      'Real-time collaboration',
      'Export to PDF/PPTX'
    ],
    dependencies: []
  },

  'grafana': {
    name: 'Grafana Monitoring',
    description: 'Metrics visualization and monitoring dashboard',
    category: 'Monitoring',
    port: 3001,
    icon: 'analytics',
    status: 'optional',
    features: [
      'Real-time metrics',
      'Custom dashboards',
      'Alerting',
      'Prometheus integration'
    ],
    dependencies: ['prometheus']
  },

  'prometheus': {
    name: 'Prometheus',
    description: 'Time-series database for metrics collection',
    category: 'Monitoring',
    port: 9090,
    icon: 'storage',
    status: 'optional',
    features: [
      'Metric scraping',
      'Time-series storage',
      'PromQL query language',
      'Alerting rules'
    ],
    dependencies: []
  }
};

/**
 * Service categories for grouping and filtering
 */
export const serviceCategories = [
  'AI Services',
  'Voice Services',
  'Agent Platform',
  'Search',
  'Infrastructure',
  'Security',
  'Billing',
  'Development',
  'Productivity',
  'Monitoring'
];

/**
 * Service status definitions
 */
export const serviceStatuses = {
  operational: {
    label: 'Operational',
    color: 'success',
    description: 'Service is running normally'
  },
  degraded: {
    label: 'Degraded',
    color: 'warning',
    description: 'Service is experiencing issues'
  },
  down: {
    label: 'Down',
    color: 'error',
    description: 'Service is unavailable'
  },
  optional: {
    label: 'Optional',
    color: 'info',
    description: 'Service is not required for core functionality'
  },
  maintenance: {
    label: 'Maintenance',
    color: 'warning',
    description: 'Service is undergoing maintenance'
  }
};

/**
 * Get service by key
 * @param {string} serviceKey - Service identifier
 * @returns {Object|null} Service description or null if not found
 */
export function getService(serviceKey) {
  return serviceDescriptions[serviceKey] || null;
}

/**
 * Get all services in a category
 * @param {string} category - Category name
 * @returns {Array} Array of service objects with keys
 */
export function getServicesByCategory(category) {
  return Object.entries(serviceDescriptions)
    .filter(([_, service]) => service.category === category)
    .map(([key, service]) => ({ key, ...service }));
}

/**
 * Get service URL (external or local based on environment)
 * @param {string} serviceKey - Service identifier
 * @param {boolean} useExternal - Use external URL if available
 * @returns {string|null} Service URL or null
 */
export function getServiceUrl(serviceKey, useExternal = true) {
  const service = getService(serviceKey);
  if (!service) return null;

  if (useExternal && service.url) {
    return service.url;
  }

  return service.localUrl || service.url || null;
}

/**
 * Check if service has dependencies
 * @param {string} serviceKey - Service identifier
 * @returns {boolean} True if service has dependencies
 */
export function hasDependencies(serviceKey) {
  const service = getService(serviceKey);
  return service && service.dependencies && service.dependencies.length > 0;
}

/**
 * Get detailed service information
 * Alias for getService (for backward compatibility)
 * @param {string} serviceKey - Service identifier
 * @returns {Object|null} Service object or null
 */
export function getServiceInfo(serviceKey) {
  return getService(serviceKey);
}

/**
 * Get GPU usage summary across all services
 * @returns {Object} GPU usage statistics
 */
export function getGPUUsageSummary() {
  const gpuServices = Object.entries(serviceDescriptions)
    .filter(([_, service]) => service.hardware && service.hardware.length > 0)
    .map(([key, service]) => ({ key, ...service }));

  return {
    totalServices: gpuServices.length,
    services: gpuServices.map(s => s.name),
    hardware: gpuServices.flatMap(s => s.hardware || []),
    utilizationEstimate: gpuServices.length > 0 ? '90-95%' : '0%'
  };
}

export default serviceDescriptions;
