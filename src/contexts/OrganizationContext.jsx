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

      const response = await fetch('/api/v1/org/my-orgs', {
        method: 'GET',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        // If user has no organizations yet, that's okay
        if (response.status === 404) {
          setOrganizations([]);
          setCurrentOrgId(null);
          setLoading(false);
          return;
        }
        throw new Error('Failed to fetch organizations');
      }

      const data = await response.json();
      console.log('[OrganizationContext] Fetched user organizations:', data);

      setOrganizations(data || []);

      // If no current org set, default to first org
      if (!currentOrgId && data && data.length > 0) {
        const firstOrg = data[0];
        // Set org ID without reloading (initial load)
        setCurrentOrgId(firstOrg.id);
        localStorage.setItem('currentOrgId', firstOrg.id);
        console.log('[OrganizationContext] Set initial organization:', firstOrg.id);
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

      // Update local state
      setCurrentOrgId(orgId);

      // Persist to localStorage
      localStorage.setItem('currentOrgId', orgId);

      // Notify backend (for analytics) - endpoint doesn't exist yet, so just skip
      // TODO: Implement /api/v1/org/{orgId}/switch endpoint if analytics needed
      console.log('[OrganizationContext] Organization switched to:', orgId);

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
    hasOrgRole,
    refreshOrganizations,
    hasOrganization: currentOrg !== null
  };

  return (
    <OrganizationContext.Provider value={value}>
      {children}
    </OrganizationContext.Provider>
  );
}

export default OrganizationContext;
