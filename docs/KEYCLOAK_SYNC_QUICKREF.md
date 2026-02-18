# Keycloak Subscription Sync - Quick Reference

## TL;DR

✅ **Status:** Code complete, ready to deploy
🎯 **Purpose:** Auto-sync Lago subscriptions to Keycloak user attributes
🔗 **Architecture:** Stripe → Lago → Webhook → Keycloak

---

## Deploy in 5 Steps

### 1. Add Environment Variables
```bash
KEYCLOAK_URL=https://auth.unicorncommander.ai
KEYCLOAK_REALM=uchub
KEYCLOAK_ADMIN_USER=admin
KEYCLOAK_ADMIN_PASSWORD=your-admin-password
KEYCLOAK_ADMIN_CLIENT_ID=admin-cli
LAGO_WEBHOOK_SECRET=<from_lago_admin>
```

### 2. Rebuild Container
```bash
docker stop ops-center-direct
docker build -t uc-1-pro-ops-center .
docker start ops-center-direct
```

### 3. Configure Lago
- **Webhook URL:** `https://unicorncommander.ai/api/v1/webhooks/lago`
- **Enable Events:** subscription.*, invoice.paid

### 4. Test Health
```bash
curl https://unicorncommander.ai/api/v1/webhooks/lago/health
```

### 5. Run Tests
```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center
./scripts/test_keycloak_webhook.sh
```

---

## What Gets Synced

| Keycloak Attribute | Description |
|-------------------|-------------|
| `subscription_tier` | `["professional"]` |
| `subscription_status` | `["active"]` |
| `subscription_id` | `["sub_abc123"]` |
| `api_calls_used` | `["0"]` |

---

## Test Commands

### Health Check
```bash
curl https://unicorncommander.ai/api/v1/webhooks/lago/health
```

### Test Webhook
```bash
curl -X POST https://unicorncommander.ai/api/v1/webhooks/lago \
  -H "Content-Type: application/json" \
  -d '{"webhook_type":"subscription.created","customer":{"email":"admin@example.com"},"subscription":{"lago_id":"test_123","plan_code":"professional","status":"active"}}'
```

### Check Keycloak Attributes
```bash
TOKEN=$(curl -sk -X POST "https://auth.unicorncommander.ai/realms/master/protocol/openid-connect/token" \
  -d "username=admin" -d "password=your-admin-password" -d "grant_type=password" -d "client_id=admin-cli" | jq -r '.access_token')

curl -sk "https://auth.unicorncommander.ai/admin/realms/uchub/users?email=admin@example.com&exact=true" \
  -H "Authorization: Bearer $TOKEN" | jq '.[0].attributes'
```

---

## Files Modified

1. `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/keycloak_integration.py` - NEW
2. `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/lago_webhooks.py` - UPDATED
3. `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/server.py` - FIXED (line 3763)

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Webhook returns HTML | Rebuild container |
| User not found | Check email, ensure user logged in |
| Auth failed | Verify admin password |
| Invalid signature | Update LAGO_WEBHOOK_SECRET |

---

## Documentation

- **Full Guide:** `docs/KEYCLOAK_SUBSCRIPTION_SYNC.md`
- **Deployment:** `docs/KEYCLOAK_WEBHOOK_DEPLOYMENT.md`
- **Summary:** `docs/IMPLEMENTATION_SUMMARY_KEYCLOAK_SYNC.md`
- **Test Script:** `scripts/test_keycloak_webhook.sh`

---

**Ready to deploy!**
