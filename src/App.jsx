import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider as MuiThemeProvider, createTheme, CssBaseline } from '@mui/material';

// Eagerly load critical components (needed on first render)
import Layout from './components/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import LoadingScreen from './components/LoadingScreen';
import { SystemProvider, useSystem } from './contexts/SystemContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { DeploymentProvider } from './contexts/DeploymentContext';
import { OrganizationProvider } from './contexts/OrganizationContext';
import { ToastProvider } from './components/Toast';
import { BrandingProvider } from './contexts/BrandingContext';

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

const muiTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#8b5cf6',
      dark: '#6d28d9',
      light: '#a855f7',
      contrastText: '#f8fbff',
    },
    secondary: {
      main: '#22d3ee',
      contrastText: '#04121a',
    },
    background: {
      default: '#070912',
      paper: '#12141f',
    },
    text: {
      primary: '#f3f5fb',
      secondary: '#aebbcf',
      disabled: '#64708a',
    },
    divider: 'rgba(148, 163, 184, 0.14)',
    error: { main: '#fb7185' },
    warning: { main: '#fbbf24' },
    success: { main: '#34d399' },
    info: { main: '#38bdf8' },
  },
  shape: {
    borderRadius: 16,
  },
  typography: {
    fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    // Display type = Space Grotesk (confident, tight), matching homegrow's craft.
    h1: { fontFamily: '"Space Grotesk", "Inter", sans-serif', fontWeight: 700, letterSpacing: '-0.025em' },
    h2: { fontFamily: '"Space Grotesk", "Inter", sans-serif', fontWeight: 700, letterSpacing: '-0.022em' },
    h3: { fontFamily: '"Space Grotesk", "Inter", sans-serif', fontWeight: 600, letterSpacing: '-0.018em' },
    h4: { fontFamily: '"Space Grotesk", "Inter", sans-serif', fontWeight: 600, letterSpacing: '-0.012em' },
    h5: { fontFamily: '"Space Grotesk", "Inter", sans-serif', fontWeight: 600, letterSpacing: '-0.008em' },
    h6: { fontWeight: 600, letterSpacing: '-0.005em' },
    button: {
      textTransform: 'none',
      fontWeight: 600,
      letterSpacing: 0,
    },
    overline: { letterSpacing: '0.06em', fontWeight: 600 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: '#070912',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(148, 163, 184, 0.12)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          // Subtle glass: translucent surface + backdrop blur (readable, not gimmicky)
          backgroundColor: 'rgba(18, 21, 33, 0.72)',
          backdropFilter: 'blur(14px) saturate(125%)',
          WebkitBackdropFilter: 'blur(14px) saturate(125%)',
          border: '1px solid rgba(160, 170, 210, 0.12)',
          // depth: luminance + a soft deep shadow + faint inner highlight
          boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.05), 0 18px 48px -24px rgba(0,0,0,0.7)',
          borderRadius: 16,
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: {
          borderRadius: 10,
          minHeight: 38,
          fontWeight: 600,
        },
        containedPrimary: {
          background: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
          color: '#f8fbff',
          boxShadow: '0 6px 18px rgba(124, 58, 237, 0.28)',
          '&:hover': {
            background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            boxShadow: '0 8px 22px rgba(124, 58, 237, 0.40)',
          },
        },
        outlined: { borderColor: 'rgba(148, 163, 184, 0.28)' },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(2, 6, 23, 0.40)',
          borderRadius: 10,
          '& fieldset': {
            borderColor: 'rgba(148, 163, 184, 0.22)',
          },
          '&:hover fieldset': {
            borderColor: 'rgba(168, 85, 247, 0.45)',
          },
          '&.Mui-focused fieldset': {
            borderColor: '#a855f7',
            borderWidth: 2,
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderColor: 'rgba(148, 163, 184, 0.12)',
        },
        head: {
          color: '#c4d2e6',
          fontWeight: 600,
          fontSize: '0.78rem',
          letterSpacing: '0.04em',
          textTransform: 'uppercase',
          backgroundColor: 'rgba(255,255,255,0.015)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { borderRadius: 8, fontWeight: 500 },
        outlined: { borderColor: 'rgba(148, 163, 184, 0.24)' },
      },
    },
    MuiSkeleton: {
      styleOverrides: {
        root: { backgroundColor: 'rgba(148, 163, 184, 0.10)', borderRadius: 8 },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#20232f',
          border: '1px solid rgba(148, 163, 184, 0.18)',
          fontSize: '0.75rem',
          borderRadius: 8,
          padding: '6px 10px',
          boxShadow: '0 8px 24px rgba(2,6,23,0.5)',
        },
        arrow: { color: '#20232f' },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: { borderRadius: 12, border: '1px solid', alignItems: 'center' },
        standardError:   { backgroundColor: 'rgba(220,38,38,0.10)', borderColor: 'rgba(248,113,113,0.30)', color: '#fca5a5' },
        standardWarning: { backgroundColor: 'rgba(217,119,6,0.10)', borderColor: 'rgba(251,191,36,0.30)', color: '#fcd34d' },
        standardInfo:    { backgroundColor: 'rgba(37,99,235,0.10)', borderColor: 'rgba(96,165,250,0.30)', color: '#93c5fd' },
        standardSuccess: { backgroundColor: 'rgba(22,163,74,0.10)', borderColor: 'rgba(74,222,128,0.30)', color: '#86efac' },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 600, minHeight: 44 },
      },
    },
  },
});

