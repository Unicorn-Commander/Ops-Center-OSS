/**
 * OrganizationContext - Multi-Organization Management
 *
 * Provides:
 * - Current organization tracking
 * - User's organization list with roles
 * - Organization switching functionality
 * - Cross-tab synchronization via BroadcastChannel
 * - LocalStorage persistence
 *
 * Created: October 17, 2025
 * Status: Production Ready
 */

import React, { createContext, useContext, useState, useEffect } from 'react';

const OrganizationContext = createContext();

// BroadcastChannel for cross-tab synchronization
let orgChannel;
if (typeof window !== 'undefined' && window.BroadcastChannel) {
  orgChannel = new BroadcastChannel('org-switcher');
}

export function useOrganization() {
  const context = useContext(OrganizationContext);
  if (!context) {
    throw new Error('useOrganization must be used within OrganizationProvider');
  }
  return context;
}

export function OrganizationProvider({ children }) {
  const [organizations, setOrganizations] = useState([]);
  const [currentOrgId, setCurrentOrgId] = useState(() => {
    // Load from localStorage on init
    return localStorage.getItem('currentOrgId') || null;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch user's organizations on mount
  useEffect(() => {
    fetchOrganizations();
  }, []);

  // Listen for organization changes from other tabs
  useEffect(() => {
    if (!orgChannel) return;

    const handleMessage = (event) => {
      if (event.data.type === 'ORG_SWITCHED') {
        console.log('[OrganizationContext] Received org switch from another tab:', event.data.orgId);
        setCurrentOrgId(event.data.orgId);
      }
    };

    orgChannel.addEventListener('message', handleMessage);
    return () => orgChannel.removeEventListener('message', handleMessage);
  }, []);

  const fetchOrganizations = async () => {
    try {
      setLoading(true);
      setError(null);

      // Try new org-centric endpoint first, fall back to legacy
      let response = await fetch('/api/v1/users/me/organizations', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });

      // Fall back to legacy endpoint if new one not available
      if (response.status === 404) {
        response = await fetch('/api/v1/org/my-orgs', {
          method: 'GET',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' }
        });
      }

      if (!response.ok) {
        // If user has no organizations yet, that's okay
        if (response.status === 404 || response.status === 401) {
          setOrganizations([]);
          setCurrentOrgId(null);
          setLoading(false);
          return;
        }
        throw new Error('Failed to fetch organizations');
      }

      const data = await response.json();
      console.log('[OrganizationContext] Fetched user organizations:', data);

      // Handle new API response format: { organizations: [...], current_org_id, default_org_id }
      const orgs = data.organizations || data || [];
      setOrganizations(orgs);

      // If no current org set, use API's current_org_id or default to first org
      if (!currentOrgId && orgs.length > 0) {
        const orgId = data.current_org_id || data.default_org_id || orgs[0].id;
        setCurrentOrgId(orgId);
        localStorage.setItem('currentOrgId', orgId);
        console.log('[OrganizationContext] Set initial organization:', orgId);
      }
    } catch (err) {
      console.error('[OrganizationContext] Error fetching organizations:', err);
      setError(err.message);
      setOrganizations([]);
    } finally {
      setLoading(false);
    }
  };

  const switchOrganization = async (orgId) => {
    try {
      console.log('[OrganizationContext] Switching to organization:', orgId);

      // Call backend to set org cookie and validate membership
      const response = await fetch('/api/v1/users/me/switch-org', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ org_id: orgId })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to switch organization');
      }

      const data = await response.json();
      console.log('[OrganizationContext] Organization switched:', data);

      // Update local state
      setCurrentOrgId(orgId);

      // Persist to localStorage
      localStorage.setItem('currentOrgId', orgId);

      // Broadcast to other tabs
      if (orgChannel) {
        orgChannel.postMessage({
          type: 'ORG_SWITCHED',
          orgId: orgId,
          timestamp: Date.now()
        });
      }

      // Reload page to update all org-scoped data
      window.location.reload();
    } catch (err) {
      console.error('[OrganizationContext] Error switching organization:', err);
      setError(err.message);
    }
  };

  const getCurrentOrganization = () => {
    if (!currentOrgId || !organizations.length) {
      return null;
    }
    return organizations.find(org => org.id === currentOrgId) || null;
  };

  const getCurrentOrgRole = () => {
    const currentOrg = getCurrentOrganization();
    return currentOrg?.role || null;
  };

  const hasOrgRole = (allowedRoles) => {
    const role = getCurrentOrgRole();
    return role && allowedRoles.includes(role);
  };

  const refreshOrganizations = () => {
    return fetchOrganizations();
  };

  // Set current organization without reloading
  const setCurrentOrg = (orgId) => {
    console.log('[OrganizationContext] Setting current org (no reload):', orgId);
    setCurrentOrgId(orgId);
    localStorage.setItem('currentOrgId', orgId);
  };

  // Legacy compatibility
  const selectOrganization = (org) => {
    if (org && org.id) {
      switchOrganization(org.id);
    }
  };

  const currentOrg = getCurrentOrganization();

  // Get tier badge color based on tier code
  const getTierColor = (tierCode) => {
    const tierColors = {
      'vip_founder': '#FFD700',      // Gold
      'founder-friend': '#FFD700',   // Gold
      'byok': '#9c27b0',             // Purple
      'managed': '#2196f3',          // Blue
      'human_interest': '#4caf50',   // Green
      'loopnet_starter': '#ff9800',  // Orange
      'loopnet_professional': '#ff5722', // Deep Orange
      'professional': '#2196f3',     // Blue
      'enterprise': '#673ab7',       // Deep Purple
      'trial': '#9e9e9e',            // Gray
      'starter': '#03a9f4',          // Light Blue
    };
    return tierColors[tierCode?.toLowerCase()] || '#9e9e9e';
  };

  // Get current org's tier code
  const getCurrentTierCode = () => {
    return currentOrg?.tier?.code || null;
  };

  // Get current org's apps
  const getCurrentOrgApps = () => {
    return currentOrg?.apps || [];
  };

  const value = {
    organizations,
    currentOrg,
    currentOrgId,
    loading,
    error,
    selectOrganization,
    switchOrganization,
    setCurrentOrg,  // New: set org without reload
    getCurrentOrganization,
    getCurrentOrgRole,
    getCurrentTierCode,
    getCurrentOrgApps,
    getTierColor,
    hasOrgRole,
    refreshOrganizations,
    hasOrganization: currentOrg !== null,
    hasMultipleOrgs: organizations.length > 1
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export default OrganizationContext;
