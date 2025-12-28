import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Eagerly load critical components (needed on first render)
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingScreen from './components/LoadingScreen';
import { SystemProvider, useSystem } from './contexts/SystemContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { DeploymentProvider } from './contexts/DeploymentContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { ToastProvider } from './components/Toast';

// Create QueryClient instance for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000 // 5 minutes
    }
  }
});

// Import touch optimization utilities
import { initTouchOptimizations } from './utils/touchOptimization';

// Import Extensions Context Provider
import { ExtensionsProvider } from './contexts/ExtensionsContext';

// Eagerly load RootRedirect (needed on first render for root route)
import RootRedirect from './components/RootRedirect';

// Lazy load all pages (loaded on-demand when route is accessed)
const PublicLanding = lazy(() => import('./pages/PublicLanding'));
const Login = lazy(() => import('./pages/Login'));
const DashboardPro = lazy(() => import('./pages/DashboardPro'));

// Apps Marketplace pages (user-facing) - lazy loaded
const AppsLauncher = lazy(() => import('./pages/AppsLauncher'));
const AppMarketplace = lazy(() => import('./pages/AppMarketplace'));
const MyApps = lazy(() => import('./pages/MyApps'));

// Extensions Marketplace pages (admin-only) - lazy loaded
const ExtensionsMarketplace = lazy(() => import('./pages/ExtensionsMarketplace'));
const CheckoutPage = lazy(() => import('./pages/extensions/CheckoutPage'));
const ProductDetailPage = lazy(() => import('./pages/extensions/ProductDetailPage'));
const SuccessPage = lazy(() => import('./pages/extensions/SuccessPage'));
const CancelledPage = lazy(() => import('./pages/extensions/CancelledPage'));
const PurchaseHistory = lazy(() => import('./pages/extensions/PurchaseHistory'));

// Account pages (lazy loaded)
const AccountProfile = lazy(() => import('./pages/account/AccountProfile'));
const AccountNotifications = lazy(() => import('./pages/account/AccountNotifications'));
const AccountSecurity = lazy(() => import('./pages/account/AccountSecurity'));
const AccountAPIKeys = lazy(() => import('./pages/account/AccountAPIKeys'));
const NotificationSettings = lazy(() => import('./pages/NotificationSettings'));

// Subscription pages (lazy loaded)
const SubscriptionPlan = lazy(() => import('./pages/subscription/SubscriptionPlan'));
const SubscriptionUsage = lazy(() => import('./pages/subscription/SubscriptionUsage'));
const SubscriptionBilling = lazy(() => import('./pages/subscription/SubscriptionBilling'));
const SubscriptionPayment = lazy(() => import('./pages/subscription/SubscriptionPayment'));
const PaymentMethods = lazy(() => import('./pages/subscription/PaymentMethods'));
const SubscriptionUpgrade = lazy(() => import('./pages/subscription/SubscriptionUpgrade'));
const SubscriptionDowngrade = lazy(() => import('./pages/subscription/SubscriptionDowngrade'));
const SubscriptionCancel = lazy(() => import('./pages/subscription/SubscriptionCancel'));

// Organization pages (lazy loaded)
const OrganizationsList = lazy(() => import('./pages/organization/OrganizationsList'));
const OrganizationTeam = lazy(() => import('./pages/organization/OrganizationTeam'));
const OrganizationRoles = lazy(() => import('./pages/organization/OrganizationRoles'));
const OrganizationSettings = lazy(() => import('./pages/organization/OrganizationSettings'));
const OrganizationBilling = lazy(() => import('./pages/organization/OrganizationBilling'));
const OrganizationBillingPro = lazy(() => import('./pages/organization/OrganizationBillingPro'));
// TODO: Create these organization credit management pages
// const OrganizationCredits = lazy(() => import('./pages/organization/OrganizationCredits'));
// const CreditAllocation = lazy(() => import('./pages/organization/CreditAllocation'));
// const CreditPurchaseOrg = lazy(() => import('./pages/organization/CreditPurchase'));
// const UsageAttribution = lazy(() => import('./pages/organization/UsageAttribution'));

