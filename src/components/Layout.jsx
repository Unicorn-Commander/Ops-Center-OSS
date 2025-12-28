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
  ChevronDoubleLeftIcon,
  ChevronDoubleRightIcon,
  LockClosedIcon,
  CpuChipIcon,
  ShoppingBagIcon,
  TicketIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';
import { ColonelLogo, MagicUnicornLogo, CenterDeepLogo } from './Logos';
import NavigationSection from './NavigationSection';
import NavigationItem from './NavigationItem';
import { routes } from '../config/routes';
import NotificationBell from './NotificationBell';
import OrganizationSelector from './OrganizationSelectorSimple';
import MobileNavigation from './MobileNavigation';
import MobileBreadcrumbs from './MobileBreadcrumbs';
import BottomNavBar from './BottomNavBar';

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
  LockClosedIcon,
  CpuChipIcon,
  ShoppingBagIcon,
  TicketIcon
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
      infrastructure: true,
      usersOrgs: true,
      billingUsage: true,
      analytics: true,
      llmHub: true,
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
                title={sidebarCollapsed ? "Ops Center - UC-1 Pro Control" : ""}
              >
                {/* The Colonel Logo */}
                <ColonelLogo className={`drop-shadow-xl ${sidebarCollapsed ? 'w-10 h-10' : 'w-14 h-14'}`} />
                {!sidebarCollapsed && (
                  <div className="text-center">
                    <h1 className={`text-2xl font-bold ${themeClasses.logo} leading-tight`}>
                      Ops Center
                    </h1>
                    <div className={`text-lg ${currentTheme === 'unicorn' ? 'text-purple-200/80' : currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400'} font-medium`}>
                      UC-1 Pro Control
                    </div>
                  </div>
                )}
              </Link>

              {/* System Management - subtitle (hidden when collapsed) */}
              {!sidebarCollapsed && (
                <>
                  <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200/70' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-400'} mb-2 font-medium`}>
                    System Management Console
                  </div>

                  {/* Version */}
                  <div className={`text-xs ${currentTheme === 'unicorn' ? 'text-purple-300/60' : currentTheme === 'light' ? 'text-gray-500' : 'text-gray-500'} font-mono`}>
                    v2.1.0
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
                <NavigationItem collapsed={sidebarCollapsed}
                  name="Dashboard"
                  href="/admin/"
                  icon={iconMap.HomeIcon}
                />

                {/* ============================ */}
                {/* MARKETPLACE - Browse & Purchase Apps */}
                {/* ============================ */}
                <NavigationItem collapsed={sidebarCollapsed}
                  name="Marketplace"
                  href="/admin/apps/marketplace"
                  icon={iconMap.ShoppingBagIcon}
                  badge="New"
                />

                {/* ============================ */}
                {/* ACCOUNT SECTION - ALL USERS */}
                {/* ============================ */}
                {/* Section Header (hidden when collapsed) */}
                {!sidebarCollapsed && (
                  <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                    currentTheme === 'unicorn'
                      ? 'text-purple-300/70'
                      : currentTheme === 'light'
                      ? 'text-gray-500'
                      : 'text-gray-400'
                  }`}>
                    <div className="flex-1 h-px bg-current opacity-20"></div>
                    <span className="text-xs font-bold uppercase tracking-wider">Account</span>
                    <div className="flex-1 h-px bg-current opacity-20"></div>
                  </div>
                )}

                <NavigationSection collapsed={sidebarCollapsed}
                  title="Account"
                  icon={iconMap.UserCircleIcon}
                  defaultOpen={sectionState.account}
                  onToggle={() => toggleSection('account')}
                >
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Profile & Preferences"
                    href="/admin/account/profile"
                    icon={iconMap.UserCircleIcon}
                    indent={true}
                  />
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Security & Sessions"
                    href="/admin/account/security"
                    icon={iconMap.LockClosedIcon}
                    indent={true}
                  />
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="API Keys (BYOK)"
                    href="/admin/account/api-keys"
                    icon={iconMap.KeyIcon}
                    indent={true}
                  />
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Notification Preferences"
                    href="/admin/account/notification-settings"
                    icon={iconMap.EnvelopeIcon}
                    indent={true}
                  />
                </NavigationSection>

                {/* ============================ */}
                {/* MY SUBSCRIPTION SECTION - ALL USERS */}
                {/* ============================ */}
                {/* Section Header (hidden when collapsed) */}
                {!sidebarCollapsed && (
                  <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                    currentTheme === 'unicorn'
                      ? 'text-purple-300/70'
                      : currentTheme === 'light'
                      ? 'text-gray-500'
                      : 'text-gray-400'
                  }`}>
                    <div className="flex-1 h-px bg-current opacity-20"></div>
                    <span className="text-xs font-bold uppercase tracking-wider">My Subscription</span>
                    <div className="flex-1 h-px bg-current opacity-20"></div>
                  </div>
                )}

                <NavigationSection collapsed={sidebarCollapsed}
                  title="My Subscription"
                  icon={iconMap.CreditCardIcon}
                  defaultOpen={sectionState.subscription}
                  onToggle={() => toggleSection('subscription')}
                >
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Current Plan"
                    href="/admin/subscription/plan"
                    icon={iconMap.RectangleStackIcon}
                    indent={true}
                  />
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Usage & Limits"
                    href="/admin/subscription/usage"
                    icon={iconMap.ChartBarIcon}
                    indent={true}
                  />
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Billing History"
                    href="/admin/subscription/billing"
                    icon={iconMap.DocumentDuplicateIcon}
                    indent={true}
                  />
                  <NavigationItem collapsed={sidebarCollapsed}
                    name="Payment Methods"
                    href="/admin/subscription/payment"
                    icon={iconMap.CreditCardIcon}
                    indent={true}
                  />
                </NavigationSection>

                {/* ============================ */}
                {/* MY ORGANIZATION SECTION - ORG ADMINS/OWNERS */}
                {/* ============================ */}
                {(userOrgRole === 'admin' || userOrgRole === 'owner') && (
                  <>
                    {/* Section Header (hidden when collapsed) */}
                    {!sidebarCollapsed && (
                      <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                        currentTheme === 'unicorn'
                          ? 'text-purple-300/70'
                          : currentTheme === 'light'
                          ? 'text-gray-500'
                          : 'text-gray-400'
                      }`}>
                        <div className="flex-1 h-px bg-current opacity-20"></div>
                        <span className="text-xs font-bold uppercase tracking-wider">My Organization</span>
                        <div className="flex-1 h-px bg-current opacity-20"></div>
                      </div>
                    )}

                    <NavigationSection collapsed={sidebarCollapsed}
                      title="My Organization"
                      icon={iconMap.BuildingOfficeIcon}
                      defaultOpen={sectionState.organization}
                      onToggle={() => toggleSection('organization')}
                    >
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Team Members"
                        href="/admin/org/team"
                        icon={iconMap.UsersIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Roles & Permissions"
                        href="/admin/org/roles"
                        icon={iconMap.ShieldCheckIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Organization Settings"
                        href="/admin/org/settings"
                        icon={iconMap.CogIcon}
                        indent={true}
                      />
                      {userOrgRole === 'owner' && (
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Organization Billing"
                          href="/admin/org/billing"
                          icon={iconMap.CurrencyDollarIcon}
                          indent={true}
                        />
                      )}
                    </NavigationSection>
                  </>
                )}

                {/* ============================ */}
                {/* INFRASTRUCTURE SECTION */}
                {/* ============================ */}
                {userRole === 'admin' && (
                  <>
                    {/* Section Header (hidden when collapsed) */}
                    {!sidebarCollapsed && (
                      <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                        currentTheme === 'unicorn'
                          ? 'text-purple-300/70'
                          : currentTheme === 'light'
                          ? 'text-gray-500'
                          : 'text-gray-400'
                      }`}>
                        <div className="flex-1 h-px bg-current opacity-20"></div>
                        <span className="text-xs font-bold uppercase tracking-wider">Infrastructure</span>
                        <div className="flex-1 h-px bg-current opacity-20"></div>
                      </div>
                    )}

                    <NavigationSection collapsed={sidebarCollapsed}
                      title="Infrastructure"
                      icon={iconMap.ComputerDesktopIcon}
                      defaultOpen={sectionState.infrastructure}
                      onToggle={() => toggleSection('infrastructure')}
                    >
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Services"
                        href="/admin/services"
                        icon={iconMap.ServerIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Forgejo (Git)"
                        href="/admin/system/forgejo"
                        icon={iconMap.CodeBracketIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Hardware Management"
                        href="/admin/infrastructure/hardware"
                        icon={iconMap.WrenchIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Local Users"
                        href="/admin/system/local-users"
                        icon={iconMap.UsersIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Monitoring"
                        href="/admin/system"
                        icon={iconMap.ChartBarIcon}
                        indent={true}
                      />
                      <NavigationSection collapsed={sidebarCollapsed}
                        title="LLM Hub"
                        icon={iconMap.CpuChipIcon}
                        defaultOpen={sectionState.llmHub}
                        onToggle={() => toggleSection('llmHub')}
                      >
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Hub Overview"
                          href="/admin/llm-hub"
                          icon={iconMap.HomeIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="LLM Management"
                          href="/admin/llm-management"
                          icon={iconMap.CogIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="LLM Providers"
                          href="/admin/litellm-providers"
                          icon={iconMap.ServerIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="LLM Usage"
                          href="/admin/llm/usage"
                          icon={iconMap.ChartBarIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Model Lists"
                          href="/admin/system/model-lists"
                          icon={iconMap.RectangleStackIcon}
                          indent={true}
                        />
                      </NavigationSection>
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Cloudflare DNS"
                        href="/admin/infrastructure/cloudflare"
                        icon={iconMap.GlobeAltIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Traefik"
                        href="/admin/traefik/dashboard"
                        icon={iconMap.ServerIcon}
                        indent={true}
                      >
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Dashboard"
                          href="/admin/traefik/dashboard"
                          icon={iconMap.ChartBarIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Routes"
                          href="/admin/traefik/routes"
                          icon={iconMap.GlobeAltIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Services"
                          href="/admin/traefik/services"
                          icon={iconMap.ServerIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="SSL Certificates"
                          href="/admin/traefik/ssl"
                          icon={iconMap.LockClosedIcon}
                          indent={true}
                        />
                        <NavigationItem collapsed={sidebarCollapsed}
                          name="Metrics"
                          href="/admin/traefik/metrics"
                          icon={iconMap.ChartBarIcon}
                          indent={true}
                        />
                      </NavigationItem>
                    </NavigationSection>
                  </>
                )}

                {/* ============================ */}
                {/* USERS & ORGANIZATIONS SECTION */}
                {/* ============================ */}
                {userRole === 'admin' && (
                  <>
                    {/* Section Header */}
                    {!sidebarCollapsed && (
                    <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                      currentTheme === 'unicorn'
                        ? 'text-purple-300/70'
                        : currentTheme === 'light'
                        ? 'text-gray-500'
                        : 'text-gray-400'
                    }`}>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                      <span className="text-xs font-bold uppercase tracking-wider">Users & Organizations</span>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                    </div>
                    )}

                    <NavigationSection collapsed={sidebarCollapsed}
                      title="Users & Organizations"
                      icon={iconMap.UsersIcon}
                      defaultOpen={sectionState.usersOrgs}
                      onToggle={() => toggleSection('usersOrgs')}
                    >
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="User Management"
                        href="/admin/system/users"
                        icon={iconMap.UsersIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Organizations"
                        href="/admin/organization/list"
                        icon={iconMap.BuildingOfficeIcon}
                        indent={true}
                      />
                    </NavigationSection>
                  </>
                )}

                {/* ============================ */}
                {/* BILLING & USAGE SECTION */}
                {/* ============================ */}
                {userRole === 'admin' && (
                  <>
                    {/* Section Header */}
                    {!sidebarCollapsed && (
                    <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                      currentTheme === 'unicorn'
                        ? 'text-purple-300/70'
                        : currentTheme === 'light'
                        ? 'text-gray-500'
                        : 'text-gray-400'
                    }`}>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                      <span className="text-xs font-bold uppercase tracking-wider">Billing & Usage</span>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                    </div>
                    )}

                    <NavigationSection collapsed={sidebarCollapsed}
                      title="Billing & Usage"
                      icon={iconMap.CurrencyDollarIcon}
                      defaultOpen={sectionState.billingUsage}
                      onToggle={() => toggleSection('billingUsage')}
                    >
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Subscription Management"
                        href="/admin/system/subscription-management"
                        icon={iconMap.CreditCardIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="App Management"
                        href="/admin/system/app-management"
                        icon={iconMap.CubeIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Pricing Management"
                        href="/admin/system/pricing-management"
                        icon={iconMap.CurrencyDollarIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Billing Dashboard"
                        href="/admin/system/billing"
                        icon={iconMap.CurrencyDollarIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="User Billing"
                        href="/admin/billing/dashboard"
                        icon={iconMap.UserCircleIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="System Billing Overview"
                        href="/admin/billing/overview"
                        icon={iconMap.ChartBarIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Invite Codes"
                        href="/admin/system/invite-codes"
                        icon={iconMap.TicketIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Buy Credits"
                        href="/admin/credits/purchase"
                        icon={iconMap.ShoppingBagIcon}
                        indent={true}
                      />
                    </NavigationSection>
                  </>
                )}

                {/* ============================ */}
                {/* ANALYTICS SECTION */}
                {/* ============================ */}
                {userRole === 'admin' && (
                  <>
                    {/* Section Header */}
                    {!sidebarCollapsed && (
                    <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                      currentTheme === 'unicorn'
                        ? 'text-purple-300/70'
                        : currentTheme === 'light'
                        ? 'text-gray-500'
                        : 'text-gray-400'
                    }`}>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                      <span className="text-xs font-bold uppercase tracking-wider">Analytics & Insights</span>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                    </div>
                    )}

                    <NavigationSection collapsed={sidebarCollapsed}
                      title="Analytics & Insights"
                      icon={iconMap.ChartBarIcon}
                      defaultOpen={sectionState.analytics}
                      onToggle={() => toggleSection('analytics')}
                    >
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Analytics Dashboard"
                        href="/admin/analytics"
                        icon={iconMap.ChartBarIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="LLM Analytics"
                        href="/admin/llm/usage"
                        icon={iconMap.CpuChipIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="User Analytics"
                        href="/admin/system/analytics"
                        icon={iconMap.UsersIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Billing Analytics"
                        href="/admin/system/billing"
                        icon={iconMap.CurrencyDollarIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Usage Metrics"
                        href="/admin/system/usage-metrics"
                        icon={iconMap.ChartPieIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Subscriptions"
                        href="/admin/billing"
                        icon={iconMap.RectangleStackIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Invoices"
                        href="/admin/system/billing#invoices"
                        icon={iconMap.DocumentDuplicateIcon}
                        indent={true}
                      />
                    </NavigationSection>
                  </>
                )}

                {/* ============================ */}
                {/* PLATFORM SECTION */}
                {/* ============================ */}
                {userRole === 'admin' && (
                  <>
                    {/* Section Header */}
                    {!sidebarCollapsed && (
                    <div className={`mt-4 mb-2 px-3 flex items-center gap-2 ${
                      currentTheme === 'unicorn'
                        ? 'text-purple-300/70'
                        : currentTheme === 'light'
                        ? 'text-gray-500'
                        : 'text-gray-400'
                    }`}>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                      <span className="text-xs font-bold uppercase tracking-wider">Platform</span>
                      <div className="flex-1 h-px bg-current opacity-20"></div>
                    </div>
                    )}

                    <NavigationSection collapsed={sidebarCollapsed}
                      title="Platform"
                      icon={iconMap.SparklesIcon}
                      defaultOpen={sectionState.platform}
                      onToggle={() => toggleSection('platform')}
                    >
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Unicorn Brigade"
                        href="/admin/brigade"
                        icon={iconMap.SparklesIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Center-Deep Search"
                        href="https://search.your-domain.com"
                        icon={iconMap.MagnifyingGlassIcon}
                        indent={true}
                        external={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Email Settings"
                        href="/admin/platform/email-settings"
                        icon={iconMap.EnvelopeIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="Platform Settings"
                        href="/admin/platform/settings"
                        icon={iconMap.CogIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="White-Label Config"
                        href="/admin/platform/white-label"
                        icon={iconMap.PaintBrushIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="API Documentation"
                        href="/admin/platform/api-docs"
                        icon={iconMap.CodeBracketIcon}
                        indent={true}
                      />
                      <NavigationItem collapsed={sidebarCollapsed}
                        name="System Settings"
                        href="/admin/system/settings"
                        icon={iconMap.CogIcon}
                        indent={true}
                      />
                    </NavigationSection>
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
                  {/* Page title can be dynamically set here */}
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
    </div>
  );
}