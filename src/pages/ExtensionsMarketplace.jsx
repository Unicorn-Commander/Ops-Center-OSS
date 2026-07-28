import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ShoppingCartIcon,
  CheckCircleIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  SparklesIcon,
  ServerIcon,
  UsersIcon,
  CodeBracketIcon,
  ChartBarIcon,
  CreditCardIcon,
  XMarkIcon,
  ArrowRightIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  TagIcon
} from '@heroicons/react/24/outline';
import { getGlassmorphismStyles } from '../styles/glassmorphism';
import { useTheme } from '../contexts/ThemeContext';
import { useExtensions } from '../contexts/ExtensionsContext';
import extensionsApi from '../api/extensionsApi';

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

// Sort options
const SORT_OPTIONS = [
  { id: 'name', label: 'Name (A-Z)' },
  { id: 'price-low', label: 'Price: Low to High' },
  { id: 'price-high', label: 'Price: High to Low' }
];

// Purely presentational icon/color per category (data itself comes from the API)
const CATEGORY_STYLES = {
  'ai-services': { icon: SparklesIcon, color: 'from-pink-500 to-rose-500' },
  services: { icon: ServerIcon, color: 'from-blue-500 to-cyan-500' },
  infrastructure: { icon: ServerIcon, color: 'from-green-500 to-emerald-500' },
  tools: { icon: CodeBracketIcon, color: 'from-purple-500 to-indigo-500' },
  analytics: { icon: ChartBarIcon, color: 'from-violet-500 to-purple-500' },
  enterprise: { icon: UsersIcon, color: 'from-cyan-500 to-blue-500' }
};

const getCategoryStyle = (category) =>
  CATEGORY_STYLES[(category || '').toLowerCase()] || { icon: SparklesIcon, color: 'from-blue-500 to-cyan-500' };

// Normalize the JSONB features column into a display list of strings
const normalizeFeatures = (features) => {
  if (!features) return [];
  if (Array.isArray(features)) return features.map(String);
  if (typeof features === 'object') {
    return Object.entries(features).map(([key, value]) =>
      value === true ? key : `${key}: ${value}`
    );
  }
  return [String(features)];
};

// Format currency
const formatCurrency = (amount) => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD'
  }).format(amount);
};

const formatBillingPeriod = (billingType) => {
  if (!billingType) return 'month';
  return billingType === 'one_time' ? 'one-time' : billingType.replace(/_/g, ' ');
};

