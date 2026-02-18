# LiteLLM + WilmerAI Integration Plan

**Date**: October 20, 2025
**Purpose**: Multi-provider LLM routing with intelligent cost/latency optimization
**Based on**: ChatGPT recommendations + Unicorn Commander requirements

---

## 🎯 Overview

Implement a **credit broker** system where Ops-Center acts as a smart router between users and multiple LLM providers, with **WilmerAI** making intelligent routing decisions based on cost, latency, quality, and user tier.

**Key Principle**: Users never see provider API keys. They buy credits, choose a "power level," and WilmerAI routes requests intelligently.

---

## 🏗️ Architecture

```
User Request
    ↓
[Ops-Center API]
    ↓
[Credit Check & Deduction]
    ↓
[WilmerAI Router Logic]
    ├→ Analyzes: task type, tokens, latency SLO, privacy flag, user tier, budget
    └→ Selects: provider, model, parameters
    ↓
[LiteLLM Proxy]
    ├→ Routes to: OpenRouter, HF, Together, DeepInfra, Groq, Fireworks, OpenAI, Anthropic, Local
    └→ Logs: tokens, cost, latency, provider
    ↓
[Response + Usage Metering]
    ├→ Updates user credits
    ├→ Logs to analytics
    └→ Returns to user
```

---

## 🔧 Components

### 1. LiteLLM Proxy (Core Router)

**Purpose**: Unified API adapter for all providers

**Configuration** (`litellm_config.yaml`):
```yaml
model_list:
  # --- Local (Free Tier) ---
  - model_name: llama3-8b-local
    litellm_params:
      model: ollama/llama3
      api_base: http://unicorn-ollama:11434
      
  - model_name: qwen-32b-local
    litellm_params:
      model: vllm/Qwen2.5-32B-Instruct-AWQ
      api_base: http://unicorn-vllm:8000
  
  # --- Free Tier Providers ---
  - model_name: llama3-70b-groq
    litellm_params:
      model: groq/llama3-70b-8192
      api_key: os.environ/GROQ_API_KEY
      
  - model_name: mixtral-8x7b-hf
    litellm_params:
      model: huggingface/mistralai/Mixtral-8x7B-Instruct-v0.1
      api_key: os.environ/HF_API_KEY
  
  # --- Paid Tier (Low Cost) ---
  - model_name: mixtral-8x22b-together
    litellm_params:
      model: together_ai/mistralai/Mixtral-8x22B-Instruct-v0.1
      api_key: os.environ/TOGETHER_API_KEY
      
  - model_name: llama3-70b-deepinfra
    litellm_params:
      model: deepinfra/meta-llama/Meta-Llama-3-70B-Instruct
      api_key: os.environ/DEEPINFRA_API_KEY
      
  - model_name: qwen-72b-fireworks
    litellm_params:
      model: fireworks_ai/accounts/fireworks/models/qwen-72b
      api_key: os.environ/FIREWORKS_API_KEY
  
  # --- OpenRouter (Multi-Model Gateway) ---
  - model_name: claude-3.5-sonnet-openrouter
    litellm_params:
      model: openrouter/anthropic/claude-3.5-sonnet
      api_key: os.environ/OPENROUTER_API_KEY
      
  - model_name: gpt-4o-openrouter
    litellm_params:
      model: openrouter/openai/gpt-4o
      api_key: os.environ/OPENROUTER_API_KEY
  
  # --- Premium (Direct) ---
  - model_name: claude-3.5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
      
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY

# General settings
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db
  
litellm_settings:
  success_callback: ["postgres"]
  failure_callback: ["postgres"]
  num_retries: 2
  request_timeout: 60
  fallbacks: true
```

---

### 2. WilmerAI Router Logic

**Purpose**: Intelligent provider selection based on context

