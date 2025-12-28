# UC-Cloud App Developer Integration Guide

**Version**: 1.0.0
**Last Updated**: November 4, 2025
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication Methods](#authentication-methods)
4. [API Endpoints](#api-endpoints)
5. [Platform Integration Examples](#platform-integration-examples)
6. [BYOK Detection & Routing](#byok-detection--routing)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)
9. [Testing Guide](#testing-guide)
10. [FAQ](#faq)

---

## Overview

UC-Cloud provides a **centralized LLM infrastructure** that:

- ✅ **Single Sign-On** - Users authenticate once via Keycloak
- ✅ **100% OpenAI-compatible API** - Drop-in replacement for OpenAI SDK
- ✅ **Automatic BYOK detection** - Uses user's own keys when available
- ✅ **Credit-based billing** - Platform keys deduct from user credits
- ✅ **100+ models** - OpenRouter, OpenAI, Anthropic, Google, and more
- ✅ **Usage tracking** - All API calls logged for billing/analytics

### Key Benefits

**For App Developers**:
- No need to manage API keys or billing
- One integration works for all users (BYOK or platform credits)
- OpenAI-compatible means minimal code changes
- Centralized rate limiting and quota management

**For Users**:
- Bring your own keys (BYOK) for unlimited usage
- Or use platform credits for pay-as-you-go
- Seamless experience across all apps
- Usage tracking and analytics in one place

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User                                 │
│              (Authenticated via Keycloak SSO)                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Accesses app
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Your App                                  │
│         (Bolt.DIY, Presenton, Open-WebUI, etc.)             │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Makes LLM requests
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Ops-Center API                             │
│              (LiteLLM Proxy + Credit System)                 │
│         https://your-domain.com/api/v1/llm              │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼────────┐   ┌──────▼──────┐
            │  User has BYOK? │   │  No BYOK?   │
            │  YES: Use their │   │  Use platform│
            │  API key        │   │  key, deduct │
            │  (no charge)    │   │  credits     │
            └───────┬─────────┘   └──────┬───────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM Providers                                   │
│  OpenRouter | OpenAI | Anthropic | Google | Others          │
└─────────────────────────────────────────────────────────────┘
```

**Request Flow**:
1. User authenticates with Keycloak (one-time)
2. User accesses your app (SSO automatically logs them in)
3. Your app makes LLM request with service key + user identifier
4. Ops-Center checks if user has BYOK for that provider
5. Routes to appropriate provider (user's key or platform key)
6. Returns response to your app (same format regardless)

---

## Authentication Methods

### Method 1: Service Keys (Recommended for UC-integrated apps)

**Best for**: Apps integrated into UC-Cloud ecosystem (Bolt.DIY, Presenton, Open-WebUI, Brigade)

**How it works**:
- Your app uses a **pre-configured service key** (e.g., `sk-bolt-diy-service-key-2025`)
- Service key identifies your app to the platform
- You **must** pass user identifier in the `user` field
- Platform handles BYOK detection and billing automatically

**Configuration**:
```javascript
// .env file
UC_CLOUD_API_URL=https://your-domain.com/api/v1/llm
UC_CLOUD_SERVICE_KEY=sk-yourapp-service-key-2025

// In your app
const API_URL = process.env.UC_CLOUD_API_URL;
const SERVICE_KEY = process.env.UC_CLOUD_SERVICE_KEY;
```

**Pre-configured Service Keys**:
- `sk-bolt-diy-service-key-2025` - Bolt.DIY development environment
- `sk-presenton-service-key-2025` - Presenton presentation generator
- `sk-brigade-service-key-2025` - Brigade agent platform
- `sk-openwebui-service-key-2025` - Open-WebUI chat interface (to be added)

**To request a new service key**: Contact the UC-Cloud admin team.

### Method 2: User API Keys (For external/third-party apps)

**Best for**: External apps, CLI tools, scripts, integrations

**How it works**:
- Users generate their own API keys from Ops-Center dashboard
- API key format: `uc_<hex-string>`
- API key is scoped to that user (billing tracked per user)
- No need to pass `user` field (inferred from API key)

**User generates key**:
1. Go to: https://your-domain.com/admin/account/api-keys
2. Click "Generate New API Key"
3. Copy key (shown only once): `uc_a1b2c3d4e5f6...`
4. Use in your app configuration

**Configuration**:
```javascript
// .env file
UC_CLOUD_API_URL=https://your-domain.com/api/v1/llm
UC_CLOUD_USER_API_KEY=uc_a1b2c3d4e5f6...

// In your app
const API_URL = process.env.UC_CLOUD_API_URL;
const USER_API_KEY = process.env.UC_CLOUD_USER_API_KEY;
```

---

## API Endpoints

### Base URL

**Production**: `https://your-domain.com/api/v1/llm`
**Internal (Docker)**: `http://ops-center-direct:8084/api/v1/llm`

### Available Endpoints

#### 1. Chat Completions (Main endpoint)

```http
POST /v1/chat/completions
Content-Type: application/json
Authorization: Bearer <service-key or user-api-key>

{
  "model": "openai/gpt-4",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "user": "user@example.com",  // REQUIRED for service keys
  "max_tokens": 1000,
  "temperature": 0.7,
  "stream": false
}
```

**Response** (OpenAI-compatible):
```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "created": 1699000000,
  "model": "openai/gpt-4",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  },
  "_metadata": {
    "provider_used": "openai/gpt-4",
    "cost_incurred": 0.0015,
    "credits_remaining": 9998.5,
    "using_byok": false
  }
}
```

#### 2. List Available Models

```http
GET /v1/models
Authorization: Bearer <service-key or user-api-key>
```

**Response**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "openai/gpt-4",
      "object": "model",
      "owned_by": "openai",
      "tier": "professional"
    },
    {
      "id": "anthropic/claude-3.5-sonnet",
      "object": "model",
      "owned_by": "anthropic",
      "tier": "professional"
    }
  ]
}
```

#### 3. Get Credit Balance

```http
GET /v1/credits
Authorization: Bearer <service-key or user-api-key>
```

**Response**:
```json
{
  "user_id": "user@example.com",
  "credits_remaining": 9998.5,
  "tier": "professional",
  "monthly_cap": null
}
```

#### 4. Get Usage Statistics

```http
GET /v1/usage?days=30
Authorization: Bearer <service-key or user-api-key>
```

**Response**:
```json
{
  "total_requests": 150,
  "total_tokens": 45000,
  "total_cost": 12.50,
  "avg_cost_per_request": 0.083,
  "providers": [
    {
      "provider": "openai",
      "requests": 100,
      "tokens": 30000,
      "cost": 8.00
    },
    {
      "provider": "anthropic",
      "requests": 50,
      "tokens": 15000,
      "cost": 4.50
    }
  ]
}
```

#### 5. Health Check

```http
GET /v1/health
```

**Response**:
```json
{
  "status": "healthy",
  "litellm_proxy": "up",
  "timestamp": "2025-11-04T12:00:00Z"
}
```

---

## Platform Integration Examples

### 1. Bolt.DIY (React + Node.js)

**Purpose**: AI-powered code generation and development environment

#### Frontend Integration (React)

```typescript
// src/lib/openai.ts
import OpenAI from 'openai';

// Initialize client
export const openai = new OpenAI({
  baseURL: import.meta.env.VITE_UC_CLOUD_API_URL || 'https://your-domain.com/api/v1/llm',
  apiKey: import.meta.env.VITE_UC_CLOUD_SERVICE_KEY || 'sk-bolt-diy-service-key-2025',
  dangerouslyAllowBrowser: true, // For client-side usage
  defaultHeaders: {
    'X-App-Name': 'Bolt.DIY',
    'X-App-Version': '1.0.0'
  }
});

// Usage in component
import { useUser } from '@/hooks/useUser';

export function CodeGenerator() {
  const { user } = useUser(); // From Keycloak SSO

  const generateCode = async (prompt: string) => {
    const completion = await openai.chat.completions.create({
      model: 'openai/gpt-4',
      messages: [
        { role: 'system', content: 'You are an expert programmer.' },
        { role: 'user', content: prompt }
      ],
      user: user.email, // CRITICAL: Pass user identifier
      max_tokens: 2000,
      temperature: 0.7
    });

    return completion.choices[0].message.content;
  };

  // ... rest of component
}
```

#### Backend Integration (Node.js/Express)

```typescript
// server/routes/ai.ts
import OpenAI from 'openai';
import { verifyKeycloakToken } from '../middleware/auth';

const openai = new OpenAI({
  baseURL: process.env.UC_CLOUD_API_URL || 'https://your-domain.com/api/v1/llm',
  apiKey: process.env.UC_CLOUD_SERVICE_KEY || 'sk-bolt-diy-service-key-2025'
});

// Protected route - requires authentication
app.post('/api/generate-code', verifyKeycloakToken, async (req, res) => {
  try {
    const { prompt } = req.body;
    const userEmail = req.user.email; // From Keycloak token

    const completion = await openai.chat.completions.create({
      model: 'openai/gpt-4',
      messages: [
        { role: 'system', content: 'You are an expert programmer.' },
        { role: 'user', content: prompt }
      ],
      user: userEmail, // For BYOK detection & billing
      max_tokens: 2000,
      metadata: {
        app: 'bolt-diy',
        feature: 'code_generation',
        user_id: req.user.sub
      }
    });

    res.json({
      code: completion.choices[0].message.content,
      credits_remaining: completion._metadata?.credits_remaining,
      using_byok: completion._metadata?.using_byok
    });
  } catch (error) {
    console.error('Code generation error:', error);
    res.status(500).json({ error: 'Failed to generate code' });
  }
});
```

#### Environment Variables (.env)

```bash
# UC-Cloud Integration
UC_CLOUD_API_URL=https://your-domain.com/api/v1/llm
UC_CLOUD_SERVICE_KEY=sk-bolt-diy-service-key-2025

# Keycloak SSO
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=bolt-diy
KEYCLOAK_CLIENT_SECRET=<from-keycloak>
```

---

### 2. Presenton (Next.js + Python Backend)

**Purpose**: AI-powered presentation generation with web grounding

#### Frontend Integration (Next.js)

```typescript
// app/lib/ai-client.ts
import OpenAI from 'openai';

export class AIClient {
  private openai: OpenAI;

  constructor() {
    this.openai = new OpenAI({
      baseURL: process.env.NEXT_PUBLIC_UC_CLOUD_API_URL || 'https://your-domain.com/api/v1/llm',
      apiKey: process.env.UC_CLOUD_SERVICE_KEY || 'sk-presenton-service-key-2025'
    });
  }

  async generateSlideContent(topic: string, userEmail: string): Promise<string> {
    const completion = await this.openai.chat.completions.create({
      model: 'anthropic/claude-3.5-sonnet',
      messages: [
        {
          role: 'system',
          content: 'You are an expert presentation designer. Generate engaging slide content.'
        },
        {
          role: 'user',
          content: `Create presentation content for: ${topic}`
        }
      ],
      user: userEmail,
      max_tokens: 3000,
      temperature: 0.8
    });

    return completion.choices[0].message.content;
  }

  async refineSlide(slideContent: string, feedback: string, userEmail: string): Promise<string> {
    const completion = await this.openai.chat.completions.create({
      model: 'openai/gpt-4',
      messages: [
        { role: 'system', content: 'You refine presentation slides based on feedback.' },
        { role: 'user', content: `Slide: ${slideContent}\nFeedback: ${feedback}` }
      ],
      user: userEmail,
      max_tokens: 2000
    });

    return completion.choices[0].message.content;
  }
}

// app/api/generate/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { AIClient } from '@/lib/ai-client';

export async function POST(req: NextRequest) {
  const session = await getServerSession();
  if (!session?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { topic } = await req.json();
  const aiClient = new AIClient();

  try {
    const content = await aiClient.generateSlideContent(topic, session.user.email);
    return NextResponse.json({ content });
  } catch (error) {
    console.error('Generation error:', error);
    return NextResponse.json({ error: 'Failed to generate' }, { status: 500 });
  }
}
```

#### Backend Integration (Python/FastAPI)

```python
# app/services/ai_service.py
from openai import AsyncOpenAI
import os

class AIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=os.getenv('UC_CLOUD_API_URL', 'https://your-domain.com/api/v1/llm'),
            api_key=os.getenv('UC_CLOUD_SERVICE_KEY', 'sk-presenton-service-key-2025')
        )

    async def generate_presentation(self, topic: str, user_email: str) -> dict:
        """Generate presentation content using UC-Cloud LLM"""
        try:
            completion = await self.client.chat.completions.create(
                model='anthropic/claude-3.5-sonnet',
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are an expert presentation designer.'
                    },
                    {
                        'role': 'user',
                        'content': f'Create a presentation about: {topic}'
                    }
                ],
                user=user_email,  # For BYOK detection
                max_tokens=4000,
                temperature=0.8,
                metadata={
                    'app': 'presenton',
                    'feature': 'presentation_generation'
                }
            )

            return {
                'content': completion.choices[0].message.content,
                'tokens_used': completion.usage.total_tokens,
                'credits_remaining': completion._metadata.get('credits_remaining'),
                'using_byok': completion._metadata.get('using_byok', False)
            }

        except Exception as e:
            print(f"AI generation error: {e}")
            raise

# app/api/routes.py
from fastapi import APIRouter, Depends
from .services.ai_service import AIService
from .middleware.auth import get_current_user

router = APIRouter()

@router.post('/generate')
async def generate_presentation(
    topic: str,
    user = Depends(get_current_user),
    ai_service: AIService = Depends()
):
    result = await ai_service.generate_presentation(topic, user.email)
    return result
```

---

### 3. Open-WebUI (Python/Svelte)

**Purpose**: Chat interface for LLM interactions

#### Backend Integration (Python)

```python
# backend/apps/webui/models/llms.py
import os
from openai import AsyncOpenAI

class UCCloudLLMProvider:
    """UC-Cloud LLM Provider for Open-WebUI"""

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url=os.getenv('UC_CLOUD_API_URL', 'https://your-domain.com/api/v1/llm'),
            api_key=os.getenv('UC_CLOUD_SERVICE_KEY', 'sk-openwebui-service-key-2025'),
            timeout=120.0
        )

    async def chat_completion(
        self,
        messages: list,
        model: str,
        user_email: str,
        stream: bool = False,
        **kwargs
    ):
        """Send chat completion request to UC-Cloud"""
        try:
            completion = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                user=user_email,  # Critical for BYOK detection
                stream=stream,
                **kwargs
            )

            if stream:
                async for chunk in completion:
                    yield chunk
            else:
                return completion

        except Exception as e:
            print(f"UC-Cloud LLM error: {e}")
            raise

    async def get_available_models(self) -> list:
        """Fetch available models from UC-Cloud"""
        try:
            models = await self.client.models.list()
            return models.data
        except Exception as e:
            print(f"Failed to fetch models: {e}")
            return []

