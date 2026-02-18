# Extensions Marketplace - Manual Testing Checklist

**Date**: November 1, 2025
**Environment**: https://unicorncommander.ai
**Test User**: test-user-123
**Admin User**: admin-user-123

---

## Prerequisites

- [ ] Backend server running on port 8084
- [ ] PostgreSQL database accessible
- [ ] Test data loaded (15 add-ons across 4 categories)
- [ ] Browser with developer tools open
- [ ] Valid session token (logged in)

---

## 1. Public Catalog Browsing (No Auth Required)

### 1.1 Browse All Add-ons
- [ ] Navigate to `/extensions/catalog`
- [ ] Verify 15 add-ons display correctly
- [ ] Verify cards show: name, description, price, category, rating
- [ ] Verify "Featured" badge appears on 4 add-ons
- [ ] Scroll pagination works (if implemented)

### 1.2 Category Filtering
- [ ] Click "AI/ML Tools" category
- [ ] Verify only 4 add-ons display
- [ ] Click "Productivity" category
- [ ] Verify only 4 add-ons display
- [ ] Click "Analytics" category
- [ ] Verify only 3 add-ons display
- [ ] Click "Security" category
- [ ] Verify only 4 add-ons display
- [ ] Click "All Categories"
- [ ] Verify all 15 add-ons return

### 1.3 Search Functionality
- [ ] Enter "analytics" in search box
- [ ] Verify results contain "Advanced Analytics Dashboard" and "Business Intelligence Suite"
- [ ] Enter "security" in search
- [ ] Verify 4 security add-ons appear
- [ ] Search for "machine learning"
- [ ] Verify relevant AI/ML add-ons appear
- [ ] Search for "xyz123nonexistent"
- [ ] Verify "No results found" message

### 1.4 Featured Add-ons Section
- [ ] Scroll to "Featured" section on homepage
- [ ] Verify 4 featured add-ons display:
  - Advanced Analytics Dashboard ($49.99)
  - Neural Network Builder ($99.99)
  - Smart Workflow Automation ($39.99)
  - Enterprise Security Shield ($99.00)
- [ ] Click "View All Featured" link
- [ ] Verify navigates to filtered view

### 1.5 Add-on Detail Page
- [ ] Click "Advanced Analytics Dashboard"
- [ ] Verify detail page loads with:
  - Full name and description
  - Base price ($49.99)
  - Billing type (monthly)
  - Feature list (5+ features)
  - Screenshots (if any)
  - Rating (4.8/5.0)
  - Review count (127)
  - Install count (3,450)
  - "Add to Cart" button
- [ ] Click "Back to Catalog" button
- [ ] Verify returns to catalog view

---

## 2. Shopping Cart Management (Auth Required)

### 2.1 View Empty Cart
- [ ] Login with test user credentials
- [ ] Navigate to `/extensions/cart`
- [ ] Verify empty cart message displays
- [ ] Verify cart totals show:
  - Subtotal: $0.00
  - Discount: $0.00
  - Total: $0.00
  - Item count: 0

### 2.2 Add Items to Cart
- [ ] Browse catalog
- [ ] Click "Add to Cart" on "Advanced Analytics Dashboard"
- [ ] Verify cart icon updates with badge (1)
- [ ] Click "Add to Cart" on "Neural Network Builder"
- [ ] Verify cart badge updates (2)
- [ ] Navigate to cart page
- [ ] Verify 2 items display with correct details
- [ ] Verify subtotal = $49.99 + $99.99 = $149.98

### 2.3 Update Quantity
- [ ] In cart, change "Advanced Analytics Dashboard" quantity to 3
- [ ] Verify subtotal updates: (3 × $49.99) + $99.99 = $249.96
- [ ] Change quantity back to 1
- [ ] Verify subtotal recalculates to $149.98

### 2.4 Remove Items
- [ ] Click "Remove" on "Advanced Analytics Dashboard"
- [ ] Verify item disappears from cart
- [ ] Verify subtotal updates to $99.99
- [ ] Verify item count badge shows 1
- [ ] Click "Remove" on last item
- [ ] Verify cart shows empty state

### 2.5 Apply Promo Code
- [ ] Add "Smart Workflow Automation" ($39.99) to cart
- [ ] In cart, enter promo code: `WELCOME25`
- [ ] Click "Apply"
- [ ] Verify discount applies: 25% off = $10.00 discount
- [ ] Verify total shows: $39.99 - $10.00 = $29.99
- [ ] Enter invalid code: `INVALID99`
- [ ] Verify error message: "Invalid or expired promo code"