**Decision Matrix**:
```python
# wilmer_router.py

class WilmerRouter:
    def select_provider(self, request):
        """
        Inputs:
          - task_type: "code", "chat", "rag", "creative", "analysis"
          - estimated_tokens: int
          - latency_slo: "instant", "fast", "normal"
          - privacy_required: bool
          - user_tier: "free", "starter", "professional", "enterprise"
          - credits_remaining: float
          - quality_requirement: "basic", "good", "best"
        
        Outputs:
          - provider: str (e.g., "groq", "openrouter:claude-3.5")
          - model: str
          - max_tokens: int
          - temperature: float
        """
        
        # Privacy-first: use local
        if request.privacy_required:
            return self._select_local_model(request)
        
        # Ultra-low latency: Groq
        if request.latency_slo == "instant":
            if request.estimated_tokens < 8000:
                return "llama3-70b-groq", {"max_tokens": 8192}
        
        # Budget-constrained: free tier
        if request.credits_remaining < 0.01 or request.user_tier == "free":
            if request.task_type == "code":
                return "qwen-32b-local", {"max_tokens": 16384}
            elif request.estimated_tokens < 8000:
                return "llama3-70b-groq", {"max_tokens": 8192}
            else:
                return "mixtral-8x7b-hf", {"max_tokens": 32768}
        
        # Code tasks: Qwen or Claude
        if request.task_type == "code":
            if request.quality_requirement == "best":
                return "claude-3.5-sonnet-openrouter", {"max_tokens": 8192}
            else:
                return "qwen-72b-fireworks", {"max_tokens": 32768}
        
        # Creative tasks: Claude or GPT-4o
        if request.task_type == "creative":
            if request.user_tier in ["enterprise", "professional"]:
                return "claude-3.5-sonnet", {"max_tokens": 8192}
            else:
                return "claude-3.5-sonnet-openrouter", {"max_tokens": 8192}
        
        # Long context RAG: Mixtral or Gemini
        if request.task_type == "rag" and request.estimated_tokens > 30000:
            return "mixtral-8x22b-together", {"max_tokens": 65536}
        
        # Default: balanced cost/quality
        if request.user_tier in ["enterprise", "professional"]:
            return "gpt-4o-openrouter", {"max_tokens": 4096}
        else:
            return "mixtral-8x22b-together", {"max_tokens": 8192}
    
    def _select_local_model(self, request):
        """Privacy-first: choose local model"""
        if request.task_type == "code":
            return "qwen-32b-local", {"max_tokens": 16384}
        else:
            return "llama3-8b-local", {"max_tokens": 8192}
```

---

### 3. User Power Levels (UX Simplification)

**Frontend**: 3 buttons instead of 30 knobs

```javascript
// User sees:
[ Eco Mode ]  [ Balanced Mode ]  [ Precision Mode ]

// Behind the scenes:
const powerLevels = {
  eco: {
    maxCostPerRequest: 0.001,
    preferredProviders: ["local", "groq", "huggingface"],
    qualityThreshold: 0.6,
    latencySLO: "normal"
  },
  balanced: {
    maxCostPerRequest: 0.01,
    preferredProviders: ["together", "fireworks", "openrouter"],
    qualityThreshold: 0.8,
    latencySLO: "fast"
  },
  precision: {
    maxCostPerRequest: 0.1,
    preferredProviders: ["anthropic", "openai", "openrouter:premium"],
    qualityThreshold: 0.95,
    latencySLO: "instant"
  }
};
```

---

### 4. Credit System

**Database Schema** (`credits` table):
```sql
CREATE TABLE user_credits (
  user_id UUID PRIMARY KEY,
  credits_remaining FLOAT DEFAULT 0,
  monthly_cap FLOAT,  -- spend ceiling
  tier TEXT,  -- "free", "starter", "professional", "enterprise"
  last_reset TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES user_credits(user_id),
  amount FLOAT,  -- positive for purchases, negative for usage
  transaction_type TEXT,  -- "purchase", "usage", "refund", "bonus"
  provider TEXT,
  model TEXT,
  tokens_used INT,
  cost FLOAT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Cost Calculation**:
```python
# Cost per 1K tokens (your markup)
PRICING = {
    "local": 0.0,
    "groq": 0.0,
    "huggingface": 0.0,
    "together": 0.002,
    "fireworks": 0.002,
    "deepinfra": 0.003,
    "openrouter:mixtral": 0.003,
    "openrouter:claude-3.5": 0.008,
    "openrouter:gpt-4o": 0.010,
    "anthropic": 0.015,
    "openai": 0.015
}

