# Quick Fixes for UC-1 Pro Signup Flow

## Issue #1: Checkout Endpoint Mismatch

### Problem
Frontend calls `/api/v1/billing/subscriptions/checkout`
Backend defines `/api/v1/billing/checkout/create`

### Solution: Update Backend Route (Recommended)

**File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/backend/stripe_api.py`

**Change Line 99** from:
```python
@router.post("/checkout/create", response_model=CheckoutSessionResponse)
```

**To**:
```python
@router.post("/subscriptions/checkout", response_model=CheckoutSessionResponse)
```

**Or add an alias route**:
```python
# Add this after line 174
@router.post("/subscriptions/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session_alias(
    request: CheckoutSessionRequest,
    user_email: str = Depends(get_current_user_email)
):
    """Alias for checkout/create for frontend compatibility"""
    return await create_checkout_session(request, user_email)
```

### After Fix:
```bash
docker restart ops-center-direct
```

---

## Issue #2: Configure Stripe Price IDs

### Problem
All subscription plans have `stripe_price_id: null`

### Solution: Run Stripe Setup Script

**Step 1**: Ensure Stripe API keys are set
```bash
docker exec ops-center-direct printenv | grep STRIPE
```

Should see:
```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

**Step 2**: Run setup script
```bash
docker exec ops-center-direct python /app/setup_stripe_products.py
```

Expected output:
```
Creating Stripe products and prices...
✓ Created product: Trial (prod_...)
✓ Created price: $1.00 (price_...)
✓ Created product: Starter (prod_...)
✓ Created price: $19.00 monthly (price_...)
✓ Created price: $190.00 yearly (price_...)
✓ Created product: Professional (prod_...)
✓ Created price: $49.00 monthly (price_...)
✓ Created price: $490.00 yearly (price_...)
✓ Created product: Enterprise (prod_...)
✓ Created price: $99.00 monthly (price_...)
✓ Created price: $990.00 yearly (price_...)
```

**Step 3**: Verify price IDs are set
```bash
docker exec ops-center-direct curl -s http://localhost:8084/api/v1/subscriptions/plans | python3 -c "import sys, json; plans = json.load(sys.stdin)['plans']; print('\\n'.join([f\"{p['name']}: {p['stripe_price_id']}\" for p in plans]))"
```

Should show price IDs instead of `null`:
```
trial: price_1ABC...
starter: price_1DEF...
professional: price_1GHI...
enterprise: price_1JKL...
```

---

## Issue #3: Frontend Tier Selection Fix (Alternative)

### If you prefer to fix frontend instead of backend:

**File**: `/home/deploy/Production/UC-1-Pro/services/ops-center/public/signup-flow.html`

**Change Line 721** from:
```javascript
const response = await fetch('/api/v1/billing/subscriptions/checkout', {
```

**To**:
```javascript
const response = await fetch('/api/v1/billing/checkout/create', {
```

**And change request body** (line 728-731) from:
```javascript
body: JSON.stringify({
    tier: selectedTierName,
    success_url: window.location.origin + '/signup-flow.html?success=true',
    cancel_url: window.location.origin + '/signup-flow.html?canceled=true'
})
```

**To**:
```javascript
body: JSON.stringify({
    tier_id: selectedTierName,  // Changed from 'tier' to 'tier_id'
    billing_cycle: 'monthly',
    success_url: window.location.origin + '/signup-flow.html?success=true',
    cancel_url: window.location.origin + '/signup-flow.html?canceled=true'
})
```

---

## Testing After Fixes

### Test 1: Verify Checkout Endpoint
```bash
# Get CSRF token first
CSRF_TOKEN=$(docker exec ops-center-direct curl -s http://localhost:8084/api/v1/auth/csrf-token | jq -r '.csrf_token')

# Test checkout endpoint (will fail auth, but should return 401 not 404)
docker exec ops-center-direct curl -s -X POST \
  http://localhost:8084/api/v1/billing/subscriptions/checkout \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d '{"tier":"professional"}' \
  | jq '.'
```

Expected: `{"detail":"Not authenticated"}` (401)
NOT: `{"detail":"Not Found"}` (404)

### Test 2: Verify Plans Have Price IDs
```bash
docker exec ops-center-direct curl -s http://localhost:8084/api/v1/subscriptions/plans | jq '.plans[] | {name: .name, price_id: .stripe_price_id}'
```

Expected:
```json
{
  "name": "trial",
  "price_id": "price_1ABC..."
}
{
  "name": "starter",
  "price_id": "price_1DEF..."
}
...
```

---

## Complete End-to-End Test

### Using Stripe Test Mode

1. **Visit Plans Page**:
   ```
   https://unicorncommander.ai/plans.html
   ```

2. **Select Professional Tier**:
   - Click "Select Professional"
   - Redirected to `/signup-flow.html?plan=professional`

3. **Create Test Account**:
   - Email: `testuser@example.com`
   - Password: `TestPassword123!`

4. **Enter Test Card**:
   - Card: `4242 4242 4242 4242`
   - Exp: `12/34`
   - CVC: `123`
   - ZIP: `12345`

5. **Complete Payment**:
   - Click "Pay"
   - Wait for webhook processing

6. **Verify Success**:
   - Should redirect to success page
   - Check Keycloak user attributes:
   ```bash
   # Check subscription tier
   docker exec uchub-keycloak /opt/keycloak/bin/kcadm.sh get users \
     -r uchub -q email=testuser@example.com --fields attributes
   ```

   Should show:
   ```json
   {
     "attributes": {
       "subscription_tier": ["professional"],
       "subscription_status": ["active"],
       "stripe_customer_id": ["cus_..."],
       "stripe_subscription_id": ["sub_..."]
     }
   }
   ```

7. **Test Access**:
   - Visit `/billing-settings.html`
   - Should show "Professional" tier badge
   - Should show active subscription

---

## Rollback Plan

If something goes wrong, rollback to previous state:

```bash
# Restart container to reload original code
docker restart ops-center-direct

# If Stripe products were created but need to be removed:
docker exec ops-center-direct python /app/cleanup_stripe_products.py
```

---

## Quick Reference Commands

```bash
# Check container status
docker ps | grep ops-center

# View logs
docker logs ops-center-direct --tail 50

# Restart after changes
docker restart ops-center-direct

# Test API from inside container
docker exec ops-center-direct curl -s http://localhost:8084/api/v1/subscriptions/plans | jq '.'

# Check Stripe products
docker exec ops-center-direct python -c "import stripe; stripe.api_key='sk_test_...'; print([p.name for p in stripe.Product.list()])"
```

---

## Estimated Time

- **Issue #1 Fix**: 5 minutes
- **Issue #2 Fix**: 10 minutes
- **Testing**: 15 minutes
- **Total**: 30 minutes

---

## Support

If issues persist:
1. Check logs: `docker logs ops-center-direct`
2. Verify environment variables
3. Test with curl from inside container first
4. Check Traefik routing (if external access issues)

---

**Created**: October 11, 2025
**For**: UC-1 Pro Ops Center
**Container**: ops-center-direct
