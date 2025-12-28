# Epic 2.5 - UX Lead Test Plan
## Responsive Design & Dark Mode Compliance

**Date**: October 24, 2025
**Version**: 1.0.0
**Status**: Ready for Testing

---

## Test Environment Setup

### Required Tools
- [ ] Chrome DevTools (Device Toolbar)
- [ ] Firefox Responsive Design Mode
- [ ] Safari Web Inspector (macOS/iOS)
- [ ] Edge DevTools
- [ ] Lighthouse (Accessibility Audit)
- [ ] axe DevTools (Chrome Extension)
- [ ] WAVE (Web Accessibility Evaluation Tool)

### Test Devices (Physical)
- [ ] iPhone 13 Mini (iOS)
- [ ] iPhone 15 Pro Max (iOS)
- [ ] Samsung Galaxy S24 (Android)
- [ ] iPad Air (iPadOS)
- [ ] Desktop 1920×1080
- [ ] Desktop 2560×1440

### Test Browsers
- [ ] Chrome/Chromium (v120+)
- [ ] Firefox (v121+)
- [ ] Safari (v17+)
- [ ] Edge (v120+)

---

## 1. Responsive Design Testing

### 1.1 DashboardPro Layout

#### Breakpoint: xs (0-599px - Mobile Portrait)

**Test Cases**:
- [ ] All metric cards stack vertically (1 column)
- [ ] No horizontal scrolling
- [ ] System health indicator visible
- [ ] Header title truncates properly (no overflow)
- [ ] Quick actions collapse to mobile menu
- [ ] Service grid shows 2 columns
- [ ] All text readable (minimum 14px font)
- [ ] Touch targets ≥ 44×44px

**Expected Layout**:
```
┌─────────────────┐
│ Header          │
│ Health: 95%  ⭕ │
├─────────────────┤
│ Metric Card 1   │
├─────────────────┤
│ Metric Card 2   │
├─────────────────┤
│ Metric Card 3   │
├─────────────────┤
│ Metric Card 4   │
├─────────────────┤
│ Quick Actions ☰ │
├─────────────────┤
│ Resources       │
│ [Gauges stacked]│
├─────────────────┤
│ System Info     │
├─────────────────┤
│ Services (2 col)│
│ [■][■]          │
│ [■][■]          │
└─────────────────┘
```

#### Breakpoint: sm (600-959px - Mobile Landscape / Small Tablet)

**Test Cases**:
- [ ] Metric cards show 2 columns
- [ ] Service grid shows 3 columns
- [ ] Resource gauges remain stacked
- [ ] System info cards visible
- [ ] Quick actions show icons + text
- [ ] Charts display at 250px height
- [ ] No content clipping

**Expected Layout**:
```
┌─────────────────────────────┐
│ Header            Health ⭕  │
├──────────────┬──────────────┤
│ Metric 1     │ Metric 2     │
├──────────────┼──────────────┤
│ Metric 3     │ Metric 4     │
├──────────────┴──────────────┤
│ Quick Actions  [Btn] [Btn]  │
├──────────────┬──────────────┤
│ Resources    │ System Info  │
│ [Gauges]     │ [Cards]      │
├──────────────┴──────────────┤
│ Services (3 columns)        │
│ [■][■][■]                   │
└─────────────────────────────┘
```

#### Breakpoint: md (960-1279px - Tablet)

**Test Cases**:
- [ ] Metric cards show 3 columns
- [ ] Service grid shows 4 columns
- [ ] Resource monitoring takes 2/3 width
- [ ] System info takes 1/3 width
- [ ] All charts display at 300px height
- [ ] Circular progress 150px diameter
- [ ] Subsystem breakdown shows all items

#### Breakpoint: lg (1280-1919px - Desktop)

**Test Cases**:
- [ ] Metric cards show 4 columns (full grid)
- [ ] Service grid shows 6 columns
- [ ] Resource/System split: 2/3 to 1/3 ratio
- [ ] All charts at full size (300px)
- [ ] Hover effects work smoothly
- [ ] All animations at 60fps

#### Breakpoint: xl (1920px+ - Large Desktop)

**Test Cases**:
- [ ] Layout maintains proper spacing
- [ ] Cards don't stretch excessively
- [ ] Max-width constraints applied
- [ ] Text remains readable (not too large)
- [ ] Images don't pixelate

---

### 1.2 Component-Specific Responsive Tests

#### SystemHealthScore Component

| Breakpoint | Circle Size | Score Text | Subsystem Breakdown |
|------------|-------------|------------|---------------------|
| xs (Mobile) | 100px | 24px bold | Icons only |
| sm (Tablet) | 120px | 28px bold | Icons + labels |
| md+ (Desktop) | 150px | 32px bold | Full details |

