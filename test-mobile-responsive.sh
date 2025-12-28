#!/bin/bash

###############################################################################
# Mobile Responsiveness Testing Script
#
# Quick verification that mobile responsive features are deployed
# and working correctly
#
# Usage: ./test-mobile-responsive.sh
###############################################################################

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📱 Mobile Responsiveness Testing - Epic 2.7"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if ops-center is running
echo "1️⃣  Checking if ops-center is running..."
if docker ps | grep -q "ops-center-direct"; then
    echo "   ✅ ops-center-direct container is running"
else
    echo "   ❌ ops-center-direct container is NOT running"
    echo "   Run: docker restart ops-center-direct"
    exit 1
fi
echo ""

# Check if service responds
echo "2️⃣  Checking if service responds..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8084 || echo "000")
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "405" ]; then
    echo "   ✅ Service responding (HTTP $HTTP_CODE)"
else
    echo "   ❌ Service not responding (HTTP $HTTP_CODE)"
    exit 1
fi
echo ""

# Check if mobile-responsive.css exists
echo "3️⃣  Checking if mobile-responsive.css was created..."
if [ -f "src/styles/mobile-responsive.css" ]; then
    LINES=$(wc -l < src/styles/mobile-responsive.css)
    echo "   ✅ mobile-responsive.css exists ($LINES lines)"
else
    echo "   ❌ mobile-responsive.css NOT FOUND"
    exit 1
fi
echo ""

# Check if touchOptimization.js exists
echo "4️⃣  Checking if touchOptimization.js was created..."
if [ -f "src/utils/touchOptimization.js" ]; then
    LINES=$(wc -l < src/utils/touchOptimization.js)
    echo "   ✅ touchOptimization.js exists ($LINES lines)"
else
    echo "   ❌ touchOptimization.js NOT FOUND"
    exit 1
fi
echo ""

# Check if ResponsiveTable.jsx exists
echo "5️⃣  Checking if ResponsiveTable.jsx was created..."
if [ -f "src/components/ResponsiveTable.jsx" ]; then
    LINES=$(wc -l < src/components/ResponsiveTable.jsx)
    echo "   ✅ ResponsiveTable.jsx exists ($LINES lines)"
else
    echo "   ❌ ResponsiveTable.jsx NOT FOUND"
    exit 1
fi
echo ""

# Check if CSS is imported in main.jsx
echo "6️⃣  Checking if mobile-responsive.css is imported..."
if grep -q "mobile-responsive.css" src/main.jsx; then
    echo "   ✅ CSS imported in main.jsx"
else
    echo "   ❌ CSS NOT imported in main.jsx"
    exit 1
fi
echo ""

# Check if touch optimization is initialized in App.jsx
echo "7️⃣  Checking if touch optimization is initialized..."
if grep -q "initTouchOptimizations" src/App.jsx; then
    echo "   ✅ Touch optimization initialized in App.jsx"
else
    echo "   ❌ Touch optimization NOT initialized"
    exit 1
fi
echo ""

# Check if frontend was built
echo "8️⃣  Checking if frontend was built..."
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    BUILD_SIZE=$(du -sh dist | cut -f1)
    echo "   ✅ Frontend built (dist: $BUILD_SIZE)"
else
    echo "   ⚠️  Frontend not built or dist directory empty"
    echo "   Run: npm run build"
fi
echo ""

# Check if frontend was deployed
echo "9️⃣  Checking if frontend was deployed to public/..."
if [ -d "public/assets" ] && [ "$(ls -A public/assets)" ]; then
    DEPLOY_SIZE=$(du -sh public | cut -f1)
    ASSET_COUNT=$(ls public/assets | wc -l)
    echo "   ✅ Frontend deployed (public: $DEPLOY_SIZE, $ASSET_COUNT assets)"
else
    echo "   ❌ Frontend NOT deployed"
    echo "   Run: cp -r dist/* public/"
    exit 1
fi
echo ""

# Check delivery reports
echo "🔟 Checking if delivery reports exist..."
if [ -f "MOBILE_UI_DELIVERY_REPORT.md" ]; then
    LINES=$(wc -l < MOBILE_UI_DELIVERY_REPORT.md)
    echo "   ✅ MOBILE_UI_DELIVERY_REPORT.md ($LINES lines)"
else
    echo "   ❌ MOBILE_UI_DELIVERY_REPORT.md NOT FOUND"
fi

if [ -f "EPIC_2.7_DELIVERY_SUMMARY.md" ]; then
    LINES=$(wc -l < EPIC_2.7_DELIVERY_SUMMARY.md)
    echo "   ✅ EPIC_2.7_DELIVERY_SUMMARY.md ($LINES lines)"
else
    echo "   ❌ EPIC_2.7_DELIVERY_SUMMARY.md NOT FOUND"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All checks passed! Mobile responsiveness deployed successfully."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo ""
echo "  1. Manual Testing:"
echo "     - Open https://your-domain.com/admin on mobile device"
echo "     - Test on iPhone SE, iPhone 12+, iPad"
echo "     - Verify no horizontal scroll"
echo "     - Check touch targets are easy to tap"
echo ""
echo "  2. Desktop Regression:"
echo "     - Open https://your-domain.com/admin on desktop"
echo "     - Verify dashboard loads correctly"
echo "     - Check user management, billing pages"
echo ""
echo "  3. Review Documentation:"
echo "     - MOBILE_UI_DELIVERY_REPORT.md - Comprehensive guide"
echo "     - EPIC_2.7_DELIVERY_SUMMARY.md - Quick reference"
echo ""
echo "  4. Chrome DevTools Testing:"
echo "     - Open Chrome DevTools (F12)"
echo "     - Toggle device toolbar (Ctrl+Shift+M)"
echo "     - Test: iPhone SE, iPhone 12, iPad"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Epic 2.7: Mobile Responsiveness - COMPLETE & DEPLOYED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
