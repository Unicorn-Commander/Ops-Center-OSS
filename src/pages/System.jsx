import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CpuChipIcon,
  CircleStackIcon,
  ServerIcon,
  BoltIcon,
  ArrowPathIcon,
  ChartBarIcon,
  ClockIcon,
  FireIcon,
  ComputerDesktopIcon,
  RectangleStackIcon,
  WifiIcon,
  XMarkIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  StopIcon,
  ShieldExclamationIcon
} from '@heroicons/react/24/outline';
import { useSystem } from '../contexts/SystemContext';
import { useTheme } from '../contexts/ThemeContext';
import { useToast } from '../components/Toast';
import MuiTooltip from '@mui/material/Tooltip';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { isCriticalProcess } from '../utils/validation';

// Format utilities
const formatBytes = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

const formatUptime = (seconds) => {
  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return `${days}d ${hours}h ${minutes}m`;
};

const formatNetworkSpeed = (bytesPerSec) => {
  if (bytesPerSec < 1024) return `${bytesPerSec.toFixed(0)} B/s`;
  if (bytesPerSec < 1024 * 1024) return `${(bytesPerSec / 1024).toFixed(2)} KB/s`;
  return `${(bytesPerSec / (1024 * 1024)).toFixed(2)} MB/s`;
};

// Temperature gauge component
const TemperatureGauge = ({ temperature, maxTemp = 100, theme }) => {
  const percentage = (temperature / maxTemp) * 100;
  const getColor = () => {
    if (temperature >= 80) return 'text-red-500';
    if (temperature >= 60) return 'text-yellow-500';
    return 'text-green-500';
  };

  return (
    <div className="flex items-center gap-3">
      <div className="relative w-16 h-16">
        <svg className="transform -rotate-90 w-16 h-16">
          <circle
            cx="32"
            cy="32"
            r="28"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
            className="text-gray-700"
          />
          <circle
            cx="32"
            cy="32"
            r="28"
            stroke="currentColor"
            strokeWidth="4"
            fill="none"
            strokeDasharray={`${percentage * 1.76} 176`}
            className={getColor()}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className={`text-xs font-bold ${theme.text.primary}`}>{temperature}°C</span>
        </div>
      </div>
    </div>
  );
};

// Process row component
const ProcessRow = ({ process, theme, onKill, killing }) => {
  const isCritical = isCriticalProcess(process.name);

  return (
    <>
      <motion.tr
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="hover:bg-gray-800/50 transition-colors"
      >
        <td className={`px-4 py-3 text-sm font-mono ${theme.text.primary}`}>
          <div className="flex items-center gap-2">
            {isCritical && (
              <ShieldExclamationIcon className="w-4 h-4 text-red-500" title="Critical Process" />
            )}
            {process.name}
          </div>
        </td>
        <td className={`px-4 py-3 text-sm ${theme.text.secondary}`}>
          {process.pid}
        </td>
        <td className={`px-4 py-3 text-sm ${theme.text.primary}`}>
          <div className="flex items-center gap-2">
            <div className="w-16 h-2 rounded-full bg-gray-700">
              <div
                className={`h-full rounded-full ${
                  process.cpu_percent > 50 ? 'bg-red-500' :
                  process.cpu_percent > 25 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${Math.min(process.cpu_percent || 0, 100)}%` }}
              />
            </div>
            <span>{(process.cpu_percent || 0).toFixed(1)}%</span>
          </div>
        </td>
        <td className={`px-4 py-3 text-sm ${theme.text.primary}`}>
          {formatBytes((process.memory_mb || 0) * 1024 * 1024)}
        </td>
        <td className={`px-4 py-3 text-sm`}>
          <span className={`px-2 py-1 text-xs rounded-full ${
            process.status === 'running'
              ? 'bg-green-500/20 text-green-400'
              : process.status === 'sleeping'
              ? 'bg-blue-500/20 text-blue-400'
              : 'bg-gray-500/20 text-gray-400'
          }`}>
            {process.status}
          </span>
        </td>
        <td className="px-4 py-3 text-sm">
          {isCritical ? (
            /* Critical infrastructure is not killable — the backend refuses too (409) */
            <span title="Protected process — critical infrastructure cannot be terminated from the console.">
              <button
                disabled
                className="p-1 rounded text-gray-500 cursor-not-allowed"
              >
                <StopIcon className="h-4 w-4" />
              </button>
            </span>
          ) : (
            <span title={`Terminate ${process.name} (PID ${process.pid}) with SIGTERM`}>
              <button
                onClick={() => onKill(process)}
                disabled={killing}
                className="p-1 rounded text-red-400 hover:text-red-300 hover:bg-red-500/10 disabled:opacity-50"
              >
                <StopIcon className="h-4 w-4" />
              </button>
            </span>
          )}
        </td>
      </motion.tr>
    </>
  );
};

