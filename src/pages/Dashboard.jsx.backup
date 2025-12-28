import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useSystem } from '../contexts/SystemContext';
import { useTheme } from '../contexts/ThemeContext';
import { ServiceLogos, getServiceInfo } from '../components/ServiceLogos';
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
  WrenchScrewdriverIcon
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

export default function Dashboard() {
  const { systemData, services, fetchSystemStatus, fetchServices } = useSystem();
  const { theme, currentTheme } = useTheme();
  const [alerts, setAlerts] = useState([]);
  const [recentActivity, setRecentActivity] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [hardwareInfo, setHardwareInfo] = useState(null);
  const [serviceViewMode, setServiceViewMode] = useState('cards'); // cards, circles, list
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  
  useEffect(() => {
    // Fetch initial data
    fetchSystemStatus();
    fetchServices();
    fetchHardwareInfo();
    
    // Set up polling
    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchServices();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);
  
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
  
  useEffect(() => {
    // Generate alerts based on system state
    const newAlerts = [];
    
    if (systemData?.memory?.percent > 85) {
      newAlerts.push({
        id: 'mem-high',
        type: 'warning',
        message: `Memory usage high: ${systemData.memory.percent.toFixed(1)}%`,
        icon: ExclamationTriangleIcon
      });
    }
    
    if (systemData?.cpu?.percent > 85) {
      newAlerts.push({
        id: 'cpu-high',
        type: 'warning',
        message: `CPU usage high: ${systemData.cpu.percent.toFixed(1)}%`,
        icon: ExclamationTriangleIcon
      });
    }
    
    // Check for stopped critical services
    services?.forEach(service => {
      if (service.status !== 'running' && ['vllm', 'open-webui', 'redis', 'postgresql'].includes(service.name)) {
        newAlerts.push({
          id: `service-${service.name}`,
          type: 'error',
          message: `Critical service ${service.name} is ${service.status}`,
          icon: ShieldExclamationIcon
        });
      }
    });
    
    setAlerts(newAlerts);
  }, [systemData, services]);
  
  useEffect(() => {
    // Simulate recent activity
    setRecentActivity([
      { id: 1, message: 'System health check completed', time: '2m ago', icon: CheckCircleIcon },
      { id: 2, message: 'Model cache optimized', time: '15m ago', icon: BoltIcon },
      { id: 3, message: 'Backup completed successfully', time: '1h ago', icon: CloudArrowDownIcon },
      { id: 4, message: 'GPU memory defragmented', time: '2h ago', icon: CpuChipIcon },
      { id: 5, message: 'Logs rotated', time: '3h ago', icon: DocumentMagnifyingGlassIcon }
    ]);
  }, []);
  
  const gpuUsage = systemData?.gpu?.[0]?.utilization || 0;
  const vramUsed = systemData?.gpu?.[0]?.memory_used || 0;
  const vramTotal = systemData?.gpu?.[0]?.memory_total || 33554432000; // 32GB default
  const vramPercent = (vramUsed / vramTotal) * 100;
  
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
        // Show system information
        alert('System information displayed below');
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
      <motion.div variants={itemVariants} className="relative">
        <div className="flex items-center justify-between">
          <div>
            <h1 className={`text-3xl font-bold ${theme.text.primary} flex items-center gap-3`}>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center shadow-lg">
                <ComputerDesktopIcon className="h-6 w-6 text-white" />
              </div>
              Operations Center
            </h1>
            <p className={`${theme.text.secondary} mt-1 ml-13`}>UC-1 Pro System Management Dashboard</p>
          </div>
          <div className="text-right">
            <div className={`text-sm ${theme.text.secondary}`}>System Status</div>
            <div className="flex items-center gap-2 mt-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className={`text-sm font-semibold ${theme.text.primary}`}>All Systems Operational</span>
            </div>
          </div>
        </div>
      </motion.div>
      
      {/* Quick Actions - Top Priority */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-blue-500/20`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
          <BoltIcon className="h-5 w-5 text-blue-500" />
          Quick Actions
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('view-logs')}
            className={`flex flex-col items-center gap-3 p-4 rounded-lg ${theme.button} hover:bg-blue-500/10 transition-all group border border-transparent hover:border-blue-500/30`}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center group-hover:shadow-lg transition-shadow">
              <DocumentMagnifyingGlassIcon className="h-5 w-5 text-white" />
            </div>
            <span className="text-sm font-medium">View Logs</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('check-updates')}
            className={`flex flex-col items-center gap-3 p-4 rounded-lg ${theme.button} hover:bg-green-500/10 transition-all group border border-transparent hover:border-green-500/30`}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center group-hover:shadow-lg transition-shadow">
              <ArrowDownTrayIcon className="h-5 w-5 text-white" />
            </div>
            <span className="text-sm font-medium">Check Updates</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('download-model')}
            className={`flex flex-col items-center gap-3 p-4 rounded-lg ${theme.button} hover:bg-purple-500/10 transition-all group border border-transparent hover:border-purple-500/30`}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg flex items-center justify-center group-hover:shadow-lg transition-shadow">
              <CloudArrowDownIcon className="h-5 w-5 text-white" />
            </div>
            <span className="text-sm font-medium">Download Model</span>
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => handleQuickAction('system-info')}
            className={`flex flex-col items-center gap-3 p-4 rounded-lg ${theme.button} hover:bg-orange-500/10 transition-all group border border-transparent hover:border-orange-500/30`}
          >
            <div className="w-10 h-10 bg-gradient-to-br from-orange-500 to-red-500 rounded-lg flex items-center justify-center group-hover:shadow-lg transition-shadow">
              <InformationCircleIcon className="h-5 w-5 text-white" />
            </div>
            <span className="text-sm font-medium">System Info</span>
          </motion.button>
        </div>
      </motion.div>
      
      {/* System Information Card */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-purple-500/20`}>
        <h2 className={`text-xl font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
          <ComputerDesktopIcon className="h-6 w-6 text-purple-500" />
          System Specifications
        </h2>
        
        {hardwareInfo && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* CPU Info */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className={`text-sm font-semibold ${theme.text.accent} mb-2`}>CPU</div>
              <div className={`text-sm ${theme.text.primary}`}>{hardwareInfo.cpu.model}</div>
              <div className={`text-xs ${theme.text.secondary} mt-1`}>
                {hardwareInfo.cpu.cores} cores, {hardwareInfo.cpu.threads} threads
              </div>
              <div className={`text-xs ${theme.text.secondary}`}>
                {hardwareInfo.cpu.baseFreq} - {hardwareInfo.cpu.maxFreq}
              </div>
            </div>
            
            {/* GPU Info */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className={`text-sm font-semibold ${theme.text.accent} mb-2`}>GPU</div>
              <div className={`text-sm ${theme.text.primary}`}>{hardwareInfo.gpu.model}</div>
              <div className={`text-xs ${theme.text.secondary} mt-1`}>
                VRAM: {hardwareInfo.gpu.vram}
              </div>
              <div className={`text-xs ${theme.text.secondary}`}>
                Driver: {hardwareInfo.gpu.driver}, CUDA: {hardwareInfo.gpu.cuda}
              </div>
            </div>
            
            {/* iGPU Info */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className={`text-sm font-semibold ${theme.text.accent} mb-2`}>iGPU</div>
              <div className={`text-sm ${theme.text.primary}`}>{hardwareInfo.igpu.model}</div>
              <div className={`text-xs ${theme.text.secondary} mt-1`}>
                Driver: {hardwareInfo.igpu.driver}
              </div>
            </div>
            
            {/* Memory Info */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className={`text-sm font-semibold ${theme.text.accent} mb-2`}>Memory</div>
              <div className={`text-sm ${theme.text.primary}`}>{hardwareInfo.memory.total} {hardwareInfo.memory.type}</div>
              <div className={`text-xs ${theme.text.secondary} mt-1`}>
                Configuration: {hardwareInfo.memory.slots}
              </div>
            </div>
            
            {/* Storage Info */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className={`text-sm font-semibold ${theme.text.accent} mb-2`}>Storage</div>
              <div className={`text-sm ${theme.text.primary}`}>{hardwareInfo.storage.primary}</div>
              <div className={`text-xs ${theme.text.secondary} mt-1`}>
                Secondary: {hardwareInfo.storage.secondary}
              </div>
            </div>
            
            {/* OS Info */}
            <div className={`p-4 rounded-lg ${currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
              <div className={`text-sm font-semibold ${theme.text.accent} mb-2`}>Operating System</div>
              <div className={`text-sm ${theme.text.primary}`}>{hardwareInfo.os.name} {hardwareInfo.os.version}</div>
              <div className={`text-xs ${theme.text.secondary} mt-1`}>
                Kernel: {hardwareInfo.os.kernel}
              </div>
              <div className={`text-xs ${theme.text.secondary}`}>
                DE: {hardwareInfo.os.desktop}
              </div>
            </div>
          </div>
        )}
      </motion.div>
      
      {/* Resource Utilization Graphs */}
      <motion.div 
        variants={itemVariants} 
        className={`${theme.card} rounded-xl p-6 cursor-pointer hover:bg-opacity-80 transition-all border border-green-500/20 hover:border-green-500/40`}
        onClick={() => window.location.href = '/admin/system'}
      >
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center justify-between`}>
          <div className="flex items-center gap-2">
            <ChartBarIcon className="h-5 w-5 text-green-500" />
            Resource Utilization
          </div>
          <span className={`text-sm ${theme.text.secondary} flex items-center gap-1`}>
            Click for details 
            <ArrowTopRightOnSquareIcon className="h-4 w-4" />
          </span>
        </h3>
        <div className="space-y-4">
          {/* GPU Usage */}
          <div>
            <div className="flex justify-between mb-1">
              <span className={`text-sm ${theme.text.secondary}`}>GPU (RTX 5090)</span>
              <span className={`text-sm ${theme.text.primary}`}>{gpuUsage.toFixed(1)}%</span>
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-3 shadow-inner">
              <motion.div 
                className={`h-3 rounded-full shadow-sm ${
                  gpuUsage > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' : 
                  gpuUsage > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 
                  'bg-gradient-to-r from-green-500 to-emerald-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${gpuUsage}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
            </div>
          </div>
          
          {/* VRAM Usage */}
          <div>
            <div className="flex justify-between mb-1">
              <span className={`text-sm ${theme.text.secondary}`}>VRAM</span>
              <span className={`text-sm ${theme.text.primary}`}>
                {formatBytes(vramUsed)} / {formatBytes(vramTotal)} ({vramPercent.toFixed(1)}%)
              </span>
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-3 shadow-inner">
              <motion.div 
                className={`h-3 rounded-full shadow-sm ${
                  vramPercent > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' : 
                  vramPercent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 
                  'bg-gradient-to-r from-blue-500 to-cyan-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${vramPercent}%` }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
          
          {/* iGPU Usage (placeholder) */}
          <div>
            <div className="flex justify-between mb-1">
              <span className={`text-sm ${theme.text.secondary}`}>iGPU (Intel UHD 770)</span>
              <span className={`text-sm ${theme.text.primary}`}>12%</span>
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-3">
              <motion.div 
                className="h-3 rounded-full bg-blue-500"
                initial={{ width: 0 }}
                animate={{ width: '12%' }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
          
          {/* CPU */}
          <div>
            <div className="flex justify-between mb-1">
              <span className={`text-sm ${theme.text.secondary}`}>CPU (i9-13900K)</span>
              <span className={`text-sm ${theme.text.primary}`}>{systemData?.cpu?.percent?.toFixed(1) || 0}%</span>
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-3">
              <motion.div 
                className={`h-3 rounded-full ${
                  systemData?.cpu?.percent > 90 ? 'bg-red-500' : 
                  systemData?.cpu?.percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${systemData?.cpu?.percent || 0}%` }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
          
          {/* Memory */}
          <div>
            <div className="flex justify-between mb-1">
              <span className={`text-sm ${theme.text.secondary}`}>Memory</span>
              <span className={`text-sm ${theme.text.primary}`}>
                {formatBytes(systemData?.memory?.used)} / {formatBytes(systemData?.memory?.total)} ({systemData?.memory?.percent?.toFixed(1) || 0}%)
              </span>
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-3">
              <motion.div 
                className={`h-3 rounded-full ${
                  systemData?.memory?.percent > 90 ? 'bg-red-500' : 
                  systemData?.memory?.percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${systemData?.memory?.percent || 0}%` }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
          
          {/* Disk */}
          <div>
            <div className="flex justify-between mb-1">
              <span className={`text-sm ${theme.text.secondary}`}>Storage</span>
              <span className={`text-sm ${theme.text.primary}`}>
                {formatBytes(systemData?.disk?.used)} / {formatBytes(systemData?.disk?.total)} ({systemData?.disk?.percent?.toFixed(1) || 0}%)
              </span>
            </div>
            <div className="w-full bg-gray-700/30 rounded-full h-3 shadow-inner">
              <motion.div 
                className={`h-3 rounded-full shadow-sm ${
                  systemData?.disk?.percent > 90 ? 'bg-gradient-to-r from-red-500 to-red-600' : 
                  systemData?.disk?.percent > 70 ? 'bg-gradient-to-r from-yellow-500 to-orange-500' : 
                  'bg-gradient-to-r from-purple-500 to-indigo-500'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${systemData?.disk?.percent || 0}%` }}
                transition={{ duration: 1, ease: "easeOut" }}
              />
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
      
      {/* Service Status Grid */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-cyan-500/20`}>
        <div className="flex items-center justify-between mb-6">
          <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
            <ServerStackIcon className="h-5 w-5 text-cyan-500" />
            Service Status
            <span className="ml-2 px-2 py-1 text-xs bg-green-500/20 text-green-400 rounded-full">
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
          {Object.keys(EnhancedServiceLogos).map(serviceKey => {
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
      
      {/* Recent Activity */}
      <motion.div variants={itemVariants} className={`${theme.card} rounded-xl p-6 border border-amber-500/20`}>
        <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
          <ClockIcon className="h-5 w-5 text-amber-500" />
          Recent Activity
        </h3>
        <div className="space-y-4">
          {recentActivity.map((activity, index) => (
            <motion.div 
              key={activity.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-start gap-4 p-3 rounded-lg bg-gray-700/20 hover:bg-gray-700/30 transition-colors"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-500 rounded-lg flex items-center justify-center flex-shrink-0">
                <activity.icon className="h-4 w-4 text-white" />
              </div>
              <div className="flex-1 min-w-0">
                <p className={`text-sm ${theme.text.primary} font-medium`}>{activity.message}</p>
                <p className={`text-xs ${theme.text.secondary} mt-1`}>{activity.time}</p>
              </div>
              <div className="w-2 h-2 bg-green-500 rounded-full flex-shrink-0 mt-2"></div>
            </motion.div>
          ))}
        </div>
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