# backend/apps/webui/routers/chats.py
from fastapi import APIRouter, Depends
from ..models.llms import UCCloudLLMProvider
from ..utils.auth import get_current_user

router = APIRouter()

@router.post('/completions')
async def chat_completion(
    request: dict,
    user = Depends(get_current_user),
    llm_provider: UCCloudLLMProvider = Depends()
):
    """Handle chat completion request"""
    messages = request.get('messages', [])
    model = request.get('model', 'openai/gpt-4')
    stream = request.get('stream', False)

    result = await llm_provider.chat_completion(
        messages=messages,
        model=model,
        user_email=user.email,
        stream=stream
    )

    return result
```

#### Frontend Integration (Svelte)

```typescript
// src/lib/apis/llm/index.ts
export const chatCompletion = async (
  messages: Message[],
  model: string,
  userEmail: string,
  stream: boolean = false
) => {
  const response = await fetch('/api/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify({
      messages,
      model,
      stream,
      user: userEmail  // Pass to backend
    })
  });

  if (!response.ok) {
    throw new Error(`Chat completion failed: ${response.statusText}`);
  }

  if (stream) {
    return response.body; // Return stream
  } else {
    return await response.json();
  }
};

// src/routes/chat/[id]/+page.svelte
<script lang="ts">
  import { chatCompletion } from '$lib/apis/llm';
  import { userStore } from '$lib/stores/user';

  async function sendMessage(content: string) {
    const messages = [
      { role: 'user', content }
    ];

    try {
      const completion = await chatCompletion(
        messages,
        selectedModel,
        $userStore.email,
        false
      );

      // Display response
      displayMessage(completion.choices[0].message.content);

      // Show credits if applicable
      if (completion._metadata?.credits_remaining) {
        showCreditsRemaining(completion._metadata.credits_remaining);
      }

      // Show BYOK indicator
      if (completion._metadata?.using_byok) {
        showBYOKIndicator();
      }

    } catch (error) {
      console.error('Chat error:', error);
      showError('Failed to send message');
    }
  }
