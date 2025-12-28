# LiteLLM Routing and Provider Management API Guide

**Created**: October 23, 2025
**Status**: Production Ready
**Version**: 1.0.0

---

## Overview

The LiteLLM Routing and Provider Management API provides comprehensive multi-provider LLM routing with WilmerAI-style cost/latency optimization and BYOK (Bring Your Own Key) support.

### Key Features

✅ **Multi-Provider Support**: OpenRouter, OpenAI, Anthropic, Together AI, HuggingFace, Google, Cohere
✅ **WilmerAI-Style Routing**: Eco/Balanced/Precision power levels
✅ **BYOK Support**: Users can use their own API keys
✅ **Cost Optimization**: Automatic model selection based on cost/latency/quality
✅ **Provider Health Monitoring**: Real-time connection testing
✅ **Usage Analytics**: Comprehensive cost and usage tracking
✅ **Encrypted API Keys**: Fernet encryption for secure key storage
✅ **Routing Strategies**: Cost, Latency, Balanced, or Custom weighted scoring

---

## Architecture

### Database Schema

The API creates 5 PostgreSQL tables:

1. **llm_providers** - Provider configurations with encrypted API keys
2. **llm_models** - Model catalog with pricing and performance data
3. **llm_routing_rules** - Routing strategy and fallback configuration
4. **user_llm_settings** - User preferences, BYOK, and credit balances
5. **llm_usage_logs** - Usage tracking for analytics and billing

### Encryption

All API keys are encrypted using Fernet (symmetric encryption) before storage:

```python
from cryptography.fernet import Fernet

# Encryption key from environment
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# Encrypt
encrypted = cipher_suite.encrypt(api_key.encode()).decode()

# Decrypt
decrypted = cipher_suite.decrypt(encrypted.encode()).decode()
```

### Power Levels (WilmerAI-Style)

**Eco Mode** - Cost optimized
- Use cheapest models from OpenRouter budget tier
- Example: `deepseek-chat`, `mistral-7b-instruct`
- Target: < $0.50 per 1M tokens

**Balanced Mode** - Balance cost and quality (default)
- Mix of mid-tier and premium models
- Example: `gpt-3.5-turbo`, `claude-3-haiku`
- Target: $1.00-$5.00 per 1M tokens

**Precision Mode** - Quality optimized
- Use best models from OpenAI/Anthropic direct
- Example: `gpt-4-turbo`, `claude-3-opus`
- Target: Quality over cost

---

## API Endpoints

### Provider Management

#### List Providers

```http
GET /api/v1/llm/providers?enabled_only=false
```

**Response**:
```json
[
  {
    "id": "uuid",
    "name": "OpenRouter",
    "type": "openrouter",
    "status": "active",
    "models": 150,
    "avg_cost_per_1m": 0.50,
    "enabled_models": ["gpt-4", "claude-3-opus"],
    "priority": 1,
    "health_status": "healthy",
    "last_health_check": "2025-10-23T12:00:00Z"
  }
]
```

#### Create Provider

```http
POST /api/v1/llm/providers
Content-Type: application/json

{
  "name": "OpenRouter",
  "type": "openrouter",
  "api_key": "sk-or-v1-...",
  "api_base_url": "https://openrouter.ai/api",
  "enabled": true,
  "priority": 1,
  "config": {
    "max_retries": 3,
    "timeout_seconds": 30
  }
}
```

**Response**:
```json
{
  "id": "uuid",
  "name": "OpenRouter",
  "type": "openrouter",
  "enabled": true,
  "priority": 1,
  "message": "Provider created successfully. Testing connection..."
}
```

#### Update Provider

```http
PUT /api/v1/llm/providers/{provider_id}
Content-Type: application/json

{
  "api_key": "sk-or-v1-new-key",
  "enabled": true,
  "priority": 2
}
```

#### Delete Provider

```http
DELETE /api/v1/llm/providers/{provider_id}
```

**Note**: Cascades delete to all associated models.

---

### Model Management

#### List Models

```http
GET /api/v1/llm/models?provider_id={uuid}&enabled_only=true&sort_by=cost
```

**Query Parameters**:
- `provider_id` - Filter by provider UUID
- `enabled_only` - Only return enabled models
- `sort_by` - Sort by `cost`, `latency`, or `name`

**Response**:
```json
[
  {
    "id": "uuid",
    "provider_id": "uuid",
    "provider_name": "OpenRouter",
    "name": "gpt-4-turbo",
    "display_name": "GPT-4 Turbo",
    "cost_per_1m_input": 10.00,
    "cost_per_1m_output": 30.00,
    "context_length": 128000,
    "enabled": true,
    "avg_latency_ms": 2500
  }
]
```

