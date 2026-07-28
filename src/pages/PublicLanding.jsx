import React, { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  MagnifyingGlassIcon,
  ChatBubbleLeftRightIcon,
  CodeBracketIcon,
  DocumentTextIcon,
  ChartBarIcon,
  CogIcon,
  ArrowRightIcon,
  GlobeAltIcon,
  CpuChipIcon,
  ServerIcon,
  SpeakerWaveIcon,
  SunIcon,
  MoonIcon,
  PaintBrushIcon,
  LockClosedIcon,
  UserCircleIcon,
  ChevronDownIcon,
  ArrowRightOnRectangleIcon,
  CreditCardIcon,
  WrenchScrewdriverIcon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';
import { ColonelLogo, MagicUnicornLogo, CenterDeepLogo } from '../components/Logos';
import { useBranding } from '../contexts/BrandingContext';
import { useTheme } from '../contexts/ThemeContext';

export default function PublicLanding() {
  const navigate = useNavigate();
  const searchInputRef = useRef(null);
  const dropdownRef = useRef(null);
  const { branding } = useBranding();
  const [searchQuery, setSearchQuery] = useState('');
  const [currentHost, setCurrentHost] = useState('localhost');
  const [userTier, setUserTier] = useState('trial');
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  const [showAdminTools, setShowAdminTools] = useState(() => {
    // Load from localStorage on init
    return localStorage.getItem('showAdminTools') === 'true';
  });
  const [myApps, setMyApps] = useState([]);
  const [isLoadingApps, setIsLoadingApps] = useState(true);
  const { theme, currentTheme, switchTheme, availableThemes } = useTheme();
  
  // Theme display configurations
  const themeDisplayNames = {
    dark: { name: 'Professional Dark', icon: MoonIcon },
    light: { name: 'Professional Light', icon: SunIcon },
    unicorn: { name: 'Magic Unicorn', icon: PaintBrushIcon },
    galaxy: { name: 'Unicorn Galaxy', icon: GlobeAltIcon },
    underground: { name: 'Underground', icon: CpuChipIcon }
  };

  // Card gradient colors - balanced dark operations palette for the launcher
  const CARD_COLORS = [
    { gradient: 'linear-gradient(135deg, #0f172a 0%, #155e75 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #1e1b4b 0%, #6d28d9 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #111827 0%, #047857 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #312e81 0%, #be123c 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #0c4a6e 0%, #1d4ed8 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #27272a 0%, #a16207 100%)', iconBg: '#0f172a' },
    { gradient: 'linear-gradient(135deg, #164e63 0%, #7c2d12 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #172554 0%, #7e22ce 100%)', iconBg: '#f8fafc' },
    { gradient: 'linear-gradient(135deg, #064e3b 0%, #0e7490 100%)', iconBg: '#0f172a' },
    { gradient: 'linear-gradient(135deg, #3f3f46 0%, #881337 100%)', iconBg: '#f8fafc' },
  ];

  const getCardColor = (index) => CARD_COLORS[index % CARD_COLORS.length];

  // Service tier mapping
  const serviceTiers = {
    'Open-WebUI': 'trial',
    'User Documentation': 'starter',
    'Bolt.diy': 'professional',
    'Grafana Monitoring': 'professional',
    'Portainer': 'professional',
    'Unicorn Orator': 'enterprise'
  };

  // Tier hierarchy for access control
  const tierHierarchy = ['trial', 'starter', 'professional', 'enterprise'];

  useEffect(() => {
    // Auto-focus search input when page loads
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }

    // Get current hostname for service links
    setCurrentHost(window.location.hostname);

    // Fetch user session to determine subscription tier and roles
    const fetchUserSession = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      try {
        const response = await fetch('/api/v1/auth/session', {
          credentials: 'include',
          signal: controller.signal
        });

        if (response.ok) {
          const data = await response.json();
          // Extract tier from session data, default to 'trial' if not found
          const tier = data?.user?.subscription_tier || data?.subscription_tier || 'trial';
          const username = data?.user?.username || data?.username || 'User';
          const email = data?.user?.email || data?.email || '';
          const roles = data?.user?.roles || data?.roles || [];

          setUserTier(tier);
          setUserInfo({ username, email, tier, roles });
        }
      } catch (error) {
        // Silent fail - default to trial tier
        console.debug('Session fetch failed, defaulting to trial tier');
        // Try to get user info from localStorage as fallback
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          try {
            const parsedUser = JSON.parse(storedUser);
            setUserInfo({
              username: parsedUser.username || 'User',
              email: parsedUser.email || '',
              tier: parsedUser.tier || 'trial',
              roles: parsedUser.roles || []
            });
          } catch (e) {
            console.debug('Failed to parse stored user info');
          }
        }
      } finally {
        clearTimeout(timeoutId);
        setIsLoadingSession(false);
      }
    };

    fetchUserSession();

    // Fetch user's authorized apps
    const fetchMyApps = async () => {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      try {
        const response = await fetch('/api/v1/my-apps/authorized', {
          credentials: 'include',
          signal: controller.signal
        });

        if (response.ok) {
          const data = await response.json();
          setMyApps(Array.isArray(data) ? data : []);
        } else {
          console.debug('my-apps returned', response.status, '— using fallback');
          setMyApps([]);
        }
      } catch (error) {
        if (error.name === 'AbortError') {
          console.debug('my-apps fetch timed out — using fallback');
        } else {
          console.debug('Error loading apps:', error);
        }
        setMyApps([]);
      } finally {
        clearTimeout(timeoutId);
        setIsLoadingApps(false);
      }
    };

    fetchMyApps();
  }, []);

  // Handle click outside dropdown to close it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    };

    if (isDropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isDropdownOpen]);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      // Open Center-Deep with the search query
      window.open(`https://search.unicorncommander.ai/search?q=${encodeURIComponent(searchQuery)}`, '_blank');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  const handleLogout = async () => {
    try {
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();

        // Clear local storage
        localStorage.removeItem('user');
        localStorage.removeItem('token');
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');

        // Redirect to Keycloak logout (clears SSO session, then shows our confirmation page)
        if (data.logout_url || data.sso_logout_url) {
          window.location.href = data.logout_url || data.sso_logout_url;
          return;
        }
      }
    } catch (error) {
      console.error('Logout failed:', error);
    }

    // Fallback: Clear local storage and redirect to home
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    window.location.href = '/auth/logout';
  };

  // Check if user has access to a service based on tier
  const hasAccess = (serviceName) => {
    // All services unlocked for now
    return true;
    // const requiredTier = serviceTiers[serviceName];
    // const userTierIndex = tierHierarchy.indexOf(userTier);
    // const requiredTierIndex = tierHierarchy.indexOf(requiredTier);
    // return userTierIndex >= requiredTierIndex;
  };

  // Handle service click
  const handleServiceClick = (e, service) => {
    if (!hasAccess(service.title)) {
      e.preventDefault();
      // Could add a modal or toast notification here
      alert(`Upgrade to ${serviceTiers[service.title]} tier or higher to access ${service.title}`);
    }
  };

  // Map API app data to service card format with appropriate styling
  const getServiceColorForCategory = (category) => {
    const categoryColors = {
      'AI & Chat': { color: 'from-blue-500 to-blue-700', textColor: 'text-blue-100' },
      'Search & Research': { color: 'from-green-500 to-green-700', textColor: 'text-green-100' },
      'Development': { color: 'from-purple-500 to-purple-700', textColor: 'text-purple-100' },
      'AI Agents': { color: 'from-purple-600 to-pink-600', textColor: 'text-purple-100' },
      'Productivity': { color: 'from-orange-500 to-orange-700', textColor: 'text-orange-100' },
      'Voice Services': { color: 'from-pink-500 to-pink-700', textColor: 'text-pink-100' }
    };
    return categoryColors[category] || { color: 'from-gray-500 to-gray-700', textColor: 'text-gray-100' };
  };

  // Convert API apps to service card format. If the API gave us nothing
  // (anonymous visitor, or the call timed out), use fallbackServices so the
  // page is never blank — restores pre-federation fast-fail behavior.
  const apiServices = myApps.map(app => {
    const colorScheme = getServiceColorForCategory(app.category);
    return {
      title: app.name,
      description: app.description,
      icon: null, // Use iconImage instead
      iconImage: app.icon_url,
      url: app.launch_url,
      color: colorScheme.color,
      textColor: colorScheme.textColor,
      accessType: app.access_type,
      featureKey: app.feature_key
    };
  });

  // Fallback static services array (used if API fails to load)
  const fallbackServices = [
    {
      title: 'Open-WebUI',
      description: 'Chat with AI models and explore advanced language capabilities',
      icon: ChatBubbleLeftRightIcon,
      iconImage: '/logos/Open-WebUI_White.png',
      url: 'https://chat.unicorncommander.ai',
      color: 'from-blue-500 to-blue-700',
      textColor: 'text-blue-100'
    },
    {
      title: 'Bolt.diy',
      description: 'AI-powered development environment for rapid prototyping',
      icon: CodeBracketIcon,
      iconImage: '/logos/bolt-diy-logo.png',
      url: 'https://bolt.unicorncommander.ai',
      color: 'from-purple-500 to-purple-700',
      textColor: 'text-purple-100'
    },
    {
      title: 'MagiCode',
      description: 'AI-powered code generation with 47+ agents - Run code locally with privacy & speed',
      icon: CodeBracketIcon,
      iconImage: '/logos/magicode-logo.png',
      url: 'https://magicode.unicorncommander.ai',
      color: 'from-purple-600 to-pink-600',
      textColor: 'text-purple-100'
    },
    {
      title: 'User Documentation',
      description: 'End-user guides and application documentation',
      icon: DocumentTextIcon,
      url: 'https://docs.unicorncommander.ai',
      color: 'from-orange-500 to-orange-700',
      textColor: 'text-orange-100'
    },
    {
      title: 'Unicorn Orator',
      description: 'Professional AI voice synthesis platform with 50+ voice options',
      icon: null,
      iconImage: '/logos/Unicorn_Orator.png',
      url: 'https://tts.unicorncommander.ai',
      color: 'from-pink-500 to-pink-700',
      textColor: 'text-pink-100'
    },
    {
      title: 'Unicorn Brigade',
      description: 'AI agent platform - Build and deploy intelligent agents',
      icon: null,
      iconImage: '/logos/The_General_Logo.png',
      url: 'https://brigade.unicorncommander.ai',
      color: 'from-purple-600 to-pink-600',
      textColor: 'text-purple-100'
    },
    {
      title: 'Forgejo',
      description: 'Self-hosted Git repository platform with CI/CD, issue tracking, and AI agent integration',
      icon: ArchiveBoxIcon,
      iconImage: null,
      url: 'https://git.unicorncommander.ai',
      color: 'from-green-500 to-emerald-600',
      textColor: 'text-green-100'
    },
    {
      title: 'Unicorn Amanuensis',
      description: 'Professional speech-to-text with speaker diarization',
      icon: null,
      iconImage: '/logos/Unicorn_Orator.png',
      url: 'https://stt.unicorncommander.ai',
      color: 'from-teal-600 to-cyan-600',
      textColor: 'text-teal-100'
    },
    {
      title: 'PresentOn',
      description: 'AI-powered presentation generation and design',
      icon: null,
      iconImage: '/logos/presenton-logo.png',
      url: 'https://presentations.unicorncommander.ai',
      color: 'from-blue-600 to-cyan-600',
      textColor: 'text-blue-100'
    },
    {
      title: 'MagicDeck',
      description: 'AI-powered presentation generator with 200+ templates and multi-agent collaboration',
      icon: null,
      iconImage: '/logos/magicdeck-logo.png',
      url: 'https://magicdeck.unicorncommander.ai',
      color: 'from-purple-600 to-indigo-600',
      textColor: 'text-purple-100'
    }
  ];

  // Use API result when present, otherwise fall back to the static list
  const services = (apiServices.length > 0 ? apiServices : fallbackServices);

  // Admin-only services (infrastructure & monitoring)
  const adminServices = [
    {
      title: 'Lago Billing',
      description: 'Subscription and billing management system',
      icon: CreditCardIcon,
      iconImage: '/logos/lago-icon.png',
      url: 'https://billing.unicorncommander.ai',
      color: 'from-green-600 to-emerald-600',
      textColor: 'text-green-100'
    },
    {
      title: 'Container Management',
      description: 'Docker container orchestration and monitoring',
      icon: ServerIcon,
      iconImage: '/logos/portainer-logo-icon.png',
      url: 'https://containers.unicorncommander.ai',
      color: 'from-indigo-500 to-indigo-700',
      textColor: 'text-indigo-100'
    },
    {
      title: 'Grafana Monitoring',
      description: 'System performance dashboards and real-time metrics',
      icon: ChartBarIcon,
      iconImage: '/logos/grafana-logo-icon.png',
      url: 'https://grafana.unicorncommander.ai',
      color: 'from-amber-500 to-orange-600',
      textColor: 'text-amber-100'
    },
    {
      title: 'Prometheus',
      description: 'Time-series metrics collection and monitoring',
      icon: ChartBarIcon,
      iconImage: '/logos/prometheus-logo-icon.png',
      url: 'https://prometheus.unicorncommander.ai',
      color: 'from-orange-500 to-red-500',
      textColor: 'text-orange-100'
    },
    {
      title: 'LiteLLM Proxy',
      description: 'Multi-provider LLM routing and management',
      icon: ServerIcon,
      iconImage: '/logos/litellm-icon.jpg',
      url: 'https://ai.unicorncommander.ai',
      color: 'from-indigo-600 to-violet-600',
      textColor: 'text-indigo-100'
    },
    {
      title: 'Umami Analytics',
      description: 'Privacy-focused website analytics platform',
      icon: ChartBarIcon,
      iconImage: '/logos/umami-logo.png',
      url: 'https://analytics.unicorncommander.ai',
      color: 'from-cyan-600 to-blue-600',
      textColor: 'text-cyan-100'
    }
  ];

  // Check if user is admin or moderator
  const isAdmin = () => {
    if (!userInfo) return false;
    // Check for admin or moderator role (could also check userTier for 'enterprise')
    const roles = userInfo.roles || [];
    return roles.includes('admin') || roles.includes('moderator');
  };

  // Handle admin tools toggle with persistence
  const handleAdminToolsToggle = () => {
    const newValue = !showAdminTools;
    setShowAdminTools(newValue);
    localStorage.setItem('showAdminTools', newValue.toString());
  };

  // Get theme-specific styling
  const getThemeStyles = () => {
    if (currentTheme === 'underground') {
      return {
        background: 'min-h-screen ops-command-bg text-slate-100',
        headerText: 'text-transparent bg-clip-text bg-gradient-to-r from-white via-violet-200 to-cyan-200',
        subText: 'text-slate-300/85',
        searchBg: 'bg-slate-950/70 backdrop-blur-xl rounded-lg shadow-2xl border border-slate-700/60',
        searchInput: 'bg-slate-950/70 border border-slate-700 text-white placeholder-slate-500 focus:ring-cyan-400',
        searchIcon: 'text-cyan-300',
        searchButton: 'bg-gradient-to-r from-violet-700 to-cyan-700 hover:from-violet-600 hover:to-cyan-600',
        cardOverlay: 'bg-slate-950/72 backdrop-blur-xl border border-slate-700/60',
        footerBg: 'bg-slate-950/82 backdrop-blur-sm border-t border-slate-800',
        logoText: 'text-slate-100',
        footerText: 'text-slate-400'
      };
    } else if (currentTheme === 'unicorn') {
      return {
        background: 'min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900',
        headerText: 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400',
        subText: 'text-purple-200/80',
        searchBg: 'bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20',
        searchInput: 'bg-white/10 border border-white/20 text-white placeholder-purple-300 focus:ring-purple-400',
        searchIcon: 'text-purple-300',
        searchButton: 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700',
        cardOverlay: 'bg-white/5 backdrop-blur-xl border border-white/10',
        footerBg: 'bg-black/20 backdrop-blur-sm border-t border-white/10',
        logoText: 'text-purple-200',
        footerText: 'text-purple-300/70'
      };
    } else if (currentTheme === 'light') {
      return {
        background: `min-h-screen ${theme.background}`,
        headerText: `${theme.text.logo}`,
        subText: `${theme.text.secondary}`,
        searchBg: `${theme.card} shadow-xl`,
        searchInput: `bg-gray-50 border border-gray-300 ${theme.text.primary} placeholder-gray-500 focus:ring-blue-500 focus:border-blue-500`,
        searchIcon: 'text-gray-600',
        searchButton: `${theme.button}`,
        cardOverlay: `${theme.card}`,
        footerBg: 'bg-gray-50/95 backdrop-blur-sm border-t border-gray-200',
        logoText: `${theme.text.primary}`,
        footerText: `${theme.text.secondary}`
      };
    } else { // dark theme
      return {
        background: `min-h-screen ${theme.background}`,
        headerText: `${theme.text.logo}`,
        subText: `${theme.text.secondary}`,
        searchBg: `${theme.card} shadow-xl`,
        searchInput: `bg-slate-700/50 border border-slate-600 ${theme.text.primary} placeholder-slate-400 focus:ring-blue-500 focus:border-blue-500`,
        searchIcon: 'text-slate-400',
        searchButton: `${theme.button}`,
        cardOverlay: `${theme.card}`,
        footerBg: 'bg-slate-900/95 backdrop-blur-sm border-t border-slate-700',
        logoText: `${theme.text.primary}`,
        footerText: `${theme.text.secondary}`
      };
    }
  };

  const styles = getThemeStyles();

  return (
    <div className={styles.background}>
      {/* Header */}
      <header className="pt-8 pb-4">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Theme Switcher & User Profile */}
          <div className="flex justify-end mb-4">
            <div className="flex items-center gap-3">
              {/* Theme Switcher */}
              <div className="flex items-center gap-2">
                {availableThemes.map((themeId) => {
                  const ThemeIcon = themeDisplayNames[themeId].icon;
                  return (
                    <button
                      key={themeId}
                      onClick={() => switchTheme(themeId)}
                      className={`p-2 rounded-lg transition-all duration-200 ${
                        currentTheme === themeId
                          ? currentTheme === 'unicorn'
                            ? 'bg-purple-600/50 text-yellow-400'
                            : currentTheme === 'light'
                            ? 'bg-blue-100 text-blue-600'
                            : 'bg-slate-700 text-blue-400'
                          : currentTheme === 'unicorn'
                          ? 'bg-white/10 text-purple-300 hover:bg-white/20'
                          : currentTheme === 'light'
                          ? 'bg-white text-gray-600 hover:bg-gray-100'
                          : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                      }`}
                      title={themeDisplayNames[themeId].name}
                    >
                      <ThemeIcon className="h-5 w-5" />
                    </button>
                  );
                })}
              </div>

              {/* User Profile Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                  className={`flex items-center gap-2 p-2 rounded-lg transition-all duration-200 ${
                    currentTheme === 'unicorn'
                      ? 'bg-white/10 text-purple-300 hover:bg-white/20'
                      : currentTheme === 'light'
                      ? 'bg-white text-gray-600 hover:bg-gray-100'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                  }`}
                  title="User Profile"
                >
                  <UserCircleIcon className="h-6 w-6" />
                  <ChevronDownIcon className={`h-4 w-4 transition-transform duration-200 ${isDropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu */}
                {isDropdownOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                    className={`absolute right-0 mt-2 w-64 rounded-xl shadow-2xl border z-50 overflow-hidden ${
                      currentTheme === 'unicorn'
                        ? 'bg-purple-900/95 backdrop-blur-xl border-white/20'
                        : currentTheme === 'light'
                        ? 'bg-white border-gray-200'
                        : 'bg-slate-800 border-slate-700'
                    }`}
                  >
                    {/* User Info Header */}
                    <div className={`p-4 border-b ${
                      currentTheme === 'unicorn'
                        ? 'border-white/10'
                        : currentTheme === 'light'
                        ? 'border-gray-200'
                        : 'border-slate-700'
                    }`}>
                      <div className="flex items-center gap-3">
                        <UserCircleIcon className={`h-10 w-10 ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-300'
                            : currentTheme === 'light'
                            ? 'text-gray-600'
                            : 'text-slate-400'
                        }`} />
                        <div className="flex-1 min-w-0">
                          <div className={`font-semibold truncate ${
                            currentTheme === 'unicorn'
                              ? 'text-white'
                              : currentTheme === 'light'
                              ? 'text-gray-900'
                              : 'text-white'
                          }`}>
                            {userInfo?.username || 'User'}
                          </div>
                          {userInfo?.email && (
                            <div className={`text-xs truncate ${
                              currentTheme === 'unicorn'
                                ? 'text-purple-300'
                                : currentTheme === 'light'
                                ? 'text-gray-600'
                                : 'text-slate-400'
                            }`}>
                              {userInfo.email}
                            </div>
                          )}
                          <div className={`text-xs font-medium mt-1 inline-block px-2 py-0.5 rounded-full ${
                            currentTheme === 'unicorn'
                              ? 'bg-purple-600/50 text-yellow-400'
                              : currentTheme === 'light'
                              ? 'bg-blue-100 text-blue-700'
                              : 'bg-slate-700 text-blue-400'
                          }`}>
                            {userTier.charAt(0).toUpperCase() + userTier.slice(1)}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Menu Items */}
                    <div className="py-2">
                      <button
                        onClick={() => {
                          setIsDropdownOpen(false);
                          navigate('/admin');
                        }}
                        className={`w-full px-4 py-2.5 text-left flex items-center gap-3 transition-colors ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-white/10'
                            : currentTheme === 'light'
                            ? 'text-gray-700 hover:bg-gray-100'
                            : 'text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <CpuChipIcon className="h-5 w-5" />
                        <span>Admin Dashboard</span>
                      </button>

                      <button
                        onClick={() => {
                          setIsDropdownOpen(false);
                          navigate('/admin/user-settings');
                        }}
                        className={`w-full px-4 py-2.5 text-left flex items-center gap-3 transition-colors ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-white/10'
                            : currentTheme === 'light'
                            ? 'text-gray-700 hover:bg-gray-100'
                            : 'text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <UserCircleIcon className="h-5 w-5" />
                        <span>User Settings</span>
                      </button>

                      <button
                        onClick={() => {
                          setIsDropdownOpen(false);
                          navigate('/admin/subscription/plan');
                        }}
                        className={`w-full px-4 py-2.5 text-left flex items-center gap-3 transition-colors ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-white/10'
                            : currentTheme === 'light'
                            ? 'text-gray-700 hover:bg-gray-100'
                            : 'text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <CreditCardIcon className="h-5 w-5" />
                        <span>Billing</span>
                      </button>

                      <button
                        onClick={() => {
                          window.open(`http://${currentHost}:8086`, '_blank');
                          setIsDropdownOpen(false);
                        }}
                        className={`w-full px-4 py-2.5 text-left flex items-center gap-3 transition-colors ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-white/10'
                            : currentTheme === 'light'
                            ? 'text-gray-700 hover:bg-gray-100'
                            : 'text-slate-300 hover:bg-slate-700'
                        }`}
                      >
                        <DocumentTextIcon className="h-5 w-5" />
                        <span>Documentation</span>
                      </button>
                    </div>

                    {/* Divider */}
                    <div className={`border-t ${
                      currentTheme === 'unicorn'
                        ? 'border-white/10'
                        : currentTheme === 'light'
                        ? 'border-gray-200'
                        : 'border-slate-700'
                    }`} />

                    {/* Logout Button */}
                    <div className="py-2">
                      <button
                        onClick={() => {
                          setIsDropdownOpen(false);
                          handleLogout();
                        }}
                        className={`w-full px-4 py-2.5 text-left flex items-center gap-3 transition-colors ${
                          currentTheme === 'unicorn'
                            ? 'text-red-400 hover:bg-red-500/20'
                            : currentTheme === 'light'
                            ? 'text-red-600 hover:bg-red-50'
                            : 'text-red-400 hover:bg-red-900/20'
                        }`}
                      >
                        <ArrowRightOnRectangleIcon className="h-5 w-5" />
                        <span>Logout</span>
                      </button>
                    </div>
                  </motion.div>
                )}
              </div>
            </div>
          </div>
          
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center"
          >
            {/* Logo and Title - Compact on Desktop */}
            <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8 mb-4">
              {/* Tenant logo from BrandingContext */}
              <img
                src={branding?.logo_url || "/logos/colonel-logo.png"}
                alt={branding?.company_name || "Unicorn Commander"}
                className="w-24 h-24 md:w-28 md:h-28 drop-shadow-2xl object-contain"
                onError={(e) => { e.currentTarget.src = "/logos/colonel-logo.png"; }}
              />
              <div className="text-center md:text-left">
                <div className="flex flex-col md:flex-row md:items-baseline md:gap-3">
                  <h1 className={`text-3xl md:text-4xl lg:text-5xl font-bold ${styles.headerText} ${currentTheme === 'unicorn' || currentTheme === 'underground' ? 'animate-gradient' : ''}`}>
                    {branding?.company_name || "Unicorn Commander"}
                  </h1>
                </div>
                <p className={`text-base md:text-lg ${styles.subText} mt-2`}>
                  {branding?.tagline || "Your services. Your infrastructure. One dashboard."}
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </header>

      {/* Services Grid */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12"
      >
        <h2 className={`text-2xl font-bold text-center mb-6 ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
          My Apps
        </h2>

        {isLoadingApps ? (
          /* Loading State */
          <div className="flex justify-center items-center py-12">
            <div className={`text-center ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.secondary}`}>
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-current mx-auto mb-4"></div>
              <p>Loading your apps...</p>
            </div>
          </div>
        ) : services.length === 0 ? (
          /* Empty State */
          <div className={`${styles.cardOverlay} rounded-xl p-12 text-center`}>
            <ServerIcon className={`h-16 w-16 mx-auto mb-4 ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.secondary}`} />
            <h3 className={`text-xl font-semibold mb-2 ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
              No Apps Available
            </h3>
            <p className={styles.subText}>
              Upgrade your subscription to access apps, or contact support if you believe this is an error.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {services.map((service, index) => {
            const isLocked = !hasAccess(service.title);
            const requiredTier = serviceTiers[service.title];
            const cardColor = getCardColor(index);

            return (
              <motion.div
                key={service.title}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.05 * index }}
              >
                <a
                  href={service.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`block group ${isLocked ? 'cursor-not-allowed' : ''}`}
                  onClick={(e) => handleServiceClick(e, service)}
                >
                  <div
                    className={`relative rounded-lg overflow-hidden transition-all duration-300 ops-app-card ${
                      isLocked
                        ? 'opacity-40'
                        : 'hover:-translate-y-1 hover:shadow-[0_16px_36px_rgba(8,47,73,0.28)]'
                    }`}
                    style={{ minHeight: '250px' }}
                  >
                    {/* Gradient background */}
                    <div className="absolute inset-0" style={{ background: cardColor.gradient }} />

                    {/* Subtle noise texture overlay */}
                    <div className="absolute inset-0 bg-white/[0.02]" />

                    {/* Gradient border — visible by default, brighter on hover */}
                    <div className="absolute inset-0 rounded-lg border border-white/[0.10] group-hover:border-cyan-200/30 transition-colors duration-300" />

                    {/* Top glow accent on hover */}
                    <div
                      className="absolute top-0 left-1/2 -translate-x-1/2 w-3/4 h-[1px] opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                      style={{ background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.5), transparent)' }}
                    />

                    {/* Lock Overlay */}
                    {isLocked && (
                      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm z-10 flex items-center justify-center">
                        <div className="text-center">
                          <LockClosedIcon className="h-8 w-8 text-white/70 mx-auto mb-1.5" />
                          <div className="text-white/70 font-medium text-xs capitalize">{requiredTier} tier required</div>
                        </div>
                      </div>
                    )}

                    {/* Card content */}
                    <div className="relative z-[1] h-full flex flex-col p-5">
                      {/* Tags — top right */}
                      {service.featureKey && (() => {
                        const tagMap = {
                          'chat_access':        ['AI Chat', 'LLM'],
                          'search_enabled':     ['Search', 'AI'],
                          'bolt_access':        ['IDE', 'Full-Stack'],
                          'brigade_access':     ['AI Agents', 'Orchestration'],
                          'tts_enabled':        ['TTS', 'Voice'],
                          'stt_enabled':        ['STT', 'Voice'],
                          'forgejo':            ['Git', 'CI/CD'],
                          'presenton_access':   ['Presentations', 'AI'],
                          'partnerpulse':       ['Dating', 'Relationships'],
                          'project_ops_access': ['Project Mgmt', 'Ops'],
                          'umami_access':       ['Analytics', 'Privacy'],
                          'listmonk':           ['Email', 'Marketing'],
                          'postiz':             ['Social', 'Scheduling'],
                          'nda_internal':       ['Business', 'NDA'],
                          'nda_visualization':  ['Business', 'Workflow'],
                          'nda_proposal':       ['Business', 'NDA'],
                        };
                        const tags = tagMap[service.featureKey] || ['App'];
                        return (
                          <div className="absolute top-4 right-4 flex gap-1.5">
                            {tags.map(tag => (
                              <span key={tag} className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider rounded-full bg-white/10 text-white/50 border border-white/[0.08]">
                                {tag}
                              </span>
                            ))}
                          </div>
                        );
                      })()}

                      {/* Icon — large, prominent */}
                      <div className="mb-4 transition-transform duration-300 group-hover:scale-105">
                        {service.iconImage ? (
                          <img
                            src={service.iconImage}
                            alt={service.title}
                            className="w-[52px] h-[52px] object-contain drop-shadow-[0_4px_16px_rgba(0,0,0,0.35)] rounded-lg"
                          />
                        ) : service.icon ? (
                          <service.icon className="h-12 w-12 text-white/80 drop-shadow-lg" />
                        ) : (
                          <ServerIcon className="h-12 w-12 text-white/80 drop-shadow-lg" />
                        )}
                      </div>

                      {/* App name */}
                      <h3 className="text-white font-bold text-base leading-snug mb-2 tracking-tight">
                        {service.title}
                      </h3>

                      {/* Description — readable, multi-line */}
                      <p className="text-white/66 text-sm leading-relaxed flex-1 line-clamp-3">
                        {service.description}
                      </p>

                      {/* Bottom row — launch hint */}
                      <div className="mt-4 pt-3 border-t border-white/[0.08] flex items-center justify-between">
                        <span className="text-white/38 text-xs font-medium group-hover:text-white/70 transition-colors duration-300">
                          Launch app
                        </span>
                        <div className="w-7 h-7 rounded-lg bg-white/[0.07] group-hover:bg-white/[0.16] flex items-center justify-center transition-all duration-300">
                          <ArrowRightIcon className="h-3.5 w-3.5 text-white/40 group-hover:text-white/80 group-hover:translate-x-0.5 transition-all duration-300" />
                        </div>
                      </div>
                    </div>
                  </div>
                </a>
              </motion.div>
            );
          })}
          </div>
        )}
      </motion.div>

      {/* Admin Tools Section - Only visible to admin/moderator users */}
      {isAdmin() && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-12"
        >
          {/* Toggle Header */}
          <div className={`${styles.cardOverlay} rounded-lg p-6 mb-6 border ${
            currentTheme === 'unicorn'
              ? 'border-purple-500/30'
              : currentTheme === 'light'
              ? 'border-gray-300'
              : 'border-slate-600'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <WrenchScrewdriverIcon className={`h-7 w-7 ${
                  currentTheme === 'unicorn'
                    ? 'text-yellow-400'
                    : currentTheme === 'light'
                    ? 'text-blue-600'
                    : 'text-blue-400'
                }`} />
                <div>
                  <h3 className={`text-2xl font-bold ${
                    currentTheme === 'unicorn'
                      ? 'text-white'
                      : theme.text.primary
                  }`}>
                    Administration & Monitoring
                  </h3>
                  <p className={`text-sm ${styles.subText} mt-1`}>
                    Infrastructure management and system monitoring tools
                  </p>
                </div>
              </div>

              {/* Toggle Switch */}
              <button
                onClick={handleAdminToolsToggle}
                className={`relative inline-flex h-8 w-16 items-center rounded-full transition-colors duration-200 ${
                  showAdminTools
                    ? currentTheme === 'unicorn'
                      ? 'bg-purple-600'
                      : 'bg-blue-600'
                    : currentTheme === 'unicorn'
                    ? 'bg-white/20'
                    : currentTheme === 'light'
                    ? 'bg-gray-300'
                    : 'bg-slate-600'
                }`}
              >
                <span
                  className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform duration-200 shadow-lg ${
                    showAdminTools ? 'translate-x-9' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>

          {/* Admin Services Grid - Conditionally rendered */}
          {showAdminTools && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.4 }}
              className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {adminServices.map((service, index) => {
                // Offset admin cards by 5 to get different colors than user apps
                const cardColor = getCardColor(index + 5);

                return (
                  <motion.div
                    key={service.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 * index }}
                  >
                    <a
                      href={service.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block group"
                    >
                      <div
                        className="rounded-lg shadow-lg transition-all duration-300 border border-white/15 overflow-hidden hover:shadow-2xl hover:-translate-y-1"
                        style={{
                          background: cardColor.gradient,
                          height: '300px',
                          display: 'flex',
                          flexDirection: 'column'
                        }}
                      >
                        {/* Icon Section - Top */}
                        <div className="p-6 pt-8 flex justify-center">
                          <div
                            className="w-16 h-16 rounded-lg flex items-center justify-center shadow-lg p-3"
                            style={{ backgroundColor: cardColor.iconBg }}
                          >
                            {service.iconImage ? (
                              <img
                                src={service.iconImage}
                                alt={service.title}
                                className="w-full h-full object-contain"
                              />
                            ) : service.icon ? (
                              <service.icon
                                className="h-12 w-12"
                                style={{ color: cardColor.iconBg === '#ffffff' ? '#667eea' : '#ffffff' }}
                              />
                            ) : (
                              <ServerIcon
                                className="h-12 w-12"
                                style={{ color: cardColor.iconBg === '#ffffff' ? '#667eea' : '#ffffff' }}
                              />
                            )}
                          </div>
                        </div>

                        {/* Content Section - White Background Bottom */}
                        <div
                          className="flex-1 flex flex-col px-6 pb-6 pt-4 mt-auto"
                          style={{
                            background: 'rgba(255,255,255,0.95)',
                            borderTopLeftRadius: '8px',
                            borderTopRightRadius: '8px'
                          }}
                        >
                          <h3 className="text-xl font-bold text-gray-900 leading-tight text-center mb-2">
                            {service.title}
                          </h3>

                          <p className="text-gray-600 text-sm leading-relaxed text-center flex-1 line-clamp-2">
                            {service.description?.length > 80
                              ? service.description.substring(0, 80) + '...'
                              : service.description}
                          </p>

                          {/* Launch Button */}
                          <button
                            className="mt-3 w-full py-2 px-4 rounded-lg font-semibold text-white text-sm transition-all duration-200 flex items-center justify-center gap-2"
                            style={{ background: cardColor.gradient }}
                          >
                            <span>Launch</span>
                            <ArrowRightIcon className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                          </button>
                        </div>
                      </div>
                    </a>
                  </motion.div>
                );
              })}
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Admin Dashboard Access */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 mb-8"
      >
        <div className={`${styles.cardOverlay} rounded-lg p-6 text-center`}>
          <div className="flex items-center justify-center gap-2 mb-4">
            <CogIcon className={`h-6 w-6 ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`} />
            <h3 className={`text-xl font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
              System Administration
            </h3>
          </div>

          <p className={`${styles.subText} mb-4`}>
            Access the admin dashboard to manage your Magic Unicorn services
          </p>

          <button
            onClick={() => navigate('/admin')}
            className={`px-8 py-3 rounded-lg transition-all duration-200 flex items-center gap-2 mx-auto text-white ${styles.searchButton}`}
          >
            <CpuChipIcon className="h-5 w-5" />
            <span>Admin Dashboard</span>
            <ArrowRightIcon className="h-4 w-4" />
          </button>
        </div>
      </motion.div>

      {/* Footer */}
      <footer className={`${styles.footerBg} py-8 mt-16`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <img
                src={branding?.logo_url || "/logos/colonel-logo.png"}
                alt={branding?.company_name || "Unicorn Commander"}
                className="w-10 h-10 object-contain"
                onError={(e) => { e.currentTarget.src = "/logos/colonel-logo.png"; }}
              />
              <div className={styles.logoText}>
                <div className="font-semibold">{branding?.company_name || "Unicorn Commander"}</div>
                <div className={`text-sm ${styles.footerText}`}>Magic Unicorn Unconventional Technology &amp; Stuff Inc</div>
              </div>
            </div>

            <div className={`text-center md:text-right text-sm ${styles.footerText}`}>
              <div className="flex items-center gap-2 justify-center md:justify-end mb-1">
                <span>Experiments • Deployments • Breakthroughs</span>
              </div>
              <div className="flex items-center gap-2 justify-center md:justify-end">
                <img src="/logos/colonel-logo.png" alt="" className="w-5 h-5" />
                <a href="https://magicunicorn.tech" target="_blank" rel="noopener noreferrer" className="hover:text-fuchsia-400 underline">
                  Magic Unicorn Unconventional Technology & Stuff Inc
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