**Test Cases**:
- [ ] Circle renders correctly at all sizes
- [ ] Score percentage visible and centered
- [ ] Animation smooth (no jank)
- [ ] Color coding works (green/yellow/red)
- [ ] Subsystem breakdown adapts properly

#### QuickActions Component

| Breakpoint | Layout | Button Size | Icons |
|------------|--------|-------------|-------|
| xs | 1 column (stacked) | Full width | 24px |
| sm | 2 columns | 50% width | 20px |
| md+ | 3 columns | Auto width | 20px |

**Test Cases**:
- [ ] Touch targets ≥ 44px on mobile
- [ ] Buttons have proper spacing (8px gap)
- [ ] Icons scale appropriately
- [ ] Text doesn't wrap awkwardly
- [ ] Hover states work on desktop
- [ ] Active states work on mobile

#### RecentActivityWidget Component

| Breakpoint | Timeline Style | Text Truncation | Items Shown |
|------------|----------------|-----------------|-------------|
| xs | Compact | After 40 chars | Top 5 |
| sm+ | Full | After 80 chars | Top 10 |

**Test Cases**:
- [ ] Timeline renders without overflow
- [ ] Long activity names truncate with ellipsis
- [ ] Timestamps format correctly
- [ ] Scrollable if > threshold items
- [ ] Touch scrolling smooth on mobile

#### ResourceChart Component

| Breakpoint | Chart Height | Charts Per Row | Legend Position |
|------------|--------------|----------------|-----------------|
| xs | 200px | 1 (stacked) | Bottom (collapsed) |
| sm | 250px | 2 | Bottom |
| md+ | 300px | 3-4 | Right |

**Test Cases**:
- [ ] Charts render without distortion
- [ ] Data points visible at all sizes
- [ ] Legends readable
- [ ] Tooltips work on hover/touch
- [ ] Responsive reflow smooth

---

## 2. Dark Mode Testing

### 2.1 Theme Context Verification

**Test Each Theme**:
1. **Unicorn Theme** (Purple/Gold Gradients)
2. **Dark Theme** (Dark background, light text)
3. **Light Theme** (Light background, dark text)

**For Each Theme, Verify**:
- [ ] Background colors correct
- [ ] Text colors readable
- [ ] Border colors visible
- [ ] Glassmorphism effects work
- [ ] Gradient overlays render
- [ ] Icons inherit correct color

### 2.2 Component Dark Mode Compliance

#### DashboardPro

**Dark Mode Checklist**:
- [ ] Main background uses `theme.background`
- [ ] Cards use `theme.card`
- [ ] Text uses `theme.text.primary/secondary`
- [ ] Accent colors use `theme.text.accent`
- [ ] Status colors use `theme.status.*`
- [ ] Glassmorphism blur adjusts (dark: 20px, light: 10px)
- [ ] Border opacity correct (dark: 0.5, light: 0.2)

#### MetricCard

**Dark Mode Checklist**:
- [ ] Background gradient adjusts per theme
- [ ] Icon color matches theme
- [ ] Title text uses `theme.text.secondary`
- [ ] Value text uses `theme.text.primary`
- [ ] Subtitle uses `theme.text.secondary` with opacity
- [ ] Hover effect visible in all themes
- [ ] Border adapts to theme

#### ResourceGauge

**Dark Mode Checklist**:
- [ ] Progress bar background adjusts
- [ ] Progress fill gradient theme-aware
- [ ] Text labels use theme colors
- [ ] Icon color theme-aware
- [ ] Shimmer effect visible in all themes

#### Chart Components (Chart.js)

**Dark Mode Configuration**:
```javascript
{
  plugins: {
    legend: {
      labels: { color: theme.text.primary }
    }
  },
  scales: {
    x: {
      ticks: { color: theme.text.secondary },
      grid: { color: theme.divider }
    },
    y: {
      ticks: { color: theme.text.secondary },
      grid: { color: theme.divider }
    }
  }
}
```

**Test Cases**:
- [ ] Chart legend readable in all themes
- [ ] Axis labels visible
- [ ] Grid lines subtle but visible
- [ ] Tooltip background contrasts with chart
- [ ] Data series colors distinct

---

## 3. Accessibility Testing (WCAG AA)

### 3.1 Color Contrast

**Automated Testing**:
- [ ] Run Lighthouse accessibility audit (score ≥ 90)
- [ ] Run axe DevTools (0 violations)
- [ ] Use WAVE to check all pages