</script>
```

---

## BYOK Detection & Routing

### How It Works

The UC-Cloud LLM proxy automatically detects if a user has configured their own API keys (BYOK - Bring Your Own Key) and routes requests accordingly.

**Detection Logic** (from `litellm_api.py`):

```python
# 1. Check if user has OpenRouter BYOK (universal proxy)
if 'openrouter' in user_keys:
    using_byok = True
    user_byok_key = user_keys['openrouter']
    detected_provider = 'openrouter'
    # Uses user's OpenRouter key for ALL models

# 2. Otherwise, check for provider-specific BYOK
else:
    detected_provider = detect_provider_from_model(request.model)
    if detected_provider in user_keys:
        using_byok = True
        user_byok_key = user_keys[detected_provider]
        # Uses user's provider-specific key

# 3. No BYOK - use platform key and charge credits
else:
    using_byok = False
    # Uses platform OpenRouter key, deducts credits
```

### Provider Detection

Model names are automatically mapped to providers:

```python
# Model prefix → Provider mapping
PROVIDER_CONFIGS = {
    'openai': {
        'model_prefixes': ['openai/', 'gpt-', 'o1-', 'o3-']
    },
    'anthropic': {
        'model_prefixes': ['anthropic/', 'claude-']
    },
    'openrouter': {
        'model_prefixes': []  # Accepts all models
    },
    'google': {
        'model_prefixes': ['google/', 'gemini-']
    }
}

