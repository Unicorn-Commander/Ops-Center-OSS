# Unicorn Commander API Integration Guide

**Version**: 2.0
**Last Updated**: November 3, 2025
**Base URL**: `https://api.your-domain.com`

---

## Overview

The Unicorn Commander API provides OpenAI-compatible LLM inference with access to 100+ models through a unified endpoint. Our API uses the same format as OpenAI's API, making integration seamless for existing applications.

**Key Features**:
- 🔑 OpenAI-compatible API format
- 🤖 100+ models (OpenAI, Anthropic, Google, etc.)
- 💰 Usage-based billing with credits
- 🔐 Secure API key authentication
- 📊 Real-time usage tracking
- 🚀 High availability with load balancing

---

## Quick Start

### 1. Get Your API Key

**Login**: https://your-domain.com/auth/login

**Navigate to API Keys**:
- Dashboard → Account → API Keys
- Or directly: https://your-domain.com/admin/account/api-keys

**Generate Key**:
1. Click "Generate New Key"
2. Name your key (e.g., "Production App")
3. Optionally set expiration date
4. **Copy immediately** - it's only shown once!

**Key Format**: `uc_sk_1234567890abcdefghijklmnopqrstuvwxyz`

---

### 2. Make Your First Request

```bash
curl -X POST https://api.your-domain.com/v1/llm/chat/completions \
  -H "Authorization: Bearer uc_sk_YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

---

## API Endpoints

### Base URL

```
https://api.your-domain.com
```

All endpoints use HTTPS. HTTP requests are automatically redirected.

### Available Endpoints

#### Chat Completions (OpenAI-compatible)

```
POST /v1/llm/chat/completions
```

**Headers**:
```
Authorization: Bearer uc_sk_YOUR_API_KEY
Content-Type: application/json
```

**Request Body**:
```json
{
  "model": "openai/gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "stream": false
}
```

**Response**:
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1699564800,
  "model": "openai/gpt-4",
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
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

#### List Available Models

```
GET /v1/llm/models
```

**Response**:
```json
{
  "data": [
    {
      "id": "openai/gpt-4",
      "object": "model",
      "created": 1699564800,
      "owned_by": "openai"
    },
    {
      "id": "anthropic/claude-3-opus",
      "object": "model",
      "created": 1699564800,
      "owned_by": "anthropic"
    }
  ]
}
```

---

## Authentication

All API requests require a valid API key in the `Authorization` header:

```
Authorization: Bearer uc_sk_YOUR_API_KEY_HERE
```

**Security Best Practices**:
- Store API keys in environment variables
- Never commit keys to version control
- Rotate keys periodically
- Use separate keys for dev/staging/production

---

## Supported Models

We support **100+ models** through our LiteLLM proxy:

### OpenAI Models
```
openai/gpt-4
openai/gpt-4-turbo
openai/gpt-4-turbo-preview
openai/gpt-3.5-turbo
openai/gpt-3.5-turbo-16k
```

### Anthropic Models
```
anthropic/claude-3-opus
anthropic/claude-3-sonnet
anthropic/claude-3-haiku
anthropic/claude-2.1
```

### Google Models
```
google/gemini-pro
google/gemini-pro-vision
google/gemini-1.5-pro
```

### OpenRouter Models (with BYOK)
```
openrouter/anthropic/claude-3.5-sonnet
openrouter/google/gemini-pro-1.5
openrouter/meta-llama/llama-3.1-405b
```

**List all models**:
```bash
curl https://api.your-domain.com/v1/llm/models \
  -H "Authorization: Bearer uc_sk_YOUR_API_KEY"
```

---

## Code Examples

### Python (OpenAI SDK)

```python
from openai import OpenAI

# Configure client
client = OpenAI(
    api_key="uc_sk_YOUR_API_KEY_HERE",
    base_url="https://api.your-domain.com/v1/llm"
)

# Chat completion
response = client.chat.completions.create(
    model="openai/gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    temperature=0.7,
    max_tokens=500
)

print(response.choices[0].message.content)
```

### JavaScript/TypeScript

```javascript
import OpenAI from 'openai';

const client = new OpenAI({
  apiKey: 'uc_sk_YOUR_API_KEY_HERE',
  baseURL: 'https://api.your-domain.com/v1/llm'
});

