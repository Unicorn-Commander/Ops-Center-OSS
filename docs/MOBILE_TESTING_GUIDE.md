```markdown
# Mobile Testing Guide
## Epic 2.7: Mobile Responsiveness

**Version**: 1.0
**Last Updated**: October 24, 2025
**Author**: Mobile Testing Lead

---

## Table of Contents

1. [Introduction](#introduction)
2. [Device Matrix](#device-matrix)
3. [Testing Methodology](#testing-methodology)
4. [Comprehensive Testing Checklist](#comprehensive-testing-checklist)
5. [Common Issues & Fixes](#common-issues--fixes)
6. [Screenshot Guidelines](#screenshot-guidelines)
7. [Performance Testing](#performance-testing)
8. [Accessibility Testing](#accessibility-testing)
9. [Automated Testing](#automated-testing)
10. [Manual Testing Workflow](#manual-testing-workflow)
11. [Bug Reporting](#bug-reporting)
12. [Appendix](#appendix)

---

## Introduction

This guide provides comprehensive testing procedures for validating mobile responsiveness of the Ops-Center application across various devices, browsers, and network conditions.

### Objectives

- ✅ Ensure Ops-Center works flawlessly on mobile devices (phones & tablets)
- ✅ Validate touch targets meet Apple HIG guidelines (44x44px minimum)
- ✅ Verify no horizontal scrolling on any page
- ✅ Confirm acceptable performance on 3G/4G networks
- ✅ Ensure WCAG 2.1 AA accessibility compliance
- ✅ Identify and document all mobile-specific issues

### Success Criteria

- **100% of pages** render correctly without horizontal scrolling
- **100% of touch targets** meet minimum size requirements
- **100% of forms** are usable on mobile devices
- **Page load time** < 3 seconds on Fast 3G
- **Performance score** > 80 on Lighthouse mobile audit
- **Accessibility score** > 95 on WAVE mobile audit

---

## Device Matrix

### Required Physical Devices (Minimum 5)

| Device | OS | Screen Size | Resolution | Test Priority |
|--------|----|-----------|-----------| -------------|
| **iPhone SE (2020)** | iOS 14+ | 4.7" | 375x667 | 🔴 Critical |
| **iPhone 12 Pro** | iOS 15+ | 6.1" | 390x844 | 🔴 Critical |
| **iPhone 12 Pro Max** | iOS 15+ | 6.7" | 428x926 | 🟡 High |
| **Samsung Galaxy S21** | Android 11+ | 6.2" | 360x800 | 🔴 Critical |
| **Samsung Galaxy S22** | Android 12+ | 6.1" | 360x780 | 🟡 High |
| **Google Pixel 5** | Android 12+ | 6.0" | 393x851 | 🟡 High |
| **Google Pixel 6 Pro** | Android 13+ | 6.7" | 412x892 | 🟢 Medium |
| **iPad Mini (6th gen)** | iPadOS 15+ | 8.3" | 768x1024 | 🔴 Critical |
| **iPad Air (5th gen)** | iPadOS 15+ | 10.9" | 820x1180 | 🟡 High |
| **iPad Pro 11"** | iPadOS 15+ | 11" | 834x1194 | 🟡 High |
| **iPad Pro 12.9"** | iPadOS 15+ | 12.9" | 1024x1366 | 🟢 Medium |
| **Samsung Tab S7** | Android 11+ | 11" | 800x1280 | 🟡 High |
| **Samsung Tab S8** | Android 12+ | 11" | 800x1280 | 🟢 Medium |
| **Amazon Fire HD 10** | Fire OS | 10.1" | 800x1280 | 🟢 Medium |

### Browser Coverage

| Browser | iOS | Android | Tablet | Test Priority |
|---------|-----|---------|--------|---------------|
| **Safari** | ✅ Required | ❌ N/A | ✅ Required | 🔴 Critical |
| **Chrome** | ✅ Required | ✅ Required | ✅ Required | 🔴 Critical |
| **Firefox** | ✅ Optional | ✅ Required | ✅ Optional | 🟡 High |
| **Edge** | ✅ Optional | ✅ Optional | ✅ Optional | 🟢 Medium |
| **Samsung Internet** | ❌ N/A | ✅ Required | ❌ N/A | 🟡 High |
| **Opera** | ✅ Optional | ✅ Optional | ✅ Optional | 🟢 Low |

### Emulated Testing (BrowserStack/Sauce Labs)

If physical devices unavailable, use these emulated configurations:

**Minimum Coverage**:
- iPhone SE (Safari, Chrome)
- iPhone 12 Pro (Safari, Chrome)
- Samsung Galaxy S21 (Chrome, Samsung Internet)
- iPad Mini (Safari, Chrome)
- Samsung Tab S7 (Chrome)

---

## Testing Methodology

### Testing Approach

We use a **three-tier testing strategy**:

1. **Automated Tests** (80+ tests) - Fast feedback on code changes
2. **Manual Testing** (100+ checklist items) - Detailed UX validation
3. **Real Device Testing** (5+ devices) - Final verification before release

### Testing Levels

#### Level 1: Smoke Testing (15 minutes)
- Dashboard loads on iPhone SE
- User Management loads on iPad Mini
- No JavaScript errors in console
- Basic navigation works

#### Level 2: Functional Testing (2 hours)
- All pages render without horizontal scrolling
- Forms are usable
- Touch targets meet minimums
- Tables/cards display correctly

#### Level 3: Comprehensive Testing (8 hours)
- Full device matrix coverage
- All browsers tested
- Performance benchmarks
- Accessibility audit
- Edge case scenarios

---

## Comprehensive Testing Checklist

### Page-by-Page Manual Testing Checklist

Use this checklist for manual testing on each device. Mark items as:
- ✅ Pass
- ❌ Fail (create bug ticket)
- ⚠️ Minor issue (note for improvement)
- ➖ Not applicable

---

#### **1. Dashboard (/admin)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 1.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 1.2 | Metric cards display single column | ☐ | ☐ | ☐ | |
| 1.3 | Charts resize to fit viewport | ☐ | ☐ | ☐ | |
| 1.4 | Navigation accessible via hamburger | ☐ | ☐ | ☐ | |
| 1.5 | Quick actions visible without scrolling | ☐ | ☐ | ☐ | |
| 1.6 | Service status cards full-width | ☐ | ☐ | ☐ | |
| 1.7 | Search bar expands on tap | ☐ | ☐ | ☐ | |
| 1.8 | All buttons meet 44x44px minimum | ☐ | ☐ | ☐ | |
| 1.9 | Page loads in < 3 seconds (Fast 3G) | ☐ | ☐ | ☐ | |
| 1.10 | No layout shift after initial load | ☐ | ☐ | ☐ | |

**Tablet (768px - 1024px)**

| # | Test Item | iPad Mini | iPad Air | Samsung Tab | Notes |
|---|-----------|-----------|----------|-------------|-------|
| 1.11 | Dashboard uses 2-column grid | ☐ | ☐ | ☐ | |
| 1.12 | Charts display side-by-side | ☐ | ☐ | ☐ | |
| 1.13 | Sidebar visible (not hamburger) | ☐ | ☐ | ☐ | |
| 1.14 | Touch targets comfortable spacing | ☐ | ☐ | ☐ | |
| 1.15 | Landscape mode functional | ☐ | ☐ | ☐ | |

---

#### **2. User Management (/admin/system/users)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 2.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 2.2 | Table converts to card layout | ☐ | ☐ | ☐ | |
| 2.3 | Search bar full-width | ☐ | ☐ | ☐ | |
| 2.4 | Filter button accessible | ☐ | ☐ | ☐ | |
| 2.5 | User cards show key info | ☐ | ☐ | ☐ | |
| 2.6 | Tap card to view details | ☐ | ☐ | ☐ | |
| 2.7 | Action buttons visible in cards | ☐ | ☐ | ☐ | |
| 2.8 | Pagination controls touchable | ☐ | ☐ | ☐ | |
| 2.9 | Multi-select checkboxes ≥ 24px | ☐ | ☐ | ☐ | |
| 2.10 | Bulk actions menu accessible | ☐ | ☐ | ☐ | |
| 2.11 | "Add User" button fixed/sticky | ☐ | ☐ | ☐ | |
| 2.12 | Empty state visible on search | ☐ | ☐ | ☐ | |

**Tablet (768px - 1024px)**

| # | Test Item | iPad Mini | iPad Air | Samsung Tab | Notes |
|---|-----------|-----------|----------|-------------|-------|
| 2.13 | Table displays with 4-5 columns | ☐ | ☐ | ☐ | |
| 2.14 | Horizontal scroll for wide tables | ☐ | ☐ | ☐ | |
| 2.15 | Sticky table header functional | ☐ | ☐ | ☐ | |
| 2.16 | Sort buttons large enough | ☐ | ☐ | ☐ | |
| 2.17 | Row hover state visible | ☐ | ☐ | ☐ | |

---

#### **3. User Detail Page (/admin/system/users/:id)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 3.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 3.2 | Tabs convert to dropdown/stack | ☐ | ☐ | ☐ | |
| 3.3 | Profile header fits viewport | ☐ | ☐ | ☐ | |
| 3.4 | Charts resize correctly | ☐ | ☐ | ☐ | |
| 3.5 | Activity timeline readable | ☐ | ☐ | ☐ | |
| 3.6 | API keys list displays correctly | ☐ | ☐ | ☐ | |
| 3.7 | Role badges wrap properly | ☐ | ☐ | ☐ | |
| 3.8 | Edit button accessible | ☐ | ☐ | ☐ | |
| 3.9 | Back button visible and functional | ☐ | ☐ | ☐ | |
| 3.10 | Breadcrumbs wrap on narrow screen | ☐ | ☐ | ☐ | |

---

#### **4. Billing Dashboard (/admin/system/billing)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 4.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 4.2 | Revenue cards single column | ☐ | ☐ | ☐ | |
| 4.3 | Charts fit viewport width | ☐ | ☐ | ☐ | |
| 4.4 | Invoice table scrollable/cards | ☐ | ☐ | ☐ | |
| 4.5 | Filter controls accessible | ☐ | ☐ | ☐ | |
| 4.6 | Export button visible | ☐ | ☐ | ☐ | |
| 4.7 | Payment status badges visible | ☐ | ☐ | ☐ | |
| 4.8 | Date pickers work on mobile | ☐ | ☐ | ☐ | |

---

#### **5. Organization Settings (/admin/organization/settings)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 5.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 5.2 | Form fields full-width | ☐ | ☐ | ☐ | |
| 5.3 | Input font-size ≥ 16px | ☐ | ☐ | ☐ | |
| 5.4 | Dropdowns accessible | ☐ | ☐ | ☐ | |
| 5.5 | Submit button visible | ☐ | ☐ | ☐ | |
| 5.6 | Logo upload works on mobile | ☐ | ☐ | ☐ | |
| 5.7 | Validation errors visible | ☐ | ☐ | ☐ | |
| 5.8 | Multi-step form shows progress | ☐ | ☐ | ☐ | |

---

#### **6. Services Management (/admin/services)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 6.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 6.2 | Service cards full-width | ☐ | ☐ | ☐ | |
| 6.3 | Start/stop buttons touchable | ☐ | ☐ | ☐ | |
| 6.4 | Status indicators visible | ☐ | ☐ | ☐ | |
| 6.5 | Service logs readable | ☐ | ☐ | ☐ | |
| 6.6 | Configuration modal fits screen | ☐ | ☐ | ☐ | |

---

#### **7. LLM Management (/admin/llm)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 7.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 7.2 | Model cards display correctly | ☐ | ☐ | ☐ | |
| 7.3 | Switch model dropdown accessible | ☐ | ☐ | ☐ | |
| 7.4 | GPU metrics chart fits viewport | ☐ | ☐ | ☐ | |
| 7.5 | Test inference modal usable | ☐ | ☐ | ☐ | |
| 7.6 | Model parameters editable | ☐ | ☐ | ☐ | |

---

#### **8. Account Settings (/admin/account/profile)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 8.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 8.2 | Tabs stack or dropdown | ☐ | ☐ | ☐ | |
| 8.3 | Profile photo upload works | ☐ | ☐ | ☐ | |
| 8.4 | Input fields full-width | ☐ | ☐ | ☐ | |
| 8.5 | Input font-size ≥ 16px (no zoom) | ☐ | ☐ | ☐ | |
| 8.6 | Save button always visible | ☐ | ☐ | ☐ | |
| 8.7 | Password toggle icon touchable | ☐ | ☐ | ☐ | |
| 8.8 | 2FA QR code displays correctly | ☐ | ☐ | ☐ | |

---

#### **9. Account Security (/admin/account/security)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 9.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 9.2 | Active sessions table/cards | ☐ | ☐ | ☐ | |
| 9.3 | Revoke session buttons touchable | ☐ | ☐ | ☐ | |
| 9.4 | Change password form usable | ☐ | ☐ | ☐ | |
| 9.5 | Enable 2FA workflow smooth | ☐ | ☐ | ☐ | |

---

#### **10. Account API Keys (/admin/account/api-keys)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 10.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 10.2 | API key cards display correctly | ☐ | ☐ | ☐ | |
| 10.3 | Generate key button touchable | ☐ | ☐ | ☐ | |
| 10.4 | Copy key button functional | ☐ | ☐ | ☐ | |
| 10.5 | Revoke key confirmation modal | ☐ | ☐ | ☐ | |
| 10.6 | Key creation modal fits screen | ☐ | ☐ | ☐ | |

---

#### **11. Subscription Plan (/admin/subscription/plan)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 11.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 11.2 | Plan cards single column | ☐ | ☐ | ☐ | |
| 11.3 | Feature lists readable | ☐ | ☐ | ☐ | |
| 11.4 | Upgrade button prominent | ☐ | ☐ | ☐ | |
| 11.5 | Current plan highlighted | ☐ | ☐ | ☐ | |
| 11.6 | Pricing clearly displayed | ☐ | ☐ | ☐ | |

---

#### **12. Subscription Usage (/admin/subscription/usage)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 12.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 12.2 | Usage chart fits viewport | ☐ | ☐ | ☐ | |
| 12.3 | Quota meters visible | ☐ | ☐ | ☐ | |
| 12.4 | Date range picker usable | ☐ | ☐ | ☐ | |
| 12.5 | Export usage button accessible | ☐ | ☐ | ☐ | |

---

#### **13. Subscription Billing (/admin/subscription/billing)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 13.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 13.2 | Invoice table converts to cards | ☐ | ☐ | ☐ | |
| 13.3 | Download invoice button touchable | ☐ | ☐ | ☐ | |
| 13.4 | Payment status badges visible | ☐ | ☐ | ☐ | |
| 13.5 | Invoice details modal fits screen | ☐ | ☐ | ☐ | |

---

#### **14. Subscription Payment (/admin/subscription/payment)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 14.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 14.2 | Payment method cards display | ☐ | ☐ | ☐ | |
| 14.3 | Add payment method usable | ☐ | ☐ | ☐ | |
| 14.4 | Stripe modal responsive | ☐ | ☐ | ☐ | |
| 14.5 | Credit card inputs ≥ 16px font | ☐ | ☐ | ☐ | |
| 14.6 | Remove card confirmation modal | ☐ | ☐ | ☐ | |

---

#### **15. Organization Team (/admin/organization/team)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 15.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 15.2 | Member cards display correctly | ☐ | ☐ | ☐ | |
| 15.3 | Invite member button accessible | ☐ | ☐ | ☐ | |
| 15.4 | Member actions touchable | ☐ | ☐ | ☐ | |
| 15.5 | Invite modal fits screen | ☐ | ☐ | ☐ | |
| 15.6 | Role dropdown accessible | ☐ | ☐ | ☐ | |

---

#### **16. Organization Roles (/admin/organization/roles)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 16.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 16.2 | Role cards single column | ☐ | ☐ | ☐ | |
| 16.3 | Permission matrix readable | ☐ | ☐ | ☐ | |
| 16.4 | Create role button accessible | ☐ | ☐ | ☐ | |
| 16.5 | Edit role modal usable | ☐ | ☐ | ☐ | |

---

#### **17. Email Settings (/admin/settings/email)**

**Mobile (< 768px)**

| # | Test Item | iPhone SE | Galaxy S21 | iPad Mini | Notes |
|---|-----------|-----------|------------|-----------|-------|
| 17.1 | No horizontal scrolling | ☐ | ☐ | ☐ | |
| 17.2 | Provider selection dropdown | ☐ | ☐ | ☐ | |
| 17.3 | Configuration form usable | ☐ | ☐ | ☐ | |
| 17.4 | Test email button accessible | ☐ | ☐ | ☐ | |
| 17.5 | Success/error messages visible | ☐ | ☐ | ☐ | |

---

### Cross-Page Testing Checklist

These items apply to **all pages**:

| # | Test Item | Pass/Fail | Notes |
|---|-----------|-----------|-------|
| CP.1 | Viewport meta tag present | ☐ | `width=device-width, initial-scale=1` |
| CP.2 | No horizontal scrolling on any page | ☐ | Check body.scrollWidth |
| CP.3 | All buttons ≥ 44x44px | ☐ | Apple HIG minimum |
| CP.4 | All input fields ≥ 48px height | ☐ | Material Design minimum |
| CP.5 | Text inputs ≥ 16px font size | ☐ | Prevents iOS zoom |
| CP.6 | Touch targets spaced ≥ 8px apart | ☐ | Prevent accidental taps |
| CP.7 | Hamburger menu opens sidebar | ☐ | On screens < 768px |
| CP.8 | Mobile menu closes after selection | ☐ | UX improvement |
| CP.9 | Active page highlighted in menu | ☐ | Visual feedback |
| CP.10 | Breadcrumbs wrap on narrow screens | ☐ | No overflow |
| CP.11 | Toasts/alerts fit mobile screen | ☐ | Max width with margins |
| CP.12 | Modals adapt to mobile viewport | ☐ | Full-screen or near full-screen |
| CP.13 | Loading spinners visible | ☐ | Indicate async operations |
| CP.14 | Error messages visible | ☐ | Red, prominent |
| CP.15 | Success messages visible | ☐ | Green, prominent |
| CP.16 | Footer stacks vertically | ☐ | Single column on mobile |
| CP.17 | Images scale to fit viewport | ☐ | max-width: 100% |
| CP.18 | Videos responsive | ☐ | 16:9 aspect ratio maintained |
| CP.19 | Charts resize correctly | ☐ | No overflow |
| CP.20 | Tables convert to cards or scroll | ☐ | No horizontal viewport overflow |

---

## Common Issues & Fixes

### Issue 1: Horizontal Scrolling

**Symptoms**:
- Page wider than viewport
- User can scroll sideways
- Content cut off on right side

**Root Causes**:
- Fixed-width elements (e.g., `width: 500px`)
- Large images without `max-width: 100%`
- Tables without overflow handling
- Negative margins pushing content outside
- `white-space: nowrap` on long text

**Fixes**:

```css
/* 1. Set max-width on body */
body {
  max-width: 100vw;
  overflow-x: hidden;
}

