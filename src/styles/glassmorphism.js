/**
 * Glassmorphism Design System
 * Extracted from PublicLanding.jsx for reuse across dashboard components
 *
 * Theme-aware styling with support for unicorn, dark, and light themes
 */

export const getGlassmorphismStyles = (currentTheme) => {
  const baseStyles = {
    // Glassmorphism card styles
    card: {
      unicorn: 'backdrop-blur-xl bg-white/10 border border-white/20',
      dark: 'backdrop-blur-xl bg-slate-800/50 border border-slate-700/50',
      light: 'backdrop-blur-xl bg-white/80 border border-gray-200/50'
    },

    // Hover effects
    cardHover: {
      base: 'transition-all duration-300 hover:shadow-2xl hover:-translate-y-1',
      scale: 'hover:scale-105'
    },

    // Gradient backgrounds
    gradients: {
      purple: 'bg-gradient-to-br from-purple-600 to-indigo-600',
      blue: 'bg-gradient-to-br from-blue-600 to-cyan-600',
      green: 'bg-gradient-to-br from-green-600 to-emerald-600',
      amber: 'bg-gradient-to-br from-amber-500 to-orange-600',
      pink: 'bg-gradient-to-br from-pink-600 to-rose-600',
      red: 'bg-gradient-to-br from-red-500 to-red-700'
    },

    // Icon containers
    iconContainer: {
      base: 'rounded-xl backdrop-blur-sm flex items-center justify-center border shadow-lg',
      unicorn: 'bg-white/10 border-white/20',
      dark: 'bg-slate-700/50 border-slate-600/50',
      light: 'bg-white/90 border-gray-200/50'
    },

    // Progress bars with gradients
    progressBar: {
      container: 'w-full bg-gray-700/30 rounded-full h-3 shadow-inner',
      fill: {
        low: 'bg-gradient-to-r from-green-500 to-emerald-500',
        medium: 'bg-gradient-to-r from-yellow-500 to-orange-500',
        high: 'bg-gradient-to-r from-red-500 to-red-600',
        vram: 'bg-gradient-to-r from-blue-500 to-cyan-500',
        storage: 'bg-gradient-to-r from-purple-500 to-indigo-500'
      }
    },

    // Accent bars
    accentBar: 'h-1 bg-gradient-to-r from-white/0 via-white/30 to-white/0',

    // Stat badges
    badge: {
      unicorn: 'bg-purple-600/50 text-yellow-400',
      dark: 'bg-slate-700 text-blue-400',
      light: 'bg-blue-100 text-blue-700'
    },

    // Service cards
    serviceCard: {
      base: 'rounded-3xl shadow-lg overflow-hidden relative h-full',
      border: 'border border-white/20'
    },

    // Activity timeline
    timeline: {
      item: 'rounded-lg bg-gray-700/20 hover:bg-gray-700/30 transition-colors',
      iconContainer: 'bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center',
      dot: 'bg-green-500 rounded-full'
    }
  };

  // Return theme-specific styles
  const theme = currentTheme || 'dark';

  return {
    ...baseStyles,
    card: baseStyles.card[theme],
    iconContainer: `${baseStyles.iconContainer.base} ${baseStyles.iconContainer[theme]}`,
    badge: baseStyles.badge[theme]
  };
};

/**
 * Get resource usage color based on percentage
 */
export const getResourceColor = (percent, type = 'default') => {
  if (type === 'vram') {
    return percent > 90 ? 'from-red-500 to-red-600' :
           percent > 70 ? 'from-yellow-500 to-orange-500' :
           'from-blue-500 to-cyan-500';
  }

  if (type === 'storage') {
    return percent > 90 ? 'from-red-500 to-red-600' :
           percent > 70 ? 'from-yellow-500 to-orange-500' :
           'from-purple-500 to-indigo-500';
  }

  return percent > 90 ? 'from-red-500 to-red-600' :
         percent > 70 ? 'from-yellow-500 to-orange-500' :
         'from-green-500 to-emerald-500';
};

/**
 * Service card color schemes
 */
export const serviceColors = {
  vllm: { gradient: 'from-purple-600 to-indigo-600', text: 'text-purple-100' },
  'open-webui': { gradient: 'from-blue-500 to-blue-700', text: 'text-blue-100' },
  postgresql: { gradient: 'from-indigo-600 to-blue-600', text: 'text-indigo-100' },
  redis: { gradient: 'from-red-500 to-red-700', text: 'text-red-100' },
  keycloak: { gradient: 'from-cyan-600 to-blue-600', text: 'text-cyan-100' },
  'center-deep': { gradient: 'from-green-500 to-emerald-600', text: 'text-green-100' },
  brigade: { gradient: 'from-purple-600 to-pink-600', text: 'text-purple-100' },
  traefik: { gradient: 'from-teal-600 to-cyan-600', text: 'text-teal-100' },
  grafana: { gradient: 'from-amber-500 to-orange-600', text: 'text-amber-100' },
  prometheus: { gradient: 'from-orange-500 to-red-500', text: 'text-orange-100' }
};

/**
 * Get service color scheme with fallback
 */
export const getServiceColorScheme = (serviceName) => {
  const key = Object.keys(serviceColors).find(k =>
    serviceName.toLowerCase().includes(k)
  );

  return serviceColors[key] || {
    gradient: 'from-gray-600 to-gray-700',
    text: 'text-gray-100'
  };
};
