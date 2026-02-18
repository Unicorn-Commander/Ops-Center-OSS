# LiteLLM Quick Start Guide

**Get LiteLLM running in 30 minutes**

---

## Overview

LiteLLM provides multi-provider LLM routing with intelligent model selection, credit management, and BYOK (Bring Your Own Key) support for UC-Cloud Ops-Center.

**Features**:
- 47 models across 9 providers (OpenAI, Anthropic, Groq, etc.)
- 6 tiers (Free to Premium)
- Credit system with power levels (ECO, BALANCED, PRECISION)
- BYOK support (users can use their own API keys)
- WilmerAI intelligent routing
- Full usage tracking and analytics

---

## Quick Start (30 Minutes)

### Step 1: Fix Critical Dependency (5 min)

```bash
cd /opt/ops-center

# Add litellm package
echo "litellm>=1.40.0" >> backend/requirements.txt

# Rebuild container
docker compose -f docker-compose.direct.yml build

# Verify
docker exec ops-center-direct python3 -c "import litellm; print('OK')"
```

### Step 2: Initialize Database (5 min)

```bash
# Create tables and seed data
docker exec ops-center-direct python3 /app/scripts/initialize_litellm_db.py

# Verify tables created
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt litellm*"

# Should show 7 tables:
# - litellm_providers
# - litellm_models
# - litellm_model_providers
# - litellm_user_credits
# - litellm_credit_transactions
# - litellm_usage_logs
# - litellm_byok_keys
```

### Step 3: Configure API Keys (10 min)

```bash
# Create environment file
cd /opt/ops-center

cat > .env.litellm << 'EOF'
# Master Key (REQUIRED)
LITELLM_MASTER_KEY=sk-litellm-YOUR_RANDOM_32_CHAR_KEY_HERE

# Database (REQUIRED)
POSTGRES_PASSWORD=unicorn

# Free Tier Provider (RECOMMENDED for testing)
GROQ_API_KEY=gsk_YOUR_GROQ_API_KEY_HERE

# Optional Paid Providers
OPENROUTER_API_KEY=sk-or-YOUR_KEY_HERE
OPENAI_API_KEY=sk-YOUR_KEY_HERE
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
HUGGINGFACE_API_KEY=hf_YOUR_KEY_HERE
TOGETHER_API_KEY=YOUR_KEY_HERE
DEEPINFRA_API_KEY=YOUR_KEY_HERE
FIREWORKS_API_KEY=fw_YOUR_KEY_HERE

# Local Providers (no keys needed)
OLLAMA_HOST=http://unicorn-ollama:11434
VLLM_HOST=http://unicorn-vllm:8000
EOF

# Set secure permissions
chmod 600 .env.litellm
```

**Get Free API Keys**:
- **Groq** (recommended): https://console.groq.com/keys
  - Free tier: 30 requests/minute
  - Ultra-fast inference
  - Models: Llama 3 70B, Mixtral 8x7B

- **HuggingFace**: https://huggingface.co/settings/tokens
  - Free tier available
  - Many open-source models

### Step 4: Deploy LiteLLM Services (5 min)

```bash
# Start containers
docker compose -f docker-compose.litellm.yml up -d

# Check status
docker ps | grep -E "litellm|wilmer"

# Expected output:
# unicorn-litellm-wilmer  (port 4000)
# unicorn-wilmer-router   (port 4001)

# View logs
docker logs unicorn-litellm-wilmer --tail 50
```

### Step 5: Restart Ops-Center (2 min)

```bash
# Restart to load new routes
docker restart ops-center-direct

# Wait for startup
sleep 10

# Verify routes registered
docker logs ops-center-direct | grep -E "litellm|byok"
```

### Step 6: Test Deployment (3 min)

