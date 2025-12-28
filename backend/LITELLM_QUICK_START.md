# LiteLLM Backend - Quick Start Guide

**Status**: Backend integrated, ready for configuration
**Date**: October 20, 2025

---

## 1. Generate Encryption Key (REQUIRED)

**WARNING**: This key must NEVER change after users add API keys!

```bash
# Generate key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Example output:
# vK8hs2D-xE3mQBpiWv7gZushLHy0WGhPNKpjulz1ygB=
```

Copy the output and add to `.env.auth`:

```bash
# Edit .env.auth
nano /home/muut/Production/UC-Cloud/services/ops-center/.env.auth

# Add this line (replace with your generated key):
BYOK_ENCRYPTION_KEY=vK8hs2D-xE3mQBpiWv7gZushLHy0WGhPNKpjulz1ygB=
```

---

## 2. Verify Configuration (Optional)

Check that LiteLLM URLs are correct in `.env.auth`:

```bash
# LiteLLM Proxy URL (for OpenAI-compatible API)
LITELLM_PROXY_URL=http://localhost:4000

# Wilmer Router URL (smart model routing)
WILMER_ROUTER_URL=http://localhost:4001
```

Update if your services run on different ports/hosts.

---

## 3. Restart Backend

```bash
# From UC-Cloud root
cd /home/muut/Production/UC-Cloud

# Restart ops-center
docker restart ops-center-direct

# Wait for startup (5-10 seconds)
sleep 10
```

---

## 4. Verify Initialization

Check logs for success messages:

```bash
docker logs ops-center-direct | grep -i litellm
```

**Expected output**:
```
INFO: LiteLLM Credit System initialized successfully
INFO: BYOK Manager initialized successfully
INFO: Wilmer Router initialized (wilmer: ..., litellm: ...)
INFO: Provider Health Monitor initialized successfully
INFO: Background health monitoring started
INFO: ✅ LiteLLM backend system fully initialized and operational
```

---

## 5. Test API Endpoints

```bash
# Test models endpoint (should return available models)
curl http://localhost:8084/api/v1/litellm/models

# Test provider health
curl http://localhost:8084/api/v1/litellm/providers/health
```

---

## Troubleshooting

### "BYOK_ENCRYPTION_KEY not set" warning in logs

**Problem**: Missing encryption key
**Solution**: Add `BYOK_ENCRYPTION_KEY` to `.env.auth` (see step 1)
**Impact**: User API keys won't persist across restarts

### "Failed to initialize LiteLLM backend system"

**Problem**: Database or Redis connection failure
**Solution**:
```bash
# Check PostgreSQL is running
docker ps | grep postgresql

# Check Redis is running
docker ps | grep redis

# Restart if needed
docker restart unicorn-postgresql unicorn-redis
docker restart ops-center-direct
```

### Import errors

**Problem**: Module not found
**Solution**: Verify all files exist
```bash
cd /home/muut/Production/UC-Cloud/services/ops-center/backend
ls -lh litellm_*.py wilmer_router.py byok_manager.py model_selector.py provider_health.py
```

---

## Next Steps

After backend is running successfully:

1. **Database Agent**: Initialize LiteLLM database tables
2. **Frontend Agent**: Build UI for model selection and BYOK
3. **Testing Agent**: End-to-end testing

---

## Quick Reference

### Environment Variables
- `BYOK_ENCRYPTION_KEY` - Fernet encryption key (REQUIRED)
- `LITELLM_PROXY_URL` - LiteLLM proxy endpoint
- `WILMER_ROUTER_URL` - Wilmer router endpoint

### API Endpoints (10 total)
- `POST /api/v1/litellm/chat/completions` - Chat
- `GET /api/v1/litellm/models` - List models
- `GET /api/v1/litellm/providers/health` - Provider status
- `POST /api/v1/litellm/byok/keys` - Add BYOK key
- `GET /api/v1/litellm/credits` - Check credits

### Logs
```bash
# All logs
docker logs ops-center-direct -f

# LiteLLM only
docker logs ops-center-direct | grep -i litellm

# Errors only
docker logs ops-center-direct | grep -i error
```

### Container Management
```bash
# Restart
docker restart ops-center-direct

# Status
docker ps | grep ops-center

# Exec into container
docker exec -it ops-center-direct bash
```

---

**Documentation**: `/backend/LITELLM_BACKEND_INTEGRATION_COMPLETE.md`
