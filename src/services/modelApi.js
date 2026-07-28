/**
 * Model API Service
 * Handles all API calls for AI Model Management
 *
 * Uses dynamic service discovery to automatically adapt to different deployments.
 */

const API_BASE = '/api/v1';

class ModelApiService {
  constructor() {
    this.serviceUrls = null;
    this.discoveryPromise = null;
  }

  /**
   * Discover service endpoints dynamically
   * Caches results to avoid repeated API calls
   */
  async discoverServices() {
    // Return cached promise if already fetching
    if (this.discoveryPromise) {
      return this.discoveryPromise;
    }

    // Return cached URLs if available
    if (this.serviceUrls) {
      return this.serviceUrls;
    }

    // Fetch service URLs
    this.discoveryPromise = fetch(`${API_BASE}/services/discovery`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Service discovery failed');
        }
        return response.json();
      })
      .then(data => {
        this.serviceUrls = data.internal_urls || {};
        this.discoveryPromise = null;
        return this.serviceUrls;
      })
      .catch(error => {
        console.error('Service discovery failed, using fallback URLs:', error);
        this.discoveryPromise = null;
        // Fallback to localhost for development
        this.serviceUrls = {
          embeddings: 'http://localhost:8082',
          reranker: 'http://localhost:8083',
          ollama: 'http://localhost:11434',
          vllm: 'http://localhost:8000',
          openwebui: 'http://localhost:8080'
        };
        return this.serviceUrls;
      });

    return this.discoveryPromise;
  }

  /**
   * Get service URL for a specific backend
   */
  async getServiceUrl(backend) {
    const urls = await this.discoverServices();
    return urls[backend] || `http://localhost:8000`;
  }

  /**
   * Refresh service discovery cache
   * Call this when deployment configuration changes
   */
  refreshServiceDiscovery() {
    this.serviceUrls = null;
    this.discoveryPromise = null;
  }
  // Get global settings for a backend
  async getGlobalSettings(backend) {
    const response = await fetch(`${API_BASE}/models/settings/${backend}`);
    if (!response.ok) throw new Error('Failed to fetch settings');
    return response.json();
  }

  // Update global settings for a backend
  async updateGlobalSettings(backend, settings) {
    const response = await fetch(`${API_BASE}/models/settings/${backend}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings)
    });
    if (!response.ok) throw new Error('Failed to update settings');
    return response.json();
  }

  // Get model-specific settings
  async getModelSettings(backend, modelId) {
    const response = await fetch(`${API_BASE}/models/${backend}/${encodeURIComponent(modelId)}/settings`);
    if (!response.ok) throw new Error('Failed to fetch model settings');
    return response.json();
  }

  // Update model-specific settings
  async updateModelSettings(modelId, backend, settings) {
    const response = await fetch(`${API_BASE}/models/settings`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: modelId,
        backend: backend,
        settings: settings
      })
    });
    if (!response.ok) throw new Error('Failed to update model settings');
    return response.json();
  }

  // Get all installed models
  async getInstalledModels() {
    const response = await fetch(`${API_BASE}/models/installed`);
    if (!response.ok) throw new Error('Failed to fetch installed models');
    return response.json();
  }

  // Download a model
  async downloadModel(modelId, backend, settings = null) {
    const response = await fetch(`${API_BASE}/models/download`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_id: modelId,
        backend: backend,
        settings: settings
      })
    });
    if (!response.ok) throw new Error('Failed to start download');
    return response.json();
  }

  // Get download status for all tasks
  async getAllDownloads() {
    const response = await fetch(`${API_BASE}/models/downloads`);
    if (!response.ok) throw new Error('Failed to fetch download status');
    return response.json();
  }

  // Get download status for a specific task
  async getDownloadStatus(taskId) {
    const response = await fetch(`${API_BASE}/models/downloads/${taskId}`);
    if (!response.ok) throw new Error('Failed to fetch download status');
    return response.json();
  }

  // Activate a model
  async activateModel(backend, modelId) {
    const response = await fetch(`${API_BASE}/models/${backend}/${encodeURIComponent(modelId)}/activate`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to activate model');
    return response.json();
  }

  // Delete a model
  async deleteModel(backend, modelId) {
    if (backend === 'embeddings' || backend === 'reranker') {
      // Direct service API call for embeddings/reranker using dynamic discovery
      const serviceUrl = await this.getServiceUrl(backend);
      const response = await fetch(`${serviceUrl}/model/cache/${encodeURIComponent(modelId)}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete model');
      return response.json();
    } else {
      const response = await fetch(`${API_BASE}/models/${backend}/${encodeURIComponent(modelId)}`, {
        method: 'DELETE'
      });
      if (!response.ok) throw new Error('Failed to delete model');
      return response.json();
    }
  }

  // Get cached models for embeddings/reranker
  async getCachedModels(backend) {
    if (backend === 'embeddings' || backend === 'reranker') {
      const serviceUrl = await this.getServiceUrl(backend);
      const response = await fetch(`${serviceUrl}/model/cached`);
      if (!response.ok) throw new Error('Failed to fetch cached models');
      return response.json();
    }
    return { cached_models: [] };
  }

  // Get available models for embeddings/reranker
  async getAvailableModels(backend) {
    if (backend === 'embeddings' || backend === 'reranker') {
      const serviceUrl = await this.getServiceUrl(backend);
      const response = await fetch(`${serviceUrl}/model/available`);
      if (!response.ok) throw new Error('Failed to fetch available models');
      return response.json();
    }
    return { models: [] };
  }

  // Switch model for embeddings/reranker
  async switchModel(backend, modelId, settings = {}) {
    if (backend === 'embeddings' || backend === 'reranker') {
      const serviceUrl = await this.getServiceUrl(backend);
      const response = await fetch(`${serviceUrl}/model/switch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model_name: modelId,
          ...settings
        })
      });
      if (!response.ok) throw new Error('Failed to switch model');
      return response.json();
    }
    return this.activateModel(backend, modelId);
  }

  // Legacy endpoints for backward compatibility
  async getLegacyModels() {
    const response = await fetch(`${API_BASE}/models`);
    if (!response.ok) throw new Error('Failed to fetch models');
    return response.json();
  }

  // Monitor download progress with polling
  async monitorDownload(taskId, onProgress, interval = 1000) {
    return new Promise((resolve, reject) => {
      const checkProgress = async () => {
        try {
          const status = await this.getDownloadStatus(taskId);
          
          if (onProgress) {
            onProgress(status);
          }

          if (status.status === 'completed') {
            resolve(status);
          } else if (status.status === 'failed') {
            reject(new Error(status.error || 'Download failed'));
          } else {
            // Continue polling
            setTimeout(checkProgress, interval);
          }
        } catch (error) {
          reject(error);
        }
      };

      checkProgress();
    });
  }
}

export default new ModelApiService();