### 2.6 Save for Later (Phase 2 Feature)
- [ ] Click "Save for Later" button
- [ ] Verify placeholder message: "Coming in Phase 2"

---

## 3. Checkout & Purchase Flow (Auth Required)

### 3.1 Create Checkout Session
- [ ] With items in cart, click "Proceed to Checkout"
- [ ] Verify redirects to Stripe checkout page
- [ ] Verify page shows:
  - Line items with correct names and prices
  - Subtotal calculation
  - Total amount
  - Payment form (card details)

### 3.2 Complete Payment (Test Mode)
- [ ] Enter test card: `4242 4242 4242 4242`
- [ ] Expiry: Any future date (e.g., 12/25)
- [ ] CVC: Any 3 digits (e.g., 123)
- [ ] ZIP: Any 5 digits (e.g., 12345)
- [ ] Click "Pay"
- [ ] Verify redirects to success page
- [ ] Verify success message displays
- [ ] Verify cart is now empty

### 3.3 View Purchase History
- [ ] Navigate to `/extensions/purchases`
- [ ] Verify completed purchase appears with:
  - Purchase date
  - Add-on name(s)
  - Amount paid
  - Status: "Completed"
  - Transaction ID

### 3.4 Activate Purchase
- [ ] In purchase history, click "Activate" button
- [ ] Verify features are granted
- [ ] Navigate to `/extensions/active`
- [ ] Verify activated add-on appears in active list

### 3.5 View Invoice
- [ ] In purchase history, click "View Invoice"
- [ ] Verify invoice displays:
  - Invoice number
  - Purchase date
  - Billing details
  - Line items
  - Payment method
  - Total paid
- [ ] Click "Download PDF"
- [ ] Verify PDF downloads correctly

### 3.6 Cancel Subscription (if applicable)
- [ ] For monthly/yearly add-on, click "Cancel Subscription"
- [ ] Verify confirmation modal appears
- [ ] Click "Confirm Cancellation"
- [ ] Verify status changes to "Canceled"
- [ ] Verify end date is set (end of current billing period)

---

## 4. Admin Management (Admin Role Required)

### 4.1 View Add-on Management Dashboard
- [ ] Login as admin user
- [ ] Navigate to `/admin/extensions`
- [ ] Verify admin dashboard displays:
  - Total add-ons count
  - Active add-ons count
  - Total sales
  - Revenue metrics
  - Recent purchases list

### 4.2 Create New Add-on
- [ ] Click "Create Add-on" button
- [ ] Fill out form:
  - Name: "Test Add-on"
  - Description: "Test description for QA"
  - Category: "Productivity"
  - Base Price: $25.00
  - Billing Type: "monthly"
  - Features: {"test": "feature1", "demo": "feature2"}
- [ ] Click "Create"
- [ ] Verify success message
- [ ] Browse public catalog
- [ ] Verify new add-on appears

### 4.3 Update Add-on
- [ ] In admin dashboard, click "Edit" on "Test Add-on"
- [ ] Change price to $29.99
- [ ] Update description
- [ ] Click "Save Changes"
- [ ] Verify success message
- [ ] View add-on detail page
- [ ] Verify changes reflected

### 4.4 Feature/Unfeature Add-on
- [ ] In admin dashboard, check "Featured" checkbox on "Test Add-on"
- [ ] Click "Save"
- [ ] Browse public homepage
- [ ] Verify "Test Add-on" appears in Featured section
- [ ] Return to admin, uncheck "Featured"
- [ ] Verify removed from Featured section

### 4.5 Deactivate Add-on (Soft Delete)
- [ ] In admin dashboard, click "Deactivate" on "Test Add-on"
- [ ] Verify confirmation modal
- [ ] Click "Confirm"
- [ ] Verify add-on status changes to "Inactive"
- [ ] Browse public catalog
- [ ] Verify "Test Add-on" no longer appears
- [ ] In admin dashboard, verify it still appears with "Inactive" badge

### 4.6 Create Promo Code
- [ ] Click "Promo Codes" tab in admin dashboard
- [ ] Click "Create Promo Code"
- [ ] Fill out form:
  - Code: `TESTCODE50`
  - Discount Type: Percentage
  - Discount Value: 50
  - Usage Limit: 100
  - Valid Until: 30 days from now
- [ ] Click "Create"
- [ ] Verify promo code appears in list
- [ ] Test as user (add item to cart, apply code)
- [ ] Verify 50% discount applies

