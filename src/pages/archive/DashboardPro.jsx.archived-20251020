import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useTheme } from '../contexts/ThemeContext';
import { EnhancedServiceLogos, EnhancedServiceCard, getEnhancedServiceInfo } from '../components/EnhancedServiceLogos';
import UpdateModal from '../components/UpdateModal';
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
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  SparklesIcon,
  RocketLaunchIcon,
  CubeTransparentIcon,
  CommandLineIcon,
  BeakerIcon,
  ArchiveBoxIcon
} from '@heroicons/react/24/outline';
import { 
  CpuChipIcon as CpuChipIconSolid,
  ServerStackIcon as ServerStackIconSolid,
  BoltIcon as BoltIconSolid 
} from '@heroicons/react/24/solid';

// Modern container animations
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.02,
      delayChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 10, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      type: "spring",
      stiffness: 100,
      damping: 10
    }
  }
};

// Format utilities
const formatBytes = (bytes) => {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  
  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
};

// Modern Metric Card Component
const MetricCard = ({ title, value, subtitle, icon: Icon, trend, color = 'blue', theme, onClick }) => {
  const colorClasses = {
    blue: 'from-blue-500/10 to-cyan-500/10 border-blue-500/20 text-blue-400',
    green: 'from-emerald-500/10 to-green-500/10 border-emerald-500/20 text-emerald-400',
    purple: 'from-purple-500/10 to-indigo-500/10 border-purple-500/20 text-purple-400',
    yellow: 'from-yellow-500/10 to-amber-500/10 border-yellow-500/20 text-yellow-400',
    red: 'from-red-500/10 to-rose-500/10 border-red-500/20 text-red-400'
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02, translateY: -2 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`
        relative p-6 rounded-2xl cursor-pointer
        bg-gradient-to-br ${colorClasses[color]}
        border backdrop-blur-xl
        transition-all duration-300 hover:shadow-2xl
        overflow-hidden group
      `}
    >
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-xl bg-gradient-to-br ${colorClasses[color]} backdrop-blur-sm`}>
            <Icon className="h-6 w-6" />
          </div>
          {trend && (
            <div className={`flex items-center gap-1 text-sm ${trend > 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend > 0 ? <ArrowTrendingUpIcon className="h-4 w-4" /> : <ArrowTrendingDownIcon className="h-4 w-4" />}
              <span>{Math.abs(trend)}%</span>
            </div>
          )}
        </div>
        
        <div className="space-y-1">
          <p className={`text-sm font-medium ${theme.text.secondary}`}>{title}</p>
          <p className={`text-3xl font-bold ${theme.text.primary}`}>{value}</p>
          {subtitle && (
            <p className={`text-xs ${theme.text.secondary} opacity-80`}>{subtitle}</p>
          )}
        </div>
      </div>
    </motion.div>
  );
};

// Modern Resource Gauge Component
const ResourceGauge = ({ title, value, max, unit, icon: Icon, gradient, theme }) => {
  const percentage = (value / max) * 100;
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-gray-400" />
          <span className={`text-sm font-medium ${theme.text.secondary}`}>{title}</span>
        </div>
        <span className={`text-sm font-bold ${theme.text.primary}`}>
          {percentage.toFixed(1)}%
        </span>
      </div>
      
      <div className="relative h-2 bg-gray-800/50 rounded-full overflow-hidden backdrop-blur-sm">
        <motion.div
          className={`absolute inset-y-0 left-0 ${gradient} rounded-full`}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 1, ease: "easeOut" }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent animate-shimmer" />
      </div>
      
      <div className="flex justify-between text-xs">
        <span className={theme.text.secondary}>
          {formatBytes(value)} used
        </span>
        <span className={`${theme.text.secondary} opacity-60`}>
          {formatBytes(max)} total
        </span>
      </div>
    </div>
  );
};

