# Stripe Webhook Quick Reference

---

## Endpoint

```
POST /api/v1/billing/webhooks/stripe/checkout
```

**No authentication required** - uses Stripe signature verification

---

## Stripe Dashboard Setup

1. **URL**: https://dashboard.stripe.com/test/webhooks
2. **Click**: "Add endpoint"
3. **Endpoint URL**: `https://your-domain.com/api/v1/billing/webhooks/stripe/checkout`
4. **Select events**: ✅ `checkout.session.completed`
5. **Copy signing secret**: `whsec_...`

---

## Environment Variables

Add to `/services/ops-center/.env.auth`:

```bash
STRIPE_WEBHOOK_SECRET=whsec_IVIJ51M4n8Ix4PsMsDFgohJWZXaAtWQh
LAGO_API_URL=http://unicorn-lago-api:3000
LAGO_API_KEY=d87f40d7-25c4-411c-bd51-677b26299e1c
```

---

## What It Does

1. Verifies Stripe signature ✓
2. Gets user from Keycloak
3. Creates Lago customer (if new)
4. Creates Lago subscription
5. Updates Keycloak user tier
6. Logs audit event

**Total time**: ~500-1000ms

---

## Testing

### Test Endpoint Accessibility

```bash
docker exec ops-center-direct curl -X POST \
  http://localhost:8084/api/v1/billing/webhooks/stripe/checkout \
  -H "Content-Type: application/json" -d '{"test": "data"}'

# Expected: {"detail":"Invalid signature"}
```

### Test Full Flow

1. Go to: https://your-domain.com/signup-flow.html
2. Sign up: `test@example.com`
3. Use card: `4242 4242 4242 4242`
4. Complete payment

### Verify Results

```bash
# Check Lago subscription
docker exec unicorn-lago-postgres psql -U lago -d lago -c \
  "SELECT * FROM subscriptions WHERE external_customer_id = 'test@example.com';"

# Check Keycloak tier
docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
  --realm uchub --query email=test@example.com | grep subscription_tier
```

---

## Monitoring

```bash
# Watch webhook logs
docker logs ops-center-direct -f | grep -i webhook

# Check for errors
docker logs ops-center-direct --tail 100 | grep "webhook.*ERROR"
```

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "Invalid signature" | Check `STRIPE_WEBHOOK_SECRET` matches Stripe dashboard |
| "User not found" | Ensure user exists in Keycloak before payment |
| "Failed to create customer" | Check Lago is running: `docker ps \| grep lago` |
| "Failed to create subscription" | Verify plan codes match: `trial`, `starter`, `professional`, `enterprise` |

---

## Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Invalid signature or payload |
| 500 | Server error |

---

## Files

- **Implementation**: `/services/ops-center/backend/stripe_api.py`
- **Documentation**: `/services/ops-center/STRIPE_WEBHOOK_IMPLEMENTATION.md`
- **Summary**: `/services/ops-center/WEBHOOK_DEPLOYMENT_SUMMARY.md`

---

**Status**: ✅ DEPLOYED
**Date**: October 23, 2025
