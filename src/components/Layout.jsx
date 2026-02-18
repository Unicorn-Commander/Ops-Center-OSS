/**
 * Layout Component - Ops Center Main Layout with Hierarchical Navigation
 *
 * UPDATED: October 13, 2025
 * CHANGES: Integrated hierarchical navigation structure with collapsible sections
 *
 * Navigation Structure:
 * - Personal Section: Dashboard, My Account, My Subscription (always visible)
 * - Organization Section: Team management, settings (org admins/owners only)
 * - System Section: Infrastructure administration (platform admins only)
 *
 * Components Used:
 * - NavigationSection: Collapsible navigation sections with expand/collapse
 * - NavigationItem: Individual navigation items with active state and theming
 *
 * Role-Based Access:
 * - role: admin → Full system administration access
 * - org_role: admin/owner → Organization management access
 * - All authenticated users → Personal sections
 */

import React, { useState } from 'react';
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
  CreditCardIcon,
  BuildingOfficeIcon,
  UsersIcon,
  ComputerDesktopIcon,
  WrenchIcon,
  CurrencyDollarIcon,
  ChartPieIcon,
  DocumentDuplicateIcon,
  RectangleStackIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  EnvelopeIcon,
  GlobeAltIcon,
  CodeBracketIcon,
  LinkIcon,
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  LockClosedIcon,
  CpuChipIcon,
  ShoppingBagIcon,
  TicketIcon,
  ChartBarSquareIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import { ColonelLogo, MagicUnicornLogo, CenterDeepLogo } from './Logos';
import NavigationSection from './NavigationSection';
import NavigationItem from './NavigationItem';
import { getNavigationStructure, getRouteByPath, hasRouteAccess } from '../config/routes';
import NotificationBell from './NotificationBell';
import OrganizationSelector from './OrganizationSelectorSimple';
import MobileNavigation from './MobileNavigation';
import MobileBreadcrumbs from './MobileBreadcrumbs';
import BottomNavBar from './BottomNavBar';
import { lazy, Suspense } from 'react';
const ColonelChatBubble = lazy(() => import('./colonel/ColonelChatBubble'));

// Icon mapping for dynamic icon resolution from route configuration
const iconMap = {
  HomeIcon,
  UserCircleIcon,
  CreditCardIcon,
  CubeIcon,
  ServerIcon,
  ChartBarIcon,
  WifiIcon,
  ArchiveBoxIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  KeyIcon,
  PuzzlePieceIcon,
  PaintBrushIcon,
  CogIcon,
  BuildingOfficeIcon,
  UsersIcon,
  ComputerDesktopIcon,
  WrenchIcon,
  CurrencyDollarIcon,
  ChartPieIcon,
  DocumentDuplicateIcon,
  RectangleStackIcon,
  MagnifyingGlassIcon,
  SparklesIcon,
  EnvelopeIcon,
  GlobeAltIcon,
  CodeBracketIcon,
  LinkIcon,
  LockClosedIcon,
  CpuChipIcon,
  ShoppingBagIcon,
  TicketIcon,
  ChartBarSquareIcon
};