# Examples:
# "gpt-4" → OpenAI
# "openai/gpt-4" → OpenAI
# "claude-3.5-sonnet" → Anthropic
# "anthropic/claude-3-opus" → Anthropic
# "gemini-pro" → Google
# "anything-else" → OpenRouter (default)
```

### User Configures BYOK

Users can configure their own API keys at:
https://your-domain.com/admin/account/api-keys

**Supported Providers**:
- OpenRouter (recommended - supports 100+ models)
- OpenAI (GPT-4, GPT-4o, DALL-E, etc.)
- Anthropic (Claude 3.5 Sonnet, Opus, etc.)
- Google AI (Gemini 2.0, Gemini 1.5 Pro, etc.)

**Benefits**:
- ✅ **No credit charges** - User pays provider directly
- ✅ **Unlimited usage** - No platform quotas
- ✅ **Same API** - Your app code doesn't change
- ✅ **Transparent billing** - User sees costs on provider dashboard

### Response Metadata

Every response includes `_metadata` with routing info:

```json
{
  "choices": [...],
  "usage": {...},
  "_metadata": {
    "provider_used": "openai/gpt-4",
    "cost_incurred": 0.0015,          // Credits deducted (0 if BYOK)
    "credits_remaining": 9998.5,       // User's remaining credits
    "using_byok": false,               // True if user's key was used
    "byok_provider": null              // Provider name if BYOK (e.g., "openrouter")
  }
}
```

**Use this to**:
- Display credit balance to users
- Show "Using your OpenRouter key" indicator
- Track when users should top up credits
- Optimize costs by recommending BYOK

---

## Error Handling

### Common Errors

#### 1. Authentication Errors (401)

```json
{
  "detail": "Authorization header required"
}
```

**Causes**:
- Missing `Authorization` header
- Invalid service key
- Expired user API key

**Solution**:
```typescript
// Always include Authorization header
const response = await fetch(API_URL + '/v1/chat/completions', {
  headers: {
    'Authorization': `Bearer ${SERVICE_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(requestBody)
});

if (response.status === 401) {
  console.error('Authentication failed - check service key');
  // Redirect to login or show error
}
```

#### 2. Insufficient Credits (402)

```json
{
  "detail": "Insufficient credits. Balance: 5.0, Estimated cost: 10.5"
}
```

**Causes**:
- User has run out of platform credits
- No BYOK configured

**Solution**:
```typescript
try {
  const completion = await openai.chat.completions.create({...});
} catch (error) {
  if (error.status === 402) {
    // Show "Top up credits" or "Add BYOK" prompt
    showCreditTopUpPrompt(error.message);
  }
}
```

#### 3. Rate Limit Exceeded (429)

```json
{
  "detail": "Monthly spending cap exceeded"
}
```

**Causes**:
- User hit monthly quota
- Tier limits reached

**Solution**:
```typescript
if (error.status === 429) {
  showUpgradePrompt('You've reached your monthly limit. Upgrade tier or add BYOK.');
}
```

#### 4. Provider Errors (503)

```json
{
  "detail": "No LLM providers configured. Please configure OpenRouter in Platform Settings."
}
```

**Causes**:
- Platform provider not configured
- Provider API down

**Solution**: Contact UC-Cloud admin team.

### Error Handling Best Practices

```typescript
// Comprehensive error handler
async function callLLM(messages: Message[], userEmail: string) {
  try {
    const completion = await openai.chat.completions.create({
      model: 'openai/gpt-4',
      messages,
      user: userEmail
    });

    return completion;

  } catch (error: any) {
    // Log error
    console.error('LLM request failed:', error);

    // Handle specific errors
    switch (error.status) {
      case 401:
        throw new Error('Authentication failed. Please check your configuration.');

      case 402:
        throw new Error('Insufficient credits. Please top up or configure BYOK.');

      case 429:
        throw new Error('Rate limit exceeded. Please upgrade your tier or wait.');

      case 500:
        throw new Error('LLM service error. Please try again later.');

      case 503:
        throw new Error('LLM provider unavailable. Please contact support.');

      default:
        throw new Error(`Unexpected error: ${error.message}`);
    }
  }
}
```

---

## Best Practices

### 1. Always Pass User Identifier

**Critical** for service keys:

```typescript
// ✅ CORRECT
const completion = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [...],
  user: userEmail  // Or user.sub from Keycloak
});

// ❌ WRONG - BYOK won't work, billing will fail
const completion = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [...]
  // Missing user field!
});
```

### 2. Handle Streaming Properly

```typescript
// Streaming responses
const stream = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [...],
  user: userEmail,
  stream: true
});

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content;
  if (content) {
    displayChunk(content);
  }
}
```

### 3. Show BYOK Status to Users

```typescript
// After completion
const completion = await openai.chat.completions.create({...});

if (completion._metadata?.using_byok) {
  showIndicator('🔑 Using your OpenRouter key');
} else {
  showIndicator(`💳 ${completion._metadata?.credits_remaining} credits remaining`);
}
```

### 4. Cache Model List

```typescript
// Cache available models (they don't change often)
let cachedModels: Model[] | null = null;
let cacheTimestamp = 0;
const CACHE_TTL = 60 * 60 * 1000; // 1 hour

async function getAvailableModels(): Promise<Model[]> {
  const now = Date.now();

  if (cachedModels && (now - cacheTimestamp) < CACHE_TTL) {
    return cachedModels;
  }

  const response = await fetch(API_URL + '/v1/models', {
    headers: { 'Authorization': `Bearer ${SERVICE_KEY}` }
  });

  cachedModels = (await response.json()).data;
  cacheTimestamp = now;

  return cachedModels;
}
```

### 5. Implement Retry Logic

```typescript
// Exponential backoff for transient errors
async function callLLMWithRetry(
  messages: Message[],
  userEmail: string,
  maxRetries = 3
) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await openai.chat.completions.create({
        model: 'gpt-4',
        messages,
        user: userEmail
      });
    } catch (error: any) {
      // Don't retry auth/credit errors
      if ([401, 402, 429].includes(error.status)) {
        throw error;
      }

      // Retry on 500/503
      if ([500, 503].includes(error.status) && i < maxRetries - 1) {
        const delay = Math.pow(2, i) * 1000; // 1s, 2s, 4s
        await new Promise(resolve => setTimeout(resolve, delay));
        continue;
      }

      throw error;
    }
  }
}
```

### 6. Add Request Metadata

```typescript
// Include metadata for better tracking
const completion = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [...],
  user: userEmail,
  metadata: {
    app: 'bolt-diy',
    feature: 'code_generation',
    user_id: user.sub,
    session_id: sessionId,
    request_id: generateRequestId()
  }
});
```

### 7. Monitor Usage

```typescript
// Periodically check usage stats
async function checkUsage(userEmail: string) {
  const response = await fetch(API_URL + '/v1/usage?days=30', {
    headers: { 'Authorization': `Bearer ${SERVICE_KEY}` }
  });

  const usage = await response.json();

  // Warn user if approaching limits
  if (usage.total_cost > 80) { // 80% of $100 tier
    showWarning('You've used 80% of your monthly credits. Consider upgrading or adding BYOK.');
  }

  return usage;
}
```

---

## Testing Guide

### 1. Local Testing with Service Key

```bash
# Test chat completion
curl -X POST https://your-domain.com/api/v1/llm/v1/chat/completions \
  -H "Authorization: Bearer sk-bolt-diy-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "user": "test@example.com",
    "max_tokens": 50
  }'

# Test model listing
curl https://your-domain.com/api/v1/llm/v1/models \
  -H "Authorization: Bearer sk-bolt-diy-service-key-2025"

# Check credit balance
curl https://your-domain.com/api/v1/llm/v1/credits \
  -H "Authorization: Bearer sk-bolt-diy-service-key-2025"
```

### 2. Test User API Key

```bash
# Generate user API key first at:
# https://your-domain.com/admin/account/api-keys

# Test with user API key (no need to pass 'user' field)
curl -X POST https://your-domain.com/api/v1/llm/v1/chat/completions \
  -H "Authorization: Bearer uc_a1b2c3d4e5f6..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### 3. Test BYOK Detection

```bash
# 1. Configure BYOK at: https://your-domain.com/admin/account/api-keys
# 2. Add OpenRouter API key
# 3. Make request and check _metadata.using_byok

curl -X POST https://your-domain.com/api/v1/llm/v1/chat/completions \
  -H "Authorization: Bearer sk-bolt-diy-service-key-2025" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Test"}],
    "user": "user-with-byok@example.com"
  }' | jq '._metadata.using_byok'

# Should return: true (if BYOK configured)
# Should return: false (if no BYOK, using platform credits)
```

### 4. Integration Test Script (Node.js)

```typescript
// test-integration.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  baseURL: 'https://your-domain.com/api/v1/llm',
  apiKey: 'sk-bolt-diy-service-key-2025'
});

