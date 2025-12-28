import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
  HomeIcon,
  CubeIcon,
  CogIcon,
  ServerIcon,
  ChartBarIcon,
  WifiIcon,
  SunIcon,
  MoonIcon,
  QuestionMarkCircleIcon,
  ArchiveBoxIcon,
  PuzzlePieceIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  KeyIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  PaintBrushIcon,
  ChevronDownIcon,
  CurrencyDollarIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import { ColonelLogo, MagicUnicornLogo, CenterDeepLogo } from './Logos';

// Role hierarchy for permission checking
const ROLE_HIERARCHY = {
  admin: 3,
  power_user: 2,
  user: 1,
  trial: 0
};

// Helper function to check role permissions
function checkRolePermission(userRole, requiredRole) {
  const userLevel = ROLE_HIERARCHY[userRole] || 0;
  const requiredLevel = ROLE_HIERARCHY[requiredRole] || 0;
  return userLevel >= requiredLevel;
}

const navigation = [
  // All users can access these
  { name: 'Dashboard', href: '/admin/', icon: HomeIcon, requiredRole: 'user' },
  { name: 'Services', href: '/admin/services', icon: ServerIcon, requiredRole: 'user' },
  { name: 'Logs', href: '/admin/logs', icon: DocumentTextIcon, requiredRole: 'user' },
  { name: 'Settings', href: '/admin/settings', icon: CogIcon, requiredRole: 'user' },
  { name: 'Landing Page', href: '/admin/landing', icon: PaintBrushIcon, requiredRole: 'user' },

  // Power User and above
  { name: 'Models & AI', href: '/admin/models', icon: CubeIcon, requiredRole: 'power_user', badge: 'Pro' },
  { name: 'Model Servers', href: '/admin/model-servers', icon: ServerIcon, requiredRole: 'power_user', badge: 'Pro' },
  { name: 'Resources', href: '/admin/system', icon: ChartBarIcon, requiredRole: 'power_user', badge: 'Pro' },
  { name: 'Network', href: '/admin/network', icon: WifiIcon, requiredRole: 'power_user', badge: 'Pro' },
  { name: 'Storage', href: '/admin/storage', icon: ArchiveBoxIcon, requiredRole: 'power_user', badge: 'Pro' },

  // Admin only
  { name: 'Subscriptions', href: '/admin/subscription-management', icon: CurrencyDollarIcon, requiredRole: 'admin', badge: 'Admin' },
  { name: 'Billing', href: 'https://billing.your-domain.com', icon: CurrencyDollarIcon, external: true, requiredRole: 'admin', badge: 'Admin' },
  { name: 'Security', href: '/admin/security', icon: ShieldCheckIcon, requiredRole: 'admin', badge: 'Admin' },
  { name: 'Authentication', href: '/admin/authentication', icon: KeyIcon, requiredRole: 'admin', badge: 'Admin' },
  { name: 'Extensions', href: '/admin/extensions', icon: PuzzlePieceIcon, requiredRole: 'admin', badge: 'Admin' },
];

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, currentTheme, switchTheme, availableThemes, isDarkMode, toggleDarkMode } = useTheme();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Theme configurations for display names
  const themes = {
    dark: { name: 'Dark', icon: '🌙' },
    light: { name: 'Light', icon: '☀️' },
    unicorn: { name: 'Unicorn', icon: '🦄' }
  };

  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');

  // Get user role with fallback
  const userRole = userInfo.role || 'user';

  // Get user initials for avatar
  const getUserInitials = () => {
    if (userInfo.name) {
      return userInfo.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
    } else if (userInfo.username) {
      return userInfo.username.slice(0, 2).toUpperCase();
    }
    return 'UC';
  };

  // Check if user is admin
  const isAdmin = userInfo.role === 'admin' || userInfo.is_superuser || userInfo.username === 'aaron' || userInfo.username === 'akadmin';

  // Filter navigation based on user role
  const filteredNavigation = navigation.filter(item => {
    // If no role requirement, show to everyone
    if (!item.requiredRole) return true;

    // Admins see everything
    if (userRole === 'admin') return true;

    // Check if user has sufficient permissions
    return checkRolePermission(userRole, item.requiredRole);
  });

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    navigate('/login');
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const themeClasses = {
    background: `min-h-screen ${theme.background}`,
    sidebar: theme.sidebar,
    nav: currentTheme === 'unicorn' 
      ? 'hover:bg-white/10'
      : currentTheme === 'light'
      ? 'hover:bg-gray-100'
      : 'hover:bg-slate-700/50',
    logo: theme.text.logo,
    brandText: theme.text.secondary,
    themeLabel: theme.text.secondary
  };

  return (
    <div className={themeClasses.background}>
      <div className="flex h-screen">
        {/* Sidebar */}
        <div className="hidden md:flex md:w-64 md:flex-col">
          <div className={`flex flex-col flex-grow pt-5 pb-4 overflow-y-auto ${themeClasses.sidebar}`}>
            {/* Brand Header */}
            <div className="flex flex-col items-center flex-shrink-0 px-4 mb-8">
              {/* Main Logo Area - Unicorn Commander prominent at top */}
              <div className="flex items-center gap-3 mb-3">
                {/* The Colonel Logo */}
                <ColonelLogo className="w-14 h-14 drop-shadow-xl" />
                <div className="text-center">
                  <h1 className={`text-2xl font-bold ${themeClasses.logo} leading-tight`}>
                    Ops Center
                  </h1>
                  <div className={`text-lg ${currentTheme === 'unicorn' ? 'text-purple-200/80' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'} font-medium`}>
                    UC-1 Pro Control
                  </div>
                </div>
              </div>
              
              {/* System Management - subtitle */}
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200/70' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-2 font-medium`}>
                System Management Console
              </div>
              
              {/* Version */}
              <div className={`text-xs ${currentTheme === 'unicorn' ? 'text-purple-300/60' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-500'} font-mono`}>
                v1.0.0
              </div>
            </div>
            <div className="mt-8 flex flex-col flex-1">
              <nav className="flex-1 px-2 space-y-1">
                {filteredNavigation.map((item) => {
                  const isActive = location.pathname === item.href;
                  const LinkComponent = item.external ? 'a' : Link;
                  const linkProps = item.external
                    ? { href: item.href, target: '_blank', rel: 'noopener noreferrer' }
                    : { to: item.href };

                  return (
                    <LinkComponent
                      key={item.name}
                      {...linkProps}
                      className={`
                        group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200
                        ${isActive
                          ? currentTheme === 'unicorn'
                            ? 'bg-white/20 text-white shadow-lg backdrop-blur-sm border border-white/20'
                            : currentTheme === 'light'
                            ? 'bg-blue-100 text-blue-900'
                            : 'bg-blue-900 text-blue-100'
                          : currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-white/10 hover:text-white'
                            : currentTheme === 'light'
                            ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                            : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                        }
                      `}
                    >
                      <div className="flex items-center">
                        <item.icon
                          className={`
                            mr-3 flex-shrink-0 h-5 w-5
                            ${isActive
                              ? currentTheme === 'unicorn'
                                ? 'text-yellow-400'
                                : currentTheme === 'light'
                                ? 'text-blue-600'
                                : 'text-blue-400'
                              : currentTheme === 'unicorn'
                                ? 'text-purple-300 group-hover:text-yellow-300'
                                : currentTheme === 'light'
                                ? 'text-gray-400 group-hover:text-gray-600'
                                : 'text-gray-400 group-hover:text-gray-300'
                            }
                          `}
                          aria-hidden="true"
                        />
                        {item.name}
                      </div>
                      {item.badge && (
                        <span className={`
                          text-xs px-2 py-0.5 rounded-full font-semibold
                          ${item.badge === 'Admin'
                            ? currentTheme === 'unicorn'
                              ? 'bg-red-500/20 text-red-300 border border-red-400/30'
                              : currentTheme === 'light'
                              ? 'bg-red-100 text-red-700 border border-red-200'
                              : 'bg-red-900/30 text-red-300 border border-red-700/50'
                            : currentTheme === 'unicorn'
                              ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-400/30'
                              : currentTheme === 'light'
                              ? 'bg-blue-100 text-blue-700 border border-blue-200'
                              : 'bg-blue-900/30 text-blue-300 border border-blue-700/50'
                          }
                        `}>
                          {item.badge}
                        </span>
                      )}
                    </LinkComponent>
                  );
                })}
              </nav>
              
              {/* Help Button */}
              <div className="px-2 mb-4">
                <button
                  onClick={() => {
                    const currentHost = window.location.hostname;
                    window.open(`http://${currentHost}:8086`, '_blank');
                  }}
                  className={`w-full flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                    currentTheme === 'unicorn'
                      ? 'text-purple-200 hover:bg-white/10 hover:text-white'
                      : currentTheme === 'light'
                      ? 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  <QuestionMarkCircleIcon className="h-5 w-5" />
                  Help & Documentation
                </button>
              </div>
              
              {/* User Info and Logout */}
              <div className="px-2 mb-4">
                <div className="border-t border-white/10 pt-4">
                  {userInfo.username && (
                    <div className={`flex items-center gap-2 px-2 mb-3 text-sm ${
                      currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'
                    }`}>
                      <UserCircleIcon className="h-5 w-5" />
                      <span>{userInfo.username}</span>
                    </div>
                  )}
                  <button
                    onClick={handleLogout}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200 ${
                      currentTheme === 'unicorn'
                        ? 'text-red-300 hover:bg-red-900/20 hover:text-red-200'
                        : currentTheme === 'light'
                        ? 'text-red-600 hover:bg-red-50 hover:text-red-700'
                        : 'text-red-400 hover:bg-red-900/20 hover:text-red-300'
                    }`}
                  >
                    <ArrowRightOnRectangleIcon className="h-5 w-5" />
                    Logout
                  </button>
                </div>
              </div>
              
              {/* Theme Switcher */}
              <div className="px-2 pb-4">
                <div className="border-t border-white/10 pt-4">
                  <div className={`text-xs ${themeClasses.themeLabel} mb-2 px-2`}>Theme</div>
                  <div className="flex gap-1">
                    {availableThemes.map((themeName) => (
                      <button
                        key={themeName}
                        onClick={() => switchTheme(themeName)}
                        className={`
                          px-2 py-1 text-xs rounded transition-all
                          ${currentTheme === themeName
                            ? 'bg-white/20 text-white'
                            : currentTheme === 'unicorn' ? 'text-purple-300/70 hover:bg-white/10 hover:text-white' : currentTheme === 'light' ? 'text-gray-600 hover:bg-gray-100' : 'text-gray-400 hover:bg-gray-700'
                          }
                        `}
                        title={`Switch to ${themeName} theme`}
                      >
                        {themes[themeName]?.icon} {themes[themeName]?.name || themeName}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex flex-col flex-1 overflow-hidden">
          {/* Header with user profile dropdown */}
          <header className={`${currentTheme === 'unicorn' ? 'bg-purple-900/30' : currentTheme === 'light' ? 'bg-white border-b border-gray-200' : 'bg-gray-800 border-b border-gray-700'} backdrop-blur-sm`}>
            <div className="flex justify-between items-center px-4 sm:px-6 md:px-8 py-4">
              <div className="flex-1" />

              {/* User Profile Dropdown */}
              <div className="relative" ref={dropdownRef}>
                <button
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className={`flex items-center gap-2 p-1.5 rounded-full transition-all ${
                    currentTheme === 'unicorn'
                      ? 'hover:bg-white/10'
                      : currentTheme === 'light'
                      ? 'hover:bg-gray-100'
                      : 'hover:bg-gray-700'
                  }`}
                >
                  {/* Avatar with initials */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                    currentTheme === 'unicorn'
                      ? 'bg-gradient-to-br from-purple-500 to-pink-500 text-white'
                      : currentTheme === 'light'
                      ? 'bg-blue-500 text-white'
                      : 'bg-blue-600 text-white'
                  }`}>
                    {getUserInitials()}
                  </div>
                  <ChevronDownIcon className={`w-4 h-4 ${
                    currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-300'
                  }`} />
                </button>

                {/* Dropdown Menu */}
                {dropdownOpen && (
                  <div className={`absolute right-0 mt-2 w-64 rounded-lg shadow-lg py-2 ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-900/95 backdrop-blur-md border border-purple-700/50'
                      : currentTheme === 'light'
                      ? 'bg-white border border-gray-200'
                      : 'bg-gray-800 border border-gray-700'
                  }`}>
                    {/* User Info */}
                    <div className={`px-4 py-2 border-b ${
                      currentTheme === 'unicorn' ? 'border-purple-700/50' : currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'
                    }`}>
                      <div className={`text-sm font-medium ${
                        currentTheme === 'unicorn' ? 'text-white' : currentTheme === 'light' ? 'text-gray-900' : 'text-white'
                      }`}>
                        {userInfo.name || userInfo.username || 'User'}
                      </div>
                      <div className={`text-xs ${
                        currentTheme === 'unicorn' ? 'text-purple-200' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-400'
                      }`}>
                        {userInfo.email || 'user@your-domain.com'}
                      </div>
                    </div>

                    {/* Menu Items */}
                    <div className="py-2">
                      {/* Admin Link - Only show if user is admin */}
                      {isAdmin && (
                        <Link
                          to="/admin"
                          onClick={() => setDropdownOpen(false)}
                          className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                            currentTheme === 'unicorn'
                              ? 'text-purple-200 hover:bg-purple-800/50 hover:text-white'
                              : currentTheme === 'light'
                              ? 'text-gray-700 hover:bg-gray-100'
                              : 'text-gray-300 hover:bg-gray-700'
                          }`}
                        >
                          <CogIcon className="w-4 h-4" />
                          Admin Dashboard
                        </Link>
                      )}

                      {/* Billing Link */}
                      <a
                        href="https://billing.your-domain.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={() => setDropdownOpen(false)}
                        className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-purple-800/50 hover:text-white'
                            : currentTheme === 'light'
                            ? 'text-gray-700 hover:bg-gray-100'
                            : 'text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        <CurrencyDollarIcon className="w-4 h-4" />
                        Billing & Subscription
                      </a>

                      {/* Profile/Settings (future) */}
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          // Future: Navigate to profile settings
                        }}
                        className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors w-full text-left ${
                          currentTheme === 'unicorn'
                            ? 'text-purple-200 hover:bg-purple-800/50 hover:text-white'
                            : currentTheme === 'light'
                            ? 'text-gray-700 hover:bg-gray-100'
                            : 'text-gray-300 hover:bg-gray-700'
                        }`}
                      >
                        <UserCircleIcon className="w-4 h-4" />
                        Profile Settings
                      </button>
                    </div>

                    {/* Logout */}
                    <div className={`border-t ${
                      currentTheme === 'unicorn' ? 'border-purple-700/50' : currentTheme === 'light' ? 'border-gray-200' : 'border-gray-700'
                    }`}>
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          handleLogout();
                        }}
                        className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors w-full text-left ${
                          currentTheme === 'unicorn'
                            ? 'text-red-300 hover:bg-red-900/20 hover:text-red-200'
                            : currentTheme === 'light'
                            ? 'text-red-600 hover:bg-red-50'
                            : 'text-red-500 hover:bg-red-900/20'
                        }`}
                      >
                        <ArrowRightOnRectangleIcon className="w-4 h-4" />
                        Logout
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </header>

          <main className="flex-1 relative overflow-y-auto focus:outline-none">
            <div className="py-6">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
                {children}
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}