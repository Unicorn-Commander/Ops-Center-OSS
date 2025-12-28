# LLM Configuration Guide for UC-Cloud Apps

**Last Updated**: October 20, 2025
**Purpose**: Configure apps to use Ops-Center as centralized LLM provider

---

## 🎯 The Simple Answer

**All apps should point to Ops-Center's LLM API endpoint:**

### Production URL (External):
```bash
OPENAI_API_BASE=https://your-domain.com/api/v1/llm
OPENAI_API_KEY=not-needed  # Ops-Center handles keys
```

### Internal URL (Docker network):
```bash
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed  # Ops-Center handles keys
```

**That's it!** Apps don't need their own OpenAI/Anthropic/OpenRouter keys.

---

## 📋 App-Specific Configuration

### 1. Unicorn Brigade

**Purpose**: Multi-agent orchestration platform
**LLM Usage**: Agent reasoning, tool calls, conversation

**Configuration** (`Unicorn-Brigade/.env` or docker-compose):
```bash
# Point to Ops-Center for LLM inference
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed

# Alternative: Use direct vLLM if you want local-only
# VLLM_URL=http://unicorn-vllm:8000
```

**Note**: Brigade will have its own **agent orchestration** API, but for LLM calls, it uses Ops-Center.

**Brigade's Own API** (for other apps to use agents):
```bash
# Apps calling Brigade agents use this:
BRIGADE_API_URL=https://api.brigade.your-domain.com
BRIGADE_API_KEY=<user-specific-key>
```

---

### 2. Open-WebUI

**Purpose**: Chat interface for users
**LLM Usage**: Chat completions, embeddings

**Configuration** (`docker-compose.yml` or environment):
```bash
# OpenAI-compatible endpoint
OPENAI_API_BASE_URL=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed

# For embeddings (if needed)
EMBEDDINGS_API_BASE_URL=http://ops-center-direct:8084/api/v1/llm
EMBEDDINGS_API_KEY=not-needed
```

**Open-WebUI Admin → Settings → Connections**:
- API Endpoint: `http://ops-center-direct:8084/api/v1/llm/chat/completions`
- API Key: Leave blank or use `not-needed`

---

### 3. Center-Deep (Search Platform)

**Purpose**: AI-powered metasearch with tool servers
**LLM Usage**: Search result synthesis, report generation

**Configuration** (`Center-Deep-Pro/.env`):
```bash
# For AI-enhanced search features
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed

# Tool servers (ports 8001-8004) also use Ops-Center
TOOL_SERVER_LLM_ENDPOINT=http://ops-center-direct:8084/api/v1/llm/chat/completions
```

---

### 4. Custom Applications

**Any app that needs LLM access**:

**Python Example**:
```python
from openai import OpenAI

# Point to Ops-Center instead of OpenAI
client = OpenAI(
    base_url="http://ops-center-direct:8084/api/v1/llm",
    api_key="not-needed"  # Ops-Center handles authentication
)

response = client.chat.completions.create(
    model="openai/gpt-3.5-turbo",  # Will use OpenRouter
    messages=[{"role": "user", "content": "Hello"}]
)
```

**JavaScript Example**:
```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  baseURL: 'http://ops-center-direct:8084/api/v1/llm',
  apiKey: 'not-needed'
});

const response = await client.chat.completions.create({
  model: 'openai/gpt-3.5-turbo',
  messages: [{ role: 'user', content: 'Hello' }]
});
```

---

## 🔀 Two Separate AI Systems

### 1. **LLM Inference** (Ops-Center provides this)

**What**: Access to language models (GPT, Claude, Llama, etc.)
**Provider**: Ops-Center LLM Router
**Endpoint**: `https://your-domain.com/api/v1/llm/chat/completions`
**Use Cases**: Chat, text generation, embeddings, completions

**Apps using this**:
- Open-WebUI (chat interface)
- Center-Deep (search synthesis)
- Brigade (agent reasoning)
- Custom apps (any text generation)

**Configuration**:
```bash
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
```

---

### 2. **Agent Orchestration** (Brigade provides this)

**What**: Multi-agent workflows, tool execution, orchestration
**Provider**: Unicorn Brigade
**Endpoint**: `https://api.brigade.your-domain.com/api/agents/{id}/invoke`
**Use Cases**: Complex tasks, multi-step workflows, agent swarms

**Apps using this**:
- Ops-Center (for admin automation)
- Open-WebUI (for complex tasks)
- Custom apps (for orchestration)

**Configuration**:
```bash
BRIGADE_API_URL=https://api.brigade.your-domain.com
BRIGADE_API_KEY=<user-generated-key>
```

**Important**: Brigade itself ALSO uses Ops-Center for LLM calls:
```
App → Brigade (orchestration)
       ↓
       Brigade → Ops-Center (LLM inference)
                  ↓
                  Ops-Center → OpenRouter → GPT/Claude/etc.
```

---

## 📊 Ops-Center LLM API Reference

### Endpoints Available

**1. Chat Completions** (OpenAI-compatible)
```bash
POST /api/v1/llm/chat/completions
Content-Type: application/json

{
  "model": "openai/gpt-3.5-turbo",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.7,
  "max_tokens": 500
}
```

