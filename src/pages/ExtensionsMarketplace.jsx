import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ShoppingCartIcon,
  CheckCircleIcon,
  LockClosedIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  SparklesIcon,
  ServerIcon,
  MicrophoneIcon,
  SpeakerWaveIcon,
  UsersIcon,
  CodeBracketIcon,
  ChartBarIcon,
  BoltIcon,
  CreditCardIcon,
  XMarkIcon,
  ArrowRightIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { getGlassmorphismStyles } from '../styles/glassmorphism';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
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

// Add-on categories
const CATEGORIES = [
  { id: 'all', label: 'All Extensions', icon: SparklesIcon },
  { id: 'services', label: 'Services', icon: ServerIcon },
  { id: 'tools', label: 'Development Tools', icon: CodeBracketIcon },
  { id: 'analytics', label: 'Analytics', icon: ChartBarIcon },
  { id: 'enterprise', label: 'Enterprise', icon: UsersIcon }
];

// Sort options
const SORT_OPTIONS = [
  { id: 'popular', label: 'Most Popular' },
  { id: 'price-low', label: 'Price: Low to High' },
  { id: 'price-high', label: 'Price: High to Low' },
  { id: 'name', label: 'Name (A-Z)' }
];

// Mock add-ons data (will be replaced with API call)
const ADDONS_DATA = [
  {
    id: 'tts',
    name: 'Text-to-Speech Service',
    category: 'services',
    price: 5.00,
    period: 'month',
    icon: SpeakerWaveIcon,
    iconColor: 'from-pink-500 to-rose-500',
    description: 'Professional-grade voice synthesis with 20+ voices and emotion control',
    features: [
      'OpenAI-compatible API',
      '20+ natural voices',
      'Emotion and speed control',
      'SSML support',
      'Multiple languages',
      'High-quality audio output'
    ],
    popular: true,
    status: 'available' // available, purchased, locked
  },
  {
    id: 'stt',
    name: 'Speech-to-Text Service',
    category: 'services',
    price: 5.00,
    period: 'month',
    icon: MicrophoneIcon,
    iconColor: 'from-blue-500 to-cyan-500',
    description: 'Advanced speech recognition with speaker diarization and 100+ languages',
    features: [
      'OpenAI-compatible API',
      'Speaker diarization',
      '100+ languages',
      'Word-level timestamps',
      'Web interface included',
      'Real-time transcription'
    ],
    popular: true,
    status: 'available'
  },
  {
    id: 'brigade',
    name: 'Brigade Agent Platform',
    category: 'tools',
    price: 10.00,
    period: 'month',
    icon: UsersIcon,
    iconColor: 'from-purple-500 to-indigo-500',
    description: 'Build and manage AI agents with The General orchestrator and 47+ pre-built specialists',
    features: [
      '47+ pre-built agents',
      'The General orchestrator',
      'Gunny conversational builder',
      'A2A protocol support',
      'Multi-provider LLM support',
      'Built-in monitoring'
    ],
    popular: true,
    status: 'available'
  },
  {
    id: 'bolt',
    name: 'Bolt.DIY Development',
    category: 'tools',
    price: 15.00,
    period: 'month',
    icon: CodeBracketIcon,
    iconColor: 'from-green-500 to-emerald-500',
    description: 'AI-powered development environment with deep SSO integration',
    features: [
      'AI coding assistant',
      'Full IDE capabilities',
      'Keycloak SSO integration',
      'Real-time collaboration',
      'Version control',
      'Code templates'
    ],
    status: 'available'
  },
  {
    id: 'presenton',
    name: 'Presenton AI Presentations',
    category: 'tools',
    price: 12.00,
    period: 'month',
    icon: SparklesIcon,
    iconColor: 'from-amber-500 to-orange-500',
    description: 'Generate professional presentations with AI, templates, and web grounding',
    features: [
      'AI slide generation',
      'Professional templates',
      'Web content grounding',
      'PPTX/PDF export',
      'Image integration',
      'Custom branding'
    ],
    status: 'available'
  },
  {
    id: 'analytics-advanced',
    name: 'Advanced Analytics',
    category: 'analytics',
    price: 20.00,
    period: 'month',
    icon: ChartBarIcon,
    iconColor: 'from-violet-500 to-purple-500',
    description: 'Comprehensive usage analytics, cost tracking, and performance monitoring',
    features: [
      'Real-time dashboards',
      'Cost optimization insights',
      'Custom reports',
      'Data export (CSV/JSON)',
      'API usage tracking',
      'Performance metrics'
    ],
    status: 'available'
  },
  {
    id: 'grafana-monitoring',
    name: 'Grafana Monitoring',
    category: 'analytics',
    price: 8.00,
    period: 'month',
    icon: ChartBarIcon,
    iconColor: 'from-orange-500 to-red-500',
    description: 'Professional monitoring with Grafana dashboards and Prometheus metrics',
    features: [
      'Pre-built dashboards',
      'Prometheus integration',
      'Alert management',
      'Custom visualizations',
      'Metric aggregation',
      'Historical data retention'
    ],
    status: 'available'
  },
  {
    id: 'team-management',
    name: 'Team Management',
    category: 'enterprise',
    price: 25.00,
    period: 'month',
    icon: UsersIcon,
    iconColor: 'from-cyan-500 to-blue-500',
    description: 'Advanced team collaboration with 10 seats, role management, and audit logs',
    features: [
      'Up to 10 team members',
      'Role-based access control',
      'Audit logging',
      'Team workspaces',
      'Resource sharing',
      'Activity monitoring'
    ],
    status: 'available'
  },
  {
    id: 'enterprise-support',
    name: 'Enterprise Support',
    category: 'enterprise',
    price: 50.00,
    period: 'month',
    icon: BoltIcon,
    iconColor: 'from-yellow-500 to-amber-500',
    description: 'Priority support with 24/7 availability, dedicated account manager, and SLA',
    features: [
      '24/7 priority support',
      'Dedicated account manager',
      '99.9% SLA guarantee',
      'Priority bug fixes',
      'Custom integrations',
      'Onboarding assistance'
    ],
    status: 'available'
  }
];

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

