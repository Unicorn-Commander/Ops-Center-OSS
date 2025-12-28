# LiteLLM Credit System API Documentation

**Version**: 1.0.0
**Date**: October 20, 2025
**Base URL**: `/api/v1/llm`

## Overview

The LiteLLM Credit System provides a unified API for LLM inference with built-in credit management, intelligent provider routing, and BYOK (Bring Your Own Key) support.

**Key Features**:
- OpenAI-compatible chat completions endpoint
- Credit-based billing with tier-based pricing
- Intelligent provider selection (WilmerAI routing)
- Three power levels (eco, balanced, precision)
- BYOK support for major providers
- Stripe integration for credit purchases
- Comprehensive usage analytics

---

## Authentication

All endpoints require authentication via Bearer token:

```bash
Authorization: Bearer <user-api-key>
```

User ID is extracted from the token and used for credit tracking.

---

## Power Levels

Users can choose from three power levels to optimize cost/performance:

### Eco Mode
- **Cost Multiplier**: 0.1x
- **Max Tokens**: 2,000
- **Temperature**: 0.7
- **Providers**: Local, Groq, HuggingFace (free tier)
- **Use Case**: Budget-conscious, simple queries

### Balanced Mode (Default)
- **Cost Multiplier**: 0.25x
- **Max Tokens**: 4,000
- **Temperature**: 0.8
- **Providers**: Together, Fireworks, OpenRouter
- **Use Case**: General purpose, good quality

### Precision Mode
- **Cost Multiplier**: 1.0x
- **Max Tokens**: 16,000
- **Temperature**: 0.3
- **Providers**: Anthropic, OpenAI, OpenRouter Premium
- **Use Case**: High-quality outputs, complex tasks

---

## Endpoints

### Chat Completions

**POST** `/api/v1/llm/chat/completions`

OpenAI-compatible chat completion with automatic provider routing and credit deduction.

#### Request Headers

```
Authorization: Bearer <user-api-key>
X-Power-Level: eco | balanced | precision (optional)
Content-Type: application/json
```

#### Request Body

```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "What is the capital of France?"
    }
  ],
  "model": "gpt-4o",  // Optional: override model selection
  "max_tokens": 500,  // Optional: override power level default
  "temperature": 0.7,  // Optional: override power level default
  "stream": false,  // Optional: enable streaming
  "task_type": "chat",  // Optional: code, chat, rag, creative, analysis
  "privacy_required": false,  // Optional: force local models
  "power_level": "balanced"  // Optional: eco, balanced, precision
}
```