#### Create Model

```http
POST /api/v1/llm/models
Content-Type: application/json

{
  "provider_id": "uuid",
  "name": "gpt-4-turbo",
  "display_name": "GPT-4 Turbo",
  "cost_per_1m_input_tokens": 10.00,
  "cost_per_1m_output_tokens": 30.00,
  "context_length": 128000,
  "enabled": true,
  "metadata": {
    "supports_vision": true,
    "supports_function_calling": true
  }
}
```

---

### Routing Rules

#### Get Routing Configuration

```http
GET /api/v1/llm/routing/rules
```

**Response**:
```json
{
  "id": "uuid",
  "strategy": "balanced",
  "fallback_providers": ["uuid1", "uuid2"],
  "model_aliases": {
    "gpt-4": "openai/gpt-4-turbo"
  },
  "config": {
    "cost_weight": 0.4,
    "latency_weight": 0.4,
    "quality_weight": 0.2,
    "max_retries": 3,
    "retry_delay_ms": 500
  },
  "power_levels": {
    "eco": "Use cheapest models (OpenRouter budget tier)",
    "balanced": "Balance cost and quality (mix of providers)",
    "precision": "Use best models (OpenAI, Anthropic direct)"
  }
}
```

#### Update Routing Rules

```http
PUT /api/v1/llm/routing/rules
Content-Type: application/json

{
  "strategy": "balanced",
  "fallback_providers": ["uuid1", "uuid2"],
  "model_aliases": {
    "gpt-4": "openai/gpt-4-turbo"
  },
  "config": {
    "cost_weight": 0.3,
    "latency_weight": 0.3,
    "quality_weight": 0.4
  }
}
```

**Strategies**:
- `cost` - Always route to cheapest model
- `latency` - Always route to fastest model
- `balanced` - Balance cost, latency, quality with configurable weights
- `custom` - Custom weighted scoring formula

---

### Usage Analytics

#### Get Usage Statistics

```http
GET /api/v1/llm/usage?user_id={user_id}&days=7&provider_id={uuid}
```

**Query Parameters**:
- `user_id` - Filter by user (admin can see all)
- `days` - Number of days to analyze (default 7)
- `provider_id` - Filter by provider

**Response**:
```json
{
  "total_requests": 1523,
  "total_tokens": 2456789,
  "total_cost": 45.67,
  "avg_cost_per_request": 0.03,
  "providers": [
    {
      "provider_id": "uuid",
      "provider_name": "OpenRouter",
      "requests": 850,
      "tokens": 1200000,
      "cost": 15.50,
      "avg_latency_ms": 1200,
      "unique_users": 45
    },
    {
      "provider_id": "uuid",
      "provider_name": "OpenAI Direct",
      "requests": 673,
      "tokens": 1256789,
      "cost": 30.17,
      "avg_latency_ms": 800,
      "unique_users": 12
    }
  ],
  "period_days": 7
}
```

---

### BYOK (Bring Your Own Key)

#### Set User BYOK

```http
POST /api/v1/llm/users/{user_id}/byok
Content-Type: application/json

{
  "provider_type": "openai",
  "api_key": "sk-...",
  "enabled": true,
  "preferences": {
    "preferred_models": ["gpt-4-turbo"],
    "max_tokens_per_request": 4000
  }
}
```

**Response**:
```json
{
  "user_id": "user@example.com",
  "provider_type": "openai",
  "enabled": true,
  "power_level": "balanced",
  "credit_balance": 0.0,
  "message": "BYOK configuration updated successfully"
}
```

#### Get User BYOK Configuration

```http
GET /api/v1/llm/users/{user_id}/byok
```

**Response** (API keys masked):
```json
{
  "user_id": "user@example.com",
  "byok_providers": {
    "openai": {
      "enabled": true,
      "preferences": {
        "preferred_models": ["gpt-4-turbo"]
      },
      "updated_at": "2025-10-23T12:00:00Z",
      "api_key": "sk-...****"
    }
  },
  "power_level": "balanced",
  "credit_balance": 0.0,
  "preferences": {}
}
```

---

### Credit System

#### Get Credit Balance

```http
GET /api/v1/llm/credits?user_id={user_id}
```

**Response**:
```json
{
  "user_id": "user@example.com",
  "credits_remaining": 100.50,
  "power_level": "balanced",
  "monthly_cap": 500.0
}
```

---

### Provider Testing

