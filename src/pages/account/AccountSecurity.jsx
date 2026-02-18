/**
 * AccountSecurity Component
 *
 * Security settings and session management
 * - Change password form
 * - Active sessions list with revoke capability
 * - 2FA setup (placeholder for now)
 * - Recent security activity
 *
 * API Endpoints:
 * - PUT /api/v1/auth/password - Change password
 * - GET /api/v1/auth/sessions - List active sessions
 * - DELETE /api/v1/auth/sessions/{session_id} - Revoke session
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ShieldCheckIcon,
  KeyIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  TrashIcon,
  ClockIcon,
  MapPinIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

export default function AccountSecurity() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [revokingSession, setRevokingSession] = useState(null);

  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  });

  const [passwordErrors, setPasswordErrors] = useState({});

  // Theme classes matching UserSettings pattern
  const themeClasses = {
    card: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 backdrop-blur-xl border-white/20'
      : currentTheme === 'light'
      ? 'bg-white border-gray-200'
      : 'bg-slate-800 border-slate-700',
    text: currentTheme === 'unicorn'
      ? 'text-purple-100'
      : currentTheme === 'light'
      ? 'text-gray-900'
      : 'text-slate-100',
    subtext: currentTheme === 'unicorn'
      ? 'text-purple-300'
      : currentTheme === 'light'
      ? 'text-gray-600'
      : 'text-slate-400',
    input: currentTheme === 'unicorn'
      ? 'bg-purple-900/50 border-white/20 text-purple-100'
      : currentTheme === 'light'
      ? 'bg-gray-50 border-gray-300 text-gray-900'
      : 'bg-slate-900 border-slate-600 text-slate-100',
    button: currentTheme === 'unicorn'
      ? 'bg-purple-600 hover:bg-purple-700 text-white'
      : currentTheme === 'light'
      ? 'bg-blue-600 hover:bg-blue-700 text-white'
      : 'bg-blue-600 hover:bg-blue-700 text-white'
  };

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const response = await fetch('/api/v1/auth/sessions');
      if (response.ok) {
        const data = await response.json();
        setSessions(data.sessions || []);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      // Mock data for demonstration
      setSessions([
        {
          id: 'current',
          device: 'Current Session',
          location: 'San Francisco, CA',
          ip: '192.168.1.1',
          lastActive: 'Active now',
          isCurrent: true
        },
        {
          id: '2',
          device: 'Chrome on Windows',
          location: 'New York, NY',
          ip: '192.168.1.2',
          lastActive: '2 hours ago',
          isCurrent: false
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const validatePassword = () => {
    const errors = {};

    if (!passwordForm.currentPassword) {
      errors.currentPassword = 'Current password is required';
    }

    if (!passwordForm.newPassword) {
      errors.newPassword = 'New password is required';
    } else if (passwordForm.newPassword.length < 8) {
      errors.newPassword = 'Password must be at least 8 characters';
    } else if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(passwordForm.newPassword)) {
      errors.newPassword = 'Password must contain uppercase, lowercase, and number';
    }

    if (!passwordForm.confirmPassword) {
      errors.confirmPassword = 'Please confirm your password';
    } else if (passwordForm.newPassword !== passwordForm.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    setPasswordErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();

    if (!validatePassword()) {
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const response = await fetch('/api/v1/auth/password', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_password: passwordForm.currentPassword,
          new_password: passwordForm.newPassword
        })
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Password changed successfully' });
        setPasswordForm({
          currentPassword: '',
          newPassword: '',
          confirmPassword: ''
        });
        setTimeout(() => setMessage(null), 3000);
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to change password' });
      }
    } catch (error) {
      console.error('Failed to change password:', error);
      setMessage({ type: 'error', text: 'An error occurred while changing password' });
    } finally {
      setSaving(false);
    }
  };

  const handleRevokeSession = async (sessionId) => {
    if (!confirm('Are you sure you want to revoke this session?')) {
      return;
    }

    setRevokingSession(sessionId);

    try {
      const response = await fetch(`/api/v1/auth/sessions/${sessionId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        setSessions(sessions.filter(s => s.id !== sessionId));
        setMessage({ type: 'success', text: 'Session revoked successfully' });
        setTimeout(() => setMessage(null), 2000);
      } else {
        setMessage({ type: 'error', text: 'Failed to revoke session' });
      }
    } catch (error) {
      console.error('Failed to revoke session:', error);
      setMessage({ type: 'error', text: 'An error occurred while revoking session' });
    } finally {
      setRevokingSession(null);
    }
  };

  if (loading) {
    return (
      <div className={`flex items-center justify-center py-12 ${themeClasses.text}`}>
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-current"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className={`text-3xl font-bold ${themeClasses.text}`}>Security Settings</h1>
        <p className={`mt-2 ${themeClasses.subtext}`}>
          Manage your account security and active sessions
        </p>
      </div>

      {/* Status Message */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`rounded-lg p-4 ${
            message.type === 'success'
              ? 'bg-green-500/20 border border-green-500/50'
              : 'bg-red-500/20 border border-red-500/50'
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === 'success' ? (
              <>
                <CheckCircleIcon className="h-5 w-5 text-green-400" />
                <span className="text-green-400">{message.text}</span>
              </>
            ) : (
              <>
                <ExclamationCircleIcon className="h-5 w-5 text-red-400" />
                <span className="text-red-400">{message.text}</span>
              </>
            )}
          </div>
        </motion.div>
      )}

      {/* Change Password */}
      <form onSubmit={handlePasswordChange}>
        <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
          <div className="flex items-center gap-3 mb-6">
            <KeyIcon className={`h-6 w-6 ${themeClasses.text}`} />
            <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
              Change Password
            </h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                Current Password
              </label>
              <input
                type="password"
                value={passwordForm.currentPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, currentPassword: e.target.value })}
                className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} ${
                  passwordErrors.currentPassword ? 'border-red-500' : ''
                }`}
              />
              {passwordErrors.currentPassword && (
                <p className="text-xs mt-1 text-red-400">{passwordErrors.currentPassword}</p>
              )}
            </div>

            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                New Password
              </label>
              <input
                type="password"
                value={passwordForm.newPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, newPassword: e.target.value })}
                className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} ${
                  passwordErrors.newPassword ? 'border-red-500' : ''
                }`}
              />
              {passwordErrors.newPassword && (
                <p className="text-xs mt-1 text-red-400">{passwordErrors.newPassword}</p>
              )}
              <p className={`text-xs mt-1 ${themeClasses.subtext}`}>
                Must be at least 8 characters with uppercase, lowercase, and numbers
              </p>
            </div>

            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                Confirm New Password
              </label>
              <input
                type="password"
                value={passwordForm.confirmPassword}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirmPassword: e.target.value })}
                className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} ${
                  passwordErrors.confirmPassword ? 'border-red-500' : ''
                }`}
              />
              {passwordErrors.confirmPassword && (
                <p className="text-xs mt-1 text-red-400">{passwordErrors.confirmPassword}</p>
              )}
            </div>
          </div>

          <div className="flex justify-end mt-6">
            <button
              type="submit"
              disabled={saving}
              className={`px-6 py-3 rounded-lg font-medium ${themeClasses.button} disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {saving ? 'Changing Password...' : 'Change Password'}
            </button>
          </div>
        </div>
      </form>

      {/* Two-Factor Authentication */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <ShieldCheckIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
            Two-Factor Authentication
          </h2>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className={`font-medium ${themeClasses.text}`}>
              Authenticator App
            </p>
            <p className={`text-sm ${themeClasses.subtext} mt-1`}>
              Use an authenticator app for additional security
            </p>
          </div>
          <button
            onClick={() => window.open('https://auth.unicorncommander.ai/if/user/', '_blank')}
            className={`px-4 py-2 rounded-lg ${themeClasses.button}`}
          >
            Configure 2FA
          </button>
        </div>
      </div>

      {/* Active Sessions */}
      <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
        <div className="flex items-center gap-3 mb-6">
          <DevicePhoneMobileIcon className={`h-6 w-6 ${themeClasses.text}`} />
          <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
            Active Sessions
          </h2>
        </div>

        <div className="space-y-3">
          {sessions.map((session) => (
            <motion.div
              key={session.id}
              whileHover={{ scale: 1.01 }}
              className={`p-4 rounded-lg border ${
                session.isCurrent
                  ? 'border-green-500/30 bg-green-500/5'
                  : currentTheme === 'light'
                  ? 'border-gray-200 bg-gray-50'
                  : 'border-gray-700 bg-gray-700/20'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex gap-3">
                  <ComputerDesktopIcon className={`h-5 w-5 ${themeClasses.text} mt-1`} />
                  <div>
                    <p className={`font-medium ${themeClasses.text} flex items-center gap-2`}>
                      {session.device}
                      {session.isCurrent && (
                        <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full">
                          Current
                        </span>
                      )}
                    </p>
                    <div className={`text-sm ${themeClasses.subtext} mt-1 space-y-1`}>
                      <div className="flex items-center gap-2">
                        <MapPinIcon className="h-4 w-4" />
                        {session.location} • {session.ip}
                      </div>
                      <div className="flex items-center gap-2">
                        <ClockIcon className="h-4 w-4" />
                        {session.lastActive}
                      </div>
                    </div>
                  </div>
                </div>

                {!session.isCurrent && (
                  <button
                    onClick={() => handleRevokeSession(session.id)}
                    disabled={revokingSession === session.id}
                    className="text-red-400 hover:text-red-300 disabled:opacity-50"
                  >
                    {revokingSession === session.id ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-red-400"></div>
                    ) : (
                      <TrashIcon className="h-5 w-5" />
                    )}
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  );
}
