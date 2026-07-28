import React, { useState, useEffect } from 'react';
import { useTheme } from '../contexts/ThemeContext';

// Tab components
import ModelCatalog from './llm/ModelCatalog';
import APIProviders from './llm/APIProviders';
import TestingLab from './llm/TestingLab';
import AnalyticsDashboard from './llm/AnalyticsDashboard';

export default function LLMHub() {
  const { theme } = useTheme();
  const [activeTab, setActiveTab] = useState('catalog');

  // Set page title
  useEffect(() => {
    document.title = 'LLM Hub - Ops Center';
  }, []);

  const tabs = [
    { id: 'catalog', label: 'Model Catalog', icon: '📋', component: ModelCatalog },
    { id: 'providers', label: 'API Providers', icon: '🔑', component: APIProviders },
    { id: 'testing', label: 'Testing Lab', icon: '🧪', component: TestingLab },
    { id: 'analytics', label: 'Analytics', icon: '📊', component: AnalyticsDashboard }
  ];

  const ActiveComponent = tabs.find(tab => tab.id === activeTab)?.component || ModelCatalog;

  return (
    <div className="min-h-screen p-6">
      {/* Page Header */}
      <div className="mb-6">
        <h1 className={`text-3xl font-bold ${theme?.text?.primary || 'text-white'}`}>
          LLM Hub - Unified Model Management
        </h1>
        <p className={`mt-2 ${theme?.text?.secondary || 'text-gray-400'}`}>
          Manage cloud APIs, test models, and monitor usage from one interface.
        </p>
      </div>

      {/* Tab Navigation */}
      <div className={`flex gap-2 mb-6 border-b ${theme?.border || 'border-gray-700'}`}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-6 py-3 font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
              activeTab === tab.id
                ? `border-b-2 border-purple-500 ${theme?.text?.primary || 'text-white'}`
                : `${theme?.text?.secondary || 'text-gray-400'} hover:${theme?.text?.primary || 'hover:text-white'}`
            }`}
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`${tab.id}-panel`}
            tabIndex={activeTab === tab.id ? 0 : -1}
          >
            <span className="mr-2" aria-hidden="true">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div
        role="tabpanel"
        id={`${activeTab}-panel`}
        aria-labelledby={`${activeTab}-tab`}
        className="animate-fadeIn"
      >
        <ActiveComponent />
      </div>
    </div>
  );
}
