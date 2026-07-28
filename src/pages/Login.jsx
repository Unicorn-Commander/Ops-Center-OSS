import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  LockClosedIcon,
  UserIcon,
  KeyIcon,
  ExclamationTriangleIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';
import { useBranding } from '../contexts/BrandingContext';

export default function Login() {
  const navigate = useNavigate();
  const { branding, loading: brandingLoading } = useBranding();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showLocalLogin, setShowLocalLogin] = useState(false);
  const [credentials, setCredentials] = useState({
    username: '',
    password: ''
  });

  const primaryColor = branding?.primary_color || '#7c3aed';
  const companyName = branding?.company_name || 'Ops-Center';
  const tagline = branding?.tagline || 'Operations Center';
  const subtitle = branding?.subtitle || '';
  const logoUrl = branding?.logo_url || '/logos/ops-center-logo.png';
  const ssoEnabled = branding?.sso_enabled !== false;
  const ssoProviderName = branding?.sso_provider_name || 'SSO';
  const upstreamName = branding?.federation_upstream_name || 'Unicorn Commander';
  const upstreamLogo = branding?.federation_upstream_logo || '/logos/The_Colonel.webp';

  // Post-login destination (set by ProtectedRoute when an expired session
  // bounces the user here). Only relative paths are honored — the backend
  // callback applies the same guard against open redirects.
  const nextParam = new URLSearchParams(window.location.search).get('next');
  const safeNext = nextParam && nextParam.startsWith('/') && !nextParam.startsWith('//') ? nextParam : null;

  const handleSSOLogin = () => {
    window.location.href = safeNext
      ? `/auth/login?return_url=${encodeURIComponent(safeNext)}`
      : '/auth/login';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(credentials)
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.access_token);
        localStorage.setItem('userInfo', JSON.stringify({
          username: credentials.username,
          tokenType: data.token_type,
          expiresIn: data.expires_in
        }));
        navigate(safeNext || '/admin/');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (err) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{
        background: `linear-gradient(135deg, ${primaryColor}15 0%, ${primaryColor}08 100%), linear-gradient(to bottom right, #0f172a 0%, #1e293b 50%, #0f172a 100%)`
      }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.5 }}
        className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl p-8 max-w-md w-full border border-white/20"
      >
        {/* Logo and Title */}
        <div className="text-center mb-8">
          {logoUrl && (
            <img
              src={logoUrl}
              alt={companyName}
              className="h-16 mx-auto mb-4 object-contain"
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          )}
          <h1 className="text-3xl font-bold text-white mb-2">
            {companyName}
          </h1>
          {subtitle && (
            <p className="text-purple-200/80 text-sm font-medium mb-1">{subtitle}</p>
          )}
          <p className="text-purple-200/60">{tagline}</p>
        </div>

        {/* Error Message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg"
          >
            <div className="flex items-center gap-2 text-red-200">
              <ExclamationTriangleIcon className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </motion.div>
        )}

        {/* SSO Button */}
        {ssoEnabled && !showLocalLogin && (
          <div className="space-y-4">
            <button
              onClick={handleSSOLogin}
              className="w-full py-3 px-4 text-white font-medium rounded-lg transition-all duration-200 flex items-center justify-center gap-2 shadow-lg"
              style={{
                background: `linear-gradient(135deg, ${primaryColor} 0%, ${primaryColor}dd 100%)`
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = `0 8px 25px ${primaryColor}40`;
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '';
              }}
            >
              <img
                src={upstreamLogo}
                alt={upstreamName}
                className="h-6 w-6 object-contain"
                onError={(e) => { e.currentTarget.style.display = 'none'; }}
              />
              Continue with {upstreamName} SSO
            </button>

            <div className="relative my-6">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-transparent text-purple-200/50">or</span>
              </div>
            </div>

            <button
              onClick={() => setShowLocalLogin(true)}
              className="w-full py-3 px-4 bg-white/5 border border-white/10 text-purple-200 font-medium rounded-lg hover:bg-white/10 transition-all duration-200 flex items-center justify-center gap-2"
            >
              <LockClosedIcon className="h-5 w-5" />
              Sign in with local account
            </button>
          </div>
        )}

        {/* Local Login Form */}
        {(!ssoEnabled || showLocalLogin) && (
          <form onSubmit={handleSubmit} className="space-y-6">
            {showLocalLogin && (
              <button
                type="button"
                onClick={() => setShowLocalLogin(false)}
                className="text-sm text-purple-300 hover:text-purple-200 transition-colors"
              >
                &larr; Back to SSO login
              </button>
            )}

            <div>
              <label className="block text-sm font-medium text-purple-200 mb-2">
                Username
              </label>
              <div className="relative">
                <UserIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-purple-300" />
                <input
                  type="text"
                  value={credentials.username}
                  onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter your username"
                  required
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-purple-200 mb-2">
                Password
              </label>
              <div className="relative">
                <KeyIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-purple-300" />
                <input
                  type="password"
                  value={credentials.password}
                  onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                  placeholder="Enter your password"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 text-white font-medium rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2"
              style={{
                background: `linear-gradient(135deg, ${primaryColor} 0%, ${primaryColor}dd 100%)`
              }}
            >
              <LockClosedIcon className="h-5 w-5" />
              {loading ? 'Logging in...' : 'Login'}
            </button>
          </form>
        )}

        {/* Footer */}
        <div className="mt-8 text-center">
          <p className="text-purple-300/50 text-xs">
            {companyName} &mdash; {tagline}
          </p>
        </div>
      </motion.div>
    </div>
  );
}