async function runTests() {
  console.log('Running UC-Cloud integration tests...\n');

  // Test 1: Chat completion
  console.log('Test 1: Chat completion');
  try {
    const completion = await openai.chat.completions.create({
      model: 'openai/gpt-4',
      messages: [{ role: 'user', content: 'Say "test passed"' }],
      user: 'test@example.com',
      max_tokens: 10
    });

    console.log('✅ Chat completion successful');
    console.log('Response:', completion.choices[0].message.content);
    console.log('Credits remaining:', completion._metadata?.credits_remaining);
    console.log('Using BYOK:', completion._metadata?.using_byok);
  } catch (error) {
    console.error('❌ Chat completion failed:', error);
  }

  console.log('\n---\n');

  // Test 2: Model listing
  console.log('Test 2: List models');
  try {
    const models = await openai.models.list();
    console.log('✅ Model listing successful');
    console.log(`Found ${models.data.length} models`);
  } catch (error) {
    console.error('❌ Model listing failed:', error);
  }

  console.log('\n---\n');

  // Test 3: Streaming
  console.log('Test 3: Streaming response');
  try {
    const stream = await openai.chat.completions.create({
      model: 'openai/gpt-4',
      messages: [{ role: 'user', content: 'Count to 5' }],
      user: 'test@example.com',
      stream: true,
      max_tokens: 50
    });

    process.stdout.write('Stream: ');
    for await (const chunk of stream) {
      const content = chunk.choices[0]?.delta?.content || '';
      process.stdout.write(content);
    }
    console.log('\n✅ Streaming successful');
  } catch (error) {
    console.error('❌ Streaming failed:', error);
  }
}

