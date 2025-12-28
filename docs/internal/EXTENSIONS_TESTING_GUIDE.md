# Extensions Marketplace - Manual Testing Guide

**Date**: November 1, 2025
**Purpose**: Step-by-step testing procedures for Extensions Marketplace
**Prerequisites**: Backend running, database seeded with sample data

---

## Quick Start

### 1. Seed the Database

```bash
# Navigate to ops-center directory
cd /home/muut/Production/UC-Cloud/services/ops-center

# Run seed script
docker exec ops-center-direct \
  psql -U unicorn -d unicorn_db \
  -f /app/sql/extensions_seed_data.sql

# Verify data loaded
docker exec ops-center-direct \
  psql -U unicorn -d unicorn_db \
  -c "SELECT id, name, base_price FROM add_ons;"
```

Expected output:
```
 id |          name          | base_price
----+------------------------+------------
  1 | Premium GPU Tier       |      49.99
  2 | Advanced AI Models     |      99.99
  3 | Custom Domain          |      19.99
  4 | Priority Support       |      29.99
  5 | Team Collaboration     |      79.99
```

### 2. Access the Marketplace

```bash
# Open browser to
https://your-domain.com/admin/extensions

# Or locally
http://localhost:8084/admin/extensions
```

---

## Test Scenarios

### Scenario 1: Browse Catalog ✅

**Steps**:
1. Navigate to `/admin/extensions`
2. Verify add-ons appear in grid layout
3. Check that each card shows:
   - Add-on icon/image
   - Name
   - Price
   - Description
   - Category badge
   - "Add to Cart" button

**Expected Results**:
- Grid displays 3 columns on desktop, 2 on tablet, 1 on mobile
- Cards have glassmorphism styling
- Hover effects work
- Loading spinner shows while fetching data
- Empty state shows if no add-ons

**Pass Criteria**: ✅ All add-ons visible with correct information

---

### Scenario 2: Add to Cart ✅

**Steps**:
1. Click "Add to Cart" on any add-on
2. Observe cart sidebar slide in from right
3. Verify item appears in cart
4. Check item count badge updates

**Expected Results**:
- Toast notification: "Added to cart"
- Cart sidebar opens automatically
- Item shows with:
  - Name
  - Quantity (default 1)
  - Price
  - Subtotal
- Cart total updates
- Item count badge shows correct number

**Pass Criteria**: ✅ Item added successfully, cart updates correctly

---

### Scenario 3: View Product Details ✅

**Steps**:
1. Click on any add-on card (anywhere except "Add to Cart" button)
2. Navigate to product detail page
3. Scroll through sections

**Expected Results**:
- URL changes to `/admin/extensions/{id}`
- Page shows:
  - Hero section with large icon
  - Product name and tagline
  - Pricing information
  - "What's included" checklist
  - Full description
  - Features grid (2 columns)
  - Use cases grid (3 columns)
  - Bottom CTA section
- "Add to Cart" button functional

**Pass Criteria**: ✅ All sections render, data accurate, animations smooth

---

### Scenario 4: Update Cart Quantities ✅

**Steps**:
1. Open cart sidebar (if not already open)
2. Click "+" button next to item
3. Observe quantity increase
4. Click "-" button
5. Observe quantity decrease
6. Try to decrease below 1
7. Try to increase above 100

**Expected Results**:
- Quantity increments smoothly
- Subtotal recalculates instantly
- Cart total updates
- Cannot decrease below 1
- Cannot increase above 100
- No page reload

**Pass Criteria**: ✅ Quantities update correctly, validation works

---

### Scenario 5: Remove from Cart ✅

**Steps**:
1. Open cart sidebar
2. Click "Remove" or trash icon next to item
3. Observe item disappear

**Expected Results**:
- Toast notification: "Removed from cart"
- Item fades out and disappears
- Cart total recalculates
- Item count decreases
- If last item, cart shows empty state

**Pass Criteria**: ✅ Item removed, cart updates correctly

---

### Scenario 6: Clear Cart ✅

**Steps**:
1. Add multiple items to cart
2. Click "Clear Cart" button at bottom of cart sidebar
3. Confirm action (if confirmation modal exists)

**Expected Results**:
- Toast notification: "Cart cleared"
- All items disappear
- Cart shows empty state
- Item count badge shows 0
- Cart total shows $0.00

**Pass Criteria**: ✅ Cart fully cleared, state reset

---

### Scenario 7: Proceed to Checkout ✅

**Steps**:
1. Add at least one item to cart
2. Click "Proceed to Checkout" in cart sidebar
3. Navigate to checkout page

