import React, { createContext, useContext, useState, useEffect } from 'react';

const DeploymentContext = createContext();

export const useDeployment = () => {
  const context = useContext(DeploymentContext);
  if (!context) {
    throw new Error('useDeployment must be used within DeploymentProvider');
  }
  return context;
};

export const DeploymentProvider = ({ children }) => {
  const [deployment, setDeployment] = useState({
    type: 'standalone', // standalone | hardware-appliance | enterprise
    primaryAppUrl: null,
    adminOnly: false,
    features: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDeploymentConfig();
  }, []);

  const fetchDeploymentConfig = async () => {
    try {
      const response = await fetch('/api/v1/deployment/config');
      if (response.ok) {
        const config = await response.json();
        setDeployment({
          type: config.deployment_type || 'standalone',
          primaryAppUrl: config.primary_app_url || null,
          adminOnly: config.admin_only_mode || false,
          features: config.enabled_features || [],
          applications: config.registered_applications || []
        });
      }
    } catch (error) {
      console.error('Failed to load deployment config:', error);
      // Default to standalone if config fetch fails
      setDeployment({
        type: 'standalone',
        primaryAppUrl: null,
        adminOnly: false,
        features: []
      });
    } finally {
      setLoading(false);
    }
  };

  const isHardwareAppliance = () => deployment.type === 'hardware-appliance';
  const isEnterprise = () => deployment.type === 'enterprise';
  const isAdminOnly = () => deployment.adminOnly;
  const getPrimaryAppUrl = () => deployment.primaryAppUrl || 'http://localhost:7777';

  return (
    <DeploymentContext.Provider value={{
      deployment,
      loading,
      isHardwareAppliance,
      isEnterprise,
      isAdminOnly,
      getPrimaryAppUrl
    }}>
      {children}
    </DeploymentContext.Provider>
  );
};