import React, { useState, useEffect } from 'react';
import {
  CheckCircleIcon,
  ExclamationCircleIcon,
  QuestionMarkCircleIcon,
  ArrowPathIcon,
  ClockIcon,
  GlobeAltIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/solid';
import { ColonelLogo, MagicUnicornLogo } from '../components/Logos';

export default function PublicStatusPage() {
  const [statusData, setStatusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/v1/website-monitor/public-status');
      if (!response.ok) {
        throw new Error('Failed to fetch status');
      }
      const data = await response.json();
      setStatusData(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchStatus, 60000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'up':
        return 'bg-green-500';
      case 'down':
        return 'bg-red-500';
      default:
        return 'bg-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'up':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'down':
        return <ExclamationCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <QuestionMarkCircleIcon className="h-5 w-5 text-gray-400" />;
    }
  };

  const getUptimeColor = (uptime) => {
    if (uptime === null || uptime === undefined) return 'text-gray-400';
    if (uptime >= 99.9) return 'text-green-500';
    if (uptime >= 99) return 'text-green-400';
    if (uptime >= 95) return 'text-yellow-500';
    return 'text-red-500';
  };

  const formatLastCheck = (timestamp) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)} min ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
    return date.toLocaleDateString();
  };

  const getOverallStatus = () => {
    if (!statusData || !statusData.services || statusData.services.length === 0) {
      return { status: 'unknown', message: 'No services monitored', color: 'gray' };
    }

    const downCount = statusData.services.filter(s => s.status === 'down').length;
    const unknownCount = statusData.services.filter(s => s.status === 'unknown').length;

    if (downCount === 0 && unknownCount === 0) {
      return { status: 'operational', message: 'All Systems Operational', color: 'green' };
    }
    if (downCount > 0) {
      return {
        status: 'degraded',
        message: `${downCount} system${downCount > 1 ? 's' : ''} experiencing issues`,
        color: 'red'
      };
    }
    return { status: 'unknown', message: 'Some systems status unknown', color: 'yellow' };
  };

  const overall = getOverallStatus();

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-700/50 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <ColonelLogo className="w-12 h-12" />
              <div>
                <h1 className="text-2xl font-bold text-white">Unicorn Commander</h1>
                <p className="text-sm text-slate-400">System Status</p>
              </div>
            </div>
            <button
              onClick={fetchStatus}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-700/50 hover:bg-slate-700 text-slate-300 transition-colors disabled:opacity-50"
            >
              <ArrowPathIcon className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Overall Status Banner */}
        <div className={`rounded-xl p-6 mb-8 border ${
          overall.color === 'green'
            ? 'bg-green-500/10 border-green-500/30'
            : overall.color === 'red'
            ? 'bg-red-500/10 border-red-500/30'
            : 'bg-yellow-500/10 border-yellow-500/30'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {overall.color === 'green' ? (
                <CheckCircleIcon className="h-10 w-10 text-green-500" />
              ) : overall.color === 'red' ? (
                <ExclamationCircleIcon className="h-10 w-10 text-red-500" />
              ) : (
                <QuestionMarkCircleIcon className="h-10 w-10 text-yellow-500" />
              )}
              <div>
                <h2 className={`text-xl font-semibold ${
                  overall.color === 'green' ? 'text-green-400'
                  : overall.color === 'red' ? 'text-red-400'
                  : 'text-yellow-400'
                }`}>
                  {overall.message}
                </h2>
                {lastUpdated && (
                  <p className="text-sm text-slate-400 mt-1">
                    Last updated: {lastUpdated.toLocaleTimeString()}
                  </p>
                )}
              </div>
            </div>
            {statusData && (
              <div className="text-right hidden sm:block">
                <div className="text-2xl font-bold text-white">
                  {statusData.services?.filter(s => s.status === 'up').length || 0}
                  <span className="text-slate-400 text-lg">/{statusData.services?.length || 0}</span>
                </div>
                <p className="text-sm text-slate-400">Services Online</p>
              </div>
            )}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="rounded-xl p-6 mb-8 bg-red-500/10 border border-red-500/30">
            <div className="flex items-center gap-3 text-red-400">
              <ExclamationCircleIcon className="h-6 w-6" />
              <span>Unable to load status data. Please try again later.</span>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && !statusData && (
          <div className="flex flex-col items-center justify-center py-16">
            <ArrowPathIcon className="h-12 w-12 text-slate-400 animate-spin mb-4" />
            <p className="text-slate-400">Loading status data...</p>
          </div>
        )}

        {/* Services List */}
        {statusData && statusData.services && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                <GlobeAltIcon className="h-5 w-5 text-slate-400" />
                Monitored Services
              </h3>
              <span className="text-sm text-slate-400">
                {statusData.services.length} service{statusData.services.length !== 1 ? 's' : ''}
              </span>
            </div>

            {statusData.services.length === 0 ? (
              <div className="rounded-xl p-8 bg-slate-800/50 border border-slate-700/50 text-center">
                <GlobeAltIcon className="h-12 w-12 text-slate-500 mx-auto mb-3" />
                <p className="text-slate-400">No services are currently being monitored.</p>
              </div>
            ) : (
              <div className="rounded-xl bg-slate-800/50 border border-slate-700/50 overflow-hidden">
                {statusData.services.map((service, index) => (
                  <div
                    key={service.name + service.url}
                    className={`flex items-center justify-between p-4 hover:bg-slate-700/30 transition-colors ${
                      index !== statusData.services.length - 1 ? 'border-b border-slate-700/50' : ''
                    }`}
                  >
                    {/* Service Info */}
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      {/* Status Indicator */}
                      <div className="flex-shrink-0">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)}`}>
                          {service.status === 'up' && (
                            <div className={`w-3 h-3 rounded-full ${getStatusColor(service.status)} animate-pulse`} />
                          )}
                        </div>
                      </div>

                      {/* Name and URL */}
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-medium text-white truncate">{service.name}</h4>
                          {service.ssl_valid && (
                            <ShieldCheckIcon className="h-4 w-4 text-green-500 flex-shrink-0" title="SSL Valid" />
                          )}
                        </div>
                        <p className="text-sm text-slate-400 truncate">{service.url}</p>
                      </div>
                    </div>

                    {/* Status Details */}
                    <div className="flex items-center gap-6 flex-shrink-0 ml-4">
                      {/* Uptime */}
                      <div className="text-right hidden sm:block">
                        <div className={`font-semibold ${getUptimeColor(service.uptime_24h)}`}>
                          {service.uptime_24h !== null && service.uptime_24h !== undefined
                            ? `${service.uptime_24h.toFixed(1)}%`
                            : '--'}
                        </div>
                        <div className="text-xs text-slate-500">24h uptime</div>
                      </div>

                      {/* Last Check */}
                      <div className="text-right hidden md:block">
                        <div className="flex items-center gap-1 text-slate-300">
                          <ClockIcon className="h-4 w-4 text-slate-500" />
                          <span className="text-sm">{formatLastCheck(service.last_check)}</span>
                        </div>
                        <div className="text-xs text-slate-500">Last check</div>
                      </div>

                      {/* Status Badge */}
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                        service.status === 'up'
                          ? 'bg-green-500/20 text-green-400'
                          : service.status === 'down'
                          ? 'bg-red-500/20 text-red-400'
                          : 'bg-gray-500/20 text-gray-400'
                      }`}>
                        {service.status === 'up' ? 'Operational' : service.status === 'down' ? 'Down' : 'Unknown'}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Legend */}
        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-400">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span>Operational</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span>Down</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-gray-400"></div>
            <span>Unknown</span>
          </div>
          <div className="flex items-center gap-2">
            <ShieldCheckIcon className="h-4 w-4 text-green-500" />
            <span>SSL Valid</span>
          </div>
        </div>

        {/* Auto-refresh Notice */}
        <div className="mt-6 text-center text-sm text-slate-500">
          Status updates automatically every 60 seconds
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700/50 bg-slate-900/50 mt-auto">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <MagicUnicornLogo className="w-6 h-6" />
              <span className="text-sm text-slate-400">
                Magic Unicorn Unconventional Technology & Stuff Inc
              </span>
            </div>
            <div className="text-sm text-slate-500">
              Powered by Unicorn Commander
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
