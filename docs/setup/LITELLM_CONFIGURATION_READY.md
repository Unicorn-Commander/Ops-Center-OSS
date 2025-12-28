# LiteLLM Configuration Ready for Deployment

**Date**: October 20, 2025
**Status**: ✅ CONFIGURATION FILES READY

---

## Summary

All LiteLLM configuration files have been prepared and are ready for user to add API keys.

## Files Created

### 1. `.env.litellm` ✅

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/.env.litellm`
**Size**: 6.2 KB (comprehensive template)

**Generated Keys**:
- ✅ `LITELLM_MASTER_KEY`: `sk-litellm-9c48b4f8abfd365ae7abaf67fae773dc3d44f642615b420c97ee94146d16d379`
- ✅ `BYOK_ENCRYPTION_KEY`: `V5rKpDMpTaHHFOcmWpwb9qkJnuLSyXf2QyygfhAlOJ8=`

**Pre-configured Variables**:
- ✅ Database URL (PostgreSQL shared instance)
- ✅ Redis host/port (shared cache)
- ✅ Local LLM endpoints (vLLM, Ollama)
- ✅ Proxy URLs (LiteLLM, Wilmer)

**User Must Add**:
- ⏳ Provider API keys (9 providers, all optional)
  - OpenRouter
  - Together AI
  - Groq
  - HuggingFace
  - Fireworks AI
  - DeepInfra
  - Anthropic
  - OpenAI
  - Google

### 2. `LITELLM_SETUP_INSTRUCTIONS.md` ✅

**Location**: `/home/muut/Production/UC-Cloud/services/ops-center/LITELLM_SETUP_INSTRUCTIONS.md`
**Size**: 18 KB (comprehensive guide)

**Sections**:
1. ✅ Overview and Architecture
2. ✅ Step-by-step setup guide
3. ✅ Provider comparison and recommendations
4. ✅ Configuration reference
5. ✅ Access methods (internal, external, via Ops-Center)
6. ✅ Subscription tier access levels
7. ✅ BYOK (Bring Your Own Key) management
8. ✅ Monitoring and logging
9. ✅ Troubleshooting common issues
10. ✅ Advanced configuration examples

### 3. Existing Files Verified ✅

**litellm_config.yaml**:
- ✅ Exists and ready (17 KB)
- ✅ Contains model routing configuration
- ✅ Defines tier system (Free, Tier 1, Tier 2, Tier 3)
- ✅ Configured for 100+ models

**docker-compose.litellm.yml**:
- ✅ Exists and ready (4.5 KB)
- ✅ Defines 2 services:
  - `unicorn-litellm-wilmer` (LiteLLM proxy on port 4000)
  - `unicorn-wilmer-router` (Smart router on port 4001)
- ✅ Network configuration (unicorn-network, web)
- ✅ Volume mounts for config files
- ✅ Health checks configured
- ✅ Traefik labels for SSL (ai.your-domain.com)

---

## What User Needs to Do

### Step 1: Add API Keys (Required)

Edit `.env.litellm` and add at least ONE provider API key:

**Recommended for Getting Started**:
```bash
# Free tier - Ultra-fast inference
GROQ_API_KEY=gsk_...

# OR

# Paid tier - Access to Claude, GPT-4, Gemini
OPENROUTER_API_KEY=sk-or-v1-...
```

**Where to Get Keys**:
- **Groq** (Free): https://console.groq.com/keys
- **OpenRouter** (Paid): https://openrouter.ai/keys
- **Together AI** (Paid): https://api.together.xyz/settings/api-keys

### Step 2: Deploy LiteLLM

```bash
cd /home/muut/Production/UC-Cloud/services/ops-center

# Start LiteLLM stack
docker compose -f docker-compose.litellm.yml up -d

# Verify containers are running
docker ps --filter "name=litellm"
docker ps --filter "name=wilmer"
```

### Step 3: Test Deployment

```bash
# Health check
curl http://localhost:4000/health

# List available models (requires LITELLM_MASTER_KEY)
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-litellm-9c48b4f8abfd365ae7abaf67fae773dc3d44f642615b420c97ee94146d16d379"
```

### Step 4: Restart Ops-Center

```bash
# Restart backend to use new LiteLLM endpoint
docker restart ops-center-direct

# Check logs
docker logs ops-center-direct --tail 50 -f
```

---

## Configuration Details

### Generated Keys Explanation

**LITELLM_MASTER_KEY**:
- Purpose: Authentication for LiteLLM API admin operations
- Format: `sk-litellm-{64-char-hex}`
- Length: 75 characters
- Cryptographically secure: ✅ Yes (32 bytes of entropy)

**BYOK_ENCRYPTION_KEY**:
- Purpose: Encrypt user API keys in database (Bring Your Own Key feature)
- Format: Fernet key (URL-safe base64)
- Algorithm: AES-128 in CBC mode with HMAC
- Cryptographically secure: ✅ Yes (generated via cryptography.Fernet)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Request                             │
│          (https://your-domain.com/api/v1/llm/*)          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Ops-Center Backend                          │
│              (ops-center-direct:8084)                        │
│  - Authentication (Keycloak SSO)                             │
│  - User tier checking                                        │
│  - Usage metering                                            │
│  - Request routing                                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│             LiteLLM Proxy                                    │
│       (unicorn-litellm-wilmer:4000)                          │
│  - Model routing                                             │
│  - Provider selection                                        │
│  - Fallback handling                                         │
│  - Cost tracking                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌──────▼──────┐
            │ Wilmer Router │   │   Caching    │
            │   (4001)      │   │   (Redis)    │
            └───────┬───────┘   └──────────────┘
                    │
        ┌───────────┼───────────────────┐
        │           │                   │
    ┌───▼───┐  ┌───▼───┐          ┌────▼────┐
    │OpenRouter│ │Groq │   ...    │vLLM Local│
    │200+ models│ │Fast│          │Qwen2.5│
    └──────────┘ └─────┘          └─────────┘
```