```bash
# Run automated tests
./test_litellm_basic.sh

# Should pass 10/10 tests

# Manual health check
curl http://localhost:4000/health
# Expected: {"status": "healthy"}

curl http://localhost:8084/api/v1/llm/health
# Expected: {"status": "healthy", "litellm_connected": true}

# List available models
curl http://localhost:8084/api/v1/llm/models
# Expected: JSON array with 47 models
```

---

## First API Call

### Test Chat Completion (Free Tier)

```bash
# Get authentication token (from Ops-Center login)
TOKEN="your-session-token-here"

# Send chat request
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "llama3-70b-groq",
    "messages": [
      {"role": "user", "content": "Hello! What is 2+2?"}
    ],
    "power_level": "eco",
    "user_email": "test@example.com"
  }'

# Expected response:
# {
#   "id": "chatcmpl-...",
#   "model": "llama3-70b-groq",
#   "choices": [{
#     "message": {
#       "role": "assistant",
#       "content": "Hello! 2+2 equals 4."
#     }
#   }],
#   "usage": {
#     "prompt_tokens": 12,
#     "completion_tokens": 8,
#     "total_tokens": 20
#   }
# }
```

### Check Credit Balance

```bash
curl http://localhost:8084/api/v1/llm/credits/balance \
  -H "Authorization: Bearer $TOKEN"

# Expected:
# {
#   "credits_remaining": 1000,
#   "credits_total": 1000,
#   "tier": "free"
# }
```

---

## Common Commands

### View Logs
```bash
# LiteLLM proxy
docker logs unicorn-litellm-wilmer -f

# WilmerAI router
docker logs unicorn-wilmer-router -f

# Ops-Center backend
docker logs ops-center-direct -f
```

### Check Database
```bash
# List users with credits
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT user_id, credits_remaining FROM litellm_user_credits;"

# View recent usage
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT * FROM litellm_usage_logs ORDER BY created_at DESC LIMIT 10;"

# Check providers
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -c "SELECT provider_name, is_active, health_status FROM litellm_providers;"
```

### Restart Services
```bash
# Restart all LiteLLM services
docker compose -f docker-compose.litellm.yml restart

# Restart specific service
docker restart unicorn-litellm-wilmer

# Reload configuration (after editing litellm_config.yaml)
docker restart unicorn-litellm-wilmer
```

---

## Model Selection Guide

### Power Levels

**ECO** (Cheapest):
- Best for: Simple queries, testing, high-volume
- Models: Groq (free), Together AI ($0.001/1k tokens)
- Cost: $0-0.003 per 1k tokens

**BALANCED** (Recommended):
- Best for: General use, production workloads
- Models: OpenRouter, Fireworks AI ($0.01-0.03/1k tokens)
- Cost: $0.01-0.03 per 1k tokens

**PRECISION** (Highest Quality):
- Best for: Complex reasoning, critical tasks
- Models: GPT-4, Claude 3.5 ($0.05-0.15/1k tokens)
- Cost: $0.05-0.15 per 1k tokens

**CUSTOM** (Manual Selection):
- User specifies exact model
- Full control over model choice

### Model Tiers

| Tier | Cost Range | Providers | Use Cases |
|------|------------|-----------|-----------|
| **FREE** | $0.00 | Groq, Local (vLLM/Ollama) | Testing, development |
| **STARTER** | $0.001-0.003 | Together AI, DeepInfra | High-volume, simple tasks |
| **BALANCED** | $0.01-0.03 | OpenRouter, Fireworks AI | General production |
| **PROFESSIONAL** | $0.05-0.15 | OpenAI, Anthropic | Quality-critical work |
| **PREMIUM** | $0.50-2.00 | GPT-4 Turbo, Claude Opus | Maximum capability |
| **SPECIALIZED** | Variable | Code models, embeddings | Domain-specific |

---

## BYOK (Bring Your Own Key)

Users can use their own API keys instead of consuming platform credits.

### User Flow

