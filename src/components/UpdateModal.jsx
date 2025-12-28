import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowDownTrayIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon,
  ClockIcon,
  ShieldCheckIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

const UpdateModal = ({ isOpen, onClose, theme }) => {
  const [updateStatus, setUpdateStatus] = useState({
    checking: false,
    updating: false,
    current_version: 'Unknown',
    latest_version: 'Unknown',
    update_available: false,
    last_check: null
  });
  
  const [updateResult, setUpdateResult] = useState(null);
  const [changelog, setChangelog] = useState([]);
  const [showChangelog, setShowChangelog] = useState(false);
  const [backupEnabled, setBackupEnabled] = useState(true);

  useEffect(() => {
    if (isOpen) {
      fetchUpdateStatus();
      fetchChangelog();
    }
  }, [isOpen]);

  const fetchUpdateStatus = async () => {
    try {
      const response = await fetch('/api/v1/updates/status');
      if (response.ok) {
        const data = await response.json();
        setUpdateStatus(data);
      }
    } catch (error) {
      console.error('Error fetching update status:', error);
    }
  };

  const fetchChangelog = async () => {
    try {
      const response = await fetch('/api/v1/updates/changelog?limit=5');
      if (response.ok) {
        const data = await response.json();
        setChangelog(data.changelog || []);
      }
    } catch (error) {
      console.error('Error fetching changelog:', error);
    }
  };

  const checkForUpdates = async () => {
    try {
      setUpdateStatus(prev => ({ ...prev, checking: true }));
      setUpdateResult(null);
      
      const response = await fetch('/api/v1/updates/check', {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setUpdateStatus(prev => ({
          ...prev,
          checking: false,
          current_version: data.current_version,
          latest_version: data.latest_version,
          update_available: data.update_available,
          last_check: new Date().toISOString()
        }));
        
        if (!data.update_available) {
          setUpdateResult({
            type: 'success',
            message: 'Your system is up to date!'
          });
        }
      } else {
        throw new Error('Failed to check for updates');
      }
    } catch (error) {
      setUpdateStatus(prev => ({ ...prev, checking: false }));
      setUpdateResult({
        type: 'error',
        message: `Error checking for updates: ${error.message}`
      });
    }
  };

  const applyUpdate = async () => {
    try {
      setUpdateStatus(prev => ({ ...prev, updating: true }));
      setUpdateResult(null);
      
      const response = await fetch(`/api/v1/updates/apply?backup_first=${backupEnabled}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        
        if (data.success) {
          setUpdateResult({
            type: 'success',
            message: data.message,
            restartRequired: data.restart_required
          });
          
          // Refresh status
          await fetchUpdateStatus();
        } else {
          setUpdateResult({
            type: 'error',
            message: data.error || 'Update failed'
          });
        }
      } else {
        throw new Error('Failed to apply update');
      }
    } catch (error) {
      setUpdateResult({
        type: 'error',
        message: `Error applying update: ${error.message}`
      });
    } finally {
      setUpdateStatus(prev => ({ ...prev, updating: false }));
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className={`${theme.card} rounded-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto m-4`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700/30">
          <h3 className={`text-xl font-semibold ${theme.text.primary} flex items-center gap-2`}>
            <ArrowDownTrayIcon className="h-6 w-6 text-blue-500" />
            System Updates
          </h3>
          <button
            onClick={onClose}
            className={`${theme.text.secondary} hover:${theme.text.primary} transition-colors`}
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Current Status */}
          <div className={`p-4 rounded-lg ${theme.currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/50'}`}>
            <h4 className={`text-sm font-semibold ${theme.text.accent} mb-3`}>Current Status</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className={theme.text.secondary}>Current Version:</span>
                <div className={`${theme.text.primary} font-mono mt-1`}>
                  {updateStatus.current_version}
                </div>
              </div>
              <div>
                <span className={theme.text.secondary}>Latest Version:</span>
                <div className={`${theme.text.primary} font-mono mt-1`}>
                  {updateStatus.latest_version}
                </div>
              </div>
              <div>
                <span className={theme.text.secondary}>Last Checked:</span>
                <div className={`${theme.text.primary} text-xs mt-1`}>
                  {formatDate(updateStatus.last_check)}
                </div>
              </div>
              <div>
                <span className={theme.text.secondary}>Update Available:</span>
                <div className="mt-1">
                  {updateStatus.update_available ? (
                    <span className="text-orange-500 text-xs">Yes - Update Available</span>
                  ) : (
                    <span className="text-green-500 text-xs">Up to Date</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Update Result */}
          {updateResult && (
            <div className={`p-4 rounded-lg border ${
              updateResult.type === 'success' 
                ? 'bg-green-500/10 border-green-500/30' 
                : 'bg-red-500/10 border-red-500/30'
            }`}>
              <div className="flex items-start gap-3">
                {updateResult.type === 'success' ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                )}
                <div>
                  <p className={updateResult.type === 'success' ? 'text-green-400' : 'text-red-400'}>
                    {updateResult.message}
                  </p>
                  {updateResult.restartRequired && (
                    <p className="text-orange-400 text-sm mt-2">
                      ⚠️ System restart required to complete the update
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex flex-col gap-4">
            {/* Check for Updates */}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={checkForUpdates}
              disabled={updateStatus.checking || updateStatus.updating}
              className="flex items-center justify-center gap-2 p-3 bg-blue-500/20 text-blue-400 rounded-lg hover:bg-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ArrowDownTrayIcon className={`h-5 w-5 ${updateStatus.checking ? 'animate-pulse' : ''}`} />
              {updateStatus.checking ? 'Checking for Updates...' : 'Check for Updates'}
            </motion.button>

            {/* Apply Update (only if available) */}
            {updateStatus.update_available && (
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="backup-enabled"
                    checked={backupEnabled}
                    onChange={(e) => setBackupEnabled(e.target.checked)}
                    className="rounded"
                  />
                  <label htmlFor="backup-enabled" className={`text-sm ${theme.text.secondary}`}>
                    Create backup before updating (recommended)
                  </label>
                </div>
                
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={applyUpdate}
                  disabled={updateStatus.updating}
                  className="flex items-center justify-center gap-2 p-3 bg-green-500/20 text-green-400 rounded-lg hover:bg-green-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors w-full"
                >
                  <ShieldCheckIcon className={`h-5 w-5 ${updateStatus.updating ? 'animate-pulse' : ''}`} />
                  {updateStatus.updating ? 'Applying Update...' : 'Apply Update Now'}
                </motion.button>
              </div>
            )}
          </div>

          {/* Changelog */}
          {changelog.length > 0 && (
            <div className="border-t border-gray-700/30 pt-4">
              <button
                onClick={() => setShowChangelog(!showChangelog)}
                className={`flex items-center gap-2 text-sm ${theme.text.secondary} hover:${theme.text.primary} transition-colors mb-3`}
              >
                <DocumentTextIcon className="h-4 w-4" />
                Recent Changes {showChangelog ? '▼' : '▶'}
              </button>
              
              {showChangelog && (
                <div className="space-y-2">
                  {changelog.map((entry, index) => (
                    <div key={index} className={`p-3 rounded-lg ${theme.currentTheme === 'light' ? 'bg-gray-100' : 'bg-gray-800/30'}`}>
                      <div className="flex items-start gap-3">
                        <div className="text-xs text-gray-500 font-mono">
                          {entry.sha}
                        </div>
                        <div className="flex-1">
                          <p className={`text-sm ${theme.text.primary}`}>
                            {entry.message}
                          </p>
                          <p className={`text-xs ${theme.text.secondary} mt-1`}>
                            by {entry.author} • {new Date(entry.date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Warning */}
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
              <div className="text-sm">
                <p className="text-yellow-400 font-medium mb-1">Important Notes:</p>
                <ul className="text-yellow-400/80 text-xs space-y-1">
                  <li>• System services may be temporarily unavailable during updates</li>
                  <li>• Always create a backup before applying updates</li>
                  <li>• Some updates may require a system restart</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-700/30">
          <button
            onClick={onClose}
            className={`px-4 py-2 ${theme.button} rounded-lg hover:bg-gray-700/50 transition-colors`}
          >
            Close
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default UpdateModal;