/* 2. Responsive images */
img {
  max-width: 100%;
  height: auto;
}

/* 3. Responsive tables */
.table-container {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

/* 4. Flexible layouts */
.container {
  max-width: 100%;
  padding: 0 16px;
  box-sizing: border-box;
}

/* 5. Prevent text overflow */
.text-content {
  word-wrap: break-word;
  overflow-wrap: break-word;
}
```

**Verification**:
```javascript
// Check in browser console
document.body.scrollWidth <= window.innerWidth
```

---

### Issue 2: Text Too Small

**Symptoms**:
- Users need to zoom to read
- iOS auto-zooms on input focus

**Root Causes**:
- Font-size < 14px for body text
- Input fields < 16px font-size
- Insufficient contrast ratio

**Fixes**:

```css
/* 1. Minimum font sizes */
body {
  font-size: 16px; /* Base size */
}

input, textarea, select {
  font-size: 16px; /* Prevents iOS zoom */
}

button {
  font-size: 14px; /* Readable */
}

/* 2. Responsive typography */
@media (max-width: 767px) {
  h1 { font-size: 24px; }
  h2 { font-size: 20px; }
  h3 { font-size: 18px; }
  p { font-size: 16px; }
}
```

**Verification**:
```javascript
// Check input font size
const input = document.querySelector('input');
const fontSize = window.getComputedStyle(input).fontSize;
console.log(parseFloat(fontSize)); // Should be >= 16
```

---

### Issue 3: Buttons Too Small

**Symptoms**:
- Hard to tap buttons accurately
- Users miss buttons frequently
- Accessibility audit failures

**Root Causes**:
- Buttons < 44x44px (Apple HIG minimum)
- Icon buttons without padding
- Inline links without touch area

**Fixes**:

```css
/* 1. Minimum button size */
button, .btn {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 24px;
}

/* 2. Icon buttons */
.icon-button {
  width: 48px;
  height: 48px;
  padding: 12px;
}

/* 3. Link padding */
a {
  padding: 8px 4px;
  min-height: 32px;
  display: inline-block;
}

/* 4. Touch target spacing */
button + button {
  margin-left: 8px;
}
```

**Verification**:
```javascript
// Check button size
const buttons = document.querySelectorAll('button');
buttons.forEach(btn => {
  const rect = btn.getBoundingClientRect();
  if (rect.width < 44 || rect.height < 44) {
    console.warn('Small button:', btn, rect);
  }
});
```

---

### Issue 4: Tables Unreadable

**Symptoms**:
- Tables overflow viewport
- Columns too narrow
- Text truncated

**Root Causes**:
- Fixed table layout
- Too many columns for mobile
- No responsive strategy

**Fixes**:

**Option A: Card Layout** (Recommended)

```css
@media (max-width: 767px) {
  table, thead, tbody, th, td, tr {
    display: block;
  }

  thead {
    display: none; /* Hide headers */
  }

  tr {
    margin-bottom: 16px;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 12px;
  }

  td {
    display: flex;
    justify-content: space-between;
    padding: 8px 0;
  }

  td::before {
    content: attr(data-label);
    font-weight: bold;
    margin-right: 8px;
  }
}
```

**Option B: Horizontal Scroll**

```css
.table-container {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 767px) {
  table {
    min-width: 600px; /* Force scroll */
  }
}
```

---

### Issue 5: Forms Zoom on Input Focus (iOS)

**Symptoms**:
- Page zooms when tapping input
- Disorienting user experience
- Hard to see submit button

**Root Causes**:
- Input font-size < 16px
- iOS Safari auto-zooms on small inputs

**Fixes**:

```css
/* Fix: Ensure 16px minimum on inputs */
input[type="text"],
input[type="email"],
input[type="password"],
input[type="search"],
input[type="tel"],
textarea,
select {
  font-size: 16px; /* Critical for iOS */
}

/* Alternative: Disable zoom (not recommended) */
/* <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"> */
```

**Verification**:
```javascript
// Check all inputs
const inputs = document.querySelectorAll('input, textarea');
inputs.forEach(input => {
  const fontSize = parseFloat(window.getComputedStyle(input).fontSize);
  if (fontSize < 16) {
    console.error('Input will cause zoom:', input);
  }
});
```

---

### Issue 6: Charts Don't Resize

**Symptoms**:
- Charts overflow viewport
- X-axis labels cut off
- Unreadable legends

**Root Causes**:
- Fixed width/height on chart canvas
- Chart.js not responsive
- Container not fluid

**Fixes**:

```javascript
// Chart.js responsive configuration
const chart = new Chart(ctx, {
  type: 'line',
  data: chartData,
  options: {
    responsive: true,
    maintainAspectRatio: true,
    aspectRatio: 2, // Width:height ratio
    scales: {
      x: {
        ticks: {
          maxRotation: 45, // Angle labels on mobile
          minRotation: 45
        }
      }
    },
    plugins: {
      legend: {
        position: 'bottom', // Move legend below chart
        labels: {
          boxWidth: 12, // Smaller legend boxes
          padding: 8
        }
      }
    }
  }
});
```

```css
/* Chart container */
.chart-container {
  position: relative;
  width: 100%;
  max-width: 100%;
  height: auto;
}

@media (max-width: 767px) {
  .chart-container {
    height: 250px; /* Fixed height on mobile */
  }
}
```

---

### Issue 7: Modals Too Large

**Symptoms**:
- Modal extends beyond viewport
- Can't see close button
- Content cut off

**Root Causes**:
- Fixed width modals
- No max-height constraint
- Poor mobile styling

**Fixes**:

```css
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 1000;
}

