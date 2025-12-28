# OpenRouter Integration - Quick Start

**For Developers**: 5-minute guide to using the OpenRouter integration

---

## Basic Usage

### 1. Create OpenRouter Account

```python
from openrouter_automation import openrouter_manager

# User provides their OpenRouter API key
account = await openrouter_manager.create_account(
    user_id="keycloak-user-id",
    api_key="sk-or-v1-abc123...",
    user_email="user@example.com"
)

# Returns:
# {
#   "user_id": "keycloak-user-id",
#   "account_id": "My API Key",
#   "free_credits": 10.0,
#   "last_synced": "2025-10-24T12:00:00Z"
# }
```

### 2. Get Account Status

```python
account = await openrouter_manager.get_account("keycloak-user-id")

print(f"Credits: ${account['free_credits']}")
print(f"Last synced: {account['last_synced']}")
```

### 3. Sync Credits

```python
# Manual sync (or use hourly background job)
credits = await openrouter_manager.sync_free_credits("keycloak-user-id")

print(f"Updated credits: ${credits}")
```

### 4. Detect Free Models

```python
# Get list of free models (cached for 1 hour)
free_models = await openrouter_manager.detect_free_models()

print(f"Found {len(free_models)} free models")
print(free_models[:3])
# ["meta-llama/llama-3.1-8b-instruct:free", "deepseek/deepseek-r1:free", ...]
```

### 5. Calculate Markup

```python
from decimal import Decimal

# Calculate markup based on user's subscription tier
markup, total, reason = await openrouter_manager.calculate_markup(
    user_id="keycloak-user-id",
    model="openai/gpt-4",
    provider_cost=Decimal("0.03")
)

print(f"Provider cost: ${provider_cost}")
print(f"Platform markup: ${markup}")
print(f"Total cost: ${total}")
print(f"Reason: {reason}")
```

### 6. Route LLM Request

```python
# Route chat completion through user's OpenRouter account
response = await openrouter_manager.route_request(
    user_id="keycloak-user-id",
    model="meta-llama/llama-3.1-8b-instruct:free",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

# Standard OpenAI-compatible response
print(response["choices"][0]["message"]["content"])
# "The capital of France is Paris."
```

---

## Direct API Client Usage

```python
from openrouter_client import OpenRouterClient

async with OpenRouterClient("sk-or-v1-abc123...") as client:
    # Get models
    models = await client.get_models()

    # Get key info
    key_info = await client.get_key_info()

    # Chat completion
    response = await client.chat_completion(
        model="meta-llama/llama-3.1-8b-instruct:free",
        messages=[{"role": "user", "content": "Hello!"}]
    )
```

---

## Error Handling

```python
from openrouter_client import OpenRouterAuthError, OpenRouterRateLimitError
from openrouter_automation import OpenRouterError

try:
    account = await openrouter_manager.create_account(...)
except OpenRouterAuthError:
    return {"error": "Invalid OpenRouter API key"}
except OpenRouterRateLimitError as e:
    return {"error": "Rate limited", "retry_after": e.retry_after}
except OpenRouterError as e:
    return {"error": str(e)}
```

---

## Testing

```bash
# Run integration tests
pytest backend/tests/integration/test_openrouter_integration.py -v

# Test with real API key
python3 -c "
import asyncio
from openrouter_client import OpenRouterClient

async def test():
    async with OpenRouterClient('your-api-key') as client:
        models = await client.get_models()
        print(f'Found {len(models)} models')

asyncio.run(test())
"
```

---

## Common Patterns

### Pattern 1: Check if user has OpenRouter account

```python
account = await openrouter_manager.get_account(user_id)
if account:
    print(f"User has {account['free_credits']} credits")
else:
    print("User needs to add OpenRouter API key")
```

### Pattern 2: Determine if model is free

```python
is_free = openrouter_manager.detect_free_model("meta-llama/llama-3.1-8b-instruct:free")
if is_free:
    print("This model is free (0% markup)")
else:
    print("This model is paid (tier-based markup applies)")
```

### Pattern 3: Cost estimation before request

```python
# Get user's subscription tier
from keycloak_integration import keycloak_service
user_attrs = await keycloak_service.get_user_attributes(user_id)
subscription_tier = user_attrs.get("subscription_tier", "trial")

# Estimate cost
provider_cost = Decimal("0.03")  # per 1K tokens
markup, total, reason = await openrouter_manager.calculate_markup(
    user_id, model, provider_cost
)

print(f"Estimated cost: ${total} ({reason})")
```

---

## Configuration

### Environment Variables

```bash
# .env.auth
OPENROUTER_SYSTEM_KEY=sk-or-v1-system-key  # Optional, for public endpoints
OPENROUTER_ENCRYPTION_KEY_PATH=/app/data/openrouter_encryption.key
```

### Database

```sql
-- Verify table exists
SELECT * FROM openrouter_accounts LIMIT 1;

-- Check user's account
SELECT user_id, openrouter_account_id, free_credits, last_synced
FROM openrouter_accounts
WHERE user_id = 'keycloak-user-id';
```

---

## Troubleshooting

### Issue: "No OpenRouter account for user"

```python
# Solution: Create account
account = await openrouter_manager.create_account(user_id, api_key)
```

### Issue: "Invalid OpenRouter API key"

```python
# Solution: Get new key from https://openrouter.ai/keys
# Then update account
account = await openrouter_manager.create_account(user_id, new_api_key)
```

### Issue: Credits not updating

```python
# Solution: Manual sync
credits = await openrouter_manager.sync_free_credits(user_id)
```

---

## Full Documentation

See `/docs/OPENROUTER_INTEGRATION_GUIDE.md` for:
- Complete API reference
- Setup instructions
- Background jobs
- Security considerations
- Monitoring & logging

---

**Quick Reference Created**: October 24, 2025
**For Questions**: See Integration Team Lead
