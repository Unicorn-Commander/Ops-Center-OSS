import React, { useState } from 'react';
import {
  TrashIcon,
  ChartBarIcon,
  FolderIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

/**
 * StorageOptimizer Component
 *
 * Tools for cleaning up unused storage and optimizing disk usage.
 */
export default function StorageOptimizer({ storageData, onCleanup }) {
  const [selectedItems, setSelectedItems] = useState([]);
  const [isScanning, setIsScanning] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);
  const [scanResults, setScanResults] = useState(null);

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
  };

  const handleScan = async () => {
    setIsScanning(true);
    try {
      // Simulate scanning for cleanup opportunities
      await new Promise(resolve => setTimeout(resolve, 2000));

      // Mock scan results
      setScanResults({
        docker_images_unused: {
          count: 5,
          size: 2.1 * 1024 * 1024 * 1024, // 2.1GB
          items: [
            { name: 'ubuntu:20.04', size: 450 * 1024 * 1024, age_days: 45 },
            { name: 'node:14-alpine', size: 180 * 1024 * 1024, age_days: 60 },
            { name: 'python:3.9-slim', size: 320 * 1024 * 1024, age_days: 30 }
          ]
        },
        docker_volumes_unused: {
          count: 3,
          size: 850 * 1024 * 1024, // 850MB
          items: [
            { name: 'old_postgres_data', size: 500 * 1024 * 1024, age_days: 90 },
            { name: 'test_volume_123', size: 250 * 1024 * 1024, age_days: 120 }
          ]
        },
        temp_files: {
          count: 127,
          size: 1.2 * 1024 * 1024 * 1024, // 1.2GB
          paths: [
            '/tmp/backup_temp',
            '/var/tmp/cache',
            '/home/ucadmin/UC-1-Pro/temp'
          ]
        },
        log_files: {
          count: 45,
          size: 680 * 1024 * 1024, // 680MB
          paths: [
            '/var/log/old_logs',
            '/home/ucadmin/UC-1-Pro/logs/archived'
          ]
        },
        cache_directories: {
          count: 8,
          size: 450 * 1024 * 1024, // 450MB
          paths: [
            '/home/ucadmin/.cache/pip',
            '/home/ucadmin/.npm',
            '/var/cache/apt/archives'
          ]
        }
      });
    } catch (error) {
      console.error('Scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  };

  const handleCleanup = async () => {
    if (selectedItems.length === 0) {
      alert('Please select items to clean up');
      return;
    }

    if (!confirm(`Are you sure you want to clean ${selectedItems.length} item(s)? This action cannot be undone.`)) {
      return;
    }

    setIsCleaning(true);
    try {
      await onCleanup(selectedItems);
      // Rescan after cleanup
      await handleScan();
      setSelectedItems([]);
    } catch (error) {
      console.error('Cleanup failed:', error);
      alert('Cleanup failed: ' + error.message);
    } finally {
      setIsCleaning(false);
    }
  };

  const toggleItem = (category, item) => {
    const itemKey = `${category}:${item}`;
    if (selectedItems.includes(itemKey)) {
      setSelectedItems(selectedItems.filter(i => i !== itemKey));
    } else {
      setSelectedItems([...selectedItems, itemKey]);
    }
  };

  const selectAllInCategory = (category) => {
    const categoryItems = scanResults[category]?.items || scanResults[category]?.paths || [];
    const categoryKeys = categoryItems.map(item =>
      `${category}:${typeof item === 'string' ? item : item.name}`
    );

    const allSelected = categoryKeys.every(key => selectedItems.includes(key));
    if (allSelected) {
      setSelectedItems(selectedItems.filter(key => !categoryKeys.includes(key)));
    } else {
      setSelectedItems([...new Set([...selectedItems, ...categoryKeys])]);
    }
  };

  const getTotalSavings = () => {
    if (!scanResults) return 0;
    let total = 0;
    Object.values(scanResults).forEach(category => {
      total += category.size || 0;
    });
    return total;
  };

  const categories = [
    {
      key: 'docker_images_unused',
      title: 'Unused Docker Images',
      icon: '🐳',
      description: 'Docker images that are not used by any containers'
    },
    {
      key: 'docker_volumes_unused',
      title: 'Unused Docker Volumes',
      icon: '📦',
      description: 'Docker volumes that are not mounted by any containers'
    },
    {
      key: 'temp_files',
      title: 'Temporary Files',
      icon: '📄',
      description: 'Temporary files and directories that can be safely deleted'
    },
    {
      key: 'log_files',
      title: 'Old Log Files',
      icon: '📋',
      description: 'Log files older than 30 days'
    },
    {
      key: 'cache_directories',
      title: 'Cache Directories',
      icon: '🗃️',
      description: 'Package manager and application cache directories'
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <SparklesIcon className="h-8 w-8 text-purple-500" />
          <div>
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Storage Optimizer
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Clean up unused files and free up disk space
            </p>
          </div>
        </div>
        <button
          onClick={handleScan}
          disabled={isScanning}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {isScanning ? (
            <>
              <ArrowPathIcon className="h-5 w-5 animate-spin" />
              Scanning...
            </>
          ) : (
            <>
              <ChartBarIcon className="h-5 w-5" />
              Scan for Cleanup
            </>
          )}
        </button>
      </div>

      {/* Summary Cards */}
      {scanResults && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Potential Savings
                </p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {formatBytes(getTotalSavings())}
                </p>
              </div>
              <SparklesIcon className="h-8 w-8 text-green-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Items Found
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Object.values(scanResults).reduce((sum, cat) => sum + (cat.count || 0), 0)}
                </p>
              </div>
              <FolderIcon className="h-8 w-8 text-blue-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                  Selected Items
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {selectedItems.length}
                </p>
              </div>
              <CheckCircleIcon className="h-8 w-8 text-purple-500" />
            </div>
          </div>
        </div>
      )}

      {/* Cleanup Categories */}
      {scanResults && (
        <div className="space-y-4">
          {categories.map(category => {
            const data = scanResults[category.key];
            if (!data || data.count === 0) return null;

            const items = data.items || data.paths || [];
            const allSelected = items.every(item =>
              selectedItems.includes(`${category.key}:${typeof item === 'string' ? item : item.name}`)
            );

            return (
              <div
                key={category.key}
                className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg overflow-hidden"
              >
                {/* Category Header */}
                <div className="p-4 bg-gray-50 dark:bg-gray-900 border-b dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{category.icon}</span>
                      <div>
                        <h3 className="font-medium text-gray-900 dark:text-white">
                          {category.title}
                        </h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {category.description}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {data.count} items
                        </div>
                        <div className="text-lg font-bold text-gray-900 dark:text-white">
                          {formatBytes(data.size)}
                        </div>
                      </div>
                      <button
                        onClick={() => selectAllInCategory(category.key)}
                        className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-300 dark:hover:bg-gray-600"
                      >
                        {allSelected ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Items List */}
                <div className="p-4 space-y-2">
                  {items.slice(0, 5).map((item, index) => {
                    const itemName = typeof item === 'string' ? item : item.name;
                    const itemSize = typeof item === 'string' ? null : item.size;
                    const itemAge = typeof item === 'string' ? null : item.age_days;
                    const itemKey = `${category.key}:${itemName}`;

                    return (
                      <label
                        key={index}
                        className="flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-900 rounded cursor-pointer"
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={selectedItems.includes(itemKey)}
                            onChange={() => toggleItem(category.key, itemName)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                          />
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">
                              {itemName}
                            </div>
                            {itemAge && (
                              <div className="text-xs text-gray-500">
                                Last used {itemAge} days ago
                              </div>
                            )}
                          </div>
                        </div>
                        {itemSize && (
                          <div className="text-sm font-medium text-gray-600 dark:text-gray-400">
                            {formatBytes(itemSize)}
                          </div>
                        )}
                      </label>
                    );
                  })}

                  {items.length > 5 && (
                    <div className="text-center pt-2">
                      <button className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400">
                        Show {items.length - 5} more items
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* No Results */}
      {!scanResults && !isScanning && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <ChartBarIcon className="h-16 w-16 mx-auto mb-4 opacity-50" />
          <p>Click "Scan for Cleanup" to find optimization opportunities</p>
        </div>
      )}

      {/* Cleanup Button */}
      {scanResults && selectedItems.length > 0 && (
        <div className="bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Ready to clean up {selectedItems.length} item(s)
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                This action cannot be undone. Make sure you have backups before proceeding.
              </p>
            </div>
            <button
              onClick={handleCleanup}
              disabled={isCleaning}
              className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center gap-2 font-medium"
            >
              {isCleaning ? (
                <>
                  <ArrowPathIcon className="h-5 w-5 animate-spin" />
                  Cleaning...
                </>
              ) : (
                <>
                  <TrashIcon className="h-5 w-5" />
                  Clean Up Now
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Warning */}
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-700 dark:text-yellow-400">
            <strong>Important:</strong> Always create a backup before performing cleanup operations.
            Some items may be needed by running services. Review the list carefully before proceeding.
          </div>
        </div>
      </div>
    </div>
  );
}