1. User navigates to Ops-Center → Settings → API Keys
2. Clicks "Add API Key"
3. Selects provider (OpenAI, Anthropic, etc.)
4. Pastes API key
5. Key is encrypted and stored
6. User can now use that provider without credits

### Example Request with BYOK

```bash
curl -X POST http://localhost:8084/api/v1/llm/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "byok": true,
    "provider": "openai"
  }'

# User's OpenAI API key will be used
# No credits deducted
```

---

## Troubleshooting

### Problem: Container won't start

```bash
# Check logs
docker logs unicorn-litellm-wilmer

# Common causes:
# 1. Missing LITELLM_MASTER_KEY in .env.litellm
# 2. Invalid YAML syntax in litellm_config.yaml
# 3. Database not accessible
# 4. Port 4000 already in use

# Fix: Verify environment
docker compose -f docker-compose.litellm.yml config

# Recreate container
docker compose -f docker-compose.litellm.yml up -d --force-recreate
```

### Problem: "Module not found: litellm"

```bash
# Fix: Add to requirements.txt
echo "litellm>=1.40.0" >> backend/requirements.txt

# Rebuild
docker compose -f docker-compose.direct.yml build
docker restart ops-center-direct

# Verify
docker exec ops-center-direct python3 -c "import litellm; print('OK')"
```

### Problem: "Provider not configured"

```bash
# Check if API key is set
docker exec unicorn-litellm-wilmer env | grep GROQ_API_KEY

# If empty, add to .env.litellm
echo "GROQ_API_KEY=gsk_YOUR_KEY_HERE" >> .env.litellm

# Restart to reload environment
docker restart unicorn-litellm-wilmer
```

### Problem: High latency

```bash
# Check provider health
curl http://localhost:8084/api/v1/llm/providers/health

# Switch to faster provider
# Use power_level: "eco" for Groq (ultra-fast)

# Check Redis cache
docker exec unicorn-redis redis-cli ping
```

---

## Next Steps

### Week 1: Basic Operation
- ✅ Deploy with Groq (free tier)
- ✅ Test chat completions
- ✅ Verify credit system
- ✅ Monitor logs for errors

### Week 2: Add Providers
- Add OpenRouter API key
- Add OpenAI API key
- Test BYOK functionality
- Configure cost limits

### Week 3: Integration
- Connect Brigade agents
- Enable Lago billing
- Set up monitoring alerts
- Create user documentation

### Week 4: Optimization
- Analyze usage patterns
- Optimize routing rules
- Fine-tune cost limits
- Performance tuning

---

## Resources

**Documentation**:
- Full guide: `LITELLM_DEPLOYMENT_CHECKLIST.md`
- Verification report: `LITELLM_VERIFICATION_REPORT.md`
- This quick start: `LITELLM_QUICK_START.md`

**Testing**:
- Basic tests: `./test_litellm_basic.sh`
- Schema tests: `backend/tests/test_litellm_schema.py`
- BYOK tests: `backend/tests/test_byok.py`

**Configuration**:
- Models: `litellm_config.yaml`
- Docker: `docker-compose.litellm.yml`
- Environment: `.env.litellm`

**Database**:
- Schema: `backend/sql/litellm_schema.sql`
- Init script: `backend/scripts/initialize_litellm_db.py`

---

## Support

**Issues?** Check in this order:
1. Run `./test_litellm_basic.sh`
2. Review logs: `docker logs unicorn-litellm-wilmer`
3. Consult `LITELLM_DEPLOYMENT_CHECKLIST.md`
4. Check database: `docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "\dt litellm*"`

**Questions?**
- Code review: See `LITELLM_VERIFICATION_REPORT.md`
- Deployment steps: See `LITELLM_DEPLOYMENT_CHECKLIST.md`
- API usage: See `backend/examples/wilmer_routing_examples.py`

---

**Ready to deploy?** Follow Step 1-6 above. Total time: 30 minutes.

**Already deployed?** Try the "First API Call" example to test it out!
