/**
 * UsageAttribution.jsx - Usage Attribution View
 *
 * Detailed credit usage analytics and attribution.
 * Features: Usage by user, date filtering, service breakdown, export to CSV.
 *
 * API: GET /api/v1/org-billing/credits/{org_id}/usage
 * Created: November 15, 2025
 */

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../../contexts/ThemeContext';
import { useOrganization } from '../../contexts/OrganizationContext';
import {
  ChartBarIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
  CalendarIcon,
  UserGroupIcon,
  ServerIcon,
  CpuChipIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.3 }
  }
};

export default function UsageAttribution() {
  const { theme, currentTheme } = useTheme();
  const { currentOrg } = useOrganization();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [usageData, setUsageData] = useState(null);
  const [error, setError] = useState(null);

  // Filters
  const [dateRange, setDateRange] = useState('30'); // 7, 30, 90, custom
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [serviceFilter, setServiceFilter] = useState('all');
  const [modelFilter, setModelFilter] = useState('all');
  const [userFilter, setUserFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (currentOrg) {
      loadUsageData();
    }
  }, [currentOrg, dateRange, startDate, endDate, serviceFilter, modelFilter]);

  const loadUsageData = async () => {
    if (!currentOrg) return;

    try {
      setLoading(true);
      setError(null);

      let url = `/api/v1/org-billing/credits/${currentOrg.id}/usage`;
      const params = new URLSearchParams();

      if (dateRange === 'custom' && startDate && endDate) {
        params.append('start_date', startDate);
        params.append('end_date', endDate);
      } else {
        params.append('days', dateRange);
      }

      if (serviceFilter !== 'all') params.append('service_type', serviceFilter);
      if (modelFilter !== 'all') params.append('model', modelFilter);

      if (params.toString()) {
        url += `?${params.toString()}`;
      }

      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
      });

      if (!response.ok) {
        throw new Error('Failed to load usage data');
      }

      const data = await response.json();
      setUsageData(data);
    } catch (err) {
      console.error('Failed to load usage data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadUsageData();
    setRefreshing(false);
  };

  const formatCredits = (amount) => {
    if (amount === null || amount === undefined) return '0';
    return Math.floor(parseFloat(amount)).toLocaleString();
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return `$${parseFloat(amount).toFixed(2)}`;
  };

  const handleExportCSV = () => {
    if (!usageData?.usage_by_user) return;

    const headers = ['User', 'Email', 'Total Credits', 'Service Type', 'Model', 'Credits Used', 'Timestamp'];
    const rows = usageData.usage_by_user.flatMap(user =>
      (user.usage_details || []).map(detail => [
        user.user_name || 'N/A',
        user.user_email,
        user.total_credits,
        detail.service_type || 'N/A',
        detail.model || 'N/A',
        detail.credits_used,
        detail.timestamp || 'N/A'
      ])
    );

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `usage-report-${currentOrg.name}-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  if (loading && !usageData) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <ArrowPathIcon className="h-12 w-12 animate-spin mx-auto mb-4 text-purple-500" />
          <p className="text-gray-400">Loading usage data...</p>
        </div>
      </div>
    );
  }

  if (!currentOrg) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-gray-400">Please select an organization</p>
      </div>
    );
  }

  const byUser = usageData?.usage_by_user || [];
  const timeline = usageData?.timeline || [];
  const byService = usageData?.by_service || [];
  const byModel = usageData?.by_model || [];

  // Filter users by search
  const filteredUsers = byUser.filter(user =>
    user.user_email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.user_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Timeline chart
  const timelineChartData = {
    labels: timeline.map(t => t.date),
    datasets: [{
      label: 'Daily Credits Used',
      data: timeline.map(t => t.credits_used),
      borderColor: 'rgb(168, 85, 247)',
      backgroundColor: 'rgba(168, 85, 247, 0.1)',
      fill: true,
      tension: 0.4
    }]
  };

  const timelineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: currentTheme.cardBackground,
        titleColor: currentTheme.text,
        bodyColor: currentTheme.textSecondary
      }
    },
    scales: {
      x: {
        ticks: { color: currentTheme.textSecondary },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      },
      y: {
        ticks: { color: currentTheme.textSecondary },
        grid: { color: 'rgba(255, 255, 255, 0.05)' }
      }
    }
  };

  // Service breakdown chart
  const serviceChartData = {
    labels: byService.map(s => s.service_type || 'Unknown'),
    datasets: [{
      data: byService.map(s => s.credits_used),
      backgroundColor: [
        'rgba(168, 85, 247, 0.8)',
        'rgba(236, 72, 153, 0.8)',
        'rgba(251, 146, 60, 0.8)',
        'rgba(34, 197, 94, 0.8)',
        'rgba(59, 130, 246, 0.8)'
      ],
      borderColor: [
        'rgb(168, 85, 247)',
        'rgb(236, 72, 153)',
        'rgb(251, 146, 60)',
        'rgb(34, 197, 94)',
        'rgb(59, 130, 246)'
      ],
      borderWidth: 2
    }]
  };

  const serviceChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
        labels: { color: currentTheme.text }
      },
      tooltip: {
        backgroundColor: currentTheme.cardBackground,
        titleColor: currentTheme.text,
        bodyColor: currentTheme.textSecondary
      }
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold" style={{ color: currentTheme.text }}>
            Usage Attribution
          </h1>
          <p className="text-sm mt-1" style={{ color: currentTheme.textSecondary }}>
            Detailed credit usage analytics and reporting
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 rounded-lg border border-purple-500 text-purple-400 hover:bg-purple-500/10 disabled:opacity-50 flex items-center gap-2"
          >
            <ArrowPathIcon className={`h-5 w-5 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={handleExportCSV}
            className="px-4 py-2 rounded-lg bg-green-600 text-white hover:bg-green-700 flex items-center gap-2"
          >
            <ArrowDownTrayIcon className="h-5 w-5" />
            Export CSV
          </button>
          <button
            onClick={() => navigate('/admin/organization/credits')}
            className="px-4 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-6"
      >
        {/* Filters */}
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-4 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Date Range */}
            <div>
              <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Date Range
              </label>
              <select
                value={dateRange}
                onChange={(e) => setDateRange(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                style={{ color: currentTheme.text }}
              >
                <option value="7">Last 7 days</option>
                <option value="30">Last 30 days</option>
                <option value="90">Last 90 days</option>
                <option value="custom">Custom Range</option>
              </select>
            </div>

            {/* Custom Date Range */}
            {dateRange === 'custom' && (
              <>
                <div>
                  <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                    Start Date
                  </label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                    style={{ color: currentTheme.text }}
                  />
                </div>
                <div>
                  <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                    End Date
                  </label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                    style={{ color: currentTheme.text }}
                  />
                </div>
              </>
            )}

            {/* Service Filter */}
            <div>
              <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Service Type
              </label>
              <select
                value={serviceFilter}
                onChange={(e) => setServiceFilter(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                style={{ color: currentTheme.text }}
              >
                <option value="all">All Services</option>
                <option value="llm">LLM (Chat)</option>
                <option value="embedding">Embeddings</option>
                <option value="image">Image Generation</option>
                <option value="tts">Text-to-Speech</option>
                <option value="stt">Speech-to-Text</option>
              </select>
            </div>

            {/* Model Filter */}
            <div>
              <label className="block text-sm mb-2" style={{ color: currentTheme.textSecondary }}>
                Model
              </label>
              <select
                value={modelFilter}
                onChange={(e) => setModelFilter(e.target.value)}
                className="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                style={{ color: currentTheme.text }}
              >
                <option value="all">All Models</option>
                {byModel.map((m, i) => (
                  <option key={i} value={m.model}>{m.model}</option>
                ))}
              </select>
            </div>
          </div>
        </motion.div>

        {/* Summary Stats */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <ChartBarIcon className="h-8 w-8 text-purple-400" />
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {formatCredits(usageData?.total_credits || 0)}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Total Credits Used
            </div>
          </div>

          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <UserGroupIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {byUser.length}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Active Users
            </div>
          </div>

          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <ServerIcon className="h-8 w-8 text-green-400" />
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {byService.length}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Services Used
            </div>
          </div>

          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <CpuChipIcon className="h-8 w-8 text-yellow-400" />
            </div>
            <div className="text-3xl font-bold mb-1" style={{ color: currentTheme.text }}>
              {byModel.length}
            </div>
            <div className="text-sm" style={{ color: currentTheme.textSecondary }}>
              Models Used
            </div>
          </div>
        </motion.div>

        {/* Charts Row */}
        <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Timeline Chart */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <h3 className="text-lg font-semibold mb-4" style={{ color: currentTheme.text }}>
              Usage Timeline
            </h3>
            <div style={{ height: '300px' }}>
              <Line data={timelineChartData} options={timelineChartOptions} />
            </div>
          </div>

          {/* Service Breakdown */}
          <div
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <h3 className="text-lg font-semibold mb-4" style={{ color: currentTheme.text }}>
              Service Breakdown
            </h3>
            <div style={{ height: '300px' }}>
              {byService.length > 0 ? (
                <Doughnut data={serviceChartData} options={serviceChartOptions} />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  No service data
                </div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Usage by User Table */}
        <motion.div
          variants={itemVariants}
          className="rounded-xl p-6 border"
          style={{
            background: currentTheme.cardBackground,
            borderColor: currentTheme.border
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold" style={{ color: currentTheme.text }}>
              Usage by User
            </h3>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-purple-500"
                style={{ color: currentTheme.text }}
              />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: `1px solid ${currentTheme.border}` }}>
                  <th className="text-left py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    User
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    Total Credits
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    Equivalent Cost
                  </th>
                  <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                    % of Total
                  </th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="text-center py-8" style={{ color: currentTheme.textSecondary }}>
                      No usage data found
                    </td>
                  </tr>
                ) : (
                  filteredUsers.map((user, index) => {
                    const percent = usageData.total_credits > 0
                      ? (user.total_credits / usageData.total_credits) * 100
                      : 0;

                    return (
                      <tr
                        key={index}
                        className="border-b hover:bg-white/5 transition-colors"
                        style={{ borderColor: currentTheme.border }}
                      >
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white font-semibold">
                              {user.user_email?.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <div className="font-medium" style={{ color: currentTheme.text }}>
                                {user.user_email}
                              </div>
                              <div className="text-xs" style={{ color: currentTheme.textSecondary }}>
                                {user.user_name || 'No name'}
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="text-right py-3 px-4 font-semibold" style={{ color: currentTheme.text }}>
                          {formatCredits(user.total_credits)}
                        </td>
                        <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                          {formatCurrency(user.total_credits * 0.01)}
                        </td>
                        <td className="text-right py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-sm font-semibold text-purple-400">
                              {percent.toFixed(1)}%
                            </span>
                            <div className="w-24 bg-gray-700 rounded-full h-2">
                              <div
                                className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                                style={{ width: `${Math.min(percent, 100)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Model Usage Table */}
        {byModel.length > 0 && (
          <motion.div
            variants={itemVariants}
            className="rounded-xl p-6 border"
            style={{
              background: currentTheme.cardBackground,
              borderColor: currentTheme.border
            }}
          >
            <h3 className="text-lg font-semibold mb-4" style={{ color: currentTheme.text }}>
              Usage by Model
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr style={{ borderBottom: `1px solid ${currentTheme.border}` }}>
                    <th className="text-left py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                      Model
                    </th>
                    <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                      Credits Used
                    </th>
                    <th className="text-right py-3 px-4" style={{ color: currentTheme.textSecondary }}>
                      % of Total
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {byModel.map((model, index) => {
                    const percent = usageData.total_credits > 0
                      ? (model.credits_used / usageData.total_credits) * 100
                      : 0;

                    return (
                      <tr
                        key={index}
                        className="border-b hover:bg-white/5 transition-colors"
                        style={{ borderColor: currentTheme.border }}
                      >
                        <td className="py-3 px-4 font-medium" style={{ color: currentTheme.text }}>
                          {model.model}
                        </td>
                        <td className="text-right py-3 px-4" style={{ color: currentTheme.text }}>
                          {formatCredits(model.credits_used)}
                        </td>
                        <td className="text-right py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-sm font-semibold text-purple-400">
                              {percent.toFixed(1)}%
                            </span>
                            <div className="w-24 bg-gray-700 rounded-full h-2">
                              <div
                                className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-500"
                                style={{ width: `${Math.min(percent, 100)}%` }}
                              />
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}
