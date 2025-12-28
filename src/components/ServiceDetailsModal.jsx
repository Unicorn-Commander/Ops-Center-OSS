import React, { useState, useEffect } from 'react';
import { XMarkIcon, ChartBarIcon, Cog6ToothIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { Tab } from '@headlessui/react';

export default function ServiceDetailsModal({ service, isOpen, onClose, onViewLogs }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchStats = async () => {
    if (!service?.container_name) return;
    
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/services/${service.container_name}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && service) {
      fetchStats();
      const interval = setInterval(fetchStats, 5000);
      return () => clearInterval(interval);
    }
  }, [isOpen, service]);

  if (!isOpen || !service) return null;

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${units[i]}`;
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">
              {service.display_name}
            </h2>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Container: {service.container_name}
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <Tab.Group>
            <Tab.List className="flex space-x-1 rounded-xl bg-gray-100 dark:bg-gray-700 p-1 mb-6">
              <Tab
                className={({ selected }) =>
                  `w-full rounded-lg py-2.5 text-sm font-medium leading-5 transition-colors
                  ${selected 
                    ? 'bg-white dark:bg-gray-600 text-blue-700 dark:text-blue-400 shadow' 
                    : 'text-gray-700 dark:text-gray-300 hover:bg-white/[0.12] hover:text-gray-900'
                  }`
                }
              >
                <div className="flex items-center justify-center gap-2">
                  <ChartBarIcon className="h-4 w-4" />
                  Statistics
                </div>
              </Tab>
              <Tab
                className={({ selected }) =>
                  `w-full rounded-lg py-2.5 text-sm font-medium leading-5 transition-colors
                  ${selected 
                    ? 'bg-white dark:bg-gray-600 text-blue-700 dark:text-blue-400 shadow' 
                    : 'text-gray-700 dark:text-gray-300 hover:bg-white/[0.12] hover:text-gray-900'
                  }`
                }
              >
                <div className="flex items-center justify-center gap-2">
                  <Cog6ToothIcon className="h-4 w-4" />
                  Configuration
                </div>
              </Tab>
            </Tab.List>

            <Tab.Panels>
              {/* Statistics Panel */}
              <Tab.Panel className="space-y-6">
                {loading && !stats ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent mx-auto mb-4"></div>
                    <p className="text-gray-500">Loading statistics...</p>
                  </div>
                ) : (
                  <>
                    {/* Resource Usage */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Resource Usage
                      </h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                          <div className="text-sm text-gray-500 dark:text-gray-400">CPU Usage</div>
                          <div className="text-2xl font-semibold text-gray-900 dark:text-white mt-1">
                            {stats?.cpu_percent || service.cpu_percent || 0}%
                          </div>
                          <div className="mt-2 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min(stats?.cpu_percent || 0, 100)}%` }}
                            />
                          </div>
                        </div>
                        <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                          <div className="text-sm text-gray-500 dark:text-gray-400">Memory Usage</div>
                          <div className="text-2xl font-semibold text-gray-900 dark:text-white mt-1">
                            {stats?.memory_percent?.toFixed(1) || 0}%
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {formatBytes((stats?.memory_usage_mb || 0) * 1024 * 1024)} / 
                            {formatBytes((stats?.memory_limit_mb || 0) * 1024 * 1024)}
                          </div>
                          <div className="mt-2 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                            <div 
                              className="bg-green-600 h-2 rounded-full transition-all"
                              style={{ width: `${Math.min(stats?.memory_percent || 0, 100)}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Network Stats */}
                    {stats?.network_rx_mb !== undefined && (
                      <div>
                        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                          Network I/O
                        </h3>
                        <div className="grid grid-cols-2 gap-4">
                          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                            <div className="text-sm text-gray-500 dark:text-gray-400">Received</div>
                            <div className="text-xl font-semibold text-gray-900 dark:text-white mt-1">
                              {stats.network_rx_mb.toFixed(2)} MB
                            </div>
                          </div>
                          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                            <div className="text-sm text-gray-500 dark:text-gray-400">Transmitted</div>
                            <div className="text-xl font-semibold text-gray-900 dark:text-white mt-1">
                              {stats.network_tx_mb.toFixed(2)} MB
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Service Info */}
                    <div>
                      <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                        Service Information
                      </h3>
                      <dl className="space-y-3">
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500 dark:text-gray-400">Status</dt>
                          <dd className="text-sm font-medium text-gray-900 dark:text-white">
                            {service.status}
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500 dark:text-gray-400">Image</dt>
                          <dd className="text-sm font-medium text-gray-900 dark:text-white">
                            {service.image}
                          </dd>
                        </div>
                        {service.port && (
                          <div className="flex justify-between">
                            <dt className="text-sm text-gray-500 dark:text-gray-400">Port</dt>
                            <dd className="text-sm font-medium text-gray-900 dark:text-white">
                              {service.port}
                            </dd>
                          </div>
                        )}
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500 dark:text-gray-400">GPU Enabled</dt>
                          <dd className="text-sm font-medium text-gray-900 dark:text-white">
                            {service.gpu_enabled ? 'Yes' : 'No'}
                          </dd>
                        </div>
                        <div className="flex justify-between">
                          <dt className="text-sm text-gray-500 dark:text-gray-400">Restart Policy</dt>
                          <dd className="text-sm font-medium text-gray-900 dark:text-white">
                            {service.restart || 'No'}
                          </dd>
                        </div>
                      </dl>
                    </div>
                  </>
                )}
              </Tab.Panel>

              {/* Configuration Panel */}
              <Tab.Panel className="space-y-6">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Environment Variables
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 font-mono text-sm">
                    {service.environment && Object.keys(service.environment).length > 0 ? (
                      <dl className="space-y-2">
                        {Object.entries(service.environment).map(([key, value]) => (
                          <div key={key} className="flex">
                            <dt className="text-blue-600 dark:text-blue-400 font-medium">
                              {key}=
                            </dt>
                            <dd className="text-gray-700 dark:text-gray-300 ml-1 break-all">
                              {typeof value === 'string' && value.length > 50 
                                ? `${value.substring(0, 50)}...` 
                                : value}
                            </dd>
                          </div>
                        ))}
                      </dl>
                    ) : (
                      <p className="text-gray-500 dark:text-gray-400">No environment variables</p>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Volumes
                  </h3>
                  <div className="space-y-2">
                    {service.volumes && service.volumes.length > 0 ? (
                      service.volumes.map((volume, index) => (
                        <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 font-mono text-sm">
                          {volume}
                        </div>
                      ))
                    ) : (
                      <p className="text-gray-500 dark:text-gray-400">No volumes mounted</p>
                    )}
                  </div>
                </div>

                <div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
                    Dependencies
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {service.depends_on && service.depends_on.length > 0 ? (
                      service.depends_on.map((dep, index) => (
                        <span 
                          key={index}
                          className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm"
                        >
                          {dep}
                        </span>
                      ))
                    ) : (
                      <p className="text-gray-500 dark:text-gray-400">No dependencies</p>
                    )}
                  </div>
                </div>
              </Tab.Panel>
            </Tab.Panels>
          </Tab.Group>
        </div>

        {/* Footer */}
        <div className="p-6 border-t dark:border-gray-700 flex justify-between">
          <button
            onClick={() => {
              onViewLogs(service.container_name);
              onClose();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            <DocumentTextIcon className="h-5 w-5" />
            View Logs
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}