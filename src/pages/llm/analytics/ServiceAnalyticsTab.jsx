/**
 * Service Analytics Tab - Service health, uptime, performance
 * Displays service status, resource utilization, error rates, response times
 */

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import {
  ServerIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import MetricCard from '../../../components/analytics/MetricCard';
import AnalyticsChart from '../../../components/analytics/AnalyticsChart';
import DateRangeSelector from '../../../components/analytics/DateRangeSelector';
import { useTheme } from '../../../contexts/ThemeContext';

// Register Chart.js scales
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const ServiceAnalyticsTab = ({ dateRange, setDateRange }) => {
  const { currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [serviceMetrics, setServiceMetrics] = useState(null);
  const [services, setServices] = useState([]);
  const [uptimeData, setUptimeData] = useState(null);
  const [resourceData, setResourceData] = useState(null);
  const [responseTimeData, setResponseTimeData] = useState(null);

  useEffect(() => {
    fetchServiceAnalytics();
  }, [dateRange]);

  const fetchServiceAnalytics = async () => {
    setLoading(true);
    try {
      // NOTE: GET /api/v1/services/analytics does not exist. The only real
      // source today is the container health endpoint.
      const statusResponse = await fetch('/api/v1/services/status', { credentials: 'include' });
      if (!statusResponse.ok) throw new Error(`HTTP ${statusResponse.status}`);

      const statusData = await statusResponse.json();
      const serviceList = statusData.services || [];

      setServices(serviceList);
      setServiceMetrics({
        servicesHealthy: serviceList.filter(s => s.status === 'healthy').length,
        servicesTotal: serviceList.length,
        // Aggregated uptime / response-time / error-rate metrics are not
        // collected yet - rendered as "—", never invented.
        avgUptime: null,
        avgResponseTime: null,
      });

      // No uptime-history, per-service resource, or response-time-history
      // endpoints exist yet. Leave the charts empty ("No data available yet")
      // instead of rendering invented series.
      setUptimeData(null);
      setResourceData(null);
      setResponseTimeData(null);
    } catch (error) {
      console.error('Error fetching service analytics:', error);
      // Honest failure state - never demo numbers
      setServiceMetrics(null);
      setServices([]);
      setUptimeData(null);
      setResourceData(null);
      setResponseTimeData(null);
    } finally {
      setLoading(false);
    }
  };

  const bgClass = currentTheme === 'unicorn'
    ? 'bg-purple-900/20 border border-purple-500/20'
    : currentTheme === 'light'
    ? 'bg-white border border-gray-200'
    : 'bg-gray-800 border border-gray-700';

  const textClass = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const subtextClass = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h3 className={`text-xl font-semibold ${textClass}`}>Service Health & Performance</h3>
        <DateRangeSelector value={dateRange} onChange={setDateRange} />
      </div>

      {/* Metric Cards - real values only; "—" when a metric is not collected yet */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          icon={CheckCircleIcon}
          label="Services Healthy"
          value={serviceMetrics ? `${serviceMetrics.servicesHealthy}/${serviceMetrics.servicesTotal}` : '—'}
          color="green"
          loading={loading}
        />
        <MetricCard
          icon={ServerIcon}
          label="Avg Uptime"
          value={serviceMetrics?.avgUptime != null ? `${serviceMetrics.avgUptime}%` : '—'}
          color="blue"
          loading={loading}
        />
        <MetricCard
          icon={ClockIcon}
          label="Avg Response Time"
          value={serviceMetrics?.avgResponseTime != null ? `${serviceMetrics.avgResponseTime}ms` : '—'}
          color="purple"
          loading={loading}
        />
        <MetricCard
          icon={ExclamationTriangleIcon}
          label="Error Rate"
          value="—"
          color="yellow"
          loading={loading}
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Uptime Trends */}
        <div className={`${bgClass} rounded-xl p-6`}>
          <AnalyticsChart
            type="line"
            title="Service Uptime (Last 7 Days)"
            data={uptimeData}
            loading={loading}
            height="300px"
          />
        </div>

        {/* Resource Utilization */}
        <div className={`${bgClass} rounded-xl p-6`}>
          <AnalyticsChart
            type="bar"
            title="Resource Utilization by Service"
            data={resourceData}
            loading={loading}
            height="300px"
          />
        </div>
      </div>

      {/* Response Time Chart */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <AnalyticsChart
          type="line"
          title="Average Response Time (24h)"
          data={responseTimeData}
          loading={loading}
          height="300px"
        />
      </div>

      {/* Service Status Table - real container health; request/error counters
          are not collected yet, so those columns show "—" */}
      <div className={`${bgClass} rounded-xl p-6`}>
        <h3 className={`text-lg font-semibold ${textClass} mb-4`}>Service Status Details</h3>
        {services.length === 0 ? (
          <p className={`text-sm ${subtextClass} py-6 text-center`}>No service status available</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className={`text-left py-3 px-4 ${subtextClass} font-medium`}>Service</th>
                  <th className={`text-center py-3 px-4 ${subtextClass} font-medium`}>Status</th>
                  <th className={`text-right py-3 px-4 ${subtextClass} font-medium`}>Uptime</th>
                  <th className={`text-right py-3 px-4 ${subtextClass} font-medium`}>Requests</th>
                  <th className={`text-right py-3 px-4 ${subtextClass} font-medium`}>Errors</th>
                  <th className={`text-right py-3 px-4 ${subtextClass} font-medium`}>Avg Response</th>
                </tr>
              </thead>
              <tbody>
                {services.map((service, index) => (
                  <tr key={index} className="border-b border-gray-800 hover:bg-gray-800/30">
                    <td className={`py-3 px-4 ${textClass} font-medium`}>{service.name}</td>
                    <td className="py-3 px-4 text-center">
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        service.status === 'healthy'
                          ? 'bg-green-500/20 text-green-400'
                          : service.status === 'degraded'
                          ? 'bg-yellow-500/20 text-yellow-400'
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {service.status}
                      </span>
                    </td>
                    <td className={`py-3 px-4 text-right ${textClass}`}>
                      {service.uptime_percentage != null ? `${service.uptime_percentage}%` : '—'}
                    </td>
                    <td className={`py-3 px-4 text-right ${textClass}`}>—</td>
                    <td className={`py-3 px-4 text-right ${textClass}`}>—</td>
                    <td className={`py-3 px-4 text-right ${textClass}`}>
                      {service.response_time_ms != null ? `${service.response_time_ms}ms` : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Error Summary - error metrics are not collected yet */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className={`${bgClass} rounded-xl p-6`}>
          <h4 className={`text-sm ${subtextClass} mb-2`}>Total Errors (24h)</h4>
          <p className={`text-3xl font-bold ${textClass}`}>—</p>
          <p className="text-sm text-gray-500 mt-2">Not tracked yet</p>
        </div>
        <div className={`${bgClass} rounded-xl p-6`}>
          <h4 className={`text-sm ${subtextClass} mb-2`}>Avg Error Rate</h4>
          <p className={`text-3xl font-bold ${textClass}`}>—</p>
          <p className="text-sm text-gray-500 mt-2">Not tracked yet</p>
        </div>
        <div className={`${bgClass} rounded-xl p-6`}>
          <h4 className={`text-sm ${subtextClass} mb-2`}>Critical Incidents</h4>
          <p className={`text-3xl font-bold ${textClass}`}>—</p>
          <p className="text-sm text-gray-500 mt-2">Not tracked yet</p>
        </div>
      </div>
    </div>
  );
};

export default ServiceAnalyticsTab;
