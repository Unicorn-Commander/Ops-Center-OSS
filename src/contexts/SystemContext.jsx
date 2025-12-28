import React, { createContext, useContext, useState, useEffect } from 'react';

const SystemContext = createContext();

export function useSystem() {
  const context = useContext(SystemContext);
  if (!context) {
    throw new Error('useSystem must be used within a SystemProvider');
  }
  return context;
}

export function SystemProvider({ children }) {
  const [systemStatus, setSystemStatus] = useState(null);
  const [services, setServices] = useState([]);
  const [models, setModels] = useState([]);
  const [activeModel, setActiveModel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Allow instant navigation by not blocking on initial load
  useEffect(() => {
    setLoading(false);
    
    // Fetch data in background with staggered timing
    setTimeout(() => fetchSystemStatus(), 200);
    setTimeout(() => fetchServices(), 400);
    setTimeout(() => fetchModels(), 600);
  }, []);

  // Setup WebSocket connection
  useEffect(() => {
    let ws;
    let reconnectInterval;

    const connect = () => {
      try {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        ws.onopen = () => {
          console.log('WebSocket connected');
          setWsConnected(true);
        };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setWsConnected(false);
        // Reconnect after 5 seconds
        reconnectInterval = setTimeout(connect, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      } catch (error) {
        console.error('WebSocket connection failed:', error);
        setWsConnected(false);
      }
    };

    connect();

    return () => {
      if (ws) ws.close();
      if (reconnectInterval) clearTimeout(reconnectInterval);
    };
  }, []);

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'system_update':
        setSystemStatus(data.data);
        break;
      case 'service_update':
        setServices(prev => 
          prev.map(s => s.name === data.data.name ? { ...s, ...data.data } : s)
        );
        break;
      case 'model_update':
        setModels(prev => 
          prev.map(m => m.id === data.data.id ? { ...m, ...data.data } : m)
        );
        break;
      default:
        console.log('Unknown WebSocket message type:', data.type);
    }
  };

  const fetchSystemStatus = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);
      
      const response = await fetch('/api/v1/system/status', {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Failed to fetch system status: ${response.status} - ${text}`);
      }
      const data = await response.json();
      setSystemStatus(data);
      setError(null);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('System status fetch error:', err);
        // Don't set global error for timeouts/network issues
      }
    }
  };

  const fetchServices = async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 8000);
      
      const response = await fetch('/api/v1/services', {
        signal: controller.signal
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) throw new Error('Failed to fetch services');
      const data = await response.json();
      setServices(data);
    } catch (err) {
      if (err.name !== 'AbortError') {
        console.error('Failed to fetch services:', err);
      }
    }
  };

  const fetchModels = async () => {
    try {
      const response = await fetch('/api/v1/models/installed');
      if (!response.ok) throw new Error('Failed to fetch models');
      const data = await response.json();
      
      // Combine vLLM and Ollama models into a single array with proper formatting
      const allModels = [];
      
      // Process vLLM models
      if (data.vllm && Array.isArray(data.vllm)) {
        data.vllm.forEach(model => {
          allModels.push({
            id: model.id,
            name: model.name || model.id.split('/').pop(),
            type: 'vLLM',
            backend: 'vllm',
            size: model.size || 'Unknown',
            last_used: model.last_modified || 'Never',
            active: false, // TODO: Get from vLLM service status
            quantization: 'Unknown',
            path: model.path,
            has_overrides: model.has_overrides || false
          });
        });
      }
      
      // Process Ollama models
      if (data.ollama && Array.isArray(data.ollama)) {
        data.ollama.forEach(model => {
          allModels.push({
            id: model.id,
            name: model.name || model.id,
            type: 'Ollama',
            backend: 'ollama',
            size: model.size ? `${(model.size / (1024**3)).toFixed(1)}GB` : 'Unknown',
            last_used: model.last_modified || 'Never',
            active: false, // Ollama models are activated on demand
            quantization: 'Unknown',
            has_overrides: model.has_overrides || false
          });
        });
      }
      
      setModels(allModels);
    } catch (err) {
      console.error('Models fetch error:', err);
      setError(err.message);
    }
  };

  const controlService = async (containerName, action) => {
    try {
      const response = await fetch(`/api/v1/services/${containerName}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action }),
      });
      if (!response.ok) throw new Error(`Failed to ${action} service`);
      const data = await response.json();
      // Update will come through WebSocket
      return data;
    } catch (err) {
      setError(err.message);
      throw err;
    }
  };

  const value = {
    systemData: systemStatus,
    systemStatus,
    services,
    models,
    activeModel,
    setActiveModel,
    loading,
    error,
    wsConnected,
    controlService,
    fetchSystemStatus,
    fetchServices,
    fetchModels,
    refreshSystem: fetchSystemStatus,
    refreshServices: fetchServices,
    refreshModels: fetchModels,
  };

  return (
    <SystemContext.Provider value={value}>
      {children}
    </SystemContext.Provider>
  );
}