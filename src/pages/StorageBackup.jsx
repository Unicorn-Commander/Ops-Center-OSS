import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useTheme } from '../contexts/ThemeContext';
import {
  ChartPieIcon,
  ArrowPathIcon,
  CloudArrowDownIcon,
  CloudArrowUpIcon,
  FolderIcon,
  ServerIcon,
  ClockIcon,
  Cog6ToothIcon,
  TrashIcon,
  DocumentDuplicateIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  InformationCircleIcon,
  CalendarIcon,
  ArchiveBoxIcon,
  CloudIcon,
  ShieldCheckIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { getTooltip } from '../data/tooltipContent';
import HelpTooltip from '../components/HelpTooltip';
import CronBuilder from '../components/CronBuilder';
import BackupRestoreModal from '../components/BackupRestoreModal';
import CloudBackupSetup from '../components/CloudBackupSetup';
import BackupVerification from '../components/BackupVerification';
import StorageOptimizer from '../components/StorageOptimizer';

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: {
      duration: 0.5
    }
  }
};

export default function StorageBackup() {
  const { theme, currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('storage');
  const [storageData, setStorageData] = useState(null);
  const [backupData, setBackupData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showBackupModal, setShowBackupModal] = useState(false);
  const [showRestoreModal, setShowRestoreModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedBackup, setSelectedBackup] = useState(null);
  const [cloudConfig, setCloudConfig] = useState(null);
  const [backupConfig, setBackupConfig] = useState({
    schedule: '0 2 * * *',
    retention_days: 7,
    backup_location: '/home/ucadmin/UC-1-Pro/backups',
    backup_enabled: true
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    await Promise.all([loadStorageData(), loadBackupData(), loadCloudConfig()]);
  };

  const loadStorageData = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/storage/info');
      if (!response.ok) throw new Error('Failed to fetch storage data');
      const data = await response.json();
      setStorageData(data);
    } catch (error) {
      console.error('Failed to load storage data:', error);
      // Fallback to mock data for development
      setStorageData({
        total_space: 1000 * 1024 * 1024 * 1024,
        used_space: 350 * 1024 * 1024 * 1024,
        free_space: 650 * 1024 * 1024 * 1024,
        volumes: []
      });
    } finally {
      setLoading(false);
    }
  };

  const loadBackupData = async () => {
    try {
      const response = await fetch('/api/v1/backups');
      if (!response.ok) throw new Error('Failed to fetch backup data');
      const data = await response.json();
      setBackupData(data);

      if (data.config) {
        setBackupConfig(data.config);
      }
    } catch (error) {
      console.error('Failed to load backup data:', error);
      // Fallback for development
      setBackupData({
        backup_enabled: true,
        schedule: '0 2 * * *',
        last_backup: new Date().toISOString(),
        next_backup: new Date(Date.now() + 86400000).toISOString(),
        retention_days: 7,
        backups: []
      });
    }
  };

  const loadCloudConfig = async () => {
    try {
      const response = await fetch('/api/v1/backups/cloud-config');
      if (response.ok) {
        const data = await response.json();
        setCloudConfig(data);
      }
    } catch (error) {
      console.error('Failed to load cloud config:', error);
    }
  };

  const refreshData = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleCreateBackup = async () => {
    try {
      const response = await fetch('/api/v1/backups/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ backup_type: 'manual' }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Backup created:', result.backup_id);
        await loadBackupData();
        alert('Backup created successfully!');
      } else {
        throw new Error('Failed to create backup');
      }
    } catch (error) {
      console.error('Error creating backup:', error);
      alert('Failed to create backup: ' + error.message);
    }
  };

  const handleRestoreBackup = async (backupId, options) => {
    try {
      const response = await fetch(`/api/v1/backups/${backupId}/restore`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(options),
      });

      if (!response.ok) throw new Error('Failed to restore backup');

      const result = await response.json();
      console.log('Backup restored:', result);
      return result;
    } catch (error) {
      console.error('Error restoring backup:', error);
      throw error;
    }
  };

  const handleDeleteBackup = async (backupId) => {
    if (!confirm(`Are you sure you want to delete backup ${backupId}?`)) {
      return;
    }

    try {
      const response = await fetch(`/api/v1/backups/${backupId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        console.log('Backup deleted:', backupId);
        await loadBackupData();
        alert('Backup deleted successfully');
      } else {
        throw new Error('Failed to delete backup');
      }
    } catch (error) {
      console.error('Error deleting backup:', error);
      alert('Failed to delete backup: ' + error.message);
    }
  };

  const handleSaveBackupConfig = async (config) => {
    try {
      const response = await fetch('/api/v1/backups/config', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Backup configuration saved:', result);
        await loadBackupData();
        setShowScheduleModal(false);
        alert('Backup configuration saved successfully!');
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch (error) {
      console.error('Error saving backup configuration:', error);
      alert('Failed to save configuration: ' + error.message);
    }
  };

  const handleSaveCloudConfig = async (config) => {
    try {
      const response = await fetch('/api/v1/backups/cloud-config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        await loadCloudConfig();
        alert('Cloud backup configuration saved successfully!');
      } else {
        throw new Error('Failed to save cloud configuration');
      }
    } catch (error) {
      console.error('Error saving cloud config:', error);
      alert('Failed to save cloud configuration: ' + error.message);
    }
  };

  const handleTestCloudConnection = async (config) => {
    try {
      const response = await fetch('/api/v1/backups/cloud-config/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      const result = await response.json();
      return result;
    } catch (error) {
      return { success: false, message: error.message };
    }
  };

  const handleVerifyBackup = async (backupId) => {
    try {
      const response = await fetch(`/api/v1/backups/${backupId}/verify`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Verification failed');

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Verification error:', error);
      return {
        status: 'error',
        message: error.message
      };
    }
  };

  const handleCleanup = async (items) => {
    try {
      const response = await fetch('/api/v1/storage/cleanup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items }),
      });

      if (!response.ok) throw new Error('Cleanup failed');

      const result = await response.json();
      await loadStorageData();
      return result;
    } catch (error) {
      console.error('Cleanup error:', error);
      throw error;
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'text-green-600 dark:text-green-400';
      case 'warning': return 'text-yellow-600 dark:text-yellow-400';
      case 'error': return 'text-red-600 dark:text-red-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy': return CheckCircleIcon;
      case 'warning': return ExclamationTriangleIcon;
      case 'error': return ExclamationTriangleIcon;
      default: return InformationCircleIcon;
    }
  };

  if (loading || !storageData || !backupData) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <motion.div
      className="space-y-6"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Storage & Backup Management
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Monitor storage usage, manage volumes, and configure backups
          </p>
        </div>

        <button
          onClick={refreshData}
          disabled={refreshing}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </motion.div>

      {/* Tab Navigation */}
      <motion.div variants={itemVariants} className="border-b dark:border-gray-700">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {[
            { id: 'storage', label: 'Storage Overview', icon: ServerIcon },
            { id: 'volumes', label: 'Volume Management', icon: FolderIcon },
            { id: 'backup', label: 'Backup & Recovery', icon: ArchiveBoxIcon },
            { id: 'schedule', label: 'Backup Scheduling', icon: CalendarIcon },
            { id: 'cloud', label: 'Cloud Backup', icon: CloudIcon },
            { id: 'verification', label: 'Verification', icon: ShieldCheckIcon },
            { id: 'optimizer', label: 'Storage Optimizer', icon: SparklesIcon }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <tab.icon className="h-5 w-5" />
                {tab.label}
              </div>
            </button>
          ))}
        </nav>
      </motion.div>

      {/* Storage Overview Tab */}
      {activeTab === 'storage' && (
        <>
          <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Total Storage</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatBytes(storageData.total_space)}
                  </p>
                </div>
                <ServerIcon className="h-8 w-8 text-blue-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Used Storage</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatBytes(storageData.used_space)}
                  </p>
                  <p className="text-sm text-gray-500">
                    {((storageData.used_space / storageData.total_space) * 100).toFixed(1)}% used
                  </p>
                </div>
                <ChartPieIcon className="h-8 w-8 text-yellow-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Available Storage</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-white">
                    {formatBytes(storageData.free_space)}
                  </p>
                  <p className="text-sm text-gray-500">
                    {((storageData.free_space / storageData.total_space) * 100).toFixed(1)}% free
                  </p>
                </div>
                <CloudArrowDownIcon className="h-8 w-8 text-green-500" />
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">Storage Usage</h2>
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mb-2">
                <span>Used: {formatBytes(storageData.used_space)}</span>
                <span>Free: {formatBytes(storageData.free_space)}</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                <div
                  className="bg-blue-600 h-4 rounded-full"
                  style={{ width: `${(storageData.used_space / storageData.total_space) * 100}%` }}
                ></div>
              </div>
            </div>

            {storageData.volumes && storageData.volumes.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
                {Object.entries(
                  storageData.volumes.reduce((acc, volume) => {
                    acc[volume.type] = (acc[volume.type] || 0) + volume.size;
                    return acc;
                  }, {})
                ).map(([type, size]) => (
                  <div key={type} className="text-center">
                    <p className="text-2xl font-bold text-gray-900 dark:text-white">
                      {formatBytes(size)}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{type}</p>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </>
      )}

      {/* Volume Management Tab */}
      {activeTab === 'volumes' && (
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Volume Management</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Monitor and manage storage volumes
            </p>
          </div>

          <div className="p-6 space-y-4">
            {storageData.volumes && storageData.volumes.length > 0 ? (
              storageData.volumes.map((volume) => {
                const HealthIcon = getHealthIcon(volume.health);
                return (
                  <div
                    key={volume.name}
                    className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <FolderIcon className="h-6 w-6 text-blue-500" />
                          <div>
                            <h3 className="font-medium text-gray-900 dark:text-white">{volume.name}</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">{volume.path}</p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Size:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {formatBytes(volume.size)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Type:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {volume.type}
                            </span>
                          </div>
                          <div className="flex items-center">
                            <span className="text-gray-600 dark:text-gray-400">Health:</span>
                            <HealthIcon className={`ml-2 h-4 w-4 ${getHealthColor(volume.health)}`} />
                            <span className={`ml-1 font-medium capitalize ${getHealthColor(volume.health)}`}>
                              {volume.health}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Last Access:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {formatDate(volume.last_accessed)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                <FolderIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p>No volumes found</p>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Backup & Recovery Tab */}
      {activeTab === 'backup' && (
        <>
          <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Backup Status</p>
                  <p className={`text-lg font-bold ${backupData.backup_enabled ? 'text-green-600' : 'text-red-600'}`}>
                    {backupData.backup_enabled ? 'Enabled' : 'Disabled'}
                  </p>
                </div>
                <ArchiveBoxIcon className={`h-8 w-8 ${backupData.backup_enabled ? 'text-green-500' : 'text-red-500'}`} />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Last Backup</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {formatDate(backupData.last_backup)}
                  </p>
                </div>
                <ClockIcon className="h-8 w-8 text-blue-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Next Backup</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {formatDate(backupData.next_backup)}
                  </p>
                </div>
                <CalendarIcon className="h-8 w-8 text-yellow-500" />
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600 dark:text-gray-400">Retention</p>
                  <p className="text-lg font-bold text-gray-900 dark:text-white">
                    {backupData.retention_days} days
                  </p>
                </div>
                <TrashIcon className="h-8 w-8 text-purple-500" />
              </div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="flex gap-4">
            <button
              onClick={handleCreateBackup}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
            >
              <CloudArrowUpIcon className="h-5 w-5" />
              Start Backup Now
            </button>
            <button
              onClick={() => setShowScheduleModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <Cog6ToothIcon className="h-5 w-5" />
              Configure Schedule
            </button>
          </motion.div>

          <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow">
            <div className="p-6 border-b dark:border-gray-700">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Backup History</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                Recent backup operations and their status
              </p>
            </div>

            <div className="p-6 space-y-4">
              {backupData.backups && backupData.backups.length > 0 ? (
                backupData.backups.map((backup) => (
                  <div
                    key={backup.id}
                    className="border dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <ArchiveBoxIcon className="h-6 w-6 text-green-500" />
                          <div>
                            <h3 className="font-medium text-gray-900 dark:text-white">{backup.id}</h3>
                            <p className="text-sm text-gray-600 dark:text-gray-400">
                              {formatDate(backup.timestamp)}
                            </p>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Size:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {formatBytes(backup.size)}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Type:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {backup.type}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Duration:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {backup.duration}
                            </span>
                          </div>
                          <div>
                            <span className="text-gray-600 dark:text-gray-400">Files:</span>
                            <span className="ml-2 font-medium text-gray-900 dark:text-white">
                              {backup.files_count?.toLocaleString() || 'N/A'}
                            </span>
                          </div>
                          <div className="flex items-center">
                            <CheckCircleIcon className="h-4 w-4 text-green-500 mr-1" />
                            <span className="font-medium text-green-600 dark:text-green-400 capitalize">
                              {backup.status}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedBackup(backup);
                            setShowRestoreModal(true);
                          }}
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 flex items-center gap-1"
                        >
                          <CloudArrowDownIcon className="h-4 w-4" />
                          Restore
                        </button>
                        <button
                          onClick={() => handleDeleteBackup(backup.id)}
                          className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700 flex items-center gap-1"
                        >
                          <TrashIcon className="h-4 w-4" />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-gray-500 dark:text-gray-400">
                  <ArchiveBoxIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
                  <p>No backups found. Create your first backup using the "Create Backup" button above.</p>
                </div>
              )}
            </div>
          </motion.div>
        </>
      )}

      {/* Backup Scheduling Tab */}
      {activeTab === 'schedule' && (
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Backup Schedule Configuration
          </h2>

          <div className="space-y-6">
            <CronBuilder
              value={backupConfig.schedule}
              onChange={(cron) => setBackupConfig({ ...backupConfig, schedule: cron })}
            />

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Retention Days
              </label>
              <input
                type="number"
                value={backupConfig.retention_days}
                onChange={(e) => setBackupConfig({ ...backupConfig, retention_days: parseInt(e.target.value) })}
                min="1"
                max="365"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
              <p className="mt-1 text-sm text-gray-500">
                Number of days to keep backups before automatic deletion
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Backup Location
              </label>
              <input
                type="text"
                value={backupConfig.backup_location}
                onChange={(e) => setBackupConfig({ ...backupConfig, backup_location: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="backup-enabled"
                checked={backupConfig.backup_enabled}
                onChange={(e) => setBackupConfig({ ...backupConfig, backup_enabled: e.target.checked })}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <label htmlFor="backup-enabled" className="ml-2 block text-sm text-gray-900 dark:text-white">
                Enable automatic backups
              </label>
            </div>

            <div className="flex justify-end pt-4 border-t dark:border-gray-700">
              <button
                onClick={() => handleSaveBackupConfig(backupConfig)}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Save Configuration
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {/* Cloud Backup Tab */}
      {activeTab === 'cloud' && (
        <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <CloudBackupSetup
            existingConfig={cloudConfig}
            onSave={handleSaveCloudConfig}
            onTest={handleTestCloudConnection}
          />
        </motion.div>
      )}

      {/* Verification Tab */}
      {activeTab === 'verification' && (
        <motion.div variants={itemVariants}>
          <BackupVerification
            backups={backupData.backups || []}
            onVerify={handleVerifyBackup}
          />
        </motion.div>
      )}

      {/* Storage Optimizer Tab */}
      {activeTab === 'optimizer' && (
        <motion.div variants={itemVariants}>
          <StorageOptimizer
            storageData={storageData}
            onCleanup={handleCleanup}
          />
        </motion.div>
      )}

      {/* Restore Modal */}
      {showRestoreModal && selectedBackup && (
        <BackupRestoreModal
          isOpen={showRestoreModal}
          onClose={() => {
            setShowRestoreModal(false);
            setSelectedBackup(null);
          }}
          backup={selectedBackup}
          onRestore={handleRestoreBackup}
        />
      )}
    </motion.div>
  );
}
