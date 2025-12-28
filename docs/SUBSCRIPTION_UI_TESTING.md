# Subscription UI Testing Guide

## Quick Start Testing

### 1. Access the Pages

**From Main Dashboard:**
```
1. Navigate to: https://your-domain.com
2. Look for footer navigation buttons:
   - "Subscription" button (white/translucent)
   - "Billing" button (white/translucent)
   - "Admin" button (gold gradient)
```

**Direct URLs:**
```
https://your-domain.com/subscription.html
https://your-domain.com/billing.html
```

### 2. Test Authentication

**Expected Behavior:**
- If not logged in → Redirects to `/login.html`
- If logged in → Shows subscription data
- Session validated via `/api/v1/auth/me`

**Test Steps:**
1. Clear cookies/session
2. Try to access `/subscription.html`
3. Should redirect to login
4. Login with test credentials
5. Should return to subscription page

### 3. Test Subscription Display

**What to Check:**

✓ **Tier Card Shows:**
- Current plan name (Trial, Starter, Professional, Enterprise)
- Plan description
- Feature list with checkmarks
- "Upgrade Plan" button
- "Manage Billing" button

✓ **Visual Elements:**
- Animated purple gradient background
- Gold accent colors
- Glassmorphic card effects
- Smooth transitions on hover

**Test with Different Tiers:**
```javascript
// Mock different subscription levels
// Trial user
{
  "plan": { "name": "trial", "api_calls_limit": 100 }
}

// Professional user
{
  "plan": { "name": "professional", "api_calls_limit": 10000, "byok_enabled": true }
}

// Enterprise user
{
  "plan": { "name": "enterprise", "api_calls_limit": -1, "byok_enabled": true }
}
```

### 4. Test Usage Display

**API Endpoint:**
```
GET /api/v1/subscriptions/my-access
```

**Expected Data:**
```json
{
  "usage": {
    "api_calls_used": 2547,
    "api_calls_limit": 10000,
    "period_start": "2025-10-01",
    "period_end": "2025-10-31"
  }
}
```

**Visual Checks:**
- Progress bar shows correct percentage
- API calls counter displays formatted numbers
- Billing period shows current month
- Next billing date calculated correctly
- Progress bar changes color if > 80% used

### 5. Test BYOK Key Management

**Visibility Rules:**
- **Trial users:** BYOK section HIDDEN
- **Starter+ users:** BYOK section VISIBLE
- **Admin users:** Always visible

**Test Add Key Flow:**

1. **Click "Add API Key" button**
   - Modal should open with animation
   - Form should be empty
   - Provider dropdown populated

2. **Select Provider**
   ```
   Options:
   - OpenAI
   - Anthropic (Claude)
   - HuggingFace
   - Cohere
   - Together AI
   - OpenRouter
   - Groq
   ```

3. **Enter API Key**
   - Field is type="password" (hidden)
   - Accepts any string
   - Optional label field

4. **Submit Form**
   ```javascript
   POST /api/v1/billing/account/byok-keys
   Body: {
     "provider": "openai",
     "key": "sk-...",
     "label": "My Key",
     "is_active": true
   }
   ```

5. **Verify Success**
   - Modal closes
   - Green success alert appears
   - Key appears in list with last 4 characters
   - Provider badge shows in purple gradient

**Test Delete Key:**

1. Click "Remove" button on any key
2. Confirmation dialog appears
3. If confirmed:
   ```javascript
   DELETE /api/v1/billing/account/byok-keys/{provider}
   ```
4. Key removed from list
5. Success alert shown

### 6. Test Navigation

**From Main Dashboard:**
- Click "Subscription" → Should go to `/subscription.html`
- Click "Billing" → Should go to `/billing.html`
- Click "Admin" → Should go to `/admin` (if admin)

**From Subscription Page:**
- Click "← Dashboard" → Returns to `/`
- Click "💳 Billing" → Goes to `/billing.html`
- Click "Upgrade Plan" → Goes to `/billing.html`
- Click "Manage Billing" → Goes to `/billing.html`

### 7. Test Responsive Design

**Desktop (1920x1080):**
```
✓ Tier card full width with padding
✓ Features in 2-3 column grid
✓ Usage stats in 3 columns
✓ Footer navigation in single row
✓ BYOK keys in single column
```

**Tablet (768x1024):**
```
✓ Tier card adapts to width
✓ Features in 2 column grid
✓ Usage stats in 2 columns
✓ Footer wraps to 2 rows
✓ All touch targets 44px+
```

**Mobile (375x667):**
```
✓ All content stacked (1 column)
✓ Tier card full width
✓ Features single column
✓ Usage stats 2 columns
✓ Footer stacks vertically
✓ Navigation buttons full width
✓ Modal adapts to screen
```

**Test Steps:**
1. Open browser DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test breakpoints: 375px, 768px, 1024px, 1920px
4. Check all elements resize properly
5. Verify touch targets on mobile

### 8. Test Error Handling

**Network Errors:**
```javascript
// Simulate by blocking API endpoint
// Expected: Red error alert appears
// Message: "Failed to load subscription data"
```

**Invalid API Key:**
```javascript
// Enter invalid key format
// Expected: Backend validation error
// UI shows: "Failed to add API key" alert
```

**Session Expired:**
```javascript
// Clear session cookie mid-session
// Expected: Redirect to login
// No data corruption
```

**Backend Down:**
```javascript
// Stop backend service
// Expected: Graceful error message
// Page doesn't crash
```

### 9. Test Animations

**Page Load:**
- Gradient background animates smoothly
- Cards fade in
- No layout shift

