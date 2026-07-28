import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowTopRightOnSquareIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline';

/**
 * DynamicServiceCards - Displays application services from landing_config.json
 * This component makes Ops-Center white-labelable by reading services dynamically
 *
 * Features:
 * - Loads services from /api/v1/landing/config
 * - Shows enabled services only
 * - Respects service order
 * - Handles "Coming Soon" services
 * - Uses deployment branding
 */

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.05,
      duration: 0.3,
      ease: "easeOut"
    }
  }),
  hover: {
    y: -4,
    transition: { duration: 0.2 }
  }
};

export default function DynamicServiceCards({ theme, className = '' }) {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchLandingConfig();
  }, []);

  const fetchLandingConfig = async () => {
    try {
      const response = await fetch('/api/v1/landing/config', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Failed to load config: ${response.status}`);
      }

      const data = await response.json();
      setConfig(data);
    } catch (err) {
      console.error('Error loading landing config:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleServiceClick = (service) => {
    if (service.url && !service.comingSoon) {
      window.open(service.url, '_blank', 'noopener,noreferrer');
    }
  };

  if (loading) {
    return (
      <div className={`${className} p-6 rounded-2xl bg-gradient-to-br from-gray-800/40 to-gray-900/40 border border-gray-700/50 backdrop-blur-xl`}>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-700/50 rounded w-1/3"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-32 bg-gray-700/30 rounded-xl"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`${className} p-6 rounded-2xl bg-gradient-to-br from-red-900/20 to-gray-900/40 border border-red-700/50 backdrop-blur-xl`}>
        <div className="flex items-center gap-3 text-red-400">
          <ExclamationCircleIcon className="h-5 w-5" />
          <p className="text-sm">Failed to load services: {error}</p>
        </div>
      </div>
    );
  }

  if (!config || !config.services || config.services.length === 0) {
    return null;
  }

  // Get enabled services, sorted by order
  const enabledServices = config.services
    .filter(service => service.enabled !== false)
    .sort((a, b) => (a.order || 999) - (b.order || 999));

  if (enabledServices.length === 0) {
    return null;
  }

  return (
    <div className={`${className} p-6 rounded-2xl bg-gradient-to-br from-gray-800/40 to-gray-900/40 border border-gray-700/50 backdrop-blur-xl`}>
      {/* Header */}
      <div className="mb-6">
        <h2 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
          {config.branding?.company_name || 'Applications'}
        </h2>
        {config.welcome?.description && (
          <p className={`text-sm ${theme.text.secondary}`}>
            {config.welcome.description}
          </p>
        )}
      </div>

      {/* Service Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {enabledServices.map((service, index) => (
          <ServiceCard
            key={service.id || service.name}
            service={service}
            theme={theme}
            index={index}
            onClick={() => handleServiceClick(service)}
          />
        ))}
      </div>
    </div>
  );
}

// Individual Service Card Component
function ServiceCard({ service, theme, index, onClick }) {
  const isComingSoon = service.comingSoon || !service.url;
  const isClickable = !isComingSoon && service.enabled !== false;

  return (
    <motion.div
      custom={index}
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      whileHover={isClickable ? "hover" : {}}
      onClick={isClickable ? onClick : undefined}
      className={`
        relative p-6 rounded-xl border backdrop-blur-sm
        ${isClickable
          ? 'cursor-pointer bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border-blue-500/20 hover:border-blue-500/40 hover:shadow-lg hover:shadow-blue-500/20'
          : 'bg-gradient-to-br from-gray-700/20 to-gray-800/20 border-gray-600/20'
        }
        transition-all duration-300 overflow-hidden group
      `}
    >
      {/* Background glow effect on hover */}
      {isClickable && (
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      )}

      <div className="relative z-10">
        {/* Header with icon/emoji */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            {service.logo_url ? (
              <img
                src={service.logo_url}
                alt={service.name}
                className="w-10 h-10 rounded-lg object-contain"
              />
            ) : service.icon && (
              <div className="text-3xl">{service.icon}</div>
            )}
          </div>

          {isComingSoon ? (
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-yellow-500/20 border border-yellow-500/30">
              <ClockIcon className="h-3.5 w-3.5 text-yellow-400" />
              <span className="text-xs font-medium text-yellow-400">Soon</span>
            </div>
          ) : (
            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
              <ArrowTopRightOnSquareIcon className="h-5 w-5 text-blue-400" />
            </div>
          )}
        </div>

        {/* Service name */}
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-2 line-clamp-1`}>
          {service.name}
        </h3>

        {/* Description */}
        <p className={`text-sm ${theme.text.secondary} line-clamp-2 mb-3`}>
          {service.description || 'No description available'}
        </p>

        {/* Footer - Status or Port info */}
        <div className="flex items-center justify-between">
          {service.port && !isComingSoon && (
            <span className={`text-xs ${theme.text.secondary} opacity-70`}>
              Port: {service.port}
            </span>
          )}
          {isClickable && (
            <div className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircleIcon className="h-4 w-4" />
              <span className="text-xs font-medium">Available</span>
            </div>
          )}
        </div>
      </div>

      {/* Hover border glow effect */}
      {isClickable && (
        <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute inset-0 rounded-xl border-2 border-blue-400/0 group-hover:border-blue-400/30 transition-colors duration-500" />
        </div>
      )}
    </motion.div>
  );
}
