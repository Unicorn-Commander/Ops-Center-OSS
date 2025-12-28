# LLM Provider Testing Guide

**Last Updated**: October 20, 2025
**Status**: Ready for Testing

---

## 🎯 What You Now Have

### ✅ Deployed Components

1. **Database** - 4 tables created with OpenRouter key pre-populated
2. **Backend API** - 17 endpoints at `/api/v1/llm-config/*`
3. **Frontend UI** - Accessible at `/admin/system/llm-providers`
4. **Navigation Link** - "LLM Providers" in sidebar under System Management
5. **Pre-populated Key** - OpenRouter API key ready for testing

### 🔍 Where to Find It

**URL**: `https://your-domain.com/admin/system/llm-providers`

**Navigation Path**:
1. Login to Ops-Center as admin
2. Look in left sidebar under "System Management Console"
3. Find "LLM Providers" (sparkles icon ✨) below "Email Settings"
4. Click to access the management interface

---

## 🧪 Testing LLM Inference from Ops-Center

### Current Status

**OpenRouter Key**: ✅ Pre-populated and active for chat
- Provider: `openrouter`
- Key: `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`
- Status: Enabled for ops-center usage
- Purpose: Active provider for "chat"

### Option 1: Test via UI (Recommended)

1. **Navigate to LLM Providers page**
   ```
   https://your-domain.com/admin/system/llm-providers
   ```

2. **Go to "API Keys" tab**
   - You should see "Default OpenRouter Key"
   - Status: Enabled (green checkmark)
   - Uses: Chat ✓

3. **Test the connection**
   - Click the "Test Connection" button on the OpenRouter key card
   - This will make a test API call to validate the key works
   - Expected result: "Connection successful" with model list

### Option 2: Test via API (Direct)

```bash
# Test the OpenRouter key directly
curl -X POST "https://your-domain.com/api/v1/llm-config/api-keys/1/test" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json"

# Expected response:
{
  "success": true,
  "provider": "openrouter",
  "models_available": 100+,
  "latency_ms": 250
}
```

### Option 3: Test LLM Routing (Full Integration)

**Prerequisites**: Ops-Center needs to integrate LLM routing with the configured providers.

**Current Gap**: The LLM router (`backend/llm_router.py`) needs to be updated to:
1. Query `active_providers` table to get which provider to use
2. If provider_type = "api_key", fetch the encrypted key from `llm_api_keys`
3. Decrypt the key with Fernet
4. Make the LLM call to the selected provider

**Test Command** (once integrated):
```bash
# Make a chat completion request through Ops-Center
curl -X POST "https://your-domain.com/api/v1/llm/chat/completions" \
  -H "Cookie: session_token=YOUR_SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openai/gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello, test message"}]
  }'

# This should route through OpenRouter (active provider for chat)
```

---

## 🚧 What Still Needs to Be Done

### 1. Encryption Key Configuration ⚠️ CRITICAL

**Issue**: API keys are stored in database without proper Fernet encryption.

**Fix Required**:
```bash
# 1. Generate encryption key
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# 2. Add to environment
echo "BYOK_ENCRYPTION_KEY=$ENCRYPTION_KEY" >> /home/muut/Production/UC-Cloud/services/ops-center/.env.auth

# 3. Restart backend
docker restart ops-center-direct

# 4. Re-encrypt existing keys (run this script)
docker exec ops-center-direct python3 /app/scripts/re_encrypt_api_keys.py
```

### 2. LLM Router Integration

**Current State**: LLM router exists but doesn't use the new provider system yet.

**File to Update**: `backend/llm_router.py`

**Changes Needed**:
```python
# In llm_router.py, add this to __init__:
from llm_config_manager import LLMConfigManager

self.config_manager = LLMConfigManager(db_pool, encryption_key)

# Add method to get active provider:
async def get_active_llm_provider(self, purpose="chat"):
    """Get the active LLM provider configuration"""
    # Query active_providers table
    active = await self.config_manager.get_active_provider(purpose)

    if active['provider_type'] == 'api_key':
        # Fetch and decrypt API key
        key_data = await self.config_manager.get_api_key(active['provider_id'])
        return {
            'type': 'api_key',
            'provider': key_data['provider'],
            'api_key': key_data['decrypted_key'],
            'base_url': PROVIDER_URLS[key_data['provider']]
        }
    elif active['provider_type'] == 'ai_server':
        # Fetch AI server config
        server = await self.config_manager.get_ai_server(active['provider_id'])
        return {
            'type': 'ai_server',
            'server_type': server['server_type'],
            'base_url': server['base_url'],
            'api_key': server['api_key']
        }

# Update route_request() to use get_active_llm_provider()
```

### 3. PostgreSQL Authentication Fix

**Issue**: Some initialization scripts fail with "password authentication failed for user unicorn"

**Temporary Workaround**: Using `docker exec` with SQL for direct access (already done)

**Permanent Fix**: Update database connection strings to use correct credentials.

**Check current credentials**:
```bash
# Inside ops-center-direct container
docker exec ops-center-direct printenv | grep POSTGRES

# Or check .env.auth
grep POSTGRES /home/muut/Production/UC-Cloud/services/ops-center/.env.auth
```

### 4. Usage Tracking Integration

**Purpose**: Track LLM API usage for billing and analytics