**Manual Contrast Checks** (using `a11y.js` utilities):

| Element | Foreground | Background | Required Ratio | Actual Ratio | Pass? |
|---------|------------|------------|----------------|--------------|-------|
| Normal Text (Dark) | #E5E7EB | #1F2937 | 4.5:1 | | |
| Normal Text (Light) | #1F2937 | #F9FAFB | 4.5:1 | | |
| Large Text (Dark) | #9CA3AF | #1F2937 | 3:1 | | |
| Large Text (Light) | #4B5563 | #F9FAFB | 3:1 | | |
| Accent Text (Unicorn) | #A78BFA | #0F172A | 4.5:1 | | |
| Success Status | #34D399 | #1F2937 | 4.5:1 | | |
| Warning Status | #FBBF24 | #1F2937 | 4.5:1 | | |
| Error Status | #F87171 | #1F2937 | 4.5:1 | | |

**Test Script**:
```javascript
import { checkColorContrast } from '../utils/a11y';

// Example checks
checkColorContrast('#E5E7EB', '#1F2937', false); // Normal text
checkColorContrast('#A78BFA', '#0F172A', false); // Accent
```

### 3.2 Keyboard Navigation

**Test Cases**:
- [ ] All interactive elements focusable
- [ ] Tab order logical (top to bottom, left to right)
- [ ] Focus indicators visible (outline or border)
- [ ] Skip to main content link works
- [ ] Enter key activates buttons
- [ ] Escape closes modals
- [ ] Arrow keys navigate lists
- [ ] Spacebar toggles checkboxes

**Test Sequence**:
1. Navigate entire page using only Tab
2. Activate buttons using Enter
3. Close modals using Escape
4. Navigate dropdowns using Arrow keys
5. Toggle switches using Spacebar

### 3.3 Screen Reader Testing

**Tools**:
- NVDA (Windows) - Free
- JAWS (Windows) - Trial
- VoiceOver (macOS/iOS) - Built-in
- TalkBack (Android) - Built-in

**Test Cases**:
- [ ] All images have alt text
- [ ] Buttons have aria-labels
- [ ] Form inputs have labels
- [ ] Error messages announced
- [ ] Loading states announced
- [ ] Success messages announced
- [ ] Charts have aria-labels describing data
- [ ] Modals trap focus correctly

**Screen Reader Announcements** (using `announceToScreenReader()`):
- [ ] "Loading dashboard data..." on mount
- [ ] "Dashboard data loaded" on success
- [ ] "Failed to load data, please retry" on error
- [ ] "Service started successfully" on action
- [ ] "User role updated" on change

### 3.4 Focus Management

**Test Cases**:
- [ ] Modal opens → Focus traps inside
- [ ] Modal closes → Focus returns to trigger
- [ ] Dropdown opens → Focus moves to first item
- [ ] Form submits → Focus moves to first error (if any)
- [ ] Page loads → Focus on skip link or main heading

---

## 4. Touch Interaction Testing (Mobile)

### 4.1 Touch Target Sizes

**Minimum Requirements**:
- All interactive elements ≥ 44×44px
- Adequate spacing between targets (≥ 8px)

**Test Cases**:
- [ ] All buttons meet minimum size
- [ ] Card click areas adequate
- [ ] Toggle switches large enough
- [ ] Dropdown triggers easy to tap
- [ ] Form inputs large enough
- [ ] Close buttons (X) adequately sized

**Measurement Tool**:
```javascript
// Use in DevTools console
document.querySelectorAll('button, a, input, [role="button"]').forEach(el => {
  const rect = el.getBoundingClientRect();
  if (rect.width < 44 || rect.height < 44) {
    console.warn('Small touch target:', el, `${rect.width}×${rect.height}px`);
  }
});
```

### 4.2 Gesture Support

**Swipe Gestures** (using `useTouchGestures` hook):
- [ ] Swipe left on alert → Dismiss
- [ ] Swipe right on activity item → View details
- [ ] Swipe down on page → Pull to refresh (if implemented)

**Tap Gestures**:
- [ ] Single tap → Select
- [ ] Double tap → Zoom (images)
- [ ] Long press → Context menu (if implemented)

**Test Cases**:
- [ ] Gestures don't conflict with scrolling
- [ ] Swipe threshold appropriate (50px)
- [ ] Velocity threshold prevents accidental swipes
- [ ] Haptic feedback works (if supported)
- [ ] No double-tap zoom issues

### 4.3 Scrolling Performance

