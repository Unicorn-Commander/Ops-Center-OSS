import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useSystem } from '../contexts/SystemContext';
import MarketplaceLanding from '../pages/public/MarketplaceLanding';
import LoadingScreen from './LoadingScreen';

/**
 * RootRedirect - Smart router for the root path (/)
 *
 * Logic:
 * 1. Check if user is authenticated (via localStorage authToken or SystemContext)
 * 2. If authenticated → redirect to /admin/dashboard
 * 3. If NOT authenticated → Check landing_page_mode setting from backend
 *    - 'direct_sso' → redirect to /auth/login (Keycloak SSO)
 *    - 'public_marketplace' → show MarketplaceLanding component
 *    - 'custom' → show CustomLandingPage (future feature)
 *
 * Backend API Expected:
 * GET /api/v1/system/settings should return:
 * {
 *   "landing_page_mode": "direct_sso" | "public_marketplace" | "custom",
 *   "branding": {
 *     "company_name": "Unicorn Commander",
 *     "logo_url": "/assets/logo.svg",
 *     "primary_color": "#7c3aed"
 *   }
 * }
 */
export default function RootRedirect() {
  const [loading, setLoading] = useState(true);
  const [authenticated, setAuthenticated] = useState(false);
  const [landingMode, setLandingMode] = useState('direct_sso');

  useEffect(() => {
    const checkAuth = async () => {
      // Check for authToken in localStorage
      const token = localStorage.getItem('authToken');

      if (token) {
        setAuthenticated(true);
        setLoading(false);
        return;
      }

      // Check for OAuth session
      try {
        const response = await fetch('/api/v1/auth/session');
        if (response.ok) {
          const data = await response.json();
          if (data.authenticated) {
            setAuthenticated(true);
            setLoading(false);
            return;
          }
        }
      } catch (error) {
        console.error('Failed to check auth session:', error);
      }

      // User is NOT authenticated - fetch landing page mode
      // Note: System settings endpoint may not exist, default to direct_sso
      try {
        const response = await fetch('/api/v1/system/settings');
        if (response.ok) {
          const data = await response.json();
          setLandingMode(data.landing_page_mode || 'direct_sso');
        } else if (response.status === 404) {
          // Endpoint doesn't exist, use default
          setLandingMode('direct_sso');
        }
      } catch (error) {
        // Network error or endpoint unavailable - use default
        console.debug('Landing page mode unavailable, using default SSO redirect');
        setLandingMode('direct_sso');
      }

      setAuthenticated(false);
      setLoading(false);
    };

    checkAuth();
  }, []);

  // Show loading screen while checking auth
  if (loading) {
    return <LoadingScreen />;
  }

  // If authenticated, redirect to user landing page (search bar, apps, user dropdown)
  // Users can access admin console via link in PublicLanding
  if (authenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  // User is NOT authenticated - show appropriate landing page
  switch (landingMode) {
    case 'public_marketplace':
      return <MarketplaceLanding />;

    case 'custom':
      // TODO: Implement custom landing page feature
      // For now, fallback to marketplace
      return <MarketplaceLanding />;

    case 'direct_sso':
    default:
      // Use window.location.replace() for immediate redirect without history
      // This prevents React from continuing to render and make API calls
      if (typeof window !== 'undefined') {
        window.location.replace('/auth/login');
      }
      // Return null to stop rendering immediately
      return null;
  }
}