runTests();
```

### 5. Verify Health

```bash
# Check system health
curl https://your-domain.com/api/v1/llm/v1/health

# Expected response:
# {
#   "status": "healthy",
#   "litellm_proxy": "up",
#   "timestamp": "2025-11-04T12:00:00Z"
# }
```

---

## FAQ

### Q: Do I need to manage API keys for each provider?

**A**: No! That's the beauty of UC-Cloud. You use **one service key** for your app, and the platform:
- Automatically detects if the user has BYOK configured
- Routes to the appropriate provider (user's key or platform key)
- Handles billing transparently

### Q: What happens if a user runs out of credits?

**A**: The API returns a `402 Payment Required` error with the message:
```
"Insufficient credits. Balance: 5.0, Estimated cost: 10.5"
```

Your app should:
1. Catch this error
2. Show a prompt to "Top up credits" or "Add BYOK"
3. Link to: `https://your-domain.com/admin/subscription/plan`

### Q: How do I know if a user is using BYOK?

**A**: Check the `_metadata` field in the response:
```json
{
  "_metadata": {
    "using_byok": true,
    "byok_provider": "openrouter",
    "cost_incurred": 0.0  // No credit charge for BYOK
  }
}
```

You can show a "🔑 Using your OpenRouter key" indicator in your UI.