// Add-on card component
const AddonCard = ({ addon, onAddToCart, inCart, highlighted, theme }) => {
  const glassStyles = getGlassmorphismStyles(theme.currentTheme);
  const isPurchased = addon.status === 'purchased';
  const { icon: Icon, color } = getCategoryStyle(addon.category);

  return (
    <motion.div
      variants={itemVariants}
      whileHover={{ scale: 1.02, y: -4 }}
      className={`relative ${glassStyles.card} rounded-2xl p-6 shadow-xl ${
        highlighted ? 'ring-2 ring-yellow-500 ring-offset-2 ring-offset-gray-900' : ''
      } ${isPurchased ? 'opacity-75' : ''}`}
    >
      {/* Icon */}
      <div className={`w-16 h-16 bg-gradient-to-br ${color} rounded-2xl flex items-center justify-center shadow-2xl mb-4`}>
        <Icon className="h-8 w-8 text-white" />
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
      {addon.features.length > 0 && (
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
      )}

      {/* Action button */}
      {isPurchased ? (
        <button
          disabled
          className="w-full py-3 px-4 bg-green-500/20 text-green-400 rounded-lg font-semibold flex items-center justify-center gap-2 cursor-not-allowed"
        >
          <CheckCircleIcon className="h-5 w-5" />
          Purchased
        </button>
      ) : inCart ? (
        <button
          disabled
          className="w-full py-3 px-4 bg-blue-500/20 text-blue-400 rounded-lg font-semibold flex items-center justify-center gap-2 cursor-not-allowed"
        >
          <ShoppingCartIcon className="h-5 w-5" />
          In Cart
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

// Shopping cart sidebar - driven by the server-side cart
const ShoppingCart = ({ cart, onRemove, onCheckout, onClose, theme }) => {
  const glassStyles = getGlassmorphismStyles(theme.currentTheme);
  const items = cart.items || [];

  if (items.length === 0) {
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
          {items.length} {items.length === 1 ? 'item' : 'items'}
        </p>
      </div>

      {/* Cart items */}
      <div className="p-6 space-y-3 max-h-96 overflow-y-auto">
        {items.map((item) => {
          const { icon: ItemIcon, color } = getCategoryStyle(item.category);
          return (
            <div
              key={item.cart_item_id}
              className={`${glassStyles.card} rounded-lg p-4 flex items-start gap-3`}
            >
              <div className={`w-10 h-10 bg-gradient-to-br ${color} rounded-lg flex items-center justify-center flex-shrink-0`}>
                <ItemIcon className="h-5 w-5 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <h4 className={`text-sm font-semibold ${theme.text.primary} truncate`}>
                  {item.name}
                </h4>
                <p className={`text-xs ${theme.text.secondary}`}>
                  {formatCurrency(Number(item.base_price))}
                  {item.quantity > 1 ? ` × ${item.quantity}` : ''}
                </p>
              </div>
              <button
                onClick={() => onRemove(item.cart_item_id)}
                className="p-1 hover:bg-red-500/20 rounded transition-colors"
              >
                <XMarkIcon className="h-5 w-5 text-red-400" />
              </button>
            </div>
          );
        })}
      </div>

      {/* Subtotal */}
      <div className="p-6 border-t border-white/10 space-y-4">
        <div className="flex items-center justify-between">
          <span className={`text-base font-semibold ${theme.text.secondary}`}>
            Subtotal
          </span>
          <span className={`text-2xl font-bold ${theme.text.primary}`}>
            {formatCurrency(Number(cart.subtotal ?? cart.total ?? 0))}
          </span>
        </div>

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
  const glassStyles = getGlassmorphismStyles(currentTheme);

  // Server-backed cart + active add-ons (shared with the checkout page)
  const { cart, addToCart, removeFromCart, activeAddons, loadActiveAddons, loadCart } = useExtensions();

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);
  const [addons, setAddons] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [showCart, setShowCart] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [sortBy, setSortBy] = useState('name');
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedAddon, setHighlightedAddon] = useState(null);

  useEffect(() => {
    loadAddons();
    loadCurrentUser();
    loadCart();
    loadActiveAddons();

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
      setLoadError(null);
      // Real catalog: GET /api/v1/extensions/catalog returns a list of
      // { id, name, description, category, base_price, billing_type, features }
      const data = await extensionsApi.getCatalog({ limit: 100 });
      const list = Array.isArray(data) ? data : (data.addons || []);
      setAddons(list.map((addon) => ({
        id: addon.id,
        name: addon.name,
        category: addon.category || 'other',
        price: Number(addon.base_price ?? 0),
        period: formatBillingPeriod(addon.billing_type),
        description: addon.description || '',
        features: normalizeFeatures(addon.features)
      })));
    } catch (error) {
      console.error('Failed to load add-ons:', error);
      // Honest error state - no fake catalog
      setAddons([]);
      setLoadError('Unable to load the extensions catalog right now.');
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

  const handleAddToCart = async (addon) => {
    const result = await addToCart(addon.id, 1);
    if (result.success) {
      setShowCart(true);
    }
  };

  const handleRemoveFromCart = async (cartItemId) => {
    const result = await removeFromCart(cartItemId);
    if (result.success && (result.cart?.items || []).length === 0) {
      setShowCart(false);
    }
  };

  const handleCheckout = () => {
    // The checkout page drives the same server cart through Stripe
    navigate('/admin/extensions/checkout');
  };

  // Purchased add-on ids (real /api/v1/extensions/active data)
  const purchasedIds = new Set((activeAddons || []).map(a => String(a.addon_id ?? a.id)));
  const cartAddonIds = new Set((cart.items || []).map(i => String(i.addon_id)));

  // Categories derived from the real catalog
  const categoryIds = Array.from(new Set(addons.map(a => a.category))).sort();
  const categories = [
    { id: 'all', label: 'All Extensions' },
    ...categoryIds.map(id => ({
      id,
      label: id.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    }))
  ];

  // Filter and sort add-ons
  const filteredAddons = addons
    .map(addon => ({
      ...addon,
      status: purchasedIds.has(String(addon.id)) ? 'purchased' : 'available'
    }))
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
        default:
          return a.name.localeCompare(b.name);
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

          {/* Current tier badge - only when the API reports a tier */}
          {currentUser?.subscription_tier && (
            <div className={`${glassStyles.card} rounded-xl px-4 py-3`}>
              <div className={`text-sm ${theme.text.secondary} mb-1`}>Current Tier</div>
              <div className={`text-lg font-bold ${theme.text.primary} capitalize`}>
                {currentUser.subscription_tier}
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
              {categories.map(cat => (
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
        {loadError ? (
          <div className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
            <ExclamationTriangleIcon className="h-16 w-16 text-red-400 mx-auto mb-4 opacity-70" />
            <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
              Couldn't load extensions
            </h3>
            <p className={`${theme.text.secondary} mb-4`}>{loadError}</p>
            <button
              onClick={loadAddons}
              className="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              <ArrowPathIcon className="h-4 w-4" />
              Try Again
            </button>
          </div>
        ) : addons.length === 0 ? (
          <div className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
            <SparklesIcon className={`h-16 w-16 ${theme.text.secondary} mx-auto mb-4 opacity-50`} />
            <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
              No extensions published yet
            </h3>
            <p className={theme.text.secondary}>
              Check back soon — new add-ons will appear here as they are released.
            </p>
          </div>
        ) : filteredAddons.length === 0 ? (
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
                  inCart={cartAddonIds.has(String(addon.id))}
                  highlighted={highlightedAddon != null && String(addon.id) === String(highlightedAddon)}
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
      {(cart.items || []).length > 0 && !showCart && (
        <motion.button
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0, opacity: 0 }}
          onClick={() => setShowCart(true)}
          className="fixed bottom-8 right-8 w-16 h-16 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full shadow-2xl flex items-center justify-center hover:scale-110 transition-transform z-40"
        >
          <ShoppingCartIcon className="h-7 w-7 text-white" />
          <span className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full text-xs font-bold flex items-center justify-center">
            {(cart.items || []).length}
          </span>
        </motion.button>
      )}
    </motion.div>
  );
}
