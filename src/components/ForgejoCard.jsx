import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';

const StatusDot = ({ online }) => {
  const color = online ? 'bg-green-500' : 'bg-red-500';

  return (
    <span className="relative flex h-3 w-3">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${color} opacity-75`}></span>
      <span className={`relative inline-flex rounded-full h-3 w-3 ${color}`}></span>
    </span>
  );
};

export default function ForgejoCard() {
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    fetchForgejoData();

    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchForgejoData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchForgejoData = async () => {
    try {
      const [healthRes, statsRes] = await Promise.all([
        axios.get('/api/v1/forgejo/health'),
        axios.get('/api/v1/forgejo/stats')
      ]);

      setHealth(healthRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch Forgejo data:', error);
      setHealth({ online: false, status: 'offline' });
    } finally {
      setLoading(false);
    }
  };

  const openForgejo = () => {
    if (health?.url) {
      window.open(health.url, '_blank');
    }
  };

  const openAdmin = (e) => {
    e.stopPropagation();
    // Navigate to Forgejo admin page (internal route)
    window.location.href = '/admin/forgejo';
  };

  return (
    <motion.div
      className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 cursor-pointer"
      whileHover={{ y: -4 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={openForgejo}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="text-4xl">
            {/* Git branch icon */}
            <svg className="w-10 h-10 text-purple-600" fill="currentColor" viewBox="0 0 24 24">
              <path d="M21.71 9.29l-4-4a1 1 0 00-1.42 0l-4 4a1 1 0 001.42 1.42L16 8.41V15a3 3 0 01-3 3H9.41l2.3-2.29a1 1 0 00-1.42-1.42l-4 4a1 1 0 000 1.42l4 4a1 1 0 001.42-1.42L9.41 20H13a5 5 0 005-5V8.41l2.29 2.3a1 1 0 001.42-1.42z"/>
            </svg>
          </div>
          {loading ? (
            <div className="animate-spin rounded-full h-3 w-3 border-2 border-purple-500 border-t-transparent"></div>
          ) : (
            <StatusDot online={health?.online} />
          )}
        </div>

        {/* Content */}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          Forgejo Git Server
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Self-hosted Git platform for repositories and collaboration
        </p>

        {/* Metrics */}
        {!loading && stats && (
          <div className="grid grid-cols-2 gap-2 text-xs mb-4">
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded px-2 py-1 border border-purple-200 dark:border-purple-800">
              <span className="text-purple-600 dark:text-purple-400">Organizations:</span>
              <span className="ml-1 font-medium text-purple-800 dark:text-purple-200">
                {stats.total_organizations || 0}
              </span>
            </div>
            <div className="bg-purple-50 dark:bg-purple-900/20 rounded px-2 py-1 border border-purple-200 dark:border-purple-800">
              <span className="text-purple-600 dark:text-purple-400">Repositories:</span>
              <span className="ml-1 font-medium text-purple-800 dark:text-purple-200">
                {stats.total_repositories || 0}
              </span>
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="grid grid-cols-2 gap-2 text-xs mb-4">
            <div className="bg-gray-100 dark:bg-gray-700 rounded px-2 py-1 animate-pulse h-8"></div>
            <div className="bg-gray-100 dark:bg-gray-700 rounded px-2 py-1 animate-pulse h-8"></div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center">
          <button
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm font-medium"
            onClick={openForgejo}
            disabled={!health?.online}
          >
            {health?.online ? 'Open Forgejo' : 'Offline'}
          </button>

          {isHovered && health?.online && (
            <div className="flex gap-2">
              <button
                onClick={openAdmin}
                className="p-2 text-purple-600 hover:text-purple-900 dark:text-purple-400 dark:hover:text-purple-200 transition-colors"
                title="Admin Settings"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Status indicator */}
      <div className="bg-purple-50 dark:bg-purple-900/20 px-6 py-2 text-xs border-t border-purple-200 dark:border-purple-800">
        <div className="flex items-center justify-between">
          <span className="text-purple-600 dark:text-purple-400">
            {health?.online ? 'Online' : 'Offline'}
            {health?.version && ` • v${health.version}`}
          </span>
          <span className="text-purple-600 dark:text-purple-400">
            Port: {health?.port || '3000'}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