async function chat() {
  const response = await client.chat.completions.create({
    model: 'openai/gpt-4',
    messages: [
      { role: 'system', content: 'You are a helpful assistant.' },
      { role: 'user', content: 'Explain quantum computing in simple terms.' }
    ],
    temperature: 0.7,
    max_tokens: 500
  });

  console.log(response.choices[0].message.content);
}

chat();
```

### cURL

```bash
curl -X POST https://api.your-domain.com/v1/llm/chat/completions \
  -H "Authorization: Bearer uc_sk_YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Explain quantum computing in simple terms."}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### PHP

```php
<?php
require 'vendor/autoload.php';

use OpenAI\Client;

$client = Client::factory()
    ->withApiKey('uc_sk_YOUR_API_KEY_HERE')
    ->withBaseUrl('https://api.your-domain.com/v1/llm')
    ->make();

$response = $client->chat()->create([
    'model' => 'openai/gpt-4',
    'messages' => [
        ['role' => 'system', 'content' => 'You are a helpful assistant.'],
        ['role' => 'user', 'content' => 'Explain quantum computing in simple terms.'],
    ],
    'temperature' => 0.7,
    'max_tokens' => 500,
]);

echo $response['choices'][0]['message']['content'];
?>
```

---

## Streaming Responses

Enable streaming to receive responses as they're generated:

```python
from openai import OpenAI

client = OpenAI(
    api_key="uc_sk_YOUR_API_KEY_HERE",
    base_url="https://api.your-domain.com/v1/llm"
)

stream = client.chat.completions.create(
    model="openai/gpt-4",
    messages=[{"role": "user", "content": "Tell me a story."}],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

---

## Pricing & Limits

### Subscription Tiers

| Tier | Price | API Calls/Month | Credits | Models |
|------|-------|-----------------|---------|--------|
| **Trial** | $1/week | 700 total | 100 | All |
| **Starter** | $19/mo | 1,000 | 1,000 | All |
| **Professional** | $49/mo | 10,000 | 10,000 | All |
| **Enterprise** | $99/mo | Unlimited | Unlimited | All |

### Usage-Based Billing

Credits are deducted based on model costs:

| Model | Input Cost | Output Cost |
|-------|------------|-------------|
| GPT-4 | ~30 credits/1K tokens | ~60 credits/1K tokens |
| GPT-3.5-turbo | ~1 credit/1K tokens | ~2 credits/1K tokens |
| Claude-3-Opus | ~15 credits/1K tokens | ~75 credits/1K tokens |
| Claude-3-Sonnet | ~3 credits/1K tokens | ~15 credits/1K tokens |

**BYOK (Bring Your Own Key)**:
- Add your own OpenRouter/OpenAI keys
- Pay providers directly (no markup)
- Still count toward API call limits

### Rate Limits

**Default Limits** (adjustable based on tier):

| Tier | Requests/Minute | Requests/Month |
|------|-----------------|----------------|
| Starter | 10 | 1,000 |
| Professional | 60 | 10,000 |
| Enterprise | 300 | Unlimited |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699564800
```

---

## Error Handling

### HTTP Status Codes

| Code | Status | Description |
|------|--------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Invalid or missing API key |
| 402 | Payment Required | Insufficient credits |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Temporary outage |

### Error Response Format

```json
{
  "error": {
    "message": "Insufficient credits. Please add credits to your account.",
    "type": "insufficient_credits",
    "code": 402
  }
}
```

### Handling Errors

```python
from openai import OpenAI, APIError, RateLimitError, AuthenticationError

client = OpenAI(
    api_key="uc_sk_YOUR_API_KEY_HERE",
    base_url="https://api.your-domain.com/v1/llm"
)

try:
    response = client.chat.completions.create(
        model="openai/gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded - please wait")
except APIError as e:
    print(f"API error: {e}")
```

---

## Monitoring & Analytics

### View Usage

**Credit Dashboard**: https://your-domain.com/admin/credits
- Real-time credit balance
- Transaction history
- Usage per model

**API Keys**: https://your-domain.com/admin/account/api-keys
- View all API keys
- Last used timestamp
- Expiration status

### Usage Tracking

Monitor your API usage programmatically:

