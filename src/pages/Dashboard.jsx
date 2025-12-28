import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useSystem } from '../contexts/SystemContext';
import { useTheme } from '../contexts/ThemeContext';
import { ServiceLogos, getServiceInfo } from '../components/ServiceLogos';
import { EnhancedServiceLogos, EnhancedServiceCard, getEnhancedServiceInfo } from '../components/EnhancedServiceLogos';
import UpdateModal from '../components/UpdateModal';
import { getGlassmorphismStyles, getResourceColor, getServiceColorScheme } from '../styles/glassmorphism';
// Safe utilities for defensive rendering (Phase 3 refactoring)
import { safeMap, safeFilter, safeFind, safeGet } from '../utils/safeArrayUtils';
import { safeToFixed, safePercent, safeNumber } from '../utils/safeNumberUtils';
import {
  CpuChipIcon,
  ServerStackIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ClockIcon,
  BoltIcon,
  ArrowPathIcon,
  TrashIcon,
  ChartBarIcon,
  CloudArrowDownIcon,
  ShieldExclamationIcon,
  FireIcon,
  ComputerDesktopIcon,
  InformationCircleIcon,
  ArrowTopRightOnSquareIcon,
  Cog6ToothIcon,
  PlayIcon,
  StopIcon,
  DocumentMagnifyingGlassIcon,
  ArrowDownTrayIcon,
  WrenchScrewdriverIcon,
  ArrowRightIcon,
  SparklesIcon,
  MagnifyingGlassIcon,
  CubeIcon
} from '@heroicons/react/24/outline';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.3
    }
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

// Format uptime
const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h ${minutes}m`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

// Service Modal Component
const ServiceModal = ({ service, isOpen, onClose, theme }) => {
  if (!isOpen) return null;
  
  const serviceInfo = getServiceInfo(service.name);
  const currentHost = window.location.hostname;
  
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50" onClick={onClose}>
      <motion.div 
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`${theme.card} rounded-xl p-6 max-w-md w-full m-4`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-4 mb-4">
          <div className={`${serviceInfo.color} p-3 rounded-lg`}>
            {serviceInfo.logo}
          </div>
          <div className="flex-1">
            <h3 className={`text-lg font-semibold ${theme.text.primary}`}>{serviceInfo.name}</h3>
            <p className={`text-sm ${theme.text.secondary}`}>{serviceInfo.description}</p>
            <div className={`text-xs ${theme.text.accent} mt-1`}>
              Status: {service.status}
            </div>
          </div>
        </div>
        
        <div className="space-y-3">
          {/* Service Actions */}
          <div className="flex gap-2">
            {service.status === 'running' ? (
              <button className="flex-1 flex items-center justify-center gap-2 p-2 bg-red-500/20 text-red-400 rounded-lg hover:bg-red-500/30">
                <StopIcon className="h-4 w-4" />
                Stop
              </button>
            ) : (
              <button className="flex-1 flex items-center justify-center gap-2 p-2 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30">
                <PlayIcon className="h-4 w-4" />
                Start
              </button>
            )}
            <button className="flex-1 flex items-center justify-center gap-2 p-2 bg-yellow-500/20 text-yellow-400 rounded-lg hover:bg-yellow-500/30">
              <ArrowPathIcon className="h-4 w-4" />
              Restart
            </button>
          </div>
          
          {/* GUI Links */}
          {serviceInfo.hasGUI && (
            <a 
              href={`http://${currentHost}:${serviceInfo.guiPort}`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2 p-3 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 w-full"
            >
              <ArrowTopRightOnSquareIcon className="h-4 w-4" />
              Open {serviceInfo.name} Interface
            </a>
          )}
          
          {/* API Endpoint */}
          {serviceInfo.apiPort && (
            <div className={`p-3 bg-gray-500/10 rounded-lg`}>
              <div className={`text-xs ${theme.text.secondary} mb-1`}>API Endpoint:</div>
              <code className={`text-xs ${theme.text.primary}`}>
                http://{currentHost}:{serviceInfo.apiPort}
              </code>
            </div>
          )}
          
          {/* View Logs */}
          <button className="flex items-center justify-center gap-2 p-3 bg-gray-500/20 text-gray-400 rounded-lg hover:bg-gray-500/30 w-full">
            <DocumentMagnifyingGlassIcon className="h-4 w-4" />
            View Logs
          </button>
        </div>
        
        <button 
          onClick={onClose}
          className={`mt-4 w-full p-2 ${theme.button} rounded-lg`}
        >
          Close
        </button>
      </motion.div>
    </div>
  );
};

