# Ops-Center LLM API Integration Guide for External Services

**Version**: 2.0
**Last Updated**: November 14, 2025
**Deployment**: centerdeep.online
**Audience**: LoopNet Leads, Center-Deep Pro, and other UC-Cloud services

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Authentication Methods](#authentication-methods)
4. [Request & Response Format](#request--response-format)
5. [Available Models](#available-models)
6. [Credit System & Billing](#credit-system--billing)
7. [Rate Limits & Quotas](#rate-limits--quotas)
8. [Code Examples](#code-examples)
9. [Error Handling](#error-handling)
10. [Internal vs External Access](#internal-vs-external-access)
11. [BYOK vs Platform Keys](#byok-vs-platform-keys)

---

## Quick Start

### For Services on Same Docker Network (Recommended)

```python
import requests

# Internal endpoint (fast, no SSL overhead)
API_BASE = "http://ops-center-centerdeep:8084/api/v1/llm"

# Use service key authentication (pre-configured trusted keys)
headers = {
    "Authorization": "Bearer sk-loopnet-service-key-2025",
    "Content-Type": "application/json"
}

response = requests.post(
    f"{API_BASE}/chat/completions",
    headers=headers,
    json={
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Extract company info from this text..."}
        ]
    }
)

result = response.json()
print(result['choices'][0]['message']['content'])
```

### For External Access (HTTPS)

```bash
# External endpoint (requires SSL, slower but accessible from anywhere)
curl -X POST https://api.centerdeep.online/api/v1/llm/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

---

## API Endpoints

### Base URLs

| Access Type | Base URL | Use Case |
|-------------|----------|----------|
| **Internal Network** | `http://ops-center-centerdeep:8084` | Services in `unicorn-network` (LoopNet, Center-Deep) |
| **External HTTPS** | `https://ops.centerdeep.online` | Browser-based apps, external services |
| **Public API** | `https://api.centerdeep.online` | Third-party integrations (if exposed) |

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/llm/chat/completions` | POST | OpenAI-compatible chat completions (main endpoint) |
| `/api/v1/llm/image/generations` | POST | Image generation (DALL-E, Stable Diffusion) |
| `/api/v1/llm/models` | GET | List available models |
| `/api/v1/llm/models/categorized` | GET | Models categorized by BYOK vs Platform |
| `/api/v1/llm/credits` | GET | Check credit balance |
| `/api/v1/llm/usage` | GET | Usage statistics |
| `/api/v1/llm/byok/keys` | GET | List user's BYOK keys |
| `/api/v1/llm/byok/keys` | POST | Add BYOK key |

---

## Authentication Methods

Ops-Center supports **4 authentication methods**, in order of preference for internal services:

### 1. Service Keys (Recommended for Internal Services)

**Format**: `sk-<service-name>-service-key-<year>`

Pre-configured trusted keys for internal UC-Cloud services. No database lookup required.

**Pre-Configured Service Keys**:
```python
SERVICE_KEYS = {
    'sk-bolt-diy-service-key-2025': 'bolt-diy-service',
    'sk-presenton-service-key-2025': 'presenton-service',
    'sk-brigade-service-key-2025': 'brigade-service',
    'sk-loopnet-service-key-2025': 'loopnet-service',  # ADD THIS
    'sk-centerdeep-service-key-2025': 'centerdeep-service'  # ADD THIS
}
```

**Example**:
```bash
Authorization: Bearer sk-loopnet-service-key-2025
```

**Advantages**:
- ✅ No database lookup (fastest)
- ✅ No expiration
- ✅ No rate limits (uses organizational billing)
- ✅ No user management needed

**Setup Required**: Add your service key to `backend/litellm_api.py` line 566-570.

---

### 2. Session Cookies (For Browser-Based Requests)

**Format**: `session_token` cookie

Used automatically when users are logged in via Keycloak SSO.

**Example**:
```javascript
// Fetch from browser (session cookie automatically included)
fetch('http://ops-center-centerdeep:8084/api/v1/llm/chat/completions', {
  method: 'POST',
  credentials: 'include',  // Include cookies
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    model: 'gpt-4o-mini',
    messages: [{ role: 'user', content: 'Hello' }]
  })
});
```

**Advantages**:
- ✅ Automatic user context
- ✅ No manual token management
- ✅ Works with Keycloak SSO

**Use Cases**: Frontend web apps, authenticated dashboards

---

### 3. User API Keys

**Format**: `uc_<64-char-hex>`

Generated via Ops-Center admin panel (`/admin/account/api-keys`).

**Example**:
```bash
Authorization: Bearer uc_a1b2c3d4e5f6789...
```

**Advantages**:
- ✅ User-specific quotas
- ✅ Revocable
- ✅ Trackable usage

**Use Cases**: External integrations, third-party apps

---

### 4. JWT Tokens

**Format**: Standard JWT

Issued by Keycloak after OAuth2 authentication.

**Example**:
```bash
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Advantages**:
- ✅ Standard OAuth2 flow
- ✅ Short-lived (secure)
- ✅ Includes user roles

**Use Cases**: OAuth2-enabled apps

---

## Request & Response Format

### Chat Completions Request

**Endpoint**: `POST /api/v1/llm/chat/completions`

**OpenAI-Compatible Schema**:
```json
{
  "model": "gpt-4o-mini",
  "messages": [
    {
      "role": "system",
      "content": "You are a helpful assistant specializing in company data extraction."
    },
    {
      "role": "user",
      "content": "Extract the company name, industry, and location from this text: ..."
    }
  ],
  "temperature": 0.7,
  "max_tokens": 500,
  "stream": false,
  "power_level": "balanced"
}
```

**Parameters**:

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `model` | string | No | auto | Model to use (see Available Models) |
| `messages` | array | Yes | - | Chat messages (role + content) |
| `temperature` | float | No | 0.7 | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | No | auto | Max tokens to generate |
| `stream` | bool | No | false | Enable streaming responses |
| `power_level` | string | No | balanced | Cost/quality tier: `eco`, `balanced`, `precision` |
| `task_type` | string | No | chat | Task type: `code`, `chat`, `rag`, `creative` |
| `privacy_required` | bool | No | false | Force local models only |

**Custom Headers**:
```
X-Power-Level: eco | balanced | precision
```

---

### Chat Completions Response

**Success Response** (200 OK):
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699564800,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Company Name: Acme Corp\nIndustry: Technology\nLocation: San Francisco, CA"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 23,
    "total_tokens": 68
  }
}
```

**Custom Response Headers**:
```
X-Provider-Used: openai          # Which provider handled the request
X-Cost-Incurred: 0.003           # Credits deducted
X-Credits-Remaining: 9997.000    # Updated balance
X-RateLimit-Limit: 10000         # Monthly quota
X-RateLimit-Remaining: 9850      # Remaining quota
X-RateLimit-Reset: 1733097600    # Unix timestamp of reset
```

---

## Available Models

### Model Selection Strategy

Ops-Center automatically routes requests based on:

1. **User Tier**: Subscription level determines model access
2. **BYOK Status**: If user has OpenRouter key, ALL models are free
3. **Power Level**: Cost/quality preference (`eco`, `balanced`, `precision`)
4. **Task Type**: Optimized model for specific tasks

### Models by Tier

#### Free Tier (Local/Open-Source)
```
- llama3-8b-local
- qwen-32b-local
- llama3-70b-groq
- mixtral-8x7b-hf
```

#### Starter Tier ($19/month, 1K calls)
```
- mixtral-8x22b-together
- llama3-70b-deepinfra
- qwen-72b-fireworks
```

#### Professional Tier ($49/month, 10K calls)
```
- claude-3.5-sonnet-openrouter
- gpt-4o-openrouter
- gpt-4o-mini
```

#### Enterprise Tier ($99/month, unlimited)
```
- claude-3.5-sonnet (direct Anthropic)
- gpt-4o (direct OpenAI)
- o1-preview
- o3-mini
```

### Power Levels

| Power Level | Cost Multiplier | Quality | Use Case |
|-------------|-----------------|---------|----------|
| `eco` | 0.5x | Good | Bulk processing, simple tasks |
| `balanced` | 1.0x | Better | General use (default) |
| `precision` | 2.0x | Best | Critical tasks, complex reasoning |

**Example**:
```json
{
  "model": "gpt-4o-mini",
  "power_level": "eco",  // 50% cheaper
  "messages": [...]
}
```

---

## Credit System & Billing

### How Credits Work

**1 credit = $0.001 USD** (0.1 cents)

Credits are deducted based on:
- **Base Model Cost**: OpenAI/Anthropic pricing
- **Power Level Multiplier**: 0.5x (eco), 1.0x (balanced), 2.0x (precision)
- **Tier Markup**: Professional +10%, Starter +20%

**Example Calculation**:
```
Base Cost (GPT-4o-mini): 100 tokens = 0.0005 credits
Power Level (balanced): x1.0 = 0.0005 credits
Tier Markup (professional): x1.1 = 0.00055 credits
Total Charged: 0.00055 credits ($0.00000055)
```

### Organizational Billing

For services like LoopNet and Center-Deep, credits are tracked at the **organization level**:

1. **Organization Credit Pool**: Shared by all users in organization
2. **User Allocations**: Admin allocates credits to users
3. **Automatic Deduction**: Each API call deducts from user's allocation
4. **Quota Reset**: Monthly reset based on subscription tier

**Database Schema**:
```sql
-- Organization credit pool
CREATE TABLE organization_credits (
  org_id UUID PRIMARY KEY,
  total_credits BIGINT NOT NULL,
  used_credits BIGINT DEFAULT 0,
  tier TEXT NOT NULL
);

-- User allocations within organization
CREATE TABLE user_credit_allocations (
  org_id UUID REFERENCES organizations(id),
  user_id TEXT NOT NULL,
  allocated_credits BIGINT NOT NULL,
  used_credits BIGINT DEFAULT 0,
  PRIMARY KEY (org_id, user_id)
);
```

### Credit Tracking API

**Check Credits**:
```bash
GET /api/v1/llm/credits
Authorization: Bearer sk-loopnet-service-key-2025

Response:
{
  "user_id": "loopnet-service",
  "credits_remaining": 10000000.0,
  "tier": "enterprise",
  "monthly_cap": null
}
```

**Usage History**:
```bash
GET /api/v1/llm/usage
Authorization: Bearer sk-loopnet-service-key-2025

Response:
{
  "total_requests": 15234,
  "total_tokens": 2500000,
  "total_cost": 125.50,
  "avg_cost_per_request": 0.0082,
  "providers": [
    {
      "provider": "openai",
      "requests": 10000,
      "tokens": 1800000,
      "cost": 90.00
    },
    {
      "provider": "anthropic",
      "requests": 5234,
      "tokens": 700000,
      "cost": 35.50
    }
  ]
}
```

---

## Rate Limits & Quotas

### Subscription Tier Limits

| Tier | Daily Limit | Monthly Limit | Reset Period |
|------|-------------|---------------|--------------|
| **Trial** | 100 calls/day | 700 total (7 days) | Daily |
| **Starter** | 34 calls/day | 1,000 calls/month | Monthly |
| **Professional** | 334 calls/day | 10,000 calls/month | Monthly |
| **Enterprise** | Unlimited | Unlimited | - |
| **VIP Founder** | Unlimited | Unlimited | - |
| **BYOK** | Unlimited | Unlimited | - |

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 10000           # Monthly quota
X-RateLimit-Remaining: 9850        # Calls remaining this period
X-RateLimit-Reset: 1733097600      # Unix timestamp of quota reset
```

### 429 Too Many Requests

When quota is exceeded:

```json
{
  "error": {
    "message": "Rate limit exceeded. Monthly limit: 10,000 calls. Used: 10,001. Resets on 2025-12-01.",
    "type": "rate_limit_error",
    "code": "quota_exceeded"
  }
}
```

**Automatic Quota Reset**:
- **Daily**: 00:00 UTC
- **Monthly**: 1st of month, 00:00 UTC

---

## Code Examples

### Python (requests)

```python
import requests
from typing import List, Dict

class OpsLLMClient:
    """Client for Ops-Center LLM API"""

    def __init__(self, service_key: str, base_url: str = "http://ops-center-centerdeep:8084"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json"
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 500,
        power_level: str = "balanced"
    ) -> Dict:
        """
        Send chat completion request

        Args:
            messages: List of {role, content} dicts
            model: Model name
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Max tokens to generate
            power_level: eco, balanced, or precision

        Returns:
            API response dict
        """
        response = requests.post(
            f"{self.base_url}/api/v1/llm/chat/completions",
            headers=self.headers,
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "power_level": power_level
            }
        )

        response.raise_for_status()
        return response.json()

    def extract_company_info(self, text: str) -> str:
        """Extract company information from text"""
        messages = [
            {
                "role": "system",
                "content": "Extract company name, industry, and location. Return as JSON."
            },
            {
                "role": "user",
                "content": text
            }
        ]

        result = self.chat_completion(
            messages=messages,
            model="gpt-4o-mini",
            power_level="eco"  # Cheaper for bulk extraction
        )

        return result['choices'][0]['message']['content']

    def check_credits(self) -> Dict:
        """Check remaining credits"""
        response = requests.get(
            f"{self.base_url}/api/v1/llm/credits",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


# Usage Example
if __name__ == "__main__":
    # Initialize client
    client = OpsLLMClient("sk-loopnet-service-key-2025")

    # Extract company info
    text = """
    Acme Corporation is a leading technology company based in San Francisco, CA.
    They specialize in cloud infrastructure and enterprise software solutions.
    """

    info = client.extract_company_info(text)
    print("Company Info:", info)

    # Check credits
    credits = client.check_credits()
    print(f"Credits Remaining: {credits['credits_remaining']}")
```

---

### Node.js (axios)

```javascript
const axios = require('axios');

class OpsLLMClient {
  constructor(serviceKey, baseURL = 'http://ops-center-centerdeep:8084') {
    this.client = axios.create({
      baseURL: baseURL,
      headers: {
        'Authorization': `Bearer ${serviceKey}`,
        'Content-Type': 'application/json'
      }
    });
  }

  async chatCompletion({ messages, model = 'gpt-4o-mini', temperature = 0.7, maxTokens = 500, powerLevel = 'balanced' }) {
    try {
      const response = await this.client.post('/api/v1/llm/chat/completions', {
        model,
        messages,
        temperature,
        max_tokens: maxTokens,
        power_level: powerLevel
      });

      return response.data;
    } catch (error) {
      console.error('Chat completion error:', error.response?.data || error.message);
      throw error;
    }
  }

  async extractCompanyInfo(text) {
    const messages = [
      {
        role: 'system',
        content: 'Extract company name, industry, and location. Return as JSON.'
      },
      {
        role: 'user',
        content: text
      }
    ];

    const result = await this.chatCompletion({
      messages,
      model: 'gpt-4o-mini',
      powerLevel: 'eco'
    });

    return result.choices[0].message.content;
  }

  async checkCredits() {
    try {
      const response = await this.client.get('/api/v1/llm/credits');
      return response.data;
    } catch (error) {
      console.error('Credits check error:', error.response?.data || error.message);
      throw error;
    }
  }
}

// Usage Example
(async () => {
  const client = new OpsLLMClient('sk-loopnet-service-key-2025');

  const text = `
    Acme Corporation is a leading technology company based in San Francisco, CA.
    They specialize in cloud infrastructure and enterprise software solutions.
  `;

  try {
    // Extract company info
    const info = await client.extractCompanyInfo(text);
    console.log('Company Info:', info);

    // Check credits
    const credits = await client.checkCredits();
    console.log('Credits Remaining:', credits.credits_remaining);
  } catch (error) {
    console.error('Error:', error.message);
  }
})();
```

---

### Curl Examples

**Basic Chat Completion**:
```bash
curl -X POST http://ops-center-centerdeep:8084/api/v1/llm/chat/completions \
  -H "Authorization: Bearer sk-loopnet-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ]
  }'
```

**With Streaming**:
```bash
curl -X POST http://ops-center-centerdeep:8084/api/v1/llm/chat/completions \
  -H "Authorization: Bearer sk-loopnet-service-key-2025" \
  -H "Content-Type: application/json" \
  -H "X-Power-Level: eco" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "user", "content": "Write a haiku about unicorns"}
    ],
    "stream": true
  }'
```

**Check Credits**:
```bash
curl -X GET http://ops-center-centerdeep:8084/api/v1/llm/credits \
  -H "Authorization: Bearer sk-loopnet-service-key-2025"
```

**List Models**:
```bash
curl -X GET http://ops-center-centerdeep:8084/api/v1/llm/models \
  -H "Authorization: Bearer sk-loopnet-service-key-2025"
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Action |
|------|---------|--------|
| **200** | Success | Process response |
| **400** | Bad Request | Check request format |
| **401** | Unauthorized | Check API key |
| **402** | Payment Required | Insufficient credits |
| **429** | Too Many Requests | Rate limit exceeded, retry after reset |
| **500** | Server Error | Retry with exponential backoff |
| **503** | Service Unavailable | LiteLLM proxy down, retry |

### Error Response Format

```json
{
  "error": {
    "message": "Insufficient credits. Balance: 5.234, Estimated cost: 10.500",
    "type": "insufficient_credits",
    "code": "payment_required",
    "param": null
  }
}
```

### Common Errors

#### 401 Unauthorized
```json
{
  "error": {
    "message": "Invalid service key",
    "type": "invalid_request_error",
    "code": "invalid_api_key"
  }
}
```

**Solution**: Verify service key is correct and added to `litellm_api.py`.

---

#### 402 Payment Required (Insufficient Credits)
```json
{
  "error": {
    "message": "Insufficient organization credits. Available: 100.500, needed: 150.750",
    "type": "insufficient_credits",
    "code": "payment_required"
  }
}
```

**Solution**: Contact admin to add credits to organization pool.

---

#### 429 Too Many Requests (Quota Exceeded)
```json
{
  "error": {
    "message": "Rate limit exceeded. Monthly limit: 10,000 calls. Used: 10,001. Resets on 2025-12-01.",
    "type": "rate_limit_error",
    "code": "quota_exceeded"
  }
}
```

**Solution**: Wait for quota reset or upgrade subscription tier.

---

### Retry Logic (Python)

```python
import time
import requests
from typing import Dict

def chat_with_retry(
    client: OpsLLMClient,
    messages: List[Dict],
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> Dict:
    """
    Send chat request with exponential backoff retry

    Args:
        client: OpsLLMClient instance
        messages: Chat messages
        max_retries: Max retry attempts
        backoff_factor: Exponential backoff multiplier

    Returns:
        API response
    """
    for attempt in range(max_retries):
        try:
            return client.chat_completion(messages)

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                # Rate limit - wait for reset
                reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
                if reset_time:
                    wait_seconds = reset_time - int(time.time())
                    print(f"Rate limit hit. Waiting {wait_seconds}s...")
                    time.sleep(wait_seconds + 1)
                    continue

            elif e.response.status_code in [500, 503]:
                # Server error - retry with backoff
                wait_seconds = backoff_factor ** attempt
                print(f"Server error. Retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
                continue

            else:
                # Other errors - don't retry
                raise

        except requests.exceptions.RequestException as e:
            # Network error - retry with backoff
            if attempt < max_retries - 1:
                wait_seconds = backoff_factor ** attempt
                print(f"Network error. Retrying in {wait_seconds}s...")
                time.sleep(wait_seconds)
                continue
            else:
                raise

    raise Exception(f"Failed after {max_retries} retries")
```

---

## Internal vs External Access

### Internal Network Access (Recommended)

**Endpoint**: `http://ops-center-centerdeep:8084`

**Advantages**:
- ✅ **Faster**: No SSL/TLS handshake overhead
- ✅ **No DNS lookup**: Direct container name resolution
- ✅ **No external routing**: Stays within Docker network
- ✅ **No Traefik overhead**: Direct connection to backend

**Use Cases**:
- LoopNet Leads backend (company enrichment)
- Center-Deep Pro (AI summaries)
- Brigade agents (LLM inference)
- Any service in `unicorn-network`

**Network Configuration**:
```yaml
# docker-compose.yml
services:
  loopnet-leads-backend:
    networks:
      - unicorn-network  # Same network as ops-center-centerdeep
    environment:
      - OPS_LLM_API=http://ops-center-centerdeep:8084/api/v1/llm
```

---

### External HTTPS Access

**Endpoint**: `https://ops.centerdeep.online`

**Advantages**:
- ✅ **Secure**: SSL/TLS encryption
- ✅ **Accessible**: From anywhere on internet
- ✅ **Browser-compatible**: CORS enabled

**Use Cases**:
- External third-party integrations
- Browser-based frontends
- Mobile apps
- Public API access

**CORS Configuration**:
```python
# backend/server.py already has CORS enabled
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## BYOK vs Platform Keys

### Bring Your Own Key (BYOK)

Users can add their own API keys from OpenRouter, OpenAI, Anthropic, Google, etc.

**How It Works**:
1. User adds API key via `/api/v1/llm/byok/keys`
2. Ops-Center encrypts and stores key
3. When user makes request, Ops-Center uses **their key**
4. **No credits charged** (user pays provider directly)

**Example - Add BYOK Key**:
```bash
curl -X POST http://ops-center-centerdeep:8084/api/v1/llm/byok/keys \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openrouter",
    "api_key": "sk-or-v1-abc123...",
    "metadata": {
      "description": "My OpenRouter key for unlimited models"
    }
  }'
```

**Advantages**:
- ✅ **Free API calls** (no credit deduction)
- ✅ **Access to ALL models** (100+ via OpenRouter)
- ✅ **No rate limits** (based on provider's limits)
- ✅ **Direct billing** (show on provider invoice)

**Use Cases**:
- High-volume users
- Cost-conscious teams
- Users wanting specific models

---

### Platform Keys (Default)

Ops-Center uses **system-level keys** (admin-managed) for users without BYOK.

**How It Works**:
1. User makes request
2. Ops-Center checks if user has BYOK
3. If no BYOK, uses **platform OpenRouter key**
4. **Credits deducted** from user/org balance

**Advantages**:
- ✅ **No setup required** (users don't need provider accounts)
- ✅ **Centralized billing** (single invoice)
- ✅ **Usage tracking** (credit system monitors all usage)

**Disadvantages**:
- ⚠️ **Credits consumed** (costs money)
- ⚠️ **Rate limits apply** (subscription tier quotas)

---

### Model Access Comparison

| Access Method | Free Tier | Starter | Professional | Enterprise | BYOK |
|---------------|-----------|---------|--------------|------------|------|
| **Local Models** | ✅ 4 models | ✅ 4 models | ✅ 4 models | ✅ 4 models | ✅ All |
| **Cloud Models** | ❌ | ✅ 7 models | ✅ 9 models | ✅ 11 models | ✅ All (100+) |
| **GPT-4o** | ❌ | ❌ | ✅ (via OpenRouter) | ✅ (direct) | ✅ (if key added) |
| **Claude 3.5 Sonnet** | ❌ | ❌ | ✅ (via OpenRouter) | ✅ (direct) | ✅ (if key added) |
| **o1-preview** | ❌ | ❌ | ❌ | ✅ | ✅ (if key added) |
| **Cost** | Free | $19/mo | $49/mo | $99/mo | Provider pricing |

---

## Integration Checklist

### For LoopNet Leads

- [ ] Add service key to `litellm_api.py` (line 569)
- [ ] Configure environment variable:
  ```bash
  OPS_LLM_API=http://ops-center-centerdeep:8084/api/v1/llm
  OPS_LLM_SERVICE_KEY=sk-loopnet-service-key-2025
  ```
- [ ] Create organization in Ops-Center database
- [ ] Allocate credits to organization
- [ ] Test company enrichment endpoint
- [ ] Monitor usage via `/api/v1/llm/usage`

---

### For Center-Deep Pro

- [ ] Add service key to `litellm_api.py` (line 569)
- [ ] Configure environment variable:
  ```bash
  OPS_LLM_API=http://ops-center-centerdeep:8084/api/v1/llm
  OPS_LLM_SERVICE_KEY=sk-centerdeep-service-key-2025
  ```
- [ ] Create organization in Ops-Center database
- [ ] Allocate credits to organization
- [ ] Test AI search summary endpoint
- [ ] Test AI analysis endpoint
- [ ] Monitor usage via `/api/v1/llm/usage`

---

## Troubleshooting

### Issue: 401 Unauthorized

**Symptoms**:
```json
{"error": {"message": "Invalid service key", "code": "invalid_api_key"}}
```

**Solution**:
1. Verify service key is added to `backend/litellm_api.py` line 566-570
2. Restart Ops-Center container: `docker restart ops-center-centerdeep`
3. Check logs: `docker logs ops-center-centerdeep -f`

---

### Issue: Connection Refused

**Symptoms**:
```
requests.exceptions.ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**Solution**:
1. Verify container is running: `docker ps | grep ops-center-centerdeep`
2. Check container health: `docker inspect ops-center-centerdeep | grep Health -A 10`
3. Verify network: `docker network inspect unicorn-network | grep ops-center-centerdeep`
4. Check if service is on same Docker network

---

### Issue: 502 Bad Gateway (External Access)

**Symptoms**: HTTPS requests to `https://ops.centerdeep.online` fail

**Solution**:
1. Check Traefik is running: `docker ps | grep traefik`
2. Verify Traefik labels in `docker-compose.centerdeep.yml`
3. Check Cloudflare DNS points to server
4. Verify SSL certificates: `docker logs traefik | grep certificate`

---

### Issue: Slow Response Times

**Symptoms**: Requests take >5 seconds

**Solution**:
1. **Use internal endpoint** (`http://ops-center-centerdeep:8084`) instead of external
2. **Lower power_level** to `eco` for faster, cheaper responses
3. **Reduce max_tokens** to minimize generation time
4. **Check LiteLLM proxy**: `docker logs uchub-litellm -f`

---

## Support & Documentation

### Internal Documentation
- **Ops-Center Guide**: `/opt/ops-center/CLAUDE.md`
- **LiteLLM API Source**: `/opt/ops-center/backend/litellm_api.py`
- **Organizational Billing**: `/opt/ops-center/backend/org_credit_integration.py`
- **Usage Tracking**: `/opt/ops-center/backend/usage_tracking.py`

### Container Information
- **Container Name**: `ops-center-centerdeep`
- **Internal Port**: 8084
- **Networks**: `unicorn-network`, `web`
- **Database**: `unicorn_db` on `unicorn-postgresql`
- **Health Check**: `http://ops-center-centerdeep:8084/` (30s interval)

### Useful Commands
```bash
# Check container status
docker ps | grep ops-center-centerdeep

# View logs
docker logs ops-center-centerdeep -f

# Restart service
docker restart ops-center-centerdeep

# Check network connectivity
docker exec loopnet-leads-backend ping ops-center-centerdeep

# Access database
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db

# Check Redis
docker exec unicorn-redis redis-cli KEYS "credit:*"
```

---

## Appendix A: Service Key Setup

### Add New Service Key to Ops-Center

**File**: `/opt/ops-center/backend/litellm_api.py`

**Location**: Line 566-570

```python
# Check for service key (format: sk-<service>-service-key-<year>)
if token.startswith('sk-'):
    logger.info(f"🔑 Token starts with 'sk-', checking service keys...")
    # Service keys are pre-configured trusted keys for internal services
    service_keys = {
        'sk-bolt-diy-service-key-2025': 'bolt-diy-service',
        'sk-presenton-service-key-2025': 'presenton-service',
        'sk-brigade-service-key-2025': 'brigade-service',
        'sk-loopnet-service-key-2025': 'loopnet-service',        # ADD THIS
        'sk-centerdeep-service-key-2025': 'centerdeep-service',  # ADD THIS
    }
```

**Restart Required**: Yes
```bash
docker restart ops-center-centerdeep
```

---

## Appendix B: Organization Setup

### Create Organization in Database

```sql
-- Connect to database
docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_db

-- Create organization
INSERT INTO organizations (id, name, tier, created_at, updated_at)
VALUES (
  'org_loopnet_leads',
  'LoopNet Leads',
  'enterprise',
  NOW(),
  NOW()
);

-- Add user to organization
INSERT INTO organization_members (org_id, user_id, role, joined_at)
VALUES (
  'org_loopnet_leads',
  'loopnet-service',
  'admin',
  NOW()
);

-- Allocate credits (10 million = 10,000,000 credits = $10,000 worth)
INSERT INTO user_credit_allocations (org_id, user_id, allocated_credits, used_credits)
VALUES (
  'org_loopnet_leads',
  'loopnet-service',
  10000000000,  -- 10 million credits (stored as milicredits)
  0
);
```

---

## Appendix C: Usage Analytics Queries

### Get Top Users by API Calls
```sql
SELECT
  user_id,
  COUNT(*) as total_calls,
  SUM(tokens_used) as total_tokens,
  SUM(credits_used) / 1000.0 as total_credits,
  AVG(response_time_ms) as avg_response_ms
FROM api_usage_logs
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY user_id
ORDER BY total_calls DESC
LIMIT 10;
```

### Get Most Expensive Models
```sql
SELECT
  model,
  COUNT(*) as calls,
  SUM(credits_used) / 1000.0 as total_credits,
  AVG(credits_used) / 1000.0 as avg_credits_per_call
FROM api_usage_logs
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY model
ORDER BY total_credits DESC
LIMIT 10;
```

### Get Organization Usage
```sql
SELECT
  o.name as org_name,
  COUNT(DISTINCT u.user_id) as active_users,
  COUNT(*) as total_calls,
  SUM(u.credits_used) / 1000.0 as total_credits
FROM api_usage_logs u
JOIN organization_members om ON u.user_id = om.user_id
JOIN organizations o ON om.org_id = o.id
WHERE u.created_at > NOW() - INTERVAL '30 days'
GROUP BY o.id, o.name
ORDER BY total_credits DESC;
```

---

**End of Integration Guide**

For questions or issues, contact the Ops-Center team or check the internal documentation.

**Version History**:
- v2.0 (Nov 14, 2025): Complete integration guide for centerdeep.online deployment
- v1.0 (Oct 29, 2025): Initial guide for unicorncommander.ai deployment
