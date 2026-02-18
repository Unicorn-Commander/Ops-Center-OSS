# Ops-Center LiteLLM Integration Guide

**Last Updated**: November 4, 2025
**Version**: 2.2.0

---

## Overview

Ops-Center provides an OpenAI-compatible LiteLLM API that integrates with popular AI applications. This guide covers setup for:

1. **Open-WebUI** - Chat interface
2. **Bolt.DIY** - AI development environment
3. **Presenton** - AI presentation generator

---

## Understanding BYOK vs Platform Models

Ops-Center separates models into two categories:

### 🆓 BYOK (Bring Your Own Key) Models

- **What**: Models accessed using YOUR API keys (OpenRouter, OpenAI, Anthropic, etc.)
- **Cost**: **NO CREDITS CHARGED** - You pay providers directly
- **Setup**: Add your API keys in `/admin/account/api-keys`
- **Example**: If you add an OpenRouter key, all 348 OpenRouter models become free for you

### 💳 Platform Models

- **What**: Models accessed using platform-managed keys
- **Cost**: **CREDITS CHARGED** from your account balance
- **Setup**: Automatic - just select and use
- **Example**: Premium models available to all users, billed per usage

---

## API Endpoints

### Base URL

```bash
# Production
https://unicorncommander.ai/api/v1/llm

# Local Development
http://localhost:8084/api/v1/llm
```

### Key Endpoints

#### 1. Chat Completions (OpenAI-compatible)

```bash
POST /chat/completions
```

**Request**:
```json
{
  "model": "openai/gpt-4",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}
```

**Headers**:
```
Authorization: Bearer YOUR_UC_API_KEY
Content-Type: application/json
```

#### 2. List All Models

```bash
GET /models
```

Returns flat list of all available models (348+ models).

#### 3. List Models by Category (NEW)

```bash
GET /models/categorized
```

Returns models organized by BYOK vs Platform:

```json
{
  "byok_models": [
    {
      "provider": "OpenRouter",
      "provider_type": "external",
      "models": [...348 models...],
      "count": 348,
      "free": true,
      "note": "Using your OpenRouter API key - no credits charged",
      "source": "byok"
    }
  ],
  "platform_models": [
    {
      "provider": "OpenAI",
      "provider_type": "external",
      "models": [...10 models...],
      "count": 10,
      "note": "Charged with credits from your account",
      "source": "platform"
    }
  ],
  "summary": {
    "total_models": 358,
    "byok_count": 348,
    "platform_count": 10,
    "has_byok_keys": true,
    "byok_providers": ["openrouter", "huggingface"]
  }
}
```

#### 4. Image Generation

```bash
POST /image/generations
```

**Request**:
```json
{
  "prompt": "A futuristic unicorn",
  "model": "dall-e-3",
  "size": "1024x1024",
  "quality": "standard",
  "n": 1
}
```

**Pricing**:
- DALL-E 3 (1024x1024): 48 credits (~$0.048)
- DALL-E 2 (1024x1024): 22 credits (~$0.022)
- Stable Diffusion XL: 6 credits (~$0.006)

---

## Integration Configurations

### 1. Open-WebUI Configuration

**Location**: Admin Settings → Connections

#### OpenAI Connection

```yaml
Base URL: https://unicorncommander.ai/api/v1/llm
API Key: uc_api_xxxxxxxxxxxxxx
```

**Steps**:
1. Login to Open-WebUI
2. Go to **Admin Panel** → **Settings** → **Connections**
3. Under **OpenAI API**:
   - **API Base URL**: `https://unicorncommander.ai/api/v1/llm`
   - **API Key**: Your UC API key (generate at `/admin/account/api-keys`)
   - Click **Verify Connection**
4. Save settings

#### Model Selection

Open-WebUI will automatically discover all available models via `/models` endpoint.

**To see BYOK vs Platform distinction**:
- Models using your BYOK keys will show as "free" in usage reports
- Platform models will show credit charges

---

### 2. Bolt.DIY Configuration

**Location**: `.env` file or Environment Variables

#### Environment Variables