// Services pages (lazy loaded)
const Brigade = lazy(() => import('./pages/Brigade'));
const LLMHub = lazy(() => import('./pages/LLMHub'));
const LLMManagement = lazy(() => import('./pages/LLMManagement'));
const LiteLLMManagement = lazy(() => import('./pages/LiteLLMManagement'));
const LLMManagementUnified = lazy(() => import('./pages/LLMManagementUnified'));
const OpenRouterSettings = lazy(() => import('./pages/OpenRouterSettings'));
const LLMUsage = lazy(() => import('./pages/LLMUsage'));
const AnalyticsDashboard = lazy(() => import('./pages/llm/AnalyticsDashboard'));

// Platform pages (lazy loaded)
const EmailSettings = lazy(() => import('./components/EmailSettings'));
const PlatformSettings = lazy(() => import('./pages/PlatformSettings'));
const CredentialsManagement = lazy(() => import('./pages/settings/CredentialsManagement'));
const ApiDocumentation = lazy(() => import('./pages/ApiDocumentation'));
const PerformanceMonitor = lazy(() => import('./components/PerformanceMonitor'));

// System pages (lazy loaded)
const AIModelManagement = lazy(() => import('./components/AIModelManagement'));
const ModelListManagement = lazy(() => import('./pages/admin/ModelListManagement'));
const Services = lazy(() => import('./pages/Services'));
const System = lazy(() => import('./pages/System'));
const HardwareManagement = lazy(() => import('./pages/HardwareManagement'));
const AdvancedAnalytics = lazy(() => import('./pages/AdvancedAnalytics'));
const UsageAnalytics = lazy(() => import('./pages/UsageAnalytics'));
const BillingDashboard = lazy(() => import('./pages/BillingDashboard'));
const SubscriptionManagement = lazy(() => import('./pages/admin/SubscriptionManagement'));
const AppManagement = lazy(() => import('./pages/admin/AppManagement'));
const WhiteLabelBuilder = lazy(() => import('./pages/admin/WhiteLabelBuilder'));
const DynamicPricingManagement = lazy(() => import('./pages/admin/DynamicPricingManagement'));
const UserManagement = lazy(() => import('./pages/UserManagement'));
const UserDetail = lazy(() => import('./pages/UserDetail'));
// Consolidated: Using LocalUserManagement for all local user operations
const LocalUserManagement = lazy(() => import('./pages/LocalUserManagement'));
const UsageMetrics = lazy(() => import('./pages/UsageMetrics'));
const Network = lazy(() => import('./pages/NetworkTabbed'));
const StorageBackup = lazy(() => import('./pages/StorageBackup'));
const Security = lazy(() => import('./pages/Security'));
const Authentication = lazy(() => import('./pages/Authentication'));
const Extensions = lazy(() => import('./pages/Extensions'));
const Logs = lazy(() => import('./pages/Logs'));
const LandingCustomization = lazy(() => import('./pages/LandingCustomization'));
const Settings = lazy(() => import('./pages/Settings'));
const SystemSettings = lazy(() => import('./pages/SystemSettings'));
const ForgejoManagement = lazy(() => import('./pages/admin/ForgejoManagement'));
const InviteCodesManagement = lazy(() => import('./pages/admin/InviteCodesManagement'));
const SystemBillingOverview = lazy(() => import('./pages/admin/SystemBillingOverview'));

// Infrastructure pages (lazy loaded)
const CloudflareDNS = lazy(() => import('./components/CloudflareDNS'));
const MigrationWizard = lazy(() => import('./pages/migration/MigrationWizard'));

// Traefik pages (lazy loaded)
const TraefikDashboard = lazy(() => import('./pages/TraefikDashboard'));
const TraefikRoutes = lazy(() => import('./pages/TraefikRoutes'));
const TraefikServices = lazy(() => import('./pages/TraefikServices'));
const TraefikSSL = lazy(() => import('./pages/TraefikSSL'));
const TraefikMetrics = lazy(() => import('./pages/TraefikMetrics'));
const TraefikConfig = lazy(() => import('./pages/TraefikConfig'));

// Credit & Usage pages (lazy loaded)
const CreditDashboard = lazy(() => import('./pages/CreditDashboard'));
const CreditPurchase = lazy(() => import('./pages/CreditPurchase'));
const TierComparison = lazy(() => import('./pages/TierComparison'));
const UpgradeFlow = lazy(() => import('./pages/UpgradeFlow'));
const UserBillingDashboard = lazy(() => import('./pages/billing/UserBillingDashboard'));