// Add-on card component
const AddonCard = ({ addon, onAddToCart, onPurchased, highlighted, theme }) => {
  const glassStyles = getGlassmorphismStyles(theme.currentTheme);
  const isPurchased = addon.status === 'purchased';
  const isLocked = addon.status === 'locked';

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ scale: 1.02, y: -4 }}
      className={`relative ${glassStyles.card} rounded-2xl p-6 shadow-xl ${
        highlighted ? 'ring-2 ring-yellow-500 ring-offset-2 ring-offset-gray-900' : ''
      } ${isPurchased ? 'opacity-75' : ''}`}
    >
      {/* Popular badge */}
      {addon.popular && !isPurchased && (
        <div className="absolute -top-3 -right-3 bg-gradient-to-r from-yellow-500 to-amber-500 text-white px-3 py-1 rounded-full text-xs font-bold shadow-lg">
          🔥 Popular
        </div>
      )}

      {/* Icon */}
      <div className={`w-16 h-16 bg-gradient-to-br ${addon.iconColor} rounded-2xl flex items-center justify-center shadow-2xl mb-4`}>
        <addon.icon className="h-8 w-8 text-white" />
      </div>

      {/* Title & Price */}
      <div className="mb-3">
        <h3 className={`text-lg font-bold ${theme.text.primary} mb-2`}>
          {addon.name}
        </h3>
        <div className="flex items-baseline gap-2">
          <span className={`text-3xl font-bold ${theme.text.primary}`}>
            {formatCurrency(addon.price)}
          </span>
          <span className={`text-sm ${theme.text.secondary}`}>
            /{addon.period}
          </span>
        </div>
      </div>

      {/* Description */}
      <p className={`text-sm ${theme.text.secondary} mb-4 line-clamp-2`}>
        {addon.description}
      </p>

      {/* Features list */}
      <ul className="space-y-2 mb-6">
        {addon.features.slice(0, 4).map((feature, index) => (
          <li key={index} className={`flex items-start gap-2 text-sm ${theme.text.secondary}`}>
            <CheckCircleIcon className="h-4 w-4 text-green-500 flex-shrink-0 mt-0.5" />
            <span>{feature}</span>
          </li>
        ))}
        {addon.features.length > 4 && (
          <li className={`text-xs ${theme.text.accent} italic`}>
            +{addon.features.length - 4} more features
          </li>
        )}
      </ul>

      {/* Action button */}
      {isPurchased ? (
        <button
          disabled
          className="w-full py-3 px-4 bg-green-500/20 text-green-400 rounded-lg font-semibold flex items-center justify-center gap-2 cursor-not-allowed"
        >
          <CheckCircleIcon className="h-5 w-5" />
          Purchased
        </button>
      ) : isLocked ? (
        <button
          disabled
          className="w-full py-3 px-4 bg-gray-500/20 text-gray-400 rounded-lg font-semibold flex items-center justify-center gap-2 cursor-not-allowed"
        >
          <LockClosedIcon className="h-5 w-5" />
          Upgrade Required
        </button>
      ) : (
        <button
          onClick={() => onAddToCart(addon)}
          className="w-full py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
        >
          <ShoppingCartIcon className="h-5 w-5" />
          Add to Cart
        </button>
      )}
    </motion.div>
  );
};