def calculate_cost(provider, model, tokens):
    base_cost = PRICING.get(provider, 0.01)
    return (tokens / 1000) * base_cost
```

---

### 5. API Endpoints

**User-Facing**:
```python
POST /api/v1/llm/chat/completions
  Headers:
    - Authorization: Bearer <user-api-key>
    - X-Power-Level: eco | balanced | precision (optional)
  Body:
    - messages: [...]
    - task_type: "code" | "chat" | "rag" | "creative" (optional)
    - privacy_required: bool (optional)
  Response:
    - Standard OpenAI format
    + X-Provider-Used: "groq"
    + X-Cost-Incurred: 0.002
    + X-Credits-Remaining: 9.998

GET /api/v1/llm/models
  Returns: List of available models per user tier

GET /api/v1/llm/usage
  Returns: Usage stats (tokens, cost, provider breakdown)

POST /api/v1/credits/purchase
  Body:
    - amount: float
    - stripe_token: str
  Returns: Updated credit balance

GET /api/v1/credits/balance
  Returns: Current balance, monthly cap, usage this month
```

**Admin-Facing**:
```python
GET /admin/llm/providers
  Returns: List of configured providers with status

POST /admin/llm/providers/{provider_id}/toggle
  Enable/disable a provider

PUT /admin/llm/routing-policy
  Update Wilmer routing rules

GET /admin/llm/usage-analytics
  Returns: Aggregated usage, cost by provider, user tier analysis
