/**
 * ServiceHealthGrid - Visual overview of all backend services with status indicators
 */

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import {
  ServerStackIcon,
  CircleStackIcon,
  CpuChipIcon,
  GlobeAltIcon,
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ShieldCheckIcon,
  MagnifyingGlassCircleIcon,
  CubeIcon,
  BeakerIcon,
  DocumentTextIcon,
  CloudIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from '@heroicons/react/24/outline';
import StatusIndicator from './StatusIndicator';

// Service configuration with icons and categories
const SERVICE_CONFIG = {
  postgresql: { name: 'PostgreSQL', icon: CircleStackIcon, category: 'database', critical: true },
  redis: { name: 'Redis', icon: CircleStackIcon, category: 'database', critical: true },
  qdrant: { name: 'Qdrant', icon: CircleStackIcon, category: 'database' },
  keycloak: { name: 'Keycloak', icon: ShieldCheckIcon, category: 'auth', critical: true },
  traefik: { name: 'Traefik', icon: GlobeAltIcon, category: 'network', critical: true },
  'open-webui': { name: 'Open-WebUI', icon: ChatBubbleLeftRightIcon, category: 'app' },
  webui: { name: 'Open-WebUI', icon: ChatBubbleLeftRightIcon, category: 'app' },
  vllm: { name: 'vLLM', icon: SparklesIcon, category: 'ai', critical: true },
  litellm: { name: 'LiteLLM', icon: CpuChipIcon, category: 'ai' },
  ollama: { name: 'Ollama', icon: CubeIcon, category: 'ai' },
  'center-deep': { name: 'Center-Deep', icon: MagnifyingGlassCircleIcon, category: 'app' },
  centerdeep: { name: 'Center-Deep', icon: MagnifyingGlassCircleIcon, category: 'app' },
  searxng: { name: 'SearXNG', icon: MagnifyingGlassCircleIcon, category: 'app' },
  brigade: { name: 'Brigade', icon: CubeIcon, category: 'app' },
  embeddings: { name: 'Embeddings', icon: BeakerIcon, category: 'ai' },
  reranker: { name: 'Reranker', icon: BeakerIcon, category: 'ai' },
  infinity: { name: 'Infinity', icon: BeakerIcon, category: 'ai' },
  whisperx: { name: 'WhisperX', icon: SparklesIcon, category: 'ai' },
  amanuensis: { name: 'Amanuensis', icon: DocumentTextIcon, category: 'ai' },
  orator: { name: 'Orator', icon: ChatBubbleLeftRightIcon, category: 'ai' },
  tts: { name: 'TTS', icon: ChatBubbleLeftRightIcon, category: 'ai' },
  stt: { name: 'STT', icon: SparklesIcon, category: 'ai' },
  grafana: { name: 'Grafana', icon: CloudIcon, category: 'monitoring' },
  prometheus: { name: 'Prometheus', icon: CloudIcon, category: 'monitoring' },
  lago: { name: 'Lago', icon: CubeIcon, category: 'billing' },
  forgejo: { name: 'Forgejo', icon: CubeIcon, category: 'app' },
  bolt: { name: 'Bolt.diy', icon: CubeIcon, category: 'app' },
  presenton: { name: 'Presenton', icon: CubeIcon, category: 'app' },
};

// Category colors
const CATEGORY_COLORS = {
  database: 'from-blue-500 to-cyan-500',
  auth: 'from-purple-500 to-indigo-500',
  network: 'from-teal-500 to-emerald-500',
  ai: 'from-pink-500 to-rose-500',
  app: 'from-amber-500 to-orange-500',
  monitoring: 'from-green-500 to-lime-500',
  billing: 'from-violet-500 to-purple-500',
  other: 'from-gray-500 to-slate-500',
};

// Get service config by matching name patterns
const getServiceConfig = (serviceName) => {
  const lowerName = serviceName.toLowerCase();
  for (const [key, config] of Object.entries(SERVICE_CONFIG)) {
    if (lowerName.includes(key)) {
      return { key, ...config };
    }
  }
  return {
    key: serviceName,
    name: serviceName,
    icon: ServerStackIcon,
    category: 'other',
    critical: false
  };
};

// Service card component
function ServiceCard({ service, config, onClick }) {
  const Icon = config.icon;
  const categoryColor = CATEGORY_COLORS[config.category] || CATEGORY_COLORS.other;
  const isRunning = service.status === 'running' || service.status === 'healthy';
  const isCritical = config.critical;

  return (
    <motion.div
      whileHover={{ scale: 1.03, y: -2 }}
      onClick={onClick}
      className={`flex flex-col items-center gap-2 p-4 rounded-xl backdrop-blur-sm border cursor-pointer transition-all ${
        isRunning
          ? isCritical
            ? 'bg-green-500/10 border-green-500/30 ring-2 ring-green-500/20'
            : 'bg-green-500/10 border-green-500/30'
          : 'bg-red-500/10 border-red-500/30'
      }`}
    >
      <div className={`w-10 h-10 bg-gradient-to-br ${categoryColor} rounded-xl flex items-center justify-center shadow-lg`}>
        <Icon className="h-5 w-5 text-white" />
      </div>
      <span className="text-sm font-medium text-white text-center truncate w-full">
        {config.name}
      </span>
      <StatusIndicator
        status={isRunning ? 'healthy' : 'stopped'}
        size="sm"
        animate={isRunning}
      />
    </motion.div>
  );
}

export default function ServiceHealthGrid({
  services = [],
  loading = false,
  onServiceClick = null,
  glassStyles = {},
  className = ''
}) {
  const [showAll, setShowAll] = useState(false);
  const INITIAL_COUNT = 12;

  // Process services
  const processedServices = services
    .filter(s => s && s.name)
    .map(service => ({
      ...service,
      config: getServiceConfig(service.name)
    }))
    .sort((a, b) => {
      // Sort: critical first, then by status, then alphabetically
      if (a.config.critical !== b.config.critical) return b.config.critical ? 1 : -1;
      const aRunning = a.status === 'running' || a.status === 'healthy';
      const bRunning = b.status === 'running' || b.status === 'healthy';
      if (aRunning !== bRunning) return bRunning ? 1 : -1;
      return a.config.name.localeCompare(b.config.name);
    });

  // Stats
  const runningCount = processedServices.filter(s =>
    s.status === 'running' || s.status === 'healthy'
  ).length;
  const totalCount = processedServices.length;

  // Displayed services
  const displayedServices = showAll
    ? processedServices
    : processedServices.slice(0, INITIAL_COUNT);
  const hasMore = processedServices.length > INITIAL_COUNT;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card || 'backdrop-blur-xl bg-white/10 border border-white/20'} rounded-2xl p-6 shadow-xl ${className}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
            <ServerStackIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-white">Service Health</h3>
            <p className="text-sm text-gray-400">
              {runningCount}/{totalCount} services running
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
          runningCount === totalCount
            ? 'bg-green-500/20 text-green-400'
            : runningCount > totalCount / 2
            ? 'bg-yellow-500/20 text-yellow-400'
            : 'bg-red-500/20 text-red-400'
        }`}>
          {runningCount === totalCount ? 'All Healthy' : `${totalCount - runningCount} Down`}
        </span>
      </div>

      {/* Loading */}
      {loading && (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
          {[...Array(12)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-700/30 rounded-xl animate-pulse" />
          ))}
        </div>
      )}

      {/* Services Grid */}
      {!loading && (
        <>
          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {displayedServices.map((service, index) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: index * 0.02 }}
              >
                <ServiceCard
                  service={service}
                  config={service.config}
                  onClick={() => onServiceClick?.(service)}
                />
              </motion.div>
            ))}
          </div>

          {/* Show More/Less */}
          {hasMore && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="flex items-center justify-center gap-2 w-full mt-4 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            >
              {showAll ? (
                <>
                  <ChevronUpIcon className="h-4 w-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDownIcon className="h-4 w-4" />
                  Show All ({processedServices.length} services)
                </>
              )}
            </button>
          )}
        </>
      )}
    </motion.div>
  );
}
