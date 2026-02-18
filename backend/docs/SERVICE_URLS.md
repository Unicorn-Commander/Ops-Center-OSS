# UC-Cloud Services - Access URLs & Integration Guide

> **Last Updated**: November 1, 2025
> **Infrastructure**: UC-Cloud Production Environment
> **Domain**: unicorncommander.ai

## Overview

This document provides the access URLs, authentication details, and integration information for all UC-Cloud services available in the marketplace.

---

## 🌐 Production Service URLs

### Featured Services (Included FREE)

| Service | Access URL | Port | SSO Provider | Realm | Status |
|---------|-----------|------|--------------|-------|--------|
| **Open-WebUI** | https://chat.unicorncommander.ai | 8080 | Keycloak | uchub | ✅ Active |
| **Center-Deep Pro** | https://search.unicorncommander.ai | 8888 | Authentik | - | ✅ Active |

### Premium Services (Paid Add-ons)

| Service | Access URL | Port | SSO Provider | Realm | Status |
|---------|-----------|------|--------------|-------|--------|
| **Presenton** | https://presentations.unicorncommander.ai | 3000 | Keycloak | uchub | ✅ Active |
| **Bolt.DIY** | https://bolt.unicorncommander.ai | 5173 | Keycloak | uchub | ✅ Active |
| **Unicorn Brigade** | https://brigade.unicorncommander.ai | 8102 | Keycloak | uchub | ✅ Active |

### Voice Services (Specialized Add-ons)

| Service | Access URL | API URL | Port | SSO Provider | Status |
|---------|-----------|---------|------|--------------|--------|
| **Amanuensis (STT)** | https://stt.unicorncommander.ai | https://stt.unicorncommander.ai/v1 | 9003 | Authentik | ✅ Active |
| **Orator (TTS)** | https://tts.unicorncommander.ai | https://tts.unicorncommander.ai/v1 | 8885 | Authentik | ✅ Active |

### Coming Soon

| Service | Expected URL | Expected Release | Status |
|---------|-------------|------------------|--------|
| **MagicDeck** | https://magicdeck.unicorncommander.ai | Q1 2026 | 🚧 Development |

---

## 🔐 Authentication & SSO

### Keycloak (uchub realm)

**Primary SSO Provider for Main Services**

- **Admin Console**: https://auth.unicorncommander.ai/admin/uchub/console/
- **Realm**: `uchub`
- **Container**: `uchub-keycloak`
- **Internal URL**: `http://uchub-keycloak:8080`
- **Admin Credentials**:
  - Username: `admin`
  - Password: `your-admin-password`

**Configured Services:**
- Open-WebUI
- Presenton
- Bolt.DIY
- Unicorn Brigade

**Identity Providers Enabled:**
- ✅ Google (alias: `google`)
- ✅ GitHub (alias: `github`)
- ✅ Microsoft (alias: `microsoft`)

**OAuth Client Configuration:**
```yaml
Client ID: ops-center
Client Secret: your-keycloak-client-secret
Type: Confidential (OpenID Connect)
Redirect URIs:
  - https://unicorncommander.ai/auth/callback
  - http://localhost:8000/auth/callback
Web Origins:
  - https://unicorncommander.ai
  - http://localhost:8000
```

### Authentik

**Secondary SSO Provider for Legacy Services**

- **Admin Console**: https://auth.unicorncommander.ai/if/flow/initial-setup/
- **Container**: `authentik-server`
- **Admin Credentials**:
  - Username: `akadmin`
  - Token: `your-authentik-api-token`

**Configured Services:**
- Center-Deep Pro
- Amanuensis (STT)
- Orator (TTS)

**OAuth Applications:**

1. **center-deep**
   - Client ID: `center-deep`
   - Client Secret: `centerdeep_oauth_secret_2025`
   - Redirect URIs: `https://search.unicorncommander.ai/auth/callback`

2. **amanuensis**
   - Client ID: `amanuensis`
   - Requires API key authentication

3. **orator**
   - Client ID: `orator`
   - Requires API key authentication

---

## 🚀 Service Activation Flow

### For FREE Services (Open-WebUI, Center-Deep)

**Automatic activation upon UC-Cloud subscription:**

1. User completes registration and payment on ops-center
2. User profile created in Keycloak/Authentik
3. User automatically granted access to FREE services
4. Services immediately accessible at their URLs
5. Welcome email sent with getting started guide

**No additional steps required** - user can immediately access:
- https://chat.unicorncommander.ai (Open-WebUI)
- https://search.unicorncommander.ai (Center-Deep)