#### Test Provider Connection

```http
POST /api/v1/llm/test
Content-Type: application/json

{
  "provider_id": "uuid",
  "model": "gpt-3.5-turbo"
}
```

**Success Response**:
```json
{
  "provider_id": "uuid",
  "provider_name": "OpenAI",
  "status": "success",
  "latency_ms": 845,
  "message": "Provider connection successful"
}
```

**Failure Response**:
```json
{
  "provider_id": "uuid",
  "provider_name": "OpenAI",
  "status": "failed",
  "error": "Invalid API key",
  "message": "Provider connection failed"
}
```

---

## Integration with Ops-Center

### Environment Variables

Add to `/services/ops-center/.env.auth`:

```bash
# LiteLLM Routing
LITELLM_PROXY_URL=http://unicorn-litellm:4000
ENCRYPTION_KEY=<generate-with-Fernet.generate_key()>

# Provider API Keys (System Defaults)
OPENROUTER_API_KEY=sk-or-v1-...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Database Migration

The database tables are automatically created on first import via `init_database()` function.

To manually initialize:

```python
from litellm_routing_api import init_database
init_database()
```

### Frontend Integration

Add route to `src/App.jsx`:

```jsx
import LLMProviderManagement from './pages/LLMProviderManagement';

// In routes
<Route path="/admin/llm/providers" element={<LLMProviderManagement />} />
```

Add navigation item to sidebar:

```jsx
{
  label: 'LLM Providers',
  icon: <CloudIcon />,
  path: '/admin/llm/providers',
  requiredRole: 'admin'
}
```

---

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def use_llm_routing():
    """Example: Create provider and use routing"""

    # Create provider
    async with httpx.AsyncClient() as client:
        response = await client.post(
            'http://localhost:8084/api/v1/llm/providers',
            json={
                'name': 'OpenRouter',
                'type': 'openrouter',
                'api_key': 'sk-or-v1-...',
                'enabled': True,
                'priority': 1
            }
        )
        provider = response.json()
        print(f"Created provider: {provider['id']}")

        # Add model
        response = await client.post(
            'http://localhost:8084/api/v1/llm/models',
            json={
                'provider_id': provider['id'],
                'name': 'gpt-3.5-turbo',
                'display_name': 'GPT-3.5 Turbo',
                'cost_per_1m_input_tokens': 0.50,
                'cost_per_1m_output_tokens': 1.50,
                'context_length': 16385,
                'enabled': True
            }
        )
        print(f"Added model: {response.json()['name']}")

        # Test provider
        response = await client.post(
            'http://localhost:8084/api/v1/llm/test',
            json={'provider_id': provider['id']}
        )
        test_result = response.json()
        print(f"Provider test: {test_result['status']} ({test_result['latency_ms']}ms)")

asyncio.run(use_llm_routing())
```

### cURL Examples

```bash
# List providers
curl http://localhost:8084/api/v1/llm/providers

# Create provider
curl -X POST http://localhost:8084/api/v1/llm/providers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI",
    "type": "openai",
    "api_key": "sk-...",
    "enabled": true,
    "priority": 1
  }'

# List models by cost
curl "http://localhost:8084/api/v1/llm/models?sort_by=cost&enabled_only=true"

# Get usage analytics
curl "http://localhost:8084/api/v1/llm/usage?days=30"

# Update routing rules
curl -X PUT http://localhost:8084/api/v1/llm/routing/rules \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "balanced",
    "config": {
      "cost_weight": 0.4,
      "latency_weight": 0.4,
      "quality_weight": 0.2
    }
  }'
```

---

## Provider Configuration

### OpenRouter

```json
{
  "name": "OpenRouter",
  "type": "openrouter",
  "api_key": "sk-or-v1-...",
  "api_base_url": "https://openrouter.ai/api",
  "priority": 1
}
```

**Models**: 150+ models including GPT-4, Claude, Llama, Mistral

### OpenAI

```json
{
  "name": "OpenAI Direct",
  "type": "openai",
  "api_key": "sk-...",
  "api_base_url": "https://api.openai.com",
  "priority": 2
}
```

**Models**: GPT-4 Turbo, GPT-4, GPT-3.5 Turbo

### Anthropic

```json
{
  "name": "Anthropic",
  "type": "anthropic",
  "api_key": "sk-ant-...",
  "api_base_url": "https://api.anthropic.com",
  "priority": 3
}
```

**Models**: Claude 3 Opus, Sonnet, Haiku

### Together AI

```json
{
  "name": "Together AI",
  "type": "together",
  "api_key": "...",
  "api_base_url": "https://api.together.xyz",
  "priority": 4
}
```