```bash
# Ops-Center LiteLLM Integration
OPENAI_API_BASE=https://unicorncommander.ai/api/v1/llm
OPENAI_API_KEY=uc_api_xxxxxxxxxxxxxx

# Optional: Default model
DEFAULT_MODEL=openai/gpt-4-turbo
```

#### Docker Compose (if using)

```yaml
services:
  bolt:
    image: your-bolt-image
    environment:
      - OPENAI_API_BASE=https://unicorncommander.ai/api/v1/llm
      - OPENAI_API_KEY=uc_api_xxxxxxxxxxxxxx
      - DEFAULT_MODEL=openai/gpt-4-turbo
    ports:
      - "5173:5173"
```

#### Testing

```bash
# Test connection from Bolt container
curl -H "Authorization: Bearer uc_api_xxxxxxxxxxxxxx" \
  https://unicorncommander.ai/api/v1/llm/models
```

---

### 3. Presenton Configuration

**Location**: `.env` or Environment Variables

#### Environment Variables

```bash
# Ops-Center LiteLLM Integration
LLM_API_BASE_URL=https://unicorncommander.ai/api/v1/llm/chat/completions
LLM_API_KEY=uc_api_xxxxxxxxxxxxxx

# Optional: Model selection
LLM_MODEL=openai/gpt-4-turbo

# Optional: Image generation
IMAGE_API_BASE_URL=https://unicorncommander.ai/api/v1/llm/image/generations
IMAGE_API_KEY=uc_api_xxxxxxxxxxxxxx
```

#### Docker Compose

```yaml
services:
  presenton-frontend:
    environment:
      - NEXT_PUBLIC_LLM_API_BASE=https://unicorncommander.ai/api/v1/llm
      - NEXT_PUBLIC_LLM_API_KEY=uc_api_xxxxxxxxxxxxxx

  presenton-backend:
    environment:
      - LLM_API_BASE_URL=https://unicorncommander.ai/api/v1/llm/chat/completions
      - LLM_API_KEY=uc_api_xxxxxxxxxxxxxx
      - IMAGE_API_BASE_URL=https://unicorncommander.ai/api/v1/llm/image/generations
```

#### Testing

```bash
# Test chat completions
curl -X POST https://unicorncommander.ai/api/v1/llm/chat/completions \
  -H "Authorization: Bearer uc_api_xxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4-turbo",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Test image generation
curl -X POST https://unicorncommander.ai/api/v1/llm/image/generations \
  -H "Authorization: Bearer uc_api_xxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A unicorn",
    "model": "dall-e-3"
  }'
```

---

## BYOK Setup Instructions

### Step 1: Add Your API Keys

1. Login to Ops-Center: https://unicorncommander.ai
2. Navigate to **Account** → **API Keys**
3. Click **Add Provider Key**
4. Select provider (OpenRouter, OpenAI, Anthropic, etc.)
5. Paste your API key
6. Click **Save**

### Step 2: Verify Key Status

```bash
GET /api/v1/llm/byok/keys
```

Response shows all your configured keys:
```json
{
  "providers": [
    {
      "provider": "openrouter",
      "enabled": true,
      "created_at": "2025-11-03T18:40:26Z"
    },
    {
      "provider": "huggingface",
      "enabled": true,
      "created_at": "2025-11-04T01:49:22Z"
    }
  ]
}
```

### Step 3: Use BYOK Models

Once keys are added, use models from that provider **without credit charges**:

```bash
POST /api/v1/llm/chat/completions
```

```json
{
  "model": "openrouter/anthropic/claude-3.5-sonnet",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

**Result**: Uses YOUR OpenRouter key → **0 credits charged**

---

## Model Naming Conventions

Models follow `provider/model-name` format:

### OpenRouter Models
```
openrouter/anthropic/claude-3.5-sonnet
openrouter/openai/gpt-4-turbo
openrouter/google/gemini-2.0-flash-exp:free
```

### Direct Provider Models
```
openai/gpt-4-turbo
anthropic/claude-3-opus
google/gemini-pro
```

### Special Suffixes
- `:free` - Free tier models (no cost on provider side)
- `:extended` - Extended context versions
- `-preview` - Preview/beta models

---

## Cost Tracking

### Credit Charges (Platform Models)

When using platform models, credits are automatically deducted:

```json
{
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  },
  "cost": {
    "credits": 0.12,
    "usd_equivalent": "$0.00012"
  }
}
```

### BYOK (No Charges)

When using BYOK models:

```json
{
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  },
  "cost": {
    "credits": 0.0,
    "note": "BYOK - no credits charged"
  }
}
```

---

## Error Handling

### Common Errors

#### 1. Insufficient Credits

```json
{
  "error": {
    "message": "Insufficient credits",
    "type": "insufficient_credits",
    "code": 402,
    "details": {
      "required": 1.2,
      "available": 0.5
    }
  }
}
```

**Solution**: Add credits at `/admin/subscription/billing`

#### 2. Invalid API Key

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": 401
  }
}
```

