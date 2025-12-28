import React, { useState, useEffect } from 'react';
import { Save, RefreshCw, Upload, Download, Plus, Trash2, Move, Eye, Palette, Settings } from 'lucide-react';

const LandingCustomization = () => {
  const [config, setConfig] = useState(null);
  const [themes, setThemes] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('theme');
  const [previewMode, setPreviewMode] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    loadConfiguration();
    loadThemes();
  }, []);

  const loadConfiguration = async () => {
    try {
      const response = await fetch('/api/v1/landing/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to load configuration:', error);
      showMessage('error', 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };

  const loadThemes = async () => {
    try {
      const response = await fetch('/api/v1/landing/themes');
      if (response.ok) {
        const data = await response.json();
        setThemes(data);
      }
    } catch (error) {
      console.error('Failed to load themes:', error);
    }
  };

  const saveConfiguration = async () => {
    setSaving(true);
    try {
      const response = await fetch('/api/v1/landing/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config)
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfig(data.config);
        showMessage('success', 'Configuration saved successfully!');
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      console.error('Failed to save configuration:', error);
      showMessage('error', 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const applyThemePreset = async (preset) => {
    try {
      const response = await fetch(`/api/v1/landing/theme/${preset}`, {
        method: 'POST'
      });
      
      if (response.ok) {
        const data = await response.json();
        setConfig(data.config);
        showMessage('success', `Applied ${themes[preset]?.name || preset} theme`);
      }
    } catch (error) {
      console.error('Failed to apply theme:', error);
      showMessage('error', 'Failed to apply theme');
    }
  };

  const addCustomLink = () => {
    const newLink = {
      id: `custom_${Date.now()}`,
      name: 'New Service',
      icon: '🔗',
      description: 'Custom service description',
      custom_url: 'https://example.com',
      enabled: true,
      order: config.services.length + config.custom_links.length + 1
    };
    
    setConfig({
      ...config,
      custom_links: [...config.custom_links, newLink]
    });
  };

  const removeCustomLink = (linkId) => {
    setConfig({
      ...config,
      custom_links: config.custom_links.filter(link => link.id !== linkId)
    });
  };

  const updateService = (serviceId, field, value) => {
    const services = config.services.map(service => 
      service.id === serviceId ? { ...service, [field]: value } : service
    );
    setConfig({ ...config, services });
  };

  const updateCustomLink = (linkId, field, value) => {
    const custom_links = config.custom_links.map(link => 
      link.id === linkId ? { ...link, [field]: value } : link
    );
    setConfig({ ...config, custom_links });
  };

  const exportConfig = () => {
    const dataStr = JSON.stringify(config, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'landing_config.json';
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const importConfig = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const importedConfig = JSON.parse(e.target.result);
          setConfig(importedConfig);
          showMessage('success', 'Configuration imported successfully');
        } catch (error) {
          showMessage('error', 'Invalid configuration file');
        }
      };
      reader.readAsText(file);
    }
  };

  const resetToDefault = async () => {
    if (window.confirm('Are you sure you want to reset to default configuration? This cannot be undone.')) {
      try {
        const response = await fetch('/api/v1/landing/reset', {
          method: 'POST'
        });
        
        if (response.ok) {
          const data = await response.json();
          setConfig(data.config);
          showMessage('success', 'Reset to default configuration');
        }
      } catch (error) {
        console.error('Failed to reset:', error);
        showMessage('error', 'Failed to reset configuration');
      }
    }
  };

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage({ type: '', text: '' }), 3000);
  };

  const openPreview = () => {
    window.open('/landing-dynamic.html', '_blank');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-600">Failed to load configuration</p>
        <button onClick={loadConfiguration} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Landing Page Customization
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Customize the appearance and content of your landing page
        </p>
      </div>

      {/* Message Alert */}
      {message.text && (
        <div className={`mb-4 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`}>
          {message.text}
        </div>
      )}

      {/* Action Buttons */}
      <div className="mb-6 flex flex-wrap gap-2">
        <button
          onClick={saveConfiguration}
          disabled={saving}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
        
        <button
          onClick={openPreview}
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 flex items-center gap-2"
        >
          <Eye className="w-4 h-4" />
          Preview
        </button>
        
        <button
          onClick={exportConfig}
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          Export
        </button>
        
        <label className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 cursor-pointer flex items-center gap-2">
          <Upload className="w-4 h-4" />
          Import
          <input type="file" accept=".json" onChange={importConfig} className="hidden" />
        </label>
        
        <button
          onClick={resetToDefault}
          className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" />
          Reset to Default
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <nav className="-mb-px flex space-x-8">
          {['theme', 'branding', 'services', 'welcome', 'admin'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        {/* Theme Tab */}
        {activeTab === 'theme' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold mb-4">Theme Settings</h2>
            
            {/* Theme Presets */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Theme Presets
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(themes).map(([key, theme]) => (
                  <button
                    key={key}
                    onClick={() => applyThemePreset(key)}
                    className={`p-3 rounded-lg border-2 transition ${
                      config.theme.preset === key
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div 
                        className="w-8 h-8 rounded"
                        style={{
                          background: `linear-gradient(135deg, ${theme.primary}, ${theme.secondary})`
                        }}
                      />
                      <span className="font-medium">{theme.name}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Custom Colors */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Custom Colors
              </label>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {['primary', 'secondary', 'accent'].map((color) => (
                  <div key={color}>
                    <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1 capitalize">
                      {color} Color
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        value={config.theme.custom_colors[color]}
                        onChange={(e) => setConfig({
                          ...config,
                          theme: {
                            ...config.theme,
                            custom_colors: {
                              ...config.theme.custom_colors,
                              [color]: e.target.value
                            }
                          }
                        })}
                        className="h-10 w-20"
                      />
                      <input
                        type="text"
                        value={config.theme.custom_colors[color]}
                        onChange={(e) => setConfig({
                          ...config,
                          theme: {
                            ...config.theme,
                            custom_colors: {
                              ...config.theme.custom_colors,
                              [color]: e.target.value
                            }
                          }
                        })}
                        className="flex-1 px-3 py-2 border rounded dark:bg-gray-700"
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Animations */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                Animations
              </label>
              <div className="space-y-2">
                {Object.entries(config.animations).map(([key, value]) => (
                  <label key={key} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={(e) => setConfig({
                        ...config,
                        animations: {
                          ...config.animations,
                          [key]: e.target.checked
                        }
                      })}
                      className="rounded"
                    />
                    <span className="text-sm capitalize">{key.replace(/_/g, ' ')}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Branding Tab */}
        {activeTab === 'branding' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Branding Settings</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Logo URL
              </label>
              <input
                type="text"
                value={config.branding.logo_url}
                onChange={(e) => setConfig({
                  ...config,
                  branding: { ...config.branding, logo_url: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
                placeholder="/magic-unicorn-logo.png"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Company Name
              </label>
              <input
                type="text"
                value={config.branding.company_name}
                onChange={(e) => setConfig({
                  ...config,
                  branding: { ...config.branding, company_name: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Company Subtitle
              </label>
              <input
                type="text"
                value={config.branding.company_subtitle}
                onChange={(e) => setConfig({
                  ...config,
                  branding: { ...config.branding, company_subtitle: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={config.branding.show_emoji}
                  onChange={(e) => setConfig({
                    ...config,
                    branding: { ...config.branding, show_emoji: e.target.checked }
                  })}
                  className="rounded"
                />
                <span className="text-sm">Show Emoji</span>
              </label>
              
              <div className="flex items-center gap-2">
                <label className="text-sm">Emoji:</label>
                <input
                  type="text"
                  value={config.branding.emoji}
                  onChange={(e) => setConfig({
                    ...config,
                    branding: { ...config.branding, emoji: e.target.value }
                  })}
                  className="w-16 px-2 py-1 border rounded dark:bg-gray-700 text-center"
                  maxLength="2"
                />
              </div>
            </div>
          </div>
        )}

        {/* Services Tab */}
        {activeTab === 'services' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Services & Links</h2>
              <button
                onClick={addCustomLink}
                className="px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-1"
              >
                <Plus className="w-4 h-4" />
                Add Custom Link
              </button>
            </div>

            <div className="space-y-3">
              {/* Built-in Services */}
              {config.services.map((service) => (
                <div key={service.id} className="p-4 border rounded-lg dark:border-gray-600">
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={service.icon}
                        onChange={(e) => updateService(service.id, 'icon', e.target.value)}
                        className="w-16 px-2 py-1 border rounded dark:bg-gray-700 text-center text-xl"
                        maxLength="2"
                        title="Emoji icon"
                      />
                      <input
                        type="text"
                        value={service.name}
                        onChange={(e) => updateService(service.id, 'name', e.target.value)}
                        className="flex-1 px-3 py-2 border rounded dark:bg-gray-700 font-medium"
                      />
                      <label className="flex items-center gap-1">
                        <input
                          type="checkbox"
                          checked={service.enabled}
                          onChange={(e) => updateService(service.id, 'enabled', e.target.checked)}
                          className="rounded"
                        />
                        <span className="text-sm">Enabled</span>
                      </label>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <input
                        type="text"
                        value={service.description}
                        onChange={(e) => updateService(service.id, 'description', e.target.value)}
                        className="w-full px-3 py-2 border rounded dark:bg-gray-700 text-sm"
                        placeholder="Service description"
                      />
                      <input
                        type="text"
                        value={service.logo_url || ''}
                        onChange={(e) => updateService(service.id, 'logo_url', e.target.value)}
                        className="w-full px-3 py-2 border rounded dark:bg-gray-700 text-sm"
                        placeholder="Logo URL (optional, e.g., /logo.png)"
                      />
                    </div>
                  </div>
                </div>
              ))}

              {/* Custom Links */}
              {config.custom_links.map((link) => (
                <div key={link.id} className="p-4 border-2 border-dashed border-green-300 rounded-lg dark:border-green-600 bg-green-50 dark:bg-green-900/20">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="flex items-center gap-3">
                      <input
                        type="text"
                        value={link.icon}
                        onChange={(e) => updateCustomLink(link.id, 'icon', e.target.value)}
                        className="w-16 px-2 py-1 border rounded dark:bg-gray-700 text-center text-xl"
                        maxLength="2"
                      />
                      <input
                        type="text"
                        value={link.name}
                        onChange={(e) => updateCustomLink(link.id, 'name', e.target.value)}
                        className="flex-1 px-3 py-2 border rounded dark:bg-gray-700 font-medium"
                      />
                      <label className="flex items-center gap-1">
                        <input
                          type="checkbox"
                          checked={link.enabled}
                          onChange={(e) => updateCustomLink(link.id, 'enabled', e.target.checked)}
                          className="rounded"
                        />
                        <span className="text-sm">Enabled</span>
                      </label>
                      <button
                        onClick={() => removeCustomLink(link.id)}
                        className="p-1 text-red-600 hover:bg-red-100 rounded"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="space-y-2">
                      <input
                        type="text"
                        value={link.description}
                        onChange={(e) => updateCustomLink(link.id, 'description', e.target.value)}
                        className="w-full px-3 py-2 border rounded dark:bg-gray-700 text-sm"
                        placeholder="Service description"
                      />
                      <input
                        type="url"
                        value={link.custom_url}
                        onChange={(e) => updateCustomLink(link.id, 'custom_url', e.target.value)}
                        className="w-full px-3 py-2 border rounded dark:bg-gray-700 text-sm"
                        placeholder="https://example.com"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Welcome Tab */}
        {activeTab === 'welcome' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Welcome Section</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Welcome Title
              </label>
              <input
                type="text"
                value={config.welcome.title}
                onChange={(e) => setConfig({
                  ...config,
                  welcome: { ...config.welcome, title: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Welcome Description
              </label>
              <textarea
                value={config.welcome.description}
                onChange={(e) => setConfig({
                  ...config,
                  welcome: { ...config.welcome, description: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
                rows="3"
              />
            </div>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={config.welcome.show_emoji}
                onChange={(e) => setConfig({
                  ...config,
                  welcome: { ...config.welcome, show_emoji: e.target.checked }
                })}
                className="rounded"
              />
              <span className="text-sm">Show emoji in welcome title</span>
            </label>
          </div>
        )}

        {/* Admin Tab */}
        {activeTab === 'admin' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Admin Section</h2>
            
            <label className="flex items-center gap-2 mb-4">
              <input
                type="checkbox"
                checked={config.admin_section.enabled}
                onChange={(e) => setConfig({
                  ...config,
                  admin_section: { ...config.admin_section, enabled: e.target.checked }
                })}
                className="rounded"
              />
              <span className="font-medium">Show Admin Section</span>
            </label>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Section Title
              </label>
              <input
                type="text"
                value={config.admin_section.title}
                onChange={(e) => setConfig({
                  ...config,
                  admin_section: { ...config.admin_section, title: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
                disabled={!config.admin_section.enabled}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Section Description
              </label>
              <textarea
                value={config.admin_section.description}
                onChange={(e) => setConfig({
                  ...config,
                  admin_section: { ...config.admin_section, description: e.target.value }
                })}
                className="w-full px-3 py-2 border rounded dark:bg-gray-700"
                rows="2"
                disabled={!config.admin_section.enabled}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Button Text
                </label>
                <input
                  type="text"
                  value={config.admin_section.button_text}
                  onChange={(e) => setConfig({
                    ...config,
                    admin_section: { ...config.admin_section, button_text: e.target.value }
                  })}
                  className="w-full px-3 py-2 border rounded dark:bg-gray-700"
                  disabled={!config.admin_section.enabled}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Button Emoji
                </label>
                <input
                  type="text"
                  value={config.admin_section.button_emoji}
                  onChange={(e) => setConfig({
                    ...config,
                    admin_section: { ...config.admin_section, button_emoji: e.target.value }
                  })}
                  className="w-16 px-2 py-1 border rounded dark:bg-gray-700 text-center"
                  maxLength="2"
                  disabled={!config.admin_section.enabled}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default LandingCustomization;