**Models**: Llama 3, Mixtral, CodeLlama

---

## Routing Logic

### Power Level Routing

**Eco Mode**:
1. Filter models by cost < $1.00 per 1M tokens
2. Sort by cost ascending
3. Select cheapest available model

**Balanced Mode**:
1. Calculate weighted score: `(cost_weight * cost) + (latency_weight * latency) + (quality_weight * quality)`
2. Sort by score
3. Select best scoring model

**Precision Mode**:
1. Filter models by quality tier (GPT-4, Claude Opus, etc.)
2. Sort by quality/capabilities descending
3. Select highest quality model

### Fallback Strategy

1. Attempt primary provider based on routing rules
2. If fails (rate limit, error, timeout):
   - Retry with exponential backoff (500ms, 1000ms, 2000ms)
   - After max retries, failover to next priority provider
3. Continue through fallback chain until success or exhausted

---

## Security Considerations

### API Key Encryption

✅ All provider API keys encrypted with Fernet before storage
✅ Encryption key stored in environment variable
✅ Keys never returned in API responses (masked as `sk-...****`)
✅ HTTPS required for production use

### Access Control

- **Admin Only**: Provider/model CRUD, routing rules, all usage analytics
- **User**: Own BYOK configuration, own usage statistics
- **Public**: None (all endpoints require authentication)

### Rate Limiting

Apply rate limits to prevent abuse:

```python
from rate_limiter import rate_limit

@router.post("/providers")
@rate_limit(max_requests=10, window_seconds=60)
async def create_provider(...):
    ...
```

---

## Monitoring & Observability

### Health Checks

Automatic health checks run:
- On provider creation
- Manual via test endpoint
- Scheduled background checks (every 5 minutes)

Health status stored in `health_status` column:
- `healthy` - Last test successful
- `unhealthy` - Last test failed
- `unknown` - Never tested or pending

### Metrics to Track

- **Request Volume**: Total requests per provider/model
- **Cost**: Total cost, cost per request, cost per user
- **Latency**: Average latency per provider/model
- **Error Rate**: Failed requests, timeout rate
- **BYOK Usage**: Percentage of requests using BYOK vs system keys

### Alerts

Configure alerts for:
- Provider health failures
- Unexpected cost spikes (>2x average)
- High error rates (>5%)
- API key expiration warnings

---

## Troubleshooting

### Provider Connection Fails

```python
# Test provider manually
response = await client.post('/api/v1/llm/test', json={
    'provider_id': 'uuid'
})

# Check health status
providers = await client.get('/api/v1/llm/providers')
# Look for health_status: 'unhealthy'
```

**Common Issues**:
- Invalid API key → Update with correct key
- Rate limited → Wait or increase limits
- Network error → Check firewall/proxy settings
- Invalid base URL → Verify API endpoint

### High Costs

```python
# Analyze usage by provider
usage = await client.get('/api/v1/llm/usage?days=7')

# Identify expensive models
models = await client.get('/api/v1/llm/models?sort_by=cost')

# Switch to Eco mode for cost-sensitive users
await client.put(f'/api/v1/llm/users/{user_id}/settings', json={
    'power_level': 'eco'
})
```

### Slow Performance

```python
# Find slowest providers
usage = await client.get('/api/v1/llm/usage?days=7')
# Check avg_latency_ms in provider stats

# Route to faster providers
await client.put('/api/v1/llm/routing/rules', json={
    'strategy': 'latency'  # Optimize for speed
})
```

---

## Roadmap

### Phase 2 Features (Planned)

- [ ] **Model Auto-Discovery**: Automatically fetch model lists from providers
- [ ] **Cost Prediction**: Estimate request cost before execution
- [ ] **A/B Testing**: Split traffic between providers for comparison
- [ ] **Custom Routing Rules**: Per-user or per-organization routing
- [ ] **Caching**: Response caching for identical requests
- [ ] **Streaming Support**: Stream responses with cost tracking
- [ ] **Webhooks**: Notify on provider failures or cost thresholds
- [ ] **Advanced Analytics**: Grafana dashboards for metrics

---

## Support & Documentation

- **API Reference**: See OpenAPI schema at `/docs`
- **Source Code**: `/backend/litellm_routing_api.py`
- **Frontend**: `/src/pages/LLMProviderManagement.jsx`
- **Database Schema**: Auto-created on initialization

**Questions?** Contact the development team or check the main UC-Cloud documentation.

---

**End of LiteLLM Routing API Guide**
