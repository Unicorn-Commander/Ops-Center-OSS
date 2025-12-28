# Epic 2.4: Self-Service Upgrades - UX Validation Checklist

**Project**: UC-Cloud Ops-Center
**Epic**: 2.4 - Self-Service Subscription Upgrades/Downgrades
**Author**: Testing & UX Lead
**Date**: October 24, 2025
**Status**: Ready for Manual Testing

---

## Overview

This comprehensive UX validation checklist ensures the subscription upgrade/downgrade feature provides an excellent user experience across all scenarios. Each item should be tested manually to verify functionality, usability, and visual polish.

---

## Visual Design ✨

### Tier Comparison Cards

- [ ] **All 4 tier cards render correctly** (Trial, Starter, Professional, Enterprise)
- [ ] **Professional tier has "Most Popular" badge** (purple/gold, positioned top-right)
- [ ] **Current tier is clearly highlighted** (checkmark icon, "Current Plan" text, distinct border)
- [ ] **Card hover effects work smoothly** (slight elevation, border color change)
- [ ] **Card spacing is consistent** (equal gaps, aligned heights)
- [ ] **Colors match UC-Cloud brand** (purple/gold theme, consistent with ops-center)
- [ ] **Typography is readable** (font sizes appropriate, hierarchy clear)
- [ ] **Icons display properly** (tier icons, feature checkmarks, badges)
- [ ] **Feature lists are scannable** (bullet points, icons, concise text)
- [ ] **Pricing is prominent** (large, bold, per-month/per-year clear)
- [ ] **Call-to-action buttons are visible** (contrasting colors, clear labels)

### Responsive Design

- [ ] **Mobile (320px-767px)**: Cards stack vertically, readable, touch-friendly
- [ ] **Tablet (768px-1023px)**: 2-column grid, balanced layout
- [ ] **Desktop (1024px-1919px)**: 4-column grid, optimal spacing
- [ ] **Large Desktop (1920px+)**: Cards don't stretch excessively, max-width applied
- [ ] **Text wraps correctly** at all breakpoints
- [ ] **Images/icons scale proportionally**
- [ ] **Buttons remain accessible** (min 44x44px touch target)
- [ ] **No horizontal scrolling** at any viewport size

### Upgrade Flow Stepper

- [ ] **Stepper shows 3 steps clearly** (Review, Payment, Confirmation)
- [ ] **Active step is highlighted** (color, icon, bold text)
- [ ] **Completed steps show checkmarks**
- [ ] **Future steps are de-emphasized** (grayed out)
- [ ] **Step labels are descriptive** ("Review Plan", not "Step 1")
- [ ] **Progress indicator animates smoothly**
- [ ] **Back button visible except on first step**
- [ ] **Next button changes to "Confirm" on last step**
- [ ] **Cancel button visible at all steps** (top-right or bottom-left)

### Loading States

- [ ] **Skeleton loaders for tier cards** (shimmer animation, realistic layout)
- [ ] **Loading spinner for API calls** (centered, appropriate size)
- [ ] **Progress bar for Stripe redirect** (shows checkout is loading)
- [ ] **Button loading states** (spinner icon, disabled state, "Processing..." text)
- [ ] **No layout shifts** during loading transitions
- [ ] **Loading indicators have aria-labels** for screen readers

### Error States

- [ ] **Error messages are visible** (red border, error icon, clear text)
- [ ] **Error text is actionable** ("Payment failed. Please update your card." not "Error 500")
- [ ] **Retry button is present** when applicable
- [ ] **Form validation errors are inline** (next to relevant fields)
- [ ] **Toast notifications appear** for transient errors (auto-dismiss after 5s)
- [ ] **Modal alerts for critical errors** (require explicit dismissal)

---

## User Flow - Upgrade 🚀

### Step 1: Viewing Tiers

- [ ] **User can access tier comparison** from multiple entry points:
  - [ ] Billing settings page
  - [ ] Subscription management page
  - [ ] Dashboard "Upgrade" CTA
  - [ ] Service access denied screen
