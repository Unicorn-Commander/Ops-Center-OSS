# Frontend LLM Configuration Specification

**For**: Frontend Developer Agent
**From**: Backend Developer Agent
**Date**: October 20, 2025
**Backend Status**: ✅ COMPLETE

---

## Quick Start

The backend API for LLM Configuration Management is ready. You need to build the React frontend.

**Base API URL**: `/api/v1/llm-config`
**Authentication**: Admin role required (Keycloak SSO session cookies)
**Full Docs**: `/services/ops-center/backend/docs/LLM_CONFIG_API.md`

---

## What You Need to Build

### 3 Main Pages

#### 1. AI Server Management (`/admin/llm-config/servers`)
**Purpose**: Manage self-hosted AI inference servers

**Components**:
- `AIServerList.jsx` - Table of servers with CRUD actions
- `AIServerModal.jsx` - Create/Edit modal form
- `AIServerHealth.jsx` - Health status widget
- `ModelExplorer.jsx` - Browse available models

**Key Features**:
- Add server: vLLM, Ollama, llama.cpp, OpenAI-compatible
- Test connection (health check)
- Get available models
- Enable/disable servers
- Delete (with safety check if in use)

#### 2. API Key Management (`/admin/llm-config/api-keys`)
**Purpose**: Manage 3rd party provider API keys (OpenRouter, OpenAI, Anthropic, etc.)

**Components**:
- `APIKeyList.jsx` - Table of keys with CRUD actions
- `APIKeyModal.jsx` - Create/Edit modal form
- `APIKeyUsage.jsx` - Usage statistics widget

**Key Features**:
- Add API key (provider selector: openrouter, openai, anthropic, google, cohere, together, fireworks)
- **SECURITY**: Never show plaintext keys (only masked: `****abc123`)
- Test key validity
- Enable/disable keys
- Delete (with safety check if in use)
- Track usage: requests, tokens, cost

#### 3. Active Provider Configuration (`/admin/llm-config/active`)
**Purpose**: Configure which provider to use for each purpose (chat/embeddings/reranking)

**Components**:
- `ActiveProviderConfig.jsx` - 3 cards for chat, embeddings, reranking
- `ProviderSelector.jsx` - Combined dropdown of AI servers + API keys

**Key Features**:
- Select active provider for chat
- Select active provider for embeddings
- Select active provider for reranking
- Optional fallback provider per purpose
- Visual indicator of current selection
- Health status display

---

## API Endpoints (All You Need)

### AI Servers

```javascript
// List servers
GET /api/v1/llm-config/servers?enabled_only=false

// Get specific server
GET /api/v1/llm-config/servers/{id}

// Create server
POST /api/v1/llm-config/servers
Body: {
  name: "Local vLLM Server",
  server_type: "vllm",  // vllm, ollama, llamacpp, openai-compatible
  base_url: "http://localhost:8000",
  enabled: true,
  use_for_chat: true,
  use_for_embeddings: false,
  use_for_reranking: false
}

// Update server
PUT /api/v1/llm-config/servers/{id}
Body: { enabled: false }  // Any fields, all optional

// Delete server
DELETE /api/v1/llm-config/servers/{id}

// Test connection
POST /api/v1/llm-config/servers/{id}/test
Response: { status: "healthy", message: "Healthy - 5 models available" }

// Get available models
GET /api/v1/llm-config/servers/{id}/models
Response: ["Qwen/Qwen2.5-32B-Instruct-AWQ", ...]
```

### API Keys

```javascript
// List keys (MASKED - never plaintext)
GET /api/v1/llm-config/api-keys?enabled_only=false
Response: [{ id: 1, provider: "openrouter", masked_key: "****e5d80", ... }]

// Get specific key (MASKED)
GET /api/v1/llm-config/api-keys/{id}

// Create key
POST /api/v1/llm-config/api-keys
Body: {
  provider: "openrouter",
  key_name: "Production Key",
  api_key: "sk-or-v1-abc123...",  // Plaintext (will be encrypted)
  use_for_ops_center: true
}
Response: { id: 1, masked_key: "****abc123", ... }  // Encrypted, never returned

// Update key
PUT /api/v1/llm-config/api-keys/{id}
Body: { key_name: "Updated Name", api_key: "new-key..." }  // Optional key rotation

// Delete key
DELETE /api/v1/llm-config/api-keys/{id}

// Test key
POST /api/v1/llm-config/api-keys/{id}/test
Response: { success: true, message: "Valid - 248 models available" }
```

### Active Providers