**Expected Results**:
- URL changes to `/admin/extensions/checkout`
- Page shows:
  - Cart items list with quantities
  - Quantity adjustment buttons (+/-)
  - Remove item buttons
  - Promo code input section
  - Pricing breakdown sidebar
  - "Proceed to Payment" button
  - Security badges (SSL, money-back guarantee)

**Pass Criteria**: ✅ Checkout page loads, all sections visible

---

### Scenario 8: Apply Promo Code ⚠️

**Steps**:
1. On checkout page, enter promo code "SAVE10"
2. Click "Apply" button
3. Observe response

**Expected Results** (Phase 1 - Not Implemented):
- Error message: "Promo code endpoint not implemented"
- No discount applied
- Cart total unchanged

**Expected Results** (Phase 2 - When Implemented):
- Toast notification: "Promo code applied! 10% off"
- Discount row appears in pricing breakdown
- Total recalculates with discount
- Promo code badge shows in checkout

**Pass Criteria**: ⚠️ Shows appropriate error (Phase 1) or applies discount (Phase 2)

---

### Scenario 9: Complete Checkout ⚠️

**Steps**:
1. On checkout page, click "Proceed to Payment"
2. Observe redirect behavior

**Expected Results** (Without Stripe Configured):
- Error message or loading state
- No redirect occurs

**Expected Results** (With Stripe Configured):
- Redirect to Stripe Checkout page
- Stripe session displays cart items
- Payment form appears
- Test card can be entered

**Test Cards** (Stripe Test Mode):
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Expiry: Any future date
- CVC: Any 3 digits

**Pass Criteria**: ⚠️ Redirects to Stripe (or shows config error if not set up)

---

### Scenario 10: Payment Success Flow ⚠️

**Steps**:
1. Complete payment on Stripe with test card
2. Redirect to success page
3. Observe animations and order summary

**Expected Results**:
- URL: `/admin/extensions/success?session_id={stripe_session_id}`
- Confetti animation plays
- Success message displays
- Order summary shows:
  - Items purchased
  - Total amount paid
  - Order ID
  - Purchase date
- Countdown timer starts (10 seconds)
- Auto-redirect to dashboard after countdown
- "View Purchase History" and "Continue Shopping" buttons available

**Pass Criteria**: ⚠️ Success page renders, order verified, redirect works

---

### Scenario 11: Payment Cancelled Flow ✅

**Steps**:
1. On Stripe Checkout, click "Back" or cancel payment
2. Redirect to cancelled page
3. Observe messaging and cart state

**Expected Results**:
- URL: `/admin/extensions/cancelled`
- Friendly message (not error-red)
- Cart summary shows items still saved
- Subtotal displayed
- "Return to Cart" button (green)
- "Continue Shopping" button (secondary)
- Reassurance section with benefits
- No cart data lost

**Pass Criteria**: ✅ Cancelled page renders, cart preserved, positive messaging

---

### Scenario 12: View Purchase History ✅

**Steps**:
1. Navigate to `/admin/purchases`
2. Switch between tabs
3. Test filtering

**Expected Results**:
- Two tabs: "Purchase History" and "Active Add-ons"
- Purchase History tab shows:
  - List of past purchases
  - Status badges (completed, pending, failed, refunded)
  - Purchase date
  - Line items with prices
  - Total amount
  - "Invoice" download button
  - Empty state if no purchases
- Active Add-ons tab shows:
  - Grid of active subscriptions
  - Add-on icons and names
  - "Active" status badge
  - Billing information
  - Renewal date (if applicable)
  - Empty state if no active add-ons
- Filtering works:
  - Search by add-on name
  - Filter by status dropdown
  - Date range (from/to)
  - Results update dynamically

**Pass Criteria**: ✅ Purchase history loads, tabs switch, filtering works

---

### Scenario 13: Download Invoice ⚠️

**Steps**:
1. On purchase history page, click "Invoice" button
2. Observe download behavior

**Expected Results** (Phase 1 - Not Implemented):
- Error toast: "Failed to download invoice"
- No file downloads

**Expected Results** (Phase 2 - When Implemented):
- PDF file downloads automatically
- Filename: `invoice-{purchase_id}.pdf`
- PDF contains:
  - Company logo and address
  - Invoice number and date
  - Customer information
  - Line items with prices
  - Subtotal, tax, total
  - Payment method
  - Terms and conditions

**Pass Criteria**: ⚠️ Shows error (Phase 1) or downloads PDF (Phase 2)

---

