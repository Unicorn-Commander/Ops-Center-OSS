# LiteLLM Credit System - Backend Implementation Complete

**Date**: October 20, 2025
**Developer**: Backend Developer #1
**Status**: ✅ COMPLETE - Ready for Database Integration

---

## Summary

Complete backend implementation for LiteLLM credit system with credit management, BYOK support, and OpenAI-compatible API endpoints.

---

## Deliverables

### 1. Core Credit Management (`litellm_credit_system.py`)

**File**: `/backend/litellm_credit_system.py`
**Lines**: 620+
**Features**:
- Credit balance tracking with Redis caching (60s TTL)
- Debit/credit transactions with PostgreSQL persistence
- Cost calculation with power level and tier-based pricing
- Transaction history with pagination
- Usage statistics and analytics
- Monthly spending cap enforcement
- Provider routing logic

**Key Classes**:
```python
class CreditSystem:
    async def get_user_credits(user_id: str) -> float
    async def debit_credits(user_id: str, amount: float, metadata: dict) -> Tuple[float, str]
    async def credit_credits(user_id: str, amount: float, reason: str) -> float
    async def get_credit_history(user_id: str, limit: int = 100) -> List[Dict]
    def calculate_cost(tokens_used: int, model: str, power_level: str, user_tier: str) -> float
    async def get_usage_stats(user_id: str, days: int = 30) -> Dict
    async def check_monthly_cap(user_id: str, amount: float) -> bool
```

---

### 2. BYOK Manager (`byok_manager.py`)

**File**: `/backend/byok_manager.py`
**Lines**: 350+
**Features**:
- Fernet symmetric encryption for API keys
- Secure key storage in PostgreSQL
- Provider-specific key validation
- Enable/disable provider keys
- Masked key display for security

**Key Classes**:
```python
class BYOKManager:
    async def store_user_api_key(user_id: str, provider: str, api_key: str, metadata: dict) -> str
    async def get_user_api_key(user_id: str, provider: str) -> Optional[str]
    async def delete_user_api_key(user_id: str, provider: str) -> bool
    async def list_user_providers(user_id: str) -> List[Dict]
    async def toggle_provider(user_id: str, provider: str, enabled: bool) -> bool
    async def get_all_user_keys(user_id: str) -> Dict[str, str]
    async def validate_api_key(user_id: str, provider: str, api_key: str) -> bool
```

**Supported Providers**:
- OpenAI (sk-... format)
- Anthropic (sk-ant-... format)
- OpenRouter (sk-or-... format)
- Together AI, Fireworks AI, DeepInfra
- Groq (gsk_... format)
- HuggingFace (hf_... format)

---

### 3. API Endpoints (`litellm_api.py`)

**File**: `/backend/litellm_api.py`
**Lines**: 720+
**Base Path**: `/api/v1/llm`

**Endpoints Implemented**:

#### Chat Completions
- `POST /chat/completions` - OpenAI-compatible chat with credit deduction
  - Pre-flight credit check
  - Monthly cap validation
  - Automatic provider routing
  - Usage tracking and metering
  - Stripe payment integration fallback

#### Credit Management
- `GET /credits` - Get current balance and tier
- `POST /credits/purchase` - Purchase credits via Stripe
- `GET /credits/history` - Transaction history with pagination

#### Models & Usage
- `GET /models` - List available models by tier
- `GET /usage` - Usage statistics and provider breakdown

#### BYOK
- `POST /byok/keys` - Add/update provider API key
- `GET /byok/keys` - List stored keys (masked)
- `DELETE /byok/keys/{provider}` - Delete provider key

#### System
- `GET /health` - Health check endpoint

---

### 4. Server Integration (`server.py`)

**Modified**: `/backend/server.py`
**Changes**:
1. Added import: `from litellm_api import router as litellm_router`
2. Registered router: `app.include_router(litellm_router)`
3. Startup initialization:
   - Created asyncpg database pool
   - Created Redis client
   - Initialized CreditSystem
   - Initialized BYOKManager
4. Shutdown cleanup:
   - Close database pool
   - Close Redis client

---

### 5. API Documentation (`LITELLM_CREDIT_API.md`)

**File**: `/backend/docs/LITELLM_CREDIT_API.md`
**Sections**:
- Overview and authentication
- Power levels (eco, balanced, precision)
- Complete endpoint reference with examples
- Request/response schemas
- Error codes and handling
- Pricing and cost calculation
- Database schema
- Environment variables
- Usage examples (Python, cURL, JavaScript)
- Rate limits by tier
- Changelog

---

## Power Levels

### Eco Mode
- **Cost**: 0.1x multiplier
- **Tokens**: 2,000 max
- **Providers**: Local, Groq, HuggingFace (free)
- **Use Case**: Budget-conscious, simple queries

### Balanced Mode (Default)
- **Cost**: 0.25x multiplier
- **Tokens**: 4,000 max
- **Providers**: Together, Fireworks, OpenRouter
- **Use Case**: General purpose

### Precision Mode
- **Cost**: 1.0x multiplier
- **Tokens**: 16,000 max
- **Providers**: Anthropic, OpenAI, Premium
- **Use Case**: High-quality, complex tasks

---

## Pricing Model

### Base Costs (per 1K tokens)

| Provider | Cost |
|----------|------|
| Local/Groq/HF | $0.000 |
| Together/Fireworks | $0.002 |
| DeepInfra | $0.003 |
| OpenRouter Mixtral | $0.003 |
| OpenRouter Claude 3.5 | $0.008 |
| OpenRouter GPT-4o | $0.010 |
| Anthropic/OpenAI | $0.015 |

### Tier Markup