.modal-content {
  max-width: 600px;
  width: 90%;
  max-height: 90vh;
  margin: 5vh auto;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

@media (max-width: 767px) {
  .modal-content {
    width: 95%;
    max-width: 100%;
    margin: 8px;
    border-radius: 8px;
  }
}
```

---

### Issue 8: Navigation Menu Issues

**Symptoms**:
- Can't access menu on mobile
- Menu doesn't close after selection
- Hamburger icon missing

**Root Causes**:
- No mobile menu implementation
- Poor JavaScript handling
- CSS conflicts

**Fixes**:

```jsx
// React mobile menu component
function MobileMenu() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        className="hamburger"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle menu"
        style={{ width: 48, height: 48 }}
      >
        {isOpen ? '✕' : '☰'}
      </button>

      <nav
        className={`mobile-menu ${isOpen ? 'open' : ''}`}
        aria-hidden={!isOpen}
      >
        <a href="/admin" onClick={() => setIsOpen(false)}>
          Dashboard
        </a>
        <a href="/admin/users" onClick={() => setIsOpen(false)}>
          Users
        </a>
        {/* More menu items */}
      </nav>
    </>
  );
}
```

```css
/* Mobile menu styles */
.hamburger {
  display: none;
}

@media (max-width: 767px) {
  .hamburger {
    display: block;
  }

  .mobile-menu {
    position: fixed;
    top: 60px;
    left: -100%;
    width: 80%;
    height: calc(100vh - 60px);
    background: white;
    transition: left 0.3s ease;
    box-shadow: 2px 0 8px rgba(0,0,0,0.2);
    z-index: 999;
  }

  .mobile-menu.open {
    left: 0;
  }

  .mobile-menu a {
    display: block;
    padding: 16px 24px;
    min-height: 48px;
    border-bottom: 1px solid #eee;
  }
}
```

---

## Screenshot Guidelines

### Required Screenshots

For each device, capture screenshots of:

1. **Homepage/Dashboard** - Full page
2. **User Management** - Table/card view
3. **User Detail Page** - Profile section
4. **Forms** - Account Settings with inputs
5. **Modals** - Any modal dialog open
6. **Mobile Menu** - Hamburger menu opened
7. **Errors** - Validation error state
8. **Loading States** - Spinners visible

### Screenshot Naming Convention

Format: `[page]_[device]_[browser]_[state].png`

Examples:
- `dashboard_iphone12_safari_default.png`
- `users_galaxys21_chrome_list-view.png`
- `modal_ipadmini_safari_open.png`
- `form_iphone12_safari_validation-error.png`

### Screenshot Tools

**iOS**:
- Built-in: Power + Volume Up
- Annotation: Markup tool in Photos app

**Android**:
- Built-in: Power + Volume Down
- Annotation: Google Photos editor

**Desktop (Emulation)**:
- Chrome DevTools: Device toolbar → More tools → Capture screenshot
- Firefox DevTools: Responsive Design Mode → Screenshot icon
- Browser Extensions: Full Page Screen Capture, Nimbus Screenshot

### Before/After Screenshots

When documenting fixes, create comparison images:

```
Before:
dashboard_before_iphone12_safari.png