#### Response

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  },
  "_metadata": {
    "provider_used": "openai",
    "cost_incurred": 0.000525,
    "credits_remaining": 9.999475,
    "transaction_id": "uuid",
    "power_level": "balanced",
    "user_tier": "professional"
  }
}
```

#### Error Responses

**402 Payment Required** - Insufficient credits
```json
{
  "detail": "Insufficient credits. Balance: 0.001, Estimated cost: 0.005"
}
```

**429 Too Many Requests** - Monthly cap exceeded
```json
{
  "detail": "Monthly spending cap exceeded"
}
```

**500 Internal Server Error** - LLM provider error
```json
{
  "detail": "LLM provider error: Connection timeout"
}
```

---

### Get Credit Balance

**GET** `/api/v1/llm/credits`

Get current credit balance and tier information.

#### Response

```json
{
  "user_id": "user@example.com",
  "credits_remaining": 9.999475,
  "tier": "professional",
  "monthly_cap": 100.0
}
```

---

### Purchase Credits

**POST** `/api/v1/llm/credits/purchase`

Purchase credits via Stripe.

#### Request Body

```json
{
  "amount": 50.0,  // $10, $50, or $100
  "stripe_token": "tok_visa"
}
```

**Credit Packages**:
- **$10** = 10,000 credits
- **$50** = 55,000 credits (10% bonus)
- **$100** = 120,000 credits (20% bonus)

#### Response

```json
{
  "success": true,
  "credits_added": 55000,
  "new_balance": 65000.0,
  "transaction_id": "ch_1234567890"
}
```

---

### Get Credit History

**GET** `/api/v1/llm/credits/history`

Get transaction history.

#### Query Parameters

- `limit` (int, optional): Max records to return (default: 100, max: 1000)
- `offset` (int, optional): Pagination offset (default: 0)

#### Response

```json
{
  "transactions": [
    {
      "id": "uuid",
      "amount": -0.000525,
      "type": "usage",
      "provider": "openai",
      "model": "gpt-4o",
      "tokens_used": 35,
      "cost": 0.000525,
      "metadata": {
        "power_level": "balanced",
        "task_type": "chat"
      },
      "created_at": "2025-10-20T05:30:00Z"
    },
    {
      "id": "uuid",
      "amount": 55000,
      "type": "purchase",
      "provider": null,
      "model": null,
      "tokens_used": 0,
      "cost": 0,
      "metadata": {
        "reason": "purchase"
      },
      "created_at": "2025-10-19T10:00:00Z"
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

---

### List Available Models

**GET** `/api/v1/llm/models`

Get list of available models based on user tier.

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama3-8b-local",
      "object": "model",
      "owned_by": "local",
      "tier": "free"
    },
    {
      "id": "qwen-32b-local",
      "object": "model",
      "owned_by": "local",
      "tier": "free"
    },
    {
      "id": "claude-3.5-sonnet-openrouter",
      "object": "model",
      "owned_by": "openrouter",
      "tier": "professional"
    },
    {
      "id": "gpt-4o",
      "object": "model",
      "owned_by": "openai",
      "tier": "enterprise"
    }
  ]
}
```

**Model Availability by Tier**:

| Tier | Models |
|------|--------|
| **Free** | llama3-8b-local, qwen-32b-local, llama3-70b-groq, mixtral-8x7b-hf |
| **Starter** | + mixtral-8x22b-together, llama3-70b-deepinfra, qwen-72b-fireworks |
| **Professional** | + claude-3.5-sonnet-openrouter, gpt-4o-openrouter |
| **Enterprise** | + claude-3.5-sonnet, gpt-4o (direct access) |

---

### Get Usage Statistics

**GET** `/api/v1/llm/usage`

Get usage statistics for the user.

#### Query Parameters

- `days` (int, optional): Number of days to include (default: 30)

#### Response

```json
{
  "total_requests": 125,
  "total_tokens": 45230,
  "total_cost": 2.35,
  "avg_cost_per_request": 0.0188,
  "providers": [
    {
      "provider": "openai",
      "requests": 50,
      "tokens": 20000,
      "cost": 1.50
    },
    {
      "provider": "anthropic",
      "requests": 30,
      "tokens": 15000,
      "cost": 0.70
    },
    {
      "provider": "local",
      "requests": 45,
      "tokens": 10230,
      "cost": 0.00
    }
  ]
}
```

---

### Health Check

**GET** `/api/v1/llm/health`

Check system health.

#### Response

```json
{
  "status": "healthy",
  "litellm_proxy": "up",
  "timestamp": "2025-10-20T05:30:00Z"
}
```

---

## BYOK (Bring Your Own Key) Endpoints

### Add/Update API Key

**POST** `/api/v1/llm/byok/keys`

Add or update your own API key for a provider.

#### Request Body

```json
{
  "provider": "openai",  // openai, anthropic, openrouter, etc.
  "api_key": "sk-..."
}
```

#### Response

```json
{
  "success": true,
  "key_id": "uuid",
  "provider": "openai",
  "message": "API key stored successfully"
}
```

**Supported Providers**:
- `openai` - OpenAI (requires sk-... format)
- `anthropic` - Anthropic (requires sk-ant-... format)
- `openrouter` - OpenRouter (requires sk-or-... format)
- `together` - Together AI
- `fireworks` - Fireworks AI
- `deepinfra` - DeepInfra
- `groq` - Groq (requires gsk_... format)
- `huggingface` - HuggingFace (requires hf_... format)

---

### List BYOK Keys

**GET** `/api/v1/llm/byok/keys`

List all stored provider keys (masked).

#### Response

```json
{
  "providers": [
    {
      "id": "uuid",
      "provider": "openai",
      "enabled": true,
      "metadata": {},
      "created_at": "2025-10-15T12:00:00Z",
      "updated_at": "2025-10-18T14:30:00Z",
      "masked_key": "***...open"
    },
    {
      "id": "uuid",
      "provider": "anthropic",
      "enabled": true,
      "metadata": {},
      "created_at": "2025-10-16T09:00:00Z",
      "updated_at": null,
      "masked_key": "***...anth"
    }
  ]
}
```

---

### Delete API Key

**DELETE** `/api/v1/llm/byok/keys/{provider}`

Delete your API key for a specific provider.

#### Response

```json
{
  "success": true,
  "provider": "openai"
}
```

---

## Pricing & Cost Calculation

### Base Costs (per 1K tokens)

| Provider | Cost |
|----------|------|
| **Free Tier** | |
| Local (Ollama, vLLM) | $0.000 |
| Groq | $0.000 |
| HuggingFace | $0.000 |
| **Paid Tier (Low Cost)** | |
| Together AI | $0.002 |
| Fireworks AI | $0.002 |
| DeepInfra | $0.003 |
| **OpenRouter** | |
| Mixtral | $0.003 |
| Claude 3.5 Sonnet | $0.008 |
| GPT-4o | $0.010 |
| **Premium (Direct)** | |
| Anthropic | $0.015 |
| OpenAI | $0.015 |

### Cost Formula

```
final_cost = (tokens / 1000) × base_cost_per_1k × power_multiplier × (1 + tier_markup)
```

**Power Multipliers**:
- Eco: 0.1x
- Balanced: 0.25x
- Precision: 1.0x

**Tier Markups**:
- Free: 0% (platform absorbs cost)
- Starter: 40%
- Professional: 60%
- Enterprise: 80%

### Example Calculation

**Scenario**: Professional tier user, Balanced mode, GPT-4o, 1000 tokens

```
Base cost: 1000 / 1000 × $0.015 = $0.015
Power multiplier: 0.25x = $0.00375
Tier markup: 1.6x = $0.006
Final cost: $0.006 (0.006 credits)
```

---

## Database Schema

### user_credits Table

```sql
CREATE TABLE user_credits (
  user_id UUID PRIMARY KEY,
  credits_remaining FLOAT DEFAULT 0,
  monthly_cap FLOAT,
  tier TEXT,  -- "free", "starter", "professional", "enterprise"
  last_reset TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### credit_transactions Table

```sql
CREATE TABLE credit_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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

### user_provider_keys Table

```sql
CREATE TABLE user_provider_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES user_credits(user_id),
  provider TEXT,  -- "openai", "anthropic", etc.
  api_key_encrypted TEXT,  -- Fernet encrypted
  enabled BOOLEAN DEFAULT TRUE,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP
);
```

---

## Environment Variables

```bash
# LiteLLM Proxy
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<generated>