| Tier | Markup |
|------|--------|
| Free | 0% (platform absorbs) |
| Starter | 40% |
| Professional | 60% |
| Enterprise | 80% |

### Cost Formula

```
final_cost = (tokens / 1000) × base_cost × power_multiplier × (1 + tier_markup)
```

---

## Database Requirements

**CRITICAL**: Database agent must create these tables:

### user_credits
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

### credit_transactions
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

CREATE INDEX idx_credit_transactions_user_id ON credit_transactions(user_id);
CREATE INDEX idx_credit_transactions_created_at ON credit_transactions(created_at);
CREATE INDEX idx_credit_transactions_type ON credit_transactions(transaction_type);
```

### user_provider_keys
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

CREATE INDEX idx_user_provider_keys_user_id ON user_provider_keys(user_id);
CREATE INDEX idx_user_provider_keys_provider ON user_provider_keys(provider);
```

---

## Environment Variables Required

**Add to `.env.auth`**:

```bash
# LiteLLM Proxy
LITELLM_PROXY_URL=http://unicorn-litellm-wilmer:4000
LITELLM_MASTER_KEY=<generated-key>

# Database (should already exist)
DATABASE_URL=postgresql://unicorn:unicorn@unicorn-postgresql:5432/unicorn_db

# Redis (should already exist)
REDIS_HOST=unicorn-redis
REDIS_PORT=6379

# Stripe (for credit purchases)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# BYOK Encryption (GENERATE THIS!)
BYOK_ENCRYPTION_KEY=<fernet-key>

# Generate encryption key:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Dependencies

**Add to `requirements.txt`**:
```
asyncpg>=0.29.0
redis>=5.0.0
cryptography>=41.0.0
stripe>=7.0.0
httpx>=0.25.0
```

---

## Testing Checklist

### Unit Tests Needed

- [ ] `test_credit_system.py`
  - Credit balance retrieval
  - Debit with insufficient funds
  - Credit addition
  - Cost calculation (all power levels)
  - Usage statistics
  - Monthly cap enforcement

- [ ] `test_byok_manager.py`
  - Key encryption/decryption
  - Key storage and retrieval
  - Key deletion
  - Provider validation
  - Enable/disable toggle

- [ ] `test_litellm_api.py`
  - Chat completion flow
  - Credit purchase
  - Transaction history
  - Model listing
  - BYOK endpoints

### Integration Tests Needed

- [ ] End-to-end chat completion with credit deduction
- [ ] Stripe payment integration
- [ ] LiteLLM proxy communication
- [ ] Database transaction rollback on errors
- [ ] Redis caching behavior

---

## Coordination with Other Agents

### Database Agent
**Required**:
- Create 3 database tables (schema provided above)
- Add indexes for performance
- Create initial user_credits entries for existing users

### Frontend Agent
**Provided**:
- Complete API schema in memory (`swarm/backend-dev/api-schema-frontend`)
- Full API documentation (`LITELLM_CREDIT_API.md`)
- Example requests (Python, cURL, JavaScript)

**Frontend Needs**:
1. Credit balance display widget
2. Power level selector (3 buttons)
3. Credit purchase modal (Stripe integration)
4. Usage analytics dashboard
5. BYOK key management UI
6. Model selector (tier-filtered)

---

## Next Steps

1. **Database Agent**: Create database tables and indexes
2. **Frontend Agent**: Build UI components using API schema
3. **DevOps**: Generate BYOK_ENCRYPTION_KEY and add to .env.auth
4. **Testing**: Run integration tests with LiteLLM proxy
5. **Deployment**: Restart ops-center-direct container

---

## Known Limitations

1. **JWT Validation**: Currently using simplified token extraction (development only)
   - Production: Implement proper JWT validation with Keycloak
2. **Stripe Test Mode**: Using test keys - switch to live keys for production
3. **No Webhooks**: Stripe webhooks not implemented (credit purchase only)
4. **Rate Limiting**: Not implemented (rely on tier enforcement middleware)

---

## API Schema for Frontend

**Stored in Memory**: `swarm/backend-dev/api-schema-frontend`
**Format**: JSON schema with all endpoints, request/response formats, power levels, and pricing

Frontend team can retrieve with:
```bash
npx claude-flow@alpha hooks session-restore --session-id "swarm-litellm"
```

---

## Files Created

1. `/backend/litellm_credit_system.py` (620 lines)
2. `/backend/byok_manager.py` (350 lines)
3. `/backend/litellm_api.py` (720 lines)
4. `/backend/docs/LITELLM_CREDIT_API.md` (800+ lines)
5. `/backend/LITELLM_BACKEND_COMPLETE.md` (this file)

**Modified**:
- `/backend/server.py` (added imports, router registration, startup/shutdown)

---

## Performance Considerations

- **Redis Caching**: 60-second TTL for credit balances (reduce DB load)
- **Database Pool**: 2-10 connections (adjust based on load)
- **Cost Calculation**: In-memory (no DB calls)
- **Async Throughout**: All I/O operations are async
- **Connection Cleanup**: Proper shutdown handlers prevent leaks

---

## Security Features

- **API Key Encryption**: Fernet symmetric encryption (BYOK keys)
- **Transaction Locking**: PostgreSQL row-level locks prevent race conditions
- **Input Validation**: Pydantic models for all requests
- **Error Sanitization**: No sensitive data in error messages
- **Rate Limiting**: Tier-based request limits (future: Redis-backed)

---

**BACKEND COMPLETE** ✅

Ready for database schema creation and frontend integration.

---

**Contact**: Backend Developer #1
**Coordination**: `swarm/backend-dev/*` memory keys
**Documentation**: `/backend/docs/LITELLM_CREDIT_API.md`
