import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import {
  CheckCircleIcon,
  ServerIcon,
  ArrowTopRightOnSquareIcon,
  Cog6ToothIcon,
  XCircleIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { getGlassmorphismStyles } from '../styles/glassmorphism';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';

// Animation variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

export default function MyApps() {
  const { theme, currentTheme } = useTheme();
  const toast = useToast();
  const glassStyles = getGlassmorphismStyles(currentTheme);

  const [loading, setLoading] = useState(true);
  const [activeServices, setActiveServices] = useState([]);

  // Mock active apps - will be replaced with API call
  const MOCK_ACTIVE_SERVICES = [
    {
      id: 'chat',
      name: 'AI Chat (Open-WebUI)',
      description: 'Advanced conversational AI interface',
      status: 'Active',
      access_url: 'https://chat.unicorncommander.ai',
      icon_url: null,
      gradient: 'from-blue-500 to-cyan-500',
      last_used: '2 hours ago',
      usage_this_month: '1,240 requests'
    },
    {
      id: 'search',
      name: 'AI Search (Magic Unicorn)',
      description: 'Privacy-focused AI metasearch',
      status: 'Active',
      access_url: 'https://search.unicorncommander.ai',
      icon_url: null,
      gradient: 'from-purple-500 to-pink-500',
      last_used: '1 day ago',
      usage_this_month: '3 searches'
    }
  ];

  useEffect(() => {
    loadActiveServices();
  }, []);

  const loadActiveServices = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/user/apps/active', { credentials: 'include' });
      // const data = await response.json();
      // setActiveServices(data.services);

      // Mock data for now
      setActiveServices(MOCK_ACTIVE_SERVICES);
    } catch (error) {
      console.error('Failed to load active apps:', error);
      toast.error('Failed to load your services');
      setActiveServices(MOCK_ACTIVE_SERVICES); // Fallback
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className={theme.text.secondary}>Loading your services...</p>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 pb-20"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-2xl`}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center shadow-xl">
                <CheckCircleIcon className="h-6 w-6 text-white" />
              </div>
              <h1 className={`text-3xl font-bold ${currentTheme === 'unicorn' ? 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400' : theme.text.primary}`}>
                My Active Apps
              </h1>
            </div>
            <p className={`${currentTheme === 'unicorn' ? 'text-purple-200/80' : theme.text.secondary} text-base`}>
              Manage and access your subscribed services
            </p>
          </div>

          {/* Add Services button */}
          <Link
            to="/apps"
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
          >
            <PlusIcon className="h-5 w-5" />
            Browse Apps
          </Link>
        </div>
      </motion.div>

      {/* Active Apps Grid */}
      {activeServices.length === 0 ? (
        <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-12 text-center`}>
          <ServerIcon className={`h-16 w-16 ${theme.text.secondary} mx-auto mb-4 opacity-50`} />
          <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
            No Active Apps
          </h3>
          <p className={`${theme.text.secondary} mb-6`}>
            You don't have any active apps yet. Browse our app marketplace to get started.
          </p>
          <Link
            to="/apps"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl"
          >
            <PlusIcon className="h-5 w-5" />
            Browse Apps
          </Link>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {activeServices.map((service) => (
            <motion.div
              key={service.id}
              variants={itemVariants}
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} rounded-2xl overflow-hidden shadow-xl`}
            >
              {/* Service Header */}
              <div className={`h-32 bg-gradient-to-br ${service.gradient} flex items-center justify-center relative overflow-hidden`}>
                {service.icon_url ? (
                  <img
                    src={service.icon_url}
                    alt={service.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <ServerIcon className="h-16 w-16 text-white opacity-90" />
                )}

                {/* Status badge */}
                <div className="absolute top-3 right-3 bg-green-500 text-white px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1">
                  <CheckCircleIcon className="h-3 w-3" />
                  {service.status}
                </div>
              </div>

              {/* Service Content */}
              <div className="p-6">
                <h3 className={`text-xl font-bold ${theme.text.primary} mb-2`}>
                  {service.name}
                </h3>
                <p className={`text-sm ${theme.text.secondary} mb-4`}>
                  {service.description}
                </p>

                {/* Usage Stats */}
                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className={`${glassStyles.card} rounded-lg p-3`}>
                    <div className={`text-xs ${theme.text.secondary} mb-1`}>Last Used</div>
                    <div className={`text-sm font-bold ${theme.text.primary}`}>
                      {service.last_used}
                    </div>
                  </div>
                  <div className={`${glassStyles.card} rounded-lg p-3`}>
                    <div className={`text-xs ${theme.text.secondary} mb-1`}>This Month</div>
                    <div className={`text-sm font-bold ${theme.text.primary}`}>
                      {service.usage_this_month}
                    </div>
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <a
                    href={service.access_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-3 px-4 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
                  >
                    Open {service.name.split(' ')[0]}
                    <ArrowTopRightOnSquareIcon className="h-5 w-5" />
                  </a>
                  <button
                    onClick={() => toast.info('Service settings coming soon')}
                    className={`py-3 px-4 ${glassStyles.card} hover:bg-white/10 rounded-lg transition-colors flex items-center justify-center`}
                    title="Service Settings"
                  >
                    <Cog6ToothIcon className={`h-5 w-5 ${theme.text.secondary}`} />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* Quick Links */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}>
        <h3 className={`text-lg font-bold ${theme.text.primary} mb-4`}>
          Quick Links
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/apps"
            className={`p-4 ${glassStyles.card} rounded-lg hover:bg-white/10 transition-colors flex items-center gap-3`}
          >
            <PlusIcon className={`h-6 w-6 ${theme.text.accent}`} />
            <div>
              <div className={`font-semibold ${theme.text.primary}`}>Browse Apps</div>
              <div className={`text-xs ${theme.text.secondary}`}>Discover new apps</div>
            </div>
          </Link>

          <Link
            to="/admin/subscription/usage"
            className={`p-4 ${glassStyles.card} rounded-lg hover:bg-white/10 transition-colors flex items-center gap-3`}
          >
            <CheckCircleIcon className={`h-6 w-6 ${theme.text.accent}`} />
            <div>
              <div className={`font-semibold ${theme.text.primary}`}>Usage & Limits</div>
              <div className={`text-xs ${theme.text.secondary}`}>Track your usage</div>
            </div>
          </Link>

          <Link
            to="/admin/subscription/billing"
            className={`p-4 ${glassStyles.card} rounded-lg hover:bg-white/10 transition-colors flex items-center gap-3`}
          >
            <Cog6ToothIcon className={`h-6 w-6 ${theme.text.accent}`} />
            <div>
              <div className={`font-semibold ${theme.text.primary}`}>Billing & Payment</div>
              <div className={`text-xs ${theme.text.secondary}`}>Manage subscription</div>
            </div>
          </Link>
        </div>
      </motion.div>
    </motion.div>
  );
}