```python
# Response includes usage information
response = client.chat.completions.create(...)

print(f"Prompt tokens: {response.usage.prompt_tokens}")
print(f"Completion tokens: {response.usage.completion_tokens}")
print(f"Total tokens: {response.usage.total_tokens}")
```

---

## BYOK (Bring Your Own Key)

Save costs by using your own API keys from providers:

### Setup BYOK

1. Go to: https://your-domain.com/admin/account/api-keys
2. Click "Add API Key" in the BYOK section
3. Select provider (OpenRouter, OpenAI, Anthropic, etc.)
4. Enter your API key
5. Test connection
6. Save

### Supported BYOK Providers

- **OpenRouter** - Access to 100+ models
- **OpenAI** - GPT-4, GPT-3.5, etc.
- **Anthropic** - Claude models
- **Google AI** - Gemini models
- **Cohere** - Command models
- **Groq** - Ultra-fast inference

### BYOK Benefits

- ✅ Pay providers directly (no markup)
- ✅ Use your existing subscriptions
- ✅ Still get centralized management
- ✅ Automatic cost tracking
- ⚠️ Still count toward API call limits

---

## Best Practices

### Security

1. **Secure Storage**:
   ```bash
   # Use environment variables
   export UNICORN_API_KEY="uc_sk_YOUR_KEY"
   ```

2. **Key Rotation**:
   - Rotate keys every 90 days
   - Immediately revoke compromised keys
   - Use separate keys per environment

3. **Access Control**:
   - Limit key permissions if possible
   - Monitor key usage for anomalies

### Performance

1. **Model Selection**:
   - Use GPT-3.5 for simpler tasks (cheaper, faster)
   - Reserve GPT-4 for complex reasoning

2. **Caching**:
   - Cache common responses
   - Use deterministic temperatures for cacheable requests

3. **Batch Processing**:
   - Batch multiple requests when possible
   - Use async processing for high volume

### Error Handling

1. **Retry Logic**:
   ```python
   import time
   from openai import RateLimitError

   max_retries = 3
   for i in range(max_retries):
       try:
           response = client.chat.completions.create(...)
           break
       except RateLimitError:
           if i < max_retries - 1:
               time.sleep(2 ** i)  # Exponential backoff
           else:
               raise
   ```

2. **Timeout Handling**:
   ```python
   client = OpenAI(
       api_key="uc_sk_YOUR_KEY",
       base_url="https://api.your-domain.com/v1/llm",
       timeout=30.0  # 30 second timeout
   )
   ```

---

## Migration from OpenAI

Migrating from OpenAI is simple - just change two parameters:

### Before (OpenAI)
```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")
```

### After (Unicorn Commander)
```python
from openai import OpenAI

client = OpenAI(
    api_key="uc_sk_...",
    base_url="https://api.your-domain.com/v1/llm"
)
```

**That's it!** All your existing code works without changes.

---

## Support & Resources

### Documentation

- **API Guide**: https://your-domain.com/docs/api
- **Dashboard**: https://your-domain.com/admin
- **Status Page**: https://status.your-domain.com

### Support

- **Email**: admin@example.com
- **Discord**: (Coming soon)
- **GitHub**: https://github.com/Unicorn-Commander

### Status & Uptime

- **API Status**: Monitor at https://status.your-domain.com
- **SLA**: 99.9% uptime guarantee (Enterprise tier)

---

## FAQ

**Q: Can I use this with the OpenAI SDK?**
A: Yes! Just change the `base_url` parameter.

**Q: What happens if I run out of credits?**
A: API requests will return a 402 error. You can add more credits or upgrade your tier.

**Q: Can I use my own API keys?**
A: Yes! Use BYOK to add your own keys from OpenRouter, OpenAI, etc.

**Q: Are there any models I can't access?**
A: All tiers have access to all models. BYOK users need their own keys for provider-specific models.

**Q: How do I monitor my usage?**
A: View real-time usage at https://your-domain.com/admin/credits

**Q: What's the difference between credits and API calls?**
A: API calls count requests. Credits measure actual cost (based on tokens used).

---

**Generated**: November 3, 2025
**Version**: 2.0
**Base URL**: https://api.your-domain.com

For the latest documentation, visit: https://your-domain.com/docs