### Subscription Tier Access

**Free Tier** (No subscription required):
- ✅ Local models (vLLM, Ollama)
- ✅ Groq (ultra-fast, free API)

**Tier 1** ($19/month):
- ✅ Free tier +
- ✅ Together AI
- ✅ HuggingFace
- ✅ Fireworks AI
- ✅ DeepInfra

**Tier 2** ($49/month):
- ✅ Tier 1 +
- ✅ OpenRouter (all 200+ models)
- ✅ Claude 3.5 Sonnet
- ✅ GPT-4
- ✅ Gemini 1.5 Pro

**Tier 3** ($99/month):
- ✅ Tier 2 +
- ✅ Direct Anthropic API
- ✅ Direct OpenAI API
- ✅ Direct Google API
- ✅ Custom endpoints
- ✅ BYOK support

### Service Endpoints

**Internal Access** (Docker network):
```
http://unicorn-litellm-wilmer:4000/v1/chat/completions
http://unicorn-wilmer-router:4001/v1/chat/completions
```

**External Access** (via Traefik):
```
https://ai.your-domain.com/v1/chat/completions
```

**Via Ops-Center** (recommended):
```
https://your-domain.com/api/v1/llm/chat/completions
```

---

## Important Notes

### Security

**DO NOT**:
- ❌ Commit `.env.litellm` to git (contains API keys)
- ❌ Share `LITELLM_MASTER_KEY` publicly
- ❌ Log API keys in application logs

**DO**:
- ✅ Keep `.env.litellm` local only
- ✅ Rotate keys periodically
- ✅ Use BYOK for users when possible
- ✅ Monitor API usage for anomalies
- ✅ Set up rate limiting per user

### Provider Recommendations

**For Development/Testing**:
1. **Groq** (Free) - Ultra-fast, good for testing
2. **HuggingFace** (Free) - Many models, rate-limited

**For Production**:
1. **OpenRouter** (Tier 2) - Best all-around choice, 200+ models
2. **Together AI** (Tier 1) - Cheap, fast, good for high-volume

**For Premium Features**:
1. **Anthropic Direct** (Tier 3) - Latest Claude models
2. **OpenAI Direct** (Tier 3) - Latest GPT models

### Cost Optimization

**Tips**:
1. Use local vLLM for tasks that don't need proprietary models
2. Route simple queries to Groq (free, fast)
3. Use OpenRouter for complex tasks (access to all models)
4. Enable Wilmer smart routing (auto-selects cheapest model for task)
5. Set up caching in Redis (reduces duplicate API calls)

### Monitoring

**Check LiteLLM health**:
```bash
docker logs unicorn-litellm-wilmer -f
```

**Check Wilmer router**:
```bash
docker logs unicorn-wilmer-router -f
```

**View metrics**:
```bash
curl http://localhost:4000/metrics  # Prometheus metrics
```

**Database queries**:
```bash
# Connect to PostgreSQL
docker exec -it unicorn-postgresql psql -U unicorn -d unicorn_db

# Check usage
SELECT model, count(*), sum(usage_tokens)
FROM litellm_usage
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY model;
```

---

## Troubleshooting

### If containers won't start:

```bash
# Check logs
docker compose -f docker-compose.litellm.yml logs

# Check if ports are available
sudo netstat -tulpn | grep -E '4000|4001'

# Remove and rebuild
docker compose -f docker-compose.litellm.yml down
docker compose -f docker-compose.litellm.yml up -d
```

### If API keys aren't working:

```bash
# Verify environment variables loaded
docker exec unicorn-litellm-wilmer printenv | grep API_KEY

# Test provider directly (example: Groq)
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_GROQ_API_KEY"
```

### If no models appear:

```bash
# Check config file is mounted
docker exec unicorn-litellm-wilmer cat /app/config.yaml | head -20

# Check LiteLLM logs
docker logs unicorn-litellm-wilmer --tail 100
```

---

## Next Steps

1. ✅ Add at least one provider API key to `.env.litellm`
2. ✅ Start LiteLLM stack with `docker compose up -d`
3. ✅ Verify containers are running with `docker ps`
4. ✅ Test health endpoint with `curl http://localhost:4000/health`
5. ✅ Restart Ops-Center backend with `docker restart ops-center-direct`
6. ✅ Test end-to-end inference via Ops-Center API
7. ⏳ Add additional provider keys as needed
8. ⏳ Monitor usage and costs via Ops-Center dashboard

---

## Support Resources

- **LiteLLM Documentation**: https://docs.litellm.ai/
- **Provider Docs**:
  - Groq: https://console.groq.com/docs
  - OpenRouter: https://openrouter.ai/docs
  - Together AI: https://docs.together.ai/
- **UC-Cloud Docs**: `/home/muut/Production/UC-Cloud/CLAUDE.md`
- **Ops-Center Docs**: `/home/muut/Production/UC-Cloud/services/ops-center/CLAUDE.md`

---

**Configuration Agent Task: COMPLETE ✅**

All files are ready. User can now add API keys and deploy LiteLLM!