// Monitoring & Analytics pages (lazy loaded)
const MonitoringOverview = lazy(() => import('./pages/MonitoringOverview'));
const GrafanaConfig = lazy(() => import('./pages/GrafanaConfig'));
const GrafanaViewer = lazy(() => import('./pages/GrafanaViewer'));
const PrometheusConfig = lazy(() => import('./pages/PrometheusConfig'));
const UmamiConfig = lazy(() => import('./pages/UmamiConfig'));
const Geeses = lazy(() => import('./pages/Geeses'));

// Lazy load non-critical components
const OnboardingTour = lazy(() => import('./components/OnboardingTour'));
const HelpPanel = lazy(() => import('./components/HelpPanel'));

// Protected Route wrapper for admin pages
function ProtectedRoute({ children }) {
  const [checking, setChecking] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  
  useEffect(() => {
    // First check if we have a token
    const token = localStorage.getItem('authToken');
    if (token) {
      setAuthenticated(true);
      setChecking(false);
      return;
    }
    
    // If no token, check for OAuth session
    fetch('/api/v1/auth/session')
      .then(res => {
        if (res.ok) {
          return res.json();
        }
        throw new Error('Not authenticated');
      })
      .then(data => {
        if (data.authenticated && data.token) {
          // Store the token for future use
          localStorage.setItem('authToken', data.token);
          // Use 'userInfo' key to match Layout.jsx
          localStorage.setItem('userInfo', JSON.stringify(data.user));
          console.log('DEBUG: Stored userInfo:', data.user);
          setAuthenticated(true);
        }
      })
      .catch(() => {
        setAuthenticated(false);
      })
      .finally(() => {
        setChecking(false);
      });
  }, []);
  
  if (checking) {
    return <div>Loading...</div>;
  }
  
  if (!authenticated) {
    // Redirect to OAuth login using window.location to force full page load
    // This allows the backend /auth/login endpoint to handle the Keycloak redirect
    if (!window.location.pathname.startsWith('/auth/')) {
      window.location.href = '/auth/login';
    }
    return <div>Loading...</div>;
  }
  
  return children;
}

// Admin content wrapper with SystemProvider
function AdminContent({ children }) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Simple check if backend is available
    fetch('/api/v1/system/status')
      .then(res => {
        if (!res.ok) throw new Error('Backend not available');
        setLoading(false);
      })
      .catch(err => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <LoadingScreen />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-red-900 text-white p-8 rounded-lg">
          <h1 className="text-xl font-bold mb-2">Connection Error</h1>
          <p>{error}</p>
          <p className="mt-4 text-sm">Please check that all services are running.</p>
        </div>
      </div>
    );
  }

  return (
    <SystemProvider>
      <OrganizationProvider>
        <ExtensionsProvider>
          {children}
        </ExtensionsProvider>
      </OrganizationProvider>
    </SystemProvider>
  );
}