// Import touch optimization utilities
import { initTouchOptimizations } from './utils/touchOptimization';

// Import Extensions Context Provider
import { ExtensionsProvider } from './contexts/ExtensionsContext';

// Import Colonel Context Provider (global Colonel status)
import { ColonelProvider } from './contexts/ColonelContext';

// Eagerly load RootRedirect (needed on first render for root route)
import RootRedirect from './components/RootRedirect';

// Lazy load all pages (loaded on-demand when route is accessed)
const PublicLanding = lazy(() => import('./pages/PublicLanding'));
const PublicStatusPage = lazy(() => import('./pages/PublicStatusPage'));
const Login = lazy(() => import('./pages/Login'));
const NotFound = lazy(() => import('./pages/NotFound'));
const MarketplaceLanding = lazy(() => import('./pages/public/MarketplaceLanding'));
const CheckoutContinue = lazy(() => import('./pages/public/CheckoutContinue'));

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
const AccountSecurity = lazy(() => import('./pages/account/AccountSecurity'));
const AccountAPIKeys = lazy(() => import('./pages/account/AccountAPIKeys'));
const NotificationSettings = lazy(() => import('./pages/NotificationSettings'));

// Subscription pages (lazy loaded)
const SubscriptionPlan = lazy(() => import('./pages/subscription/SubscriptionPlan'));
const SubscriptionUsage = lazy(() => import('./pages/subscription/SubscriptionUsage'));
const SubscriptionBilling = lazy(() => import('./pages/subscription/SubscriptionBilling'));
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
// Admin pricing/policy pages (June 2026)
const AppModelPolicy = lazy(() => import('./pages/admin/AppModelPolicy'));
const CreditPackages = lazy(() => import('./pages/admin/CreditPackages'));
const AgentPricing = lazy(() => import('./pages/admin/AgentPricing'));
const OrgFeatures = lazy(() => import('./pages/admin/OrgFeatures'));
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

// Federation pages (lazy loaded)
const FederationSettings = lazy(() => import('./pages/admin/FederationSettings'));
const FederationNodes = lazy(() => import('./pages/admin/FederationNodes'));
const FederationContracts = lazy(() => import('./pages/admin/FederationContracts'));
const NetworkVPNKeys = lazy(() => import('./pages/admin/NetworkVPNKeys'));
const FederationTopology = lazy(() => import('./pages/admin/FederationTopology'));
const FederationServiceCatalog = lazy(() => import('./pages/admin/FederationServiceCatalog'));

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
const CreditPurchase = lazy(() => import('./pages/CreditPurchase'));
const CreditDashboard = lazy(() => import('./pages/CreditDashboard'));
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
const PricingRates = lazy(() => import('./pages/admin/PricingRates'));

// Lazy load non-critical components
const OnboardingTour = lazy(() => import('./components/OnboardingTour'));
const HelpPanel = lazy(() => import('./components/HelpPanel'));

