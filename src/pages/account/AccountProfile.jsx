/**
 * AccountProfile Component
 *
 * Personal information management for user accounts
 * - View and edit name, username, email
 * - Avatar/profile picture upload
 * - Form validation and error handling
 * - Success/error messaging
 *
 * API Endpoints:
 * - GET /api/v1/auth/session - Load current user data
 * - PUT /api/v1/auth/profile - Update profile information
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  UserCircleIcon,
  EnvelopeIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  PhotoIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../../contexts/ThemeContext';

export default function AccountProfile() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState(null);
  const [errors, setErrors] = useState({});

  const [profile, setProfile] = useState({
    username: '',
    name: '',
    email: '',
    avatar: null,
    role: ''
  });

  const [avatarPreview, setAvatarPreview] = useState(null);

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
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      const response = await fetch('/api/v1/auth/session');
      if (response.ok) {
        const data = await response.json();
        if (data.user) {
          setProfile({
            username: data.user.username || '',
            name: data.user.name || '',
            email: data.user.email || '',
            avatar: data.user.avatar || null,
            role: data.user.role || 'viewer'
          });
          if (data.user.avatar) {
            setAvatarPreview(data.user.avatar);
          }
        }
      }
    } catch (error) {
      console.error('Failed to load profile:', error);
      setMessage({ type: 'error', text: 'Failed to load profile information' });
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!profile.name.trim()) {
      newErrors.name = 'Name is required';
    }

    if (!profile.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(profile.email)) {
      newErrors.email = 'Invalid email format';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 2 * 1024 * 1024) {
        setMessage({ type: 'error', text: 'Avatar must be less than 2MB' });
        return;
      }

      if (!file.type.startsWith('image/')) {
        setMessage({ type: 'error', text: 'File must be an image' });
        return;
      }

      const reader = new FileReader();
      reader.onloadend = () => {
        setAvatarPreview(reader.result);
        setProfile({ ...profile, avatar: file });
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const formData = new FormData();
      formData.append('name', profile.name);
      formData.append('email', profile.email);
      if (profile.avatar instanceof File) {
        formData.append('avatar', profile.avatar);
      }

      const response = await fetch('/api/v1/auth/profile', {
        method: 'PUT',
        body: formData
      });

      if (response.ok) {
        setMessage({ type: 'success', text: 'Profile updated successfully' });
        setTimeout(() => setMessage(null), 3000);
      } else {
        const error = await response.json();
        setMessage({ type: 'error', text: error.detail || 'Failed to update profile' });
      }
    } catch (error) {
      console.error('Failed to update profile:', error);
      setMessage({ type: 'error', text: 'An error occurred while updating profile' });
    } finally {
      setSaving(false);
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
        <h1 className={`text-3xl font-bold ${themeClasses.text}`}>Profile Settings</h1>
        <p className={`mt-2 ${themeClasses.subtext}`}>
          Update your personal information and profile picture
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

      {/* Profile Form */}
      <form onSubmit={handleSubmit}>
        <div className={`rounded-xl border p-6 ${themeClasses.card}`}>
          <div className="flex items-center gap-3 mb-6">
            <UserCircleIcon className={`h-6 w-6 ${themeClasses.text}`} />
            <h2 className={`text-xl font-semibold ${themeClasses.text}`}>
              Personal Information
            </h2>
          </div>

          <div className="space-y-6">
            {/* Avatar Upload */}
            <div className="flex items-center gap-6">
              <div className="relative">
                {avatarPreview ? (
                  <img
                    src={avatarPreview}
                    alt="Profile"
                    className="w-24 h-24 rounded-full object-cover border-4 border-white/10"
                  />
                ) : (
                  <div className={`w-24 h-24 rounded-full ${themeClasses.input} flex items-center justify-center border-4 border-white/10`}>
                    <UserCircleIcon className={`h-12 w-12 ${themeClasses.subtext}`} />
                  </div>
                )}
                <label
                  htmlFor="avatar-upload"
                  className="absolute bottom-0 right-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center cursor-pointer hover:bg-blue-700 transition-colors"
                >
                  <PhotoIcon className="h-4 w-4 text-white" />
                  <input
                    id="avatar-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                  />
                </label>
              </div>
              <div>
                <p className={`font-medium ${themeClasses.text}`}>Profile Picture</p>
                <p className={`text-sm ${themeClasses.subtext} mt-1`}>
                  Upload a profile picture (max 2MB)
                </p>
              </div>
            </div>

            {/* Username (Read-only) */}
            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                Username
              </label>
              <input
                type="text"
                value={profile.username}
                disabled
                className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} opacity-60 cursor-not-allowed`}
              />
              <p className={`text-xs mt-1 ${themeClasses.subtext}`}>
                Username cannot be changed
              </p>
            </div>

            {/* Full Name */}
            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                Full Name *
              </label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} ${
                  errors.name ? 'border-red-500' : ''
                }`}
                placeholder="Enter your full name"
              />
              {errors.name && (
                <p className="text-xs mt-1 text-red-400">{errors.name}</p>
              )}
            </div>

            {/* Email Address */}
            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                Email Address *
              </label>
              <div className="relative">
                <EnvelopeIcon className={`absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 ${themeClasses.subtext}`} />
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  className={`w-full pl-10 pr-4 py-2 rounded-lg border ${themeClasses.input} ${
                    errors.email ? 'border-red-500' : ''
                  }`}
                  placeholder="your@email.com"
                />
              </div>
              {errors.email && (
                <p className="text-xs mt-1 text-red-400">{errors.email}</p>
              )}
            </div>

            {/* Role (Read-only) */}
            <div>
              <label className={`block text-sm font-medium mb-2 ${themeClasses.text}`}>
                Account Role
              </label>
              <input
                type="text"
                value={profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
                disabled
                className={`w-full px-4 py-2 rounded-lg border ${themeClasses.input} opacity-60 cursor-not-allowed`}
              />
              <p className={`text-xs mt-1 ${themeClasses.subtext}`}>
                Contact support to change your role
              </p>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="flex justify-end mt-6">
          <button
            type="submit"
            disabled={saving}
            className={`px-6 py-3 rounded-lg font-medium ${themeClasses.button} disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2`}
          >
            {saving ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                Saving...
              </>
            ) : (
              <>
                <CheckCircleIcon className="h-5 w-5" />
                Save Changes
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