### Q: Can users switch between BYOK and platform credits?

**A**: Yes! Users can:
1. Add/remove BYOK keys at any time
2. Platform automatically uses BYOK when available
3. Falls back to platform credits if BYOK removed

### Q: What models are available?

**A**: 100+ models via OpenRouter, including:
- OpenAI: `gpt-4`, `gpt-4o`, `gpt-4o-mini`, `o1-preview`
- Anthropic: `claude-3.5-sonnet`, `claude-3-opus`
- Google: `gemini-2.0-flash`, `gemini-1.5-pro`
- Meta: `llama-3.1-405b`, `llama-3.3-70b`
- Many more...

Fetch the full list: `GET /v1/models`

### Q: How are credits calculated?

**A**: Credits are based on token usage:
- 1 credit ≈ $0.001 (one-tenth of a cent)
- Example: 1000 tokens with gpt-4 (~$0.03) = 30 credits

Exact pricing varies by model. Check `_metadata.cost_incurred` in responses.

### Q: Can I use this for production apps?

**A**: Yes! UC-Cloud is production-ready with:
- ✅ SSL/TLS encryption
- ✅ 99.9% uptime SLA
- ✅ Rate limiting and quota management
- ✅ Comprehensive error handling
- ✅ Usage analytics and monitoring

