# Authentication & API Metering Flow - Complete Guide

**Last Updated**: October 30, 2025
**Author**: Claude Code
**Version**: 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Phase 1: User Signup & Authentication](#phase-1-user-signup--authentication)
3. [Phase 2: Session & JWT Token Generation](#phase-2-session--jwt-token-generation)
4. [Phase 3: Automatic Token Usage Across Apps](#phase-3-automatic-token-usage-across-apps)
5. [Phase 4: API Call Flow with Metering](#phase-4-api-call-flow-with-metering)
6. [Phase 5: OpenRouter Integration](#phase-5-openrouter-integration)
7. [Phase 6: Usage Tracking & Response](#phase-6-usage-tracking--response)
8. [Database Schema](#database-schema)
9. [OpenRouter-Specific Features](#openrouter-specific-features)
10. [Summary](#summary)

---

## Overview

This document explains the complete end-to-end flow of authentication and API metering in the UC-Cloud ecosystem, with special attention to OpenRouter integration. It covers:

- How users authenticate via Keycloak SSO
- How JWT tokens are generated and shared across apps
- How API calls are metered and billed
- How OpenRouter serves as a universal LLM proxy
- How BYOK (Bring Your Own Key) works

**Key Services**:
- **Keycloak** - Identity provider (SSO)
- **Ops-Center** - API gateway and billing
- **OpenRouter** - Universal LLM proxy (200+ models)
- **PostgreSQL** - User data, API keys, transactions
- **Apps** - Open-WebUI, Brigade, Bolt.DIY, Center-Deep

---

## Phase 1: User Signup & Authentication

### User Registration Flow

```
User visits: https://unicorncommander.ai
   │
   ├── Option A: Email/Password (Keycloak local account)
   │   └── Creates account in Keycloak uchub realm
   │
   ├── Option B: Google OAuth (via Keycloak)
   │   └── Redirects to Google → Returns to Keycloak
   │
   ├── Option C: GitHub OAuth (via Keycloak)
   │   └── Redirects to GitHub → Returns to Keycloak
   │
   └── Option D: Microsoft OAuth (via Keycloak)
       └── Redirects to Microsoft → Returns to Keycloak

Result: User created in Keycloak with UUID
Example: 7a6bfd31-0120-4a30-9e21-0fc3b8006579
```

### What Happens Behind the Scenes

1. **User clicks "Sign Up"** on Ops-Center landing page
2. **Redirected to Keycloak** login page at `auth.unicorncommander.ai`
3. **User chooses authentication method**:
   - Email/Password: Keycloak validates and stores credentials
   - OAuth (Google/GitHub/Microsoft): Keycloak initiates OAuth flow
4. **OAuth flow** (if applicable):
   - Keycloak redirects to provider (e.g., Google)
   - User authenticates with provider
   - Provider returns authorization code to Keycloak
   - Keycloak exchanges code for user profile
5. **User created in Keycloak**:
   - UUID assigned (used as `user_id` throughout system)
   - Email stored
   - OAuth provider linked (if applicable)
6. **User attributes initialized**:
   - `subscription_tier`: "trial"
   - `subscription_status`: "active"
   - `api_calls_limit`: 100
   - `api_calls_used`: 0
   - `credits_remaining`: 100 (trial credits)

---

## Phase 2: Session & JWT Token Generation

### Keycloak Token Structure

After successful login, Keycloak generates **three tokens**:

#### 1. ID Token (JWT) - User Identity

Contains user information for the client application:

```json
{
  "sub": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "email": "admin@example.com",
  "preferred_username": "aaron",
  "given_name": "Aaron",
  "family_name": "User",
  "realm_access": {
    "roles": ["admin", "default-roles-uchub"]
  },
  "email_verified": true,
  "iss": "https://auth.unicorncommander.ai/realms/uchub",
  "aud": "ops-center",
  "exp": 1730318400,
  "iat": 1730314800
}
```

#### 2. Access Token (JWT) - API Authorization

Used for authorizing API requests:

```json
{
  "sub": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "scope": "openid email profile",
  "client_id": "ops-center",
  "realm_access": {
    "roles": ["admin"]
  },
  "resource_access": {
    "ops-center": {
      "roles": ["user", "admin"]
    }
  },
  "exp": 1730318400,
  "iat": 1730314800,
  "iss": "https://auth.unicorncommander.ai/realms/uchub",
  "aud": ["ops-center", "account"]
}
```

**Expiration**: 1 hour (configurable in Keycloak)

#### 3. Refresh Token - Token Renewal

Long-lived token used to obtain new access tokens without re-login:

```json
{
  "sub": "7a6bfd31-0120-4a30-9e21-0fc3b8006579",
  "session_state": "abc123...",
  "scope": "openid email profile",
  "exp": 1732906800,
  "iat": 1730314800
}
```

**Expiration**: 30 days (configurable in Keycloak)

### Token Storage

Tokens are stored in two locations:

1. **Browser Cookies** (Ops-Center, Brigade, Center-Deep):
   ```
   session_token=<uuid>
   Domain: .unicorncommander.ai  (note the leading dot!)
   Secure: true
   HttpOnly: true
   SameSite: Lax
   Max-Age: 86400 (24 hours)
   ```

2. **localStorage** (SPAs like Bolt.DIY):
   ```javascript
   localStorage.setItem('authToken', access_token);
   localStorage.setItem('refreshToken', refresh_token);
   localStorage.setItem('idToken', id_token);
   ```

---

## Phase 3: Automatic Token Usage Across Apps

### Cross-Domain Authentication with Cookies

**The Magic of Cookie Domain: `.unicorncommander.ai`**

When Ops-Center sets a cookie with domain `.unicorncommander.ai` (note the leading dot), the browser **automatically sends this cookie to ALL subdomains**:

```
Ops-Center Sets Cookie
   │
   │  Set-Cookie: session_token=abc123;
   │              Domain=.unicorncommander.ai;
   │              Secure; HttpOnly; SameSite=Lax
   │
   └── Browser automatically sends cookie to:
       ├── unicorncommander.ai ✅
       ├── brigade.unicorncommander.ai ✅
       ├── chat.unicorncommander.ai ✅ (Open-WebUI)
       ├── search.unicorncommander.ai ✅ (Center-Deep)
       └── api.unicorncommander.ai ✅ (Brigade API)

Result: Single Sign-On (SSO) across all subdomains!
```

### Apps on Subdomains (Automatic Authentication)

These apps receive the session cookie automatically:

| App | URL | Authentication Method |
|-----|-----|----------------------|
| Ops-Center | https://unicorncommander.ai | Session cookie (auto) |
| Brigade | https://brigade.unicorncommander.ai | Session cookie (auto) |
| Brigade API | https://api.brigade.unicorncommander.ai | Session cookie (auto) |
| Open-WebUI | https://chat.unicorncommander.ai | Session cookie (auto) |
| Center-Deep | https://search.unicorncommander.ai | Session cookie (auto) |

**How it works**:
1. User logs in to Ops-Center once
2. Cookie is set for `.unicorncommander.ai`
3. User visits `brigade.unicorncommander.ai`
4. Browser automatically sends the cookie
5. Brigade validates the session with Keycloak
6. User is authenticated without re-login!

### Apps NOT on Subdomains (API Key Required)

For apps hosted on different domains or localhost, users must generate API keys:

| App | Deployment | Authentication Method |
|-----|-----------|----------------------|
| Bolt.DIY | localhost:5173 or different domain | API key (manual) |
| Presenton | localhost:3000 or different domain | API key (manual) |
| External integrations | Any domain | API key (manual) |

**How to generate API key**:

1. User logs in to Ops-Center
2. Navigate to `/admin/account/api-keys`
3. Click "Generate API Key"
4. Copy the key (shown only once): `uc_1234567890abcdef...`
5. Paste into app settings

**How app uses API key**:

```javascript
// Frontend (Bolt.DIY, Presenton, etc.)
const API_KEY = 'uc_1234567890abcdef...';

fetch('https://unicorncommander.ai/api/v1/llm/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'openai/gpt-4o',
    messages: [{ role: 'user', content: 'Hello' }]
  })
});
```

---

## Phase 4: API Call Flow with Metering

### Complete Request Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  User Makes LLM API Call                                         │
└─────────────────────────────────────────────────────────────────┘

Frontend (Open-WebUI, Bolt.DIY, Brigade, etc.)
   │
   │  POST https://unicorncommander.ai/api/v1/llm/chat/completions
   │  Headers:
   │    Authorization: Bearer <session-token OR api-key>
   │    Content-Type: application/json
   │  Body:
   │    {
   │      "model": "openai/gpt-4o",
   │      "messages": [{"role": "user", "content": "Hello"}],
   │      "temperature": 0.7,
   │      "max_tokens": 1000
   │    }
   │
   ▼
Ops-Center Backend (backend/litellm_api.py)
   │
   ├── STEP 1: Authentication [lines 397-443]
   │   Function: get_user_id(authorization: str)
   │   │
   │   ├── Extract token from Authorization header
   │   │   Token format: "Bearer <token>"
   │   │
   │   ├── Check if token starts with "uc_" (API key)
   │   │   └── api_key_manager.validate_api_key(token)
   │   │       ├── Extract prefix: "uc_1234"
   │   │       ├── Query database for matching prefix
   │   │       ├── bcrypt verify against stored hash
   │   │       └── Return: {"user_id": "...", "permissions": [...]}
   │   │
   │   └── Otherwise: Validate JWT token
   │       └── api_key_manager.validate_jwt_token(token)
   │           ├── jwt.decode(token, secret, algorithm='HS256')
   │           ├── Check expiration
   │           └── Return: {"user_id": "...", "permissions": [...]}
   │
   ├── STEP 2: Get User Tier & Credits [lines 503-506]
   │   Function: credit_system.get_user_tier(user_id)
   │   │
   │   └── Query Keycloak user attributes:
   │       - subscription_tier: "professional"
   │       - subscription_status: "active"
   │       - api_calls_limit: 10,000
   │       - api_calls_used: 247
   │       - credits_remaining: 9,999.98
   │
   ├── STEP 3: Check BYOK (Bring Your Own Key) [lines 509-530]
   │   Function: byok_manager.get_all_user_keys(user_id)
   │   │
   │   ├── Query user_provider_keys table:
   │   │   SELECT provider, api_key_encrypted, enabled
   │   │   FROM user_provider_keys
   │   │   WHERE user_id = '...' AND enabled = TRUE
   │   │
   │   ├── Decrypt keys with Fernet cipher
   │   │   └── Returns: {'openrouter': 'sk-or-v1-...', 'openai': 'sk-...'}
   │   │
   │   ├── If user has OpenRouter BYOK:
   │   │   using_byok = True
   │   │   user_byok_key = 'sk-or-v1-...'
   │   │   detected_provider = 'openrouter'
   │   │   └── User will pay OpenRouter directly (no credit charge)
   │   │
   │   └── If no BYOK:
   │       using_byok = False
   │       └── Will use system OpenRouter key (charge credits)
   │
   ├── STEP 4: Estimate Cost & Check Credits [lines 532-560]
   │   │
   │   ├── Estimate tokens from message content
   │   │   estimated_tokens = sum(len(msg.content.split()) * 1.5)
   │   │   Example: "Hello, how are you?" → 4 words * 1.5 = 6 tokens
   │   │
   │   ├── Calculate estimated cost
   │   │   cost = calculate_cost(
   │   │     tokens=6,
   │   │     model='openai/gpt-4o',
   │   │     power_level='balanced',
   │   │     user_tier='professional'
   │   │   )
   │   │   Example: 0.01 credits (rough estimate)
   │   │
   │   ├── Check credit balance (skip if using BYOK)
   │   │   current_balance = 9,999.98 credits
   │   │   if current_balance < estimated_cost:
   │   │      raise HTTPException(402, "Insufficient credits")
   │   │
   │   └── Check monthly cap
   │       monthly_spent = 1,247.32 credits
   │       monthly_cap = 50,000 credits
   │       if monthly_spent + estimated_cost > monthly_cap:
   │          raise HTTPException(429, "Monthly cap exceeded")
   │
   └── STEP 5: Route to Provider (OpenRouter)
       [lines 562-668]
       └── See Phase 5 below
```

### Authentication Code Reference

**File**: `backend/litellm_api.py`

```python
async def get_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user ID from authorization header

    Supports two authentication methods:
    1. API Key: Bearer uc_<hex-key>
    2. JWT Token: Bearer <jwt-token>
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    if not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="Invalid authorization format")

    # Extract token
    token = authorization[7:]  # Remove "Bearer "

    # Try API key validation first (format: uc_<hex>)
    if token.startswith('uc_'):
        from api_key_manager import get_api_key_manager
        manager = get_api_key_manager()
        user_info = await manager.validate_api_key(token)

        if user_info:
            return user_info['user_id']
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired API key")

    # Try JWT token validation
    try:
        from api_key_manager import get_api_key_manager
        manager = get_api_key_manager()
        payload = manager.validate_jwt_token(token)

        if payload and 'user_id' in payload:
            return payload['user_id']
        else:
            raise HTTPException(status_code=401, detail="Invalid or expired JWT token")
    except Exception as e:
        logger.error(f"JWT validation error: {e}")
        raise HTTPException(status_code=401, detail="Token validation failed")
```

---

## Phase 5: OpenRouter Integration

### Why OpenRouter?

**OpenRouter is a universal LLM proxy** that provides access to 200+ models from multiple providers through a single API:

- **OpenAI**: GPT-4o, GPT-4o-mini, o1-preview, o1-mini, DALL-E 3
- **Anthropic**: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- **Google**: Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.0 Ultra
- **Meta**: Llama 3.3 70B, Llama 3.1 405B, Llama 3.1 70B
- **Mistral**: Mistral Large, Mistral Medium, Mixtral 8x22B
- **Cohere**: Command R+, Command R
- **Perplexity**: Sonar Large, Sonar Medium
- **50+ more providers**

**Benefits**:
1. **Single Integration** - One API for all models
2. **Unified Pricing** - Pay one provider, access all
3. **Automatic Failover** - If one provider is down, OpenRouter routes to another
4. **Competitive Pricing** - Often cheaper than going direct
5. **BYOK Support** - Users can bring their own OpenRouter key

### OpenRouter API Call Flow

#### Scenario A: Using BYOK (User's OpenRouter Key)

```
User has OpenRouter account with own API key
   │
   ├── User adds OpenRouter key in Ops-Center
   │   POST /api/v1/llm/byok/keys
   │   Body: {
   │     "provider": "openrouter",
   │     "api_key": "sk-or-v1-1234567890abcdef..."
   │   }
   │   └── Key encrypted with Fernet and stored in database
   │
   ├── User makes LLM request
   │   POST /api/v1/llm/chat/completions
   │   Headers: Authorization: Bearer <session-token>
   │   Body: {"model": "openai/gpt-4o", "messages": [...]}
   │
   ├── Ops-Center detects user has OpenRouter BYOK
   │   using_byok = True
   │   api_key = user's decrypted OpenRouter key
   │
   ├── Ops-Center calls OpenRouter with user's key
   │   POST https://openrouter.ai/api/v1/chat/completions
   │   Headers:
   │     Authorization: Bearer sk-or-v1-1234567890abcdef...
   │     HTTP-Referer: https://unicorncommander.ai
   │     X-Title: UC-1 Pro Ops Center
   │   Body: <user's request>
   │
   ├── OpenRouter charges user's account
   │   User's OpenRouter balance: $10.00 → $9.98 (-$0.02)
   │
   └── Ops-Center returns response WITHOUT credit charge
       Response: {
         ...
         '_metadata': {
           'using_byok': true,
           'byok_provider': 'openrouter',
           'cost_incurred': 0.0,  // No credit charge!
           'credits_remaining': 9999.98  // Unchanged
         }
       }
```

**Code Reference**: `backend/litellm_api.py` [lines 583-599]

```python
if using_byok:
    # User is using their own API key
    logger.info(f"Using BYOK for {user_id} with provider {detected_provider}")

    # Get provider config
    provider_config = PROVIDER_CONFIGS.get(detected_provider, PROVIDER_CONFIGS['openrouter'])
    base_url = provider_config['base_url']  # https://openrouter.ai/api/v1
    api_key = user_byok_key
    provider_name = detected_provider.title()

    # Build headers
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        **provider_config['default_headers']  # HTTP-Referer, X-Title
    }
```

#### Scenario B: Using System Key (Default - Charge Credits)

```
User does NOT have OpenRouter key (or has it disabled)
   │
   ├── User makes LLM request
   │   POST /api/v1/llm/chat/completions
   │   Headers: Authorization: Bearer <session-token>
   │   Body: {"model": "anthropic/claude-3.5-sonnet", "messages": [...]}
   │
   ├── Ops-Center detects no BYOK
   │   using_byok = False
   │   └── Will use system OpenRouter key and charge credits
   │
   ├── Ops-Center retrieves system OpenRouter key
   │   Query: SELECT id, api_key_encrypted FROM llm_providers
   │          WHERE enabled = true AND type = 'openrouter'
   │   └── Decrypt system key with SystemKeyManager
   │       api_key = 'sk-or-v1-system-key...'
   │
   ├── Ops-Center calls OpenRouter with system key
   │   POST https://openrouter.ai/api/v1/chat/completions
   │   Headers:
   │     Authorization: Bearer sk-or-v1-system-key...
   │     HTTP-Referer: https://unicorncommander.ai
   │     X-Title: UC-1 Pro Ops Center
   │   Body: <user's request>
   │
   ├── OpenRouter charges system account
   │   System OpenRouter balance: $100.00 → $99.50 (-$0.50)
   │   (System pays OpenRouter)
   │
   ├── Ops-Center calculates user credit cost
   │   OpenRouter cost: $0.50
   │   User credit cost: $0.50 * 1.0 = 0.50 credits
   │   (1 credit = $1.00 for professional tier)
   │
   ├── Ops-Center debits user credits
   │   credit_system.debit_credits(
   │     user_id=user_id,
   │     amount=0.50,
   │     metadata={
   │       'provider': 'openrouter',
   │       'model': 'anthropic/claude-3.5-sonnet',
   │       'tokens_used': 500,
   │       'cost': 0.50
   │     }
   │   )
   │   User credits: 10,000 → 9,999.50 (-0.50)
   │
   └── Ops-Center returns response with cost
       Response: {
         ...
         '_metadata': {
           'using_byok': false,
           'cost_incurred': 0.50,
           'credits_remaining': 9999.50,
           'transaction_id': 'abc123...'
         }
       }
```

**Code Reference**: `backend/litellm_api.py` [lines 600-650]

```python
else:
    # Using system OpenRouter key (charge credits)
    logger.info(f"Using system OpenRouter key for {user_id}")

    # Get system key manager
    system_key_manager = SystemKeyManager(credit_system.db_pool, BYOK_ENCRYPTION_KEY)

    # Get provider info from database
    async with credit_system.db_pool.acquire() as conn:
        provider = await conn.fetchrow("""
            SELECT id, name, type, api_key_encrypted, config
            FROM llm_providers
            WHERE enabled = true AND type = 'openrouter'
            ORDER BY priority DESC
            LIMIT 1
        """)

        if not provider:
            raise HTTPException(
                status_code=503,
                detail="No LLM providers configured"
            )

        # Get system API key (prefer database over environment)
        api_key = await system_key_manager.get_system_key(provider['id'])
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="No API key configured for system provider"
            )

    # Build headers for OpenRouter
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://unicorncommander.ai",
        "X-Title": "UC-1 Pro Ops Center"
    }
```

### OpenRouter Required Headers

OpenRouter requires two custom headers for tracking and attribution:

```python
headers = {
    'Authorization': f'Bearer {api_key}',
    'HTTP-Referer': 'https://unicorncommander.ai',  # REQUIRED
    'X-Title': 'UC-1 Pro Ops Center'  # REQUIRED
}
```

**Why required?**:
- `HTTP-Referer`: OpenRouter uses this for analytics and attribution
- `X-Title`: Displayed in OpenRouter dashboard for tracking

**What happens if omitted?**:
- OpenRouter may reject the request with 400 Bad Request
- Analytics won't work properly

---

## Phase 6: Usage Tracking & Response

### After OpenRouter Responds

```
OpenRouter returns response
   │
   │  Response: {
   │    "id": "chatcmpl-abc123",
   │    "model": "openai/gpt-4o-mini",
   │    "choices": [{
   │      "message": {
   │        "role": "assistant",
   │        "content": "Hello! How can I help you?"
   │      }
   │    }],
   │    "usage": {
   │      "prompt_tokens": 21,
   │      "completion_tokens": 26,
   │      "total_tokens": 47
   │    }
   │  }
   │
   ▼
Ops-Center processes response [lines 669-741]
   │
   ├── Extract actual usage
   │   usage = response['usage']
   │   tokens_used = usage['total_tokens']  // 47
   │   model = response['model']  // "openai/gpt-4o-mini"
   │
   ├── Calculate actual cost (more accurate than estimate)
   │   actual_cost = credit_system.calculate_cost(
   │     tokens_used=47,
   │     model='openai/gpt-4o-mini',
   │     power_level='balanced',
   │     user_tier='professional'
   │   )
   │   Result: $0.000002 → 0.02 credits
   │   (GPT-4o-mini: $0.15 per 1M input tokens, $0.60 per 1M output)
   │
   ├── Debit credits (if NOT using BYOK)
   │   if using_byok:
   │       # Skip credit charge - user paid provider directly
   │       new_balance = await credit_system.get_user_credits(user_id)
   │       transaction_id = None
   │       actual_cost = 0.0
   │   else:
   │       # Charge credits
   │       new_balance, transaction_id = await credit_system.debit_credits(
   │           user_id=user_id,
   │           amount=0.02,
   │           metadata={
   │               'provider': 'openrouter',
   │               'model': 'openai/gpt-4o-mini',
   │               'tokens_used': 47,
   │               'power_level': 'balanced',
   │               'cost': 0.02
   │           }
   │       )
   │       Result: 10,000 - 0.02 = 9,999.98 credits
   │
   ├── Track usage event (Epic 1.8: Usage Metering)
   │   await usage_meter.track_usage(
   │       user_id=user_id,
   │       service='litellm',
   │       model='openai/gpt-4o-mini',
   │       tokens=47,
   │       cost=0.02,
   │       is_free=False,
   │       metadata={
   │           'provider': 'openrouter',
   │           'transaction_id': transaction_id,
   │           'power_level': 'balanced',
   │           'task_type': 'chat'
   │       }
   │   )
   │   └── Stored in usage_events table for analytics
   │
   └── Return response with metadata
       {
         'id': 'chatcmpl-abc123',
         'model': 'openai/gpt-4o-mini',
         'choices': [...],
         'usage': {
           'prompt_tokens': 21,
           'completion_tokens': 26,
           'total_tokens': 47
         },
         '_metadata': {
           'provider_used': 'openai/gpt-4o-mini',
           'cost_incurred': 0.02,
           'credits_remaining': 9999.98,
           'transaction_id': 'uuid-123',
           'power_level': 'balanced',
           'user_tier': 'professional',
           'using_byok': false,
           'byok_provider': null
         }
       }
```

### Usage Tracking Tables

**credit_transactions** - Financial records:
```sql
INSERT INTO credit_transactions (
    id, user_id, amount, balance_after, reason, metadata, created_at
) VALUES (
    'uuid-123',
    '7a6bfd31-0120-4a30-9e21-0fc3b8006579',
    -0.02,  -- Negative for debit
    9999.98,  -- New balance
    'inference',
    '{"provider":"openrouter","model":"openai/gpt-4o-mini","tokens":47}',
    NOW()
);
```

**usage_events** - Analytics records:
```sql
INSERT INTO usage_events (
    id, user_id, service, model, tokens, cost, metadata, created_at
) VALUES (
    'uuid-456',
    '7a6bfd31-0120-4a30-9e21-0fc3b8006579',
    'litellm',
    'openai/gpt-4o-mini',
    47,
    0.02,
    '{"provider":"openrouter","power_level":"balanced"}',
    NOW()
);
```

---

## Database Schema

### User Authentication & API Keys

```sql
-- User API Keys (for external apps like Bolt.DIY)
CREATE TABLE user_api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,  -- Keycloak user UUID
    key_name VARCHAR(255) NOT NULL,  -- "Bolt.DIY Production"
    key_hash TEXT NOT NULL,  -- bcrypt hashed: $2b$12$...
    key_prefix VARCHAR(20) NOT NULL,  -- "uc_1234" for quick lookup
    permissions JSONB DEFAULT '["llm:inference", "llm:models"]'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    last_used TIMESTAMP,
    expires_at TIMESTAMP,  -- NULL = never expires
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_user_api_keys_user_id ON user_api_keys(user_id);
CREATE INDEX idx_user_api_keys_prefix ON user_api_keys(key_prefix);
CREATE INDEX idx_user_api_keys_active ON user_api_keys(is_active, expires_at);
```

### BYOK (Bring Your Own Key)

```sql
-- User Provider Keys (BYOK - encrypted with Fernet)
CREATE TABLE user_provider_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- 'openrouter', 'openai', 'anthropic'
    api_key_encrypted TEXT NOT NULL,  -- Fernet encrypted
    enabled BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider)
);

CREATE INDEX idx_user_provider_keys_user_id ON user_provider_keys(user_id);
CREATE INDEX idx_user_provider_keys_enabled ON user_provider_keys(enabled);
```

### System Provider Keys (Admin-Configured)

```sql
-- LLM Providers (system-level configuration)
CREATE TABLE llm_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(50) NOT NULL UNIQUE,  -- 'openrouter'
    type VARCHAR(50) NOT NULL,  -- 'openrouter', 'openai', 'anthropic'
    api_key_encrypted TEXT,  -- Fernet encrypted system key
    api_key_source VARCHAR(20) DEFAULT 'environment',  -- 'database' or 'environment'
    api_key_updated_at TIMESTAMP,
    api_key_last_tested TIMESTAMP,
    api_key_test_status VARCHAR(20),  -- 'success', 'failed', 'not_tested'
    enabled BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 0,
    config JSONB DEFAULT '{}'::jsonb,  -- {"base_url": "...", "model_prefixes": [...]}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_llm_providers_enabled ON llm_providers(enabled, priority);
```

### Credit System

```sql
-- Credit Transactions (financial records)
CREATE TABLE credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 6) NOT NULL,  -- Positive = credit, Negative = debit
    balance_after DECIMAL(10, 6) NOT NULL,
    reason VARCHAR(50) NOT NULL,  -- 'inference', 'purchase', 'admin_adjustment', 'refund'
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id, created_at DESC);
CREATE INDEX idx_credit_transactions_reason ON credit_transactions(reason);
```

### Usage Metering (Analytics)

```sql
-- Usage Events (for analytics and dashboards)
CREATE TABLE usage_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    service VARCHAR(50) NOT NULL,  -- 'litellm', 'openwebui', 'brigade'
    model VARCHAR(100),  -- 'openai/gpt-4o-mini'
    tokens INTEGER,
    cost DECIMAL(10, 6),
    is_free BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_usage_events_user_id ON usage_events(user_id, created_at DESC);
CREATE INDEX idx_usage_events_model ON usage_events(model);
CREATE INDEX idx_usage_events_service ON usage_events(service);
```

---

## OpenRouter-Specific Features

### Provider Configuration

**File**: `backend/litellm_api.py` [lines 55-81]

```python
# Provider configurations for BYOK routing
PROVIDER_CONFIGS = {
    'openai': {
        'base_url': 'https://api.openai.com/v1',
        'model_prefixes': ['openai/', 'gpt-', 'o1-', 'o3-'],
        'default_headers': {}
    },
    'anthropic': {
        'base_url': 'https://api.anthropic.com/v1',
        'model_prefixes': ['anthropic/', 'claude-'],
        'default_headers': {
            'anthropic-version': '2023-06-01'
        }
    },
    'openrouter': {
        'base_url': 'https://openrouter.ai/api/v1',
        'model_prefixes': [],  # Accepts all models (universal proxy)
        'default_headers': {
            'HTTP-Referer': 'https://unicorncommander.ai',
            'X-Title': 'UC-1 Pro Ops Center'
        }
    },
    'google': {
        'base_url': 'https://generativelanguage.googleapis.com/v1beta',
        'model_prefixes': ['google/', 'gemini-'],
        'default_headers': {}
    }
}
```

### Model Detection

```python
def detect_provider_from_model(model_name: str) -> str:
    """
    Detect provider from model name

    Examples:
    - "openai/gpt-4" → "openai"
    - "claude-3-opus" → "anthropic"
    - "gemini-2.0-flash" → "google"
    - "llama-3.3-70b" → "openrouter" (default)

    Returns:
        Provider name (openai, anthropic, openrouter, google)
    """
    if not model_name:
        return 'openrouter'  # Default to OpenRouter

    model_lower = model_name.lower()

    # Check each provider's prefixes
    for provider, config in PROVIDER_CONFIGS.items():
        for prefix in config['model_prefixes']:
            if model_lower.startswith(prefix.lower()):
                return provider

    # Default to OpenRouter (handles all models)
    return 'openrouter'
```

### Available Models (200+)

OpenRouter provides access to models from:

- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4-turbo, o1-preview, o1-mini, DALL-E 3
- **Anthropic**: Claude 3.5 Sonnet (latest), Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **Google**: Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash, Gemini 1.0 Ultra
- **Meta**: Llama 3.3 70B, Llama 3.1 405B, Llama 3.1 70B, Llama 3.1 8B
- **Mistral**: Mistral Large 2, Mistral Small, Mixtral 8x22B, Mixtral 8x7B
- **Cohere**: Command R+, Command R
- **Perplexity**: Sonar Large, Sonar Medium
- **DeepSeek**: DeepSeek Chat, DeepSeek Coder
- **01.AI**: Yi 34B, Yi 6B
- **And 150+ more...**

### Why BYOK with OpenRouter is Powerful

```
User with OpenRouter BYOK gets:
   │
   ├── Access to ALL 200+ models
   ├── Direct billing to their OpenRouter account
   ├── No credit limits from Ops-Center
   ├── Lower latency (one less hop)
   └── OpenRouter's promotional credits (if new account)

System benefits:
   │
   ├── No cost to system (user pays directly)
   ├── Reduced OpenRouter API usage on system account
   └── Users can use models not enabled by system
```

---

## Summary

### Complete Flow Recap

```
┌─────────────────────────────────────────────────────────────────┐
│  End-to-End Flow                                                │
└─────────────────────────────────────────────────────────────────┘

1. User signs up → Keycloak creates account with UUID
2. User logs in → Keycloak issues JWT tokens (ID, access, refresh)
3. JWT stored in cookie (.unicorncommander.ai domain)
4. Cookie automatically sent to all subdomains
5. User makes LLM request → Ops-Center validates JWT or API key
6. Ops-Center checks:
   ├── User tier (professional = 10,000 API calls/month)
   ├── Credit balance (10,000 credits = $10,000 worth of usage)
   └── BYOK status (using own OpenRouter key?)
7. If BYOK:
   ├── Use user's OpenRouter key
   ├── OpenRouter charges user's account
   └── No credit deduction in Ops-Center
8. If no BYOK:
   ├── Use system OpenRouter key
   ├── OpenRouter charges system account
   └── Ops-Center debits user credits (1 credit ≈ $1)
9. OpenRouter routes to appropriate provider (OpenAI, Anthropic, etc.)
10. OpenRouter returns response → Ops-Center adds metadata
11. Ops-Center tracks usage in database (transactions + analytics)
12. Response returned to user with cost and balance info
```

### Apps That Work Automatically (SSO via Cookie)

| App | URL | Auth Method |
|-----|-----|-------------|
| Ops-Center | https://unicorncommander.ai | Session cookie ✅ |
| Brigade | https://brigade.unicorncommander.ai | Session cookie ✅ |
| Brigade API | https://api.brigade.unicorncommander.ai | Session cookie ✅ |
| Open-WebUI | https://chat.unicorncommander.ai | Session cookie ✅ |
| Center-Deep | https://search.unicorncommander.ai | Session cookie ✅ |

### Apps That Need API Keys (Different Domains)

| App | Deployment | Auth Method |
|-----|-----------|-------------|
| Bolt.DIY | localhost or different domain | API key (uc_...) |
| Presenton | localhost or different domain | API key (uc_...) |
| External integrations | Any domain | API key (uc_...) |

### Cost Structure

**System Account (Default)**:
- System pays OpenRouter directly
- System charges users credits
- 1 credit = $1.00 worth of API usage (for professional tier)
- Example: GPT-4o-mini request costs $0.02 → 0.02 credits

**BYOK (User Account)**:
- User pays OpenRouter directly
- No credit charge in Ops-Center
- User gets access to ALL OpenRouter models
- User can use OpenRouter promotional credits

### Key Files Reference

| File | Purpose |
|------|---------|
| `backend/litellm_api.py` | Main LLM API endpoint with metering |
| `backend/api_key_manager.py` | API key generation and validation |
| `backend/byok_manager.py` | User provider key management (BYOK) |
| `backend/litellm_credit_system.py` | Credit debit/credit logic |
| `backend/usage_metering.py` | Usage tracking for analytics |
| `.env.auth` | Configuration (BYOK_ENCRYPTION_KEY, etc.) |

### Important Environment Variables

```bash
# Keycloak SSO
KEYCLOAK_URL=http://uchub-keycloak:8080
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

# BYOK Encryption
BYOK_ENCRYPTION_KEY=<base64-fernet-key>  # For encrypting user API keys

# JWT Authentication
JWT_SECRET_KEY=<secret>  # For signing JWT tokens

# Database
POSTGRES_HOST=unicorn-postgresql
POSTGRES_DB=unicorn_db
```

---

## Frequently Asked Questions

### Q: What happens if user runs out of credits?

**A**: API requests return `402 Payment Required`. User must purchase more credits or add BYOK.

### Q: Can users use models not enabled by the system?

**A**: Yes, if they have BYOK. System OpenRouter key only works with enabled models.

### Q: How long do API keys last?

**A**: Default 90 days. Configurable per key. Can be revoked anytime.

### Q: How are JWT tokens refreshed?

**A**: Refresh tokens are used to get new access tokens without re-login. Handled automatically by Keycloak.

### Q: What if system OpenRouter key expires or runs out of credits?

**A**: All non-BYOK users will get `503 Service Unavailable`. Admin must add credits or update key.

### Q: Can users have multiple BYOK keys?

**A**: Yes, one per provider (OpenRouter, OpenAI, Anthropic, Google). System picks the right one based on model.

### Q: What's the difference between `user_api_keys` and `user_provider_keys`?

**A**:
- `user_api_keys`: API keys for authenticating users (uc_...) to Ops-Center
- `user_provider_keys`: User's LLM provider keys (OpenRouter, OpenAI, etc.) for BYOK

---

**Document Status**: ✅ Complete and Production-Ready
**Last Reviewed**: October 30, 2025
**Next Review**: When adding new providers or authentication methods
