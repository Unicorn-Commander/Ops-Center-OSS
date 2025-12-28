# System Settings API - Quick Reference

**Quick access guide for common operations**

---

## Deployment (One-Time Setup)

```bash
# 1. Generate encryption key
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 2. Add to environment
echo "SYSTEM_SETTINGS_ENCRYPTION_KEY=<key>" >> /home/muut/Production/UC-Cloud/services/ops-center/.env.auth

# 3. Apply database schema
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db \
  -f /app/sql/system_settings.sql

# 4. Restart service
docker restart ops-center-direct

# 5. Verify
curl http://localhost:8084/api/v1/system/settings/categories
```

---

## Common API Calls

### List All Settings
```bash
curl -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings
```

### List by Category
```bash
# LLM settings
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings?category=llm"

# Email settings
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings?category=email"
```

### Get Specific Setting
```bash
# Masked value
curl -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings/OPENROUTER_API_KEY

# Full value (admin only)
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings/OPENROUTER_API_KEY?show_value=true"
```

### Create/Update Setting
```bash
curl -X POST \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "key": "OPENAI_API_KEY",
    "value": "sk-proj-abc123...",
    "category": "llm",
    "description": "OpenAI API key",
    "is_sensitive": true
  }' \
  http://localhost:8084/api/v1/system/settings
```

### Bulk Update
```bash
curl -X POST \
  -H "Cookie: session_token=..." \
  -H "Content-Type: application/json" \
  -d '{
    "settings": [
      {"key": "SMTP_HOST", "value": "smtp.gmail.com"},
      {"key": "SMTP_PORT", "value": "587"}
    ]
  }' \
  http://localhost:8084/api/v1/system/settings/bulk
```

### Delete Setting
```bash
curl -X DELETE \
  -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings/OLD_API_KEY
```

### Get Audit Log
```bash
# All changes
curl -H "Cookie: session_token=..." \
  http://localhost:8084/api/v1/system/settings/audit/log

# For specific setting
curl -H "Cookie: session_token=..." \
  "http://localhost:8084/api/v1/system/settings/audit/log?key=STRIPE_SECRET_KEY"
```

---

## Setting Categories

| Category | Description | Example Keys |
|----------|-------------|--------------|
| `security` | Security & encryption | BYOK_ENCRYPTION_KEY, JWT_SECRET_KEY |
| `llm` | LLM provider keys | OPENROUTER_API_KEY, OPENAI_API_KEY |
| `billing` | Payment processing | STRIPE_SECRET_KEY, LAGO_API_KEY |
| `email` | Email configuration | SMTP_HOST, SMTP_PASSWORD |
| `storage` | Storage & backups | S3_ACCESS_KEY_ID, S3_BUCKET_NAME |
| `integration` | Third-party services | GITHUB_TOKEN, SLACK_BOT_TOKEN |
| `monitoring` | Monitoring & logging | SENTRY_DSN, LOG_LEVEL |
| `system` | System configuration | EXTERNAL_HOST, SYSTEM_TIMEZONE |

---

## Pre-Populated Settings

### Security (4)
```
BYOK_ENCRYPTION_KEY
JWT_SECRET_KEY
SESSION_SECRET
CSRF_SECRET_KEY
```

### LLM Providers (8)
```
OPENROUTER_API_KEY
OPENAI_API_KEY
ANTHROPIC_API_KEY
GOOGLE_AI_API_KEY
COHERE_API_KEY
LITELLM_MASTER_KEY
DEFAULT_LLM_MODEL
LLM_REQUEST_TIMEOUT
```

### Billing (6)
```
STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET
LAGO_API_KEY
LAGO_API_URL
LAGO_PUBLIC_URL
```

### Email (12)
```
SMTP_HOST
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
SMTP_USE_TLS
SMTP_FROM_EMAIL
SMTP_FROM_NAME
EMAIL_PROVIDER_TYPE
OAUTH2_CLIENT_ID
OAUTH2_CLIENT_SECRET
OAUTH2_TENANT_ID
OAUTH2_REFRESH_TOKEN
```

---

## Troubleshooting

### Settings Not Saving
```bash
# Check encryption key is set
docker exec ops-center-direct env | grep ENCRYPTION_KEY

# Check database connection
docker exec unicorn-postgresql psql -U unicorn -d unicorn_db -c "SELECT COUNT(*) FROM system_settings;"
```

### Decryption Errors
```bash
# Verify encryption key matches
# If key changed, settings encrypted with old key won't decrypt

# Fix: Delete and recreate settings with new key
```

### Cache Issues
```bash
# Flush Redis cache
docker exec unicorn-redis redis-cli FLUSHDB

# Or restart Redis
docker restart unicorn-redis
```

### Permission Denied
```bash
# Check user role
# Must be 'admin' or 'moderator'

# Assign role in Keycloak:
# https://auth.your-domain.com/admin/uchub/console
```

---

## File Locations

```
/home/muut/Production/UC-Cloud/services/ops-center/
├── backend/
│   ├── system_settings_manager.py   # Core logic
│   ├── system_settings_api.py       # REST API
│   └── sql/
│       └── system_settings.sql      # Database schema
├── docs/
│   └── SYSTEM_SETTINGS_API.md       # Full documentation
├── SYSTEM_SETTINGS_IMPLEMENTATION_SUMMARY.md
└── SYSTEM_SETTINGS_QUICK_REFERENCE.md  # This file
```

---

## Python Example

```python
import requests

session = requests.Session()
# ... login to get session_token cookie ...

# List all LLM settings
response = session.get(
    "http://localhost:8084/api/v1/system/settings",
    params={"category": "llm"}
)
for setting in response.json()["settings"]:
    print(f"{setting['key']}: {setting['value']}")

# Update API key
session.post(
    "http://localhost:8084/api/v1/system/settings",
    json={
        "key": "OPENROUTER_API_KEY",
        "value": "sk-or-v1-new-key...",
        "category": "llm",
        "is_sensitive": True
    }
)
```

---

## JavaScript Example

```javascript
// List settings
const settings = await fetch('/api/v1/system/settings?category=email', {
  credentials: 'include'
}).then(r => r.json()).then(d => d.settings);

// Update setting
await fetch('/api/v1/system/settings', {
  method: 'POST',
  credentials: 'include',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    key: 'SMTP_HOST',
    value: 'smtp.gmail.com',
    category: 'email'
  })
});
```

---

## Security Notes

- All values encrypted with Fernet (AES-128 CBC)
- Sensitive values masked by default (show last 8 chars)
- Full decryption requires `show_values=true` parameter
- All changes audited with user, IP, timestamp
- Admin/moderator role required for all operations

---

## Next Steps

1. ✅ Backend API complete
2. ⏳ Build frontend GUI (React page)
3. ⏳ Add navigation link to sidebar
4. ⏳ Test end-to-end workflow

---

For full documentation, see: `/docs/SYSTEM_SETTINGS_API.md`