// Modern Service Status Grid
const ServiceStatusGrid = ({ services, theme, onServiceClick }) => {
  const getStatusColor = (status) => {
    switch(status) {
      case 'running': return 'bg-emerald-500';
      case 'stopped': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      case 'restarting': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
      {services?.map((service) => (
        <motion.button
          key={service.name}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onServiceClick(service)}
          className={`
            relative p-4 rounded-xl
            bg-gradient-to-br from-gray-800/50 to-gray-900/50
            border border-gray-700/50 backdrop-blur-sm
            hover:border-gray-600 transition-all duration-300
            group overflow-hidden
          `}
        >
          {/* Hover effect */}
          <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
          
          <div className="relative z-10 flex flex-col items-center gap-2">
            <div className="text-2xl">{getEnhancedServiceInfo(service.name).icon}</div>
            <span className={`text-xs font-medium ${theme.text.primary}`}>
              {service.display_name || service.name}
            </span>
            <div className={`w-2 h-2 rounded-full ${getStatusColor(service.status)} animate-pulse`} />
          </div>
        </motion.button>
      ))}
    </div>
  );
};

export default function DashboardPro() {
  const { systemData, services, fetchSystemStatus, fetchServices } = useSystem();
  const { theme, currentTheme } = useTheme();
  const [alerts, setAlerts] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [hardwareInfo, setHardwareInfo] = useState(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState(null);
  
  useEffect(() => {
    fetchSystemStatus();
    fetchServices();
    fetchHardwareInfo();
    
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchServices();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
  const fetchHardwareInfo = async () => {
    try {
      const response = await fetch('/api/v1/system/hardware');
      if (!response.ok) throw new Error('Failed to fetch hardware info');
      const data = await response.json();
      setHardwareInfo(data);
    } catch (error) {
      console.error('Failed to fetch hardware info:', error);
    }
  };
  
  // Calculate system health score
  const calculateHealthScore = () => {
    let score = 100;
    if (systemData?.cpu?.percent > 80) score -= 10;
    if (systemData?.memory?.percent > 85) score -= 15;
    if (systemData?.disk?.percent > 90) score -= 20;
    const stoppedServices = services?.filter(s => s.status !== 'running').length || 0;
    score -= stoppedServices * 5;
    return Math.max(0, score);
  };
  
  const healthScore = calculateHealthScore();
  const gpuUsage = systemData?.gpu?.[0]?.utilization || 0;
  const vramUsed = systemData?.gpu?.[0]?.memory_used || 0;
  const vramTotal = systemData?.gpu?.[0]?.memory_total || 33554432000;
  
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6 p-6"
    >
      {/* Modern Header */}
      <motion.div variants={itemVariants} className="relative">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-4xl font-bold ${theme.text.primary} tracking-tight`}>
              Operations Center
            </h1>
            <p className={`${theme.text.secondary} mt-2`}>
              System Intelligence Dashboard • UC-1 Pro
            </p>
          </div>
          
          {/* System Health Indicator */}
          <div className="text-right">
            <div className={`text-sm font-medium ${theme.text.secondary} mb-2`}>System Health</div>
            <div className="flex items-center gap-3">
              <div className={`
                text-3xl font-bold
                ${healthScore >= 80 ? 'text-emerald-400' : healthScore >= 60 ? 'text-yellow-400' : 'text-red-400'}
              `}>
                {healthScore}%
              </div>
              <div className="relative w-20 h-20">
                <svg className="transform -rotate-90 w-20 h-20">
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    className="text-gray-700"
                  />
                  <circle
                    cx="40"
                    cy="40"
                    r="36"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="none"
                    strokeDasharray={`${healthScore * 2.26} 226`}
                    className={`
                      transition-all duration-1000
                      ${healthScore >= 80 ? 'text-emerald-400' : healthScore >= 60 ? 'text-yellow-400' : 'text-red-400'}
                    `}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  {healthScore >= 80 ? (
                    <CheckCircleIcon className="h-8 w-8 text-emerald-400" />
                  ) : healthScore >= 60 ? (
                    <ExclamationTriangleIcon className="h-8 w-8 text-yellow-400" />
                  ) : (
                    <ShieldExclamationIcon className="h-8 w-8 text-red-400" />
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Key Metrics Grid */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="GPU Utilization"
          value={`${gpuUsage.toFixed(1)}%`}
          subtitle="RTX 5090"
          icon={CpuChipIcon}
          trend={5}
          color="purple"
          theme={theme}
          onClick={() => setSelectedMetric('gpu')}
        />
        <MetricCard
          title="Active Services"
          value={services?.filter(s => s.status === 'running').length || 0}
          subtitle={`of ${services?.length || 0} total`}
          icon={ServerStackIcon}
          color="green"
          theme={theme}
          onClick={() => setSelectedMetric('services')}
        />
        <MetricCard
          title="Memory Usage"
          value={`${systemData?.memory?.percent?.toFixed(1) || 0}%`}
          subtitle={formatBytes(systemData?.memory?.used)}
          icon={BoltIcon}
          trend={-2}
          color="blue"
          theme={theme}
          onClick={() => setSelectedMetric('memory')}
        />
        <MetricCard
          title="System Uptime"
          value={formatUptime(systemData?.uptime || 0)}
          subtitle="Continuous operation"
          icon={ClockIcon}
          color="yellow"
          theme={theme}
        />
      </motion.div>
      
      {/* Quick Actions Bar */}
      <motion.div 
        variants={itemVariants}
        className={`
          p-4 rounded-2xl
          bg-gradient-to-r from-purple-900/20 via-indigo-900/20 to-blue-900/20
          border border-purple-500/20 backdrop-blur-xl
        `}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <SparklesIcon className="h-5 w-5 text-purple-400" />
            <span className={`font-medium ${theme.text.primary}`}>Quick Actions</span>
          </div>
          
          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => window.location.href = '/admin/models'}
              className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-medium text-sm hover:from-purple-700 hover:to-indigo-700 transition-all shadow-lg"
            >
              <div className="flex items-center gap-2">
                <CubeTransparentIcon className="h-4 w-4" />
                Manage Models
              </div>
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => window.location.href = '/admin/logs'}
              className="px-4 py-2 rounded-lg bg-gray-800 text-white font-medium text-sm hover:bg-gray-700 transition-all"
            >
              <div className="flex items-center gap-2">
                <DocumentMagnifyingGlassIcon className="h-4 w-4" />
                View Logs
              </div>
            </motion.button>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowUpdateModal(true)}
              className="px-4 py-2 rounded-lg bg-gray-800 text-white font-medium text-sm hover:bg-gray-700 transition-all"
            >
              <div className="flex items-center gap-2">
                <ArrowDownTrayIcon className="h-4 w-4" />
                Check Updates
              </div>
            </motion.button>
          </div>
        </div>
      </motion.div>
      
      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Resource Monitoring */}
        <motion.div 
          variants={itemVariants}
          className={`
            lg:col-span-2 p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className={`text-xl font-bold ${theme.text.primary}`}>
              Resource Monitoring
            </h2>
            <button 
              onClick={() => window.location.href = '/admin/system'}
              className={`text-sm ${theme.text.accent} hover:underline flex items-center gap-1`}
            >
              View Details
              <ArrowTopRightOnSquareIcon className="h-4 w-4" />
            </button>
          </div>
          
          <div className="space-y-6">
            <ResourceGauge
              title="GPU Memory (VRAM)"
              value={vramUsed}
              max={vramTotal}
              icon={CpuChipIcon}
              gradient="bg-gradient-to-r from-purple-500 to-indigo-500"
              theme={theme}
            />
            
            <ResourceGauge
              title="System Memory"
              value={systemData?.memory?.used || 0}
              max={systemData?.memory?.total || 1}
              icon={ServerStackIcon}
              gradient="bg-gradient-to-r from-blue-500 to-cyan-500"
              theme={theme}
            />
            
            <ResourceGauge
              title="Storage"
              value={systemData?.disk?.used || 0}
              max={systemData?.disk?.total || 1}
              icon={ArchiveBoxIcon}
              gradient="bg-gradient-to-r from-emerald-500 to-green-500"
              theme={theme}
            />
            
            <ResourceGauge
              title="CPU Usage"
              value={systemData?.cpu?.percent || 0}
              max={100}
              icon={BoltIcon}
              gradient="bg-gradient-to-r from-yellow-500 to-orange-500"
              theme={theme}
            />
          </div>
        </motion.div>
        
        {/* System Information */}
        <motion.div 
          variants={itemVariants}
          className={`
            p-6 rounded-2xl
            bg-gradient-to-br from-gray-800/40 to-gray-900/40
            border border-gray-700/50 backdrop-blur-xl
          `}
        >
          <h2 className={`text-xl font-bold ${theme.text.primary} mb-6`}>
            System Information
          </h2>
          
          {hardwareInfo && (
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-gray-800/50 backdrop-blur-sm">
                <div className={`text-xs font-medium ${theme.text.accent} mb-2`}>PROCESSOR</div>
                <div className={`text-sm font-bold ${theme.text.primary}`}>
                  {hardwareInfo.cpu.model}
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  {hardwareInfo.cpu.cores} cores • {hardwareInfo.cpu.threads} threads
                </div>
              </div>
              
              <div className="p-4 rounded-xl bg-gray-800/50 backdrop-blur-sm">
                <div className={`text-xs font-medium ${theme.text.accent} mb-2`}>GRAPHICS</div>
                <div className={`text-sm font-bold ${theme.text.primary}`}>
                  {hardwareInfo.gpu.model}
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  {hardwareInfo.gpu.vram} • CUDA {hardwareInfo.gpu.cuda}
                </div>
              </div>
              
              <div className="p-4 rounded-xl bg-gray-800/50 backdrop-blur-sm">
                <div className={`text-xs font-medium ${theme.text.accent} mb-2`}>MEMORY</div>
                <div className={`text-sm font-bold ${theme.text.primary}`}>
                  {hardwareInfo.memory.total} {hardwareInfo.memory.type}
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  {hardwareInfo.memory.slots}
                </div>
              </div>
              
              <div className="p-4 rounded-xl bg-gray-800/50 backdrop-blur-sm">
                <div className={`text-xs font-medium ${theme.text.accent} mb-2`}>OPERATING SYSTEM</div>
                <div className={`text-sm font-bold ${theme.text.primary}`}>
                  {hardwareInfo.os.name} {hardwareInfo.os.version}
                </div>
                <div className={`text-xs ${theme.text.secondary} mt-1`}>
                  Kernel {hardwareInfo.os.kernel}
                </div>
              </div>
            </div>
          )}
        </motion.div>
      </div>
      
      {/* Services Status */}
      <motion.div 
        variants={itemVariants}
        className={`
          p-6 rounded-2xl
          bg-gradient-to-br from-gray-800/40 to-gray-900/40
          border border-gray-700/50 backdrop-blur-xl
        `}
      >
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-xl font-bold ${theme.text.primary}`}>
            Service Status
          </h2>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className={`text-sm ${theme.text.secondary}`}>
                {services?.filter(s => s.status === 'running').length || 0} Running
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-gray-500" />
              <span className={`text-sm ${theme.text.secondary}`}>
                {services?.filter(s => s.status !== 'running').length || 0} Stopped
              </span>
            </div>
          </div>
        </div>
        
        <ServiceStatusGrid 
          services={services}
          theme={theme}
          onServiceClick={setSelectedService}
        />
      </motion.div>
      
      {/* Update Modal */}
      <UpdateModal
        isOpen={showUpdateModal}
        onClose={() => setShowUpdateModal(false)}
        theme={theme}
      />
    </motion.div>
  );
}