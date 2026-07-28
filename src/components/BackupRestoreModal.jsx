import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  CloudArrowDownIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon,
  ArrowPathIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

/**
 * BackupRestoreModal Component
 *
 * Modal for restoring backups with options and progress tracking.
 */
export default function BackupRestoreModal({
  isOpen,
  onClose,
  backup,
  onRestore
}) {
  const [restoreLocation, setRestoreLocation] = useState('/home/ucadmin/UC-1-Pro');
  const [restoreOption, setRestoreOption] = useState('overwrite');
  const [isRestoring, setIsRestoring] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('idle'); // idle, restoring, success, error
  const [errorMessage, setErrorMessage] = useState('');

  const handleRestore = async () => {
    setIsRestoring(true);
    setStatus('restoring');
    setProgress(0);

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);

      // Call the actual restore API
      await onRestore(backup.id, {
        restore_location: restoreLocation,
        overwrite: restoreOption === 'overwrite',
        create_new: restoreOption === 'create_new'
      });

      clearInterval(progressInterval);
      setProgress(100);
      setStatus('success');

      // Auto-close after 2 seconds on success
      setTimeout(() => {
        onClose();
      }, 2000);
    } catch (error) {
      setStatus('error');
      setErrorMessage(error.message || 'Failed to restore backup');
    } finally {
      setIsRestoring(false);
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

  if (!isOpen || !backup) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
        onClick={() => !isRestoring && onClose()}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          onClick={(e) => e.stopPropagation()}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        >
          {/* Header */}
          <div className="p-6 border-b dark:border-gray-700">
            <div className="flex justify-between items-start">
              <div className="flex items-center gap-3">
                <CloudArrowDownIcon className="h-8 w-8 text-blue-500" />
                <div>
                  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                    Restore Backup
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {backup.id}
                  </p>
                </div>
              </div>
              {!isRestoring && (
                <button
                  onClick={onClose}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              )}
            </div>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Backup Information */}
            <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-lg">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
                Backup Details
              </h3>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Created:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">
                    {formatDate(backup.timestamp)}
                  </span>
                </div>
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
                  <span className="text-gray-600 dark:text-gray-400">Files:</span>
                  <span className="ml-2 font-medium text-gray-900 dark:text-white">
                    {backup.files_count?.toLocaleString() || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Restore Options */}
            {status === 'idle' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Restore Location
                  </label>
                  <input
                    type="text"
                    value={restoreLocation}
                    onChange={(e) => setRestoreLocation(e.target.value)}
                    placeholder="/path/to/restore/location"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-white"
                  />
                  <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Specify where to restore the backup files
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Restore Method
                  </label>
                  <div className="space-y-2">
                    <label className="flex items-start p-3 border border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                      <input
                        type="radio"
                        name="restore-option"
                        value="overwrite"
                        checked={restoreOption === 'overwrite'}
                        onChange={(e) => setRestoreOption(e.target.value)}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          Overwrite existing files
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Replace current files with backup files. Existing data will be overwritten.
                        </div>
                      </div>
                    </label>

                    <label className="flex items-start p-3 border border-gray-300 dark:border-gray-600 rounded-md cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700">
                      <input
                        type="radio"
                        name="restore-option"
                        value="create_new"
                        checked={restoreOption === 'create_new'}
                        onChange={(e) => setRestoreOption(e.target.value)}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500"
                      />
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          Create new location
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          Restore to a new directory. Existing files will not be modified.
                        </div>
                      </div>
                    </label>
                  </div>
                </div>

                {/* Warning */}
                {restoreOption === 'overwrite' && (
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-sm font-medium text-yellow-800 dark:text-yellow-400">
                          Warning: This action cannot be undone
                        </h4>
                        <p className="text-sm text-yellow-700 dark:text-yellow-500 mt-1">
                          Restoring with overwrite will replace all existing files in {restoreLocation}.
                          Make sure you have a recent backup before proceeding.
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Progress */}
            {status === 'restoring' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Restoring backup...</span>
                  <span className="font-medium text-gray-900 dark:text-white">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.3 }}
                    className="bg-blue-600 h-3 rounded-full flex items-center justify-end pr-2"
                  >
                    {progress > 10 && (
                      <ArrowPathIcon className="h-3 w-3 text-white animate-spin" />
                    )}
                  </motion.div>
                </div>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
                  Please wait while the backup is being restored. Do not close this window.
                </p>
              </div>
            )}

            {/* Success */}
            {status === 'success' && (
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <CheckCircleIcon className="h-6 w-6 text-green-600 dark:text-green-500" />
                  <div>
                    <h4 className="text-sm font-medium text-green-800 dark:text-green-400">
                      Backup restored successfully!
                    </h4>
                    <p className="text-sm text-green-700 dark:text-green-500 mt-1">
                      All files have been restored to {restoreLocation}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Error */}
            {status === 'error' && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-500 flex-shrink-0" />
                  <div>
                    <h4 className="text-sm font-medium text-red-800 dark:text-red-400">
                      Restore failed
                    </h4>
                    <p className="text-sm text-red-700 dark:text-red-500 mt-1">
                      {errorMessage}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Info Box */}
            {status === 'idle' && (
              <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <InformationCircleIcon className="h-5 w-5 text-blue-600 dark:text-blue-500 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-blue-700 dark:text-blue-400">
                    <strong>Restore Process:</strong>
                    <ul className="list-disc list-inside mt-1 space-y-1">
                      <li>Extracts backup archive to specified location</li>
                      <li>Verifies file integrity with checksums</li>
                      <li>Restores file permissions and ownership</li>
                      <li>Creates restore log in backup directory</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="p-6 border-t dark:border-gray-700 flex justify-end gap-3">
            {status === 'idle' && (
              <>
                <button
                  onClick={onClose}
                  disabled={isRestoring}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 dark:bg-gray-600 dark:text-gray-300 dark:hover:bg-gray-500 rounded-md disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRestore}
                  disabled={isRestoring || !restoreLocation}
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md disabled:opacity-50 flex items-center gap-2"
                >
                  <CloudArrowDownIcon className="h-4 w-4" />
                  Start Restore
                </button>
              </>
            )}
            {(status === 'success' || status === 'error') && (
              <button
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                Close
              </button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