After:
dashboard_after_iphone12_safari.png
```

Use annotation tools to highlight:
- ❌ Issues (red circles/arrows)
- ✅ Fixes (green checkmarks)
- ⚠️ Warnings (yellow highlights)

---

## Performance Testing

### Network Throttling

Test on simulated mobile networks:

**Chrome DevTools**:
1. Open DevTools (F12)
2. Network tab → Throttling dropdown
3. Select: Slow 3G, Fast 3G, or Custom

**Custom 3G Preset**:
```
Download: 1.6 Mbps
Upload: 750 Kbps
Latency: 150ms
```

### Performance Metrics

Track these Core Web Vitals:

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| **FCP** (First Contentful Paint) | < 1.8s | 1.8s - 3s | > 3s |
| **LCP** (Largest Contentful Paint) | < 2.5s | 2.5s - 4s | > 4s |
| **FID** (First Input Delay) | < 100ms | 100 - 300ms | > 300ms |
| **CLS** (Cumulative Layout Shift) | < 0.1 | 0.1 - 0.25 | > 0.25 |
| **TTI** (Time to Interactive) | < 3.8s | 3.8s - 7.3s | > 7.3s |

### Lighthouse Mobile Audit

Run Lighthouse in Chrome DevTools:

```bash
# Command line
lighthouse https://your-domain.com/admin \
  --preset=perf \
  --form-factor=mobile \
  --throttling.rttMs=150 \
  --throttling.throughputKbps=1638 \
  --throttling.cpuSlowdownMultiplier=4 \
  --output=html \
  --output-path=./lighthouse-mobile-report.html