export default function Layout({ children }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { theme, currentTheme, switchTheme, availableThemes, isDarkMode, toggleDarkMode } = useTheme();

  // Theme configurations for display names
  const themes = {
    dark: { name: 'Dark', icon: '🌙' },
    light: { name: 'Light', icon: '☀️' },
    unicorn: { name: 'Unicorn', icon: '🦄' }
  };

  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
  const userRole = userInfo.role || 'viewer';
  const userOrgRole = userInfo.org_role || null;

  // Debug logging
  console.log('DEBUG Layout: userInfo from localStorage:', userInfo);
  console.log('DEBUG Layout: userRole:', userRole);
  console.log('DEBUG Layout: userOrgRole:', userOrgRole);

  // Collapsible section state management - Load from localStorage
  const loadSectionState = () => {
    const saved = localStorage.getItem('navSectionState');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Failed to parse saved section state:', e);
      }
    }
    // Default state
    return {
      account: true,
      subscription: true,
      organization: true,
      peopleAccess: true,
      billingPlans: true,
      aiModels: true,
      infrastructure: true,
      monitoring: true,
      integrations: true,
      platform: true
    };
  };

  const [sectionState, setSectionState] = useState(loadSectionState);

  // Sidebar collapse state - Load from localStorage
  const loadSidebarCollapsed = () => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  };

  const [sidebarCollapsed, setSidebarCollapsed] = useState(loadSidebarCollapsed);

  // Toggle sidebar collapsed state
  const toggleSidebar = () => {
    setSidebarCollapsed(prev => {
      const newState = !prev;
      localStorage.setItem('sidebarCollapsed', newState.toString());
      return newState;
    });
  };

  // Save section state to localStorage whenever it changes
  const toggleSection = (sectionName) => {
    setSectionState(prev => {
      const newState = {
        ...prev,
        [sectionName]: !prev[sectionName]
      };
      localStorage.setItem('navSectionState', JSON.stringify(newState));
      return newState;
    });
  };

  const handleLogout = async () => {
    try {
      // Call backend logout endpoint
      const response = await fetch('/api/v1/auth/logout', {
        method: 'POST',
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();

        // Clear local storage
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        localStorage.removeItem('user');
        localStorage.removeItem('token');

        // Redirect to Keycloak logout (clears SSO session, then shows our confirmation page)
        if (data.logout_url) {
          window.location.href = data.logout_url;
          return;
        }
      }
    } catch (error) {
      console.error('Logout API call failed:', error);
    }

    // Fallback: Clear local storage and redirect to home
    localStorage.removeItem('authToken');
    localStorage.removeItem('userInfo');
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    window.location.href = '/';
  };

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

  const navStructure = getNavigationStructure();

  const resolveIcon = (iconName) => {
    if (!iconName) return null;
    return iconMap[iconName] || null;
  };

  // Section header renderer with color differentiation for user vs admin sections
  const renderSectionHeader = (label, isAdminSection = false) => {
    if (sidebarCollapsed) return null;

    // User sections: Blue/Teal tones - accessible to all users
    // Admin sections: Amber/Gold tones - system admin only
    const getUserSectionColor = () => {
      if (currentTheme === 'unicorn') return 'text-cyan-300/80';
      if (currentTheme === 'light') return 'text-blue-600';
      return 'text-cyan-400';
    };

    const getAdminSectionColor = () => {
      if (currentTheme === 'unicorn') return 'text-amber-300/80';
      if (currentTheme === 'light') return 'text-amber-600';
      return 'text-amber-400';
    };

    const sectionColor = isAdminSection ? getAdminSectionColor() : getUserSectionColor();

    return (
      <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${sectionColor}`}>
        <div className="flex-1 h-px bg-current opacity-20"></div>
        <span className="text-xs font-bold uppercase tracking-wider flex items-center gap-1">
          {isAdminSection && (
            <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
          )}
          {label}
        </span>
        <div className="flex-1 h-px bg-current opacity-20"></div>
      </div>
    );
  };

  const renderNavItem = (route, indent = false) => {
    if (!route || route.nav === false) return null;
    if (!hasRouteAccess(route, userRole, userOrgRole)) return null;

    const Icon = resolveIcon(route.icon);
    return (
      <NavigationItem
        key={route.path}
        collapsed={sidebarCollapsed}
        name={route.name}
        href={route.path}
        icon={Icon}
        indent={indent}
        external={route.external}
      />
    );
  };

  const renderNavSection = (sectionKey, sectionConfig) => {
    if (!sectionConfig || !sectionConfig.children) return null;
    const Icon = resolveIcon(sectionConfig.icon);
    const children = Object.values(sectionConfig.children)
      .map(child => renderNavItem(child, true))
      .filter(Boolean);

    if (children.length === 0) return null;

    return (
      <NavigationSection
        collapsed={sidebarCollapsed}
        title={sectionConfig.section}
        icon={Icon}
        defaultOpen={sectionState[sectionKey]}
        onToggle={() => toggleSection(sectionKey)}
      >
        {children}
      </NavigationSection>
    );
  };

  const currentRoute = getRouteByPath(location.pathname);
  const currentTitle = currentRoute?.name || 'Ops-Center';

  return (
    <div className={themeClasses.background}>
      {/* Mobile Navigation - Hamburger menu and drawer */}
      <MobileNavigation user={userInfo} currentPath={location.pathname} />

      <div className="flex h-screen">
        {/* Sidebar - Desktop Only */}
        <div className={`hidden md:flex md:flex-col transition-all duration-300 ${
          sidebarCollapsed ? 'md:w-20' : 'md:w-64'
        }`}>
          <div className={`flex flex-col flex-grow pt-5 pb-4 overflow-y-auto overflow-x-hidden ${themeClasses.sidebar}`}>
            {/* Brand Header */}
            <div className={`flex flex-col items-center flex-shrink-0 mb-8 transition-all duration-300 ${
              sidebarCollapsed ? 'px-2' : 'px-4'
            }`}>
              {/* Main Logo Area - Clickable to navigate to landing page */}
              <Link
                to="/"
                className={`flex items-center ${sidebarCollapsed ? 'flex-col gap-1' : 'gap-3'} mb-3 cursor-pointer transition-all duration-200 rounded-lg p-2 ${
                  currentTheme === 'unicorn'
                    ? 'hover:bg-white/10'
                    : currentTheme === 'light'
                    ? 'hover:bg-gray-100'
                    : 'hover:bg-slate-700/50'
                }`}
                title={sidebarCollapsed ? "Ops-Center - Operations Console" : ""}
              >
                {/* Magic Unicorn Logo */}
                <MagicUnicornLogo className={`drop-shadow-xl ${sidebarCollapsed ? 'w-10 h-10' : 'w-14 h-14'}`} />
                {!sidebarCollapsed && (
                  <div className="text-center">
                    <h1 className={`text-2xl font-bold ${themeClasses.logo} leading-tight`}>
                      Ops-Center
                    </h1>
                    <div className={`text-lg ${currentTheme === 'unicorn' ? 'text-purple-200/80' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'} font-medium`}>
                      Operations Console
                    </div>
                  </div>
                )}
              </Link>

              {/* Powered By - subtitle (hidden when collapsed) */}
              {!sidebarCollapsed && (
                <>
                  <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200/70' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-2 font-medium`}>
                    Powered by <a href="https://unicorncommander.com" target="_blank" rel="noopener noreferrer" className="underline hover:text-purple-300">Unicorn Commander</a>
                  </div>

                  {/* Version */}
                  <div className={`text-xs ${currentTheme === 'unicorn' ? 'text-purple-300/60' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-500'} font-mono`}>
                    v2.4.0
                  </div>
                </>
              )}
            </div>

            {/* Collapse/Expand Button - Positioned after brand header */}
            <div className="px-4 mb-4">
              <button
                onClick={toggleSidebar}
                className={`
                  w-full flex items-center ${sidebarCollapsed ? 'justify-center' : 'justify-between'} px-3 py-2 rounded-lg transition-all duration-200
                  ${currentTheme === 'unicorn'
                    ? 'bg-purple-500/20 text-purple-200 hover:bg-purple-500/30'
                    : currentTheme === 'light'
                    ? 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                    : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                  }
                `}
                aria-label={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
                aria-expanded={!sidebarCollapsed}
                title={sidebarCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
              >
                {!sidebarCollapsed && (
                  <span className="text-xs font-semibold uppercase tracking-wider">
                    Collapse
                  </span>
                )}
                {sidebarCollapsed ? (
                  <ChevronDoubleRightIcon className="h-5 w-5" />
                ) : (
                  <ChevronDoubleLeftIcon className="h-5 w-5" />
                )}
              </button>
            </div>

            <div className="mt-4 flex flex-col flex-1">
              <nav className="flex-1 px-2 space-y-1">
                {/* ============================ */}
                {/* DASHBOARD - Top Level */}
                {/* ============================ */}
                {renderNavItem(navStructure.personal.dashboard)}
                {renderNavItem(navStructure.personal.myDashboard)}
                {renderNavItem(navStructure.personal.marketplace)}

                {renderSectionHeader('Account')}
                {renderNavSection('account', navStructure.personal.account)}

                {renderSectionHeader('Subscription & Credits')}
                {renderNavSection('subscription', navStructure.personal.subscription)}

                {(userOrgRole === 'admin' || userOrgRole === 'owner') && (
                  <>
                    {renderSectionHeader('My Organization')}
                    {renderNavSection('organization', navStructure.organization)}
                  </>
                )}

                {userRole === 'admin' && (
                  <>
                    {renderSectionHeader('People & Access', true)}
                    {renderNavSection('peopleAccess', navStructure.system.children.peopleAccess)}

                    {renderSectionHeader('Billing & Plans', true)}
                    {renderNavSection('billingPlans', navStructure.system.children.billingPlans)}

                    {renderSectionHeader('AI & Models', true)}
                    {renderNavSection('aiModels', navStructure.system.children.aiModels)}

                    {renderSectionHeader('Infrastructure', true)}
                    {renderNavSection('infrastructure', navStructure.system.children.infrastructure)}

                    {renderSectionHeader('Monitoring', true)}
                    {renderNavSection('monitoring', navStructure.system.children.monitoring)}

                    {renderSectionHeader('Integrations', true)}
                    {renderNavSection('integrations', navStructure.system.children.integrations)}

                    {renderSectionHeader('Platform', true)}
                    {renderNavSection('platform', navStructure.system.children.platform)}
                  </>
                )}
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
          {/* Mobile Breadcrumbs - Shows below header on mobile */}
          <MobileBreadcrumbs path={location.pathname} />

          {/* Top Header Bar */}
          <header className={`${
            currentTheme === 'unicorn'
              ? 'bg-gradient-to-r from-purple-900/50 to-pink-900/50 backdrop-blur-md border-b border-purple-500/20'
              : currentTheme === 'light'
              ? 'bg-white border-b border-gray-200'
              : 'bg-slate-800 border-b border-slate-700'
          } shadow-sm`}>
            <div className="flex items-center justify-between px-4 md:px-4 py-3 pl-20 md:pl-4">
              {/* pl-20 on mobile to account for hamburger menu button */}
              {/* Left: Page Title or Breadcrumbs */}
              <div className="flex-1">
                <h2 className={`text-lg font-semibold ${
                  currentTheme === 'unicorn'
                    ? 'text-white'
                    : currentTheme === 'light'
                    ? 'text-gray-900'
                    : 'text-white'
                }`}>
                  {currentTitle}
                </h2>
              </div>

              {/* Right: Upgrade Button, Organization Selector, Notification Bell and User Info */}
              <div className="flex items-center gap-4">
                {/* Upgrade Button (if not Enterprise tier) */}
                {userInfo.subscription_tier && userInfo.subscription_tier !== 'enterprise' && (
                  <Link
                    to="/admin/upgrade"
                    className={`
                      px-4 py-2 rounded-lg font-semibold text-sm
                      bg-gradient-to-r from-purple-600 to-pink-600
                      text-white
                      hover:from-purple-700 hover:to-pink-700
                      transition-all duration-200
                      shadow-lg hover:shadow-xl
                      flex items-center gap-2
                      ${currentTheme === 'unicorn' ? 'ring-2 ring-purple-400/50' : ''}
                    `}
                  >
                    <SparklesIcon className="h-5 w-5" />
                    <span>Upgrade</span>
                  </Link>
                )}

                {/* Organization Selector */}
                <OrganizationSelector />

                {/* Notification Bell (Admin only) */}
                {userInfo.role === 'admin' && (
                  <div className={`${
                    currentTheme === 'unicorn'
                      ? 'text-purple-200'
                      : currentTheme === 'light'
                      ? 'text-gray-600'
                      : 'text-gray-300'
                  }`}>
                    <NotificationBell />
                  </div>
                )}

                {/* User Avatar/Name */}
                <div className="flex items-center gap-2">
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full ${
                    currentTheme === 'unicorn'
                      ? 'bg-purple-500 text-white'
                      : currentTheme === 'light'
                      ? 'bg-gray-200 text-gray-700'
                      : 'bg-slate-600 text-white'
                  }`}>
                    {userInfo.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div className="flex flex-col">
                    <span className={`text-sm font-medium ${
                      currentTheme === 'unicorn'
                        ? 'text-white'
                        : currentTheme === 'light'
                        ? 'text-gray-700'
                        : 'text-gray-200'
                    }`}>
                      {userInfo.username || 'User'}
                    </span>
                    {userInfo.subscription_tier && (
                      <span className={`text-xs ${
                        currentTheme === 'unicorn'
                          ? 'text-purple-300'
                          : currentTheme === 'light'
                          ? 'text-gray-500'
                          : 'text-gray-400'
                      }`}>
                        {userInfo.subscription_tier === 'professional' && '💼 Pro'}
                        {userInfo.subscription_tier === 'enterprise' && '🏢 Enterprise'}
                        {userInfo.subscription_tier === 'starter' && '🚀 Starter'}
                        {userInfo.subscription_tier === 'trial' && '🔬 Trial'}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </header>

          <main className="flex-1 relative overflow-y-auto focus:outline-none">
            <div className="py-6 pb-20 md:pb-6">
              {/* pb-20 on mobile to account for bottom nav bar */}
              <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
                {children}
              </div>
            </div>
          </main>
        </div>
      </div>

      {/* Bottom Navigation Bar - Mobile Only */}
      <BottomNavBar currentPath={location.pathname} userRole={userInfo.role} />

      {/* Colonel Chat Bubble - Admin Only, hidden on Colonel page */}
      {userRole === 'admin' && !location.pathname.startsWith('/admin/ai/colonel') && (
        <Suspense fallback={null}>
          <ColonelChatBubble />
        </Suspense>
      )}
    </div>
  );
}