```

---

### 6. BYOK (Bring Your Own Key)

**Optional feature**: Users can add their own provider keys

**Database**:
```sql
CREATE TABLE user_provider_keys (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES user_credits(user_id),
  provider TEXT,  -- "openai", "anthropic", etc.
  api_key_encrypted TEXT,  -- encrypted with Fernet
  enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Routing Logic**:
```python
def select_provider(request):
    # Check if user has BYOK for preferred provider
    user_keys = get_user_provider_keys(request.user_id)
    
    if "openai" in user_keys and request.quality == "best":
        return "user:openai", user_keys["openai"]
    
    # Otherwise use platform keys
    return wilmer_router.select_provider(request)
```

---

## 📊 Provider Recommendations

### Tier 0: Free (Always Available)
| Provider | Model | Cost | Speed | Use Case |
|----------|-------|------|-------|----------|
| **Local** | Qwen 2.5 32B | $0 | Medium | Code, privacy |
| **Local** | Llama 3 8B | $0 | Fast | Chat, basic |
| **Groq** | Llama 3 70B | $0 | Ultrafast | Quick QA |
| **HuggingFace** | Mixtral 8x7B | $0 | Slow | Long context |

### Tier 1: Starter ($19/mo + usage)
| Provider | Model | Cost/1K | Speed | Use Case |
|----------|-------|---------|-------|----------|
| **Together** | Mixtral 8x22B | $0.001 | Fast | Balanced tasks |
| **Fireworks** | Qwen 72B | $0.0009 | Fast | Code tasks |
| **DeepInfra** | Llama 3 70B | $0.0007 | Medium | General |

### Tier 2: Professional ($49/mo + usage)
| Provider | Model | Cost/1K | Speed | Use Case |
|----------|-------|---------|-------|----------|
| **OpenRouter** | Claude 3.5 | $0.003 | Medium | Premium tasks |
| **OpenRouter** | GPT-4o | $0.005 | Medium | Best quality |

### Tier 3: Enterprise ($99/mo + usage)
| Provider | Model | Cost/1K | Speed | Use Case |
|----------|-------|---------|-------|----------|
| **Anthropic** | Claude 3.5 Sonnet | $0.003 | Fast | Direct access |
| **OpenAI** | GPT-4o | $0.005 | Fast | Direct access |

---

## 💰 Pricing Strategy

**Platform Subscription** (includes baseline compute):
- **Free**: $0/mo - 100 requests/day (local + free providers only)
- **Starter**: $19/mo - 1,000 requests + $10 credits
- **Professional**: $49/mo - 10,000 requests + $50 credits
- **Enterprise**: $99/mo - Unlimited requests + $200 credits

**Pay-As-You-Go Credits**:
- $10 = 10,000 credits
- $50 = 55,000 credits (10% bonus)
- $100 = 120,000 credits (20% bonus)

**Cost Markup**:
- Free tier: 0% (platform absorbs cost)
- Starter: 40% markup (covers infra)
- Professional: 60% markup
- Enterprise: 80% markup (SLA, support)

---

## 🛠️ Implementation Steps

### Phase 1: Infrastructure (Week 1)
1. ✅ Deploy LiteLLM Proxy container
2. ✅ Configure provider API keys
3. ✅ Create database tables
4. ✅ Implement credit system
5. ✅ Build basic routing logic

### Phase 2: WilmerAI Router (Week 2)
1. ✅ Implement decision matrix
2. ✅ Add task type detection
3. ✅ Build cost estimation
4. ✅ Add fallback logic
5. ✅ Implement quality feedback loop

### Phase 3: Frontend (Week 3)
1. ✅ LLM Management page (`/admin/llm`)
2. ✅ Provider configuration UI
3. ✅ Credit purchase flow
4. ✅ Usage analytics dashboard
5. ✅ Power level selector component

### Phase 4: BYOK & Advanced Features (Week 4)
1. ✅ BYOK key storage
2. ✅ Custom routing policies
3. ✅ A/B testing framework
4. ✅ Provider health monitoring
5. ✅ Auto-scaling logic

---

## 📁 File Structure

```
backend/
├── litellm_proxy/
│   ├── config.yaml                    # LiteLLM configuration
│   ├── Dockerfile                     # LiteLLM container
│   └── docker-compose.litellm.yml     # LiteLLM service
├── wilmer_router.py                   # Routing logic
├── llm_manager.py                     # Provider management
├── credits_manager.py                 # Credit system
└── llm_api.py                         # API endpoints

frontend/
├── src/pages/
│   └── LLMManagement.jsx              # Provider config UI
├── src/components/
│   ├── PowerLevelSelector.jsx         # Eco/Balanced/Precision
│   ├── ProviderCard.jsx               # Provider status card
│   ├── UsageChart.jsx                 # Cost/usage visualization
│   └── CreditBalance.jsx              # Credit display widget

docker-compose.llm.yml                 # LiteLLM + dependencies
```

---

## 🧪 Testing Plan

1. **Unit Tests**: Routing logic, credit calculations
2. **Integration Tests**: Provider API calls, fallback logic
3. **Load Tests**: Concurrent requests, rate limiting
4. **Cost Tests**: Verify markup calculations
5. **E2E Tests**: User flow from credit purchase to inference

---

## 🚀 Deployment Checklist

- [ ] Environment variables configured
- [ ] Provider API keys stored securely
- [ ] LiteLLM proxy deployed
- [ ] Database migrations run
- [ ] Frontend built and deployed
- [ ] Monitoring dashboards set up
- [ ] Alert rules configured
- [ ] Documentation updated

---

## 📈 Success Metrics

- **Cost Efficiency**: Average cost per request < $0.005
- **Latency**: P95 latency < 3 seconds
- **Availability**: 99.9% uptime
- **User Satisfaction**: Power level usage > 80%
- **Revenue**: $2,000/mo within 3 months

---

**Status**: Design complete, ready for implementation
**Estimated Timeline**: 4 weeks
**Next Step**: Deploy LiteLLM proxy and create database tables

