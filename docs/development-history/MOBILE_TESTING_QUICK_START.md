# Mobile Testing Quick Start Guide

**Epic 2.7: Mobile Responsiveness**
**Status**: ✅ Ready to Execute

---

## ⚡ 5-Minute Quick Start

### 1. Install Dependencies

```bash
cd /opt/ops-center
npm install
npx playwright install --with-deps chromium
```

### 2. Run Tests

```bash
# All mobile tests (135 tests, ~3-5 minutes)
npm run test:mobile

# View report
npm run test:mobile:report
```

### 3. Review Results

Open `playwright-report/index.html` in browser to see:
- ✅ Tests passed
- ❌ Tests failed
- ⚠️ Issues found

---

## 📋 What Was Delivered

| Item | Count | Lines |
|------|-------|-------|
| **Automated Tests** | 135 tests | 2,710 |
| **Documentation** | 4 files | 3,241 |
| **Total** | 7 files | **5,951** |

---

## 🧪 Test Suites

### Responsiveness (80 tests)
```bash
npm run test:mobile:responsiveness
```
Tests: Viewports, layout, touch targets, tables, forms, navigation

### Accessibility (30 tests)
```bash
npm run test:mobile:accessibility
```
Tests: WCAG AA, screen readers, zoom, contrast, touch targets

### Performance (25 tests)
```bash
npm run test:mobile:performance
```
Tests: Load times, Web Vitals, scroll, memory, bundles

---

## 📱 Devices Tested

**Automated**:
- iPhone SE (375x667)
- iPhone 12 Pro (390x844)
- iPhone 12 Pro Max (428x926)
- Galaxy S21 (360x800)
- iPad Mini (768x1024)
- iPad Pro (1024x1366)

**Manual** (20+ devices):
- See `/docs/MOBILE_TESTING_GUIDE.md` Section 2

---

## 📖 Documentation

| Document | Purpose | Lines |
|----------|---------|-------|
| `tests/mobile/README.md` | Quick start, troubleshooting | 473 |
| `docs/MOBILE_TESTING_GUIDE.md` | Manual testing checklist (100+ items) | 1,449 |
| `MOBILE_TESTING_DELIVERY_REPORT.md` | Complete delivery docs | 846 |
| `EPIC_2.7_MOBILE_TESTING_COMPLETE.md` | Summary & completion report | 473 |

---

## 🎯 Success Criteria

**Before Release**:
- [ ] All 135 automated tests passing
- [ ] Manual testing on 5+ devices
- [ ] P0 issues fixed
- [ ] Lighthouse score > 80
- [ ] No horizontal scrolling
- [ ] Forms usable (no iOS zoom)

---

## 🔧 Common Commands

```bash
# Run all tests
npm run test:mobile

# Run with UI (debug mode)
npm run test:mobile:ui

# Run specific test
npx playwright test -g "iPhone SE"

# View report
npm run test:mobile:report

# Debug failing test
npx playwright test --debug -g "test name"
```

---

## 🐛 Troubleshooting

**Tests fail: "Connection refused"**
```bash
# Ensure Ops-Center is running
docker ps | grep ops-center-direct
```

**Tests fail: "Element not found"**
```bash
# Use Playwright Inspector
npx playwright test --debug
```

**Need more info?**
- See `tests/mobile/README.md` - Troubleshooting section
- See `docs/MOBILE_TESTING_GUIDE.md` - Common Issues & Fixes

---

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Page Load (Fast 3G) | < 3s |
| First Contentful Paint | < 2s |
| Largest Contentful Paint | < 2.5s |
| Cumulative Layout Shift | < 0.1 |
| Time to Interactive | < 5s |
| First Input Delay | < 100ms |
| Lighthouse Score | > 80 |

---

## ✅ Test Coverage

**Automated**: 135 tests
- 80 responsiveness tests
- 30 accessibility tests
- 25 performance tests

**Manual**: 100+ checklist items
- 17 pages covered
- 20+ devices
- 6+ browsers

---

## 📞 Support

**For Questions**:
1. Check `tests/mobile/README.md`
2. Review `docs/MOBILE_TESTING_GUIDE.md`
3. See `MOBILE_TESTING_DELIVERY_REPORT.md`

**For Bugs Found**:
- Use bug template in Mobile Testing Guide
- Include device, browser, screenshots
- Attach console errors

---

## 🚀 Next Steps

**Day 1**:
1. Install dependencies
2. Run automated tests
3. Review results

**Day 2**:
4. Fix P0 issues
5. Re-run tests
6. Manual smoke test

**Week 1**:
7. Execute manual checklist
8. Test on 5+ devices
9. Performance baseline

---

**Quick Links**:
- Tests: `/tests/mobile/`
- Docs: `/docs/MOBILE_TESTING_GUIDE.md`
- Report: `/MOBILE_TESTING_DELIVERY_REPORT.md`

---

**Status**: ✅ READY TO EXECUTE

**Date**: October 24, 2025