# Database
DATABASE_URL=postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db

# Redis
REDIS_HOST=unicorn-redis
REDIS_PORT=6379

# Stripe (for credit purchases)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# BYOK Encryption
BYOK_ENCRYPTION_KEY=<fernet-key>  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| 401 | Unauthorized | Provide valid Bearer token |
| 402 | Payment Required | Insufficient credits - purchase more |
| 400 | Bad Request | Invalid request format or parameters |
| 404 | Not Found | User or resource not found |
| 429 | Too Many Requests | Monthly cap exceeded or rate limit hit |
| 500 | Internal Server Error | System error - contact support |

---

## Usage Examples

### Python (with OpenAI SDK)

```python
import openai

# Configure client
client = openai.OpenAI(
    base_url="https://your-domain.com/api/v1/llm",
    api_key="your-api-key"
)

# Make request with power level
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing"}
    ],
    extra_headers={
        "X-Power-Level": "precision"
    }
)

print(response.choices[0].message.content)
print(f"Cost: ${response._metadata['cost_incurred']}")
print(f"Credits remaining: {response._metadata['credits_remaining']}")
```

### cURL

```bash
# Chat completion
curl -X POST https://your-domain.com/api/v1/llm/chat/completions \
  -H "Authorization: Bearer your-api-key" \
  -H "X-Power-Level: balanced" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# Check balance
curl https://your-domain.com/api/v1/llm/credits \
  -H "Authorization: Bearer your-api-key"

# Purchase credits
curl -X POST https://your-domain.com/api/v1/llm/credits/purchase \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 50.0,
    "stripe_token": "tok_visa"
  }'

# Add BYOK key
curl -X POST https://your-domain.com/api/v1/llm/byok/keys \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-..."
  }'
```

### JavaScript (Fetch API)

```javascript
// Chat completion
const response = await fetch('https://your-domain.com/api/v1/llm/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-api-key',
    'X-Power-Level': 'balanced',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    messages: [
      { role: 'user', content: 'What is AI?' }
    ]
  })
});

const data = await response.json();
console.log('Response:', data.choices[0].message.content);
console.log('Cost:', data._metadata.cost_incurred);
console.log('Remaining:', data._metadata.credits_remaining);
```

---

## Rate Limits

| Tier | Requests/Minute | Requests/Hour | Requests/Day |
|------|----------------|---------------|--------------|
| Free | 5 | 50 | 100 |
| Starter | 20 | 500 | 1,000 |
| Professional | 60 | 3,000 | 10,000 |
| Enterprise | Unlimited | Unlimited | Unlimited |

---

## Support

- **Documentation**: https://docs.your-domain.com
- **Email**: support@magicunicorn.tech
- **Status Page**: https://status.your-domain.com

---

## Changelog

### Version 1.0.0 (October 20, 2025)

- Initial release
- OpenAI-compatible chat completions
- Credit system with tier-based pricing
- Three power levels (eco, balanced, precision)
- BYOK support for 8 providers
- Stripe integration for credit purchases
- Usage analytics and history
- Health monitoring

---

**License**: MIT
**Copyright**: Magic Unicorn Unconventional Technology & Stuff Inc, 2025