```

**Target Scores**:
- Performance: > 90
- Accessibility: > 95
- Best Practices: > 90
- SEO: > 90

### WebPageTest Mobile Testing

Use WebPageTest.org for real device testing:

1. Go to https://www.webpagetest.org/
2. Enter URL: `https://your-domain.com/admin`
3. Select:
   - Test Location: `Dulles, VA - Moto G4 - 3G`
   - Browser: `Chrome`
   - Connection: `3G`
4. Click "Start Test"

**Target Metrics**:
- Load Time: < 3 seconds
- Speed Index: < 3 seconds
- Time to Interactive: < 5 seconds

---

## Accessibility Testing

### Mobile-Specific Accessibility

Beyond standard WCAG 2.1 AA, test:

1. **Touch Targets**: ≥ 44x44px (Apple HIG)
2. **Font Sizes**: ≥ 16px for inputs (iOS zoom prevention)
3. **Contrast Ratios**: 4.5:1 for text, 3:1 for graphics
4. **Zoom Support**: Page works at 200% zoom
5. **Screen Reader**: VoiceOver (iOS), TalkBack (Android)
6. **Orientation**: Works in portrait and landscape
7. **Motion**: Respects prefers-reduced-motion

### Screen Reader Testing

**iOS VoiceOver**:
1. Settings → Accessibility → VoiceOver → On
2. Three-finger swipe left/right to navigate
3. Double-tap to activate elements
4. Swipe up/down to access rotor

