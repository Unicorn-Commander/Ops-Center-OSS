import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, Link } from 'react-router-dom';
import {
  CheckCircleIcon,
  SparklesIcon,
  ServerIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  TagIcon,
  ArrowRightIcon,
  CreditCardIcon,
  StarIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { getGlassmorphismStyles } from '../styles/glassmorphism';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import { safeMap, safeFilter, safeSome, safeIncludes } from '../utils/safeUtils';

// Animation variants
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

// App categories
const CATEGORIES = [
  { id: 'all', label: 'All Apps', icon: SparklesIcon },
  { id: 'ai', label: 'AI & Chat', icon: SparklesIcon },
  { id: 'tools', label: 'Development', icon: ServerIcon },
  { id: 'analytics', label: 'Productivity', icon: ChartBarIcon }
];

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

// App Card Component
const AppCard = ({ service, onAddToSubscription, userHasService, theme }) => {
  const glassStyles = getGlassmorphismStyles(theme.currentTheme);
  const isFree = service.base_price === 0;
  const isActive = userHasService;

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ scale: 1.02, y: -4 }}
      className={`${glassStyles.card} rounded-2xl overflow-hidden shadow-xl h-full flex flex-col`}
    >
      {/* App Icon/Image Header */}
      <div className={`h-40 bg-gradient-to-br ${service.gradient || 'from-blue-500 to-purple-500'} flex items-center justify-center relative`}>
        {service.icon_url ? (
          <img
            src={service.icon_url}
            alt={service.name}
            className="h-24 w-24 object-contain"
          />
        ) : (
          <service.icon className="h-24 w-24 text-white opacity-90" />
        )}

        {/* Status badges */}
        {service.featured && (
          <div className="absolute top-3 right-3 bg-yellow-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
            <StarIcon className="h-3 w-3" />
            Featured
          </div>
        )}
        {isActive && (
          <div className="absolute top-3 left-3 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
            <CheckCircleIcon className="h-3 w-3" />
            Active
          </div>
        )}
      </div>

      {/* App Content */}
      <div className="p-6 flex-1 flex flex-col">
        {/* Title & Pricing */}
        <div className="mb-4">
          <div className="flex items-start justify-between gap-3 mb-2">
            <h3 className={`text-xl font-bold ${theme.text.primary}`}>
              {service.name}
            </h3>
            <div className="text-right flex-shrink-0">
              {isFree ? (
                <span className="inline-block px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-bold">
                  FREE
                </span>
              ) : (
                <div>
                  <div className={`text-2xl font-bold ${theme.text.primary}`}>
                    {formatCurrency(service.base_price)}
                  </div>
                  <div className={`text-xs ${theme.text.secondary}`}>
                    /month
                  </div>
                </div>
              )}
            </div>
          </div>

          <p className={`text-sm ${theme.text.secondary} line-clamp-2 mb-3`}>
            {service.description}
          </p>
        </div>

        {/* Key Features */}
        <div className="mb-6 flex-1">
          <div className={`text-xs font-bold ${theme.text.accent} uppercase mb-2`}>
            Key Features
          </div>
          <ul className="space-y-2">
            {safeMap((service.features || []).slice(0, 4), (feature, idx) => (
              <li key={idx} className={`flex items-start gap-2 text-sm ${theme.text.secondary}`}>
                <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Action Button */}
        <div className="mt-auto">
          {isActive ? (
            <button
              disabled
              className="w-full py-3 px-4 bg-green-500/20 text-green-400 rounded-lg font-semibold flex items-center justify-center gap-2 cursor-not-allowed"
            >
              <CheckCircleIcon className="h-5 w-5" />
              Active in Subscription
            </button>
          ) : (
            <button
              onClick={() => onAddToSubscription(service)}
              className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              {isFree ? 'Activate App' : 'Add to Subscription'}
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default function AppsMarketplace() {
  const navigate = useNavigate();
  const { theme, currentTheme } = useTheme();
  const toast = useToast();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [loading, setLoading] = useState(true);
  const [services, setServices] = useState([]);
  const [userServices, setUserServices] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Mock apps data - will be replaced with API call
  const MOCK_SERVICES = [
    {
      id: 'chat',
      name: 'AI Chat (Open-WebUI)',
      category: 'ai',
      base_price: 0,
      description: 'Advanced conversational AI interface with support for multiple LLM models',
      features: [
        'Multiple AI models',
        'Conversation history',
        'File uploads & analysis',
        'Custom prompts library',
        'RAG support',
        'API access'
      ],
      icon: SparklesIcon,
      gradient: 'from-blue-500 to-cyan-500',
      featured: true,
      access_url: 'https://chat.your-domain.com'
    },
    {
      id: 'search',
      name: 'AI Search (Center-Deep)',
      category: 'ai',
      base_price: 0,
      description: 'Privacy-focused AI-powered metasearch across 70+ search engines',
      features: [
        '70+ search engines',
        'AI-enhanced results',
        'Privacy protection',
        'Custom filters',
        'Real-time results',
        'API access'
      ],
      icon: MagnifyingGlassIcon,
      gradient: 'from-purple-500 to-pink-500',
      featured: true,
      access_url: 'https://search.your-domain.com'
    },
    {
      id: 'tts',
      name: 'Text-to-Speech',
      category: 'ai',
      base_price: 5.00,
      description: 'Professional-grade voice synthesis with 20+ voices and emotion control',
      features: [
        'OpenAI-compatible API',
        '20+ natural voices',
        'Emotion control',
        'SSML support',
        'Multiple languages',
        'High-quality audio'
      ],
      icon: ServerIcon,
      gradient: 'from-pink-500 to-rose-500'
    },
    {
      id: 'stt',
      name: 'Speech-to-Text',
      category: 'ai',
      base_price: 5.00,
      description: 'Advanced speech recognition with speaker diarization and 100+ languages',
      features: [
        'OpenAI-compatible API',
        'Speaker diarization',
        '100+ languages',
        'Word-level timestamps',
        'Web interface',
        'Real-time transcription'
      ],
      icon: ServerIcon,
      gradient: 'from-blue-500 to-indigo-500'
    },
    {
      id: 'brigade',
      name: 'Brigade Agent Platform',
      category: 'tools',
      base_price: 10.00,
      description: 'Build and manage AI agents with The General orchestrator',
      features: [
        '47+ pre-built agents',
        'The General orchestrator',
        'Gunny builder',
        'A2A protocol',
        'Multi-provider LLM',
        'Built-in monitoring'
      ],
      icon: ServerIcon,
      gradient: 'from-purple-500 to-indigo-500',
      featured: true
    },
    {
      id: 'forgejo',
      name: 'Forgejo Git Server',
      category: 'tools',
      base_price: 0,
      description: 'Self-hosted Git server with GitHub-like features - repositories, issues, pull requests, and wikis',
      features: [
        'Unlimited repositories',
        'Pull requests & code review',
        'Issues & project tracking',
        'Git LFS support',
        'CI/CD with Actions',
        'SSO integration'
      ],
      icon: ServerIcon,
      gradient: 'from-orange-500 to-red-500',
      featured: false,
      access_url: 'https://git.your-domain.com'
    },
    {
      id: 'analytics',
      name: 'Advanced Analytics',
      category: 'analytics',
      base_price: 20.00,
      description: 'Comprehensive usage analytics and performance monitoring',
      features: [
        'Real-time dashboards',
        'Cost optimization',
        'Custom reports',
        'Data export',
        'API tracking',
        'Performance metrics'
      ],
      icon: ChartBarIcon,
      gradient: 'from-violet-500 to-purple-500'
    }
  ];

  useEffect(() => {
    loadServices();
    loadCurrentUser();
    loadUserServices();
  }, []);

  const loadServices = async () => {
    try {
      setLoading(true);
      // Call tier-filtered apps API
      const response = await fetch('/api/v1/my-apps/authorized', { credentials: 'include' });

      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }

      const data = await response.json();

      // Transform API response to match MOCK_SERVICES structure
      const transformedServices = data.map(app => {
        // Convert features object to array of strings
        const featuresList = app.features && typeof app.features === 'object'
          ? Object.values(app.features).filter(f => f != null && typeof f === 'string')
          : [];

        return {
          id: app.slug,
          name: app.name,
          category: app.category,
          base_price: 0,  // API doesn't return base_price for tier-included apps
          description: app.description,
          features: featuresList,
          icon: ServerIcon,  // Default icon, could map based on category/slug
          icon_url: app.icon_url,  // Pass through icon URL from API
          gradient: getCategoryGradient(app.category),
          featured: app.access_type === 'tier_included',
          access_url: app.launch_url
        };
      });

      setServices(transformedServices);
    } catch (error) {
      console.error('Failed to load apps:', error);
      toast.error('Failed to load apps - using fallback');
      setServices(MOCK_SERVICES); // Fallback to mock data
    } finally {
      setLoading(false);
    }
  };

  // Helper function to map category to gradient colors
  const getCategoryGradient = (category) => {
    const gradients = {
      'ai': 'from-blue-500 to-cyan-500',
      'tools': 'from-purple-500 to-indigo-500',
      'analytics': 'from-violet-500 to-purple-500',
      'communication': 'from-pink-500 to-rose-500',
      'storage': 'from-emerald-500 to-green-500'
    };
    return gradients[category] || 'from-gray-500 to-gray-600';
  };

  const loadCurrentUser = async () => {
    try {
      const response = await fetch('/api/v1/auth/user', { credentials: 'include' });
      if (response.ok) {
        const data = await response.json();
        setCurrentUser(data.user || data);
      }
    } catch (error) {
      console.error('Failed to load user:', error);
    }
  };

  const loadUserServices = async () => {
    try {
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/user/apps', { credentials: 'include' });
      // const data = await response.json();
      // setUserServices(data.apps.map(s => s.id));

      // Mock: user has chat and search by default
      setUserServices(['chat', 'search']);
    } catch (error) {
      console.error('Failed to load user apps:', error);
    }
  };

  const handleAddToSubscription = (service) => {
    if (service.base_price === 0) {
      // Free app - activate immediately
      toast.success(`${service.name} activated!`);
      setUserServices([...userServices, service.id]);
    } else {
      // Paid app - redirect to checkout
      toast.info('Redirecting to checkout...');
      navigate(`/apps/${service.id}/checkout`);
    }
  };

  // Filter apps
  const filteredServices = safeFilter(services, service => {
    // Category filter
    if (selectedCategory !== 'all' && service.category !== selectedCategory) {
      return false;
    }
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        safeIncludes((service.name || '').toLowerCase(), query) ||
        safeIncludes((service.description || '').toLowerCase(), query) ||
        safeSome(service.features || [], f => safeIncludes((f || '').toLowerCase(), query))
      );
    }
    return true;
  });

  // Separate featured and regular apps
  const featuredServices = safeFilter(filteredServices, s => s.featured);
  const regularServices = safeFilter(filteredServices, s => !s.featured);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className={theme.text.secondary}>Loading apps...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 pb-20"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-2xl`}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-xl">
                <ServerIcon className="h-6 w-6 text-white" />
              </div>
              <h1 className={`text-3xl font-bold ${currentTheme === 'unicorn' ? 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400' : theme.text.primary}`}>
                Available Apps
              </h1>
            </div>
            <p className={`${currentTheme === 'unicorn' ? 'text-purple-200/80' : theme.text.secondary} text-base`}>
              Discover powerful AI apps and tools to enhance your workflow
            </p>
          </div>

          {/* Current tier badge */}
          {currentUser && (
            <div className={`${glassStyles.card} rounded-xl px-4 py-3`}>
              <div className={`text-sm ${theme.text.secondary} mb-1`}>Current Plan</div>
              <div className={`text-lg font-bold ${theme.text.primary} capitalize`}>
                {currentUser.subscription_tier || 'Free'}
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Filters & Search */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
            <input
              type="text"
              placeholder="Search apps..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 ${glassStyles.card} rounded-lg ${theme.text.primary} placeholder-gray-500 focus:ring-2 focus:ring-blue-500 focus:outline-none`}
            />
          </div>

          {/* Category filter */}
          <div className="relative">
            <FunnelIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 ${glassStyles.card} rounded-lg ${theme.text.primary} focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer`}
            >
              {CATEGORIES.map(cat => (
                <option key={cat.id} value={cat.id}>{cat.label}</option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* Featured Apps Section */}
      {featuredServices.length > 0 && (
        <motion.div variants={itemVariants}>
          <h2 className={`text-2xl font-bold ${theme.text.primary} mb-4 flex items-center gap-2`}>
            <StarIcon className="h-6 w-6 text-yellow-500" />
            Featured Apps
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {featuredServices.map((service) => (
              <AppCard
                key={service.id}
                service={service}
                onAddToSubscription={handleAddToSubscription}
                userHasService={userServices.includes(service.id)}
                theme={theme}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* All Apps Section */}
      {regularServices.length > 0 && (
        <motion.div variants={itemVariants}>
          <h2 className={`text-2xl font-bold ${theme.text.primary} mb-4`}>
            All Apps
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {regularServices.map((service) => (
              <AppCard
                key={service.id}
                service={service}
                onAddToSubscription={handleAddToSubscription}
                userHasService={userServices.includes(service.id)}
                theme={theme}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* No results */}
      {filteredServices.length === 0 && (
        <div className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
          <ServerIcon className={`h-16 w-16 ${theme.text.secondary} mx-auto mb-4 opacity-50`} />
          <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
            No apps found
          </h3>
          <p className={theme.text.secondary}>
            Try adjusting your filters or search query
          </p>
        </div>
      )}

      {/* View My Apps Link */}
      <motion.div variants={itemVariants} className="text-center">
        <Link
          to="/apps/my"
          className={`inline-flex items-center gap-2 px-6 py-3 ${glassStyles.card} rounded-lg ${theme.text.primary} hover:bg-white/10 transition-colors`}
        >
          <CheckCircleIcon className="h-5 w-5" />
          View My Active Apps
          <ArrowRightIcon className="h-5 w-5" />
        </Link>
      </motion.div>
    </motion.div>
  );
}