// Feature to service mapping - controls which services are visible based on user's tier features
const FEATURE_SERVICE_MAP = {
  chat_access: ['webui', 'openwebui'],
  search_enabled: ['searxng', 'centerdeep'],
  tts_enabled: ['tts', 'orator'],
  stt_enabled: ['whisperx', 'amanuensis'],
  billing_dashboard: ['lago'],
  litellm_access: ['litellm', 'vllm'],
  brigade_access: ['brigade'],
  bolt_access: ['bolt'],
  presenton_access: ['presenton'],
  // Infrastructure services always visible
  _base_services: ['redis', 'postgresql', 'qdrant', 'embeddings', 'reranker']
};

export default function Dashboard() {
  const { systemData, services, fetchSystemStatus, fetchServices } = useSystem();
  const { theme, currentTheme } = useTheme();
  const [alerts, setAlerts] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [hardwareInfo, setHardwareInfo] = useState(null);
  const [serviceViewMode, setServiceViewMode] = useState('cards'); // cards, circles, list
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [userFeatures, setUserFeatures] = useState([]);
  const [loadingFeatures, setLoadingFeatures] = useState(true);

  // Get glassmorphism styles based on current theme
  const glassStyles = getGlassmorphismStyles(currentTheme);
  
  useEffect(() => {
    // Fetch initial data
    fetchSystemStatus();
    fetchServices();
    fetchHardwareInfo();
    fetchCurrentUser();
    fetchRecentActivity();
    loadUserFeatures();

    // Set up polling
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchServices();
    }, 5000);

    // Refresh activity every 30 seconds
    const activityInterval = setInterval(fetchRecentActivity, 30000);

    return () => {
      clearInterval(interval);
      clearInterval(activityInterval);
    };
  }, []);

  // Load user features to control service visibility
  const loadUserFeatures = async () => {
    try {
      // Get current user
      let user = {};
      try {
        user = JSON.parse(localStorage.getItem('user') || '{}');
      } catch (e) {
        console.error('Failed to parse user from localStorage:', e);
      }

      // Admin users see all services
      if (user.role === 'admin') {
        setUserFeatures([]);
        setLoadingFeatures(false);
        return;
      }

      // If no tier, user sees base services only
      if (!user.subscription_tier) {
        setUserFeatures([]);
        setLoadingFeatures(false);
        return;
      }

      // Fetch features for user's tier
      const response = await fetch(`/api/v1/tiers/${user.subscription_tier}/features`, {
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        // Extract feature keys from the response
        const featureKeys = (data.features || [])
          .filter(f => f != null && f.feature_key)
          .map(f => f.feature_key);
        setUserFeatures(featureKeys);
      }
    } catch (error) {
      console.error('Error loading user features:', error);
      // On error, show base services only (fail-safe)
      setUserFeatures([]);
    } finally {
      setLoadingFeatures(false);
    }
  };
  
  // Fetch hardware information
  const fetchHardwareInfo = async () => {
    try {
      const response = await fetch('/api/v1/system/hardware');
      if (!response.ok) throw new Error('Failed to fetch hardware info');
      const data = await response.json();
      setHardwareInfo(data);
    } catch (error) {
      console.error('Failed to fetch hardware info:', error);
      // Fallback to mock data if API fails
      setHardwareInfo({
        cpu: {
          model: 'Unknown CPU',
          cores: 0,
          threads: 0,
          baseFreq: 'Unknown',
          maxFreq: 'Unknown'
        },
        gpu: {
          model: 'GPU detection failed',
          vram: 'Unknown',
          driver: 'Unknown',
          cuda: 'Unknown'
        },
        igpu: {
          model: 'Unknown iGPU',
          driver: 'Unknown'
        },
        memory: {
          total: 'Unknown',
          type: 'Unknown',
          slots: 'Unknown'
        },
        storage: {
          primary: 'Unknown',
          secondary: 'Unknown'
        },
        os: {
          name: 'Unknown OS',
          version: 'Unknown',
          kernel: 'Unknown',
          desktop: 'Unknown'
        }
      });
    }
  };

  // Fetch current user information
  const fetchCurrentUser = async () => {
    try {
      const response = await fetch('/api/v1/auth/user', {
        credentials: 'include'
      });
      if (response.ok) {
        const userData = await response.json();
        const user = userData.user || userData;
        setCurrentUser(user);
        // Also store in localStorage for feature checking
        localStorage.setItem('user', JSON.stringify(user));
      }
    } catch (error) {
      console.error('Failed to fetch current user:', error);
    }
  };

  // Filter services based on user features
  const getVisibleServices = () => {
    // Admin users see all services
    if (currentUser?.role === 'admin') {
      return Object.keys(EnhancedServiceLogos);
    }

    // If features still loading, show base services only
    if (loadingFeatures) {
      return FEATURE_SERVICE_MAP._base_services;
    }

    // If user has no features, show base services only
    if (userFeatures.length === 0) {
      return FEATURE_SERVICE_MAP._base_services;
    }

    // Build list of visible services based on enabled features
    const visibleServices = new Set(FEATURE_SERVICE_MAP._base_services);

    userFeatures.forEach(featureKey => {
      const services = FEATURE_SERVICE_MAP[featureKey];
      if (services) {
        services.forEach(service => visibleServices.add(service));
      }
    });

    return Array.from(visibleServices);
  };

  const visibleServiceKeys = getVisibleServices();

  // Fetch recent activity from audit logs
  const fetchRecentActivity = async () => {
    try {
      const response = await fetch('/api/v1/audit/recent?limit=5', {
        credentials: 'include'
      });

      if (!response.ok) {
        console.debug('No recent activity available');
        setRecentActivity([]);
        return;
      }

      const data = await response.json();

      // Map icon strings to actual icon components
      const iconMap = {
        'CheckCircleIcon': CheckCircleIcon,
        'BoltIcon': BoltIcon,
        'CloudArrowDownIcon': CloudArrowDownIcon,
        'CpuChipIcon': CpuChipIcon,
        'DocumentMagnifyingGlassIcon': DocumentMagnifyingGlassIcon,
        'PlayIcon': PlayIcon,
        'StopIcon': StopIcon,
        'ArrowPathIcon': ArrowPathIcon,
        'ArrowDownTrayIcon': ArrowDownTrayIcon,
        'InformationCircleIcon': InformationCircleIcon
      };

      // Transform API response to component format
      // REFACTORED: Using safeMap to prevent crashes on malformed API data
      const activities = safeMap(data.logs || [], (log) => ({
        id: log.id || log.timestamp,
        message: log.details || log.action || 'System event',
        time: formatActivityTime(log.timestamp),
        icon: iconMap[getIconForAction(log.action)] || InformationCircleIcon
      }));

      setRecentActivity(activities);

    } catch (error) {
      console.error('Failed to fetch recent activity:', error);
      setRecentActivity([]);
    }
  };

  // Helper: Format timestamp to relative time
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

  // Helper: Map action types to icons
  const getIconForAction = (action) => {
    if (!action) return 'InformationCircleIcon';
    const actionMap = {
      'auth.login': 'CheckCircleIcon',
      'service.start': 'PlayIcon',
      'service.stop': 'StopIcon',
      'service.restart': 'ArrowPathIcon',
      'backup': 'CloudArrowDownIcon',
      'system.update': 'ArrowDownTrayIcon',
      'model': 'BoltIcon',
      'log': 'DocumentMagnifyingGlassIcon',
      'gpu': 'CpuChipIcon',
    };

    for (const [key, iconName] of Object.entries(actionMap)) {
      if (action.toLowerCase().includes(key)) {
        return iconName;
      }
    }

    return 'InformationCircleIcon';
  };
  
  useEffect(() => {
    // Generate alerts based on system state
    // REFACTORED: Using safe utilities to prevent undefined crashes
    const newAlerts = [];

    const memPercent = safeNumber(systemData?.memory?.percent);
    if (memPercent > 85) {
      newAlerts.push({
        id: 'mem-high',
        type: 'warning',
        message: `Memory usage high: ${safeToFixed(memPercent, 1)}%`,
        icon: ExclamationTriangleIcon
      });
    }

    const cpuPercent = safeNumber(systemData?.cpu?.percent);
    if (cpuPercent > 85) {
      newAlerts.push({
        id: 'cpu-high',
        type: 'warning',
        message: `CPU usage high: ${safeToFixed(cpuPercent, 1)}%`,
        icon: ExclamationTriangleIcon
      });
    }

    // Check for stopped critical services - using safeFilter to prevent crashes
    const criticalServiceNames = ['vllm', 'open-webui', 'redis', 'postgresql'];
    safeFilter(services, (service) => {
      return service?.name && service.status !== 'running' && criticalServiceNames.includes(service.name);
    }).forEach(service => {
      newAlerts.push({
        id: `service-${service.name}`,
        type: 'error',
        message: `Critical service ${service.name} is ${service.status}`,
        icon: ShieldExclamationIcon
      });
    });

    setAlerts(newAlerts);
  }, [systemData, services]);
  
  // Removed simulated activity - now fetches real audit log data
  
  const gpuUsage = systemData?.gpu?.[0]?.utilization || 0;
  const vramUsed = systemData?.gpu?.[0]?.memory_used || 0;
  const vramTotal = systemData?.gpu?.[0]?.memory_total || 33554432000; // 32GB default
  const vramPercent = (vramUsed / vramTotal) * 100;

  // Calculate system status dynamically
  const criticalServices = ['vllm', 'open-webui', 'redis', 'postgresql', 'keycloak'];
  const runningServices = services?.filter(s => s?.status === 'running' || s?.status === 'healthy') || [];
  const criticalRunning = services?.filter(s =>
    s?.name && criticalServices.some(cs => s.name.includes(cs)) &&
    (s?.status === 'running' || s?.status === 'healthy')
  ) || [];

  const getSystemStatus = () => {
    if (!services || services.length === 0) {
      return { text: 'Loading...', color: 'bg-gray-500', status: 'unknown' };
    }

    const criticalDown = criticalServices.length - criticalRunning.length;
    const totalServices = services.length;
    const runningCount = runningServices.length;
    const percentage = (runningCount / totalServices) * 100;

    if (criticalDown > 0) {
      return {
        text: `Critical Services Down (${criticalDown})`,
        color: 'bg-red-500',
        status: 'critical'
      };
    }
    if (percentage === 100) {
      return { text: 'All Systems Operational', color: 'bg-green-500', status: 'healthy' };
    }
    if (percentage >= 90) {
      return { text: 'Degraded Performance', color: 'bg-yellow-500', status: 'degraded' };
    }
    return { text: 'System Issues Detected', color: 'bg-orange-500', status: 'issues' };
  };

  const systemStatus = getSystemStatus();
  
  // Safer quick actions
  const handleQuickAction = (action) => {
    console.log('Quick action:', action);
    switch(action) {
      case 'view-logs':
        // Navigate to logs page
        window.location.href = '/admin/logs';
        break;
      case 'check-updates':
        // Show update modal
        setShowUpdateModal(true);
        break;
      case 'download-model':
        // Navigate to models page
        window.location.href = '/admin/models';
        break;
      case 'system-info':
        // Scroll to hardware section
        document.getElementById('hardware-info')?.scrollIntoView({ behavior: 'smooth' });
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
      {/* Page Header - Glassmorphism Style */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-2xl ${glassStyles.cardHover.base}`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-2xl transform hover:scale-110 transition-transform duration-300">
              <ComputerDesktopIcon className="h-8 w-8 text-white" />
            </div>
            <div>
              <h1 className={`text-3xl font-bold ${currentTheme === 'unicorn' ? 'text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-blue-400' : theme.text.primary}`}>
                {currentUser ? `Welcome back, ${currentUser.firstName || currentUser.username || 'User'}` : 'Operations Center'}
              </h1>
              <p className={`${currentTheme === 'unicorn' ? 'text-purple-200/80' : theme.text.secondary} mt-1 text-base`}>
                {currentUser ? 'UC-1 Pro System Management Dashboard' : 'Loading...'}
              </p>
            </div>
          </div>
          <div className={`text-right ${glassStyles.card} rounded-xl p-4 min-w-[200px]`}>
            <div className={`text-sm font-medium ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.secondary} mb-2`}>System Status</div>
            <div className="flex items-center justify-end gap-3">
              <div className={`w-3 h-3 ${systemStatus.color} rounded-full ${systemStatus.status === 'healthy' || systemStatus.status === 'unknown' ? 'animate-pulse shadow-lg' : ''}`}></div>
              <span className={`text-base font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>{systemStatus.text}</span>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Quick Actions - Glassmorphism Cards */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-xl`}>
        <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-6 flex items-center gap-3`}>
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg">
            <BoltIcon className="h-6 w-6 text-white" />
          </div>
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <motion.button
            whileHover={{ scale: 1.05, y: -4 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleQuickAction('view-logs')}
            className={`flex flex-col items-center gap-4 p-6 rounded-2xl ${glassStyles.card} ${glassStyles.cardHover.base} group relative overflow-hidden`}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative w-14 h-14 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl flex items-center justify-center shadow-2xl group-hover:shadow-blue-500/50 transition-all">
              <DocumentMagnifyingGlassIcon className="h-7 w-7 text-white" />
            </div>
            <span className={`relative text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>View Logs</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05, y: -4 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleQuickAction('check-updates')}
            className={`flex flex-col items-center gap-4 p-6 rounded-2xl ${glassStyles.card} ${glassStyles.cardHover.base} group relative overflow-hidden`}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-green-500/10 to-emerald-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative w-14 h-14 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center shadow-2xl group-hover:shadow-green-500/50 transition-all">
              <ArrowDownTrayIcon className="h-7 w-7 text-white" />
            </div>
            <span className={`relative text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>Check Updates</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05, y: -4 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleQuickAction('download-model')}
            className={`flex flex-col items-center gap-4 p-6 rounded-2xl ${glassStyles.card} ${glassStyles.cardHover.base} group relative overflow-hidden`}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-indigo-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative w-14 h-14 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-2xl flex items-center justify-center shadow-2xl group-hover:shadow-purple-500/50 transition-all">
              <CloudArrowDownIcon className="h-7 w-7 text-white" />
            </div>
            <span className={`relative text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>Download Model</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05, y: -4 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => handleQuickAction('system-info')}
            className={`flex flex-col items-center gap-4 p-6 rounded-2xl ${glassStyles.card} ${glassStyles.cardHover.base} group relative overflow-hidden`}
          >
            <div className="absolute inset-0 bg-gradient-to-br from-orange-500/10 to-red-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <div className="relative w-14 h-14 bg-gradient-to-br from-orange-500 to-red-500 rounded-2xl flex items-center justify-center shadow-2xl group-hover:shadow-orange-500/50 transition-all">
              <InformationCircleIcon className="h-7 w-7 text-white" />
            </div>
            <span className={`relative text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>System Info</span>
          </motion.button>
        </div>
      </motion.div>

      {/* Available Apps Widget */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-xl`}>
        <div className="flex items-center justify-between mb-6">
          <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} flex items-center gap-3`}>
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-purple-500 rounded-xl flex items-center justify-center shadow-lg">
              <CubeIcon className="h-6 w-6 text-white" />
            </div>
            Available Apps
          </h3>
          <Link
            to="/apps"
            className={`text-sm ${theme.text.accent} hover:underline flex items-center gap-1`}
          >
            View All
            <ArrowRightIcon className="h-4 w-4" />
          </Link>
        </div>

        <p className={`text-sm ${theme.text.secondary} mb-6`}>
          Discover powerful AI apps and tools to enhance your workflow
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Featured App Cards */}
          <motion.div
            whileHover={{ scale: 1.02 }}
            className={`${glassStyles.card} rounded-xl p-5 flex items-start gap-4 cursor-pointer`}
            onClick={() => window.location.href = '/apps'}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center flex-shrink-0 shadow-lg">
              <SparklesIcon className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className={`text-base font-bold ${theme.text.primary} mb-1`}>
                AI Chat
              </div>
              <div className={`text-xs ${theme.text.secondary} mb-2`}>
                FREE - Included in your plan
              </div>
              <div className={`text-xs ${theme.text.secondary}`}>
                Advanced conversational AI interface
              </div>
            </div>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.02 }}
            className={`${glassStyles.card} rounded-xl p-5 flex items-start gap-4 cursor-pointer`}
            onClick={() => window.location.href = '/apps'}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center flex-shrink-0 shadow-lg">
              <MagnifyingGlassIcon className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className={`text-base font-bold ${theme.text.primary} mb-1`}>
                AI Search
              </div>
              <div className={`text-xs ${theme.text.secondary} mb-2`}>
                FREE - Included in your plan
              </div>
              <div className={`text-xs ${theme.text.secondary}`}>
                Privacy-focused metasearch engine
              </div>
            </div>
          </motion.div>

          <motion.div
            whileHover={{ scale: 1.02 }}
            className={`${glassStyles.card} rounded-xl p-5 flex items-start gap-4 cursor-pointer`}
            onClick={() => window.location.href = '/apps'}
          >
            <div className="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-500 rounded-lg flex items-center justify-center flex-shrink-0 shadow-lg">
              <ServerStackIcon className="h-6 w-6 text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <div className={`text-base font-bold ${theme.text.primary} mb-1`}>
                Voice Services
              </div>
              <div className={`text-xs text-blue-400 mb-2`}>
                $5/month - Add-on
              </div>
              <div className={`text-xs ${theme.text.secondary}`}>
                Text-to-Speech & Speech-to-Text
              </div>
            </div>
          </motion.div>
        </div>

        <div className="mt-6 flex justify-center">
          <Link
            to="/apps"
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600 text-white rounded-lg font-semibold transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
          >
            Browse All Apps
            <ArrowRightIcon className="h-5 w-5" />
          </Link>
        </div>
      </motion.div>

      {/* System Information Card - Glassmorphism */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-xl`}>
        <h2 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-6 flex items-center gap-3`}>
          <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
            <ComputerDesktopIcon className="h-6 w-6 text-white" />
          </div>
          System Specifications
        </h2>
        
        {hardwareInfo && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* CPU Info */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} p-6 rounded-xl ${glassStyles.cardHover.base} border-l-4 border-blue-500`}
            >
              <div className="flex items-center gap-3 mb-3">
                <CpuChipIcon className="h-6 w-6 text-blue-500" />
                <div className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`}>CPU</div>
              </div>
              <div className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-2`}>{hardwareInfo.cpu.model}</div>
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary} space-y-1`}>
                <div>{hardwareInfo.cpu.cores} cores, {hardwareInfo.cpu.threads} threads</div>
                <div>{hardwareInfo.cpu.baseFreq} - {hardwareInfo.cpu.maxFreq}</div>
              </div>
            </motion.div>

            {/* GPU Info */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} p-6 rounded-xl ${glassStyles.cardHover.base} border-l-4 border-purple-500`}
            >
              <div className="flex items-center gap-3 mb-3">
                <FireIcon className="h-6 w-6 text-purple-500" />
                <div className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`}>GPU</div>
              </div>
              <div className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-2`}>{hardwareInfo.gpu.model}</div>
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary} space-y-1`}>
                <div>VRAM: {hardwareInfo.gpu.vram}</div>
                <div>Driver: {hardwareInfo.gpu.driver}, CUDA: {hardwareInfo.gpu.cuda}</div>
              </div>
            </motion.div>

            {/* iGPU Info */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} p-6 rounded-xl ${glassStyles.cardHover.base} border-l-4 border-cyan-500`}
            >
              <div className="flex items-center gap-3 mb-3">
                <CpuChipIcon className="h-6 w-6 text-cyan-500" />
                <div className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`}>iGPU</div>
              </div>
              <div className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-2`}>{hardwareInfo.igpu.model}</div>
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>
                Driver: {hardwareInfo.igpu.driver}
              </div>
            </motion.div>

            {/* Memory Info */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} p-6 rounded-xl ${glassStyles.cardHover.base} border-l-4 border-green-500`}
            >
              <div className="flex items-center gap-3 mb-3">
                <ServerStackIcon className="h-6 w-6 text-green-500" />
                <div className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`}>Memory</div>
              </div>
              <div className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-2`}>{hardwareInfo.memory.total} {hardwareInfo.memory.type}</div>
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>
                Configuration: {hardwareInfo.memory.slots}
              </div>
            </motion.div>

            {/* Storage Info */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} p-6 rounded-xl ${glassStyles.cardHover.base} border-l-4 border-amber-500`}
            >
              <div className="flex items-center gap-3 mb-3">
                <ServerStackIcon className="h-6 w-6 text-amber-500" />
                <div className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`}>Storage</div>
              </div>
              <div className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-2`}>{hardwareInfo.storage.primary}</div>
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>
                Secondary: {hardwareInfo.storage.secondary}
              </div>
            </motion.div>

            {/* OS Info */}
            <motion.div
              whileHover={{ scale: 1.02 }}
              className={`${glassStyles.card} p-6 rounded-xl ${glassStyles.cardHover.base} border-l-4 border-pink-500`}
            >
              <div className="flex items-center gap-3 mb-3">
                <ComputerDesktopIcon className="h-6 w-6 text-pink-500" />
                <div className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.accent}`}>Operating System</div>
              </div>
              <div className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-2`}>{hardwareInfo.os.name} {hardwareInfo.os.version}</div>
              <div className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary} space-y-1`}>
                <div>Kernel: {hardwareInfo.os.kernel}</div>
                <div>DE: {hardwareInfo.os.desktop}</div>
              </div>
            </motion.div>
          </div>
        )}
      </motion.div>
      
      {/* Resource Utilization Graphs - Glassmorphism with Enhanced Gradients */}
      <motion.div
        variants={itemVariants}
        className={`${glassStyles.card} rounded-2xl p-8 cursor-pointer ${glassStyles.cardHover.base} shadow-xl relative overflow-hidden group`}
        onClick={() => window.location.href = '/admin/system'}
        whileHover={{ scale: 1.01 }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-emerald-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-6 flex items-center justify-between relative z-10`}>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg">
              <ChartBarIcon className="h-6 w-6 text-white" />
            </div>
            Resource Utilization
          </div>
          <span className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.secondary} flex items-center gap-2 group-hover:text-green-400 transition-colors`}>
            Click for details
            <ArrowTopRightOnSquareIcon className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
          </span>
        </h3>
        <div className="space-y-5 relative z-10">
          {/* GPU Usage */}
          <div>
            <div className="flex justify-between mb-2">
              <span className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>
                GPU {systemData?.gpu?.[0]?.name ? `(${systemData?.gpu?.[0]?.name})` : ''}
              </span>
              <span className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>{gpuUsage.toFixed(1)}%</span>
            </div>
            <div className={`w-full ${glassStyles.card} rounded-full h-4 shadow-inner relative overflow-hidden`}>
              <motion.div
                className={`h-4 rounded-full shadow-lg ${
                  gpuUsage > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                  gpuUsage > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                  'bg-gradient-to-r from-green-500 to-emerald-500'
                } relative`}
                initial={{ width: 0 }}
                animate={{ width: `${gpuUsage}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
              </motion.div>
            </div>
          </div>

          {/* VRAM Usage */}
          <div>
            <div className="flex justify-between mb-2">
              <span className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>VRAM</span>
              <span className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
                {formatBytes(vramUsed)} / {formatBytes(vramTotal)} ({vramPercent.toFixed(1)}%)
              </span>
            </div>
            <div className={`w-full ${glassStyles.card} rounded-full h-4 shadow-inner relative overflow-hidden`}>
              <motion.div
                className={`h-4 rounded-full shadow-lg ${
                  vramPercent > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                  vramPercent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                  'bg-gradient-to-r from-blue-500 to-cyan-500'
                } relative`}
                initial={{ width: 0 }}
                animate={{ width: `${vramPercent}%` }}
                transition={{ duration: 1 }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
              </motion.div>
            </div>
          </div>
          
          {/* iGPU Usage - only show if data available */}
          {systemData?.igpu?.utilization !== undefined && (
            <div>
              <div className="flex justify-between mb-2">
                <span className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>
                  iGPU ({systemData.igpu.model || 'Intel UHD 770'})
                </span>
                <span className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>{systemData.igpu.utilization}%</span>
              </div>
              <div className={`w-full ${glassStyles.card} rounded-full h-4 shadow-inner relative overflow-hidden`}>
                <motion.div
                  className="h-4 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 shadow-lg relative"
                  initial={{ width: 0 }}
                  animate={{ width: `${systemData.igpu.utilization}%` }}
                  transition={{ duration: 1 }}
                >
                  <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
                </motion.div>
              </div>
            </div>
          )}

          {/* CPU */}
          <div>
            <div className="flex justify-between mb-2">
              <span className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>
                CPU {hardwareInfo?.cpu?.model ? `(${hardwareInfo?.cpu?.model.split(' ').slice(0, 2).join(' ')})` : ''}
              </span>
              <span className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>{systemData?.cpu?.percent?.toFixed(1) || 0}%</span>
            </div>
            <div className={`w-full ${glassStyles.card} rounded-full h-4 shadow-inner relative overflow-hidden`}>
              <motion.div
                className={`h-4 rounded-full shadow-lg ${
                  systemData?.cpu?.percent > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                  systemData?.cpu?.percent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                  'bg-gradient-to-r from-green-500 to-emerald-500'
                } relative`}
                initial={{ width: 0 }}
                animate={{ width: `${systemData?.cpu?.percent || 0}%` }}
                transition={{ duration: 1 }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
              </motion.div>
            </div>
          </div>

          {/* Memory */}
          <div>
            <div className="flex justify-between mb-2">
              <span className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>Memory</span>
              <span className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
                {formatBytes(systemData?.memory?.used)} / {formatBytes(systemData?.memory?.total)} ({systemData?.memory?.percent?.toFixed(1) || 0}%)
              </span>
            </div>
            <div className={`w-full ${glassStyles.card} rounded-full h-4 shadow-inner relative overflow-hidden`}>
              <motion.div
                className={`h-4 rounded-full shadow-lg ${
                  systemData?.memory?.percent > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                  systemData?.memory?.percent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                  'bg-gradient-to-r from-green-500 to-emerald-500'
                } relative`}
                initial={{ width: 0 }}
                animate={{ width: `${systemData?.memory?.percent || 0}%` }}
                transition={{ duration: 1 }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
              </motion.div>
            </div>
          </div>

          {/* Disk */}
          <div>
            <div className="flex justify-between mb-2">
              <span className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>Storage</span>
              <span className={`text-sm font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>
                {formatBytes(systemData?.disk?.used)} / {formatBytes(systemData?.disk?.total)} ({systemData?.disk?.percent?.toFixed(1) || 0}%)
              </span>
            </div>
            <div className={`w-full ${glassStyles.card} rounded-full h-4 shadow-inner relative overflow-hidden`}>
              <motion.div
                className={`h-4 rounded-full shadow-lg ${
                  systemData?.disk?.percent > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' :
                  systemData?.disk?.percent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' :
                  'bg-gradient-to-r from-purple-500 to-indigo-500'
                } relative`}
                initial={{ width: 0 }}
                animate={{ width: `${systemData?.disk?.percent || 0}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              >
                <div className="absolute inset-0 bg-gradient-to-t from-white/20 to-transparent"></div>
              </motion.div>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Alerts Section */}
      {alerts.length > 0 && (
        <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6`}>
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4`}>
            System Alerts ({alerts.length})
          </h3>
          <div className="space-y-2">
            {alerts.map(alert => (
              <div key={alert.id} className={`flex items-center gap-3 p-3 rounded-lg ${
                alert.type === 'error' ? 'bg-red-500/10 border border-red-500/30' :
                'bg-yellow-500/10 border border-yellow-500/30'
              }`}>
                <alert.icon className={`h-5 w-5 ${
                  alert.type === 'error' ? 'text-red-500' : 'text-yellow-500'
                }`} />
                <span className={theme.text.primary}>{alert.message}</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
      
      {/* Service Status Grid - Glassmorphism */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-xl`}>
        <div className="flex items-center justify-between mb-6">
          <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} flex items-center gap-3`}>
            <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-blue-500 rounded-xl flex items-center justify-center shadow-lg">
              <ServerStackIcon className="h-6 w-6 text-white" />
            </div>
            Service Status
            <span className={`ml-2 px-3 py-1 text-sm font-bold ${glassStyles.card} text-green-400 rounded-full shadow-lg`}>
              {services?.filter(s => s.status === 'running').length || 0} Running
            </span>
          </h3>
          <div className="flex items-center gap-3">
            <div className="text-xs text-gray-500">View:</div>
            <div className="flex gap-1 p-1 bg-gray-700/30 rounded-lg">
              <button 
                onClick={() => setServiceViewMode('cards')}
                className={`px-3 py-1 text-xs rounded-md transition-all ${serviceViewMode === 'cards' ? 'bg-blue-500 text-white shadow-sm' : `${theme.text.secondary} hover:bg-blue-500/20`}`}
              >
                Cards
              </button>
              <button 
                onClick={() => setServiceViewMode('circles')}
                className={`px-3 py-1 text-xs rounded-md transition-all ${serviceViewMode === 'circles' ? 'bg-blue-500 text-white shadow-sm' : `${theme.text.secondary} hover:bg-blue-500/20`}`}
              >
                Circles
              </button>
            </div>
          </div>
        </div>
        
        <div className={`grid ${serviceViewMode === 'circles' ? 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5' : 'grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6'} gap-3`}>
          {Object.keys(EnhancedServiceLogos)
            .filter(serviceKey => visibleServiceKeys.includes(serviceKey))
            .map(serviceKey => {
              const serviceData = services?.find(s => s.name.includes(serviceKey));
              const status = serviceData?.status || 'unknown';

              return (
                <motion.div
                  key={serviceKey}
                  whileHover={{ scale: 1.05 }}
                >
                  <EnhancedServiceCard
                    serviceKey={serviceKey}
                    serviceData={serviceData}
                    status={status}
                    onClick={setSelectedService}
                    theme={theme}
                    currentTheme={currentTheme}
                    viewMode={serviceViewMode}
                  />
                </motion.div>
              );
            })}
        </div>
      </motion.div>
      
      {/* Recent Activity - Glassmorphism Timeline */}
      <motion.div variants={itemVariants} className={`${glassStyles.card} rounded-2xl p-8 shadow-xl`}>
        <h3 className={`text-xl font-bold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary} mb-6 flex items-center gap-3`}>
          <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-xl flex items-center justify-center shadow-lg">
            <ClockIcon className="h-6 w-6 text-white" />
          </div>
          Recent Activity
        </h3>
        {recentActivity.length === 0 ? (
          <div className={`text-center py-12 ${glassStyles.card} rounded-xl`}>
            <InformationCircleIcon className="h-16 w-16 text-gray-500 mx-auto mb-3 opacity-50" />
            <p className={`text-base font-semibold ${currentTheme === 'unicorn' ? 'text-purple-200' : theme.text.secondary}`}>No recent activity</p>
            <p className={`text-sm ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.secondary} mt-2`}>System events will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {recentActivity.map((activity, index) => (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                whileHover={{ scale: 1.01, x: 4 }}
                className={`flex items-start gap-4 p-5 rounded-xl ${glassStyles.card} hover:shadow-lg transition-all group relative overflow-hidden`}
              >
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative w-12 h-12 bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg group-hover:shadow-xl transition-shadow">
                  <activity.icon className="h-6 w-6 text-white" />
                </div>
                <div className="flex-1 min-w-0 relative">
                  <p className={`text-sm font-semibold ${currentTheme === 'unicorn' ? 'text-white' : theme.text.primary}`}>{activity.message}</p>
                  <p className={`text-xs ${currentTheme === 'unicorn' ? 'text-purple-300' : theme.text.secondary} mt-2 flex items-center gap-2`}>
                    <ClockIcon className="h-3 w-3" />
                    {activity.time}
                  </p>
                </div>
                <div className="relative w-3 h-3 bg-green-500 rounded-full flex-shrink-0 mt-3 shadow-lg animate-pulse"></div>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
      
      {/* Service Modal */}
      <ServiceModal 
        service={selectedService}
        isOpen={!!selectedService}
        onClose={() => setSelectedService(null)}
        theme={theme}
      />
      
      {/* Update Modal */}
      <UpdateModal
        isOpen={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        theme={theme}
      />
    </motion.div>
  );
}