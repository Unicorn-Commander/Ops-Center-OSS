# Admin Subscription Management - Quick Start Guide

## 🚀 Quick Deploy

```bash
# 1. Restart ops-center to load new code
cd /home/muut/Production/UC-1-Pro
docker restart unicorn-ops-center

# 2. Check logs
docker logs -f unicorn-ops-center
```

## 🔐 Access Admin Dashboard

1. **Login:** https://your-domain.com/login.html
2. **Admin Panel:** https://your-domain.com/admin/subscriptions.html

**Admin Credentials:**
- Login via Keycloak at https://auth.your-domain.com/realms/uchub
- Must have admin role

## 📊 API Endpoints

### List All Subscriptions
```bash
GET /api/v1/admin/subscriptions/list
```

### Update Subscription
```bash
PATCH /api/v1/admin/subscriptions/{email}
{
  "tier": "professional",
  "status": "active",
  "notes": "Upgraded by admin"
}
```

### Reset Usage
```bash
POST /api/v1/admin/subscriptions/{email}/reset-usage
```

### Get Analytics
```bash
GET /api/v1/admin/subscriptions/analytics/overview
GET /api/v1/admin/subscriptions/analytics/revenue-by-tier
GET /api/v1/admin/subscriptions/analytics/usage-stats
```

## 🎯 Subscription Tiers

| Tier | Price | API Calls/Day |
|------|-------|---------------|
| Free | $0 | 100 |
| Trial | $0 | 1,000 |
| Starter | $19/mo | 10,000 |
| Professional | $49/mo | 100,000 |
| Enterprise | $99/mo | 1,000,000 |

## 🧪 Testing

### Quick Test (in container)
```bash
docker exec -it unicorn-ops-center python3 /app/tests/quick_test.py
```

### Full Test Suite
```bash
docker exec -it unicorn-ops-center bash
cd /app/tests
./run_admin_tests.sh
```

### Manual Test via curl
```bash
# Get your session cookie from browser (login first)
SESSION_COOKIE="your_session_cookie_here"

# List subscriptions
curl -X GET "https://your-domain.com/api/v1/admin/subscriptions/list" \
  -H "Cookie: session=$SESSION_COOKIE"

# Update user
curl -X PATCH "https://your-domain.com/api/v1/admin/subscriptions/user@example.com" \
  -H "Cookie: session=$SESSION_COOKIE" \
  -H "Content-Type: application/json" \
  -d '{"tier":"professional","status":"active"}'
```

## 📁 Key Files

**Backend:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/keycloak_integration.py`
- `/home/muut/Production/UC-1-Pro/services/ops-center/backend/admin_subscriptions_api.py`

**Frontend:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/public/admin/subscriptions.html`

**Tests:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/tests/test_keycloak_admin.py`

**Docs:**
- `/home/muut/Production/UC-1-Pro/services/ops-center/docs/ADMIN_SUBSCRIPTION_API.md`
- `/home/muut/Production/UC-1-Pro/services/ops-center/KEYCLOAK_ADMIN_IMPLEMENTATION.md`

## 🔧 Environment Variables

```bash
KEYCLOAK_URL=https://auth.your-domain.com
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=admin-cli
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD=your-test-password
```

## ✅ Success Checklist

- [ ] Ops-center container restarted
- [ ] Can access admin dashboard
- [ ] Can view subscription list
- [ ] Can update user subscription
- [ ] Can reset usage
- [ ] Analytics showing correctly

## 🆘 Troubleshooting

**Error: "Admin access required"**
- Ensure user has admin role in Keycloak
- Check session cookie is valid

**Error: "Failed to get admin token"**
- Verify KEYCLOAK_ADMIN_PASSWORD is correct
- Check Keycloak is accessible at https://auth.your-domain.com

**Empty user list:**
- Verify KEYCLOAK_REALM is set to "uchub"
- Check users exist in Keycloak admin console

## 📞 Support

- Check container logs: `docker logs unicorn-ops-center`
- Keycloak admin: https://auth.your-domain.com/admin/uchub/console
- Full docs: `/home/muut/Production/UC-1-Pro/services/ops-center/docs/ADMIN_SUBSCRIPTION_API.md`
