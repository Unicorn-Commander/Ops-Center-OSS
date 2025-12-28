# LiteLLM Setup Instructions

## Overview

LiteLLM provides a unified OpenAI-compatible API for 100+ LLM providers. This guide walks you through configuring and deploying LiteLLM for Ops-Center.

## Architecture

```
User Request → Ops-Center (8084) → LiteLLM Proxy (4000) → Provider APIs
                                  ↓
                            Wilmer Router (4001)
                                  ↓
                        (Caching, Rate Limiting, Metrics)
```

## Step 1: Add Your API Keys

Edit `.env.litellm` and add your provider API keys. You only need to configure the providers you want to use.

### Recommended Setup (Start Here)

**For Most Users:**
1. **GROQ_API_KEY** (Free) - Ultra-fast inference for Llama/Mixtral models
2. **OPENROUTER_API_KEY** (Tier 2) - Access to Claude, GPT-4, Gemini, 200+ models
3. **TOGETHER_API_KEY** (Tier 1) - Cheap, fast inference for open models

**How to Get Keys:**

```bash
# Groq (Free Tier)
# Visit: https://console.groq.com/keys
# 1. Sign up with email
# 2. Go to "API Keys"
# 3. Create new key
# 4. Copy and paste into .env.litellm

# OpenRouter (Pay-as-you-go)
# Visit: https://openrouter.ai/keys
# 1. Sign up with email
# 2. Add $5-$10 credits
# 3. Create API key
# 4. Copy and paste into .env.litellm

# Together AI (Free Trial + Paid)
# Visit: https://api.together.xyz/settings/api-keys
# 1. Sign up with email
# 2. Get $25 free credits
# 3. Create API key
# 4. Copy and paste into .env.litellm
```

### Optional Providers

**Premium Direct Access (Tier 3):**
- `ANTHROPIC_API_KEY` - Direct Claude access (more expensive than OpenRouter)
- `OPENAI_API_KEY` - Direct GPT access (more expensive than OpenRouter)
- `GOOGLE_API_KEY` - Direct Gemini access (has free tier)

**Additional Budget Options (Tier 1):**
- `HUGGINGFACE_API_KEY` - Free tier, 1000+ models
- `FIREWORKS_API_KEY` - Fast function calling
- `DEEPINFRA_API_KEY` - Long context support

## Step 2: Verify Configuration Files

Check that all required files are present:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Verify files exist
ls -lh litellm_config.yaml          # LiteLLM model routing config (17KB)
ls -lh .env.litellm                 # Environment variables (just created)
ls -lh docker-compose.litellm.yml   # Docker compose file (4.5KB)
```

## Step 3: Deploy LiteLLM Stack

Start the LiteLLM proxy and Wilmer router:

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Start LiteLLM services
docker compose -f docker-compose.litellm.yml up -d

# Check container status
docker ps --filter "name=litellm"
docker ps --filter "name=wilmer"
```

Expected containers:
- `unicorn-litellm-wilmer` - Main LiteLLM proxy (port 4000)
- `unicorn-wilmer-router` - Smart router with caching (port 4001)

## Step 4: Verify Deployment

Test that LiteLLM is running:

```bash
# Health check LiteLLM proxy
curl http://localhost:4000/health

# Health check Wilmer router
curl http://localhost:4001/health

# List available models
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-9c48b4f8abfd365ae7abaf67fae773dc3d44f642615b420c97ee94146d16d379"
```

## Step 5: Restart Ops-Center Backend

Ops-Center needs to be restarted to use the new LiteLLM endpoint:

```bash
# Restart backend
docker restart ops-center-direct

# Check logs
docker logs ops-center-direct --tail 50 -f
```

## Step 6: Test End-to-End

Test LLM inference through Ops-Center:

```bash
# Test via Ops-Center API
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_OPS_CENTER_TOKEN" \
  -d '{
    "model": "groq/llama-3.1-8b-instant",
    "messages": [{"role": "user", "content": "Hello! Say hi back."}]
  }'
```

## Configuration Reference

### LiteLLM Config File (`litellm_config.yaml`)

The config file defines:
- **Model Routing**: Which provider serves which model
- **Tier System**: Free, Tier 1, Tier 2, Tier 3 access levels
- **Fallbacks**: Automatic failover if primary provider fails
- **Cost Management**: Budgets and rate limits

### Environment Variables (`.env.litellm`)

Key variables:
- `LITELLM_MASTER_KEY`: Authentication for LiteLLM API (generated)
- `BYOK_ENCRYPTION_KEY`: Encrypts user API keys in database (generated)
- `PROVIDER_API_KEY`: Your API keys for each provider
- `DATABASE_URL`: PostgreSQL connection (shared with UC-Cloud)
- `REDIS_HOST`: Redis for caching (shared with UC-Cloud)

### Docker Compose (`docker-compose.litellm.yml`)

Defines:
- **unicorn-litellm-wilmer**: Main proxy container
- **unicorn-wilmer-router**: Smart router with caching
- **Networks**: Connected to `unicorn-network`, `web` (Traefik)
- **Volumes**: Configuration mounts