**Solution**: Generate new UC API key at `/admin/account/api-keys`

#### 3. Model Not Available

```json
{
  "error": {
    "message": "Model not found",
    "type": "invalid_request_error",
    "code": 404,
    "details": {
      "model": "invalid/model-name",
      "available_models": "/api/v1/llm/models"
    }
  }
}
```

**Solution**: Check available models at `/api/v1/llm/models`

#### 4. Rate Limit Exceeded

```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "code": 429,
    "retry_after": 60
  }
}
```

**Solution**: Wait and retry, or upgrade subscription tier

---

## Advanced Features

### 1. Model Filtering by Capability

Filter models by features:

```bash
GET /api/v1/llm/models?capability=function_calling
GET /api/v1/llm/models?capability=vision
GET /api/v1/llm/models?context_length_min=32000
```

### 2. Provider-Specific Headers

Some providers require additional headers:

```bash
# OpenRouter
curl -H "X-Title: My App Name" \
     -H "HTTP-Referer: https://myapp.com" \
     ...

# Anthropic
curl -H "anthropic-version: 2023-06-01" \
     ...
```

Ops-Center automatically adds these for you.

### 3. Streaming Responses

Enable streaming for real-time output:

```json
{
  "model": "openai/gpt-4-turbo",
  "messages": [...],
  "stream": true
}
```

Response comes as Server-Sent Events (SSE):
```
data: {"choices": [{"delta": {"content": "Hello"}}]}
data: {"choices": [{"delta": {"content": " world"}}]}
data: [DONE]
```

---

## Monitoring & Analytics

### Usage Dashboard

View your API usage at:
- **Subscription → Usage**: https://unicorncommander.ai/admin/subscription/usage

Shows:
- Total requests by model
- Credit consumption
- BYOK vs Platform usage split
- Top models used
- Cost trends

### Real-time Logs

View live API logs (admin only):
- **System → Logs**: https://unicorncommander.ai/admin/logs

---

## Troubleshooting

### Bolt.DIY Not Connecting

**Check**:
1. Environment variables are set correctly
2. API key is valid: `curl -H "Authorization: Bearer YOUR_KEY" https://unicorncommander.ai/api/v1/llm/models`
3. Firewall allows outbound HTTPS
4. Base URL doesn't have trailing slash

### Presenton Not Generating Images

**Check**:
1. Image generation endpoint configured: `/api/v1/llm/image/generations`
2. Sufficient credits for image generation (48+ credits)
3. Model specified correctly (e.g., `dall-e-3`)

### Open-WebUI Shows Wrong Credits

**Check**:
1. Refresh the models list in Open-WebUI admin
2. Check BYOK keys are enabled: `/api/v1/llm/byok/keys`
3. Verify provider name matches (case-sensitive)

---

## Support

- **Documentation**: https://unicorncommander.ai/docs
- **API Reference**: https://unicorncommander.ai/docs/api
- **Status Page**: https://status.unicorncommander.ai

---

## Changelog

### v2.2.0 (November 4, 2025)

- ✅ Added `/models/categorized` endpoint
- ✅ BYOK vs Platform model separation
- ✅ Image generation API
- ✅ Enhanced cost tracking

### v2.1.0 (October 29, 2025)

- ✅ Credit system authentication fixes
- ✅ OpenRouter integration
- ✅ BYOK key management

### v2.0.0 (October 15, 2025)

- ✅ Initial LiteLLM API release
- ✅ OpenAI-compatible endpoints
- ✅ Multi-provider routing