function AppRoutes() {
  const location = useLocation();
  const [showHelp, setShowHelp] = useState(false);
  
  // Keyboard shortcut for help (only on admin pages)
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === '?' && !e.target.matches('input, textarea, select') && location.pathname.startsWith('/admin')) {
        setShowHelp(!showHelp);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showHelp, location.pathname]);
  
  const getCurrentPage = () => {
    const path = location.pathname.slice(1);
    return path || 'dashboard';
  };
  
  return (
    <>
      <Suspense fallback={<LoadingScreen />}>
        <Routes>
          {/* Root Route - Smart redirect based on auth status and landing page mode */}
          <Route path="/" element={<RootRedirect />} />

          {/* User Landing Page - Authenticated users (search bar, apps, user dropdown) */}
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <PublicLanding />
            </ProtectedRoute>
          } />

          {/* Admin Login - NO SystemProvider */}
          <Route path="/admin/login" element={<Login />} />

        {/* Admin Dashboard - Protected Routes WITH SystemProvider */}
        <Route path="/admin/*" element={
          <ProtectedRoute>
            <AdminContent>
              <Layout>
                <Routes>
                  {/* Default Landing - Apps Launcher */}
                  <Route path="/" element={<AppsLauncher />} />

                  {/* Dashboard (legacy - still accessible) */}
                  <Route path="dashboard" element={<DashboardPro />} />

                  {/* ============================================================ */}
                  {/* ACCOUNT SECTION - Personal user settings */}
                  {/* ============================================================ */}
                  <Route path="account/profile" element={<AccountProfile />} />
                  <Route path="account/notifications" element={<AccountNotifications />} />
                  <Route path="account/notification-settings" element={<NotificationSettings />} />
                  <Route path="account/security" element={<AccountSecurity />} />
                  <Route path="account/api-keys" element={<AccountAPIKeys />} />

                  {/* ============================================================ */}
                  {/* SUBSCRIPTION SECTION - Personal billing & usage */}
                  {/* ============================================================ */}
                  <Route path="subscription/plan" element={<SubscriptionPlan />} />
                  <Route path="subscription/upgrade" element={<SubscriptionUpgrade />} />
                  <Route path="subscription/downgrade" element={<SubscriptionDowngrade />} />
                  <Route path="subscription/cancel" element={<SubscriptionCancel />} />
                  <Route path="subscription/usage" element={<SubscriptionUsage />} />
                  <Route path="subscription/billing" element={<SubscriptionBilling />} />
                  <Route path="subscription/payment" element={<PaymentMethods />} />

                  {/* ============================================================ */}
                  {/* ORGANIZATION SECTION - Team & org management */}
                  {/* ============================================================ */}
                  <Route path="organization/list" element={<OrganizationsList />} />
                  <Route path="organization/team" element={<OrganizationTeam />} />
                  <Route path="organization/roles" element={<OrganizationRoles />} />
                  <Route path="organization/settings" element={<OrganizationSettings />} />
                  <Route path="organization/billing" element={<OrganizationBilling />} />
                  <Route path="organization/:orgId/billing" element={<OrganizationBillingPro />} />
                  {/* TODO: Uncomment when organization credit pages are created */}
                  {/* <Route path="organization/credits" element={<OrganizationCredits />} /> */}
                  {/* <Route path="organization/credits/allocate" element={<CreditAllocation />} /> */}
                  {/* <Route path="organization/credits/purchase" element={<CreditPurchaseOrg />} /> */}
                  {/* <Route path="organization/credits/usage" element={<UsageAttribution />} /> */}
                  {/* Legacy routes for backwards compatibility */}
                  <Route path="org/team" element={<OrganizationTeam />} />
                  <Route path="org/roles" element={<OrganizationRoles />} />
                  <Route path="org/settings" element={<OrganizationSettings />} />
                  <Route path="org/billing" element={<OrganizationBilling />} />

                  {/* ============================================================ */}
                  {/* SERVICES SECTION - Platform services */}
                  {/* ============================================================ */}
                  <Route path="brigade" element={<Brigade />} />
                  <Route path="llm-hub" element={<LLMHub />} />
                  <Route path="llm-management" element={<LLMManagement />} />
                  <Route path="litellm-providers" element={<LiteLLMManagement />} />
                  <Route path="llm-models" element={<LLMManagementUnified />} />
                  <Route path="openrouter-settings" element={<OpenRouterSettings />} />
                  <Route path="llm/usage" element={<LLMUsage />} />
                  <Route path="analytics" element={<AnalyticsDashboard />} />

                  {/* ============================================================ */}
                  {/* INTEGRATIONS SECTION - External APIs & Services */}
                  {/* ============================================================ */}
                  <Route path="integrations/credentials" element={<PlatformSettings />} />
                  <Route path="integrations/email" element={<EmailSettings />} />

                  {/* Legacy Platform Settings routes (redirects) */}
                  <Route path="platform/email-settings" element={<Navigate to="/admin/integrations/email" replace />} />
                  <Route path="platform/settings" element={<Navigate to="/admin/integrations/credentials" replace />} />
                  <Route path="platform/credentials" element={<CredentialsManagement />} />
                  <Route path="platform/api-docs" element={<ApiDocumentation />} />
                  <Route path="platform/performance" element={<PerformanceMonitor />} />

                  {/* ============================================================ */}
                  {/* SYSTEM SECTION - Platform administration */}
                  {/* ============================================================ */}
                  <Route path="system/models" element={<AIModelManagement />} />
                  <Route path="system/model-lists" element={<ModelListManagement />} />
                  <Route path="system/services" element={<Services />} />
                  <Route path="system/resources" element={<System />} />
                  <Route path="system/hardware" element={<HardwareManagement />} />
                  <Route path="infrastructure/hardware" element={<HardwareManagement />} />
                  <Route path="system/analytics" element={<AdvancedAnalytics />} />
                  <Route path="system/usage-analytics" element={<UsageAnalytics />} />
                  <Route path="system/billing" element={<BillingDashboard />} />
                  <Route path="system/subscription-management" element={<SubscriptionManagement />} />
                  <Route path="system/app-management" element={<AppManagement />} />
                  <Route path="system/pricing-management" element={<DynamicPricingManagement />} />
                  <Route path="platform/white-label" element={<WhiteLabelBuilder />} />
                  <Route path="system/users" element={<UserManagement />} />
                  <Route path="system/users/:userId" element={<UserDetail />} />
                  {/* Local User Management - consolidated to single route */}
                  <Route path="system/local-users" element={<LocalUserManagement />} />
                  <Route path="system/usage-metrics" element={<UsageMetrics />} />
                  <Route path="system/network" element={<Network />} />
                  <Route path="system/storage" element={<StorageBackup />} />
                  <Route path="system/security" element={<Security />} />
                  <Route path="system/authentication" element={<Authentication />} />
                  <Route path="system/extensions" element={<Extensions />} />
                  <Route path="system/landing" element={<LandingCustomization />} />
                  <Route path="system/settings" element={<SystemSettings />} />
                  <Route path="system/forgejo" element={<ForgejoManagement />} />
                  <Route path="system/invite-codes" element={<InviteCodesManagement />} />

                  {/* ============================================================ */}
                  {/* MONITORING & ANALYTICS SECTION - Metrics, Logs, Analytics */}
                  {/* ============================================================ */}
                  <Route path="monitoring/overview" element={<MonitoringOverview />} />
                  <Route path="monitoring/grafana" element={<GrafanaConfig />} />
                  <Route path="monitoring/grafana/dashboards" element={<GrafanaViewer />} />
                  <Route path="monitoring/prometheus" element={<PrometheusConfig />} />
                  <Route path="monitoring/umami" element={<UmamiConfig />} />
                  <Route path="monitoring/logs" element={<Logs />} />
                  <Route path="monitoring/geeses" element={<Geeses />} />

                  {/* ATLAS Multi-Agent System (Geeses) */}
                  <Route path="geeses" element={<Geeses />} />

                  {/* Legacy system/logs route (redirect) */}
                  <Route path="system/logs" element={<Navigate to="/admin/monitoring/logs" replace />} />

                  {/* ============================================================ */}
                  {/* INFRASTRUCTURE SECTION - Network & DNS */}
                  {/* ============================================================ */}
                  <Route path="integrations/cloudflare" element={<CloudflareDNS />} />
                  <Route path="infrastructure/migration" element={<MigrationWizard />} />

                  {/* Legacy cloudflare route (redirect) */}
                  <Route path="infrastructure/cloudflare" element={<Navigate to="/admin/integrations/cloudflare" replace />} />

                  {/* ============================================================ */}
                  {/* TRAEFIK SECTION - Reverse Proxy Management */}
                  {/* ============================================================ */}
                  <Route path="traefik/dashboard" element={<TraefikDashboard />} />
                  <Route path="traefik/routes" element={<TraefikRoutes />} />
                  <Route path="traefik/services" element={<TraefikServices />} />
                  <Route path="traefik/ssl" element={<TraefikSSL />} />
                  <Route path="traefik/metrics" element={<TraefikMetrics />} />

                  {/* System Traefik Config - Comprehensive management */}
                  <Route path="system/traefik" element={<TraefikConfig />} />

                  {/* ============================================================ */}
                  {/* CREDITS & USAGE SECTION - Credit metering system */}
                  {/* ============================================================ */}
                  <Route path="credits" element={<CreditDashboard />} />
                  <Route path="credits/purchase" element={<CreditPurchase />} />
                  <Route path="credits/tiers" element={<TierComparison />} />

                  {/* ============================================================ */}
                  {/* BILLING SECTION - Organization billing dashboards */}
                  {/* ============================================================ */}
                  <Route path="billing/dashboard" element={<UserBillingDashboard />} />
                  <Route path="billing/overview" element={<SystemBillingOverview />} />

                  {/* ============================================================ */}
                  {/* UPGRADE & PLANS SECTION - Subscription management */}
                  {/* ============================================================ */}
                  <Route path="upgrade" element={<UpgradeFlow />} />
                  <Route path="plans" element={<TierComparison />} />

                  {/* ============================================================ */}
                  {/* APPS LAUNCHER & MARKETPLACE - User-Facing Apps */}
                  {/* ============================================================ */}
                  <Route path="apps" element={<AppsLauncher />} />
                  <Route path="apps/marketplace" element={<AppMarketplace />} />
                  <Route path="apps/my" element={<MyApps />} />

                  {/* ============================================================ */}
                  {/* EXTENSIONS MARKETPLACE - Admin Add-ons & Purchases */}
                  {/* ============================================================ */}
                  <Route path="extensions" element={<ExtensionsMarketplace />} />
                  <Route path="extensions/:id" element={<ProductDetailPage />} />
                  <Route path="extensions/checkout" element={<CheckoutPage />} />
                  <Route path="extensions/success" element={<SuccessPage />} />
                  <Route path="extensions/cancelled" element={<CancelledPage />} />
                  <Route path="purchases" element={<PurchaseHistory />} />

                  {/* ============================================================ */}
                  {/* LEGACY ROUTES - Backwards compatibility (DEPRECATED) */}
                  {/* Will be removed after November 13, 2025 */}
                  {/* ============================================================ */}

                  {/* System admin routes - redirect to new system/* namespace */}
                  <Route path="models" element={<Navigate to="/admin/system/models" replace />} />
                  <Route path="services" element={<Navigate to="/admin/system/services" replace />} />
                  <Route path="system" element={<Navigate to="/admin/system/resources" replace />} />
                  <Route path="network" element={<Navigate to="/admin/system/network" replace />} />
                  <Route path="storage" element={<Navigate to="/admin/system/storage" replace />} />
                  <Route path="logs" element={<Navigate to="/admin/system/logs" replace />} />
                  <Route path="security" element={<Navigate to="/admin/system/security" replace />} />
                  <Route path="authentication" element={<Navigate to="/admin/system/authentication" replace />} />
                  <Route path="extensions" element={<Navigate to="/admin/system/extensions" replace />} />
                  <Route path="landing" element={<Navigate to="/admin/system/landing" replace />} />
                  <Route path="settings" element={<Navigate to="/admin/system/settings" replace />} />

                  {/* Personal routes - redirect to new account/* namespace */}
                  <Route path="user-settings" element={<Navigate to="/admin/account/profile" replace />} />

                  {/* Billing routes - redirect to new subscription/* namespace */}
                  <Route path="billing" element={<Navigate to="/admin/subscription/plan" replace />} />
                </Routes>
              </Layout>
            </AdminContent>
          </ProtectedRoute>
        } />
        </Routes>
      </Suspense>

      {/* Help Panel - only show on admin pages */}
      {location.pathname.startsWith('/admin') && (
        <Suspense fallback={null}>
          <HelpPanel
            isOpen={showHelp}
            onClose={() => setShowHelp(false)}
            currentPage={getCurrentPage()}
          />
        </Suspense>
      )}
    </>
  );
}

function App() {
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    // Initialize touch optimizations for mobile devices
    initTouchOptimizations({
      preventZoom: false, // Allow zoom for accessibility
      optimizeTargets: true,
      addHoverStates: true,
      enableRipple: false
    });

    // Check if user needs onboarding (only on admin pages)
    const hasCompletedTour = localStorage.getItem('uc1-tour-completed');
    if (!hasCompletedTour && window.location.pathname.startsWith('/admin')) {
      setTimeout(() => setShowOnboarding(true), 1000);
    }
  }, []);

  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <DeploymentProvider>
          <ThemeProvider>
            <ToastProvider>
              <Router>
                <AppRoutes />
                {showOnboarding && (
                  <Suspense fallback={null}>
                    <OnboardingTour onComplete={() => setShowOnboarding(false)} />
                  </Suspense>
                )}
              </Router>
            </ToastProvider>
          </ThemeProvider>
        </DeploymentProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