### For PREMIUM Services (Presenton, Bolt, Brigade)

**User subscribes via marketplace:**

1. User browses marketplace at https://unicorncommander.ai/marketplace
2. User clicks "Subscribe" on desired service
3. Payment processed via Stripe integration
4. Backend creates subscription record in `service_subscriptions` table
5. User added to service-specific Keycloak client group
6. SSO automatically grants access to service URL
7. User receives welcome email with:
   - Service access URL
   - Getting started guide
   - API documentation (if applicable)
   - Trial period information (14 days)

**Backend Database Updates:**
```sql
-- Subscription created
INSERT INTO service_subscriptions (
    user_id,
    addon_id,
    subscribed_at,
    expires_at,
    status,
    trial_ends_at,
    is_trial
) VALUES (
    'user-uuid',
    addon_id,
    NOW(),
    NOW() + INTERVAL '1 month',
    'trial',
    NOW() + INTERVAL '14 days',
    TRUE
);

-- User-addon relationship created
INSERT INTO user_add_ons (
    user_id,
    add_on_id,
    enabled,
    installed_at
) VALUES (
    'user-uuid',
    addon_id,
    TRUE,
    NOW()
);
```

### For VOICE SERVICES (Amanuensis, Orator)

**Requires API key generation:**

1. User subscribes via marketplace
2. Payment processed
3. Backend generates API key for user
4. API key stored in user profile (encrypted)
5. User receives:
   - Service access URL (web UI)
   - API key for programmatic access
   - API documentation
   - SDK download links (Python, JavaScript)
   - Usage limits and tracking dashboard

**API Authentication Example:**
```bash
# Amanuensis (Speech-to-Text)
curl -X POST https://stt.unicorncommander.ai/v1/transcribe \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -F "file=@meeting.mp3"

# Orator (Text-to-Speech)
curl -X POST https://tts.unicorncommander.ai/v1/synthesize \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, world!",
    "voice": "en-US-Neural",
    "emotion": "happy"
  }'
```

---

## 📊 Usage Tracking & Limits

### FREE Services
- **Open-WebUI**: Unlimited conversations, 10GB document storage
- **Center-Deep**: Unlimited searches, no rate limiting

### PREMIUM Services
- **Presenton**: 100 presentations/month
- **Bolt.DIY**: 500 AI generations/month, 100 deployments/month, 50GB storage
- **Unicorn Brigade**: 1000 orchestrations/month, 50 custom agents, 10,000 tool calls/month

### VOICE Services
- **Amanuensis**: 300 hours transcription/month
- **Orator**: 500,000 characters/month

**Usage tracking backend:**
```sql
-- Track service usage
CREATE TABLE service_usage (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    addon_id INTEGER REFERENCES add_ons(id),
    usage_date DATE DEFAULT CURRENT_DATE,
    usage_count INTEGER DEFAULT 0,
    usage_type VARCHAR(50), -- 'api_call', 'generation', 'transcription', etc.
    metadata JSONB,
    UNIQUE(user_id, addon_id, usage_date, usage_type)
);
```

---

## 🔧 API Integration

### Services with Public APIs

#### Amanuensis (Speech-to-Text)
```python
# Python SDK Example
from unicorn_amanuensis import AmanuensisClient

client = AmanuensisClient(api_key="YOUR_API_KEY")
result = client.transcribe("meeting.mp3", diarization=True)
print(result.text)
print(result.speakers)  # Who said what
```

#### Orator (Text-to-Speech)
```javascript
// JavaScript SDK Example
import { OratorClient } from '@unicorn-cloud/orator';

const client = new OratorClient({ apiKey: 'YOUR_API_KEY' });
const audio = await client.synthesize({
  text: 'Welcome to UC-Cloud!',
  voice: 'en-US-Neural',
  emotion: 'excited'
});
await audio.save('welcome.mp3');
```

#### Bolt.DIY API
```bash
# Deploy a project via API
curl -X POST https://bolt.unicorncommander.ai/api/v1/deploy \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "my-project",
    "target": "vercel",
    "env_vars": {"API_KEY": "xxx"}
  }'
```

---

## 🛠️ Docker & Infrastructure

### Network Configuration

All services are connected via Docker networks:
- **web**: External-facing services via Traefik
- **unicorn-network**: Internal service communication
- **uchub-network**: Keycloak realm network

### Container Names

