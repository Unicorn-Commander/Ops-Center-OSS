# LiteLLM Configuration Update Guide

## Overview

This guide explains how to update the LiteLLM proxy to use the OpenRouter API key stored in the Ops-Center database.

## Current Architecture

```
┌─────────────────────┐
│   Ops-Center API    │  Admin updates OpenRouter key via:
│  (ops-center-direct)│  PUT /api/v1/admin/platform-keys/openrouter
└──────────┬──────────┘
           │ Stores encrypted key in PostgreSQL
           ▼
┌─────────────────────┐
│   PostgreSQL DB     │  platform_settings table:
│ (unicorn-postgresql)│  - key: "openrouter_api_key"
└─────────────────────┘  - value: <encrypted>
           │
           │ LiteLLM needs to read this key
           ▼
┌─────────────────────┐
│  LiteLLM Proxy      │  Currently reads from:
│  (uchub-litellm)    │  - Environment variable: OPENROUTER_API_KEY
└─────────────────────┘  - Config file: /app/litellm_config.yaml
```

## Option 1: Environment Variable (Recommended)

Update the LiteLLM container environment variable to use the database key.

### Steps:

1. **Retrieve the decrypted key from Ops-Center API**:
   ```bash
   # As admin user, call:
   curl -X GET https://unicorncommander.ai/api/v1/admin/platform-keys/openrouter/decrypted \
     -H "Cookie: session_token=YOUR_SESSION_TOKEN"

   # Response:
   # {
   #   "api_key": "sk-or-v1-...",
   #   "source": "database"
   # }
   ```

2. **Update Docker Compose environment**:
   ```bash
   cd /opt/uc-cloud

   # Edit the LiteLLM service environment
   vim docker-compose.yml  # Or wherever uchub-litellm is defined

   # Add/update:
   environment:
     OPENROUTER_API_KEY: "sk-or-v1-YOUR_KEY_HERE"
   ```

3. **Restart LiteLLM container**:
   ```bash
   docker restart uchub-litellm

   # Or full rebuild:
   docker compose up -d --force-recreate uchub-litellm
   ```

4. **Verify**:
   ```bash
   # Check LiteLLM logs
   docker logs uchub-litellm --tail 50

   # Should see: "OpenRouter API key loaded successfully"
   ```

## Option 2: Configuration File

Update the LiteLLM config YAML to use the environment variable.

### Steps:

1. **Locate LiteLLM config**:
   ```bash
   # Find the config file (usually mounted as a volume)
   docker inspect uchub-litellm | grep -A 5 "Mounts"

   # Common locations:
   # - /app/litellm_config.yaml (inside container)
   # - /opt/uc-cloud/billing/litellm/config.yaml (host)
   ```

2. **Edit config file**:
   ```yaml
   model_list:
     - model_name: gpt-4
       litellm_params:
         model: openrouter/openai/gpt-4
         api_key: os.environ/OPENROUTER_API_KEY  # Read from environment

   general_settings:
     master_key: os.environ/LITELLM_MASTER_KEY
   ```

3. **Restart LiteLLM**:
   ```bash
   docker restart uchub-litellm
   ```

## Option 3: Automatic Sync (Future Enhancement)

Implement a background service to automatically sync the database key to LiteLLM.

### Concept:

```python
# In ops-center backend (platform_keys_api.py)

async def sync_openrouter_key_to_litellm(api_key: str):
    """
    Automatically update LiteLLM config when OpenRouter key changes
    """
    # Option A: Update Docker container environment
    # Option B: Write to shared config file
    # Option C: Call LiteLLM admin API to update key
    pass
```

This would be triggered after:
- `PUT /api/v1/admin/platform-keys/openrouter` succeeds

## LiteLLM Admin API (Option 4)

Use LiteLLM's admin API to update keys dynamically without restart.

### Steps:

1. **Get LiteLLM master key**:
   ```bash
   # From environment or database
   echo $LITELLM_MASTER_KEY
   ```

2. **Update key via LiteLLM API**:
   ```bash
   # LiteLLM admin endpoint (if available)
   curl -X POST http://uchub-litellm:4000/key/update \
     -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "provider": "openrouter",
       "api_key": "sk-or-v1-NEW_KEY"
     }'
   ```

3. **No restart needed**:
   - LiteLLM reloads keys dynamically

**Note**: Check LiteLLM documentation to confirm if this API exists.

## Current State of LiteLLM in UC-Cloud

Based on the UC-Cloud setup:

1. **Container**: `uchub-litellm`
2. **Port**: 4000 (internal)
3. **Config**: Likely at `/opt/uc-cloud/billing/litellm/config.yaml`
4. **Environment**: Defined in `docker-compose.billing.yml`

### To Update:

```bash
# 1. Get the key from Ops-Center API
API_KEY=$(curl -s -X GET https://unicorncommander.ai/api/v1/admin/platform-keys/openrouter/decrypted \
  -H "Cookie: session_token=$SESSION_TOKEN" | jq -r '.api_key')

# 2. Update Docker environment
cd /opt/uc-cloud/billing
vim docker-compose.billing.yml

# Add under uchub-litellm service:
environment:
  OPENROUTER_API_KEY: "${OPENROUTER_API_KEY}"

# 3. Update .env.billing file
echo "OPENROUTER_API_KEY=$API_KEY" >> .env.billing

# 4. Restart LiteLLM
docker compose -f docker-compose.billing.yml restart uchub-litellm
```

## Verification

After updating:

```bash
# 1. Check LiteLLM is running
docker ps | grep litellm

# 2. Check logs
docker logs uchub-litellm --tail 100

# 3. Test LLM inference
curl -X POST http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "model": "openai/gpt-4",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# 4. Check Ops-Center LLM API
curl -X POST https://unicorncommander.ai/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Cookie: session_token=$SESSION_TOKEN" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Test"}]
  }'
```

## Troubleshooting

### Key Not Working

```bash
# Check if key is set in container
docker exec uchub-litellm printenv | grep OPENROUTER

# Check config file
docker exec uchub-litellm cat /app/litellm_config.yaml

# Check LiteLLM startup logs
docker logs uchub-litellm | grep -i "openrouter\|api_key\|error"
```

### LiteLLM Won't Start

```bash
# Check config syntax
docker exec uchub-litellm python -c "import yaml; yaml.safe_load(open('/app/litellm_config.yaml'))"

# Check environment variables
docker exec uchub-litellm env

# Restart with verbose logging
docker restart uchub-litellm && docker logs uchub-litellm -f
```

## Best Practices

1. **Never hardcode keys** - Always use environment variables or encrypted database storage
2. **Use secrets management** - Consider Docker secrets or Kubernetes secrets in production
3. **Rotate keys regularly** - Update OpenRouter keys periodically
4. **Monitor usage** - Track OpenRouter API usage in Ops-Center billing dashboard
5. **Test after updates** - Always verify LLM inference works after key changes

## Future Enhancements

1. **Automatic key rotation** - Scheduled key rotation with zero downtime
2. **Key versioning** - Keep history of previous keys
3. **Multi-provider support** - Manage keys for OpenAI, Anthropic, Google, etc.
4. **Key health monitoring** - Automatically test keys and alert on failures
5. **BYOK integration** - Allow users to provide their own OpenRouter keys

## Related Documentation

- Ops-Center API: `/services/ops-center/backend/platform_keys_api.py`
- LiteLLM Config: `/billing/litellm/config.yaml`
- Billing System: `/billing/PLANS_CREATED.md`
- UC-Cloud Main: `/CLAUDE.md`