**Test Cases**:
- [ ] Smooth scroll on touch devices
- [ ] No scroll jank (maintain 60fps)
- [ ] Momentum scrolling works
- [ ] Overscroll bounce appropriate (iOS)
- [ ] Long lists use virtualization (if needed)

**Performance Metrics**:
```javascript
// Use Chrome DevTools Performance panel
// Record scroll interaction
// Check:
// - FPS should be ≥ 60
// - No layout shifts during scroll
// - No forced reflows
```

---

## 5. Loading States & Skeletons

### 5.1 DashboardSkeleton Component

**Test Cases**:
- [ ] Skeleton matches actual layout
- [ ] Pulse animation smooth
- [ ] No layout shift when data loads
- [ ] Skeleton visible for ≥ 500ms (prevents flash)
- [ ] Transition from skeleton to content smooth

**Breakpoint Adaptation**:
- [ ] Mobile: Skeleton shows 1 column layout
- [ ] Tablet: Skeleton shows 2 column layout
- [ ] Desktop: Skeleton shows full grid layout
- [ ] Service count matches breakpoint

### 5.2 Lazy Loading

**Test Cases**:
- [ ] Charts lazy load on scroll (if below fold)
- [ ] Images lazy load with blur placeholder
- [ ] Suspense boundaries work correctly
- [ ] Error boundaries catch lazy load failures
- [ ] Retry mechanism works

---

## 6. Performance Benchmarks

### 6.1 Load Time

**Targets**:
- Initial load < 2 seconds (3G network)
- Time to Interactive (TTI) < 3 seconds
- First Contentful Paint (FCP) < 1 second

**Test Conditions**:
- [ ] Desktop (Fast 4G)
- [ ] Mobile (Slow 3G)
- [ ] Desktop (Offline → online)

**Lighthouse Scores**:
- [ ] Performance ≥ 90
- [ ] Accessibility ≥ 95
- [ ] Best Practices ≥ 90
- [ ] SEO ≥ 90

### 6.2 Animation Performance

**Targets**:
- All animations at 60fps
- No dropped frames during scroll
- No layout thrashing

**Test Cases**:
- [ ] Hover animations smooth
- [ ] Page transitions smooth
- [ ] Chart updates smooth
- [ ] Skeleton pulse animation smooth
- [ ] Modal open/close smooth

**Performance Profiling**:
```javascript
// Use React DevTools Profiler
// Record interaction
// Check for:
// - Components rendering too often
// - Expensive calculations
// - Unnecessary re-renders
```

### 6.3 Memory Usage

**Test Cases**:
- [ ] No memory leaks on page transitions
- [ ] WebSocket connections cleaned up
- [ ] Event listeners removed on unmount
- [ ] Intervals/timeouts cleared
- [ ] Chart instances destroyed

**Testing Method**:
```javascript
// Chrome DevTools Memory panel
// 1. Take heap snapshot
// 2. Navigate around dashboard
// 3. Force garbage collection
// 4. Take another snapshot
// 5. Compare → Should not grow significantly
```

---

## 7. Cross-Browser Testing

### 7.1 Chrome/Chromium

**Test Cases**:
- [ ] All features work
- [ ] Glassmorphism renders
- [ ] Backdrop-filter works
- [ ] Grid layout correct
- [ ] Flexbox layout correct
- [ ] CSS variables work

### 7.2 Firefox

**Test Cases**:
- [ ] All features work
- [ ] Backdrop-filter fallback works
- [ ] Grid layout correct
- [ ] Scrollbar styling correct
- [ ] Font rendering acceptable

### 7.3 Safari (macOS/iOS)

**Known Issues to Check**:
- [ ] Backdrop-filter with -webkit- prefix
- [ ] Date input styling
- [ ] Flexbox gaps support
- [ ] Touch events vs pointer events
- [ ] Safe area insets (iOS)

### 7.4 Edge

**Test Cases**:
- [ ] All features work
- [ ] Legacy Edge (pre-Chromium) not supported (warn user)
- [ ] Chromium Edge works identically to Chrome

---

## 8. Device-Specific Testing

### 8.1 iOS Devices

**Test Cases**:
- [ ] Safe area respected (notch devices)
- [ ] Tap delay removed (300ms fix)
- [ ] Scroll bounce appropriate
- [ ] Fixed position elements don't jump
- [ ] Font smoothing looks good

**Safari-Specific**:
- [ ] Add to Home Screen works
- [ ] Standalone mode works (if PWA)
- [ ] Status bar color correct

### 8.2 Android Devices

**Test Cases**:
- [ ] Back button behavior correct
- [ ] Chrome Android features work
- [ ] Material Design guidelines followed
- [ ] Navigation bar color correct
- [ ] Font rendering acceptable