### Scenario 14: Error Handling ✅

**Steps**:
1. Disconnect internet
2. Try to load catalog
3. Reconnect and retry
4. Try to access non-existent add-on (e.g., `/admin/extensions/99999`)

**Expected Results**:
- Network error:
  - Toast: "Failed to load catalog"
  - Empty state with retry button
  - No app crash
- 404 error:
  - Toast: "Add-on not found"
  - Redirect to catalog or show 404 page
  - No app crash
- Retry mechanism:
  - "Retry" button reloads data
  - Loading spinner shows
  - Success or error message

**Pass Criteria**: ✅ Errors handled gracefully, user can recover

---

### Scenario 15: Mobile Responsiveness ✅

**Steps**:
1. Open DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test on different screen sizes:
   - iPhone SE (375px)
   - iPhone 12 Pro (390px)
   - iPad (768px)
   - Desktop (1920px)

**Expected Results**:
- Catalog grid:
  - 1 column on mobile (< 640px)
  - 2 columns on tablet (640px - 1024px)
  - 3 columns on desktop (> 1024px)
- Cart sidebar:
  - Full-width overlay on mobile
  - Sidebar on desktop
  - Swipe gesture to close (mobile)
- Checkout page:
  - Stacked layout on mobile
  - 2-column layout on desktop
  - Sidebar sticky on scroll
- Touch targets:
  - Minimum 44x44px on mobile
  - Easy to tap buttons
  - No accidental clicks
- Typography:
  - 16px base on mobile (no zoom)
  - 18px on desktop
  - Readable line heights

**Pass Criteria**: ✅ All layouts responsive, touch-friendly, readable

---

## API Testing (Backend)

### Test Catalog Endpoint

```bash
# List all add-ons
curl -X GET http://localhost:8084/api/v1/extensions/catalog \
  -H "Cookie: session_token=test" | jq

# Get single add-on
curl -X GET http://localhost:8084/api/v1/extensions/1 \
  -H "Cookie: session_token=test" | jq

# Search add-ons
curl -X GET "http://localhost:8084/api/v1/extensions/search?q=gpu" \
  -H "Cookie: session_token=test" | jq

# List categories
curl -X GET http://localhost:8084/api/v1/extensions/categories/list \
  -H "Cookie: session_token=test" | jq
```

### Test Cart Endpoint

```bash
# Get cart
curl -X GET http://localhost:8084/api/v1/cart \
  -H "Cookie: session_token=test" | jq

# Add to cart
curl -X POST "http://localhost:8084/api/v1/cart/add?addon_id=1&quantity=2" \
  -H "Cookie: session_token=test" | jq

# Update quantity (replace {item_id} with actual ID from get cart response)
curl -X PUT "http://localhost:8084/api/v1/cart/{item_id}?quantity=3" \
  -H "Cookie: session_token=test" | jq

# Remove from cart
curl -X DELETE "http://localhost:8084/api/v1/cart/{item_id}" \
  -H "Cookie: session_token=test" | jq

# Clear cart
curl -X DELETE http://localhost:8084/api/v1/cart/clear \
  -H "Cookie: session_token=test" | jq
```

---

## Browser Console Testing

### Check for JavaScript Errors

1. Open browser console (F12 → Console tab)
2. Navigate through marketplace
3. Perform all actions
4. Look for:
   - ❌ Red errors (should be none)
   - ⚠️ Yellow warnings (should be minimal)
   - ℹ️ Blue info (API calls logged)

### Monitor Network Requests

1. Open browser DevTools (F12 → Network tab)
2. Filter by "Fetch/XHR"
3. Perform actions and verify:
   - ✅ Status 200 (success)
   - ❌ Status 401 (auth error)
   - ❌ Status 404 (not found)
   - ❌ Status 500 (server error)

### Check Response Times

All API calls should complete within:
- Catalog: < 500ms
- Cart operations: < 300ms
- Search: < 200ms

---

## Performance Testing

### Lighthouse Audit

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse https://your-domain.com/admin/extensions \
  --output html \
  --output-path ./lighthouse-report.html \
  --chrome-flags="--headless"

# Open report
xdg-open ./lighthouse-report.html
```

**Target Scores**:
- Performance: > 90
- Accessibility: > 95
- Best Practices: > 90
- SEO: > 80

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test catalog endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 \
  -H "Cookie: session_token=test" \
  http://localhost:8084/api/v1/extensions/catalog
```

**Target**:
- Requests per second: > 50
- Average response time: < 200ms
- 99th percentile: < 500ms

---

## Common Issues & Solutions