### 4.7 View Sales Analytics
- [ ] Navigate to `/admin/extensions/analytics`
- [ ] Verify charts display:
  - Revenue over time (line chart)
  - Sales by category (pie chart)
  - Top selling add-ons (bar chart)
  - Conversion funnel (funnel chart)
- [ ] Change date range filter
- [ ] Verify charts update with filtered data

### 4.8 Manage Reviews (if implemented)
- [ ] View add-on detail page
- [ ] Verify reviews section displays
- [ ] As admin, click "Delete" on inappropriate review
- [ ] Verify confirmation modal
- [ ] Verify review is removed

---

## 5. Edge Cases & Error Handling

### 5.1 Authentication Errors
- [ ] Logout
- [ ] Try to access `/extensions/cart`
- [ ] Verify redirects to login page
- [ ] Try to POST to cart API directly (via curl/Postman)
- [ ] Verify returns 401 Unauthorized

### 5.2 Invalid Add-on ID
- [ ] Navigate to `/extensions/99999` (non-existent ID)
- [ ] Verify 404 error page displays
- [ ] Verify error message: "Add-on not found"

### 5.3 Quantity Limits
- [ ] Add item to cart
- [ ] Try to set quantity to 101
- [ ] Verify error: "Maximum quantity is 100"

### 5.4 Expired Promo Code
- [ ] In cart, enter: `EXPIRED10`
- [ ] Click "Apply"
- [ ] Verify error: "Promo code has expired"

### 5.5 Payment Declined
- [ ] Add items to cart
- [ ] Proceed to Stripe checkout
- [ ] Enter test card: `4000 0000 0000 0002` (declined)
- [ ] Click "Pay"
- [ ] Verify error message from Stripe
- [ ] Verify cart is not cleared
- [ ] Verify no purchase is created

### 5.6 SQL Injection Prevention
- [ ] In search box, enter: `'; DROP TABLE add_ons; --`
- [ ] Verify search returns no results (or safe results)
- [ ] Verify no database error
- [ ] Check database tables still exist
- [ ] In promo code field, enter: `' OR '1'='1`
- [ ] Verify returns error, not unauthorized discount

### 5.7 XSS Prevention
- [ ] As admin, create add-on with name: `<script>alert('XSS')</script>`
- [ ] View add-on in public catalog
- [ ] Verify script does NOT execute
- [ ] Verify name displays as plain text

### 5.8 Rate Limiting (if implemented)
- [ ] Make 100 rapid requests to `/api/v1/extensions/catalog`
- [ ] Verify rate limit kicks in (429 status)
- [ ] Wait 60 seconds
- [ ] Verify requests work again

---

## 6. Performance & Load Testing

### 6.1 Response Times
- [ ] Measure catalog list load time: _____ ms (target: <200ms)
- [ ] Measure add-on detail load time: _____ ms (target: <150ms)
- [ ] Measure cart operations: _____ ms (target: <100ms)
- [ ] Measure search query time: _____ ms (target: <300ms)

### 6.2 Large Dataset
- [ ] If possible, seed 1000+ add-ons
- [ ] Test catalog pagination
- [ ] Test search performance
- [ ] Verify no timeouts

### 6.3 Concurrent Users
- [ ] Open 10 browser tabs
- [ ] Simulate 10 users adding items to cart simultaneously
- [ ] Verify no race conditions
- [ ] Verify cart integrity for each user

---

## 7. Mobile & Browser Compatibility

### 7.1 Mobile Responsive
- [ ] Open on mobile device (or Chrome DevTools device emulation)
- [ ] Browse catalog
- [ ] Verify cards stack vertically
- [ ] Verify "Add to Cart" button accessible
- [ ] Complete purchase flow
- [ ] Verify Stripe checkout is mobile-friendly

### 7.2 Browser Testing
- [ ] Test on Chrome (latest)
- [ ] Test on Firefox (latest)
- [ ] Test on Safari (if Mac available)
- [ ] Test on Edge (latest)
- [ ] Verify consistent behavior across all browsers

---

## Test Summary

**Total Tests**: 100+
**Categories**: 7
**Critical Paths**: 4 (Browse → Add to Cart → Checkout → Purchase)

**Pass Criteria**:
- All critical paths complete successfully
- No JavaScript errors in console
- No database errors in backend logs
- All auth checks working correctly
- Cart calculations accurate
- Stripe integration functional

**Sign-off**:

- Tester Name: ___________________________
- Date: ___________________________
- Status: ☐ PASS ☐ FAIL ☐ NEEDS REVIEW
- Notes: ___________________________
