import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate, useParams } from 'react-router-dom';
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
const PublicStatusPage = lazy(() => import('./pages/PublicStatusPage'));
const Login = lazy(() => import('./pages/Login'));

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
const ModelListManagement = lazy(() => import('./pages/admin/ModelListManagement'));
// AIModelManagement is an alias for ModelListManagement (legacy)
const AIModelManagement = ModelListManagement;
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
const Logs = lazy(() => import('./pages/Logs'));
const LandingCustomization = lazy(() => import('./pages/LandingCustomization'));
const SystemSettings = lazy(() => import('./pages/SystemSettings'));
const ForgejoManagement = lazy(() => import('./pages/admin/ForgejoManagement'));
const InviteCodesManagement = lazy(() => import('./pages/admin/InviteCodesManagement'));
const SystemBillingOverview = lazy(() => import('./pages/admin/SystemBillingOverview'));
const LocalModelsManagement = lazy(() => import('./pages/admin/LocalModelsManagement'));
const RAGServicesManagement = lazy(() => import('./pages/admin/RAGServicesManagement'));
const GPUServicesManagement = lazy(() => import('./pages/admin/GPUServicesManagement'));
const GraniteApiKeysManagement = lazy(() => import('./pages/admin/GraniteApiKeysManagement'));
const AdminInfraDashboard = lazy(() => import('./pages/admin/Dashboard'));
const AdminRedirect = lazy(() => import('./components/AdminRedirect'));
const AlertsManagement = lazy(() => import('./pages/admin/AlertsManagement'));
const WebhooksManagement = lazy(() => import('./pages/admin/WebhooksManagement'));
const SystemAuditLog = lazy(() => import('./pages/admin/SystemAuditLog'));

// Colonel AI Command System (Phase 1)
const ColonelChat = lazy(() => import('./pages/admin/ColonelChat'));
const ColonelOnboarding = lazy(() => import('./pages/admin/ColonelOnboarding'));
const ColonelStatus = lazy(() => import('./pages/admin/ColonelStatus'));

// Infrastructure pages (lazy loaded)
const CloudflareDNS = lazy(() => import('./pages/network/CloudflareDNS'));
const MigrationWizard = lazy(() => import('./pages/migration/MigrationWizard'));

// Traefik pages (lazy loaded)
const TraefikDashboard = lazy(() => import('./pages/TraefikDashboard'));
const TraefikRoutes = lazy(() => import('./pages/TraefikRoutes'));
const TraefikServices = lazy(() => import('./pages/TraefikServices'));
const TraefikSSL = lazy(() => import('./pages/TraefikSSL'));
const TraefikMetrics = lazy(() => import('./pages/TraefikMetrics'));
const TraefikConfig = lazy(() => import('./pages/TraefikConfig'));

// User-facing dashboard (lazy loaded)
const UserDashboard = lazy(() => import('./pages/UserDashboard'));

// Credit & Usage pages (lazy loaded)
// CreditDashboard was removed — billing/credits now uses CreditPurchase
const CreditDashboard = lazy(() => import('./pages/CreditPurchase'));
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
const WebsiteMonitor = lazy(() => import('./pages/admin/WebsiteMonitor'));
const ExternalMonitoringTools = lazy(() => import('./pages/admin/ExternalMonitoringTools'));

// Revenue Dashboard (consolidates BillingDashboard + UserBillingDashboard + SystemBillingOverview)
const RevenueDashboard = lazy(() => import('./pages/admin/RevenueDashboard'));

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

