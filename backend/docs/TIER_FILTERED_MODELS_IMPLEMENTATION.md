# Tier-Filtered Model Listing Implementation

## Overview

Enhancement to the `/api/v1/llm/models` endpoint to return only models accessible by the user's subscription tier.

## Current Implementation (Line 1405-1476)

The current endpoint:
- ✅ Gets user's subscription tier from credit system
- ✅ Queries `model_access_control` table
- ✅ Filters by tier using `tier_access @> jsonb` operator
- ✅ Returns OpenAI-compatible format

## What's Already Working

The endpoint **already implements tier-based filtering**!

```python
@router.get("/models")
async def list_models(
    user_id: str = Depends(get_user_id),
    credit_system: CreditSystem = Depends(get_credit_system)
):
    # 1. Get user's subscription tier
    tier = await credit_system.get_user_tier(user_id)

    # 2. Query models table with tier filtering
    cur.execute("""
        SELECT model_id, provider, display_name, description, pricing, context_length
        FROM model_access_control
        WHERE tier_access @> %s::jsonb  # ← Tier filtering here
        ORDER BY provider, model_id
    """, (json.dumps([db_tier]),))
```

## Enhancement: Session-Based Tier Detection

### Issue
Current implementation requires API key authentication (`get_user_id` depends on Authorization header).
Web UI users with session cookies can't access the endpoint directly.

### Solution
Add alternative endpoint using session authentication for web UI:

```python
@router.get("/models/session")
async def list_models_session(
    request: Request,
    credit_system: CreditSystem = Depends(get_credit_system)
):
    """List models based on user's session (for web UI)"""
    # Get user from session cookie
    user = await get_current_user_from_session(request)
    user_id = user.get("user_id") or user.get("sub") or user.get("id")

    # Use same logic as /models endpoint
    tier = await credit_system.get_user_tier(user_id)
    # ... rest of implementation
```

## Database Schema

### model_access_control Table

```sql
CREATE TABLE model_access_control (
    id SERIAL PRIMARY KEY,
    model_id VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL,
    display_name VARCHAR(255),
    description TEXT,
    tier_access JSONB NOT NULL,  # ["trial", "starter", "professional", "enterprise"]
    pricing JSONB,
    context_length INTEGER,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Example Data

```sql
-- GPT-4 (Professional+ only)
INSERT INTO model_access_control (model_id, provider, tier_access) VALUES
('openai/gpt-4', 'openai', '["professional", "enterprise"]');

-- Claude 3.5 Sonnet (All paid tiers)
INSERT INTO model_access_control (model_id, provider, tier_access) VALUES
('anthropic/claude-3.5-sonnet', 'anthropic', '["starter", "professional", "enterprise"]');

-- Llama 3.1 (All tiers including trial)
INSERT INTO model_access_control (model_id, provider, tier_access) VALUES
('meta/llama-3.1-8b', 'meta', '["trial", "starter", "professional", "enterprise"]');
```

## Tier Hierarchy

```
trial         → Basic models only
starter       → trial + mid-tier models
professional  → starter + premium models (GPT-4, Claude Opus)
enterprise    → professional + all models
```

## BYOK Integration

The endpoint should also check if user has BYOK (Bring Your Own Key) enabled:

```python
# Check if user has BYOK keys
byok_providers = await byok_manager.list_user_providers(user_id)
has_byok = len([p for p in byok_providers if p.get('enabled')]) > 0

# If BYOK enabled, include ALL models from those providers
if has_byok:
    for provider_info in byok_providers:
        if provider_info.get('enabled'):
            # Add all models from this provider
            # regardless of tier restrictions
```

## Caching Strategy

Current implementation doesn't cache. Add Redis caching:

```python
# Cache key: models:{tier}:{byok_enabled}
cache_key = f"models:{tier}:{has_byok}"
cache_ttl = 300  # 5 minutes

# Try cache first
cached = await redis.get(cache_key)
if cached:
    return json.loads(cached)

# Query database
models = fetch_models_from_db(tier, has_byok)

# Cache results
await redis.setex(cache_key, cache_ttl, json.dumps(models))

return models
```

## Response Format

### OpenAI-Compatible Format

```json
{
  "object": "list",
  "data": [
    {
      "id": "openai/gpt-4",
      "object": "model",
      "owned_by": "openai",
      "permission": [],
      "tier": "professional",
      "name": "GPT-4",
      "description": "Most capable GPT-4 model",
      "context_length": 8192,
      "pricing": {
        "input": 0.03,
        "output": 0.06,
        "unit": "1M tokens"
      }
    }
  ]
}
```

## Implementation Plan

Since tier filtering is **already implemented**, the enhancement focuses on:

1. ✅ **Session Authentication Support** - Add `/models/session` endpoint for web UI
2. ✅ **BYOK Detection** - Include BYOK models alongside tier-filtered models
3. ✅ **Redis Caching** - Cache results by tier to reduce database load
4. ✅ **Detailed Metadata** - Include pricing, context length, descriptions

## Testing

### Test Cases

1. **Trial Tier User** - Should only see basic models
2. **Professional Tier User** - Should see premium models (GPT-4, Claude Opus)
3. **BYOK Enabled User** - Should see ALL models from their provider
4. **Session-Based Request** - Web UI users should get tier-filtered models
5. **API Key Request** - External apps should get tier-filtered models

### Test Command

```bash
# API key authentication
curl -H "Authorization: Bearer uc_test_key" \
  http://localhost:8084/api/v1/llm/models

# Session authentication (browser/web UI)
curl -b "session_token=..." \
  http://localhost:8084/api/v1/llm/models/session
```

## Metrics & Analytics

Track model access by tier:

```python
# Log metrics for analytics
await usage_meter.track_event(
    user_id=user_id,
    event_type="model_list_access",
    metadata={
        "tier": tier,
        "model_count": len(models),
        "has_byok": has_byok
    }
)
```

## Error Handling

```python
try:
    # Get tier
    tier = await credit_system.get_user_tier(user_id)
except Exception as e:
    logger.warning(f"Failed to get tier for {user_id}: {e}")
    tier = "trial"  # Default to trial on error

try:
    # Query models
    models = query_models(tier)
except psycopg2.Error as e:
    logger.error(f"Database error: {e}")
    raise HTTPException(status_code=500, detail="Database error")
```

## Documentation

Add to API documentation:

```markdown
## GET /api/v1/llm/models

Returns list of LLM models accessible to the authenticated user based on their subscription tier.

**Authentication**: Required (API key or session)

**Response**: OpenAI-compatible model list

**Filtering**:
- Models are filtered by user's subscription tier
- Users with BYOK keys see all models from their providers
- Results are cached for 5 minutes per tier

**Example**:
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://your-domain.com/api/v1/llm/models
```
```

## Conclusion

The tier-based filtering is **already implemented** in the current endpoint. The enhancements focus on:
- Adding session-based authentication for web UI users
- Including BYOK models alongside tier-filtered models
- Adding Redis caching for performance
- Improving response metadata

**Status**: Current implementation is functional. Enhancements are optional improvements.