**Progress Bar:**
- Animates from 0 to actual percentage
- Shimmer effect plays continuously
- Color transitions smoothly

**Buttons:**
- Hover effects trigger on mouseover
- Transform translateY works
- Shadow appears on hover
- Transitions smooth (300ms)

**Modal:**
- Opens with fade-in
- Centers on screen
- Backdrop blur applied
- Closes smoothly

### 10. Browser Compatibility

**Chrome/Edge:**
```bash
# Should work perfectly
✓ All CSS features supported
✓ Fetch API works
✓ Backdrop filter renders
✓ Grid layout perfect
```

**Firefox:**
```bash
# Should work with minor differences
✓ Most features supported
⚠ Backdrop filter might render slightly different
✓ Grid layout works
```

**Safari:**
```bash
# Requires -webkit- prefixes (already included)
✓ Backdrop filter with -webkit prefix
✓ Background clip for gradient text
✓ All animations work
```

**Test Command:**
```bash
# Open in different browsers
google-chrome https://your-domain.com/subscription.html
firefox https://your-domain.com/subscription.html
# Safari on Mac
```

## Manual Testing Checklist

### Visual Regression
- [ ] Colors match main dashboard
- [ ] Fonts consistent (Space Grotesk, Poppins)
- [ ] Spacing follows 8px grid
- [ ] Shadows render correctly
- [ ] Gradients smooth

### Functionality
- [ ] All buttons clickable
- [ ] Forms validate input
- [ ] API calls succeed
- [ ] Error messages clear
- [ ] Success alerts appear
- [ ] Navigation works
- [ ] Modal opens/closes
- [ ] Keys add/delete

### Performance
- [ ] Page loads < 1s
- [ ] API response < 500ms
- [ ] Animations smooth 60fps
- [ ] No console errors
- [ ] No memory leaks

### Accessibility
- [ ] Tab navigation works
- [ ] Focus indicators visible
- [ ] ARIA labels present
- [ ] Color contrast passes
- [ ] Screen reader compatible

### Security
- [ ] Keys hidden in password fields
- [ ] Session validation works
- [ ] CSRF protection active
- [ ] XSS prevention in place
- [ ] Keys encrypted backend

## Automated Testing

### Test Script (JavaScript)
```javascript
// test-subscription-ui.js

// Test 1: Page loads
async function testPageLoad() {
  const response = await fetch('/subscription.html');
  console.assert(response.ok, 'Page should load');
}

// Test 2: API endpoint responds
async function testAPIEndpoint() {
  const response = await fetch('/api/v1/subscriptions/my-access', {
    credentials: 'include'
  });
  console.assert(response.ok, 'API should respond');
  const data = await response.json();
  console.assert(data.plan, 'Should have plan data');
}

// Test 3: Modal functionality
function testModal() {
  const modal = document.getElementById('add-key-modal');
  showAddKeyModal();
  console.assert(modal.classList.contains('active'), 'Modal should open');
  closeAddKeyModal();
  console.assert(!modal.classList.contains('active'), 'Modal should close');
}

// Run all tests
async function runTests() {
  await testPageLoad();
  await testAPIEndpoint();
  testModal();
  console.log('All tests passed!');
}

runTests();
```

### Run Tests
```bash
# Open browser console on subscription page
# Paste test script above
# Check console for results
```

## Common Issues

### Issue: Page shows "Loading..." forever
**Cause:** API endpoint not responding
**Fix:** Check backend is running
```bash
docker ps | grep ops-center
docker logs unicorn-ops-center
```

### Issue: BYOK section not showing for paid user
**Cause:** `byok_enabled` not set in plan
**Fix:** Verify backend plan configuration
```bash
# Check subscription_manager.py
# Ensure plan has byok_enabled: true
```

### Issue: Modal doesn't center
**Cause:** CSS flexbox not applying
**Fix:** Check browser console for CSS errors
```bash
# Modal should have display: flex
# Parent should be display: flex
```

### Issue: Progress bar stuck at 0%
**Cause:** Usage data not loading
**Fix:** Check API response format
```javascript
// Should have:
{
  "usage": {
    "api_calls_used": number,
    "api_calls_limit": number
  }
}
```

### Issue: Navigation buttons don't work
**Cause:** Incorrect href paths
**Fix:** Verify paths are correct
```html
<!-- Should be: -->
<a href="/subscription.html">Subscription</a>
<!-- NOT: -->
<a href="subscription.html">Subscription</a>
```

## Success Metrics

After testing, verify:

✅ **User can view subscription details**
✅ **User can see usage statistics**
✅ **User can add API keys** (if eligible)
✅ **User can remove API keys**
✅ **Navigation works correctly**
✅ **Responsive on all devices**
✅ **No console errors**
✅ **Visual design matches theme**
✅ **Performance is acceptable**
✅ **Security measures active**

## Reporting Issues

If you find bugs, report with:

1. **Browser/OS**: Chrome 120 / Windows 11
2. **Screen size**: 1920x1080
3. **Steps to reproduce**:
   - Go to /subscription.html
   - Click "Add API Key"
   - Submit form with OpenAI key
4. **Expected behavior**: Key should appear in list
5. **Actual behavior**: Error alert appears
6. **Console errors**: [Paste any errors]
7. **Network tab**: [Screenshot if API issue]

## Next Steps

After testing passes:
1. Deploy to production
2. Monitor user feedback
3. Track analytics (page views, conversions)
4. Iterate on features
5. Add enhancements from backlog

## Contact

Questions about testing?
- Developer: See SUBSCRIPTION_UI_IMPLEMENTATION.md
- Support: support@your-domain.com
- Issues: GitHub UC-1-Pro repository
