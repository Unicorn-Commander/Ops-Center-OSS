/**
 * Admin Dashboard - Status-focused infrastructure monitoring
 *
 * Redesigned to show real-time status indicators for:
 * - Critical services health (PostgreSQL, Redis, Keycloak, vLLM, Traefik)
 * - GPU status (Tesla P40 detection and memory)
 * - Local inference providers (Ollama, vLLM, llama.cpp)
 * - Billing & credits overview
 * - Hosted websites via Traefik
 * - Service health grid
 * - Recent activity timeline
 */

import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useSystem } from '../../contexts/SystemContext';
import { useTheme } from '../../contexts/ThemeContext';
import { getGlassmorphismStyles } from '../../styles/glassmorphism';

// Dashboard section components
import CriticalServicesCard from '../../components/admin/CriticalServicesCard';
import GPUStatusCard from '../../components/admin/GPUStatusCard';
import LocalInferenceCard from '../../components/admin/LocalInferenceCard';
import BillingOverviewCard from '../../components/admin/BillingOverviewCard';
import HostedWebsitesGrid from '../../components/admin/HostedWebsitesGrid';
import ServiceHealthGrid from '../../components/admin/ServiceHealthGrid';
import ProgressBar from '../../components/admin/ProgressBar';

// Icons
import {
  ComputerDesktopIcon,
  BoltIcon,
  ClockIcon,
  ArrowPathIcon,
  DocumentMagnifyingGlassIcon,
  ArrowDownTrayIcon,
  CloudArrowDownIcon,
  InformationCircleIcon,
  CheckCircleIcon,
  PlayIcon,
  StopIcon,
  ShieldExclamationIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';

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

// Format bytes to human readable
const formatBytes = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Format timestamp to relative time
const formatActivityTime = (timestamp) => {
  if (!timestamp) return 'Unknown time';
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHr = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHr / 24);

    if (diffSec < 60) return `${diffSec}s ago`;
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHr < 24) return `${diffHr}h ago`;
    return `${diffDay}d ago`;
  } catch (e) {
    return 'Unknown time';
  }
};

// Map action types to icons
const getIconForAction = (action) => {
  if (!action) return InformationCircleIcon;
  const actionMap = {
    'auth.login': CheckCircleIcon,
    'service.start': PlayIcon,
    'service.stop': StopIcon,
    'service.restart': ArrowPathIcon,
    'backup': CloudArrowDownIcon,
    'system.update': ArrowDownTrayIcon,
    'model': BoltIcon,
    'log': DocumentMagnifyingGlassIcon,
    'gpu': CpuChipIcon,
  };

  for (const [key, icon] of Object.entries(actionMap)) {
    if (action.toLowerCase().includes(key)) {
      return icon;
    }
  }
  return InformationCircleIcon;
};