```javascript
// Get all active providers
GET /api/v1/llm-config/active
Response: {
  chat: {
    purpose: "chat",
    provider_type: "api_key",
    provider_id: 1,
    provider: { /* full provider object */ }
  },
  embeddings: { ... }
}

// Get active provider for specific purpose
GET /api/v1/llm-config/active/chat

// Set active provider
POST /api/v1/llm-config/active
Body: {
  purpose: "chat",
  provider_type: "ai_server",  // or "api_key"
  provider_id: 1,
  fallback_provider_type: "api_key",  // Optional
  fallback_provider_id: 2  // Optional
}
```

---

## Example API Client Service

**Create**: `/src/services/llmConfigApi.js`

```javascript
const API_BASE = '/api/v1/llm-config';

export const llmConfigApi = {
  // AI Servers
  async listServers(enabledOnly = false) {
    const res = await fetch(`${API_BASE}/servers?enabled_only=${enabledOnly}`, {
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createServer(data) {
    const res = await fetch(`${API_BASE}/servers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateServer(id, data) {
    const res = await fetch(`${API_BASE}/servers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteServer(id) {
    const res = await fetch(`${API_BASE}/servers/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async testServer(id) {
    const res = await fetch(`${API_BASE}/servers/${id}/test`, {
      method: 'POST',
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getServerModels(id) {
    const res = await fetch(`${API_BASE}/servers/${id}/models`, {
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // API Keys
  async listAPIKeys(enabledOnly = false) {
    const res = await fetch(`${API_BASE}/api-keys?enabled_only=${enabledOnly}`, {
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async createAPIKey(data) {
    const res = await fetch(`${API_BASE}/api-keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async updateAPIKey(id, data) {
    const res = await fetch(`${API_BASE}/api-keys/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteAPIKey(id) {
    const res = await fetch(`${API_BASE}/api-keys/${id}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
  },

  async testAPIKey(id) {
    const res = await fetch(`${API_BASE}/api-keys/${id}/test`, {
      method: 'POST',
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Active Providers
  async getActiveProviders() {
    const res = await fetch(`${API_BASE}/active`, {
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async setActiveProvider(data) {
    const res = await fetch(`${API_BASE}/active`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      credentials: 'include'
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};
```

---

## Data Models (TypeScript)

```typescript
// AI Server
interface AIServer {
  id: number;
  name: string;
  server_type: 'vllm' | 'ollama' | 'llamacpp' | 'openai-compatible';
  base_url: string;
  api_key?: string;
  model_path?: string;
  enabled: boolean;
  use_for_chat: boolean;
  use_for_embeddings: boolean;
  use_for_reranking: boolean;
  last_health_check?: string;  // ISO 8601
  health_status: 'healthy' | 'degraded' | 'down' | 'unknown';
  metadata: Record<string, any>;
  created_by: string;
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
}

// API Key (MASKED)
interface APIKey {
  id: number;
  provider: 'openrouter' | 'openai' | 'anthropic' | 'google' | 'cohere' | 'together' | 'fireworks';
  key_name: string;
  masked_key: string;  // "****abc123"
  enabled: boolean;
  use_for_ops_center: boolean;
  last_used?: string;  // ISO 8601
  requests_count: number;
  tokens_used: number;
  cost_usd: number;
  metadata: Record<string, any>;
  created_by: string;
  created_at: string;  // ISO 8601
  updated_at: string;  // ISO 8601
}

// Active Provider
interface ActiveProvider {
  purpose: 'chat' | 'embeddings' | 'reranking';
  provider_type: 'ai_server' | 'api_key';
  provider_id: number;
  provider: AIServer | APIKey;  // Full provider object
  fallback_provider_type?: 'ai_server' | 'api_key';
  fallback_provider_id?: number;
  updated_by?: string;
  updated_at?: string;  // ISO 8601
}
```

---

## UI/UX Requirements

### Color Scheme (Health Status)
```javascript
const healthColors = {
  healthy: '#4caf50',    // Green
  degraded: '#ff9800',   // Orange
  down: '#f44336',       // Red
  unknown: '#9e9e9e'     // Gray
};
```

### Tables
- **Pagination**: 10 items per page
- **Sortable**: All columns
- **Search**: Real-time filter
- **Actions**: Edit, Delete, Test (per row)
- **Bulk Actions**: Enable/Disable, Delete (multiple rows)
- **Auto-refresh**: Every 60 seconds (with toggle)

### Modals
- **Max width**: 600px
- **Validation**: Instant feedback on all fields
- **Loading state**: Show spinner during submit
- **Toast notifications**: Success/error messages
- **Keyboard shortcuts**: Esc to close, Enter to submit

### Security Warnings
- ⚠️ **Never show plaintext API keys** (only masked)
- ⚠️ **Confirm before delete** (especially if in use)
- ⚠️ **Warn when editing key** ("This will replace the existing key")
- ⚠️ **Never log keys to console** (security risk)

---

## Example Component Skeleton

```javascript
// src/pages/LLMConfigServers.jsx

import React, { useState, useEffect } from 'react';
import { llmConfigApi } from '../services/llmConfigApi';
import { useToast } from '../contexts/ToastContext';

export default function LLMConfigServers() {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingServer, setEditingServer] = useState(null);
  const toast = useToast();

  useEffect(() => {
    loadServers();
  }, []);

  const loadServers = async () => {
    try {
      setLoading(true);
      const data = await llmConfigApi.listServers();
      setServers(data);
    } catch (error) {
      toast.error('Failed to load servers: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingServer(null);
    setModalOpen(true);
  };

  const handleEdit = (server) => {
    setEditingServer(server);
    setModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this server?')) return;
    try {
      await llmConfigApi.deleteServer(id);
      toast.success('Server deleted');
      loadServers();
    } catch (error) {
      toast.error('Failed to delete: ' + error.message);
    }
  };

  const handleTest = async (id) => {
    try {
      const result = await llmConfigApi.testServer(id);
      toast.info(`Health: ${result.status} - ${result.message}`);
      loadServers();  // Refresh to show updated health status
    } catch (error) {
      toast.error('Test failed: ' + error.message);
    }
  };

  return (
    <div>
      <h1>AI Servers</h1>
      <button onClick={handleCreate}>Add Server</button>

      {loading ? (
        <div>Loading...</div>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>URL</th>
              <th>Health</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {servers.map(server => (
              <tr key={server.id}>
                <td>{server.name}</td>
                <td>{server.server_type}</td>
                <td>{server.base_url}</td>
                <td>
                  <span style={{ color: healthColors[server.health_status] }}>
                    {server.health_status}
                  </span>
                </td>
                <td>
                  <button onClick={() => handleEdit(server)}>Edit</button>
                  <button onClick={() => handleTest(server.id)}>Test</button>
                  <button onClick={() => handleDelete(server.id)}>Delete</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {modalOpen && (
        <AIServerModal
          server={editingServer}
          onClose={() => setModalOpen(false)}
          onSave={() => {
            setModalOpen(false);
            loadServers();
          }}
        />
      )}
    </div>
  );
}
```

---

## Routes to Add

**Add to** `src/config/routes.js`:

```javascript
{
  path: '/admin/llm-config',
  element: <LLMConfigLayout />,
  roles: ['admin'],
  children: [
    { path: '', element: <Navigate to="servers" replace /> },
    { path: 'servers', element: <LLMConfigServers /> },
    { path: 'api-keys', element: <LLMConfigAPIKeys /> },
    { path: 'active', element: <LLMConfigActive /> },
  ]
}
```

**Add to sidebar navigation**:
```javascript
{
  label: 'LLM Configuration',
  path: '/admin/llm-config',
  icon: SettingsIcon,
  roles: ['admin']
}
```

---

## Testing Checklist

### Manual Testing
- [ ] Create AI server (vLLM)
- [ ] Test server connection
- [ ] Get available models
- [ ] Update server settings
- [ ] Delete server
- [ ] Create API key (OpenRouter)
- [ ] Test API key validity
- [ ] Update API key
- [ ] Delete API key
- [ ] Set active provider for chat
- [ ] Set active provider with fallback
- [ ] View active providers

### Security Testing
- [ ] Verify API keys never shown in plaintext
- [ ] Verify API keys not logged to console
- [ ] Verify delete confirmation works
- [ ] Verify admin-only access enforced
- [ ] Verify session cookies required

### Error Handling
- [ ] Test with invalid server URL
- [ ] Test with invalid API key
- [ ] Test delete server in use (should fail)
- [ ] Test delete API key in use (should fail)
- [ ] Test without authentication (should redirect)

---

## Full Documentation

**API Reference**: `/services/ops-center/backend/docs/LLM_CONFIG_API.md` (1,214 lines)
**Backend Summary**: `/services/ops-center/backend/LLM_CONFIG_BACKEND_COMPLETE.md` (800+ lines)

**Questions?**:
1. Read API documentation for complete endpoint specs
2. Check example API client code above
3. See TypeScript data models above
4. Review UI/UX requirements above

---

## Ready to Build!

**Backend Status**: ✅ COMPLETE
**Your Task**: Build 3 pages with 9 components
**Estimated Time**: 4-6 hours
**Difficulty**: Medium (standard CRUD UI)

**Start with**:
1. Create API client service (`llmConfigApi.js`)
2. Build AIServerList component (simplest)
3. Build AIServerModal component (form)
4. Test with real backend
5. Repeat for API keys and active providers

**Good luck!** 🚀

---

**Backend Developer Agent**
**October 20, 2025**
