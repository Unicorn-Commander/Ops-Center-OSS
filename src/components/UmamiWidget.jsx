import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useTheme } from '../contexts/ThemeContext';
import { getGlassmorphismStyles } from '../styles/glassmorphism';
import {
  ChartBarIcon,
  EyeIcon,
  UsersIcon,
  ArrowTopRightOnSquareIcon,
  ArrowPathIcon,
  ExclamationCircleIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';

/**
 * UmamiWidget - Compact analytics dashboard widget
 *
 * Displays aggregated Umami analytics data including:
 * - Total pageviews today
 * - Total visitors today
 * - Top 3 websites by traffic
 * - Link to full Umami dashboard
 *
 * Auto-refreshes every 5 minutes
 */
export default function UmamiWidget() {
  const { theme, currentTheme } = useTheme();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Umami dashboard URL
  const UMAMI_DASHBOARD_URL = 'https://analytics.unicorncommander.ai';

  useEffect(() => {
    fetchUmamiData();

    // Auto-refresh every 5 minutes (300000ms)
    const interval = setInterval(fetchUmamiData, 300000);
    return () => clearInterval(interval);
  }, []);

  const fetchUmamiData = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch('/api/v1/umami/dashboard?period=24h', {
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch analytics: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch Umami data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Format large numbers with K/M suffixes
  const formatNumber = (num) => {
    if (!num && num !== 0) return '0';
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toLocaleString();
  };

  // Get top 3 websites by pageviews
  const getTopWebsites = () => {
    if (!data?.websites) return [];

    return data.websites
      .filter(w => w.stats?.pageviews?.value > 0)
      .sort((a, b) => (b.stats?.pageviews?.value || 0) - (a.stats?.pageviews?.value || 0))
      .slice(0, 3);
  };

  const topWebsites = getTopWebsites();

  // Loading state
  if (loading && !data) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
            <ChartBarIcon className="h-6 w-6 text-white" />
          </div>
          <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
            Analytics
          </h3>
        </div>
        <div className="space-y-4">
          <div className="animate-pulse">
            <div className={`h-16 ${currentTheme === 'light' ? 'bg-gray-200' : 'bg-gray-700'} rounded-xl`}></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className={`h-20 ${currentTheme === 'light' ? 'bg-gray-200' : 'bg-gray-700'} rounded-xl animate-pulse`}></div>
            <div className={`h-20 ${currentTheme === 'light' ? 'bg-gray-200' : 'bg-gray-700'} rounded-xl animate-pulse`}></div>
          </div>
        </div>
      </motion.div>
    );
  }

  // Error state
  if (error && !data) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
            <ChartBarIcon className="h-6 w-6 text-white" />
          </div>
          <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
            Analytics
          </h3>
        </div>
        <div className={`flex flex-col items-center justify-center py-8 ${glassStyles.card} rounded-xl`}>
          <ExclamationCircleIcon className="h-12 w-12 text-yellow-500 mb-3" />
          <p className={`text-sm ${theme.text.secondary} text-center mb-4`}>
            Unable to load analytics data
          </p>
          <button
            onClick={fetchUmamiData}
            className="flex items-center gap-2 px-4 py-2 bg-teal-500/20 text-teal-400 rounded-lg hover:bg-teal-500/30 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            Retry
          </button>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
            <ChartBarIcon className="h-6 w-6 text-white" />
          </div>
          <div>
            <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
              Analytics
            </h3>
            {lastUpdated && (
              <p className={`text-xs ${theme.text.secondary}`}>
                Updated {lastUpdated.toLocaleTimeString()}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={fetchUmamiData}
            disabled={loading}
            className={`p-2 rounded-lg ${glassStyles.card} hover:bg-teal-500/20 transition-colors`}
            title="Refresh analytics"
          >
            <ArrowPathIcon className={`h-4 w-4 ${theme.text.secondary} ${loading ? 'animate-spin' : ''}`} />
          </button>
          <a
            href={UMAMI_DASHBOARD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className={`p-2 rounded-lg ${glassStyles.card} hover:bg-teal-500/20 transition-colors`}
            title="Open Umami Dashboard"
          >
            <ArrowTopRightOnSquareIcon className={`h-4 w-4 ${theme.text.secondary}`} />
          </a>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        {/* Pageviews Today */}
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`${glassStyles.card} rounded-xl p-4 border-l-4 border-teal-500`}
        >
          <div className="flex items-center gap-2 mb-2">
            <EyeIcon className="h-5 w-5 text-teal-500" />
            <span className={`text-xs font-medium ${theme.text.secondary}`}>Pageviews Today</span>
          </div>
          <p className={`text-2xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
            {formatNumber(data?.totals?.pageviews || 0)}
          </p>
        </motion.div>

        {/* Visitors Today */}
        <motion.div
          whileHover={{ scale: 1.02 }}
          className={`${glassStyles.card} rounded-xl p-4 border-l-4 border-cyan-500`}
        >
          <div className="flex items-center gap-2 mb-2">
            <UsersIcon className="h-5 w-5 text-cyan-500" />
            <span className={`text-xs font-medium ${theme.text.secondary}`}>Visitors Today</span>
          </div>
          <p className={`text-2xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
            {formatNumber(data?.totals?.visitors || 0)}
          </p>
        </motion.div>
      </div>

      {/* Top Websites */}
      <div className="mb-4">
        <h4 className={`text-sm font-semibold ${theme.text.secondary} mb-3 flex items-center gap-2`}>
          <GlobeAltIcon className="h-4 w-4" />
          Top Websites (24h)
        </h4>

        {topWebsites.length > 0 ? (
          <div className="space-y-2">
            {topWebsites.map((website, index) => (
              <motion.div
                key={website.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`${glassStyles.card} rounded-lg p-3 flex items-center justify-between`}
              >
                <div className="flex items-center gap-3">
                  <span className={`w-6 h-6 flex items-center justify-center rounded-full text-xs font-bold ${
                    index === 0 ? 'bg-yellow-500/20 text-yellow-400' :
                    index === 1 ? 'bg-gray-400/20 text-gray-300' :
                    'bg-amber-700/20 text-amber-600'
                  }`}>
                    {index + 1}
                  </span>
                  <div>
                    <p className={`text-sm font-medium ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} truncate max-w-[120px]`}>
                      {website.name || website.domain}
                    </p>
                    <p className={`text-xs ${theme.text.secondary} truncate max-w-[120px]`}>
                      {website.domain}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-teal-400' : 'text-teal-500'}`}>
                    {formatNumber(website.stats?.pageviews?.value || 0)}
                  </p>
                  <p className={`text-xs ${theme.text.secondary}`}>
                    views
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className={`${glassStyles.card} rounded-lg p-4 text-center`}>
            <p className={`text-sm ${theme.text.secondary}`}>
              No website data available
            </p>
          </div>
        )}
      </div>

      {/* Summary Row */}
      <div className={`${glassStyles.card} rounded-lg p-3 flex items-center justify-between`}>
        <div className="flex items-center gap-4">
          <div className="text-center">
            <p className={`text-xs ${theme.text.secondary}`}>Sites</p>
            <p className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
              {data?.totals?.websites_count || 0}
            </p>
          </div>
          <div className="h-8 w-px bg-gray-600/30"></div>
          <div className="text-center">
            <p className={`text-xs ${theme.text.secondary}`}>Visits</p>
            <p className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
              {formatNumber(data?.totals?.visits || 0)}
            </p>
          </div>
        </div>
        <a
          href={UMAMI_DASHBOARD_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-cyan-500 text-white rounded-lg text-sm font-medium hover:from-teal-600 hover:to-cyan-600 transition-all shadow-lg hover:shadow-xl"
        >
          Full Dashboard
          <ArrowTopRightOnSquareIcon className="h-4 w-4" />
        </a>
      </div>
    </motion.div>
  );
}