| Service | Container Name | Networks |
|---------|---------------|----------|
| Ops Center | ops-center-direct | web, unicorn-network, uchub-network |
| Open-WebUI | unicorn-open-webui | web, unicorn-network |
| Center-Deep | unicorn-center-deep | web, unicorn-network |
| Presenton | unicorn-presenton | web, unicorn-network, uchub-network |
| Bolt.DIY | unicorn-bolt | web, unicorn-network, uchub-network |
| Brigade | unicorn-brigade | web, unicorn-network, uchub-network |
| Amanuensis | unicorn-amanuensis | web, unicorn-network |
| Orator | unicorn-orator | web, unicorn-network |
| Keycloak | uchub-keycloak | uchub-network, web |
| Authentik | authentik-server | web, unicorn-network |
| Traefik | traefik | web |

### SSL/TLS Certificates

- Managed by **Traefik** with Let's Encrypt
- Auto-renewal configured
- Wildcard certificate for `*.unicorncommander.ai`
- All services accessible via HTTPS

---

## 📝 Service Management Scripts

### Check Service Status
```bash
# Check all UC-Cloud services
docker ps --filter "name=unicorn-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check specific service
docker logs unicorn-open-webui --tail 100
```

### Restart Service
```bash
# Restart single service
docker restart unicorn-open-webui

# Restart all services
cd /opt/uc-cloud/services
docker-compose restart
```

### View Service Logs
```bash
# Real-time logs
docker logs -f unicorn-open-webui

# Last 100 lines with timestamps
docker logs --tail 100 -t unicorn-open-webui
```

### Test SSO Authentication
```bash
# Run automated SSO verification
cd /opt/ops-center/backend/tests
python3 verify_uchub_sso.py
```

---

## 🐛 Troubleshooting

### Service Not Accessible

**Check container status:**
```bash
docker ps -a | grep unicorn-service-name
```

**Check if on correct networks:**
```bash
docker network inspect web | grep unicorn-service-name
```

**Add to network if missing:**
```bash
docker network connect web unicorn-service-name
docker network connect unicorn-network unicorn-service-name
```

### SSO Login Issues

**Check Keycloak realm:**
```bash
# Access Keycloak admin console
open https://auth.unicorncommander.ai/admin/uchub/console/

# Verify client configuration
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get clients \
  --realm uchub --fields clientId,redirectUris
```

**Check user group membership:**
```bash
# User should be in service-specific groups
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query email=user@example.com
```

### API Key Issues

**Regenerate API key:**
```bash
# Run ops-center API key generation script
cd /opt/ops-center/backend
python3 scripts/generate_api_key.py --user-id USER_UUID --service amanuensis
```

**Check API key in database:**
```sql
SELECT id, email, api_keys FROM users WHERE email = 'user@example.com';
```

---

## 📚 Documentation Links

- **UC-Cloud Main Docs**: https://docs.unicorncommander.ai
- **Open-WebUI Guide**: https://docs.unicorncommander.ai/services/open-webui
- **Presenton Guide**: https://docs.unicorncommander.ai/services/presenton
- **Bolt.DIY Guide**: https://docs.unicorncommander.ai/services/bolt
- **Brigade Guide**: https://docs.unicorncommander.ai/services/brigade
- **Amanuensis API**: https://docs.unicorncommander.ai/api/amanuensis
- **Orator API**: https://docs.unicorncommander.ai/api/orator
- **SSO Setup Guide**: /services/ops-center/SSO-SETUP-COMPLETE.md
- **Keycloak uchub Realm**: /services/ops-center/UCHUB-REALM-SETUP.md

---

## 🔐 Security Notes

### API Key Storage
- API keys are encrypted in the database using AES-256
- Keys are never logged or displayed in plain text
- Keys should be stored in environment variables, not hardcoded

### SSO Best Practices
- Users should enable 2FA in Keycloak
- Session timeout is 30 minutes of inactivity
- Token refresh is handled automatically

### Rate Limiting
- API endpoints are rate-limited per user
- Web UI has CAPTCHA on login after 3 failed attempts
- DDoS protection via Cloudflare

---

## 📞 Support

For service access issues:
- **Email**: support@unicorncommander.ai
- **Documentation**: https://docs.unicorncommander.ai
- **Status Page**: https://status.unicorncommander.ai (coming soon)

For billing/subscription issues:
- **Email**: billing@unicorncommander.ai
- **Account Portal**: https://unicorncommander.ai/account

---

**Last verified**: November 1, 2025
**Maintainer**: UC-Cloud DevOps Team