// Shopping cart sidebar
const ShoppingCart = ({ cart, onRemove, onCheckout, onClose, theme }) => {
  const glassStyles = getGlassmorphismStyles(theme.currentTheme);
  const subtotal = cart.reduce((sum, item) => sum + item.price, 0);

  if (cart.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ x: 400, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 400, opacity: 0 }}
      className={`fixed top-4 right-4 w-96 max-h-[calc(100vh-2rem)] overflow-hidden ${glassStyles.card} rounded-2xl shadow-2xl z-50`}
    >
      {/* Header */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center justify-between mb-2">
          <h3 className={`text-xl font-bold ${theme.text.primary} flex items-center gap-2`}>
            <ShoppingCartIcon className="h-6 w-6" />
            Shopping Cart
          </h3>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          >
            <XMarkIcon className={`h-5 w-5 ${theme.text.secondary}`} />
          </button>
        </div>
        <p className={`text-sm ${theme.text.secondary}`}>
          {cart.length} {cart.length === 1 ? 'item' : 'items'}
        </p>
      </div>

      {/* Cart items */}
      <div className="p-6 space-y-3 max-h-96 overflow-y-auto">
        {cart.map((item) => (
          <div
            key={item.id}
            className={`${glassStyles.card} rounded-lg p-4 flex items-start gap-3`}
          >
            <div className={`w-10 h-10 bg-gradient-to-br ${item.iconColor} rounded-lg flex items-center justify-center flex-shrink-0`}>
              <item.icon className="h-5 w-5 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <h4 className={`text-sm font-semibold ${theme.text.primary} truncate`}>
                {item.name}
              </h4>
              <p className={`text-xs ${theme.text.secondary}`}>
                {formatCurrency(item.price)}/{item.period}
              </p>
            </div>
            <button
              onClick={() => onRemove(item.id)}
              className="p-1 hover:bg-red-500/20 rounded transition-colors"
            >
              <XMarkIcon className="h-5 w-5 text-red-400" />
            </button>
          </div>
        ))}
      </div>

      {/* Subtotal */}
      <div className="p-6 border-t border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <span className={`text-base font-semibold ${theme.text.secondary}`}>
            Subtotal
          </span>
          <span className={`text-2xl font-bold ${theme.text.primary}`}>
            {formatCurrency(subtotal)}
          </span>
        </div>
        <p className={`text-xs ${theme.text.secondary}`}>
          Billed monthly. Cancel anytime.
        </p>

        {/* Checkout button */}
        <button
          onClick={onCheckout}
          className="w-full py-3 px-4 bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white rounded-lg font-bold transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
        >
          <CreditCardIcon className="h-5 w-5" />
          Proceed to Checkout
          <ArrowRightIcon className="h-5 w-5" />
        </button>
      </div>
    </motion.div>
  );
};

