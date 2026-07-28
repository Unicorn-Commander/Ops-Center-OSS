import React, { useState, lazy, Suspense } from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import {
  ChartBarIcon,
  UserGroupIcon,
  ServerIcon
} from '@heroicons/react/24/outline';

const BillingDashboard = lazy(() => import('../BillingDashboard'));
const UserBillingDashboard = lazy(() => import('../billing/UserBillingDashboard'));
const SystemBillingOverview = lazy(() => import('./SystemBillingOverview'));

const TABS = [
  { id: 'overview', label: 'Overview', icon: ChartBarIcon },
  { id: 'per-user', label: 'Per-User', icon: UserGroupIcon },
  { id: 'system', label: 'System', icon: ServerIcon }
];

export default function RevenueDashboard() {
  const { theme, currentTheme } = useTheme();
  const [activeTab, setActiveTab] = useState('overview');

  const cardBg = currentTheme === 'unicorn'
    ? 'bg-white/10 backdrop-blur-md border border-purple-500/20'
    : currentTheme === 'light'
    ? 'bg-white border border-gray-200'
    : 'bg-slate-800 border border-slate-700';

  const textPrimary = currentTheme === 'light' ? 'text-gray-900' : 'text-white';
  const textSecondary = currentTheme === 'light' ? 'text-gray-600' : 'text-gray-400';

  return (
    <div className="space-y-6">
      <div>
        <h1 className={`text-2xl font-bold ${textPrimary}`}>Revenue Dashboard</h1>
        <p className={`mt-1 ${textSecondary}`}>
          Billing analytics, per-user revenue, and system billing overview.
        </p>
      </div>

      {/* Tab bar */}
      <div className={`rounded-xl ${cardBg}`}>
        <div className="border-b border-gray-200/20">
          <nav className="flex -mb-px" aria-label="Revenue views">
            {TABS.map(tab => {
              const isActive = activeTab === tab.id;
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
            {activeTab === 'overview' && <BillingDashboard />}
            {activeTab === 'per-user' && <UserBillingDashboard />}
            {activeTab === 'system' && <SystemBillingOverview />}
          </Suspense>
        </div>
      </div>
    </div>
  );
}
