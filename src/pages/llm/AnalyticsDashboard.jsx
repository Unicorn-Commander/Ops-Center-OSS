/**
 * Comprehensive Analytics Dashboard
 *
 * Multi-section analytics platform with 5 tabs:
 * 1. Overview - Key metrics from all systems
 * 2. User Analytics - User growth, activity, engagement
 * 3. Billing Analytics - Revenue, subscriptions, usage costs
 * 4. Service Analytics - Service health, uptime, performance
 * 5. LLM Analytics - Existing LLM metrics
 */

import React, { useState, useEffect, lazy, Suspense } from 'react';
import { Tabs, Tab, Box, CircularProgress } from '@mui/material';
import { useTheme } from '../../contexts/ThemeContext';
import {
  ChartBarIcon,
  UsersIcon,
  CurrencyDollarIcon,
  ServerIcon,
  CpuChipIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

// Lazy load tab components for performance
const OverviewTab = lazy(() => import('./analytics/OverviewTab'));
const UserAnalyticsTab = lazy(() => import('./analytics/UserAnalyticsTab'));
const BillingAnalyticsTab = lazy(() => import('./analytics/BillingAnalyticsTab'));
const ServiceAnalyticsTab = lazy(() => import('./analytics/ServiceAnalyticsTab'));
const LLMAnalyticsTab = lazy(() => import('./analytics/LLMAnalyticsTab'));

// Loading component
const TabLoadingFallback = () => (
  <div className="flex items-center justify-center h-96">
    <div className="text-center">
      <CircularProgress />
      <p className="text-gray-400 mt-4">Loading analytics...</p>
    </div>
  </div>
);

// Tab Panel component
function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function AnalyticsDashboard() {
  const { currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [dateRange, setDateRange] = useState('30d');

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const tabsConfig = [
    { label: 'Overview', icon: ChartBarIcon },
    { label: 'Users', icon: UsersIcon },
    { label: 'Billing', icon: CurrencyDollarIcon },
    { label: 'Services', icon: ServerIcon },
    { label: 'LLM', icon: CpuChipIcon },
  ];

  // Theme-based styles
  const bgClass = currentTheme === 'unicorn'
    ? 'bg-purple-900/20 border border-purple-500/20'
    : currentTheme === 'light'
    ? 'bg-white border border-gray-200'
    : 'bg-gray-800 border border-gray-700';

  const textClass = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const subtextClass = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  return (
    <div className="p-6">
      {/* Header Section */}
      <div className="mb-6">
        <h2 className={`text-3xl font-bold ${textClass} mb-2`}>
          Analytics Dashboard
        </h2>
        <p className={subtextClass}>
          Comprehensive insights across users, billing, services, and AI operations
        </p>
      </div>

      {/* Tabs Navigation */}
      <div className={`${bgClass} rounded-xl`}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              color: currentTheme === 'light' ? '#6b7280' : '#9ca3af',
              fontSize: '0.95rem',
              fontWeight: 500,
              textTransform: 'none',
              minHeight: 64,
              '&.Mui-selected': {
                color: currentTheme === 'unicorn' ? '#a855f7' : currentTheme === 'light' ? '#7c3aed' : '#a855f7',
              },
            },
            '& .MuiTabs-indicator': {
              backgroundColor: currentTheme === 'unicorn' ? '#a855f7' : currentTheme === 'light' ? '#7c3aed' : '#a855f7',
              height: 3,
            },
          }}
        >
          {tabsConfig.map((tab, index) => (
            <Tab
              key={index}
              label={
                <div className="flex items-center gap-2">
                  <tab.icon className="w-5 h-5" />
                  <span>{tab.label}</span>
                </div>
              }
            />
          ))}
        </Tabs>

        {/* Tab Panels */}
        <Suspense fallback={<TabLoadingFallback />}>
          <TabPanel value={activeTab} index={0}>
            <OverviewTab dateRange={dateRange} setDateRange={setDateRange} />
          </TabPanel>
          <TabPanel value={activeTab} index={1}>
            <UserAnalyticsTab dateRange={dateRange} setDateRange={setDateRange} />
          </TabPanel>
          <TabPanel value={activeTab} index={2}>
            <BillingAnalyticsTab dateRange={dateRange} setDateRange={setDateRange} />
          </TabPanel>
          <TabPanel value={activeTab} index={3}>
            <ServiceAnalyticsTab dateRange={dateRange} setDateRange={setDateRange} />
          </TabPanel>
          <TabPanel value={activeTab} index={4}>
            <LLMAnalyticsTab dateRange={dateRange} setDateRange={setDateRange} />
          </TabPanel>
        </Suspense>
      </div>
    </div>
  );
}