function ParamRedirect({ to }) {
  const params = useParams();
  const resolved = to.replace(/:([A-Za-z0-9_]+)/g, (_, key) => params[key] || '');
  return <Navigate to={resolved} replace />;
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

          {/* Public Status Page - No auth required */}
          <Route path="/status" element={<PublicStatusPage />} />

          {/* Admin Login - NO SystemProvider */}
          <Route path="/admin/login" element={<Login />} />

          {/* Colonel Pop-out - Protected but NO Layout wrapper */}
          <Route path="/admin/ai/colonel-popout" element={
            <ProtectedRoute>
              <AdminContent>
                <ColonelChat popout={true} />
              </AdminContent>
            </ProtectedRoute>
          } />

        {/* Admin Dashboard - Protected Routes WITH SystemProvider */}
        <Route path="/admin/*" element={
          <ProtectedRoute>
            <AdminContent>
              <Layout>
                <Routes>
                  {/* Default Landing - Smart redirect based on role */}
                  <Route path="/" element={<AdminRedirect />} />

                  {/* Dashboard alias for backwards compatibility */}
                  <Route path="dashboard" element={<AdminInfraDashboard />} />

                  {/* User Dashboard - Personal credits, usage, subscription overview */}
                  <Route path="my-dashboard" element={<UserDashboard />} />

                  {/* Apps Launcher (moved from default) */}
                  <Route path="apps" element={<AppsLauncher />} />

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
                  <Route path="organization/list" element={<Navigate to="/admin/people/organizations" replace />} />
                  <Route path="organization/team" element={<OrganizationTeam />} />
                  <Route path="organization/roles" element={<OrganizationRoles />} />
                  <Route path="organization/settings" element={<OrganizationSettings />} />
                  <Route path="organization/billing" element={<OrganizationBilling />} />
                  <Route path="organization/:orgId/billing" element={<ParamRedirect to="/admin/people/organizations/:orgId/billing" />} />
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
                  <Route path="llm-hub" element={<Navigate to="/admin/ai" replace />} />
                  <Route path="llm-management" element={<Navigate to="/admin/ai/management" replace />} />
                  <Route path="litellm-providers" element={<Navigate to="/admin/ai/providers" replace />} />
                  <Route path="llm-models" element={<Navigate to="/admin/ai/models" replace />} />
                  <Route path="openrouter-settings" element={<Navigate to="/admin/ai/openrouter" replace />} />
                  <Route path="llm/usage" element={<Navigate to="/admin/ai/usage" replace />} />
                  <Route path="analytics" element={<Navigate to="/admin/monitoring/analytics" replace />} />

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
                  {/* ADMIN IA - New Paths (Phase 1) */}
                  {/* ============================================================ */}
                  {/* People & Access */}
                  <Route path="people/users" element={<UserManagement />} />
                  <Route path="people/users/:userId" element={<UserDetail />} />
                  <Route path="people/organizations" element={<OrganizationsList />} />
                  <Route path="people/organizations/:orgId/billing" element={<OrganizationBillingPro />} />
                  <Route path="people/invite-codes" element={<InviteCodesManagement />} />
                  <Route path="people/authentication" element={<Authentication />} />

                  {/* Billing & Plans */}
                  <Route path="billing/tiers" element={<SubscriptionManagement />} />
                  <Route path="billing/tiers/compare" element={<TierComparison />} />
                  <Route path="billing/apps" element={<AppManagement />} />
                  <Route path="billing/pricing" element={<DynamicPricingManagement />} />
                  <Route path="billing/revenue" element={<RevenueDashboard />} />
                  <Route path="billing/system" element={<BillingDashboard />} />
                  <Route path="billing/user" element={<UserBillingDashboard />} />
                  <Route path="billing/overview" element={<SystemBillingOverview />} />
                  <Route path="billing/credits" element={<CreditDashboard />} />
                  <Route path="billing/credits/purchase" element={<CreditPurchase />} />

                  {/* AI & Models */}
                  <Route path="ai" element={<LLMHub />} />
                  <Route path="ai/management" element={<LLMManagement />} />
                  <Route path="ai/providers" element={<LiteLLMManagement />} />
                  <Route path="ai/models" element={<LLMManagementUnified />} />
                  <Route path="ai/registry" element={<AIModelManagement />} />
                  <Route path="ai/openrouter" element={<OpenRouterSettings />} />
                  <Route path="ai/usage" element={<LLMUsage />} />
                  <Route path="ai/model-lists" element={<ModelListManagement />} />
                  <Route path="ai/local-models" element={<LocalModelsManagement />} />
                  <Route path="ai/rag-services" element={<RAGServicesManagement />} />
                  <Route path="ai/gpu-services" element={<GPUServicesManagement />} />
                  <Route path="ai/granite-keys" element={<GraniteApiKeysManagement />} />

                  {/* Colonel AI Command System */}
                  <Route path="ai/colonel" element={<ColonelChat />} />
                  <Route path="ai/colonel/setup" element={<ColonelOnboarding />} />
                  <Route path="ai/colonel/status" element={<ColonelStatus />} />

                  {/* Infrastructure */}
                  <Route path="infra/dashboard" element={<AdminInfraDashboard />} />
                  <Route path="infra/services" element={<Services />} />
                  <Route path="infra/resources" element={<System />} />
                  <Route path="infra/hardware" element={<HardwareManagement />} />
                  <Route path="infra/local-users" element={<LocalUserManagement />} />
                  <Route path="infra/network" element={<Network />} />
                  <Route path="infra/storage" element={<StorageBackup />} />
                  <Route path="infra/traefik" element={<TraefikConfig />} />
                  <Route path="infra/traefik/dashboard" element={<TraefikDashboard />} />
                  <Route path="infra/traefik/routes" element={<TraefikRoutes />} />
                  <Route path="infra/traefik/services" element={<TraefikServices />} />
                  <Route path="infra/traefik/ssl" element={<TraefikSSL />} />
                  <Route path="infra/traefik/metrics" element={<TraefikMetrics />} />
                  <Route path="infra/migration" element={<MigrationWizard />} />

                  {/* Platform */}
                  <Route path="platform/landing" element={<LandingCustomization />} />
                  <Route path="platform/white-label" element={<WhiteLabelBuilder />} />
                  <Route path="platform/extensions" element={<ExtensionsMarketplace />} />
                  <Route path="platform/purchases" element={<PurchaseHistory />} />

                  {/* ============================================================ */}
                  {/* SYSTEM SECTION - Platform administration */}
                  {/* ============================================================ */}
                  <Route path="system/models" element={<Navigate to="/admin/ai/registry" replace />} />
                  <Route path="system/model-lists" element={<Navigate to="/admin/ai/model-lists" replace />} />
                  <Route path="system/local-models" element={<Navigate to="/admin/ai/local-models" replace />} />
                  <Route path="system/rag-services" element={<Navigate to="/admin/ai/rag-services" replace />} />
                  <Route path="system/gpu-services" element={<Navigate to="/admin/ai/gpu-services" replace />} />
                  <Route path="system/services" element={<Navigate to="/admin/infra/services" replace />} />
                  <Route path="system/resources" element={<Navigate to="/admin/infra/resources" replace />} />
                  <Route path="system/hardware" element={<Navigate to="/admin/infra/hardware" replace />} />
                  <Route path="infrastructure/hardware" element={<Navigate to="/admin/infra/hardware" replace />} />
                  <Route path="system/analytics" element={<Navigate to="/admin/monitoring/analytics/advanced" replace />} />
                  <Route path="system/usage-analytics" element={<Navigate to="/admin/monitoring/usage-analytics" replace />} />
                  <Route path="system/billing" element={<Navigate to="/admin/billing/system" replace />} />
                  <Route path="system/subscription-management" element={<Navigate to="/admin/billing/tiers" replace />} />
                  <Route path="system/app-management" element={<Navigate to="/admin/billing/apps" replace />} />
                  <Route path="system/pricing-management" element={<Navigate to="/admin/billing/pricing" replace />} />
                  <Route path="platform/white-label" element={<WhiteLabelBuilder />} />
                  {/* Local User Management - consolidated to single route */}
                  <Route path="system/local-users" element={<Navigate to="/admin/infra/local-users" replace />} />
                  <Route path="system/usage-metrics" element={<Navigate to="/admin/monitoring/usage-metrics" replace />} />
                  <Route path="system/network" element={<Navigate to="/admin/infra/network" replace />} />
                  <Route path="system/storage" element={<Navigate to="/admin/infra/storage" replace />} />
                  <Route path="system/security" element={<Security />} />
                  <Route path="system/authentication" element={<Navigate to="/admin/people/authentication" replace />} />
                  <Route path="system/extensions" element={<Navigate to="/admin/platform/extensions" replace />} />
                  <Route path="system/landing" element={<Navigate to="/admin/platform/landing" replace />} />
                  <Route path="system/settings" element={<SystemSettings />} />
                  <Route path="system/forgejo" element={<ForgejoManagement />} />
                  <Route path="system/invite-codes" element={<Navigate to="/admin/people/invite-codes" replace />} />

                  {/* ============================================================ */}
                  {/* MONITORING & ANALYTICS SECTION - Metrics, Logs, Analytics */}
                  {/* ============================================================ */}
                  <Route path="monitoring/analytics" element={<AnalyticsDashboard />} />
                  <Route path="monitoring/analytics/advanced" element={<AdvancedAnalytics />} />
                  <Route path="monitoring/usage-analytics" element={<UsageAnalytics />} />
                  <Route path="monitoring/usage-metrics" element={<UsageMetrics />} />
                  <Route path="monitoring/tools" element={<ExternalMonitoringTools />} />
                  <Route path="monitoring/overview" element={<MonitoringOverview />} />
                  <Route path="monitoring/grafana" element={<GrafanaConfig />} />
                  <Route path="monitoring/grafana/dashboards" element={<GrafanaViewer />} />
                  <Route path="monitoring/prometheus" element={<PrometheusConfig />} />
                  <Route path="monitoring/umami" element={<UmamiConfig />} />
                  <Route path="monitoring/umami-dashboard" element={<UmamiConfig />} />
                  <Route path="monitoring/website-monitor" element={<WebsiteMonitor />} />
                  <Route path="monitoring/logs" element={<Logs />} />
                  <Route path="monitoring/alerts" element={<AlertsManagement />} />
                  <Route path="monitoring/audit" element={<SystemAuditLog />} />

                  {/* Legacy system/logs route (redirect) */}
                  <Route path="system/logs" element={<Navigate to="/admin/monitoring/logs" replace />} />

                  {/* ============================================================ */}
                  {/* INFRASTRUCTURE SECTION - Network & DNS */}
                  {/* ============================================================ */}
                  <Route path="integrations/cloudflare" element={<CloudflareDNS />} />
                  <Route path="integrations/webhooks" element={<WebhooksManagement />} />
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
                  <Route path="credits" element={<Navigate to="/admin/billing/credits" replace />} />
                  <Route path="credits/purchase" element={<Navigate to="/admin/billing/credits/purchase" replace />} />
                  <Route path="credits/tiers" element={<Navigate to="/admin/billing/tiers/compare" replace />} />

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
                  <Route path="extensions" element={<Navigate to="/admin/platform/extensions" replace />} />
                  <Route path="extensions/:id" element={<ProductDetailPage />} />
                  <Route path="extensions/checkout" element={<CheckoutPage />} />
                  <Route path="extensions/success" element={<SuccessPage />} />
                  <Route path="extensions/cancelled" element={<CancelledPage />} />
                  <Route path="purchases" element={<Navigate to="/admin/platform/purchases" replace />} />

                  {/* ============================================================ */}
                  {/* LEGACY ROUTES - Backwards compatibility (DEPRECATED) */}
                  {/* Will be removed after November 13, 2025 */}
                  {/* ============================================================ */}

                  {/* System admin routes - redirect to new system/* namespace */}
                  <Route path="models" element={<Navigate to="/admin/ai/registry" replace />} />
                  <Route path="services" element={<Navigate to="/admin/infra/services" replace />} />
                  <Route path="system" element={<Navigate to="/admin/infra/resources" replace />} />
                  <Route path="network" element={<Navigate to="/admin/infra/network" replace />} />
                  <Route path="storage" element={<Navigate to="/admin/infra/storage" replace />} />
                  <Route path="logs" element={<Navigate to="/admin/monitoring/logs" replace />} />
                  <Route path="security" element={<Navigate to="/admin/system/security" replace />} />
                  <Route path="authentication" element={<Navigate to="/admin/people/authentication" replace />} />
                  <Route path="landing" element={<Navigate to="/admin/platform/landing" replace />} />
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