**Table Exists**: `llm_usage_log` (created but not populated)

**Integration Points**:
- After each LLM call, log to `llm_usage_log`
- Track: user_id, provider_id, model, tokens, cost, latency, timestamp
- Aggregate for billing dashboard
- Alert on quota limits

---

## 📋 Step-by-Step Testing Checklist

### Phase 1: Verify Deployment ✅ (Complete)

- [x] Database tables created
- [x] OpenRouter key pre-populated
- [x] Active provider set for chat
- [x] Backend API endpoints registered
- [x] Frontend UI built and deployed
- [x] Navigation link added to sidebar
- [x] All files deployed to production

### Phase 2: UI Testing (Do This Now)

- [ ] **Login** to Ops-Center as admin
- [ ] **Navigate** to "LLM Providers" in sidebar
- [ ] **Verify** page loads with two tabs (AI Servers / API Keys)
- [ ] **Check** API Keys tab shows "Default OpenRouter Key"
- [ ] **Click** "Test Connection" button
- [ ] **Confirm** test passes and shows available models
- [ ] **Try** adding a new AI server (optional)
- [ ] **Try** adding another API key (optional)

### Phase 3: Backend Integration (Next Steps)

- [ ] Add `BYOK_ENCRYPTION_KEY` to environment
- [ ] Update `llm_router.py` to use provider system
- [ ] Test LLM routing through Ops-Center API
- [ ] Verify usage logging works
- [ ] Test failover to backup provider
- [ ] Monitor performance and latency

### Phase 4: Production Validation

- [ ] Load test with 100 concurrent requests
- [ ] Verify encryption/decryption works correctly
- [ ] Test all provider types (OpenRouter, OpenAI, Anthropic)
- [ ] Test AI server connections (vLLM, Ollama)
- [ ] Verify audit logging captures all operations
- [ ] Test admin-only access control

---

## 🎯 Quick Test Script

Save this as `/tmp/test_llm_providers.sh`:

```bash
#!/bin/bash

echo "=== LLM Provider System Test ==="
echo ""

# Test 1: Check database
echo "1. Checking database..."
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT id, provider, key_name, use_for_ops_center FROM llm_api_keys;" | grep -i openrouter
if [ $? -eq 0 ]; then
    echo "   ✅ OpenRouter key found in database"
else
    echo "   ❌ OpenRouter key not found"
fi

# Test 2: Check backend API
echo ""
echo "2. Checking backend API..."
RESPONSE=$(curl -s http://localhost:8084/api/v1/llm-config/health)
if echo "$RESPONSE" | grep -q "healthy"; then
    echo "   ✅ Backend API responding"
else
    echo "   ❌ Backend API not responding"
fi

# Test 3: Check frontend files
echo ""
echo "3. Checking frontend deployment..."
if [ -f "/home/muut/Production/UC-Cloud/services/ops-center/public/assets/LLMProviderSettings-BMmaRIT2.js" ]; then
    echo "   ✅ Frontend bundle deployed"
else
    echo "   ❌ Frontend bundle missing"
fi

# Test 4: Check active provider
echo ""
echo "4. Checking active provider..."
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT purpose, provider_type, provider_id FROM active_providers WHERE purpose='chat';" | grep -i api_key
if [ $? -eq 0 ]; then
    echo "   ✅ Active provider configured for chat"
else
    echo "   ❌ No active provider for chat"
fi

echo ""
echo "=== Test Complete ==="
echo ""
echo "Next: Login to https://your-domain.com/admin/system/llm-providers"
echo "and click 'Test Connection' on the OpenRouter key."
```

Run with:
```bash
chmod +x /tmp/test_llm_providers.sh
/tmp/test_llm_providers.sh
```

---

## 🔐 Security Notes

### Current State
- ⚠️ API keys stored **WITHOUT proper encryption** (placeholder only)
- ⚠️ Need to add `BYOK_ENCRYPTION_KEY` to environment
- ✅ Admin-only access control working
- ✅ Session-based authentication via Keycloak
- ✅ Audit logging enabled

### Production Requirements
1. **Add encryption key** - Generate and store securely
2. **Re-encrypt keys** - Run migration script to encrypt existing keys
3. **Rotate keys** - Implement key rotation policy (every 90 days)
4. **Monitor access** - Review audit logs regularly
5. **Test failover** - Ensure backup providers work

---

## 📞 Next Actions

### For You (User):

1. **Login to Ops-Center**: https://your-domain.com
2. **Go to LLM Providers**: Click link in sidebar (under System Management)
3. **Test OpenRouter Key**: Click "Test Connection" button
4. **Report Back**: Let me know if you see the page and if the test passes

### For Development:

1. **Add encryption key** to environment (5 min)
2. **Integrate with LLM router** (30 min)
3. **Test inference** end-to-end (15 min)
4. **Add usage tracking** (1 hour)

---

## 📚 Related Documentation

- **Deployment Summary**: `LLM_PROVIDER_MANAGEMENT_DEPLOYED.md`
- **API Reference**: `backend/docs/LLM_CONFIG_API.md`
- **Routes Config**: `src/config/routes.js` (lines 288-295)
- **Database Schema**: `backend/sql/llm_config_schema.sql`

---

**Status**: System deployed and ready for UI testing. Backend integration pending.

**Priority**: Test the UI first, then we'll integrate with the LLM router.