// Protected Route wrapper for admin pages
function ProtectedRoute({ children }) {
  const [checking, setChecking] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  
  useEffect(() => {
    // ALWAYS verify the server session — a cached localStorage token may be
    // expired, which used to render every admin page as a sea of 401s with
    // stale user data instead of sending the user back to login.
    fetch('/api/v1/auth/session', { credentials: 'include' })
      .then(res => {
        if (res.ok) {
          return res.json();
        }
        throw new Error('Not authenticated');
      })
      .then(data => {
        if (data.authenticated) {
          if (data.token) {
            localStorage.setItem('authToken', data.token);
          }
          if (data.user) {
            // Use 'userInfo' key to match Layout.jsx; refresh so role/tier are current
            localStorage.setItem('userInfo', JSON.stringify(data.user));
          }
          setAuthenticated(true);
        } else {
          throw new Error('Not authenticated');
        }
      })
      .catch(() => {
        // Clear stale client-side auth state so the UI can't half-render as a
        // logged-in user whose session is actually dead.
        localStorage.removeItem('authToken');
        localStorage.removeItem('userInfo');
        setAuthenticated(false);
      })
      .finally(() => {
        setChecking(false);
      });
  }, []);
  
  if (checking) {
    return <LoadingScreen />;
  }
  
  if (!authenticated) {
    // Send unauthenticated users to the BRANDED /admin/login SPA page.
    // From there they can click "Continue with SSO" to start the Keycloak
    // flow, or use a local-account fallback. This avoids bouncing them
    // straight to the upstream IdP and losing tenant branding context.
    const path = window.location.pathname;
    if (path !== '/admin/login' && !path.startsWith('/auth/')) {
      // Preserve original destination so post-login can return user there.
      const next = encodeURIComponent(path + window.location.search);
      window.location.href = `/admin/login?next=${next}`;
    }
    return <LoadingScreen />;
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
          <ColonelProvider>
            {children}
          </ColonelProvider>
        </ExtensionsProvider>
      </OrganizationProvider>
    </SystemProvider>
  );
}