**Android TalkBack**:
1. Settings → Accessibility → TalkBack → On
2. Swipe right to move forward
3. Swipe left to move backward
4. Double-tap to activate

**Test Checklist**:
- ☐ All images have alt text
- ☐ Form inputs have labels
- ☐ Buttons have accessible names
- ☐ Headings follow logical hierarchy
- ☐ Links describe destination
- ☐ Tables have proper structure

### WAVE Mobile Audit

Use WAVE Chrome extension:

1. Install: https://wave.webaim.org/extension/
2. Open page on mobile viewport
3. Click WAVE icon
4. Review errors and warnings

**Target**:
- 0 Errors
- < 5 Warnings
- 0 Contrast errors

---

## Automated Testing

### Running Automated Tests

```bash
# Install dependencies
cd /home/muut/Production/UC-Cloud/services/ops-center
npm install playwright @axe-core/playwright lighthouse

# Run all mobile tests
npx playwright test tests/mobile/

# Run specific test suite
npx playwright test tests/mobile/mobile-responsiveness.test.js
npx playwright test tests/mobile/mobile-accessibility.test.js
npx playwright test tests/mobile/mobile-performance.test.js

# Run tests with UI
npx playwright test --ui

# Generate HTML report
npx playwright test --reporter=html
```

### Test Coverage