### 8.3 Tablets (iPad, Android Tablets)

**Test Cases**:
- [ ] Split-screen mode works
- [ ] Landscape orientation optimized
- [ ] Touch and mouse input both work
- [ ] Hover effects appropriate
- [ ] Text selection works

---

## 9. Regression Testing Checklist

Run after each update to ensure nothing broke:

### Core Functionality
- [ ] Dashboard loads without errors
- [ ] All metric cards display data
- [ ] Charts render correctly
- [ ] Service status updates in real-time
- [ ] Quick actions work
- [ ] Theme switching works
- [ ] Navigation works

### Edge Cases
- [ ] Empty state (no data)
- [ ] Error state (API failure)
- [ ] Loading state (slow network)
- [ ] Offline state (no connection)
- [ ] Very long names (overflow handling)
- [ ] Very large numbers (formatting)

---

## 10. User Acceptance Criteria

### System Admin User
- [ ] Can view all metrics clearly
- [ ] Can access all quick actions
- [ ] Can monitor all services
- [ ] Dashboard loads quickly
- [ ] Works on their primary device (desktop)

### Org Admin User
- [ ] Can view relevant metrics
- [ ] Dashboard readable on tablet
- [ ] Can access common actions
- [ ] Responds smoothly to interactions

### Mobile User
- [ ] Dashboard usable on phone
- [ ] All critical info visible
- [ ] Touch interactions work well
- [ ] Loads fast on mobile network
- [ ] Text readable without zooming

---

## Test Execution Matrix

| Test Category | Priority | Time Est. | Status | Notes |
|---------------|----------|-----------|--------|-------|
| **Responsive Design** | | | | |
| - xs breakpoint | High | 2h | ⏳ | |
| - sm breakpoint | High | 1.5h | ⏳ | |
| - md breakpoint | Medium | 1h | ⏳ | |
| - lg breakpoint | Medium | 1h | ⏳ | |
| - xl breakpoint | Low | 0.5h | ⏳ | |
| **Dark Mode** | | | | |
| - Unicorn theme | High | 1h | ⏳ | |
| - Dark theme | High | 1h | ⏳ | |
| - Light theme | Medium | 1h | ⏳ | |
| **Accessibility** | | | | |
| - Color contrast | High | 2h | ⏳ | |
| - Keyboard nav | High | 1.5h | ⏳ | |
| - Screen reader | Medium | 2h | ⏳ | |
| **Touch** | | | | |
| - Touch targets | High | 1h | ⏳ | |
| - Gestures | Medium | 1h | ⏳ | |
| - Scrolling | Medium | 0.5h | ⏳ | |
| **Performance** | | | | |
| - Load time | High | 1h | ⏳ | |
| - Animations | Medium | 1h | ⏳ | |
| - Memory | Low | 1h | ⏳ | |
| **Cross-Browser** | | | | |
| - Chrome | High | 1h | ⏳ | |
| - Firefox | Medium | 1h | ⏳ | |
| - Safari | High | 1.5h | ⏳ | |
| - Edge | Low | 0.5h | ⏳ | |
| **Total** | | **25h** | | |

---

## Issue Tracking Template

When issues are found, log them using this format:

```markdown
### Issue #[NUMBER]

**Title**: [Brief description]
**Severity**: Critical / High / Medium / Low
**Category**: Responsive / Dark Mode / Accessibility / Performance / Touch
**Breakpoint**: xs / sm / md / lg / xl (if responsive)
**Theme**: Unicorn / Dark / Light (if dark mode)
**Browser**: Chrome / Firefox / Safari / Edge
**Device**: Desktop / Tablet / Mobile

**Description**:
[Detailed description of the issue]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**:
[What should happen]

**Actual Behavior**:
[What actually happens]

**Screenshots**:
[Attach screenshots if applicable]

**Fix Suggestion**:
[Optional: Suggested fix]
```

---

## Sign-Off Checklist

Before marking Epic 2.5 as complete:

- [ ] All high-priority tests passed
- [ ] All critical issues resolved
- [ ] All medium-priority issues documented (can defer to Phase 3)
- [ ] Lighthouse accessibility score ≥ 95
- [ ] All WCAG AA requirements met
- [ ] Works on all 5 breakpoints
- [ ] Works in all 3 themes
- [ ] Works in 4 major browsers
- [ ] Performance benchmarks met
- [ ] User acceptance criteria met
- [ ] Documentation complete
- [ ] Code reviewed and approved

---

**Test Plan Version**: 1.0.0
**Last Updated**: October 24, 2025
**Next Review**: After Epic 2.5 completion