export default function AdminDashboard() {
  const { systemData, services, fetchSystemStatus, fetchServices } = useSystem();
  const { theme, currentTheme } = useTheme();

  // State
  const [gpuInfo, setGpuInfo] = useState(null);
  const [gpuLoading, setGpuLoading] = useState(true);
  const [gpuError, setGpuError] = useState(null);

  const [localInference, setLocalInference] = useState(null);
  const [localInferenceLoading, setLocalInferenceLoading] = useState(true);

  const [billingData, setBillingData] = useState(null);
  const [billingLoading, setBillingLoading] = useState(true);

  const [traefikRoutes, setTraefikRoutes] = useState([]);
  const [routesLoading, setRoutesLoading] = useState(true);
  const [websiteStatus, setWebsiteStatus] = useState({});

  const [recentActivity, setRecentActivity] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  // Glassmorphism styles
  const glassStyles = getGlassmorphismStyles(currentTheme);

  // Fetch GPU info
  const fetchGPUInfo = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/gpu-services/status', {
        credentials: 'include'
      });
      if (!response.ok) {
        throw new Error('GPU info not available');
      }
      const data = await response.json();
      // Extract gpu_info from the response (contains gpus array, total_memory_mb, etc.)
      setGpuInfo(data.gpu_info || null);
      setGpuError(null);
    } catch (error) {
      console.debug('GPU info fetch error:', error.message);
      setGpuError('No GPU detected');
    } finally {
      setGpuLoading(false);
    }
  }, []);

  // Fetch local inference status
  const fetchLocalInference = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/local-inference/status', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setLocalInference(data);
      }
    } catch (error) {
      console.debug('Local inference status not available');
    } finally {
      setLocalInferenceLoading(false);
    }
  }, []);

  // Fetch billing dashboard
  const fetchBillingData = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/billing/analytics/dashboard?days=30', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setBillingData({
          balance: data.total_credits || 10000,
          used: data.credits_used || 0,
          limit: data.credits_limit || 10000,
          tier: data.tier || 'professional',
          mrr: data.mrr,
          activeSubscriptions: data.active_subscriptions
        });
      } else {
        // API returned error (403, 500, etc.) - use fallback
        console.debug('Billing API returned', response.status);
        setBillingData({
          balance: 10000,
          used: 0,
          limit: 10000,
          tier: 'professional'
        });
      }
    } catch (error) {
      console.debug('Billing data not available:', error.message);
      // Set fallback data
      setBillingData({
        balance: 10000,
        used: 0,
        limit: 10000,
        tier: 'professional'
      });
    } finally {
      setBillingLoading(false);
    }
  }, []);

  // Fetch Traefik routes (using live API that reads from Docker labels)
  const fetchTraefikRoutes = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/traefik/live/routes', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setTraefikRoutes(data);
      }
    } catch (error) {
      console.debug('Traefik routes not available');
    } finally {
      setRoutesLoading(false);
    }
  }, []);

  // Fetch website health status for Traefik routes
  const fetchWebsiteStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/traefik/live/website-status', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        // Convert to domain -> status map for HostedWebsitesGrid
        const statusMap = {};
        Object.entries(data).forEach(([domain, info]) => {
          statusMap[domain] = info.status; // 'up', 'down', or 'unknown'
        });
        setWebsiteStatus(statusMap);
      }
    } catch (error) {
      console.debug('Website status not available');
    }
  }, []);

  // Fetch recent activity
  const fetchRecentActivity = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/audit/recent?limit=5', {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        const activities = (data.logs || []).map((log) => ({
          id: log.id || log.timestamp,
          message: log.details || log.action || 'System event',
          time: formatActivityTime(log.timestamp),
          icon: getIconForAction(log.action),
          category: log.category || 'system'
        }));
        setRecentActivity(activities);
      }
    } catch (error) {
      console.debug('Audit log not available');
    }
  }, []);

  // Fetch current user
  const fetchCurrentUser = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/auth/user', {
        credentials: 'include'
      });
      if (response.ok) {
        const userData = await response.json();
        setCurrentUser(userData.user || userData);
      }
    } catch (error) {
      console.debug('User info not available');
    }
  }, []);

  // Refresh all data
  const refreshAll = useCallback(async () => {
    setLastChecked(new Date().toLocaleTimeString());
    await Promise.all([
      fetchSystemStatus(),
      fetchServices(),
      fetchGPUInfo(),
      fetchLocalInference(),
      fetchBillingData(),
      fetchTraefikRoutes(),
      fetchWebsiteStatus(),
      fetchRecentActivity()
    ]);
  }, [fetchSystemStatus, fetchServices, fetchGPUInfo, fetchLocalInference, fetchBillingData, fetchTraefikRoutes, fetchWebsiteStatus, fetchRecentActivity]);

  // Initial fetch
  useEffect(() => {
    fetchCurrentUser();
    refreshAll();
  }, []);

  // Polling intervals
  useEffect(() => {
    // Critical services: 10s
    const criticalInterval = setInterval(() => {
      fetchSystemStatus();
      fetchServices();
    }, 10000);

    // GPU: 5s
    const gpuInterval = setInterval(fetchGPUInfo, 5000);

    // Other data: 30s
    const otherInterval = setInterval(() => {
      fetchLocalInference();
      fetchBillingData();
      fetchTraefikRoutes();
      fetchWebsiteStatus();
      fetchRecentActivity();
    }, 30000);

    return () => {
      clearInterval(criticalInterval);
      clearInterval(gpuInterval);
      clearInterval(otherInterval);
    };
  }, [fetchSystemStatus, fetchServices, fetchGPUInfo, fetchLocalInference, fetchBillingData, fetchTraefikRoutes, fetchWebsiteStatus, fetchRecentActivity]);

  // Calculate system status
  const criticalServiceNames = ['vllm', 'open-webui', 'redis', 'postgresql', 'keycloak', 'traefik'];
  const runningServices = services?.filter(s => s?.status === 'running' || s?.status === 'healthy') || [];
  const criticalRunning = services?.filter(s =>
    s?.name && criticalServiceNames.some(cs => s.name.toLowerCase().includes(cs)) &&
    (s?.status === 'running' || s?.status === 'healthy')
  ) || [];

  const getSystemStatus = () => {
    if (!services || services.length === 0) {
      return { text: 'Loading...', color: 'bg-gray-500', status: 'unknown' };
    }
    const criticalDown = criticalServiceNames.length - criticalRunning.length;
    if (criticalDown > 0) {
      return { text: `${criticalDown} Critical Down`, color: 'bg-red-500', status: 'critical' };
    }
    if (runningServices.length === services.length) {
      return { text: 'All Systems Operational', color: 'bg-green-500', status: 'healthy' };
    }
    return { text: 'Degraded Performance', color: 'bg-yellow-500', status: 'degraded' };
  };

  const systemStatus = getSystemStatus();

  // Quick actions handler
  const handleQuickAction = (action) => {
    switch(action) {
      case 'view-logs':
        window.location.href = '/admin/monitoring/logs';
        break;
      case 'refresh':
        refreshAll();
        break;
      case 'gpu-services':
        window.location.href = '/admin/system/gpu-services';
        break;
      case 'traefik':
        window.location.href = '/admin/network/traefik-dashboard';
        break;
    }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-2xl">
              <ComputerDesktopIcon className="h-7 w-7 text-white" />
            </div>
            <div>
              <h1 className={`text-2xl font-bold ${currentTheme === 'unicorn' ? 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400' : 'text-white'}`}>
                {currentUser ? `Welcome back, ${currentUser.firstName || currentUser.username || 'Admin'}` : 'Admin Dashboard'}
              </h1>
              <p className={`${currentTheme === 'unicorn' ? 'text-purple-200/80' : 'text-gray-400'} text-sm`}>
                Infrastructure Status Overview
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => handleQuickAction('refresh')}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              title="Refresh all data"
            >
              <ArrowPathIcon className="h-5 w-5 text-gray-400" />
            </button>
            <div className={`${glassStyles.card} rounded-xl px-4 py-2`}>
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 ${systemStatus.color} rounded-full ${systemStatus.status === 'healthy' ? 'animate-pulse' : ''}`} />
                <span className="text-sm font-medium text-white">{systemStatus.text}</span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* Critical Services - Full Width */}
      <motion.div variants={itemVariants}>
        <CriticalServicesCard
          services={services}
          loading={!services || services.length === 0}
          lastChecked={lastChecked}
          onRefresh={refreshAll}
          glassStyles={glassStyles}
        />
      </motion.div>

      {/* GPU Status + Local Inference - Side by Side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div variants={itemVariants}>
          <GPUStatusCard
            gpuInfo={gpuInfo}
            loading={gpuLoading}
            error={gpuError}
            glassStyles={glassStyles}
          />
        </motion.div>
        <motion.div variants={itemVariants}>
          <LocalInferenceCard
            status={localInference}
            loading={localInferenceLoading}
            glassStyles={glassStyles}
          />
        </motion.div>
      </div>

      {/* Billing Overview - Full Width */}
      <motion.div variants={itemVariants}>
        <BillingOverviewCard
          billingData={billingData}
          loading={billingLoading}
          glassStyles={glassStyles}
        />
      </motion.div>

      {/* Resource Utilization */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}
      >
        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg">
            <CpuChipIcon className="h-5 w-5 text-white" />
          </div>
          Resource Utilization
        </h3>
        <div className="space-y-4">
          <ProgressBar
            value={systemData?.cpu?.percent || 0}
            max={100}
            type="default"
            label="CPU"
            height="md"
          />
          <ProgressBar
            value={systemData?.memory?.used || 0}
            max={systemData?.memory?.total || 1}
            type="default"
            label={`Memory (${formatBytes(systemData?.memory?.used)} / ${formatBytes(systemData?.memory?.total)})`}
            height="md"
          />
          <ProgressBar
            value={systemData?.disk?.used || 0}
            max={systemData?.disk?.total || 1}
            type="storage"
            label={`Storage (${formatBytes(systemData?.disk?.used)} / ${formatBytes(systemData?.disk?.total)})`}
            height="md"
          />
        </div>
      </motion.div>

      {/* Hosted Websites - Full Width */}
      <motion.div variants={itemVariants}>
        <HostedWebsitesGrid
          routes={traefikRoutes}
          websiteStatus={websiteStatus}
          loading={routesLoading}
          glassStyles={glassStyles}
        />
      </motion.div>

      {/* Service Health Grid - Full Width */}
      <motion.div variants={itemVariants}>
        <ServiceHealthGrid
          services={services}
          loading={!services || services.length === 0}
          glassStyles={glassStyles}
        />
      </motion.div>

      {/* Recent Activity Timeline */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}>
        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
            <ClockIcon className="h-5 w-5 text-white" />
          </div>
          Recent Activity
        </h3>
        {recentActivity.length === 0 ? (
          <div className="text-center py-8">
            <InformationCircleIcon className="h-12 w-12 text-gray-500 mx-auto mb-3 opacity-50" />
            <p className="text-sm text-gray-400">No recent activity</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentActivity.map((activity, index) => {
              const ActivityIcon = activity.icon || InformationCircleIcon;
              return (
              <motion.div
                key={activity.id || index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className={`flex items-start gap-4 p-4 rounded-xl backdrop-blur-sm bg-white/5 border border-white/10 hover:bg-white/10 transition-colors`}
              >
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0">
                  <ActivityIcon className="h-5 w-5 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white">{activity.message}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      activity.category === 'auth' ? 'bg-purple-500/20 text-purple-400' :
                      activity.category === 'service' ? 'bg-blue-500/20 text-blue-400' :
                      activity.category === 'billing' ? 'bg-green-500/20 text-green-400' :
                      'bg-gray-500/20 text-gray-400'
                    }`}>
                      {activity.category}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <ClockIcon className="h-3 w-3" />
                      {activity.time}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
            })}
          </div>
        )}
      </motion.div>

      {/* Quick Actions */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-6 shadow-xl`}>
        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
            <BoltIcon className="h-5 w-5 text-white" />
          </div>
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('view-logs')}
            className={`flex flex-col items-center gap-3 p-4 rounded-xl ${glassStyles.card} hover:bg-white/10 transition-colors`}
          >
            <DocumentMagnifyingGlassIcon className="h-6 w-6 text-blue-400" />
            <span className="text-sm font-medium text-white">View Logs</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('gpu-services')}
            className={`flex flex-col items-center gap-3 p-4 rounded-xl ${glassStyles.card} hover:bg-white/10 transition-colors`}
          >
            <CpuChipIcon className="h-6 w-6 text-purple-400" />
            <span className="text-sm font-medium text-white">GPU Services</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('traefik')}
            className={`flex flex-col items-center gap-3 p-4 rounded-xl ${glassStyles.card} hover:bg-white/10 transition-colors`}
          >
            <ShieldExclamationIcon className="h-6 w-6 text-teal-400" />
            <span className="text-sm font-medium text-white">Traefik Dashboard</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('refresh')}
            className={`flex flex-col items-center gap-3 p-4 rounded-xl ${glassStyles.card} hover:bg-white/10 transition-colors`}
          >
            <ArrowPathIcon className="h-6 w-6 text-green-400" />
            <span className="text-sm font-medium text-white">Refresh All</span>
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
