import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  MagnifyingGlassIcon,
  XMarkIcon,
  CheckIcon,
  CurrencyDollarIcon,
  SparklesIcon,
  UserGroupIcon,
  KeyIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { useTheme } from '../contexts/ThemeContext';

export default function SubscriptionManagement() {
  const { theme, currentTheme } = useTheme();
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState([]);
  const [filteredPlans, setFilteredPlans] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [planToDelete, setPlanToDelete] = useState(null);
  const [saving, setSaving] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    id: '',
    name: '',
    display_name: '',
    description: '',
    price_monthly: 0,
    price_yearly: 0,
    features: [],
    services: [],
    api_call_limit: 1000,
    byok_enabled: false,
    priority_support: false,
    team_seats: 1,
    active: true
  });

  // Available features and services
  const availableFeatures = [
    'All Models Access',
    'BYOK (Bring Your Own Keys)',
    'Priority Support',
    'Team Management',
    'SSO Integration',
    'Audit Logs',
    'Custom Branding',
    'Advanced Analytics',
    'API Access',
    'Webhooks',
    'SLA Guarantee',
    'Dedicated Support'
  ];

  const availableServices = [
    { id: 'ops-center', name: 'Ops Center', icon: ChartBarIcon },
    { id: 'chat', name: 'Open-WebUI', icon: SparklesIcon },
    { id: 'search', name: 'Center-Deep Search', icon: MagnifyingGlassIcon },
    { id: 'billing', name: 'Billing Portal', icon: CurrencyDollarIcon },
    { id: 'litellm', name: 'LiteLLM Proxy', icon: KeyIcon },
    { id: 'lago', name: 'Lago Billing', icon: ChartBarIcon },
    { id: 'tts', name: 'Unicorn Orator (TTS)', icon: SparklesIcon },
    { id: 'stt', name: 'Unicorn Amanuensis (STT)', icon: SparklesIcon },
    { id: 'vllm', name: 'vLLM Engine', icon: SparklesIcon },
    { id: 'embeddings', name: 'Embeddings Service', icon: SparklesIcon }
  ];

  useEffect(() => {
    loadPlans();
  }, []);

  useEffect(() => {
    filterPlans();
  }, [searchQuery, plans]);

  const loadPlans = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/subscriptions/plans');
      if (response.ok) {
        const data = await response.json();
        setPlans(data);
      } else {
        console.error('Failed to load plans');
      }
    } catch (error) {
      console.error('Error loading plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterPlans = () => {
    if (!searchQuery.trim()) {
      setFilteredPlans(plans);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered = plans.filter(plan =>
      plan.name?.toLowerCase().includes(query) ||
      plan.display_name?.toLowerCase().includes(query) ||
      plan.description?.toLowerCase().includes(query)
    );
    setFilteredPlans(filtered);
  };

  const getTierBadgeColor = (planName) => {
    const name = planName?.toLowerCase() || '';
    if (name.includes('trial')) return 'bg-blue-500 text-white';
    if (name.includes('starter')) return 'bg-green-500 text-white';
    if (name.includes('professional') || name.includes('pro')) return 'bg-purple-500 text-white';
    if (name.includes('enterprise')) return 'bg-gradient-to-r from-yellow-500 to-orange-500 text-white';
    return 'bg-gray-500 text-white';
  };

  const openCreateModal = () => {
    setFormData({
      id: '',
      name: '',
      display_name: '',
      description: '',
      price_monthly: 0,
      price_yearly: 0,
      features: [],
      services: ['ops-center', 'chat'],
      api_call_limit: 1000,
      byok_enabled: false,
      priority_support: false,
      team_seats: 1,
      active: true
    });
    setModalMode('create');
    setSelectedPlan(null);
    setShowModal(true);
  };

  const openEditModal = (plan) => {
    setFormData({
      id: plan.id,
      name: plan.name || '',
      display_name: plan.display_name || '',
      description: plan.description || '',
      price_monthly: plan.price_monthly || 0,
      price_yearly: plan.price_yearly || 0,
      features: plan.features || [],
      services: plan.services || [],
      api_call_limit: plan.api_call_limit || 1000,
      byok_enabled: plan.byok_enabled || false,
      priority_support: plan.priority_support || false,
      team_seats: plan.team_seats || 1,
      active: plan.active !== false
    });
    setModalMode('edit');
    setSelectedPlan(plan);
    setShowModal(true);
  };

  const handleSavePlan = async () => {
    setSaving(true);
    try {
      const url = modalMode === 'create'
        ? '/api/v1/subscriptions/plans'
        : `/api/v1/subscriptions/plans/${formData.id}`;

      const method = modalMode === 'create' ? 'POST' : 'PUT';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        await loadPlans();
        setShowModal(false);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to save plan'}`);
      }
    } catch (error) {
      console.error('Error saving plan:', error);
      alert('Failed to save plan');
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePlan = async () => {
    if (!planToDelete) return;

    try {
      const response = await fetch(`/api/v1/subscriptions/plans/${planToDelete.id}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        await loadPlans();
        setShowDeleteConfirm(false);
        setPlanToDelete(null);
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to delete plan'}`);
      }
    } catch (error) {
      console.error('Error deleting plan:', error);
      alert('Failed to delete plan');
    }
  };

  const toggleFeature = (feature) => {
    setFormData(prev => ({
      ...prev,
      features: prev.features.includes(feature)
        ? prev.features.filter(f => f !== feature)
        : [...prev.features, feature]
    }));
  };

  const toggleService = (serviceId) => {
    setFormData(prev => ({
      ...prev,
      services: prev.services.includes(serviceId)
        ? prev.services.filter(s => s !== serviceId)
        : [...prev.services, serviceId]
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className={`text-3xl font-bold ${theme.text.primary}`}>
            Subscription Plans
          </h1>
          <p className={`mt-2 ${theme.text.secondary}`}>
            Manage subscription tiers, pricing, and app/feature access
          </p>
        </div>
        <button
          onClick={openCreateModal}
          className={`${theme.button} flex items-center gap-2 px-6 py-3 rounded-lg font-semibold transition-all shadow-lg`}
        >
          <PlusIcon className="h-5 w-5" />
          Create New Plan
        </button>
      </div>

      {/* Search Bar */}
      <div className={`${theme.card} rounded-lg p-4`}>
        <div className="relative">
          <MagnifyingGlassIcon className={`absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 ${theme.text.secondary}`} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search plans by name, tier, or features..."
            className={`w-full pl-10 pr-4 py-2 rounded-lg border ${
              currentTheme === 'light'
                ? 'border-gray-300 bg-white text-gray-900'
                : 'border-gray-600 bg-gray-700 text-white'
            } focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-600 rounded transition-colors`}
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 gap-6">
        {filteredPlans.length === 0 ? (
          <div className={`${theme.card} rounded-lg p-12 text-center`}>
            <CurrencyDollarIcon className={`h-16 w-16 mx-auto mb-4 ${theme.text.secondary} opacity-50`} />
            <p className={`text-lg ${theme.text.primary} mb-2`}>
              {searchQuery ? 'No plans found' : 'No subscription plans yet'}
            </p>
            <p className={`${theme.text.secondary}`}>
              {searchQuery ? 'Try a different search query' : 'Create your first subscription plan to get started'}
            </p>
          </div>
        ) : (
          filteredPlans.map((plan) => (
            <motion.div
              key={plan.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className={`${theme.card} rounded-lg overflow-hidden hover:shadow-xl transition-shadow duration-300`}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className={`text-xl font-bold ${theme.text.primary}`}>
                        {plan.display_name || plan.name}
                      </h3>
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getTierBadgeColor(plan.name)}`}>
                        {plan.name?.toUpperCase()}
                      </span>
                      {!plan.active && (
                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500 text-white">
                          INACTIVE
                        </span>
                      )}
                    </div>
                    {plan.description && (
                      <p className={`text-sm ${theme.text.secondary} mb-3`}>
                        {plan.description}
                      </p>
                    )}
                    <div className="flex items-center gap-6 mb-4">
                      <div>
                        <span className={`text-3xl font-bold ${theme.text.primary}`}>
                          ${plan.price_monthly}
                        </span>
                        <span className={`text-sm ${theme.text.secondary}`}>/month</span>
                      </div>
                      {plan.price_yearly > 0 && (
                        <div>
                          <span className={`text-2xl font-bold ${theme.text.accent}`}>
                            ${plan.price_yearly}
                          </span>
                          <span className={`text-sm ${theme.text.secondary}`}>/year</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openEditModal(plan)}
                      className={`p-2 rounded-lg ${
                        currentTheme === 'light'
                          ? 'hover:bg-blue-50 text-blue-600'
                          : 'hover:bg-blue-900/30 text-blue-400'
                      } transition-colors`}
                      title="Edit plan"
                    >
                      <PencilIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => {
                        setPlanToDelete(plan);
                        setShowDeleteConfirm(true);
                      }}
                      className={`p-2 rounded-lg ${
                        currentTheme === 'light'
                          ? 'hover:bg-red-50 text-red-600'
                          : 'hover:bg-red-900/30 text-red-400'
                      } transition-colors`}
                      title="Delete plan"
                    >
                      <TrashIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className={`p-3 rounded-lg ${
                    currentTheme === 'light' ? 'bg-gray-50' : 'bg-gray-700/30'
                  }`}>
                    <div className={`text-xs ${theme.text.secondary} mb-1`}>API Calls</div>
                    <div className={`text-lg font-bold ${theme.text.primary}`}>
                      {plan.api_call_limit === -1 ? 'Unlimited' : plan.api_call_limit?.toLocaleString()}
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${
                    currentTheme === 'light' ? 'bg-gray-50' : 'bg-gray-700/30'
                  }`}>
                    <div className={`text-xs ${theme.text.secondary} mb-1`}>Team Seats</div>
                    <div className={`text-lg font-bold ${theme.text.primary}`}>
                      {plan.team_seats || 1}
                    </div>
                  </div>
                  <div className={`p-3 rounded-lg ${
                    currentTheme === 'light' ? 'bg-gray-50' : 'bg-gray-700/30'
                  }`}>
                    <div className={`text-xs ${theme.text.secondary} mb-1`}>Apps</div>
                    <div className={`text-lg font-bold ${theme.text.primary}`}>
                      {plan.services?.length || 0}
                    </div>
                  </div>
                </div>

                {/* Features */}
                {plan.features && plan.features.length > 0 && (
                  <div className="mb-4">
                    <h4 className={`text-sm font-semibold ${theme.text.primary} mb-2`}>Features:</h4>
                    <div className="flex flex-wrap gap-2">
                      {plan.features.map((feature, idx) => (
                        <span
                          key={idx}
                          className={`px-2 py-1 rounded text-xs ${
                            currentTheme === 'light'
                              ? 'bg-green-100 text-green-700'
                              : 'bg-green-900/30 text-green-400'
                          }`}
                        >
                          <CheckIcon className="inline h-3 w-3 mr-1" />
                          {feature}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Apps */}
                {plan.services && plan.services.length > 0 && (
                  <div>
                    <h4 className={`text-sm font-semibold ${theme.text.primary} mb-2`}>Available Apps:</h4>
                    <div className="flex flex-wrap gap-2">
                      {plan.services.map((serviceId, idx) => {
                        const service = availableServices.find(s => s.id === serviceId);
                        return (
                          <span
                            key={idx}
                            className={`px-2 py-1 rounded text-xs ${
                              currentTheme === 'light'
                                ? 'bg-blue-100 text-blue-700'
                                : 'bg-blue-900/30 text-blue-400'
                            }`}
                          >
                            {service?.name || serviceId}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          ))
        )}
      </div>

      {/* Create/Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4 overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className={`${theme.card} rounded-lg w-full max-w-4xl my-8`}
            >
              <div className="p-6 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h2 className={`text-2xl font-bold ${theme.text.primary}`}>
                    {modalMode === 'create' ? 'Create New Plan' : 'Edit Plan'}
                  </h2>
                  <button
                    onClick={() => setShowModal(false)}
                    className={`p-2 hover:bg-gray-700 rounded transition-colors`}
                  >
                    <XMarkIcon className="h-6 w-6" />
                  </button>
                </div>
              </div>

              <div className="p-6 space-y-6 max-h-[70vh] overflow-y-auto">
                {/* Basic Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Plan ID <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.id}
                      onChange={(e) => setFormData({ ...formData, id: e.target.value })}
                      disabled={modalMode === 'edit'}
                      placeholder="trial, starter, professional"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      } ${modalMode === 'edit' ? 'opacity-50 cursor-not-allowed' : ''}`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Plan Name <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      placeholder="Trial, Starter, Professional"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Display Name
                    </label>
                    <input
                      type="text"
                      value={formData.display_name}
                      onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                      placeholder="Professional Plan"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Description
                    </label>
                    <input
                      type="text"
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      placeholder="For growing teams and businesses"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                </div>

                {/* Pricing */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Monthly Price (USD) <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="number"
                      value={formData.price_monthly}
                      onChange={(e) => setFormData({ ...formData, price_monthly: parseFloat(e.target.value) || 0 })}
                      min="0"
                      step="0.01"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Yearly Price (USD)
                    </label>
                    <input
                      type="number"
                      value={formData.price_yearly}
                      onChange={(e) => setFormData({ ...formData, price_yearly: parseFloat(e.target.value) || 0 })}
                      min="0"
                      step="0.01"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                </div>

                {/* Limits & Settings */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      API Call Limit (-1 for unlimited)
                    </label>
                    <input
                      type="number"
                      value={formData.api_call_limit}
                      onChange={(e) => setFormData({ ...formData, api_call_limit: parseInt(e.target.value) || 0 })}
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                  <div>
                    <label className={`block text-sm font-medium ${theme.text.secondary} mb-2`}>
                      Team Seats
                    </label>
                    <input
                      type="number"
                      value={formData.team_seats}
                      onChange={(e) => setFormData({ ...formData, team_seats: parseInt(e.target.value) || 1 })}
                      min="1"
                      className={`w-full px-3 py-2 rounded-lg border ${
                        currentTheme === 'light'
                          ? 'border-gray-300 bg-white text-gray-900'
                          : 'border-gray-600 bg-gray-700 text-white'
                      }`}
                    />
                  </div>
                </div>

                {/* Toggles */}
                <div className="flex flex-wrap gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.byok_enabled}
                      onChange={(e) => setFormData({ ...formData, byok_enabled: e.target.checked })}
                      className="w-5 h-5 rounded border-gray-600"
                    />
                    <span className={theme.text.primary}>BYOK Enabled</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.priority_support}
                      onChange={(e) => setFormData({ ...formData, priority_support: e.target.checked })}
                      className="w-5 h-5 rounded border-gray-600"
                    />
                    <span className={theme.text.primary}>Priority Support</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.active}
                      onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                      className="w-5 h-5 rounded border-gray-600"
                    />
                    <span className={theme.text.primary}>Active</span>
                  </label>
                </div>

                {/* Features */}
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-3`}>
                    Features
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {availableFeatures.map((feature) => (
                      <label
                        key={feature}
                        className={`flex items-center gap-2 p-2 rounded cursor-pointer ${
                          formData.features.includes(feature)
                            ? currentTheme === 'light'
                              ? 'bg-blue-100 border-blue-300'
                              : 'bg-blue-900/30 border-blue-700'
                            : currentTheme === 'light'
                              ? 'bg-gray-50 border-gray-200'
                              : 'bg-gray-700/30 border-gray-600'
                        } border`}
                      >
                        <input
                          type="checkbox"
                          checked={formData.features.includes(feature)}
                          onChange={() => toggleFeature(feature)}
                          className="w-4 h-4"
                        />
                        <span className={`text-sm ${theme.text.primary}`}>{feature}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Apps/Services */}
                <div>
                  <label className={`block text-sm font-medium ${theme.text.secondary} mb-3`}>
                    Available Apps
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    {availableServices.map((service) => {
                      const ServiceIcon = service.icon;
                      return (
                        <label
                          key={service.id}
                          className={`flex items-center gap-2 p-3 rounded cursor-pointer ${
                            formData.services.includes(service.id)
                              ? currentTheme === 'light'
                                ? 'bg-green-100 border-green-300'
                                : 'bg-green-900/30 border-green-700'
                              : currentTheme === 'light'
                                ? 'bg-gray-50 border-gray-200'
                                : 'bg-gray-700/30 border-gray-600'
                          } border`}
                        >
                          <input
                            type="checkbox"
                            checked={formData.services.includes(service.id)}
                            onChange={() => toggleService(service.id)}
                            className="w-4 h-4"
                          />
                          <ServiceIcon className="h-4 w-4" />
                          <span className={`text-sm ${theme.text.primary}`}>{service.name}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="p-6 border-t border-gray-700 flex gap-3">
                <button
                  onClick={() => setShowModal(false)}
                  className={`flex-1 px-6 py-3 rounded-lg border ${
                    currentTheme === 'light'
                      ? 'border-gray-300 hover:bg-gray-50 text-gray-700'
                      : 'border-gray-600 hover:bg-gray-700 text-white'
                  } transition-colors font-semibold`}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSavePlan}
                  disabled={saving || !formData.id || !formData.name}
                  className={`flex-1 ${theme.button} px-6 py-3 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {saving ? 'Saving...' : modalMode === 'create' ? 'Create Plan' : 'Save Changes'}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteConfirm && planToDelete && (
          <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className={`${theme.card} rounded-lg w-full max-w-md p-6`}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="p-3 bg-red-900/30 rounded-full">
                  <ExclamationTriangleIcon className="h-6 w-6 text-red-400" />
                </div>
                <h3 className={`text-xl font-bold ${theme.text.primary}`}>
                  Delete Plan
                </h3>
              </div>

              <p className={`${theme.text.secondary} mb-4`}>
                Are you sure you want to delete the <strong>{planToDelete.display_name || planToDelete.name}</strong> plan?
                This action cannot be undone.
              </p>

              <div className={`p-3 rounded-lg ${
                currentTheme === 'light' ? 'bg-yellow-50 border border-yellow-200' : 'bg-yellow-900/20 border border-yellow-700/30'
              } mb-6`}>
                <p className={`text-sm ${currentTheme === 'light' ? 'text-yellow-800' : 'text-yellow-400'}`}>
                  <strong>Warning:</strong> Users currently subscribed to this plan may lose access to services.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setPlanToDelete(null);
                  }}
                  className={`flex-1 px-4 py-2 rounded-lg border ${
                    currentTheme === 'light'
                      ? 'border-gray-300 hover:bg-gray-50 text-gray-700'
                      : 'border-gray-600 hover:bg-gray-700 text-white'
                  } transition-colors font-semibold`}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDeletePlan}
                  className="flex-1 px-4 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white font-semibold transition-colors"
                >
                  Delete Plan
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