function AppRoutes() {
  const location = useLocation();
  const [showHelp, setShowHelp] = useState(false);
  const isAdminShellRoute = location.pathname.startsWith('/admin') && location.pathname !== '/admin/login';
  // Role (same source Layout uses) — the Help button/panel is an admin affordance;
  // end users get the floating Guide bubble instead.
  let userRole = 'viewer';
  try { userRole = JSON.parse(localStorage.getItem('userInfo') || '{}').role || 'viewer'; } catch (_) { userRole = 'viewer'; }
  const isAdmin = userRole === 'admin';
  
  // Keyboard shortcut for help (only on admin pages)
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === '?' && !e.target.matches('input, textarea, select') && isAdminShellRoute) {
        setShowHelp(!showHelp);
      }
    };
    
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [showHelp, location.pathname, isAdminShellRoute]);

  // Sidebar "Help & Documentation" (Layout.jsx) opens the same panel via this event
  useEffect(() => {
    const openHelp = () => { if (isAdminShellRoute) setShowHelp(true); };
    window.addEventListener('uc:open-help', openHelp);
    return () => window.removeEventListener('uc:open-help', openHelp);
  }, [isAdminShellRoute]);
  
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
          <Route path="/pricing" element={<MarketplaceLanding />} />
          <Route path="/checkout/continue" element={<CheckoutContinue />} />

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
                  <Route path="account/notifications" element={<Navigate to="/admin/account/notification-settings" replace />} />
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
                  <Route path="people/org-features" element={<OrgFeatures />} />

                  {/* Billing & Plans */}
                  <Route path="billing/tiers" element={<SubscriptionManagement />} />
                  <Route path="billing/tiers/compare" element={<TierComparison />} />
                  <Route path="billing/apps" element={<AppManagement />} />
                  <Route path="billing/pricing" element={<DynamicPricingManagement />} />
                  <Route path="billing/rates" element={<PricingRates />} />
                  <Route path="billing/revenue" element={<RevenueDashboard />} />
                  <Route path="billing/system" element={<BillingDashboard />} />
                  <Route path="billing/user" element={<UserBillingDashboard />} />
                  <Route path="billing/overview" element={<SystemBillingOverview />} />
                  <Route path="billing/credits" element={<CreditPurchase />} />
                  <Route path="billing/credits/purchase" element={<CreditPurchase />} />
                  <Route path="billing/inference-policy" element={<AppModelPolicy />} />
                  <Route path="billing/credit-packs" element={<CreditPackages />} />
                  <Route path="billing/agent-pricing" element={<AgentPricing />} />

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
                  <Route path="infra/network/vpn-keys" element={<NetworkVPNKeys />} />
                  <Route path="infra/storage" element={<StorageBackup />} />
                  <Route path="infra/traefik" element={<TraefikConfig />} />
                  <Route path="infra/traefik/dashboard" element={<TraefikDashboard />} />
                  <Route path="infra/traefik/routes" element={<TraefikRoutes />} />
                  <Route path="infra/traefik/services" element={<TraefikServices />} />
                  <Route path="infra/traefik/ssl" element={<TraefikSSL />} />
                  <Route path="infra/traefik/metrics" element={<TraefikMetrics />} />
                  <Route path="infra/migration" element={<MigrationWizard />} />
                  <Route path="infra/federation" element={<FederationSettings />} />
                  <Route path="infra/federation/nodes" element={<FederationNodes />} />
                  <Route path="infra/federation/contracts" element={<FederationContracts />} />
                  <Route path="infra/federation/topology" element={<FederationTopology />} />
                  <Route path="infra/federation/services" element={<FederationServiceCatalog />} />

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
                  <Route path="system/users" element={<Navigate to="/admin/people/users" replace />} />
                  <Route path="system/users/:userId" element={<ParamRedirect to="/admin/people/users/:userId" />} />
                  <Route path="billing/dashboard" element={<Navigate to="/admin/billing/revenue" replace />} />
                  <Route path="system/subscription-management" element={<Navigate to="/admin/billing/tiers" replace />} />
                  <Route path="system/app-management" element={<Navigate to="/admin/billing/apps" replace />} />
                  <Route path="system/pricing-management" element={<Navigate to="/admin/billing/pricing" replace />} />
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
                  <Route path="credits" element={<CreditDashboard />} />
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

                  {/* Catch-all: unknown /admin/* URLs get a real 404 inside the shell */}
                  <Route path="*" element={<NotFound admin />} />

                </Routes>
              </Layout>
            </AdminContent>
          </ProtectedRoute>
        } />

        {/* Catch-all: unknown public URLs get a real 404 instead of a blank page */}
        <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>

      {/* Help Panel - only show on admin pages */}
      {isAdminShellRoute && (
        <Suspense fallback={null}>
          <HelpPanel
            isOpen={showHelp}
            onClose={() => setShowHelp(false)}
            currentPage={getCurrentPage()}
          />
        </Suspense>
      )}

      {/* Floating Help / Ask-the-Guide launcher — admins only (end users get the
          Guide bubble; the '?' shortcut still opens the panel for anyone). */}
      {isAdminShellRoute && !showHelp && isAdmin && (
        <button
          onClick={() => setShowHelp(true)}
          title="Help & The Guide  (press ?)"
          aria-label="Open Help and ask the Guide"
          className="fixed bottom-20 right-5 z-40 flex items-center gap-2 pl-3 pr-4 py-2 rounded-full shadow-lg text-white bg-gradient-to-br from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 transition-colors"
        >
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 3l1.6 3.8L17.5 8.4 13.6 10 12 13.8 10.4 10 6.5 8.4 10.4 6.8z" />
            <circle cx="18" cy="17" r="1.5" />
            <circle cx="6" cy="16" r="1" />
          </svg>
          <span className="text-sm font-medium">Help</span>
        </button>
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

    // Onboarding tour DISABLED 2026-06-07. The 8-step feature walkthrough
    // ("Welcome to UC-1 Pro Admin Dashboard! 🦄") is parked until it is replaced
    // by a real first-run SETUP CHECKLIST (LLM provider keys, email/SMTP, Stripe,
    // Cloudflare token, federation). It no longer auto-shows on admin pages.
    // (showOnboarding stays false → <OnboardingTour/> never mounts.)
  }, []);

  return (
    <ErrorBoundary>
      <MuiThemeProvider theme={muiTheme}>
        <CssBaseline />
        <QueryClientProvider client={queryClient}>
          <BrandingProvider>
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
            </BrandingProvider>
          </QueryClientProvider>
      </MuiThemeProvider>
    </ErrorBoundary>
  );
}

export default App;
