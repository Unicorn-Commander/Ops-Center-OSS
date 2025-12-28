import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import axios from 'axios';

const StatusDot = ({ status }) => {
  const colors = {
    healthy: 'bg-green-500',
    starting: 'bg-yellow-500',
    unhealthy: 'bg-red-500',
    unknown: 'bg-gray-500'
  };

  return (
    <span className="relative flex h-3 w-3">
      <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${colors[status]} opacity-75`}></span>
      <span className={`relative inline-flex rounded-full h-3 w-3 ${colors[status]}`}></span>
    </span>
  );
};

export default function ServiceCard({ service }) {
  const [metrics, setMetrics] = useState(null);
  const [isHovered, setIsHovered] = useState(false);

  const openService = () => {
    if (service.url) {
      window.open(service.url, '_blank');
    }
  };

  const restartService = async (e) => {
    e.stopPropagation();
    try {
      await axios.post(`/api/v1/services/${service.id}/restart`);
      // Show success toast
    } catch (error) {
      console.error('Failed to restart service:', error);
    }
  };

  const viewLogs = (e) => {
    e.stopPropagation();
    // Open logs modal or navigate to logs page
    console.log('View logs for', service.id);
  };

  return (
    <motion.div
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden transform transition-all duration-300 hover:scale-105 ${service.url ? 'cursor-pointer' : ''}`}
      whileHover={{ y: -4 }}
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={service.url ? openService : undefined}
    >
      <div className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="text-4xl">{service.icon}</div>
          <StatusDot status={service.status} />
        </div>

        {/* Content */}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">
          {service.name}
        </h3>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          {service.description}
        </p>

        {/* Metrics */}
        {metrics && (
          <div className="grid grid-cols-2 gap-2 text-xs mb-4">
            <div className="bg-gray-100 dark:bg-gray-700 rounded px-2 py-1">
              <span className="text-gray-600 dark:text-gray-400">Requests:</span>
              <span className="ml-1 font-medium">{metrics.requests}/s</span>
            </div>
            <div className="bg-gray-100 dark:bg-gray-700 rounded px-2 py-1">
              <span className="text-gray-600 dark:text-gray-400">Latency:</span>
              <span className="ml-1 font-medium">{metrics.latency}ms</span>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-between items-center">
          {service.url ? (
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium"
              onClick={openService}
            >
              Open
            </button>
          ) : (
            <span className="px-4 py-2 bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded-lg text-sm font-medium">
              API Only
            </span>
          )}
          
          {isHovered && (
            <div className="flex gap-2">
              <button
                onClick={restartService}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                title="Restart"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              <button
                onClick={viewLogs}
                className="p-2 text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white transition-colors"
                title="View Logs"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Port indicator */}
      <div className="bg-gray-50 dark:bg-gray-900 px-6 py-2 text-xs text-gray-500 dark:text-gray-400">
        Port: {service.port}
      </div>
    </motion.div>
  );
}