export default function ExtensionsMarketplace() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { theme, currentTheme } = useTheme();
  const toast = useToast();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [loading, setLoading] = useState(true);
  const [addons, setAddons] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [cart, setCart] = useState([]);
  const [showCart, setShowCart] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('popular');
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedAddon, setHighlightedAddon] = useState(null);

  useEffect(() => {
    loadAddons();
    loadCurrentUser();

    // Check if redirected from locked service
    const highlight = searchParams.get('highlight');
    if (highlight) {
      setHighlightedAddon(highlight);
      // Scroll to highlighted addon after render
      setTimeout(() => {
        const element = document.getElementById(`addon-${highlight}`);
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }, 500);
    }
  }, [searchParams]);

  const loadAddons = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/addons', { credentials: 'include' });
      // const data = await response.json();
      // setAddons(data.addons);

      // Mock data for now
      setAddons(ADDONS_DATA);
    } catch (error) {
      console.error('Failed to load add-ons:', error);
      toast.error('Failed to load extensions');
      setAddons(ADDONS_DATA); // Fallback to mock data
    } finally {
      setLoading(false);
    }
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

  const handleAddToCart = (addon) => {
    if (!cart.find(item => item.id === addon.id)) {
      setCart([...cart, addon]);
      setShowCart(true);
      toast.success(`${addon.name} added to cart`);
    } else {
      toast.info('Item already in cart');
    }
  };

  const handleRemoveFromCart = (addonId) => {
    setCart(cart.filter(item => item.id !== addonId));
    if (cart.length === 1) {
      setShowCart(false);
    }
  };

  const handleCheckout = () => {
    // Navigate to checkout page
    navigate('/admin/extensions/checkout');
  };

  // Filter and sort add-ons
  const filteredAddons = addons
    .filter(addon => {
      // Category filter
      if (selectedCategory !== 'all' && addon.category !== selectedCategory) {
        return false;
      }
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          addon.name.toLowerCase().includes(query) ||
          addon.description.toLowerCase().includes(query) ||
          addon.features.some(f => f.toLowerCase().includes(query))
        );
      }
      return true;
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'price-low':
          return a.price - b.price;
        case 'price-high':
          return b.price - a.price;
        case 'name':
          return a.name.localeCompare(b.name);
        case 'popular':
        default:
          return (b.popular ? 1 : 0) - (a.popular ? 1 : 0);
      }
    });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className={theme.text.secondary}>Loading extensions...</p>
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
                <SparklesIcon className="h-6 w-6 text-white" />
              </div>
              <h1 className={`text-3xl font-bold ${currentTheme === 'unicorn' ? 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400' : theme.text.primary}`}>
                Extensions & Add-ons
              </h1>
            </div>
            <p className={`${currentTheme === 'unicorn' ? 'text-purple-200/80' : theme.text.secondary} text-base`}>
              Enhance your subscription with additional services and features
            </p>
          </div>

          {/* Current tier badge */}
          {currentUser && (
            <div className={`${glassStyles.card} rounded-xl px-4 py-3`}>
              <div className={`text-sm ${theme.text.secondary} mb-1`}>Current Tier</div>
              <div className={`text-lg font-bold ${theme.text.primary} capitalize`}>
                {currentUser.subscription_tier || 'Free'}
              </div>
            </div>
          )}
        </div>
      </motion.div>

      {/* Filters & Search */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
            <input
              type="text"
              placeholder="Search extensions..."
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

          {/* Sort */}
          <div className="relative">
            <TagIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className={`w-full pl-10 pr-4 py-2 ${glassStyles.card} rounded-lg ${theme.text.primary} focus:ring-2 focus:ring-blue-500 focus:outline-none appearance-none cursor-pointer`}
            >
              {SORT_OPTIONS.map(opt => (
                <option key={opt.id} value={opt.id}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* Add-ons Grid */}
      <motion.div variants={itemVariants}>
        {filteredAddons.length === 0 ? (
          <div className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
            <SparklesIcon className={`h-16 w-16 ${theme.text.secondary} mx-auto mb-4 opacity-50`} />
            <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
              No extensions found
            </h3>
            <p className={theme.text.secondary}>
              Try adjusting your filters or search query
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAddons.map((addon) => (
              <div
                key={addon.id}
                id={`addon-${addon.id}`}
              >
                <AddonCard
                  addon={addon}
                  onAddToCart={handleAddToCart}
                  highlighted={highlightedAddon === addon.id}
                  theme={theme}
                />
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Shopping Cart Sidebar */}
      {showCart && (
        <ShoppingCart
          cart={cart}
          onRemove={handleRemoveFromCart}
          onCheckout={handleCheckout}
          onClose={() => setShowCart(false)}
          theme={theme}
        />
      )}

      {/* Floating cart button */}
      {cart.length > 0 && !showCart && (
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          onClick={() => setShowCart(true)}
          className="fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform z-40"
        >
          <ShoppingCartIcon className="h-7 w-7 text-white" />
          <span className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs font-bold flex items-center justify-center">
            {cart.length}
          </span>
        </motion.button>
      )}
    </motion.div>
  );
}
