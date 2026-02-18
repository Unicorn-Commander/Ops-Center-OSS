import React, { useState, useEffect, lazy, Suspense } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import {
  ChartBarIcon,
  CircleStackIcon,
  ChartPieIcon,
  ExclamationTriangleIcon,
  WrenchScrewdriverIcon
} from '@heroicons/react/24/outline';

const GrafanaConfig = lazy(() => import('../GrafanaConfig'));
const PrometheusConfig = lazy(() => import('../PrometheusConfig'));
const UmamiConfig = lazy(() => import('../UmamiConfig'));

const TABS = [
  { id: 'grafana', label: 'Grafana', icon: ChartBarIcon },
  { id: 'prometheus', label: 'Prometheus', icon: CircleStackIcon },
  { id: 'umami', label: 'Umami Analytics', icon: ChartPieIcon }
];

export default function ExternalMonitoringTools() {
  const { theme, currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('grafana');
  const [serviceStatus, setServiceStatus] = useState({
    grafana: null,
    prometheus: null,
    umami: null
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkServices();
  }, []);

  const checkServices = async () => {
    setLoading(true);
    const checks = {};

    // Check Grafana
    try {
      const res = await fetch('/api/v1/monitoring/grafana/health');
      checks.grafana = res.ok ? 'connected' : 'unreachable';
    } catch {
      checks.grafana = 'not_configured';
    }

    // Check Prometheus
    try {
      const res = await fetch('/api/v1/monitoring/prometheus/health');
      checks.prometheus = res.ok ? 'connected' : 'unreachable';
    } catch {
      checks.prometheus = 'not_configured';
    }

    // Check Umami
    try {
      const res = await fetch('/api/v1/monitoring/umami/health');
      checks.umami = res.ok ? 'connected' : 'unreachable';
    } catch {
      checks.umami = 'not_configured';
    }

    setServiceStatus(checks);
    setLoading(false);

    // Auto-select first available tab
    const firstAvailable = TABS.find(t => checks[t.id] === 'connected');
    if (firstAvailable) {
      setActiveTab(firstAvailable.id);
    }
  };

  const anyConfigured = Object.values(serviceStatus).some(s => s === 'connected');

  const getStatusBadge = (status) => {
    if (status === 'connected') {
      return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Connected</span>;
    }
    if (status === 'unreachable') {
      return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">Unreachable</span>;
    }
    return <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-600">Not Configured</span>;
  };

  const cardBg = currentTheme === 'unicorn'
    ? 'bg-white/10 backdrop-blur-md border border-purple-500/20'
    : currentTheme === 'light'
    ? 'bg-white border border-gray-200'
    : 'bg-slate-800 border border-slate-700';

  const textPrimary = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const textSecondary = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  if (!anyConfigured) {
    return (
      <div className={`rounded-xl p-12 text-center ${cardBg}`}>
        <WrenchScrewdriverIcon className={`h-16 w-16 mx-auto mb-4 ${textSecondary}`} />
        <h2 className={`text-xl font-semibold mb-2 ${textPrimary}`}>No Monitoring Tools Configured</h2>
        <p className={`mb-6 max-w-md mx-auto ${textSecondary}`}>
          Set up Grafana, Prometheus, or Umami to enable external monitoring dashboards and analytics.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
          {TABS.map(tab => (
            <div key={tab.id} className={`rounded-lg p-4 ${cardBg}`}>
              <tab.icon className={`h-8 w-8 mx-auto mb-2 ${textSecondary}`} />
              <h3 className={`font-medium ${textPrimary}`}>{tab.label}</h3>
              <p className={`text-xs mt-1 ${textSecondary}`}>
                {tab.id === 'grafana' && 'Metrics dashboards & visualization'}
                {tab.id === 'prometheus' && 'Time-series metrics collection'}
                {tab.id === 'umami' && 'Privacy-focused web analytics'}
              </p>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-2xl font-bold ${textPrimary}`}>External Monitoring Tools</h1>
        <p className={`mt-1 ${textSecondary}`}>
          Configure and manage Grafana, Prometheus, and Umami integrations.
        </p>
      </div>

      {/* Tab bar */}
      <div className={`rounded-xl ${cardBg}`}>
        <div className="border-b border-gray-200/20">
          <nav className="flex -mb-px" aria-label="Monitoring tools">
            {TABS.map(tab => {
              const isActive = activeTab === tab.id;
              const status = serviceStatus[tab.id];
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    flex items-center gap-2 px-6 py-3 text-sm font-medium border-b-2 transition-colors
                    ${isActive
                      ? currentTheme === 'unicorn'
                        ? 'border-purple-400 text-purple-200'
                        : currentTheme === 'light'
                        ? 'border-blue-500 text-blue-600'
                        : 'border-blue-400 text-blue-300'
                      : `border-transparent ${textSecondary} hover:${textPrimary}`
                    }
                  `}
                >
                  <tab.icon className="h-4 w-4" />
                  {tab.label}
                  {getStatusBadge(status)}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab content */}
        <div className="p-0">
          <Suspense fallback={
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
            </div>
          }>
            {activeTab === 'grafana' && <GrafanaConfig />}
            {activeTab === 'prometheus' && <PrometheusConfig />}
            {activeTab === 'umami' && <UmamiConfig />}
          </Suspense>
        </div>
      </div>
    </div>
  );
}