**2. List Models**
```bash
GET /api/v1/llm/models

# Returns available models from active provider
{
  "data": [
    {"id": "openai/gpt-4", "provider": "openrouter"},
    {"id": "anthropic/claude-3-opus", "provider": "openrouter"}
  ]
}
```

**3. Embeddings** (if configured)
```bash
POST /api/v1/llm/embeddings
Content-Type: application/json

{
  "model": "text-embedding-ada-002",
  "input": "Text to embed"
}
```

---

## 🔧 Current Active Provider

**As of now, Ops-Center is configured to use:**

- **Provider**: OpenRouter
- **API Key**: Pre-populated (encrypted in database)
- **Purpose**: Chat completions
- **Models Available**: 100+ (GPT-4, Claude, Llama, Mistral, etc.)

**To change provider**:
1. Go to: https://your-domain.com/admin/system/llm-providers
2. Add a new API key or AI server
3. Click "Set as Active" for desired purpose (chat/embeddings/reranking)
4. All apps automatically use the new provider! ✅

---

## 🚀 Deployment Checklist

### For Each App:

**Step 1**: Update environment variables
```bash
# In app's .env or docker-compose.yml
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed
```

**Step 2**: Restart the app
```bash
docker restart <app-container-name>
```

**Step 3**: Test LLM access
```bash
# Inside app container
curl -X POST http://ops-center-direct:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "openai/gpt-3.5-turbo", "messages": [{"role": "user", "content": "test"}]}'
```

**Step 4**: Verify logs
```bash
docker logs ops-center-direct | grep "LLM request"
```

---

## 🔐 Authentication & Authorization

### Internal Apps (on Docker network):
- **No API key needed** when calling from internal network
- Ops-Center trusts requests from `unicorn-network`

### External Apps (public internet):
- **Session-based auth**: Include Keycloak session cookie
- **API keys**: Generate user API key in Ops-Center
- **Service tokens**: For service-to-service calls (planned)

### Usage Tracking:
- All LLM calls logged to `llm_usage_log` table
- Per-user metering for billing
- Quota enforcement based on subscription tier

---

## 📈 Benefits of Centralized LLM Routing

### 1. **Single Point of Configuration**
- Change API keys in one place (Ops-Center UI)
- All apps instantly use new provider
- No need to redeploy apps

### 2. **Cost Optimization**
- Centralized billing through one account
- Easy to switch to cheaper providers
- Track usage across all apps

### 3. **Fallback & Reliability**
- Automatic failover to backup providers
- Health monitoring
- Rate limiting and retry logic

### 4. **Security**
- API keys never exposed to apps
- Encrypted storage in database
- Audit trail for all LLM calls

### 5. **Flexibility**
- Mix and match providers (OpenRouter for chat, local vLLM for embeddings)
- A/B testing different models
- Per-user provider selection (BYOK)

---

## 🧪 Testing Matrix

| App | Endpoint to Test | Expected Result |
|-----|-----------------|-----------------|
| **Open-WebUI** | Chat with model | Uses Ops-Center → OpenRouter |
| **Brigade** | Agent invocation | Agent uses Ops-Center for LLM |
| **Center-Deep** | AI search tool | Search synthesis via Ops-Center |
| **Custom App** | API call | Ops-Center routes to active provider |

---

## 🐛 Troubleshooting

### Issue: "Connection refused" when calling Ops-Center LLM API

**Cause**: Ops-Center backend not running or LLM router not initialized

**Fix**:
```bash
# Check backend is running
docker ps | grep ops-center-direct

# Check LLM router logs
docker logs ops-center-direct | grep "LLM"

# Restart backend
docker restart ops-center-direct
```

---

### Issue: "Invalid API key" error

**Cause**: App is still trying to use direct OpenAI/Anthropic endpoint

**Fix**:
```bash
# Verify environment variables
docker exec <app-container> printenv | grep OPENAI

# Should show:
# OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
# OPENAI_API_KEY=not-needed

# If not, update and restart
```

---

### Issue: "Model not found"

**Cause**: Active provider doesn't support requested model

**Fix**:
1. Check available models:
   ```bash
   curl http://ops-center-direct:8084/api/v1/llm/models
   ```
2. Use a model from the list
3. OR add a provider that supports the model (in LLM Providers UI)

---

## 📚 Related Documentation

- **LLM Provider UI**: `LLM_PROVIDER_MANAGEMENT_DEPLOYED.md`
- **Provider Integration**: `LLM_PROVIDER_INTEGRATION.md`
- **Testing Guide**: `LLM_TESTING_GUIDE.md`
- **System Settings**: `SYSTEM_SETTINGS_GUIDE.md`

---

## 🎯 Quick Reference Card

### Apps Configuration (Copy/Paste):

**Unicorn Brigade**:
```bash
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed
```

**Open-WebUI**:
```bash
OPENAI_API_BASE_URL=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed
```

**Center-Deep**:
```bash
OPENAI_API_BASE=http://ops-center-direct:8084/api/v1/llm
OPENAI_API_KEY=not-needed
```

**Custom Python App**:
```python
from openai import OpenAI
client = OpenAI(
    base_url="http://ops-center-direct:8084/api/v1/llm",
    api_key="not-needed"
)
```

---

**Remember**: You only configure providers in Ops-Center UI. Apps just need the endpoint URL!

**Ops-Center is the single source of truth for LLM access.**
