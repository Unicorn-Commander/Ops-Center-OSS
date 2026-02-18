import React, { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import LoadingScreen from './LoadingScreen';

/**
 * AdminRedirect - Smart router for /admin/ landing
 *
 * Redirects based on user role:
 * - Admins → /admin/dashboard (infrastructure dashboard)
 * - Regular users → /admin/my-dashboard (personal credits/usage)
 */
export default function AdminRedirect() {
  const [loading, setLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Check user role from localStorage or session
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}');
    const role = userInfo.role || 'viewer';

    // Admin role has full access
    const adminRoles = ['admin', 'super_admin', 'platform_admin'];
    setIsAdmin(adminRoles.includes(role?.toLowerCase()));
    setLoading(false);
  }, []);

  if (loading) {
    return <LoadingScreen />;
  }

  // Admins go to infrastructure dashboard
  if (isAdmin) {
    return <Navigate to="/admin/dashboard" replace />;
  }

  // Regular users go to their personal dashboard
  return <Navigate to="/admin/my-dashboard" replace />;
}