### Q: How do I get a service key for my app?

**A**: Contact the UC-Cloud admin team with:
1. Your app name
2. App description
3. Expected usage volume
4. Integration timeline

They'll provision a service key like: `sk-yourapp-service-key-2025`

### Q: Is there a rate limit?

**A**: Yes, per user tier:
- **Trial**: 100 requests/day
- **Starter**: 1,000 requests/month
- **Professional**: 10,000 requests/month
- **Enterprise**: Unlimited
- **BYOK**: No platform limits (subject to provider limits)

### Q: Can I use this with LangChain/LlamaIndex?

**A**: Yes! Since it's OpenAI-compatible:

```python
# LangChain
from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(
    base_url="https://your-domain.com/api/v1/llm",
    api_key="sk-yourapp-service-key-2025",
    model="openai/gpt-4"
)

# LlamaIndex
from llama_index.llms import OpenAI

llm = OpenAI(
    api_base="https://your-domain.com/api/v1/llm",
    api_key="sk-yourapp-service-key-2025",
    model="openai/gpt-4"
)
```

### Q: What about data privacy?

**A**:
- All requests are encrypted (HTTPS/TLS)
- User data not logged or stored by default
- BYOK requests go directly to user's provider
- Compliant with GDPR and SOC 2 standards

---

## Support & Resources

### Documentation
- **Main Docs**: https://docs.your-domain.com
- **API Reference**: https://docs.your-domain.com/api
- **Ops-Center Guide**: https://docs.your-domain.com/ops-center

### Developer Resources
- **GitHub**: https://github.com/Unicorn-Commander/UC-Cloud
- **Sample Apps**: https://github.com/Unicorn-Commander/examples
- **Discord Community**: https://discord.gg/unicorncommander

### Support
- **Email**: support@magicunicorn.tech
- **Status Page**: https://status.your-domain.com
- **Issue Tracker**: https://github.com/Unicorn-Commander/UC-Cloud/issues

### Contact
- **Organization**: Magic Unicorn Unconventional Technology & Stuff Inc
- **Website**: https://your-domain.com
- **License**: MIT

---

**Happy Building!** 🦄✨

If you have questions or need help integrating your app, reach out to the UC-Cloud team.