export default function System() {
  const { systemStatus, controlService, fetchSystemStatus } = useSystem();
  const { theme } = useTheme();
  const toast = useToast();
  const [historicalData, setHistoricalData] = useState({
    cpu: [],
    memory: [],
    gpu: [],
    network: [],
    diskIo: []
  });
  const [refreshInterval, setRefreshInterval] = useState(2000);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [selectedView, setSelectedView] = useState('overview');
  const [hardwareInfo, setHardwareInfo] = useState(null);
  const [diskIoStats, setDiskIoStats] = useState(null);
  const [networkStats, setNetworkStats] = useState({ in: 0, out: 0 });
  const [temperatures, setTemperatures] = useState({});
  const [errors, setErrors] = useState({
    hardware: null,
    diskIo: null,
    network: null
  });
  const [retryCount, setRetryCount] = useState({
    hardware: 0,
    diskIo: 0,
    network: 0
  });
  // Pending destructive action awaiting confirmation:
  // { type: 'kill', process } | { type: 'cache' }
  const [confirmAction, setConfirmAction] = useState(null);
  const [actionBusy, setActionBusy] = useState(false);
  const maxDataPoints = 30;
  const maxRetries = 3;
  const dataRef = useRef(historicalData);

  // Fetch data on mount and interval
  useEffect(() => {
    fetchHardwareInfo();
    fetchDiskIo();
    fetchNetworkStats();

    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchSystemStatus();
      fetchDiskIo();
      fetchNetworkStats();
      updateHistoricalData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);

  const fetchHardwareInfo = async () => {
    try {
      const response = await fetch('/api/v1/system/hardware', { credentials: 'include' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setHardwareInfo(data);
      setErrors(prev => ({ ...prev, hardware: null }));
      setRetryCount(prev => ({ ...prev, hardware: 0 }));
    } catch (error) {
      console.error('Failed to fetch hardware info:', error);
      const errorMsg = `Failed to load hardware information: ${error.message}`;
      setErrors(prev => ({ ...prev, hardware: errorMsg }));

      // Retry logic for transient failures
      if (retryCount.hardware < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, hardware: prev.hardware + 1 }));
          fetchHardwareInfo();
        }, 2000 * (retryCount.hardware + 1)); // Exponential backoff
      } else {
        toast.error(errorMsg);
      }
    }
  };

  const fetchDiskIo = async () => {
    try {
      const response = await fetch('/api/v1/system/disk-io', { credentials: 'include' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      setDiskIoStats(data);
      setErrors(prev => ({ ...prev, diskIo: null }));
      setRetryCount(prev => ({ ...prev, diskIo: 0 }));
    } catch (error) {
      console.error('Failed to fetch disk I/O:', error);
      const errorMsg = `Failed to load disk I/O statistics: ${error.message}`;
      setErrors(prev => ({ ...prev, diskIo: errorMsg }));

      // Retry logic for transient failures
      if (retryCount.diskIo < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, diskIo: prev.diskIo + 1 }));
          fetchDiskIo();
        }, 2000 * (retryCount.diskIo + 1));
      } else {
        toast.warning(errorMsg); // Use warning since disk I/O is less critical
      }
    }
  };

  const fetchNetworkStats = async () => {
    try {
      const response = await fetch('/api/v1/network/status', { credentials: 'include' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      // Network status endpoint returns different structure
      setNetworkStats({
        in: data.bytes_recv_per_sec || 0,
        out: data.bytes_sent_per_sec || 0
      });
      setErrors(prev => ({ ...prev, network: null }));
      setRetryCount(prev => ({ ...prev, network: 0 }));
    } catch (error) {
      console.error('Failed to fetch network stats:', error);
      const errorMsg = `Failed to load network statistics: ${error.message}`;
      setErrors(prev => ({ ...prev, network: errorMsg }));
      setNetworkStats({ in: 0, out: 0 }); // Fallback to zero

      // Retry logic for transient failures
      if (retryCount.network < maxRetries) {
        setTimeout(() => {
          setRetryCount(prev => ({ ...prev, network: prev.network + 1 }));
          fetchNetworkStats();
        }, 2000 * (retryCount.network + 1));
      } else {
        toast.warning(errorMsg);
      }
    }
  };

  const updateHistoricalData = () => {
    if (!systemStatus) return;

    const timestamp = new Date().toLocaleTimeString();

    const newData = {
      cpu: [...dataRef.current.cpu, {
        time: timestamp,
        usage: systemStatus.cpu?.percent || 0,
        temp: systemStatus.cpu?.temp || 0
      }].slice(-maxDataPoints),

      memory: [...dataRef.current.memory, {
        time: timestamp,
        used: ((systemStatus.memory?.used || 0) / (1024 * 1024 * 1024)).toFixed(2),
        percent: systemStatus.memory?.percent || 0
      }].slice(-maxDataPoints),

      gpu: systemStatus.gpu?.[0] ? [...dataRef.current.gpu, {
        time: timestamp,
        utilization: systemStatus.gpu[0]?.utilization || 0,
        memory: ((systemStatus.gpu[0]?.memory_used || 0) / (1024 * 1024 * 1024)).toFixed(2),
        temp: systemStatus.gpu[0]?.temperature || 0,
        power: systemStatus.gpu[0]?.power_draw || 0
      }].slice(-maxDataPoints) : dataRef.current.gpu,

      network: [...dataRef.current.network, {
        time: timestamp,
        in: networkStats.in,
        out: networkStats.out
      }].slice(-maxDataPoints),

      diskIo: diskIoStats ? [...dataRef.current.diskIo, {
        time: timestamp,
        read: (diskIoStats.read_bytes || 0) / 1024 / 1024,
        write: (diskIoStats.write_bytes || 0) / 1024 / 1024
      }].slice(-maxDataPoints) : dataRef.current.diskIo
    };

    dataRef.current = newData;
    setHistoricalData(newData);
  };

  const handleRestartService = async (serviceName) => {
    try {
      await controlService(serviceName, 'restart');
    } catch (error) {
      console.error('Error restarting service:', error);
    }
  };

  const handleKillProcess = async (process) => {
    setActionBusy(true);
    try {
      const response = await fetch(`/api/v1/system/process/${process.pid}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        if (data.exited) {
          toast.success(data.message || `Terminated ${process.name} (PID ${process.pid})`);
        } else {
          toast.warning(data.message || `SIGTERM sent to ${process.name}; it has not exited yet`);
        }
        fetchSystemStatus();
      } else {
        // 409 = protected process (backend explains why), 404 = already gone, 403 = access denied
        toast.error(data.detail || `Failed to terminate process (HTTP ${response.status})`);
      }
    } catch (error) {
      console.error('Error terminating process:', error);
      toast.error('Network error terminating process');
    } finally {
      setActionBusy(false);
      setConfirmAction(null);
    }
  };

  const handleClearCache = async () => {
    setActionBusy(true);
    try {
      const response = await fetch('/api/v1/system/cache', {
        method: 'DELETE',
        credentials: 'include'
      });
      const data = await response.json().catch(() => ({}));
      if (response.ok) {
        const keys = data.total_keys_deleted ?? 0;
        const tmpFiles = (data.tmp_files_removed || []).length;
        toast.success(
          `Cache cleared: ${keys} cache ${keys === 1 ? 'key' : 'keys'} deleted` +
          (tmpFiles ? `, ${tmpFiles} temp ${tmpFiles === 1 ? 'file' : 'files'} removed` : '')
        );
        if ((data.errors || []).length > 0) {
          toast.warning(`Some cache namespaces could not be cleared: ${data.errors[0]}`);
        }
      } else {
        toast.error(data.detail || `Failed to clear cache (HTTP ${response.status})`);
      }
    } catch (error) {
      console.error('Error clearing cache:', error);
      toast.error('Network error clearing cache');
    } finally {
      setActionBusy(false);
      setConfirmAction(null);
    }
  };

  if (!systemStatus || !systemStatus.cpu) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <ArrowPathIcon className="h-12 w-12 text-purple-500 animate-spin mx-auto mb-4" />
          <h2 className={`text-xl font-semibold mb-2 ${theme.text.primary}`}>Loading System Data</h2>
          <p className={theme.text.secondary}>Please wait while we gather system information...</p>
        </div>
      </div>
    );
  }

  const chartTheme = {
    textColor: '#9ca3af',
    gridColor: 'rgba(255,255,255,0.1)',
    tooltipBackground: 'rgba(0,0,0,0.9)',
    tooltipBorder: '#6366f1',
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary}`}>
            System Resources Monitor
          </h1>
          <p className={`mt-2 ${theme.text.secondary}`}>
            Real-time system performance and resource monitoring
          </p>
        </div>

        <div className="flex items-center gap-4">
          <select
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-white"
          >
            <option value={1000}>1 second</option>
            <option value={2000}>2 seconds</option>
            <option value={5000}>5 seconds</option>
            <option value={10000}>10 seconds</option>
          </select>

          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-lg flex items-center gap-2 ${
              autoRefresh
                ? 'bg-green-600 text-white'
                : 'bg-gray-700 text-gray-300'
            }`}
          >
            <ArrowPathIcon className={`h-5 w-5 ${autoRefresh ? 'animate-spin' : ''}`} />
            {autoRefresh ? 'Auto-refresh On' : 'Auto-refresh Off'}
          </button>

          <span title="Clear app-level caches (Redis cache namespaces + temp artifacts). Sessions and quotas are untouched.">
            <button
              onClick={() => setConfirmAction({ type: 'cache' })}
              disabled={actionBusy}
              className="px-4 py-2 rounded-lg bg-gray-700 text-gray-200 hover:bg-gray-600 disabled:opacity-50 flex items-center gap-2"
            >
              <TrashIcon className="h-5 w-5" />
              Clear Cache
            </button>
          </span>
        </div>
      </div>

      {/* View Selector */}
      <div className="flex gap-1 p-1 bg-gray-800/50 rounded-lg w-fit">
        {[
          { id: 'overview', name: 'Overview', icon: ChartBarIcon },
          { id: 'processes', name: 'Processes', icon: RectangleStackIcon },
          { id: 'hardware', name: 'Hardware', icon: ComputerDesktopIcon },
          { id: 'network', name: 'Network', icon: WifiIcon }
        ].map(({ id, name, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setSelectedView(id)}
            className={`px-4 py-2 rounded-md text-sm transition-all flex items-center gap-2 ${
              selectedView === id
                ? 'bg-purple-600 text-white shadow-lg'
                : 'text-gray-400 hover:text-white hover:bg-purple-600/20'
            }`}
          >
            <Icon className="h-4 w-4" />
            {name}
          </button>
        ))}
      </div>

      {/* Overview View */}
      {selectedView === 'overview' && (
        <>
          {/* System Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-br from-blue-500/10 to-cyan-500/10 border border-blue-500/20 rounded-2xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    CPU Usage
                    <MuiTooltip title="Share of total processor capacity in use across all cores right now. Sustained high values indicate the machine is compute-bound and may slow down." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </p>
                  <p className={`text-3xl font-bold ${theme.text.primary}`}>
                    {systemStatus.cpu.percent.toFixed(1)}%
                  </p>
                  <p className={`text-xs mt-1 ${theme.text.secondary}`}>
                    {systemStatus.cpu?.cores || 0} cores @ {(systemStatus.cpu?.freq_current / 1000).toFixed(2) || 0} GHz
                  </p>
                </div>
                <CpuChipIcon className="h-12 w-12 text-blue-400" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/20 rounded-2xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    Memory
                    <MuiTooltip title="Portion of system RAM currently allocated. When this approaches 100% the system swaps to disk, which sharply degrades performance." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </p>
                  <p className={`text-3xl font-bold ${theme.text.primary}`}>
                    {systemStatus.memory?.percent?.toFixed(1) || 0}%
                  </p>
                  <p className={`text-xs mt-1 ${theme.text.secondary}`}>
                    {formatBytes(systemStatus.memory?.used || 0)} of {formatBytes(systemStatus.memory?.total || 0)}
                  </p>
                </div>
                <CircleStackIcon className="h-12 w-12 text-green-400" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-purple-500/10 to-indigo-500/10 border border-purple-500/20 rounded-2xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    Disk Usage
                    <MuiTooltip title="How full the primary storage volume is. A nearly full disk can stop services from writing logs or data and cause failures." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </p>
                  <p className={`text-3xl font-bold ${theme.text.primary}`}>
                    {systemStatus.disk?.percent?.toFixed(1) || 0}%
                  </p>
                  <p className={`text-xs mt-1 ${theme.text.secondary}`}>
                    {formatBytes(systemStatus.disk?.used || 0)} of {formatBytes(systemStatus.disk?.total || 0)}
                  </p>
                </div>
                <ServerIcon className="h-12 w-12 text-purple-400" />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="bg-gradient-to-br from-yellow-500/10 to-amber-500/10 border border-yellow-500/20 rounded-2xl p-6"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className={`text-sm ${theme.text.secondary}`}>
                    System Uptime
                    <MuiTooltip title="How long the machine has run since its last reboot. A recent reset can explain why other metrics look unusually low." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </p>
                  <p className={`text-2xl font-bold ${theme.text.primary}`}>
                    {formatUptime(systemStatus.uptime || 0)}
                  </p>
                  <p className={`text-xs mt-1 ${theme.text.secondary}`}>
                    Load: {systemStatus.load_average?.map(l => l.toFixed(2)).join(', ') || 'N/A'}
                    <MuiTooltip title="Average number of processes waiting to run over the last 1, 5, and 15 minutes. A value above your core count means the CPU is over-subscribed." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </p>
                </div>
                <ClockIcon className="h-12 w-12 text-yellow-400" />
              </div>
            </motion.div>
          </div>

          {/* Real-time Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU Chart */}
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl p-6">
              <h2 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${theme.text.primary}`}>
                <CpuChipIcon className="h-5 w-5" />
                CPU Usage History
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={historicalData.cpu}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                  <XAxis dataKey="time" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                  <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartTheme.tooltipBackground,
                      border: `1px solid ${chartTheme.tooltipBorder}`,
                      borderRadius: '8px'
                    }}
                  />
                  <Area type="monotone" dataKey="usage" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} name="CPU %" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Memory Chart */}
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl p-6">
              <h2 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${theme.text.primary}`}>
                <CircleStackIcon className="h-5 w-5" />
                Memory Usage History
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={historicalData.memory}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                  <XAxis dataKey="time" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                  <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} domain={[0, 100]} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartTheme.tooltipBackground,
                      border: `1px solid ${chartTheme.tooltipBorder}`,
                      borderRadius: '8px'
                    }}
                  />
                  <Line type="monotone" dataKey="percent" stroke="#10b981" strokeWidth={2} dot={false} name="Memory %" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* GPU Section */}
          {systemStatus.gpu && systemStatus.gpu.length > 0 && (
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl p-6">
              <h2 className={`text-lg font-semibold mb-6 flex items-center gap-2 ${theme.text.primary}`}>
                <FireIcon className="h-5 w-5" />
                GPU Performance - {systemStatus.gpu[0]?.name || 'Unknown GPU'}
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div className="bg-gray-800/50 rounded-xl p-4">
                  <div className={`text-sm ${theme.text.secondary} mb-2`}>
                    GPU Utilization
                    <MuiTooltip title="Percent of the graphics processor actively doing work. For AI inference, high utilization means the GPU is busy serving model requests." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </div>
                  <div className={`text-2xl font-bold ${theme.text.primary}`}>
                    {systemStatus.gpu[0]?.utilization?.toFixed(1) || 0}%
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-xl p-4">
                  <div className={`text-sm ${theme.text.secondary} mb-2`}>
                    VRAM Usage
                    <MuiTooltip title="GPU video memory in use versus total. Models must fit in VRAM to load; running out forces them onto slower system memory or fails." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </div>
                  <div className={`text-2xl font-bold ${theme.text.primary}`}>
                    {formatBytes(systemStatus.gpu[0]?.memory_used || 0)}
                  </div>
                  <div className={`text-xs ${theme.text.secondary}`}>
                    of {formatBytes(systemStatus.gpu[0]?.memory_total || 0)}
                  </div>
                </div>

                <div className="bg-gray-800/50 rounded-xl p-4">
                  <div className={`text-sm ${theme.text.secondary} mb-2`}>
                    Temperature
                    <MuiTooltip title="Current GPU core temperature. Cards throttle their speed to protect the hardware once they get too hot (typically above 80–85°C)." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </div>
                  <TemperatureGauge temperature={systemStatus.gpu[0]?.temperature || 0} theme={theme} />
                </div>

                <div className="bg-gray-800/50 rounded-xl p-4">
                  <div className={`text-sm ${theme.text.secondary} mb-2`}>
                    Power Draw
                    <MuiTooltip title="Watts the GPU is currently pulling versus its rated limit. Sitting near the limit means the card is working at full capacity." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </div>
                  <div className={`text-2xl font-bold ${theme.text.primary}`}>
                    {systemStatus.gpu[0]?.power_draw?.toFixed(0) || 0}W
                  </div>
                  <div className={`text-xs ${theme.text.secondary}`}>
                    / {systemStatus.gpu[0]?.power_limit?.toFixed(0) || 0}W
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <h3 className={`text-sm font-medium mb-3 ${theme.text.secondary}`}>
                    GPU Utilization & Temperature
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={historicalData.gpu}>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                      <XAxis dataKey="time" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                      <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} domain={[0, 100]} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: chartTheme.tooltipBackground,
                          border: `1px solid ${chartTheme.tooltipBorder}`,
                          borderRadius: '8px'
                        }}
                      />
                      <Line type="monotone" dataKey="utilization" stroke="#f59e0b" strokeWidth={2} dot={false} name="Utilization %" />
                      <Line type="monotone" dataKey="temp" stroke="#ef4444" strokeWidth={2} dot={false} name="Temperature °C" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div>
                  <h3 className={`text-sm font-medium mb-3 ${theme.text.secondary}`}>
                    VRAM Usage & Power Draw
                  </h3>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={historicalData.gpu}>
                      <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                      <XAxis dataKey="time" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                      <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: chartTheme.tooltipBackground,
                          border: `1px solid ${chartTheme.tooltipBorder}`,
                          borderRadius: '8px'
                        }}
                      />
                      <Line type="monotone" dataKey="memory" stroke="#8b5cf6" strokeWidth={2} dot={false} name="Memory GB" />
                      <Line type="monotone" dataKey="power" stroke="#06b6d4" strokeWidth={2} dot={false} name="Power W" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>
          )}

          {/* Network & Disk I/O */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Network Bandwidth */}
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl p-6">
              <h2 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${theme.text.primary}`}>
                <WifiIcon className="h-5 w-5" />
                Network Bandwidth
                <MuiTooltip title="Live inbound (download) and outbound (upload) network throughput. Spikes can reveal heavy transfers, syncs, or unexpected traffic." arrow>
                  <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                </MuiTooltip>
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={historicalData.network}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                  <XAxis dataKey="time" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                  <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartTheme.tooltipBackground,
                      border: `1px solid ${chartTheme.tooltipBorder}`,
                      borderRadius: '8px'
                    }}
                  />
                  <Area type="monotone" dataKey="in" stackId="1" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Download" />
                  <Area type="monotone" dataKey="out" stackId="1" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} name="Upload" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Disk I/O */}
            <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl p-6">
              <h2 className={`text-lg font-semibold mb-4 flex items-center gap-2 ${theme.text.primary}`}>
                <ServerIcon className="h-5 w-5" />
                Disk I/O Performance
                <MuiTooltip title="Rate of data being read from and written to disk. High sustained I/O can bottleneck databases and file-heavy workloads even when CPU is idle." arrow>
                  <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                </MuiTooltip>
              </h2>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={historicalData.diskIo}>
                  <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                  <XAxis dataKey="time" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                  <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: chartTheme.tooltipBackground,
                      border: `1px solid ${chartTheme.tooltipBorder}`,
                      borderRadius: '8px'
                    }}
                  />
                  <Area type="monotone" dataKey="read" stackId="1" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} name="Read MB" />
                  <Area type="monotone" dataKey="write" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} name="Write MB" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* CPU Cores */}
          <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl p-6">
            <h2 className={`text-lg font-semibold mb-4 ${theme.text.primary}`}>
              CPU Cores Usage
            </h2>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={systemStatus.cpu?.per_cpu?.map((usage, index) => ({
                name: `Core ${index}`,
                usage: usage || 0
              })) || []}>
                <CartesianGrid strokeDasharray="3 3" stroke={chartTheme.gridColor} />
                <XAxis dataKey="name" stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} />
                <YAxis stroke={chartTheme.textColor} tick={{ fill: chartTheme.textColor }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: chartTheme.tooltipBackground,
                    border: `1px solid ${chartTheme.tooltipBorder}`,
                    borderRadius: '8px'
                  }}
                />
                <Bar dataKey="usage" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {/* Processes View */}
      {selectedView === 'processes' && (
        <div className="bg-gray-800/40 border border-gray-700/50 rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-gray-700">
            <h3 className={`text-lg font-semibold ${theme.text.primary} flex items-center gap-2`}>
              <RectangleStackIcon className="h-5 w-5 text-blue-500" />
              Top Processes by CPU Usage
            </h3>
            <p className={`text-sm mt-1 ${theme.text.secondary}`}>
              Showing {systemStatus.processes?.length || 0} processes
            </p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-800/50">
                  <th className={`px-4 py-3 text-left text-xs font-medium uppercase ${theme.text.secondary}`}>
                    Process Name
                  </th>
                  <th className={`px-4 py-3 text-left text-xs font-medium uppercase ${theme.text.secondary}`}>
                    PID
                  </th>
                  <th className={`px-4 py-3 text-left text-xs font-medium uppercase ${theme.text.secondary}`}>
                    CPU %
                    <MuiTooltip title="Share of CPU this individual process is consuming. The biggest values here usually explain a high overall CPU reading." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </th>
                  <th className={`px-4 py-3 text-left text-xs font-medium uppercase ${theme.text.secondary}`}>
                    Memory
                    <MuiTooltip title="RAM held by this process. A single process growing without bound here can be a memory leak." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </th>
                  <th className={`px-4 py-3 text-left text-xs font-medium uppercase ${theme.text.secondary}`}>
                    Status
                    <MuiTooltip title="The process state: 'running' is actively using the CPU, while 'sleeping' is idle and waiting — sleeping is normal and not a problem." arrow>
                      <InfoOutlinedIcon sx={{ fontSize: 14, ml: 0.5, opacity: 0.6, verticalAlign: 'middle', cursor: 'help' }} />
                    </MuiTooltip>
                  </th>
                  <th className={`px-4 py-3 text-left text-xs font-medium uppercase ${theme.text.secondary}`}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {systemStatus.processes?.slice(0, 20).map((process) => (
                  <ProcessRow
                    key={process.pid}
                    process={process}
                    theme={theme}
                    killing={actionBusy}
                    onKill={(proc) => setConfirmAction({ type: 'kill', process: proc })}
                  />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Hardware View */}
      {selectedView === 'hardware' && (
        <>
          {/* Error Alert for Hardware Info */}
          {errors.hardware && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-red-900/20 border border-red-500/50 rounded-xl p-4 flex items-start gap-3"
            >
              <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-200 text-sm font-medium">{errors.hardware}</p>
                {retryCount.hardware > 0 && retryCount.hardware < maxRetries && (
                  <p className="text-red-300 text-xs mt-1">Retrying... (Attempt {retryCount.hardware}/{maxRetries})</p>
                )}
              </div>
              <button
                onClick={fetchHardwareInfo}
                className="px-3 py-1 bg-red-600 text-white text-xs rounded hover:bg-red-500 transition-colors"
              >
                Retry Now
              </button>
            </motion.div>
          )}

          {/* Hardware Info Grid */}
          {hardwareInfo && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* CPU Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
          >
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <CpuChipIcon className="h-5 w-5 text-blue-500" />
              CPU Information
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Model:</span>
                <span className={`${theme.text.primary} font-mono text-xs`}>
                  {hardwareInfo.cpu.model}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Cores:</span>
                <span className={theme.text.primary}>
                  {hardwareInfo.cpu.cores} ({hardwareInfo.cpu.threads} threads)
                </span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Base Frequency:</span>
                <span className={theme.text.primary}>{hardwareInfo.cpu.baseFreq}</span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Max Frequency:</span>
                <span className={theme.text.primary}>{hardwareInfo.cpu.maxFreq}</span>
              </div>
            </div>
          </motion.div>

          {/* GPU Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
          >
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <FireIcon className="h-5 w-5 text-red-500" />
              GPU Information
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Model:</span>
                <span className={`${theme.text.primary} font-mono text-xs`}>
                  {hardwareInfo.gpu.model}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>VRAM:</span>
                <span className={theme.text.primary}>{hardwareInfo.gpu.vram}</span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Driver:</span>
                <span className={theme.text.primary}>{hardwareInfo.gpu.driver}</span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>CUDA:</span>
                <span className={theme.text.primary}>{hardwareInfo.gpu.cuda}</span>
              </div>
            </div>
          </motion.div>

          {/* Memory Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
          >
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <CircleStackIcon className="h-5 w-5 text-green-500" />
              Memory Information
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Total:</span>
                <span className={theme.text.primary}>
                  {hardwareInfo.memory.total} {hardwareInfo.memory.type}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Configuration:</span>
                <span className={theme.text.primary}>{hardwareInfo.memory.slots}</span>
              </div>
            </div>
          </motion.div>

          {/* Storage Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
          >
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <ServerIcon className="h-5 w-5 text-indigo-500" />
              Storage Information
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Primary:</span>
                <span className={theme.text.primary}>{hardwareInfo.storage.primary}</span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Secondary:</span>
                <span className={theme.text.primary}>{hardwareInfo.storage.secondary}</span>
              </div>
            </div>
          </motion.div>

          {/* OS Details */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6"
          >
            <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
              <BoltIcon className="h-5 w-5 text-orange-500" />
              Operating System
            </h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className={theme.text.secondary}>OS:</span>
                <span className={theme.text.primary}>
                  {hardwareInfo.os.name} {hardwareInfo.os.version}
                </span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Kernel:</span>
                <span className={theme.text.primary}>{hardwareInfo.os.kernel}</span>
              </div>
              <div className="flex justify-between">
                <span className={theme.text.secondary}>Desktop:</span>
                <span className={theme.text.primary}>{hardwareInfo.os.desktop}</span>
              </div>
            </div>
          </motion.div>
            </div>
          )}
        </>
      )}

      {/* Network View */}
      {selectedView === 'network' && (
        <div className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-6">
          <h3 className={`text-lg font-semibold ${theme.text.primary} mb-4 flex items-center gap-2`}>
            <WifiIcon className="h-5 w-5 text-blue-500" />
            Network Statistics
          </h3>
          <div className="text-center py-8">
            <p className={`${theme.text.secondary} mb-4`}>
              Network statistics and configuration coming soon...
            </p>
            <p className={`text-sm ${theme.text.secondary}`}>
              This feature will include network interfaces, bandwidth monitoring, and connection details.
            </p>
          </div>
        </div>
      )}

      {/* Confirm destructive actions (kill process / clear cache) */}
      <AnimatePresence>
        {confirmAction && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
            onClick={() => !actionBusy && setConfirmAction(null)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-gray-800 rounded-2xl border border-gray-700 p-6 max-w-md w-full shadow-2xl"
            >
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-3 rounded-xl ${confirmAction.type === 'kill' ? 'bg-red-500/10' : 'bg-yellow-500/10'}`}>
                  {confirmAction.type === 'kill' ? (
                    <StopIcon className="h-6 w-6 text-red-400" />
                  ) : (
                    <TrashIcon className="h-6 w-6 text-yellow-400" />
                  )}
                </div>
                <h3 className={`text-xl font-bold ${theme.text.primary}`}>
                  {confirmAction.type === 'kill' ? 'Terminate Process?' : 'Clear App Caches?'}
                </h3>
              </div>

              {confirmAction.type === 'kill' ? (
                <p className={`${theme.text.secondary} mb-6`}>
                  Send SIGTERM to{' '}
                  <span className={`font-mono ${theme.text.primary}`}>
                    {confirmAction.process?.name}
                  </span>{' '}
                  (PID {confirmAction.process?.pid})? The process will be asked to shut
                  down gracefully. Critical infrastructure processes are refused by the server.
                </p>
              ) : (
                <p className={`${theme.text.secondary} mb-6`}>
                  This deletes the app-level Redis cache namespaces (API/analytics/settings
                  caches and metrics history) plus known temp artifacts. Sessions, quotas,
                  and rate limits are not touched. Cached data will be recomputed on demand.
                </p>
              )}

              <div className="flex gap-3">
                <button
                  onClick={() => setConfirmAction(null)}
                  disabled={actionBusy}
                  className="flex-1 px-4 py-2 rounded-xl bg-gray-700 text-white font-medium hover:bg-gray-600 transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={() =>
                    confirmAction.type === 'kill'
                      ? handleKillProcess(confirmAction.process)
                      : handleClearCache()
                  }
                  disabled={actionBusy}
                  className={`flex-1 px-4 py-2 rounded-xl text-white font-medium transition-colors disabled:opacity-50 ${
                    confirmAction.type === 'kill'
                      ? 'bg-red-600 hover:bg-red-500'
                      : 'bg-yellow-600 hover:bg-yellow-500'
                  }`}
                >
                  {actionBusy
                    ? 'Working...'
                    : confirmAction.type === 'kill'
                    ? 'Terminate'
                    : 'Clear Cache'}
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