**80+ Automated Tests**:
- 15 Viewport Tests (6 devices)
- 20 Layout Tests (grid, stacking, responsive)
- 15 Touch Target Tests (44x44px compliance)
- 10 Table Tests (responsive data display)
- 12 Form Tests (input optimization)
- 8 Navigation Tests (mobile menu)

**30+ Accessibility Tests**:
- Touch target sizes
- Font size compliance
- Color contrast ratios
- Screen reader compatibility
- Zoom support
- Keyboard navigation

**25+ Performance Tests**:
- Page load times (3G/4G)
- Web Vitals (FCP, LCP, CLS, TTI, FID)
- Touch response times
- Scroll performance
- Resource loading
- Memory usage

### CI/CD Integration

Add to GitHub Actions workflow:

```yaml
# .github/workflows/mobile-tests.yml
name: Mobile Responsiveness Tests

on: [push, pull_request]

jobs:
  mobile-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd services/ops-center
          npm install

      - name: Install Playwright
        run: npx playwright install --with-deps

      - name: Run mobile responsiveness tests
        run: npx playwright test tests/mobile/mobile-responsiveness.test.js

      - name: Run mobile accessibility tests
        run: npx playwright test tests/mobile/mobile-accessibility.test.js

      - name: Run mobile performance tests
        run: npx playwright test tests/mobile/mobile-performance.test.js

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v2
        with:
          name: mobile-test-results
          path: playwright-report/
```

---

## Manual Testing Workflow

### Step-by-Step Process

#### 1. Pre-Testing Setup (15 minutes)

- [ ] Charge all devices to 100%
- [ ] Connect to stable WiFi
- [ ] Clear browser cache on all devices
- [ ] Enable network throttling in DevTools
- [ ] Open testing checklist spreadsheet
- [ ] Set up screenshot naming convention

#### 2. Device Testing Session (2 hours per device)

**For each device**:

1. **Dashboard Page** (15 min)
   - Load page
   - Check for horizontal scrolling
   - Test all interactive elements
   - Capture screenshots
   - Note any issues

2. **User Management** (20 min)
   - Load user list
   - Test search/filter
   - Test table/card layout
   - Click into user detail
   - Test bulk actions

3. **Forms** (20 min)
   - Account Settings
   - Test input focus (no zoom)
   - Test dropdowns
   - Test date pickers
   - Submit form

4. **Navigation** (15 min)
   - Open hamburger menu
   - Navigate to all sections
   - Test breadcrumbs
   - Test back button

5. **Modals** (15 min)
   - Open various modals
   - Check sizing
   - Test form submission
   - Test close button

6. **Edge Cases** (15 min)
   - Rotate to landscape
   - Test with long content
   - Test with no data
   - Test error states