- [ ] **Current tier is immediately visible** (highlighted, no need to search)
- [ ] **User can compare features** side-by-side
- [ ] **Tooltips explain complex features** (hover over info icons)
- [ ] **Annual pricing toggle works** (monthly ↔ yearly, saves 16%)
- [ ] **Currency displays correctly** (user's locale, symbol, formatting)

### Step 2: Initiating Upgrade

- [ ] **Clicking "Upgrade" opens upgrade flow modal**
- [ ] **Modal has clear title** ("Upgrade to Professional")
- [ ] **Stepper shows step 1 of 3 active**
- [ ] **Plan comparison is visible** (Current: Starter → New: Professional)
- [ ] **Feature differences highlighted** (green for new features, yellow for upgrades)
- [ ] **Price change is clear** ($19/mo → $49/mo)
- [ ] **User can change billing cycle** (monthly/yearly toggle)
- [ ] **Estimated annual savings shown** for yearly billing
- [ ] **"Next" button is enabled** (not disabled)
- [ ] **User can cancel** at any time (X button, Cancel button, ESC key)

### Step 3: Payment Preview

- [ ] **Stepper shows step 2 of 3 active**
- [ ] **Proration calculation is visible** and accurate:
  - [ ] Current plan remaining days shown
  - [ ] Credit amount displayed ($X.XX)
  - [ ] New plan prorated cost shown
  - [ ] **Immediate charge amount is prominent** ("You'll be charged $39.50 today")
  - [ ] Next billing date and amount shown ("Next billing: $49.00 on Nov 24, 2025")
- [ ] **Breakdown is expandable** (click to see detailed calculation)
- [ ] **Proration math is explained** in plain language
- [ ] **User can go back** to change plan or billing cycle
- [ ] **"Continue to Payment" button is clear**

### Step 4: Payment Confirmation

- [ ] **Stepper shows step 3 of 3 active**
- [ ] **Payment method is displayed** (card ending in 4242, or "Add Payment Method")
- [ ] **Billing address is shown** (if available)
- [ ] **Final charge amount is repeated** ("Total: $39.50")
- [ ] **Terms of service link is visible** and functional
- [ ] **"Confirm Payment" button is prominent** (primary color, large)
- [ ] **User confirms understanding** (checkbox: "I understand I'll be charged $39.50")
- [ ] **Confirm button is disabled** until checkbox is checked
- [ ] **Security badges displayed** (Stripe, SSL, payment card icons)

### Step 5: Stripe Checkout

- [ ] **Clicking "Confirm" triggers Stripe checkout**
- [ ] **Loading state shows** while checkout session creates
- [ ] **Redirects to Stripe in < 2 seconds**
- [ ] **Stripe Checkout opens** in new tab/window (user preference)
- [ ] **Stripe Checkout is pre-filled** (email, customer name)
- [ ] **User can complete payment** on Stripe
- [ ] **User can cancel** and return to ops-center
- [ ] **Test card works** (4242 4242 4242 4242) in test mode

### Step 6: Return & Confirmation

- [ ] **User redirected back to ops-center** after payment
- [ ] **Success page displays** with confetti animation 🎉
- [ ] **Success message is clear** ("Welcome to Professional!")
- [ ] **New tier features highlighted** ("You now have access to...")
- [ ] **Next steps are actionable** ("Explore new features", "Go to Dashboard")
- [ ] **Confirmation email mentioned** ("Check your inbox for receipt")
- [ ] **User can close modal** and see updated tier

### Step 7: UI Updates

- [ ] **Dashboard reflects new tier** immediately (no refresh required)
- [ ] **Billing settings show Professional**
- [ ] **Usage limits updated** (10,000 API calls/month)
- [ ] **Services unlocked** (if any were tier-gated)
- [ ] **Subscription page shows** next billing date and amount
- [ ] **Invoice history includes** upgrade transaction
- [ ] **API keys page shows** new rate limits

---

## User Flow - Downgrade ⬇️

### Step 1: Initiating Downgrade

- [ ] **User clicks "Downgrade" button** on lower tier card
- [ ] **Warning modal opens** (not immediate downgrade)
- [ ] **Modal title is clear** ("Downgrade to Starter")
- [ ] **Warning icon is visible** (⚠️ yellow/orange)

### Step 2: Understanding Impact

- [ ] **Warning message explains timing** ("Change takes effect at end of billing period")
- [ ] **Current period end date shown** ("November 24, 2025")
- [ ] **User retains access until then** ("You'll keep Professional features until Nov 24")
- [ ] **Feature loss is highlighted** ("You will lose access to:"):
  - [ ] List of features being removed
  - [ ] Icons show what's being lost (red X or minus icon)
  - [ ] API limit decrease shown (10,000 → 1,000)
- [ ] **Cost savings shown** ("Save $30/month starting Nov 24")
- [ ] **Refund policy explained** (if applicable)

### Step 3: Confirmation

- [ ] **Confirmation checkbox required** ("I understand my plan will downgrade on Nov 24")
- [ ] **Checkbox must be checked** before "Confirm Downgrade" button enables
- [ ] **"Cancel" button is prominent** (allows user to back out)
- [ ] **"Confirm Downgrade" button is secondary color** (not as prominent as upgrade)
- [ ] **User can click Cancel** at any time (ESC key works)

### Step 4: Scheduled Downgrade

- [ ] **Success message displays** ("Downgrade scheduled for Nov 24")
- [ ] **Confirmation email mentioned**
- [ ] **User can cancel downgrade** ("Changed your mind? Cancel downgrade")
- [ ] **Modal closes** after 3 seconds or user clicks "Done"

### Step 5: UI Reflects Scheduled Change

- [ ] **Billing settings show pending downgrade** (banner or badge)
- [ ] **Current tier still shown as Professional** (with note: "Downgrading to Starter on Nov 24")
- [ ] **Cancel downgrade button visible** in billing settings
- [ ] **Countdown to downgrade** visible (optional but helpful)
- [ ] **Services remain accessible** (no immediate restrictions)

### Step 6: Canceling Scheduled Downgrade

- [ ] **User can click "Cancel Downgrade"** button
- [ ] **Confirmation modal opens** ("Keep your Professional plan?")
- [ ] **User confirms cancellation**
- [ ] **Scheduled downgrade is removed** from Stripe/Lago
- [ ] **UI updates** to remove pending downgrade badge
- [ ] **Confirmation message shows** ("You'll stay on Professional")

---

## Error Handling 🚫

### Invalid Tier Selection

- [ ] **Selecting current tier shows error** ("You're already on Professional")
- [ ] **Button is disabled** for current tier
- [ ] **Cannot downgrade to Trial** (only for new signups)
- [ ] **Cannot upgrade to non-existent tier** (returns 404)

### Payment Failures

- [ ] **Card declined shows friendly error** ("Payment failed. Please try a different card.")
- [ ] **Insufficient funds handled gracefully** ("Payment failed. Please check your card balance.")
- [ ] **Network timeout retries automatically** (or offers retry button)
- [ ] **Stripe error codes translated** to user-friendly messages
- [ ] **User can update payment method** from error screen
- [ ] **Retry button re-attempts payment** without losing context

### API Failures

- [ ] **Lago API timeout shows error** ("Unable to process upgrade. Please try again.")
- [ ] **Keycloak sync failure logged** (but doesn't block upgrade)
- [ ] **Email delivery failure** doesn't prevent upgrade (logged for retry)
- [ ] **Partial upgrade failure** triggers rollback
- [ ] **User notified of technical issues** with support contact info

### Network Errors

- [ ] **Offline detection** ("You appear to be offline. Please check your connection.")
- [ ] **Request timeout** shows retry option (default: 30s timeout)
- [ ] **Intermittent failures retry automatically** (max 3 attempts)
- [ ] **Form data preserved** if network fails (user doesn't lose progress)

### Edge Cases

- [ ] **Concurrent upgrade requests** deduplicated (only one processes)
- [ ] **User clicks "Upgrade" twice** - second click ignored or idempotent
- [ ] **Upgrade during billing cycle change** handled gracefully
- [ ] **Subscription in "past_due" status** requires payment method update first
- [ ] **Cancelled subscription** cannot be upgraded (must reactivate)

---

## Accessibility ♿

### Screen Reader Compatibility

- [ ] **All tier cards have aria-labels** ("Trial tier, $1 per week, current plan")
- [ ] **Buttons have descriptive labels** ("Upgrade to Professional tier for $49 per month")
- [ ] **Form fields have labels** (not just placeholders)
- [ ] **Error messages have role="alert"** for immediate announcement
- [ ] **Loading states announced** ("Loading subscription plans")
- [ ] **Stepper progress announced** ("Step 2 of 3: Payment preview")
- [ ] **Modal focus trapped** (Tab key doesn't leave modal)
- [ ] **Modal closes on ESC key**

### Keyboard Navigation

- [ ] **All interactive elements keyboard-accessible** (Tab, Enter, Space)
- [ ] **Focus indicators visible** (outline on buttons, links, form fields)
- [ ] **Tab order is logical** (left-to-right, top-to-bottom)
- [ ] **Stepper navigable by keyboard** (arrow keys optional but helpful)
- [ ] **Modal opens with focus on first element** (usually close button or first input)
- [ ] **Modal closes with ESC key**
- [ ] **No keyboard traps** (user can always escape)

### Color Contrast

- [ ] **WCAG AA compliance** (4.5:1 for normal text, 3:1 for large text)
- [ ] **Tier card text readable** on colored backgrounds
- [ ] **Button text high contrast** (white on purple, or high-contrast combo)
- [ ] **Link text distinguishable** (underline or sufficient contrast)
- [ ] **Error text readable** (red should be dark enough)
- [ ] **Disabled state distinguishable** (not just color - opacity or pattern too)
- [ ] **Focus indicators high contrast** (3:1 minimum)

### Visual Indicators

- [ ] **Information not conveyed by color alone** (icons + text, not just green/red)
- [ ] **Loading states have animation** (not just color change)
- [ ] **Error states have icon** (! or X, not just red border)
- [ ] **Success states have icon** (✓ or ✅, not just green background)
- [ ] **Tier differences use icons** (not just color coding)

---

## Performance ⚡

### Page Load Times

- [ ] **Tier comparison page loads < 2 seconds** (first contentful paint)
- [ ] **Tier cards render progressively** (skeleton → content)
- [ ] **API calls < 500ms** (tier data, subscription status)
- [ ] **Stripe checkout redirects < 1 second** (session creation fast)
- [ ] **No layout shifts** (CLS score < 0.1)
- [ ] **Images optimized** (WebP format, appropriate sizes)
- [ ] **Bundle size reasonable** (code-split large components)

### Interaction Responsiveness

- [ ] **Button clicks respond < 100ms** (visual feedback immediate)
- [ ] **Form inputs responsive** (no lag when typing)
- [ ] **Modal animations smooth** (60fps, no jank)
- [ ] **Stepper transitions smooth** (fade or slide, < 300ms)
- [ ] **Hover effects immediate** (no delay)
- [ ] **Scroll performance good** (no stuttering)

### Data Freshness

- [ ] **Subscription data cached** (60s TTL, reduces API calls)
- [ ] **Cache invalidated on updates** (after upgrade/downgrade)
- [ ] **Optimistic UI updates** (UI changes before API confirmation)
- [ ] **Background refetch** if data stale
- [ ] **Manual refresh button** available (if needed)

---

## Mobile Experience 📱

### Touch Interactions

- [ ] **Tap targets ≥ 44x44px** (buttons, links, cards)
- [ ] **No hover-dependent features** (touch doesn't have hover)
- [ ] **Swipe to dismiss modals** (optional enhancement)
- [ ] **Pull to refresh** subscription data (optional)
- [ ] **Touch feedback visible** (ripple effect on buttons)
- [ ] **No accidental taps** (sufficient spacing between elements)

### Mobile Layout

- [ ] **Cards stack vertically** (1 column on mobile)
- [ ] **Full-width buttons** (easier to tap)
- [ ] **Sticky CTAs** (upgrade button always visible)
- [ ] **Modal covers full screen** (not floating on mobile)
- [ ] **Keyboard doesn't hide inputs** (scroll into view)
- [ ] **Safe areas respected** (no content behind notch/home indicator)

### Mobile Performance

- [ ] **Fast loading on 3G** (< 5 seconds)
- [ ] **Bundle size optimized** (< 200KB gzipped)
- [ ] **Images compressed** (WebP, lazy-loaded)
- [ ] **Animations performant** (CSS transforms, not layout changes)
- [ ] **No jank on scroll** (60fps)

---

## Cross-Browser Compatibility 🌐

### Desktop Browsers

- [ ] **Chrome/Edge (latest)** - All features work
- [ ] **Firefox (latest)** - All features work
- [ ] **Safari (latest)** - All features work
- [ ] **Opera (latest)** - All features work
- [ ] **Brave (latest)** - All features work

### Mobile Browsers

- [ ] **Safari iOS (latest)** - All features work
- [ ] **Chrome Android (latest)** - All features work
- [ ] **Samsung Internet** - All features work
- [ ] **Firefox Mobile** - All features work

### Browser Features

- [ ] **Cookies enabled** (required for session)
- [ ] **JavaScript enabled** (React app requires JS)
- [ ] **LocalStorage available** (for preferences)
- [ ] **Stripe.js loads** (3rd-party script)
- [ ] **CSS Grid/Flexbox** supported (modern browsers)
- [ ] **No console errors** in any browser

---

## Security & Privacy 🔒

### Payment Security

- [ ] **Stripe.js loads over HTTPS** (secure checkout)
- [ ] **Card data never sent to ops-center** (Stripe handles it)
- [ ] **PCI-DSS compliant** (Stripe certified)
- [ ] **SSL certificate valid** (no warnings)
- [ ] **HTTPS enforced** (HTTP redirects to HTTPS)

### Session Security

- [ ] **Session token secure** (httpOnly cookie)
- [ ] **CSRF protection enabled** (token validated)
- [ ] **XSS protection** (input sanitized, CSP headers)
- [ ] **Rate limiting applied** (prevent abuse)
- [ ] **Session expires** after inactivity (30 min)

### Data Privacy

- [ ] **Privacy policy linked** (clear data usage)
- [ ] **User can download data** (GDPR compliance)
- [ ] **User can delete account** (with confirmation)
- [ ] **Email unsubscribe link** (in all emails)
- [ ] **No tracking without consent** (cookie banner)

---

## Email Notifications 📧

### Upgrade Confirmation Email

- [ ] **Email sent immediately** after successful upgrade
- [ ] **Email arrives within 5 minutes**
- [ ] **Subject line clear** ("Welcome to Professional - UC-Cloud")
- [ ] **Email body includes**:
  - [ ] Personalized greeting (user's name)
  - [ ] Confirmation of tier change (Trial → Professional)
  - [ ] Next billing date and amount
  - [ ] New features unlocked (list or link)
  - [ ] Call to action (Explore new features)
  - [ ] Receipt/invoice (or link to download)
  - [ ] Support contact information
- [ ] **Email is mobile-responsive**
- [ ] **HTML email renders correctly** (Gmail, Outlook, Apple Mail)
- [ ] **Plain-text fallback** available
- [ ] **Unsubscribe link** visible (footer)

### Downgrade Scheduled Email

- [ ] **Email sent after scheduling downgrade**
- [ ] **Subject line clear** ("Downgrade Scheduled - UC-Cloud")
- [ ] **Email body includes**:
  - [ ] Confirmation of scheduled downgrade (Professional → Starter)
  - [ ] Effective date (end of billing period)
  - [ ] Features that will be lost
  - [ ] How to cancel downgrade (link)
  - [ ] New price after downgrade
  - [ ] Support contact
- [ ] **Email is actionable** (cancel link works)

### Payment Failed Email

- [ ] **Email sent after payment failure**
- [ ] **Subject line urgent but not alarming** ("Action Required: Payment Failed")
- [ ] **Email body includes**:
  - [ ] Explanation of failure (friendly language)
  - [ ] Action to take (Update payment method)
  - [ ] Link to update card (secure)
  - [ ] Next retry attempt date
  - [ ] What happens if not resolved (downgrade/cancellation)
  - [ ] Support contact
- [ ] **Email is urgent but helpful** (not scary)

---

## Documentation & Help 📚

### Inline Help

- [ ] **Tooltip on "Proration"** explains what it means
- [ ] **Tooltip on "API Calls"** explains limits
- [ ] **Info icons** next to complex features
- [ ] **Help button** in modal (links to docs or opens chat)
- [ ] **FAQ link** visible ("How does billing work?")

### Support Access

- [ ] **"Need help?" link** in footer
- [ ] **Chat widget** accessible (if available)
- [ ] **Support email** visible (support@your-domain.com)
- [ ] **Billing issues** get priority support
- [ ] **Error codes documented** (user can self-serve)

---

## Admin Features 🔧

### Admin Can Upgrade Users

- [ ] **Admin can upgrade any user** from user management page
- [ ] **Admin bypass payment** (manual upgrade, invoice later)
- [ ] **Admin see upgrade history** (who upgraded when)
- [ ] **Admin can refund** upgrades (within reason)
- [ ] **Admin audit log** records all changes

### Analytics & Monitoring

- [ ] **Upgrade conversion rate tracked** (views → upgrades)
- [ ] **Funnel drop-off identified** (where users abandon)
- [ ] **Payment failure rate** monitored
- [ ] **Average time to upgrade** measured
- [ ] **Most popular tier** identified (for marketing)

---

## Deployment Readiness Checklist ✅

### Pre-Deployment

- [ ] **All P0 bugs fixed** (critical, blocking release)
- [ ] **All P1 bugs fixed** (high priority, UX issues)
- [ ] **P2 bugs documented** (nice-to-have, post-launch)
- [ ] **Test coverage ≥ 80%** (backend + frontend)
- [ ] **E2E tests pass** (critical user flows)
- [ ] **Performance benchmarks met** (load times, API response)
- [ ] **Security audit passed** (pen test if applicable)
- [ ] **Accessibility audit passed** (WCAG AA compliance)

### Post-Deployment Monitoring

- [ ] **Error tracking enabled** (Sentry or similar)
- [ ] **Analytics tracking** (Google Analytics, Mixpanel)
- [ ] **Uptime monitoring** (Pingdom, UptimeRobot)
- [ ] **Payment webhook monitoring** (Stripe dashboard alerts)
- [ ] **User feedback collection** (in-app surveys, NPS)
- [ ] **Support tickets categorized** (billing issues tagged)

---

## Testing Sign-Off

**Tested By**: ___________________________
**Date**: ___________________________
**Environment**: [ ] Staging [ ] Production
**Test Result**: [ ] Pass [ ] Fail (see issues below)

### Critical Issues Found (P0/P1)

1. ________________________________________________
2. ________________________________________________
3. ________________________________________________

### Recommendations

1. ________________________________________________
2. ________________________________________________
3. ________________________________________________

### Deployment Approval

[ ] **Ready for production** - All critical issues resolved
[ ] **Not ready** - Issues must be fixed before launch

**Approver**: ___________________________
**Date**: ___________________________

---

## Appendix: Test Accounts

### Test Users (Staging Environment)

| Email | Password | Current Tier | Use Case |
|-------|----------|--------------|----------|
| trial_user@test.com | Test123! | Trial | Test Trial → Starter upgrade |
| starter_user@test.com | Test123! | Starter | Test Starter → Professional upgrade |
| pro_user@test.com | Test123! | Professional | Test downgrade to Starter |
| enterprise_user@test.com | Test123! | Enterprise | Test all tier features |

### Test Payment Cards (Stripe Test Mode)

| Card Number | Description | Expected Behavior |
|-------------|-------------|-------------------|
| 4242 4242 4242 4242 | Success | Payment succeeds |
| 4000 0000 0000 0002 | Decline | Card declined |
| 4000 0000 0000 9995 | Insufficient Funds | Payment fails |
| 4000 0027 6000 3184 | 3D Secure | Requires authentication |

### Test Proration Scenarios

| Current Tier | New Tier | Days Left | Expected Credit | Immediate Charge |
|--------------|----------|-----------|-----------------|------------------|
| Starter ($19) | Professional ($49) | 15 | $9.50 | $39.50 |
| Starter ($19) | Professional ($49) | 5 | $3.17 | $45.83 |
| Professional ($49) | Enterprise ($99) | 20 | $32.67 | $66.33 |

---

**End of UX Validation Checklist**

*This checklist should be used by QA testers, UX designers, product managers, and developers to ensure a high-quality user experience before launching Epic 2.4.*