## Accessing LiteLLM

### Internal Access (Docker Network)

From Ops-Center backend:
```python
LITELLM_URL = "http://unicorn-litellm-wilmer:4000"
```

### External Access (via Traefik)

From outside the server:
```
https://ai.your-domain.com
```

### Via Ops-Center API (Recommended)

All Ops-Center services route through:
```
https://your-domain.com/api/v1/llm/chat/completions
```

## Subscription Tier Access

LiteLLM enforces subscription tiers:

**Free Tier:**
- Local models (vLLM, Ollama)
- Groq (ultra-fast, free)

**Tier 1 ($19/month):**
- Free tier +
- Together AI
- HuggingFace
- Fireworks AI
- DeepInfra

**Tier 2 ($49/month):**
- Tier 1 +
- OpenRouter (all models)
- Access to Claude, GPT-4, Gemini

**Tier 3 ($99/month):**
- Tier 2 +
- Direct Anthropic API
- Direct OpenAI API
- Direct Google API
- Custom endpoints

## Managing User API Keys (BYOK)

Users with paid subscriptions can add their own API keys:

1. User goes to Ops-Center → Settings → API Keys
2. Adds provider API key (encrypted with `BYOK_ENCRYPTION_KEY`)
3. LiteLLM uses user's key instead of platform key
4. User sees provider costs directly, not charged by platform

This is configured in `litellm_config.yaml` under the `byok` section.

## Monitoring & Logs

### View LiteLLM Logs

```bash
# LiteLLM proxy logs
docker logs unicorn-litellm-wilmer -f

# Wilmer router logs
docker logs unicorn-wilmer-router -f
```

### Check Metrics

```bash
# LiteLLM Prometheus metrics
curl http://localhost:4000/metrics

# Wilmer router metrics
curl http://localhost:4001/metrics
```

### Database Queries

```bash
# Connect to PostgreSQL
docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_db

# Check LiteLLM usage
SELECT * FROM litellm_usage ORDER BY created_at DESC LIMIT 10;

# Check BYOK keys (encrypted)
SELECT user_id, provider, created_at FROM user_provider_keys;
```

## Troubleshooting

### Issue: "No models available"

**Solution**: Check that at least one provider API key is configured in `.env.litellm`

```bash
# Verify environment variables loaded
docker exec unicorn-litellm-wilmer printenv | grep API_KEY
```

### Issue: "Authentication failed"

**Solution**: Verify `LITELLM_MASTER_KEY` matches in:
- `.env.litellm`
- Ops-Center backend configuration
- Your API request headers

### Issue: "Provider API error"

**Solution**: Check provider API key is valid and has credits

```bash
# Test provider API directly (example with Groq)
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY"
```

### Issue: "Container won't start"

**Solution**: Check Docker logs for errors

```bash
docker logs unicorn-litellm-wilmer
docker logs unicorn-wilmer-router

# Check if ports are already in use
sudo netstat -tulpn | grep -E '4000|4001'
```

### Issue: "Database connection failed"

**Solution**: Ensure PostgreSQL is running and accessible

```bash
# Check PostgreSQL container
docker ps --filter "name=postgresql"

# Test connection
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT 1;"
```

## Advanced Configuration

### Adding Custom Models

Edit `litellm_config.yaml` and add to the `model_list` section:

```yaml
- model_name: custom/my-model
  litellm_params:
    model: custom/my-model
    api_base: https://my-custom-endpoint.com/v1
    api_key: os.environ/MY_CUSTOM_API_KEY
  model_info:
    mode: chat
    tier: tier2
```

Then add `MY_CUSTOM_API_KEY` to `.env.litellm`.

### Configuring Fallbacks

LiteLLM automatically falls back to alternative providers if one fails. Configure in `litellm_config.yaml`:

```yaml
router_settings:
  enable_fallbacks: true
  fallback_models:
    - groq/llama-3.1-8b-instant
    - together/llama-3.1-8b-instruct
```

### Rate Limiting

Configure per-user rate limits in `litellm_config.yaml`:

```yaml
general_settings:
  max_requests_per_minute: 60
  max_tokens_per_minute: 100000
```

## Security Best Practices

1. **Never commit `.env.litellm` to git** - Contains sensitive API keys
2. **Rotate LITELLM_MASTER_KEY** - Change periodically for security
3. **Use BYOK for users** - Let users provide their own keys when possible
4. **Monitor usage** - Set up alerts for unusual API usage patterns
5. **Keep keys encrypted** - BYOK_ENCRYPTION_KEY encrypts user keys in DB

## Next Steps

1. Configure at least one provider API key (recommend: Groq for free tier)
2. Deploy LiteLLM stack with docker compose
3. Test inference via Ops-Center API
4. Add additional providers as needed
5. Monitor usage and costs via Ops-Center dashboard

## Support

- **LiteLLM Docs**: https://docs.litellm.ai/
- **UC-Cloud Docs**: /home/muut/Production/UC-Cloud/CLAUDE.md
- **GitHub Issues**: https://github.com/Unicorn-Commander/UC-Cloud/issues