7. **Performance** (20 min)
   - Run Lighthouse audit
   - Test on 3G throttling
   - Check load times
   - Monitor battery drain

#### 3. Documentation (30 minutes)

- [ ] Fill out testing checklist
- [ ] Annotate screenshots
- [ ] Create bug tickets
- [ ] Update test report

---

## Bug Reporting

### Bug Report Template

```markdown
**Bug Title**: [Page] - [Issue] on [Device]

**Severity**:
- 🔴 Critical (blocks core functionality)
- 🟡 High (major UX issue)
- 🟢 Medium (minor UX issue)
- 🔵 Low (cosmetic)

**Device**: iPhone 12 Pro
**OS**: iOS 15.6
**Browser**: Safari 15
**Viewport**: 390x844

**Steps to Reproduce**:
1. Navigate to /admin/system/users
2. Tap "Add User" button
3. Fill in form fields
4. Tap "Submit"

**Expected Result**:
User created successfully, modal closes, list refreshes

**Actual Result**:
Modal doesn't close, form validation errors not visible

**Screenshots**:
![Before](bug-screenshot-before.png)
![After](bug-screenshot-after.png)

**Console Errors**:
```
Uncaught TypeError: Cannot read property 'close' of undefined
  at submitHandler (UserForm.jsx:45)
```

**Suggested Fix**:
Add null check before calling modal.close()
```

---

## Appendix

### A. Responsive Breakpoints

```css
/* Mobile First Approach */
/* xs: 0-575px (phones) */
@media (min-width: 0px) { }

/* sm: 576-767px (large phones) */
@media (min-width: 576px) { }

/* md: 768-991px (tablets) */
@media (min-width: 768px) { }

/* lg: 992-1199px (desktops) */
@media (min-width: 992px) { }

/* xl: 1200-1399px (large desktops) */
@media (min-width: 1200px) { }

/* xxl: 1400px+ (extra large) */
@media (min-width: 1400px) { }
```

### B. Touch Target Size Reference

| Element Type | Minimum Size | Recommended Size | Notes |
|--------------|-------------|------------------|-------|
| Primary button | 44x44px | 48x48px | Apple HIG / Material Design |
| Secondary button | 44x44px | 48x48px | Same as primary |
| Icon button | 48x48px | 56x56px | More padding needed |
| Link in text | 32px height | 40px height | Inline padding |
| Checkbox/Radio | 24x24px | 32x32px | With label clickable |
| Toggle switch | 44x44px | 48x48px | Including handle area |
| Dropdown | 44px height | 48px height | Full width on mobile |
| Text input | 44px height | 48px height | Font-size ≥ 16px |

### C. Font Size Reference

| Element | Desktop | Mobile | iOS Prevention |
|---------|---------|--------|----------------|
| Body text | 16px | 16px | - |
| Headings h1 | 32px | 24-28px | - |
| Headings h2 | 24px | 20-22px | - |
| Headings h3 | 20px | 18px | - |
| Buttons | 14-16px | 14-16px | - |
| **Text inputs** | 14-16px | **16px** | ✅ Prevents zoom |
| Captions | 12-14px | 12-14px | - |

### D. Useful Testing Tools

**Browser DevTools**:
- Chrome DevTools (Mobile emulation)
- Firefox Responsive Design Mode
- Safari Web Inspector (iOS simulator)

**Real Device Testing**:
- BrowserStack (cloud devices)
- Sauce Labs (cloud devices)
- AWS Device Farm (real devices)

**Accessibility**:
- WAVE (web accessibility evaluator)
- axe DevTools (Chrome extension)
- Lighthouse (Chrome DevTools)
- VoiceOver (iOS screen reader)
- TalkBack (Android screen reader)

**Performance**:
- Lighthouse CI
- WebPageTest.org
- Chrome DevTools Performance tab
- Firefox Performance Profiler

**Screenshot/Recording**:
- Nimbus Screenshot (Chrome extension)
- Full Page Screen Capture (Firefox)
- Loom (screen recording)
- iOS Screen Recording (built-in)

### E. Quick Reference Commands

```bash
# Run all mobile tests
npx playwright test tests/mobile/

# Run specific viewport test
npx playwright test -g "iPhone SE"

# Run accessibility tests only
npx playwright test tests/mobile/mobile-accessibility.test.js

# Run with headed browser (see UI)
npx playwright test --headed

# Generate HTML report
npx playwright test --reporter=html

# Run Lighthouse audit
lighthouse https://your-domain.com/admin \
  --preset=perf \
  --form-factor=mobile \
  --output=html

# Check viewport meta tag
curl -s https://your-domain.com/admin | grep viewport
```

---

## Changelog

**v1.0 - October 24, 2025**
- Initial mobile testing guide created
- 100+ item comprehensive checklist
- 17 pages covered
- Common issues & fixes documented
- Screenshot guidelines added
- Performance testing procedures
- Accessibility testing procedures
- Automated testing integration

---

**END OF GUIDE**

For questions or updates, contact the Mobile Testing Lead.
```
