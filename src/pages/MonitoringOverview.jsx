import React from 'react';
import { Link } from 'react-router-dom';
import {
  PresentationChartBarIcon,
  ChartBarIcon,
  CircleStackIcon,
  ChartPieIcon,
  DocumentTextIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';

/**
 * MonitoringOverview - Overview of all monitoring and analytics tools
 *
 * Provides quick access to:
 * - Grafana dashboards (visualization)
 * - Prometheus metrics (collection)
 * - Umami analytics (web tracking)
 * - System logs (error tracking)
 */
export default function MonitoringOverview() {
  const tools = [
    {
      name: 'Grafana',
      description: 'Visualization dashboards for metrics and logs',
      icon: ChartBarIcon,
      link: '/admin/monitoring/grafana',
      external: 'http://grafana.your-domain.com:3000',
      status: 'planned',
      color: 'from-orange-500 to-red-500'
    },
    {
      name: 'Prometheus',
      description: 'Time-series metrics collection and alerting',
      icon: CircleStackIcon,
      link: '/admin/monitoring/prometheus',
      external: 'http://prometheus.your-domain.com:9090',
      status: 'planned',
      color: 'from-red-500 to-pink-500'
    },
    {
      name: 'Umami Analytics',
      description: 'Privacy-focused web analytics tracking',
      icon: ChartPieIcon,
      link: '/admin/monitoring/umami',
      external: 'http://umami.your-domain.com:3000',
      status: 'planned',
      color: 'from-blue-500 to-indigo-500'
    },
    {
      name: 'System Logs',
      description: 'Service logs and error tracking',
      icon: DocumentTextIcon,
      link: '/admin/monitoring/logs',
      status: 'active',
      color: 'from-gray-500 to-slate-500'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <PresentationChartBarIcon className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold text-white">
              Monitoring & Analytics
            </h1>
          </div>
          <p className="text-gray-300">
            Comprehensive system monitoring, metrics visualization, and analytics tracking
          </p>
        </div>

        {/* Tools Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {tools.map((tool) => (
            <div
              key={tool.name}
              className="bg-white/10 backdrop-blur-lg rounded-lg p-6 border border-white/20 hover:border-purple-400/50 transition-all"
            >
              {/* Tool Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`p-3 rounded-lg bg-gradient-to-br ${tool.color}`}>
                    <tool.icon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white">{tool.name}</h3>
                    <span
                      className={`inline-block px-2 py-1 text-xs rounded-full ${
                        tool.status === 'active'
                          ? 'bg-green-500/20 text-green-400'
                          : 'bg-yellow-500/20 text-yellow-400'
                      }`}
                    >
                      {tool.status === 'active' ? 'Active' : 'Planned'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Tool Description */}
              <p className="text-gray-300 mb-4">{tool.description}</p>

              {/* Actions */}
              <div className="flex gap-3">
                <Link
                  to={tool.link}
                  className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-center transition-colors"
                >
                  Configure
                </Link>
                {tool.external && (
                  <a
                    href={tool.external}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg flex items-center gap-2 transition-colors"
                  >
                    Open
                    <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Stats */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white/5 backdrop-blur-lg rounded-lg p-6 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Active Dashboards</div>
            <div className="text-3xl font-bold text-white">0</div>
            <div className="text-gray-500 text-xs mt-1">Grafana dashboards</div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg rounded-lg p-6 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Metrics Collected</div>
            <div className="text-3xl font-bold text-white">0</div>
            <div className="text-gray-500 text-xs mt-1">Prometheus time series</div>
          </div>

          <div className="bg-white/5 backdrop-blur-lg rounded-lg p-6 border border-white/10">
            <div className="text-gray-400 text-sm mb-1">Page Views</div>
            <div className="text-3xl font-bold text-white">0</div>
            <div className="text-gray-500 text-xs mt-1">Umami tracked views</div>
          </div>
        </div>

        {/* Info Banner */}
        <div className="mt-8 bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <PresentationChartBarIcon className="w-6 h-6 text-blue-400 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-white font-semibold mb-1">Configuration Required</h4>
              <p className="text-gray-300 text-sm">
                Monitoring tools are currently in planning phase. Click "Configure" on each tool
                to set up credentials, data sources, and integration settings. Once configured,
                external links will allow direct access to dashboards.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
