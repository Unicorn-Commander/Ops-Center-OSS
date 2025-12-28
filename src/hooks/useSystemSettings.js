/**
 * System Settings Hook
 * Provides API integration for managing system settings
 */

import { useState, useEffect, useCallback } from 'react';

const useSystemSettings = () => {
  const [settings, setSettings] = useState({});
  const [metadata, setMetadata] = useState({});
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  // Get auth token from localStorage
  const getAuthToken = () => {
    return localStorage.getItem('authToken');
  };

  // Fetch all settings with metadata
  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const token = getAuthToken();
      const response = await fetch('/api/v1/admin/settings', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch settings: ${response.statusText}`);
      }

      const data = await response.json();

      // Organize settings by category
      const settingsByCategory = {};
      const metadataByKey = {};

      data.forEach(setting => {
        const { key, value, category, type, description, options } = setting;

        if (!settingsByCategory[category]) {
          settingsByCategory[category] = {};
        }

        settingsByCategory[category][key] = value;
        metadataByKey[key] = { type, description, options, category };
      });

      setSettings(settingsByCategory);
      setMetadata(metadataByKey);

    } catch (err) {
      console.error('Error fetching settings:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch categories list
  const fetchCategories = useCallback(async () => {
    try {
      const token = getAuthToken();
      const response = await fetch('/api/v1/admin/settings/categories', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch categories: ${response.statusText}`);
      }

      const data = await response.json();
      setCategories(data.categories || []);

    } catch (err) {
      console.error('Error fetching categories:', err);
    }
  }, []);

  // Update single setting
  const updateSetting = async (key, value) => {
    setSaving(true);
    setError(null);

    try {
      const token = getAuthToken();
      const response = await fetch(`/api/v1/admin/settings/${key}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ value })
      });

      if (!response.ok) {
        throw new Error(`Failed to update setting: ${response.statusText}`);
      }

      const data = await response.json();

      // Update local state
      const settingMetadata = metadata[key];
      if (settingMetadata) {
        setSettings(prev => ({
          ...prev,
          [settingMetadata.category]: {
            ...prev[settingMetadata.category],
            [key]: value
          }
        }));
      }

      return data;

    } catch (err) {
      console.error('Error updating setting:', err);
      setError(err.message);
      throw err;
    } finally {
      setSaving(false);
    }
  };

  // Bulk update settings
  const bulkUpdateSettings = async (updates) => {
    setSaving(true);
    setError(null);

    try {
      const token = getAuthToken();
      const response = await fetch('/api/v1/admin/settings/bulk-update', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ settings: updates })
      });

      if (!response.ok) {
        throw new Error(`Failed to bulk update settings: ${response.statusText}`);
      }

      const data = await response.json();

      // Refresh settings after bulk update
      await fetchSettings();

      return data;

    } catch (err) {
      console.error('Error bulk updating settings:', err);
      setError(err.message);
      throw err;
    } finally {
      setSaving(false);
    }
  };

  // Get setting value by key
  const getSetting = (key) => {
    const settingMetadata = metadata[key];
    if (!settingMetadata) return null;

    return settings[settingMetadata.category]?.[key] || null;
  };

  // Get all settings for a category
  const getCategorySettings = (category) => {
    return settings[category] || {};
  };

  // Initialize on mount
  useEffect(() => {
    fetchSettings();
    fetchCategories();
  }, [fetchSettings, fetchCategories]);

  return {
    settings,
    metadata,
    categories,
    loading,
    saving,
    error,
    fetchSettings,
    updateSetting,
    bulkUpdateSettings,
    getSetting,
    getCategorySettings
  };
};

export default useSystemSettings;