### Issue: Catalog Returns Empty Array

**Symptom**: GET `/api/v1/extensions/catalog` returns `[]`

**Cause**: Database not seeded

**Solution**:
```bash
docker exec ops-center-direct \
  psql -U unicorn -d unicorn_db \
  -f /app/sql/extensions_seed_data.sql
```

---

### Issue: 401 Unauthorized on All Requests

**Symptom**: All API calls return 401

**Cause**: No session cookie

**Solution**:
1. Log in via `/auth/login`
2. Verify session cookie in browser DevTools (Application → Cookies)
3. Cookie should be named `session_token`

---

### Issue: Cart Not Persisting

**Symptom**: Cart empties on page refresh

**Cause**: Backend using test user ID

**Solution**:
- This is expected in Phase 1 (all users share cart)
- Phase 2: Integrate Keycloak authentication

---

### Issue: Promo Code Fails

**Symptom**: Promo code shows error

**Cause**: Backend endpoint not implemented (Phase 2)

**Solution**:
- Expected behavior in Phase 1
- Test will be skipped until Phase 2

---

### Issue: Stripe Redirect Fails

**Symptom**: "Proceed to Payment" shows error

**Cause**: Stripe not configured

**Solution**:
1. Add Stripe API keys to `.env.auth`
2. Restart backend: `docker restart ops-center-direct`
3. Use Stripe test mode keys

---

### Issue: Invoice Download 404

**Symptom**: Invoice button shows "Not found"

**Cause**: PDF generation not implemented (Phase 2)

**Solution**:
- Expected behavior in Phase 1
- Test will be skipped until Phase 2

---

## Test Report Template

Use this template to document test results:

```markdown
# Extensions Marketplace Test Report

**Date**: YYYY-MM-DD
**Tester**: Name
**Environment**: Production / Staging / Local
**Browser**: Chrome 119 / Firefox 120 / Safari 17

## Test Results

| Scenario | Pass | Fail | Notes |
|----------|------|------|-------|
| Browse Catalog | ✅ | ❌ | |
| Add to Cart | ✅ | ❌ | |
| View Product Details | ✅ | ❌ | |
| Update Quantities | ✅ | ❌ | |
| Remove from Cart | ✅ | ❌ | |
| Clear Cart | ✅ | ❌ | |
| Proceed to Checkout | ✅ | ❌ | |
| Apply Promo Code | ⚠️ | ❌ | Phase 2 |
| Complete Checkout | ⚠️ | ❌ | Needs Stripe |
| Payment Success | ⚠️ | ❌ | Needs Stripe |
| Payment Cancelled | ✅ | ❌ | |
| View Purchase History | ✅ | ❌ | |
| Download Invoice | ⚠️ | ❌ | Phase 2 |
| Error Handling | ✅ | ❌ | |
| Mobile Responsive | ✅ | ❌ | |

## Summary

**Total Tests**: 15
**Passed**: X
**Failed**: Y
**Skipped**: Z (Phase 2)

**Critical Issues**: None / List issues

**Recommendations**: List recommendations
```

---

## Next Steps After Testing

### If Tests Pass ✅

1. **Seed production database**
   - Review seed data
   - Adjust pricing and features
   - Add real add-on descriptions

2. **Configure Stripe**
   - Create Stripe account
   - Add API keys
   - Set up webhooks
   - Test with real test cards

3. **Integrate Keycloak**
   - Update `get_current_user()` function
   - Validate session tokens
   - Test with multiple users

4. **Phase 2 Features**
   - Implement promo codes
   - Add invoice generation
   - Enhance product pages
   - Add user reviews

### If Tests Fail ❌

1. **Document Issues**
   - Screenshot errors
   - Copy error messages
   - Note reproduction steps

2. **Check Logs**
   ```bash
   docker logs ops-center-direct --tail 100
   ```

3. **Debug**
   - Check browser console
   - Verify API responses
   - Test backend directly with curl

4. **Report**
   - Create GitHub issue
   - Include error details
   - Attach logs and screenshots

---

## Support & Documentation

- **Integration Report**: `/FRONTEND_BACKEND_INTEGRATION_REPORT.md`
- **Backend Completion**: `/EXTENSIONS_MARKETPLACE_COMPLETE.md`
- **API Documentation**: `/backend/extensions_*_api.py` (inline comments)
- **Frontend Documentation**: `/src/pages/extensions/*.jsx` (JSDoc comments)

---

**Testing Guide Version**: 1.0.0
**Last Updated**: November 1, 2025
**Status**: Ready for Testing

